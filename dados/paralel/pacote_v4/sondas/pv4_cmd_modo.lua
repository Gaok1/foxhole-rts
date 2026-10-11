-- pv4_cmd_modo.lua - liga/desliga ondas automaticas (como Shift+F4) ou inicia o Assalto (como Alt+F6) pelo canal. NAO injeta teclado.
-- Preparado e NAO executado. Edite MODO: "ondas" (LIGA: so alterna se estiver desligada) | "sem_ondas" (DESLIGA: so alterna se estiver ligada)
--   | "assalto" (rts.newAssault) | "limpar" (clearEnemies).
-- ATENCAO: newGame (Shift+F6 / pv4_cmd_partida.lua) JA liga as ondas (toggleWaves no fim). Por isso "ondas"/"sem_ondas" aqui sao idempotentes:
-- um toggle cego desligaria as ondas que a partida acabou de ligar. sv.save so grava com combat.auto ligado.
-- "assalto": esperado = nenhum comboio, frente inimiga intacta, recrutar usa mao de obra (ramo legado), Shift+J recusa
-- ("bases avancadas so numa partida com logistica (fora do Assalto)").
local MODO = "ondas"
if MODO == "ondas" then
    if not combat.auto then toggleWaves() end
    out("ondas automaticas", tostring(combat.auto))
elseif MODO == "sem_ondas" then
    if combat.auto then toggleWaves() end
    out("ondas automaticas", tostring(combat.auto))
elseif MODO == "assalto" then local ok, e = pcall(rts.newAssault); out("assalto", tostring(ok), tostring(e), "modo", tostring(combat.mode))
elseif MODO == "limpar" then clearEnemies(); out("inimigos limpos")
end
