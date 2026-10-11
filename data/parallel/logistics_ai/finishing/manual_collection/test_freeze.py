"""COLETA_MANUAL: o travamento antigo se resolve. Caminhao de recurso destruido com bmat=0 e sucata=0 sob consumo continuo
(pior caso do acabamento: `test_truck_bmat.py`, "limite conhecido"): no candidato v2 o caminhao fica destruido para
sempre; no v3 os trabalhadores da base coletam a pe e a fabrica reconstroi o caminhao (tempo X).

  cd /d/GitHub/foxhole-rts && PYTHONPATH=D:/tools/pylibs PYTHONDONTWRITEBYTECODE=1 \
      python data/parallel/logistics_ai/finishing/manual_collection/test_freeze.py
"""
import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parent))
import harness_coleta as H  # noqa: E402

LEGACY_V3 = H.TEXT_V3.replace("manualStart = true,", "manualStart = false,", 1)

SCENARIO = r'''
newMatch()
local L, res = A.logi, resTruck()
local killAt, killed = 60, nil
local rebuilt = nil
for step = 1, 9000 do                                   -- 900 s
    -- consumo continuo do jogador: caixas de municao, fuzis e bandagens somem a cada quadro (camisas ficam: recrutar e outro fluxo)
    L.base.ammo, L.base.rifle, L.base.medical = 0, 0, 0
    L.fac.ammo, L.fac.shirts, L.fac.rifle, L.fac.medical = 0, 0, 0, 0
    if not killed and clock >= killAt then
        L.bmat, L.salvage = 0, 0                        -- pior caso: sem bmat nem sucata
        assert(L.hit(res, 1e9, clock) and res.state == "dead")
        killed = clock
    end
    stepOnce()
    if killed and not rebuilt and res.state ~= "dead" then rebuilt = clock - killed end
end
return rebuilt and string.format("%.1f", rebuilt) or "nunca"
'''


def run(text, version):
    lua = H.new_game(text, version=version)
    return str(lua.execute(SCENARIO))


def t_antes_e_depois(version):
    before = run(H.TEXT_V2, version)
    assert before == "nunca", "baseline v2: o caminhao deveria ficar destruido para sempre (900 s), foi " + before
    after = run(LEGACY_V3, version)
    assert after != "nunca", "v3 deveria reconstruir o caminhao"
    x = float(after)
    assert 60 <= x <= 600, x
    return "v2: caminhao %s em 900 s | v3 (inicio legado, caminhao morre aos 60 s com bmat=0 e sucata=0): volta em X = %.1f s" % (before, x)


def t_partida_manual_pior_caso(version):
    """Partida manual: o caminhao nunca existiu e o bmat e 40; mesmo consumo continuo, ele sai (X desde o inicio)."""
    lua = H.new_game(version=version)
    r = lua.execute(SCENARIO.replace("local killAt, killed = 60, nil", "local killAt, killed = -1, 0"))
    assert str(r) != "nunca"
    return "partida manual sob consumo continuo: caminhao em %s s" % r


for v in ("lua54", "lua55"):
    H.case("[%s] travamento antigo (recurso morto, bmat=0, sucata=0): v2 trava, v3 resolve" % v, t_antes_e_depois, v)
    H.case("[%s] partida manual sob consumo continuo" % v, t_partida_manual_pior_caso, v)
H.finish("test_travamento")
