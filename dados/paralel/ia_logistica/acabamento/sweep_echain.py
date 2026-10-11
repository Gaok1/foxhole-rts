"""Varredura offline dos parametros de CFG.ECHAIN (calibracao do item 1). Reproduzivel:

  cd /d/GitHub/foxhole-rts && PYTHONPATH=D:/tools/pylibs PYTHONDONTWRITEBYTECODE=1 \
      python dados/paralel/ia_logistica/acabamento/sweep_echain.py [--grid] > saida.txt

Sem argumentos: tabela antes/depois (original x calibrado) por cenario e semente. --grid: varre a grade e lista
quais conjuntos passam nos criterios (ver CRITERIOS). O modelo de luta e o do test_ia_logistica.py (cada onda dura
`fight` s e some): serve para comparar PARAMETROS, nao para medir equilibrio de combate.
"""
import itertools
import json
import statistics
import sys
from pathlib import Path

HERE = Path(__file__).resolve().parent
sys.path.insert(0, str(HERE))
from simlib import Sim, load_module, IA_DIR  # noqa: E402

FIGHTS = (45, 90)             # s de luta por onda no modelo (cadencia de 60 e 105 s por onda)
SEEDS = tuple(range(1, 21))   # sementes do corte parcial
PS = (0.25, 0.5, 0.75)        # fracao de comboios destruidos no corte parcial

V1 = {"free": 3, "trip": 25.0, "minLoad": 3, "front0": {"ammo": 2, "shirts": 10}, "want": {"ammo": 6, "shirts": 30}}  # = ia_logistica.lua original
V2 = {}  # = padroes de ia_logistica_v2.lua (free 5, trip 20, want 4/20, front0 2/10, minLoad 3)


def tot(waves, key):
    return sum(w[key] for w in waves)


def first_short(waves):
    for w in waves:
        if w["short"] > 0:
            return w["wave"]
    return None


def wave_t(waves, n):
    for w in waves:
        if w["wave"] == n:
            return w["t"]
    return waves[-1]["t"]


def metrics(sim, params, fight):
    """Todas as execucoes de um conjunto de parametros para uma cadencia de ondas (fight s de luta por onda)."""
    res = {}
    common = dict(secs=3000, fight=fight)
    res["ctl"] = sim.run(params, **common)
    res["T"] = sim.run(params, cut="all", **common)
    # M: corte total a partir da onda 5 (estoque da frente ja no nivel do alvo)
    res["M"] = sim.run(params, cut="window", cutFrom=wave_t(res["ctl"]["waves"], 5) - 1, **common)
    # R: corte total ate a onda da primeira falta e libera; mede a volta ao normal depois disso
    fs = first_short(res["T"]["waves"]) or 8
    res["R"] = sim.run(params, cut="window", cutFrom=0, cutTo=wave_t(res["T"]["waves"], fs) + 1, **common)
    res["R_fs"] = fs
    res["R_end"] = wave_t(res["T"]["waves"], fs) + 1
    res["scarce"] = sim.run(params, scarce=True, **common)
    res["ctl30"] = sim.run(params, secs=3000, fight=30)
    res["P"] = {p: [sim.run(params, cut="frac", p=p, seed=s, **common) for s in SEEDS] for p in PS}
    return res


def summarize(res):
    """Numeros que entram nos criterios."""
    ctl, T, M, R = res["ctl"], res["T"], res["M"], res["R"]
    out = {}
    out["ctl_ok"] = all(all(w["short"] == 0 for w in r["waves"]) and r["ok"] and len(r["waves"]) >= 10 for r in (ctl, res["ctl30"]))
    fsT = first_short(T["waves"])
    out["T_first"] = fsT or 99
    tail = [w for w in T["waves"] if w["wave"] >= 5]
    out["T_mean"] = statistics.mean(w["sent"] / w["asked"] for w in tail)
    out["T_floor"] = min(w["sent"] / w["asked"] for w in T["waves"] if w["wave"] >= fsT) if fsT else 1.0
    out["T_short"] = tot(T["waves"], "short")
    out["T_attr"] = (tot(T["waves"], "byCut") / out["T_short"]) if out["T_short"] else 1.0
    out["M_first"] = first_short(M["waves"]) or 99
    out["M_last"] = statistics.mean(w["sent"] / w["asked"] for w in M["waves"][-2:])
    last_cut_wave = res["R_fs"]
    after = [w for w in R["waves"] if w["wave"] > last_cut_wave]
    rec = next((w["wave"] for w in after if w["short"] == 0), None)
    out["R_waves"] = (rec - last_cut_wave) if rec else 99
    out["R_secs"] = (wave_t(R["waves"], rec) - res["R_end"]) if rec else 9999
    out["R_stays"] = bool(rec) and all(w["short"] == 0 for w in R["waves"] if w["wave"] >= rec)
    out["R_n"] = len(after)
    out["scarce_floor"] = min(w["sent"] / w["asked"] for w in res["scarce"]["waves"])
    out["scarce_ok"] = res["scarce"]["ok"] and len(res["scarce"]["waves"]) >= 10
    sp = {p: statistics.mean(tot(r["waves"], "short") for r in runs) for p, runs in res["P"].items()}
    out["P_short"] = sp
    out["P_frac"] = {p: (sp[p] / out["T_short"] if out["T_short"] else 0) for p in sp}
    ps = sum(tot(r["waves"], "short") for runs in res["P"].values() for r in runs)
    pb = sum(tot(r["waves"], "byCut") for runs in res["P"].values() for r in runs)
    out["P_attr"] = pb / ps if ps else 1.0
    out["all_ok"] = all(r["ok"] for r in (ctl, T, M, R)) and all(r["ok"] for runs in res["P"].values() for r in runs)
    return out


