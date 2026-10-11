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
cv2.hp = 20
table.insert(api.squad, amb)
amb.pawn.K2_GetActorLocation = function() return {X=cv2.X, Y=cv2.Y, Z=0} end
local cut0, lost0, front0 = api.combat.convoysCut, L.en.led.lost.shirts + L.en.led.lost.ammo, L.en.front.shirts + L.en.front.ammo
L.convoyTick(1.0, clock)
assert(cv2.state == "dead" and api.combat.convoysCut == cut0 + 1)
assert(L.en.led.lost.shirts + L.en.led.lost.ammo > lost0 and L.en.front.shirts + L.en.front.ammo == front0)
assert(#L.en.rebuild == 1 and L.eAudit(), select(2, L.eAudit()))
