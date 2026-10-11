"""BASES_AVANCADAS: construcao (Shift+J com 2 toques), recusas, rollback de spawn, pedido pendente com reserva de bmat.

  cd /d/GitHub/foxhole-rts && PYTHONPATH=D:/tools/pylibs PYTHONDONTWRITEBYTECODE=1 \
      python dados/paralel/bases_avancadas/etapa2/test_construcao.py
"""
import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parent))
import harness_bases as H  # noqa: E402

PRE = r'''
newMatch()
local L, C = A.logi, A.CFG
local F = C.FWD
local FR = C.FRIENDLY_TEAM
for _, tr in ipairs(L.trucks) do tr.state, tr.hp = 'idle', C.LOGI.hp end   -- partida manual comeca com o caminhao de recurso por construir (reserva 100): isola a base
local function pressTwice(c)
    L.fwdKey(c); clock = clock + 1.0
    return L.fwdKey(c)
end
'''


def t_construcao_ok(v):
    lua = H.new_game(version=v)
    lua.execute(PRE + r'''
local pt = mkPoint(4000, 0, FR)
L.bmat = 412
-- 1o toque: so informa (custo e local), nada muda
L.fwdKey({X = 4000, Y = 0})
assert(pt.fb == nil and L.bmat == 412 and SPAWNED_FWD == 0 and #L.fwd == 0, "1o toque nao constroi")
assert(saw("Base avançada em A: 300 bmat (fábrica tem 412)") and saw("Shift+J de novo"), "mensagem de custo")
-- depois da janela de 4 s volta a ser 1o toque
clock = clock + 5.0
L.fwdKey({X = 4000, Y = 0})
assert(pt.fb == nil and L.bmat == 412 and SPAWNED_FWD == 0, "confirmacao expirada")
clock = clock + 1.0
L.fwdKey({X = 4000, Y = 0})   -- 2o toque dentro de 4 s
local fb = pt.fb
assert(fb and L.fwd[1] == fb and fb.dep == pt.dep and pt.dep.fb == fb, "base ligada ao ponto e ao deposito")
assert(L.bmat == 112, "debito de 300 bmat so apos o spawn: " .. L.bmat)
assert(SPAWNED_FWD == 1 and fwdLive() == 1 and #fwdActors() == 1)
assert(fb.hp == 1725 and fb.maxHp == 1725 and fb.code == "ForwardBase1")
assert(#fb.exits >= F.minExits, "saidas validadas: " .. #fb.exits)
assert(dist(fb, pt) <= 300 + 1e-6, "dentro do anel do ponto")
for _, e in ipairs(fb.exits) do assert(math.abs(dist(e, fb) - F.exitR) < 1e-6) end
assert((pt.dep.shirts or 0) == 0 and (pt.dep.rifle or 0) == 0, "estoque da base nasce vazio (a compra e da estrutura)")
assert(A.logi.fwdAudit(fb))
-- repetir Shift+J num ponto que ja tem base: informa, nao cobra, nao duplica
for i = 1, 4 do clock = clock + 1.0; L.fwdKey({X = 4000, Y = 0}) end
assert(L.bmat == 112 and fwdLive() == 1 and #L.fwd == 1, "repetir nao cobra nem duplica")
assert(saw("BASE AVANÇADA A:"))
''')
    return "1o toque informa, 2o constroi: -300 bmat apos o spawn, base ligada ao deposito, saidas validadas, repetir nao duplica"


