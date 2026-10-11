"""Contratacao automatica sob ameaca: funcoes reais, atores/navegacao mockados."""
from pathlib import Path
from lupa import LuaRuntime

source = (Path(__file__).resolve().parents[1] / 'mod/FoxholeRTS/Scripts/main.lua').read_text(encoding='utf-8')
lua = LuaRuntime()
lua.execute('''
logi,CFG={},{COLETA={workers=3,spawnEvery=3,danger=3500,fireQuiet=8},FRIENDLY_TEAM=1}
alive=function(m) return m.pawn and m.pawn.Health>0 end
loc=function(m) return m.pos end
flatDist=function(a,b) return math.sqrt((a.X-b.X)^2+(a.Y-b.Y)^2) end
suppression=function(m) return m.supp or 0 end
isLocalAuthority=function() return authority end
groundZ=function() return 0 end
slotFor=function() return {} end
syncMarkers=function() end
log=function() end
notify=function() notices=notices+1 end
spawnSoldier=function()
 spawns=spawns+1
 if spawnFails then return nil end
 return {role='worker',pawn={Health=100,K2_DestroyActor=function() destroyed=destroyed+1 end}}
end
anim={untrack=function() untracked=untracked+1 end}
releaseController=function() end
function fixture()
 authority=true;enemies={};squad={};spawns=0;notices=0;destroyed=0;untracked=0;commits=0
 spawnFails=false;commitFails=false
 depot={shirts=10};exit={X=250,Y=0,Z=0}
 logi.col={units={},made=0}
 logi.spawnSite=function() return {at=exit,dep=depot,name='base'} end
 logi.spawnCommit=function()
  commits=commits+1
  if commitFails then return false end
  depot.shirts=depot.shirts-1;return true
 end
end
function enemy(x,hp,destroying)
 return {pos={X=x,Y=0,Z=0},pawn={Health=hp or 100,bActorIsBeingDestroyed=destroying}}
end
''')
for start, end in [
    ('function logi.colThreat', 'function logi.colFree'),
    ('function logi.colMaintain', '-- Rota (A*'),
]:
    lua.execute(source[source.index(start):source.index(end, source.index(start))])
lua.execute('''
fixture();enemies={enemy(3750)} -- fronteira: 35m da saida, nao do centro da base
assert(logi.colThreat(exit))
logi.colMaintain(100)
assert(spawns==0 and commits==0 and depot.shirts==10 and #squad==0 and logi.col.made==0)
assert(logi.col.spawnBlocked and notices==1)
for t=101,130 do logi.colMaintain(t) end
assert(spawns==0 and depot.shirts==10 and notices==2) -- aviso/checagem limitados, sem queimar camisas
enemies[1].pos.X=3751;logi.colMaintain(133)
assert(spawns==1 and commits==1 and depot.shirts==9 and #squad==1 and not logi.col.spawnBlocked)
assert(logi.col.made==1 and not squad[1].sel)
logi.colMaintain(134);assert(spawns==1) -- intervalo existente preservado

for _,case in ipairs({'morto','destruindo','distante'}) do
 fixture()
 enemies={enemy(case=='distante' and 5000 or 250,case=='morto' and 0 or 100,case=='destruindo')}
 logi.colMaintain(100);assert(spawns==1 and depot.shirts==9,case)
end
fixture();authority=false;logi.colMaintain(100);assert(spawns==0 and depot.shirts==10)
fixture();spawnFails=true;logi.colMaintain(100);assert(spawns==1 and commits==0 and depot.shirts==10)
fixture();commitFails=true;logi.colMaintain(100)
assert(spawns==1 and commits==1 and depot.shirts==10 and #squad==0 and destroyed==1 and untracked==1)
fixture();for i=1,3 do squad[i]={role='worker',pawn={Health=100}} end
logi.colMaintain(100);assert(spawns==0 and depot.shirts==10)
fixture();logi.spawnSite=function() return nil,'sem camisas' end
logi.colMaintain(100);assert(spawns==0 and logi.col.spawnBlocked=='sem camisas')

fixture();local m={pos=exit,pawn={Health=100}}
assert(logi.colCalm(m,100));enemies={enemy(250)};assert(not logi.colCalm(m,100))
enemies={};m.supp=.05;assert(not logi.colCalm(m,100))
m.supp=0;m.nextShot=95;assert(not logi.colCalm(m,100));assert(logi.colCalm(m,103))
''')
print('PASS: ameaca na saida impede gasto/spawn, retomada normal, mortos/destruindo, autoridade, rollback e limite')
