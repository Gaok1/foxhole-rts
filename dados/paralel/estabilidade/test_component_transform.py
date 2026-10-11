"""Comparacao Lua dos dois caminhos; quaternion nativo e coberto pelo oracle ao vivo."""
from pathlib import Path
from lupa import LuaRuntime
base = Path(__file__).resolve().parent

def run(code):
    lua = LuaRuntime()
    lua.execute("""
rts={}; CFG={CAM_PITCH=-60,OUTLINE={back=50,pixels=500,copies=4}}
function valid(x) return x and x.IsValid() end
function rts.clearOutline(m) m.outline=nil end
calls, converts, reads = 0, 0, 0
local function obj(t) t.IsValid=function() return true end; return t end
StaticFindObject=function() return obj({MakeTransform=function(_,p,r,s)
converts=converts+1; return {Rotation={X=r.Pitch,Y=r.Yaw,Z=r.Roll,W=1}} end}) end
camera={X=-170,Y=30,Z=450}; rts.cam=obj({K2_GetActorLocation=function() return camera end})
m={pawn=obj({}),outline={},outlineSources={}}
for part=1,2 do
local source=obj({K2_GetComponentLocation=function() reads=reads+1;return {X=part*15,Y=-40,Z=30} end,
K2_GetComponentRotation=function() reads=reads+1;return {Pitch=-60,Yaw=77,Roll=13} end,
K2_GetComponentScale=function() reads=reads+1;return {X=1.1,Y=0.9,Z=1.3} end,
K2_GetComponentToWorld=function() reads=reads+1; return {Translation={X=part*15,Y=-40,Z=30},
Rotation={X=-60,Y=77,Z=13,W=1},Scale3D={X=1.1,Y=0.9,Z=1.3}} end})
for copy=1,4 do
local a=obj({K2_SetActorLocation=function(self,p) calls=calls+1;self.pos=p end,
K2_SetActorRotation=function(self,r) calls=calls+1;self.rot=r end,
SetActorScale3D=function(self,s) calls=calls+1;self.scale=s end,
K2_SetActorTransform=function(self,t,sweep,hit,teleport)
assert(sweep==false and teleport==true); calls=calls+1
self.pos={X=t.Translation.X,Y=t.Translation.Y,Z=t.Translation.Z}
self.scale=t.Scale3D;self.rot={Pitch=t.Rotation.X,Yaw=t.Rotation.Y,Roll=t.Rotation.Z}
end})
m.outline[#m.outline+1]=a;m.outlineSources[#m.outlineSources+1]=source
end end
""")
    lua.execute(code)
    states=[]
    for step in range(3):
        lua.execute('rts.updateOutline(m)')
        states.append([[lua.eval(f'm.outline[{i}].{group}.{field}')
                       for group, fields in [('pos','XYZ'),('rot',['Pitch','Yaw','Roll']),('scale','XYZ')]
                       for field in fields] for i in range(1,9)])
        lua.execute('camera.X=camera.X+100; camera.Z=camera.Z+30')
    return states, lua.eval('calls'), lua.eval('converts'), lua.eval('reads')

before=(base/'component_transform.before.lua').read_text(encoding='utf-8')
after=(base/'component_transform.after.lua').read_text(encoding='utf-8')
source=(base.parents[2]/'mod/FoxholeRTS/Scripts/main.lua').read_text(encoding='utf-8')
assert source.count(after)==1, 'Fonte mudou: revisar regressao'
start=source.index('function rts.updateOutline(m)')
actual=source[start:source.index('\nfunction rts.setOutline',start)]
assert actual==after
old, oldcalls, oldconversions, oldreads=run(before)
new, newcalls, conversions, reads=run(actual)
assert old==new, 'Projecao/rotacao/escala divergiram'
assert (oldcalls,newcalls,oldconversions,conversions,oldreads,reads)==(24,24,6,0,18,6) if actual==after else (oldcalls,newcalls,oldconversions,conversions,oldreads,reads)==(24,24,6,6,18,18)
print(f'OK: fonte real8copias/2pecas/3cameras identica; reads+conversoes baseline24->atual{reads+conversions}; setters24')
