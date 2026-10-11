"""VARIANTE v2 (acabamento) de ia_logistica/test_ia_logistica.py contra build_patch_v2 (IA calibrada: free 5, trip 20,
want 4/20; eRestore com motivo; versao futura do elogi). Mesmos testes, NENHUMA expectativa precisou mudar (as que
dependem do piso leem E.free do proprio CFG); so caminhos/imports (diffs/test_ia_logistica_v2.diff).

Testes offline da IA_LOGISTICA sobre o main.lua candidato COMPLETO executado em memoria (lupa).

$env:PYTHONPATH='D:/tools/pylibs'; python dados/paralel/ia_logistica/acabamento/test_ia_logistica_v2.py
Roda tudo duas vezes: main+IA e main+ECONOMIA+IA (ordem declarada). Substitui so fronteiras de engine:
spawnEnemies/waveSpawnPoint (soldados falsos), SpawnActor/LoadAsset (caminhao falso) e, num teste, logi.drive.
NAO prova fisica Unreal, rota real, LOS, equilibrio de combate nem desempenho: isso e gate do laboratorio.
"""
import re
import sys
from pathlib import Path
from lupa import LuaRuntime

HERE = Path(__file__).resolve().parent
ROOT = HERE.parents[3]
sys.dont_write_bytecode = True
sys.path.insert(0, str(HERE))
from build_patch_v2 import build, stacked  # noqa: E402

# ---- custos reais do jogo (dados/custos_do_jogo.txt), conferidos contra CFG do candidato ----
COSTS = ROOT.joinpath("dados/custos_do_jogo.txt").read_text(encoding="utf-8")


def row(name):
    m = re.search(r"^%s \| (.*)$" % re.escape(name), COSTS, re.M)
    assert m, name
    return m.group(1)


ammo = re.match(r"custo=Clothx(\d+) qtd=(\d+) tempo=(\d+)", row("RifleAmmo")).groups()
shirts = re.match(r"custo=Clothx(\d+) qtd=(\d+) tempo=(\d+)", row("SoldierSupplies")).groups()
truck = re.match(r"vida=(\d+) custo=Clothx(\d+) .*carga=(\d+)", row("TruckC")).groups()
GAME = dict(ammo_bmat=int(ammo[0]), ammo_time=int(ammo[2]), shirts_bmat=int(shirts[0]), shirts_units=int(shirts[1]),
            shirts_time=int(shirts[2]), truck_hp=int(truck[0]), truck_cost=int(truck[1]), truck_cap=int(truck[2]))

orders = ROOT.joinpath("tools/test_orders.py").read_text(encoding="utf-8")
a = orders.index("lua.execute('''") + len("lua.execute('''")
SCAFFOLD = orders[a:orders.index("''')", a)]

HARNESS = '''
return {logi=logi, CFG=CFG, combat=combat, ai=ai, sv=sv, waveTick=waveTick, squad=squad, points=points, economy=economy,
  enemies=function() return enemies end,
  clearEnemies=function() for i=#enemies,1,-1 do table.remove(enemies,i) end end,
  setSpawn=function(fn) spawnEnemies=fn end,
  setWavePoint=function(fn) waveSpawnPoint=fn end,
  setAuthority=function(fn) isLocalAuthority=fn end,
  fakeSpawn=function(at, count, sameWave, quiet)
    if not sameWave then combat.wave = combat.wave + 1; combat.waveSize, combat.broken = 0, false end
    local made = math.max(0, count - (spawnFail or 0))
    for i = 1, made do table.insert(enemies, {fake=true}) end
    combat.waveSize = (combat.waveSize or 0) + made
    if not sameWave then combat.lastSpawn = {X=at.X, Y=at.Y, Z=0} end
  end}
'''

