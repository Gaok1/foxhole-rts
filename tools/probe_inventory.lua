-- Diagnostico SOMENTE LEITURA para o canal cmd.lua do laboratorio isolado.
-- Nao chama pickup/equip, nao cria itens e nao altera flags do personagem.
assert(valid(world()) and ksl():IsServer(world()) and not ksl():IsDedicatedServer(world()),
    "requer autoridade local")
assert(not world():GetFullName():find("MainMenu", 1, true), "nao executar no menu")

local function inspect(label, fn)
    local ok, value = pcall(fn)
    out(label, ok and tostring(value) or ("INDISPONIVEL: " .. tostring(value)))
end
local function objectName(obj)
    return valid(obj) and obj:GetFullName() or "nil/invalido"
end
local function inventory(label, items)
    out(label .. ".count", items:GetArrayNum())
    items:ForEach(function(i, entry)
        local item = entry:get()
        out(label, i, item.CodeName:ToString(), item.StackSize, objectName(item.PickupCDO))
    end)
end

out("world", world():GetFullName())
out("soldados", #squad())
for i, m in ipairs(squad()) do
    out("soldado", i, "grupo", m.group)
    if valid(m.pawn) then
        local p = m.pawn
        inspect("pawn", function() return objectName(p) end)
        inspect("classe", function() return objectName(p:GetClass()) end)
        inspect("HP", function() return p.Health end)
        inspect("atividade", function() return p.CharacterActivityStateInternal end)
        inspect("controller", function() return objectName(p.Controller) end)
        inspect("PlayerState", function() return objectName(m.hpc.PlayerState) end)
        inspect("local", function() return m.hpc.bIsLocalPlayerController end)
        inspect("ItemHolder", function() return objectName(p.ItemHolder) end)
        inspect("EquipmentHolder", function() return objectName(p.EquipmentItemHolder) end)
        inspect("inventario", function() inventory("inventario", p.ItemHolderItems); return "OK" end)
        inspect("equipamento", function() inventory("equipamento", p.EquipmentItemHolderItems); return "OK" end)
    else
        out("pawn invalido: ignorado")
    end
end
out("FIM: diagnostico nao tentou adquirir/equipar/disparar itens")
