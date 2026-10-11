"""ENSAIO_INTEGRACAO: monta a pilha completa de patches paralelos sobre uma COPIA do main.lua (offline).

Ordem final (ancoras unicas, fail-closed; o primeiro erro para com mensagem clara):
  0. main.lua real (ESTABILIDADE ja integrada)       somente leitura
  1. ECONOMIA      data/parallel/economy/build_patch.py       build(texto)
  2. IA_LOGISTICA  data/parallel/logistics_ai/build_patch.py   build(texto)[0]
  3. INTERFACE     painel rebaseado (este arquivo, interface_build): troca a FUNCAO logi.hudLine inteira,
                   por limites de texto, e reaplica a reconciliacao (extraHud, returnCargo, eHud)
  4. PERSISTENCIA  data/parallel/persistence/build_patch.py   build_on(texto)

Nenhum build alheio e executado como script: so as funcoes puras build/build_on sao importadas (sem gravar
bytecode), portanto nada e escrito nas pastas dos outros agentes. O main.lua real so e lido (SHA256 antes e depois
sao registrados e conferidos). O ESTRADAS nao entra (sem driver integravel).

PILHA v2 (variante `v2`; a v1 acima continua reproduzivel e inalterada): entregas de logistics_ai/finishing/ (somente
leitura): ECONOMIA > IA_LOGISTICA v2 (calibracao CFG.ECHAIN) > reserva de bmat (patch_reserva_bmat) > INTERFACE (painel
rebaseado + estado da reserva e piso gratis) > PERSISTENCIA v2 (elogi: descarta so a secao).

Uso (raiz do repo, bash):
  PYTHONPATH=D:/tools/pylibs PYTHONDONTWRITEBYTECODE=1 python data/parallel/integration_rehearsal/build_stack.py [v1|v2|all]
Saidas nesta pasta: candidate/main.lua (CRLF como o real), candidate/SHA256.txt, stack.diff (CRLF, main real ->
candidato), stack_lf.diff (o mesmo em LF) e painel_rebase.patch (LF, etapa anterior -> + painel rebaseado).
A variante v2 grava candidate_v2/, stack_v2.diff, stack_v2_lf.diff e painel_rebase_v2.patch.
"""
import sys

sys.dont_write_bytecode = True  # nao gravar __pycache__ nas pastas dos outros agentes

import difflib  # noqa: E402
import hashlib  # noqa: E402
import importlib.util  # noqa: E402
from pathlib import Path  # noqa: E402

HERE = Path(__file__).resolve().parent
ROOT = HERE.parents[2]
MAIN = ROOT / "mod/FoxholeRTS/Scripts/main.lua"
PAR = ROOT / "data/parallel"
HEADER = "mod/FoxholeRTS/Scripts/main.lua"


class StackError(Exception):
    pass


def load_module(name, path):
    spec = importlib.util.spec_from_file_location(name, path)
    mod = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(mod)  # so define funcoes; os blocos __main__ dos builds NAO rodam
    return mod


def sha256(path_or_bytes):
    data = path_or_bytes if isinstance(path_or_bytes, bytes) else Path(path_or_bytes).read_bytes()
    return hashlib.sha256(data).hexdigest()


def read_main():
    """Le o main.lua real (bytes), exige CRLF consistente e devolve (texto LF, sha256 dos bytes)."""
    raw = MAIN.read_bytes()
    if raw.startswith(b"\xef\xbb\xbf"):
        raise StackError("main.lua tem BOM; os builds paralelos assumem sem BOM")
    if raw.count(b"\r\n") != raw.count(b"\n") or raw.count(b"\r") != raw.count(b"\r\n"):
        raise StackError("main.lua nao e CRLF consistente: nao e seguro regravar com CRLF")
    return raw.decode("utf-8").replace("\r\n", "\n"), sha256(raw)


def to_crlf_bytes(text):
    assert "\r" not in text
    return text.replace("\n", "\r\n").encode("utf-8")


# ----------------------------------------------------------------------------------------------- INTERFACE
PAINEL = PAR / "interface/painel.lua"


