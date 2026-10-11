-- Próximo lote: fotografar contrato NPC/roster sem mutar atores nem ler IDs Steam.
-- Não executa RPC, OnRep, spawn, movimento ou callbacks persistentes.
local staticsClass = StaticFindObject('/Script/Engine.GameplayStatics')
if not valid(staticsClass) then out('GATE', 'GameplayStatics ausente'); return end
local stateGetter = false
staticsClass:ForEachFunction(function(f)
    if f:GetFName():ToString() ~= 'GetGameState' then return end
    local count, result, context = 0, false, false
    f:ForEachProperty(function(p)
        count = count + 1
        local name = p:GetFName():ToString()
        local object = p:GetClass():GetFName():ToString() == 'ObjectProperty'
        if name == 'ReturnValue' then result = object end
        if name == 'WorldContextObject' then context = object end
    end)
    stateGetter = count == 2 and result and context
end)
if not stateGetter then out('GATE', 'GetGameState assinatura divergente'); return end
local state = gs():GetGameState(world())
if not valid(state) or state.bActorIsBeingDestroyed then out('GATE', 'GameState ausente'); return end
local controllerClass = StaticFindObject('/Script/Engine.Controller')
if not valid(controllerClass) then out('GATE', 'Controller ausente'); return end
local confirmed = false
controllerClass:ForEachFunction(function(f)
    if f:GetFName():ToString() ~= 'IsLocalController' then return end
    local count, correct = 0, false
    f:ForEachProperty(function(p)
        count = count + 1
        correct = p:GetFName():ToString() == 'ReturnValue'
            and p:GetClass():GetFName():ToString() == 'BoolProperty'
    end)
    confirmed = count == 1 and correct
end)
if not confirmed then out('GATE', 'IsLocalController assinatura divergente'); return end

local roster, total = {}, 0
state.PlayerArray:ForEach(function(_, value)
    local ps = value:get()
    if valid(ps) and not ps.bActorIsBeingDestroyed then
        roster[ps:GetAddress()] = true
        total = total + 1
    end
end)
local seen, observed, members = {}, 0, 0
local function inspect(controller, origin)
    if not valid(controller) or controller.bActorIsBeingDestroyed then
        out('GATE', origin, 'controlador ausente/destruindo'); return
    end
    local address = controller:GetAddress()
    if seen[address] then return end
    seen[address] = true
    local ps = controller.PlayerState
    local psAlive = valid(ps) and not ps.bActorIsBeingDestroyed
    local member = psAlive and roster[ps:GetAddress()] == true or false
    local localController = controller:IsLocalController()
    if type(localController) ~= 'boolean' then out('GATE', origin, 'getter nao booleano'); return end
    observed = observed + 1
    if member then members = members + 1 end
    out('NPC_CONTRACT', origin, 'LOCAL', localController,
        'PLAYER', valid(controller.Player), 'PAWN', valid(controller.Pawn),
        'PLAYERSTATE', psAlive, 'IN_ROSTER', member,
        'BOT', psAlive and tostring(ps.bIsABot) or 'ausente',
        'INACTIVE', psAlive and tostring(ps.bIsInactive) or 'ausente')
end
inspect(playerController(), 'comandante')
for _, unit in ipairs(squad()) do inspect(unit.hpc, 'aliado') end
for _, unit in ipairs(enemies()) do inspect(unit.hpc, 'inimigo') end
for _, controller in ipairs(hpcPool()) do inspect(controller, 'pool') end
out('ROSTER', 'TOTAL', total, 'OBSERVED_CONTROLLERS', observed, 'MEMBERS', members)
out('LIMIT', 'nao le UniqueId; roster/localidade nao provam produtor do item nulo ou correcao do crash')
out('DONE', 'native_npc_roster_v1')
