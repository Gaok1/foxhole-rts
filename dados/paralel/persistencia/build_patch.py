"""Gera o main.lua candidato da PERSISTENCIA sem tocar no main.lua real.

Ordem obrigatoria: fonte atual -> patch ECONOMIA (dados/paralel/economia/build_patch.py, importado e aplicado
aqui em memoria) -> patch PERSISTENCIA. Ancoras exatas e unicas (fail-closed): se o main.lua ou o patch da
economia mudarem, o build para em vez de aplicar por aproximacao.

Saidas (todas nesta pasta):
  candidato/main.lua            candidato completo (economia + persistencia)
  persistencia.patch            diff economia-candidato -> candidato final (aplicar DEPOIS do patch da economia)
  persistencia_completo.patch   diff main.lua atual -> candidato final (referencia)
Uso (raiz do repo, bash): PYTHONPATH=D:/tools/pylibs python dados/paralel/persistencia/build_patch.py
"""
from pathlib import Path
import difflib
import importlib.util
import sys

sys.dont_write_bytecode = True  # nao gravar __pycache__ nas pastas de outros agentes ao importar os builds deles

HERE = Path(__file__).resolve().parent
ROOT = HERE.parents[2]
ECON = ROOT / "dados/paralel/economia/build_patch.py"
IA = ROOT / "dados/paralel/ia_logistica/build_patch.py"


def economy_build():
    spec = importlib.util.spec_from_file_location("economia_build_patch", ECON)
    mod = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(mod)
    return mod.build


def read(name):
    return HERE.joinpath(name).read_text(encoding="utf-8-sig")


OLD_COMMENT = '''-- Salvar e continuar (Ctrl+F6). Com ondas automaticas, a partida e gravada a cada SAVE_EVERY s em SAVE_FILE
-- (Lua "return {...}", lido com load num ambiente vazio): onda, placar, mao de obra, dificuldade, pontos e
-- donos, barreiras, trincheiras e cada soldado vivo dos dois lados (classe, posicao, vida, abates, municao).
-- Vitoria ou derrota apagam o save. Caixas, morteiros e alvos nao sao gravados (duram segundos).
'''
NEW_COMMENT = '''-- Salvar e continuar (Ctrl+F6). Com ondas automaticas, a partida e gravada a cada SAVE_EVERY s em SAVE_FILE
-- (texto "return {...}" lido por sv.decode, parser de literais; nunca load/dofile): onda, placar, mao de obra,
-- dificuldade, pontos e donos, barreiras, trincheiras, postos, arames, cada soldado vivo dos dois lados,
-- logistica (schema da ECONOMIA), carteira/infraestrutura implantada e estoque do comboio inimigo (schema v2).
-- Vitoria ou derrota apagam o save. Caixas, morteiros, alvos, rotas e comboios em transito nao sao gravados.
'''

OLD_PARSE = '''function sv.parse(txt)
    local chunk = load(txt or "", "save", "t", {})
    if not chunk then return nil end
    local ok, d = pcall(chunk)
    if ok and type(d) == "table" and d.v == 1 then return d end
    return nil
end

'''
OLD_SAVE_READ_CLEAR = '''function sv.save()
    if not combat.auto or combat.won or #squad == 0 then return false end
    local f = io.open(CFG.SAVE_FILE, "w")
    if not f then return false end
    f:write("return " .. sv.ser(sv.collect()) .. "\\n")
    f:close()
    return true
end

function sv.read()
    local f = io.open(CFG.SAVE_FILE, "r")
    if not f then return nil end
    local txt = f:read("*a")
    f:close()
    return sv.parse(txt)
end

function sv.clear() os.remove(CFG.SAVE_FILE) end

'''
OLD_LOAD = '''function sv.load()
    if not isLocalAuthority() then return false end
    local d = sv.read()
    if not d then notify("nenhuma partida salva", 3.0); return false end
    local here = sv.map()
    if d.map and here and d.map ~= here then notify("a partida salva é de outro mapa (" .. d.map .. ")", 4.0); return false end
    if d.logi and not logi.ready() then return false end
    local n = sv.restore(d)
    if d.logi then pcall(logi.restore, d.logi) end
    local where = combat.mode == "assault" and string.format("assalto, pontos inimigos %d/%d", pointsOwned(CFG.ENEMY_TEAM), #points)
        or string.format("onda %d/%d", combat.wave, CFG.WAVES_TO_WIN)
    notify(string.format("PARTIDA CONTINUADA (%s): %s, %d soldados, %d inimigos, mão de obra %.0f",
        CFG.DIFFICULTIES[S.difficulty].name, where, n, #enemies, economy.manpower), 8.0)
    log(string.format("save carregado: onda %d, %d soldados, %d inimigos, %d pontos, %d barreiras, %d trincheiras, %d postos, %d arames",
        combat.wave, n, #enemies, #points, #structures, #S.trenches, #S.tents, #S.wires))
    return true
end

'''


