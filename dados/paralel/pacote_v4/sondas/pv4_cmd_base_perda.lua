-- pv4_cmd_base_perda.lua - provoca a PERDA de uma base avancada pelo canal. Preparado e NAO executado. Edite:
--   MODO "morteiro" : 8 morteiros INIMIGOS (callMortar com time inimigo) sobre a base; a vida e do MOD (1725), dano x2 por granada
--                     dentro de raio*1.5; ~14 granadas derrubam; espere ~4 s apos o ultimo (delay 3 s).
--        "direto"   : chama logi.fwdLose(fb, "destruida") sem passar pelo caminho do morteiro (so a contabilidade da perda).
--        "captura"  : 5 inimigos sobre o ponto (spawnEnemies) para o inimigo tomar o ponto; leva dezenas de segundos (ponto
--                     neutro primeiro, depois inimigo). Observe com pv4_estado.lua; a base e perdida uma vez, ao virar INIMIGO do ponto
--                     ja neutralizado (neutro = INATIVA, estoque preservado).
--   INDICE qual base de logi.fwd (1 = a primeira).
-- Esperado: alerta "BASE AVANCADA X destruida/capturada: perdeu N camisas e M fuzis" UMA vez; ator destruido sem residuo
-- (FindAllOf("BPForwardBase1_C") sem ativos); estoque da base zerado; recapturar o ponto NAO traz a base de volta; o razao por base fecha
-- (pv4_estado: razao true); o painel perde a linha "base X".
local MODO, INDICE = "morteiro", 1
local fb = logi.fwd[INDICE]
assert(fb, "nao ha base avancada no indice " .. INDICE)
out("ANTES", "base", fb.pt.name, "hp_mod", fb.hp, "camisas", fb.dep.shirts, "fuzis", fb.dep.rifle, "bases", #logi.fwd)
if MODO == "direto" then
    out("fwdLose", tostring(logi.fwdLose(fb, "destruída")))
elseif MODO == "morteiro" then
    for i = 1, 8 do callMortar(fb.X, fb.Y, CFG.ENEMY_TEAM) end
    out("morteiros enviados: 8; rode pv4_estado.lua em ~6 s")
elseif MODO == "captura" then
    spawnEnemies({ X = fb.X + 300, Y = fb.Y, Z = fb.Z }, 5, true, true)
    out("5 inimigos criados sobre o ponto " .. fb.pt.name .. "; acompanhe com pv4_estado.lua a cada ~20 s")
end
