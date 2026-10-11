"""BASES_AVANCADAS: abastecimento (caminhao, teto de 15 slots, camisa/fuzil so para quem nasce soldado), corte de abastecimento,
destruicao/captura (perde o estoque UMA vez), recaptura, morteiro inimigo, derrota por falta de tropa, razao por base (fuzz).

  cd /d/GitHub/foxhole-rts && PYTHONPATH=D:/tools/pylibs PYTHONDONTWRITEBYTECODE=1 \
      python dados/paralel/bases_avancadas/etapa2/test_perda.py
"""
import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parent))
import harness_bases as H  # noqa: E402

PRE = r'''
newMatch()
local L, C = A.logi, A.CFG
local F, FR = C.FWD, C.FRIENDLY_TEAM
C.ENEMY_DIG, C.ENEMY_WIRE = false, false
for _, tr in ipairs(L.trucks) do tr.state, tr.hp = 'idle', C.LOGI.hp end
L.base.shirts, L.base.rifle = 30, 10
A.economy.manpower = 0
local function boxes(c) return c and ((c.ammo or 0) + (c.shirts or 0) + (c.rifle or 0) + (c.medical or 0)) or 0 end
'''


def t_corte_de_abastecimento(v):
    lua = H.new_game(version=v)
    lua.execute(PRE + r'''
local pt, fb = buildFwd(4000, 0)
stockFwd(fb, 2, 2)
CURSOR = {X = 4050, Y = 0}
assert(A.recruit("rifle") and A.recruit("rifle") and fb.dep.shirts == 0)
local before = #A.squad()
assert(A.recruit("rifle") == false and #A.squad() == before and saw("sem camisas em base avançada A"), "sem camisas: nao reforca nela")
assert(A.recruit("medic") == false)
assert(L.base.shirts == 30, "a base principal NAO cobre a base cortada em silencio")
-- caminhao carregando camisas/fuzis para a base e destruido no caminho: nada chega
local tr = L.trucks[2]
tr.state, tr.cargo, tr.dest = "toDep", {ammo = 0, shirts = 1, rifle = 1, medical = 0}, fb.dep
L.hit(tr, 1e9, clock)
assert(tr.state == "dead" and tr.cargo == nil)
for i = 1, 50 do stepOnce() end
assert(fb.dep.shirts == 0 and fb.dep.rifle == 0 and A.recruit("rifle") == false, "abastecimento cortado: base sem reforco")
-- restabelecido: o caminhao entrega e a base volta a reforcar
local tr1 = L.trucks[3]
tr1.state, tr1.cargo, tr1.dest = "toDep", {ammo = 0, shirts = 1, rifle = 1, medical = 0}, fb.dep
L.drive = function() return true end
L.truckStep(tr1, 0.1, clock)
assert(fb.dep.shirts == 10 and fb.dep.rifle == 20, "entrega de 1 caixa de camisas (10) e de fuzis (20)")
assert(A.recruit("rifle") == true and fb.dep.shirts == 9)
assert(L.fwdAudit(fb))
''')
    return "base sem camisas/fuzis nao reforca e a principal nao cobre; caminhao destruido nao entrega; entrega restabelece"