def criteria(s):
    """CRITERIOS (cada um e uma frase no RELATORIO). Retorna lista de falhas."""
    f = []
    if not s["ctl_ok"]:
        f.append("sem corte: alguma onda saiu menor que a atual")
    if not s["all_ok"] or not s["scarce_ok"]:
        f.append("razao/auditoria falhou")
    if s["T_first"] < 5:
        f.append("corte total desde o inicio: falta ja na onda %s (<5)" % s["T_first"])
    if not (0.40 <= s["T_mean"] <= 0.65):
        f.append("corte total: media das ondas 5-10 = %.2f fora de [0.40, 0.65]" % s["T_mean"])
    if s["T_floor"] < 0.33:
        f.append("corte total: piso %.2f < 0.33 do pedido" % s["T_floor"])
    if s["T_attr"] < 0.75 or s["P_attr"] < 0.75:
        f.append("rastreabilidade byCut %.2f/%.2f < 0.75 do que faltou" % (s["T_attr"], s["P_attr"]))
    if s["M_first"] > 9:
        f.append("corte a partir da onda 5 nao morde antes da onda 10")
    pf = s["P_frac"]
    if not (pf[0.25] < pf[0.5] < pf[0.75] < 1.0):
        f.append("parcial nao monotono %s" % {k: round(v, 2) for k, v in pf.items()})
    if pf[0.25] > 0.5 or pf[0.75] < 0.4:
        f.append("parcial fora das faixas (p=.25 <= .5 e p=.75 >= .4 do corte total): %s" % {k: round(v, 2) for k, v in pf.items()})
    if s["R_waves"] > 3 or s["R_secs"] > 300:
        f.append("recuperacao: %s ondas / %s s depois do fim do corte (max 3 ondas e 300 s)" % (s["R_waves"], s["R_secs"]))
    return f


def make_sim():
    """Sempre o modulo v2 (ele aceita os parametros de V1 por override; o v1 e reproduzido por V1)."""
    bp = load_module("bp_v2", HERE / "build_patch_v2.py")
    return Sim(lambda s: bp.stacked(s))


def fmt_waves(r):
    return " ".join("%d:%d/%d%s" % (w["wave"], w["sent"], w["asked"], "[i%d]" % w["byCut"] if w["byCut"] else "") for w in r["waves"])


def tabela(sim):
    """Tabela antes/depois por cenario, cadencia e semente (saida em TABELA_CALIBRACAO.txt)."""
    out = []
    for fight in FIGHTS:
        per = 60 if fight == 45 else 105
        out.append("=== cadencia: luta de %d s por onda (~%d s por onda) ===" % (fight, per))
        for label, P in (("v1 (original: free 3, trip 25, want 6/30)", V1), ("v2 (calibrado: free 5, trip 20, want 4/20)", V2)):
            res = metrics(sim, P, fight)
            s = summarize(res)
            out.append("-- " + label)
            for name, key in (("controle (sem corte)", "ctl"), ("corte total desde 0 s", "T"), ("corte total desde a onda 5", "M"),
                              ("corte ate a 1a falta, depois livre", "R"), ("escassez (retaguarda sem bmat/sucata)", "scarce")):
                out.append("   %-40s %s" % (name, fmt_waves(res[key])))
            for p in PS:
                runs = res["P"][p]
                sh = statistics.mean(tot(r["waves"], "short") for r in runs)
                share = statistics.mean(r["lostAmmo"] + r["lostShirts"] for r in runs) / statistics.mean(r["carried"] for r in runs)
                out.append("   parcial p=%.2f (20 sementes): faltaram %.1f soldados no total (%.0f%% do corte total); carga perdida no razao = %.0f%% da despachada"
                           % (p, sh, 100 * s["P_frac"][p], 100 * share))
            for seed in (1, 2, 3):
                out.append("   semente %d, p=0.50: %s" % (seed, fmt_waves(res["P"][0.5][seed - 1])))
            fails = criteria(s)
            out.append("   CRITERIOS: %s" % ("todos atendidos" if not fails else "; ".join(fails)))
    return chr(10).join(out)


