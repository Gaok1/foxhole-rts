-- Sonda PREPARADA (nao executada) para o agente LABORATORIO: copiar para D:/tools/foxhole-lab/ e rodar com
-- `sh D:/tools/foxhole-lab/run.sh t_persist_estado.lua` (sem botloop rodando). Somente leitura: nao salva,
-- nao continua, nao spawna. Imprime a contabilidade que precisa ser igual antes de salvar e depois de continuar.
local L, C = logi, CFG
local function n(x) return x == nil and "nil" or string.format("%.3f", x) end
out("mundo", sv.worldPath and sv.worldPath() or "(sem sv.worldPath: candidato nao aplicado)")
out("logi.on", tostring(L.on), "bmat", n(L.bmat), "sucata", n(L.salvage))
out("job", L.job and (L.job.kind .. " " .. n(L.job.left) .. "/" .. n(L.job.total)) or "-")
for _, kind in ipairs((C.LOGI and C.LOGI.products) or { "ammo", "shirts" }) do
    local cargo, deps = 0, (L.base and L.base[kind]) or 0
    for _, tr in ipairs(L.trucks or {}) do cargo = cargo + ((tr.cargo and tr.cargo[kind]) or 0) end
    for _, pt in ipairs(points()) do deps = deps + ((pt.dep and pt.dep[kind]) or 0) end
    out("produto", kind, "fabrica", (L.fac and L.fac[kind]) or 0, "carga", cargo, "depositos", n(deps))
end
for i, tr in ipairs(L.trucks or {}) do
    local p = tr.pawn
    out("caminhao", i, tr.state, "hp", n(tr.hp), "salv", tostring(tr.salv), "pawn", p and tostring(valid(p)) or "-",
        "escondido", p and valid(p) and tostring(p.bHidden) or "-", "rota", tostring(tr.route ~= nil))
end
local W = S.deploy
out("carteira", W and string.format("bmat %s gasto %s registros %d", tostring(W.bmat), tostring(W.spent), #(W.built or {})) or "nil")
for i, r in ipairs((W and W.built) or {}) do
    out("  pago", i, r.kind, tostring(r.code), n(r.x), n(r.y), n(r.z), n(r.yaw))
end
for _, cls in ipairs({ "BPRefinery_C", "BPFactory_C", "BPTruckW_C", "BPDestroyedRefinery_C", "BPDestroyedFactory_C", "BPSalvageField_C" }) do
    local live, hidden = 0, 0
    for _, a in ipairs(FindAllOf(cls) or {}) do
        if valid(a) and not a.bActorIsBeingDestroyed then
            live = live + 1
            if a.bHidden then hidden = hidden + 1 end
        end
    end
    out("atores", cls, "ativos", live, "ocultos", hidden)
end
out("inimigo", "combat.cargo", tostring(combat.cargo), "convoys", tostring(combat.convoys), "cut", tostring(combat.convoysCut),
    "elogi", L.eSnapshot and "IA_LOGISTICA integrada" or "-")
out("partida", "onda", combat.wave, "auto", tostring(combat.auto), "pontos", #points(), "soldados", #squad(), "inimigos", #enemies(),
    "barreiras", #structures(), "trincheiras", #trenches(), "postos", #S.tents, "arames", #S.wires)
out("degradado", sv.degraded and sv.degraded.why or "-")
local d, why, src = sv.read()
out("arquivo", d and ("valido v" .. tostring(d.v) .. " de save" .. tostring(src)) or ("sem save valido: " .. tostring(why)))
