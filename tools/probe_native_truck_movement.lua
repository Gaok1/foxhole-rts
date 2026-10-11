-- Leitura somente: contrato do movimento real antes de substituir o driver em reta.
-- Executar no proximo lote integrado, pelo canal, sem bot concorrente.
out('WORLD', world():GetFullName())
local setup, why = logi.scan()
if not setup then out('GATE', why); return end
local truck = setup.trucks[1]
if not valid(truck) or truck.bActorIsBeingDestroyed then out('GATE', 'truck invalido'); return end
out('TRUCK', truck:GetFullName(), 'ACTOR_COLLISION', truck:GetActorEnableCollision())

local function metadata(object, label)
    local cls = object:GetClass()
    for depth = 1, 12 do
        if not valid(cls) then break end
        out('CLASS', label, depth, cls:GetFullName())
        cls:ForEachProperty(function(p)
            local name = p:GetFName():ToString()
            if name:find('Movement') or name:find('Collision') or name:find('Root')
                or name:find('Updated') or name:find('Driver') or name:find('Input') then
                out('PROPERTY', label, name, p:GetClass():GetFName():ToString())
            end
            local kind = p:GetClass():GetFName():ToString()
            if (name == 'UpdatedComponent' or name == 'UpdatedPrimitive') and kind == 'ObjectProperty' then
                local value = object[name]
                out('OBJECT_PROPERTY', label, name, valid(value) and value:GetFullName() or 'invalido')
            elseif name == 'bIgnoreNonRootComponentsDuringVehicleMovement' and kind == 'BoolProperty' then
                out('BOOL_PROPERTY', label, name, object[name])
            end
        end)
        cls:ForEachFunction(function(f)
            local name = f:GetFName():ToString()
            if name:find('Move') or name:find('Drive') or name:find('Input') then
                out('FUNCTION', label, f:GetFullName())
                f:ForEachProperty(function(p)
                    out('PARAM', label, name, p:GetFName():ToString(), p:GetClass():GetFName():ToString())
                end)
            end
        end)
        cls = cls:GetSuperStruct()
    end
end

-- Getter sem parametros, retorno objeto: assinatura confirmada antes da chamada.
local function objectGetter(ownerClass, name, call)
    local cls = StaticFindObject(ownerClass)
    if not valid(cls) then out('GATE', name, 'classe ausente'); return end
    local confirmed = false
    cls:ForEachFunction(function(f)
        if f:GetFName():ToString() == name then
            local count, objectReturn = 0, false
            f:ForEachProperty(function(p)
                count = count + 1
                objectReturn = p:GetFName():ToString() == 'ReturnValue'
                    and p:GetClass():GetFName():ToString() == 'ObjectProperty'
                out('GETTER_PARAM', name, p:GetFName():ToString(), p:GetClass():GetFName():ToString())
            end)
            confirmed = count == 1 and objectReturn
        end
    end)
    if not confirmed then out('GATE', name, 'assinatura nao confirmada'); return end
    local value = call()
    if not valid(value) then out('GATE', name, 'retorno invalido'); return end
    out('OBJECT', name, value:GetFullName())
    metadata(value, name)
end

metadata(truck, 'truck')
objectGetter('/Script/Engine.Actor', 'K2_GetRootComponent', function() return truck:K2_GetRootComponent() end)
objectGetter('/Script/Engine.Pawn', 'GetMovementComponent', function() return truck:GetMovementComponent() end)
out('LIMIT', 'Root/UpdatedComponent nao provam envelope integral nem autorizam movimento, colisao ou arestas')
out('DONE', 'native_truck_movement_v1')
