-- pv4_cmd_morteiro.lua - morteiro NOSSO (equivale a Ctrl+5; gasta 40 de mao de obra, recarga 20 s) sobre o comboio inimigo carregado, com
-- mira adiantada (o comboio anda a CFG.ECONVOY.speed = 900 cm/s e as granadas caem ~2,5 s depois). NAO usa mouse. Preparado e NAO executado.
-- IA_LOGISTICA L5: o mesmo resultado de L4 (uma perda no razao, alerta "COMBOIO INIMIGO DESTRUIDO (+25)"); um morteiro sobre caminhao JA
-- destruido nao registra 2a perda (rode este arquivo uma 2a vez no mesmo lugar depois da destruicao: edite REPETIR_NO_LUGAR = true).
local REPETIR_NO_LUGAR = false
if REPETIR_NO_LUGAR then
    assert(_G.pv4Mort, "nenhum alvo guardado (rode antes com REPETIR_NO_LUGAR = false)")
    out("repetindo em", string.format("%.0f,%.0f", _G.pv4Mort.x, _G.pv4Mort.y), "convoysCut antes", combat.convoysCut)
    callMortar(_G.pv4Mort.x, _G.pv4Mort.y)
    out("agendado; confira daqui a ~4 s: convoysCut NAO deve subir de novo")
    return
end
local foe
for _, tr in ipairs(logi.foes or {}) do if tr.state ~= "dead" and tr.cargo then foe = tr; break end end
assert(foe, "nenhum comboio inimigo carregado na estrada agora")
local x, y = foe.X, foe.Y
if foe.to then
    local dx, dy = foe.to.X - foe.X, foe.to.Y - foe.Y
    local d = math.sqrt(dx * dx + dy * dy)
    if d > 1 then local lead = CFG.ECONVOY.speed * CFG.MORTAR.delay; x, y = x + dx / d * lead, y + dy / d * lead end
end
_G.pv4Mort = { x = x, y = y }
out("comboio", foe.id, "estado", foe.state, "alvo", string.format("%.0f,%.0f", x, y), "convoysCut antes", combat.convoysCut, "mao de obra", economy.manpower)
out("callMortar", tostring(callMortar(x, y)))