def painel_rebased(v2=False):
    """painel.lua + reconciliation_extraHud.patch (4 hunks) + uso de logi.eHud quando a IA esta integrada.
    v2=True (pilha v2): + estado de reserva de bmat (logi.rebuildReserve) e piso gratis da cadeia inimiga (CFG.ECHAIN.free)."""
    p = PAINEL.read_text(encoding="utf-8-sig").replace("\r\n", "\n")

    def sub(old, new):
        nonlocal p
        if p.count(old) != 1:
            raise StackError("painel.lua: ancora da reconciliacao nao unica/ausente (%d): %r" % (p.count(old), old[:70]))
        p = p.replace(old, new, 1)

    # cabecalho de proposta isolada -> comentario de projeto
    sub("-- Proposta isolada: substituir somente logi.hudLine; nenhuma escrita em estoques/atores.\n"
        "-- O TextBlock e o atual hudTick continuam sendo o renderizador (0,25 s de tempo real).\n",
        "-- Painel da logistica (INTERFACE, rebaseado na pilha): so leitura, nenhuma escrita em estoques/atores.\n"
        "-- O TextBlock e o hudTick continuam sendo o renderizador (0,25 s de tempo real). logi.extraHud (ECONOMIA) e\n"
        "-- logi.eHud (IA_LOGISTICA) sao opcionais: usados somente se existirem.\n")
    # reconciliation_extraHud.patch, hunk 1-4
    sub('toRef="à refinaria", toDep="ao depósito", dead="destruído" }',
        'toRef="à refinaria", toDep="ao depósito", returnCargo="retornando carga à fábrica", dead="destruído" }')
    sub('string.format("%d munição + %d camisas (caixas)", cargo.ammo, cargo.shirts)',
        'string.format("%d munição + %d camisas (caixas)", cargo.ammo or 0, cargo.shirts or 0)')
    # ECONOMIA: a carga do caminhao pode ter fuzis/bandagens (caixas); sem isto o painel mostraria "0 munição + 0 camisas".
    sub('string.format("%d munição + %d camisas (caixas)", cargo.ammo or 0, cargo.shirts or 0)\n            or string.format("%.0f sucata", tr.salv or 0)',
        'string.format("%d munição + %d camisas (caixas)", cargo.ammo or 0, cargo.shirts or 0)\n'
        '            .. ((cargo.rifle or 0) > 0 and string.format(" + %d fuzis", cargo.rifle) or "")\n'
        '            .. ((cargo.medical or 0) > 0 and string.format(" + %d bandagens", cargo.medical) or "")\n'
        '            or string.format("%.0f sucata", tr.salv or 0)')
    sub('(tr.state == "toField" and "campo" or tr.state == "toRef" and "refinaria" or',
        '(tr.state == "returnCargo" and "fábrica" or tr.state == "toField" and "campo" or tr.state == "toRef" and "refinaria" or')
    sub('    return table.concat(lines, "\\n")\nend',
        '    return table.concat(lines, "\\n") .. (logi.extraHud and logi.extraHud() or "")\nend')
    # IA_LOGISTICA: combat.cargo virou alias (soldados que a frente equipa); a linha informativa e logi.eHud.
    sub('''    if combat.mode ~= "assault" then
        lines[#lines + 1] = string.format("INIMIGO | carga %d%s", combat.cargo or 0,
            #(logi.foes or {}) > 0 and " | comboio na estrada" or "")
    end
''', '''    if combat.mode ~= "assault" then
        local chain = logi.eHud and logi.eHud() or nil  -- cadeia inimiga real (IA_LOGISTICA); eHud devolve " | INIMIGO: ..."
        if chain then
            chain = chain:gsub("^ | ", "")
            if chain ~= "" then lines[#lines + 1] = chain end
        else
            lines[#lines + 1] = string.format("INIMIGO | carga %d%s", combat.cargo or 0,
                #(logi.foes or {}) > 0 and " | comboio na estrada" or "")
        end
    end
''')
    if v2:
        # reserva de bmat (patch_reserva_bmat): a fabrica deixa de iniciar receita para juntar o preco do caminhao destruido
        sub('        fab = logi.nextKind() and "aguarda bmat" or "parada: demanda atendida"\n',
            '''        local keep = logi.rebuildReserve and logi.rebuildReserve() or 0
        local kind = logi.nextKind()
        local rc = kind and C.recipes[kind]
        if keep > 0 and rc and logi.bmat - (rc.bmat or 0) < keep then
            fab = string.format("guarda %d bmat para reconstruir caminhão (bmat %.0f)", keep, logi.bmat)
        else
            fab = kind and "aguarda bmat" or "parada: demanda atendida"
        end
''')
        # piso gratis por onda da cadeia inimiga (CFG.ECHAIN.free): o que a onda recebe mesmo com a cadeia cortada
        sub('            if chain ~= "" then lines[#lines + 1] = chain end\n',
            '''            if chain ~= "" then
                lines[#lines + 1] = chain .. (CFG.ECHAIN and string.format(" | piso grátis %d/onda", CFG.ECHAIN.free) or "")
            end
''')
    return p.rstrip("\n") + "\n"


