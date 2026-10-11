"""BASES_AVANCADAS: recrutar no ramo logistico pela interface comum (spawnSite pura -> spawnSquad -> spawnCommit): base principal ou
base avancada ativa com estoque, a mais proxima do cursor; cursor dentro de uma base = so ela (sem fallback); sem mao de obra;
ponto sem base nao reforca (CFG.SPAWN.pointSpawn); ramo legado / Assalto identicos ao candidate_v3.

  cd /d/GitHub/foxhole-rts && PYTHONPATH=D:/tools/pylibs PYTHONDONTWRITEBYTECODE=1 \
      python data/parallel/forward_bases/stage2/test_recruitment.py
"""
import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parent))
import harness_bases as H  # noqa: E402

PRE = r'''
newMatch()
local L, C = A.logi, A.CFG
local F, FR = C.FWD, C.FRIENDLY_TEAM
for _, tr in ipairs(L.trucks) do tr.state, tr.hp = 'idle', C.LOGI.hp end
L.base.shirts, L.base.rifle = 30, 10
A.economy.manpower = 0   -- o ramo logistico nao usa mao de obra
local function last() return SPAWNS[#SPAWNS] end
local function snap()
    local s = {#A.squad(), A.economy.manpower, L.base.shirts, L.base.rifle, L.exitN or 0}
    for _, fb in ipairs(L.fwd) do s[#s + 1] = fb.dep.shirts; s[#s + 1] = fb.dep.rifle; s[#s + 1] = fb.exitI end
    return table.concat(s, ",")
end
'''


def t_base_principal(v):
    lua = H.new_game(version=v)
    lua.execute(PRE + r'''
for i = #A.squad(), 1, -1 do table.remove(A.squad(), i) end   -- esquadrao vazio: o teto de combate nao interfere
local n0 = #A.squad()
assert(A.recruit("rifle") == true)
assert(#A.squad() == n0 + 1 and L.base.shirts == 29 and L.base.rifle == 9 and A.economy.manpower == 0, "fuzileiro: 1 camisa + 1 fuzil, sem mao de obra")
local s = last()
assert(math.abs(sdist(s, L.base) - 250) < 1e-6, "nasceu no anel da base, nao ao lado do esquadrao: " .. sdist(s, L.base))
assert(s.role == "rifle" and L.exitN == 1)
-- mg/sniper/medic gastam so camisa
for _, role in ipairs({"mg", "sniper", "medic"}) do
    local sh, ri = L.base.shirts, L.base.rifle
    assert(A.recruit(role) == true and L.base.shirts == sh - 1 and L.base.rifle == ri, role .. " so camisa")
end
-- oficial: so um
assert(A.recruit("officer") == true and L.base.shirts == 25)
assert(A.recruit("officer") == false and L.base.shirts == 25, "segundo oficial recusado sem debito")
-- falha de spawn: nada debitado
SPAWN_FAIL = true
local sh, ri, n = L.base.shirts, L.base.rifle, #A.squad()
assert(A.recruit("rifle") == false and L.base.shirts == sh and L.base.rifle == ri and #A.squad() == n and (L.exitN or 0) == 5)
SPAWN_FAIL = false
-- sem fuzil: fuzileiro recusa, medico nao
L.base.rifle = 0
assert(A.recruit("rifle") == false and saw("sem fuzis em base"))
assert(A.recruit("medic") == true)
L.base.shirts = 0
assert(A.recruit("medic") == false and saw("sem camisas em base"))
assert(A.economy.manpower == 0)
''')
    return "base principal: nasce no anel, 1 camisa (+1 fuzil so o fuzileiro), sem mao de obra, oficial unico, falha de spawn nao debita"


