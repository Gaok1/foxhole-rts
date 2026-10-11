-- SONDA A2 (SO LEITURA) - canal run.sh. Classes de base/spawn: carregam? pai, CDO, propriedades e UFunctions
-- cujo NOME sugere spawn/estoque/dano. Nao instancia nada (sem SpawnActor). LoadAsset so traz a classe para a memoria.
-- Caminhos: o padrao /Game/Blueprints/Structures/Bases/BP<Nome>.BP<Nome>_C vem da lista do pak (dados/arquivos_do_pak.txt);
-- o sufixo _C e a convencao dos BPs ja usados (BPRefinery_C...). Lote 16 leu CDO assim (TeamId=255).
local NAMES = { "ForwardBase1", "ForwardBase1BuildSite", "DestroyedForwardBase1", "BorderBase", "TownBase1",
    "RelicBase1", "HomeRegionBase", "FortBaseT1", "FrontierBase", "StaticBase1", "SafeHouse", "DestroyedSafeHouse" }
local DIRS = { "/Game/Blueprints/Structures/Bases/", "/Game/Blueprints/Structures/", "/Game/Blueprints/Structures/Forts/" }
local PROP_RX = { "spawn", "respawn", "inventory", "itemholder", "holder", "stock", "capacity", "slot", "team", "faction",
    "health", "owner", "supply", "shirt", "tier", "baseclass" }
local FUNC_RX = { "spawn", "respawn", "stock", "item", "inventory", "damage", "destroy", "health", "team", "capture", "ownership" }

local function hit(name, list)
    local n = name:lower()
    for _, r in ipairs(list) do if n:find(r, 1, true) then return true end end
    return false
end

for _, nm in ipairs(NAMES) do
    local found = false
    for _, dir in ipairs(DIRS) do
        local path = dir .. "BP" .. nm .. ".BP" .. nm .. "_C"
        local okc, cls = pcall(LoadAsset, path)
        if okc and cls and cls:IsValid() then
            found = true
            out("CLASSE", nm, path)
            local chain, c = {}, cls
            for _ = 1, 6 do
                local oks, sup = pcall(function() return c:GetSuperStruct() end)
                if not (oks and sup and sup:IsValid()) then break end
                chain[#chain + 1] = sup:GetFName():ToString()
                c = sup
            end
            out("PAIS", nm, table.concat(chain, " > "))
            pcall(function()
                cls:ForEachProperty(function(p)
                    local pn = p:GetFName():ToString()
                    if hit(pn, PROP_RX) then out("PROP", nm, pn, p:GetClass():GetFName():ToString()) end
                end)
            end)
            pcall(function()
                cls:ForEachFunction(function(f)
                    local fn = f:GetFName():ToString()
                    if hit(fn, FUNC_RX) then out("FUNC", nm, fn) end
                end)
            end)
            -- CDO: so campos ja lidos em lotes anteriores (simples)
            local cdo = StaticFindObject(dir .. "BP" .. nm .. ".Default__BP" .. nm .. "_C")
            if cdo and cdo:IsValid() then
                for _, f in ipairs({ "TeamId", "MaxHealth", "Health", "CodeName" }) do
                    local okv, v = pcall(function() return cdo[f] end)
                    if okv and v ~= nil then
                        if type(v) ~= "number" and type(v) ~= "boolean" then okv, v = pcall(function() return v:ToString() end) end
                        out("CDO", nm, f, tostring(v))
                    end
                end
                local okb, b = pcall(function() return cdo.BaseStructureClass end)
                if okb and b and b:IsValid() then out("CDO", nm, "BaseStructureClass", b:GetFullName()) end
            end
            break
        end
    end
    if not found then out("SEM_CLASSE", nm, "nenhum dos diretorios carregou") end
end
out("DONE", "A2: nenhuma instancia criada")
