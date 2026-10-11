-- pv4_state.lua - SONDA SO DE LEITURA da pilha v4 (PACOTE_V4). Preparada e NAO executada no jogo.
-- Uso (nunca com o botloop rodando): copiar para D:/tools/foxhole-lab/ e rodar
--     sh D:/tools/foxhole-lab/run.sh pv4_state.lua
-- Imprime, em secoes independentes (cada uma em pcall; um erro numa secao nao esconde as outras): constantes que o candidato
-- v4 usa, fabrica/reservas, caminhoes, coleta manual e trabalhadores, depositos e bases avancadas, razoes (coleta, base,
-- cadeia inimiga), estado do save (sv.degraded) e o tamanho do painel. NAO altera estado, NAO cria atores, NAO grava arquivo.
-- Roda no env de runCommandFile: so enxerga o que la esta (out, logi, CFG, combat, squad(), points(), sv, S, economy, rts,
-- valid, world, gs, ...). Para comparar antes/depois (save -> continuar), rode duas vezes e compare as saidas com diff.
local L, C = logi, CFG
local function n(x) if x == nil then return "nil" end return string.format("%.2f", x) end
local function b(x) return tostring(x) end
local function sec(name, fn)
    local ok, err = pcall(fn)
    if not ok then out("ERRO secao " .. name, tostring(err)) end
end

sec("mundo", function()
    out("MUNDO", sv.worldPath and sv.worldPath() or "?", "modo", b(combat.mode), "onda", b(combat.wave), "auto", b(combat.auto),
        "rts.active", b(rts.active), "logi.on", b(L.on), "t(s)", n(gs():GetTimeSeconds(world())))
end)

sec("constantes", function()
    out("CFG", "COLETA.manualStart", b(C.COLETA and C.COLETA.manualStart), "bmat0", b(C.COLETA and C.COLETA.bmat0),
        "workers", b(C.COLETA and C.COLETA.workers), "DEPLOY.budget", b(C.DEPLOY.budget), "SQUAD_MAX", b(C.SQUAD_MAX))
    out("CFG", "FWD.cost", b(C.FWD and C.FWD.cost), "hp", b(C.FWD and C.FWD.hp), "cap", b(C.FWD and C.FWD.cap), "max",
        b(C.FWD and C.FWD.max), "confirm", b(C.FWD and C.FWD.confirm), "pending", b(C.FWD and C.FWD.pending),
        "strict", b(C.FWD and C.FWD.strict), "ruin", b(C.FWD and C.FWD.ruin), "teamId", b(C.FWD and C.FWD.teamId),
        "visual", b(C.FWD and C.FWD.visual))
    out("CFG", "SPAWN.pointSpawn", b(C.SPAWN and C.SPAWN.pointSpawn), "startRifles", b(C.SPAWN and C.SPAWN.startRifles),
        "ECHAIN.free", b(C.ECHAIN and C.ECHAIN.free), "trip", b(C.ECHAIN and C.ECHAIN.trip), "PERSIST.version",
        b(C.PERSIST and C.PERSIST.version), "fwdVersion", b(C.PERSIST and C.PERSIST.fwdVersion))
end)

if not L.on then out("LOGISTICA DESLIGADA: inicie uma partida (Shift+F6) e rode de novo"); return end

sec("fabrica", function()
    out("FABRICA", "bmat", n(L.bmat), "sucata", n(L.salvage), "prio", b(L.prio),
        "job", L.job and (b(L.job.kind) .. " " .. n(L.job.left) .. "/" .. n(L.job.total)) or "-",
        "pronto m/c/f/b", b(L.fac.ammo) .. "/" .. b(L.fac.shirts) .. "/" .. b(L.fac.rifle) .. "/" .. b(L.fac.medical))
    out("RESERVA", "caminhao", b(L.rebuildReserve and L.rebuildReserve()), "base avancada", b(L.fwdReserve and L.fwdReserve()),
        "pedido", L.fwdOrder and (b(L.fwdOrder.pt.name) .. " custo " .. b(L.fwdOrder.cost) .. " t0 " .. n(L.fwdOrder.t0)) or "-",
        "livre p/ base", n(L.bmat - (L.rebuildReserve and L.rebuildReserve() or 0)))
end)

