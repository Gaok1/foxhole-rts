-- pv4_cmd_base_shiftj.lua - executa pelo canal o que a tecla Shift+J chama: logi.fwdKey(cursor). NAO injeta teclado.
-- Preparado e NAO executado. Os 2 toques saem no mesmo instante (a janela de 4 s de tempo real e respeitada: 0 s < 4 s). A tecla
-- real (e o plain() que impede o J de disparar junto) e item do TESTE_MANUAL, nao deste script.
-- Edite as linhas abaixo:
--   PONTO    nome do ponto (ex.: "A"); nil = primeiro ponto SEU sem base.
--   TOQUES   1 (so informa custo/local) ou 2 (constroi, ou registra o pedido pendente se faltar bmat).
--   CREDITAR true = soma ao logi.bmat o que falta para 300 + reserva do caminhao, para o ensaio nao esperar a fabrica.
--            REGISTRE: a contabilidade de bmat do jogador deixa de valer depois disso (o ensaio B1 testa a classe, nao a economia).
-- Cada mensagem do mod (notify) tambem vai para o UE4SS.log com o prefixo [FoxholeRTS]: leia-o para o texto exato.
local PONTO, TOQUES, CREDITAR = nil, 2, false
local pt
for _, p in ipairs(points()) do
    if (PONTO == nil and p.owner == CFG.FRIENDLY_TEAM and not p.fb) or (PONTO ~= nil and p.name == PONTO) then pt = p; break end
end
assert(pt, "ponto nao encontrado (PONTO=" .. tostring(PONTO) .. ")")
if CREDITAR then
    local falta = CFG.FWD.cost + logi.rebuildReserve() - logi.bmat
    if falta > 0 then logi.bmat = logi.bmat + falta; out("CREDITADO bmat", falta, "(laboratorio)") end
end
local cur = { X = pt.X, Y = pt.Y, Z = pt.Z }
out("ANTES", "ponto", pt.name, "bases", #logi.fwd, "bmat", logi.bmat, "reserva caminhao", logi.rebuildReserve(), "pedido", logi.fwdOrder and logi.fwdOrder.pt.name or "-")
for i = 1, TOQUES do out("toque", i, "retorno", tostring(logi.fwdKey(cur))) end
out("DEPOIS", "bases", #logi.fwd, "bmat", logi.bmat, "pedido", logi.fwdOrder and logi.fwdOrder.pt.name or "-",
    "base no ponto", tostring(pt.fb ~= nil), "linha", pt.fb and logi.fwdLine(pt.dep) or "-")
