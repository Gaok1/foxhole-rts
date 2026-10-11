-- Somente reflexao/CDOs: nao spawna, detona, escreve propriedades ou chama RPC.
for _, name in ipairs({"WarProjectile", "TimedProjectile"}) do
    local cls = StaticFindObject("/Script/War." .. name)
    assert(valid(cls), "classe ausente: " .. name)
    out("CLASS", cls:GetFullName())
    cls:ForEachProperty(function(p)
        out("PROP", name, p:GetFName():ToString(), p:GetClass():GetFName():ToString())
    end)
    cls:ForEachFunction(function(f)
        local n = f:GetFName():ToString()
        if n == "Detonate" or n == "ApplyExplosiveDamageAndSpawnFx" then
            out("FUNCTION", f:GetFullName())
            f:ForEachProperty(function(p)
                out("PARAM", n, p:GetFName():ToString(), p:GetClass():GetFName():ToString())
            end)
        end
    end)
end
for _, name in ipairs({"Grenade", "BPGrenadeW", "BPHEGrenade", "BPHELaunchedGrenade"}) do
    local path = "/Game/Blueprints/Items/" .. name
    local cls = LoadAsset(path .. "." .. name .. "_C")
    assert(valid(cls), "asset ausente: " .. name)
    local cdo = StaticFindObject(path .. ".Default__" .. name .. "_C")
    assert(valid(cdo), "CDO ausente: " .. name)
    out("PROJECTILE_CDO", name, cdo:GetFullName())
    local ancestor, timed = cls, false
    while valid(ancestor) do
        out("SUPER", name, ancestor:GetFullName())
        if ancestor:GetFName():ToString() == "TimedProjectile" then timed = true end
        ancestor = ancestor:GetSuperStruct()
    end
    out("DEFAULTS", name, "EXPLOSIVE", cdo.ExplosiveCodeName:ToString(),
        "LIFE", cdo.ProjectileLife, "AUTO", cdo.AutoDetonateTime,
        "FUSE", timed and cdo.FuseTimer or "nao temporizado")
    local template = cdo.ExplosionTemplate
    out("EXPLOSION_TEMPLATE", name, valid(template) and template:GetFullName() or "nulo")
end
out("LIMIT", "CDO/schema nao prova spawn, fuse inicializado ou dano")
