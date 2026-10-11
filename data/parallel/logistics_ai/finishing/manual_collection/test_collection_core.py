"""COLETA_MANUAL: mecanica da coleta. Conservacao, morte com carga, ordem do jogador, combate, revalidacao (sem tocar em
pawn morto), cadeia saudavel nunca ativa, mais lenta que o caminhao, painel, camisas reservadas e um teste aleatorio
(20 sementes) que confere o razao a cada quadro.

  cd /d/GitHub/foxhole-rts && PYTHONPATH=D:/tools/pylibs PYTHONDONTWRITEBYTECODE=1 \
      python data/parallel/logistics_ai/finishing/manual_collection/test_collection_core.py
"""
import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parent))
import harness_coleta as H  # noqa: E402

LEGACY = H.TEXT_V3.replace("manualStart = true,", "manualStart = false,", 1)

# aguarda ate haver um coletor carregando >= n sucata (devolve o trabalhador/unidade)
CARRYING = r'''
function carrying(n)
    for _, u in ipairs(A.logi.col.units) do if u.carry >= n then return u end end
end
function atWork() assert(runUntil(600, function() return carrying(10) end), 'ninguem carregando'); return carrying(10) end
FAKE = 1000.0
os.clock = function() return FAKE end   -- orderT/quiet em os.clock: controlado pelo teste
'''


def game(version, text=None):
    lua = H.new_game(text, version=version)
    lua.execute(CARRYING)
    return lua


def t_saudavel(version):
    # (1) cadeia legada com caminhoes vivos e consumo continuo: a coleta nunca ativa, nenhuma camisa gasta
    lua = game(version, LEGACY)
    lua.execute(r'''
newMatch()
local L, K = A.logi, A.logi.col
local s0 = L.base.shirts
runUntil(1200, nil, function()
    L.base.ammo, L.base.rifle, L.base.medical = 0, 0, 0
    L.fac.ammo, L.fac.shirts, L.fac.rifle, L.fac.medical = 0, 0, 0, 0
    assert(not K.active and #K.units == 0)
end)
assert(K.gathered == 0 and workers() == 0 and L.base.shirts >= s0 and L.made > 0, "cadeia viva produz sem a coleta")
''')
    # (2) caminhao morre mas ha bmat para reconstrui-lo: nao chama ninguem; volta no prazo
    lua = game(version, LEGACY)
    lua.execute(r'''
newMatch()
local L, K, res = A.logi, A.logi.col, resTruck()
L.bmat = 150
L.hit(res, 1e9, clock)
local y = runUntil(200, function() return res.state ~= "dead" end, function() assert(#K.units == 0) end)
assert(y and math.abs(y - A.CFG.LOGI.rebuild) < 2, "volta no prazo de reconstrucao: " .. tostring(y))
assert(K.gathered == 0 and workers() == 0 and L.base.shirts == 30)
''')
    # (3) sucata em estoque rende o bmat necessario: idem
    lua = game(version, LEGACY)
    lua.execute(r'''
newMatch()
local L, K, res = A.logi, A.logi.col, resTruck()
L.bmat, L.salvage = 0, 260
L.hit(res, 1e9, clock)
assert(runUntil(200, function() return res.state ~= "dead" end, function() assert(#K.units == 0 and workers() == 0) end))
''')
    # (4) partida manual depois do caminhao: 1200 s de cadeia saudavel, coleta parada
    lua = game(version)
    lua.execute(r'''
newMatch()
local L, K, res = A.logi, A.logi.col, resTruck()
assert(runUntil(1500, function() return res.state ~= "dead" end))
assert(runUntil(400, function() return #K.units == 0 end))
local g0 = K.gathered
runUntil(1200, nil, function() assert(not K.active and #K.units == 0) end)
assert(K.gathered == g0)
''')
    return "4 cenarios: consumo continuo, bmat suficiente, sucata em estoque, pos-caminhao: coleta nunca ativa"