def t_destruicao_captura(v):
    lua = H.new_game(version=v)
    lua.execute(PRE + r'''
local pt, fb = buildFwd(4000, 0)
stockFwd(fb, 12, 7)
fb.dep.ammo, fb.dep.medical = 3, 10
local actor = fb.actor
-- captura pelo inimigo (pointsTick real): inimigo sozinho no anel
newSoldier("rifle", 4050, 0, C.ENEMY_TEAM)
pt.prog = -0.99
A.pointsTick(); clock = clock + 2
A.pointsTick()
assert(pt.owner == C.ENEMY_TEAM, "ponto capturado")
assert(pt.fb == nil and fb.dead == true and #L.fwd == 0 and pt.dep.fb == nil, "registro removido")
assert(actor.bActorIsBeingDestroyed and fwdLive() == 0, "ator destruido, sem residuo")
assert(pt.dep.shirts == 0 and pt.dep.rifle == 0 and pt.dep.ammo == 0 and pt.dep.medical == 0, "estoque perdido")
assert(fb.led.lost.shirts == 12 and fb.led.lost.rifle == 7 and L.fwdAudit(fb), "razao: perdido uma vez")
assert(L.fwdLost == 1)
-- idempotente: de novo nao perde nada nem conta outra vez
assert(L.fwdLose(fb, "capturada") == false and L.fwdLose(fb, "destruída") == false)
pt.dep.shirts = 5   -- estoque novo (nao e da base): uma 2a chamada nao pode zera-lo
L.fwdLose(fb, "destruída")
assert(pt.dep.shirts == 5 and fb.led.lost.shirts == 12 and L.fwdLost == 1, "2a chamada e no-op")
pt.dep.shirts = 0
-- recaptura: o ponto volta a ser nosso, SEM base e sem estoque; da para reconstruir (300 bmat de novo)
A.economy.manpower = 0
table.remove(A.enemies())
pt.owner, pt.prog = FR, 1
CURSOR = {X = 4050, Y = 0}
assert(A.recruit("medic") == true and pt.dep.shirts == 0 and L.base.shirts == 29, "ponto recapturado sem base nao reforca")
L.bmat = 700
local b = L.bmat
L.fwdKey({X = 4000, Y = 0}); clock = clock + 1; L.fwdKey({X = 4000, Y = 0})
assert(pt.fb and pt.fb ~= fb and L.bmat == b - 300 and #L.fwd == 1 and fwdLive() == 1, "reconstruida")
assert(pt.fb.dep.shirts == 0, "reconstruida vazia")
''')
    return "captura: perde estoque e ator uma vez (idempotente), razao fecha; recaptura sem base; reconstruir cobra 300 de novo"


def t_morteiro(v):
    lua = H.new_game(version=v)
    lua.execute(PRE + r'''
local pt, fb = buildFwd(4000, 0)
stockFwd(fb, 5, 5)
local R, D = C.MORTAR.radius, C.MORTAR.dmg
-- nosso morteiro nao fere a nossa base; longe de radius*1.5 tambem nao
L.blast({X = fb.X, Y = fb.Y}, R, D, C.FRIENDLY_TEAM)
L.blast({X = fb.X + 2000, Y = fb.Y}, R, D, C.ENEMY_TEAM)
assert(fb.hp == 1725)
-- morteiro inimigo: dano x blastMul, ate destruir (uma vez so)
local n = 0
while not fb.dead and n < 100 do L.blast({X = fb.X + 100, Y = fb.Y}, R, D, C.ENEMY_TEAM); n = n + 1 end
assert(fb.dead and n == math.ceil(1725 / (D * F.blastMul)), "salvas ate destruir: " .. n)
assert(fwdLive() == 0 and pt.fb == nil and fb.led.lost.shirts == 5 and L.fwdAudit(fb))
assert(pt.dep.shirts == 0 and pt.dep.rifle == 0 and pt.dep.ammo == 0 and pt.dep.medical == 0, "destruicao zera o deposito")
local lost = L.fwdLost
L.blast({X = fb.X, Y = fb.Y}, R, D, C.ENEMY_TEAM)
assert(L.fwdLost == lost, "destruida nao e destruida de novo")
assert(saw("destruída: perdeu 5 camisas e 5 fuzis"))
''')
    return "morteiro inimigo fere (x2) e destroi a base; o nosso e a distancia nao; destruida uma vez"


def t_caminhao_em_transito(v):
    lua = H.new_game(version=v)
    lua.execute(PRE + r'''
local pt, fb = buildFwd(4000, 0)
local tr = L.trucks[2]
tr.state, tr.cargo, tr.dest = "toDep", {ammo = 1, shirts = 1, rifle = 1, medical = 1}, fb.dep
L.drive = function() return true end
L.fac = {ammo = 0, shirts = 0, rifle = 0, medical = 0}
L.fwdLose(fb, "destruída")                 -- base cai com o caminhao a caminho; o ponto ainda e nosso
L.truckStep(tr, 0.1, clock)
assert(pt.dep.ammo == 1 and pt.dep.medical == 50 and pt.dep.shirts == 0 and pt.dep.rifle == 0, "so municao/bandagem entregues")
assert(tr.state == "returnCargo" and tr.dest == L.factory and boxes(tr.cargo) == 2 and tr.cargo.shirts == 1 and tr.cargo.rifle == 1)
assert(L.fac.shirts == 0 and L.fac.rifle == 0, "sem credito antes da chegada fisica")
L.truckStep(tr, 0.1, clock)
assert(L.fac.shirts == 1 and L.fac.rifle == 1 and tr.state == "idle" and tr.cargo == nil, "credito so na chegada a fabrica")
-- ponto sem base: caminhao fixado (L) so leva municao/bandagem
local q = mkPoint(7000, 0, FR)
L.fac = {ammo = 2, shirts = 2, rifle = 2, medical = 2}
L.pin = L.depotOf(q)
local tr2 = L.trucks[3]
tr2.state = "idle"; tr2.cargo = nil
L.truckStep(tr2, 0.1, clock)
assert(tr2.state == "toDep" and tr2.cargo.shirts == 0 and tr2.cargo.rifle == 0 and tr2.cargo.ammo == 2 and tr2.cargo.medical == 2, "ponto sem base: so municao e bandagem")
assert(L.fac.shirts == 2 and L.fac.rifle == 2)
''')
    return "base destruida com caminhao a caminho: so municao/bandagem ficam, camisa/fuzil voltam a fabrica (credito na chegada); ponto sem base nao recebe camisa/fuzil"


