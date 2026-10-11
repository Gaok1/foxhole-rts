"""Gera o main.lua candidato da IA_LOGISTICA em memoria (ancoras unicas, fail-closed). NAO toca main.lua.

Ordem declarada: main.lua atual (com ESTABILIDADE ja integrada) -> ECONOMIA (dados/paralel/economia/build_patch.py)
-> IA_LOGISTICA (este). O patch tambem aplica sobre o main.lua sem a ECONOMIA (testado), porque nenhuma ancora
depende de texto da ECONOMIA. A ancora do HUD e opcional: o patch da INTERFACE substitui essa linha; nesse caso o
painel continua lendo combat.cargo (alias mantido = soldados que a frente inimiga equipa).

Uso (raiz do repositorio):  $env:PYTHONPATH='D:/tools/pylibs'; python dados/paralel/ia_logistica/build_patch.py
Saidas nesta pasta: ia_logistica.patch (sobre main+ECONOMIA), ia_logistica_base.patch (sobre main puro),
main_candidato.lua (main+ECONOMIA+IA, so para check_globals/inspecao; nunca copiar por cima do main.lua).
"""
import sys
from pathlib import Path
import difflib
import importlib.util

sys.dont_write_bytecode = True  # nao gravar __pycache__ nas pastas dos outros agentes
HERE = Path(__file__).resolve().parent
ROOT = HERE.parents[3]
MAIN = ROOT / "mod/FoxholeRTS/Scripts/main.lua"


def economia_build():
    spec = importlib.util.spec_from_file_location("economia_build", ROOT / "dados/paralel/economia/build_patch.py")
    mod = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(mod)
    return mod.build


