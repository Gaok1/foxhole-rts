-- pv4_B1_limpar.lua - destroi o ator do ensaio pv4_B1_forwardbase.lua (PACOTE_V4). Preparado e NAO executado.
-- Destroi SO o ator guardado em _G.pv4B1; nunca toca logi.fwd, pontos, estoques ou save. Confere que ele sumiu.
local B = _G.pv4B1
if not (B and B.actor) then out("B1 LIMPAR", "nada a limpar (_G.pv4B1 ausente)"); return end
local a = B.actor
local ok, alive = pcall(function() return valid(a) and not a.bActorIsBeingDestroyed end)
if ok and alive then
    local okd, err = pcall(function() a:K2_DestroyActor() end)
    out("B1 LIMPAR", "K2_DestroyActor", tostring(okd), tostring(err))
else
    out("B1 LIMPAR", "ator ja invalido/em destruicao (ok)", tostring(ok), tostring(alive))
end
-- IsValid continua true ate o GC (AGENTS.md): conferir pelo bActorIsBeingDestroyed
local ok2, still = pcall(function() return valid(a) and not a.bActorIsBeingDestroyed end)
out("B1 LIMPAR", "ainda_ativo_apos_destroy", tostring(ok2 and still), "(esperado false)")
_G.pv4B1 = nil