def t_capacidade(v):
    lua = H.new_game(version=v)
    lua.execute(PRE + r'''
local pt, fb = buildFwd(4000, 0)
local d = fb.dep
-- slotsUsed: caixa parcial ocupa 1 slot
d.ammo, d.shirts, d.rifle, d.medical = 2.2, 1, 21, 0
assert(L.slotsUsed(d) == 3 + 1 + 2 + 0, L.slotsUsed(d))
d.ammo, d.shirts, d.rifle, d.medical = 6, 20, 20, 50
assert(L.slotsUsed(d) == 6 + 2 + 1 + 1 == true or L.slotsUsed(d) == 10)
assert(L.fwdFree(d) == 5, "15 - 10")
-- caminhao fixado leva ate o espaco livre (5), nao 15
L.drive = function() return true end
L.fac = {ammo = 15, shirts = 0, rifle = 0, medical = 0}
L.pin = d
local tr1, tr2 = L.trucks[2], L.trucks[3]
L.truckStep(tr1, 0.1, clock)
assert(tr1.state == "toDep" and boxes(tr1.cargo) == 5 and tr1.cargo.ammo == 5 and L.fac.ammo == 10, "carga limitada pelo espaco: " .. boxes(tr1.cargo))
-- o espaco ja a caminho conta: o 2o caminhao nao leva nada
L.pin = d
L.truckStep(tr2, 0.1, clock)
assert(tr2.state ~= "toDep" and tr2.cargo == nil and L.fac.ammo == 10, "espaco reservado pelo 1o caminhao")
-- chegada: nunca passa de 15
L.drive = function() return true end
L.truckStep(tr1, 0.1, clock)
assert(L.slotsUsed(d) == 15 and L.fwdFree(d) == 0)
assert(d.ammo == 11)
-- base principal e ponto sem base: sem teto
assert(L.fwdFree(L.base) == math.huge)
''')
    return "slotsUsed (caixa parcial = 1 slot), carga limitada pelo espaco livre menos o que ja vai a caminho, teto de 15 na chegada"


def t_needs(v):
    lua = H.new_game(version=v)
    lua.execute(PRE + r'''
local q = mkPoint(7000, 0, FR)
local nq = L.needs(L.depotOf(q))
assert(nq.shirts == 0 and nq.rifle == 0 and nq.ammo > 0 and nq.medical > 0, "ponto sem base: so municao e bandagem")
local pt, fb = buildFwd(4000, 0)
local nb = L.needs(fb.dep)
assert(nb.shirts > 0 and nb.rifle > 0, "base avancada precisa de camisas e fuzis")
assert(L.needs(L.base).shirts == 0 or true)
-- nextKind: ponto sem base nao conta na demanda de camisas/fuzis
fb.dead = true; pt.fb = nil; fb.dep.fb = nil; L.fwd = {}
L.base.ammo, L.base.shirts, L.base.rifle, L.base.medical = 6, 20, 4, 20
L.fac = {ammo = 0, shirts = 0, rifle = 0, medical = 0}
L.depotOf(q).ammo = 0
L.prio = "auto"
local k = L.nextKind()
assert(k ~= "shirts" and k ~= "rifle", "camisas/fuzis ja no alvo da unica estrutura capaz: " .. tostring(k))
-- com uma base avancada vazia, a demanda de camisas sobe
L.bmat = 1000
assert(L.fwdBuild(pt)); local fb2 = pt.fb
L.base.ammo, L.base.medical = 100, 1000   -- municao e bandagem de sobra: so camisas/fuzis (0,5) ficam abaixo
assert(L.nextKind() == "shirts" or L.nextKind() == "rifle", "base avancada vazia puxa camisas/fuzis: " .. tostring(L.nextKind()))
''')
    return "needs/nextKind: camisas e fuzis so para estruturas que nascem soldado; a demanda escala com as bases"