def interface_build(s, v2=False):
    """Troca a funcao logi.hudLine inteira (qualquer variante: original, com ECONOMIA, com IA). v2: painel da pilha v2."""
    start = "function logi.hudLine()\n"
    if s.count(start) != 1:
        raise StackError("INTERFACE: 'function logi.hudLine()' nao unica/ausente (%d)" % s.count(start))
    a = s.index(start)
    b = s.index("\nend\n", a) + len("\nend\n")
    tail = "\n-- Comboio inimigo (lote 13)"
    if not s[b:].startswith(tail):
        raise StackError("INTERFACE: apos logi.hudLine nao vem '-- Comboio inimigo (lote 13)'; limite da funcao mudou")
    new = painel_rebased(v2)
    new_fn = new[new.index(start):]
    return s[:a] + new_fn + s[b:]


# ----------------------------------------------------------------------------------------------- pilha
ACAB = PAR / "logistics_ai/finishing"   # entregas v2 (somente leitura): IA calibrada, reserva de bmat, PERSISTENCIA v2


def stages(source, variant="v1"):
    """Devolve [(nome, texto)] cumulativo, em ordem. `source` e o main.lua real em LF.

    v1: ECONOMIA > IA_LOGISTICA > INTERFACE > PERSISTENCIA                         (candidate/)
    v2: ECONOMIA > IA_LOGISTICA v2 > reserva de bmat > INTERFACE v2 > PERSISTENCIA v2   (candidate_v2/)
    """
    eco = load_module("par_economia_build", PAR / "economy/build_patch.py")
    out = [("main real", source)]
    if variant == "v1":
        ia = load_module("par_ia_build", PAR / "logistics_ai/build_patch.py")
        pers = load_module("par_pers_build", PAR / "persistence/build_patch.py")
        steps = (("ECONOMIA", lambda s: eco.build(s)),
                 ("IA_LOGISTICA", lambda s: ia.build(s)[0]),
                 ("INTERFACE (painel rebaseado)", interface_build),
                 ("PERSISTENCIA", lambda s: pers.build_on(s)))
    elif variant == "v2":
        ia = load_module("par_ia_build_v2", ACAB / "build_patch_v2.py")
        res = load_module("par_reserva_bmat", ACAB / "patch_bmat_reserve.py")
        pers = load_module("par_pers_build_v2", ACAB / "build_persistence_v2.py")
        steps = (("ECONOMIA", lambda s: eco.build(s)),
                 ("IA_LOGISTICA v2", lambda s: ia.build(s)[0]),
                 ("reserva de bmat", lambda s: res.apply(s)),
                 ("INTERFACE v2 (painel rebaseado)", lambda s: interface_build(s, v2=True)),
                 ("PERSISTENCIA v2", lambda s: pers.build_on(s)))
    else:
        raise StackError("variante desconhecida: %r" % variant)
    cur = source
    for name, fn in steps:
        try:
            cur = fn(cur)
        except (AssertionError, StackError, ValueError) as e:
            raise StackError("ETAPA %s FALHOU: %s: %s" % (name, type(e).__name__, e)) from e
        out.append((name, cur))
    return out


def alt_order_interface_before_ia(source):
    """v1, ordem alternativa (ECONOMIA -> INTERFACE -> IA -> PERSISTENCIA): deve dar o mesmo texto."""
    eco = load_module("par_economia_build", PAR / "economy/build_patch.py")
    ia = load_module("par_ia_build", PAR / "logistics_ai/build_patch.py")
    pers = load_module("par_pers_build", PAR / "persistence/build_patch.py")
    return pers.build_on(ia.build(interface_build(eco.build(source)))[0])


