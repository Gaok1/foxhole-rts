"""Hipotese offline de mascara residual; nao comprova shader/flicker Unreal.
Nao altera main.lua. Executar com PYTHONPATH=D:/tools/pylibs.
"""
from pathlib import Path
from lupa import LuaRuntime

root = Path(__file__).resolve().parents[3]
source = (root / 'mod/FoxholeRTS/Scripts/main.lua').read_text(encoding='utf-8')
start = source.index('function rts.outlineDepth(m, on)')
end = source.index('function rts.clearOutline(m)', start)
before = source[start:end]
old = 'if on and c.CustomDepthStencilValue ~= 1 then c:SetCustomDepthStencilValue(1) end'
new = 'if c.CustomDepthStencilValue ~= (on and 1 or 0) then c:SetCustomDepthStencilValue(on and 1 or 0) end'
assert before.count(old) == 1
after = before.replace(old, new)

def run(code):
    lua = LuaRuntime()
    lua.execute('''
    rts={}
    function valid(x) return x and x.valid~=false end
    c={bRenderCustomDepth=true,CustomDepthStencilValue=1,writes=0}
    function c:SetRenderCustomDepth(value) self.bRenderCustomDepth=value end
    function c:SetCustomDepthStencilValue(value) self.CustomDepthStencilValue=value; self.writes=self.writes+1 end
    m={pawn={},outlineParts={c}}
    ''')
    lua.execute(code)
    lua.execute('rts.outlineDepth(m,false); c.bRenderCustomDepth=true')
    residual = lua.eval('c.CustomDepthStencilValue')
    lua.execute('''
    rts.outlineDepth(m,false)
    local writes=c.writes
    rts.outlineDepth(m,false); assert(c.writes==writes)
    rts.outlineDepth(m,true)
    assert(c.bRenderCustomDepth and c.CustomDepthStencilValue==1)
    m.pawn.bActorIsBeingDestroyed=true
    writes=c.writes; rts.outlineDepth(m,false); assert(c.writes==writes)
    ''')
    return residual

assert run(before) == 1, 'Baseline nao reproduz stencil residual'
assert run(after) == 0, 'Proposta nao limpa stencil residual'
print('PASS: baseline retém1; proposta limpa0/não duplica writes/reseleção1/guard destruição. Render nativo pendente.')
