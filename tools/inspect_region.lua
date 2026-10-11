-- Sonda somente de leitura pelo canal run.sh; nao usa teclado/mouse nem a imagem como inventario.
-- As contagens sao de atores carregados agora, nao de tudo que existe numa guerra/servidor.
out("WORLD", world():GetFullName())
out("RTS", rts.active)
local p = playerPawn()
if valid(p) then
    local l = p:K2_GetActorLocation()
    out("COMMANDER", p.Health, l.X, l.Y, l.Z)
end
for _, cls in ipairs({"PlayerStart", "ResourceField", "Refinery", "SpecializedFactory",
    "BPSalvageField_C", "BPRefinery_C", "BPFactory_C", "BPTruckW_C", "BPTruckC_C",
    "BPDestroyedFactory_C", "BPDestroyedRefinery_C", "BPDestroyedVehicleFactory_C",
    "DestroyedStructure", "Landscape", "LandscapeSplinesComponent",
    "LandscapeSplineSegment", "LandscapeSplineControlPoint", "LevelStreaming"}) do
    local count = 0
    for _, a in ipairs(FindAllOf(cls) or {}) do
        if valid(a) then
            count = count + 1
            if count <= 3 then
                out("OBJECT", cls, a:GetFullName())
                if cls:find("^BP") or cls == "PlayerStart" then
                    local l = a:K2_GetActorLocation()
                    out("POSITION", cls, l.X, l.Y, l.Z)
                end
            end
        end
    end
    out("COUNT", cls, count)
end
-- Inclui classes derivadas/variantes que a lista acima nao antecipou; sem ler propriedades desconhecidas.
local counts = {}
for _, a in ipairs(FindAllOf("Actor") or {}) do
    if valid(a) then
        local c = a:GetClass():GetFName():ToString()
        counts[c] = (counts[c] or 0) + 1
    end
end
local names = {}
for c in pairs(counts) do
    local n = c:lower()
    if n:find("factory") or n:find("refin") or n:find("resource") or n:find("field")
        or n:find("truck") or n:find("mine") or n:find("salvage") or n:find("stream") then
        names[#names + 1] = c
    end
end
table.sort(names)
for _, c in ipairs(names) do out("VARIANT", c, counts[c]) end
out("DONE", "Nao inferir ausencia no mapa pela imagem ou somente por uma classe pesquisada.")
