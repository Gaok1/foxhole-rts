-- pv4_cmd_partida.lua - equivale a Shift+F6 (newGame) pelo canal; NAO injeta teclado. Preparado e NAO executado.
-- ATENCAO: newGame JA liga as ondas automaticas (toggleWaves no fim; a saida mostra auto=true). Para medir a coleta sem pressao rode
-- pv4_cmd_modo.lua com MODO="sem_ondas" logo depois.
-- Mude/rode so com o dono do laboratorio, sem botloop. Recusa (sem apagar a partida atual) se faltam campo/refinaria/fabrica/2 caminhoes
-- ativos: o motivo sai no UE4SS.log ("Partida nao iniciada: ..."). Em CallumsCapeHex rode Alt+L antes (logi.deploy, ver pv4_cmd_implantar.lua).
-- Saida: o que a v4 promete no inicio (coleta manual): caminhoes 3 (1 de recurso "dead" + 2 de suprimento), bmat 40, camisas 30,
-- fuzis 10, painel sem caminhao de recurso. Os 3 trabalhadores nascem a partir de ~5 s (CFG.COLETA.delay), um a cada ~3 s (spawnEvery), 1 camisa cada.
local ok, err = pcall(newGame)
out("newGame", tostring(ok), tostring(err))
out("logi.on", tostring(logi.on), "caminhoes", #logi.trucks, "modo", tostring(combat.mode), "auto", tostring(combat.auto))
if logi.on then
    for i, tr in ipairs(logi.trucks) do out("  caminhao", i, tr.kind, tr.state, "hp", tr.hp, "ator", tostring(tr.pawn ~= nil)) end
    out("  bmat", logi.bmat, "sucata", logi.salvage, "camisas", logi.base.shirts, "fuzis", logi.base.rifle, "reserva caminhao",
        logi.rebuildReserve and logi.rebuildReserve() or "-")
    out("  esperado v4 (manualStart): caminhoes 3 (res=dead), bmat 40, camisas 30, fuzis 10, reserva 100; trabalhadores em ~5 s")
end
