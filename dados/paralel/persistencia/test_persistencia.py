"""Testes offline da PERSISTENCIA contra o candidato completo (main.lua atual + ECONOMIA + PERSISTENCIA).

Cada "carga do jogo" e um LuaRuntime novo executando o chunk candidato inteiro (estado Lua zerado, como ao
reiniciar o jogo); o arquivo de save passa de uma carga para a outra pelo sistema de arquivos falso.
Roda em Lua 5.4 (UE4SS) e 5.5 (padrao do lupa). Nao abre jogo, laboratorio, canal nem arquivos reais.
Uso (raiz do repo, bash): PYTHONPATH=D:/tools/pylibs python dados/paralel/persistencia/test_persistencia.py
"""
from pathlib import Path
import importlib
import sys

HERE = Path(__file__).resolve().parent
ROOT = HERE.parents[2]
sys.path.insert(0, str(HERE))
import build_patch  # noqa: E402

SOURCE = ROOT.joinpath("mod/FoxholeRTS/Scripts/main.lua").read_text(encoding="utf-8")
STACKS = {"main+ECONOMIA+PERSISTENCIA": build_patch.build(SOURCE)}
SKIPPED = []
try:  # IA_LOGISTICA e entrega paralela em andamento: testada se o build dela fechar, senao registrada como SKIP
    STACKS["main+ECONOMIA+IA_LOGISTICA+PERSISTENCIA"] = build_patch.build_with_ia(SOURCE)
except Exception as e:  # noqa: BLE001
    SKIPPED.append(f"pilha com IA_LOGISTICA: build falhou ({type(e).__name__}: {e})")
CANDIDATE = STACKS["main+ECONOMIA+PERSISTENCIA"]
scaffold = ROOT.joinpath("tools/test_orders.py").read_text(encoding="utf-8")
start = scaffold.index("lua.execute('''") + len("lua.execute('''")
PRELUDE = scaffold[start:scaffold.index("''')", start)]
HARNESS = HERE.joinpath("harness_test.lua").read_text(encoding="utf-8")
SAVE = "ue4ss/Mods/FoxholeRTS/save.txt"
API_TAIL = '''
return { sv=sv, logi=logi, CFG=CFG, S=S, combat=combat, economy=economy, rts=rts, fort=fort,
    points=function() return points end, squad=function() return squad end, enemies=function() return enemies end,
    structures=function() return structures end, addPoint=function(x, y) return addPoint(x, y) end,
    hooks={ authority=function(fn) isLocalAuthority=fn end, spawnSoldier=function(fn) spawnSoldier=fn end,
            addPoint=function(fn) addPoint=fn end } }
'''
RESULTS = []


def new_load(version, files=None):
    """Uma carga do jogo: chunk candidato inteiro num runtime novo; files = arquivos herdados do disco."""
    lua = importlib.import_module("lupa." + version).LuaRuntime()
    lua.execute(PRELUDE)
    lua.globals().api = lua.execute(CANDIDATE + API_TAIL)
    lua.execute(HARNESS)
    for path, text in (files or {}).items():
        lua.globals().FS.files[path] = text
    return lua


def disk(lua):
    return {k: v for k, v in lua.eval("FS.files").items()}


def case(name, version, fn, stack):
    global CANDIDATE
    CANDIDATE = STACKS[stack]
    fn(version)
    RESULTS.append(f"{stack} / {version}: {name}")


