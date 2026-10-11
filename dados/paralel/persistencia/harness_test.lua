-- Suporte de teste (offline, lupa). Executado DEPOIS do candidato completo; `api` vem do retorno do chunk.
-- Substitui so as fronteiras de engine/sistema: arquivos (io/os com semantica do Windows: rename nao
-- sobrescreve), mundo (atores, spawn, traces) e spawn de soldado/ponto/fortificacao. Todo o resto e o
-- codigo real do candidato (sv, logi, economia, clearSquad, sv.restore).
H = { logs = {}, spawnCount = 0, spawnFailAt = nil, pointFail = nil, noSurface = nil, spawned = 0, spawnFailAt2 = nil }
print = function(...)
    local parts = {}
    for i = 1, select("#", ...) do parts[#parts + 1] = tostring(select(i, ...)) end
    H.logs[#H.logs + 1] = table.concat(parts, " ")
end
function H.saw(text)
    for _, l in ipairs(H.logs) do if l:find(text, 1, true) then return true end end
    return false
end

-- Sistema de arquivos falso.
FS = { files = {}, failOpen = {}, failWrite = false, failRename = {}, crash = nil }
local function exists(p) return FS.files[p] ~= nil end
io.open = function(path, mode)
    mode = mode or "r"
    if FS.failOpen[path] then return nil, "negado" end
    if mode:sub(1, 1) == "r" then
        if not exists(path) then return nil, "não existe" end
        local h = {}
        function h:seek(whence) if whence == "end" then return #FS.files[path] end return 0 end
        function h:read() return FS.files[path] end
        function h:close() return true end
        return h
    end
    FS.files[path] = ""  -- abrir para escrita trunca na hora, como o SO
    local h = {}
    function h:write(s)
        if FS.failWrite then FS.files[path] = FS.files[path] .. s:sub(1, #s // 2); return nil, "disco cheio" end
        FS.files[path] = FS.files[path] .. s
        return h
    end
    function h:flush() return true end
    function h:close() return true end
    return h
end
os.rename = function(a, b)
    if FS.crash == a .. ">" .. b then error("QUEDA SIMULADA") end
    if FS.failRename[a .. ">" .. b] or not exists(a) or exists(b) then return nil, "falhou" end
    FS.files[b], FS.files[a] = FS.files[a], nil
    return true
end
os.remove = function(p)
    if not exists(p) then return nil, "não existe" end
    FS.files[p] = nil
    return true
end

-- Mundo falso.
WORLD = { name = "World /Game/Maps/Master/CallumsCapeHex.CallumsCapeHex", addr = 1 }
ACT = {}
local UE = require("UEHelpers")
local w = UE.GetWorld()
w.GetFullName = function() return WORLD.name end
w.GetAddress = function() return WORLD.addr end
local k = UE.GetKismetSystemLibrary()
k.LineTraceSingleForObjects = function(_, _, a, _, _, _, _, _, hit)
    if H.noSurface and H.noSurface(a.X, a.Y) then return false end
    hit.ImpactPoint = { X = a.X, Y = a.Y, Z = 0 }
    return true
end
FindAllOf = function(cls) return ACT[cls] end

function H.actor(cls, x, y, z, yaw)
    local a = { cls = cls, position = { X = x, Y = y, Z = z or 0 }, rot = { Pitch = 0, Yaw = yaw or 0, Roll = 0 },
                bHidden = false, collision = true }
    a.IsValid = function(self) return true end
    a.K2_GetActorLocation = function(self) return self.position end
    a.K2_SetActorLocation = function(self, p) self.position = { X = p.X, Y = p.Y, Z = p.Z } end
    a.K2_GetActorRotation = function(self) return self.rot end
    a.K2_SetActorRotation = function(self, r) self.rot = r end
    a.SetActorHiddenInGame = function(self, h) self.bHidden = h end
    a.SetActorEnableCollision = function(self, c) self.collision = c end
    a.GetActorEnableCollision = function(self) return self.collision end
    a.GetClass = function(self) return { GetFullName = function() return self.cls end,
        GetFName = function() return { ToString = function() return self.cls end } end } end
    a.K2_DestroyActor = function(self) self.bActorIsBeingDestroyed = true end
    a.OnRep_Health = function() end
    ACT[cls] = ACT[cls] or {}
    table.insert(ACT[cls], a)
    return a
end

-- Ativos vivos (sem flag de destruicao) de uma classe.
function H.live(cls)
    local n = 0
    for _, a in ipairs(ACT[cls] or {}) do if not a.bActorIsBeingDestroyed then n = n + 1 end end
    return n
end

LoadAsset = function(path)
    local kind = path:find("Refinery") and "Refinery" or (path:find("Factory") and "Factory" or "TruckW")
    return { kind = kind, IsValid = function() return true end }
end
w.SpawnActor = function(_, cls, l, r)
    if type(cls) ~= "table" or not cls.kind then return nil end
    H.spawned = H.spawned + 1
    local a = H.actor("BP" .. cls.kind .. "_C", l.X, l.Y, l.Z, r and r.Yaw or 0)
    a.Health = cls.kind == "Refinery" and 2700 or (cls.kind == "Factory" and 2000 or 900)
    if H.spawned == H.spawnFailAt2 then a.Health = 1 end
    a.MaxHealth = a.Health
    a.CodeName = { ToString = function() return cls.kind end }
    local ruin = cls.kind == "Refinery" and "BPDestroyedRefinery_C" or "BPDestroyedFactory_C"
    a.BaseStructureClass = { IsValid = function() return true end, GetFullName = function() return ruin end }
    return a
end

-- Hex com campo ativo e ruinas (carga nova: nada implantado). opts.trucks = caminhoes nativos.
function H.newWorld(opts)
    opts = opts or {}
    ACT = {}
    H.actor("BPSalvageField_C", -2500, -3000, 0)
    H.ruinR = H.actor("BPDestroyedRefinery_C", -4000, 3000, 0, 23)
    H.ruinF = H.actor("BPDestroyedFactory_C", opts.factoryX or -5000, 3000, 0, opts.factoryYaw or 23)
    for i = 1, opts.trucks or 0 do H.actor("BPTruckW_C", -5000 + 900 * i, 6000, 0) end
    if opts.active then
        H.actor("BPRefinery_C", -4000, 3000, 0, 23); H.actor("BPFactory_C", opts.factoryX or -5000, 3000, 0, 23)
    end
end

-- Hooks de engine dentro do candidato.
api.hooks.authority(function() return true end)
api.hooks.spawnSoldier(function(x, y, z, slot, team, role)
    H.spawnCount = H.spawnCount + 1
    if H.spawnCount == H.spawnFailAt then return nil end
    local pawn = H.actor("Pawn", x, y, z)
    pawn.Health, pawn.MaxHealth = 100, 100
    return { pawn = pawn, team = team, role = role, slot = slot }
end)
api.hooks.addPoint(function(x, y)
    local P = api.points()
    if #P >= api.CFG.POINT_MAX then return nil end
    for _, q in ipairs(P) do
        if (q.X - x) ^ 2 + (q.Y - y) ^ 2 < (2 * api.CFG.POINT_RADIUS) ^ 2 then return nil end
    end
    if H.pointFail and H.pointFail(x, y) then return nil end
    local pt = { X = x, Y = y, Z = 0, name = string.char(64 + #P + 1), owner = nil, prog = 0, dots = {} }
    P[#P + 1] = pt
    return pt
end)
api.fort.wall = function(x, y, z, yaw) return H.actor("Wall", x, y, z, yaw) end
api.fort.place = function(p)
    local tr = { actor = H.actor("Trench", p.X, p.Y, 0), X = p.X, Y = p.Y, Z = 0 }
    table.insert(api.S.trenches, tr); return tr
end
api.fort.tentAt = function(x, y, yaw)
    local tn = { actor = H.actor("Tent", x, y, 0, yaw), X = x, Y = y, Z = 0, yaw = yaw }
    table.insert(api.S.tents, tn); return tn
end
api.fort.wireAt = function(x, y, yaw)
    local wr = { X = x, Y = y, yaw = yaw, ux = 1, uy = 0, actors = { H.actor("Wire", x, y, 0, yaw) } }
    table.insert(api.S.wires, wr); return wr
end
api.rts.home = { X = 0, Y = 0, Z = 0 }
api.rts.active = true
terrainZ = function(x, y) if H.noGround and H.noGround(x, y) then return nil end return 0 end

function H.unit(role, x, y, team, hp)
    local pawn = H.actor("Pawn", x, y, 0)
    pawn.Health, pawn.MaxHealth = hp or 100, 100
    return { pawn = pawn, team = team or api.CFG.FRIENDLY_TEAM, role = role, kills = 2, ammo = 30, group = 1 }
end

-- Contabilidade observavel: tudo que nao pode aparecer nem sumir num ciclo salvar/continuar.
function H.ledger()
    local L, C = api.logi, api.CFG
    if not L.on then
        local W = api.S.deploy
        return string.format("logi=off bmat=%s | carteira=%s | pontos=%d soldados=%d inimigos=%d", tostring(L.bmat),
            W and string.format("%d/%d/%d", W.bmat, W.spent, #(W.built or {})) or "-", #api.points(), #api.squad(), #api.enemies())
    end
    local parts = { string.format("bmat=%.3f salv=%.3f", L.bmat, L.salvage) }
    parts[#parts + 1] = L.job and string.format("job=%s:%.3f/%.3f", L.job.kind, L.job.left, L.job.total) or "job=-"
    for _, kind in ipairs(C.LOGI.products) do
        local cargo = 0
        for _, tr in ipairs(L.trucks) do cargo = cargo + ((tr.cargo and tr.cargo[kind]) or 0) end
        local deps = (L.base[kind] or 0)
        for _, pt in ipairs(api.points()) do deps = deps + ((pt.dep and pt.dep[kind]) or 0) end
        parts[#parts + 1] = string.format("%s:fac=%d,cargo=%d,dep=%.3f", kind, L.fac[kind] or 0, cargo, deps)
    end
    for i, tr in ipairs(L.trucks) do parts[#parts + 1] = string.format("t%d=%s/%.0f/%s", i, tr.state, tr.hp, tostring(tr.salv)) end
    local W = api.S.deploy
    parts[#parts + 1] = W and string.format("carteira=%d/%d/%d", W.bmat, W.spent, #(W.built or {})) or "carteira=-"
    if L.eSnapshot then  -- IA_LOGISTICA integrada: o estado inimigo e a cadeia dela (razao completo)
        parts[#parts + 1] = "inimigo=" .. H.canon(L.eSnapshot()) .. " soldados=" .. tostring(api.combat.cargo)
    else
        parts[#parts + 1] = string.format("inimigo=%s/%s/%s", tostring(api.combat.cargo), tostring(api.combat.convoys), tostring(api.combat.convoysCut))
    end
    parts[#parts + 1] = string.format("pontos=%d soldados=%d inimigos=%d", #api.points(), #api.squad(), #api.enemies())
    return table.concat(parts, " | ")
end

-- Partida rica: logistica ativa sobre a implantacao, producao em curso, caminhao carregado a caminho de
-- um ponto, estoques em base e ponto, fortificacoes, soldados dos dois lados e estoque inimigo.
function H.richMatch()
    local L, C = api.logi, api.CFG
    assert(L.start(), "logística não iniciou")
    api.addPoint(3000, 0); api.addPoint(6000, 0)
    local P = api.points()
    P[1].owner, P[1].prog = C.FRIENDLY_TEAM, 1
    P[2].owner, P[2].prog = C.ENEMY_TEAM, -1
    L.bmat, L.salvage = 123.5, 40
    L.fac = { ammo = 2, shirts = 1, rifle = 1, medical = 0 }
    L.base.ammo, L.base.shirts, L.base.rifle, L.base.medical = 3, 15, 20, 50
    local dep = L.depotOf(P[1]); dep.ammo, dep.shirts, dep.rifle = 1, 10, 0
    L.job = { kind = "rifle", left = 4.25, total = 14 }
    L.trucks[1].state, L.trucks[1].salv = "toRef", 100
    L.trucks[2].state, L.trucks[2].cargo, L.trucks[2].dest = "toDep", { ammo = 1, shirts = 1, rifle = 0, medical = 1 }, dep
    local S = api.squad()
    S[#S + 1] = H.unit("rifle", 100, 50); S[#S + 1] = H.unit("sniper", 200, 50, nil, 63); S[#S + 1] = H.unit("medic", 300, 50)
    local E = api.enemies()
    E[#E + 1] = H.unit("rifle", 5800, 0, C.ENEMY_TEAM); E[#E].post = P[2]
    api.structures()[1] = H.actor("Wall", 1000, 200, 0, 90)
    api.fort.place({ X = 1500, Y = 0 }); api.fort.tentAt(500, -500, 0); api.fort.wireAt(2000, 0, 45)
    api.combat.auto, api.combat.won, api.combat.wave, api.combat.kills = true, false, 3, 9
    if not L.eSnapshot then api.combat.cargo, api.combat.convoys, api.combat.convoysCut = 1, 4, 2 end
    api.economy.manpower = 77
    api.combat.startT = clock - 120
end

function H.snapshotFiles()
    local out = {}
    for p, c in pairs(FS.files) do out[p] = c end
    return out
end
function H.sameFiles(a)
    for p, c in pairs(a) do if FS.files[p] ~= c then return false end end
    for p in pairs(FS.files) do if a[p] == nil then return false end end
    return true
end

function H.deq(a, b)
    if type(a) ~= type(b) then return false end
    if type(a) ~= "table" then return a == b end
    for k, v in pairs(a) do if not H.deq(v, b[k]) then return false end end
    for k in pairs(b) do if a[k] == nil then return false end end
    return true
end

-- Texto canonico (chaves ordenadas, numeros com 3 casas como no save) para comparar estados.
function H.canon(v)
    if type(v) == "number" then return string.format("%.3f", v) end
    if type(v) ~= "table" then return tostring(v) end
    local keys = {}
    for k in pairs(v) do keys[#keys + 1] = k end
    table.sort(keys, function(a, b) return tostring(a) < tostring(b) end)
    local out = {}
    for _, k in ipairs(keys) do out[#out + 1] = tostring(k) .. "=" .. H.canon(v[k]) end
    return "{" .. table.concat(out, ",") .. "}"
end
