"""Executa o Lua da proposta, sem engine. PYTHONPATH=D:/tools/pylibs python este_arquivo"""
from pathlib import Path
from lupa import LuaRuntime
root = Path(__file__).parent
lua = LuaRuntime()
lua.execute('''
combat={mode="defense",cargo=2}
CFG={LOGI={want={ammo=20,shirts=20},recipes={ammo={name="munição",units=1},shirts={name="camisas",units=10}}}}
logi={on=true,salvage=12,bmat=30,prio="auto",fac={ammo=2,shirts=3},trucks={}}
dep={name="base",ammo=1,shirts=0}
function logi.depots() return {dep} end
function logi.nextKind() return "ammo" end
''')
lua.execute(root.joinpath('painel.lua').read_text(encoding='utf-8-sig'))
def text(): return lua.eval('logi.hudLine()')
assert 'camisas 3 caixas (30 unidades)' in text()
assert 'abaixo da meta' in text()
assert 'aguarda bmat' in text()
lua.execute('logi.job={kind="shirts",left=4,total=8}; logi.trucks={{state="toDep",cargo={ammo=2,shirts=3},dest=dep}}')
assert 'camisas: 4 s restantes (total 8 s)' in text()
lua.execute('logi.job.total=nil')
assert 'camisas: 4 s restantes' in text() and '(total' not in text()
assert '2 munição + 3 camisas (caixas)' in text()
assert 'destino base' in text()
assert lua.eval('dep.ammo == 1 and dep.shirts == 0 and logi.fac.shirts == 3')
lua.execute('logi.trucks[1].state="dead"')
assert 'perdida' in text() and 'destino base' not in text()
lua.execute('logi.trucks={};logi.job=nil;dep.ammo=20;dep.shirts=20;function logi.nextKind() return nil end')
assert 'abaixo da meta' not in text() and 'demanda atendida' in text()
assert 'INIMIGO | carga 2' in text()
lua.execute('logi.foes={{}}')
assert 'comboio na estrada' in text()
lua.execute('combat.mode="assault"')
assert 'INIMIGO' not in text()
for state, kind, label, dest in [
    ('idle','res','iniciando coleta','campo'),
    ('idle','sup','retorno/aguarda fábrica','fábrica'),
    ('toField','res','ao campo','campo'),
    ('loading','res','carregando sucata','campo'),
    ('toRef','res','à refinaria','refinaria'),
]:
    lua.execute(f'logi.trucks={{{{state="{state}",kind="{kind}"}}}}')
    assert label in text() and ('destino ' + dest) in text()
lua.execute('dep.name="A2"')
assert 'A2 | munição 20' in text()
lua.execute('logi.on=false;logi.fac=nil;logi.trucks=nil')
assert text() == 'LOGÍSTICA INATIVA'
print('PASS: painel Lua; unidades, produção, trânsito, morte, metas, inativo; sem mutação')
