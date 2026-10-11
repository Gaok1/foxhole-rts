"""BASES_AVANCADAS: painel (logi.fwdLine pura <= 96 caracteres, estados; hudLine so leitura; linha do pedido pendente), teclas
(Shift+J registrada, sem colisao, fim-a-fim pelo `bindings`; J puro ignora disparo com modificador), HELP_TEXT, e analise estatica dos
unicos lugares que gravam camisas (estoque).

  cd /d/GitHub/foxhole-rts && PYTHONPATH=D:/tools/pylibs PYTHONDONTWRITEBYTECODE=1 \
      python dados/paralel/bases_avancadas/etapa2/test_painel_teclas.py
"""
import re
import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parent))
import harness_bases as H  # noqa: E402

PRE = r'''
newMatch()
local L, C = A.logi, A.CFG
local FR = C.FRIENDLY_TEAM
for _, tr in ipairs(L.trucks) do tr.state, tr.hp = 'idle', C.LOGI.hp end
L.base.shirts, L.base.rifle = 30, 0
'''


def t_fwdline(v):
    lua = H.new_game(version=v)
    lua.execute(PRE + r'''
local pt, fb = buildFwd(4000, 0)
-- estados
local d = fb.dep
stockFwd(fb, 12, 3);                  local s1 = L.fwdLine(d)
assert(s1 == "base A | camisas 12 | fuzis 3 | slots 3/15 | reforça: tudo", s1)
stockFwd(fb, 12, 0);                  local s2 = L.fwdLine(d); assert(s2:find("só sem fuzil (sem fuzis)", 1, true), s2)
stockFwd(fb, 0, 0); d.ammo = 6;       local s3 = L.fwdLine(d); assert(s3:find("reforça: NÃO (sem camisas)", 1, true) and s3:find("slots 6/15", 1, true), s3)
stockFwd(fb, 5, 5)
pt.owner, pt.prog = nil, 0;           local s4 = L.fwdLine(d); assert(s4:find("INATIVA (ponto neutro)", 1, true), s4)
pt.owner, pt.prog = FR, 1
local sb = L.fwdLine(L.base);         assert(sb == "base | camisas 30 | fuzis 0 | slots — | reforça: só sem fuzil (sem fuzis)", sb)
-- largura maxima
stockFwd(fb, 120, 100); d.ammo, d.medical = 15, 50
for _, s in ipairs({L.fwdLine(d), L.fwdLine(L.base), s2, s3, s4}) do assert(utf8.len(s) <= 96, utf8.len(s) .. ": " .. s) end
-- pura: nao muda estado
local snap = A.sv.ser({L.snapshot(), L.fwdSnapshot()})
for i = 1, 3 do L.fwdLine(d); L.fwdLine(L.base) end
assert(A.sv.ser({L.snapshot(), L.fwdSnapshot()}) == snap)
''')
    return "fwdLine: 4 estados, <= 96 caracteres, pura"


def t_hudline(v):
    lua = H.new_game(version=v)
    res = lua.execute(PRE + r'''
local pt, fb = buildFwd(4000, 0)
stockFwd(fb, 12, 3)
local snap = A.sv.ser({L.snapshot(), L.fwdSnapshot(), L.eSnapshot()})
local t = A.hudLine()
assert(A.sv.ser({L.snapshot(), L.fwdSnapshot(), L.eSnapshot()}) == snap, "hudLine so leitura")
assert(t:find("base | camisas 30 | fuzis 0 | slots — | reforça", 1, true), t)
assert(t:find("base A | camisas 12 | fuzis 3 | slots 3/15 | reforça: tudo", 1, true), t)
-- pedido pendente: a fabrica diz o que guarda (e a reserva do caminhao destruido aparece junto)
L.fwdOrder = {pt = mkPoint(7000, 0, FR), cost = 300, t0 = clock}
L.bmat, L.job = 140, nil
t = A.hudLine()
assert(t:find("Fábrica | guarda 300 bmat para base avançada em B (bmat 140)", 1, true), t)
L.trucks[2].state, L.trucks[2].hp = "dead", 0
t = A.hudLine()
assert(t:find("guarda 400 bmat para reconstruir caminhão e base avançada em B (bmat 140)", 1, true), t)
L.fwdOrder = nil
t = A.hudLine()
assert(t:find("guarda 100 bmat para reconstruir caminhão (bmat 140)", 1, true) and not t:find("base avançada em", 1, true), t)
-- linhas e largura do painel (gate visual do laboratorio)
L.trucks[2].state, L.trucks[2].hp = "idle", C.LOGI.hp
local lines, w = 0, 0
for l in A.hudLine():gmatch("[^\n]+") do lines = lines + 1; w = math.max(w, utf8.len(l)) end
return lines .. "x" .. w
''')
    return "hudLine: so leitura, linha por base, 'guarda 300 bmat para base avançada em B', combinado com caminhao; painel %s (linhas x largura)" % res


