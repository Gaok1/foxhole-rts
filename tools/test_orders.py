"""Offline checks of the actual mod functions; requires lupa (no game or UE4SS).

Local setup: $env:PYTHONPATH='D:\\tools\\pylibs'; python tools/test_orders.py
Mocks check Lua decisions, NOT Unreal physics, hooks or keyboard integration.
"""
from pathlib import Path
from lupa import LuaRuntime

lua = LuaRuntime()
lua.execute('''
server, dedicated, menu = true, false, false
clock = 0
terrainZ = function() return 0 end
local w = {IsValid = function() return true end,
    GetAddress = function() return 1 end,
    GetFullName = function() return menu and "MainMenu" or "HomeRegionW" end}
w.SpawnActor = function(_, cls, l) return mockSpawnActor and mockSpawnActor(cls, l) or nil end
-- synthetic terrain: flat ground at Z=0 and a wall at X=500 for |Y| <= 1000
function crossesWall(a, b)
    if (a.X - 500) * (b.X - 500) > 0 or a.X == b.X then return false end
    local t = (500 - a.X) / (b.X - a.X)
    return math.abs(a.Y + t * (b.Y - a.Y)) <= 1000
end
local k = {IsServer = function() return server end,
    ExecuteConsoleCommand = function() end,
    IsDedicatedServer = function() return dedicated end,
    LineTraceSingle = function(_, _, a, b, _, _, _, _, hit)
        if a.X == b.X and a.Y == b.Y then
            local z = terrainZ(a.X, a.Y)
            if z == nil then return false end
            hit.ImpactPoint = {X=a.X, Y=a.Y, Z=z}
            hit.ImpactNormal = {X=0,Y=0,Z=1}
            hit.bStartPenetrating = false
            hit.Actor = {get=function() return {IsValid=function() return true end,
                GetClass=function() return {GetFName=function() return {ToString=function() return terrainClass or "Landscape" end} end} end} end}
            return true
        end
        return crossesWall(a, b)
    end,
    SphereTraceSingle = function(_, _, a, b) return crossesWall(a, b) end,
    CapsuleTraceSingle = function(_,_,a,b,r,h,ch,complex,ignore,debug,hit)
        assert(r==50 and h==90, "capsula de resgate deve cobrir CollisionCylinder real")
        hit.bStartPenetrating=rescueOccupied~=false; return rescueOccupied~=false end}
package.preload.UEHelpers = function() return {
    GetWorld = function() return w end,
    GetKismetSystemLibrary = function() return k end,
    GetPlayerController = function() return nil end,
    GetGameplayStatics = function() return {GetTimeSeconds = function() return clock end, GetRealTimeSeconds = function() return clock end,
        GetPlayerController = function() return nil end} end,
} end
Key = setmetatable({}, {__index = function(_, k) return k end})
ModifierKey = {SHIFT = "SHIFT", CONTROL = "CONTROL", ALT = "ALT"}
bindings = {}
function RegisterKeyBind(k, a, b)
    if type(a) == "function" then bindings[k] = a else bindings[a[1] .. "+" .. k] = b end
end
function ExecuteInGameThread(f) f() end
function LoopInGameThreadAfterFrames(_, f) frame = f end
function StaticFindObject() return nil end
function FindAllOf() return nil end
-- Never open the lab command channel while testing.
io.open = function() return nil end
''')
source = (Path(__file__).resolve().parents[1] / "mod/FoxholeRTS/Scripts/main.lua").read_text(encoding="utf-8")
# Same lexical scope, no production test API or copied implementation.
api = lua.execute(source + '''
return {squad=squad, rts=rts, selectGroup=selectGroup, logi=logi, move=issueMove, stop=stopSelected, recruit=recruit, economy=economy,
    selectAt=selectAt, selectBox=selectBox, suppression=suppression, suppress=suppress,
    attack=issueAttack, plan=planPath, planStart=planStart, planStep=planStep, pathTick=pathTick, routeTo=routeTo, build=buildAt, medicTick=medicTick,
    waveTick=waveTick, toggleWaves=toggleWaves, combat=combat,
    points=points, pointStep=pointStep, enemyObjective=enemyObjective, waveSpawnPoint=waveSpawnPoint,
    callMortar=callMortar, mortar=mortar, rank=rank, credit=credit, retreat=retreatSelected, queue=queueMove,
    setDifficulty=setDifficulty, CFG=CFG, S=S, fire=fire, resupply=resupply, ammoFrac=ammoFrac,
    dropCrate=dropCrate, supplyTick=supplyTick, digTrench=digTrench, ai=ai, sv=sv, foes=function() return enemies end, fort=fort,
    anim=anim, reap=reap, corpses=corpses, corpseTick=corpseTick, newGame=newGame, anchor=spawnAnchor}
''')
lua.globals().api = api
lua.execute('''
-- Simular a fronteira do quadro depois de cada entrada; fila assincrona tem teste proprio.
for key, callback in pairs(bindings) do
    bindings[key] = function(...)
        callback(...)
        if api.rts.drainGameQueue then api.rts.drainGameQueue() end
    end
end
''')
lua.execute('''
local function soldier(group, hp, valid, x, y)
    local cm = {stops=0, StopMovementImmediately=function(self) self.stops=self.stops+1 end}
    local pawn = {Health=hp, CharacterMovement=cm, vel={X=500, Y=0, Z=0}, consumed=0,
        IsValid=function() return valid end,
        K2_GetActorLocation=function() return {X=x or 0, Y=y or 0, Z=0} end,
        GetVelocity=function(self) return self.vel end,
        ConsumeMovementInputVector=function(self) self.consumed=self.consumed+1 end}
    cm.StopMovementImmediately = function(self) self.stops=self.stops+1; pawn.vel={X=0, Y=0, Z=0} end
    return {group=group, sel=(group == 1), pawn=pawn, target={X=99}, detour={}, stuckAt={}, lastMoveT=1}
end
local a, b = soldier(1, 100, true), soldier(2, 100, true)
local dead, invalid = soldier(1, 0, true), soldier(1, 100, false)
for _, m in ipairs({a,b,dead,invalid}) do table.insert(api.squad, m) end
bindings.END() -- inactive RTS: no keyboard action
assert(a.target and a.pawn.CharacterMovement.stops == 0)
api.rts.active = true
local labMap = api.CFG.LAB_MAP
api.CFG.LAB_MAP = "/Game/Maps/Master/DeadlandsHex"
assert(api.rts.isLabMap("World /Game/Maps/Master/DeadLandsHex.DeadLandsHex"))
assert(not api.rts.isLabMap("World /Game/Maps/Master/DeadLandsHexProxy.DeadLandsHexProxy"))
assert(not api.rts.isLabMap("World /Game/Maps/MainMenu.MainMenu"))
api.CFG.LAB_MAP = labMap
bindings.END()
assert(a.target == nil and a.detour == nil and a.stuckAt == nil and a.lastMoveT == nil)
assert(a.halted and a.pawn.CharacterMovement.stops == 1 and a.pawn.consumed == 1)
-- residual input re-accelerates a frictionless pawn: halt must brake again, not latch
a.pawn.vel = {X=0, Y=333, Z=0}
bindings.END()
assert(a.pawn.CharacterMovement.stops == 2)
bindings.END() -- already still: discards input, no extra brake
assert(a.pawn.CharacterMovement.stops == 2 and a.pawn.consumed == 3)
assert(b.target and dead.target and invalid.target)
assert(api.move({X=1000,Y=2000,Z=300}) == 1)
assert(a.target.X == 1000 and a.target.Y == 2000 and a.target.Z == 300)  -- alone: exactly on the goal
assert(b.target.X == 99)
for _, m in ipairs(api.squad) do m.sel = true end
assert(api.move({X=1000,Y=2000,Z=300}) == 2)
-- two: a line across the march direction, centred on the goal, 160 cm apart
local dx, dy = b.target.X - a.target.X, b.target.Y - a.target.Y
assert(math.abs(math.sqrt(dx * dx + dy * dy) - 160) < 1e-6)
assert(math.abs((a.target.X + b.target.X) / 2 - 1000) < 1e-6 and math.abs((a.target.Y + b.target.Y) / 2 - 2000) < 1e-6)
assert(math.abs(dx * 1000 + dy * 2000) < 1e-6)  -- perpendicular to (0,0) -> (1000,2000)
for _, mode in ipairs({"client", "dedicated", "menu"}) do
    server, dedicated, menu = mode ~= "client", mode == "dedicated", mode == "menu"
    local old = a.target
    assert(api.stop() == 0 and api.move({X=0,Y=0,Z=0}) == 0 and a.target == old)
    frame() -- must return before any gameplay calls (engine APIs intentionally absent)
end
server, dedicated, menu = true, false, false
assert(api.stop() == 2 and a.target == nil and b.target == nil)
assert(dead.pawn.CharacterMovement.stops == 0 and invalid.pawn.CharacterMovement.stops == 0)
for i=#api.squad,1,-1 do table.remove(api.squad,i) end
assert(api.stop() == 0 and api.move({X=0,Y=0,Z=0}) == 0)
-- Death contract: retire before native health notification replaces the mesh/AnimInstance.
local fallen = soldier(1, 0, true)
fallen.team = api.CFG.ENEMY_TEAM
fallen.moveDefaults = {friction=8, brake=2048, accel=2048}
fallen.pawn.CharacterMovement.GroundFriction = 0
fallen.pawn.CharacterMovement.BrakingDecelerationWalking = 0
fallen.pawn.CharacterMovement.MaxAcceleration = 20000
fallen.pawn.bIsInScopeMode = true
fallen.animAddr = 101
api.anim.units[101] = fallen
local notified, destroyed = 0, 0
local haloDestroyed = false
fallen.outline = {{IsValid=function() return true end, K2_DestroyActor=function() haloDestroyed=true end}}
fallen.pawn.Mesh = {SetRenderCustomDepth=function(_, on) assert(not on) end}
fallen.outlineParts = {fallen.pawn.Mesh}
fallen.pawn.Mesh.IsValid = function() return true end
fallen.pawn.OnRep_Health = function(self)
    assert(haloDestroyed and fallen.outline == nil, "outline must be destroyed before native death")
    assert(fallen.animAddr == nil and api.anim.units[101] == nil, "native death must not retain the animation cache")
    assert(self.vel.X == 0 and self.vel.Y == 0 and self.consumed == 1 and not self.bIsInScopeMode)
    assert(self.CharacterMovement.GroundFriction == 8 and self.CharacterMovement.BrakingDecelerationWalking == 2048)
    assert(self.CharacterMovement.MaxAcceleration == 2048)
    notified = notified + 1
end
fallen.pawn.K2_DestroyActor = function() destroyed = destroyed + 1 end
local casualties = {fallen}
assert(api.reap(casualties, "teste") == 1 and #casualties == 0 and notified == 1)
assert(#api.corpses == 1 and destroyed == 0)
api.anim.retire(fallen)
assert(notified == 1 and fallen.pawn.CharacterMovement.stops == 1, "death cleanup must run only once")
local staleInstance = {GetAddress=function() return 101 end}
setmetatable(staleInstance, {__newindex=function() error("writing animation after death") end})
api.anim.onUpdate({get=function() return staleInstance end})
fallen.aiming = true
table.insert(api.squad, fallen)
api.anim.nextPosture = nil
api.anim.postureTick()
assert(not fallen.pawn.bIsInScopeMode and not fallen.crouch, "posture tick must not write to a dead pawn")
table.remove(api.squad)
-- An old owner cannot remove a new unit whose AnimInstance address was recycled.
fallen.animAddr = 101
api.anim.units[101] = a
api.anim.untrack(fallen)
assert(api.anim.units[101] == a and fallen.animAddr == nil)
api.anim.units[101] = nil
api.corpseTick()
assert(destroyed == 0)
clock = clock + api.CFG.CORPSE_TTL + 0.1
api.corpseTick()
assert(destroyed == 1 and #api.corpses == 0)
local gone = soldier(1, 0, false)
gone.pawn.ConsumeMovementInputVector = function() error("touching invalid pawn") end
api.anim.retire(gone)
assert(gone.retired and gone.pawn.consumed == 0)
-- click/box selection: nearest living soldier within reach; empty click clears; Shift toggles/adds
local p1, p2, p3 = soldier(1, 100, true, 0, 0), soldier(2, 100, true, 500, 0), soldier(1, 0, true, 40, 0)
for _, m in ipairs({p1, p2, p3}) do m.sel = false; table.insert(api.squad, m) end
assert(api.selectAt({X=30, Y=0}, false) == p1 and p1.sel and not p2.sel and not p3.sel)
assert(api.selectAt({X=480, Y=20}, true) == p2 and p1.sel and p2.sel)
assert(api.selectAt({X=480, Y=20}, true) == p2 and p1.sel and not p2.sel)
assert(api.selectAt({X=2000, Y=2000}, false) == nil and not p1.sel and not p2.sel)
assert(api.selectBox({X=-100, Y=-100}, {X=600, Y=100}, false) == 2 and p1.sel and p2.sel and not p3.sel)
assert(api.selectBox({X=400, Y=-100}, {X=600, Y=100}, false) == 1 and not p1.sel and p2.sel)
assert(api.selectBox({X=-100, Y=-100}, {X=100, Y=100}, true) == 1 and p1.sel and p2.sel)
for i=#api.squad,1,-1 do table.remove(api.squad,i) end
-- attack order: focuses selected living soldiers only; a move order or H cancels the focus
local foe = soldier(2, 100, true, 900, 0)
local q1, q2, q3 = soldier(1, 100, true), soldier(2, 100, true), soldier(1, 0, true)
q2.sel = false
for _, m in ipairs({q1, q2, q3}) do table.insert(api.squad, m) end
assert(api.attack(foe) == 1 and q1.focus == foe and q1.target == nil and q2.focus == nil and q3.focus == nil)
assert(api.attack(soldier(2, 0, true)) == 0 and q1.focus == foe)  -- dead target: order ignored
assert(api.move({X=0,Y=0,Z=0}) == 1 and q1.focus == nil and q1.target)
api.attack(foe); assert(api.stop() == 1 and q1.focus == nil)
assert(q1.hold == true)  -- End (hold) holds position (no automatic cover seeking)
assert(api.move({X=0,Y=0,Z=0}) == 1 and q1.hold == false)
api.attack(foe); api.stop(); api.attack(foe); assert(q1.hold == false)
for i=#api.squad,1,-1 do table.remove(api.squad,i) end
-- path planning: straight when clear; around the wall otherwise, every leg clear, ending at the goal
local direct = api.plan({X=0, Y=0, Z=0}, {X=300, Y=0, Z=0}, {})
assert(#direct == 1 and direct[1].X == 300)
local route, nodes = api.plan({X=0, Y=0, Z=0}, {X=1000, Y=0, Z=0}, {})
assert(#route > 1 and route[#route].X == 1000 and route[#route].Y == 0, "no detour")
local prev = {X=0, Y=0}
for _, w in ipairs(route) do assert(not crossesWall(prev, w), "leg crosses wall"); prev = w end
assert(nodes > 0 and nodes < 900)
-- Strict vehicle access: validated detour; never the infantry's unchecked straight fallback.
local nav = {body=100, bodyZ=130, cell=200, step=80, height=800, margin=1600, maxNodes=1600}
local from, goal = {X=0,Y=0,Z=0}, {X=1000,Y=0,Z=0}
local job = api.planStart(from, goal, {}, nav)
while not job.result do api.planStep(job, 4) end
assert(not job.failed and #job.result > 1 and job.result[#job.result].X == goal.X)
prev = from
for _, w in ipairs(job.result) do assert(not crossesWall(prev,w)); prev=w end
local limited = {}; for k,v in pairs(nav) do limited[k]=v end; limited.maxNodes=1
job = api.planStart(from, goal, {}, limited)
while not job.result do api.planStep(job,4) end
assert(job.failed and #job.result == 0, "strict budget exhaustion must not send a truck through the wall")
local flat = terrainZ
for _, missing in ipairs({false,true}) do
    terrainZ = function(x)
        if x < 100 then return 0 end
        if missing then return nil end
        return 300
    end
    job = api.planStart(from, {X=300,Y=0,Z=0}, {}, nav)
    while not job.result do api.planStep(job,4) end
    assert(job.failed and #job.result == 0, "no ground / impassable step must not become a successful access")
end
terrainZ = flat
-- Recuperacao so com imobilidade comprovada; sweep bloqueado nao vira sucesso.
assert(api.CFG.PATH_BODY==50, "folga de soldado deve refletir raio nativo50, nao32")
assert(not api.rts.hitStartsInside({bStartPenetrating=true,Time=.776,Distance=19400}), "bitfield incorreto nao recusa impacto distante")
assert(api.rts.hitStartsInside({bStartPenetrating=false,bBlockingHit=true,Time=0,Distance=0}), "origem penetrada continua recusada")
assert(api.rts.hitStartsInside({Time=0/0,Distance=10})==nil, "tempo NaN nao prova piso livre")
assert(api.rts.hitStartsInside({Time=.5,Distance=0})==nil, "escalares inconsistentes nao autorizam resgate")
assert(api.rts.hitStartsInside({})==nil, "metadados ausentes nao provam penetracao nem folga")
assert(api.rts.hitStartsInside({Time=1,Distance=0,bBlockingHit=false})==false, "trace livre confirmado")
local stuck = soldier(1,100,true,0,0)
stuck.target={X=1000,Y=0,Z=0}
local rescue={m=stuck,calm=true,state="toRef",carry=40,legT=10}
local pos={X=0,Y=0,Z=0}
local moves=0
stuck.pawn.K2_SetActorLocation=function(_,p,sweep)
    assert(sweep==true and p.X*p.X+p.Y*p.Y<=160*160+0.01)
    moves=moves+1 -- colisao nativa simulada: nao desloca
    return false
end
terrainZ=function() return -90 end
assert(not api.logi.colRecover(rescue,pos,0) and moves==0)
assert(not api.logi.colRecover(rescue,pos,3) and moves==0)
for t=4,24,4 do assert(not api.logi.colRecover(rescue,pos,t)) end
assert(moves==96 and rescue.rescueTries==6 and not rescue.rescues)
api.logi.colRecover(rescue,pos,28)
assert(moves==96 and rescue.carry==40 and rescue.legT==10)
stuck.pathJob={}
api.logi.colRecover(rescue,pos,32)
assert(rescue.rescueWatch==nil and moves==96)
stuck.pathJob=nil
local rescuePos={X=0,Y=0,Z=0}
stuck.pawn.K2_GetActorLocation=function() return rescuePos end
local teleports=0
stuck.pawn.K2_SetActorLocation=function(_,p,sweep,hit)
    if sweep then hit.bStartPenetrating=true; return false end
    assert(rescueOccupied==false)
    teleports=teleports+1; rescuePos=p; return true
end
rescue.rescueTries=0; rescue.rescueWatch=nil
api.logi.colRecover(rescue,pos,40)
assert(not api.logi.colRecover(rescue,pos,44) and teleports==0)
local originalGo=api.logi.colGo
local replans=0
api.logi.colGo=function() replans=replans+1 end
rescueOccupied=false
assert(api.logi.colRecover(rescue,pos,48) and teleports==1 and replans==1)
assert(rescue.rescues==1 and rescue.carry==40 and rescue.legT==10)
api.logi.colGo=originalGo; rescueOccupied=nil
terrainZ=flat
-- Faixa estreita de rocha entre amostras antigas: nao pode virar atalho transitavel.
local fineNav={cell=300,margin=300,maxNodes=100,step=290,height=1200,sample=50,body=32,bodyZ=75}
terrainZ=function(x) return x>=120 and x<=180 and 200 or 0 end
job=api.planStart({X=0,Y=0,Z=0},{X=300,Y=0,Z=0},{},fineNav)
while not job.result do api.planStep(job,4) end
assert(job.failed and #job.result==0, "narrow rock must not be skipped by terrain sampling")
terrainZ=function(x) return x*.2 end
job=api.planStart({X=0,Y=0,Z=0},{X=300,Y=0,Z=60},{},fineNav)
assert(job.result and not job.failed and #job.result==1, "gentle slope must remain walkable")
terrainZ=flat
-- Chegada regional: centro bloqueado, mas existe uma parada acessivel no raio de entrega.
local regionalNav = {cell=100,margin=800,maxNodes=2500,step=60,height=400,body=32,bodyZ=75,arrivalRadius=250}
local regional = api.planStart({X=0,Y=0,Z=0}, {X=500,Y=0,Z=0}, {}, regionalNav)
while not regional.result do api.planStep(regional,4) end
assert(not regional.failed and regional.arrivalPoint and #regional.result > 0)
local endpoint = regional.result[#regional.result]
assert((endpoint.X-500)^2 + endpoint.Y^2 <= 250^2 and endpoint.X < 400,
    "regional stop must be inside the service radius, outside the wall")
-- move order behind the wall: soldier waits for the route job, then gets waypoints around the wall
local walker = soldier(1, 100, true, 0, 0)
walker.sel = true
table.insert(api.squad, walker)
assert(api.move({X=1000, Y=0, Z=0}) == 1 and walker.pathJob and walker.path == nil)
local ticks = 0
while walker.pathJob and ticks < 200 do api.pathTick(); ticks = ticks + 1 end
assert(walker.pathJob == nil and walker.path and #walker.path >= 1, "no waypoints after planning")
-- Coleta: uma busca esgotada nao vira ordem de atravessar o muro.
local oldMax = api.CFG.PATH_MAX_NODES
api.CFG.PATH_MAX_NODES = 1
api.routeTo(walker, {X=1000,Y=0,Z=0}, true)
while walker.pathJob do api.pathTick() end
assert(walker.target == nil and walker.path == nil and walker.pathBlocked, "failed collection must stop, not use direct fallback")
-- O comportamento legado fora da coleta nao muda neste lote.
api.routeTo(walker, {X=1000,Y=0,Z=0})
while walker.pathJob do api.pathTick() end
assert(walker.target and not walker.pathBlocked)
api.CFG.PATH_MAX_NODES = oldMax
local carrier = {m=walker,k=1,state="toField"}
api.logi.colGo(carrier, {X=1000,Y=0,Z=0}, 100)
assert(carrier.legT == 100 and walker.pathJob.noFallback)
api.logi.colGo(carrier, {X=1000,Y=0,Z=0}, 120)
assert(carrier.legT == 100, "retry must not renew the same leg timeout")
carrier.state = "toRef"
api.logi.colGo(carrier, {X=1000,Y=0,Z=0}, 140)
assert(carrier.legT == 140, "a new transport leg starts its own timeout")
for i=#api.squad,1,-1 do table.remove(api.squad,i) end
-- suppression: accumulates per shot, caps at 1, decays 0.35/s
local u = {}
api.suppress(u, 0.2); api.suppress(u, 0.2)
assert(math.abs(api.suppression(u) - 0.4) < 1e-9)
for i=1,10 do api.suppress(u, 0.3) end
assert(api.suppression(u) == 1.0)
clock = clock + 2
assert(math.abs(api.suppression(u) - 0.3) < 1e-9)
clock = clock + 10
assert(api.suppression(u) == 0.0)
-- medic: heals the most wounded ally in reach (stops bleeding), respects the period, walks to far wounded
local medic = soldier(1, 100, true, 0, 0); medic.role = "medic"; medic.target = nil
local light = soldier(1, 80, true, 200, 0)
local heavy = soldier(1, 30, true, 300, 0); heavy.pawn.bIsBleeding = true
heavy.pawn.OnRep_IsBleeding = function() end
local allies = {medic, light, heavy}
api.medicTick(medic, allies)
assert(heavy.pawn.Health == 42 and heavy.pawn.bIsBleeding == false and light.pawn.Health == 80)
api.medicTick(medic, allies)  -- inside MEDIC_PERIOD: nothing
assert(heavy.pawn.Health == 42)
clock = clock + 2
api.medicTick(medic, allies)
assert(heavy.pawn.Health == 54)
local far = soldier(1, 10, true, 1000, 0)
clock = clock + 2
api.medicTick(medic, {medic, far})
assert(far.pawn.Health == 10 and medic.target and medic.target.X == 850, "medic should walk to the far wounded")
-- waves: clearing the last wave wins and stops; toggling again starts a new campaign
local vet = soldier(1, 100, true); table.insert(api.squad, vet)
api.combat.auto, api.combat.wave, api.combat.nextWaveAt = true, 10, nil
api.waveTick()
assert(api.combat.won == true and api.combat.auto == false)
api.toggleWaves()
assert(api.combat.auto == true and api.combat.wave == 0 and api.combat.won == false)
api.combat.wave = 3; api.waveTick()  -- mid-campaign: schedules the next wave, no victory
assert(api.combat.won == false and api.combat.nextWaveAt)
api.toggleWaves()
for i=#api.squad,1,-1 do table.remove(api.squad,i) end
-- capture points: one soldier takes CAPTURE_TIME from neutral; up to 3 stack; contested freezes;
-- the owner loses the point only when progress crosses 0; empty points drift back to the owner's side
local pt = {X=0, Y=0, Z=0, name="A", prog=0.0}
assert(api.pointStep(pt, 1, 0, 5) == false and math.abs(pt.prog - 0.5) < 1e-9 and pt.owner == nil)
assert(api.pointStep(pt, 1, 0, 5) == true and pt.owner == 1 and pt.prog == 1.0)
assert(api.pointStep(pt, 2, 2, 5) == false and pt.prog == 1.0)
assert(api.pointStep(pt, 0, 3, 2) == false and math.abs(pt.prog - 0.4) < 1e-9 and pt.owner == 1)
assert(api.pointStep(pt, 0, 0, 4) == false and math.abs(pt.prog - 0.6) < 1e-9)
assert(api.pointStep(pt, 0, 9, 3) == true and pt.owner == nil and pt.prog < 0)
assert(api.pointStep(pt, 0, 9, 10) == true and pt.owner == 0 and pt.prog == -1.0)
-- enemy objective: nearest point not fully held by the enemy
local e1 = soldier(0, 100, true, 0, 0)
local pB = {X=3000, Y=0, Z=0, name="B", prog=0.0}
table.insert(api.points, pt); table.insert(api.points, pB)
assert(api.enemyObjective(e1) == pB)
-- waves: enemy holding every point is a defeat
local vet2 = soldier(1, 100, true); table.insert(api.squad, vet2)
api.combat.auto = true; pB.owner, pB.prog = 0, -1.0
api.waveTick()
assert(api.combat.auto == false and api.enemyObjective(e1) == nil)
-- an enemy-held point far from the squad becomes the wave entry
assert(api.waveSpawnPoint().from == "B")
pB.X = 900  -- too close to the squad: falls back to the ring around it
assert(api.waveSpawnPoint() == nil or api.waveSpawnPoint().from == nil)
-- domination: holding every point for HOLD_TO_WIN wins; losing one resets the clock
for i=#api.squad,1,-1 do table.remove(api.squad,i) end
table.insert(api.squad, soldier(1, 100, true))
pt.owner, pB.owner = 1, 1
api.combat.auto, api.combat.won, api.combat.holdSince, api.combat.nextWaveAt = true, false, nil, math.huge  -- no wave spawns here
api.waveTick(); assert(api.combat.holdSince and api.combat.won == false)
clock = clock + 50; pB.owner = nil; api.waveTick(); assert(api.combat.holdSince == nil)
pB.owner = 1; api.waveTick(); clock = clock + 91; api.waveTick()
assert(api.combat.won == true and api.combat.auto == false)
pB.owner = nil  -- the retreat test below wants pt as the only point we own
-- retreat: selected soldiers route to the nearest point we own, stop shooting; a move order ends it
for i=#api.squad,1,-1 do table.remove(api.squad,i) end
pt.owner, pt.X, pt.Y = 1, -2000, 0
local r1, r2 = soldier(1, 100, true, 0, 0), soldier(2, 100, true, 100, 0)
r1.sel, r2.sel = true, false
table.insert(api.squad, r1); table.insert(api.squad, r2)
assert(api.retreat() == 1 and r1.retreat and r1.pathJob and r1.target.X < -1900 and not r2.retreat)
local mv = api.move({X=0, Y=0, Z=0}); assert(mv == 1 and r1.retreat == nil, "move=" .. tostring(mv) .. " retreat=" .. tostring(r1.retreat) .. " sel=" .. tostring(r1.sel) .. " hp=" .. tostring(r1.pawn.Health))
for i=#api.points,1,-1 do table.remove(api.points,i) end
for i=#api.squad,1,-1 do table.remove(api.squad,i) end
-- order queue: a busy soldier queues the goal, an idle one leaves now; a plain move order drops the queue
local q1, q2 = soldier(1, 100, true, 0, 0), soldier(1, 100, true, 50, 0)
q1.sel, q2.sel, q2.target = true, true, nil
table.insert(api.squad, q1); table.insert(api.squad, q2)
assert(api.queue({X=3000, Y=0, Z=0}) == 2)
assert(q1.queue and #q1.queue == 1 and q1.target.X == 99)          -- q1 was busy (target X=99)
assert(q2.queue == nil and q2.pathJob and q2.target.X > 2800)      -- q2 was idle: routed at once
assert(api.queue({X=5000, Y=0, Z=0}) == 2 and #q1.queue == 2 and #q2.queue == 1)
assert(api.move({X=0, Y=0, Z=0}) == 2 and q1.queue == nil and q2.queue == nil)
for i=#api.squad,1,-1 do table.remove(api.squad,i) end
-- veterancy: a rank every 2 kills, capped at 3
local vet = {team = 1, role = "rifle"}
assert(api.rank(vet) == 0)
api.credit(vet); assert(api.rank(vet) == 0)
api.credit(vet); assert(api.rank(vet) == 1 and vet.kills == 2)
for i = 1, 10 do api.credit(vet) end
assert(api.rank(vet) == 3 and vet.kills == 12)
-- mortar refuses without manpower or while reloading, and never charges on refusal
api.economy.manpower = 10
assert(api.callMortar({X=0, Y=0}) == false and api.economy.manpower == 10)
api.economy.manpower = 100; api.mortar.readyAt = clock + 5
assert(api.callMortar({X=0, Y=0}) == false and api.economy.manpower == 100)
api.mortar.readyAt = 0
-- building refuses without manpower or on top of a soldier, and never charges on refusal
api.economy.manpower = 5
assert(api.build({X=0, Y=0, Z=0}) == false and api.economy.manpower == 5)
api.economy.manpower = 100
local blocker = soldier(1, 100, true, 100, 0)
table.insert(api.squad, blocker)
assert(api.build({X=0, Y=0, Z=0}) == false and api.economy.manpower == 100)
for i=#api.squad,1,-1 do table.remove(api.squad,i) end
-- recruiting refuses without manpower or room, and never charges on refusal
api.economy.manpower = 10
assert(api.recruit("rifle") == false and #api.squad == 0 and api.economy.manpower == 10)
api.economy.manpower = 200
for i=1,12 do table.insert(api.squad, soldier(1, 100, true)) end
assert(api.recruit("mg") == false and #api.squad == 12 and api.economy.manpower == 200)
server = false
assert(api.recruit("rifle") == false)
-- ammo: our dry soldier refuses to fire (no cooldown spent), resupply refills a fraction per second, capped
local dry = {role = "rifle", team = 1, ammo = 0, nextShot = 0, pawn = {}}
api.fire(dry, {}, 100, 100, 0)
assert(dry.dry == true and dry.nextShot == 0 and api.combat.dryOut >= 1)
api.resupply(dry, 2)
assert(math.abs(dry.ammo - 12) < 1e-9 and dry.dry == nil and math.abs(api.ammoFrac(dry) - 0.3) < 1e-9)
api.resupply(dry, 100)
assert(dry.ammo == 40 and api.ammoFrac({role = "mg"}) == 1.0)
server = true
-- supply crate: refuses without manpower / at the limit; a live crate refills nearby soldiers, expires on time
api.economy.manpower = 5
assert(api.dropCrate({X=0, Y=0}) == false and api.economy.manpower == 5)
api.economy.manpower = 200
for i=1,api.CFG.CRATE.max do table.insert(api.S.crates, {X=9999, Y=9999, untilT=math.huge}) end
assert(api.dropCrate({X=0, Y=0}) == false and api.economy.manpower == 200)
api.S.crates = {{X=0, Y=0, untilT=clock + 5}}
for i=#api.squad,1,-1 do table.remove(api.squad,i) end
local near, far = soldier(1, 100, true, 100, 0), soldier(1, 100, true, 5000, 0)
near.ammo, far.ammo = 0, 0
table.insert(api.squad, near); table.insert(api.squad, far)
api.supplyTick(1)
assert(math.abs(near.ammo - 10) < 1e-9 and far.ammo == 0, tostring(near.ammo))
clock = clock + 6
api.supplyTick(1)
assert(#api.S.crates == 0)
for i=#api.squad,1,-1 do table.remove(api.squad,i) end
-- trench: a move order into it seats up to cap soldiers inside, the rest form a line; inside halves suppression
api.S.trenches = {{X=1000, Y=0, Z=0}}
for i=#api.squad,1,-1 do table.remove(api.squad,i) end
for i=1,6 do local m = soldier(1, 100, true, 0, (i - 3) * 100); m.sel = true; table.insert(api.squad, m) end
assert(api.move({X=1000, Y=0, Z=0}) == 6)
local inside = 0
for _, m in ipairs(api.squad) do
    local dx, dy = m.target.X - 1000, m.target.Y
    if dx * dx + dy * dy <= api.CFG.TRENCH.radius ^ 2 then inside = inside + 1 end
end
assert(inside == api.CFG.TRENCH.cap, "inside=" .. inside)
local dug, open = soldier(1, 100, true, 1000, 50), soldier(1, 100, true, 0, 0)
api.suppress(dug, 0.4); api.suppress(open, 0.4)
assert(math.abs(dug.supp - 0.2) < 1e-6 and math.abs(open.supp - 0.4) < 1e-6)
-- refusals: too close to another trench, no manpower, limit; never charged
api.economy.manpower = 200
assert(api.digTrench({X=1100, Y=0}) == false and api.economy.manpower == 200)
api.economy.manpower = 5
assert(api.digTrench({X=5000, Y=0}) == false and api.economy.manpower == 5)
api.economy.manpower = 200
for i=1,api.CFG.TRENCH.max do table.insert(api.S.trenches, {X=i * 10000, Y=9999, Z=0}) end
assert(api.digTrench({X=-5000, Y=0}) == false and api.economy.manpower == 200)
api.S.trenches = {}
for i=#api.squad,1,-1 do table.remove(api.squad,i) end
-- enemy economy: income only from enemy-held points, capped; no spawn without a live wave;
-- reinforcements leave from the enemy point nearest our squad
for i=#api.points,1,-1 do table.remove(api.points,i) end
for i=#api.squad,1,-1 do table.remove(api.squad,i) end
table.insert(api.squad, soldier(1, 100, true, 0, 0))
local eNear, eFar = {X=1000, Y=0, Z=0, name="N", prog=-1, owner=0}, {X=9000, Y=0, Z=0, name="F", prog=-1, owner=0}
table.insert(api.points, eFar); table.insert(api.points, eNear); table.insert(api.points, {X=0, Y=5000, Z=0, name="O", prog=1, owner=1})
api.ai.reset()
api.ai.tick()
clock = clock + 1; api.ai.tick()
assert(math.abs(api.ai.mp - 2 * api.CFG.AI.rate) < 1e-9 and api.ai.sent == 0, tostring(api.ai.mp))
for _ = 1, 400 do clock = clock + 1; api.ai.tick() end
assert(api.ai.mp == api.CFG.AI.cap and api.ai.sent == 0)
assert(api.ai.source() == eNear)
for i=#api.points,1,-1 do table.remove(api.points,i) end
for i=#api.squad,1,-1 do table.remove(api.squad,i) end
api.ai.reset()
-- save: collect -> text -> parse keeps the match (owners incl. neutral, units, trenches); bad text is rejected
for i=#api.squad,1,-1 do table.remove(api.squad,i) end
local vet = soldier(1, 63, true, 120, -40); vet.role, vet.kills, vet.ammo = "sniper", 5, 7
table.insert(api.squad, vet); table.insert(api.squad, soldier(2, 0, true, 0, 0))  -- dead: not saved
table.insert(api.points, {X=100, Y=200, Z=0, name="A", prog=0.5, owner=nil})
table.insert(api.points, {X=900, Y=200, Z=0, name="B", prog=-1, owner=0})
table.insert(api.S.trenches, {X=300, Y=400, Z=0})
api.combat.wave, api.combat.kills, api.economy.manpower = 4, 17, 88.5
local d = api.sv.parse("return " .. api.sv.ser(api.sv.collect()))
assert(d and d.wave == 4 and d.kills == 17 and math.abs(d.mp - 88.5) < 1e-3 and d.map == "HomeRegionW")
assert(#d.squad == 1 and d.squad[1].role == "sniper" and d.squad[1].kills == 5 and d.squad[1].ammo == 7 and d.squad[1].hp == 63)
assert(d.squad[1].x == 120 and d.squad[1].y == -40 and #d.enemies == 0)
assert(#d.points == 2 and d.points[1].owner == -1 and d.points[2].owner == 0 and d.points[1].prog == 0.5)
assert(#d.trenches == 1 and d.trenches[1].x == 300)
assert(api.sv.parse("return {v=2}") == nil and api.sv.parse("os.exit()") == nil and api.sv.parse("return os") == nil)
assert(api.sv.save() == false)  -- io.open is mocked off; never writes during tests
for i=#api.squad,1,-1 do table.remove(api.squad,i) end
for i=#api.points,1,-1 do table.remove(api.points,i) end
api.S.trenches = {}
api.combat.wave, api.combat.kills = 0, 0
-- area fire: no line of sight (wall at X=500) -> suppress-only on enemies inside the circle, spends ammo;
-- a move order cancels it
for i=#api.squad,1,-1 do table.remove(api.squad,i) end
local gun = soldier(1, 100, true, 0, 0); gun.role, gun.team, gun.nextShot = "rifle", 1, 0
gun.hpc = {SetControlRotation=function() end}
table.insert(api.squad, gun)
local inA, outA = soldier(1, 100, true, 1000, 0), soldier(1, 100, true, 1000, 2000)
inA.team, outA.team = 0, 0
local foes = api.foes(); table.insert(foes, inA); table.insert(foes, outA)
assert(api.rts.areaOrder({X=1000, Y=0, Z=0}) == 1 and gun.area and gun.target == nil)
assert(api.rts.areaStep(gun) == true and gun.areaShooting)
assert(gun.ammo == 39 and (inA.supp or 0) > 0 and (outA.supp or 0) == 0, tostring(gun.ammo))
api.move({X=0, Y=500, Z=0})
assert(gun.area == nil)
for i=#foes,1,-1 do table.remove(foes,i) end
for i=#api.squad,1,-1 do table.remove(api.squad,i) end
-- barbed wire: slows anyone inside the band (both sides), not beside it or past its ends
api.S.wires = {{X=0, Y=0, ux=1, uy=0, yaw=0, actors={}}}
assert(api.fort.wireFactor({X=0, Y=50}) == api.CFG.WIRE.slow and api.fort.wireFactor({X=300, Y=-100}) == api.CFG.WIRE.slow)
assert(api.fort.wireFactor({X=0, Y=200}) == 1.0 and api.fort.wireFactor({X=400, Y=0}) == 1.0)
-- aid tent: heals calm soldiers within the radius, not suppressed ones nor ones outside
for i=#api.squad,1,-1 do table.remove(api.squad,i) end
local calm, hot, far = soldier(1, 50, true, 100, 0), soldier(1, 50, true, 100, 0), soldier(1, 50, true, 5000, 0)
for _, m in ipairs({calm, hot, far}) do m.pawn.MaxHealth = 100; table.insert(api.squad, m) end
api.suppress(hot, 0.8)
api.S.tents = {{X=0, Y=0, Z=0, yaw=0}}
api.supplyTick(1.0)
assert(calm.pawn.Health == 50 + api.CFG.TENT.heal and hot.pawn.Health == 50 and far.pawn.Health == 50, tostring(calm.pawn.Health))
-- save keeps tents and wires
local d2 = api.sv.parse("return " .. api.sv.ser(api.sv.collect()))
assert(#d2.tents == 1 and #d2.wires == 1 and d2.wires[1].yaw == 0)
api.S.wires, api.S.tents = {}, {}
for i=#api.squad,1,-1 do table.remove(api.squad,i) end
-- assault: enemy holding every point is not a defeat, no waves are sent, all points ours with no enemy = victory
for i=#api.squad,1,-1 do table.remove(api.squad,i) end
for i=#api.points,1,-1 do table.remove(api.points,i) end
table.insert(api.squad, soldier(1, 100, true, 0, 0))
for i = 1, 3 do table.insert(api.points, {X=i * 3000, Y=0, Z=0, name=string.char(64 + i), prog=-1, owner=0}) end
api.combat.mode, api.combat.auto, api.combat.won, api.combat.wave, api.combat.nextWaveAt = "assault", true, false, 0, nil
api.ai.reset()
api.waveTick()
assert(api.combat.auto == true and api.combat.won == false and api.combat.nextWaveAt == nil and api.combat.wave == 0)
for _, pt in ipairs(api.points) do pt.owner, pt.prog = 1, 1 end
api.waveTick()
assert(api.combat.won == true and api.combat.auto == false)
api.combat.mode, api.combat.won, api.combat.holdSince = nil, false, nil
for i=#api.points,1,-1 do table.remove(api.points,i) end
for i=#api.squad,1,-1 do table.remove(api.squad,i) end
-- officer: aura speeds up suppression recovery nearby, not far away; only one officer may be recruited
for i=#api.squad,1,-1 do table.remove(api.squad,i) end
local off, nearU, farU = soldier(1, 100, true, 0, 0), soldier(1, 100, true, 300, 0), soldier(1, 100, true, 5000, 0)
off.role = "officer"
for _, m in ipairs({off, nearU, farU}) do table.insert(api.squad, m) end
assert(api.rts.officerNear(nearU) == true and api.rts.officerNear(farU) == false)
api.suppress(nearU, 0.8); api.suppress(farU, 0.8)
clock = clock + 1
local sn, sf = api.suppression(nearU), api.suppression(farU)
assert(sn < sf and math.abs((0.8 - sn) - api.CFG.OFFICER.decay * (0.8 - sf)) < 1e-6, sn .. " " .. sf)
api.economy.manpower = 200
assert(api.recruit("officer") == false and api.economy.manpower == 200)
-- enemy MG that lost sight keeps suppressing the last seen spot (no ammo of its own is spent)
for i=#api.squad,1,-1 do table.remove(api.squad,i) end
local hidden = soldier(1, 100, true, 1000, 0)
table.insert(api.squad, hidden)
local emg = soldier(1, 100, true, 0, 0); emg.role, emg.team, emg.nextShot = "mg", 0, 0
emg.hpc = {SetControlRotation=function() end}; emg.stillSince = clock - 5
emg.seen = {X=1000, Y=0, Z=0, t=clock}
assert(api.rts.enemyArea(emg) == true and (hidden.supp or 0) > 0 and emg.ammo == nil)
emg.seen.t = clock - 60
assert(api.rts.enemyArea(emg) == false)
for i=#api.squad,1,-1 do table.remove(api.squad,i) end
-- medevac: badly wounded idle soldier heads for the aid tent; a recent player order holds it back
for i=#api.squad,1,-1 do table.remove(api.squad,i) end
local hurt, ordered = soldier(1, 20, true, 0, 0), soldier(1, 20, true, 0, 50)
for _, m in ipairs({hurt, ordered}) do m.pawn.MaxHealth = 100; m.target = nil; table.insert(api.squad, m) end
ordered.orderT = os.clock()
api.S.tents = {{X=3000, Y=0, Z=0, yaw=0}}
api.rts.medevacStep(hurt); api.rts.medevacStep(ordered)
assert(hurt.medevac and hurt.retreat and hurt.target and math.abs(hurt.target.X - 3000) <= 151, tostring(hurt.target))
assert(not ordered.medevac and ordered.target == nil)
hurt.pawn.Health = 90; api.rts.medevacStep(hurt)
assert(hurt.medevac == nil and hurt.retreat == nil)
api.S.tents = {}
for i=#api.squad,1,-1 do table.remove(api.squad,i) end
-- morale: a wave down to a quarter flees home and the fled leave the list without counting as kills
local foes2 = api.foes()
for i=#foes2,1,-1 do table.remove(foes2,i) end
local r1, r2 = soldier(1, 100, true, 0, 0), soldier(1, 100, true, 100, 0)
for _, e in ipairs({r1, r2}) do e.team, e.home = 0, {X=5000, Y=0, Z=0}; e.hpc = {SetControlRotation=function() end}; table.insert(foes2, e) end
api.combat.mode, api.combat.waveSize, api.combat.broken = nil, 8, false
api.rts.moraleCheck()
assert(api.combat.broken and r1.flee and r2.flee and r1.retreat)
local kills0 = api.combat.kills
r1.pawn.K2_GetActorLocation = function() return {X=4900, Y=0, Z=0} end
r1.pawn.K2_DestroyActor = function() end; r1.hpc.IsValid = function() return false end
r1._lf = nil
assert(api.rts.fleeStep(r1) == true and r1.fled)
api.rts.purgeFled()
assert(#api.foes() == 1 and api.combat.kills == kills0)
for i=#foes2,1,-1 do table.remove(foes2,i) end
api.combat.waveSize, api.combat.broken = nil, false
-- front alerts: same kind/place is throttled; Space walks newest -> older and focuses the camera
api.S.alerts, api.S.alertNew = {}, 0
api.rts.alert("ataque", {X=0, Y=0, Z=0}, "ponto A sob ataque")
api.rts.alert("ataque", {X=100, Y=0, Z=0}, "ponto A sob ataque")
api.rts.alert("onda", {X=9000, Y=0, Z=0}, "onda 3")
assert(#api.S.alerts == 2 and api.S.alertNew == 2)
api.rts.cam = nil
api.rts.jumpAlert()
assert(api.rts.focus.X == 9000 and api.S.alertNew == 0)
api.rts.jumpAlert()
assert(api.rts.focus.X == 0)
-- groups: Alt+N moves the selection, N selects it, 0 selects all
for i=#api.squad,1,-1 do table.remove(api.squad,i) end
local g1, g2 = soldier(1, 100, true, 0, 0), soldier(1, 100, true, 400, 0)
g1.sel, g2.sel = true, false
table.insert(api.squad, g1); table.insert(api.squad, g2)
api.rts.assignGroup(4)
assert(g1.group == 4 and g2.group == 1)
api.selectGroup(4)
assert(g1.sel and not g2.sel)
api.selectGroup(0)
assert(g1.sel and g2.sel)
for i=#api.squad,1,-1 do table.remove(api.squad,i) end
-- logistics: refinery 2:1, factory spends bmat on the scarcer crate, supply truck delivers to the base,
-- recruiting spends a shirt (point without shirts falls back to the base), resupply draws ammo crates
local L = api.logi
api.rts.home = {X=0, Y=0, Z=0}
L.reset()
local oldFind = FindAllOf
local actors = {}
FindAllOf = function(cls) return actors[cls] end
local function nativeActor(x,y)
    return {Health=900, hidden=true, collision=true, position={X=x,Y=y,Z=0},
        IsValid=function() return true end,
        K2_GetActorLocation=function(self) return self.position end,
        K2_SetActorLocation=function(self,p) self.position=p end,
        K2_SetActorRotation=function() end,
        SetActorHiddenInGame=function(self,h) self.hidden=h end,
        SetActorEnableCollision=function(self,c) self.collision=c end,
        K2_DestroyActor=function() end}
end
-- Absence is runtime evidence, not a screenshot; a refused new game preserves the existing squad.
local stay = soldier(1,100,true)
table.insert(api.squad, stay)
assert(not L.start() and not L.on and #L.trucks == 0)
assert(not api.newGame() and not api.rts.newAssault() and api.squad[1] == stay and not api.combat.auto)
table.remove(api.squad)
actors.BPSalvageField_C = {nativeActor(-2500,-3000)}
assert(api.anchor().X == -1900 and api.anchor().Y == -3000, "real field is the last-resort regional spawn anchor")
actors.PlayerStart = {nativeActor(50,200)}
assert(api.anchor().X == 650 and api.anchor().Y == 200, "prefer native player start to a resource field")
actors.PlayerStart = nil
actors.BPRefinery_C = {nativeActor(-4000,1500)}
actors.BPFactory_C = {nativeActor(-3200,1500)}
actors.BPTruckW_C = {nativeActor(-3100,1500),nativeActor(-3000,1500),nativeActor(-2900,1500)}
for _,cls in ipairs({"BPSalvageField_C","BPRefinery_C","BPFactory_C","BPTruckW_C"}) do
    local present = actors[cls]; actors[cls] = {}
    assert(not L.start() and not L.on and #L.trucks == 0, "must not create phantom " .. cls)
    actors[cls] = present
end
-- Hidden actors still count; native LOS/camera visibility is not availability.
assert(L.scan() and actors.BPFactory_C[1].hidden)
assert(L.start() and L.on and #L.trucks == 3 and L.base.shirts == 30)
for _,tr in ipairs(L.trucks) do assert(tr.pawn and tr.pawn:IsValid()) end
local priorBase, priorTrucks = L.base, L.trucks
local priorFactory = actors.BPFactory_C
actors.BPFactory_C = {}
assert(not L.start() and L.on and L.base == priorBase and L.trucks == priorTrucks, "failed start must preserve previous logistics")
actors.BPFactory_C = priorFactory
priorFactory[1].bActorIsBeingDestroyed = true
assert(not L.scan(), "IsValid alone does not make a destroyed actor usable")
priorFactory[1].bActorIsBeingDestroyed = false
-- ADAPTACAO coleta manual: a partida nova comeca SEM caminhao de recurso (reserva de 100 bmat, fabrica parada). O resto deste
-- bloco testa o fluxo refinaria -> fabrica -> caminhao de suprimento com o de recurso vivo: torna-o vivo explicitamente.
assert(L.trucks[1].kind == 'res' and L.trucks[1].state == 'dead' and L.bmat == api.CFG.COLETA.bmat0 and L.rebuildReserve() == 100)
L.trucks[1].state, L.trucks[1].hp = 'idle', api.CFG.LOGI.hp
L.salvage, L.bmat = 100, 0
L.tick(); clock = clock + 0.5; L.tick()
assert(L.bmat > 0 and L.salvage < 100)
-- Reconstrucao nao pode gastar/ativar sem ator fisico integro.
local oldParking, oldLoad, oldSpawn = L.parking, LoadAsset, mockSpawnActor
L.parking=function() return {{X=100,Y=200,Z=0,Yaw=0}} end
LoadAsset=function() return {IsValid=function() return true end} end
local rebuild={kind="res",state="dead",hp=0,rebuildT=clock}
L.bmat=100
mockSpawnActor=function() return nil end
L.truckStep(rebuild, .1, clock)
assert(L.bmat==100 and rebuild.state=="dead" and rebuild.hp==0 and rebuild.rebuildT==clock+5)
mockSpawnActor=function() local p=nativeActor(100,200); p.Health=900; p.bActorIsBeingDestroyed=true; return p end
L.truckStep(rebuild,.1,clock+5)
assert(L.bmat==100 and rebuild.state=="dead" and not rebuild.pawn)
mockSpawnActor=function() local p=nativeActor(100,200); p.Health=900; return p end
L.truckStep(rebuild,.1,clock+10)
assert(L.bmat==0 and rebuild.state=="idle" and rebuild.hp==900 and rebuild.pawn and not rebuild.pawn.hidden)
L.parking, LoadAsset, mockSpawnActor=oldParking, oldLoad, oldSpawn
L.bmat, L.base.ammo, L.base.shirts = 80, 0, 20
L.factoryStep(0.01)
assert(L.job and L.job.kind == "ammo" and L.bmat == 0)
L.factoryStep(100)
assert(L.fac.ammo == 1 and L.job == nil)
local sup = L.trucks[2]
sup.X, sup.Y = L.factory.X, L.factory.Y
L.truckStep(sup, 0.1, clock)
assert(sup.state == "toDep" and sup.dest == L.base and sup.cargo.ammo == 1)
for _ = 1, 400 do L.truckStep(sup, 0.5, clock) end
assert(sup.state == "idle" and L.base.ammo == 1)
local rifle = soldier(1, 100, true, 0, 0); rifle.role = "rifle"; rifle.ammo = 0
local full = api.CFG.WEAPONS.rifle.ammo
api.resupply(rifle, 1.0, 1.0, L.base)
assert(rifle.ammo == full and math.abs(L.base.ammo - (1 - 1 / api.CFG.LOGI.reloads)) < 1e-6)
L.base.ammo = 0; rifle.ammo = 0
api.resupply(rifle, 1.0, 1.0, L.base)
assert(rifle.ammo == 0 and L.base.dryT)
-- VARIANTE v2 (acabamento) de logistics_ai/test_orders_convoy_block.lua: as expectativas numericas leem CFG.ECHAIN
-- (free/front0) em vez de assumir free 3 (calibracao v2: free 5). Mesma logica do bloco original.
-- Proposta para tools/test_orders.py (IA_LOGISTICA): substitui o bloco "enemy convoy" (do comentario
-- "-- enemy convoy: missing cargo shrinks the wave..." ate "assert(cv2.state == "dead" ...)").
-- O contrato antigo (combat.cargo abstrato, +1 por chegada, perWave/cut) deixa de existir.
-- enemy convoy (IA_LOGISTICA): real crates from the enemy rear; a wave = free garrison + what the front equips
api.combat.auto, api.combat.mode, api.combat.lastSpawn = true, nil, {X=4000, Y=0, Z=0}
for i=#L.foes,1,-1 do table.remove(L.foes,i) end
assert(L.eReset() and L.eActive() and L.eAudit())
local w0 = api.combat.wave
local EC = api.CFG.ECHAIN
local paid1 = 10 - EC.free
assert(L.waveCut(10) == 10)                      -- free garrison + paid (front0: 10 shirts, 2 ammo crates = 12 loads)
api.combat.wave = w0 + 1; assert(L.eCommit(10) == paid1)
assert(L.en.front.shirts == EC.front0.shirts - paid1 and math.abs(L.en.front.ammo - (EC.front0.ammo - paid1 / api.CFG.LOGI.reloads)) < 1e-9)
local canNow = (L.eSoldiers())
assert(L.waveCut(EC.free + canNow + 4) == EC.free + canNow and L.en.waves[#L.en.waves].short == 4)   -- shortage shrinks the next wave
api.combat.wave = w0 + 2; L.eCommit(EC.free + canNow)
assert(L.eAudit())
for _ = 1, 400 do L.eTick(0.5, clock) end        -- rear produces from its own bmat/salvage, never for free
assert(L.en.fac.ammo + L.en.fac.shirts > 0 and L.en.led.spent > 0 and L.eAudit())
L.convoyT = 0
local previousSpawn, previousLoad = mockSpawnActor, LoadAsset
LoadAsset = function() return nil end
local nConv, rear = api.combat.convoys, L.en.fac.ammo + L.en.fac.shirts
assert(not L.convoySpawn(clock))
assert(#L.foes == 0 and api.combat.convoys == nConv and L.en.fac.ammo + L.en.fac.shirts == rear)
LoadAsset = function() return {IsValid=function() return true end} end
assert(not L.convoySpawn(clock))  -- class loaded, but failed to create actor
assert(#L.foes == 0 and api.combat.convoys == nConv and L.en.fac.ammo + L.en.fac.shirts == rear)
mockSpawnActor = function(_, p) return nativeActor(p.X,p.Y) end
local spawnTruck = mockSpawnActor
mockSpawnActor = function(_, p)
    local dying = spawnTruck(nil,p); dying.bActorIsBeingDestroyed = true
    dying.SetActorEnableCollision = function() error("must not touch dying pawn") end
    return dying
end
assert(not L.convoySpawn(clock))
assert(#L.foes == 0 and api.combat.convoys == nConv and L.en.fac.ammo + L.en.fac.shirts == rear,
    "IsValid but being destroyed must not create a phantom convoy or debit the rear")
mockSpawnActor = spawnTruck
L.convoyTick(0.1, clock)
assert(#L.foes == 1 and L.foes[1].state == "toFront" and L.eAudit())
local cv = L.foes[1]
local carried = (cv.cargo.ammo or 0) + (cv.cargo.shirts or 0) * api.CFG.LOGI.recipes.shirts.units
assert(carried > 0 and L.en.fac.ammo + L.en.fac.shirts < rear)
local before = L.en.front.ammo + L.en.front.shirts
for i=#api.squad,1,-1 do table.remove(api.squad,i) end
for _ = 1, 400 do L.convoyTick(0.5, clock) end
assert(#L.foes == 0 and L.en.delivered == 1 and L.en.ready == api.CFG.ECHAIN.trucks)
assert(math.abs(L.en.front.ammo + L.en.front.shirts - before - carried) < 1e-6 and L.eAudit())
L.waveCut(16); api.combat.wave = api.combat.wave + 1; L.eCommit(16)  -- the front spends, so it asks again
for _ = 1, 40 do L.eTick(0.5, clock) end
L.convoyT = 0
local amb = soldier(1, 100, true, 20000, 0); amb.role = "rifle"
api.combat.lastSpawn = {X=4000, Y=0, Z=0}
L.convoyTick(0.01, clock)
local cv2 = L.foes[1]
assert(cv2 and cv2.cargo, "second convoy leaves with real cargo")
cv2.pawn.Health = 20
table.insert(api.squad, amb)
amb.pawn.K2_GetActorLocation = function() return {X=cv2.X, Y=cv2.Y, Z=0} end
local cut0, lost0, front0 = api.combat.convoysCut, L.en.led.lost.shirts + L.en.led.lost.ammo, L.en.front.shirts + L.en.front.ammo
amb.role = "worker"
L.convoyTick(1.0, clock)
assert(cv2.hp == 20 and api.combat.convoysCut == cut0,
    "trabalhador desarmado nao danifica comboio nem perde carga")
amb.role = "rifle"
L.convoyTick(1.0, clock)
assert(cv2.hp == 20 and cv2.state ~= "dead", "rifle nao aplica DPS ficticio ao veiculo")
cv2.pawn.Health = 0 -- simula observacao de dano nativo, NAO implementacao de combate
L.convoyTick(1.0, clock)
assert(cv2.state == "dead" and api.combat.convoysCut == cut0 + 1)
assert(L.en.led.lost.shirts + L.en.led.lost.ammo > lost0 and L.en.front.shirts + L.en.front.ammo == front0)
assert(#L.en.rebuild == 1 and L.eAudit(), select(2, L.eAudit()))
do
    local hostile = soldier(1, 100, true); hostile.role = "worker"
    hostile.pawn.K2_GetActorLocation = function() return {X=0,Y=0,Z=0} end
    local hostiles = api.foes()
    for i=#hostiles,1,-1 do table.remove(hostiles,i) end
    table.insert(hostiles,hostile)
    local friendlyTruck = {X=0,Y=0,Z=0,hp=100,state="toField",moving=true}
    L.ambushStep(friendlyTruck,1,clock)
    assert(friendlyTruck.hp==100,"desarmado inimigo tambem nao embosca")
    hostile.role="rifle"
    L.ambushStep(friendlyTruck,1,clock)
    assert(friendlyTruck.hp==100,"alerta armado nao inventa dano de fuzil")
    table.remove(hostiles)
end
for i=#api.squad,1,-1 do table.remove(api.squad,i) end
api.combat.auto = false
L.reset()
assert(not L.on)
-- Initial deployment is an atomic scenario budget, NOT the game's construction/inventory.
local oldActive, oldWallet = api.rts.active, api.S.deploy
api.rts.active, api.S.deploy = true, nil
actors.BPRefinery_C, actors.BPFactory_C, actors.BPTruckW_C = {}, {}, {}
local function ruinActor(name,x,y,hidden,collision)
    local a = nativeActor(x,y)
    a.bHidden, a.collision = hidden, collision
    a.GetActorEnableCollision = function(self) return self.collision end
    a.SetActorHiddenInGame = function(self,v) self.bHidden=v end
    a.K2_GetActorRotation = function() return {Pitch=0,Yaw=23,Roll=0} end
    a.GetClass = function() return {GetFullName=function() return name end} end
    return a
end
local rr = ruinActor("BPDestroyedRefinery_C",-4000,3000,true,false)
local rf = ruinActor("BPDestroyedFactory_C",-5000,3000,false,true)
actors.BPDestroyedRefinery_C, actors.BPDestroyedFactory_C = {rr}, {rf}
LoadAsset = function(path)
    local kind = path:find("Refinery") and "Refinery" or (path:find("Factory") and "Factory" or "TruckW")
    return {kind=kind, IsValid=function() return true end}
end
local spawned, failAt = 0, nil
mockSpawnActor = function(cls,p)
    spawned = spawned+1
    local a = nativeActor(p.X,p.Y); a.position.Z=p.Z
    a.Health = cls.kind=="Refinery" and 2700 or (cls.kind=="Factory" and 2000 or 900)
    a.MaxHealth = a.Health
    a.K2_GetActorRotation = function() return {Yaw=23} end
    a.CodeName = {ToString=function() return cls.kind end}
    local original = cls.kind=="Refinery" and rr or rf
    a.BaseStructureClass = {IsValid=function() return true end,GetFullName=function() return original:GetClass():GetFullName() end}
    a.K2_DestroyActor = function(self) self.bActorIsBeingDestroyed=true end
    if spawned==failAt then
        a.bActorIsBeingDestroyed=true
        a.K2_GetActorLocation=function() error("must not touch failed native spawn") end
    end
    local list=actors["BP"..cls.kind.."_C"]
    list[#list+1]=a
    return a
end
local plan = assert(L.deployPlan())
assert(plan.cost==1000 and #plan.builds==2 and #plan.parking==2 and spawned==0)  -- ADAPTACAO: sem caminhao de recurso na implantacao
for i,p in ipairs(plan.parking) do for j,q in ipairs(plan.parking) do
    if i~=j then assert((p.X-q.X)^2+(p.Y-q.Y)^2>=api.CFG.DEPLOY.spacing^2) end
end end
api.S.deploy.bmat=999  -- ADAPTACAO: falta 1 para o novo custo 1000
assert(not L.deployPlan() and spawned==0)
api.S.deploy.bmat=1000  -- ADAPTACAO: orcamento 1000
terrainClass="Warehouse"
assert(not L.deployPlan() and not L.deploy() and spawned==0, "roof is not a parking surface; no mutation")
terrainClass=nil
local field=actors.BPSalvageField_C; actors.BPSalvageField_C={}
assert(not L.deployPlan() and spawned==0, "never invent a field")
actors.BPSalvageField_C=field
server=false; assert(not L.deploy()); server=true
api.rts.active=false; assert(not L.deploy()); api.rts.active=true
local survivor = soldier(1,100,true); table.insert(api.squad,survivor)
failAt=4
assert(not L.deploy() and api.S.deploy.bmat==1000 and api.S.deploy.spent==0)  -- ADAPTACAO: orcamento 1000
assert(rr.bHidden and not rr.collision and not rf.bHidden and rf.collision, "rollback must restore original states")
assert(not L.scan() and api.squad[1]==survivor and not L.on, "failed deployment preserves session")
for _,cls in ipairs({"BPRefinery_C","BPFactory_C","BPTruckW_C"}) do
    for _,a in ipairs(actors[cls]) do assert(a.bActorIsBeingDestroyed) end
    actors[cls]={}
end
spawned,failAt=0,nil
assert(L.deploy() and spawned==4 and L.scan() and api.S.deploy.bmat==0 and api.S.deploy.spent==1000)  -- ADAPTACAO: 2 estruturas + 2 caminhoes
assert(rr.bHidden and not rr.collision and rf.bHidden and not rf.collision)
assert(L.deploy() and spawned==4 and api.S.deploy.spent==1000, "idempotent; no free duplicate buildings or trucks")
assert(not L.on and api.squad[1]==survivor, "deployment does not start waves/clear units")
assert(L.start())
for _,tr in ipairs(L.trucks) do
    if tr.pawn then assert(tr.X==tr.pawn.position.X and tr.Y==tr.pawn.position.Y, "preserve actual parking at startup")
    else assert(tr.kind=="res" and tr.state=="dead" and not tr.X, "ADAPTACAO: o de recurso ainda nao existe") end
end
L.reset(); table.remove(api.squad)
api.rts.active, api.S.deploy = oldActive, oldWallet
FindAllOf, mockSpawnActor, LoadAsset = oldFind, previousSpawn, previousLoad
api.rts.home = nil
-- difficulty cycles easy -> normal -> hard -> easy and overrides the wave/economy values
assert(api.S.difficulty == 2 and api.CFG.ENEMY_ACCURACY == 0.7)
assert(api.setDifficulty(3) == "difícil" and api.CFG.ENEMY_ACCURACY == 0.85 and api.CFG.WAVE_GROWTH == 1.0)
assert(api.setDifficulty(4) == "fácil" and api.S.difficulty == 1 and api.CFG.MANPOWER_RATE == 1.2)
assert(api.setDifficulty(2) == "normal" and api.CFG.FLANK_CHANCE == 0.4 and api.CFG.WAVE_SQUAD_SCALE == 0.4)
''')
# Mod keys must not collide with the game's default bindings (Default__InputSettings read in game, 2026-10-07).
lua.execute('''
-- Actual outline helpers: attachment, latest pose transform, selection/RTS gates and partial rollback.
local oldFind, oldSpawn = StaticFindObject, mockSpawnActor
local anchored, spawned = false, {}
local function object(t) t.IsValid=function() return true end; return t end
local fill = object({SetVectorParameterValue=function() assert(anchored) end,
    SetScalarParameterValue=function() assert(anchored) end})
StaticFindObject = function(path)
    return object({path=path, CreateDynamicMaterialInstance=function() return fill end,
        -- Mock de transporte: conversao quaternion real verificada pelo oracle nativo.
        MakeTransform=function(_,p,r,scale) return {Rotation={X=r.Pitch,Y=r.Yaw,Z=r.Roll,W=1}} end})
end
function FName(s) return s end
mockSpawnActor = function(cls)
    if cls.path == '/Script/Engine.PostProcessVolume' then
        return object({AddOrUpdateBlendable=function() anchored=true end, K2_DestroyActor=function() end})
    end
    local c = object({SetSkeletalMesh=function() end, SetMasterPoseComponent=function(self, src) self.master=src end,
        SetCollisionEnabled=function() end, SetCastShadow=function() end,
        CreateDynamicMaterialInstance=function() return object({SetVectorParameterValue=function() end}) end,
        GetNumMaterials=function() return 2 end, SetMaterial=function() end})
    local a = object({SkeletalMeshComponent=c, SetActorEnableCollision=function() end,
        K2_AttachToComponent=function(self, src) self.parent=src end,
        K2_SetActorLocation=function(self, p) self.pos=p end,
        K2_SetActorRotation=function(self, rot) self.rot=rot end,
        SetActorScale3D=function(self, s) self.scale=s end,
        K2_SetActorTransform=function(self,t,sweep,hit,teleport)
            assert(sweep==false and teleport==true)
            self.pos={X=t.Translation.X,Y=t.Translation.Y,Z=t.Translation.Z}
            self.rot={Pitch=t.Rotation.X,Yaw=t.Rotation.Y,Roll=t.Rotation.Z}
            self.scale={X=t.Scale3D.X,Y=t.Scale3D.Y,Z=t.Scale3D.Z}
        end,
        K2_DestroyActor=function(self) self.dead=true end})
    spawned[#spawned+1]=a; return a
end
local p={X=10,Y=20,Z=30}
local src=object({bVisible=true,bHiddenInGame=false,SkeletalMesh=object({}), K2_GetComponentLocation=function() return p end,
    K2_GetComponentRotation=function() return {Pitch=0,Yaw=77,Roll=0} end,
    K2_GetComponentScale=function() return {X=1,Y=1,Z=1} end,
    K2_GetComponentToWorld=function() return {Translation={X=p.X,Y=p.Y,Z=p.Z},
        Rotation={X=0,Y=77,Z=0,W=1},Scale3D={X=1,Y=1,Z=1}} end,
    SetCustomDepthStencilValue=function(self,s) self.stencil=s end,
    SetRenderCustomDepth=function(self,on) self.depth=on end})
local limb=object({bVisible=true,bHiddenInGame=false,SkeletalMesh=object({}),
    K2_GetComponentLocation=src.K2_GetComponentLocation,K2_GetComponentRotation=src.K2_GetComponentRotation,
    K2_GetComponentScale=src.K2_GetComponentScale,K2_GetComponentToWorld=src.K2_GetComponentToWorld,
    SetCustomDepthStencilValue=src.SetCustomDepthStencilValue,SetRenderCustomDepth=src.SetRenderCustomDepth})
local m={sel=true, team=1, pawn=object({Health=100, Mesh=src,
    K2_GetComponentsByClass=function() return {{get=function() return src end},{get=function() return limb end}} end})}
local cam={X=-1000,Y=-800,Z=1700}
api.rts.cam=object({K2_GetActorLocation=function() return cam end})
api.rts.active=true; api.rts.dist=3000
api.rts.setOutline(m,true)
assert(anchored and #m.outline==8 and src.depth and limb.depth and src.stencil==1 and limb.stencil==1)
for i,a in ipairs(m.outline) do
    local part=i<=4 and src or limb
    assert(a.parent==part and a.SkeletalMeshComponent.master==part and a.rot.Yaw==77)
end
local function projectedAlignment()
    local a=m.outline[1]; local q=a.scale.X
    local pitch=math.rad(api.CFG.CAM_PITCH)
    local radius=((p.X-cam.X)*math.cos(pitch)+(p.Z-cam.Z)*math.sin(pitch))*q/api.CFG.OUTLINE.pixels
    -- First copy is offset only along screen-right; remove that intentional border width.
    assert(math.abs(a.pos.X-(cam.X+(p.X-cam.X)*q))<0.001)
    assert(math.abs(a.pos.Y-radius-(cam.Y+(p.Y-cam.Y)*q))<0.001)
    assert(math.abs(a.pos.Z-(cam.Z+(p.Z-cam.Z)*q))<0.001)
end
projectedAlignment()
p.X=p.X+1000; cam.Y=cam.Y+600; api.rts.updateOutline(m); projectedAlignment()
local saved=m.outline
m.sel=false; api.rts.setOutline(m,true)
assert(m.outline==nil and not src.depth and not limb.depth)
limb.depth=true; api.rts.setOutline(m,false); assert(not limb.depth, "native limb highlighting must be reset each frame")
for _,a in ipairs(saved) do assert(a.dead) end
m.sel=true; api.rts.active=false; api.rts.setOutline(m,true); assert(m.outline==nil)
api.rts.active=true; m.team=api.CFG.ENEMY_TEAM; api.rts.setOutline(m,true); assert(m.outline==nil)
m.team=1; m.pawn.Health=0; api.rts.setOutline(m,true); assert(m.outline==nil)
m.pawn.Health=100
local goodSpawn=mockSpawnActor
mockSpawnActor=function(cls) if #spawned>=11 then return nil end; return goodSpawn(cls) end
api.rts.setOutline(m,true)
assert(m.outline==nil and not src.depth)
for _,a in ipairs(spawned) do assert(a.dead) end
StaticFindObject, mockSpawnActor=oldFind, oldSpawn
api.rts.outlineVolume, api.rts.outlineMid=nil,nil
''')
GAME_KEYS = {"A", "B", "BACKSPACE", "C", "COMMA", "D", "E", "EIGHT", "ENTER", "ESCAPE", "F", "F1", "F8", "FIVE", "FOUR",
             "G", "H", "I", "L", "LEFT_MOUSE_BUTTON_noRTS", "M", "N", "NINE", "O", "ONE", "P", "PERIOD", "Q", "R", "S",
             "SEVEN", "SIX", "SPACE", "T", "TAB", "THREE", "TWO", "U", "V", "W", "X", "Y", "Z", "ZERO",
             "SHIFT+ONE", "SHIFT+TWO", "SHIFT+THREE", "SHIFT+FOUR", "SHIFT+FIVE", "SHIFT+SIX", "SHIFT+SEVEN",
             "SHIFT+E", "SHIFT+F", "SHIFT+Q", "SHIFT+V", "SHIFT+X"}