BODY = r'''
local A = api
local L, C, combat = A.logi, A.CFG, A.combat
local G = game
local E = C.ECHAIN
local function ok() local good, why = L.eAudit(); assert(good, why); return true end
local function truckActor(x, y)
    return {position={X=x,Y=y,Z=0}, IsValid=function() return true end,
        K2_GetActorLocation=function(self) return self.position end,
        K2_SetActorLocation=function(self,p) self.position=p end, K2_SetActorRotation=function() end,
        SetActorHiddenInGame=function(self,h) self.hidden=h end, SetActorEnableCollision=function() end,
        K2_DestroyActor=function(self) self.destroyed=true end}
end
LoadAsset = function() return {IsValid=function() return true end} end
mockSpawnActor = function(_, p) return truckActor(p.X, p.Y) end
A.sv.clear = function() end
local realDrive = L.drive
local function setup()
    L.reset()
    L.on, L.prio, L.salvage, L.bmat, L.made, L.job, L.t = true, "auto", 0, 0, 0, nil, nil
    L.fac = {ammo=0, shirts=0, rifle=0, medical=0}
    L.base = {name="base", X=0, Y=0, Z=0, ammo=6, shirts=30, rifle=0, medical=0}
    L.factory, L.field, L.refinery = {name="fábrica", X=-3000, Y=0, Z=0}, {X=-5000, Y=0, Z=0}, {X=-4000, Y=0, Z=0}
    L.trucks, L.drive = {}, realDrive
    combat.auto, combat.mode, combat.wave, combat.convoys, combat.convoysCut = true, nil, 0, 0, 0
    combat.lastSpawn, combat.nextWaveAt, combat.won = {X=4000, Y=0, Z=0}, nil, false
    L.convoyT = 1e9  -- tests dispatch explicitly unless a scenario opens the timer
    spawnFail = 0
    for i=#A.squad,1,-1 do table.remove(A.squad,i) end
    A.clearEnemies()
    L.eReset()
end
local function tick(n, dt) for _ = 1, n do clock = clock + dt; L.convoyTick(dt, clock); ok() end end
local function units(c) return (c.ammo or 0) + (c.shirts or 0) * L.eUnits("shirts") end
local function total(k) return L.eHave(k) + L.en.led.used[k] + L.en.led.lost[k] end

-- 1. Custos reais do jogo (sem custo zero por schema) e contrato da frota.
assert(C.LOGI.recipes.ammo.bmat == G.ammo_bmat and C.LOGI.recipes.ammo.time == G.ammo_time)
assert(C.LOGI.recipes.shirts.bmat == G.shirts_bmat and C.LOGI.recipes.shirts.units == G.shirts_units and C.LOGI.recipes.shirts.time == G.shirts_time)
assert(C.LOGI.truckCost == G.truck_cost and C.ECONVOY.hp == G.truck_hp and C.LOGI.cap == G.truck_cap)
assert(E.trucks == C.LOGI.supply and C.ECONVOY.cargo0 == nil and C.ECONVOY.perWave == nil)

-- 2. Partida nova: estoque de cenario entra no razao como "inicial"; nada mais existe.
setup()
assert(L.en.front.ammo == E.front0.ammo and L.en.front.shirts == E.front0.shirts and L.en.bmat == E.bmat0 and ok())
assert(combat.cargo == math.min(E.front0.shirts, math.floor(E.front0.ammo * C.LOGI.reloads)))

-- 3. Fail-closed: receita sem custo positivo recusa a cadeia; nenhuma producao, nenhum comboio.
local saved = C.LOGI.recipes.ammo.bmat
C.LOGI.recipes.ammo.bmat = 0
setup()
assert(L.en.err and L.en.err:find("ammo"))
L.convoyT = 0; tick(200, 0.5)
assert(L.en.led.spent == 0 and L.en.fac.ammo + L.en.fac.shirts == 0 and #L.foes == 0 and combat.convoys == 0)
assert(L.eHud():find("recusada"))
C.LOGI.recipes.ammo.bmat = saved
C.LOGI.recipes.shirts.time = nil
setup(); assert(L.en.err); C.LOGI.recipes.shirts.time = G.shirts_time

-- 4. Producao: sucata por viagem -> refinaria 2:1 -> receita debitada ao iniciar, caixa so ao concluir.
setup()
local bmat0 = L.en.bmat
tick(1, 0.5)
assert(L.en.job and L.en.led.spent == C.LOGI.recipes[L.en.job.kind].bmat and L.en.bmat < bmat0)
local job = L.en.job.kind
local made0 = L.en.led.made[job]
tick(math.ceil(L.en.job.total / 0.5) + 1, 0.5)
assert(L.en.led.made[job] == made0 + L.eUnits(job) and L.en.fac[job] >= 1)
tick(math.ceil(E.trip / 0.5) + 1, 0.5); assert(L.en.led.salv > 0 and L.en.led.refined > 0)
tick(2000, 0.5)  -- estoque cheio: a fabrica para (regra 2x alvo do jogador), sem passar disso
for _, k in ipairs(E.kinds) do assert(L.eHave(k) <= 2 * E.want[k] + 15 * L.eUnits(k), k) end
local spentFull = L.en.led.spent
tick(200, 0.5); assert(L.en.led.spent == spentFull, "factory must idle when everything is >= 2x the target")

-- 5. Comboio: sem caminhao livre, sem carga ou com spawn falho, nada sai e nada e debitado.
setup()
assert(not L.convoySpawn(clock) and #L.foes == 0)           -- retaguarda vazia: sem comboio fantasma
tick(120, 0.5)
local rear = L.en.fac.ammo + L.en.fac.shirts
assert(rear > 0)
L.en.front.ammo, L.en.front.shirts = 0, 0                   -- (ajuste de cenario: registra como consumo)
L.en.led.used.ammo, L.en.led.used.shirts = L.en.led.used.ammo + E.front0.ammo, L.en.led.used.shirts + E.front0.shirts
ok()
local ready = L.en.ready
L.en.ready = 0
assert(not L.convoySpawn(clock) and L.en.fac.ammo + L.en.fac.shirts == rear)
L.en.ready = ready
mockSpawnActor = function() return nil end
assert(not L.convoySpawn(clock) and L.en.fac.ammo + L.en.fac.shirts == rear and L.en.ready == ready)
mockSpawnActor = function(_, p) local t = truckActor(p.X, p.Y); t.bActorIsBeingDestroyed = true; return t end
assert(not L.convoySpawn(clock) and L.en.fac.ammo + L.en.fac.shirts == rear and #L.foes == 0)
mockSpawnActor = function(_, p) return truckActor(p.X, p.Y) end
assert(L.convoySpawn(clock) and #L.foes == 1 and L.en.ready == ready - 1 and ok())
local cv = L.foes[1]
local carried = units(cv.cargo)
assert(carried > 0 and L.en.fac.ammo + L.en.fac.shirts == rear - cv.cargo.ammo - cv.cargo.shirts)
assert(cv.cargo.ammo + cv.cargo.shirts <= C.LOGI.cap)

-- 6. Chegada credita a frente uma unica vez; o caminhao volta a frota.
local front0 = L.en.front.ammo + L.en.front.shirts
local guard = 0
while cv.cargo do tick(1, 0.5); guard = guard + 1; assert(guard < 400) end
assert(math.abs(L.en.front.ammo + L.en.front.shirts - front0 - carried) < 1e-9 and L.en.delivered == 1)
tick(400, 0.5)
assert(#L.foes == 0 and L.en.ready == ready and L.en.delivered == 1)
assert(math.abs(L.en.front.ammo + L.en.front.shirts - front0 - carried) < 1e-9, "no double delivery")

-- 7. Destruicao: carga perdida uma vez (tiro + morteiro depois), frente nao recebe, reconstrucao paga bmat.
setup(); tick(200, 0.5)
L.en.front.ammo, L.en.front.shirts = 0, 0
L.en.led.used.ammo, L.en.led.used.shirts = L.en.led.used.ammo + E.front0.ammo, L.en.led.used.shirts + E.front0.shirts
assert(L.convoySpawn(clock))
cv = L.foes[1]
carried = {ammo=cv.cargo.ammo, shirts=cv.cargo.shirts * L.eUnits("shirts")}
tick(4, 0.5)
local lost0 = {ammo=L.en.led.lost.ammo, shirts=L.en.led.lost.shirts}
assert(L.hit(cv, 1e9, clock) and cv.state == "dead" and not cv.cargo)
assert(not L.hit(cv, 1e9, clock))                                   -- morto nao morre de novo
L.blast({X=cv.X, Y=cv.Y, Z=0}, 500, 1e9, C.FRIENDLY_TEAM)            -- morteiro no mesmo lugar
assert(L.en.led.lost.ammo == lost0.ammo + carried.ammo and L.en.led.lost.shirts == lost0.shirts + carried.shirts)
assert(L.en.front.ammo == 0 and L.en.front.shirts == 0 and #L.en.rebuild == 1 and combat.convoysCut == 1 and ok())
tick(1, 0.5); assert(#L.foes == 0 and ok())
-- reconstrucao: so depois de LOGI.rebuild s e com LOGI.truckCost bmat
local spent = L.en.led.spent
L.en.bmat = 0; L.en.led.bmat0 = L.en.led.bmat0 - (L.en.led.bmat0 + L.en.led.refined / C.LOGI.ratio - L.en.led.spent)  -- zera bmat no razao
ok()
L.en.salvage, L.en.tripT = 0, 1e9; L.en.led.salv = L.en.led.refined
ok()
tick(2 * C.LOGI.rebuild, 0.5)
assert(#L.en.rebuild == 1 and L.en.ready == E.trucks - 1, "no bmat: truck waits")
L.en.tripT = 0
local guard2 = 0
while #L.en.rebuild > 0 do tick(1, 0.5); guard2 = guard2 + 1; assert(guard2 < 2000) end
assert(L.en.ready == E.trucks and L.en.led.spent >= spent + C.LOGI.truckCost and ok())

-- 8. Ator invalido no caminho: perda explicita, nunca entrega.
setup(); tick(200, 0.5)
L.en.front.ammo, L.en.front.shirts = 0, 0
L.en.led.used.ammo, L.en.led.used.shirts = L.en.led.used.ammo + E.front0.ammo, L.en.led.used.shirts + E.front0.shirts
assert(L.convoySpawn(clock)); cv = L.foes[1]
local inTransit = units(cv.cargo)
cv.pawn.bActorIsBeingDestroyed = true
tick(1, 0.5)
assert(#L.foes == 0 and L.en.front.ammo + L.en.front.shirts == 0 and L.en.led.lost.ammo + L.en.led.lost.shirts == inTransit and ok())

-- 9. Rota ausente (contrato ESTRADAS): parado com carga, volta depois de ECHAIN.stuck s, credito so na chegada.
setup(); tick(200, 0.5)
L.en.front.ammo, L.en.front.shirts = 0, 0
L.en.led.used.ammo, L.en.led.used.shirts = L.en.led.used.ammo + E.front0.ammo, L.en.led.used.shirts + E.front0.shirts
assert(L.convoySpawn(clock)); cv = L.foes[1]
local boxes = cv.cargo.ammo + cv.cargo.shirts
local rearNow = L.en.fac.ammo + L.en.fac.shirts
L.drive = function(tr) tr.routeStatus = "rota_ausente"; return false end
tick(math.floor(E.stuck / 0.5) - 2, 0.5)
assert(cv.state == "toFront" and cv.cargo and L.en.front.ammo + L.en.front.shirts == 0)
tick(4, 0.5)
assert(cv.state == "back" and cv.cargo and L.en.fac.ammo + L.en.fac.shirts >= rearNow and ok())
local rearBack = L.en.fac.ammo + L.en.fac.shirts
L.drive = function() return true end
tick(1, 0.5)
assert(#L.foes == 0 and L.en.ready == E.trucks and L.en.fac.ammo + L.en.fac.shirts >= rearBack + boxes and ok())
L.drive = realDrive

-- 10. Onda: guarnicao gratuita + pagos ate o que a frente equipa; debito so do que nasceu.
setup()
local can = (L.eSoldiers())
local w = combat.wave
assert(L.waveCut(2) == 2 and L.en.waves[1].paid == 0)                 -- onda pequena: so a guarnicao
L.eCommit(2)
assert(L.waveCut(50) == E.free + can and L.en.waves[2].short == 50 - E.free - can)
assert(L.en.waves[2].limit == "shirts" or L.en.waves[2].limit == "ammo")
local frontBefore = {ammo=L.en.front.ammo, shirts=L.en.front.shirts}
assert(L.eCommit(E.free + can) == 0, "no new wave opened (spawn refused): nothing is debited")
assert(L.en.front.ammo == frontBefore.ammo and L.en.front.shirts == frontBefore.shirts)
L.waveCut(E.free + 4); combat.wave = w + 1
assert(L.eCommit(E.free + 1) == 1, "only paid soldiers that were actually spawned are debited")
assert(L.en.front.shirts == frontBefore.shirts - 1 and ok())
-- wiring real: waveTick -> logi.waveCut -> spawn -> logi.eCommit
setup()
A.setSpawn(A.fakeSpawn); A.setWavePoint(function() return {X=4000, Y=0, Z=0} end)
for _ = 1, 6 do table.insert(A.squad, {}) end
combat.wave = 0
A.waveTick(); clock = clock + 100; A.waveTick()
local rec = L.en.waves[#L.en.waves]
assert(combat.wave == 1 and #A.enemies() == rec.asked - rec.short and rec.sent == #A.enemies())
assert(L.en.led.used.shirts == rec.paid * E.shirts and ok())
A.clearEnemies()
spawnFail = 100  -- engine recusa todos: nada consumido
local used = L.en.led.used.shirts
A.waveTick(); clock = clock + 100; A.waveTick()
assert(#A.enemies() == 0 and L.en.led.used.shirts == used and ok())
spawnFail = 0

-- 11. Reforco pelos pontos (ai.tick): limitado pela frente e pago depois do spawn.
setup()
A.setSpawn(A.fakeSpawn)
table.insert(A.points, {X=3000, Y=0, Z=0, name="B", owner=C.ENEMY_TEAM, prog=-1})
table.insert(A.enemies(), {fake=true})
A.ai.reset(); A.ai.mp, A.ai.nextT = 200, 0
L.en.led.used.ammo = L.en.led.used.ammo + L.en.front.ammo; L.en.front.ammo = 0  -- frente sem municao
A.ai.tick()
assert(#A.enemies() == 1 and A.ai.sent == 0 and ok(), "no ammo at the front: no reinforcement")
L.en.front.ammo = 1; L.en.led.used.ammo = L.en.led.used.ammo - 1   -- devolve 1 caixa ao estoque (6 cargas)
ok()
A.ai.tick()
local sent = A.ai.sent
assert(sent >= 2 and sent <= 3 and #A.enemies() == 1 + sent and L.en.led.used.shirts == sent * E.shirts and ok())
A.clearEnemies(); for i=#A.points,1,-1 do table.remove(A.points,i) end

-- 12. Assalto e partida sem logistica: comportamento antigo (abstrato), nada consumido.
setup()
combat.mode = "assault"
assert(L.waveCut(9) == 9 and L.eAfford(3) == 3 and L.eConsume(3) == 0 and not L.eActive())
combat.mode = nil
L.reset()
assert(L.waveCut(9) == 9 and L.eAfford(3) == 3 and L.eConsume(3) == 0 and L.eHud() == "")
assert(L.eAudit())

-- 13. Save/continue: transito vira pendente, restauracao substitui (nao soma), repetir nao duplica,
-- reenvio usa a carga pendente, save invalido/legado recomeca do cenario com aviso.
setup(); tick(200, 0.5)
L.en.front.ammo, L.en.front.shirts = 0, 0
L.en.led.used.ammo, L.en.led.used.shirts = L.en.led.used.ammo + E.front0.ammo, L.en.led.used.shirts + E.front0.shirts
assert(L.convoySpawn(clock)); cv = L.foes[1]
local onRoad = {ammo=cv.cargo.ammo, shirts=cv.cargo.shirts}
local snap = A.sv.parse("return " .. A.sv.ser(L.eSnapshot()))   -- mesma serializacao do save
local wholeSave = A.sv.collect()
assert(wholeSave.elogi and wholeSave.elogi.pending.ammo == onRoad.ammo, "sv.collect carries the enemy chain")
assert(snap and snap.pending.ammo == onRoad.ammo and snap.pending.shirts == onRoad.shirts and snap.ready == E.trucks)
local totals = {ammo=total("ammo"), shirts=total("shirts")}
setup()                                   -- logi.start faz reset + estado de cenario
assert(L.eRestore(snap) and ok())
assert(L.en.pending.ammo == onRoad.ammo and L.en.ready == E.trucks and total("ammo") == totals.ammo and total("shirts") == totals.shirts)
assert(L.eRestore(snap) and total("ammo") == totals.ammo, "repeated restore replaces, never adds")
assert(L.convoySpawn(clock) and L.en.pending == nil and L.foes[1].cargo.ammo == onRoad.ammo and ok())
local good = A.sv.parse("return " .. A.sv.ser(L.eSnapshot()))
setup()
local fresh = L.en
good.front.shirts = good.front.shirts + 5                      -- carga criada a mao: o razao nao fecha
assert(not L.eRestore(good) and L.en == fresh and L.en.front.shirts == E.front0.shirts and ok())
good.front.shirts = good.front.shirts - 5; good.bmat = -1
assert(not L.eRestore(good) and ok())
good.bmat = 0; good.ready = E.trucks + 1
assert(not L.eRestore(good))
assert(not L.eRestore(nil) and L.en == fresh and ok())          -- save legado: recomeca do cenario, avisado
L.on = false; assert(not L.eRestore(snap))
-- wiring real: sv.load chama logi.restore e depois logi.eRestore(d.elogi)
setup()
local called = {}
local oldRead, oldReady, oldRestore, oldSvRestore = A.sv.read, L.ready, L.restore, A.sv.restore
A.setAuthority(function() return true end)
A.sv.read = function() return {v=1, map="HomeRegionW", logi={}, elogi=snap, wave=1} end
L.ready = function() return {} end
L.restore = function() called.restore = true; setup(); return true end
A.sv.restore = function() return 0 end
A.sv.load()
assert(called.restore and L.en.pending and L.en.pending.ammo == onRoad.ammo and ok())
A.sv.read, L.ready, L.restore, A.sv.restore = oldRead, oldReady, oldRestore, oldSvRestore

-- 14. Propriedade: sequencias aleatorias de producao, comboios, chegadas, tiros, morteiro, ator invalido,
-- ondas, reforcos, save/restore e troca de modo nunca criam nem duplicam carga, bmat, sucata ou caminhao.
for seed = 1, 25 do
    math.randomseed(seed)
    setup(); L.convoyT = 0
    for step = 1, 600 do
        local r = math.random()
        if r < 0.55 then tick(1, math.random() * 0.5)
        elseif r < 0.62 then L.convoySpawn(clock)
        elseif r < 0.68 and #L.foes > 0 then L.hit(L.foes[math.random(#L.foes)], math.random() * 1200, clock)
        elseif r < 0.70 and #L.foes > 0 then L.blast({X=L.foes[1].X, Y=L.foes[1].Y, Z=0}, 300, 2000, C.FRIENDLY_TEAM)
        elseif r < 0.72 and #L.foes > 0 then local p = L.foes[math.random(#L.foes)].pawn; if p then p.bActorIsBeingDestroyed = true end
        elseif r < 0.80 then
            L.waveCut(math.random(1, 16))
            if math.random() < 0.8 then combat.wave = combat.wave + 1 end
            L.eCommit(math.random(0, 16))
        elseif r < 0.85 then L.eConsume(L.eAfford(math.random(0, 3)), "reforço")
        elseif r < 0.88 then
            local s = A.sv.parse("return " .. A.sv.ser(L.eSnapshot()))
            for i=#L.foes,1,-1 do table.remove(L.foes,i) end          -- logi.reset: atores somem
            local why = select(2, L.eValid(s)); L.eReset(); assert(L.eRestore(s), tostring(why) .. " seed " .. seed .. " step " .. step)
        elseif r < 0.90 then combat.mode = (combat.mode == nil) and "assault" or nil
        elseif r < 0.92 then L.drive = (L.drive == realDrive) and function(tr) tr.routeStatus = "bloqueado"; return false end or realDrive
        end
        ok()
        for _, k in ipairs(E.kinds) do assert(L.en.front[k] >= -1e-9 and L.en.fac[k] >= 0) end
    end
    L.drive = realDrive; combat.mode = nil
end

-- 15. Partida completa por waveTick (cenarios deterministas) -> tabela de ondas para o relatorio.
function scenario(name, opt)
    math.randomseed(7)
    setup()
    A.setSpawn(A.fakeSpawn); A.setWavePoint(function() return {X=4000, Y=0, Z=0} end)
    for _ = 1, 6 do table.insert(A.squad, {}) end
    if opt.scarce then
        L.en.bmat, L.en.led.bmat0, L.en.tripT = 0, 0, 1e12
    end
    L.convoyT = clock + C.ECONVOY.first
    local t0, fightEnd = clock, nil
    for step = 1, opt.secs * 2 do
        clock = clock + 0.5
        L.tick()
        A.waveTick()
        if #A.enemies() > 0 and not fightEnd then fightEnd = clock + opt.fight end
        if fightEnd and clock >= fightEnd then A.clearEnemies(); fightEnd = nil end
        local cutNow = opt.cut and clock - t0 >= (opt.cutFrom or 0) and clock - t0 < (opt.cutTo or 1e12)
        if cutNow then
            for _, tr in ipairs(L.foes) do if tr.state == "toFront" and tr.cargo then L.hit(tr, 1e9, clock) end end
        end
        ok()
        if not combat.auto then break end
    end
    return L.en.waves, combat.won
end
'''

