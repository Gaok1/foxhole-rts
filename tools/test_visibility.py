"""Testa funções reais; mocks não provam LOS/renderização Unreal."""
from pathlib import Path
from lupa import LuaRuntime

src = (Path(__file__).resolve().parents[1] / "mod/FoxholeRTS/Scripts/main.lua").read_text(encoding="utf-8")
lua = LuaRuntime()
lua.execute('''
rts={focus={X=100,Y=200,Z=300},home={X=900,Y=900,Z=0}}
S={eye=true}; CFG={EYE_EVERY=.2}
realTime=0; gameTime=0; floor=700; calls=0
pawn={IsValid=function() return true end,
 K2_SetActorLocation=function(_,p) calls=calls+1; last=p end}
function valid(p) return p and p:IsValid() end
function playerPawn() return pawn end
function world() return {} end
function now() return gameTime end
function gs() return {GetRealTimeSeconds=function() return realTime end} end
function groundZ(x,y) assert(x==rts.focus.X and y==rts.focus.Y); return floor end
vsync=0; reads=0; writes={}
function ksl() return {
 GetConsoleVariableIntValue=function(_,n) assert(n=='r.VSync'); reads=reads+1; return vsync end,
 ExecuteConsoleCommand=function(_,w,s,pc) writes[#writes+1]=s; vsync=tonumber(s:match('r.VSync (%d+)')) end}
end
''')
lua.execute(src[src.index("function rts.syncVideo("):src.index("function rts.gfx(")])
lua.execute(src[src.index("function rts.eyeTick()"):src.index("local function step(name, f)")])
lua.execute('''
rts.eyeTick(); assert(calls==1 and last.X==100 and last.Y==200 and last.Z==710)
assert(rts.home.X==900, 'base não segue o olho')
rts.focus={X=500,Y=600,Z=0}; realTime=.1; rts.eyeTick(); assert(calls==1)
realTime=.21; rts.eyeTick(); assert(calls==2 and last.X==500, 'pausa não congela LOS')
floor=nil; realTime=1; rts.eyeTick(); assert(calls==2, 'sem chão não teleporta')
floor=700; rts.focus.X=0/0; realTime=2; rts.eyeTick(); assert(calls==2)
rts.focus.X=500; pawn=nil; realTime=3; rts.eyeTick(); assert(calls==2)
S.eye=false; realTime=4; rts.eyeTick(); assert(calls==2)
for _,initial in ipairs({0,1}) do
 vsync=initial; reads=0; writes={}; rts.oldVSync=nil
 rts.syncVideo(nil,true); assert(vsync==1 and reads==1 and rts.oldVSync==initial)
 rts.syncVideo(nil,true); assert(reads==1 and rts.oldVSync==initial, 'reentrada preserva original')
 rts.syncVideo(nil,false); assert(vsync==initial and rts.oldVSync==nil)
 local n=#writes; rts.syncVideo(nil,false); assert(#writes==n, 'saída repetida não altera configuração')
end
''')
print("PASS: olho no foco/chão, pausa, throttle, invalidade e VSync/restauração idempotente")
lua.execute('''
S.eye=true; rts.home={X=900,Y=1000,Z=0}; rts.base=function() return rts.home end
pawn={IsValid=function() return true end, K2_GetActorLocation=function() return {X=5000,Y=5000,Z=0} end}
squad={}; CFG.SQUAD_SIZE=1; CFG.SQUAD_MAX=12; CFG.FRIENDLY_TEAM=1
function isLocalAuthority() return true end
function ensureCommander() return pawn end
function groundZ() return 0 end
function slotFor() return {X=0,Y=0} end
function roleFor() return 'rifle' end
rts.combatCount=function() return #squad end
function spawnSoldier(x,y,z) spawned={X=x,Y=y,Z=z}; return {sel=true} end
function syncMarkers() end
function notify() end
function composition() return '' end
''')
lua.globals().spawnSquad = lua.execute(src[src.index("local function spawnSquad("):src.index("local function cursorPoint()")] + "return spawnSquad")
lua.execute('''
assert(spawnSquad(1)==1 and spawned.X==1200 and spawned.Y==1300, 'nova partida usa base, não foco do olho')
squad={}; spawnSquad(1,nil,{X=2000,Y=3000,Z=0}); assert(spawned.X==2000 and spawned.Y==3000, 'spawn explícito preservado')
S.eye=false; squad={}; spawnSquad(1); assert(spawned.X==5300 and spawned.Y==5300, 'modo nativo usa comandante')
''')
print("PASS: spawn inicial independente do olho, spawn explícito e modo nativo preservados")
