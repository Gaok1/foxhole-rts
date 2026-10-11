"""BASES_AVANCADAS (decisao do orquestrador): trabalhadores (role "worker") NAO contam no CFG.SQUAD_MAX (12). O limite deles e o da
coleta (CFG.COLETA.workers). Vale para recruit, spawnSquad (F6/newGame) e colMaintain. No candidate_v3 o esquadrao cheio bloqueava os
trabalhadores: o caso de comparacao mostra a expectativa alterada.

  cd /d/GitHub/foxhole-rts && PYTHONPATH=D:/tools/pylibs PYTHONDONTWRITEBYTECODE=1 \
      python data/parallel/forward_bases/stage2/test_workers.py
"""
import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parent))
import harness_bases as H  # noqa: E402

FULL = r'''
newMatch({workers = true})
local L, C = A.logi, A.CFG
while combatants() < C.SQUAD_MAX do newSoldier("rifle", 0, 0) end
assert(combatants() == 12 and workers() == 0)
L.base.shirts, L.base.rifle = 30, 10
A.economy.manpower = 0
'''


def t_fora_do_teto(v):
    lua = H.new_game(version=v)
    lua.execute(FULL + r'''
runUntil(40, function() return workers() == C.COLETA.workers end)
assert(workers() == 3, "trabalhadores nascem com o esquadrao de combate cheio: " .. workers())
assert(combatants() == 12 and #A.squad() == 15)
assert(not saw("esquadrão cheio"), "sem aviso de esquadrao cheio para trabalhadores")
-- repoe os mortos, sempre no limite da coleta (nao do SQUAD_MAX)
for _, m in ipairs(A.squad()) do if m.role == "worker" then m.pawn.Health = 0 end end
A.reap(A.squad(), "squad")
runUntil(60, function() return workers() == 3 end)
assert(workers() == 3 and #A.squad() <= 15)
runUntil(30)
assert(workers() == 3, "nunca passa do limite da coleta")
''')
    return "esquadrao de combate cheio (12) + 3 trabalhadores = 15; repoe os mortos; nunca passa de CFG.COLETA.workers"


def t_limite_da_coleta(v):
    lua = H.new_game(version=v)
    lua.execute(r'''
newMatch({workers = true})
A.CFG.COLETA.workers = 2
A.logi.base.shirts = 30
runUntil(60)
assert(workers() == 2, "limite = CFG.COLETA.workers (2): " .. workers())
''')
    return "limite dos trabalhadores e o da coleta (workers=2 -> 2)"


def t_recrutar_com_trabalhadores(v):
    lua = H.new_game(version=v)
    lua.execute(r'''
newMatch({workers = true})
local L, C = A.logi, A.CFG
L.base.shirts, L.base.rifle = 40, 40
A.economy.manpower = 0
runUntil(40, function() return workers() == 3 end)
assert(workers() == 3)
-- trabalhadores nao ocupam as vagas de combate: 6 iniciais + 6 recrutados = 12; o 13o recusa
local ok = 0
for i = 1, 8 do if A.recruit("rifle") then ok = ok + 1 end end
assert(ok == 6 and combatants() == 12 and #A.squad() == 15, "recrutados " .. ok .. ", combate " .. combatants())
assert(A.recruit("rifle") == false and saw("esquadrao no maximo (12)"))
-- F6 / newGame (spawnSquad): o teto tambem so olha o combate
for _, m in ipairs(A.squad()) do if m.role ~= "worker" then m.pawn.Health = 0 end end
A.reap(A.squad(), "squad")
assert(combatants() == 0 and workers() == 3)
local made = A.spawnSquad(20)
assert(made == C.SQUAD_MAX and combatants() == 12 and workers() == 3, "spawnSquad enche ate 12 de combate: " .. made)
assert(A.spawnSquad(1) == 0)
''')
    return "vagas de combate (12) independem dos trabalhadores: recruit e spawnSquad; 13o recusado"


def t_comparacao_v3(v):
    res = {}
    for name, text in (("v3", H.TEXT_V3), ("v4", H.TEXT_V4)):
        lua = H.new_game(text, version=v)
        res[name] = lua.execute(FULL + r'''
runUntil(40, function() return workers() == C.COLETA.workers end)
return workers()
''')
    assert res["v3"] == 0 and res["v4"] == 3, res
    return "expectativa alterada: com 12 de combate o v3 criava %d trabalhadores (bloqueados), o v4 cria %d" % (res["v3"], res["v4"])


for v in ("lua54", "lua55"):
    H.case("[%s] trabalhadores fora do SQUAD_MAX" % v, t_fora_do_teto, v)
    H.case("[%s] limite = CFG.COLETA.workers" % v, t_limite_da_coleta, v)
    H.case("[%s] recruit/spawnSquad so contam combate" % v, t_recrutar_com_trabalhadores, v)
    H.case("[%s] comparacao com o v3" % v, t_comparacao_v3, v)
H.finish("test_trabalhadores")
