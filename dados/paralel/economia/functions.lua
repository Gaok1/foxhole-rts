-- Bloco de funções substitui need/nextKind; usa contabilidade existente (fac, dep, cargo).
function logi.needs(dep)
    local C, result = CFG.LOGI, {}
    for _, kind in ipairs(C.products) do
        local units = C.recipes[kind].units or 1
        local missing = C.want[kind] - (dep[kind] or 0)
        for _, tr in ipairs(logi.trucks) do
            if tr.state ~= "dead" and tr.dest == dep and tr.cargo then missing = missing - (tr.cargo[kind] or 0) * units end
        end
        local rounding = (kind == "ammo" or kind == "shirts") and 0.5 or 0
        result[kind] = math.max(0, math.ceil(missing / units - rounding))
    end
    return result
end
function logi.need(dep)
    local n = logi.needs(dep)
    return n.ammo, n.shirts
end
function logi.nextKind()
    local C = CFG.LOGI
    if logi.prio ~= "auto" then return C.recipes[logi.prio] and logi.prio or nil end
    local deps, best, ratio = logi.depots(), nil, 2.0
    for _, kind in ipairs(C.products) do
        local units = C.recipes[kind].units or 1
        local have = (logi.fac[kind] or 0) * units
        for _, d in ipairs(deps) do have = have + (d[kind] or 0) end
        for _, tr in ipairs(logi.trucks) do
            if tr.state ~= "dead" and tr.cargo then have = have + (tr.cargo[kind] or 0) * units end
        end
        if logi.job and logi.job.kind == kind then have = have + units end
        local r = have / (C.want[kind] * #deps)
        if r < ratio then best, ratio = kind, r end
    end
    return best
end
function logi.pickDest()
    if logi.pin then
        if logi.pin == logi.base or (logi.pin.pt and logi.pin.pt.owner == CFG.FRIENDLY_TEAM) then return logi.pin end
        logi.pin = nil
    end
    local best, score = nil, 0
    for _, d in ipairs(logi.depots()) do
        local needs, n = logi.needs(d), 0
        for _, kind in ipairs(CFG.LOGI.products) do n = n + needs[kind] * (CFG.LOGI.recipes[kind].units or 1) / CFG.LOGI.want[kind] end
        if n > score then best, score = d, n end
    end
    return best
end
-- Comprimento de estoque/cargo centralizado: caixas -> caixas (retorno) ou unidades (depósito).
function logi.moveCargo(cargo, dest, unpack)
    for _, kind in ipairs(CFG.LOGI.products) do
        local n = cargo[kind] or 0
        dest[kind] = (dest[kind] or 0) + n * (unpack and (CFG.LOGI.recipes[kind].units or 1) or 1)
    end
end
-- Regra própria: médico recebe uma bandagem de depósito aliado próximo a cada tratamento efetivo.
function logi.medicalDepot(m)
    local here, best, distance = loc(m), nil, CFG.POINT_RADIUS
    for _, dep in ipairs(logi.depots()) do
        local d = flatDist(here, dep)
        if (dep.medical or 0) >= 1 and d <= distance then best, distance = dep, d end
    end
    return best
end
