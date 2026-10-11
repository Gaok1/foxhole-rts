from pathlib import Path
from lupa import LuaRuntime
base=Path(__file__).resolve().parent
source=(base.parents[2]/'mod/FoxholeRTS/Scripts/main.lua').read_text(encoding='utf-8')
before=(base/'anim_hook.before.lua').read_text(encoding='utf-8')
after=(base/'anim_hook.after.lua').read_text(encoding='utf-8')
assert source.count(after)==1,'Drift da fonte integrada: revisar hook'
start=source.index('function anim.track(m)')
end=source.index('\nfunction anim.untrack',start)
actual=source[start:end]
assert actual==after
baseline=source.replace(actual,before,1)
assert baseline.count(before)==1
def check(code):
    lua=LuaRuntime()
    lua.execute("""
anim={units={},onUpdate=function() end}; CFG={ANIM_ABP='ABP'}
function log() end
attempts=0
function RegisterHook(path,fn) attempts=attempts+1; assert(fn==anim.onUpdate); if attempts==1 then error('simulada') end end
local inst={IsValid=function() return true end,GetAddress=function() return 42 end}
m={pawn={Mesh={GetAnimInstance=function() return inst end}}}
""")
    lua.execute(code)
    lua.execute('anim.track(m)')
    assert lua.eval('anim.units[42]==m and m.animAddr==42')
    first=lua.eval('anim.hooked')
    lua.execute('anim.track(m);anim.track(m)')
    return first,lua.eval('attempts'),lua.eval('anim.hooked'),lua.eval('anim.units[42]==m')
assert check(baseline[start:baseline.index("\nfunction anim.untrack",start)])==(True,1,True,True)
assert check(after)==(False,2,True,True)
assert check(actual)==(False,2,True,True)
print('OK: falha inicial antes suprimia retry; fonte REAL tenta novamente1vez e nao duplica hook/cache')
