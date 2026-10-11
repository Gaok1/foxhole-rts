"""Executa observador real de HP; mocks nao certificam lifecycle Unreal."""
from pathlib import Path
from lupa import LuaRuntime

source = (Path(__file__).resolve().parents[1] / 'mod/FoxholeRTS/Scripts/main.lua').read_text(encoding='utf-8')
block = source[source.index('function logi.syncHealth'):source.index('-- IA_LOGISTICA')]
lua = LuaRuntime()
lua.execute('''
logi, combat = {}, {}
CFG={ENEMY_TEAM=2,ECONVOY={bounty=25},LOGI={rebuild=30}}
losses, credits, alerts = 0,0,0
valid=function(a) return a and not a.invalid end
logOnce=function() end
earn=function(n) credits=credits+n end
rts={alert=function() alerts=alerts+1 end}
logi.eLose=function(tr) losses=losses+1;tr.cargo=nil;tr.lostDone=true;return 'carga perdida' end
function truck(hp,team)
  return {state='toDep',team=team,hp=900,moving=true,cargo={ammo=3},salv=40,dest={},route={},
    pawn={Health=hp,K2_DestroyActor=function() error('nao destruir casco') end,
    SetActorHiddenInGame=function() error('nao esconder casco') end,
    OnRep_Health=function() error('nao antecipar morte') end}}
end
''')
lua.execute(block)
lua.execute('''
tr=truck(780,1); actor=tr.pawn
assert(logi.syncHealth(tr,10) and tr.hp==780 and actor.Health==780 and tr.cargo.ammo==3)
actor.Health=0
assert(not logi.syncHealth(tr,11) and tr.state=='dead' and tr.rebuildT==41)
assert(tr.pawn==nil and not tr.moving and tr.route==nil and tr.dest==nil and tr.salv==nil and tr.cargo==nil)
assert(logi.lost==1 and credits==0 and actor.Health==0)
assert(not logi.syncHealth(tr,99) and logi.lost==1 and tr.rebuildT==41)
tr=truck(0,2)
assert(not logi.syncHealth(tr,12) and losses==1 and credits==25 and combat.convoysCut==1)
assert(not logi.syncHealth(tr,13) and losses==1 and credits==25)
tr=truck(900,2);tr.pawn.bActorIsBeingDestroyed=true
assert(not logi.syncHealth(tr,14) and losses==2 and credits==25)
tr=truck(900,1);tr.pawn.invalid=true
assert(not logi.syncHealth(tr,15) and logi.lost==2)
tr=truck(900,1);tr.pawn=nil
assert(not logi.syncHealth(tr,16) and logi.lost==3)
for _,hp in ipairs({0/0,math.huge,-math.huge,'schema'}) do
  tr=truck(hp,1)
  assert(not logi.syncHealth(tr,17) and tr.state=='toDep' and tr.cargo.ammo==3 and logi.lost==3)
end
tr=truck(-5,1)
assert(not logi.syncHealth(tr,18) and tr.hp==0 and logi.lost==4)
''')
assert 'logi.hit' not in source and 'CFG.LOGI.dps' not in source
drive = source[source.index('function logi.drive'):source.index('-- Deposito para')]
assert drive.index('logi.syncHealth') < drive.index('flatDist')
step = source[source.index('function logi.truckStep'):source.index('-- Alerta de proximidade')]
assert step.index('logi.syncHealth') < step.index('logi.drive')
assert 'ApplyDamage' not in block and 'emit' not in block
print('PASS: HP real, perda unica, TTL preservado, invalidos/schema, sem DPS de veiculos; gates antes de transporte')
