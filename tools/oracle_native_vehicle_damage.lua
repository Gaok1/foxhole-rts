-- Laboratorio: primeiro rodar t_settings_oracle_spawn.lua e aguardar >3s.
-- Ator exclusivo guardado pelo mundo; NAO manter settings somente em Lua entre comandos.
-- Testa API de dano generico, nao disparo/municao/impacto. 1500 e sobrecarga de teste.
local q = assert(_G.nativeSettingsOracle, "spawn do oracle ausente")
local function mark(message)
    log("NATIVE_VEHICLE_ORACLE " .. message)
    out("CHECKPOINT", message)
end
assert(valid(q.gi) and not valid(q.gi.ServerSettings), "contexto inesperado")
assert(valid(q.a) and not q.a.bActorIsBeingDestroyed and q.a.Health == 900, "ator invalido")
local ok, err = pcall(function()
    local cls = StaticFindObject("/Script/War.ServerSettings")
    local settings = StaticConstructObject(cls, q.gi)
    assert(valid(settings) and settings:GetClass():GetAddress() == cls:GetAddress(), "settings invalido")
    q.gi.ServerSettings = settings -- ancora nativa imediata, antes de chamadas/espera
    assert(valid(q.gi.ServerSettings), "associacao falhou")
    for _, row in ipairs({
        {"BPLightKineticDamageType", 45},
        {"BPHeavyKineticDamageType", 55},
        {"BPExplosiveDamageType", 1500},
    }) do
        assert(valid(q.a) and not q.a.bActorIsBeingDestroyed and q.a.Health > 0, "ator perdido")
        local dt = LoadAsset("/Game/Blueprints/DamageTypes/" .. row[1] .. "." .. row[1] .. "_C")
        assert(valid(dt), "tipo ausente")
        local before = q.a.Health
        mark("BEFORE " .. row[1] .. " HP=" .. before)
        local result = gs():ApplyDamage(q.a, row[2], playerController(), playerPawn(), dt)
        local live = valid(q.a) and not q.a.bActorIsBeingDestroyed
        out("NATIVE_HIT", row[1], "BASE", row[2], "BEFORE", before,
            "RETURN", result, "ALIVE_ACTOR", live, "AFTER", live and q.a.Health or "destruido")
        mark("AFTER " .. row[1])
    end
end)
local restored, restoreErr = pcall(function() q.gi.ServerSettings = q.original end)
out("RESTORE", restored, "SETTINGS_VALID", valid(q.gi.ServerSettings), restoreErr)
if valid(q.a) and not q.a.bActorIsBeingDestroyed then q.a:K2_DestroyActor() end
_G.nativeSettingsOracle = nil
out("CLEANUP", ok, err)
assert(restored and not valid(q.gi.ServerSettings), "restauracao falhou")
