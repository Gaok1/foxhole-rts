-- SONDA A4 (SO LEITURA) - canal run.sh, com partida em andamento (pontos de controle criados).
-- Mede, para cada ponto de controle, quantos lugares de uma base avancada passam no predicado proposto na
-- ESPECIFICACAO (secao 3.3): chao Landscape (nunca telhado/veiculo), relevo, folga lateral, e quantas "saidas"
-- (lugares de nascimento ao redor) cada candidato tem. So tracos de linha/esfera; nao cria atores.
-- FOOTPRINT: valor PROVISORIO ate a sonda A3 medir o ForwardBase1 (bounds somente-colidindo). Ajustar HALF.
local HALF, EXIT_R, MAX_SLOPE, MAX_H, EXIT_MIN = 600.0, 800.0, 60.0, 250.0, 3
local NOCOL = CFG.NOCOL

local function landscapeZ(x, y, refZ)
    local h = {}
    if not ksl():LineTraceSingle(world(), { X = x, Y = y, Z = 20000 }, { X = x, Y = y, Z = -5000 }, 0, false, {}, 0, h, true, NOCOL, NOCOL, 0) then return nil end
    local a = h.Actor and h.Actor:get()
    if not valid(a) or not a:GetClass():GetFName():ToString():find("Landscape", 1, true) then return nil, "nao-landscape" end
    local z = h.ImpactPoint.Z
    if refZ and math.abs(z - refZ) > MAX_H then return nil, "desnivel" end
    return z
end

local function spotOk(x, y, ref)
    local z = landscapeZ(x, y, ref)
    if not z then return nil end
    for k = 0, 7 do
        local a = k * math.pi / 4
        local gz = landscapeZ(x + math.cos(a) * HALF, y + math.sin(a) * HALF, ref)
        if not gz or math.abs(gz - z) > MAX_SLOPE then return nil end
    end
    -- folga lateral: esfera de raio HALF*0.5 na altura do tronco, canal de movimento (1)
    if ksl():SphereTraceSingle(world(), { X = x, Y = y, Z = z + HALF * 0.5 + 40 }, { X = x + 1, Y = y, Z = z + HALF * 0.5 + 40 },
        HALF * 0.5, CFG.MOVE_CHANNEL, false, {}, 0, {}, true, NOCOL, NOCOL, 0) then return nil end
    return z
end

local function exits(x, y, z)
    local n = 0
    for k = 0, 7 do
        local a = k * math.pi / 4
        local ex, ey = x + math.cos(a) * EXIT_R, y + math.sin(a) * EXIT_R
        local gz = landscapeZ(ex, ey, z)
        if gz and math.abs(gz - z) <= MAX_SLOPE * 2 then n = n + 1 end
    end
    return n
end

for i, pt in ipairs(points()) do
    local good, tried, best = 0, 0, nil
    for _, r in ipairs({ 0, 150, 300 }) do
        for k = 0, (r == 0 and 0 or 7) do
            local a = k * math.pi / 4
            local x, y = pt.X + math.cos(a) * r, pt.Y + math.sin(a) * r
            tried = tried + 1
            local z = spotOk(x, y, pt.Z)
            if z then
                local e = exits(x, y, z)
                if e >= EXIT_MIN then
                    good = good + 1
                    if not best then best = string.format("%.0f,%.0f,%.0f saidas=%d", x, y, z, e) end
                end
            end
        end
    end
    out("PONTO", i, pt.name, string.format("%.0f,%.0f,%.0f", pt.X, pt.Y, pt.Z), "dono=" .. tostring(pt.owner),
        "candidatos=" .. tried, "validos=" .. good, "primeiro=" .. tostring(best))
end
-- base principal: saidas ao redor de rts.base()
local b = rts.base()
if b then
    local z = landscapeZ(b.X, b.Y)
    out("BASE", string.format("%.0f,%.0f,%.0f", b.X, b.Y, b.Z), "landscapeZ=" .. tostring(z), "saidas=" .. tostring(z and exits(b.X, b.Y, z)))
end
out("DONE", "A4: HALF=" .. HALF .. " provisorio")