def t_pura(v):
    lua = H.new_game(version=v)
    lua.execute(PRE + r'''
local pt, fb = buildFwd(4000, 0)
stock(fb.dep, 12, 3)
local before = snap()
for i = 1, 6 do
    local site = L.spawnSite("rifle", {X = 3900, Y = 100})
    assert(site and site.kind == "fwd" and site.fb == fb and site.explicit == true and site.need.shirts == 1 and site.need.rifle == 1)
    L.spawnSite("rifle", nil); L.spawnSite("mg", {X = -100, Y = 0})
end
assert(snap() == before and SPAWNED == 0, "spawnSite e pura: nenhum estado muda")
local s, w = L.spawnSite("inexistente", nil); assert(s == nil and w == "função sem receita")
L.on = false; s, w = L.spawnSite("rifle", nil); assert(s == nil and w == "ramo legado"); L.on = true
A.combat.mode = "assault"; s, w = L.spawnSite("rifle", nil); assert(s == nil and w == "ramo legado"); A.combat.mode = nil
''')
    return "spawnSite pura (nada muda em 18 chamadas), recusa funcao sem receita, legado e Assalto"


def t_mais_proxima(v):
    lua = H.new_game(version=v)
    lua.execute(PRE + r'''
local ptA, fbA = buildFwd(4000, 0)
local ptB, fbB = buildFwd(0, 4000)
stockFwd(fbA, 10, 5); stockFwd(fbB, 10, 5)
-- cursor longe de qualquer anel: a mais proxima COM estoque
CURSOR = {X = 6500, Y = -2000}            -- perto de A
assert(A.recruit("rifle") and fbA.dep.shirts == 9 and fbB.dep.shirts == 10 and L.base.shirts == 30)
CURSOR = {X = -2000, Y = 6500}            -- perto de B
assert(A.recruit("rifle") and fbB.dep.shirts == 9 and fbA.dep.shirts == 9)
CURSOR = {X = -3000, Y = -3000}           -- perto da base principal
assert(A.recruit("rifle") and L.base.shirts == 29)
-- a mais proxima sem fuzil e pulada; o medico (so camisa) usa a mais proxima
fbA.led.lost.rifle = fbA.led.lost.rifle + fbA.dep.rifle; fbA.dep.rifle = 0
CURSOR = {X = 6500, Y = -2000}
assert(A.recruit("rifle") and fbA.dep.shirts == 9 and L.base.rifle == 8 and fbB.dep.rifle == 4, "fuzileiro pulou A (sem fuzil) e usou a base principal")
local b = fbA.dep.shirts
assert(A.recruit("medic") and fbA.dep.shirts == b - 1, "medico nasce em A: so precisa de camisa")
-- sem cursor e sem esquadrao: a frente (ponto inimigo mais perto da base) ou a base
for i = #A.squad(), 1, -1 do table.remove(A.squad(), i) end
CURSOR = nil
local site = L.spawnSite("medic", nil)
assert(site and site.kind == "base" and site.explicit == false, "sem referencia: base principal")
-- saida: a base avancada gira entre as saidas validadas, sem deslocamento de formacao
fbA.dep.shirts = fbA.dep.shirts + 10; fbA.led.rx.shirts = fbA.led.rx.shirts + 10; fbA.exitI = 0   -- como uma entrega de caminhao
CURSOR = {X = 6500, Y = -2000}
local seen = {}
for i = 1, #fbA.exits + 2 do
    assert(A.recruit("medic"))
    local s = last()
    local e = fbA.exits[((i - 1) % #fbA.exits) + 1]
    assert(math.abs(s.x - e.X) < 1e-6 and math.abs(s.y - e.Y) < 1e-6 and math.abs(s.z - (e.Z + 90)) < 1e-6, "nasce na saida " .. i)
    seen[s.x .. "," .. s.y] = true
end
local n = 0; for _ in pairs(seen) do n = n + 1 end
assert(n == #fbA.exits, "usou todas as saidas em rodizio")
assert(L.fwdAudit(fbA) and L.fwdAudit(fbB), "razao por base fecha")
''')
    return "mais proxima do cursor com estoque; pula base sem fuzil (medico usa); saida em rodizio, exata, sem formacao"


