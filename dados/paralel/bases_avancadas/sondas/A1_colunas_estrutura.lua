-- SONDA A1 (SO LEITURA) - canal run.sh. Quais colunas BPStructureDynamicData tem alem das 5 ja exportadas
-- (MaxHealth, ResourceAmounts, AltResourceAmounts, RepairCost, StoredItemCapacity) e o que as linhas de base valem.
-- Regras (AGENTS.md): nunca percorrer toda propriedade de toda linha; so tipos simples; so a lista de chaves abaixo.
-- Esta tabela ja foi percorrida inteira (592 linhas) pelo exportador sem queda; mesmo assim, uma sonda por vez.
local KEYS = { "ForwardBase1", "ForwardBase1BuildSite", "DestroyedForwardBase1", "BorderBase", "FrontierBase",
    "StaticBase1", "TownBase1", "RelicBase1", "HomeRegionBase", "GarrisonStation", "Hospital", "FieldHospital",
    "StorageBox", "Factory" }
local want = {}
for _, k in ipairs(KEYS) do want[k] = true end
local SIMPLE = { BoolProperty = true, IntProperty = true, Int16Property = true, FloatProperty = true,
    NameProperty = true, ByteProperty = true, UInt16Property = true, Int64Property = true }

local dt = LoadAsset("/Game/Blueprints/Data/BPStructureDynamicData.BPStructureDynamicData")
assert(dt and dt:IsValid(), "tabela nao carregou")

-- 1) catalogo de colunas (nome:tipo) pela RowStruct, sem ler valores
local cols = {}
local ok, err = pcall(function()
    dt.RowStruct:ForEachProperty(function(p)
        local n = p:GetFName():ToString()
        local t = p:GetClass():GetFName():ToString()
        cols[#cols + 1] = { n = n, t = t }
        out("COLUNA", n, t)
    end)
end)
if not ok then out("ERRO_RowStruct", tostring(err)) end

-- 2) valores das colunas simples, so das linhas da lista
dt:ForEachRow(function(key, row)
    local k = tostring(key)
    if not want[k] then return end
    for _, c in ipairs(cols) do
        if SIMPLE[c.t] then
            local okv, v = pcall(function() return row[c.n] end)
            if okv and v ~= nil then
                if c.t == "NameProperty" then v = v:ToString() end
                out("LINHA", k, c.n, tostring(v))
            end
        end
    end
end)
out("DONE", "A1: colunas simples de 14 linhas; structs/arrays (ResourceAmounts etc.) nao lidos aqui")
