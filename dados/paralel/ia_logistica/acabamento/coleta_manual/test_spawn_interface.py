"""COLETA_MANUAL: interface comum de nascimento (bases_avancadas/ESPECIFICACAO.md 4.3) usada so pelo trabalhador:
logi.spawnSite (pura, decide) -> spawnSoldier (engine) -> logi.spawnCommit (revalida e debita UMA vez). Garante: spawnSite
nao muda estado; funcao sem receita e ramo legado recusam com razao; camisa so e debitada apos spawn confirmado; o commit
revalida; estoque inicial da partida manual (camisas >= trabalhadores, startRifles = 10) e do legado inalterado.

  cd /d/GitHub/foxhole-rts && PYTHONPATH=D:/tools/pylibs PYTHONDONTWRITEBYTECODE=1 \
      python dados/paralel/ia_logistica/acabamento/coleta_manual/test_spawn_interface.py
"""
import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parent))
import harness_coleta as H  # noqa: E402

LEGACY_V3 = H.TEXT_V3.replace("manualStart = true,", "manualStart = false,", 1)


def t_receita_e_estoque_inicial(version):
    lua = H.new_game(version=version)
    lua.execute(r'''
local C = A.CFG
assert(C.SPAWN.roles.worker.shirts == 1 and C.SPAWN.roles.worker.sites[1] == "base" and #C.SPAWN.roles.worker.sites == 1)
assert(C.SPAWN.startRifles == 10)
newMatch()
local L = A.logi
assert(L.base.rifle == 10, "fuzis iniciais so na partida manual: " .. tostring(L.base.rifle))
assert(L.base.shirts >= C.COLETA.workers, "camisas para os primeiros trabalhadores: " .. tostring(L.base.shirts))
''')
    lua = H.new_game(LEGACY_V3, version=version)
    lua.execute(r'''
newMatch()
assert(A.logi.base.rifle == 0 and A.logi.base.shirts == A.CFG.LOGI.shirts0, "legado: estoque inicial como no v2")
''')
    return "manual: base com 10 fuzis e >= 3 camisas; legado: estoque do v2 intacto"


def t_site_puro_e_recusas(version):
    lua = H.new_game(version=version)
    lua.execute(r'''
local L = A.logi
-- antes de logi.start: ramo legado
local site, why = L.spawnSite("worker", nil)
assert(site == nil and why == "ramo legado", tostring(why))
newMatch()
local b = L.base
local s0, r0, n0 = b.shirts, b.rifle, #A.squad()
local site, why = L.spawnSite("worker", nil)
assert(site and why == nil and site.kind == "base" and site.dep == b and site.need.shirts == 1 and site.explicit == false)
assert(site.at.exact == true and type(site.at.X) == "number" and type(site.at.Y) == "number" and type(site.at.Z) == "number")
assert(math.abs(dist(site.at, b) - 250) < 1e-6, "saida no anel de 250 cm ao redor da base")
for i = 1, 5 do L.spawnSite("worker", nil) end
assert(b.shirts == s0 and b.rifle == r0 and #A.squad() == n0 and SPAWNED == 0, "spawnSite e pura: nenhum estado muda")
local s2, w2 = L.spawnSite("medic_inexistente", nil)
assert(s2 == nil and w2 == "função sem receita", tostring(w2))
b.shirts = 0
local s3, w3 = L.spawnSite("worker", nil)
assert(s3 == nil and w3:find("sem camisas", 1, true), tostring(w3))
b.shirts = 1
assert(L.spawnSite("worker", nil), "1 camisa basta para 1 trabalhador")
local s4, w4 = L.spawnSite("worker", nil, {sites = {"posto"}})
assert(s4 == nil and w4 == "nenhum local de nascimento permitido", tostring(w4))
''')
    return "pura (5 chamadas, zero mudanca); recusas: ramo legado, sem receita, sem camisas, local nao permitido"


def t_commit_apenas_apos_spawn(version):
    lua = H.new_game(version=version)
    lua.execute(r'''
newMatch()
local L = A.logi
local s0 = L.base.shirts
SPAWN_FAIL = true
runUntil(30)
assert(workers() == 0 and L.base.shirts == s0, "spawn falhou: nada debitado")
SPAWN_FAIL = false
runUntil(4)
assert(workers() == 1 and L.base.shirts == s0 - 1, "spawn confirmado: exatamente 1 camisa")
-- commit revalida: estoque mudou entre decidir e criar
local site = L.spawnSite("worker", nil)
L.base.shirts = 0
local ok, why = L.spawnCommit(site, "worker")
assert(ok == false and why == "estoque insuficiente" and L.base.shirts == 0, "commit sem estoque nao debita nada")
assert(L.spawnCommit(nil, "worker") == false)
L.base.shirts = 5
assert(L.spawnCommit(site, "worker") == true and L.base.shirts == 4, "commit valido debita 1")
''')
    return "falha de spawn nao debita; confirmado debita 1; commit sem estoque recusa; commit com site nulo recusa"


def t_commit_recusado_desfaz_o_ator(version):
    """Se o commit recusar depois do ator criado (nao deveria no game thread), o ator e desfeito: nada no esquadrao."""
    lua = H.new_game(version=version)
    lua.execute(r'''
newMatch()
local L = A.logi
local real = L.spawnCommit
local calls = 0
L.spawnCommit = function() calls = calls + 1; return false, "estoque insuficiente" end
local s0 = L.base.shirts
runUntil(30)
assert(calls >= 1 and workers() == 0 and #A.squad() == 6 and L.base.shirts == s0, "ator desfeito: nada no esquadrao nem na carteira")
L.spawnCommit = real
''')
    return "commit recusado desfaz o ator: esquadrao e camisas intactos"


def t_worker_nao_gasta_camisa_direto(version):
    """O codigo novo nunca debita dep.shirts fora de spawnCommit (a unica excecao nao migrada e recruit(), do v2)."""
    src = H.TEXT_V3
    a = src.index("function logi.spawnSite")
    b = src.index("function logi.tick()")
    novo = src[a:b]
    import re
    c0 = novo.index("function logi.spawnCommit")
    c1 = novo.index(chr(10) + "end" + chr(10), c0) + 5
    resto = novo[:c0] + novo[c1:]
    assert re.search(r"\.shirts(\s*,\s*[\w.]+)*\s*=(?!=)", novo[c0:c1]), "spawnCommit deve debitar camisas"
    assert not re.search(r"\.shirts(\s*,\s*[\w.]+)*\s*=(?!=)", resto), "debito de camisa fora de spawnCommit"
    return "unica atribuicao de .shirts no codigo novo esta em spawnCommit"


for v in ("lua54", "lua55"):
    H.case("[%s] receita CFG.SPAWN e estoque inicial (startRifles=10)" % v, t_receita_e_estoque_inicial, v)
    H.case("[%s] spawnSite pura e recusas com razao" % v, t_site_puro_e_recusas, v)
    H.case("[%s] spawnCommit debita so apos spawn confirmado" % v, t_commit_apenas_apos_spawn, v)
    H.case("[%s] commit recusado desfaz o ator" % v, t_commit_recusado_desfaz_o_ator, v)
H.case("debito de camisa so em spawnCommit (analise estatica)", t_worker_nao_gasta_camisa_direto, "lua54")
H.finish("test_spawn_interface")
