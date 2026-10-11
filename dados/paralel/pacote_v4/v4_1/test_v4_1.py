"""v4.1: trabalhadores (role "worker") nao entram na escala das ondas inimigas nem seguram a derrota.

Teste NOVO e de CONTRASTE: roda os mesmos casos contra o candidato_v4 (espera-se FALHA nos casos marcados [muda]) e contra o v4.1 (tudo PASS).
Nao edita nada; so le. Usa o harness de bases (etapa2/harness_bases.py) com um TAIL que expoe spawnEnemies/waveSpawnPoint como hooks
(gotcha 54: codigo no fim do mesmo chunk reatribui `local function`).

  cd /d/GitHub/foxhole-rts && PYTHONPATH=D:/tools/pylibs PYTHONDONTWRITEBYTECODE=1 python dados/paralel/pacote_v4/v4_1/test_v4_1.py [--so-v41 ARQ]
Saida: uma linha por caso e variante. rc 0 = v4 falha nos [muda] E v4.1 passa em tudo.
"""
import argparse
import os
import sys
from pathlib import Path

sys.dont_write_bytecode = True
HERE = Path(__file__).resolve().parent
ROOT = HERE.parents[3]
sys.path.insert(0, str(ROOT / "dados/paralel/bases_avancadas/etapa2"))
import harness_bases as H  # noqa: E402

V4 = ROOT / "dados/paralel/bases_avancadas/etapa2/candidato_v4/main.lua"
V41 = HERE / "candidato/main.lua"

TAIL = H.TAIL.replace("hooks={", "squadCenter=function() return squadCenter() end, hooks={spawnEnemies=function(fn) spawnEnemies=fn end, waveSpawnPoint=function(fn) waveSpawnPoint=fn end, ")


def game(text, version):
    lua = H.lua_runtime(version)
    lua.execute(H.SCAFFOLD)
    api = lua.execute(text + TAIL)
    lua.globals().api = api
    lua.execute(H.WORLD)
    lua.execute(r'''
WAVES = {}
A.hooks.waveSpawnPoint(function() return {X = 20000, Y = 0, Z = 0} end)
A.hooks.spawnEnemies(function(at, n, same, quiet) WAVES[#WAVES + 1] = n end)
-- primeira onda: nextWaveAt vencido; chama waveTick e devolve o n que o spawn recebeu (soma dos grupos)
function firstWave()
    A.combat.auto, A.combat.wave, A.combat.nextWaveAt = true, 0, -1
    WAVES = {}
    math.randomseed(7)
    A.waveTick()
    local s = 0
    for _, n in ipairs(WAVES) do s = s + n end
    return s
end
''')
    return lua


WAVE = r'''
newMatch({workers = true, noSquad = true})
A.CFG.COLETA.workers = 0
for i = 1, NC do newSoldier("rifle", 300 + 100 * i, 0) end
for i = 1, NW do newSoldier("worker", -3000, 100 * i) end
assert(combatants() == NC and workers() == NW)
return firstWave()
'''


def wave(text, v, nc, nw):
    lua = game(text, v)
    lua.globals().NC, lua.globals().NW = nc, nw
    return lua.execute(WAVE)


def c_onda_igual(text, v):   # [muda]
    base = wave(text, v, 6, 0)
    com = wave(text, v, 6, 3)
    ctl = wave(text, v, 9, 0)
    assert ctl > base, "controle inutil: 9 de combate nao gera onda maior que 6 (waveCut/limite): %s vs %s" % (ctl, base)
    assert com == base, "6 soldados + 3 trabalhadores deu onda %s, esperado igual a 6 sem trabalhadores (%s); 9 de combate daria %s" % (com, base, ctl)
    return "6c+3t = 6c = %s (9c daria %s)" % (base, ctl)


def c_sem_trabalhadores_igual(text, v):   # nao muda: sem trabalhadores v4 == v4.1
    a = wave(text, v, 6, 0)
    assert a >= 1
    return "6c sem trabalhadores = %s" % a


def c_so_trabalhadores(text, v):   # [muda] 0 combate + 3 trabalhadores: a onda e a minima, como sem esquadrao
    a = wave(text, v, 1, 0)
    b = wave(text, v, 1, 3)
    assert a == b, "1c + 3t deu %s, esperado %s" % (b, a)
    return "1c+3t = 1c = %s" % a


def c_derrota_assalto(text, v):   # [muda]
    lua = game(text, v)
    lua.execute(r'''
newMatch({workers = true, noSquad = true})
A.CFG.COLETA.workers = 0
newSoldier("worker", -3000, 0); newSoldier("worker", -3000, 100); newSoldier("worker", -3000, 200)
A.combat.mode, A.combat.auto = "assault", true
A.economy.manpower = 0
A.waveTick()
assert(A.combat.auto == false, "Assalto: so trabalhadores vivos e sem mao de obra para um fuzileiro = derrota")
''')
    return "Assalto sem combate e sem mao de obra: derrota mesmo com 3 trabalhadores vivos"


