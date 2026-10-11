"""Suite existente tools/test_orders.py contra os candidatos em memoria (main.lua intacto).

$env:PYTHONPATH='D:/tools/pylibs'; python dados/paralel/ia_logistica/test_orders_candidato.py
Roda tres combinacoes: main+IA, main+ECONOMIA+IA (ordem declarada) e, de controle, a suite sem mudanca
no main puro. O unico bloco trocado da suite e o do comboio inimigo (contrato abstrato antigo removido):
test_orders_bloco_comboio.lua. Tambem roda test_integracao.py da ECONOMIA sobre main+ECONOMIA+IA.
"""
import sys
from pathlib import Path

HERE = Path(__file__).resolve().parent
ROOT = HERE.parents[2]
sys.path.insert(0, str(HERE))
from build_patch import build, stacked, economia_build  # noqa: E402

ORDERS = ROOT / "tools/test_orders.py"
SRC_LINE = 'source = (Path(__file__).resolve().parents[1] / "mod/FoxholeRTS/Scripts/main.lua").read_text(encoding="utf-8")'
OLD_START = "-- enemy convoy: missing cargo shrinks the wave; arriving adds cargo; our soldiers nearby destroy it\n"
OLD_END = 'assert(cv2.state == "dead" and api.combat.convoysCut == cut0 + 1)\n'


def suite(transform, swap_block):
    s = ORDERS.read_text(encoding="utf-8")
    assert s.count(SRC_LINE) == 1
    s = s.replace(SRC_LINE, "source = __transform(" + SRC_LINE.split(" = ", 1)[1] + ")")
    if swap_block:
        assert s.count(OLD_START) == 1 and s.count(OLD_END) == 1, "bloco do comboio mudou na suite"
        a = s.index(OLD_START)
        b = s.index(OLD_END, a) + len(OLD_END)
        s = s[:a] + HERE.joinpath("test_orders_bloco_comboio.lua").read_text(encoding="utf-8") + s[b:]
    g = {"__file__": str(ORDERS), "__name__": "__main__", "__transform": transform}
    exec(compile(s, str(ORDERS), "exec"), g)


def economia_integracao(transform):
    t = ROOT.joinpath("dados/paralel/economia/test_integracao.py").read_text(encoding="utf-8")
    t = t.replace("from build_patch import build, ROOT, HERE\n", "")
    assert t.count("proposal=build(source)") == 1
    t = t.replace("proposal=build(source)", "proposal=__transform(source)")
    exec(compile(t, "economia/test_integracao.py", "exec"), {"__transform": transform, "ROOT": ROOT, "__name__": "__main__"})


results = []
for name, fn, swap in (("main puro (controle)", lambda s: s, False),
                       ("main+IA", lambda s: build(s)[0], True),
                       ("main+ECONOMIA+IA", stacked, True)):
    print("==", name)
    suite(fn, swap)
    results.append(name)
print("== ECONOMIA test_integracao sobre main+ECONOMIA+IA")
economia_integracao(stacked)
results.append("economia/test_integracao")
print("PASS: %d execucoes: %s" % (len(results), ", ".join(results)))
