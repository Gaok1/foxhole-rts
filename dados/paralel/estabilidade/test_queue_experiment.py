from pathlib import Path
from lupa import LuaRuntime
base=Path(__file__).resolve().parent
source=(base.parents[2]/'mod/FoxholeRTS/Scripts/main.lua').read_text(encoding='utf-8')
old=(base/'queue_experiment.before.txt').read_text(encoding='utf-8').split('\n\n')
new=(base/'queue_experiment.after.txt').read_text(encoding='utf-8').split('\n\n')
assert len(old)==len(new)==2
assert 'CFG.KEYBIND_QUEUE = true' in source, 'Variante de fila nao integrada'
new[0]=source[source.index('CFG.KEYBIND_QUEUE ='):source.index('-- Teclas com e sem modificador')]
start=source.index('local function frameBody()')
new[1]=source[start:source.index('    step("hudTick"',start)].rstrip()
lua=LuaRuntime()
lua.execute("""
CFG={}; S={}; rts={}; execCalls=0; errors=0
function ExecuteInGameThread(f) execCalls=execCalls+1; f() end
function log(message) errors=errors+1 end
""")
api=lua.execute(new[0]+'\nreturn onGame')
lua.globals().wrap=api
lua.execute("""
order={}
CFG.KEYBIND_QUEUE=false
local immediate=wrap(function() order[#order+1]='old' end)
immediate();assert(execCalls==1 and order[1]=='old')
CFG.KEYBIND_QUEUE=true
local later=wrap(function() order[#order+1]='later' end)
wrap(function() order[#order+1]='first';later() end)()
wrap(function() error('simulada') end)()
wrap(function() order[#order+1]='last' end)()
assert(#order==1 and execCalls==1)
rts.drainGameQueue()
assert(table.concat(order,',')=='old,first,last' and errors==1 and #S.gameQueue==1)
rts.drainGameQueue()
assert(table.concat(order,',')=='old,first,last,later' and S.gameQueue==nil)
rts.drainGameQueue();assert(#order==4)
""")
# Extrair inicio real da proposta: dreno antes gate de autoridade/menu.
assert new[1].index('rts.drainGameQueue()')<new[1].index('isLocalAuthority()')
lua.execute("""
function isLocalAuthority() return false end
wrap(function() order[#order+1]='menu' end)()
""")
lua.execute(new[1]+'\nend\nframeBody()')
assert lua.eval("order[#order]=='menu'")
print('OK: fonte real integrada: false original, trueFIFO/erro/reentrancia/menu e nenhum Execute extra; nao prova thread-safety UE4SS')
