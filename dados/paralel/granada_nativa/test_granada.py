"""Mocks do candidato real; nao prova engine/trajectory/friendlyfire/lifetime nativo."""
from pathlib import Path
from lupa import LuaRuntime

HERE = Path(__file__).resolve().parent
source = (HERE / 'main_candidato.lua').read_text(encoding='utf-8')
block = source[source.index('function rts.grenadeNumber'):source.index('local function mortarTick()')]
assert 'st.grenade' not in source and 'CFG.GRENADE.arc' not in source
assert 'meshActor' not in block and 'ApplyDamage' not in block and 'logi.blast' not in block

def run(failure=None):
    lua = LuaRuntime()
    lua.globals().failure = failure
    lua.execute('''
      rts, mortar, CFG = {}, {grenades={}}, {GRENADE={range=1800,cooldown=18}}
      clock, acquire, release, tracked, destroyed, finishCalls = 0,0,0,0,0,0
      valid=function(x) return x~=nil and x~=false end
      isLocalAuthority=function() return failure~='authority' end
      now=function() return 10 end
      alive=function(m) return m.pawn.Health>0 end
      loc=function(m) return m.at end
      flatDist=function(a,b) return math.sqrt((a.X-b.X)^2+(a.Y-b.Y)^2) end
      playCue=function() end; logOnce=function() end
      rts.nativeAcquire=function() acquire=acquire+1;return failure~='acquire' end
      rts.nativeRelease=function() release=release+1 end
      rts.nativeTrack=function(a) assert(a==actor); if failure=='track' then return false end; tracked=tracked+1;return true end
      local row={GrenadeFuseTimer=4,MinTossSpeed=390,MaxTossSpeed=1100,GrenadeRangeLimit=2000}
      if failure=='data' then row.GrenadeFuseTimer=nil end
      LoadAsset=function(path)
        if path:find('DynamicData') then return {ForEachRow=function(_,f) f('GrenadeW',row) end} end
        return failure~='class' and {} or nil
      end
      StaticFindObject=function() return {GetCDO=function() return {MakeTransform=function(_,p,r,s) return {Translation=p,Rotation=r,Scale3D=s} end} end} end
      world=function() return {} end
      actor={Health=1,FuseTimer=20,MovementComp={GetGravityZ=function() return failure=='gravity' and 0 or -980 end},
             K2_DestroyActor=function() destroyed=destroyed+1 end}
      if failure=='movement' then actor.MovementComp=nil end
      local engine={BeginDeferredActorSpawnFromClass=function() return failure~='spawn' and actor or nil end,
        SuggestProjectileVelocity_CustomArc=function(_,_,v)
          if failure=='solver' then return false end
          v.X= failure=='speed' and 2000 or failure=='nan' and 0/0 or 818; v.Y=0;v.Z=0;return true
        end,
        FinishSpawningActor=function(_,a)
          finishCalls=finishCalls+1; assert(a.FuseTimer==4 and a.MovementComp.Velocity.X==818)
          if failure=='finish' then return nil end
          if failure=='error' then error('falha engine') end
          return a
        end}
      gs=function() return engine end
      shooter={pawn={Health=100},at={X=0,Y=0,Z=90},team=1}
      target={pawn={Health=100},at={X=failure=='range' and 3000 or 750,Y=0,Z=90}}
      if failure=='position' then shooter.at.X=0/0 end
      if failure=='cooldown' then shooter.nextGrenade=11 end
    ''')
    lua.execute(block)
    result = lua.eval('throwGrenade(shooter,target)')
    return lua.globals(), result

state, result = run()
assert result and state.tracked==1 and state.release==0 and state.destroyed==0
assert state.shooter.nextGrenade==28 and state.mortar.grenades[1]==1
for failure in ('authority','cooldown','data','range','position','class','acquire','spawn','movement','gravity','solver','speed','nan','finish','error','track'):
    state, result = run(failure)
    assert not result, failure
    assert state.shooter.nextGrenade in (None,11) and state.mortar.grenades[1] is None, failure
    assert state.tracked==0, failure
    if failure in ('spawn','movement','gravity','solver','speed','nan','finish','error','track'):
        assert state.release==1, failure
    if failure in ('movement','gravity','solver','speed','nan','finish','error','track'):
        assert state.destroyed==1, failure
lua=LuaRuntime()
assert lua.eval('load')(source) is not None
print('PASS: 17 cenarios de granada candidata, lease/falhas/cooldown; sintaxe main candidata')
print('NAO prova Unreal, owner/equipe, trajetoria, soldierdeath ou estabilidade')
