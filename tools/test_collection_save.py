"""Persistência real da carga manual; mundo, spawn e navegação são mocks."""
from pathlib import Path
from lupa import LuaRuntime

source = (Path(__file__).resolve().parents[1] / 'mod/FoxholeRTS/Scripts/main.lua').read_text(encoding='utf-8')
lua = LuaRuntime()
lua.execute('''
logi,sv,S,combat,economy,ai={},{},{},{shots={},hits={}},{},{}
CFG={FRIENDLY_TEAM=1,ENEMY_TEAM=0,SAVE_EVERY=60,MANPOWER_START=100,POINT_MAX=10,
 AI={every=20},COLETA={workers=3,cap=40,scan=2},WEAPONS={worker={},rifle={}},
 DIFFICULTIES={{}},DEPLOY={sites={}}}
points,squad,enemies,structures={},{},{},{}
S.trenches,S.tents,S.wires={},{},{}
now=function() return 100 end
alive=function(m) return m.pawn.Health>0 end
logi.colLive=function(m) return alive(m) and not m.pawn.bActorIsBeingDestroyed end
logi.colGo=function(u,dest,t) u.goal=dest;u.legT=t;u.retryT=t+2;u.m.target=dest end
logi.snapshot=function() return {} end
logi.eSnapshot=function() return nil end
sv.map=function() return 'CallumsCapeHex' end
sv.worldPath=sv.map
world=function() return {GetFullName=function() return 'World /Game/Maps/CallumsCapeHex' end} end
sv.infraSnapshot=function() return nil end
sv.enemySnapshot=function() return nil end
logi.fwdSnapshot=function() return nil end
logi.validateSave=function() return true end
log=function() end
halt=function() end
loc=function(m) return m.pos end
groundZ=function() return 0 end
slotFor=function(i) return i end
setDifficulty=function() end
syncMarkers=function() end
clearSquad=function() squad={};enemies={} end
function spawnSoldier(x,y,z,slot,team,role)
 if role==failRole then return nil end
 return {role=role,pos={X=x,Y=y,Z=z},pawn={Health=100,OnRep_Health=function() end}}
end
function fixture(state)
 logi.on=true;logi.salvage=12;failRole=nil
 logi.field={X=10000,Y=0,Z=0};logi.refinery={X=20000,Y=0,Z=0}
 dead={role='rifle',pos={X=0,Y=0,Z=90},pawn={Health=0}}
 rifle=spawnSoldier(10,0,90,1,1,'rifle')
 worker=spawnSoldier(10000,0,90,2,1,'worker')
 squad={dead,rifle,worker}
 u={m=worker,state=state or 'toRef',carry=35.7774,orderT=worker.orderT}
 worker.col=u
 logi.col={units={u},gathered=50.9012,delivered=10.1234,lost=5.0004,trips=1,why={}}
end
''')
for start, end in [
    ('function logi.colReset', '-- Soldado ainda'),
    ('function logi.colRelease', '-- Onde nasce'),
    ('function logi.colAudit', 'function logi.spawnTruck'),
    ('function sv.ser', 'function sv.map'),
    ('local function unitData', '-- Persistencia v2'),
    ('CFG.PERSIST =', 'function sv.parseSave'),
    ('function sv.restore', '-- Por quadro: grava'),
]:
    begin = source.index(start)
    lua.execute(source[begin:source.index(end, begin)])
lua.execute('''
for _,state in ipairs({'toField','gather','toRef'}) do
 fixture(state)
 local d=sv.collect()
 assert(d.collection and #d.collection.units==1,'save omitiu a carga manual')
 assert(d.collection.units[1].index==2 and #d.squad==2)
 assert(d.collection.units[1].carry==35.7774 and logi.salvage==12)
 assert(sv.validate(d))
 local text='return '..sv.ser(d)
 local decoded=assert(sv.decode(text));assert(sv.validate(decoded))
 assert(sv.restore(decoded)==2)
 logi.colReset() -- logi.start/reset também ocorre entre recriar soldados e reatar coleta
 assert(logi.colRestore(decoded.collection))
 local restored=logi.col.units[1]
 assert(restored.m==squad[2] and restored.m.role=='worker' and restored.carry==35.777)
 assert(restored.state==(state=='gather' and 'toField' or state))
 assert(restored.goal==(state=='toRef' and logi.refinery or logi.field))
 assert(logi.salvage==12 and logi.colAudit() and logi.col.trips==1)
 local again=sv.collect();assert(again.collection.units[1].carry==35.777)
 decoded.collection.units[1].carry=0
 assert(restored.carry==35.777) -- copias, sem vinculo a tabela do save
end
fixture();worker.pawn.Health=0
local d=sv.collect()
assert(#d.collection.units==0 and d.collection.lost==40.7778 and logi.salvage==12)
fixture();worker.orderT=1
d=sv.collect();assert(#d.collection.units==0 and not worker.col)
fixture();d=sv.collect();failRole='worker'
sv.restore(d);logi.colReset();local old=logi.col
assert(not logi.colRestore(d.collection) and logi.col==old and #old.units==0)
assert(logi.salvage==12) -- falha nao realoca a carga ao soldado restante
fixture();d=sv.collect()
for _,mutate in ipairs({
 function(c) c.units[2]=c.units[1] end,
 function(c) c.units[1].index=1 end,
 function(c) c.units[1].index=99 end,
 function(c) c.units[1].carry=41 end,
 function(c) c.units[1].carry=-1 end,
 function(c) c.units[1].carry=0/0 end,
 function(c) c.units[1].state='entregou' end,
 function(c) c.units[1].unknown=1 end,
 function(c) c.gathered=99 end,
 function(c) c.v=2 end,
}) do
 local changed=assert(sv.decode('return '..sv.ser(d)))
 mutate(changed.collection)
 assert(not sv.validate(changed),'schema invalido aceito')
end
d.collection=nil;assert(sv.validate(d) and logi.colRestore(nil)) -- legado sem carga inventada
''')
print('PASS: coleta serializada/validada/reatada por slot salvo, carga e razão preservadas, sem crédito no load')
