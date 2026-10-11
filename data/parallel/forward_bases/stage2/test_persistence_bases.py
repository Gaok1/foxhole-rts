"""BASES_AVANCADAS: save/continue com bases (extensao `fwd` v1 dentro do schema v2): ida e volta (atores refeitos, estoque por indice,
saidas recalculadas), repeticao sem duplicar, base cuja posicao nao valida mais, falha de spawn com rollback, save adulterado,
compatibilidade (v3 recusa fwd; v4 abre save sem fwd), base inativa, base destruida nao e salva.

  cd /d/GitHub/foxhole-rts && PYTHONPATH=D:/tools/pylibs PYTHONDONTWRITEBYTECODE=1 \
      python data/parallel/forward_bases/stage2/test_persistence_bases.py
"""
import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parent))
import harness_bases as H  # noqa: E402

SAVE = H.SAVE_PATH
WORLD = "H.newWorld({active = true, trucks = 3})"

STATE = r'''
function fwdState()
    local L = api.logi
    local out = {}
    for _, fb in ipairs(L.fwd) do
        local idx
        for i, p in ipairs(api.points()) do if p == fb.pt then idx = i end end
        out[#out + 1] = string.format("%s:%.1f,%.1f,%.1f,%.1f hp=%.1f stock=%d/%d/%.2f/%d exits=%d dead=%s", tostring(idx), fb.X, fb.Y, fb.Z, fb.yaw, fb.hp,
            fb.dep.shirts, fb.dep.rifle, fb.dep.ammo, fb.dep.medical, #fb.exits, tostring(fb.dead))
    end
    table.sort(out)
    return table.concat(out, " | ")
end
function sessionState()
    local L = api.logi
    return table.concat({ tostring(api.squad()), #api.squad(), tostring(api.points()), #api.points(), tostring(L.on), tostring(L.bmat),
        tostring(#L.fwd), tostring(fwdLive()), tostring(api.combat.auto), H.ledger() }, "|")
end
'''

BUILD = r'''
local L, C = api.logi, api.CFG
local P = api.points()
L.bmat = 1500
assert(L.fwdBuild(P[1]), "base no ponto A")
local fb = P[1].fb
fb.hp = 1000
fb.dep.shirts, fb.dep.rifle, fb.dep.ammo, fb.dep.medical = 12, 3, 2.5, 7
fb.led.init.shirts, fb.led.init.rifle = 12, 3
'''


def make_save(v, build=BUILD, text=None, extra=""):
    a = H.persist_game(text, version=v)
    a.execute(WORLD + "; H.richMatch()")
    a.execute(STATE)
    a.execute(build + extra)
    assert a.eval("api.sv.save()") is True, a.eval("table.concat(H.logs, '\\n')")
    return a, {k: x for k, x in a.eval("FS.files").items()}


def load_in(v, files, setup="", text=None):
    b = H.persist_game(text, version=v, files=files)
    b.execute(WORLD)
    b.execute(STATE)
    if setup:
        b.execute(setup)
    return b


def refused(lua, expect):
    lua.execute("H.logs = {}")
    before, snap = lua.eval("sessionState()"), lua.eval("H.snapshotFiles()")
    assert lua.eval("api.sv.load()") is False
    assert lua.eval("H.saw(%r)" % expect), (expect, lua.eval("table.concat(H.logs, ' / ')"))
    assert lua.eval("sessionState()") == before, "recusa alterou a sessao"
    assert lua.eval("H.sameFiles")(snap), "recusa alterou arquivos"


