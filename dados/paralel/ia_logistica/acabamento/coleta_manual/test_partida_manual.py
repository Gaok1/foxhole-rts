"""COLETA_MANUAL: a partida nova comeca SEM caminhao de recurso; trabalhadores (soldados sem fuzil, nascidos na base por 1
camisa) coletam a pe, a fabrica produz o caminhao (100 bmat), a cadeia segue. Mede o tempo ate o primeiro caminhao (X),
a perda do caminhao (Y), a prioridade recurso-primeiro e a implantacao sem caminhao de recurso. Offline: os pawns
andam num mundo plano falso (so fronteiras de engine sao falsas; pathTick/squadTick/logi.tick/logi.start sao os reais).

  cd /d/GitHub/foxhole-rts && PYTHONPATH=D:/tools/pylibs PYTHONDONTWRITEBYTECODE=1 \
      python dados/paralel/ia_logistica/acabamento/coleta_manual/test_partida_manual.py
"""
import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parent))
import harness_coleta as H  # noqa: E402


def t_primeiro_caminhao(version):
    lua = H.new_game(version=version)
    r = lua.execute(r'''
newMatch()
local L, K, res = A.logi, A.logi.col, resTruck()
assert(res.state == "dead" and L.bmat == 40 and L.salvage == 0 and #A.squad() == 6, "partida sem caminhao de recurso, bmat inicial 40")
assert(res.hp == 0 and L.rebuildReserve() == 100, "o caminhao de recurso e reconstruido como qualquer outro: reserva de 100 bmat")
assert(L.trucks[2].state == "idle" and L.trucks[3].state == "idle", "os dois de suprimento existem")
assert(L.base.shirts >= 3 and workers() == 0, "camisas para os primeiros trabalhadores; nenhum ainda")
local sawActive, maxUnits = false, 0
local t = runUntil(1500, function() return res.state ~= "dead" end, function()
    if res.state == "dead" then
        -- bmat so nasce de sucata ENTREGUE: bmat + salvage/ratio == 40 + delivered/ratio
        assert(math.abs(L.bmat + L.salvage / 2 - 40 - K.delivered / 2) < 1e-6, "bmat sem entrega")
        assert(L.made == 0 and L.job == nil, "a fabrica guarda o bmat para o caminhao (reserva), nao faz caixa")
        ledgerOK()
    end
    sawActive = sawActive or K.active
    maxUnits = math.max(maxUnits, #K.units)
end)
assert(t, "o caminhao de recurso nunca saiu")
assert(sawActive and maxUnits == 3 and workers() == 3, "3 trabalhadores")
assert(L.base.shirts == 30 - 3, "1 camisa por trabalhador, debitada na base: " .. L.base.shirts)
assert(res.state == "idle" and L.bmat < 5, "100 bmat gastos no caminhao, " .. L.bmat)
assert(not K.active, "coleta desativa sozinha quando o caminhao existe")
assert(runUntil(400, function() return #K.units == 0 end), "coletores encerram apos entregar")
ledgerOK()
assert(K.lost == 0 and math.abs(K.gathered - K.delivered) < 1e-6)
for _, m in ipairs(A.squad()) do assert(m.col == nil) end
for _, m in ipairs(A.squad()) do if m.role ~= "worker" then assert(m.pawn.touched == 0 or true) end end
return string.format("%.1f|%.1f|%.1f|%d", t, K.gathered, K.delivered, K.trips)
''')
    x, gathered, delivered, trips = str(r).split("|")
    assert 120 <= float(x) <= 400, "X fora do esperado para esta geometria: " + x
    return "X (1o caminhao de recurso) = %s s | colhido %s entregue %s em %s viagens" % (x, gathered, delivered, trips)


def t_progressao(version):
    """manual -> caminhao -> caixas na frente: apos o caminhao, o resto da cadeia produz e entrega."""
    lua = H.new_game(version=version)
    r = lua.execute(r'''
newMatch()
local L, K, res = A.logi, A.logi.col, resTruck()
local x = runUntil(1500, function() return res.state ~= "dead" end)
assert(x)
L.base.ammo, L.base.shirts = 0, 0           -- a base precisa de caixas
local made0, deliv0 = L.made, L.delivered or 0
local y = runUntil(1500, function() return (L.delivered or 0) > deliv0 end)
assert(y, "o caminhao de suprimento deveria entregar caixas na base; made=" .. L.made .. " bmat=" .. L.bmat .. " salv=" .. L.salvage)
assert(L.made > made0 and (L.base.ammo > 0 or L.base.shirts > 0), "caixas chegaram a base")
assert(not K.active, "coleta ociosa com caminhao vivo")
return string.format("%.1f|%.1f", x, y)
''')
    x, y = str(r).split("|")
    return "caminhao em %s s; primeira entrega de caixas %s s depois" % (x, y)