# accepted overlaps: pawn actions, and the RTS disables the commander pawn's input: 1/2/3 equip, 4/5/0 emotes,
# SPACE climb (CenterMapOnPlayer only inside the map screen), Q mount, E use; mouse buttons fire/aim
ACCEPTED = {"ONE", "TWO", "THREE", "FOUR", "FIVE", "ZERO", "SPACE", "Q", "E", "L"}  # L: lock vehicle
registered = set(lua.eval("(function() local t = {} for k in pairs(bindings) do t[#t+1] = k end return table.concat(t, ',') end)()").split(","))
clash = sorted(k for k in registered if k in GAME_KEYS and k not in ACCEPTED)
assert not clash, f"mod keys collide with game bindings: {clash}"
# ADAPTACAO bases avancadas: Shift+J (construir base avancada) existe, nao colide com tecla do jogo e J continua livre
assert "SHIFT+J" in registered and "SHIFT+J" not in GAME_KEYS and "J" not in GAME_KEYS and "J" in registered, registered
assert not [k for k in registered if k.endswith("+J") and k != "SHIFT+J"], "so Shift+J usa J com modificador"
print("teclas: SHIFT+J registrada, fora de GAME_KEYS; J livre no jogo")
assert {"J", "K", "HOME", "END", "CONTROL+FIVE", "F11", "CONTROL+ONE", "CONTROL+TWO", "CONTROL+THREE", "SHIFT+F5", "CONTROL+SIX", "CONTROL+SEVEN", "CONTROL+F6", "CONTROL+F7", "CONTROL+RIGHT_MOUSE_BUTTON", "CONTROL+EIGHT", "CONTROL+NINE", "ALT+F6", "CONTROL+ZERO", "PAUSE", "CONTROL+SPACE", "INS", "SPACE", "Q", "E", "FOUR", "FIVE", "ZERO", "ALT+ONE", "ALT+FIVE", "L", "SHIFT+L", "CONTROL+L", "ALT+L"} <= registered, registered
print("PASS: syntax, lab map case matching, H gating, selected/all orders, repeated braking, resume, dead/invalid units, native death cleanup/cache/corpse TTL, authority guards, empty squad, click/box selection, attack order, hold, path planning (sync + async job + strict no-fallback terrain access), suppression, medic, victory, capture points (progress, contest, objective, defeat, domination), order queue, veterancy, retreat, mortar refusals, build refusals, recruit refusals, ammo, supply crates, trenches, enemy economy, save/continue, area fire, barbed wire, aid tent, assault mode, officer aura, enemy area fire, medevac, morale, difficulty, front alerts, groups 1-5, logistics (real hidden actors, refused startup preserves state, regional spawn), enemy convoy (no phantom spawn), no key clashes with the game")