def t_ida_e_volta(v):
    a, files = make_save(v)
    state_a = a.eval("fwdState()")
    assert files[SAVE].count('["fwd"]') == 1 and "actor" not in files[SAVE] and "exits" not in files[SAVE], "so indice/XYZ/yaw/hp"
    assert 'userdata' not in files[SAVE]
    b = load_in(v, files)
    b.execute("H.logs = {}")
    assert b.eval("api.sv.load()") is True, b.eval("table.concat(H.logs, '\\n')")
    assert b.eval("api.sv.degraded") is None
    assert b.eval("fwdState()") == state_a, (b.eval("fwdState()"), state_a)
    assert b.eval("fwdLive()") == 1 and b.eval("SPAWNED_FWD") == 1, "um ator refeito, nenhum a mais"
    fb_ok = b.eval(r'''(function()
        local L = api.logi
        local fb = L.fwd[1]
        return fb.pt == api.points()[1] and fb.dep == fb.pt.dep and fb.pt.dep.fb == fb and #fb.exits >= api.CFG.FWD.minExits
            and fb.maxHp == 1725 and L.fwdAudit(fb) and fb.led.init.shirts == 12 and fb.led.init.rifle == 3
    end)()''')
    assert fb_ok
    # a base restaurada funciona: reforca por estoque
    b.execute(r'''CURSOR = nil; local P = api.points(); assert(api.logi.spawnSite("rifle", {X = P[1].X + 50, Y = P[1].Y}).kind == "fwd")''')
    # salvar de novo: a secao fwd e igual (ida e volta estavel)
    assert b.eval("api.sv.save()") is True
    f2 = {k: x for k, x in b.eval("FS.files").items()}
    b.globals().T1, b.globals().T2 = files[SAVE], f2[SAVE]
    assert b.eval("H.canon(api.sv.decode(T1).fwd) == H.canon(api.sv.decode(T2).fwd)"), "secao fwd estavel"
    return "ida/volta: mesmo estado (XYZ, yaw, hp, estoque por indice), 1 ator, saidas recalculadas, secao fwd estavel"


def t_repeticao(v):
    a, files = make_save(v)
    state_a = a.eval("fwdState()")
    b = load_in(v, files)
    for i in range(3):
        assert b.eval("api.sv.load()") is True, i
        assert b.eval("fwdState()") == state_a and b.eval("fwdLive()") == 1 and b.eval("#api.logi.fwd") == 1, "repeticao %d duplicou" % i
    assert b.eval("SPAWNED_FWD") == 1, "a base viva da mesma posicao e adotada, nao duplicada"
    # carga nova a cada vez (ator refeito do zero) tambem converge
    for i in range(3):
        files = {k: x for k, x in b.eval("FS.files").items()}
        b = load_in(v, files)
        assert b.eval("api.sv.load()") is True and b.eval("fwdState()") == state_a and b.eval("fwdLive()") == 1
        assert b.eval("api.sv.save()") is True
    return "3 continuacoes na mesma sessao + 3 cargas novas: sempre 1 base, mesmo estado, sem duplicar"


def t_posicao_invalida(v):
    a, files = make_save(v)
    # chao deixou de ser Landscape (telhado/prop) ou sumiu: Continuar recusado antes de tocar em nada
    b = load_in(v, files, "terrainClass = 'Warehouse'")
    refused(b, "sem chão Landscape na base avançada salva 1")
    assert b.eval("fwdLive()") == 0
    # base na posicao salva sem saidas livres
    b = load_in(v, files, "local P = {X = %s, Y = 0}; terrainZ = function(x, y) local d = math.sqrt((x - P.X)^2 + (y - P.Y)^2); if d > 700 and d < 900 then return nil end return 0 end"
                % a.eval("api.logi.fwd[1].X"))
    refused(b, "sem saídas livres")
    assert b.eval("fwdLive()") == 0
    # classe nao carrega
    b = load_in(v, files, "LOAD_FAIL = true")
    refused(b, "classe da base avançada não carregou")
    # mundo ja com a sessao propria: continua recusando e preserva
    b = load_in(v, files, "terrainClass = 'Warehouse'")
    b.execute("assert(api.logi.start()); api.combat.auto = true; local S = api.squad(); S[#S + 1] = H.unit('rifle', 10, 10)")
    refused(b, "sem chão Landscape")
    return "posicao/classe invalida: Continuar recusado no preflight, partida atual e arquivo preservados, nenhum ator criado"


