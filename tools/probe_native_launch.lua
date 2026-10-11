-- Apenas schema e CDO de movimento; nao dispara nem spawna.
for _, row in ipairs({
    {"GameplayStatics", {SuggestProjectileVelocity_CustomArc=true,
        BeginDeferredActorSpawnFromClass=true, FinishSpawningActor=true}},
    {"ProjectileMovementComponent", {SetVelocityInLocalSpace=true}},
    {"MovementComponent", {GetGravityZ=true}},
    {"Actor", {K2_GetActorTransform=true}},
}) do
    local cls = StaticFindObject("/Script/Engine." .. row[1])
    assert(valid(cls), "classe ausente: " .. row[1])
    cls:ForEachFunction(function(f)
        if row[2][f:GetFName():ToString()] then
            out("FUNCTION", f:GetFullName())
            f:ForEachProperty(function(p)
                out("PARAM", p:GetFName():ToString(), p:GetClass():GetFName():ToString())
            end)
        end
    end)
end
local path = "/Game/Blueprints/Items/BPGrenadeW"
assert(valid(LoadAsset(path .. ".BPGrenadeW_C")), "asset ausente")
local cdo = StaticFindObject(path .. ".Default__BPGrenadeW_C")
assert(valid(cdo), "CDO ausente")
local movement = cdo.MovementComp
out("MOVEMENT_COMPONENT", valid(movement) and movement:GetFullName() or "nulo")
if valid(movement) then
    out("MOVEMENT_DEFAULTS", "INITIAL_SPEED", movement.InitialSpeed,
        "MAX_SPEED", movement.MaxSpeed, "GRAVITY_SCALE", movement.ProjectileGravityScale,
        "LOCAL_VELOCITY", movement.bInitialVelocityInLocalSpace)
end
out("LIMIT", "schema nao prova binding de FVector/FTransform nem lancamento")
