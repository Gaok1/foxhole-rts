-- ===== BASES AVANCADAS (inicio do bloco; ver CFG.FWD) =====
-- Soldados de combate (trabalhadores da coleta nao contam no SQUAD_MAX; o limite deles e CFG.COLETA.workers).
function rts.combatCount()
    local n = 0
    for _, m in ipairs(squad) do if m.role ~= "worker" then n = n + 1 end end
    return n
end

-- Slots de caixa ocupados num deposito (caixa parcial ocupa 1 slot): municao em caixas, camisas/fuzis/bandagens em unidades.
function logi.slotsUsed(dep)
    local R = CFG.LOGI.recipes
    local function c(x) return math.ceil((x or 0) - 1e-9) end
    return c(dep.ammo) + c((dep.shirts or 0) / R.shirts.units) + c((dep.rifle or 0) / R.rifle.units) + c((dep.medical or 0) / R.medical.units)
end

-- Deposito que nasce soldado: a base principal ou a base avancada ATIVA (ponto ainda nosso).
function logi.spawnCapable(dep)
    if dep == logi.base then return true end
    if CFG.SPAWN.pointSpawn then return true end   -- true restaura o antigo: todo ponto (sem base) recebe camisas/fuzis
    local fb = dep.fb
    return fb ~= nil and not fb.dead and dep.pt ~= nil and dep.pt.owner == CFG.FRIENDLY_TEAM
end

-- Slots livres para a carga de um caminhao (descontando o que ja vai a caminho); base principal e ponto sem base: sem teto.
function logi.fwdFree(dep)
    if not dep.fb then return math.huge end
    local used = logi.slotsUsed(dep)
    for _, tr in ipairs(logi.trucks) do
        if tr.state ~= "dead" and tr.dest == dep and tr.cargo then
            for _, kind in ipairs(CFG.LOGI.products) do used = used + (tr.cargo[kind] or 0) end
        end
    end
    return math.max(0, CFG.FWD.cap - used)
end

function logi.fwdReserve() return logi.fwdOrder and logi.fwdOrder.cost or 0 end

-- Razao por base (camisas e fuzis, inteiros): inicial + recebido == estoque + consumido + perdido.
function logi.fwdAudit(fb)
    local L = fb.led
    for _, k in ipairs({ "shirts", "rifle" }) do
        local have = fb.dead and 0 or (fb.dep[k] or 0)   -- perdida: o estoque virou 'perdido' (o deposito pode ser reaproveitado por outra base)
        if L.init[k] + L.rx[k] ~= have + L.used[k] + L.lost[k] then return false, k end
    end
    return true
end

