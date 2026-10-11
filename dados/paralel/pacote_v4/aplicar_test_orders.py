"""PACOTE_V4: gera a versao de tools/test_orders.py para o main.lua integrado (pilha v4).

Por padrao e um DRY-RUN: imprime o diff e nao grava nada. Quem integra decide:
  python dados/paralel/pacote_v4/aplicar_test_orders.py                 # so mostra o diff
  python dados/paralel/pacote_v4/aplicar_test_orders.py --out ARQ.py    # grava a versao nova em outro arquivo
  python dados/paralel/pacote_v4/aplicar_test_orders.py --write         # troca tools/test_orders.py (guarda tools/test_orders.py.pre_v4)

O que troca (as mesmas trocas do bases_avancadas/etapa2/test_orders_v4.py, que ja passa no candidato; esta copia nao muda a linha
que le o main.lua, porque depois da integracao o main real E a v4):
  1. bloco 'enemy convoy' -> ia_logistica/acabamento/test_orders_bloco_comboio_v2.lua (cadeia inimiga com razao fechado)
  2. 8 trocas da coleta manual (implantacao 1000 / 2 vagas / 4 atores, caminhao de recurso por construir)
  3. asserção de SHIFT+J no teste de teclas (registrada, fora de GAME_KEYS, J livre no jogo)
Idempotente: se o arquivo ja tem a marca 'ADAPTACAO bases avancadas', avisa e sai sem mexer. Aborta se qualquer ancora nao for unica.
So le arquivos; so grava com --out/--write.
"""
import argparse
import difflib
import importlib.util
import sys
from pathlib import Path

sys.dont_write_bytecode = True
HERE = Path(__file__).resolve().parent
ROOT = HERE.parents[2]
ETAPA2 = ROOT / "dados/paralel/bases_avancadas/etapa2"
BLOCO = ROOT / "dados/paralel/ia_logistica/acabamento/test_orders_bloco_comboio_v2.lua"
TARGET = ROOT / "tools/test_orders.py"
MARK = "ADAPTACAO bases avancadas"


def load_adaptacoes():
    """ADAPTACOES e os marcadores do bloco do comboio, lidos do test_orders_v4.py (sem executar a suite)."""
    sys.path.insert(0, str(ETAPA2))
    spec = importlib.util.spec_from_file_location("test_orders_v4_pacote", ETAPA2 / "test_orders_v4.py")
    mod = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(mod)
    return mod.ADAPTACOES, mod.CONVOY_START, mod.CONVOY_END


def swap_once(text, old, new, what):
    if text.count(old) != 1:
        raise SystemExit("ancora nao unica (%d) em %s: %r\nabortado, nada gravado" % (text.count(old), what, old[:80]))
    return text.replace(old, new, 1)


def build(src_bytes):
    crlf = src_bytes.count(b"\r\n") > 0
    s = src_bytes.decode("utf-8").replace("\r\n", "\n")
    if MARK in s:
        return None, crlf
    adapt, c_start, c_end = load_adaptacoes()
    if s.count(c_start) != 1 or s.count(c_end) != 1:
        raise SystemExit("bloco do comboio nao encontrado de forma unica em tools/test_orders.py; abortado")
    a = s.index(c_start)
    b = s.index(c_end, a) + len(c_end)
    s = s[:a] + BLOCO.read_bytes().decode("utf-8").replace("\r\n", "\n") + s[b:]
    for old, new, why in adapt:
        s = swap_once(s, old, new, why)
    return s, crlf


def main():
    ap = argparse.ArgumentParser(description=__doc__, formatter_class=argparse.RawDescriptionHelpFormatter)
    ap.add_argument("--write", action="store_true", help="troca tools/test_orders.py (backup .pre_v4 ao lado)")
    ap.add_argument("--out", help="grava a versao nova neste arquivo")
    ap.add_argument("--src", default=str(TARGET), help="arquivo de entrada (padrao: tools/test_orders.py)")
    args = ap.parse_args()
    src = Path(args.src)
    raw = src.read_bytes()
    new, crlf = build(raw)
    if new is None:
        print("ja aplicado (marca '%s' presente em %s): nada a fazer" % (MARK, src))
        return 0
    old_txt = raw.decode("utf-8").replace("\r\n", "\n")
    diff = list(difflib.unified_diff(old_txt.splitlines(), new.splitlines(), "tools/test_orders.py (atual)",
                                     "tools/test_orders.py (v4)", lineterm="", n=1))
    print("\n".join(diff))
    print("\n%d linhas de diff; fim de linha %s" % (len(diff), "CRLF" if crlf else "LF"), file=sys.stderr)
    out = new.replace("\n", "\r\n") if crlf else new
    if args.out:
        Path(args.out).write_bytes(out.encode("utf-8"))
        print("gravado em", args.out, file=sys.stderr)
    if args.write:
        bak = src.with_name(src.name + ".pre_v4")
        if bak.exists():
            raise SystemExit("%s ja existe; mova-o antes de repetir --write" % bak)
        bak.write_bytes(raw)
        src.write_bytes(out.encode("utf-8"))
        print("gravado %s (backup %s)" % (src, bak), file=sys.stderr)
    return 0


if __name__ == "__main__":
    sys.exit(main())
