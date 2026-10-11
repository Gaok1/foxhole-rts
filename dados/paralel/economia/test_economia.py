from pathlib import Path
import re
from lupa import LuaRuntime
root=Path(__file__).parent
lua=LuaRuntime()
module=lua.execute(root.joinpath('economia.lua').read_text(encoding='utf-8-sig'))
lua.globals().E=module
source=root.parents[2].joinpath('dados/custos_do_jogo.txt').read_text(encoding='utf-8')
for kind in ['rifle','grenade','medical']:
    recipe=module.recipes[kind]
    pattern=rf'^{recipe.code} \| custo=(\S+) qtd=(\d+) tempo=(\d+)$'
    matches=re.findall(pattern, source, re.M)
    assert len(matches)==1, ('schema/receita ausente ou duplicada',recipe.code)
    costs,units,seconds=matches[0]
    expected={}
    for part in costs.split('+'):
        match=re.fullmatch(r'([A-Za-z]+)x([1-9][0-9]*)',part)
        assert match,part
        expected[match[1]]=int(match[2])
    assert dict(recipe.costs.items())==expected
    assert recipe.units==int(units) and recipe.time==int(seconds)
lua.execute('''
f={materials={Cloth=300,Explosive=0},boxes={}}
t={capacity=2};d={friendly=true,stock={}}
-- Explosivo ausente: nenhuma dedução parcial de Cloth.
assert(not E.start(f,'grenade') and f.materials.Cloth==300)
assert(not E.start(f,'inexistente'))
assert(E.start(f,'rifle') and f.materials.Cloth==200)
assert(not E.start(f,'medical'))
assert(not E.tick(f,69) and not f.boxes.rifle)
assert(E.tick(f,1) and f.boxes.rifle==1)
assert(not E.tick(f,999) and f.boxes.rifle==1)
assert(not E.load(f,t,'rifle',0) and not E.load(f,t,'rifle',3))
assert(E.load(f,t,'rifle',1) and f.boxes.rifle==0)
assert(not E.load(f,t,'rifle',1))
d.friendly=false
assert(not E.deliver(t,d) and t.cargo.boxes==1)
d.friendly=true
assert(E.deliver(t,d) and d.stock.rifle==20)
assert(not E.deliver(t,d) and d.stock.rifle==20)
assert(not E.consume(d,{rifle=1,medical=1}) and d.stock.rifle==20)
assert(E.consume(d,{rifle=1}) and d.stock.rifle==19)
assert(not E.consume(d,{rifle=-1}) and not E.consume(d,{}))
assert(E.start(f,'medical') and f.materials.Cloth==120)
assert(E.cancel(f) and f.materials.Cloth==200)
assert(not E.cancel(f) and f.materials.Cloth==200)
assert(E.start(f,'medical') and E.tick(f,40))
assert(E.load(f,t,'medical',1))
assert(E.returnCargo(t,f) and f.boxes.medical==1)
assert(not E.returnCargo(t,f) and f.boxes.medical==1)
assert(E.load(f,t,'medical',1))
local lost=E.destroy(t)
assert(lost.kind=='medical' and lost.boxes*lost.units==50)
assert(not E.destroy(t) and not E.deliver(t,d) and not E.returnCargo(t,f))
-- Conservação rifles: 20 produzidos = 19 estoque + 1 consumido.
assert(d.stock.rifle+1==20 and f.boxes.rifle==0)
-- Conservação médico: 50 produzidos = 50 perdidos; sem retorno/entrega fictícia.
assert(f.boxes.medical==0 and (d.stock.medical or 0)==0)
f.materials.Explosive=40
assert(E.start(f,'grenade') and f.materials.Cloth==20 and f.materials.Explosive==0)
assert(not E.tick(f,-1) and not E.tick(f,0/0))
assert(E.tick(f,100) and f.boxes.grenade==1)
-- Schema/custo não vira produção gratuita.
E.recipes.bad={costs={},units=20,time=1}
assert(not E.start(f,'bad'))
E.recipes.bad.costs={Cloth=0}
assert(not E.start(f,'bad'))
''')
print('PASS: custos extraídos + escassez/produção/cancelamento/transporte/perda/consumo/conservação')