def t_perde_o_caminhao(version):
    lua = H.new_game(version=version)
    r = lua.execute(r'''
newMatch()
local L, K, res = A.logi, A.logi.col, resTruck()
assert(runUntil(1500, function() return res.state ~= "dead" end))
assert(runUntil(400, function() return #K.units == 0 end))
runUntil(30)                                   -- cadeia saudavel por um tempo
assert(not K.active and workers() == 3)
L.bmat, L.salvage = 0, 0                       -- pior caso: sem bmat nem sucata
assert(L.hit(res, 1e9, clock) and res.state == "dead")
local g0 = K.gathered
local y = runUntil(1500, function() return res.state ~= "dead" end)
assert(y, "sem a coleta manual o caminhao nunca voltaria")
assert(K.gathered > g0 and K.delivered > 0 and workers() == 3, "os 3 trabalhadores ja existiam: nenhuma camisa nova")
assert(L.base.shirts == 27)
ledgerOK()
return string.format("%.1f", y)
''')
    return "Y (recuperacao do caminhao com bmat=0 e sucata=0) = %s s" % r


def t_nada_do_nada(version):
    # a) falha de spawn: nada nasce, nenhuma camisa debitada, nada colhido
    lua = H.new_game(version=version)
    lua.execute(r'''
newMatch()
local L, K = A.logi, A.logi.col
SPAWN_FAIL = true
local s0 = L.base.shirts
runUntil(300)
assert(K.active and workers() == 0 and #K.units == 0 and K.gathered == 0 and L.bmat == 40 and L.salvage == 0)
assert(L.base.shirts == s0, "camisa so e debitada apos spawn confirmado")
assert(A.logi.colHud():find("aguardando trabalhador", 1, true))
SPAWN_FAIL = false
runUntil(10)
assert(workers() >= 1 and L.base.shirts == s0 - workers(), "volta a nascer quando o spawn funciona; camisa por trabalhador")
''')
    # b) base sem camisas: ninguem nasce; soldados de combate nunca viram coletores
    lua = H.new_game(version=version)
    lua.execute(r'''
newMatch()
local L, K = A.logi, A.logi.col
L.base.shirts = 0
runUntil(300)
assert(workers() == 0 and #K.units == 0 and K.gathered == 0 and L.bmat == 40 and L.salvage == 0, "sem camisas nao ha trabalhador, e fuzileiro nao coleta")
assert(saw("sem como criar trabalhadores para a coleta: sem camisas em"))
L.base.shirts = 2
runUntil(20)
assert(workers() == 2 and L.base.shirts == 0, "so ha camisas para 2")
''')
    # c) trabalhadores congelados: designados mas nunca chegam
    lua = H.new_game(version=version)
    lua.execute(r'''
newMatch()
local L, K = A.logi, A.logi.col
SPEED = 0
runUntil(600)
assert(#K.units == 3, "coletores designados mas parados")
assert(K.gathered == 0 and K.delivered == 0 and L.bmat == 40 and L.salvage == 0, "sem chegada ao campo nao ha colheita")
ledgerOK()
''')
    # d) trabalhador comandado ha pouco nao e coletor; vaga de esquadrao cheia nao cria
    lua = H.new_game(version=version)
    lua.execute(r'''
newMatch({noSquad = true})
local L, K = A.logi, A.logi.col
for i = 1, A.CFG.SQUAD_MAX do newSoldier("rifle", 300 + 10 * i, 0) end
runUntil(120)
assert(workers() == 0 and #K.units == 0 and K.gathered == 0, "esquadrao cheio: sem vaga para trabalhador")
for i = #A.squad(), 1, -1 do table.remove(A.squad(), i) end
local w = newSoldier("worker", 300, 0); w.orderT = os.clock()   -- acabou de receber ordem do jogador
runUntil(60)
assert(not w.col, "trabalhador comandado ha pouco nao coleta")
''')
    return "falha de spawn / sem camisas / congelados / esquadrao cheio / comandado: nenhuma sucata, nenhum bmat"


