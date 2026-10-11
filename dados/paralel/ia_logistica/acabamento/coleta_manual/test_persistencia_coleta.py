"""COLETA_MANUAL x PERSISTENCIA: salvar e continuar DURANTE a coleta. A carga em maos NAO e salva (descarte explicito e
registrado); o schema v2 do save nao muda. Garante: nada de sucata creditada por salvar/continuar, nada duplicado, a coleta
recomeca sozinha, trabalhadores voltam como soldados role "worker", save com implantacao v3 (2 caminhoes pagos) refaz a infra.

  cd /d/GitHub/foxhole-rts && PYTHONPATH=D:/tools/pylibs PYTHONDONTWRITEBYTECODE=1 \
      python dados/paralel/ia_logistica/acabamento/coleta_manual/test_persistencia_coleta.py
"""
import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parent))
import harness_coleta as H  # noqa: E402

# partida em andamento: logi.start real (res morto, bmat 40), esquadrao, ondas ligadas; trabalhadores teletransportados ao campo
MATCH = r'''
function stepTo(secs, hook)
    local t0 = clock
    while clock - t0 < secs do
        clock = clock + 0.5
        api.tick.n = api.tick.n + 1
        api.logi.tick()
        if hook then hook() end
    end
end
function startMatch(deploy)
    H.newWorld(deploy and {} or {active = true, trucks = 3})
    if deploy then assert(api.logi.deploy() == true, table.concat(H.logs, "|")) end
    assert(api.logi.start(), table.concat(H.logs, "|"))
    api.logi.convoyT = 1e9
    local S = api.squad()
    S[#S + 1] = H.unit("rifle", 100, 50); S[#S + 1] = H.unit("rifle", 200, 50)
    api.combat.auto, api.combat.won, api.combat.wave, api.combat.kills = true, false, 2, 5
    api.combat.startT = clock - 60
    api.economy.manpower = 77
end
-- leva os trabalhadores ao campo (teletransporte: o movimento real e do harness de movimento) e deixa colher
function work(secs)
    local L = api.logi
    stepTo(16)                                   -- delay + nascimento (3 s cada) + recrutamento
    for _, u in ipairs(L.col.units) do u.m.target, u.m.pathJob = nil, nil; u.m.pawn.position = {X = L.field.X + 100, Y = L.field.Y, Z = 0} end
    stepTo(secs)
end
function inHand() local n = 0 for _, u in ipairs(api.logi.col.units) do n = n + u.carry end return n end
function nWorkers() local n = 0 for _, m in ipairs(api.squad()) do if m.role == "worker" then n = n + 1 end end return n end
'''


def first_load(version, deploy=False):
    lua = H.persist_game(H.TEXT_V3, version)
    lua.execute(MATCH)
    lua.execute("startMatch(%s)" % ("true" if deploy else "false"))
    return lua


