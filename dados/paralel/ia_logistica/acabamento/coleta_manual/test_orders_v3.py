"""COLETA_MANUAL: tools/test_orders.py (suite do mod) executado contra o candidato v3 (copia em memoria; o arquivo
original nao e editado), com o bloco 'enemy convoy' trocado pelo da IA v2 (como o ensaio de integracao faz). Cada
expectativa que a coleta manual obriga a mudar fica em ADAPTACOES abaixo, com o motivo; qualquer outra falha e regressao.

  cd /d/GitHub/foxhole-rts && PYTHONPATH=D:/tools/pylibs PYTHONDONTWRITEBYTECODE=1 \
      python dados/paralel/ia_logistica/acabamento/coleta_manual/test_orders_v3.py
"""
import re
import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parent))
import harness_coleta as H  # noqa: E402

ROOT = H.ROOT
ACAB = ROOT / "dados/paralel/ia_logistica/acabamento"
ORDERS_SRC_LINE = 'source = (Path(__file__).resolve().parents[1] / "mod/FoxholeRTS/Scripts/main.lua").read_text(encoding="utf-8")'
CONVOY_START = "-- enemy convoy: missing cargo shrinks the wave; arriving adds cargo; our soldiers nearby destroy it\n"
CONVOY_END = 'assert(cv2.state == "dead" and api.combat.convoysCut == cut0 + 1)\n'

# (trecho original, substituto, motivo). Vazio = a suite passa sem nenhuma adaptacao.
ADAPTACOES = [
    ("""L.salvage, L.bmat = 100, 0
L.tick(); clock = clock + 0.5; L.tick()
""",
     """-- ADAPTACAO coleta manual: a partida nova comeca SEM caminhao de recurso (reserva de 100 bmat, fabrica parada). O resto deste
-- bloco testa o fluxo refinaria -> fabrica -> caminhao de suprimento com o de recurso vivo: torna-o vivo explicitamente.
assert(L.trucks[1].kind == 'res' and L.trucks[1].state == 'dead' and L.bmat == api.CFG.COLETA.bmat0 and L.rebuildReserve() == 100)
L.trucks[1].state, L.trucks[1].hp = 'idle', api.CFG.LOGI.hp
L.salvage, L.bmat = 100, 0
L.tick(); clock = clock + 0.5; L.tick()
""",
     "start() deixa o caminhao de recurso por construir; o teste do fluxo da fabrica o torna vivo"),
    ("assert(plan.cost==1100 and #plan.builds==2 and #plan.parking==3 and spawned==0)",
     "assert(plan.cost==1000 and #plan.builds==2 and #plan.parking==2 and spawned==0)  -- ADAPTACAO: sem caminhao de recurso na implantacao",
     "implantacao: 400+400+2x100 = 1000 e 2 vagas (antes 1100 e 3)"),
    ("api.S.deploy.bmat=1099\n", "api.S.deploy.bmat=999  -- ADAPTACAO: falta 1 para o novo custo 1000\n", "um a menos que o custo (1000)"),
    ("api.S.deploy.bmat=1100\n", "api.S.deploy.bmat=1000  -- ADAPTACAO: orcamento 1000\n", "carteira cheia agora vale 1000"),
    ("assert(not L.deploy() and api.S.deploy.bmat==1100 and api.S.deploy.spent==0)",
     "assert(not L.deploy() and api.S.deploy.bmat==1000 and api.S.deploy.spent==0)  -- ADAPTACAO: orcamento 1000", "rollback preserva a carteira de 1000"),
    ("assert(L.deploy() and spawned==5 and L.scan() and api.S.deploy.bmat==0 and api.S.deploy.spent==1100)",
     "assert(L.deploy() and spawned==4 and L.scan() and api.S.deploy.bmat==0 and api.S.deploy.spent==1000)  -- ADAPTACAO: 2 estruturas + 2 caminhoes",
     "implantacao gasta 1000 e cria 4 atores"),
    ('    assert(tr.X==tr.pawn.position.X and tr.Y==tr.pawn.position.Y, "preserve actual parking at startup")',
     '    if tr.pawn then assert(tr.X==tr.pawn.position.X and tr.Y==tr.pawn.position.Y, "preserve actual parking at startup")\n'
     '    else assert(tr.kind=="res" and tr.state=="dead" and not tr.X, "ADAPTACAO: o de recurso ainda nao existe") end',
     "so os 2 caminhoes de suprimento tem ator no inicio; o de recurso nasce quando a fabrica o constroi"),
    ('assert(L.deploy() and spawned==5 and api.S.deploy.spent==1100, "idempotent;',
     'assert(L.deploy() and spawned==4 and api.S.deploy.spent==1000, "idempotent;', "idempotencia com 4 atores / 1000"),
]



def swap_once(text, old, new, what):
    assert text.count(old) == 1, "%s: ancora nao unica (%d): %r" % (what, text.count(old), old[:70])
    return text.replace(old, new, 1)


def build_source():
    s = (ROOT / "tools/test_orders.py").read_text(encoding="utf-8")
    s = swap_once(s, ORDERS_SRC_LINE, "source = __CANDIDATE", "tools/test_orders.py")
    assert s.count(CONVOY_START) == 1 and s.count(CONVOY_END) == 1, "bloco do comboio mudou na suite"
    a = s.index(CONVOY_START)
    b = s.index(CONVOY_END, a) + len(CONVOY_END)
    s = s[:a] + (ACAB / "test_orders_bloco_comboio_v2.lua").read_text(encoding="utf-8") + s[b:]
    for old, new, why in ADAPTACOES:
        s = swap_once(s, old, new, why)
        print("adaptacao: " + why)
    return s


def main(candidate_text):
    s = build_source()
    try:
        exec(compile(s, "tools/test_orders.py[candidato v3]", "exec"),
             {"__file__": str(ROOT / "tools/test_orders.py"), "__name__": "__main__", "__CANDIDATE": candidate_text})
    except Exception as e:  # noqa: BLE001  (diagnostico: mostra o trecho Lua da falha)
        m = re.search(r"\]:(\d+):", str(e))
        if m:
            n = int(m.group(1))
            for blk in s.split("lua.execute('''")[1:]:
                ls = blk.split("\n")
                if len(ls) >= n:
                    print("--- trecho Lua perto da linha %d:" % n)
                    for i in range(max(0, n - 6), min(len(ls), n + 2)):
                        print("%4d %s%s" % (i + 1, "> " if i + 1 == n else "  ", ls[i][:200]))
                    break
        raise


if __name__ == "__main__":
    main(H.TEXT_V3)