def t_recusas(v):
    lua = H.new_game(version=v)
    lua.execute(PRE + r'''
local function refused(why, fn)
    local bmat, n, spawned = L.bmat, #L.fwd, SPAWNED_FWD
    fn()
    assert(L.bmat == bmat and #L.fwd == n and SPAWNED_FWD == spawned and L.fwdOrder == nil, "recusa sem debito/ator/pedido: " .. why)
end
L.bmat = 1000
local ok, p
-- ponto neutro e ponto inimigo
local pn = mkPoint(4000, 0, nil)
refused("ponto neutro", function() pressTwice({X = 4000, Y = 0}) end)
assert(saw("não é seu"))
local pe = mkPoint(4000, 4000, C.ENEMY_TEAM)
refused("ponto inimigo", function() pressTwice({X = 4000, Y = 4000}) end)
-- cursor fora de qualquer ponto
refused("fora de ponto", function() pressTwice({X = -3000, Y = 3000}) end)
assert(saw("ponha o cursor dentro de um ponto"))
-- ponto nosso perto demais da base e sem inimigo perto
pn.owner, pn.prog = FR, 1
pe.owner = nil
local near = mkPoint(-1800, 1800, FR)
refused("perto da base", function() pressTwice({X = -1800, Y = 1800}) end)
assert(saw("perto demais da base"))
table.remove(A.points())   -- libera a vaga (POINT_MAX = 5)
-- ... mas perto de um ponto inimigo qualifica (distancia 'avancada' = frente)
pe.owner, pe.prog = C.ENEMY_TEAM, -1
-- inimigo vivo no anel do ponto
local foe = newSoldier("rifle", 4100, 100, C.ENEMY_TEAM)
refused("inimigo no anel", function() pressTwice({X = 4000, Y = 0}) end)
assert(saw("há inimigos no ponto A"))
table.remove(A.enemies())
-- sem logistica / Assalto
L.on = false
refused("sem logistica", function() pressTwice({X = 4000, Y = 0}) end)
L.on = true
A.combat.mode = "assault"
refused("assalto", function() pressTwice({X = 4000, Y = 0}) end)
A.combat.mode = nil
-- chao que nao e Landscape (telhado/veiculo/prop)
terrainClass = "StaticMeshActor"
refused("telhado", function() pressTwice({X = 4000, Y = 0}) end)
assert(saw("sem lugar:"))
terrainClass = nil
-- terreno inclinado
terrainZ = function(x, y) return (x - 4000) * 0.5 end
refused("inclinado", function() pressTwice({X = 4000, Y = 0}) end)
terrainZ = function() return 0 end
-- obra do mod no caminho
A.S.trenches[#A.S.trenches + 1] = {X = 4000, Y = 0, Z = 0}
refused("trincheira no caminho", function() pressTwice({X = 4000, Y = 0}) end)
A.S.trenches = {}
-- sem saidas livres (chao so ate 650 cm do centro: nenhuma saida a 800)
terrainZ = function(x, y) if dist({X = x, Y = y}, {X = 4000, Y = 0}) > 650 then return nil end return 0 end
refused("sem saidas", function() pressTwice({X = 4000, Y = 0}) end)
terrainZ = function() return 0 end
-- classe que nao carrega
LOAD_FAIL = true
refused("classe nao carrega", function() pressTwice({X = 4000, Y = 0}) end)
LOAD_FAIL = nil
-- plano B (malha) esta declarado mas nao implementado
F.visual = "mesh"
refused("plano B", function() pressTwice({X = 4000, Y = 0}) end)
assert(saw("plano B"))
F.visual = "native"
-- deposito do ponto acima do teto de slots
pn.dep = nil
local dep = L.depotOf(pn); dep.ammo = 20
refused("deposito acima do teto", function() pressTwice({X = 4000, Y = 0}) end)
dep.ammo = 0
-- finalmente passa (nada acima deixou resto)
pressTwice({X = 4000, Y = 0})
assert(pn.fb and L.bmat == 700 and #L.fwd == 1)
-- limite CFG.FWD.max
for i = 1, F.max - 1 do
    local q = mkPoint(4000 + 2500 * i, 0, FR)
    q.Y = 0
    local ok2 = L.fwdBuild(q); assert(ok2, "base " .. (i + 1))
end
assert(#L.fwd == F.max)
local extra = mkPoint(4000, -3000, FR)
refused("limite", function() pressTwice({X = 4000, Y = -3000}) end)
assert(saw("limite de bases avançadas"))
''')
    return "recusas sem debito/ator: neutro, inimigo, fora de ponto, perto da base, inimigo no anel, sem logistica, Assalto, telhado, inclinado, obra do mod, sem saidas, classe, plano B, teto de slots, limite"


