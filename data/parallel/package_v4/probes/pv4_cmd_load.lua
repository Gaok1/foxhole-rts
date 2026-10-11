-- pv4_cmd_load.lua - continua a partida salva (sv.load, equivale a Ctrl+F6) pelo canal e mede o tempo. NAO injeta teclado.
-- Preparado e NAO executado. Esperado: true e "PARTIDA CONTINUADA (...)" no UE4SS.log; recusa devolve false e a partida atual e o arquivo
-- ficam como estavam ("Continuar recusado (partida atual e save preservados): motivo"). Compare pv4_state.lua antes do save e depois do load.
local t0 = os.clock()
local ok, res = pcall(sv.load)
local ms = (os.clock() - t0) * 1000
out("sv.load", tostring(ok), tostring(res), string.format("%.1f ms", ms), "squad", #squad(), "bases", #logi.fwd, "degradado", sv.degraded and sv.degraded.why or "-")
