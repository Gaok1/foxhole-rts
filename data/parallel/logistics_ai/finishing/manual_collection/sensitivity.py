"""COLETA_MANUAL: tabela de sensibilidade do tempo ate o primeiro caminhao de recurso (X) contra distancia campo-refinaria,
numero de trabalhadores e capacidade de carga. Mesmo harness dos testes (pawns andam num mundo plano falso; nao e fisica Unreal).
Os numeros de design (rate/cap/workers/bmat0) sao PROPOSTAS; esta tabela mostra o quanto o X depende de cada um.

  cd /d/GitHub/foxhole-rts && PYTHONPATH=D:/tools/pylibs PYTHONDONTWRITEBYTECODE=1 \
      python data/parallel/logistics_ai/finishing/manual_collection/sensitivity.py
"""
import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parent))
import harness_coleta as H  # noqa: E402

RUN = r'''
A.CFG.COLETA.workers = %(workers)d
A.CFG.COLETA.cap = %(cap)d
A.CFG.COLETA.rate = %(rate)s
newMatch({fx = %(fx)d, fy = 3000})
local L, K, res = A.logi, A.logi.col, resTruck()
local t = runUntil(%(limit)d, function() return res.state ~= "dead" end)
return t and string.format("%%.0f", t) or "nunca"
'''


def run(workers=3, cap=40, rate=0.5, fx=-12000, limit=3000):
    lua = H.new_game(version="lua54")
    return str(lua.execute(RUN % dict(workers=workers, cap=cap, rate=rate, fx=fx, limit=limit)))


def main():
    lines = ["Tempo ate o primeiro caminhao de recurso (s), partida manual (bmat0=40, caminhao 100 bmat, razao 2 sucata : 1 bmat)",
             "distancia campo-refinaria em metros = (|fx| - 4000) / 100 (cm); rate 0,5 sucata/s por trabalhador parado no campo", ""]
    dists = (-12000, -30000, -51000)
    lines.append("a) trabalhadores x distancia (cap 40, rate 0,5)")
    lines.append("   trab | " + " | ".join("%4d m" % ((abs(f) - 4000) // 100) for f in dists))
    for w in (1, 2, 3, 5):
        lines.append("   %4d | " % w + " | ".join("%6s" % run(workers=w, fx=f) for f in dists))
    lines.append("")
    lines.append("b) capacidade de carga x distancia (3 trabalhadores, rate 0,5)")
    lines.append("   cap  | " + " | ".join("%4d m" % ((abs(f) - 4000) // 100) for f in dists))
    for c in (20, 40, 80):
        lines.append("   %4d | " % c + " | ".join("%6s" % run(cap=c, fx=f) for f in dists))
    lines.append("")
    lines.append("c) taxa de coleta x distancia (3 trabalhadores, cap 40)")
    lines.append("   rate | " + " | ".join("%4d m" % ((abs(f) - 4000) // 100) for f in dists))
    for r in ("0.25", "0.5", "1.0"):
        lines.append("   %4s | " % r + " | ".join("%6s" % run(rate=r, fx=f) for f in dists))
    text = "\n".join(lines)
    print(text)
    Path(__file__).resolve().parent.joinpath("SENSITIVITY.txt").write_text(text + "\n", encoding="utf-8", newline="\n")


if __name__ == "__main__":
    main()