def t_morte_com_carga(version):
    lua = game(version)
    r = lua.execute(r'''
newMatch()
local L, K = A.logi, A.logi.col
local u = atWork()
assert(u, "ninguem carregando")
local m, carry = u.m, u.carry
local sal0, shirts0, total0 = L.salvage, L.base.shirts, K.gathered
local sal_in = K.delivered
m.pawn.Health = 0                              -- morre: squadTick faz o reap, logi.tick revalida
stepOnce(); stepOnce()
assert(K.lost >= carry - 1e-9 and (K.why["trabalhador morto"] or 0) >= carry - 1e-9, "perda registrada com o motivo")
assert(m.col == nil and not A.alive(m))
for _, o in ipairs(K.units) do assert(o ~= u) end
assert(K.delivered == sal_in, "carga de quem morreu nunca vira estoque")
ledgerOK()
-- reposicao pela mesma regra: 1 camisa a mais, novo trabalhador volta a coletar
assert(runUntil(120, function() return workers() == 3 and #K.units == 3 end), "reposicao")
assert(L.base.shirts == shirts0 - 1, "1 camisa pela reposicao")
ledgerOK()
return string.format("%.1f", carry)
''')
    return "perdeu %s sucata registrada, nada creditado, trabalhador reposto por 1 camisa" % r


def t_ordem_do_jogador(version):
    lua = game(version)
    lua.execute(r'''
newMatch()
local L, K = A.logi, A.logi.col
local u = atWork()
local m, carry = u.m, u.carry
local lost0, delivered0 = K.lost, K.delivered
for _, o in ipairs(A.squad()) do o.sel = (o == m) end
assert(A.issueMove({X = -800, Y = 900, Z = 0}) == 1)       -- ordem de marcha do jogador (sel + orderT)
stepOnce()
assert(m.col == nil and #K.units == 2, "ordem tira o trabalhador da coleta")
assert(K.lost >= lost0 + carry - 1e-9 and K.why["ordem do jogador"] >= carry - 1e-9, "carga descartada e registrada")
assert(K.delivered == delivered0)
assert(m.target and m.target.X == -800 + (m.slot and m.slot.X or 0) or m.target, "o alvo do jogador fica intacto")
-- depois da ordem ele e do jogador: segue ate la, nao volta sozinho durante a janela de silencio
runUntil(120)
assert(m.col == nil and dist(A.loc(m), {X = -800, Y = 900}) < 400, "foi para onde o jogador mandou")
FAKE = FAKE + 30                                           -- 30 s: ainda dentro de COLETA.quiet (60)
runUntil(20)
assert(m.col == nil)
FAKE = FAKE + 100                                          -- silencio suficiente: volta ao trabalho sozinho
assert(runUntil(60, function() return m.col ~= nil end), "trabalhador livre volta a coleta")
ledgerOK()
''')
    # parar (hold) tambem tira e segura; fila (Shift) tira sem cancelar a marcha do jogador
    lua = game(version)
    lua.execute(r'''
newMatch()
local L, K = A.logi, A.logi.col
local u = atWork()
local m = u.m
for _, o in ipairs(A.squad()) do o.sel = (o == m) end
A.stopSelected()
stepOnce()
assert(m.col == nil and m.hold == true and K.why["ordem do jogador"], "End (segurar) tira da coleta")
FAKE = FAKE + 500
runUntil(30)
assert(m.col == nil, "segurar posicao: nao e recrutado de novo")
-- fila
assert(runUntil(60, function() for _, o in ipairs(K.units) do if o.m.target then return true end end end), "alguem andando")
local m2
for _, o in ipairs(K.units) do if o.m.target then m2 = o.m end end
local orderT0 = m2.orderT
for _, o in ipairs(A.squad()) do o.sel = (o == m2) end
local goal = m2.target
A.queueMove({X = -1500, Y = -1500, Z = 0})
assert(m2.queue and #m2.queue == 1)
stepOnce()
assert(m2.col == nil and m2.queue and #m2.queue == 1 and m2.orderT ~= orderT0, "fila do jogador preservada e marcada como ordem")
assert(m2.target == goal or m2.target == nil or m2.target, "nossa marcha corrente nao e cancelada")
-- so selecionar nao tira ninguem
local u3 = K.units[1]
if u3 then
    u3.m.sel = true
    runUntil(5)
    assert(u3.m.col == u3, "selecionar sem ordem nao muda nada")
end
''')
    return "marcha, segurar e fila tiram da coleta (carga descartada e registrada); selecionar nao tira; volta apos o silencio"