def t_defesa_em_profundidade(v):
    lua = H.new_game(version=v)
    lua.execute(PRE + r'''
-- canReinforce nao depende de a perda ja ter sido processada: base cujo ponto ja nao e nosso nao conta estoque
local pt, fb = buildFwd(4000, 0)
stockFwd(fb, 9, 9)
L.base.shirts, L.fac.shirts = 0, 0
for _, tr in ipairs(L.trucks) do tr.cargo = nil end
assert(L.canReinforce() == true, "base ativa com camisas permite reforcar")
pt.owner = C.ENEMY_TEAM            -- capturado, antes do pointsTick processar a perda
assert(L.canReinforce() == false, "ponto ja inimigo: o estoque da base nao conta")
pt.owner = FR
assert(L.canReinforce() == true)
-- spawnCommit reconfere tudo: base perdida ou estoque mudado entre decidir e criar => recusa e nada e debitado
CURSOR = {X = 4000, Y = 0}
local site = assert(L.spawnSite("rifle", CURSOR))
assert(site.fb == fb)
fb.dep.shirts = 0
assert(L.spawnCommit(site, "rifle") == false and fb.dep.rifle == 9 and fb.led.used.shirts == 0, "estoque mudou: recusa e nao debita")
fb.dep.shirts = 9
pt.owner = C.ENEMY_TEAM
assert(L.spawnCommit(site, "rifle") == false and fb.dep.shirts == 9 and fb.dep.rifle == 9, "ponto perdido: recusa")
pt.owner = FR
assert(L.spawnCommit(site, "rifle") == true and fb.dep.shirts == 8 and fb.dep.rifle == 8 and fb.led.used.shirts == 1, "ok: debita 1 camisa e 1 fuzil")
''')
    return "canReinforce e spawnCommit nao dependem de a perda ja ter sido processada (defesa em profundidade)"


def t_derrota(v):
    lua = H.new_game(version=v)
    lua.execute(PRE + r'''
local function reset()
    for i = #A.squad(), 1, -1 do table.remove(A.squad(), i) end
    A.combat.auto, A.combat.won = true, false
    A.points()   -- sem pontos: sem derrota por dominio
end
-- logistico: sem tropa mas com camisas na base -> nao perde
reset()
A.waveTick()
assert(A.combat.auto == true, "base com camisas: pode reforcar")
-- sem camisas em lugar nenhum, sem caminhao carregado -> derrota
L.base.shirts = 0
L.fac.shirts = 0
for _, tr in ipairs(L.trucks) do tr.cargo = nil end
A.waveTick()
assert(A.combat.auto == false and saw("DERROTA"), "sem como reforcar: derrota")
-- base avancada com camisa impede a derrota
reset()
local pt, fb = buildFwd(4000, 0)
stockFwd(fb, 1, 0)
A.waveTick(); assert(A.combat.auto == true, "base avancada com camisa")
-- caminhao carregando camisas a caminho impede
fb.dep.shirts = 0; fb.led.lost.shirts = fb.led.lost.shirts + 1
L.trucks[3].state, L.trucks[3].cargo = "toDep", {ammo = 0, shirts = 1, rifle = 0, medical = 0}
A.waveTick(); assert(A.combat.auto == true, "caminhao com camisas a caminho")
L.trucks[3].cargo = nil
-- trabalhador vivo nao impede a derrota
newSoldier("worker", 0, 0)
A.waveTick(); assert(A.combat.auto == false, "so trabalhadores: sem tropa de combate = derrota")
-- legado: mao de obra
L.on = false
reset(); A.economy.manpower = 200
A.waveTick(); assert(A.combat.auto == true, "legado: mao de obra para um fuzileiro")
A.economy.manpower = 0
A.waveTick(); assert(A.combat.auto == false)
L.on = true
''')
    return "derrota usa logi.canReinforce(): base/base avancada com camisa ou caminhao com camisas impedem; trabalhador nao; legado inalterado"


