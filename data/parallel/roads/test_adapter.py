from pathlib import Path
from lupa import LuaRuntime
l=LuaRuntime()
l.globals().adapter=l.execute(Path(__file__).with_name('native_adapter.lua').read_text(encoding='utf-8'))
l.execute('''
local snapshot={epoch='world:hash',nodes={a={},b={},c={}},edges={a={{to='b',segment='s',road_asset=true}},b={{to='c',segment='s',road_asset=true}}}}
local net=adapter.graph(snapshot,'session1',{})
assert(not net.edges.a[1].validated)
local p={epoch=net.epoch,surface=true,clearance=true,support=true,segment='s',from='a',to='b'}
assert(not adapter.graph(snapshot,'session1',{s=p}).edges.a[1].validated, 'prova antiga de spline inteira recusada')
local proof={a={b=p}}
assert(adapter.graph(snapshot,'session1',proof).edges.a[1].validated)
assert(not adapter.graph(snapshot,'session1',proof).edges.b[1].validated, 'mesma spline, trecho ainda não inspecionado')
proof.b={c=p}
assert(not adapter.graph(snapshot,'session1',proof).edges.b[1].validated, 'prova copiada para outro trecho recusada')
p.segment='outra'
assert(not adapter.graph(snapshot,'session1',proof).edges.a[1].validated)
p.segment='s'
assert(not adapter.graph(snapshot,'session2',proof).edges.a[1].validated)
snapshot.edges.a[1].road_asset=false
assert(not adapter.graph(snapshot,'session1',proof).edges.a[1].validated)
local a=adapter.access({}, {},{body=160,step=30,maxNodes=100},{},function() return {failed=false} end)
assert(adapter.accessTick(a,function() return nil end,4)=='planning')
assert(adapter.accessTick(a,function(job) job.failed=true; return {} end,4)=='failed')
local tr={cargo={ammo=5,shirts=2}},fac
fac={ammo=1,shirts=3}
assert(not adapter.returnCargo(tr,fac,function() return false end,.1))
assert(tr.cargo.ammo==5 and fac.ammo==1 and tr.state=='returnCargo')
assert(adapter.returnCargo(tr,fac,function() return true end,.1))
assert(not tr.cargo and fac.ammo==6 and fac.shirts==5 and tr.state=='idle')
''')
print('OK adapter: provas por sessao, asset nao autoriza fisica, acesso incremental, retorno fisico')
