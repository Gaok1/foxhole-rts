-- pv4_cmd_prio.lua - equivale a Shift+L (logi.cyclePrio): auto -> munição -> camisas -> fuzis -> bandagens -> auto. NAO injeta teclado.
-- Preparado e NAO executado. Rode N vezes ate chegar na prioridade desejada (edite VEZES). A mensagem "fabrica: <nome>" vai ao UE4SS.log.
local VEZES = 1
for _ = 1, VEZES do logi.cyclePrio() end
out("prioridade", tostring(logi.prio), "bmat", logi.bmat, "job", logi.job and logi.job.kind or "-")
