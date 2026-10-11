"""Regressao do telhado da base viva no preflight; nao prova fisica Unreal."""
from pathlib import Path
import re
from lupa import LuaRuntime

source = (Path(__file__).resolve().parents[1] / 'mod/FoxholeRTS/Scripts/main.lua').read_text(encoding='utf-8')
lua = LuaRuntime()
lua.execute('''
logi={fwd={}}
CFG={DEPLOY={maxHeight=100},PERSIST={tol=100},FWD={asset='base',minExits=2},NOCOL={}}
function valid(a) return a and a.alive end
function LoadAsset() return {alive=true} end
function world() return {} end
function flatDist(a,b) return math.sqrt((a.X-b.X)^2+(a.Y-b.Y)^2) end
function logi.fwdExits() return {{},{}} end
local landscape={alive=true}
function landscape:GetClass() return {GetFName=function() return {ToString=function() return 'Landscape' end} end} end
roof={alive=true,bActorIsBeingDestroyed=false}
local roofActor={alive=true}
function roofActor:GetClass() return {GetFName=function() return {ToString=function() return 'BPForwardBase1_C' end} end} end
trace={}
function ksl() return trace end
function trace:LineTraceSingle(w,a,b,channel,complex,ignore,draw,h)
 local skipped=false
 for _,v in ipairs(ignore) do if v==roof then skipped=true end end
 h.Actor={get=function() return skipped and landscape or roofActor end}
 h.ImpactPoint={Z=0}
 return true
end
saved={fwd={list={{x=0,y=0,z=0}}}}
''')
for name in ('parkingGround', 'fwdPreflight'):
    match = re.search(rf'^function logi\.{name}\([^\n]*\).*?^end$', source, re.M | re.S)
    assert match, name
    lua.execute(match.group())
lua.execute('''
-- Sem base correspondente, nao ignorar um predio que cobre o ponto salvo.
assert(not logi.fwdPreflight(saved))
logi.fwd={{X=0,Y=0,actor=roof,dead=false}}
assert(logi.fwdPreflight(saved))
-- Cache morto, ator em destruicao e base de outro local nao autorizam ignorar.
logi.fwd[1].dead=true; assert(not logi.fwdPreflight(saved))
logi.fwd[1].dead=false; roof.bActorIsBeingDestroyed=true; assert(not logi.fwdPreflight(saved))
roof.bActorIsBeingDestroyed=false; logi.fwd[1].X=100; assert(not logi.fwdPreflight(saved))
assert(not logi.parkingGround(0,0,{Z=0})) -- estacionamento normal permanece estrito
''')
print('PASS: preflight ignora apenas sua base viva; estacionamento permanece estrito')
