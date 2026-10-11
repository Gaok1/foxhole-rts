"""Regressao: suites existentes contra o candidato ECONOMIA + PERSISTENCIA, em memoria (main.lua real intacto).

1. tools/test_orders.py inteiro, com o main.lua trocado pelo candidato.
2. data/parallel/economy/test_integration.py inteiro, com o build da economia trocado pelo build combinado
   (prova que a persistencia nao muda producao/transporte/recrutamento/medico/snapshot da economia).
3. tools/check_globals.py no candidato gerado em candidate/main.lua.
Uso (raiz do repo, bash): PYTHONPATH=D:/tools/pylibs python data/parallel/persistence/test_regression.py
"""
from pathlib import Path
import subprocess
import sys
import types

HERE = Path(__file__).resolve().parent
ROOT = HERE.parents[2]
sys.path.insert(0, str(HERE))
import build_patch  # noqa: E402

source = ROOT.joinpath("mod/FoxholeRTS/Scripts/main.lua").read_text(encoding="utf-8")
candidate = build_patch.build(source)

# 1. test_orders.py
orders = ROOT.joinpath("tools/test_orders.py").read_text(encoding="utf-8")
anchor = 'source = (Path(__file__).resolve().parents[1] / "mod/FoxholeRTS/Scripts/main.lua").read_text(encoding="utf-8")'
assert orders.count(anchor) == 1, "âncora do test_orders mudou"
orders = orders.replace(anchor, "source = CANDIDATE")
exec(compile(orders, "tools/test_orders.py[candidato]", "exec"),
     {"__file__": str(ROOT / "tools/test_orders.py"), "CANDIDATE": candidate, "__name__": "test_orders_candidate"})
print("PASS 1/3: tools/test_orders.py contra o candidato economia+persistência")

# 1b. tools/test_orders.py contra a pilha com a IA_LOGISTICA (se o build dela fechar)
try:
    candidate_ia = build_patch.build_with_ia(source)
except Exception as e:  # noqa: BLE001
    candidate_ia = None
    print(f"SKIP 1b: pilha com IA_LOGISTICA não construiu ({type(e).__name__}: {e})")
if candidate_ia:
    # A IA_LOGISTICA remove o contrato abstrato do comboio; o bloco correspondente da suite e trocado pelo dela
    # (mesma tecnica de logistics_ai/test_orders_candidate.py), o resto da suite fica intacto.
    orders_ia = orders.replace("source = CANDIDATE", "source = CANDIDATE_IA")
    old_start = "-- enemy convoy: missing cargo shrinks the wave; arriving adds cargo; our soldiers nearby destroy it\n"
    old_end = 'assert(cv2.state == "dead" and api.combat.convoysCut == cut0 + 1)\n'
    assert orders_ia.count(old_start) == 1 and orders_ia.count(old_end) == 1, "bloco do comboio mudou na suíte"
    a = orders_ia.index(old_start)
    b = orders_ia.index(old_end, a) + len(old_end)
    orders_ia = orders_ia[:a] + ROOT.joinpath("data/parallel/logistics_ai/test_orders_convoy_block.lua").read_text(encoding="utf-8") + orders_ia[b:]
    exec(compile(orders_ia, "tools/test_orders.py[candidato+IA]", "exec"),
         {"__file__": str(ROOT / "tools/test_orders.py"), "CANDIDATE_IA": candidate_ia, "__name__": "test_orders_candidate_ia"})
    print("PASS 1b: tools/test_orders.py contra main+ECONOMIA+IA_LOGISTICA+PERSISTENCIA")

# 2. economy/test_integration.py com o build combinado
fake = types.ModuleType("build_patch")
fake.build, fake.ROOT, fake.HERE = build_patch.build, ROOT, ROOT / "data/parallel/economy"
saved = sys.modules.get("build_patch")
sys.modules["build_patch"] = fake
try:
    integ = ROOT.joinpath("data/parallel/economy/test_integration.py").read_text(encoding="utf-8")
    exec(compile(integ, "economy/test_integration.py[candidato]", "exec"), {"__name__": "economia_candidate"})
finally:
    if saved is not None:
        sys.modules["build_patch"] = saved
print("PASS 2/3: economy/test_integration.py contra o candidato economia+persistência")

# 3. check_globals no candidato escrito em disco (gerado pelo build_patch)
cand_file = HERE / "candidate/main.lua"
assert cand_file.exists() and cand_file.read_text(encoding="utf-8") == candidate, "rode build_patch.py antes (candidato desatualizado)"
r = subprocess.run([sys.executable, str(ROOT / "tools/check_globals.py"), str(cand_file)], capture_output=True, text=True)
print(r.stdout.strip())
assert r.returncode == 0, r.stdout + r.stderr
print("PASS 3/3: check_globals.py no candidato")
cand_ia = HERE / "candidate/main_with_ai.lua"
if candidate_ia and cand_ia.exists():
    assert cand_ia.read_text(encoding="utf-8") == candidate_ia, "rode build_patch.py antes (candidato com IA desatualizado)"
    r = subprocess.run([sys.executable, str(ROOT / "tools/check_globals.py"), str(cand_ia)], capture_output=True, text=True)
    assert r.returncode == 0, r.stdout + r.stderr
    print("PASS 3b: check_globals.py no candidato com IA_LOGISTICA")

# 4. Suite da IA_LOGISTICA (test_logistics_ai.py) contra main+ECONOMIA+IA_LOGISTICA+PERSISTENCIA.
#    O build dela e trocado pelo empilhado com a persistencia; os dois rotulos dela rodam a mesma pilha.
if candidate_ia:
    import importlib.util
    spec = importlib.util.spec_from_file_location("ia_logistica_build_patch_reg", build_patch.IA)
    ia_mod = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(ia_mod)
    stack = lambda s: build_patch.build_on(ia_mod.build(build_patch.economy_build()(s))[0])  # noqa: E731
    fake_ia = types.ModuleType("build_patch")
    fake_ia.build, fake_ia.stacked = (lambda s: (stack(s), True)), stack
    saved = sys.modules.get("build_patch")
    sys.modules["build_patch"] = fake_ia
    try:
        ia_test = ROOT / "data/parallel/logistics_ai/test_logistics_ai.py"
        exec(compile(ia_test.read_text(encoding="utf-8"), "logistics_ai/test_logistics_ai.py[candidato]", "exec"),
             {"__name__": "__main__", "__file__": str(ia_test)})
    finally:
        if saved is not None:
            sys.modules["build_patch"] = saved
    print("PASS 4: logistics_ai/test_logistics_ai.py contra main+ECONOMIA+IA_LOGISTICA+PERSISTENCIA")
