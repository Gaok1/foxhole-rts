-- pv4_cmd_matar_caminhao.lua - destroi um caminhao NOSSO pelo canal (logi.hit com dano enorme). Preparado e NAO executado.
-- Edite as duas linhas abaixo antes de rodar.
--   KIND = "res" (caminhao de recurso) ou "sup" (suprimento).
--   ZERAR = true: zera logi.bmat e logi.salvage antes (COLETA item 6: sem material nem caminhao, a coleta manual REATIVA e a
--           fabrica reconstroi o caminhao quando juntar 100 bmat). ATENCAO: altera estoque do jogador; so no ensaio.
-- Esperado: alerta "CAMINHAO DESTRUIDO: carga perdida"; o caminhao volta em CFG.LOGI.rebuild = 30 s por 100 bmat se houver bmat
-- (reserva de bmat: a fabrica guarda 100 por caminhao destruido); o painel mostra "Fabrica | guarda 100 bmat para reconstruir caminhao".
local KIND, ZERAR = "res", false
if ZERAR then logi.bmat, logi.salvage = 0, 0 end
local t = gs():GetTimeSeconds(world())
local alvo
for i, tr in ipairs(logi.trucks) do
    if tr.kind == KIND and tr.state ~= "dead" then alvo = i; break end
end
if not alvo then out("nenhum caminhao " .. KIND .. " vivo (ja destruido ou ainda por construir)"); return end
out("destruindo caminhao", alvo, KIND, "hp", logi.trucks[alvo].hp, "resultado", tostring(logi.hit(logi.trucks[alvo], 1e9, t)))
out("estado", logi.trucks[alvo].state, "bmat", logi.bmat, "sucata", logi.salvage, "reserva", logi.rebuildReserve())