function logi.fwdMake(pt, x, y, z, yaw, hp, actor, exits)
    local dep = logi.depotOf(pt)
    local fb = { pt = pt, dep = dep, code = CFG.FWD.code, X = x, Y = y, Z = z, yaw = yaw, hp = hp, maxHp = CFG.FWD.hp, actor = actor,
        exits = exits, exitI = 0, dead = false,
        led = { init = { shirts = dep.shirts or 0, rifle = dep.rifle or 0 }, rx = { shirts = 0, rifle = 0 },
                used = { shirts = 0, rifle = 0 }, lost = { shirts = 0, rifle = 0 } } }
    pt.fb, dep.fb = fb, fb
    logi.fwd[#logi.fwd + 1] = fb
    return fb
end

-- Saidas de nascimento: pontos num anel ao redor da base, SO chao Landscape (nunca telhado) e capsula livre.
-- Calculadas na construcao e na restauracao; nunca com groundZ (o canal Visibility acerta telhado).
function logi.fwdExits(x, y, z)
    local F, out = CFG.FWD, {}
    for k = 0, 7 do
        local a = k * math.pi / 4
        local ex, ey = x + math.cos(a) * F.exitR, y + math.sin(a) * F.exitR
        local gz = logi.parkingGround(ex, ey, { Z = z })
        if gz and math.abs(gz - z) <= 2 * F.maxSlope
            and not ksl():SphereTraceSingle(world(), { X = ex, Y = ey, Z = gz + 130 }, { X = ex, Y = ey, Z = gz + 131 }, 50,
                CFG.MOVE_CHANNEL, false, {}, 0, {}, true, CFG.NOCOL, CFG.NOCOL, 0) then
            out[#out + 1] = { X = ex, Y = ey, Z = gz }
        end
    end
    return out
end

-- O footprint (anel de 8 pontos a `half`) e Landscape plano, sem obra do mod por perto e com varredura de esfera livre.
function logi.fwdFits(x, y, z)
    local F = CFG.FWD
    for k = 0, 7 do
        local a = k * math.pi / 4
        local gz = logi.parkingGround(x + math.cos(a) * F.half, y + math.sin(a) * F.half, { Z = z })
        if not gz or math.abs(gz - z) > F.maxSlope then return false, "fora de superfície (terreno irregular ou não é chão)" end
    end
    local here = { X = x, Y = y }
    for _, o in ipairs(structures) do
        if valid(o) and flatDist(here, o:K2_GetActorLocation()) < F.half + F.clear then return false, "barreira do mod no caminho" end
    end
    for _, list in ipairs({ S.trenches, S.tents, S.wires }) do
        for _, o in ipairs(list) do
            if flatDist(here, o) < F.half + F.clear then return false, "obra do mod (trincheira/posto/arame) no caminho" end
        end
    end
    if ksl():SphereTraceSingle(world(), { X = x - F.half, Y = y, Z = z + F.half / 2 + 40 }, { X = x + F.half, Y = y, Z = z + F.half / 2 + 40 },
        F.half / 2, CFG.MOVE_CHANNEL, false, {}, 0, {}, true, CFG.NOCOL, CFG.NOCOL, 0) then return false, "obstáculo no terreno" end
    return true
end

-- Procura o lugar: centros a 0 / 150 / 300 cm do centro do ponto (1 + 8 + 8), yaw voltado ao inimigo mais perto.
function logi.fwdPlace(pt)
    local F = CFG.FWD
    local yaw = (fort.facing({ X = pt.X, Y = pt.Y }, enemies) or 90) - 90
    local offs = { { 0, 0 } }
    for _, r in ipairs({ 150, 300 }) do
        for k = 0, 7 do offs[#offs + 1] = { math.cos(k * math.pi / 4) * r, math.sin(k * math.pi / 4) * r } end
    end
    local why = "sem superfície livre"
    for _, o in ipairs(offs) do
        local x, y = pt.X + o[1], pt.Y + o[2]
        local z = logi.parkingGround(x, y, pt)
        if z then
            local fits, w = logi.fwdFits(x, y, z)
            if fits then
                local exits = logi.fwdExits(x, y, z)
                if #exits >= F.minExits then return { x = x, y = y, z = z, yaw = yaw, exits = exits } end
                why = string.format("poucas saídas livres (%d < %d)", #exits, F.minExits)
            else why = w end
        end
    end
    return nil, why
end

-- Spawn do ator com os asserts do contrato (como logi.applyPlan); em falha desfaz o que nasceu. Retorna ator ou nil, motivo.
function logi.fwdSpawn(cls, x, y, z, yaw)
    local F, a = CFG.FWD, nil
    local ok, why = pcall(function()
        a = world():SpawnActor(cls, { X = x, Y = y, Z = z }, { Pitch = 0, Yaw = yaw, Roll = 0 })
        assert(valid(a) and not a.bActorIsBeingDestroyed, "base não nasceu ativa")
        if F.strict then
            assert(a.Health == F.hp and a.MaxHealth == F.hp, "vida inicial da base divergiu")
            assert(a.CodeName:ToString() == F.code, "CodeName da base divergiu")
        end
        local l = a:K2_GetActorLocation()
        assert(flatDist(l, { X = x, Y = y }) < 100 and math.abs(l.Z - z) < 100, "base deslocada")
        local dy = math.abs((a:K2_GetActorRotation().Yaw - yaw) % 360)
        assert(math.min(dy, 360 - dy) < 1, "rotação da base divergiu")
        if F.teamId ~= nil then a.TeamId = F.teamId end
    end)
    if not ok then
        if valid(a) and not a.bActorIsBeingDestroyed then pcall(function() a:K2_DestroyActor() end) end
        return nil, tostring(why)
    end
    return a
end

-- Condicoes de construcao que nao dependem de bmat (valem de novo ao executar um pedido pendente). nil = pode; senao o motivo.
function logi.fwdCheck(pt)
    local F = CFG.FWD
    if not logi.on or combat.mode == "assault" then return "bases avançadas só numa partida com logística (fora do Assalto)" end
    if not rts.active or not isLocalAuthority() then return "precisa do modo RTS com autoridade local" end
    if F.visual ~= "native" then return "visual '" .. tostring(F.visual) .. "' (plano B) não implementado" end
    if pt.owner ~= CFG.FRIENDLY_TEAM then return "o ponto " .. pt.name .. " não é seu" end
    if pt.fb then return "já há base avançada no ponto " .. pt.name end
    if #logi.fwd >= F.max then return "limite de bases avançadas (" .. F.max .. ")" end
    if pt.dep and logi.slotsUsed(pt.dep) > F.cap then
        return string.format("o depósito do ponto %s guarda %d slots (teto da base: %d)", pt.name, logi.slotsUsed(pt.dep), F.cap)
    end
    local o = logi.fwdOrder
    if o and o.pt ~= pt then return "já há um pedido de base avançada pendente (ponto " .. o.pt.name .. ")" end
    if presence(enemies, pt) > 0 then return "há inimigos no ponto " .. pt.name end
    local far = flatDist(pt, logi.base) >= F.minFromBase
    if not far then
        for _, q in ipairs(points) do
            if q.owner == CFG.ENEMY_TEAM and flatDist(pt, q) <= F.maxToEnemyPoint then far = true end
        end
    end
    if not far then
        return string.format("ponto %s perto demais da base (mín. %.0f m) e longe de pontos inimigos (%.0f m)", pt.name,
            F.minFromBase / 100, F.maxToEnemyPoint / 100)
    end
    return nil
end

-- Constroi no ponto. Retorna true | false, motivo, tipo ("bmat" = falta bmat; "fail"). Debita bmat SO depois do ator validado.
function logi.fwdBuild(pt)
    local F = CFG.FWD
    local why = logi.fwdCheck(pt)
    if why then return false, why, "fail" end
    local free = logi.bmat - logi.rebuildReserve()   -- caminhao destruido tem prioridade sobre a base
    if free < F.cost then
        return false, string.format("faltam %.0f bmat (fábrica tem %.0f)", F.cost - free, logi.bmat), "bmat"
    end
    local cls = LoadAsset(F.asset)
    if not valid(cls) then return false, "classe da base avançada não carregou", "fail" end
    local plan, w = logi.fwdPlace(pt)
    if not plan then return false, "sem lugar: " .. tostring(w), "fail" end
    local a, err = logi.fwdSpawn(cls, plan.x, plan.y, plan.z, plan.yaw)
    if not a then return false, "ator recusado, nada debitado: " .. tostring(err), "fail" end
    logi.fwdMake(pt, plan.x, plan.y, plan.z, plan.yaw, F.hp, a, plan.exits)
    logi.bmat = logi.bmat - F.cost
    logi.fwdBuilt = (logi.fwdBuilt or 0) + 1
    notify(string.format("BASE AVANÇADA %s construída (-%d bmat; fábrica %.0f). Mande caminhões com camisas e fuzis (L sobre ela)", pt.name, F.cost, logi.bmat), 6.0)
    return true
end

-- Shift+J: 1o toque mostra custo e local; 2o toque (mesmo ponto, F.confirm s em tempo real) constroi ou reserva o bmat.
function logi.fwdKey(c)
    local F = CFG.FWD
    if not logi.on or combat.mode == "assault" then
        notify("bases avançadas só numa partida com logística (fora do Assalto)", 3.0); return false
    end
    if not c then return false end
    local pt, any
    for _, q in ipairs(points) do
        if flatDist(c, q) <= CFG.POINT_RADIUS then any = q; if q.owner == CFG.FRIENDLY_TEAM then pt = q end end
    end
    if not pt then
        S.fwdConfirm = nil
        notify(any and ("o ponto " .. any.name .. " não é seu") or "Shift+J: ponha o cursor dentro de um ponto de controle seu", 3.0)
        return false
    end
    local rt = gs():GetRealTimeSeconds(world())
    local cf = S.fwdConfirm
    local again = cf and cf.pt == pt and rt - cf.t <= F.confirm
    if pt.fb then
        S.fwdConfirm = nil
        notify(string.format("BASE AVANÇADA %s: %s", pt.name, logi.fwdLine(pt.dep)), 5.0)
        return false
    end
    local o = logi.fwdOrder
    if o and o.pt == pt then
        if again then
            S.fwdConfirm, logi.fwdOrder = nil, nil
            notify("pedido de base avançada cancelado: a fábrica volta a produzir", 4.0)
        else
            S.fwdConfirm = { pt = pt, t = rt }
            notify(string.format("pedido pendente em %s (a fábrica guarda %d bmat). Shift+J de novo em %.0f s cancela", pt.name, o.cost, F.confirm), 4.0)
        end
        return false
    end
    local why = logi.fwdCheck(pt)
    if why then S.fwdConfirm = nil; notify(why, 4.0); return false end
    if not again then
        S.fwdConfirm = { pt = pt, t = rt }
        local free = logi.bmat - logi.rebuildReserve()
        if free >= F.cost then
            notify(string.format("Base avançada em %s: %d bmat (fábrica tem %.0f). Shift+J de novo em %.0f s para construir", pt.name, F.cost, logi.bmat, F.confirm), 5.0)
        else
            notify(string.format("Base avançada em %s: %d bmat, faltam %.0f (fábrica tem %.0f). Shift+J de novo em %.0f s reserva o bmat e a fábrica para até juntar",
                pt.name, F.cost, F.cost - free, logi.bmat, F.confirm), 6.0)
        end
        return false
    end
    S.fwdConfirm = nil
    local ok, w, kind = logi.fwdBuild(pt)
    if ok then return true end
    if kind == "bmat" then
        logi.fwdOrder = { pt = pt, cost = F.cost, t0 = now() }
        notify(string.format("pedido de base avançada em %s registrado: %s; a fábrica guarda %d bmat (até %.0f s)", pt.name, w, F.cost, F.pending), 6.0)
    else
        notify("base avançada recusada, nada debitado: " .. tostring(w), 6.0)
    end
    return false
end

-- Pedido pendente: constroi sozinho quando o bmat (descontada a reserva de caminhao) chega; cancela por prazo ou condicao perdida.
function logi.fwdTick(dt, t)
    local o = logi.fwdOrder
    if not o then return end
    local function cancel(why)
        logi.fwdOrder = nil
        notify("pedido de base avançada em " .. o.pt.name .. " cancelado (" .. why .. "); a fábrica volta a produzir", 5.0)
    end
    if t - o.t0 > CFG.FWD.pending then return cancel("tempo esgotado") end
    local why = logi.fwdCheck(o.pt)
    if why then return cancel(why) end
    if logi.bmat - logi.rebuildReserve() < o.cost then return end
    local ok, w, kind = logi.fwdBuild(o.pt)
    if ok then logi.fwdOrder = nil
    elseif kind ~= "bmat" then cancel(tostring(w)) end
end

-- Perda unica e idempotente (captura, morteiro): conta o que se perde, zera o deposito, destroi o ator, solta o ponto.
function logi.fwdLose(fb, why)
    if not fb or fb.dead then return false end
    fb.dead = true
    local dep = fb.dep
    local ls, lr = dep.shirts or 0, dep.rifle or 0
    fb.led.lost.shirts, fb.led.lost.rifle = fb.led.lost.shirts + ls, fb.led.lost.rifle + lr
    for _, kind in ipairs(CFG.LOGI.products) do dep[kind] = 0 end
    local a = fb.actor
    fb.actor = nil
    if a and valid(a) and not a.bActorIsBeingDestroyed then pcall(function() a:K2_DestroyActor() end) end
    if CFG.FWD.ruin then pcall(logi.fwdRuin, fb) end
    if fb.pt.fb == fb then fb.pt.fb = nil end
    if dep.fb == fb then dep.fb = nil end
    for i = #logi.fwd, 1, -1 do if logi.fwd[i] == fb then table.remove(logi.fwd, i) end end
    logi.fwdLost = (logi.fwdLost or 0) + 1
    pcall(rts.alert, "perdido", fb.pt, string.format("BASE AVANÇADA %s %s: perdeu %d camisas e %d fuzis", fb.pt.name,
        why == "capturada" and "capturada" or "destruída", ls, lr))
    return true
end

function logi.fwdRuin(fb)
    local cls = LoadAsset(CFG.FWD.ruinAsset)
    if not valid(cls) then return end
    local r = world():SpawnActor(cls, { X = fb.X, Y = fb.Y, Z = fb.Z }, { Pitch = 0, Yaw = fb.yaw, Roll = 0 })
    if valid(r) and not r.bActorIsBeingDestroyed then S.fwdRuins[#S.fwdRuins + 1] = r end
end

-- Morteiro inimigo (logi.blast com team inimigo): base dentro de radius*1.5 leva dmg*blastMul (vida do MOD).
function logi.fwdBlast(hit, radius, dmg)
    local list = {}
    for _, fb in ipairs(logi.fwd) do list[#list + 1] = fb end
    for _, fb in ipairs(list) do
        if not fb.dead and flatDist(hit, fb) <= radius * 1.5 then
            fb.hp = fb.hp - dmg * CFG.FWD.blastMul
            if fb.hp <= 0 then logi.fwdLose(fb, "destruída")
            else pcall(rts.alert, "sobfogo", fb.pt, "base avançada " .. fb.pt.name .. " sob fogo") end
        end
    end
end

-- Reinicio da partida/logistica: destroi os atores das bases (o estagio do Continuar NAO e tocado) e os pedidos.
function logi.fwdReset()
    for _, fb in ipairs(logi.fwd or {}) do
        local a = fb.actor
        fb.actor, fb.dead = nil, true
        if a and valid(a) and not a.bActorIsBeingDestroyed then pcall(function() a:K2_DestroyActor() end) end
        if fb.pt and fb.pt.fb == fb then fb.pt.fb = nil end
        if fb.dep and fb.dep.fb == fb then fb.dep.fb = nil end
    end
    logi.fwd = {}
    for _, r in ipairs(S.fwdRuins or {}) do
        if valid(r) and not r.bActorIsBeingDestroyed then pcall(function() r:K2_DestroyActor() end) end
    end
    S.fwdRuins, S.fwdConfirm = {}, nil
    logi.fwdOrder, logi.exitN = nil, 0
end

-- Linha do painel (pura, <= 96 caracteres): estoque, slots e se a base reforca.
function logi.fwdLine(dep)
    local fb = dep.fb
    local sh, ri = dep.shirts or 0, dep.rifle or 0
    local name = dep == logi.base and "base" or ("base " .. tostring(dep.name))
    local slots = fb and string.format("%d/%d", logi.slotsUsed(dep), CFG.FWD.cap) or "—"
    local state
    if fb and dep.pt and dep.pt.owner ~= CFG.FRIENDLY_TEAM then state = "INATIVA (ponto neutro)"
    elseif sh < 1 then state = "reforça: NÃO (sem camisas)"
    elseif ri < 1 then state = "reforça: só sem fuzil (sem fuzis)"
    else state = "reforça: tudo" end
    return string.format("%s | camisas %d | fuzis %d | slots %s | %s", name, sh, ri, slots, state)
end

-- Existe como reforcar? Estrutura ativa com >= 1 camisa, caixa de camisa pronta na fabrica ou caminhao carregando camisas.
function logi.canReinforce()
    if not logi.on then return false end
    if (logi.base.shirts or 0) >= 1 then return true end
    for _, fb in ipairs(logi.fwd) do
        if not fb.dead and fb.pt.owner == CFG.FRIENDLY_TEAM and (fb.dep.shirts or 0) >= 1 then return true end
    end
    if (logi.fac.shirts or 0) >= 1 then return true end
    for _, tr in ipairs(logi.trucks) do
        if tr.state ~= "dead" and tr.cargo and (tr.cargo.shirts or 0) >= 1 then return true end
    end
    return false
end

-- Derrota por falta de tropa: ramo logistico = nenhum soldado de combate e nenhum jeito de reforcar; legado/Assalto = mao de obra.
function logi.noReinforce()
    if logi.on and combat.mode ~= "assault" then return rts.combatCount() == 0 and not logi.canReinforce() end
    return #squad == 0 and economy.manpower < CFG.WEAPONS.rifle.cost
end

-- Interface comum de nascimento (ESPECIFICACAO 4.3). PURA: nao muda estoque, nem rodizio de saidas, nem cria ator.
-- Retorna site = {dep, kind = "base"|"fwd"|"point", name, fb, at = {X, Y, Z, exact = true}, need = {shirts, rifle}, explicit} ou nil + motivo.
function logi.spawnSite(role, cursor, opts)
    local R = CFG.SPAWN.roles[role]
    if not R then return nil, "função sem receita" end
    if not logi.on or (combat.mode == "assault" and role ~= "worker") then return nil, "ramo legado" end
    local allow = {}
    for _, k in ipairs((opts and opts.sites) or R.sites or { "base", "fwd" }) do allow[k] = true end
    if CFG.SPAWN.pointSpawn and not (opts and opts.sites) and not R.sites then allow.point = true end
    local need = { shirts = R.shirts or 0, rifle = R.rifle or 0 }
    local cands, inactive = {}, {}
    local dep0 = (role == "worker") and logi.workerDepot() or logi.base
    if allow.base and dep0 then cands[#cands + 1] = { dep = dep0, kind = "base", name = dep0.name or "base", X = dep0.X, Y = dep0.Y } end
    if allow.fwd then
        for _, fb in ipairs(logi.fwd) do
            local c = { dep = fb.dep, kind = "fwd", fb = fb, name = "base avançada " .. tostring(fb.pt.name), X = fb.pt.X, Y = fb.pt.Y }
            if not fb.dead and fb.pt.owner == CFG.FRIENDLY_TEAM then cands[#cands + 1] = c else inactive[#inactive + 1] = c end
        end
    end
    if allow.point then
        for _, pt in ipairs(points) do
            if pt.owner == CFG.FRIENDLY_TEAM and not pt.fb then
                cands[#cands + 1] = { dep = logi.depotOf(pt), kind = "point", name = "ponto " .. tostring(pt.name), X = pt.X, Y = pt.Y }
            end
        end
    end
    if #cands == 0 and #inactive == 0 then return nil, "nenhum local de nascimento permitido" end
    local function short(c)   -- motivo pelo qual c nao reforca (nil = pode)
        local dep = c.dep
        if c.kind == "fwd" and (not c.fb.exits or #c.fb.exits == 0) then return c.name .. " sem saídas livres" end
        local keep = (role == "worker") and 0 or logi.workerReserve(dep)
        if (dep.shirts or 0) < need.shirts + keep then
            return keep > 0 and "camisas reservadas aos trabalhadores da coleta" or ("sem camisas em " .. c.name)
        end
        if (dep.rifle or 0) < need.rifle then return "sem fuzis em " .. c.name end
        return nil
    end
    local explicit = nil
    if cursor and cursor.X and cursor.Y then   -- cursor dentro do anel de uma base: so ela conta (nunca cai para outra em silencio)
        local bd = math.huge
        for _, list in ipairs({ cands, inactive }) do
            for _, c in ipairs(list) do
                local d = flatDist(cursor, c)
                if d <= CFG.POINT_RADIUS and d < bd then explicit, bd = c, d end
            end
        end
    end
    local pick
    if explicit then
        for _, c in ipairs(inactive) do
            if c == explicit then return nil, explicit.name .. " inativa (o ponto não é seu): recapture-o" end
        end
        local why = short(explicit)
        if why then return nil, why .. "; mova o cursor para fora das bases para usar a mais próxima com estoque" end
        pick = explicit
    else
        local ref = (cursor and cursor.X and cursor.Y) and cursor or squadCenter()
        if not ref then   -- sem cursor e sem esquadrao: a frente = ponto inimigo mais perto da base
            local bd = math.huge
            for _, q in ipairs(points) do
                if q.owner == CFG.ENEMY_TEAM and flatDist(q, logi.base) < bd then ref, bd = q, flatDist(q, logi.base) end
            end
        end
        ref = ref or logi.base
        local best, bd, nd, nwhy = nil, math.huge, math.huge, nil
        for _, c in ipairs(cands) do
            local d, why = flatDist(ref, c), short(c)
            if d < nd then nd, nwhy = d, why end
            if not why and d < bd then best, bd = c, d end
        end
        if not best then return nil, nwhy or "nenhum local de nascimento permitido" end
        pick = best
    end
    local dep, at = pick.dep, nil
    if pick.kind == "fwd" then
        local e = pick.fb.exits[(pick.fb.exitI % #pick.fb.exits) + 1]
        at = { X = e.X, Y = e.Y, Z = e.Z, exact = true }
    elseif pick.kind == "point" then
        at = { X = pick.X, Y = pick.Y, Z = dep.Z, name = dep.name }
    else
        local a = ((logi.exitN or 0) + 1) * 1.7   -- anel de saidas simples ao redor da base principal
        at = { X = dep.X + math.cos(a) * 250, Y = dep.Y + math.sin(a) * 250, Z = dep.Z, exact = true, ground = true }
    end
    return { dep = dep, kind = pick.kind, name = pick.name, fb = pick.fb, explicit = explicit ~= nil, need = need, at = at }
end

-- Depois do ator confirmado: revalida e debita (UNICO ponto que gasta camisa/fuzil de nascimento no codigo novo); gira a saida; razao.
function logi.spawnCommit(site, role)
    local dep, need = site and site.dep, site and site.need
    if not dep or not need then return false, "site inválido" end
    local fb = site.fb
    if fb and (fb.dead or fb.pt.owner ~= CFG.FRIENDLY_TEAM) then
        log("spawnCommit recusado: base indisponível (" .. tostring(role) .. ")")
        return false, "base indisponível"
    end
    if (dep.shirts or 0) < need.shirts or (dep.rifle or 0) < need.rifle then
        log("spawnCommit recusado: estoque mudou (" .. tostring(role) .. ")")
        return false, "estoque insuficiente"
    end
    dep.shirts, dep.rifle = (dep.shirts or 0) - need.shirts, (dep.rifle or 0) - need.rifle
    if fb then
        fb.exitI = (fb.exitI or 0) + 1
        fb.led.used.shirts, fb.led.used.rifle = fb.led.used.shirts + need.shirts, fb.led.used.rifle + need.rifle
    elseif site.kind == "base" then logi.exitN = (logi.exitN or 0) + 1 end
    return true
end

-- Recrutar no ramo logistico (fora do Assalto): decidir (spawnSite) -> criar (spawnSquad) -> debitar (spawnCommit). Sem mao de obra.
function logi.recruit(role, at)
    local w = CFG.WEAPONS[role]
    if not w then return false end
    local cursor = nil
    if at and at.X and at.Y then cursor = at
    elseif rts.active then local ok, c = pcall(cursorPoint); if ok then cursor = c end end
    local site, why = logi.spawnSite(role, cursor)
    if not site then notify(why or "sem local de nascimento", 4.0); return false end
    if spawnSquad(1, role, site.at) < 1 then return false end   -- falha de spawn: nada debitado
    local m = squad[#squad]
    local ok, why2 = logi.spawnCommit(site, role)
    if not ok then   -- estoque mudou entre decidir e criar (nao deveria: game thread sincrono): desfaz o ator
        table.remove(squad)
        pcall(destroyMarker, m)
        pcall(function() m.pawn:K2_DestroyActor() end)
        releaseController(m.hpc)
        notify("recrutamento desfeito: " .. tostring(why2), 3.0)
        return false
    end
    notify(string.format("recrutado %s em %s (-1 camisa%s) | camisas %d, fuzis %d", w.name, site.name,
        site.need.rifle > 0 and ", -1 fuzil" or "", site.dep.shirts or 0, site.dep.rifle or 0), 3.0)
    return true
end

-- ---- Persistencia: extensao `fwd` v1 do schema v2 (por indice de ponto/XYZ/yaw/hp; nunca ator) ----
function logi.fwdSnapshot()
    if not logi.on then return nil end
    local list = {}
    for _, fb in ipairs(logi.fwd) do
        if not fb.dead then
            local idx
            for i, pt in ipairs(points) do if pt == fb.pt then idx = i end end
            if idx then list[#list + 1] = { pt = idx, code = fb.code, x = fb.X, y = fb.Y, z = fb.Z, yaw = fb.yaw, hp = fb.hp } end
        end
    end
    if #list == 0 then return nil end
    return { version = CFG.PERSIST.fwdVersion, list = list }
end

-- Validacao pura do bloco d.fwd contra o save d (pontos e logistica DO SAVE). true ou nil, motivo.
function logi.fwdValid(d)
    local P, F, W = CFG.PERSIST, CFG.FWD, d.fwd
    local function fin(x) return type(x) == "number" and x == x and x ~= math.huge and x ~= -math.huge end
    local function coord(x) return fin(x) and math.abs(x) <= P.maxCoord end
    if type(W) ~= "table" then return nil, "bases avançadas" end
    if d.logi == nil then return nil, "bases avançadas sem logística" end
    for k in pairs(W) do if k ~= "version" and k ~= "list" then return nil, "bases campo " .. tostring(k) end end
    if W.version ~= P.fwdVersion then
        return nil, (type(W.version) == "number" and W.version > P.fwdVersion) and "bases de versão futura" or "bases versão"
    end
    local list = W.list
    if type(list) ~= "table" then return nil, "bases lista" end
    local n = 0
    for k in pairs(list) do
        if type(k) ~= "number" or k % 1 ~= 0 or k < 1 or k > #list then return nil, "bases lista" end
        n = n + 1
    end
    if n ~= #list or n > F.max then return nil, "bases lista" end
    local pts, seen = d.points or {}, {}
    for i, r in ipairs(list) do
        if type(r) ~= "table" then return nil, "base " .. i end
        for k in pairs(r) do
            if k ~= "pt" and k ~= "code" and k ~= "x" and k ~= "y" and k ~= "z" and k ~= "yaw" and k ~= "hp" then return nil, "base " .. i .. " campo " .. tostring(k) end
        end
        if type(r.pt) ~= "number" or r.pt % 1 ~= 0 or r.pt < 1 or r.pt > #pts or seen[r.pt] then return nil, "base " .. i .. " ponto" end
        seen[r.pt] = true
        if r.code ~= F.code then return nil, "base " .. i .. " código" end
        if not (coord(r.x) and coord(r.y) and coord(r.z) and fin(r.yaw)) then return nil, "base " .. i .. " posição" end
        if not (fin(r.hp) and r.hp > 0 and r.hp <= F.hp) then return nil, "base " .. i .. " vida" end
        local q = pts[r.pt]
        if flatDist({ X = r.x, Y = r.y }, { X = q.x, Y = q.y }) > CFG.POINT_RADIUS then return nil, "base " .. i .. " longe do ponto" end
        if q.owner == CFG.ENEMY_TEAM then return nil, "base " .. i .. " em ponto inimigo" end
        local s = d.logi.pts and d.logi.pts[r.pt]
        if s then
            local R = CFG.LOGI.recipes
            local function c(x) return math.ceil((x or 0) - 1e-9) end
            local slots = c(s.a) + c((s.s or 0) / R.shirts.units) + c((s.r or 0) / R.rifle.units) + c((s.m or 0) / R.medical.units)
            if slots > F.cap then return nil, "base " .. i .. " estoque acima do teto de " .. F.cap .. " slots" end
        end
    end
    return true
end

-- Preflight sem mutacao: classe carregavel, chao Landscape no XYZ salvo (tolerancia PERSIST.tol) e saidas >= minExits.
function logi.fwdPreflight(d)
    local F, tol = CFG.FWD, CFG.PERSIST.tol
    local cls = LoadAsset(F.asset)
    if not valid(cls) then return nil, "classe da base avançada não carregou" end
    for i, r in ipairs(d.fwd.list) do
        local gz = logi.parkingGround(r.x, r.y, { Z = r.z })
        if not gz or math.abs(gz - r.z) > tol then return nil, "sem chão Landscape na base avançada salva " .. i end
        if #logi.fwdExits(r.x, r.y, r.z) < F.minExits then return nil, "base avançada salva " .. i .. " sem saídas livres" end
    end
    return true
end

function logi.fwdStageClear()
    for _, st in pairs(S.fwdStage or {}) do
        local a = st.actor
        if a and valid(a) and not a.bActorIsBeingDestroyed then pcall(function() a:K2_DestroyActor() end) end
    end
    S.fwdStage = {}
end

-- Estagio do Continuar: cria TODOS os atores salvos (ou nenhum). Base viva da mesma posicao e adotada em vez de duplicada.
function logi.fwdStage(d)
    logi.fwdStageClear()
    local F = CFG.FWD
    local cls = LoadAsset(F.asset)
    if not valid(cls) then return false, "classe da base avançada não carregou" end
    local made, adopt = {}, {}
    for i, r in ipairs(d.fwd.list) do
        local old = nil
        for _, fb in ipairs(logi.fwd) do
            if not fb.dead and valid(fb.actor) and not fb.actor.bActorIsBeingDestroyed and flatDist(fb, { X = r.x, Y = r.y }) < 50 then old = fb end
        end
        if old then adopt[i] = old
        else
            local a, why = logi.fwdSpawn(cls, r.x, r.y, r.z, r.yaw)
            if not a then
                for _, x in ipairs(made) do pcall(function() x:K2_DestroyActor() end) end
                return false, why
            end
            made[#made + 1] = a
            S.fwdStage[i] = { actor = a }
        end
    end
    for i, old in pairs(adopt) do   -- sem falha possivel daqui: o ator muda de dono (logi.reset nao o destruira)
        S.fwdStage[i] = { actor = old.actor }
        old.actor = nil
    end
    return true
end

-- Depois de logi.restore: liga cada estagio ao ponto salvo (por indice) e recalcula as saidas. Retorna lista de problemas.
function logi.fwdBind(fwd)
    local problems = {}
    for i, r in ipairs(fwd.list) do
        local st, pt, why = S.fwdStage[i], points[r.pt], nil
        if not (logi.on and pt and st and valid(st.actor) and not st.actor.bActorIsBeingDestroyed) then why = "ator, ponto ou logística ausente"
        else
            local exits = logi.fwdExits(r.x, r.y, r.z)
            if #exits < CFG.FWD.minExits then why = "poucas saídas livres"
            else logi.fwdMake(pt, r.x, r.y, r.z, r.yaw, r.hp, st.actor, exits); st.actor = nil end
        end
        if why then problems[#problems + 1] = string.format("base avançada %s não refeita (%s)", pt and pt.name or "?", why) end
    end
    logi.fwdStageClear()   -- o que sobrou (falha de bind) e destruido
    return problems
end
-- ===== BASES AVANCADAS (fim do bloco) =====