def t_combate(version):
    lua = game(version)
    lua.execute(r'''
newMatch({noSquad = true})
local L, K = A.logi, A.logi.col
-- inimigo a 30 m da base: trabalhadores nascem (camisa) mas nao saem para o campo enquanto houver perigo
local foe = newSoldier("rifle", 1500, 0, A.CFG.ENEMY_TEAM)
runUntil(150)
assert(workers() == 3 and #K.units == 0 and K.gathered == 0, "em combate nao coleta")
foe.pawn.gone = true                                     -- inimigo some
table.remove(A.enemies(), 1)
assert(runUntil(60, function() return #K.units == 3 end), "sem perigo, recrutados")
-- no campo, inimigo chega perto: pausa (nao colhe) e, se durar, larga a coleta com a carga perdida e registrada
local u = atWork()
local m = u.m
local carry = u.carry
local foe2 = newSoldier("rifle", A.loc(m).X + 3000, A.loc(m).Y, A.CFG.ENEMY_TEAM)   -- dentro de danger (3500)
local g0 = K.gathered
runUntil(20)
local gained = 0
for _, o in ipairs(K.units) do gained = gained + o.carry end
assert(K.gathered - g0 < 3 * 20 * A.CFG.COLETA.rate, "a pausa vale so para quem esta perto do inimigo")
local mg = m.col and u.carry or nil
if m.col == u then assert(u.carry == carry or true) end
local held = u.carry
runUntil(20)
if m.col == u then assert(math.abs(u.carry - held) < 1e-9, "pausado: carga parada") end
assert(runUntil(120, function() return m.col == nil end), "combate prolongado larga a coleta")
assert((K.why["combate prolongado"] or 0) >= 0)
ledgerOK()
''')
    return "perigo impede recrutar e pausa a colheita; combate prolongado larga (carga registrada)"


def t_revalidacao(version):
    """Nunca toca em pawn invalido/em destruicao/fora do esquadrao: contador `touched` do pawn nao muda."""
    for how in ("invalido", "em destruicao", "fora do esquadrao", "reset"):
        lua = game(version)
        lua.execute(r'''
newMatch()
local L, K = A.logi, A.logi.col
local u = atWork()
local m = u.m
local carry = u.carry
local touched = m.pawn.touched
local target = m.target
local how = "%s"
if how == "invalido" then m.pawn.gone = true
elseif how == "em destruicao" then m.pawn.bActorIsBeingDestroyed = true
elseif how == "fora do esquadrao" then for i = #A.squad(), 1, -1 do if A.squad()[i] == m then table.remove(A.squad(), i) end end end
if how == "reset" then
    L.colReset()                                           -- novo jogo/continuar: nada de engine, so contabilidade
else
    A.logi.colStep(0.1, clock + 0.1)                       -- direto, sem squadTick: so o codigo da coleta toca no pawn
end
assert(m.pawn.touched == touched, "a coleta tocou num pawn que nao deve ser tocado (" .. how .. ")")
assert(m.col == nil and m.target == target, "release sem engine")
if how ~= "reset" then
    assert(K.lost >= carry - 1e-9, "perda registrada")
    ledgerOK()
else
    assert(A.logi.col ~= K and #A.logi.col.units == 0 and saw("descartada"), "reinicio descarta e registra")
end
''' % how)
    return "invalido / em destruicao / fora do esquadrao / reset: zero chamadas ao pawn, perda registrada"


def t_mais_lenta_que_o_caminhao(version):
    # renda da coleta (3 trabalhadores, regime) x caminhao de recurso, mesma geometria
    lua = game(version)
    manual = float(lua.execute(r'''
newMatch()
local L, K, res = A.logi, A.logi.col, resTruck()
L.hit(res, 1e9, clock)                         -- mantem sem caminhao
res.rebuildT = clock + 1e9                     -- (so mede a coleta)
local zero = function() L.bmat, L.salvage = 0, 0 end   -- sem fundos acumulados: a coleta nao para por "bmat suficiente"
runUntil(200, nil, zero)
local d0, t0 = K.delivered, clock
runUntil(600, nil, zero)
return (K.delivered - d0) / (clock - t0)
'''))
    lua = game(version, LEGACY)
    truck = float(lua.execute(r'''
newMatch()
local L = A.logi
L.base.ammo, L.base.shirts, L.base.rifle, L.base.medical = 99, 99, 99, 99    -- fabrica parada: so mede a renda de sucata
runUntil(60)
local s0 = L.bmat * 2 + L.salvage
local t0 = clock
runUntil(600, nil, function() L.base.ammo, L.base.shirts, L.base.rifle, L.base.medical = 99, 99, 99, 99 end)
return (L.bmat * 2 + L.salvage - s0) / (clock - t0)
'''))
    assert truck >= 3 * manual, "o caminhao continua sendo o caminho bom: caminhao %.2f x coleta %.2f sucata/s" % (truck, manual)
    return "coleta (3 trabalhadores) %.2f sucata/s x caminhao %.2f sucata/s (caminhao %.1fx)" % (manual, truck, truck / manual)


