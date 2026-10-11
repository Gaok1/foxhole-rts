"""Patch isolado do item 2 (hipotese bmat x caminhao do jogador): reserva de bmat para reconstruir caminhao.

Aplica-se DEPOIS da pilha ECONOMIA -> IA_LOGISTICA (qualquer das duas versoes da IA; nao toca a cadeia inimiga):

    from patch_reserva_bmat import apply
    final = apply(ia_logistica_build(economia_build(main)))

Problema (provado em test_bmat_caminhao.py): com consumo continuo a fabrica inicia uma receita assim que o bmat
chega a 80 (receitas de 80 bmat, 100 para fuzil) e o caminhao destruido precisa de LOGI.truckCost = 100 bmat; o
bmat nunca passa de ~80 e o caminhao nunca e reconstruido. A ordem das chamadas em logi.tick NAO e a causa
(trocar fabrica e caminhoes de lugar nao resolve: o limiar de 80 vence o de 100 em qualquer ordem).

Correcao minima: enquanto houver caminhao destruido, a fabrica so inicia uma receita se sobrar, depois de
debita-la, LOGI.truckCost bmat por caminhao destruido. Mesma decisao que a cadeia inimiga ja usa. Sem local novo de
topo (funcao em `logi`), sem tecla, sem constante nova de CFG, nada no save (o estado e derivado dos caminhoes).
"""
import difflib
from pathlib import Path

FACTORY_ANCHOR = (
    "    local kind = logi.nextKind()\n"
    "    local rc = kind and C.recipes[kind]\n"
    "    if not rc or type(rc.bmat) ~= \"number\" or rc.bmat <= 0 or type(rc.time) ~= \"number\" or rc.time <= 0 or logi.bmat < rc.bmat then return end\n"
)
FACTORY_NEW = (
    "    local kind = logi.nextKind()\n"
    "    local rc = kind and C.recipes[kind]\n"
    "    if not rc or type(rc.bmat) ~= \"number\" or rc.bmat <= 0 or type(rc.time) ~= \"number\" or rc.time <= 0 or logi.bmat < rc.bmat then return end\n"
    "    local keep = logi.rebuildReserve()\n"
    "    if logi.bmat - rc.bmat < keep then  -- guarda bmat para o caminhao destruido (senao a fabrica gasta cada 80 antes de juntar 100)\n"
    "        local t = now()\n"
    "        if t - (logi.rebuildNoteT or -1e9) >= 20.0 then\n"
    "            logi.rebuildNoteT = t\n"
    "            notify(string.format(\"fábrica guarda %d bmat para reconstruir caminhão\", keep), 3.0)\n"
    "        end\n"
    "        return\n"
    "    end\n"
)
FUNC_ANCHOR = "function logi.factoryStep(dt)\n"
FUNC_NEW = (
    "-- bmat que a fabrica nao pode gastar: LOGI.truckCost por caminhao do jogador destruido e ainda nao reconstruido.\n"
    "function logi.rebuildReserve()\n"
    "    local n = 0\n"
    "    for _, tr in ipairs(logi.trucks or {}) do if tr.state == \"dead\" then n = n + 1 end end\n"
    "    return n * CFG.LOGI.truckCost\n"
    "end\n\n"
    + FUNC_ANCHOR
)


def apply(s):
    assert s.count(FACTORY_ANCHOR) == 1, ("âncora da fábrica não única/ausente", s.count(FACTORY_ANCHOR))
    assert s.count(FUNC_ANCHOR) == 1 and "function logi.rebuildReserve" not in s, "patch já aplicado ou âncora ausente"
    s = s.replace(FACTORY_ANCHOR, FACTORY_NEW, 1)
    return s.replace(FUNC_ANCHOR, FUNC_NEW, 1)


def diff(a, b):
    return "".join(difflib.unified_diff(a.splitlines(True), b.splitlines(True),
                                        fromfile="a/mod/FoxholeRTS/Scripts/main.lua (ECONOMIA+IA)", tofile="b/mod/FoxholeRTS/Scripts/main.lua"))
