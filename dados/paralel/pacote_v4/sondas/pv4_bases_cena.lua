-- pv4_bases_cena.lua - SONDA SO DE LEITURA da cena para BASES AVANCADAS (PACOTE_V4). Preparada e NAO executada.
-- Uso (partida com logistica em andamento, pontos criados; sem botloop):
--     sh D:/tools/foxhole-lab/run.sh pv4_bases_cena.lua
-- Para cada ponto de controle: dono, distancia ate a base principal e ate o ponto inimigo mais perto (cm), o que logi.fwdCheck(pt)
-- responde (nil = pode construir; senao o motivo) e o que logi.fwdPlace(pt) acha (centro, saidas livres, ms gastos). fwdCheck e
-- fwdPlace so fazem tracos de linha/esfera (nada de SpawnActor, nada debitado, nenhum estado alterado); estas sao as mesmas
-- chamadas que Shift+J faz, entao a saida diz POR QUE a tecla recusaria. Complementa as sondas A3/A4 de bases_avancadas/sondas.
-- Ao final: quantos pontos sao elegiveis (L2 do roteiro: tem de haver pelo menos um por partida em cada hex testado).
local L, C = logi, CFG
local function n(x) if x == nil then return "nil" end return string.format("%.1f", x) end
local function dist(a, b) local dx, dy = a.X - b.X, a.Y - b.Y return math.sqrt(dx * dx + dy * dy) end
if not L.on then out("LOGISTICA DESLIGADA: inicie uma partida (Shift+F6) e rode de novo"); return end
out("CFG", "minFromBase", C.FWD.minFromBase, "maxToEnemyPoint", C.FWD.maxToEnemyPoint, "half", C.FWD.half, "clear", C.FWD.clear,
    "maxSlope", C.FWD.maxSlope, "minExits", C.FWD.minExits, "exitR", C.FWD.exitR, "max", C.FWD.max, "asset", C.FWD.asset)
local eligible, total = 0, 0
for i, p in ipairs(points()) do
    total = total + 1
    local dBase = dist(p, L.base)
    local dEnemy, en = math.huge, "-"
    for _, q in ipairs(points()) do
        if q.owner == C.ENEMY_TEAM then
            local d = dist(p, q)
            if d < dEnemy then dEnemy, en = d, q.name end
        end
    end
    local why = nil
    local okc, resc = pcall(L.fwdCheck, p)
    if okc then why = resc else why = "ERRO fwdCheck: " .. tostring(resc) end
    local t0 = os.clock()
    local okp, place, pwhy = pcall(L.fwdPlace, p)
    local ms = (os.clock() - t0) * 1000
    local spot = "-"
    if okp and place then
        spot = string.format("centro (%s,%s,%s) yaw %s saidas %d", n(place.x), n(place.y), n(place.z), n(place.yaw), #place.exits)
    elseif okp then spot = "sem lugar: " .. tostring(pwhy)
    else spot = "ERRO fwdPlace: " .. tostring(place) end
    if okc and why == nil and okp and place then eligible = eligible + 1 end
    out("PONTO", i, p.name, "dono", tostring(p.owner), "XY", n(p.X) .. "," .. n(p.Y), "dist_base", n(dBase),
        "dist_ponto_inimigo", dEnemy == math.huge and "-" or (n(dEnemy) .. " (" .. en .. ")"),
        "fwdCheck", tostring(why or "OK (pode)"), "fwdPlace", spot, "fwdPlace_ms", n(ms), "base_ja", tostring(p.fb ~= nil))
end
out("RESUMO", "pontos", total, "elegiveis (fwdCheck OK e lugar achado)", eligible, "bases", #L.fwd, "pedido", L.fwdOrder and L.fwdOrder.pt.name or "-",
    "bmat", n(L.bmat), "reserva caminhao", L.rebuildReserve and L.rebuildReserve() or "-")