def t_rollback(v):
    lua = H.new_game(version=v)
    lua.execute(PRE + r'''
local pt = mkPoint(4000, 0, FR)
L.bmat = 500
for _, mode in ipairs({"nil", "destroying", "health", "shifted", "yaw", "code"}) do
    FWD_FAIL = mode
    local ok, why, kind = L.fwdBuild(pt)
    assert(ok == false and kind == "fail" and why:find("nada debitado", 1, true), mode .. ": " .. tostring(why))
    assert(L.bmat == 500 and pt.fb == nil and #L.fwd == 0 and pt.dep == nil, mode .. ": sem debito nem registro")
    for _, a in ipairs(fwdActors()) do assert(a.bActorIsBeingDestroyed, mode .. ": ator que nasceu foi desfeito") end
end
-- strict=false aceita vida/codigo diferentes (relaxavel ate o ensaio B1)
FWD_FAIL = "health"; F.strict = false
assert(L.fwdBuild(pt) == true and L.bmat == 200)
assert(saw("construída"))
''')
    return "6 falhas de spawn (nil, em destruicao, vida, deslocado, rotacao, CodeName): ator desfeito, bmat e ponto intactos; strict=false relaxa"


def t_pendente(v):
    lua = H.new_game(version=v)
    lua.execute(PRE + r'''
local pt = mkPoint(4000, 0, FR)
-- sem bmat: 2o toque registra pedido; a fabrica para de iniciar receitas
L.bmat = 150
L.fwdKey({X = 4000, Y = 0}); assert(saw("faltam 150 (fábrica tem 150)"))
clock = clock + 1.0; L.fwdKey({X = 4000, Y = 0})
assert(L.fwdOrder and L.fwdOrder.pt == pt and L.fwdOrder.cost == 300 and pt.fb == nil and L.bmat == 150, "pedido registrado, nada debitado")
assert(L.fwdReserve() == 300)
L.job = nil
L.factoryStep(1); assert(L.job == nil, "fabrica parou (reserva de 300)")
local h = A.hudLine()
assert(h:find("Fábrica | guarda 300 bmat para base avançada em A (bmat 150)", 1, true), h)
-- outro ponto: so um pedido por vez
local q = mkPoint(7000, 0, FR)
L.fwdKey({X = 7000, Y = 0}); assert(saw("pedido de base avançada pendente"))
-- bmat chega a 300 sozinho (refinaria): constroi no tick
L.salvage = 400
local ok = runUntil(120, function() return pt.fb ~= nil end)
assert(ok and pt.fb and L.fwdOrder == nil, "construiu sozinho")
assert(L.bmat >= 0 and L.bmat < 150 + 200 - 300 + 1, "bmat debitado uma vez: " .. L.bmat)
assert(#L.fwd == 1 and fwdLive() == 1)
-- cancelar com o mesmo atalho (2 toques) devolve a fabrica
L.fwd, pt.fb = {}, nil
for _, a in ipairs(fwdActors()) do a.bActorIsBeingDestroyed = true end
L.bmat = 0
L.fwdOrder = {pt = pt, cost = 300, t0 = clock}
clock = clock + 1; L.fwdKey({X = 4000, Y = 0})
assert(saw("Shift+J de novo em 4 s cancela"))
clock = clock + 1; L.fwdKey({X = 4000, Y = 0})
assert(L.fwdOrder == nil)
-- cancela por prazo
L.fwdOrder = {pt = pt, cost = 300, t0 = clock}
clock = clock + F.pending + 1; stepOnce()
assert(L.fwdOrder == nil and saw("tempo esgotado"))
-- cancela se o ponto foi perdido / inimigo no anel / base principal
L.fwdOrder = {pt = pt, cost = 300, t0 = clock}
pt.owner = C.ENEMY_TEAM; stepOnce()
assert(L.fwdOrder == nil and saw("não é seu"))
pt.owner = FR
L.fwdOrder = {pt = pt, cost = 300, t0 = clock}
newSoldier("rifle", 4100, 100, C.ENEMY_TEAM); stepOnce()
assert(L.fwdOrder == nil and saw("há inimigos"))
table.remove(A.enemies())
-- caminhao destruido tem prioridade: reserva do caminhao sai antes do pedido
L.fwdOrder = nil
L.salvage = 0
L.bmat = 350
L.trucks[2].state, L.trucks[2].hp, L.trucks[2].rebuildT = "dead", 0, clock + 1e9
L.fwdOrder = {pt = pt, cost = 300, t0 = clock}
assert(L.rebuildReserve() == 100)
stepOnce()
assert(pt.fb == nil and L.fwdOrder, "350 - 100 (caminhao) = 250 < 300: pedido espera")
L.bmat = 400
stepOnce()
assert(pt.fb and L.bmat == 100 and L.rebuildReserve() == 100, "400 - 300 = 100 sobra para o caminhao")
assert(L.fwdOrder == nil)
''')
    return "pedido pendente: reserva para a fabrica, painel 'guarda 300 bmat', um por vez, constroi sozinho, cancela (2 toques, prazo, ponto perdido, inimigo), caminhao destruido tem prioridade"


