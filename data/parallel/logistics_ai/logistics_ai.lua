-- IA_LOGISTICA (proposta 2026-10-09, CLAUDE_IA_LOGISTICA): cadeia inimiga com contabilidade fechada.
-- Inserido por build_patch.py no lugar de convoySpawn/convoyTick/waveCut; NAO cria locais de topo
-- (tudo em CFG.ECHAIN e na tabela logi). Mesmas regras do jogador: sucata por viagem (LOGI.trip), refinaria
-- LOGI.refine/s a LOGI.ratio:1, receitas de CFG.LOGI.recipes (custo/tempo da tabela do jogo x LOGI.time; debito
-- ao iniciar, caixa ao concluir), caminhao de LOGI.cap caixas que custa LOGI.truckCost bmat para reconstruir
-- (TruckC: Cloth100, 900 HP, carga 15 em data/game_costs.txt). Producao fica na retaguarda fora do mapa;
-- o trecho retaguarda -> frente e um caminhao real (BPTruckC) movido por logi.drive, o mesmo contrato de rota do
-- jogador (ESTRADAS troca o driver; chegada so com drive == true). Unidades: caixas na retaguarda e na carga;
-- unidades de produto na frente (municao: caixa; camisas: LOGI.recipes.shirts.units).
-- Razao: inicial + produzido == retaguarda + em transito + pendente + frente + consumido + perdido (por produto);
-- bmat0 + refinado/ratio == bmat + gasto; sucata colhida == sucata + refinada. logi.eAudit() confere.
CFG.ECHAIN = {
    kinds = { "ammo", "shirts" },             -- o que a frente inimiga consome (receitas reais em CFG.LOGI.recipes)
    shirts = 1,                               -- camisas por soldado pago (= recrutamento do jogador)
    free = 3,                                 -- BONUS ABSTRATO explicito: guarnicao minima gratuita por onda (era o minimo antigo)
    trip = 25.0,                              -- s por viagem do caminhao de recurso da retaguarda (fora do mapa; calibrar no lab)
    bmat0 = 240, front0 = { ammo = 2, shirts = 10 },  -- estoque de cenario (entra no razao como "inicial")
    want = { ammo = 6, shirts = 30 },         -- alvo da frente em unidades (~30 soldados; a fabrica para em 2x)
    trucks = 2,                               -- frota de comboio (= LOGI.supply do jogador)
    minLoad = 3,                              -- caixas minimas por comboio (ou tudo que a frente pede, se menos)
    stuck = 20.0,                             -- s com rota ausente/bloqueada (driver de ESTRADAS) antes de voltar carregado
    keep = 40,                                -- eventos e registros de onda guardados
    tol = 0.05,                               -- folga do razao lido do save (sv.ser grava numeros com 3 casas)
}

-- Unidades por caixa e consumo por soldado pago. Municao: um carregamento completo = 1/LOGI.reloads caixa.
function logi.eUnits(k) return (CFG.LOGI.recipes[k] and CFG.LOGI.recipes[k].units) or 1 end
function logi.eNeed(k)
    if k == "ammo" then return 1 / CFG.LOGI.reloads end
    return CFG.ECHAIN[k] or 0
end

