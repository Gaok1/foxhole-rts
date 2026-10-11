"""Regressao do recuo automatico real; nao certifica navegacao/combate Unreal."""
from pathlib import Path
from lupa import LuaRuntime

source = (Path(__file__).resolve().parents[1] / 'mod/FoxholeRTS/Scripts/main.lua').read_text(encoding='utf-8')
lua = LuaRuntime()
lua.execute('''
logi,rts,combat,S={},{},{},{tents={}}
squad,enemies,points={},{},{{X=0,Y=0,Z=0,owner=1,name='A'}}
CFG={FRIENDLY_TEAM=1,POINT_RADIUS=500,TENT={radius=500},
 MEDEVAC={below=.3,done=.8,quiet=15,every=1,giveUp=45},
 COLETA={workers=3,delay=0,scan=2,fieldR=1000,refR=1500,rate=1,cap=40,pause=60,leg=180},
 LOGI={ratio=2,truckCost=100}}
clock=100
now=function() return clock end
loc=function(m) return m.pos end
flatDist=function(a,b) return math.sqrt((a.X-b.X)^2+(a.Y-b.Y)^2) end
routeTo=function(m,g) m.target=g; m.pathJob={};routes=(routes or 0)+1 end
weapon=function() return {name='trabalhador'} end
notify=function() end
log=function(s) lastLog=s end
halt=function(m) m.halted=true end
alive=function(m) return m.pawn.Health>0 end
logi.colLive=function(m) return alive(m) end
logi.colDown=function() return true end
logi.colMaintain=function() error('nao repor trabalhador vivo') end
logi.colCalm=function() return true end
logi.colRecover=function() end
logi.colGo=function(u,site,t)
 routeTo(u.m,site);u.goal=u.m.target;u.retryT=t+2
 if u.routeState~=u.state then u.legT,u.routeState=t,u.state end
end
function fixture(state)
 clock=100;routes=0;logi.bmat=40;logi.salvage=0
 logi.field={X=10000,Y=0,Z=0};logi.refinery={X=20000,Y=0,Z=0}
 m={pawn={Health=20,MaxHealth=100},role='worker',pos={X=10000,Y=0,Z=90}}
 u={m=m,state=state or 'gather',carry=35.8,legT=90,retryT=0,routeState=state or 'gather'}
 m.col=u;squad={m}
 logi.col={units={u},active=false,since=1000,scanT=1000,gathered=35.8,delivered=0,lost=0,why={},trips=0}
end
''')
for start, end in [
    ('function rts.medevacStep', '-- Aliados:'),
    ('function logi.colRelease', '-- Onde nasce'),
    ('function logi.colUnit', '-- Uma linha para o painel'),
    ('function logi.colAudit', '-- Reconstrucao transacional'),
]:
    lua.execute(source[source.index(start):source.index(end, source.index(start))])
lua.execute('''
fixture()
rts.medevacStep(m)
assert(m.medevac and m.retreat and routes==1)
local evacGoal=m.target
for i=1,70 do clock=100+i;logi.colStep(1,clock) end
assert(m.col==u and u.evacuating and u.carry==35.8 and logi.col.lost==0)
assert(m.target==evacGoal and routes==1 and logi.salvage==0 and logi.colAudit())
assert(u.legT==160) -- tempo de evacuacao nao vira timeout de caminhada
m.pawn.Health=90;rts.medevacStep(m)
assert(not m.medevac and not m.retreat)
logi.colStep(1,clock)
assert(not u.evacuating and u.state=='toField' and routes==2 and m.target==logi.field)
assert(u.carry==35.8 and logi.colAudit())

fixture('toRef');rts.medevacStep(m);logi.colStep(1,clock)
m.pawn.Health=90;rts.medevacStep(m);logi.colStep(1,clock)
assert(u.state=='toRef' and m.target==logi.refinery and u.carry==35.8)
m.pos=logi.refinery;logi.colStep(1,clock)
assert(logi.salvage==35.8 and logi.col.delivered==35.8 and u.carry==0 and logi.colAudit())
logi.colStep(1,clock);assert(logi.salvage==35.8) -- entrega unica, somente na refinaria

fixture();rts.medevacStep(m);logi.colStep(1,clock)
m.pawn.Health=0;logi.colStep(1,clock)
assert(not m.col and logi.col.lost==35.8 and logi.col.why['trabalhador morto']==35.8 and logi.colAudit())
logi.colStep(1,clock);assert(logi.col.lost==35.8)

for _,field in ipairs({'orderT','hold','focus','area','queue','retreat'}) do
 fixture();rts.medevacStep(m);logi.colStep(1,clock)
 if field=='retreat' then m.medevac=nil end -- Home explicito, nao medevac
 m[field]=true
 local goal=m.target
 logi.colStep(1,clock)
 assert(not m.col and logi.col.lost==35.8 and logi.col.why['ordem do jogador']==35.8)
 assert(m.target==goal and logi.colAudit()) -- ordem explicita intacta
end
''')
print('PASS: medevac real conserva carga/rota/timeout, retoma campo ou refinaria; morte e ordens perdem uma vez')