# ---------------------------------------------------------------- 1. parser de literais e schema
def t_parser(v):
    lua = new_load(v)
    lua.execute(r'''
local sv = api.sv
local real = load
load = function() error("load chamado na leitura do save") end
local loadstring_ = loadstring
local data = { a = "aspas \" barra \\ quebra\n retorno\r nulo\0 fim", b = -12.5, c = 7, d = true, e = false,
               f = { [1] = { x = 1.25 }, [2] = { y = "ç ã" } }, [3] = 1e15 }
local back = sv.decode("return " .. sv.ser(data))
assert(back and back.a == data.a and back.b == -12.5 and back.c == 7 and back.d == true and back.e == false)
assert(back.f[1].x == 1.25 and back.f[2].y == "ç ã" and back[3] == 1e15)
for _, bad in ipairs({ "os.exit()", "return os", "return {v=2}", 'return {["a"]=nil}', 'return {["a"]=x}',
    'return {["a"]=function() end}', 'return (function() while true do end end)()', 'return {["a"]=1,["a"]=2}',
    'return {["a"]=1} os.exit()', 'return {["a"]=1e999}', 'return {["a"]=0x10}', 'return {["a"]=1 --[[x]]}',
    'return {["a"]="sem fim}', 'return {["a"]="\\q"}', 'return {[1.5]=1}', 'return {["a"]=-}', "", "return",
    'return {["a"]="linha\nnova"}', 'return {["a"]={}', 'return {["a"]=1}}' }) do
    local d, why = sv.decode(bad)
    assert(d == nil and type(why) == "string", "aceitou: " .. bad)
end
local deep = "return " .. string.rep('{["a"]=', 13) .. "1" .. string.rep("}", 13)
assert(sv.decode(deep) == nil)
assert(sv.decode("return " .. string.rep(" ", api.CFG.PERSIST.maxBytes)) == nil)
local many = {}
for i = 1, api.CFG.PERSIST.maxItems + 1 do many[i] = 1 end
assert(sv.decode("return " .. sv.ser(many)) == nil)
-- userdata nunca entra: ser escreveria "nil", o parser recusa; sv.pure detecta antes.
assert(sv.pure({ a = { b = io.stdout } }) == false and sv.pure({ a = 0/0 }) == false and sv.pure({ a = { 1, "x" } }))
assert(sv.decode("return " .. sv.ser({ a = io.stdout })) == nil)
load = real
''')


def t_schema(v):
    lua = new_load(v)
    lua.execute(r'''
local sv, C = api.sv, api.CFG
local function base()
    return { v = 2, world = "/Game/Maps/Master/CallumsCapeHex.CallumsCapeHex", map = "CallumsCapeHex", diff = 2,
        points = { { x = 0, y = 0, owner = -1, prog = 0 } }, squad = { { role = "rifle", x = 1, y = 2, hp = 50 } },
        infra = { version = 1, budget = 1100, bmat = 0, spent = 1100, built = {
            { kind = "site", code = "Refinery", x = 1, y = 2, z = 3, yaw = 4 }, { kind = "site", code = "Factory", x = 1, y = 2, z = 3, yaw = 4 },
            { kind = "truck", x = 1, y = 2, z = 3, yaw = 0 }, { kind = "truck", x = 1, y = 2, z = 3, yaw = 0 }, { kind = "truck", x = 1, y = 2, z = 3, yaw = 0 } } } }
end
assert(sv.validate(base()))
local function bad(mut, expect)
    local d = base(); mut(d)
    local ok, why = sv.validate(d)
    assert(not ok, "aceitou: " .. tostring(expect))
    if expect then assert(tostring(why):find(expect, 1, true), tostring(why)) end
end
bad(function(d) d.v = 3 end, "versão futura v3")
bad(function(d) d.v = "2" end, "versão desconhecida")
bad(function(d) d.world = nil end, "sem mundo")
bad(function(d) d.extra = 1 end, "campo desconhecido")
bad(function(d) d.infra.version = 2 end, "infra de versão futura")
bad(function(d) d.infra.bmat = 100 end, "carteira incoerente")
bad(function(d) d.infra.built[5] = nil end, "não confere")
bad(function(d) d.infra.built[2].code = "Refinery" end, "instalação")
bad(function(d) d.infra.built[1].code = "Bunker" end, "instalação")
bad(function(d) d.infra.built[1].x = 1e9 end, "infra 1")
bad(function(d) d.infra.built[1].actor = 1 end)
bad(function(d) d.squad[1].role = "tank" end, "squad 1")
bad(function(d) d.squad[1].post = 2 end, "squad 1")
bad(function(d) d.squad[1].x = 0/0 end)
bad(function(d) d.points[1].owner = 7 end, "dono")
bad(function(d) d.points[3] = { x = 0, y = 0, owner = -1 } end, "pontos")
bad(function(d) d.enemy = { version = 1, cargo = 1, convoys = 0, cut = 0 } end, "inimigo")  -- sem logi
bad(function(d) d.v = 1 end, "v1 com campos de v2")
bad(function(d) d.logi = { version = 2, bmat = -1 } end, "logística inválida")
bad(function(d) d.logi = { version = 9 } end, "logística inválida")
local legacy = { v = 1, map = "CallumsCapeHex", diff = 2, wave = 1, points = {}, squad = {}, logi = { bmat = 40, fa = 1, fs = 1, ba = 6, bs = 20, pts = {} } }
assert(sv.validate(legacy), "v1 legado deve ser aceito")
-- o validador nao troca a lista viva de pontos (proxy so durante a chamada)
local live = api.points()
assert(sv.validate({ v = 2, world = "x", points = { { x = 0, y = 0, owner = 1 } }, logi = { version = 2, pts = { [1] = { a = 1 } } } }))
assert(api.points() == live)
''')


