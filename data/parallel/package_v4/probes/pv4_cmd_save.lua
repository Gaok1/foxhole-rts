-- pv4_cmd_save.lua - grava a partida (sv.save) pelo canal e mede o tempo. NAO injeta teclado. Preparado e NAO executado.
-- sv.save so grava com ondas automaticas ligadas (combat.auto), partida nao encerrada e esquadrao nao vazio. O autosave faz o mesmo a cada 30 s.
-- Medida (persistencia, "Medicoes pedidas"): ms de sv.save no game thread (offline: ~11 ms para 120 unidades; ao vivo e gate).
-- Depois: listar os arquivos (save.txt, .bak, .tmp, .corrupt) com SHA256 FORA do jogo (ver ROTEIRO_LOTE).
local t0 = os.clock()
local ok, res = pcall(sv.save)
local ms = (os.clock() - t0) * 1000
out("sv.save", tostring(ok), tostring(res), string.format("%.1f ms", ms), "auto", tostring(combat.auto), "squad", #squad(), "degradado", sv.degraded and sv.degraded.why or "-")
