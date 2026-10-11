-- Canal run.sh: exporta somente colunas conhecidas. Nunca percorrer toda propriedade de toda linha.
-- ProductionResource (receitas) usa ItemCodeName; CodeNameSmallQuantity (estruturas/veiculos) usa CodeName.
local function production(r)
    if r.Quantity == 0 then return nil end
    return r.ItemCodeName:ToString() .. "x" .. r.Quantity
end
local function small(r)
    if r.Quantity == 0 then return nil end
    return r.CodeName:ToString() .. "x" .. r.Quantity
end
local function array(a, read)
    local parts = {}
    a:ForEach(function(_, v)
        local s = read(v:get())
        if s then parts[#parts + 1] = s end
    end)
    return table.concat(parts, "+")
end
local function amounts(ra)
    local first, other = small(ra.Resource), array(ra.OtherResources, small)
    return (first or "") .. (first and other ~= "" and "+" or "") .. other
end
local f = assert(io.open("D:/tools/foxhole-lab/data_costs.txt", "w"))
local function dump(name, describe)
    local dt = LoadAsset("/Game/Blueprints/Data/" .. name .. "." .. name)
    assert(dt and dt:IsValid(), "tabela nao carregou: " .. name)
    f:write("## " .. name .. "\n")
    local n = 0
    dt:ForEachRow(function(key, row)
        -- Erro de schema interrompe a exportacao; nunca converter falha de leitura em custo zero.
        f:write(tostring(key) .. " | " .. describe(row) .. "\n")
        n = n + 1
    end)
    f:flush()
    out(name, n)
end
dump("BPItemDynamicData", function(r)
    return string.format("custo=%s qtd=%d tempo=%.0f", array(r.CostPerCrate, production), r.QuantityPerCrate, r.CrateProductionTime)
end)
dump("BPStructureDynamicData", function(r)
    return string.format("vida=%d custo=%s alt=%s reparo=%d estoque=%d", r.MaxHealth, amounts(r.ResourceAmounts), amounts(r.AltResourceAmounts), r.RepairCost, r.StoredItemCapacity)
end)
dump("BPVehicleDynamicData", function(r)
    return string.format("vida=%d custo=%s comb=%.0f consumo=%.3f carga=%d forca=%.0f blind=%d", r.MaxHealth, amounts(r.ResourceAmounts), r.FuelCapacity, r.FuelConsumptionPerSecond, r.ItemHolderCapacity, r.EngineForce, r.TankArmour)
end)
dump("BPAmmoDynamicData", function(r)
    return string.format("dano=%.0f supr=%.1f raio=%.0f", r.Damage, r.Suppression, r.ExplosionRadius)
end)
f:close()
out("PASS", "dados exportados; vazio significa quantidade zero, nao erro ignorado")
