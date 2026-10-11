-- COLETA MANUAL: soldados reais do jogador carregam sucata do campo ate a refinaria. Estado em logi.col
-- (units = {m = registro do soldado, state, carry, goal, ...}); nunca guarda ator/userdata entre quadros: revalida
-- pertencer ao esquadrao + alive + bActorIsBeingDestroyed a cada passo (mesma regra do anim.untrack).
-- Conservacao: gathered == delivered + lost + sucata em maos; logi.salvage so cresce em delivered.
function logi.trucksNeeded() return CFG.LOGI.supply + (CFG.COLETA.manualStart and 0 or 1) end

-- Sem caminhao de recurso vivo (destruido, ainda nao construido ou ausente).
function logi.colDown()
    for _, tr in ipairs(logi.trucks or {}) do
        if tr.kind == "res" then return tr.state == "dead" end
    end
    return true
end

function logi.colReset()
    local K = logi.col
    for _, u in ipairs(K and K.units or {}) do
        if u.carry > 0 then log(string.format("coleta manual: %.1f sucata em mãos descartada (reinício)", u.carry)) end
        if u.m.col == u then u.m.col = nil end
    end
    logi.col = { units = {}, active = false, gathered = 0, delivered = 0, lost = 0, why = {}, trips = 0 }
    return logi.col
end

-- Soldado ainda no esquadrao, vivo e nao em destruicao (revalidacao antes de tocar no pawn).
function logi.colLive(m)
    for _, o in ipairs(squad) do
        if o == m then return alive(m) and not m.pawn.bActorIsBeingDestroyed end
    end
    return false
end

function logi.colCalm(m, t)
    local C = CFG.COLETA
    if suppression(m) >= 0.05 or t < (m.nextShot or -1e9) + C.fireQuiet then return false end
    local here = loc(m)
    for _, e in ipairs(enemies) do
        if alive(e) and flatDist(here, loc(e)) <= C.danger then return false end
    end
    return true
end

function logi.colFree(m, t)
    local C = CFG.COLETA
    if m.role ~= "worker" or m.col or not logi.colLive(m) then return false end
    if m.hold or m.target or m.pathJob or m.focus or m.area or m.retreat or m.medevac or m.queue then return false end
    if os.clock() - (m.orderT or -1e9) < C.quiet then return false end
    if (m.pawn.Health or 0) < (m.pawn.MaxHealth or 100) * C.minHp then return false end
    return logi.colCalm(m, t)
end

function logi.colRelease(u, why, keep)
    local K = logi.col
    for i = #K.units, 1, -1 do if K.units[i] == u then table.remove(K.units, i) end end
    if u.carry > 0 then
        K.lost, K.why[why] = K.lost + u.carry, (K.why[why] or 0) + u.carry
        log(string.format("coleta manual: trabalhador sai da coleta (%s), %.1f sucata perdida", why, u.carry))
        u.carry = 0
    else
        log("coleta manual: trabalhador sai da coleta (" .. why .. ")")
    end
    local m = u.m
    if m.col == u then
        m.col = nil
        if not keep and m.target == u.goal and logi.colLive(m) then  -- ainda e a nossa marcha: cancela e freia
            m.target, m.path, m.pathJob, m.detour, m.stuckAt, m.lastMoveT = nil, nil, nil, nil, nil, nil
            pcall(halt, m)
        end
    end
end

-- Onde nasce o trabalhador: deposito (com X/Y/Z e shirts) que paga a camisa. Isolado aqui: a base avancada troca esta funcao.
function logi.workerDepot() return logi.base end

-- Camisas do deposito dos trabalhadores que o recrutamento de combate nao pode gastar enquanto nao ha caminhao de recurso
-- (senao base sem camisa + sem bmat = nenhum trabalhador = travado de novo). Vale so para o deposito de nascimento.
function logi.workerReserve(dep)
    if dep ~= logi.workerDepot() or not logi.colDown() then return 0 end
    local n = 0
    for _, m in ipairs(squad) do if m.role == "worker" and alive(m) then n = n + 1 end end
    return math.max(0, CFG.COLETA.workers - n)
