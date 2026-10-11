"""$env:PYTHONPATH='D:/tools/pylibs'; python data/parallel/roads/test_roads.py"""
from pathlib import Path
from lupa import LuaRuntime
lua=LuaRuntime()
lua.globals().roads=lua.execute(Path(__file__).with_name('roads.lua').read_text(encoding='utf-8'))
lua.execute('''
local net={epoch='Callums:1',nodes={a={X=0,Y=0,Z=0},b={X=100,Y=0,Z=0},
 c={X=100,Y=100,Z=0},d={X=900,Y=0,Z=0}},edges={a={{to='b',validated=true}},
 b={{to='c',validated=true}},c={},d={}}}
local r=assert(roads.plan(net,'a','c',net.epoch))
assert(#r.ids==3 and r.distance==200)
local p,why=roads.plan(net,'a','d',net.epoch); assert(not p and why=='rota_ausente')
p,why=roads.plan(net,'a','c','HomeRegionW'); assert(not p and why=='regiao_invalida')
local cargo={ammo=5,shirts=2}; local pos=net.nodes.a
local state,nextPos,reached=roads.advance(net,r,pos,.5,100,true,function() return true end)
assert(state=='movendo' and nextPos.X==50 and not reached and r.index==2)
state=roads.advance(net,r,pos,.5,100,true,function() return false end)
assert(state=='bloqueado' and r.index==2 and cargo.ammo==5 and cargo.shirts==2)
net.edges.a[1].blocked=true
state=roads.advance(net,r,pos,.5,100,true,function() return true end); assert(state=='bloqueado')
net.edges.a[1].blocked=false; net.edges.a[1].validated=false
p,why=roads.plan(net,'a','c',net.epoch); assert(not p and why=='rota_ausente')
net.edges.a[1].validated=true
state=roads.advance(net,r,pos,.5,100,false,function() return true end); assert(state=='veiculo_destruido')
net.epoch='Callums:2'; state=roads.advance(net,r,pos,.5,100,true,function() return true end)
assert(state=='regiao_invalida' and cargo.ammo==5)
net.epoch='Callums:1'; pos={X=50,Y=0,Z=0}
state,nextPos,reached=roads.advance(net,r,pos,.5,100,true,function() return true end)
assert(nextPos.X==100 and reached); roads.commit(r,reached); assert(r.index==3)
pos=nextPos; state,nextPos,reached=roads.advance(net,r,pos,.5,200,true,function() return true end)
assert(nextPos.Y==100 and reached); roads.commit(r,reached)
state=roads.advance(net,r,nextPos,.5,100,true,function() return true end); assert(state=='chegou')
''')
print('OK: grafo, desconexao, epoch, bloqueio, confirmacao, carga, morte e chegada')
