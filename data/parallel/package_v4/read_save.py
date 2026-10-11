"""PACOTE_V4: le um save.txt FORA do jogo com o parser/validador do proprio main.lua (lupa), sem executar o conteudo e sem escrever nada.

Uso (passo V2 do ROTEIRO_LOTE; tambem serve para conferir um save adulterado antes de usar no passo V9):
  cd /d/GitHub/foxhole-rts
  PYTHONPATH=D:/tools/pylibs PYTHONDONTWRITEBYTECODE=1 python data/parallel/package_v4/read_save.py <save.txt> [--main ARQ]

Imprime: decode ok/erro (parser de literais), parseSave ok/erro (validacao completa: schema v2, secoes infra/elogi/fwd, razao da carteira),
chaves de topo, versao, mundo, contagens (soldados, pontos, bases em `fwd`, registros pagos em `infra`), e se ha endereco/ator no texto
(nao deve haver). Valida com o main escolhido (padrao: mod/FoxholeRTS/Scripts/main.lua) no mundo falso do harness: a checagem de
mundo/superficie/ruinas e do Continuar real (preflight) NAO e reproduzida aqui; isso e o passo V4 do laboratorio.
"""
import os
import sys
from pathlib import Path

sys.dont_write_bytecode = True
HERE = Path(__file__).resolve().parent
ROOT = HERE.parents[2]
import argparse  # noqa: E402

ap = argparse.ArgumentParser(description=__doc__, formatter_class=argparse.RawDescriptionHelpFormatter)
ap.add_argument("save")
ap.add_argument("--main", default=str(ROOT / "mod/FoxholeRTS/Scripts/main.lua"))
ns = ap.parse_args()
main = Path(ns.main)
save = Path(ns.save)
os.environ["BASES_V4_FILE"] = str(main.resolve())
sys.path.insert(0, str(ROOT / "data/parallel/forward_bases/stage2"))
import harness_bases as H  # noqa: E402

txt = save.read_bytes().decode("utf-8", errors="replace").replace("\r\n", "\n")
print("arquivo: %s (%d bytes) | main: %s" % (save, save.stat().st_size, main))
for v in ("lua54", "lua55"):
    lua = H.persist_game(version=v)
    lua.globals().TXT = txt
    res = lua.execute(r'''
local out = {}
local function say(...) local t = {} for i = 1, select("#", ...) do t[#t + 1] = tostring(select(i, ...)) end out[#out + 1] = table.concat(t, " ") end
local sv = api.sv
if not sv.decode then return "este main nao tem o parser de literais (sv.decode): nao e a pilha v4/PERSISTENCIA v2" end
local d, err = sv.decode(TXT)
say("decode:", d and "OK" or "ERRO", err or "")
local p, perr = sv.parseSave(TXT)
say("parseSave:", p and "OK" or "ERRO", perr or "")
local dd = d or {}
local keys = {}
for k in pairs(dd) do keys[#keys + 1] = tostring(k) end
table.sort(keys)
say("chaves:", table.concat(keys, ","))
say("versao v =", tostring(dd.v), "| mundo =", tostring(dd.world))
local n = function(t) return type(t) == "table" and #t or "-" end
say("soldados", n(dd.squad), "inimigos", n(dd.enemies), "pontos", n(dd.points), "barreiras", n(dd.walls),
    "| fwd.list", type(dd.fwd) == "table" and n(dd.fwd.list) or "-", "| infra.built", type(dd.infra) == "table" and n(dd.infra.built) or "-",
    "gasto", type(dd.infra) == "table" and tostring(dd.infra.spent) or "-", "| elogi", dd.elogi ~= nil and "presente" or "ausente")
say("trecho com 'userdata' ou 'function' ou '0x':", (TXT:find("userdata", 1, true) or TXT:find("function", 1, true) or TXT:find("0x", 1, true)) and "ENCONTRADO (ruim)" or "nenhum (bom)")
return table.concat(out, "\n")
''')
    print("== %s\n%s" % (v, res))
