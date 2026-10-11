from pathlib import Path
from lupa import LuaRuntime
base=Path(__file__).resolve().parent
before=(base/'depth.before.lua').read_text(encoding='utf-8')
after=(base/'depth.after.lua').read_text(encoding='utf-8')
source=(base.parents[2]/'mod/FoxholeRTS/Scripts/main.lua').read_text(encoding='utf-8')
assert source.count(after)==1,'Drift na fonte integrada: revisar teste'
start=source.index('function rts.outlineDepth(m, on)')
end=source.index('\nfunction rts.clearOutline',start)
actual=source[start:end]
assert actual==after
baseline=source.replace(actual,before,1)
assert baseline.count(before)==1
def check(code):
    lua=LuaRuntime()
    lua.execute("""
rts={}; function valid(x) return x and x.IsValid() end
local function obj(t) t.IsValid=function() return true end; return t end
writes,stencils=0,0
component=obj({bRenderCustomDepth=false,CustomDepthStencilValue=0,
SetRenderCustomDepth=function(self,on) writes=writes+1;self.bRenderCustomDepth=on end,
SetCustomDepthStencilValue=function(self,value) stencils=stencils+1;self.CustomDepthStencilValue=value end})
m={pawn=obj({}),outlineParts={component}}
""")
    lua.execute(code)
    lua.execute("""
rts.outlineDepth(m,true);assert(component.bRenderCustomDepth and component.CustomDepthStencilValue==1)
rts.outlineDepth(m,true) -- sem mudanca/input: nao precisa escrever
component.bRenderCustomDepth=false;component.CustomDepthStencilValue=0 -- nativo desfez selecionado
rts.outlineDepth(m,true);assert(component.bRenderCustomDepth and component.CustomDepthStencilValue==1)
rts.outlineDepth(m,false);assert(not component.bRenderCustomDepth)
component.bRenderCustomDepth=true -- nativo reativou amigo nao selecionado/olho
rts.outlineDepth(m,false);assert(not component.bRenderCustomDepth)
rts.outlineDepth(m,false) -- sem mudanca/input
m.pawn.bActorIsBeingDestroyed=true;rts.outlineDepth(m,true)
""")
    return lua.eval('writes'),lua.eval('stencils')
assert check(baseline[start:baseline.index("\nfunction rts.clearOutline",start)])==(6,3)
assert check(after)==(4,2)
assert check(actual)==(4,2)
print('OK: flags reais reaplicadas apos mudanca nativa, seminput/retirada preservados; fonte REAL writes6->4/stencils3->2')