def alt_orders_v2(source):
    """v2: ordens alternativas que devem dar o MESMO texto. Devolve {rotulo: texto}."""
    eco = load_module("par_economia_build", PAR / "economy/build_patch.py")
    ia = load_module("par_ia_build_v2", ACAB / "build_patch_v2.py")
    res = load_module("par_reserva_bmat", ACAB / "patch_bmat_reserve.py")
    pers = load_module("par_pers_build_v2", ACAB / "build_persistence_v2.py")
    ui = lambda s: interface_build(s, v2=True)  # noqa: E731
    e = eco.build(source)
    return {
        "ECO > IA > INTERFACE > reserva > PERS": pers.build_on(res.apply(ui(ia.build(e)[0]))),
        "ECO > INTERFACE > IA > reserva > PERS": pers.build_on(res.apply(ia.build(ui(e))[0])),
        "ECO > INTERFACE > reserva > IA > PERS": pers.build_on(ia.build(res.apply(ui(e)))[0]),
        "ECO > IA > reserva > PERS > INTERFACE": ui(pers.build_on(res.apply(ia.build(e)[0]))),
    }


def udiff(a, b, fa=HEADER, fb=HEADER):
    return "".join(difflib.unified_diff(a.splitlines(True), b.splitlines(True), fromfile="a/" + fa, tofile="b/" + fb))


def build_candidate(variant="v1"):
    """Fonte unica para os testes: (source_lf, sha_real, [(nome, texto)])."""
    source, sha = read_main()
    return source, sha, stages(source, variant)


def main(variant="v1"):
    source, sha_before = read_main()
    st = stages(source, variant)
    final = st[-1][1]
    sfx = "" if variant == "v1" else "_v2"
    out = HERE / ("candidato" + sfx)
    out.mkdir(exist_ok=True)
    cand = out / "main.lua"
    cand.write_bytes(to_crlf_bytes(final))
    full = udiff(source, final)
    # stack.diff tem CRLF como o main.lua real (aplica direto com `git apply -p1`/`patch -p1` no arquivo CRLF);
    # stack_lf.diff e a mesma coisa em LF, so para leitura/revisao.
    HERE.joinpath("pilha%s.diff" % sfx).write_bytes(to_crlf_bytes(full))
    HERE.joinpath("pilha%s_lf.diff" % sfx).write_text(full, encoding="utf-8", newline="\n")
    names = [n for n, _ in st]
    i = [k for k, n in enumerate(names) if n.startswith("INTERFACE")][0]
    HERE.joinpath("painel_rebase%s.patch" % sfx).write_text(udiff(st[i - 1][1], st[i][1]), encoding="utf-8", newline="\n")
    sha_after = sha256(MAIN)
    assert sha_before == sha_after, "main.lua real MUDOU durante o build (nao deveria)"
    out.joinpath("SHA256.txt").write_text(
        "variante: %s (%s)\nmain.lua real (antes) : %s\nmain.lua real (depois): %s\niguais: %s\n%s/main.lua (CRLF): %s\n"
        % (variant, " > ".join(names[1:]), sha_before, sha_after, sha_before == sha_after, out.name, sha256(cand)),
        encoding="utf-8", newline="\n")
    print("== variante %s: %s" % (variant, " > ".join(names[1:])))
    for (n0, t0), (n1, t1) in zip(st, st[1:]):
        d = udiff(t0, t1).splitlines()[2:]
        print("etapa OK: %-34s +%d/-%d linhas" % (n1, sum(1 for l in d if l.startswith("+")), sum(1 for l in d if l.startswith("-"))))
    print("main.lua real SHA256 antes/depois: %s / %s (iguais)" % (sha_before, sha_after))
    print("%s/main.lua SHA256 (CRLF):  %s" % (out.name, sha256(cand)))
    print("pilha%s.diff (CRLF), pilha%s_lf.diff e painel_rebase%s.patch (LF) gerados" % (sfx, sfx, sfx))


if __name__ == "__main__":
    args = [a.lstrip("-") for a in sys.argv[1:]] or ["v1"]   # `v1` (padrao), `v2` ou `all`
    variants = ["v1", "v2"] if "all" in args else [a for a in args if a in ("v1", "v2")]
    if not variants:
        print("uso: build_stack.py [v1|v2|all]")
        sys.exit(2)
    try:
        for v in variants:
            main(v)
    except StackError as e:
        print("FALHA:", e)
        sys.exit(1)
