-- pv4_cmd_recruit.lua - executa pelo canal o que Ctrl+1/2/3/4/0 chamam: recruit(papel, cursor). NAO injeta teclado.
-- Preparado e NAO executado. Edite as linhas abaixo:
--   ROLE   "rifle" | "mg" | "sniper" | "medic" | "officer"
--   ONDE   nome do ponto cujo CENTRO sera o cursor (ex.: "A", base avancada); "base" = centro da base principal;
--          "longe" = cursor longe de qualquer base/ponto (usa a base mais PERTO do esquadrao/cursor com estoque); nil = sem cursor.
--   VEZES  quantos recrutas seguidos.
-- Esperado (RELATORIO etapa2): cursor DENTRO de uma base = nasce so nela (sem camisas/fuzis la = recusa com motivo, sem cair noutra);
-- ponto sem base nao reforca; fuzileiro gasta 1 camisa + 1 fuzil; mg/sniper/medic/officer so 1 camisa; mao de obra NAO e gasta.
-- O texto exato esta no UE4SS.log ([FoxholeRTS] recrutado ... | camisas N, fuzis M).
local ROLE, ONDE, VEZES = "rifle", "A", 1
local at = nil
if ONDE == "base" then at = { X = logi.base.X, Y = logi.base.Y }
elseif ONDE == "longe" then at = { X = logi.base.X + 90000, Y = logi.base.Y + 90000 }
elseif ONDE ~= nil then
    for _, p in ipairs(points()) do if p.name == ONDE then at = { X = p.X, Y = p.Y } end end
    assert(at, "ponto " .. tostring(ONDE) .. " nao existe")
end
local function estoque()
    local t = { string.format("base c%d/f%d", logi.base.shirts or 0, logi.base.rifle or 0) }
    for _, fb in ipairs(logi.fwd) do t[#t + 1] = string.format("%s c%d/f%d", fb.pt.name, fb.dep.shirts or 0, fb.dep.rifle or 0) end
    return table.concat(t, " | ")
end
out("ANTES", "esquadrao", #squad(), "mao de obra", economy.manpower, estoque())
for i = 1, VEZES do
    local antes = #squad()
    local ok = recruit(ROLE, at)
    local onde = "-"
    if #squad() > antes then   -- onde nasceu: distancia ate a saida de base mais perto (nasce NA saida, exact = true) e ate a base principal
        local m = squad()[#squad()]
        local okp, l = pcall(function() return m.pawn:K2_GetActorLocation() end)
        if okp and l then
            local best, nome = math.huge, "-"
            for _, fb in ipairs(logi.fwd) do
                for _, e in ipairs(fb.exits or {}) do
                    local d = math.sqrt((l.X - e.X) ^ 2 + (l.Y - e.Y) ^ 2)
                    if d < best then best, nome = d, fb.pt.name end
                end
            end
            local db = math.sqrt((l.X - logi.base.X) ^ 2 + (l.Y - logi.base.Y) ^ 2)
            onde = string.format("XYZ %.0f,%.0f,%.0f | saida de base %s a %.0f cm | base principal a %.0f cm | papel %s", l.X, l.Y, l.Z, nome, best, db, tostring(m.role))
        end
    end
    out("recruit", ROLE, i, tostring(ok), onde)
end
out("DEPOIS", "esquadrao", #squad(), "mao de obra", economy.manpower, estoque())
