-- Primeiro gate da configuracao local autorizada: constructor nativo, sem associar ao mundo.
-- Nao escreve no CDO/GameInstance, nao aplica dano, nao chama RPC nem inventario.
local cls = StaticFindObject("/Script/War.ServerSettings")
assert(valid(cls), "classe ServerSettings ausente")
assert(cls:GetSuperStruct():GetFName():ToString() == "SaveGame", "ancestral inesperado")
local gi = world().OwningGameInstance
assert(valid(gi), "GameInstance ausente")
local original = gi.ServerSettings
local settings = StaticConstructObject(cls, gi)
assert(valid(settings), "constructor nao retornou objeto valido")
out("SETTINGS_INSTANCE", settings:GetFullName())
local tweaks = settings.WarTweakables
local values = {
    {"SpawnInvulnerabilityTime", settings.SpawnInvulnerabilityTime, 3.0},
    {"GlobalRefineYieldModifier", settings.GlobalRefineYieldModifier, 1.0},
    {"MinTankArmourMultiplier", tweaks.MinTankArmourMultiplier, 1.0},
    {"BallisticPenetrationMaxDistance", tweaks.BallisticPenetrationMaxDistance, 4000.0},
    {"BallisticPenetrationDistanceExponent", tweaks.BallisticPenetrationDistanceExponent, 1.5},
}
for _, row in ipairs(values) do
    out("NATIVE_DEFAULT", row[1], row[2], "EXPECTED_STATIC", row[3])
    assert(row[2] == row[3], "default divergente: " .. row[1])
end
local after = gi.ServerSettings
assert(valid(original) == valid(after), "validade do contexto mudou")
assert(not valid(original) or original:GetAddress() == after:GetAddress(), "contexto foi substituido")
out("CONTEXT_UNCHANGED", "BEFORE_VALID", valid(original), "AFTER_VALID", valid(after))
out("LIMIT", "instancia passiva; nao associada; nao prova dano nem disparo")