# ---------------------------------------------------------------- 2. ida e volta numa carga nova do hex
def first_load(v, deploy=True, world_opts=None):
    """Carga A: implanta (Alt+L) sobre ruinas, joga, grava. Devolve (runtime, ledger antes, disco)."""
    a = new_load(v)
    a.execute(f"H.newWorld({world_opts or '{}'})")
    if deploy:
        a.execute("assert(api.logi.deploy())")
    a.execute("H.richMatch()")
    ledger = a.eval("H.ledger()")
    assert a.eval("api.sv.save()") is True, "save falhou"
    files = disk(a)
    assert SAVE in files and all(ord(c) < 128 for c in files[SAVE]), "save deve ser ASCII"
    assert "load(" not in files[SAVE] and "function" not in files[SAVE]
    return a, ledger, files


def t_roundtrip(v):
    a, ledger, files = first_load(v)
    assert a.eval("H.spawned") == 5 and "carteira=0/1100/5" in ledger, ledger
    b = new_load(v, files)
    b.execute("H.newWorld()")
    assert b.eval("H.live('BPRefinery_C') + H.live('BPFactory_C') + H.live('BPTruckW_C')") == 0
    assert b.eval("api.sv.load()") is True, b.eval("table.concat(H.logs, '\\n')")
    after = b.eval("H.ledger()")
    assert after == ledger, f"\nantes {ledger}\ndepois {after}"
    assert b.eval("H.spawned") == 5 and b.eval("H.live('BPRefinery_C')") == 1 and b.eval("H.live('BPFactory_C')") == 1
    assert b.eval("H.live('BPTruckW_C')") == 3 and b.eval("H.ruinR.bHidden and not H.ruinR.collision")
    assert b.eval("api.sv.degraded") is None and b.eval("api.logi.on") is True
    assert b.eval("#api.structures()") == 1 and b.eval("#api.S.trenches") == 1 and b.eval("#api.S.tents") == 1
    assert b.eval("#api.S.wires") == 1 and b.eval("api.enemies()[1].post == api.points()[2]")
    assert b.eval("api.economy.manpower") == 77 and b.eval("api.combat.wave") == 3
    # caminhao a caminho do ponto A entrega no deposito do ponto A (indice estavel), uma unica vez
    b.execute('''
local L = api.logi
local tr = L.trucks[2]
assert(tr.state == "toDep" and tr.dest == api.points()[1].dep and not tr.route)
L.drive = function() return true end
L.truckStep(tr, 1, clock)
assert(api.points()[1].dep.ammo == 2 and api.points()[1].dep.medical == 50 and not tr.cargo)
''')
    # Gravar de novo na carga B: mesmo conteudo de infra/logistica (nenhum ator/endereco entrou)
    assert b.eval("api.sv.save()") is True
    lua_eq = b.eval('''(function()
        local A = api.sv.decode(FS.files["ue4ss/Mods/FoxholeRTS/save.txt.bak"])
        local B = api.sv.decode(FS.files["ue4ss/Mods/FoxholeRTS/save.txt"])
        return H.deq(A.infra, B.infra) and A.world == B.world and B.v == 2 and (api.logi.eSnapshot and (B.enemy == nil and B.elogi ~= nil) or (B.enemy.cargo == 1 and B.elogi == nil))
    end)()''')
    assert lua_eq