def t_falha_de_spawn(v):
    # duas bases salvas; a 2a nao nasce: a 1a (estagio) e destruida, nada vaza, sessao preservada
    two = BUILD + r'''
L.fwdOrder = nil
assert(L.fwdBuild(mkPoint(9000, 3000, C.FRIENDLY_TEAM)), "2a base")
local f2 = api.points()[#api.points()].fb
f2.dep.shirts = 4; f2.led.init.shirts = 4
'''
    a, files = make_save(v, two)
    assert a.eval("#api.logi.fwd") == 2
    b = load_in(v, files, "FWD_FAIL_AT = 2")
    before = b.eval("fwdLive()")
    refused(b, "base avançada salva não foi refeita")
    assert b.eval("fwdLive()") == before == 0 and b.eval("#api.logi.fwd") == 0, "estagio desfeito"
    assert b.eval("H.live('BPForwardBase1_C')") == 0
    # sem a falha, as duas voltam
    b = load_in(v, files)
    assert b.eval("api.sv.load()") is True and b.eval("#api.logi.fwd") == 2 and b.eval("fwdLive()") == 2
    # a infraestrutura paga falha DEPOIS do estagio: as bases do estagio tambem sao desfeitas (rollback conjunto)
    a2 = H.persist_game(version=v)
    a2.execute("H.newWorld({trucks = 3}); assert(api.logi.deploy()); H.richMatch()")
    a2.execute(STATE)
    a2.execute(BUILD)
    assert a2.eval("api.sv.save()") is True
    files2 = {k: x for k, x in a2.eval("FS.files").items()}
    b = H.persist_game(version=v, files=files2)
    b.execute("H.newWorld({trucks = 3}); local S = api.squad(); S[1] = H.unit('rifle', 10, 10); H.spawnFailAt2 = 2")
    b.execute(STATE)
    b.execute("H.logs = {}")
    snap = b.eval("H.snapshotFiles()")
    assert b.eval("api.sv.load()") is False and b.eval("H.saw('infraestrutura salva não foi refeita')")
    assert b.eval("fwdLive()") == 0 and b.eval("#api.logi.fwd") == 0, "base do estagio desfeita junto com a infraestrutura"
    assert b.eval("H.sameFiles")(snap)
    return "spawn da 2a base falha: 1a desfeita, sessao e arquivo preservados; falha da infraestrutura depois do estagio desfaz as bases"


def t_save_adulterado(v):
    a, files = make_save(v)
    lua = H.persist_game(version=v)
    lua.execute(WORLD + "; H.richMatch()")
    lua.globals().TXT = files[SAVE]
    res = lua.execute(r'''
local sv = api.sv
local function fresh() local d = assert(sv.decode(TXT)); return d end
assert(sv.validate(fresh()), "save original valido")
local function bad(mut, expect)
    local d = fresh(); mut(d)
    local ok, why = sv.validate(d)
    assert(not ok, "aceitou: " .. expect)
    assert(tostring(why):find(expect, 1, true), expect .. " <> " .. tostring(why))
    assert(select(1, sv.parseSave("return " .. sv.ser(d))) == nil)
end
local R = function(d) return d.fwd.list[1] end
bad(function(d) R(d).extra = 1 end, "campo extra")
bad(function(d) d.fwd.extra = 1 end, "bases campo")
bad(function(d) d.fwd.version = 2 end, "versão futura")
bad(function(d) d.fwd.version = 0 end, "bases versão")
bad(function(d) R(d).pt = 9 end, "ponto")
bad(function(d) R(d).pt = 0 end, "ponto")
bad(function(d) R(d).pt = 1.5 end, "ponto")
bad(function(d) d.fwd.list[2] = {pt = 1, code = "ForwardBase1", x = 3000, y = 0, z = 0, yaw = 0, hp = 10} end, "ponto")      -- pt duplicado
bad(function(d) R(d).code = "Garrison" end, "código")
bad(function(d) R(d).hp = 0 end, "vida")
bad(function(d) R(d).hp = 99999 end, "vida")
bad(function(d) R(d).hp = 0/0 end, "tabela de dados")
bad(function(d) R(d).x = 1e12 end, "posição")
bad(function(d) R(d).yaw = "a" end, "posição")
bad(function(d) R(d).x = R(d).x + 900 end, "longe do ponto")
bad(function(d) d.logi.pts[1].a = 40 end, "teto")                                     -- estoque acima de 15 slots
bad(function(d) d.logi = nil; d.elogi = nil; d.enemy = nil end, "sem logística")
bad(function(d) d.points[1].owner = api.CFG.ENEMY_TEAM end, "em ponto inimigo")
bad(function(d) d.fwd.list = {1} end, "base 1")
bad(function(d) d.fwd = 5 end, "bases avançadas")
bad(function(d)
    d.fwd.list = {}
    for i = 1, 4 do d.fwd.list[i] = {pt = 1, code = "ForwardBase1", x = 3000, y = 0, z = 0, yaw = 0, hp = 10} end
end, "lista")
-- fwd = {} (zero bases) e aceito
local d = fresh(); d.fwd.list = {}
assert(sv.validate(d))
return "ok"
''')
    # carga com save adulterado: recusa e preserva
    bad_txt = files[SAVE].replace('["version"]=1', '["version"]=7', 1)
    assert bad_txt != files[SAVE]
    f = dict(files)
    f[SAVE] = bad_txt
    b = load_in(v, f)
    refused(b, "save inválido ou incompatível")
    return "21 adulteracoes recusadas (campo, versao, pt invalido/duplicado, vida, posicao, teto de slots, sem logistica, ponto inimigo, lista)"