def t_selecao_explicita(v):
    lua = H.new_game(version=v)
    lua.execute(PRE + r'''
local ptA, fbA = buildFwd(4000, 0)
stock(fbA.dep, 10, 0)           -- A: camisas, sem fuzis
local before = snap()
-- cursor DENTRO do anel de A: so A conta -> recusa clara, sem cair na base principal que tem fuzis
CURSOR = {X = 4100, Y = 100}
assert(A.recruit("rifle") == false and snap() == before and SPAWNED == 0)
assert(saw("sem fuzis em base avançada A") and saw("mova o cursor para fora das bases"), LOG[#LOG])
-- o medico nasce em A (so camisa)
assert(A.recruit("medic") == true and fbA.dep.shirts == 9 and L.base.shirts == 30)
-- cursor dentro da base principal sem camisas: recusa, mesmo com A abastecida
fbA.dep.rifle = 5
L.base.shirts = 0
CURSOR = {X = 100, Y = 100}
before = snap()
assert(A.recruit("rifle") == false and snap() == before and saw("sem camisas em base"))
assert(fbA.dep.shirts == 9 and fbA.dep.rifle == 5, "A nao foi usada em silencio")
-- cursor fora dos aneis: o automatico acha A
CURSOR = {X = 7000, Y = 3000}
assert(A.recruit("rifle") == true and fbA.dep.shirts == 8)
-- nenhuma tem estoque: recusa com o motivo da mais proxima
fbA.dep.shirts = 0
CURSOR = {X = 7000, Y = 3000}
assert(A.recruit("rifle") == false and saw("sem camisas em base avançada A"))
-- ponto neutro com base: INATIVA, cursor nela recusa; automatico a ignora
fbA.dep.shirts, L.base.shirts = 5, 5
ptA.owner, ptA.prog = nil, 0
CURSOR = {X = 4100, Y = 0}
assert(A.recruit("medic") == false and saw("inativa"))
assert(fbA.dep.shirts == 5, "estoque preservado na base inativa")
CURSOR = {X = 6500, Y = -2000}
assert(A.recruit("medic") == true and L.base.shirts == 4 and fbA.dep.shirts == 5, "automatico ignora a inativa")
-- recaptura: volta a ativa com o estoque que tinha
ptA.owner, ptA.prog = FR, 1
CURSOR = {X = 4100, Y = 0}
assert(A.recruit("medic") == true and fbA.dep.shirts == 4)
''')
    return "cursor dentro de uma base = so ela (recusa clara, sem fallback); base inativa ignorada e preservada; recapturada volta"


def t_ponto_sem_base(v):
    lua = H.new_game(version=v)
    lua.execute(PRE + r'''
local pt = mkPoint(4000, 0, FR)
local dep = L.depotOf(pt)
dep.shirts, dep.rifle = 5, 5
CURSOR = {X = 4050, Y = 0}   -- dentro do anel do ponto
assert(A.recruit("rifle") == true)
assert(L.base.shirts == 29 and dep.shirts == 5 and dep.rifle == 5, "ponto sem base nao reforca: nasce na base principal")
local s = last()
assert(math.abs(sdist(s, L.base) - 250) < 1e-6)
-- pointSpawn = true restaura o antigo
C.SPAWN.pointSpawn = true
assert(A.recruit("rifle") == true)
assert(dep.shirts == 4 and dep.rifle == 4 and L.base.shirts == 29, "pointSpawn: nasce no ponto e gasta o estoque dele")
assert(sdist(last(), pt) < 600)
C.SPAWN.pointSpawn = false
''')
    return "ponto de controle sem base nao e local de reforco; CFG.SPAWN.pointSpawn=true restaura o antigo"