def t_repeat(v):
    _, ledger, files = first_load(v)
    b = new_load(v, files)
    b.execute("H.newWorld()")
    for i in range(3):
        assert b.eval("api.sv.load()") is True
        assert b.eval("H.ledger()") == ledger, f"repetição {i}"
        assert b.eval("H.spawned") == 5, "restauração repetida não pode duplicar atores"
        assert b.eval("H.live('BPTruckW_C')") == 3 and b.eval("H.live('BPFactory_C')") == 1
        assert b.eval("H.live('Pawn')") >= 3
    # pawns antigos foram destruidos; vivos = exatamente o save (3 nossos + 1 inimigo)
    assert b.eval("H.live('Pawn')") == 4, b.eval("H.live('Pawn')")
    # mesma carga, sem reiniciar: continuar em cima da propria implantacao tambem nao cria nada
    a, ledger_a, _ = first_load(v)
    assert a.eval("api.sv.load()") is True and a.eval("H.spawned") == 5 and a.eval("H.ledger()") == ledger_a
    # Alt+L na carga nova antes de continuar: implantacao identica, continuar nao cobra nem duplica
    c = new_load(v, files)
    c.execute("H.newWorld(); assert(api.logi.deploy())")
    assert c.eval("H.spawned") == 5 and c.eval("api.sv.load()") is True
    assert c.eval("H.spawned") == 5 and c.eval("H.ledger()") == ledger


# ---------------------------------------------------------------- 3. recusas antes de qualquer mutacao
PRESERVE = '''
local function state()
    local L = api.logi
    return table.concat({ tostring(api.squad()), #api.squad(), tostring(api.points()), #api.points(), tostring(L.on),
        tostring(L.bmat), tostring(api.S.deploy), api.S.deploy and api.S.deploy.bmat or -1, H.spawned,
        tostring(api.combat.auto), H.ledger() }, "|")
end
H.state = state
'''


def refused(lua, expect):
    lua.execute(PRESERVE)
    before, files = lua.eval("H.state()"), lua.eval("H.snapshotFiles()")
    lua.execute("H.logs = {}")
    assert lua.eval("api.sv.load()") is False
    assert lua.eval(f"H.saw({expect!r})"), (expect, lua.eval("table.concat(H.logs, ' / ')"))
    assert lua.eval("H.state()") == before, "recusa alterou a sessão"
    assert lua.eval("H.sameFiles")(files), "recusa alterou arquivos"


def live_session(v, files, world="{}"):
    """Carga B com uma partida própria em andamento (implantação + partida), sobre a qual se tenta continuar."""
    b = new_load(v, files)
    b.execute(f"H.newWorld({world}); H.mySession = true")
    b.execute("assert(api.logi.deploy()); assert(api.logi.start()); local S = api.squad(); S[#S+1] = H.unit('rifle', 10, 10); api.combat.auto = true")
    return b


