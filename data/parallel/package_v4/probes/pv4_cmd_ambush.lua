-- pv4_cmd_ambush.lua - manda os soldados de COMBATE (nao os trabalhadores) ao comboio inimigo carregado com orderMoveTo (equivale ao
-- botao direito; NAO usa mouse). Preparado e NAO executado. IA_LOGISTICA L4: soldados nossos a menos de CFG.LOGI.ambush = 1500 cm do
-- comboio o danificam; destruido, o razao registra "comboio N perdido (destruido): -X municao, -Y camisas" UMA vez, sai o alerta
-- "COMBOIO INIMIGO DESTRUIDO (+25)", a frente nao muda e a cadeia passa a "reconstruindo 1".
-- Rode quando pv4_state.lua mostrar um comboio carregado ("comboio N estado=... carga=...").
local foe
for _, tr in ipairs(logi.foes or {}) do if tr.state ~= "dead" and tr.cargo then foe = tr; break end end
assert(foe, "nenhum comboio inimigo carregado na estrada agora")
local n = 0
for _, m in ipairs(squad()) do
    m.sel = (m.role ~= "worker")
    if m.sel then n = n + 1 end
end
out("comboio", foe.id, "estado", foe.state, "XY", string.format("%.0f,%.0f", foe.X, foe.Y), "soldados de combate mandados", n)
orderMoveTo(foe.X, foe.Y, foe.Z or 0)
out("repita pv4_state.lua a cada ~5 s; o comboio anda em reta a CFG.ECONVOY.speed = 900 cm/s")