def t_teto_e_reserva(v):
    lua = H.new_game(version=v)
    lua.execute(PRE + r'''
-- SQUAD_MAX: so combate conta
while combatants() < C.SQUAD_MAX do newSoldier("rifle", 0, 0) end
local n = #A.squad()
assert(A.recruit("rifle") == false and #A.squad() == n and L.base.shirts == 30 and saw("esquadrao no maximo"))
''')
    lua = H.new_game(version=v)
    lua.execute(PRE + r'''
-- reserva das camisas dos trabalhadores (v3): sem caminhao de recurso, a base nao gasta as 3 ultimas camisas em combate
C.COLETA.workers = 3
L.trucks[1].state, L.trucks[1].hp = "dead", 0
L.base.shirts = 3
assert(L.workerReserve(L.base) == 3)
local ptA, fbA = buildFwd(4000, 0)
stock(fbA.dep, 4, 2)
CURSOR = {X = -3000, Y = -3000}
assert(A.recruit("rifle") == true and fbA.dep.shirts == 3 and L.base.shirts == 3, "base reservada: a mais proxima SEM reserva (A) reforca")
CURSOR = {X = 100, Y = 100}
assert(A.recruit("rifle") == false and saw("camisas reservadas aos trabalhadores"), LOG[#LOG])
''')
    return "SQUAD_MAX so de combate; reserva de camisas dos trabalhadores continua valendo na base principal"


def t_legado(v):
    """Ramo legado e Assalto: mesmo resultado do candidate_v3 (mao de obra, deposito antigo, sem spawnSite)."""
    out = {}
    for name, text in (("v3", H.TEXT_V3), ("v4", H.TEXT_V4)):
        lua = H.new_game(text, version=v)
        out[name] = lua.execute(r'''
local res = {}
-- (a) sem logistica
A.logi.on = false
A.economy.manpower = 200
A.hooks.authority(function() return true end)
for i = 1, 3 do newSoldier("rifle", 100 * i, 0) end
local ok1 = A.recruit("rifle")
res[#res + 1] = table.concat({tostring(ok1), A.economy.manpower, #A.squad(), SPAWNED, tostring(A.recruit("officer")), A.economy.manpower}, "/")
A.economy.manpower = 5
res[#res + 1] = table.concat({tostring(A.recruit("mg")), A.economy.manpower, #A.squad()}, "/")
-- (b) Assalto com logistica ativa: mao de obra + deposito antigo
newMatch()
local L = A.logi
for _, tr in ipairs(L.trucks) do tr.state, tr.hp = 'idle', A.CFG.LOGI.hp end
A.combat.mode = "assault"
A.economy.manpower = 200
local sh, ri = L.base.shirts, L.base.rifle
local ok2 = A.recruit("rifle")
res[#res + 1] = table.concat({tostring(ok2), A.economy.manpower, L.base.shirts - sh, L.base.rifle - ri, #A.squad()}, "/")
A.combat.mode = nil
return table.concat(res, " | ")
''')
    assert out["v3"] == out["v4"], "legado/Assalto divergem do v3:\n v3=%s\n v4=%s" % (out["v3"], out["v4"])
    return "legado/Assalto identicos ao v3: " + out["v4"]


for v in ("lua54", "lua55"):
    H.case("[%s] base principal" % v, t_base_principal, v)
    H.case("[%s] spawnSite pura" % v, t_pura, v)
    H.case("[%s] mais proxima do cursor com estoque, saidas" % v, t_mais_proxima, v)
    H.case("[%s] selecao explicita sem fallback, base inativa" % v, t_selecao_explicita, v)
    H.case("[%s] ponto sem base / pointSpawn" % v, t_ponto_sem_base, v)
    H.case("[%s] teto de combate e reserva dos trabalhadores" % v, t_teto_e_reserva, v)
    H.case("[%s] legado e Assalto identicos ao v3" % v, t_legado, v)
H.finish("test_recrutamento")
