"""PACOTE_V4: bateria offline PERMANENTE para o main.lua DEPOIS da integracao da pilha v4.

Nao escreve nada em disco (so stdout): le o main, executa copias em memoria dos testes originais com a obtencao do candidato trocada
(tecnicas `BASES_V4_FILE` e `__CANDIDATE`, as mesmas de forward_bases/stage2/test_stack_v4.py, cujo texto e reaproveitado aqui:
os passos 05-09 dele nao dependem do build). Nao roda build_*.py, run_all.sh nem test_stack_v3.py (eles gravam arquivos).

  cd /d/GitHub/foxhole-rts
  PYTHONPATH=D:/tools/pylibs PYTHONDONTWRITEBYTECODE=1 python data/parallel/package_v4/post_integration_battery.py [--main ARQ] [--rapido] [--sensibilidade]

  --main ARQ        arquivo a testar (padrao: mod/FoxholeRTS/Scripts/main.lua). Antes da integracao, ensaie com
                    --main data/parallel/forward_bases/stage2/candidate_v4/main.lua
  --base ARQ        main ANTERIOR a integracao (padrao: package_v4/pre_integration_base/main_actual_33d6c7e5.lua, SHA 33d6c7e5...).
                    Varios testes antigos montam pilhas alternativas ('sem IA', 'sem coleta') aplicando os build_*.py ao main
                    original; depois da integracao o main real nao tem mais as ancoras, entao a leitura de
                    mod/FoxholeRTS/Scripts/main.lua feita POR ESSES TESTES (Path.read_text) e redirecionada, em memoria, para este arquivo.
  --rapido          pula as suites lentas (IA 25x600 passos e persistencia_v2)
  --sensibilidade   inclui sensitivity_bases.py (21 mutantes; lento)
Saida: uma linha PASS/FAIL por item e RESUMO. rc 0 = tudo PASS. Nada aqui prova fisica Unreal, rota, entrada nem equilibrio.
"""
import argparse
import contextlib
import io
import os
import subprocess
import sys
import time
import traceback
import types
from pathlib import Path
import hashlib

sys.dont_write_bytecode = True
HERE = Path(__file__).resolve().parent
PARALEL = HERE.parent
ROOT = PARALEL.parents[1]
ETAPA2 = PARALEL / "forward_bases/stage2"
ACAB = PARALEL / "logistics_ai/finishing"
COLETA = ACAB / "manual_collection"
TOOLS = ROOT / "tools"
MAIN_REAL = ROOT / "mod/FoxholeRTS/Scripts/main.lua"
PILHA_V4 = ETAPA2 / "test_stack_v4.py"
BASE_DEFAULT = HERE / "pre_integration_base/main_actual_33d6c7e5.lua"
BASE_SHA = "33d6c7e5920a3b5e00b7f3bafbc7b8a86c984db810217241a567afe0901ee679"
SUMMARY = []
# Os testes imprimem pelo print do Lua (stdout em C): descartamos o fd 1 e escrevemos o nosso relatorio por uma copia dele.
REAL = os.fdopen(os.dup(1), "w", buffering=1, encoding="utf-8", errors="replace")
os.dup2(os.open(os.devnull, os.O_WRONLY), 1)


def say(*a):
    print(*a, file=REAL, flush=True)


def report(name, ok, dt, note=""):
    SUMMARY.append((name, ok, dt, note))
    say("%s  %s (%.1f s)%s" % ("PASS" if ok else "FAIL", name, dt, ("  -> " + note) if note else ""))


def run_proc(name, cmd, env_extra=None, must_have=None):
    env = dict(os.environ, PYTHONDONTWRITEBYTECODE="1", PYTHONIOENCODING="utf-8")
    env.update(env_extra or {})
    t0 = time.time()
    r = subprocess.run(cmd, cwd=str(ROOT), env=env, capture_output=True, text=True, encoding="utf-8", errors="replace")
    out = (r.stdout or "") + (r.stderr or "")
    ok = r.returncode == 0 and (must_have is None or must_have in out)
    note = ""
    if not ok:
        lines = [l for l in out.strip().splitlines() if l.strip()]
        key = [l for l in lines if "FALHARAM" in l or l.startswith("FAIL") or "Error" in l][:3]
        note = "rc=%d; %s" % (r.returncode, " | ".join(key or lines[-3:])[:600])
    report(name, ok, time.time() - t0, note)
    return ok


