local roles = {"rifle", "mg", "rifle", "medic", "sniper"}
rts._botI = (rts._botI or 0) + 1
local r = roles[(rts._botI % #roles) + 1]
local A = points()[1]
if #squad() < 12 and economy.manpower >= 45 then recruit(r, A.owner == 1 and A or nil) end
local en = enemies()
if #en > 0 and mortar.readyAt <= gs():GetTimeSeconds(world()) and economy.manpower >= 40 then
  local sx, sy, n = 0, 0, 0
  for _, e in ipairs(en) do if e.pawn:IsValid() and (e.pawn.Health or 0) > 0 then local l = e.pawn:K2_GetActorLocation(); sx, sy, n = sx + l.X, sy + l.Y, n + 1 end end
  if n >= 2 then callMortar(sx / n, sy / n) end
end
-- quem esta longe de A volta (sem ordem pendente)
for _, m in ipairs(squad()) do
  if m.pawn:IsValid() and not m.target and not m.focus then
    local l = m.pawn:K2_GetActorLocation()
    if math.sqrt((l.X - A.X)^2 + (l.Y - A.Y)^2) > 700 then m.target = {X = A.X + math.random(-200, 200), Y = A.Y + math.random(-200, 200), Z = l.Z} end
  end
end
local t = {}
for _, pt in ipairs(points()) do t[#t+1] = pt.name .. "=" .. tostring(pt.owner) end
out(table.concat(t, " "), "onda", combat.wave, "inim", #en, "sq", #squad(), "mp", math.floor(economy.manpower), "k/l", combat.kills, combat.losses, "auto", tostring(combat.auto), "won", tostring(combat.won), "mort", mortar.calls[1], mortar.calls[0], "gr", mortar.grenades[1], mortar.grenades[0], "dry", combat.dryOut or 0, "rs", math.floor(combat.resupplied or 0))
