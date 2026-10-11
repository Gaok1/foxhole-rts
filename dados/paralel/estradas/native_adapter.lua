-- Contrato nativo -> roads.plan. Provas fisicas sao emitidas pelo validador vivo,
-- nunca deduzidas do asset. Este modulo nao chama UFunction nem mexe em estoque.
local adapter={}
function adapter.graph(snapshot,session,proofs)
    assert(type(session)=='string' and session~='','sessao obrigatoria')
    local net={epoch=snapshot.epoch..':'..session,nodes=snapshot.nodes,edges={}}
    for id,list in pairs(snapshot.edges) do
        net.edges[id]={}
        for _,edge in ipairs(list) do
            -- Uma prova de um trecho não autoriza todos os trechos da mesma spline.
            local proof=proofs and proofs[id] and proofs[id][edge.to]
            net.edges[id][#net.edges[id]+1]={to=edge.to,blocked=edge.blocked,
                validated=edge.road_asset==true and proof~=nil and proof.epoch==net.epoch
                    and proof.segment==edge.segment and proof.from==id and proof.to==edge.to
                    and proof.surface==true and proof.clearance==true and proof.support==true}
        end
    end
    return net
end
-- Acesso curto entre parada exterior validada e rede. planStart/planStep existentes
-- sao injetados pelo integrador (locais nao acessiveis de modulo externo).
function adapter.access(start,goal,nav,ignore,planStart)
    assert(nav and nav.body and nav.step and nav.maxNodes,'perfil estrito obrigatorio')
    return {job=planStart(start,goal,ignore,nav),status='planning'}
end
function adapter.accessTick(access,planStep,budget)
    if access.status~='planning' then return access.status end
    local result=planStep(access.job,budget)
    if result then
        access.status=(access.job.failed or #result==0) and 'failed' or 'ready'
        access.path=access.status=='ready' and result or nil
    end
    return access.status
end
-- Destino caiu: preserva carga; somente confirma devolucao ao chegar fisicamente.
function adapter.returnCargo(tr,factory,drive,dt)
    tr.dest=factory
    tr.state='returnCargo'
    if not drive(tr,factory,dt) then return false end
    factory.ammo=(factory.ammo or 0)+tr.cargo.ammo
    factory.shirts=(factory.shirts or 0)+tr.cargo.shirts
    tr.cargo,tr.dest,tr.state=nil,nil,'idle'
    return true
end
return adapter
