from pathlib import Path
from lupa import LuaRuntime
from build_patch import build, ROOT, HERE
source=ROOT.joinpath('mod/FoxholeRTS/Scripts/main.lua').read_text(encoding='utf-8')
proposal=build(source)
# Execute complete candidate chunk, not copies of production functions.
scaffold=ROOT.joinpath('tools/test_orders.py').read_text(encoding='utf-8')
start=scaffold.index("lua.execute('''")+len("lua.execute('''")
end=scaffold.index("''')",start)
lua=LuaRuntime();lua.execute(scaffold[start:end])
api=lua.execute(proposal+'''
return {logi=logi,CFG=CFG,points=points,medicTick=medicTick,recruit=recruit,economy=economy,squad=squad,
    hooks={spawn=function(fn) spawnSquad=fn end, authority=function(fn) isLocalAuthority=fn end}}
''')
lua.globals().api=api
lua.execute('''
local L,C,P=api.logi,api.CFG,api.points
clock=0
local function init()
    L.on=true;L.prio='auto';L.salvage=0;L.bmat=300;L.made=0;L.job=nil
    L.fac={ammo=0,shirts=0,rifle=0,medical=0}
    L.base={name='base',X=0,Y=0,Z=0,ammo=6,shirts=20,rifle=0,medical=0}
    L.factory={name='fábrica',X=1000,Y=0,Z=0}
    L.trucks={{kind='res',state='idle',hp=900},{kind='sup',state='idle',hp=900},{kind='sup',state='idle',hp=900}}
    P[1]={name='A',X=0,Y=0,Z=0,owner=C.FRIENDLY_TEAM}
end
init()
assert(C.LOGI.recipes.rifle.bmat==100 and C.LOGI.recipes.rifle.units==20)
assert(C.LOGI.recipes.medical.bmat==80 and C.LOGI.recipes.medical.units==50)
assert(not C.LOGI.recipes.grenade) -- Explosive supply not implemented.
L.prio='rifle';L.factoryStep(0)
assert(L.bmat==200 and L.job.kind=='rifle')
L.factoryStep(14)
assert(L.fac.rifle==1 and not L.job)
L.prio='medical';L.factoryStep(0);L.factoryStep(8)
assert(L.bmat==120 and L.fac.medical==1)
L.prio='auto'
assert(L.needs(L.base).rifle==1 and L.needs(L.base).medical==1)
-- Direct engine drive mocked, decisions remain actual candidate functions.
L.drive=function() return true end
L.pin=L.base
local tr=L.trucks[2]
L.truckStep(tr,1,1)
assert(tr.state=='toDep' and tr.cargo.rifle==1 and tr.cargo.medical==1)
assert(L.fac.rifle==0 and L.fac.medical==0)
L.truckStep(tr,1,2)
assert(L.base.rifle==20 and L.base.medical==50 and tr.state=='idle')
L.truckStep(tr,1,3)
assert(L.base.rifle==20 and L.base.medical==50)
-- Capture invalidation returns closed boxes exactly once.
L.fac.rifle=1;L.pin=L.depotOf(P[1]);L.truckStep(tr,1,4)
P[1].owner=C.ENEMY_TEAM
L.truckStep(tr,1,5)
assert(L.fac.rifle==0 and tr.cargo.rifle==1 and tr.state=='returnCargo')
L.drive=function() return false end
L.truckStep(tr,1,6)
assert(L.fac.rifle==0 and tr.cargo.rifle==1)
L.drive=function() return true end
L.truckStep(tr,1,6)
assert(L.fac.rifle==1 and not tr.cargo and tr.state=='idle')
-- Destruction deletes all product cargo; never recredits factory/depot.
P[1].owner=C.FRIENDLY_TEAM
L.pin=L.depotOf(P[1]);L.truckStep(tr,1,7)
assert(tr.cargo.rifle==1)
tr.X,tr.Y,tr.Z=0,0,0
L.hit(tr,1000,8)
assert(tr.state=='dead' and not tr.cargo and L.fac.rifle==0)
-- Recruitment actual control path; spy replaces only engine spawn boundary.
api.economy.manpower=100
api.hooks.authority(function() return true end)
api.hooks.spawn(function() return 0 end)
local shirts,rifles=L.base.shirts,L.base.rifle
assert(not api.recruit('rifle',{X=0,Y=0,Z=0}))
assert(L.base.shirts==shirts and L.base.rifle==rifles and api.economy.manpower==100)
api.hooks.spawn(function() return 1 end)
assert(api.recruit('rifle',{X=0,Y=0,Z=0}))
assert(L.base.shirts==shirts-1 and L.base.rifle==rifles-1)
L.base.rifle=0
assert(not api.recruit('rifle',{X=0,Y=0,Z=0}))
-- Medic actual treatment consumes only after health gain near stocked depot.
local function soldier(role,hp,x)
    return {role=role,team=C.FRIENDLY_TEAM,pawn={Health=hp,MaxHealth=100,
        IsValid=function() return true end,K2_GetActorLocation=function() return {X=x or 0,Y=0,Z=0} end,
        OnRep_Health=function() end,OnRep_IsBleeding=function() end}}
end
local medic,target=soldier('medic',100),soldier('rifle',50)
L.base.medical=0
api.medicTick(medic,{target})
assert(target.pawn.Health==50)
L.base.medical=2
api.medicTick(medic,{target})
assert(target.pawn.Health==62 and L.base.medical==1)
api.medicTick(medic,{target})
assert(target.pawn.Health==62 and L.base.medical==1)
clock=100;target.pawn.Health=100
api.medicTick(medic,{target})
assert(L.base.medical==1)
-- Save preserves debited job, transit boxes, loading sucata and depot unit stocks.
init();P[1].owner=C.FRIENDLY_TEAM
L.job={kind='rifle',left=4,total=14};L.bmat=200
L.trucks[1].state='toRef';L.trucks[1].salv=100
L.trucks[2].state='toDep';L.trucks[2].cargo={ammo=0,shirts=0,rifle=1,medical=1};L.trucks[2].dest=L.base
L.base.medical=3
local saved=L.snapshot()
assert(L.validateSave(saved))
-- Memento: invalid saved data and unavailable world must preserve live state.
local oldBase,oldJob=L.base,L.job
saved.bmat=-1
assert(not L.restore(saved) and L.base==oldBase and L.job==oldJob)
saved.bmat=200
local validCargo=saved.trucks[2].cargo
saved.trucks[2].cargo={rifle=-1}
assert(not L.restore(saved) and L.base==oldBase and L.job==oldJob)
saved.trucks[2].cargo=validCargo
saved.version=99
assert(not L.restore(saved) and L.base==oldBase)
saved.version=2
L.ready=function() return nil end
assert(not L.restore(saved) and L.base==oldBase and L.job==oldJob)
L.ready=function() return {} end
L.start=function() init();return true end
assert(L.restore(saved))
assert(L.bmat==200 and L.job.left==4 and L.base.medical==3)
assert(L.trucks[1].salv==100 and L.trucks[2].cargo.rifle==1)
L.truckStep(L.trucks[2],1,clock)
assert(L.base.rifle==20 and L.base.medical==53 and not L.trucks[2].cargo)
L.factoryStep(4)
assert(L.fac.rifle==1 and not L.job and L.bmat==200)
-- save's tables are not live aliases; restore replacement does not append cargo.
assert(saved.trucks[2].cargo.rifle==1)
assert(L.restore(saved))
assert(L.base.rifle==0 and L.trucks[2].cargo.rifle==1)
-- Save com destino perdido preserva carga no caminhão até retorno físico.
saved.trucks[2].dest=1
P[1].owner=C.ENEMY_TEAM
L.start=function() local owner=P[1].owner;init();P[1].owner=owner;return true end
assert(L.restore(saved))
local returning=L.trucks[2]
assert(returning.state=='returnCargo' and returning.cargo.rifle==1 and L.fac.rifle==0)
L.drive=function() return false end
L.truckStep(returning,1,clock)
assert(returning.cargo.rifle==1 and L.fac.rifle==0)
local backSave=L.snapshot()
assert(backSave.trucks[2].state=='returnCargo' and backSave.trucks[2].dest==-1)
assert(L.validateSave(backSave) and L.restore(backSave))
assert(L.trucks[2].state=='returnCargo' and L.trucks[2].cargo.medical==1 and L.fac.medical==0)
L.drive=function() return true end
L.truckStep(L.trucks[2],1,clock)
assert(L.fac.rifle==1 and L.fac.medical==1 and not L.trucks[2].cargo)
L.drive=function() return false end
L.truckStep(L.trucks[2],1,clock)
assert(L.fac.rifle==1 and L.fac.medical==1)
local legacy={bmat=40,fa=1,fs=1,ba=6,bs=20,pts={}}
assert(L.restore(legacy) and L.fac.rifle==0 and L.base.medical==0)
''')
print('PASS: complete main.lua candidate executed in memory; production/trucks/recruit/medic/save/memento')