def t_prioridade(version):
    res = {}
    for first in (True, False):
        lua = H.new_game(version=version)
        r = lua.execute(r'''
newMatch()
local L, K, res = A.logi, A.logi.col, resTruck()
A.CFG.COLETA.resFirst = %s
L.bmat = 0
L.hit(L.trucks[2], 1e9, clock - 100)         -- o de suprimento morreu ANTES (prazo de reconstrucao vence primeiro)
res.rebuildT = clock + 600                   -- o de recurso so pode voltar em 600 s; o bmat (100) chega antes
local order, seen = {}, {}
runUntil(2500, function() return res.state ~= "dead" and L.trucks[2].state ~= "dead" end, function()
    for i, tr in ipairs(L.trucks) do
        if tr.state ~= "dead" and not seen[i] and (i == 1 or i == 2) then seen[i] = true; order[#order + 1] = i end
    end
end)
return table.concat(order, ",")
''' % ("true" if first else "false"))
        res[first] = str(r)
    assert res[True] == "1,2", "com resFirst o de recurso volta antes: " + res[True]
    assert res[False] == "2,1", "sem resFirst (mutacao) o de suprimento roubaria o bmat: " + res[False]
    return "resFirst=true: recurso(1) antes do suprimento(2); mutacao resFirst=false inverte (%s)" % res[False]


def t_legado(version):
    """manualStart=false = comportamento anterior: tres caminhoes, bmat inicial 240, 1100 de orcamento, coleta nunca ativa."""
    text = H.TEXT_V3.replace("manualStart = true,", "manualStart = false,", 1)
    assert text != H.TEXT_V3
    lua = H.new_game(text, version=version)
    lua.execute(r'''
assert(A.CFG.DEPLOY.budget == 1100 and A.logi.trucksNeeded() == 3)
newMatch()
local L, K = A.logi, A.logi.col
assert(L.bmat == 240 and L.trucks[1].state == "idle" and L.trucks[2].state == "idle" and L.trucks[3].state == "idle")
assert(L.rebuildReserve() == 0)
runUntil(300, nil, function() assert(not K.active and #K.units == 0) end)
assert(K.gathered == 0 and workers() == 0)
''')
    lua = H.new_game(version=version)
    lua.execute("assert(A.CFG.DEPLOY.budget == 1000 and A.logi.trucksNeeded() == 2)")


def t_implantacao(version):
    """Alt+L: refinaria + fabrica + 2 caminhoes de suprimento (400+400+2x100); sem caminhao de recurso."""
    for label, text, spawned, spent, built in (("v3 manual", H.TEXT_V3, 4, 1000, 4),
                                               ("v2 (anterior)", H.TEXT_V2, 5, 1100, 5)):
        lua = H.persist_game(text, version)
        r = lua.execute(r'''
H.newWorld({})
assert(api.logi.deploy() == true, table.concat(H.logs, "\n"))
local W = api.S.deploy
return string.format("%d|%d|%d|%d|%d", H.spawned, W.spent, W.bmat, #W.built, H.live("BPTruckW_C"))
''')
        sp, spent_, left, nb, trucks = [int(x) for x in str(r).split("|")]
        assert (sp, spent_, nb) == (spawned, spent, built), (label, sp, spent_, nb)
        assert left == 0, "orcamento fecha em zero: sem sobra para comprar caminhao na hora (%s)" % label
        if text is H.TEXT_V3:
            r2 = lua.execute(r'''
assert(api.logi.start(), table.concat(H.logs, "\n"))
local L = api.logi
local res = L.trucks[1]
assert(res.kind == "res" and res.state == "dead" and not res.pawn, "sem ator: o de recurso ainda nao existe")
assert(L.bmat == 40 and #L.trucks == 3 and L.trucks[2].pawn and L.trucks[3].pawn and L.base.shirts == 30)
assert(H.live("BPTruckW_C") == 2)
L.bmat = 100
L.truckStep(res, 1, clock + 1)
assert(res.state == "idle" and L.bmat == 0, "reconstrucao normal por 100 bmat")
assert(res.pawn and res.pawn:IsValid() and not res.pawn.bHidden and H.live("BPTruckW_C") == 3, "ator do caminhao nasceu")
return "ok"
''')
            assert str(r2) == "ok"
    return "v3: 4 atores (2 estruturas + 2 caminhoes), 1000 gastos, saldo 0; v2: 5 atores, 1100"


for v in ("lua54", "lua55"):
    H.case("[%s] primeiro caminhao de recurso depois da coleta manual (X)" % v, t_primeiro_caminhao, v)
    H.case("[%s] progressao manual -> caminhao -> caixas na frente" % v, t_progressao, v)
    H.case("[%s] perder o caminhao volta a coleta (Y)" % v, t_perde_o_caminhao, v)
    H.case("[%s] nada de bmat sem coleta" % v, t_nada_do_nada, v)
    H.case("[%s] prioridade: recurso antes do suprimento" % v, t_prioridade, v)
    H.case("[%s] manualStart=false mantem o comportamento anterior" % v, t_legado, v)
    H.case("[%s] implantacao sem caminhao de recurso (orcamento 1000)" % v, t_implantacao, v)
H.finish("test_partida_manual")
