-- Candidato offline: tempo/dados do jogo, balistica/movimento/dano/FX nativos.
-- Lease pertence ao chamador ate nativeTrack transferi-la ao acompanhamento.
function rts.grenadeNumber(v)
    return type(v) == "number" and v == v and v > -math.huge and v < math.huge
end

function rts.nativeGrenadeData()
    if rts.grenadeData then return rts.grenadeData end
    local dt = LoadAsset("/Game/Blueprints/Data/BPGrenadeDynamicData.BPGrenadeDynamicData")
    if not valid(dt) then return nil end
    local data
    dt:ForEachRow(function(key, row)
        if tostring(key) == "GrenadeW" then
            data = { fuse = row.GrenadeFuseTimer, min = row.MinTossSpeed,
                     max = row.MaxTossSpeed, range = row.GrenadeRangeLimit }
        end
    end)
    if not data then return nil end
    for _, v in pairs(data) do if not rts.grenadeNumber(v) or v < 0 then return nil end end
    if not (data.fuse and data.min and data.max and data.range) or data.fuse <= 0 or data.min <= 0
        or data.max < data.min then return nil end
    rts.grenadeData = data
    return data
end

function throwGrenade(m, target)
    if not isLocalAuthority() or not m or not target or not alive(m) or not alive(target) then return false end
    if m.pawn.bActorIsBeingDestroyed or target.pawn.bActorIsBeingDestroyed then return false end
    local t = now()
    if t < (m.nextGrenade or 0) then return false end
    local actor, acquired, tracked
    local ok, thrown = pcall(function()
        local data = rts.nativeGrenadeData()
        if not data then return false end
        local ml, tl = loc(m), loc(target)
        for _, p in ipairs({ ml, tl }) do
            for _, k in ipairs({ "X", "Y", "Z" }) do if not rts.grenadeNumber(p[k]) then return false end end
        end
        -- Row real GrenadeW usa range0: sem teto adicional, nao alcance zero.
        local range = data.range > 0 and math.min(CFG.GRENADE.range, data.range) or CFG.GRENADE.range
        if flatDist(ml, tl) > range then return false end
        local cls = LoadAsset("/Game/Blueprints/Items/BPGrenadeW.BPGrenadeW_C")
        local mathcls = StaticFindObject("/Script/Engine.KismetMathLibrary")
        if not valid(cls) or not valid(mathcls) then return false end
        local start = { X = ml.X, Y = ml.Y, Z = ml.Z + 40 }
        local finish = { X = tl.X, Y = tl.Y, Z = tl.Z - 60 }
        local xf = mathcls:GetCDO():MakeTransform(start, { Pitch = 0, Yaw = 0, Roll = 0 }, { X = 1, Y = 1, Z = 1 })
        if not rts.nativeAcquire() then return false end
        acquired = true
        actor = gs():BeginDeferredActorSpawnFromClass(world(), cls, xf, 1, m.pawn)
        if not valid(actor) or actor.bActorIsBeingDestroyed then return false end
        actor.FuseTimer = data.fuse -- antes do BeginPlay que captura a duracao
        local move = actor.MovementComp
        if not valid(move) then return false end
        local gravity, velocity = move:GetGravityZ(), { X = 0, Y = 0, Z = 0 }
        if not rts.grenadeNumber(gravity) or gravity >= 0 then return false end
        if not gs():SuggestProjectileVelocity_CustomArc(world(), velocity, start, finish, gravity, 0.5) then return false end
        for _, k in ipairs({ "X", "Y", "Z" }) do if not rts.grenadeNumber(velocity[k]) then return false end end
        local speed = math.sqrt(velocity.X^2 + velocity.Y^2 + velocity.Z^2)
        if not rts.grenadeNumber(speed) or speed < data.min or speed > data.max then return false end
        move.Velocity = velocity
        local finished = gs():FinishSpawningActor(actor, xf)
        if not valid(finished) or finished.bActorIsBeingDestroyed then return false end
        if not rts.nativeTrack(actor) then return false end
        tracked = true
        return true
    end)
    if not ok or not thrown then
        if actor and valid(actor) and not actor.bActorIsBeingDestroyed then pcall(function() actor:K2_DestroyActor() end) end
        if acquired and not tracked then rts.nativeRelease() end
        if not ok then logOnce("granada nativa", thrown) end
        return false
    end
    m.throwAnimUntil, m.nextGrenade = os.clock() + 0.8, t + CFG.GRENADE.cooldown
    local tm = m.team or 0
    mortar.grenades[tm] = (mortar.grenades[tm] or 0) + 1
    pcall(playCue, CFG.GRENADE.pin, loc(m))
    return true
end
