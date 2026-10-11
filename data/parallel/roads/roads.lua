-- Núcleo offline. Não descobre nem presume estradas: recebe grafo nativo validado.
-- Nenhum userdata/cache por endereço. Coordenadas em cm, epoch muda com mundo/rede.
local roads = {}
local function dist(a,b)
    return math.sqrt((a.X-b.X)^2+(a.Y-b.Y)^2+(a.Z-b.Z)^2)
end
function roads.plan(net, startId, endId, epoch)
    if not net or net.epoch ~= epoch then return nil, 'regiao_invalida' end
    if not net.nodes[startId] or not net.nodes[endId] then return nil, 'acesso_ausente' end
    local cost, prev, closed = {[startId]=0}, {}, {}
    -- ponytail: Dijkstra O(V²), uma região; heap só após medição de orçamento.
    while true do
        local best
        for id,c in pairs(cost) do
            if not closed[id] and (not best or c < cost[best]) then best=id end
        end
        if not best then return nil, 'rota_ausente' end
        if best == endId then break end
        closed[best]=true
        for _,e in ipairs(net.edges[best] or {}) do
            -- Ponte/água/folga entram pela validação do trecho, nunca pelo nome do asset.
            if e.validated == true and not e.blocked and net.nodes[e.to] then
                local c=cost[best]+dist(net.nodes[best],net.nodes[e.to])
                if not closed[e.to] and (not cost[e.to] or c < cost[e.to]) then
                    cost[e.to],prev[e.to]=c,best
                end
            end
        end
    end
    local ids, id={},endId
    while id do table.insert(ids,1,id); id=prev[id] end
    return {ids=ids, index=2, epoch=epoch, distance=cost[endId]}
end
-- Retorna estado e ponto proposto; o adaptador deve executar sweep e confirmar posição
-- antes de atualizar tr.X/Y/Z. Nenhum estoque/carga é alterado por esta função.
function roads.advance(net, route, position, dt, speed, alive, clear)
    if not alive then return 'veiculo_destruido' end
    if not route or route.epoch ~= net.epoch then return 'regiao_invalida' end
    if dt < 0 or speed <= 0 then return 'parametro_invalido' end
    if route.index > #route.ids then return 'chegou',position end
    local a,b=route.ids[route.index-1],route.ids[route.index]
    local edge
    for _,e in ipairs(net.edges[a] or {}) do if e.to==b then edge=e; break end end
    if not edge or edge.validated ~= true or edge.blocked then return 'bloqueado' end
    local target=net.nodes[b]
    if not target then return 'regiao_invalida' end
    local d=dist(position,target)
    local step=math.min(d,speed*math.min(dt,0.5))
    local p=d==0 and target or {X=position.X+(target.X-position.X)*step/d,
        Y=position.Y+(target.Y-position.Y)*step/d,Z=position.Z+(target.Z-position.Z)*step/d}
    if not clear or not clear(position,p) then return 'bloqueado' end
    -- O índice só progride depois da confirmação do adaptador, via roads.commit.
    return 'movendo',p,step==d
end
function roads.commit(route, reached)
    if reached then route.index=route.index+1 end
end
return roads
