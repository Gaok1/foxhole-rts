-- pv4_cmd_send.lua - equivale a L (logi.sendTo): o PROXIMO caminhao de suprimento vai ao deposito sob o "cursor". NAO injeta teclado.
-- Preparado e NAO executado. Edite ONDE: nome do ponto (ex.: "A", a base avancada) ou "base" (deposito da base principal) ou nil (automatico).
-- Esperado (BASES): o caminhao leva so o que cabe na base avancada (15 slots; caixa parcial conta 1) e camisas/fuzis so a quem pode reforcar
-- (base principal ou base avancada ativa); ponto sem base recebe so municao e bandagens. Acompanhe com pv4_state.lua (CAMINHAO ... carga).
local ONDE = "A"
local cur = nil
if ONDE == "base" then cur = { X = logi.base.X, Y = logi.base.Y, Z = logi.base.Z }
elseif ONDE ~= nil then
    for _, p in ipairs(points()) do if p.name == ONDE then cur = { X = p.X, Y = p.Y, Z = p.Z } end end
    assert(cur, "ponto " .. ONDE .. " nao existe")
end
logi.sendTo(cur)
out("sendTo", tostring(ONDE), "pino ->", logi.pin and (logi.pin == logi.base and "base" or tostring(logi.pin.name)) or "automatico")