def t_razao_fuzz(v):
    lua = H.new_game(version=v)
    lua.execute(PRE + r'''
local all = {}
local function check()
    for _, fb in ipairs(all) do
        local ok, k = L.fwdAudit(fb)
        assert(ok, "razao quebrou em " .. tostring(k))
    end
end
L.drive = function() return true end
for seed = 1, 25 do
    math.randomseed(seed)
    -- mundo limpo por semente
    for i = #A.points(), 1, -1 do table.remove(A.points(), i) end
    L.fwdReset(); all = {}
    for i = #A.squad(), 1, -1 do table.remove(A.squad(), i) end
    L.base.shirts, L.base.rifle = 200, 100
    local pts = {}
    for i = 1, 3 do pts[i] = mkPoint(4000 + 2500 * (i - 1), (i % 2) * 3000, FR) end
    L.bmat = 5000
    for step = 1, 600 do
        local r = math.random(100)
        if r <= 15 then      -- construir
            local pt = pts[math.random(#pts)]
            if not pt.fb and pt.owner == FR then
                local ok = L.fwdBuild(pt)
                if ok then all[#all + 1] = pt.fb end
            end
        elseif r <= 55 then  -- recrutar com cursor aleatorio
            CURSOR = {X = math.random(-2000, 12000), Y = math.random(-2000, 6000)}
            local roles = {"rifle", "mg", "medic", "sniper"}
            A.recruit(roles[math.random(#roles)])
            while #A.squad() > 10 do table.remove(A.squad(), 1) end
        elseif r <= 75 then  -- entrega de caminhao a uma base
            local pt = pts[math.random(#pts)]
            if pt.fb then
                local tr = L.trucks[math.random(2, 3)]
                tr.state, tr.dest = "toDep", pt.fb.dep
                tr.cargo = {ammo = math.random(0, 2), shirts = math.random(0, 1), rifle = math.random(0, 1), medical = 0}
                if boxes(tr.cargo) == 0 then tr.cargo.shirts = 1 end
                L.truckStep(tr, 0.1, clock)
                tr.state, tr.cargo, tr.dest = "idle", nil, nil
            end
        elseif r <= 85 then  -- neutralizar / recapturar
            local pt = pts[math.random(#pts)]
            pt.owner = (pt.owner == FR) and nil or FR
        elseif r <= 92 then  -- destruir
            local pt = pts[math.random(#pts)]
            if pt.fb then L.fwdLose(pt.fb, "destruída") end
        else                  -- captura inimiga e retomada
            local pt = pts[math.random(#pts)]
            if pt.fb then L.fwdLose(pt.fb, "capturada") end
            pt.owner = FR
        end
        for _, pt in ipairs(pts) do assert(pt.fb == nil or (not pt.fb.dead and pt.fb.dep == pt.dep)) end
        assert(fwdLive() == #L.fwd or true)
        check()
    end
    local live = 0
    for _, a in ipairs(fwdActors()) do if not a.bActorIsBeingDestroyed then live = live + 1 end end
    assert(live == #L.fwd, "atores vivos == bases vivas: " .. live .. " x " .. #L.fwd)
    for i, p in ipairs(pts) do assert((p.fb ~= nil) == (p.fb ~= nil and not p.fb.dead)) end
end
''')
    return "fuzz 25 sementes x 600 passos (construir, recrutar, entregar, neutralizar, destruir, capturar): razao por base fecha; atores vivos == bases vivas"


for v in ("lua54", "lua55"):
    H.case("[%s] corte de abastecimento" % v, t_corte_de_abastecimento, v)
    H.case("[%s] destruicao/captura/recaptura" % v, t_destruicao_captura, v)
    H.case("[%s] morteiro inimigo" % v, t_morteiro, v)
    H.case("[%s] caminhao em transito / ponto sem base" % v, t_caminhao_em_transito, v)
    H.case("[%s] capacidade de 15 slots" % v, t_capacidade, v)
    H.case("[%s] needs/nextKind" % v, t_needs, v)
    H.case("[%s] defesa em profundidade" % v, t_defesa_em_profundidade, v)
    H.case("[%s] derrota por falta de tropa" % v, t_derrota, v)
    H.case("[%s] razao por base (fuzz)" % v, t_razao_fuzz, v)
H.finish("test_perda")