def t_teclas(v):
    lua = H.new_game(version=v)
    lua.execute(r'''
    -- Simular quadro apos entrada; comportamento assincrono tem regressao dedicada.
    for key, callback in pairs(bindings) do
        bindings[key] = function(...)
            callback(...)
            if A.rts.drainGameQueue then A.rts.drainGameQueue() end
        end
    end
    ''')
    lua.execute(PRE + r'''
assert(bindings["SHIFT+J"] and bindings["J"])
local nB = #A.points()
L.bmat = 1000
mkPoint(4000, 0, FR)
CURSOR = {X = 4000, Y = 0}
local n0 = #A.points()
-- J puro com modificador apertado (Shift): ignorado pelo mod (plain)
PC.IsInputKeyDown = function(self, k) return k.KeyName == "LeftShift" end
CURSOR = {X = 9000, Y = 3000}
bindings["J"]()
assert(#A.points() == n0, "J com Shift apertado nao cria ponto")
PC.IsInputKeyDown = function() return false end
bindings["J"]()
assert(#A.points() == n0 + 1, "J puro cria ponto")
-- Shift+J fim-a-fim: 1o toque informa, 2o constroi
CURSOR = {X = 4000, Y = 0}
bindings["SHIFT+J"]()
assert(#L.fwd == 0 and saw("Shift+J de novo"))
clock = clock + 1
bindings["SHIFT+J"]()
assert(#L.fwd == 1 and L.bmat == 700 and fwdLive() == 1)
-- RTS desligado: nada acontece
A.rts.active = false
L.fwd[1].pt.fb = nil; L.fwd = {}
bindings["SHIFT+J"](); clock = clock + 1; bindings["SHIFT+J"]()
assert(#L.fwd == 0)
A.rts.active = true
-- Assalto / sem logistica: mensagem, nada construido
A.combat.mode = "assault"; LOG = {}
bindings["SHIFT+J"]()
assert(saw("fora do Assalto") and #L.fwd == 0)
''')
    # lista de teclas: Shift+J nao esta em GAME_KEYS (parse do proprio tools/test_orders.py) e nao colide com teclas do mod
    src = (H.ROOT / "tools/test_orders.py").read_text(encoding="utf-8")
    game = set(re.findall(r'"([A-Z0-9_+]+)"', src[src.index("GAME_KEYS = {"):src.index("# accepted overlaps")]))
    assert "SHIFT+J" not in game and "J" not in game, "J / Shift+J livres no jogo"
    reg = set(lua.eval("(function() local t = {} for k in pairs(bindings) do t[#t+1] = k end return table.concat(t, ',') end)()").split(","))
    assert "SHIFT+J" in reg and "J" in reg
    mods = sorted(k for k in reg if k.endswith("+J"))
    assert mods == ["SHIFT+J"], mods
    return "Shift+J registrada e livre (GAME_KEYS %d teclas); J ignora disparo com modificador; fim-a-fim 2 toques; RTS desligado/Assalto nao constroem" % len(game)


def t_help(v):
    lua = H.new_game(version=v)
    txt = lua.eval("api.help()")
    assert "Shift+J: base avançada (300 bmat, 2 toques)" in txt
    assert "logística: nasce na base ou numa base avançada" in txt
    return "HELP_TEXT cita Shift+J e o novo local de nascimento"


def t_estatica(v):
    t = H.TEXT_V4
    cur, res = None, {}
    for i, l in enumerate(t.split("\n"), 1):
        m = re.match(r"(?:local\s+)?function\s+([\w.:]+)", l)
        if m:
            cur = m.group(1)
        if re.search(r"\.shirts(\s*,\s*[\w.]+)*\s*=(?!=)", l) and not l.strip().startswith("--"):
            res.setdefault(cur, []).append(i)
    allowed = {"recruit": "ramo legado/Assalto (mao de obra)", "logi.needs": "tabela de resultado (nao e estoque)",
               "logi.snapshot": "monta o save", "logi.restore": "carrega o save", "logi.fwdLose": "contador do razao (perdido)",
               "logi.spawnCommit": "UNICO debito de nascimento"}
    extra = set(res) - set(allowed)
    assert not extra, "atribuicao de .shirts fora do esperado: %s" % {k: res[k] for k in extra}
    # ramo logistico do recruit nao debita: logi.recruit nao tem atribuicao
    assert "logi.recruit" not in res
    # o ramo logistico nunca toca em economy.manpower
    a = t.index("function logi.recruit(")
    b = t.index("\nend\n", a)
    assert "manpower" not in t[a:b]
    return "estoque de camisas so e gravado em: " + ", ".join(sorted(res))


for v in ("lua54", "lua55"):
    H.case("[%s] logi.fwdLine" % v, t_fwdline, v)
    H.case("[%s] hudLine" % v, t_hudline, v)
    H.case("[%s] teclas Shift+J" % v, t_teclas, v)
    H.case("[%s] HELP_TEXT" % v, t_help, v)
H.case("analise estatica: unicos lugares que gravam camisas", t_estatica, "lua54")
H.finish("test_painel_teclas")
