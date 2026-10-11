-- pv4_cmd_capturar.lua - manda os soldados de COMBATE a um ponto de controle (orderMoveTo, como o botao direito; NAO usa mouse) para
-- captura-lo pela mecanica normal (um soldado leva 10 s de neutro a dono). Preparado e NAO executado. Edite PONTO (nome, ex.: "A").
-- Usos: ter um "ponto seu" para o ensaio B1 e para Shift+J (pv4_cmd_base_shiftj.lua). Confirme com pv4_estado.lua (PONTO ... dono 1 = seu).
local PONTO = "A"
local alvo
for _, p in ipairs(points()) do if p.name == PONTO then alvo = p end end
assert(alvo, "ponto " .. PONTO .. " nao existe")
local n = 0
for _, m in ipairs(squad()) do
    m.sel = (m.role ~= "worker")
    if m.sel then n = n + 1 end
end
assert(n > 0, "sem soldados de combate")
orderMoveTo(alvo.X, alvo.Y, alvo.Z or 0)
out("capturar", PONTO, "dono atual", tostring(alvo.owner), "soldados mandados", n, "(1 = seu, 0 = inimigo, nil = neutro)")
