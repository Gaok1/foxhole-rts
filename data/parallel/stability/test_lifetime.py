"""Teste das decisoes Lua; nao certifica lifetime nativo nem causa dos crashes.
$env:PYTHONPATH='D:/tools/pylibs'; python data/parallel/stability/test_lifetime.py
"""
from pathlib import Path
from lupa import LuaRuntime
root = Path(__file__).resolve().parents[3]
base = Path(__file__).resolve().parent
source = (root / 'mod/FoxholeRTS/Scripts/main.lua').read_text(encoding='utf-8')
before = (base / 'update_outline.before.lua').read_text(encoding='utf-8')
after = (base / 'update_outline.after.lua').read_text(encoding='utf-8')
# Fonte integrada e baseline revertido apenas em memoria: detectar drift dos dois blocos.
old_blocks, new_blocks = before.split('\n\n'), after.split('\n\n')
assert len(old_blocks) == len(new_blocks) == 2
baseline = source
for old, new in zip(old_blocks, new_blocks):
    assert source.count(new) == 1, 'Fonte integrada mudou: revisar regressao'
    baseline = baseline.replace(new, old, 1)
for old in old_blocks:
    assert baseline.count(old) == 1, 'Baseline ambiguo: revisar regressao'

def check(code, case):
    lua = LuaRuntime()
    lua.execute("rts={}; CFG={CAM_PITCH=45,OUTLINE={back=50,pixels=500,copies=4}}; function valid(x) return x and x.IsValid() end; calls=0; cleared=false")
    start = code.index('function rts.outlineDepth(m, on)')
    end = code.index('function rts.setOutline(m, on)', start)
    lua.execute(code[start:end])
    lua.execute("""
local function object(t) t.IsValid=function() return true end; return t end
rts.cam=object({K2_GetActorLocation=function() return {X=0,Y=0,Z=0} end})
StaticFindObject=function() return object({MakeTransform=function() return {Rotation={X=0,Y=0,Z=0,W=1}} end}) end
local src=object({K2_GetComponentLocation=function() calls=calls+1; return {X=10,Y=10,Z=10} end,
K2_GetComponentRotation=function() return {} end,K2_GetComponentScale=function() return {X=1,Y=1,Z=1} end,
K2_GetComponentToWorld=function() calls=calls+1; return {Translation={X=10,Y=10,Z=10},Rotation={X=0,Y=0,Z=0,W=1},Scale3D={X=1,Y=1,Z=1}} end})
local clone=object({K2_SetActorLocation=function() calls=calls+1 end,K2_SetActorRotation=function() end,SetActorScale3D=function() end,K2_SetActorTransform=function() calls=calls+1 end})
src.SetRenderCustomDepth=function() assert(not m.pawn.bActorIsBeingDestroyed, "depth acessou pawn em destruicao") end
m={pawn=object({K2_GetComponentsByClass=function() calls=calls+100; return {} end}),outline={clone},outlineSources={src},outlineParts={src}}
clone.K2_DestroyActor=function() end
""")
    lua.execute(case)
    lua.execute('rts.updateOutline(m)')
    if lua.eval('m.outline == nil'):
        lua.execute('cleared=true')
    return lua.eval('calls'), lua.eval('cleared')

cases = ['m.outline[1].bActorIsBeingDestroyed=true', 'm.pawn.bActorIsBeingDestroyed=true',
         'm.outlineSources[1].IsValid=function() return false end']
for case in cases:
    assert check(baseline, case)[0] > 0, 'Baseline deixou de reproduzir: revisar teste'
    assert check(source, case) == (0, True), case
assert check(source, 'rts.cam.bActorIsBeingDestroyed=true') == (0, False)
assert check(baseline, 'rts.cam.bActorIsBeingDestroyed=true') == (2, False)
assert check(source, 'm.outlineSources=nil') == (0, True)
try:
    check(baseline, 'm.outlineSources=nil')
except Exception as error:
    assert 'outlineSources' in str(error), str(error)
else:
    raise AssertionError('Baseline deveria falhar com fonte ausente')
assert check(source, '') == (2, False)
print('OK: fonte integrada real cobre clone/pawn destruindo, fonte invalida/ausente e camera destruindo; baseline reproduz regressao; vivo preservado')