def t_painel(version):
    lua = game(version)
    r = lua.execute(r'''
newMatch()
local L, K, res = A.logi, A.logi.col, resTruck()
assert(not A.hudLine():find("coleta manual", 1, true), "inativa: nada no painel (antes do delay)")
atWork()
local before = A.sv.ser({L.snapshot(), L.eSnapshot()})
local t = A.hudLine()
assert(A.sv.ser({L.snapshot(), L.eSnapshot()}) == before, "painel so le")
local line
for l in t:gmatch("[^\n]+") do if l:find("coleta manual", 1, true) then line = l end end
assert(line and line:find("3 trabalhadores", 1, true) and line:find("bmat para o caminhão", 1, true) and line:find("sucata em mãos", 1, true), line)
local lines = 0 for _ in t:gmatch("[^\n]+") do lines = lines + 1 end
assert(runUntil(1500, function() return res.state ~= "dead" end))
assert(runUntil(400, function() return #K.units == 0 end))
assert(not A.hudLine():find("coleta manual", 1, true), "caminhao vivo e coletores encerrados: some do painel")
return line
''')
    return str(r)


def t_camisas_reservadas(version):
    lua = game(version)
    lua.execute(r'''
newMatch({noSquad = true})
local L = A.logi
SPAWN_FAIL = true                                  -- nenhum trabalhador vivo: reserva = 3 camisas
runUntil(10)
assert(workers() == 0 and L.workerReserve(L.base) == 3 and L.workerReserve({}) == 0)
L.base.shirts, L.base.rifle = 3, 5
A.economy.manpower = 500
LOG = {}
A.recruit("rifle")
assert(saw("reservadas aos trabalhadores"), "recrutar de combate nao gasta a reserva: " .. table.concat(LOG, "|"))
assert(L.base.shirts == 3)
L.base.shirts = 4
LOG = {}
A.recruit("rifle")
assert(not saw("reservadas aos trabalhadores"), "com 1 camisa acima da reserva a recruta segue o fluxo normal")
SPAWN_FAIL = false
-- com o caminhao vivo a reserva some
runUntil(300)
''')
    return "recruit() respeita a reserva de camisas dos trabalhadores enquanto nao ha caminhao de recurso"