def split_pilha_source(main_path):
    """Texto do test_stack_v4.py com o bloco 'constroi o candidato' trocado por 'le o main'. Somente em memoria."""
    s = PILHA_V4.read_text(encoding="utf-8")

    def swap(text, old, new):
        assert text.count(old) == 1, "ancora do test_pilha_v4 mudou: %r" % old[:70]
        return text.replace(old, new, 1)

    s = swap(s, "import build_pilha as bp  # noqa: E402\nimport build_coleta  # noqa: E402\nimport build_bases  # noqa: E402  (V4)\n",
             "bp = __BP\n")
    a = s.index('SOURCE, SHA_BEFORE, STAGES = bp.build_candidate("v2")')
    marker = "MAIN_FILE = bp.MAIN\n"
    b = s.index(marker, a) + len(marker)
    block = (
        "SOURCE = SHA_BEFORE = CAND_V3 = CAND_V2 = None\nSTAGES = []\n"
        "CAND = __MAIN_TEXT\n"
        'CAND_LEGACY = CAND.replace("manualStart = true,", "manualStart = false,", 1)\nassert CAND_LEGACY != CAND\n'
        "CAND_FILE = CAND_V3_FILE = CAND_V2_FILE = MAIN_FILE = __MAIN_PATH\n"
    )
    return s[:a] + block + s[b:]


def load_pilha(main_path):
    text = main_path.read_bytes().decode("utf-8").replace("\r\n", "\n")
    bp = types.SimpleNamespace(ROOT=ROOT, PAR=PARALEL, ACAB=ACAB, MAIN=main_path)
    g = {"__name__": "test_pilha_v4_pos", "__file__": str(PILHA_V4), "__BP": bp, "__MAIN_TEXT": text, "__MAIN_PATH": main_path}
    exec(compile(split_pilha_source(main_path), "test_stack_v4.py[pos-integracao]", "exec"), g)
    return g, text


def run_step(g, fname):
    """Executa uma etapa decorada do test_pilha_v4 (ela mesma imprime PASS/FAIL); registra no nosso resumo."""
    before = len(g["SUMMARY"])
    sys_stdout = sys.stdout
    buf = io.StringIO()
    with contextlib.redirect_stdout(buf):
        g[fname]()
    sys.stdout = sys_stdout
    line = buf.getvalue().strip().splitlines()[-1] if buf.getvalue().strip() else ""
    n, ok, dt, note = g["SUMMARY"][before]
    report("pilha/" + n[:110], ok, dt, note if not ok else "")
    if not ok:
        say("   " + "\n   ".join(g["LOG"][-1].splitlines()[-12:]))
    return ok