sec("caminhoes", function()
    for i, tr in ipairs(L.trucks) do
        local c = tr.cargo
        local alive = false
        if tr.pawn then local ok, v = pcall(function() return valid(tr.pawn) and not tr.pawn.bActorIsBeingDestroyed end); alive = ok and v end
        out("CAMINHAO", i, "tipo", b(tr.kind), "estado", b(tr.state), "hp", n(tr.hp), "ator_vivo", b(alive),
            "XY", n(tr.X) .. "," .. n(tr.Y), "destino", tr.dest and b(tr.dest.name) or "-",
            "carga", c and (b(c.ammo or 0) .. "m/" .. b(c.shirts or 0) .. "c/" .. b(c.rifle or 0) .. "f/" .. b(c.medical or 0) .. "b") or "-",
            "sucata", n(tr.salv))
    end
end)

sec("coleta", function()
    local K = L.col
    local w, comb = 0, 0
    for _, m in ipairs(squad()) do if m.role == "worker" then w = w + 1 else comb = comb + 1 end end
    out("ESQUADRAO", "trabalhadores", w, "combate", comb, "total", #squad(), "mao_de_obra", n(economy.manpower))
    if not K then out("COLETA", "(sem estado de coleta)"); return end
    local ok, why = true, "-"
    if L.colAudit then ok, why = L.colAudit() end
    out("COLETA", "ativa", b(K.active), "unidades", #K.units, "colhido", n(K.gathered), "entregue", n(K.delivered),
        "perdido", n(K.lost), "viagens", b(K.trips), "razao", b(ok), b(why), "colDown", b(L.colDown and L.colDown()))
    out("COLETA_PAINEL", b(L.colHud and L.colHud()))
end)

sec("depositos", function()
    for _, d in ipairs(L.depots()) do
        out("DEPOSITO", d.name, "munic", n(d.ammo), "camisas", b(d.shirts), "fuzis", b(d.rifle), "bandagens", b(d.medical),
            "slots", b(L.slotsUsed and L.slotsUsed(d)), "reforca", b(L.spawnCapable and L.spawnCapable(d)))
        if L.fwdLine and (d == L.base or d.fb) then out("  LINHA", L.fwdLine(d)) end
    end
    out("PODE_REFORCAR", b(L.canReinforce and L.canReinforce()), "noReinforce", b(L.noReinforce and L.noReinforce()))
end)

sec("bases", function()
    out("BASES", "n", #L.fwd, "perdidas", b(L.fwdLost or 0), "S.fwdConfirm", b(S.fwdConfirm ~= nil))
    for i, fb in ipairs(L.fwd) do
        local cls, hp, alive = "-", "-", false
        if fb.actor then
            local ok, v = pcall(function() return valid(fb.actor) and not fb.actor.bActorIsBeingDestroyed end)
            alive = ok and v
            if alive then
                pcall(function() cls = fb.actor:GetClass():GetFName():ToString() end)
                pcall(function() hp = n(fb.actor.Health) .. "/" .. n(fb.actor.MaxHealth) end)
            end
        end
        local ok, why = L.fwdAudit(fb)
        out("BASE", i, "ponto", b(fb.pt.name), "dono", b(fb.pt.owner), "morta", b(fb.dead), "hp_mod", n(fb.hp) .. "/" .. n(fb.maxHp),
            "XYZ", n(fb.X) .. "," .. n(fb.Y) .. "," .. n(fb.Z), "yaw", n(fb.yaw), "saidas", fb.exits and #fb.exits or "-",
            "ator_vivo", b(alive), "classe", cls, "hp_ator", hp, "razao", b(ok), b(why),
            "ledger init/rx/usado/perdido camisas", b(fb.led.init.shirts) .. "/" .. b(fb.led.rx.shirts) .. "/" .. b(fb.led.used.shirts) .. "/" .. b(fb.led.lost.shirts),
            "fuzis", b(fb.led.init.rifle) .. "/" .. b(fb.led.rx.rifle) .. "/" .. b(fb.led.used.rifle) .. "/" .. b(fb.led.lost.rifle))
    end
end)

sec("pontos", function()
    for i, p in ipairs(points()) do
        out("PONTO", i, p.name, "dono", b(p.owner), "XY", n(p.X) .. "," .. n(p.Y), "base", b(p.fb ~= nil),
            "estoque", p.dep and (b(p.dep.shirts) .. "c/" .. b(p.dep.rifle) .. "f") or "-")
    end
end)

sec("cadeia inimiga", function()
    if not L.eReport then out("CADEIA_INIMIGA", "(ausente)"); return end
    local good, why = L.eAudit()
    out("CADEIA_INIMIGA", "auditoria", b(good), b(why), "ativa", b(L.eActive()))
    out(L.eReport())
    for _, tr in ipairs(L.foes or {}) do
        local alive = false
        if tr.pawn then local ok, v = pcall(function() return valid(tr.pawn) and not tr.pawn.bActorIsBeingDestroyed end); alive = ok and v end
        out("COMBOIO", b(tr.id), "estado", b(tr.state), "hp", n(tr.hp), "XY", n(tr.X) .. "," .. n(tr.Y),
            "carga", tr.cargo and L.eFmt(tr.cargo) or "-", "ator_vivo", b(alive), "routeStatus", b(tr.routeStatus))
    end
    if L.en then for i = math.max(1, #L.en.events - 5), #L.en.events do out("EVENTO " .. L.en.events[i]) end end
    out("HUD" .. L.eHud())
end)

sec("lugares", function()
    local function d(a, c) if not (a and c) then return "nil" end return n(math.sqrt((a.X - c.X) ^ 2 + (a.Y - c.Y) ^ 2)) end
    out("LUGARES", "campo", n(L.field and L.field.X) .. "," .. n(L.field and L.field.Y), "refinaria", n(L.refinery and L.refinery.X) .. "," .. n(L.refinery and L.refinery.Y),
        "fabrica", n(L.factory and L.factory.X) .. "," .. n(L.factory and L.factory.Y), "base", n(L.base.X) .. "," .. n(L.base.Y))
    out("DISTANCIAS (cm)", "campo-refinaria", d(L.field, L.refinery), "refinaria-fabrica", d(L.refinery, L.factory), "fabrica-base", d(L.factory, L.base),
        "(coleta: 80 m = 165 s ate o 1o caminhao; 470 m = ~359 s no harness)")
end)

sec("atores", function()
    local function count(cls)
        local c = 0
        for _, a in ipairs(FindAllOf(cls) or {}) do if valid(a) and not a.bActorIsBeingDestroyed then c = c + 1 end end
        return c
    end
    out("ATORES ATIVOS", "BPTruckW_C", count("BPTruckW_C"), "BPTruckC_C", count("BPTruckC_C"), "BPForwardBase1_C", count("BPForwardBase1_C"),
        "BPDestroyedForwardBase1_C", count("BPDestroyedForwardBase1_C"), "BPRefinery_C", count("BPRefinery_C"), "BPFactory_C", count("BPFactory_C"),
        "(esperado: BPForwardBase1_C == bases vivas em BASES n)")
end)

sec("save", function()
    out("SAVE", "degradado", sv.degraded and sv.degraded.why or "-", "pedido_pendente_salvo", "nao (por desenho)")
end)

sec("painel", function()
    local h = L.hudLine()
    local lines, widest = 0, 0
    for line in (h .. "\n"):gmatch("(.-)\n") do
        lines = lines + 1
        local len = utf8.len(line) or #line
        if len > widest then widest = len end
    end
    out("PAINEL", "linhas", lines, "mais_larga", widest, "(v4 offline: 12-13 linhas x 222; clipping real e gate visual)")
end)