end

-- Interface comum de nascimento (so o local "base" e o trabalhador; ver CFG.SPAWN). PURA: nao muda estoque nem cria ator.
-- Retorna site = {dep, kind, name, at = {X, Y, Z, exact = true}, need = {shirts, rifle}, explicit} ou nil + motivo.
function logi.spawnSite(role, cursor, opts)
    local R = CFG.SPAWN.roles[role]
    if not R then return nil, "função sem receita" end
    if not logi.on then return nil, "ramo legado" end
    local allowed = false
    for _, k in ipairs((opts and opts.sites) or R.sites or { "base" }) do if k == "base" then allowed = true end end
    local dep = logi.workerDepot()
    if not allowed or not dep then return nil, "nenhum local de nascimento permitido" end
    local need = { shirts = R.shirts or 0, rifle = R.rifle or 0 }
    local keep = role == "worker" and 0 or logi.workerReserve(dep)   -- soldados de combate nao gastam a reserva dos trabalhadores
    if (dep.shirts or 0) < need.shirts + keep then
        return nil, keep > 0 and "camisas reservadas aos trabalhadores da coleta" or "sem camisas em " .. (dep.name or "base")
    end
    if (dep.rifle or 0) < need.rifle then return nil, "sem fuzis em " .. (dep.name or "base") end
    local a = ((logi.col and logi.col.made or 0) + 1) * 1.7   -- anel de saidas simples ao redor da base
    return { dep = dep, kind = "base", name = dep.name or "base", explicit = false, need = need,
        at = { X = dep.X + math.cos(a) * 250, Y = dep.Y + math.sin(a) * 250, Z = dep.Z, exact = true } }
end

-- Depois do ator confirmado: revalida e debita (unico ponto que mexe em dep.shirts/dep.rifle no codigo novo).
function logi.spawnCommit(site, role)
    local dep, need = site and site.dep, site and site.need
    if not dep or not need then return false, "site inválido" end
    if (dep.shirts or 0) < need.shirts or (dep.rifle or 0) < need.rifle then
        log("spawnCommit recusado: estoque mudou (" .. tostring(role) .. ")")
        return false, "estoque insuficiente"
    end
    dep.shirts, dep.rifle = (dep.shirts or 0) - need.shirts, (dep.rifle or 0) - need.rifle
    return true
end