def t_compat(v):
    a, files = make_save(v)
    # mod antigo (v3) le o save com fwd: recusa fail-closed, sem mudar nada
    b = H.persist_game(H.TEXT_V3, version=v, files=files)
    b.execute("H.newWorld({active = true, trucks = 3})")
    b.execute("H.logs = {}")
    assert b.eval("api.sv.load()") is False and b.eval("H.saw('campo desconhecido: fwd')")
    # v4 abre save de v3 (sem fwd)
    a3 = H.persist_game(H.TEXT_V3, version=v)
    a3.execute(WORLD + "; H.richMatch()")
    assert a3.eval("api.sv.save()") is True
    f3 = {k: x for k, x in a3.eval("FS.files").items()}
    assert "fwd" not in f3[SAVE]
    c = load_in(v, f3)
    assert c.eval("api.sv.load()") is True and c.eval("#api.logi.fwd") == 0
    # v4 sem bases: o save nao ganha a chave fwd (continua abrindo no v3)
    a4, f4 = make_save(v, "local L = api.logi; L.bmat = 1500")
    assert "fwd" not in f4[SAVE]
    d = H.persist_game(H.TEXT_V3, version=v, files=f4)
    d.execute("H.newWorld({active = true, trucks = 3})")
    assert d.eval("api.sv.load()") is True
    return "v3 recusa save com fwd ('campo desconhecido: fwd'); v4 abre save do v3; v4 sem bases grava save compativel com o v3"


def t_inativa_e_perdida(v):
    # base INATIVA (ponto neutro) e salva/restaurada com estoque; base DESTRUIDA nao e salva
    a, files = make_save(v, BUILD, extra=r'''
local P = api.points()
P[1].owner, P[1].prog = nil, 0
''')
    assert a.eval("#api.logi.fwd") == 1
    b = load_in(v, files)
    assert b.eval("api.sv.load()") is True
    assert b.eval("#api.logi.fwd") == 1 and b.eval("api.logi.fwd[1].dep.shirts") == 12 and b.eval("api.points()[1].owner") is None
    assert b.eval("api.logi.spawnCapable(api.logi.fwd[1].dep)") is False
    b.execute("local P = api.points(); P[1].owner, P[1].prog = api.CFG.FRIENDLY_TEAM, 1")
    assert b.eval("api.logi.spawnCapable(api.logi.fwd[1].dep)") is True, "recapturada: ativa de novo, estoque preservado"
    a2, files2 = make_save(v, BUILD, extra="api.logi.fwdLose(api.points()[1].fb, 'destruída')")
    assert "fwd" not in files2[SAVE]
    c = load_in(v, files2)
    assert c.eval("api.sv.load()") is True and c.eval("#api.logi.fwd") == 0 and c.eval("fwdLive()") == 0
    assert c.eval("api.points()[1].dep.shirts") == 0
    return "inativa: restaurada com estoque (reativa ao recapturar); destruida: nao entra no save"


def t_pedido_nao_salvo(v):
    a, files = make_save(v, "local L = api.logi; L.bmat = 0; L.fwdOrder = {pt = api.points()[1], cost = 300, t0 = clock}")
    assert "fwdOrder" not in files[SAVE] and "pedido" not in files[SAVE]
    b = load_in(v, files)
    assert b.eval("api.sv.load()") is True and b.eval("api.logi.fwdOrder") is None
    return "pedido pendente nao e salvo (cancela ao carregar)"


for v in ("lua54", "lua55"):
    H.case("[%s] ida e volta" % v, t_ida_e_volta, v)
    H.case("[%s] repeticao sem duplicar" % v, t_repeticao, v)
    H.case("[%s] posicao que nao valida mais" % v, t_posicao_invalida, v)
    H.case("[%s] falha de spawn / rollback conjunto" % v, t_falha_de_spawn, v)
    H.case("[%s] save adulterado" % v, t_save_adulterado, v)
    H.case("[%s] compatibilidade v3/v4" % v, t_compat, v)
    H.case("[%s] inativa e destruida" % v, t_inativa_e_perdida, v)
    H.case("[%s] pedido pendente nao e salvo" % v, t_pedido_nao_salvo, v)
H.finish("test_persistencia_bases")
