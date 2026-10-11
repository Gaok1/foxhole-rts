"""Auditoria executavel do main.lua ATUAL (sem patch): prova que a carga inimiga de hoje e abstrata.

$env:PYTHONPATH='D:/tools/pylibs'; python data/parallel/logistics_ai/test_base_audit.py
Cada assert descreve o comportamento atual; o patch da IA_LOGISTICA substitui estes contratos.
"""
import re
from pathlib import Path
from lupa import LuaRuntime

ROOT = Path(__file__).resolve().parents[3]
src = ROOT.joinpath("mod/FoxholeRTS/Scripts/main.lua").read_text(encoding="utf-8")
orders = ROOT.joinpath("tools/test_orders.py").read_text(encoding="utf-8")
a = orders.index("lua.execute('''") + len("lua.execute('''")
lua = LuaRuntime()
lua.execute(orders[a:orders.index("''')", a)])
lua.globals().print = lambda *x: None
api = lua.execute(src + "\nreturn {logi=logi, combat=combat, CFG=CFG, squad=squad}")
lua.globals().api = api
lua.execute(r'''
local L, combat, C = api.logi, api.combat, api.CFG
L.on, L.bmat, L.salvage = true, 0, 0
L.fac = {ammo=0, shirts=0}
L.base = {name="base", X=0, Y=0, Z=0, ammo=0, shirts=0}
L.foes, L.trucks = {}, {}
combat.auto, combat.mode, combat.cargo = true, nil, 0
-- A1: comboio chega e cria 1 carga sem debitar nada em lugar nenhum (nao existe retaguarda nem producao).
local cv = {kind="foe", team=0, hp=900, off=0, state="toFront", from={X=0,Y=0,Z=0}, to={X=300,Y=0,Z=0}, X=0, Y=0, Z=0}
table.insert(L.foes, cv)
for _ = 1, 10 do L.convoyTick(0.5, 0) end
assert(combat.cargo == 1 and L.bmat == 0 and L.salvage == 0 and L.fac.ammo == 0, "A1: carga criada do nada")
assert(cv.cargo == nil, "A1: o caminhao inimigo nao carrega nada; destruir so impede o +1")
-- A2: onda: ate perWave cargas; cada uma que falta tira cut soldados (minimo 3). Contador, nao estoque.
combat.cargo = 0
assert(L.waveCut(10) == 10 - C.ECONVOY.perWave * C.ECONVOY.cut and combat.cargo == 0, "A2: corte abstrato")
assert(L.waveCut(4) == 3, "A2: piso 3 gratis")
-- A3: snapshot nao guarda combat.cargo nem comboios em transito; logi.start repoe cargo0 (presente/perda no continue).
L.prio = "auto"
local snap = L.snapshot()
for k in pairs(snap) do assert(k ~= "cargo" and k ~= "foes", "A3") end
''')
# A3 (texto): logi.start reescreve a carga; A4: inimigo nao gasta municao no tiro (so `if ours`).
assert "combat.cargo, combat.convoys, combat.convoysCut = CFG.ECONVOY.cargo0, 0, 0" in src
assert len(re.findall(r"if ours then (?:shooter|m)\.ammo = ", src)) == 2, "A4: municao so do nosso lado"
# A5: ondas e reforcos nascem sem custo material (spawnEnemies nao debita nada); ai.mp regenera por ponto.
spawn = src[src.index("local function spawnEnemies"):src.index("local function squadCenter")]
assert "logi." not in spawn and "economy" not in spawn
assert "ai.mp = math.min(CFG.AI.cap, ai.mp + held * CFG.AI.rate * dt)" in src
# A6: morteiro inimigo sem custo; trincheira/arame inimigos gratis.
assert "o inimigo nao (controlado pela IA)" in src and "(de graca)" in src
print("PASS: auditoria do main atual (A1 carga do nada, A2 corte abstrato, A3 save sem carga, A4 municao inimiga infinita, "
      "A5 ondas/reforcos sem custo material, A6 morteiro/fortificacao gratis)")