def grade(sim):
    keys = []
    for free, want, front0, trip in itertools.product((3, 4, 5, 6), ((3, 15), (4, 20), (5, 25), (6, 30)), ((2, 10), (3, 15), (4, 20)), (20.0, 25.0, 30.0)):
        keys.append({"free": free, "trip": trip, "front0": {"ammo": front0[0], "shirts": front0[1]}, "want": {"ammo": want[0], "shirts": want[1]}})
    ok = 0
    for p in keys:
        res = {f: summarize(metrics(sim, p, f)) for f in FIGHTS}
        fails = [x for f in FIGHTS for x in criteria(res[f])]
        print("PASSA" if not fails else "falha(%d)" % len(fails), json.dumps(p),
              {f: (res[f]["T_first"], round(res[f]["T_mean"], 2), res[f]["M_first"], res[f]["R_waves"], res[f]["R_secs"]) for f in FIGHTS},
              ("" if not fails else "| " + fails[0]), flush=True)
        ok += not fails
    print("conjuntos que passam: %d de %d" % (ok, len(keys)))


def sensibilidade(sim):
    """Uma mudanca por vez em torno do v2 (cada linha: que criterios deixam de ser atendidos)."""
    rows = [("v2 (calibrado)", {})]
    for t in (15.0, 25.0, 30.0, 40.0):
        rows.append(("trip=%g" % t, {"trip": t}))
    for m in (1, 5, 8):
        rows.append(("minLoad=%d" % m, {"minLoad": m}))
    for f in (3, 4, 6):
        rows.append(("free=%d" % f, {"free": f}))
    for w in ((3, 15), (5, 25), (6, 30)):
        rows.append(("want=%d/%d" % w, {"want": {"ammo": w[0], "shirts": w[1]}}))
    for f0 in ((3, 15), (4, 20)):
        rows.append(("front0=%d/%d" % f0, {"front0": {"ammo": f0[0], "shirts": f0[1]}}))
    for b in (120, 480):
        rows.append(("bmat0=%d" % b, {"bmat0": b}))
    out = ["parametro        cadencia  1a falta(T)  media 5-10(T)  1a falta(M)  recuperacao       criterios nao atendidos"]
    for name, P in rows:
        for fight in FIGHTS:
            s = summarize(metrics(sim, P, fight))
            fails = criteria(s)
            out.append("%-16s %-9s %-12s %-14.2f %-12s %-17s %s" % (
                name, "%ds" % (fight + 15), s["T_first"], s["T_mean"], s["M_first"], "%s ondas/%s s" % (s["R_waves"], s["R_secs"]),
                "nenhum" if not fails else " | ".join(f.split(":")[0] for f in fails)))
    return chr(10).join(out)


def cadencias(sim):
    """Controle (SEM corte) em cadencias de onda mais rapidas que a da tabela: onde a producao, e nao a interdicao, limita."""
    out = ["onda a cada ~N s (luta + 15 s de espera) | v1 (original) | v2 (calibrado); formato onda:enviados/pedidos, so ondas curtas marcadas com *"]
    for fight in (5, 15, 25, 30, 35, 45, 90):
        row = []
        for P in (V1, V2):
            r = sim.run(P, secs=3000, fight=fight)
            short = sum(w["short"] for w in r["waves"])
            row.append("faltaram %2d em %s" % (short, " ".join("%d:%d/%d%s" % (w["wave"], w["sent"], w["asked"], "*" if w["short"] else "") for w in r["waves"] if w["short"]) or "-"))
        out.append("~%3d s | %-52s | %s" % (fight + 15, row[0], row[1]))
    return chr(10).join(out)


if __name__ == "__main__":
    sim = make_sim()
    if "--grid" in sys.argv:
        grade(sim)
    elif "--sens" in sys.argv:
        print(sensibilidade(sim))
    elif "--cad" in sys.argv:
        print(cadencias(sim))
    else:
        print(tabela(sim))
