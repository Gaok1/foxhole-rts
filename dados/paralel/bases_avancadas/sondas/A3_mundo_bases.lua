-- SONDA A3 (SO LEITURA) - canal run.sh, no mundo JA carregado (HomeRegionW, CallumsCapeHex, DeadLandsHex...).
-- Quais atores de base/spawn/hospital existem agora (ativos E ruinas), onde, com que time/vida, e quais COMPONENTES
-- (so classe e nome; NAO ler propriedades de componente: MasterPoseComponent/AnimClass ja derrubou o UE4SS).
-- Contagem local do estado carregado; zero numa classe nao prova ausencia (AGENTS.md). Rodar sem o robo ativo.
out("WORLD", world():GetFullName())
local RX = { "base", "hospital", "garrison", "safehouse", "spawn", "seaport", "storage", "playerstart", "keep", "bunker" }
local function interesting(name)
    local n = name:lower()
    for _, r in ipairs(RX) do if n:find(r, 1, true) then return true end end
    return false
end
local counts, samples = {}, {}
for _, a in ipairs(FindAllOf("Actor") or {}) do
    if valid(a) then
        local c = a:GetClass():GetFName():ToString()
        if interesting(c) then
            counts[c] = (counts[c] or 0) + 1
            samples[c] = samples[c] or {}
            if #samples[c] < 3 then samples[c][#samples[c] + 1] = a end
        end
    end
end
local names = {}
for c in pairs(counts) do names[#names + 1] = c end
table.sort(names)
local ACTOR = StaticFindObject("/Script/Engine.ActorComponent")
for _, c in ipairs(names) do
    out("CLASSE", c, counts[c])
    for _, a in ipairs(samples[c]) do
        local l = a:K2_GetActorLocation()
        local r = a:K2_GetActorRotation()
        local function field(f)
            local ok, v = pcall(function() return a[f] end)
            if not ok or v == nil then return "-" end
            if type(v) == "number" or type(v) == "boolean" then return tostring(v) end
            local ok2, s = pcall(function() return v:ToString() end)
            return ok2 and s or "?"
        end
        out("ATOR", c, string.format("%.0f,%.0f,%.0f yaw=%.1f", l.X, l.Y, l.Z, r.Yaw), "team=" .. field("TeamId"),
            "hp=" .. field("Health") .. "/" .. field("MaxHealth"), "code=" .. field("CodeName"),
            "hidden=" .. field("bHidden"), "morrendo=" .. field("bActorIsBeingDestroyed"))
        -- bounds: false = todos os componentes (inclui volumes gigantes, nao e footprint); true = so colidindo
        for _, only in ipairs({ false, true }) do
            local o, e = {}, {}
            local ok = pcall(function() a:GetActorBounds(only, o, e) end)
            if ok and e.X then out("BOUNDS", c, "somenteColidindo=" .. tostring(only), string.format("extent %.0f,%.0f,%.0f", e.X, e.Y, e.Z)) end
        end
        if c ~= "PlayerStart" then
            pcall(function()
                local comps = a:K2_GetComponentsByClass(ACTOR)
                local list = {}
                comps:ForEach(function(_, v)
                    local comp = v:get()
                    list[#list + 1] = comp:GetClass():GetFName():ToString() .. ":" .. comp:GetFName():ToString()
                end)
                out("COMPONENTES", c, table.concat(list, " | "))
            end)
        end
    end
end
-- pontos de controle do mod, para distancia aos candidatos (so se houver partida)
pcall(function()
    for i, pt in ipairs(points()) do out("PONTO_DO_MOD", i, pt.name, string.format("%.0f,%.0f,%.0f", pt.X, pt.Y, pt.Z), tostring(pt.owner)) end
end)
out("DONE", "A3: nada foi alterado")