def t_salvar_durante_a_coleta(version):
    a = first_load(version)
    r = a.execute(r'''
work(20)
local L, K = api.logi, api.logi.col
assert(#K.units == 3 and inHand() >= 25 and nWorkers() == 3, "coleta em andamento: " .. inHand())
local hand = inHand()
local bmat, salv = L.bmat, L.salvage
local ok = api.sv.save()
assert(ok == true, table.concat(H.logs, "|"))
return string.format("%.4f|%.4f|%.4f|%d", bmat, salv, hand, L.base.shirts)
''')
    bmat, salv, hand, shirts = [float(x) for x in str(r).split("|")]
    files = {p: c for p, c in a.eval("FS.files").items()}
    text = files[H.SAVE_PATH]
    assert "carry" not in text and "gathered" not in text, "a coleta nao entra no save"
    b = H.persist_game(H.TEXT_V3, version, files)
    b.execute(MATCH)
    b.execute("H.newWorld({active = true, trucks = 3})")
    assert b.eval("api.sv.load()") is True, b.eval("table.concat(H.logs, '\\n')")
    out = b.execute(r'''
local L, K = api.logi, api.logi.col
return string.format("%.4f|%.4f|%d|%d|%d|%s|%d", L.bmat, L.salvage, #K.units, nWorkers(), L.base.shirts, L.trucks[1].state, #api.squad())
''')
    bmat2, salv2, units, workers, shirts2, state, squad = str(out).split("|")
    assert abs(float(bmat2) - bmat) < 1e-3 and abs(float(salv2) - salv) < 1e-3, "estoque identico ao salvo (a carga em maos nao entra)"
    assert int(units) == 0 and state == "dead", "coleta recomeca do zero; caminhao segue por construir"
    assert int(workers) == 3 and int(squad) == 5 and int(float(shirts2)) == int(shirts), "trabalhadores voltam como role worker; camisas como salvas"
    # a coleta recomeca sozinha e nada foi creditado pela carga antiga
    c = b.execute(r'''
local L, K = api.logi, api.logi.col
assert(K.gathered == 0 and K.delivered == 0)
stepTo(14)
local dbg = {}
for _, m in ipairs(api.squad()) do dbg[#dbg + 1] = string.format("%s free=%s tgt=%s pj=%s hold=%s orderT=%s", m.role, tostring(L.colFree(m, clock)), tostring(m.target), tostring(m.pathJob), tostring(m.hold), tostring(m.orderT)) end
assert(K.active and #K.units == 3, "recrutados de novo (restaurados nao tem ordem do jogador) active=" .. tostring(K.active) .. " units=" .. #K.units .. " " .. table.concat(dbg, " ; "))
assert(math.abs(L.salvage - SALV) < 1e-3)
return "ok"
'''.replace("SALV", repr(salv)))
    assert str(c) == "ok"
    return "salvou com %.1f sucata em maos: continuar devolveu bmat %.2f e sucata %.2f exatamente; 3 trabalhadores; coleta recomeca" % (hand, bmat, salv)


def t_repetir_nao_cria_nada(version):
    a = first_load(version)
    a.execute("work(20)")
    ledger = None
    files = None
    cur = a
    for i in range(4):
        assert cur.eval("api.sv.save()") is True
        files = {p: c for p, c in cur.eval("FS.files").items()}
        nxt = H.persist_game(H.TEXT_V3, version, files)
        nxt.execute(MATCH)
        nxt.execute("H.newWorld({active = true, trucks = 3})")
        assert nxt.eval("api.sv.load()") is True, nxt.eval("table.concat(H.logs, '\\n')")
        row = str(nxt.execute(r'''return string.format("%.4f|%.4f|%d|%d", api.logi.bmat, api.logi.salvage, api.logi.base.shirts, nWorkers())'''))
        ledger = ledger or row
        assert row == ledger, "continuar/salvar repetido nao pode criar nem destruir nada: %s x %s" % (row, ledger)
        cur = nxt
    return "4 ciclos salvar+continuar: %s (bmat|sucata|camisas|trabalhadores) identico" % ledger


def t_continuar_na_mesma_sessao(version):
    """Continuar sem reiniciar o jogo: a carga em maos de antes e descartada e registrada (log), nunca creditada."""
    a = first_load(version)
    a.execute("work(20)")
    r = a.execute(r'''
local L = api.logi
local hand, salv = inHand(), L.salvage
assert(hand > 0 and api.sv.save() == true)
H.logs = {}
H.newWorld({active = true, trucks = 3})        -- mundo recarregado, mesmo Lua
assert(api.sv.load() == true, table.concat(H.logs, "|"))
assert(H.saw("descartada (reinício)"), "descarte registrado: " .. table.concat(H.logs, "|"))
assert(math.abs(L.salvage - salv) < 1e-3 and #L.col.units == 0 and L.col.gathered == 0)
return string.format("%.1f", hand)
''')
    return "continuar na mesma sessao descarta %s sucata em maos (log) sem creditar" % r