FINAL = r'''
local A = api
local L = A.logi
local out = {}
local res = {}
for _, sc in ipairs({
    {"controle", {secs=1500, fight=45}},
    {"interdicao total", {secs=1500, fight=45, cut=true}},
    {"interdicao 0-420 s, depois livre", {secs=1500, fight=45, cut=true, cutTo=420}},
    {"escassez (retaguarda sem bmat/sucata)", {secs=1500, fight=45, scarce=true}},
}) do
    local waves, won = scenario(sc[1], sc[2])
    local rows = {}
    for _, w in ipairs(waves) do rows[#rows + 1] = string.format("%d:%d/%d%s", w.wave, w.sent or -1, w.asked, w.byCut > 0 and ("[i" .. w.byCut .. "]") or "") end
    if DEBUG then for _, w in ipairs(waves) do print(string.format("  %s w%d front m%.2f c%g ghost m%.2f c%g short %d byCut %d", sc[1], w.wave, w.front.ammo, w.front.shirts, w.ghost.ammo, w.ghost.shirts, w.short, w.byCut)) end end
    out[#out + 1] = string.format("%-40s venceu=%s lost(m=%g,c=%g) convoys=%d cut=%d | ondas enviados/pedidos: %s", sc[1], tostring(won),
        L.en.led.lost.ammo, L.en.led.lost.shirts, A.combat.convoys or 0, A.combat.convoysCut or 0, table.concat(rows, " "))
    res[sc[1]] = {waves=waves, won=won, lost=L.en.led.lost.ammo + L.en.led.lost.shirts, cut=A.combat.convoysCut}
end
local TABLE = table.concat(out, string.char(10))
local function check(c, msg) if not c then error(tostring(msg) .. string.char(10) .. TABLE) end end
local ctl, cut, rec, sc = res["controle"], res["interdicao total"], res["interdicao 0-420 s, depois livre"], res["escassez (retaguarda sem bmat/sucata)"]
local function short(ws, from, to) local s = 0; for i = from or 1, math.min(to or #ws, #ws) do s = s + ws[i].short end; return s end
local function byCut(ws) local s = 0; for _, w in ipairs(ws) do s = s + w.byCut end; return s end
check(#ctl.waves >= 10 and ctl.won, "control match must reach the end")
check(short(ctl.waves) == 0, "uncut chain sustains every wave (calibration)")
check(cut.cut > 0 and cut.lost > 0 and short(cut.waves) > 0 and byCut(cut.waves) > 0, "interdiction must reach the front")
local lower = 0
for i = 1, math.min(#ctl.waves, #cut.waves) do if (cut.waves[i].sent or 0) < (ctl.waves[i].sent or 0) then lower = lower + 1 end end
check(lower >= 3, "interdicted waves are smaller than control waves at the same index")
check(short(rec.waves, 1, 6) > 0 and short(rec.waves, #rec.waves) == 0 and (rec.waves[#rec.waves].sent or 0) > (rec.waves[#rec.waves - 1].sent or 0), "front recovers after interdiction stops")
for _, w in ipairs(sc.waves) do check(w.sent >= math.min(w.asked, A.CFG.ECHAIN.free)) end
check(sc.waves[#sc.waves].sent == A.CFG.ECHAIN.free and #sc.waves >= 10, "scarcity: floor waves, the match goes on")
return table.concat(out, "\n")
'''


def run(label, transform):
    lua = LuaRuntime()
    lua.execute(SCAFFOLD)
    candidate = transform(ROOT.joinpath("mod/FoxholeRTS/Scripts/main.lua").read_text(encoding="utf-8"))
    api = lua.execute(candidate + HARNESS)
    lua.globals().api = api
    lua.globals().game = lua.table_from(GAME)
    real_print = print
    lua.globals().print = (lambda *a: real_print(*a) if a and str(a[0]).startswith("  ") else None)  # so a tabela de depuracao
    lua.execute(BODY)
    table = lua.execute(FINAL)
    print("== %s: PASS (custos do jogo, cenario, fail-closed, producao, comboio sem fantasma, entrega unica, "
          "perda unica + reconstrucao, ator invalido, rota ausente, onda/commit, reforco, assalto/sem logistica, "
          "save/continue, 25x600 passos aleatorios com razao fechado, partida completa)" % label)
    print(table)


run("main+IA", lambda s: build(s)[0])
run("main+ECONOMIA+IA", stacked)
print("PASS: test_ia_logistica (2 candidatos)")