def c_assalto_com_combate(text, v):   # nao muda
    lua = game(text, v)
    lua.execute(r'''
newMatch({workers = true, noSquad = true})
A.CFG.COLETA.workers = 0
newSoldier("rifle", 300, 0); newSoldier("worker", -3000, 0)
A.combat.mode, A.combat.auto = "assault", true
A.economy.manpower = 0
A.waveTick()
assert(A.combat.auto == true, "Assalto com 1 soldado de combate nao perde")
''')
    return "Assalto com 1 de combate e sem mao de obra: segue"


def c_aviso(text, v):   # [muda]
    lua = game(text, v)
    lua.execute(r'''
newMatch({workers = true, noSquad = true})
A.CFG.COLETA.workers = 0
for i = 1, 6 do newSoldier("rifle", 300 + 100 * i, 0) end
for i = 1, 3 do newSoldier("worker", -3000, 100 * i) end
LOG = {}
A.combat.auto, A.combat.wave, A.combat.nextWaveAt = true, 0, nil
A.waveTick()
local l = lastlog("proxima onda em")
assert(l, "sem aviso")
assert(l:find("esquadrao 6,", 1, true), "aviso conta trabalhadores: " .. tostring(l))
''')
    return "aviso 'esquadrao 6' (nao 9)"


def c_centro(text, v):   # [muda]
    lua = game(text, v)
    lua.execute(r'''
newMatch({workers = true, noSquad = true})
A.CFG.COLETA.workers = 0
assert(A.squadCenter() == nil, "ninguem vivo: nil")
local ws = {}
for i = 1, 3 do ws[i] = newSoldier("worker", -3000, 100 * i) end
local c = A.squadCenter()
assert(c and math.abs(c.X + 3000) < 0.01 and math.abs(c.Y - 200) < 0.01, "so trabalhadores vivos: centro deles")
local rs = {}
for i = 1, 6 do rs[i] = newSoldier("rifle", 300 + 100 * i, 0) end
c = A.squadCenter()
assert(math.abs(c.X - 650) < 0.01 and math.abs(c.Y) < 0.01, "6 combatentes + 3 trabalhadores longe: centro so dos combatentes, deu X=" .. tostring(c.X) .. " Y=" .. tostring(c.Y))
for i = 1, 6 do rs[i].pawn.Health = 0 end
c = A.squadCenter()
assert(math.abs(c.X + 3000) < 0.01, "combatentes mortos: volta ao centro dos vivos (trabalhadores)")
''')
    return "centro = so combatentes (650,0); so trabalhadores: o deles; ninguem: nil"


CASES = [("onda igual com 3 trabalhadores", c_onda_igual, True),
         ("1 de combate + 3 trabalhadores", c_so_trabalhadores, True),
         ("sem trabalhadores: igual", c_sem_trabalhadores_igual, False),
         ("aviso da proxima onda", c_aviso, True),
         ("squadCenter so de combatentes", c_centro, True),
         ("Assalto: derrota sem tropa de combate", c_derrota_assalto, True),
         ("Assalto: com combate segue", c_assalto_com_combate, False)]


def run(label, path, expect_fail_marked):
    text = H.read_lf(path)
    bad = []
    for name, fn, muda in CASES:
        for v in ("lua54", "lua55"):
            try:
                note = fn(text, v)
                res, msg = True, note
            except BaseException as e:  # noqa: BLE001
                res, msg = False, "%s: %s" % (type(e).__name__, str(e)[:260])
            esperado = (not res) if (expect_fail_marked and muda) else res
            tag = "ok " if esperado else "ERRO"
            print("%s  [%s] %-40s %-5s %s%s" % (tag, label, name, v, "PASS" if res else "FAIL", ("  -> " + msg) if msg else ""))
            if not esperado:
                bad.append((name, v))
    return bad


def main():
    ap = argparse.ArgumentParser()
    ap.add_argument("--so-v41", default=None, help="roda so este arquivo como v4.1 (todos PASS)")
    ns = ap.parse_args()
    bad = []
    if ns.so_v41:
        bad += run("v4.1", Path(ns.so_v41), False)
    else:
        bad += run("v4  ", V4, True)   # os casos [muda] TEM de falhar aqui (contraste)
        bad += run("v4.1", V41, False)
    print("\nRESUMO: %s" % ("OK (v4 falha nos [muda], v4.1 passa em tudo)" if not bad else "PROBLEMAS: %s" % bad))
    sys.exit(1 if bad else 0)


if __name__ == "__main__":
    main()
