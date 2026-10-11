-- Proposta isolada: substituir somente logi.hudLine; nenhuma escrita em estoques/atores.
-- O TextBlock e o atual hudTick continuam sendo o renderizador (0,25 s de tempo real).
function logi.hudLine()
    if not logi.on then return "LOGÍSTICA INATIVA" end
    local C = CFG.LOGI
    local function recipeName(kind)
        return C.recipes[kind] and C.recipes[kind].name or tostring(kind)
    end
    local fab
    if logi.job then
        fab = string.format("%s: %.0f s restantes", recipeName(logi.job.kind), math.max(0, logi.job.left))
        if logi.job.total then fab = fab .. string.format(" (total %.0f s)", logi.job.total) end
    else
        fab = logi.nextKind() and "aguarda bmat" or "parada: demanda atendida"
    end
    local lines = {
        string.format("LOGÍSTICA | sucata %.0f | bmat %.0f | prioridade %s", logi.salvage, logi.bmat, logi.prio),
        "Fábrica | " .. fab,
        string.format("Pronto | munição %d caixas | camisas %d caixas (%d unidades)",
            logi.fac.ammo, logi.fac.shirts, logi.fac.shirts * C.recipes.shirts.units),
    }
    for _, d in ipairs(logi.depots()) do
        -- Estoque físico, não necessidade após descontar carga em trânsito.
        local a, sh = d.ammo or 0, d.shirts or 0
        local low = a < C.want.ammo or sh < C.want.shirts
        lines[#lines + 1] = string.format("%s | munição %.0f | camisas %d%s", d.name, a, sh,
            low and " | abaixo da meta" or "")
    end
    local states = { idle="retorno/aguarda fábrica", toField="ao campo", loading="carregando sucata",
        toRef="à refinaria", toDep="ao depósito", dead="destruído" }
    for i, tr in ipairs(logi.trucks) do
        local cargo = tr.cargo
        local load = cargo and string.format("%d munição + %d camisas (caixas)", cargo.ammo, cargo.shirts)
            or string.format("%.0f sucata", tr.salv or 0)
        local dest = tr.dest and tr.dest.name or
            (tr.state == "toField" and "campo" or tr.state == "toRef" and "refinaria" or
                tr.state == "loading" and "campo" or
                tr.state == "idle" and (tr.kind == "res" and "campo" or "fábrica") or "—")
        -- Não apresentar carga/destino histórico como entrega pendente de veículo morto.
        if tr.state == "dead" then load, dest = "perdida", "—" end
        lines[#lines + 1] = string.format("Caminhão %d | %s | %s | destino %s", i,
            (tr.state == "idle" and tr.kind == "res") and "iniciando coleta" or
                states[tr.state] or tostring(tr.state), load, dest)
    end
    if combat.mode ~= "assault" then
        lines[#lines + 1] = string.format("INIMIGO | carga %d%s", combat.cargo or 0,
            #(logi.foes or {}) > 0 and " | comboio na estrada" or "")
    end
    lines[#lines + 1] = "Ctrl+L: foco na cadeia | Q/E: frentes | Espaço: último alerta"
    return table.concat(lines, "\n")
end