-- Mantem ate COLETA.workers trabalhadores vivos enquanto a coleta e necessaria (repoe os mortos). decidir -> criar -> commit.
function logi.colMaintain(t)
    local C, K = CFG.COLETA, logi.col
    if t < (K.spawnT or 0) or not isLocalAuthority() then return end
    K.spawnT = t + C.spawnEvery
    local n = 0
    for _, m in ipairs(squad) do if m.role == "worker" and alive(m) then n = n + 1 end end
    if n >= C.workers then return end
    local site, why = logi.spawnSite("worker", nil)
    if not site or #squad >= CFG.SQUAD_MAX then
        if t >= (K.noteT or 0) then
            K.noteT = t + 30.0
            notify(site and "esquadrão cheio: não há vaga para trabalhadores" or ("sem como criar trabalhadores para a coleta: " .. tostring(why)), 4.0)
        end
        return
    end
    local at = site.at
    local m = spawnSoldier(at.X, at.Y, (groundZ(at.X, at.Y) or at.Z) + 90, slotFor(#squad + 1), CFG.FRIENDLY_TEAM, "worker")
    if not m then return end  -- spawn falhou: nada debitado
    local ok = logi.spawnCommit(site, "worker")
    if not ok then  -- estoque mudou entre decidir e criar (nao deveria: game thread sincrono): desfaz o ator
        pcall(anim.untrack, m)
        pcall(function() m.pawn:K2_DestroyActor() end)
        releaseController(m.hpc)
        return
    end
    K.made = (K.made or 0) + 1
    m.group, m.sel = (#squad % 2) + 1, false
    squad[#squad + 1] = m
    pcall(syncMarkers)
    log(string.format("coleta manual: trabalhador nasceu em %s (-1 camisa, restam %d)", site.name, site.dep.shirts or 0))
end

-- Rota (A* do mod, routeTo) ate o ponto de espera do lugar, do lado de onde o soldado vem.
function logi.colGo(u, site, t)
    local m, C = u.m, CFG.COLETA
    local here = loc(m)
    local a = math.atan(here.Y - site.Y, here.X - site.X) + (u.k or 0) * 0.7
    local goal = { X = site.X + math.cos(a) * C.stand, Y = site.Y + math.sin(a) * C.stand, Z = site.Z }
    routeTo(m, goal)
    u.goal, u.legT, u.retryT = goal, t, t + C.retry
end

function logi.colUnit(u, K, dt, t, need)
    local C, m = CFG.COLETA, u.m
    local F, R = logi.field, logi.refinery
    local here = loc(m)
    if t >= (u.calmT or 0) then u.calm, u.calmT = logi.colCalm(m, t), t + 0.5 end
    if u.calm then
        u.pausedFor = 0
    else
        u.pausedFor, u.legT = (u.pausedFor or 0) + dt, u.legT + dt
        if u.pausedFor > C.pause then return logi.colRelease(u, "combate prolongado") end
    end
    if u.state ~= "gather" and t - u.legT > C.leg then return logi.colRelease(u, "preso no caminho") end
    if not need and u.state ~= "toRef" then
        if u.carry <= 0 then return logi.colRelease(u, "coleta encerrada") end
        u.state = "toRef"
        if u.calm then logi.colGo(u, R, t) end
    end
    local marching = m.target or m.pathJob
    if u.state == "gather" then
        if flatDist(here, F) > C.fieldR then
            u.state, u.legT = "toField", t
        elseif u.calm then
            local take = math.min(C.rate * dt, C.cap - u.carry)
            u.carry, K.gathered = u.carry + take, K.gathered + take
            if u.carry >= C.cap - 1e-9 then
                K.gathered, u.carry = K.gathered + (C.cap - u.carry), C.cap  -- carga cheia exata (sem 39.999999 por erro de ponto flutuante)
                u.state = "toRef"; logi.colGo(u, R, t)
            end
        end
    elseif u.state == "toField" then
        if not marching and flatDist(here, F) <= C.fieldR then u.state = "gather"
        elseif not marching and u.calm and t >= u.retryT then logi.colGo(u, F, t) end
    elseif u.state == "toRef" then
        if flatDist(here, R) <= C.refR then  -- chegada: unico ponto onde a sucata vira estoque da refinaria
            logi.salvage, K.delivered, K.trips = logi.salvage + u.carry, K.delivered + u.carry, K.trips + 1
            u.carry = 0
            if not need then return logi.colRelease(u, "entregou") end
            u.state = "toField"
            logi.colGo(u, F, t)
        elseif not marching and u.calm and t >= u.retryT then logi.colGo(u, R, t) end
    end
end

function logi.colStep(dt, t)
    local C, K = CFG.COLETA, logi.col or logi.colReset()
    if not (logi.field and logi.refinery) then return end
    local L = CFG.LOGI
    local down = logi.colDown()
    local need = down and (logi.bmat + logi.salvage / L.ratio < L.truckCost)  -- falta bmat para o caminhao: sem renda
    if not K.active then
        if down then
            K.since = K.since or t
            if t - K.since >= C.delay then
                K.active = true
                notify("COLETA MANUAL: sem caminhão de recurso; trabalhadores da base coletam sucata até a fábrica fazer o caminhão", 8.0)
            end
        else
            K.since = nil
        end
    elseif not down then
        K.active, K.since = false, nil
        notify("caminhão de recurso pronto: coleta manual encerrada", 4.0)
    end
    for i = #K.units, 1, -1 do
        local u = K.units[i]
        local m = u.m
        if not logi.colLive(m) then
            logi.colRelease(u, "trabalhador morto")
        elseif m.orderT ~= u.orderT or m.hold or m.focus or m.area or m.retreat or m.medevac or m.queue then
            logi.colRelease(u, "ordem do jogador", true)  -- a ordem do jogador (alvo, fila) fica intacta
        else
            logi.colUnit(u, K, dt, t, need)
        end
    end
    if K.active and need then logi.colMaintain(t) end
    if K.active and need and t >= (K.scanT or 0) then
        K.scanT = t + C.scan
        if #K.units < C.workers then
            local best, bs = nil, math.huge
            for _, m in ipairs(squad) do
                if logi.colFree(m, t) then
                    local s = flatDist(loc(m), logi.field) + (m.sel and 1e6 or 0)  -- prefere quem o jogador nao selecionou
                    if s < bs then best, bs = m, s end
                end
            end
            if best then
                local u = { m = best, state = "toField", carry = 0, orderT = best.orderT, k = #K.units + 1 }
                best.col = u
                K.units[#K.units + 1] = u
                logi.colGo(u, logi.field, t)
                log(string.format("coleta manual: trabalhador %d vai ao campo de sucata (%d coletores)", u.k, #K.units))
            end
        end
    end
end

-- Uma linha para o painel da logistica; nil quando inativa (nao polui).
function logi.colHud()
    local K, L = logi.col, CFG.LOGI
    if not K or not (K.active or #K.units > 0) then return nil end
    local hand = 0
    for _, u in ipairs(K.units) do hand = hand + u.carry end
    local who = #K.units == 0 and "aguardando trabalhador"
        or string.format("%d trabalhador%s", #K.units, #K.units == 1 and "" or "es")
    return string.format("coleta manual: %s | %d/%d bmat para o caminhão | %.0f sucata em mãos", who,
        math.floor(logi.bmat + logi.salvage / L.ratio), L.truckCost, hand)
end

-- Razao da coleta: colhido == entregue + perdido + em maos.
function logi.colAudit()
    local K, hand = logi.col, 0
    for _, u in ipairs(K.units) do
        hand = hand + u.carry
        if u.carry < -1e-9 or u.carry > CFG.COLETA.cap + 1e-9 then return false, "carga fora de [0, cap]" end
    end
    if math.abs(K.gathered - K.delivered - K.lost - hand) > 1e-6 then return false, "razão da coleta não fecha" end
    if #K.units > CFG.COLETA.workers then return false, "coletores demais" end
    return true
end

-- Caminhao construido pela fabrica sem ator (partida manual: o de recurso nao e implantado): nasce no campo.
-- Visual apenas; o custo ja foi debitado do bmat da fabrica. Falha silenciosa: segue como caminhao abstrato.
function logi.spawnTruck(tr)
    local home = tr.kind == "res" and logi.field or logi.factory
    local cls = LoadAsset(CFG.DEPLOY.truck)
    if not valid(cls) then return end
    local x, y = home.X + 400, home.Y + 300
    local z = groundZ(x, y) or home.Z
    local a = world():SpawnActor(cls, { X = x, Y = y, Z = z + CFG.DEPLOY.off }, { Pitch = 0, Yaw = 0, Roll = 0 })
    if not (valid(a) and not a.bActorIsBeingDestroyed and a.Health == CFG.LOGI.hp) then
        if valid(a) and not a.bActorIsBeingDestroyed then pcall(function() a:K2_DestroyActor() end) end
        return
    end
    a.TeamId = CFG.FRIENDLY_TEAM
    pcall(function() a:SetActorEnableCollision(false) end)
    tr.pawn, tr.off = a, CFG.DEPLOY.off
    logi.place(tr, x, y)
end