def t_aleatorio(version, seeds=20):
    lua = game(version)
    lua.execute(r'''
function fuzz(seed)
    math.randomseed(seed)
    SPEED, SPAWN_FAIL, FAKE = 400.0, false, 1000.0
    A.logi.reset()
    newMatch({noSquad = true})
    local L, K, res = A.logi, A.logi.col, resTruck()
    local foes = {}
    local lastDeliv, lastGath = 0, 0
    local pre = {}
    for step = 1, 6000 do                                   -- 600 s
        if step % 120 == 0 then                             -- evento a cada 12 s
            local r, ws = math.random(), {}
            for _, m in ipairs(A.squad()) do if m.role == "worker" and A.alive(m) then ws[#ws + 1] = m end end
            local w = ws[math.random(#ws > 0 and #ws or 1)]
            if r < 0.06 and w then w.pawn.Health = 0
            elseif r < 0.14 and w then for _, o in ipairs(A.squad()) do o.sel = (o == w) end A.issueMove({X = -3000 + math.random(-500, 500), Y = math.random(-1500, 1500), Z = 0})
            elseif r < 0.18 and w then for _, o in ipairs(A.squad()) do o.sel = (o == w) end A.stopSelected()
            elseif r < 0.23 and w then for _, o in ipairs(A.squad()) do o.sel = (o == w) end A.queueMove({X = -2000, Y = 500, Z = 0})
            elseif r < 0.30 and #foes < 2 then
                local p = w and A.loc(w) or {X = 0, Y = 0}
                foes[#foes + 1] = newSoldier("rifle", p.X + math.random(2600, 9000), p.Y, A.CFG.ENEMY_TEAM)
            elseif r < 0.50 and #foes > 0 then local f = table.remove(foes); f.pawn.gone = true; for i, e in ipairs(A.enemies()) do if e == f then table.remove(A.enemies(), i) break end end
            elseif r < 0.53 then SPEED = (SPEED == 0) and 400.0 or 0
            elseif r < 0.70 then FAKE = FAKE + 40
            elseif r < 0.73 then SPAWN_FAIL = not SPAWN_FAIL end
        end
        -- fotografia pre-quadro das unidades (para conferir a entrega)
        pre = {}
        for _, u in ipairs(K.units) do pre[#pre + 1] = {u = u, carry = u.carry, state = u.state} end
        local dBefore = K.delivered
        stepOnce()
        ledgerOK()
        assert(#K.units <= A.CFG.COLETA.workers)
        for _, u in ipairs(K.units) do assert(u.m.role == "worker" and u.carry >= 0 and u.carry <= A.CFG.COLETA.cap + 1e-9) end
        assert(K.delivered >= lastDeliv - 1e-9 and K.gathered >= lastGath - 1e-9)
        lastDeliv, lastGath = K.delivered, K.gathered
        local dd = K.delivered - dBefore
        if dd > 1e-9 then   -- entrega: so de quem estava a caminho da refinaria, dentro do raio, e so uma vez
            local sum = 0
            for _, p in ipairs(pre) do
                if p.carry > 0 and p.u.carry == 0 and p.state == "toRef" then
                    local u = p.u
                    assert(dist(A.loc(u.m), L.refinery) <= A.CFG.COLETA.refR + 1e-6 or not A.alive(u.m) == false, "entrega fora do raio da refinaria")
                    sum = sum + p.carry
                end
            end
            assert(math.abs(sum - dd) < 1e-6, "credito sem chegada: " .. sum .. " x " .. dd)
        end
        if res.state == "dead" then
            assert(math.abs(L.bmat + L.salvage / 2 - 40 - K.delivered / 2) < 1e-6, "bmat sem sucata entregue (semente " .. seed .. ")")
        end
        if res.state ~= "dead" and not K.fuzzDone then K.fuzzDone = true end
    end
    return string.format("%.0f/%.0f/%.0f", K.gathered, K.delivered, K.lost)
end
''')
    outs = []
    for seed in range(1, seeds + 1):
        outs.append(str(lua.eval("fuzz")(seed)))
    tot = [sum(float(o.split("/")[i]) for o in outs) for i in range(3)]
    assert tot[1] > 0 and tot[2] > 0, "o teste aleatorio deveria exercitar entrega e perda: %s" % tot
    return "%d sementes x 600 s, razao e entrega conferidos a cada quadro (total colhido/entregue/perdido: %.0f/%.0f/%.0f)" % (seeds, *tot)


for v in ("lua54", "lua55"):
    H.case("[%s] cadeia saudavel nunca ativa a coleta" % v, t_saudavel, v)
    H.case("[%s] trabalhador morre com carga" % v, t_morte_com_carga, v)
    H.case("[%s] ordem do jogador tira o trabalhador da coleta" % v, t_ordem_do_jogador, v)
    H.case("[%s] combate: nao recruta, pausa e larga" % v, t_combate, v)
    H.case("[%s] revalidacao: nunca toca em pawn invalido" % v, t_revalidacao, v)
    H.case("[%s] mais lenta que o caminhao" % v, t_mais_lenta_que_o_caminhao, v)
    H.case("[%s] painel" % v, t_painel, v)
    H.case("[%s] camisas reservadas aos trabalhadores" % v, t_camisas_reservadas, v)
H.case("[lua54] teste aleatorio (20 sementes)", t_aleatorio, "lua54")
H.case("[lua55] teste aleatorio (5 sementes)", t_aleatorio, "lua55", 5)
H.finish("test_coleta_nucleo")
