-- Sonda de canal para o LABORATORIO (NAO executada por CLAUDE_IA_LOGISTICA). Copiar para D:/tools/foxhole-lab/
-- e rodar com: sh D:/tools/foxhole-lab/run.sh t_ia_logistica.lua   (nunca com o botloop rodando)
-- So le estado do mod (tabelas logi/combat/CFG do env de runCommandFile); nao move atores nem altera estoque.
-- Pre-condicao: main.lua com o patch IA_LOGISTICA publicado e partida com logistica (Shift+F6) em andamento.
if not logi or not logi.eReport then out("IA_LOGISTICA ausente neste main.lua"); return end
local good, why = logi.eAudit()
out(string.format("auditoria=%s (%s) ativo=%s modo=%s onda=%d auto=%s", tostring(good), why, tostring(logi.eActive()),
    tostring(combat.mode), combat.wave or 0, tostring(combat.auto)))
out(logi.eReport())
for i, tr in ipairs(logi.foes or {}) do
    local p = tr.pawn
    local ok, alive = pcall(function() return p ~= nil and p:IsValid() and not p.bActorIsBeingDestroyed end)
    out(string.format("comboio %s estado=%s hp=%.0f XY=(%.0f,%.0f) carga=%s ator_ativo=%s rota=%s",
        tostring(tr.id), tostring(tr.state), tr.hp or -1, tr.X or 0, tr.Y or 0,
        tr.cargo and logi.eFmt(tr.cargo) or "-", tostring(ok and alive), tostring(tr.routeStatus)))
end
local en = logi.en
if en then
    for i = math.max(1, #en.events - 9), #en.events do out("evento " .. en.events[i]) end
end
out("HUD:" .. logi.eHud())