def t_prioridade_caminhao(v):
    lua = H.new_game(version=v)
    lua.execute(PRE + r'''
local pt = mkPoint(4000, 0, FR)
L.trucks[2].state, L.trucks[2].hp, L.trucks[2].rebuildT = "dead", 0, clock + 1e9
L.bmat = 350
assert(L.rebuildReserve() == 100)
L.fwdKey({X = 4000, Y = 0})
assert(saw("faltam 50"), "1o toque ja diz que a reserva do caminhao come bmat")
clock = clock + 1.0
L.fwdKey({X = 4000, Y = 0})
assert(pt.fb == nil and SPAWNED_FWD == 0 and L.bmat == 350, "caminhao destruido primeiro: nada construido")
assert(L.fwdOrder and L.fwdOrder.pt == pt and L.fwdReserve() == 300 and L.fwdOrder.cost == 300, "pedido registrado, depois da reserva do caminhao")
assert(L.rebuildReserve() == 100 and L.bmat - L.rebuildReserve() == 250, "reserva do caminhao intacta")
''')
    return "Shift+J com caminhao destruido: 350 - 100 < 300 => nao constroi, registra pedido depois da reserva do caminhao"


def t_bmat_conservacao(v):
    lua = H.new_game(version=v)
    lua.execute(PRE + r'''
L.bmat = 1000
local before = L.bmat
local made = 0
for i = 1, F.max do
    local q = mkPoint(4000 + 2500 * (i - 1), 0, FR)
    if L.fwdBuild(q) then made = made + 1 end
end
assert(made == F.max and L.bmat == before - made * F.cost, "bmat = antes - 300 x bases")
-- falha de spawn nao gasta
FWD_FAIL = "health"
local q = mkPoint(4000, 3000, FR)
local b = L.bmat
L.fwdBuild(q)
assert(L.bmat == b)
''')
    return "razao de bmat: -300 por base construida, 0 por tentativa falha"


for v in ("lua54", "lua55"):
    H.case("[%s] construcao ok (2 toques)" % v, t_construcao_ok, v)
    H.case("[%s] recusas" % v, t_recusas, v)
    H.case("[%s] rollback de spawn" % v, t_rollback, v)
    H.case("[%s] pedido pendente com reserva" % v, t_pendente, v)
    H.case("[%s] caminhao destruido tem prioridade (Shift+J)" % v, t_prioridade_caminhao, v)
    H.case("[%s] razao de bmat" % v, t_bmat_conservacao, v)
H.finish("test_construcao")
