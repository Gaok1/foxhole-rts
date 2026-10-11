-- pv4_B1_forwardbase.lua - ENSAIO B1 da BASE AVANCADA (PACOTE_V4). Preparado e NAO executado. CRIA UM ATOR NATIVO.
-- So com autorizacao do dono do laboratorio, depois das sondas de leitura (pv4_estado, pv4_bases_cena e A1-A4) e DEPOIS do gate de
-- estabilidade. Roda em ESTAGIOS pelo canal (sem botloop):
--     sh D:/tools/foxhole-lab/run.sh pv4_B1_forwardbase.lua      1a vez: carrega a classe, escolhe o lugar, nasce 1 BPForwardBase1_C
--     (esperar 15 s) sh ... pv4_B1_forwardbase.lua               2a vez: relatorio parcial     (esperar 60 s)
--     sh ... pv4_B1_forwardbase.lua                              3a vez: relatorio de 60 s
--     sh D:/tools/foxhole-lab/run.sh pv4_B1_limpar.lua           destroi o ator do ensaio
-- NAO usa logi.fwdBuild: nenhum bmat e debitado, nada entra em logi.fwd / pt.fb / save. O ator e do ensaio e so ele.
-- O que decide (CFG.FWD, bases_avancadas/etapa2/RELATORIO.md secao 6): nasce integra? Health == MaxHealth == 1725? CodeName ==
-- "ForwardBase1"? (strict=true do mod RECUSA se divergir); TeamId (CFG.FWD.teamId=nil hoje: o mod nao escreve); posicao/rotacao
-- como pedidas; ator some com K2_DestroyActor sem residuo; ms do spawn; 60 s de UE4SS.log sem Registry/respawn nativo.
-- Leitura do log: procurar no UE4SS.log (D:\FoxholeLab\Foxhole\War\Binaries\Win64\ue4ss\UE4SS.log) entre o T0 e o fim: "Registry",
-- "ForwardBase", "Spawn", "Access violation". Registrar PID, hash do main e hora de cada estagio.
local L, C = logi, CFG
local function n(x) if x == nil then return "nil" end return string.format("%.1f", x) end
local function now() return gs():GetRealTimeSeconds(world()) end
local function prop(a, name)
    local ok, v = pcall(function() return a[name] end)
    if not ok then return "ERRO(" .. tostring(v) .. ")" end
    if v == nil then return "nil" end
    local t = type(v)
    if t == "number" or t == "boolean" then return tostring(v) end
    local ok2, s = pcall(function() return v:ToString() end)
    if ok2 and s then return tostring(s) end
    return tostring(v)
end

local B = _G.pv4B1
if B and B.actor then
    -- estagios 2 e 3: relatorio
    local a = B.actor
    local ok, alive = pcall(function() return valid(a) and not a.bActorIsBeingDestroyed end)
    out("B1 RELATORIO", "decorrido_s", n(now() - B.t0), "ator_vivo", tostring(ok and alive))
    if ok and alive then
        local l = a:K2_GetActorLocation()
        local r = a:K2_GetActorRotation()
        out("B1 ATOR", "classe", prop(a, "CodeName"), "Health", prop(a, "Health"), "MaxHealth", prop(a, "MaxHealth"), "TeamId", prop(a, "TeamId"),
            "XYZ", n(l.X) .. "," .. n(l.Y) .. "," .. n(l.Z), "yaw", n(r.Yaw), "pedido", n(B.x) .. "," .. n(B.y) .. "," .. n(B.z) .. " yaw " .. n(B.yaw))
        out("B1 ATOR", "GetFullName", select(2, pcall(function() return a:GetFullName() end)))
    end
    out("B1 ESTADO DO MOD", "bases registradas", #L.fwd, "auditoria cadeia inimiga", tostring((L.eAudit and L.eAudit()) or "-"),
        "(o ensaio nao registra a base no mod)")
    out("B1 PROXIMO", B.stage == 2 and "esperar 60 s e rodar de novo; depois pv4_B1_limpar.lua" or "ler o UE4SS.log; depois pv4_B1_limpar.lua")
    B.stage = (B.stage or 1) + 1
    return
end

-- estagio 1: preparar e nascer
assert(L.on, "inicie uma partida com logistica (Shift+F6) antes")
assert(rts.active, "RTS inativo")
local F = C.FWD
local pt
for _, p in ipairs(points()) do if p.owner == C.FRIENDLY_TEAM and not p.fb then pt = p; break end end
assert(pt, "nenhum ponto seu sem base: capture um ponto ou crie com J")
local place, why = L.fwdPlace(pt)
assert(place, "sem lugar valido no ponto " .. pt.name .. ": " .. tostring(why))
out("B1 LUGAR", "ponto", pt.name, "centro", n(place.x) .. "," .. n(place.y) .. "," .. n(place.z), "yaw", n(place.yaw), "saidas", #place.exits)
local cls = LoadAsset(F.asset)
assert(valid(cls), "classe nao carregou: " .. F.asset .. " (caminho INFERIDO; confira o resultado da sonda A2)")
out("B1 CLASSE", "carregou", select(2, pcall(function() return cls:GetFullName() end)))
local t0 = os.clock()
local a = world():SpawnActor(cls, { X = place.x, Y = place.y, Z = place.z }, { Pitch = 0, Yaw = place.yaw, Roll = 0 })
local ms = (os.clock() - t0) * 1000
assert(a ~= nil, "SpawnActor devolveu nil")
local okv, alive = pcall(function() return valid(a) and not a.bActorIsBeingDestroyed end)
_G.pv4B1 = { actor = a, t0 = now(), x = place.x, y = place.y, z = place.z, yaw = place.yaw, stage = 2 }
out("B1 SPAWN", "ms", n(ms), "valido_e_ativo", tostring(okv and alive))
if okv and alive then
    out("B1 ATOR", "CodeName", prop(a, "CodeName"), "Health", prop(a, "Health"), "MaxHealth", prop(a, "MaxHealth"), "TeamId", prop(a, "TeamId"))
    out("B1 CONTRATO strict", "Health==MaxHealth==" .. tostring(F.hp), tostring(prop(a, "Health") == tostring(F.hp) and prop(a, "MaxHealth") == tostring(F.hp)),
        "CodeName==" .. F.code, tostring(prop(a, "CodeName") == F.code))
end
out("B1 PROXIMO", "esperar 15 s e rodar este arquivo de novo (estagio 2); limpar com pv4_B1_limpar.lua ao final")