def build(s):
    chunk = HERE.joinpath("ia_logistica_v2.lua").read_text(encoding="utf-8-sig")

    def replace(old, new, optional=False):
        nonlocal s
        n = s.count(old)
        if optional and n == 0:
            return False
        assert n == 1, ("âncora não única", old[:80], n)
        s = s.replace(old, new, 1)
        return True

    def cut(start, stop):
        """Remove de `start` (inclusive) ate `stop` (exclusivo); ambos unicos."""
        nonlocal s
        assert s.count(start) == 1 and s.count(stop) == 1, ("âncora de corte", start[:60], stop[:60])
        a = s.index(start)
        b = s.index(stop, a)
        s = s[:a] + s[b:]

    # 1. Comentario/CFG do comboio: sem carga abstrata (cargo0/perWave/cut); retry quando falta carga.
    replace("-- (ECONVOY.front). Chegando deixa 1 carga (combat.cargo); cada onda gasta ate perWave cargas e cada uma que\n"
            "-- falta tira cut soldados dela.",
            "-- (ECONVOY.front) levando caixas reais da retaguarda inimiga (CFG.ECHAIN, logi.e*); a onda so recebe, alem da\n"
            "-- guarnicao gratuita, os soldados que a frente equipa.")
    replace("hp = 900, perWave = 2, cut = 2, cargo0 = 2, bounty = 25,", "hp = 900, bounty = 25, retry = 5.0,")
    # 2. Partida nova: cadeia com estoque de cenario no razao, nao carga abstrata de presente.
    replace("    combat.cargo, combat.convoys, combat.convoysCut = CFG.ECONVOY.cargo0, 0, 0\n",
            "    combat.convoys, combat.convoysCut = 0, 0\n    logi.eReset()\n")
    replace("    logi.foes, logi.convoyT = {}, nil\n", "    logi.foes, logi.convoyT, logi.en, combat.cargo = {}, nil, nil, 0\n")
    # 3. Destruicao do comboio inimigo: carga sai como perda registrada, uma vez.
    replace('        combat.convoysCut = (combat.convoysCut or 0) + 1\n        earn(CFG.ECONVOY.bounty)\n'
            '        pcall(rts.alert, "comboioX", tr, string.format("COMBOIO INIMIGO DESTRUÍDO (+%d): a próxima onda vem mais fraca", CFG.ECONVOY.bounty))',
            '        combat.convoysCut = (combat.convoysCut or 0) + 1\n        local lost = logi.eLose(tr, "destruído")\n'
            '        earn(CFG.ECONVOY.bounty)\n'
            '        pcall(rts.alert, "comboioX", tr, string.format("COMBOIO INIMIGO DESTRUÍDO (+%d): %s", CFG.ECONVOY.bounty, lost))')
    # 4. Troca convoySpawn/convoyTick/waveCut pelo modulo (inserido antes de logi.snapshot).
    cut("function logi.convoySpawn(t)", "-- Dano num caminhao (nosso ou inimigo); true se destruiu.")
    cut("function logi.convoyTick(dt, t)", "function logi.snapshot()")
    replace("function logi.snapshot()", chunk.rstrip() + "\n\nfunction logi.snapshot()")
    # 5. HUD (opcional: a INTERFACE pode ter trocado a linha).
    hud = replace('        foe = string.format(" | INIMIGO: carga %d%s", combat.cargo or 0, #logi.foes > 0 and ", comboio na estrada" or "")',
                  '        foe = logi.eHud()', optional=True)
    # 6. Onda: debito depois do spawn (so soldados pagos que nasceram).
    replace("            spawnEnemies(p, n)\n        end\n", "            spawnEnemies(p, n)\n        end\n        logi.eCommit(combat.waveSize or 0)\n")
    # 7. Reforco pelos pontos: limitado e pago pela frente.
    replace("    local n = math.min(math.random(2, 3), CFG.AI.max - ai.sent, math.floor(ai.mp / CFG.AI.cost))\n    if n < 1 then return end",
            "    local n = math.min(math.random(2, 3), CFG.AI.max - ai.sent, math.floor(ai.mp / CFG.AI.cost))\n"
            "    n = logi.eAfford(n)  -- reforco tambem precisa de camisa + carregamento na frente\n    if n < 1 then return end")
    replace("    if made > 0 then\n        ai.mp = ai.mp - made * CFG.AI.cost",
            "    if made > 0 then\n        logi.eConsume(made, \"reforço\")\n        ai.mp = ai.mp - made * CFG.AI.cost")
    # 8. Save/continue: cadeia (com carga em transito como pendente) junto da logistica.
    replace("wires = {}, logi = logi.snapshot() }", "wires = {}, logi = logi.snapshot(), elogi = logi.eSnapshot() }")
    replace("    if d.logi then pcall(logi.restore, d.logi) end\n",
            "    if d.logi then pcall(logi.restore, d.logi); pcall(logi.eRestore, d.elogi) end\n")
    for gone in ("cargo0", "perWave", "E.cut"):
        assert gone not in s, ("resto do contrato abstrato antigo", gone)
    return s, hud


def stacked(source):
    """main -> ECONOMIA -> IA (ordem declarada)."""
    return build(economia_build()(source))[0]


if __name__ == "__main__":
    source = MAIN.read_text(encoding="utf-8")
    eco = economia_build()(source)
    final, hud = build(eco)
    base, _ = build(source)

    def diff(a, b):
        return "".join(difflib.unified_diff(a.splitlines(True), b.splitlines(True),
                                            fromfile="a/mod/FoxholeRTS/Scripts/main.lua", tofile="b/mod/FoxholeRTS/Scripts/main.lua"))
    HERE.joinpath("ia_logistica_v2.patch").write_text(diff(eco, final), encoding="utf-8")
    HERE.joinpath("ia_logistica_v2_base.patch").write_text(diff(source, base), encoding="utf-8")
    HERE.joinpath("main_candidato_v2.lua").write_text(final, encoding="utf-8")
    print("patches gerados (HUD %s); main.lua intacto" % ("trocado" if hud else "mantido pela INTERFACE"))
