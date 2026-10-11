function logi.snapshot()
    if not logi.on then return nil end
    local d = { version=2, salvage=logi.salvage, bmat=logi.bmat, fa=logi.fac.ammo, fs=logi.fac.shirts,
        fr=logi.fac.rifle or 0, fm=logi.fac.medical or 0, ba=logi.base.ammo, bs=logi.base.shirts,
        br=logi.base.rifle or 0, bm=logi.base.medical or 0, prio=logi.prio, pts={}, trucks={} }
    for i, pt in ipairs(points) do d.pts[i] = pt.dep and { a=pt.dep.ammo, s=pt.dep.shirts, r=pt.dep.rifle or 0, m=pt.dep.medical or 0 } or false end
    if logi.job then d.job={kind=logi.job.kind,left=logi.job.left,total=logi.job.total} end
    for i, tr in ipairs(logi.trucks) do
        local q={state=tr.state,hp=tr.hp,salv=tr.salv or 0,wait=math.max(0,(tr.waitT or now())-now()),
            rebuild=math.max(0,(tr.rebuildT or now())-now())}
        if tr.cargo then
            q.cargo={}
            for _, kind in ipairs(CFG.LOGI.products) do q.cargo[kind]=tr.cargo[kind] or 0 end
            q.dest=tr.state=="returnCargo" and -1 or 0
            if tr.state~="returnCargo" and tr.dest ~= logi.base then
                for k, pt in ipairs(points) do if pt.dep == tr.dest then q.dest=k end end
            end
        end
        d.trucks[i]=q
    end
    return d
end
-- Pré-validação completa antes de start/reset; save legado sem novos campos continua aceito.
function logi.validateSave(d)
    local function number(n) return type(n)=="number" and n==n and n>=0 and n<math.huge end
    local function integer(n) return number(n) and n%1==0 end
    if type(d)~="table" or (d.version and d.version~=2) then return false end
    for _, key in ipairs({"salvage","bmat","ba"}) do if not number(d[key] or 0) then return false end end
    for _, key in ipairs({"fa","fs","fr","fm","bs","br","bm"}) do if not integer(d[key] or 0) then return false end end
    if d.prio and d.prio~="auto" and not CFG.LOGI.recipes[d.prio] then return false end
    if d.job then
        local j=d.job
        if type(j)~="table" or not CFG.LOGI.recipes[j.kind] or not number(j.left) or not number(j.total) or j.left>j.total then return false end
    end
    if d.pts and type(d.pts)~="table" then return false end
    for i,q in pairs(d.pts or {}) do
        if not integer(i) or i<1 or not points[i] then return false end
        if q then
            if type(q)~="table" or not number(q.a or 0) then return false end
            for _, key in ipairs({"s","r","m"}) do if not integer(q[key] or 0) then return false end end
        end
    end
    if d.trucks and type(d.trucks)~="table" then return false end
    local states={idle=true,toField=true,loading=true,toRef=true,toDep=true,returnCargo=true,dead=true}
    for i,q in pairs(d.trucks or {}) do
        if not integer(i) or i<1 or i>CFG.LOGI.supply+1 or type(q)~="table" or not states[q.state]
            or not number(q.hp) or not integer(q.salv or 0) or not number(q.wait or 0) or not number(q.rebuild or 0) then return false end
        if (i==1 and (q.state=="toDep" or q.state=="returnCargo")) or (i>1 and (q.state=="toField" or q.state=="toRef" or q.state=="loading")) then return false end
        if q.state=="dead" and (q.cargo or (q.salv or 0)>0) then return false end
        if (q.state=="toDep" or q.state=="returnCargo") and not q.cargo then return false end
        if q.cargo then
            if i==1 or (q.state~="toDep" and q.state~="returnCargo") or type(q.cargo)~="table" then return false end
            if q.state=="returnCargo" then
                if q.dest~=-1 then return false end
            elseif not integer(q.dest) or (q.dest>0 and not points[q.dest]) then return false end
            local n=0
            for key,value in pairs(q.cargo) do if not CFG.LOGI.recipes[key] or not integer(value) then return false end;n=n+value end
            if n<1 or n>CFG.LOGI.cap then return false end
        end
    end
    return true
end
function logi.restore(d)
    if not logi.validateSave(d) then return false end
    -- ready é só preflight; nenhuma estrutura do save é restaurada ou construída aqui.
    local setup=logi.ready()
    if not setup then return false end
    if not logi.start(setup) then return false end
    logi.salvage,logi.bmat,logi.prio=d.salvage or 0,d.bmat or 0,d.prio or "auto"
    logi.fac={ammo=d.fa or 0,shirts=d.fs or 0,rifle=d.fr or 0,medical=d.fm or 0}
    logi.base.ammo,logi.base.shirts,logi.base.rifle,logi.base.medical=d.ba or 0,d.bs or 0,d.br or 0,d.bm or 0
    for i,q in pairs(d.pts or {}) do
        if q then local dep=logi.depotOf(points[i]);dep.ammo,dep.shirts,dep.rifle,dep.medical=q.a or 0,q.s or 0,q.r or 0,q.m or 0 end
    end
    if d.job then logi.job={kind=d.job.kind,left=d.job.left,total=d.job.total} end
    for i,q in pairs(d.trucks or {}) do
        local tr=logi.trucks[i]
        tr.state,tr.hp,tr.salv=q.state,q.hp,(q.salv or 0)>0 and q.salv or nil
        tr.waitT,tr.rebuildT=now()+(q.wait or 0),now()+(q.rebuild or 0)
        if q.cargo then
            tr.cargo={};for _, kind in ipairs(CFG.LOGI.products) do tr.cargo[kind]=q.cargo[kind] or 0 end
            tr.dest=q.state=="returnCargo" and logi.factory or q.dest==0 and logi.base or logi.depotOf(points[q.dest])
            if q.state~="returnCargo" and tr.dest~=logi.base and tr.dest.pt.owner~=CFG.FRIENDLY_TEAM then
                tr.dest,tr.state=logi.factory,"returnCargo"
            end
            -- Coordenadas/trajeto antigo não são prova de rota regional segura: replanejar.
            tr.route,tr.routeDest,tr.pathJob=nil,nil,nil
        end
        if tr.state=="dead" and tr.pawn and valid(tr.pawn) then tr.pawn:SetActorHiddenInGame(true) end
    end
    return true
end