def main():
    ap = argparse.ArgumentParser(description=__doc__, formatter_class=argparse.RawDescriptionHelpFormatter)
    ap.add_argument("--main", default=str(MAIN_REAL))
    ap.add_argument("--base", default=str(BASE_DEFAULT))
    ap.add_argument("--rapido", action="store_true")
    ap.add_argument("--sensibilidade", action="store_true")
    args = ap.parse_args()
    main_path = Path(args.main).resolve()
    default = main_path == MAIN_REAL.resolve()
    sha_before = hashlib.sha256(main_path.read_bytes()).hexdigest()
    say("alvo: %s\nSHA256: %s\nraiz: %s" % (main_path, sha_before, ROOT))
    base = Path(args.base).resolve()
    assert hashlib.sha256(base.read_bytes()).hexdigest() == BASE_SHA, "o --base nao e o main anterior a integracao (SHA 33d6c7e5...)"
    base_text = base.read_bytes().decode("utf-8").replace("\r\n", "\n")
    orig_read_text = Path.read_text

    def read_text(self, *a, **k):   # testes antigos leem o 'main real' para montar pilhas alternativas: entregue-lhes o main ANTERIOR
        try:
            if self.resolve() == MAIN_REAL.resolve():
                return base_text
        except OSError:
            pass
        return orig_read_text(self, *a, **k)
    Path.read_text = read_text
    say("base (main anterior, so para as pilhas alternativas dos testes antigos): %s" % base)
    env_main = {"BASES_V4_FILE": str(main_path)}
    py = [sys.executable, "-B"]

    # 1. estatico: sintaxe, locais, check_globals
    t0 = time.time()
    g, text = load_pilha(main_path)
    try:
        notes = []
        for ver in ("lua54", "lua55"):
            ok, err = g["compiles"](ver, text)
            assert ok, "%s nao compila: %s" % (ver, err)
            slack = g["lua_slack"](ver, text)
            notes.append("%s folga %d locais" % (ver, slack))
            assert slack >= 1, "limite de 200 locais estourado (%s)" % ver
        report("estatico/sintaxe Lua 5.4 e 5.5 + limite de 200 locais", True, time.time() - t0, "; ".join(notes) + " (v4: 22)")
    except AssertionError as e:
        report("estatico/sintaxe Lua 5.4 e 5.5 + limite de 200 locais", False, time.time() - t0, str(e)[:300])
    t0 = time.time()
    r = subprocess.run(py + [str(TOOLS / "check_globals.py"), str(main_path)], cwd=str(ROOT), capture_output=True, text=True)
    out = r.stdout + r.stderr
    report("estatico/tools/check_globals.py", r.returncode == 0 and "aviso" not in out, time.time() - t0, out.strip()[:300])
    for needle in ("function logi.hudLine(", "function logi.extraHud(", "function logi.fwdKey(", "function logi.rebuildReserve("):
        if text.count(needle) != 1:
            report("estatico/definicao unica " + needle, False, 0.0, "contagem %d" % text.count(needle))
    report("estatico/sem residuos do contrato antigo (cargo0/perWave/ECONVOY.cut, load(txt, ESTRADAS)", all(
        x not in text for x in ("cargo0", "perWave", "ECONVOY.cut", "load(txt", "native_adapter", "roads.")), 0.0)

    # 2. tools
    run_proc("tools/test_costs.py", py + [str(TOOLS / "test_costs.py")])
    run_proc("tools/test_inventory_probe.py", py + [str(TOOLS / "test_inventory_probe.py")])
    # 3. test_orders: texto adaptado em memoria (vale antes e depois de gravar a versao nova em tools/)
    t0 = time.time()
    try:
        sys.path.insert(0, str(HERE))
        import aplicar_test_orders as AT
        raw = (TOOLS / "test_orders.py").read_bytes()
        built, _ = AT.build(raw)
        s = (built if built is not None else raw.decode("utf-8").replace("\r\n", "\n"))
        line = 'source = (Path(__file__).resolve().parents[1] / "mod/FoxholeRTS/Scripts/main.lua").read_text(encoding="utf-8")'
        assert s.count(line) == 1
        s = s.replace(line, "source = __CANDIDATE")
        buf = io.StringIO()
        with contextlib.redirect_stdout(buf):
            exec(compile(s, "tools/test_orders.py[v4]", "exec"), {"__file__": str(TOOLS / "test_orders.py"), "__name__": "__main__", "__CANDIDATE": text})
        report("tools/test_orders.py (versao v4, em memoria; teclas incl. SHIFT+J)", True, time.time() - t0,
               "tools/test_orders.py em disco " + ("ja esta adaptado" if built is None else "ainda NAO adaptado: rode apply_test_orders.py --write"))
    except BaseException as e:  # noqa: BLE001
        report("tools/test_orders.py (versao v4, em memoria)", False, time.time() - t0, "%s: %s" % (type(e).__name__, str(e)[:300]))
    if default and b"ADAPTACAO bases avancadas" in (TOOLS / "test_orders.py").read_bytes():
        run_proc("tools/test_orders.py em disco (processo separado)", py + [str(TOOLS / "test_orders.py")], must_have="PASS")

    # 4. suites das bases e da coleta, apontadas ao main (BASES_V4_FILE)
    for name in ("construcao", "recrutamento", "perda", "trabalhadores", "persistencia_bases", "painel_teclas", "coleta_sobre_v4"):
        run_proc("bases/test_%s.py" % name, py + [str(ETAPA2 / ("test_%s.py" % name))], env_main)

    # 4b. v4.1: trabalhadores nao escalam a onda nem seguram a derrota (so faz sentido no v4.1; no v4 puro este item FALHA, de proposito)
    run_proc("v4_1/test_v4_1.py (trabalhadores fora da escala das ondas)", py + [str(HERE / "v4_1/test_v4_1.py"), "--so-v41", str(main_path)], env_main)

    # 5. suites das outras pastas (passos 05-09 do test_pilha_v4, ja com a obtencao do candidato trocada)
    steps = ["t_economia", "t_elogi", "t_elogi_legacy", "t_bmat", "t_interface_original", "t_interface_candidato",
             "t_interface_integrada", "t_interface_v2", "t_contrato_estradas"]
    if not args.rapido:
        steps = ["t_economia", "t_ia"] + steps[1:] + ["t_persistencia", "t_persistencia_legacy"]
    for fn in steps:
        try:
            run_step(g, fn)
        except BaseException as e:  # noqa: BLE001
            report("pilha/" + fn, False, 0.0, "%s: %s\n%s" % (type(e).__name__, e, traceback.format_exc()[-600:]))

    if args.sensibilidade:
        run_proc("bases/sensitivity_bases.py (21 mutantes)", py + [str(ETAPA2 / "sensitivity_bases.py")], env_main)

    Path.read_text = orig_read_text
    sha_after = hashlib.sha256(main_path.read_bytes()).hexdigest()
    report("alvo intacto ao fim (SHA256 igual)", sha_after == sha_before, 0.0, sha_after[:12])
    bad = [s for s in SUMMARY if not s[1]]
    say("\nRESUMO: %d itens, %d PASS, %d FAIL%s" % (len(SUMMARY), len(SUMMARY) - len(bad), len(bad),
                                                 " (--rapido: IA 25x600 e persistencia_v2 NAO rodaram)" if args.rapido else ""))
    for n, ok, dt, note in bad:
        say("  FAIL", n, "->", note[:300])
    say("(offline: lupa Lua 5.4 e 5.5; nao prova fisica Unreal, rota real, entrada, equilibrio nem desempenho)")
    return 1 if bad else 0


if __name__ == "__main__":
    sys.exit(main())
