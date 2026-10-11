"""BASES_AVANCADAS: roda as suites da COLETA MANUAL (acabamento/coleta_manual/test_*.py, SOMENTE LEITURA) contra o candidato_v4.
Tecnica: o harness da coleta (harness_coleta.py) e importado e o seu TEXT_V3 (o candidato que ele testa) e trocado, em memoria, pelo
texto do candidato_v4; os arquivos de teste da coleta rodam sem edicao do arquivo (texto trocado em memoria). Nada e escrito fora desta pasta.

As expectativas que as decisoes novas obrigam a mudar ficam em ADAPTACOES (trecho trocado em memoria, com o motivo); o resto passa inalterado.

  cd /d/GitHub/foxhole-rts && PYTHONPATH=D:/tools/pylibs PYTHONDONTWRITEBYTECODE=1 \
      python dados/paralel/bases_avancadas/etapa2/test_coleta_sobre_v4.py
"""
import contextlib
import io
import sys
from pathlib import Path

HERE = Path(__file__).resolve().parent
ROOT = HERE.parents[3]
COLETA = ROOT / "dados/paralel/ia_logistica/acabamento/coleta_manual"
sys.path.insert(0, str(HERE))
sys.path.insert(0, str(COLETA))
import harness_bases as HB  # noqa: E402
import harness_coleta as HC  # noqa: E402

assert HC.TEXT_V3 == HB.TEXT_V3, "o v3 que a coleta testa e o v3 do build"
HC.TEXT_V3 = HB.TEXT_V4          # as suites da coleta passam a exercitar o v4
SUITES = ["test_partida_manual", "test_coleta_nucleo", "test_travamento", "test_persistencia_coleta", "test_spawn_interface"]

# Expectativas alteradas (suite -> [(trecho original, substituto, motivo)]). O arquivo da coleta NAO e editado: o texto e trocado em memoria.
ADAPTACOES = {
    "test_partida_manual": [
        ('assert(workers() == 0 and #K.units == 0 and K.gathered == 0, "esquadrao cheio: sem vaga para trabalhador")',
         'assert(workers() == A.CFG.COLETA.workers and #A.squad() == A.CFG.SQUAD_MAX + A.CFG.COLETA.workers, '
         '"ADAPTACAO bases avancadas: trabalhadores nao contam no SQUAD_MAX; o esquadrao de combate cheio nao os bloqueia (" .. workers() .. ")")',
         "decisao do orquestrador: trabalhadores fora do CFG.SQUAD_MAX (antes: esquadrao cheio = nenhum trabalhador)"),
    ],
    "test_spawn_interface": [
        ('b = src.index("function logi.tick()")',
         'b = src.index("-- ---- Persistencia: extensao `fwd` v1")   # ADAPTACAO: no v4 spawnSite/spawnCommit/recruit ficam depois de logi.tick',
         "spawnSite/spawnCommit foram para o bloco BASES AVANCADAS (precisam de squadCenter/structures, declarados depois)"),
    ],
}


def source(name):
    path = COLETA / (name + ".py")
    s = path.read_text(encoding="utf-8")
    for old, new, why in ADAPTACOES.get(name, []):
        assert s.count(old) == 1, "%s: ancora nao unica: %r" % (name, old[:60])
        s = s.replace(old, new)
        print("adaptacao [%s]: %s" % (name, why), file=sys.__stdout__)
    return path, s


def run(name):
    HC.RESULTS.clear()
    buf = io.StringIO()
    rc = 0
    try:
        with contextlib.redirect_stdout(buf):
            path, s = source(name)
            exec(compile(s, str(path), "exec"), {"__name__": "__main__", "__file__": str(path)})
    except SystemExit as e:
        rc = e.code or 0
    out = buf.getvalue()
    lines = [l for l in out.splitlines() if l.startswith(("PASS", "FAIL"))]
    return rc, lines, out


def main():
    bad = 0
    for name in SUITES:
        rc, lines, out = run(name)
        npass = sum(1 for l in lines if l.startswith("PASS") and "test_" not in l[:12])
        fails = [l for l in lines if l.startswith("FAIL")]
        unexpected = fails
        status = "PASS" if rc == 0 and not unexpected else "FAIL"
        print("%s  %s sobre o candidato_v4 (%d linhas PASS, %d FAIL)" % (status, name, npass, len(fails)))
        for l in fails:
            print("      " + l[:300])
        if status == "FAIL":
            bad += 1
            print(out[-1500:])
    print("\ncoleta sobre v4: %d suites, %d com falha" % (len(SUITES), bad))
    sys.exit(1 if bad else 0)


if __name__ == "__main__":
    main()
