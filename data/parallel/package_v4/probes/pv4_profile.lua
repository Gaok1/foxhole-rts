-- pv4_profile.lua - le o perfil por sistema do mod (profile()) e REINICIA a janela. SO leitura de estado do jogo. Preparado e NAO executado.
-- Uso: rode no INICIO de cada janela (descarta a janela anterior e zera) e no FIM (a saida do segundo uso e a janela). Mesmo contrato dos
-- t_crash_*: profile() devolve "mod: X ms/quadro em N quadros | stratTick ..., squadTick ..." desde a chamada anterior.
-- Registrar sempre: qual janela (sem coleta / com coleta / com 3 bases ...), numero de soldados, selecionados e atores de contorno.
local n_sel, n_clone = 0, 0
for _, m in ipairs(squad()) do
    if m.sel then n_sel = n_sel + 1 end
    n_clone = n_clone + #(m.outline or {})
end
out("PERFIL", "soldados", #squad(), "selecionados", n_sel, "copias de contorno", n_clone, "bases", logi.fwd and #logi.fwd or 0,
    "coletores", (logi.col and #logi.col.units) or 0, "pausado", tostring(rts.paused))
out("PROFILE", profile())
