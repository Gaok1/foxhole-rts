"""Snapshot real deve observar morte antes de salvar carga/créditos; engine mockado."""
from pathlib import Path
from lupa import LuaRuntime

source = (Path(__file__).resolve().parents[1] / 'mod/FoxholeRTS/Scripts/main.lua').read_text(encoding='utf-8')
lua = LuaRuntime()
lua.execute('''
logi,sv,rts,combat,S,economy,ai={},{},{},{},{},{},{}
CFG={ENEMY_TEAM=0,ECONVOY={bounty=25},LOGI={rebuild=30,
 products={'ammo','shirts'},recipes={ammo={units=2},shirts={units=5}}},ECHAIN={kinds={'ammo','shirts'}}}
now=function() return 100 end
valid=function(a) return a and not a.invalid end
logOnce=function() end
earn=function(n) economy.manpower=economy.manpower+n end
rts.alert=function() end
logi.eEvent=function() end
logi.colSnapshot=function() return nil end
sv.map=function() return 'CallumsCapeHex' end
sv.worldPath=sv.map
sv.infraSnapshot=function() return {} end
sv.enemySnapshot=function() return {} end
logi.fwdSnapshot=function() return {} end
points,squad,enemies,structures={},{},{},{}
S.trenches,S.tents,S.wires={},{},{}
function fixture(hp)
 logi.on=false
 economy.manpower=100;combat.convoysCut=0
 logi.en={salvage=0,bmat=40,tripT=0,ready=0,rebuild={},seq=1,delivered=0,
 fac={ammo=0,shirts=0},front={ammo=0,shirts=0},ghost={ammo=0,shirts=0},
 led={bmat0=40,salv=0,refined=0,spent=0,init={ammo=6,shirts=5},
 made={ammo=0,shirts=0},used={ammo=0,shirts=0},lost={ammo=0,shirts=0}}}
 actor={Health=hp,K2_DestroyActor=function() error('nao destruir casco') end,
 SetActorHiddenInGame=function() error('nao esconder casco') end}
 tr={state='toDep',hp=900,team=0,cargo={ammo=3,shirts=1},pawn=actor}
 logi.foes={tr}
end
''')
for start, end in [
    ('function logi.syncHealth', '-- Morteiro proprio'),
    ('function logi.eUnits', 'function logi.eNeed'),
    ('function logi.eLose', '-- Caminhao de volta'),
    ('function logi.eSnapshot', '-- Validacao completa antes de substituir'),
    ('function logi.snapshot', '-- Pré-validação completa antes de start/reset'),
    ('function sv.collect', '-- Persistencia v2'),
]:
    begin = source.index(start)
    lua.execute(source[begin:source.index(end, begin)])
lua.execute('''
fixture(0)
local save=sv.collect()
assert(save.elogi.pending.ammo==0 and save.elogi.pending.shirts==0,
 'save ressuscitou carga de ator com HP nativo zero')
assert(save.elogi.ready==0 and #save.elogi.rebuild==1 and save.elogi.rebuild[1]==30)
assert(save.elogi.led.lost.ammo==6 and save.elogi.led.lost.shirts==5)
assert(save.mp==125 and combat.convoysCut==1 and tr.state=='dead' and tr.pawn==nil)
local again=sv.collect()
assert(again.mp==125 and #again.elogi.rebuild==1 and combat.convoysCut==1)
assert(actor.Health==0 and save.elogi.led.lost.ammo==6)
for _,flag in ipairs({'invalid','bActorIsBeingDestroyed'}) do
 fixture(900);actor[flag]=true
 save=sv.collect()
 assert(save.mp==100 and save.elogi.ready==0 and #save.elogi.rebuild==1)
 assert(save.elogi.pending.ammo==0 and save.elogi.led.lost.ammo==6)
end
fixture(780)
save=sv.collect()
assert(save.mp==100 and save.elogi.ready==1 and #save.elogi.rebuild==0)
assert(save.elogi.pending.ammo==3 and save.elogi.pending.shirts==1 and tr.hp==780)
assert(save.elogi.led.lost.ammo==0 and tr.pawn==actor and actor.Health==780)
tr.cargo.ammo=0;logi.en.led.lost.ammo=99
assert(save.elogi.pending.ammo==3 and save.elogi.led.lost.ammo==0)
fixture(900);logi.en=nil
assert(sv.collect().elogi==nil)
for _,hp in ipairs({0/0,math.huge,-math.huge,'schema'}) do
 fixture(hp)
 local ok=pcall(sv.collect)
 assert(not ok,'HP desconhecido nao pode salvar carga/HP antigos')
 assert(tr.state=='toDep' and tr.cargo.ammo==3 and logi.en.led.lost.ammo==0)
 assert(#logi.en.rebuild==0 and economy.manpower==100 and not tr.moving)
 fixture(hp);logi.foes={};logi.on=true;logi.trucks={tr}
 logi.base={};logi.fac={};logi.salvage=0;logi.bmat=40
 ok=pcall(sv.collect)
 assert(not ok,'snapshot amigo tambem deve recusar HP desconhecido')
 assert(tr.state=='toDep' and tr.cargo.ammo==3)
end
''')
begin = source.index('function sv.save()')
lua.execute(source[begin:source.index('function sv.sameBuilt', begin)])
lua.execute('''
combat.auto=true;combat.won=false;combat.startT=1;squad={{}}
log=function(s) lastLog=s end
sv.validate=function() error('nao validar snapshot incompleto') end
sv.writeAtomic=function() error('nao tocar arquivo anterior') end
fixture('schema')
assert(sv.save()==false and lastLog:find('preservado'))
''')
print('PASS: snapshot observa HP/perda nativa, sem carga ressuscitada; créditos coerentes/perda única/copias')
