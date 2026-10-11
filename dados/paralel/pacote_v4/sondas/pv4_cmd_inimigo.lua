-- pv4_cmd_inimigo.lua - cria inimigos reais num lugar escolhido (spawnEnemies) pelo canal. NAO injeta teclado. Preparado e NAO executado.
-- Edite ONDE e N. Usos no roteiro: COLETA item 7 (inimigo perto do campo: trabalhadores pausam, morte repoe por 1 camisa) e
-- BASES (inimigo no anel do ponto: Shift+J recusa "ha inimigos no ponto X"; captura/perda do ponto).
--   ONDE  "campo" (800 cm do campo de sucata) | "base" (a 2500 cm da base principal) | nome de ponto (ex.: "B")
--   N     quantos (use 1 para o teste da coleta)
-- Cada chamada com sameWave = true NAO conta como nova onda. Limpe depois com pv4_cmd_modo.lua (MODO = "limpar").
local ONDE, N = "campo", 1
local at
if ONDE == "campo" then at = { X = logi.field.X + 800, Y = logi.field.Y, Z = logi.field.Z }
elseif ONDE == "base" then at = { X = logi.base.X + 2500, Y = logi.base.Y, Z = logi.base.Z }
else
    for _, p in ipairs(points()) do if p.name == ONDE then at = { X = p.X + 300, Y = p.Y, Z = p.Z } end end
end
assert(at, "lugar nao encontrado: " .. tostring(ONDE))
out("ANTES", "inimigos", #enemies())
spawnEnemies(at, N, true, true)
out("DEPOIS", "inimigos", #enemies(), "em", string.format("%.0f,%.0f", at.X, at.Y))