def build_on(s):
    """Aplica somente a PERSISTENCIA sobre um texto que ja contem o patch da ECONOMIA."""
    def replace(old, new):
        nonlocal s
        assert s.count(old) == 1, ("âncora não única/ausente", old[:80], s.count(old))
        s = s.replace(old, new, 1)

    assert "function logi.validateSave(d)" in s and "version=2" in s, "aplicar o patch da ECONOMIA antes"
    assert "function logi.applyPlan(" not in s and "CFG.PERSIST" not in s, "persistência já aplicada"
    replace(read("implantacao.before.lua"), read("implantacao.after.lua"))
    replace("""function logi.deployWallet()
    local id = world():GetFullName() .. ":" .. tostring(world():GetAddress())
    if not S.deploy or S.deploy.world ~= id then S.deploy = { world = id, bmat = CFG.DEPLOY.budget, spent = 0 } end
    return S.deploy
end
""", """-- Identidade desta CARGA do mundo (endereco muda a cada carga). Nunca vai para o save.
function logi.walletId()
    return world():GetFullName() .. ":" .. tostring(world():GetAddress())
end

function logi.deployWallet()
    local id = logi.walletId()
    if not S.deploy or S.deploy.world ~= id then
        S.deploy = { world = id, budget = CFG.DEPLOY.budget, bmat = CFG.DEPLOY.budget, spent = 0, built = {} }
    end
    return S.deploy
end
""")
    replace(OLD_COMMENT, NEW_COMMENT)
    replace("local d = { v = 1, map = sv.map(), diff = S.difficulty,",
            "local d = { v = 2, map = sv.map(), world = sv.worldPath(), diff = S.difficulty,")
    replace("        q.dug, q.wired = pt.dug or nil, pt.wired or nil\n    end\n    return d\nend\n",
            "        q.dug, q.wired = pt.dug or nil, pt.wired or nil\n    end\n"
            "    d.infra, d.enemy = sv.infraSnapshot(), sv.enemySnapshot()\n    return d\nend\n")
    replace(OLD_PARSE, "")
    replace(OLD_SAVE_READ_CLEAR, "")
    # Com a IA_LOGISTICA aplicada antes, a linha de restauracao da logistica dela substitui a original.
    ia_line = "    if d.logi then pcall(logi.restore, d.logi); pcall(logi.eRestore, d.elogi) end\n"
    plain_line = "    if d.logi then pcall(logi.restore, d.logi) end\n"
    if s.count(OLD_LOAD.replace(plain_line, ia_line)) == 1:
        replace(OLD_LOAD.replace(plain_line, ia_line), "")
    else:
        replace(OLD_LOAD, "")
    replace("-- Recria a partida de d (tabela de sv.collect) sobre um campo limpo.\n",
            read("persistencia.lua").rstrip() + "\n\n-- Recria a partida de d (tabela de sv.collect) sobre um campo limpo.\n")
    assert "load(txt" not in s, "leitura de save ainda executa código"
    return s


def build(source):
    """Ordem principal: main -> ECONOMIA -> PERSISTENCIA."""
    return build_on(economy_build()(source))


def build_with_ia(source):
    """Ordem com a cadeia inimiga: main -> ECONOMIA -> IA_LOGISTICA -> PERSISTENCIA (a IA ancora na linha
    original de sv.load, que a PERSISTENCIA substitui; por isso a IA vem antes)."""
    spec = importlib.util.spec_from_file_location("ia_logistica_build_patch", IA)
    mod = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(mod)
    return build_on(mod.build(economy_build()(source))[0])


def diff(a, b, fa, fb):
    return "".join(difflib.unified_diff(a.splitlines(True), b.splitlines(True), fromfile=fa, tofile=fb))


if __name__ == "__main__":
    source = ROOT.joinpath("mod/FoxholeRTS/Scripts/main.lua").read_text(encoding="utf-8")
    econ = economy_build()(source)
    final = build_on(econ)
    out = HERE / "candidato"
    out.mkdir(exist_ok=True)
    out.joinpath("main.lua").write_text(final, encoding="utf-8", newline="\r\n")  # CRLF como o main.lua real
    HERE.joinpath("persistencia.patch").write_text(
        diff(econ, final, "a/mod/FoxholeRTS/Scripts/main.lua (com ECONOMIA)", "b/mod/FoxholeRTS/Scripts/main.lua"),
        encoding="utf-8", newline="\n")
    HERE.joinpath("persistencia_completo.patch").write_text(
        diff(source, final, "a/mod/FoxholeRTS/Scripts/main.lua", "b/mod/FoxholeRTS/Scripts/main.lua"),
        encoding="utf-8", newline="\n")
    msg = "candidato/main.lua, persistencia.patch e persistencia_completo.patch gerados"
    try:  # pilha opcional com a IA_LOGISTICA (entrega paralela em andamento)
        spec = importlib.util.spec_from_file_location("ia_logistica_build_patch", IA)
        ia = importlib.util.module_from_spec(spec)
        spec.loader.exec_module(ia)
        with_ia = ia.build(econ)[0]
        final_ia = build_on(with_ia)
        out.joinpath("main_com_ia.lua").write_text(final_ia, encoding="utf-8", newline="\r\n")
        HERE.joinpath("persistencia_sobre_ia.patch").write_text(
            diff(with_ia, final_ia, "a/mod/FoxholeRTS/Scripts/main.lua (com ECONOMIA+IA_LOGISTICA)", "b/mod/FoxholeRTS/Scripts/main.lua"),
            encoding="utf-8", newline="\n")
        msg += "; candidato/main_com_ia.lua e persistencia_sobre_ia.patch (ordem ECONOMIA -> IA_LOGISTICA -> PERSISTENCIA)"
    except Exception as e:  # noqa: BLE001
        msg += f"; pilha com IA_LOGISTICA NÃO gerada ({type(e).__name__}: {e})"
    print(msg + "; main.lua real intacto")