function logi.eEvent(msg)
    local en = logi.en
    if not en then return end
    en.events[#en.events + 1] = string.format("%.0f %s", now(), msg)
    if #en.events > CFG.ECHAIN.keep then table.remove(en.events, 1) end
    log("cadeia inimiga: " .. msg)
end

-- Estado novo da cadeia (logi.start). Receita sem custo/tempo positivo recusa a cadeia inteira (fail-closed):
-- sem producao, a onda recebe so a guarnicao gratuita; nunca custo zero por erro de schema.
function logi.eReset()
    local E = CFG.ECHAIN
    local en = { salvage = 0, bmat = E.bmat0, tripT = E.trip, job = nil, fac = {}, front = {}, pending = nil,
        ready = E.trucks, rebuild = {}, seq = 0, events = {}, waves = {}, ghost = {}, delivered = 0,
        led = { bmat0 = E.bmat0, salv = 0, refined = 0, spent = 0, init = {}, made = {}, used = {}, lost = {} } }
    for _, k in ipairs(E.kinds) do
        local rc = CFG.LOGI.recipes[k]
        if type(rc) ~= "table" or type(rc.bmat) ~= "number" or rc.bmat <= 0 or type(rc.time) ~= "number" or rc.time <= 0
            or (rc.units ~= nil and (type(rc.units) ~= "number" or rc.units < 1)) then
            en.err = "receita inválida: " .. tostring(k)
        end
        en.fac[k], en.front[k], en.ghost[k] = 0, (E.front0[k] or 0), 0
        en.led.init[k], en.led.made[k], en.led.used[k], en.led.lost[k] = en.front[k], 0, 0, 0
    end
    logi.en = en
    combat.cargo = logi.eSoldiers()
    if en.err then log("cadeia inimiga recusada: " .. en.err) end
    return en
end

-- Ativa so numa partida com logistica e fora do assalto (assalto e partidas sem logistica seguem abstratos).
function logi.eActive()
    return logi.on == true and logi.en ~= nil and combat.mode ~= "assault"
end

-- Soldados que a frente consegue equipar (camisa + carregamento), e o produto que limita.
function logi.eSoldiers(st)
    local en = logi.en
    st = st or (en and en.front)
    if not st then return 0 end
    local n, lim = math.huge, nil
    for _, k in ipairs(CFG.ECHAIN.kinds) do
        local q = logi.eNeed(k)
        if q > 0 then
            local m = math.floor((st[k] or 0) / q + 1e-6)
            if m < n then n, lim = m, k end
        end
    end
    if n == math.huge then return 0, nil end
    return n, lim
end

-- Unidades em transito (comboios vivos + carga pendente de reenvio apos continuar o save).
function logi.eTransit(k)
    local n = 0
    for _, tr in ipairs(logi.foes or {}) do
        if tr.cargo then n = n + (tr.cargo[k] or 0) end
    end
    if logi.en and logi.en.pending then n = n + (logi.en.pending[k] or 0) end
    return n * logi.eUnits(k)
end

function logi.eHave(k)
    local en = logi.en
    return en.fac[k] * logi.eUnits(k) + en.front[k] + logi.eTransit(k)
end

-- Fabrica inimiga: o produto com menos estoque total frente ao alvo; tudo >= 2x o alvo para (regra do jogador).
function logi.eNextKind()
    local en, E = logi.en, CFG.ECHAIN
    local best, ratio = nil, 2.0
    for _, k in ipairs(E.kinds) do
        local have = logi.eHave(k) + ((en.job and en.job.kind == k) and logi.eUnits(k) or 0)
        local r = have / E.want[k]
        if r < ratio then best, ratio = k, r end
    end
    return best
end

-- Producao da retaguarda (pura: sem UE). dt ja limitado pelo chamador (logi.tick: <= 0,5 s).
function logi.eTick(dt, t)
    local en, C, E = logi.en, CFG.LOGI, CFG.ECHAIN
    if not logi.eActive() or en.err or not (dt > 0) then return end
    local L = en.led
    en.tripT = en.tripT - dt
    if en.tripT <= 0 then
        en.tripT = en.tripT + E.trip
        en.salvage, L.salv = en.salvage + C.trip, L.salv + C.trip
    end
    local r = math.min(en.salvage, C.refine * dt)
    en.salvage, L.refined, en.bmat = en.salvage - r, L.refined + r, en.bmat + r / C.ratio
    if en.job then
        en.job.left = en.job.left - dt
        if en.job.left <= 0 then
            local k = en.job.kind
            en.fac[k], L.made[k] = en.fac[k] + 1, L.made[k] + logi.eUnits(k)
            en.job = nil
        end
    end
    -- Reconstrucao antes da fabrica: sem caminhao livre, caixa nova nao anda; a fabrica guarda bmat para ele
    -- (decisao da IA; sem isso a fabrica gastava cada 80 bmat e o caminhao de 100 nunca voltava).
    local due = false
    for i = #en.rebuild, 1, -1 do
        if t >= en.rebuild[i] then
            if en.bmat >= C.truckCost then
                en.bmat, L.spent = en.bmat - C.truckCost, L.spent + C.truckCost
                table.remove(en.rebuild, i)
                en.ready = en.ready + 1
                logi.eEvent(string.format("caminhão de comboio reconstruído (-%d bmat)", C.truckCost))
            else
                due = true
            end
        end
    end
    if not en.job and not (due and en.ready == 0) then
        local k = logi.eNextKind()
        local rc = k and C.recipes[k]
        if rc and en.bmat >= rc.bmat then
            en.bmat, L.spent = en.bmat - rc.bmat, L.spent + rc.bmat
            en.job = { kind = k, left = rc.time * C.time, total = rc.time * C.time }
        end
    end
end

-- Carga do proximo comboio sem debitar: primeiro a pendente (save), senao o que falta na frente, ate LOGI.cap caixas.
function logi.eLoad()
    local en, E = logi.en, CFG.ECHAIN
    local cargo, room, boxes, wanted = {}, CFG.LOGI.cap, 0, 0
    local src = en.pending
    for _, k in ipairs(E.kinds) do
        local n
        if src then
            n = math.min(src[k] or 0, room)
        else
            local want = math.ceil(math.max(0, E.want[k] - en.front[k] - logi.eTransit(k)) / logi.eUnits(k) - 1e-9)
            n = math.min(en.fac[k], want, room)
            wanted = wanted + want
        end
        cargo[k], room, boxes = n, room - n, boxes + n
    end
    if boxes < 1 then return nil, false end
    -- Decisao da IA: nao arriscar um caminhao (100 bmat) por uma caixa; sai com ECHAIN.minLoad caixas ou
    -- com tudo o que a frente pede (o que for menor). Carga pendente do save sai sempre.
    if not src and boxes < math.min(E.minLoad, math.min(wanted, CFG.LOGI.cap)) then return nil, false end
    return cargo, src ~= nil
end

function logi.eFmt(c)
    return string.format("%d cx munição, %d cx camisas", c.ammo or 0, c.shirts or 0)
end

-- Comboio: so sai com caminhao livre, carga real e ator ativo; a retaguarda so e debitada depois do spawn.
function logi.convoySpawn(t)
    local en, E = logi.en, CFG.ECONVOY
    if not en or en.err or en.ready < 1 then return false end
    local cargo, fromPending = logi.eLoad()
    if not cargo then return false end  -- sem carga, sem comboio fantasma
    local R, F = logi.convoyRoute()
    if not R then return false end
    local ok, cls = pcall(LoadAsset, E.class)
    if not (ok and cls and cls:IsValid()) then return false end
    local a = world():SpawnActor(cls, { X = R.X, Y = R.Y, Z = R.Z + E.off }, { Pitch = 0, Yaw = 0, Roll = 0 })
    if not valid(a) or a.bActorIsBeingDestroyed then return false end  -- IsValid continua true ate o GC
    local tr = { kind = "foe", team = CFG.ENEMY_TEAM, hp = E.hp, off = E.off, state = "toFront", from = R, to = F,
        n = #logi.foes + 1, cargo = {} }
    pcall(function() a:SetActorEnableCollision(false) end); tr.pawn = a
    logi.place(tr, R.X, R.Y)
    -- transacao: daqui em diante nada falha antes do debito
    local src = fromPending and en.pending or en.fac
    local left = 0
    for _, k in ipairs(CFG.ECHAIN.kinds) do
        tr.cargo[k] = cargo[k] or 0
        src[k] = src[k] - tr.cargo[k]
        left = left + (fromPending and src[k] or 0)
    end
    if fromPending and left == 0 then en.pending = nil end
    en.ready, en.seq = en.ready - 1, en.seq + 1
    tr.id = en.seq
    logi.foes[#logi.foes + 1] = tr
    combat.convoys = (combat.convoys or 0) + 1
    logi.eEvent(string.format("comboio %d saiu: %s", tr.id, logi.eFmt(tr.cargo)))
    pcall(rts.alert, "comboio", { X = (R.X + F.X) / 2, Y = (R.Y + F.Y) / 2, Z = F.Z },
        string.format("COMBOIO INIMIGO a caminho da frente (%s): destrua para enfraquecer a próxima onda", logi.eFmt(tr.cargo)))
    return true
end

-- Chegada confirmada a frente: caixas viram unidades uma unica vez.
function logi.eDeliver(tr)
    local en = logi.en
    if not (en and tr.cargo) then return end
    local add = {}
    for _, k in ipairs(CFG.ECHAIN.kinds) do
        add[k] = (tr.cargo[k] or 0) * logi.eUnits(k)
        en.front[k] = en.front[k] + add[k]
    end
    tr.cargo = nil
    en.delivered = en.delivered + 1
    logi.eEvent(string.format("comboio %s entregou na frente: +%g munição, +%g camisas", tostring(tr.id), add.ammo or 0, add.shirts or 0))
    notify(string.format("comboio inimigo chegou à frente: equipa %d soldados", (logi.eSoldiers())), 3.0)
end

-- Caminhao perdido (destruido, ator invalido ou removido): carga sai do razao como perda, uma unica vez;
-- o caminhao entra na fila de reconstrucao (LOGI.rebuild s e LOGI.truckCost bmat, como o do jogador).
function logi.eLose(tr, why)
    local en = logi.en
    if tr.lostDone then return "já registrado" end
    tr.lostDone = true
    if not en then tr.cargo = nil; return "sem cadeia" end
    local units = {}
    for _, k in ipairs(CFG.ECHAIN.kinds) do
        local u = ((tr.cargo and tr.cargo[k]) or 0) * logi.eUnits(k)
        en.led.lost[k] = en.led.lost[k] + u
        en.ghost[k] = en.ghost[k] + u  -- carga que a frente teria (diagnostico de atribuicao, fora do razao)
        units[k] = u
    end
    tr.cargo = nil
    en.rebuild[#en.rebuild + 1] = now() + CFG.LOGI.rebuild
    local msg = string.format("comboio %s perdido (%s): -%g munição, -%g camisas", tostring(tr.id), why or "?", units.ammo or 0, units.shirts or 0)
    logi.eEvent(msg)
    return string.format("a frente perde %g munição e %g camisas", units.ammo or 0, units.shirts or 0)
end

-- Caminhao de volta a retaguarda: devolve carga nao entregue (so na chegada fisica) e volta a frota.
function logi.eHome(tr)
    local en = logi.en
    if not en then return end
    if tr.cargo then
        for _, k in ipairs(CFG.ECHAIN.kinds) do en.fac[k] = en.fac[k] + (tr.cargo[k] or 0) end
        logi.eEvent(string.format("comboio %s voltou com a carga: %s", tostring(tr.id), logi.eFmt(tr.cargo)))
        tr.cargo = nil
    end
    en.ready = en.ready + 1
end

-- Rota ausente/bloqueada por CFG.ECHAIN.stuck s (status escrito pelo driver de ESTRADAS em tr.routeStatus).
function logi.eStuck(tr, dt)
    local s = tr.routeStatus
    if s == "rota_ausente" or s == "regiao_invalida" or s == "bloqueado" then tr.stuck = (tr.stuck or 0) + dt
    else tr.stuck = 0 end
    return tr.stuck >= CFG.ECHAIN.stuck
end

function logi.convoyTick(dt, t)
    local E = CFG.ECONVOY
    logi.eTick(dt, t)
    if combat.auto and combat.mode ~= "assault" and t >= (logi.convoyT or 0) then
        logi.convoyT = t + (logi.convoySpawn(t) and E.every or E.retry)
    end
    for i = #logi.foes, 1, -1 do
        local tr = logi.foes[i]
        local gone = tr.state == "dead"
        if not gone and tr.pawn ~= nil and (not valid(tr.pawn) or tr.pawn.bActorIsBeingDestroyed) then
            tr.state = "dead"
            logi.eLose(tr, "ator do caminhão inválido")  -- perda explicita, nunca entrega fantasma
            gone = true
        end
        if not gone then
            if tr.state == "toFront" then
                if logi.drive(tr, tr.to, dt, E.speed) then
                    logi.eDeliver(tr)
                    tr.state = "back"
                elseif logi.eStuck(tr, dt) then
                    tr.state = "back"  -- volta carregado; credito so na chegada a retaguarda
                    logi.eEvent(string.format("comboio %s sem rota: voltando com a carga", tostring(tr.id)))
                end
            elseif tr.state == "back" and logi.drive(tr, tr.from, dt, E.speed) then
                logi.eHome(tr)
                tr.home = true
                gone = true
            end
            -- nossos soldados perto atiram no caminhao
            local n, shooter = 0, nil
            for _, m in ipairs(squad) do
                if alive(m) and flatDist(loc(m), tr) <= CFG.LOGI.ambush then n, shooter = n + 1, m end
            end
            if n > 0 and not tr.home then
                if t >= (tr.fxT or 0) and shooter then
                    tr.fxT = t + E.fx
                    local d, dx, dy = flatDist(loc(shooter), tr)
                    pcall(rts.shotFx, shooter, dx, dy, d)
                end
                if logi.hit(tr, n * CFG.LOGI.dps * dt, t) then gone = true end
            end
        end
        if gone then
            if not tr.home and not tr.lostDone then logi.eLose(tr, "removido") end  -- nunca some carga sem registro
            if tr.icon and valid(tr.icon) then pcall(function() tr.icon:K2_DestroyActor() end) end
            if tr.pawn and valid(tr.pawn) then pcall(function() tr.pawn:K2_DestroyActor() end) end
            table.remove(logi.foes, i)
        end
    end
    if logi.en then combat.cargo = logi.eSoldiers() end
end

-- Consumo real na frente: k soldados pagos levam camisa + carregamento. Retorna o que foi debitado.
function logi.eConsume(k, why)
    if not logi.eActive() or not (k and k > 0) then return 0 end
    local en = logi.en
    k = math.min(math.floor(k), (logi.eSoldiers()))
    if k < 1 then return 0 end
    for _, kind in ipairs(CFG.ECHAIN.kinds) do
        local q = math.min(en.front[kind], k * logi.eNeed(kind))
        en.front[kind], en.led.used[kind] = en.front[kind] - q, en.led.used[kind] + q
    end
    combat.cargo = logi.eSoldiers()
    return k
end

-- Reforco pelos pontos (ai.tick): limita ao que a frente equipa; o debito vem depois do spawn (eConsume).
function logi.eAfford(n)
    if not logi.eActive() then return n end
    return math.min(n, (logi.eSoldiers()))
end

-- Onda (waveTick): guarnicao gratuita + soldados pagos ate o que a frente equipa. So decide; o debito e
-- logi.eCommit depois do spawn (soldado que nao nasceu nao consome). Registro da onda: pedido, enviado,
-- produto limitante e quantos soldados a carga perdida em comboios desde a onda anterior teria equipado.
function logi.waveCut(n)
    if not logi.eActive() then return n end
    local en, E = logi.en, CFG.ECHAIN
    local free = math.min(n, E.free)
    local can, lim = logi.eSoldiers()
    local paid = math.min(n - free, can)
    local short = n - free - paid
    -- Atribuicao (contrafactual): com a carga perdida ainda nao "gasta" (ghost), quantos soldados a mais a frente
    -- equiparia? Esses faltam por interdicao; o ghost e gasto como se tivessem saido. Diagnostico, fora do razao.
    local with = {}
    for _, k in ipairs(E.kinds) do with[k] = en.front[k] + en.ghost[k] end
    local byCut = math.min(short, math.max(0, (logi.eSoldiers(with)) - can))
    local rec = { wave = combat.wave + 1, asked = n, free = free, paid = paid, short = short, limit = short > 0 and lim or nil,
        front = { ammo = en.front.ammo, shirts = en.front.shirts }, ghost = { ammo = en.ghost.ammo, shirts = en.ghost.shirts },
        byCut = byCut }
    for _, k in ipairs(E.kinds) do en.ghost[k] = math.max(0, en.ghost[k] - byCut * logi.eNeed(k)) end
    en.waves[#en.waves + 1] = rec
    if #en.waves > E.keep then table.remove(en.waves, 1) end
    en.plan = { w0 = combat.wave, free = free, paid = paid, rec = rec }
    if short > 0 then
        notify(string.format("faltou suprimento ao inimigo: a onda vem com %d a menos (falta %s%s)", short,
            lim == "ammo" and "munição" or "camisas", rec.byCut > 0 and string.format("; %d por comboios destruídos", rec.byCut) or ""), 4.0)
    end
    logi.eEvent(string.format("onda %d: pedido %d, grátis %d, pagos %d, faltaram %d (%s), atribuídos à interdição %d",
        rec.wave, n, free, paid, short, tostring(rec.limit), rec.byCut))
    return free + paid
end

-- Depois do spawn da onda: debita so os soldados pagos que nasceram (a guarnicao gratuita conta primeiro).
function logi.eCommit(made)
    local en = logi.en
    local p = en and en.plan
    if not p then return 0 end
    en.plan = nil
    if combat.wave == p.w0 then made = 0 end  -- spawn recusado antes de abrir a onda: nada nasceu
    local k = logi.eConsume(math.max(0, math.min(p.paid, (made or 0) - p.free)), "onda")
    p.rec.sent, p.rec.paidMade = made or 0, k
    return k
end

-- Conservacao verificavel (canal/laboratorio: out(logi.eAudit())).
function logi.eAudit()
    local en = logi.en
    if not en then return true, "sem cadeia" end
    local L, bad = en.led, {}
    for _, k in ipairs(CFG.ECHAIN.kinds) do
        local diff = (L.init[k] + L.made[k]) - (logi.eHave(k) + L.used[k] + L.lost[k])
        if math.abs(diff) > 1e-6 then bad[#bad + 1] = string.format("%s desvio %.6f", k, diff) end
        if en.front[k] < -1e-9 or en.fac[k] < 0 then bad[#bad + 1] = k .. " negativo" end
    end
    local db = (L.bmat0 + L.refined / CFG.LOGI.ratio) - (en.bmat + L.spent)
    if math.abs(db) > 1e-6 then bad[#bad + 1] = string.format("bmat desvio %.6f", db) end
    local ds = L.salv - (en.salvage + L.refined)
    if math.abs(ds) > 1e-6 then bad[#bad + 1] = string.format("sucata desvio %.6f", ds) end
    if en.bmat < -1e-9 or en.ready < 0 then bad[#bad + 1] = "bmat/frota negativo" end
    local road = 0  -- frota: livre + reconstruindo + na estrada == ECHAIN.trucks (nenhum caminhao criado do nada)
    for _, tr in ipairs(logi.foes or {}) do if not tr.lostDone and not tr.home then road = road + 1 end end
    if en.ready + #en.rebuild + road ~= CFG.ECHAIN.trucks then
        bad[#bad + 1] = string.format("frota %d+%d+%d ~= %d", en.ready, #en.rebuild, road, CFG.ECHAIN.trucks)
    end
    return #bad == 0, #bad == 0 and "razão fechado" or table.concat(bad, "; ")
end

function logi.eHud()
    local en = logi.en
    if not en then return "" end
    if en.err then return " | INIMIGO: cadeia recusada (" .. en.err .. ")" end
    local moving = 0
    for _, tr in ipairs(logi.foes) do if tr.state ~= "dead" and tr.cargo then moving = moving + 1 end end
    return string.format(" | INIMIGO: frente equipa %d (m%.1f c%d) | retaguarda bmat %.0f, cx m%d c%d | comboios %d na estrada, %d perdidos",
        (logi.eSoldiers()), en.front.ammo, en.front.shirts, en.bmat, en.fac.ammo, en.fac.shirts, moving, combat.convoysCut or 0)
end

-- Relatorio para o canal/laboratorio: estado, razao, ultimas ondas e eventos.
function logi.eReport()
    local en = logi.en
    if not en then return "cadeia inimiga: inativa" end
    local ok, why = logi.eAudit()
    local L, out = en.led, {}
    out[#out + 1] = string.format("cadeia inimiga ativa=%s err=%s | sucata %.1f bmat %.1f job=%s | frota livre %d, reconstruindo %d, na estrada %d | pendente %s",
        tostring(logi.eActive()), tostring(en.err), en.salvage, en.bmat, en.job and (en.job.kind .. string.format(" %.1f s", en.job.left)) or "-",
        en.ready, #en.rebuild, #logi.foes, en.pending and logi.eFmt(en.pending) or "-")
    for _, k in ipairs(CFG.ECHAIN.kinds) do
        out[#out + 1] = string.format("  %s: inicial %g + produzido %g = retaguarda %g + trânsito %g + frente %g + consumido %g + perdido %g",
            k, L.init[k], L.made[k], en.fac[k] * logi.eUnits(k), logi.eTransit(k), en.front[k], L.used[k], L.lost[k])
    end
    out[#out + 1] = string.format("  razão: %s (%s) | bmat0 %g + refinado %g/%g = bmat %.3f + gasto %g", ok and "OK" or "FALHA", why,
        L.bmat0, L.refined, CFG.LOGI.ratio, en.bmat, L.spent)
    for i = math.max(1, #en.waves - 4), #en.waves do
        local w = en.waves[i]
        out[#out + 1] = string.format("  onda %d: pedido %d grátis %d pagos %d enviados %s faltaram %d (%s) interdição %d",
            w.wave, w.asked, w.free, w.paid, tostring(w.sent), w.short, tostring(w.limit), w.byCut)
    end
    return table.concat(out, "\n")
end

-- Save: carga em transito vira "pendente" (o ator nao e recriado; reenviada da retaguarda pelo proximo comboio),
-- caminhoes na estrada voltam a frota livre, reconstrucao guarda o tempo restante. Copias, sem userdata.
function logi.eSnapshot()
    local en = logi.en
    if not en then return nil end
    local t = now()
    local function copy(s) local d = {}; for _, k in ipairs(CFG.ECHAIN.kinds) do d[k] = s[k] or 0 end; return d end
    local pend, road = copy(en.pending or {}), 0
    for _, tr in ipairs(logi.foes or {}) do
        if tr.state ~= "dead" and not tr.lostDone then
            road = road + 1
            for _, k in ipairs(CFG.ECHAIN.kinds) do pend[k] = pend[k] + ((tr.cargo and tr.cargo[k]) or 0) end
        end
    end
    local rb = {}
    for i, r in ipairs(en.rebuild) do rb[i] = math.max(0, r - t) end
    local L = en.led
    return { v = 1, salvage = en.salvage, bmat = en.bmat, trip = en.tripT, ready = en.ready + road, rebuild = rb,
        fac = copy(en.fac), front = copy(en.front), pending = pend, seq = en.seq, delivered = en.delivered,
        job = en.job and { kind = en.job.kind, left = en.job.left, total = en.job.total } or nil,
        led = { bmat0 = L.bmat0, salv = L.salv, refined = L.refined, spent = L.spent,
            init = copy(L.init), made = copy(L.made), used = copy(L.used), lost = copy(L.lost) } }
end

-- Validacao completa antes de substituir (nunca soma): numeros finitos >= 0, frota coerente, receita do job
-- conhecida e o proprio razao do save fechado. Invalido/ausente: mantem o estado novo de logi.start e avisa.
function logi.eValid(d)
    local E = CFG.ECHAIN
    local function num(x) return type(x) == "number" and x == x and x >= 0 and x < math.huge end
    local function int(x) return num(x) and x % 1 == 0 end
    if type(d) ~= "table" or d.v ~= 1 then return false, "versão" end
    for _, key in ipairs({ "salvage", "bmat", "trip" }) do if not num(d[key]) then return false, key end end
    if not int(d.ready) or type(d.rebuild) ~= "table" or not int(d.seq or 0) or not int(d.delivered or 0) then return false, "frota" end
    for _, r in ipairs(d.rebuild) do if not num(r) then return false, "reconstrução" end end
    if d.ready + #d.rebuild > E.trucks then return false, "frota maior que a configurada" end
    local L = d.led
    if type(L) ~= "table" then return false, "razão" end
    for _, key in ipairs({ "bmat0", "salv", "refined", "spent" }) do if not num(L[key]) then return false, "razão " .. key end end
    for _, grp in ipairs({ "fac", "front", "pending" }) do if type(d[grp]) ~= "table" then return false, grp end end
    for _, grp in ipairs({ "init", "made", "used", "lost" }) do if type(L[grp]) ~= "table" then return false, "razão " .. grp end end
    for _, k in ipairs(E.kinds) do
        if not int(d.fac[k]) or not int(d.pending[k]) or not num(d.front[k]) then return false, "estoque " .. k end
        for _, grp in ipairs({ "init", "made", "used", "lost" }) do if not num(L[grp][k]) then return false, "razão " .. k end end
        local u = logi.eUnits(k)
        local diff = (L.init[k] + L.made[k]) - ((d.fac[k] + d.pending[k]) * u + d.front[k] + L.used[k] + L.lost[k])
        if math.abs(diff) > E.tol then return false, "razão não fecha em " .. k end
    end
    if math.abs((L.bmat0 + L.refined / CFG.LOGI.ratio) - (d.bmat + L.spent)) > E.tol then return false, "razão bmat" end
    if math.abs(L.salv - (d.salvage + L.refined)) > E.tol then return false, "razão sucata" end
    if d.job ~= nil then
        local j = d.job
        if type(j) ~= "table" or not CFG.LOGI.recipes[j.kind] or not num(j.left) or not num(j.total) or j.left > j.total then return false, "job" end
    end
    return true
end

function logi.eRestore(d)
    if not (logi.on and logi.en) then return false end
    if d == nil then logi.eEvent("save sem cadeia inimiga: começa do estoque de cenário"); return false end
    local ok, why = logi.eValid(d)
    if not ok then
        logi.eEvent("save da cadeia inimiga recusado (" .. tostring(why) .. "): começa do estoque de cenário")
        notify("cadeia inimiga do save inválida: recomeça do estoque inicial", 4.0)
        return false
    end
    local t, en = now(), logi.en
    local function copy(s) local r = {}; for _, k in ipairs(CFG.ECHAIN.kinds) do r[k] = s[k] or 0 end; return r end
    en.salvage, en.bmat, en.tripT, en.ready, en.seq, en.delivered = d.salvage, d.bmat, d.trip, d.ready, d.seq or 0, d.delivered or 0
    en.fac, en.front = copy(d.fac), copy(d.front)
    local pend = copy(d.pending)
    local any = false
    for _, k in ipairs(CFG.ECHAIN.kinds) do if pend[k] > 0 then any = true end end
    en.pending = any and pend or nil
    en.rebuild = {}
    for i, r in ipairs(d.rebuild) do en.rebuild[i] = t + r end
    en.job = d.job and { kind = d.job.kind, left = d.job.left, total = d.job.total } or nil
    en.led = { bmat0 = d.led.bmat0, salv = d.led.salv, refined = d.led.refined, spent = d.led.spent,
        init = copy(d.led.init), made = copy(d.led.made), used = copy(d.led.used), lost = copy(d.led.lost) }
    -- sv.ser arredonda a 3 casas: a sobra (<= ECHAIN.tol, ja validada) e absorvida nos termos de origem
    -- (inicial/bmat0/colhido) para o razao em memoria fechar exato; nunca vira estoque.
    local Ld = en.led
    for _, k in ipairs(CFG.ECHAIN.kinds) do Ld.init[k] = logi.eHave(k) + Ld.used[k] + Ld.lost[k] - Ld.made[k] end
    Ld.bmat0 = en.bmat + Ld.spent - Ld.refined / CFG.LOGI.ratio
    Ld.salv = en.salvage + Ld.refined
    en.plan = nil
    combat.cargo = logi.eSoldiers()
    logi.eEvent("cadeia inimiga restaurada do save" .. (en.pending and (" (reenviar " .. logi.eFmt(en.pending) .. ")") or ""))
    return true
end
