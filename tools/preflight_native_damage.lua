-- Leitura de contexto nativo, sem ApplyDamage, RPC, inventario ou criacao de servidor.
-- Rodar pelo canal do laboratorio. Campo ausente/objeto nulo nao autoriza recriar dano.
local function hasObjectProperty(obj, name)
    local cls, found = obj:GetClass(), false
    while valid(cls) do
        cls:ForEachProperty(function(p)
            if p:GetFName():ToString() == name then
                assert(p:GetClass():GetFName():ToString() == "ObjectProperty", "schema diferente: " .. name)
                found = true
            end
        end)
        cls = cls:GetSuperStruct()
    end
    return found
end
local w = world()
assert(valid(w), "mundo ausente")
out("WORLD", w:GetFullName())
assert(hasObjectProperty(w, "OwningGameInstance"), "OwningGameInstance nao comprovado")
local gi = w.OwningGameInstance
assert(valid(gi), "GameInstance nulo")
out("GAME_INSTANCE", gi:GetFullName())
assert(hasObjectProperty(gi, "ServerSettings"), "ServerSettings nao comprovado")
local settings = gi.ServerSettings
out("NATIVE_DAMAGE_CONTEXT", "SERVER_SETTINGS_VALID", valid(settings),
    "OBJECT", valid(settings) and settings:GetFullName() or "nulo")
out("LIMIT", "diagnostico somente; nao criar/alterar ServerSettings nem contornar guards")
