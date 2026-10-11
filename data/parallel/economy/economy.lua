-- Proposta pura: estoques em caixas na fábrica/caminhão; unidades no depósito/frente.
-- Não depende de UE4SS, inventário, RPC ou carga inicial gratuita.
local E = {}
E.recipes = {
    rifle = { code="RifleW", costs={Cloth=100}, units=20, time=70 },
    grenade = { code="GrenadeW", costs={Cloth=100, Explosive=40}, units=20, time=100 },
    medical = { code="Bandages", costs={Cloth=80}, units=50, time=40 },
}
local function integer(n) return type(n)=="number" and n>=0 and n%1==0 end
function E.start(factory, kind)
    local rc=E.recipes[kind]
    if not rc or factory.job then return false,"receita inválida/ocupada" end
    if not integer(rc.units) or rc.units<1 or not integer(rc.time) or rc.time<1 or next(rc.costs)==nil then
        return false,"schema inválido"
    end
    for material,amount in pairs(rc.costs) do
        if not integer(amount) or amount<1 then return false,"custo inválido" end
        local have=factory.materials[material] or 0
        if not integer(have) or have<amount then return false,"falta "..material end
    end
    -- Copiar receita reservada: mudança posterior de tabela não altera débito/reembolso/produção.
    local costs={}
    for material,amount in pairs(rc.costs) do
        factory.materials[material]=factory.materials[material]-amount;costs[material]=amount
    end
    factory.job={kind=kind,left=rc.time,costs=costs,units=rc.units}
    return true
end
function E.tick(factory, dt)
    if type(dt)~="number" or dt<0 or dt~=dt or dt==math.huge then return false end
    local job=factory.job
    if not job then return false end
    job.left=job.left-dt
    if job.left>0 then return false end
    factory.boxes[job.kind]=(factory.boxes[job.kind] or 0)+1
    factory.job=nil
    return true
end
function E.cancel(factory)
    local job=factory.job
    if not job then return false end
    for material,amount in pairs(job.costs) do factory.materials[material]=(factory.materials[material] or 0)+amount end
    factory.job=nil
    return true
end
function E.load(factory, truck, kind, count)
    if truck.dead or truck.cargo or not E.recipes[kind] or not integer(count) or count<1 then return false end
    local have=factory.boxes[kind] or 0
    if have<count or count>truck.capacity then return false end
    factory.boxes[kind]=have-count
    truck.cargo={kind=kind,boxes=count,units=E.recipes[kind].units}
    return true
end
function E.deliver(truck, depot)
    if truck.dead or not truck.cargo or not depot.friendly then return false end
    local cargo=truck.cargo
    depot.stock[cargo.kind]=(depot.stock[cargo.kind] or 0)+cargo.boxes*cargo.units
    truck.cargo=nil
    return true
end
function E.returnCargo(truck, factory)
    if truck.dead or not truck.cargo then return false end
    local cargo=truck.cargo
    factory.boxes[cargo.kind]=(factory.boxes[cargo.kind] or 0)+cargo.boxes
    truck.cargo=nil
    return true
end
function E.destroy(truck)
    if truck.dead then return false end
    truck.dead=true
    local cargo=truck.cargo
    truck.cargo=nil
    return cargo -- contabilizar perda, não crédito em estoque
end
function E.consume(depot, costs)
    if not depot.friendly or next(costs)==nil then return false end
    for kind,amount in pairs(costs) do
        if not E.recipes[kind] or not integer(amount) or amount<1 or (depot.stock[kind] or 0)<amount then return false end
    end
    for kind,amount in pairs(costs) do depot.stock[kind]=depot.stock[kind]-amount end
    return true
end
return E
