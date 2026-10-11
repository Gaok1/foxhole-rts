-- Canal de comandos do laboratorio: apenas CDO/reflexao, sem disparo ou dano.
-- Nao troca valores, nao le inventario e nao chama RPC.
for _, short in ipairs({ "BPLightKineticDamageType", "BPHeavyKineticDamageType",
    "BPExplosiveDamageType", "BPAntiTankKineticDamageType", "BPHighExplosiveDamageType", "BPFireDamageType" }) do
    local path = "/Game/Blueprints/DamageTypes/" .. short
    local cls = LoadAsset(path .. "." .. short .. "_C")
    assert(valid(cls), "classe ausente: " .. short)
    local cdo = StaticFindObject(path .. ".Default__" .. short .. "_C")
    assert(valid(cdo), "CDO ausente: " .. short)
    out("DAMAGE_TYPE", short, "TYPE", tostring(cdo.Type), "BYPASS_SPAWN", cdo.bBypassesSpawnInvulnerability,
        "ARMOUR", cdo.bApplyTankArmourMechanics, "PENETRATE", cdo.bCanPenetrateArmour)
end
out("LIMIT", "CDO nao prova fluxo de disparo, impacto ou reducao de Health")
