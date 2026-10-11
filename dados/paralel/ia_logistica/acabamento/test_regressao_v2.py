"""Regressao da pilha completa proposta (ECONOMIA -> IA_LOGISTICA v2 -> reserva de bmat -> PERSISTENCIA v2), em memoria
(main.lua real intacto). Mesma tecnica de persistencia/test_regressao.py.

  cd /d/GitHub/foxhole-rts && PYTHONPATH=D:/tools/pylibs PYTHONDONTWRITEBYTECODE=1 PYTHONIOENCODING=utf-8 \
      python dados/paralel/ia_logistica/acabamento/test_regressao_v2.py

1. tools/test_orders.py inteiro sobre a pilha completa (o bloco do comboio abstrato e trocado pelo da IA, como em
   ia_logistica/test_orders_candidato.py).
2. economia/test_integracao.py sobre a pilha completa.
3. test_ia_logistica_v2.py sobre a pilha completa (as duas rotulagens rodam a mesma pilha).
4. tools/check_globals.py no candidato gerado e contagem de locais de topo (178, como o main atual).
5. As ordens reserva->persistencia e persistencia->reserva geram o mesmo texto (os patches comutam).
"""
import subprocess
import sys
import types
from pathlib import Path

HERE = Path(__file__).resolve().parent
ROOT = HERE.parents[3]
sys.dont_write_bytecode = True
sys.path.insert(0, str(HERE))
import build_persistencia_v2 as bp  # noqa: E402

source = ROOT.joinpath("mod/FoxholeRTS/Scripts/main.lua").read_text(encoding="utf-8")
full = bp.build_full(source)

# 1. test_orders.py com o bloco do comboio da IA
orders = ROOT.joinpath("tools/test_orders.py").read_text(encoding="utf-8")
anchor = 'source = (Path(__file__).resolve().parents[1] / "mod/FoxholeRTS/Scripts/main.lua").read_text(encoding="utf-8")'
assert orders.count(anchor) == 1, "âncora do test_orders mudou"
orders = orders.replace(anchor, "source = CANDIDATE")
old_start = "-- enemy convoy: missing cargo shrinks the wave; arriving adds cargo; our soldiers nearby destroy it\n"
old_end = 'assert(cv2.state == "dead" and api.combat.convoysCut == cut0 + 1)\n'
assert orders.count(old_start) == 1 and orders.count(old_end) == 1, "bloco do comboio mudou na suíte"
a = orders.index(old_start)
b = orders.index(old_end, a) + len(old_end)
orders = orders[:a] + HERE.joinpath("test_orders_bloco_comboio_v2.lua").read_text(encoding="utf-8") + orders[b:]
exec(compile(orders, "tools/test_orders.py[pilha completa]", "exec"),
     {"__file__": str(ROOT / "tools/test_orders.py"), "CANDIDATE": full, "__name__": "test_orders_full"})
print("PASS 1/5: tools/test_orders.py contra a pilha completa")

# 2. economia/test_integracao.py
fake = types.ModuleType("build_patch")
fake.build, fake.ROOT, fake.HERE = bp.build_full, ROOT, ROOT / "dados/paralel/economia"
saved = sys.modules.get("build_patch")
sys.modules["build_patch"] = fake
try:
    integ = ROOT.joinpath("dados/paralel/economia/test_integracao.py").read_text(encoding="utf-8")
    exec(compile(integ, "economia/test_integracao.py[pilha completa]", "exec"), {"__name__": "economia_full"})
finally:
    if saved is not None:
        sys.modules["build_patch"] = saved
    else:
        sys.modules.pop("build_patch", None)
print("PASS 2/5: economia/test_integracao.py contra a pilha completa")

# 3. test_ia_logistica_v2.py sobre a pilha completa
fake_ia = types.ModuleType("build_patch_v2")
fake_ia.build, fake_ia.stacked = (lambda s: (bp.build_full(s), True)), bp.build_full
saved = sys.modules.get("build_patch_v2")
sys.modules["build_patch_v2"] = fake_ia
try:
    ia_test = HERE / "test_ia_logistica_v2.py"
    exec(compile(ia_test.read_text(encoding="utf-8"), "test_ia_logistica_v2.py[pilha completa]", "exec"),
         {"__name__": "__main__", "__file__": str(ia_test)})
finally:
    if saved is not None:
        sys.modules["build_patch_v2"] = saved
    else:
        sys.modules.pop("build_patch_v2", None)
print("PASS 3/5: test_ia_logistica_v2.py contra a pilha completa")

# 4. check_globals + locais de topo
cand = HERE / "main_final_v2.lua"
assert cand.exists() and cand.read_text(encoding="utf-8") == full, "rode build_persistencia_v2.py antes (candidato desatualizado)"
r = subprocess.run([sys.executable, str(ROOT / "tools/check_globals.py"), str(cand)], capture_output=True, text=True)
print(r.stdout.strip() or "(check_globals sem saída)")
assert r.returncode == 0, r.stdout + r.stderr


def top_locals(text):
    return sum(1 for line in text.splitlines() if line.startswith("local "))


assert top_locals(full) == top_locals(source) == 178, (top_locals(full), top_locals(source))
print("PASS 4/5: check_globals limpo; locais de topo %d (main atual %d)" % (top_locals(full), top_locals(source)))

# 5. comutatividade reserva x persistencia
reserva = bp.reserva()
ia_econ = bp.ia_build()(bp.economy_build()(source))[0]
assert bp.build_on(reserva(ia_econ)) == reserva(bp.build_on(ia_econ)), "os patches nao comutam"
print("PASS 5/5: reserva->persistencia == persistencia->reserva")

# 6. (se a pasta do ensaio de integracao existir) a pilha v2 compoe com o painel da INTERFACE rebaseado, em qualquer ordem
try:
    sys.path.insert(0, str(ROOT / "dados/paralel/ensaio_integracao"))
    import build_pilha as pilha  # noqa: E402  (so define funcoes; o __main__ dele nao roda)
except Exception as e:  # noqa: BLE001
    print("SKIP 6/6: ensaio_integracao indisponivel (%s: %s)" % (type(e).__name__, e))
else:
    src_lf, _ = pilha.read_main()
    base = bp.ia_build()(bp.economy_build()(src_lf))[0]
    with_ui_a = bp.build_on(reserva(pilha.interface_build(base)))
    with_ui_b = bp.build_on(pilha.interface_build(reserva(base)))
    assert with_ui_a == with_ui_b, "INTERFACE e reserva nao comutam"
    assert top_locals(with_ui_a) == 178
    print("PASS 6/6: ECONOMIA+IA_v2+INTERFACE(rebaseada)+reserva+PERSISTENCIA_v2 compoe, comuta e mantem 178 locais de topo")