def t_refusals(v):
    _, _, files = first_load(v)
    # mapa errado (mesmo nome curto em outro caminho tambem e outro mundo)
    for name in ["World /Game/Maps/Master/DeadLandsHex.DeadLandsHex", "World /Game/Other/CallumsCapeHex.CallumsCapeHex"]:
        b = new_load(v, files); b.execute("H.newWorld()")
        b.execute(f"WORLD.name = {name!r}")
        refused(b, "outro mundo")
    # caixa diferente no caminho do pacote nao e outro mundo (gotcha DeadlandsHex/DeadLandsHex)
    b = new_load(v, files); b.execute("H.newWorld(); WORLD.name = 'World /Game/Maps/Master/callumscapehex.CallumsCapeHex'")
    assert b.eval("api.sv.load()") is True
    # ruina da fabrica em outro lugar / rotacao diferente: recusa sem spawn
    b = new_load(v, files); b.execute("H.newWorld({factoryX = -9000})"); refused(b, "nem ruína na posição salva")
    b = new_load(v, files); b.execute("H.newWorld({factoryYaw = 90})"); refused(b, "rotação diferente")
    # campo de sucata ausente: nunca inventado
    b = new_load(v, files); b.execute("H.newWorld(); ACT.BPSalvageField_C = {}"); refused(b, "sem campo de sucata")
    # sem vaga de terreno para os caminhoes pagos (telhado)
    b = new_load(v, files); b.execute("H.newWorld(); terrainClass = 'Warehouse'"); refused(b, "sem vagas de terreno")
    # ponto salvo sem superficie / parede sem chao (regiao nao carregada)
    b = new_load(v, files); b.execute("H.newWorld(); H.noSurface = function(x) return x == 6000 end"); refused(b, "sem superfície no ponto salvo 2")
    b = new_load(v, files); b.execute("H.newWorld(); H.noGround = function(x, y) return x == 1000 and y == 200 end"); refused(b, "sem chão para walls 1")
    # sessao propria na carga com implantacao DIFERENTE da salva: recusa e preserva tudo
    b = live_session(v, files)
    b.execute("api.S.deploy.built[5] = nil; api.S.deploy.built[4] = nil; api.S.deploy.spent = 900; api.S.deploy.bmat = 200")
    refused(b, "implantação diferente da salva")
    # arquivo em versao futura / corrompido / grande demais / ausente: sessao viva e arquivo preservados
    future = dict(files); future[SAVE] = files[SAVE].replace('["v"]=2', '["v"]=3')
    b = live_session(v, future); refused(b, "versão futura v3")
    trunc = dict(files); trunc[SAVE] = files[SAVE][: len(files[SAVE]) // 2]
    b = live_session(v, trunc); refused(b, "save inválido ou incompatível")
    neg = dict(files); neg[SAVE] = files[SAVE].replace('["bmat"]=123.500', '["bmat"]=-5')
    assert neg[SAVE] != files[SAVE]
    b = live_session(v, neg); refused(b, "logística inválida")
    b = live_session(v, {}); refused(b, "nenhuma partida salva")
    # cadeia inimiga (chave `elogi` da IA_LOGISTICA): com o módulo, valor inválido recusa o save inteiro;
    # sem o módulo, a chave é de outra versão do mod e também recusa (não descarta estoque inimigo calado)
    mutate = 'local P = "%s"; local d = api.sv.decode(FS.files[P]); %s; FS.files[P] = "return " .. api.sv.ser(d)'
    b = live_session(v, files)
    if b.eval("api.logi.eSnapshot ~= nil"):
        b.execute(mutate % (SAVE, "d.elogi.ready = -1")); refused(b, "cadeia inimiga inválida")
    else:
        b.execute(mutate % (SAVE, "d.elogi = { v = 1 }")); refused(b, "campo desconhecido: elogi")
    # save sem caminhoes pagos numa carga sem caminhoes nativos: nao cria caminhao de graca
    a2 = new_load(v); a2.execute("H.newWorld({trucks = 3}); assert(api.logi.deploy()); H.richMatch()")
    assert a2.eval("api.S.deploy.spent") == 800 and a2.eval("api.sv.save()") is True
    b = new_load(v, disk(a2)); b.execute("H.newWorld()"); refused(b, "o save só pagou 0")
    # mesma carga com caminhoes nativos: continua sem spawn de caminhao e sem reembolso
    b = new_load(v, disk(a2)); b.execute("H.newWorld({trucks = 3})")
    assert b.eval("api.sv.load()") is True and b.eval("H.spawned") == 2 and b.eval("api.S.deploy.bmat") == 300


def t_apply_rollback(v):
    _, _, files = first_load(v)
    b = new_load(v, files)
    b.execute("H.newWorld(); local S = api.squad(); S[1] = H.unit('rifle', 10, 10); H.spawnFailAt2 = 2")  # fabrica nasce com HP errado
    b.execute(PRESERVE)
    before = b.eval("H.state()")
    assert b.eval("api.sv.load()") is False and b.eval("H.saw('infraestrutura salva não foi refeita')")
    assert b.eval("H.live('BPRefinery_C') + H.live('BPFactory_C') + H.live('BPTruckW_C')") == 0, "spawn parcial não desfeito"
    assert b.eval("not H.ruinR.bHidden and H.ruinR.collision and not H.ruinF.bHidden and H.ruinF.collision"), "ruínas não restauradas"
    assert b.eval("api.S.deploy == nil"), "carteira criada/alterada numa falha"
    b.execute("H.spawned = 0")
    assert b.eval("H.state()").split("|")[:8] == before.split("|")[:8]
    # tentar de novo depois da falha funciona e nao duplica
    b.execute("H.spawnFailAt2 = nil")
    assert b.eval("api.sv.load()") is True and b.eval("H.spawned") == 5


# ---------------------------------------------------------------- 4. falha depois do preflight
def t_partial(v):
    _, ledger, files = first_load(v)
    # um soldado nao nasce: partida continua, mas o save bom nao e sobrescrito
    b = new_load(v, files)
    b.execute("H.newWorld(); H.spawnFailAt = 2")
    assert b.eval("api.sv.load()") is True
    assert b.eval("api.sv.degraded ~= nil") and b.eval("H.saw('INCOMPLETA: soldados 2/3')")
    good = b.eval("FS.files['ue4ss/Mods/FoxholeRTS/save.txt']")
    assert b.eval("api.sv.save()") is False and b.eval("H.saw('autosave suspenso')")
    assert b.eval("FS.files['ue4ss/Mods/FoxholeRTS/save.txt']") == good
    assert b.eval("FS.files['ue4ss/Mods/FoxholeRTS/save.txt.bak']") is None
    # logistica foi restaurada (pontos intactos) e a contabilidade bate, salvo os soldados
    assert b.eval("H.ledger()").split(" | ")[:-1] == ledger.split(" | ")[:-1]
    # nova partida (startT novo, como toggleWaves): autosave volta
    b.execute("api.combat.startT = clock - 5")
    assert b.eval("api.sv.save()") is True
    # ponto nao volta (addPoint recusa depois do preflight): deposito por indice nao pode trocar de dono
    b = new_load(v, files)
    b.execute("H.newWorld(); H.pointFail = function(x) return x == 3000 end")
    assert b.eval("api.sv.load()") is True
    assert b.eval("H.saw('logística não restaurada')") and b.eval("H.saw('pontos 1/2')")
    assert b.eval("api.logi.on") is False and b.eval("api.logi.bmat") == 0, "sem estoque inicial fictício"
    assert b.eval("api.sv.save()") is False
    # infraestrutura paga continua coerente: nova tentativa nao recobra nem duplica
    b.execute("H.pointFail = nil")
    assert b.eval("api.sv.load()") is True and b.eval("H.spawned") == 5 and b.eval("H.ledger()") == ledger


# ---------------------------------------------------------------- 5. gravacao atomica
def t_atomic(v):
    lua = new_load(v)
    lua.execute('''
local sv, P = api.sv, "ue4ss/Mods/FoxholeRTS/save.txt"
local function doc(n) return "return " .. sv.ser({ v = 1, map = "M", wave = n }) .. "\\n" end
assert(sv.writeAtomic(P, doc(1)) and FS.files[P] == doc(1) and not FS.files[P .. ".tmp"] and not FS.files[P .. ".bak"])
assert(sv.writeAtomic(P, doc(2)) and FS.files[P] == doc(2) and FS.files[P .. ".bak"] == doc(1))
-- temporario nao abre
FS.failOpen[P .. ".tmp"] = true
assert(not sv.writeAtomic(P, doc(3)) and FS.files[P] == doc(2) and FS.files[P .. ".bak"] == doc(1))
FS.failOpen[P .. ".tmp"] = nil
-- disco cheio no meio da escrita
FS.failWrite = true
assert(not sv.writeAtomic(P, doc(3)) and FS.files[P] == doc(2) and not FS.files[P .. ".tmp"])
FS.failWrite = false
-- rename final falha: o anterior volta ao lugar
FS.failRename[P .. ".tmp>" .. P] = true
assert(not sv.writeAtomic(P, doc(3)) and FS.files[P] == doc(2) and FS.files[P .. ".tmp"] == doc(3))
FS.failRename[P .. ".tmp>" .. P] = nil
FS.files[P .. ".tmp"] = nil
-- queda entre os dois renames: a leitura acha o temporario completo
FS.crash = P .. ".tmp>" .. P
assert(not pcall(sv.writeAtomic, P, doc(4)))
FS.crash = nil
assert(FS.files[P] == nil and FS.files[P .. ".bak"] == doc(2) and FS.files[P .. ".tmp"] == doc(4))
local d, _, src = sv.read()
assert(d and d.wave == 4 and src == ".tmp")
-- save principal corrompido: proxima gravacao o guarda como .corrupt e preserva o .bak bom
FS.files[P], FS.files[P .. ".tmp"] = "return {lixo", nil
local d2, _, src2 = sv.read()
assert(d2 and d2.wave == 2 and src2 == ".bak", "corrompido cai no .bak")
assert(sv.writeAtomic(P, doc(5)) and FS.files[P .. ".corrupt"] == "return {lixo" and FS.files[P .. ".bak"] == doc(2))
-- vitoria/derrota apaga tudo
sv.clear()
assert(next(FS.files) == nil)
-- sv.save nunca grava NaN nem dado fora do schema: arquivo anterior fica
FS.files[P] = doc(9)
H.newWorld({ active = true, trucks = 3 })
H.richMatch()
api.logi.bmat = 0/0
assert(api.sv.save() == false and FS.files[P] == doc(9) and H.saw("save recusado"))
api.logi.bmat = 10
assert(api.sv.save() == true and api.sv.read().v == 2)
''')


# ---------------------------------------------------------------- 6. legado v1
def t_legacy(v):
    lua = new_load(v)
    # Texto no formato exato do v1 (sv.ser identico; sem world/infra/enemy; logi sem version)
    lua.execute('''
local v1 = { v = 1, map = "CallumsCapeHex", diff = 2, wave = 2, kills = 3, losses = 1, elapsed = 50, mp = 60, aimp = 5,
    shots = 10, hits = 4, nextIn = 12, points = { { x = 3000, y = 0, owner = 1, prog = 1 } },
    squad = { { role = "rifle", x = 0, y = 0, z = 0, hp = 90, kills = 1, ammo = 20, group = 1 } }, enemies = {},
    walls = {}, trenches = {}, tents = {}, wires = {}, logi = { salvage = 10, bmat = 40, fa = 1, fs = 1, ba = 6, bs = 20, prio = "auto",
    pts = { { a = 2, s = 5 } } } }
FS.files["ue4ss/Mods/FoxholeRTS/save.txt"] = "return " .. api.sv.ser(v1) .. "\\n"
H.newWorld({ active = true, trucks = 3 })
assert(api.sv.load() == true and api.sv.degraded == nil)
assert(api.logi.bmat == 40 and api.logi.fac.rifle == 0 and api.points()[1].dep.ammo == 2)
assert(api.S.deploy == nil, "v1 não mexe na carteira")
-- v1 de outro mapa (so nome curto): recusa
FS.files["ue4ss/Mods/FoxholeRTS/save.txt"] = "return " .. api.sv.ser(v1):gsub("CallumsCapeHex", "DeadLandsHex") .. "\\n"
assert(api.sv.load() == false and H.saw("outro mapa"))
-- v1 numa carga so com ruinas: recusa antes de limpar (precisa de Alt+L, como hoje)
FS.files["ue4ss/Mods/FoxholeRTS/save.txt"] = "return " .. api.sv.ser(v1) .. "\\n"
H.newWorld()
local n = #api.squad()
assert(api.sv.load() == false and #api.squad() == n and H.saw("sem atores ativos"))
''')


CASES = [("parser de literais (sem load, sem userdata)", t_parser), ("schema/versões/migração v1", t_schema),
         ("ida e volta em carga nova + regravação", t_roundtrip), ("restauração repetida e Alt+L antes (sem duplicar)", t_repeat),
         ("recusas preservam sessão e arquivo", t_refusals), ("rollback da infraestrutura", t_apply_rollback),
         ("falha após preflight: autosave suspenso, sem estoque fictício", t_partial), ("gravação atômica/recuperação", t_atomic),
         ("legado v1", t_legacy)]

if __name__ == "__main__":
    for stack in STACKS:
        for version in ("lua54", "lua55"):
            for name, fn in CASES:
                case(name, version, fn, stack)
    for r in RESULTS:
        print("PASS", r)
    for s in SKIPPED:
        print("SKIP", s)
    print(f"PASS: {len(RESULTS)} casos ({len(CASES)} cenários x Lua 5.4/5.5 x {len(STACKS)} pilha(s)); SKIP: {len(SKIPPED)}")