def t_implantacao_v3(version):
    a = first_load(version, deploy=True)
    a.execute("work(20)")
    r = a.execute(r'''
assert(H.spawned == 4 and api.S.deploy.spent == 1000, "implantacao v3: 2 estruturas + 2 caminhoes")
assert(api.sv.save() == true)
return api.logi.salvage
''')
    files = {p: c for p, c in a.eval("FS.files").items()}
    b = H.persist_game(H.TEXT_V3, version, files)
    b.execute(MATCH)
    b.execute("H.newWorld({})")
    assert b.eval("api.sv.load()") is True, b.eval("table.concat(H.logs, '\\n')")
    out = b.execute(r'''
return string.format("%d|%d|%d|%s", H.spawned, H.live("BPTruckW_C"), api.S.deploy.spent, api.logi.trucks[1].state)
''')
    assert str(out) == "4|2|1000|dead", out
    # v2 nao abre um save de v3 com trabalhadores no esquadrao (papel desconhecido) nem a implantacao de 2 caminhoes (precisa de 3)
    c = H.persist_game(H.TEXT_V2, version, files)
    c.execute(MATCH.split("function startMatch")[0])
    c.execute("H.newWorld({})")
    assert c.eval("api.sv.load()") is False
    logs = str(c.eval("table.concat(H.logs, string.char(10))"))
    assert "squad" in logs, logs
    # save de v3 feito ANTES de nascer qualquer trabalhador: so a implantacao incompativel
    a0 = first_load(version, deploy=True)
    assert a0.eval("api.sv.save()") is True
    files0 = {p: c for p, c in a0.eval("FS.files").items()}
    d = H.persist_game(H.TEXT_V2, version, files0)
    d.execute(MATCH.split("function startMatch")[0])
    d.execute("H.newWorld({})")
    assert d.eval("api.sv.load()") is False
    logs0 = str(d.eval("table.concat(H.logs, string.char(10))"))
    assert "faltam 3 caminhões e o save só pagou 2" in logs0, logs0
    return "v3 refaz 2 estruturas + 2 caminhoes (sem cobrar de novo); v2 recusa o save de v3 (papel worker desconhecido no esquadrao; sem trabalhadores: faltam 3 caminhoes e o save pagou 2)"


def t_save_do_v2_abre_no_v3(version):
    """Compatibilidade para tras: save feito no candidato v2 (3 caminhoes, sem trabalhadores) continua no v3."""
    a = H.persist_game(H.TEXT_V2, version)
    a.execute(MATCH.split("function startMatch")[0])
    a.execute(r'''
H.newWorld({active = true, trucks = 3})
assert(api.logi.start())
local S = api.squad()
S[#S + 1] = H.unit("rifle", 100, 50); S[#S + 1] = H.unit("rifle", 200, 50)
api.combat.auto, api.combat.won, api.combat.startT = true, false, clock - 60
api.logi.bmat = 123.5
assert(api.sv.save() == true, table.concat(H.logs, "|"))
''')
    files = {p: c for p, c in a.eval("FS.files").items()}
    b = H.persist_game(H.TEXT_V3, version, files)
    b.execute(MATCH)
    b.execute("H.newWorld({active = true, trucks = 3})")
    assert b.eval("api.sv.load()") is True, b.eval("table.concat(H.logs, '\\n')")
    out = b.execute(r'''
stepTo(30)
local L = api.logi
return string.format("%.1f|%s|%s|%s|%s", L.bmat, L.trucks[1].state, tostring(L.col.active), tostring(#L.col.units), tostring(nWorkers()))
''')
    bm, st, active, units, workers = str(out).split("|")
    assert st != "dead" and active == "false" and units == "0" and workers == "0", out
    return "save do v2 abre no v3: caminhoes vivos, coleta inativa, nenhum trabalhador criado"


for v in ("lua54", "lua55"):
    H.case("[%s] salvar durante a coleta; continuar" % v, t_salvar_durante_a_coleta, v)
    H.case("[%s] 4 ciclos salvar+continuar nao criam nem destroem" % v, t_repetir_nao_cria_nada, v)
    H.case("[%s] continuar na mesma sessao descarta a carga (registrado)" % v, t_continuar_na_mesma_sessao, v)
    H.case("[%s] save com implantacao v3 (2 caminhoes pagos)" % v, t_implantacao_v3, v)
    H.case("[%s] save do v2 abre no v3" % v, t_save_do_v2_abre_no_v3, v)
H.finish("test_persistencia_coleta")
