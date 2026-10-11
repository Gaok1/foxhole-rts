-- pv4_cmd_trabalhador_ordem.lua - da uma ordem de movimento ao 1o trabalhador pelo canal (equivale ao botao direito, SEM mouse).
-- Preparado e NAO executado. Esperado (COLETA, item 5): ele sai da coleta (a carga em maos e perdida, log "coleta manual: ...") e,
-- sem nova ordem por CFG.COLETA.quiet = 60 s, volta sozinho. Confirme com pv4_estado.lua antes, logo depois e ~70 s depois.
local w
for _, m in ipairs(squad()) do if m.role == "worker" then w = m; break end end
assert(w, "sem trabalhador vivo no esquadrao (a coleta so os cria enquanto o caminhao de recurso nao existe)")
for _, m in ipairs(squad()) do m.sel = (m == w) end
local l = w.pawn:K2_GetActorLocation()
out("ordem ao trabalhador", "de", string.format("%.0f,%.0f", l.X, l.Y), "para", string.format("%.0f,%.0f", l.X + 4000, l.Y), "carga em maos", logi.col and "ver pv4_estado" or "-")
orderMoveTo(l.X + 4000, l.Y, l.Z)
