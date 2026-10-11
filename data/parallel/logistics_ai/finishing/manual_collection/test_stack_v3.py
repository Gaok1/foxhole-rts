"""COLETA_MANUAL: COPIA ADAPTADA de integration_rehearsal/test_stack.py (variante v2) apontando ao candidate_v3 =
candidate_v2 (ECONOMIA > IA v2 > reserva_bmat > INTERFACE v2 > PERSISTENCIA v2) + coleta manual (build_coleta.apply).
Todas as etapas do original sao mantidas; cada mudanca de expectativa/caminho esta marcada com `V3:` (diff em diffs/test_stack_v3.diff).
Original (v2) abaixo:

Uso (raiz do repo, bash):
  PYTHONPATH=D:/tools/pylibs PYTHONDONTWRITEBYTECODE=1 python data/parallel/logistics_ai/finishing/manual_collection/test_stack_v3.py

O main.lua real so e lido. Os testes das outras pastas NAO sao editados: cada um e executado em memoria por
exec() de uma COPIA do codigo-fonte com a(s) linha(s) de obtencao do candidato trocadas (tecnica ja usada por
logistics_ai/test_orders_candidate.py e persistence/test_regression.py). Cada etapa imprime PASS/FAIL; a saida
detalhada vai para test_output.txt (esta pasta). Nada aqui prova fisica Unreal, rota real, input, equilibrio
ou desempenho: isso e laboratorio.
"""
import sys

sys.dont_write_bytecode = True

import contextlib  # noqa: E402
import io  # noqa: E402
import re  # noqa: E402
import subprocess  # noqa: E402
import tempfile  # noqa: E402
import time  # noqa: E402
import traceback  # noqa: E402
import types  # noqa: E402
from pathlib import Path  # noqa: E402

from lupa import LuaRuntime  # noqa: E402

HERE = Path(__file__).resolve().parent
ENSAIO = HERE.parents[2] / "integration_rehearsal"   # V3: build_stack.py vive no ensaio (somente leitura)
sys.path.insert(0, str(HERE))
sys.path.insert(0, str(ENSAIO))
import build_pilha as bp  # noqa: E402
import build_coleta  # noqa: E402

ROOT = bp.ROOT
PAR = bp.PAR
TOOLS = ROOT / "tools"
LOG = []          # saida detalhada (vai para test_output.txt)
SUMMARY = []      # (etapa, ok, segundos, nota)


def log(*a):
    LOG.append(" ".join(str(x) for x in a))


def step(name):
    """Decorador: roda a etapa capturando stdout; imprime PASS/FAIL e registra."""
    def deco(fn):
        def run():
            buf = io.StringIO()
            t0 = time.time()
            ok, note = True, ""
            try:
                with contextlib.redirect_stdout(buf):
                    note = fn() or ""
            except BaseException as e:  # noqa: BLE001
                ok = False
                note = "%s: %s" % (type(e).__name__, str(e)[:400])
                buf.write("\n" + traceback.format_exc())
            dt = time.time() - t0
            SUMMARY.append((name, ok, dt, note))
            print("%s  %s (%.1f s)%s" % ("PASS" if ok else "FAIL", name, dt, ("  -> " + note) if note else ""))
            log("=" * 100, "\n" + ("PASS " if ok else "FAIL ") + name, "\n" + buf.getvalue())
        return run
    return deco


# ------------------------------------------------------------------------------------------------ candidato
VARIANT = "v3"                  # V3: pilha v2 + coleta manual
V2 = True                       # V3: toda a logica de "v2" do original vale (calibracao, reserva, elogi...)
SFX = "_v3"
ACAB = bp.ACAB                  # entregas v2 (somente leitura)
SOURCE, SHA_BEFORE, STAGES = bp.build_candidate("v2")
STAGES = STAGES + [("COLETA MANUAL", build_coleta.apply(STAGES[-1][1]))]   # V3: ultima etapa
CAND = STAGES[-1][1]            # texto LF do candidato v3
CAND_V2 = STAGES[-2][1]         # V3: candidato v2 (base da coleta)
CAND_LEGACY = CAND.replace("manualStart = true,", "manualStart = false,", 1)   # V3: mesma pilha com o inicio antigo (3 caminhoes, 1100)
assert CAND_LEGACY != CAND
CAND_FILE = HERE / "candidate_v3" / "main.lua"
CAND_V2_FILE = ENSAIO / "candidate_v2" / "main.lua"
MAIN_FILE = bp.MAIN


def exec_src(text, name, g):
    exec(compile(text, name, "exec"), g)


def swap_once(text, old, new, what):
    assert text.count(old) == 1, "%s: ancora nao unica (%d): %r" % (what, text.count(old), old[:70])
    return text.replace(old, new, 1)


ORDERS_SRC_LINE = 'source = (Path(__file__).resolve().parents[1] / "mod/FoxholeRTS/Scripts/main.lua").read_text(encoding="utf-8")'
CONVOY_START = "-- enemy convoy: missing cargo shrinks the wave; arriving adds cargo; our soldiers nearby destroy it\n"
CONVOY_END = 'assert(cv2.state == "dead" and api.combat.convoysCut == cut0 + 1)\n'
CONVOY_BLOCK = (ACAB / "test_orders_convoy_block_v2.lua") if V2 else (PAR / "logistics_ai/test_orders_convoy_block.lua")


def run_test_orders(candidate_text, swap):
    s = (TOOLS / "test_orders.py").read_text(encoding="utf-8")
    s = swap_once(s, ORDERS_SRC_LINE, "source = __CANDIDATE", "tools/test_orders.py")
    if swap:
        assert s.count(CONVOY_START) == 1 and s.count(CONVOY_END) == 1, "bloco do comboio mudou na suite"
        a = s.index(CONVOY_START)
        b = s.index(CONVOY_END, a) + len(CONVOY_END)
        s = s[:a] + CONVOY_BLOCK.read_text(encoding="utf-8") + s[b:]
    exec_src(s, "tools/test_orders.py[candidato]", {"__file__": str(TOOLS / "test_orders.py"), "__name__": "__main__",
                                                    "__CANDIDATE": candidate_text})


def scaffold():
    t = (TOOLS / "test_orders.py").read_text(encoding="utf-8")
    a = t.index("lua.execute('''") + len("lua.execute('''")
    return t[a:t.index("''')", a)]


SCAFFOLD = scaffold()


def top_level_locals(text):
    """Mesma contagem de tools/check_globals.py (linhas que comecam em `local`)."""
    top = 0
    for line in text.splitlines():
        m = re.match(r"local\s+function\s+\w+", line)
        if m:
            top += 1
            continue
        m = re.match(r"local\s+([\w\s,]+?)(?:=|$)", line)
        if m:
            top += len([n for n in m.group(1).split(",") if n.strip()])
    return top


def lua_runtime(version):
    import importlib
    return importlib.import_module("lupa." + version).LuaRuntime()


def compiles(version, text):
    lua = lua_runtime(version)
    ok, err = lua.eval("function(s) local f, e = load(s, '=candidato', 't'); return f ~= nil, e end")(text)
    return bool(ok), err


# ------------------------------------------------------------------------------------------------ etapas
@step("00 integridade: build reproduz candidato%s/main.lua (CRLF) e main.lua real intacto" % SFX)
def t_integridade():
    disk = CAND_FILE.read_bytes()
    assert disk == bp.to_crlf_bytes(CAND), "candidate_v3/main.lua em disco diferente do build atual: rode build_collection.py"
    assert CAND_V2_FILE.read_bytes() == bp.to_crlf_bytes(CAND_V2), "V3: candidate_v2 em disco diferente do build (rode build_stack.py v2)"
    assert disk.count(b"\r\n") == disk.count(b"\n") == disk.count(b"\r"), "candidato nao e CRLF consistente"
    assert bp.sha256(MAIN_FILE) == SHA_BEFORE, "main.lua real mudou durante os testes"
    names = [n for n, _ in STAGES]
    return "SHA256 main real %s...; etapas: %s" % (SHA_BEFORE[:12], " > ".join(names[1:]))


@step("01 sintaxe (lupa Lua 5.4 = UE4SS e 5.5) + limite de 200 locais por chunk")
def t_sintaxe():
    notes = []
    for v in ("lua54", "lua55"):
        ok, err = compiles(v, CAND)
        assert ok, "%s nao compila: %s" % (v, err)
        # folga real: maior numero de locais extras que o chunk aceita (o compilador conta de verdade)
        lo, hi = 0, 250
        while lo < hi:
            mid = (lo + hi + 1) // 2
            extra = "\nlocal " + ",".join("__z%d" % i for i in range(mid)) + "\n"
            if compiles(v, CAND + extra)[0]:
                lo = mid
            else:
                hi = mid - 1
        notes.append("%s: compila; folga real %d locais (=> %d ativos no fim do chunk)" % (v, lo, 200 - lo))
    real = top_level_locals(SOURCE)
    cand = top_level_locals(CAND)
    for n, t in STAGES:
        log("locais de topo (check_globals) apos %-30s: %d" % (n, top_level_locals(t)))
    assert cand <= 180, "locais de topo %d > 180 (limite do check_globals)" % cand
    return "locais de topo (contagem do check_globals): main real %d -> candidato %d; %s" % (real, cand, "; ".join(notes))


@step("02 tools/check_globals.py contra o candidato")
def t_check_globals():
    base = subprocess.run([sys.executable, "-B", str(TOOLS / "check_globals.py"), str(MAIN_FILE)], capture_output=True, text=True)
    r = subprocess.run([sys.executable, "-B", str(TOOLS / "check_globals.py"), str(CAND_FILE)], capture_output=True, text=True)
    print("--- main real: rc=%d\n%s\n--- candidato: rc=%d\n%s%s" % (base.returncode, base.stdout, r.returncode, r.stdout, r.stderr))
    assert r.returncode == 0, "check_globals reprovou o candidato:\n" + r.stdout
    warn = [l for l in r.stdout.splitlines() if "aviso" in l]
    assert not warn, "avisos de sombra de nome de topo:\n" + "\n".join(warn)
    return "rc=0, sem saida (main real: rc=%d)" % base.returncode


@step("03a tools/test_orders.py no main real (controle, sem mudanca)")
def t_orders_controle():
    run_test_orders(SOURCE, swap=False)


@step("03b tools/test_orders.py contra o candidato (bloco 'enemy convoy' da IA%s)" % (" v2" if V2 else ""))
def t_orders_candidato():
    # V3: a suite roda com as ADAPTACOES documentadas em test_orders_v3.py (implantacao sem caminhao de recurso)
    import test_orders_v3
    test_orders_v3.main(CAND)


@step("04 tools/test_costs.py e tools/test_inventory_probe.py (independentes do main.lua)")
def t_tools_independentes():
    for name in ("test_costs.py", "test_inventory_probe.py"):
        txt = (TOOLS / name).read_text(encoding="utf-8")
        assert "main.lua" not in txt, name + " passou a depender do main.lua: adaptar"
        r = subprocess.run([sys.executable, "-B", str(TOOLS / name)], capture_output=True, text=True, cwd=str(ROOT))
        print(name, "rc=", r.returncode, r.stdout, r.stderr)
        assert r.returncode == 0, name + " falhou:\n" + r.stdout + r.stderr
    return "ambos PASS; nao leem o main.lua (nada a apontar para o candidato)"


@step("05 economy/test_integration.py contra o candidato")
def t_economia():
    t = (PAR / "economy/test_integration.py").read_text(encoding="utf-8")
    t = swap_once(t, "from build_patch import build, ROOT, HERE\n", "", "economy/test_integration.py")
    t = swap_once(t, "proposal=build(source)", "proposal=__CANDIDATE", "economy/test_integration.py")
    exec_src(t, "economy/test_integration.py[candidato]", {"__name__": "__main__", "ROOT": ROOT, "__CANDIDATE": CAND})


@step("06 logistics_ai/test_ia_logistica%s.py contra o candidato (25x600 passos aleatorios + partidas)" % SFX)
def t_ia():
    p = (ACAB / "test_logistics_ai_v2.py") if V2 else (PAR / "logistics_ai/test_logistics_ai.py")
    t = p.read_text(encoding="utf-8")
    t = swap_once(t, "from build_patch_v2 import build, stacked  # noqa: E402" if V2 else "from build_patch import build, stacked  # noqa: E402",
                  "stacked = lambda s: __CANDIDATE  # noqa: E731", "ia test import")
    t = swap_once(t, 'run("main+IA", lambda s: build(s)[0])\nrun("main+ECONOMIA+IA", stacked)\nprint("PASS: test_ia_logistica (2 candidatos)")',
                  'run("pilha completa", stacked)\nprint("PASS: test_ia_logistica (pilha completa)")', "ia test runs")
    exec_src(t, "logistics_ai/test_ia_logistica%s.py[candidato]" % SFX, {"__name__": "__main__", "__file__": str(p), "__CANDIDATE": CAND})


# V3: expectativas da suite de persistencia que dependem do tamanho da implantacao (antes 2 estruturas + 3 caminhoes = 1100, 5 atores;
# agora 2 estruturas + 2 caminhoes = 1000, 4 atores). A suite tambem roda a pilha SEM a coleta (main + ECONOMIA + PERSISTENCIA_v2),
# que continua com 1100/5: por isso cada troca e CONDICIONAL a pilha candidata (_v3() == CANDIDATE e o candidato v3). Valem para todas
# as ocorrencias; o resto da suite fica intacto.
V3_PERSIST_ADAPT = [
    ('H.spawned") == 5', 'H.spawned") == (4 if _v3() else 5)', "atores criados pela implantacao: 5 -> 4"),
    ('"carteira=0/1100/5" in ledger', '("carteira=0/1000/4" if _v3() else "carteira=0/1100/5") in ledger',
     "carteira esperada apos a implantacao: 0/1100/5 -> 0/1000/4"),
    ("H.live('BPTruckW_C')\") == 3", "H.live('BPTruckW_C')\") == (2 if _v3() else 3)", "caminhoes vivos apos refazer a implantacao: 3 -> 2"),
    ('b.eval("api.S.deploy.bmat") == 300', 'b.eval("api.S.deploy.bmat") == (200 if _v3() else 300)', "saldo da carteira (1000 - 800): 300 -> 200"),
    ("RESULTS = []\n", "RESULTS = []\n\n\ndef _v3():\n    return CANDIDATE is __CANDIDATE\n\n\n", "helper _v3() (pilha candidata v3?)"),
]

# V3: test_elogi.py t_no_module: um save da pilha v3 (implantacao de 2 caminhoes pagos) lido por um mod SEM a coleta (que exige 3
# caminhoes) e recusado por desenho (ja ocorre entre v3 e v2: faltam 3 e o save so pagou 2). Para continuar testando o que o caso testa
# (so o elogi e descartado), o mundo de carga ganha 1 caminhao nativo (faltam 2 = pagos 2).
V3_ELOGI_ADAPT = [
    ('    tp.CANDIDATE = STACKS[NO_IA]\n    b = tp.new_load(v, files)\n    b.execute("H.newWorld()")\n',
     '    tp.CANDIDATE = STACKS[NO_IA]\n    b = tp.new_load(v, files)\n    b.execute("H.newWorld({trucks = 1})")  # ADAPTACAO v3: 1 caminhao nativo (mod sem coleta exige 3; o save pagou 2)\n',
     "t_no_module: mundo de carga com 1 caminhao nativo (o mod sem a coleta exige 3 caminhoes; o save v3 pagou 2)"),
]


def persist_v2_source(legacy=False):
    """Texto de finishing/test_persistence_v2.py com as 3 pilhas dele trocadas por: main+ECONOMIA+PERSISTENCIA_v2 (cenario
    'mod sem IA', que o test_elogi usa) e o CANDIDATO v2 completo (com INTERFACE)."""
    p = ACAB / "test_persistence_v2.py"
    t = p.read_text(encoding="utf-8")
    t = swap_once(t, '    STACKS["main+ECONOMIA+IA_v2+PERSISTENCIA_v2"] = build_patch.build_with_ia(SOURCE)\n'
                     '    STACKS["pilha completa (ECONOMIA+IA_v2+reserva bmat+PERSISTENCIA_v2)"] = build_patch.build_full(SOURCE)\n',
                  '    STACKS["pilha v2 completa (ECO+IA_v2+reserva+INTERFACE+PERS_v2)"] = __CANDIDATE\n', "persistencia_v2 STACKS")
    if not legacy:   # V3: numeros da implantacao manual; legacy=True roda a suite SEM nenhuma alteracao numerica (inicio antigo)
        for old, new, why in V3_PERSIST_ADAPT:
            assert t.count(old) >= 1, "adaptacao sem alvo: " + why
            t = t.replace(old, new)
            print("adaptacao persistencia:", why)
    return p, t


def _elogi(cand, legacy):
    p, t = persist_v2_source(legacy)
    et = (ACAB / "test_elogi.py").read_text(encoding="utf-8")
    if not legacy:
        for old, new, why in V3_ELOGI_ADAPT:
            assert et.count(old) == 1, "adaptacao sem alvo unico: " + why
            et = et.replace(old, new)
            print("adaptacao elogi:", why)
    mod = types.ModuleType("test_persistencia_v2")
    mod.__dict__.update({"__name__": "test_persistencia_v2", "__file__": str(p), "__CANDIDATE": cand})
    exec_src(t, "finishing/test_persistence_v2.py[candidato, modulo]", mod.__dict__)
    assert len(mod.STACKS) == 2 and "pilha v2 completa (ECO+IA_v2+reserva+INTERFACE+PERS_v2)" in mod.STACKS, list(mod.STACKS)
    saved = sys.modules.get("test_persistencia_v2")
    sys.modules["test_persistencia_v2"] = mod
    try:
        e = ACAB / "test_elogi.py"
        exec_src(et, "finishing/test_elogi.py[candidato]", {"__name__": "__main__", "__file__": str(e)})
    finally:
        if saved is None:
            sys.modules.pop("test_persistencia_v2", None)
        else:
            sys.modules["test_persistencia_v2"] = saved


@step("06b finishing/test_elogi.py contra o candidato v3 (politica unica do elogi; 5.4 e 5.5; sem modulo; numeros da implantacao manual)")
def t_elogi():
    _elogi(CAND, False)


@step("06b-L finishing/test_elogi.py contra o candidato v3 com manualStart=false (suite sem NENHUMA alteracao: caminho antigo intacto)")
def t_elogi_legacy():
    _elogi(CAND_LEGACY, True)


@step("06c finishing/test_truck_bmat.py (reserva de bmat; pilha completa = candidato v2)")
def t_bmat():
    p = ACAB / "test_truck_bmat.py"
    t = p.read_text(encoding="utf-8")
    t = swap_once(t, "    import build_persistencia_v2 as bpp  # noqa: E402\n    full = play(make(bpp.build_full), ",
                  "    full = play(make(lambda s: __CANDIDATE), ", "bmat pilha completa")
    exec_src(t, "finishing/test_truck_bmat.py[candidato]", {"__name__": "__main__", "__file__": str(p), "__CANDIDATE": CAND})


@step("07a interface/test_interface.py original (painel.lua da INTERFACE, mock proprio)")
def t_interface_original():
    exec_src((PAR / "interface/test_interface.py").read_text(encoding="utf-8"), "interface/test_interface.py",
             {"__name__": "__main__", "__file__": str(PAR / "interface/test_interface.py")})


def candidate_hudline():
    a = CAND.index("function logi.hudLine()\n")
    b = CAND.index("\nend\n", a) + len("\nend\n")
    return CAND[a:b]


@step("07b interface/test_interface.py com o logi.hudLine do CANDIDATO (mock proprio, sem extraHud/eHud)")
def t_interface_candidato():
    p = PAR / "interface/test_interface.py"
    t = p.read_text(encoding="utf-8")
    t = swap_once(t, "lua.execute(root.joinpath('painel.lua').read_text(encoding='utf-8-sig'))",
                  "lua.execute(__HUDLINE)", "interface/test_interface.py")
    exec_src(t, "interface/test_interface.py[candidato]", {"__name__": "__main__", "__file__": str(p), "__HUDLINE": candidate_hudline()})


HARNESS_TAIL = '''
return {logi=logi, CFG=CFG, combat=combat, points=points, squad=squad, economy=economy, sv=sv, ai=ai,
  hudLine=function() return logi.hudLine() end}
'''

HUD_BODY = r'''
local A = api
local L, C, combat, P = A.logi, A.CFG, A.combat, A.points
local function setup()
    L.reset()
    L.on, L.prio, L.salvage, L.bmat, L.made, L.job, L.t = true, "auto", 12, 100, 0, nil, nil
    L.fac = {ammo=1, shirts=2, rifle=3, medical=4}
    L.base = {name="base", X=0, Y=0, Z=0, ammo=6, shirts=30, rifle=2, medical=5}
    L.factory, L.field, L.refinery = {name="fábrica", X=-3000, Y=0, Z=0}, {X=-5000, Y=0, Z=0}, {X=-4000, Y=0, Z=0}
    L.trucks = {}
    combat.auto, combat.mode, combat.wave, combat.convoys, combat.convoysCut = true, nil, 0, 0, 0
    combat.lastSpawn, combat.nextWaveAt, combat.won = {X=4000, Y=0, Z=0}, nil, false
    for i = #P, 1, -1 do table.remove(P, i) end
    P[1] = {name="A", X=0, Y=0, Z=0, owner=C.FRIENDLY_TEAM}
    L.eReset()
end
local function snap() return A.sv.ser({L.snapshot(), L.eSnapshot()}) end
local function has(t, s) assert(t:find(s, 1, true), "HUD sem '" .. s .. "':\n" .. t) end
local function lacks(t, s) assert(not t:find(s, 1, true), "HUD com '" .. s .. "' indevido:\n" .. t) end

setup()
local dep = L.depotOf(P[1])
dep.ammo, dep.shirts, dep.rifle, dep.medical = 1, 0, 0, 0
L.job = {kind="rifle", left=4, total=70}
L.trucks = {
  {kind="sup", n=1, state="returnCargo", hp=900, dest=L.factory, cargo={ammo=1, shirts=2, rifle=1, medical=1}},
  {kind="sup", n=2, state="toDep", hp=900, dest=dep, cargo={ammo=0, shirts=0, rifle=2, medical=1}},
  {kind="res", n=3, state="idle", hp=900},
  {kind="sup", n=4, state="dead", hp=0, cargo=nil},
}
local before = snap()
local t = A.hudLine(); local first = t
-- ECONOMIA (extraHud): fuzis/bandagens; INTERFACE: estados, cargas e destinos; IA: linha INIMIGO da cadeia real
has(t, "fuzis: 4 s restantes") ; has(t, "(total 70 s)")
has(t, "retornando carga à fábrica"); has(t, "destino fábrica")
has(t, "Fuzis: fábrica 3 caixas"); has(t, "bandagens")
has(t, "caixas fuzis"); has(t, "perdida")
has(t, "1 munição + 2 camisas (caixas) + 1 fuzis + 1 bandagens"); has(t, "0 munição + 0 camisas (caixas) + 2 fuzis + 1 bandagens")
has(t, "INIMIGO: frente equipa"); lacks(t, "INIMIGO | carga")
has(t, "Ctrl+L")
assert(snap() == before, "hudLine alterou estado (deve ser so leitura)")
-- sem logistica
L.on = false; assert(A.hudLine() == "LOGÍSTICA INATIVA"); L.on = true
-- assalto: sem linha inimiga
combat.mode = "assault"; t = A.hudLine(); lacks(t, "INIMIGO"); combat.mode = nil
-- cadeia inimiga recusada aparece (sem erro)
local keep = L.en; L.en = nil
t = A.hudLine(); lacks(t, "INIMIGO")        -- sem cadeia: eHud() == "" e nenhuma linha
L.en = keep
-- caminhao com carga parcial (campos ausentes) nao quebra o painel
L.trucks[1].cargo = {ammo=nil, shirts=nil}
t = A.hudLine(); has(t, "0 munição + 0 camisas")
-- tamanho do painel (gate visual do laboratorio)
local lines = 0; for _ in first:gmatch("[^\n]+") do lines = lines + 1 end
local width = 0; for l in first:gmatch("[^\n]+") do width = math.max(width, utf8.len(l) or #l) end
print(string.format("painel: %d linhas, largura maxima %d caracteres (4 caminhoes, 2 depositos)", lines, width))
return lines .. "x" .. width .. "\n" .. first
'''

CONTRACT_BODY = r'''
local A = api
local L, C, combat, P = A.logi, A.CFG, A.combat, A.points
LoadAsset = function() return {IsValid=function() return true end} end
local function truckActor(x, y)
    return {position={X=x,Y=y,Z=0}, IsValid=function() return true end,
        K2_GetActorLocation=function(self) return self.position end,
        K2_SetActorLocation=function(self,p) self.position=p end, K2_SetActorRotation=function() end,
        SetActorHiddenInGame=function() end, SetActorEnableCollision=function() end, K2_DestroyActor=function() end}
end
mockSpawnActor = function(_, p) return truckActor(p.X, p.Y) end
local function setup()
    L.reset()
    L.on, L.prio, L.salvage, L.bmat, L.made, L.job, L.t, L.pin = true, "auto", 0, 0, 0, nil, nil, nil
    L.fac = {ammo=0, shirts=0, rifle=0, medical=0}
    L.base = {name="base", X=0, Y=0, Z=0, ammo=6, shirts=30, rifle=0, medical=0}
    L.factory, L.field, L.refinery = {name="fábrica", X=-3000, Y=0, Z=0}, {X=-5000, Y=0, Z=0}, {X=-4000, Y=0, Z=0}
    L.trucks = {{kind="sup", n=1, state="idle", hp=900}}
    combat.auto, combat.mode, combat.wave, combat.convoys, combat.convoysCut = true, nil, 0, 0, 0
    combat.lastSpawn, combat.nextWaveAt, combat.won = {X=4000, Y=0, Z=0}, nil, false
    for i = #P, 1, -1 do table.remove(P, i) end
    P[1] = {name="A", X=0, Y=0, Z=0, owner=C.FRIENDLY_TEAM}
    L.eReset()
end
local function boxes(t) return (t and ((t.ammo or 0) + (t.shirts or 0) + (t.rifle or 0) + (t.medical or 0))) or 0 end
local function depTotal(d) return (d.ammo or 0) + (d.shirts or 0) + (d.rifle or 0) + (d.medical or 0) end
local statuses = {"rota_ausente", "bloqueado", "regiao_invalida"}

-- (a) jogador, destino = deposito: o driver so devolve true na chegada; false (qualquer routeStatus) nao entrega
setup()
local tr, dep = L.trucks[1], L.depotOf(P[1])
dep.ammo, dep.shirts, dep.rifle, dep.medical = 0, 0, 0, 0
L.fac = {ammo=1, shirts=1, rifle=1, medical=1}; L.pin = dep
L.drive = function() return true end            -- chegou a fabrica: carrega
L.truckStep(tr, 1, 1)
assert(tr.state == "toDep" and tr.dest == dep and boxes(tr.cargo) == 4 and boxes(L.fac) == 0, "carregou na fabrica")
for _, st in ipairs(statuses) do
    L.drive = function(t) t.routeStatus = st; return false end
    for i = 1, 30 do L.truckStep(tr, 1, 10 + i) end
    assert(tr.state == "toDep" and boxes(tr.cargo) == 4 and depTotal(dep) == 0 and boxes(L.fac) == 0,
        "sem chegada nao ha entrega (" .. st .. ")")
end
L.drive = function() return true end
L.truckStep(tr, 1, 100)
assert(not tr.cargo and tr.state == "idle" and dep.ammo == 1 and dep.shirts == 10 and dep.rifle == 20 and dep.medical == 50, "entrega na chegada")
local snapDep = depTotal(dep)
for i = 1, 5 do L.truckStep(tr, 1, 101 + i) end
assert(depTotal(dep) == snapDep, "entrega uma unica vez")

-- (b) destino perdido: returnCargo, carga fica no caminhao; so a chegada fisica devolve a caixa fechada a fabrica
setup()
tr, dep = L.trucks[1], L.depotOf(P[1])
L.fac = {ammo=0, shirts=0, rifle=2, medical=0}; L.pin = dep
L.drive = function() return true end
L.truckStep(tr, 1, 1)
assert(tr.state == "toDep" and tr.cargo.rifle == 2)
P[1].owner = C.ENEMY_TEAM                                   -- ponto capturado
L.drive = function(t) t.routeStatus = "bloqueado"; return false end
L.truckStep(tr, 1, 2)
assert(tr.state == "returnCargo" and tr.dest == L.factory and tr.cargo.rifle == 2 and L.fac.rifle == 0, "sem credito imediato")
for i = 1, 50 do L.truckStep(tr, 1, 3 + i) end
assert(tr.state == "returnCargo" and tr.cargo.rifle == 2 and L.fac.rifle == 0, "driver false mantem tudo")
-- salvar/restaurar durante o retorno: a carga continua no caminhao, fabrica continua em 0
local snap = L.snapshot()
assert(snap, "snapshot")
L.drive = function() return true end
L.truckStep(tr, 1, 200)
assert(not tr.cargo and tr.state == "idle" and L.fac.rifle == 2, "chegada confirmada devolve uma vez")
L.truckStep(tr, 1, 201); assert(L.fac.rifle + boxes(tr.cargo) == 2, "conservacao: nenhuma caixa duplicada")

-- (c) comboio inimigo: usa o MESMO driver; rota ausente => volta carregado; credito so na chegada
setup()
L.convoyT = 1e9
for i = 1, 400 do clock = clock + 0.5; L.convoyTick(0.5, clock) end         -- retaguarda produz
L.en.front.ammo, L.en.front.shirts = 0, 0
L.en.led.used.ammo, L.en.led.used.shirts = L.en.led.used.ammo + C.ECHAIN.front0.ammo, L.en.led.used.shirts + C.ECHAIN.front0.shirts
assert(L.convoySpawn(clock) and #L.foes == 1)
local cv = L.foes[1]
local front0 = L.en.front.ammo + L.en.front.shirts
L.drive = function(t) t.routeStatus = "rota_ausente"; return false end
for i = 1, math.floor(C.ECHAIN.stuck / 0.5) + 6 do clock = clock + 0.5; L.convoyTick(0.5, clock) end
assert(cv.state == "back" and cv.cargo and L.en.front.ammo + L.en.front.shirts == front0, "preso: volta carregado, frente nao recebe")
L.drive = function() return true end
clock = clock + 0.5; L.convoyTick(0.5, clock)
assert(#L.foes == 0, "chegada na retaguarda encerra o comboio")
assert(L.eAudit(), "razao da cadeia inimiga fechado")

-- (d) driver unico e substituivel: o comboio e os caminhoes chamam logi.drive(tr, dest, dt[, speed])
assert(type(L.drive) == "function")
return "ok"
'''


def run_lua_body(body, candidate_text=None, version=None):
    lua = LuaRuntime() if version is None else lua_runtime(version)
    lua.execute(SCAFFOLD)
    api = lua.execute((candidate_text or CAND) + HARNESS_TAIL)
    lua.globals().api = api
    return lua.execute(body)


@step("07c painel no candidato completo: estados, fuzis/bandagens, returnCargo, linha INIMIGO da IA, so leitura")
def t_interface_integrada():
    res = str(run_lua_body(HUD_BODY))
    size, sample = res.split("\n", 1)
    print("amostra do painel (1a renderizacao do teste):\n" + sample)
    return "hudLine integrado OK (%s linhas x largura)" % size


HUD_V2_BODY = r"""
local A = api
local L, C, combat, P = A.logi, A.CFG, A.combat, A.points
local function setup()
    L.reset()
    L.on, L.prio, L.salvage, L.bmat, L.made, L.job, L.t, L.pin = true, "auto", 12, 100, 0, nil, nil, nil
    L.fac = {ammo=0, shirts=0, rifle=0, medical=0}
    L.base = {name="base", X=0, Y=0, Z=0, ammo=0, shirts=0, rifle=0, medical=0}
    L.factory, L.field, L.refinery = {name="fábrica", X=-3000, Y=0, Z=0}, {X=-5000, Y=0, Z=0}, {X=-4000, Y=0, Z=0}
    L.trucks = {{kind="res", n=1, state="idle", hp=900}, {kind="sup", n=2, state="idle", hp=900}}
    combat.auto, combat.mode, combat.wave, combat.convoys, combat.convoysCut = true, nil, 0, 0, 0
    combat.lastSpawn, combat.nextWaveAt, combat.won = {X=4000, Y=0, Z=0}, nil, false
    for i = #P, 1, -1 do table.remove(P, i) end
    P[1] = {name="A", X=0, Y=0, Z=0, owner=C.FRIENDLY_TEAM}
    L.eReset()
end
local function snap() return A.sv.ser({L.snapshot(), L.eSnapshot()}) end
local function has(t, s) assert(t:find(s, 1, true), "HUD sem '" .. s .. "':\n" .. t) end
local function lacks(t, s) assert(not t:find(s, 1, true), "HUD com '" .. s .. "' indevido:\n" .. t) end
local function line(t, key) for l in t:gmatch("[^\n]+") do if l:find(key, 1, true) then return l end end end
local out = {}

-- 1. reserva de bmat: caminhao de suprimento destruido, bmat abaixo de receita + preco do caminhao
setup()
L.trucks[2].state = "dead"; L.trucks[2].hp = 0
assert(L.rebuildReserve() == C.LOGI.truckCost and L.nextKind(), "pre-condicao: reserva 100 e algo a produzir")
L.bmat = 130
local before = snap()
local t = A.hudLine()
has(t, "Fábrica | guarda 100 bmat para reconstruir caminhão (bmat 130)"); lacks(t, "Fábrica | aguarda bmat")
assert(snap() == before, "hudLine nao pode alterar estado")
L.factoryStep(1); assert(L.job == nil, "a fabrica de fato nao inicia receita (o painel diz a verdade)")
out[#out + 1] = line(t, "Fábrica")
-- bmat suficiente para receita + caminhao: o painel para de dizer que guarda e a fabrica inicia
L.bmat = 300; t = A.hudLine(); lacks(t, "Fábrica | guarda"); L.factoryStep(1); assert(L.job, "com bmat de sobra a fabrica produz")
t = A.hudLine(); has(t, "Fábrica | "); lacks(t, "Fábrica | guarda"); has(t, "s restantes")
-- sem caminhao destruido e sem bmat: texto antigo
setup(); L.bmat = 5; t = A.hudLine(); has(t, "Fábrica | aguarda bmat"); lacks(t, "Fábrica | guarda")
-- caminhao de recurso destruido tambem conta
setup(); L.trucks[1].state = "dead"; L.trucks[1].hp = 0; L.bmat = 130; t = A.hudLine(); has(t, "guarda 100 bmat")
-- dois caminhoes destruidos: reserva 200
setup(); for _, tr in ipairs(L.trucks) do tr.state = "dead"; tr.hp = 0 end; L.bmat = 150; t = A.hudLine(); has(t, "guarda 200 bmat")
-- reconstruido (state != dead): volta ao normal
setup(); L.trucks[2].state = "idle"; L.bmat = 130; t = A.hudLine(); lacks(t, "Fábrica | guarda")

-- 2. linha INIMIGO e o piso gratis (CFG.ECHAIN.free = 5)
setup()
assert(C.ECHAIN.free == 5 and C.ECHAIN.trip == 20.0 and C.ECHAIN.want.ammo == 4 and C.ECHAIN.want.shirts == 20, "calibracao v2")
t = A.hudLine()
has(t, "INIMIGO: frente equipa"); has(t, "| piso grátis 5/onda"); lacks(t, "INIMIGO | carga")
out[#out + 1] = line(t, "INIMIGO")
-- cadeia cortada: frente zerada (consumo registrado no razao) => a onda cai ao piso, e o painel mostra o mesmo numero
L.en.led.used.ammo, L.en.led.used.shirts = L.en.led.used.ammo + L.en.front.ammo, L.en.led.used.shirts + L.en.front.shirts
L.en.front.ammo, L.en.front.shirts = 0, 0
assert(L.eAudit())
t = A.hudLine()
has(t, "INIMIGO: frente equipa 0"); has(t, "piso grátis 5/onda")
out[#out + 1] = line(t, "INIMIGO")
assert(L.waveCut(13) == C.ECHAIN.free, "onda de 13 com a frente vazia recebe exatamente o piso gratis = o que o painel mostra")
-- assalto e sem cadeia: nada de INIMIGO nem piso
combat.mode = "assault"; t = A.hudLine(); lacks(t, "INIMIGO"); lacks(t, "piso"); combat.mode = nil
local keep = L.en; L.en = nil; t = A.hudLine(); lacks(t, "INIMIGO"); lacks(t, "piso"); L.en = keep
-- cadeia recusada (schema): mostra o erro, sem quebrar
L.en.err = "ammo"; t = A.hudLine(); has(t, "cadeia recusada"); L.en.err = nil
local lines = 0; for _ in t:gmatch("[^\n]+") do lines = lines + 1 end
return table.concat(out, "\n")
"""


@step("07d painel v2: reserva de bmat ('guarda N bmat ...') e linha INIMIGO com o piso gratis (free=5)")
def t_interface_v2():
    res = str(run_lua_body(HUD_V2_BODY))
    print("linhas do painel v2:\n" + res)
    return res.replace("\n", " || ")


@step("08-L persistencia_v2 contra o candidato v3 com manualStart=false (suite sem NENHUMA alteracao: caminho antigo intacto)")
def t_persistencia_legacy():
    p, t = persist_v2_source(True)
    exec_src(t, "finishing/test_persistence_v2.py[candidato, legado]", {"__name__": "__main__", "__file__": str(p), "__CANDIDATE": CAND_LEGACY})


@step("08 persistencia_v2 contra o candidato v3 (Lua 5.4 e 5.5, 9 cenarios; numeros da implantacao manual)")
def t_persistencia():
    if V2:
        p, t = persist_v2_source()
        exec_src(t, "finishing/test_persistence_v2.py[candidato]", {"__name__": "__main__", "__file__": str(p), "__CANDIDATE": CAND})
        return
    p = PAR / "persistence/test_persistence.py"
    t = p.read_text(encoding="utf-8")
    t = swap_once(t, "import build_patch  # noqa: E402\n", "build_patch = None\n", "persistencia import")
    t = swap_once(t, 'STACKS = {"main+ECONOMIA+PERSISTENCIA": build_patch.build(SOURCE)}',
                  'STACKS = {"pilha completa (ECO+IA+INTERFACE+PERS)": __CANDIDATE}', "persistencia STACKS")
    t = swap_once(t, '    STACKS["main+ECONOMIA+IA_LOGISTICA+PERSISTENCIA"] = build_patch.build_with_ia(SOURCE)', "    pass", "persistencia IA stack")
    t = swap_once(t, 'CANDIDATE = STACKS["main+ECONOMIA+PERSISTENCIA"]', "CANDIDATE = __CANDIDATE", "persistencia CANDIDATE")
    exec_src(t, "persistence/test_persistence.py[candidato]", {"__name__": "__main__", "__file__": str(p), "__CANDIDATE": CAND})


@step("09 contrato ESTRADAS: driver true so na chegada / routeStatus (jogador, returnCargo, comboio inimigo)")
def t_contrato_estradas():
    # estatico: logi.drive tem uma unica definicao e todo uso consome o retorno numa condicao
    assert CAND.count("function logi.drive(") == 1, "logi.drive deve ter uma unica definicao (ponto de troca da ESTRADAS)"
    uses = [l for l in CAND.splitlines() if "logi.drive(" in l and "function logi.drive(" not in l]
    assert len(uses) >= 6, uses
    for l in uses:
        assert re.search(r"\b(if|elseif)\b.*logi\.drive\(", l), "retorno de logi.drive ignorado: " + l.strip()
    for l in uses:
        log("uso de logi.drive:", l.strip())
    # dinamico
    run_lua_body(CONTRACT_BODY)
    return "%d usos de logi.drive, todos condicionais; driver false (rota_ausente/bloqueado/regiao_invalida) nunca entrega" % len(uses)


def git_apply(dirp, patch, check=False):
    args = ["git", "-c", "core.autocrlf=false", "apply", "--whitespace=nowarn", "-p1"] + (["--check"] if check else []) + [str(patch)]
    r = subprocess.run(args, cwd=str(dirp), capture_output=True, text=True)
    return r.returncode, (r.stdout + r.stderr).strip()


def eol(path):
    b = Path(path).read_bytes()
    crlf, lf, cr = b.count(bytes([13, 10])), b.count(bytes([10])), b.count(bytes([13]))
    return "CRLF" if lf and crlf == lf == cr else ("LF" if cr == 0 else "misto")


@step("10 conflitos e patches entregues: painel.patch x ECONOMIA reproduzido; sequencia dos .patch e stack.diff aplicam limpo")
def t_ordem_patches():
    notes = []
    eco = bp.load_module("par_economia_build", PAR / "economy/build_patch.py")
    if V2:
        seq = [("economy_integrated.patch", PAR / "economy/economy_integrated.patch"),
               ("logistics_ai_v2.patch", ACAB / "logistics_ai_v2.patch"),
               ("bmat_reserve.patch", ACAB / "bmat_reserve.patch"),
               ("painel_rebase_v2.patch", ENSAIO / "painel_rebase_v2.patch"),
               ("persistence_v2_over_ai.patch", ACAB / "persistence_v2_over_ai.patch")]
    else:
        seq = [("economy_integrated.patch", PAR / "economy/economy_integrated.patch"),
               ("logistics_ai.patch", PAR / "logistics_ai/logistics_ai.patch"),
               ("painel_rebase.patch", HERE / "painel_rebase.patch"),
               ("persistence_over_ai.patch", PAR / "persistence/persistence_over_ai.patch")]
    eols = {n: eol(p) for n, p in seq + [("painel.patch", PAR / "interface/painel.patch")]}
    notes.append("fim de linha dos .patch: " + ", ".join("%s=%s" % kv for kv in eols.items()))
    with tempfile.TemporaryDirectory() as td:
        d = Path(td)
        f = d / bp.HEADER
        f.parent.mkdir(parents=True)

        def lf_patch(p):
            """Os .patch alheios tem fim de linha misto (economy/ia/painel em CRLF, persistencia em LF): normaliza p/ LF."""
            q = d / ("n_" + Path(p).name)
            q.write_bytes(Path(p).read_bytes().replace(bytes([13, 10]), bytes([10])))
            return q

        f.write_bytes(SOURCE.encode("utf-8"))                       # LF
        # painel.patch original aplica sozinho no main atual
        rc, out = git_apply(d, lf_patch(PAR / "interface/painel.patch"), check=True)
        assert rc == 0, "painel.patch original nao aplica no main atual: " + out
        notes.append("painel.patch original aplica no main atual (sozinho)")
        # ... e o gerador da ECONOMIA falha depois dele (conflito conhecido)
        assert git_apply(d, lf_patch(PAR / "interface/painel.patch"))[0] == 0
        after_painel = f.read_text(encoding="utf-8")
        try:
            eco.build(after_painel)
            raise AssertionError("ECONOMIA aplicou sobre a INTERFACE: o conflito conhecido sumiu?")
        except AssertionError as e:
            assert "âncora não única" in str(e) and "table.concat(deps" in str(e), "falha diferente do esperado: " + str(e)
            notes.append("conflito reproduzido (ECONOMIA depois de painel.patch): ancora 'table.concat(deps, \" | \"), foe)' ausente")
        # sequencia dos .patch entregues, em ordem
        f.write_bytes(SOURCE.encode("utf-8"))
        for name, p in seq:
            rc, out = git_apply(d, lf_patch(p))
            assert rc == 0, "%s NAO aplica na sequencia: %s" % (name, out)
        final = f.read_text(encoding="utf-8")
        assert final == CAND_V2, "sequencia dos %d .patch diverge do candidato v2 do build_pilha (%d x %d chars)" % (len(seq), len(final), len(CAND_V2))
        notes.append("%s aplicam em sequencia e == candidato v2 (byte a byte, LF)" % ">".join(n.replace(".patch", "") for n, _ in seq))
        # V3: manual_collection_lf.patch (a/main.lua b/main.lua) sobre o candidato v2 == candidato v3
        h = d / "coleta"
        h.mkdir()
        (h / "main.lua").write_bytes(CAND_V2.encode("utf-8"))
        rc, out = git_apply(h, HERE / "manual_collection_lf.patch")
        assert rc == 0, "manual_collection_lf.patch NAO aplica no candidato v2: " + out
        assert (h / "main.lua").read_text(encoding="utf-8") == CAND, "candidato v2 + manual_collection_lf.patch != candidato v3"
        notes.append("manual_collection_lf.patch aplica sobre o candidato v2 e == candidato v3 (LF)")
        # stack_v2.diff (CRLF) aplica direto no main.lua real (CRLF) e reproduz candidate_v2; manual_collection.patch (CRLF) leva a v3
        g = d / "real"
        gf = g / bp.HEADER
        gf.parent.mkdir(parents=True)
        gf.write_bytes(bp.MAIN.read_bytes())
        rc, out = git_apply(g, ENSAIO / "stack_v2.diff")
        assert rc == 0, "stack_v2.diff nao aplica no main real (CRLF): " + out
        assert gf.read_bytes() == CAND_V2_FILE.read_bytes(), "stack_v2.diff aplicado != candidate_v2/main.lua"
        k = d / "crlf"
        k.mkdir()
        (k / "main.lua").write_bytes(CAND_V2_FILE.read_bytes())
        rc, out = git_apply(k, HERE / "manual_collection.patch")
        assert rc == 0, "manual_collection.patch (CRLF) nao aplica em candidate_v2/main.lua: " + out
        assert (k / "main.lua").read_bytes() == CAND_FILE.read_bytes(), "candidate_v2 + manual_collection.patch != candidate_v3/main.lua (bytes)"
        notes.append("stack_v2.diff -> candidate_v2 e manual_collection.patch (CRLF) -> candidate_v3 reproduzem os arquivos byte a byte")
    return "; ".join(notes)


@step("11 ordens alternativas produzem o MESMO texto (comutacao)")
def t_ordem_alternativa():
    if V2:
        alts = bp.alt_orders_v2(SOURCE)
        for k, v in alts.items():
            assert build_coleta.apply(v) == CAND, "ordem alternativa + coleta diverge do candidato v3: " + k  # V3
        return "%d ordens alternativas dao texto identico (%s)" % (len(alts), "; ".join(alts))
    alt = bp.alt_order_interface_before_ia(SOURCE)
    assert alt == CAND, "ordem alternativa diverge do candidato"
    return "texto identico (a IA e o painel rebaseado comutam)"


@step("12 candidato nao toca o ESTRADAS e nao deixa residuos do contrato abstrato antigo")
def t_residuos():
    for gone in ("cargo0", "perWave", "combat.cargo = CFG.ECONVOY"):
        assert gone not in CAND, gone
    assert not re.search(r"ECONVOY\.(cargo0|perWave|cut)\b", CAND), "resto do contrato abstrato do comboio"
    assert "load(txt" not in CAND, "sv.parse ainda executa codigo"
    assert "roads." not in CAND and "native_adapter" not in CAND, "ESTRADAS nao deveria estar integrada"
    assert CAND.count("function logi.extraHud(") == 1 and CAND.count("function logi.hudLine(") == 1
    if V2:
        assert CAND.count("function logi.rebuildReserve(") == 1 and CAND.count("logi.rebuildReserve()") >= 2
        m = re.search(r"CFG\.ECHAIN = \{.*?free = (\d+).*?trip = ([\d.]+).*?want = \{ ammo = (\d+), shirts = (\d+) \}", CAND, re.S)
        assert m and m.groups() == ("5", "20.0", "4", "20"), ("calibracao v2 esperada free 5 / trip 20 / want 4,20", m and m.groups())
        return "v2: calibracao free=5 trip=20 want=4/20; rebuildReserve unica; sem cargo0/perWave/ECONVOY.cut; sem load(txt; sem ESTRADAS"
    return "sem cargo0/perWave/ECONVOY.cut; sem load(txt; sem ESTRADAS; extraHud e hudLine unicas"


STEPS = [t_integridade, t_sintaxe, t_check_globals, t_orders_controle, t_orders_candidato, t_tools_independentes,
         t_economia, t_ia] + ([t_elogi, t_elogi_legacy, t_bmat] if V2 else []) + [
         t_interface_original, t_interface_candidato, t_interface_integrada] + ([t_interface_v2] if V2 else []) + [
         t_persistencia, t_persistencia_legacy, t_contrato_estradas, t_ordem_patches, t_ordem_alternativa, t_residuos]

if __name__ == "__main__":
    print("variante %s | candidato: %s (%d linhas, %d bytes CRLF); main real SHA256 %s" % (VARIANT, CAND_FILE, CAND.count("\n"), CAND_FILE.stat().st_size, SHA_BEFORE))
    for s in STEPS:
        s()
    after = bp.sha256(MAIN_FILE)
    same = after == SHA_BEFORE
    SUMMARY.append(("99 main.lua real intacto ao fim (SHA256 igual)", same, 0.0, after))
    print("%s  99 main.lua real intacto ao fim (SHA256 %s...)" % ("PASS" if same else "FAIL", after[:12]))
    (HERE / ("saida_testes%s.txt" % SFX)).write_text("\n".join(LOG), encoding="utf-8", newline="\n")
    bad = [s for s in SUMMARY if not s[1]]
    print("\nRESUMO: %d etapas, %d PASS, %d FAIL" % (len(SUMMARY), len(SUMMARY) - len(bad), len(bad)))
    for n, ok, dt, note in SUMMARY:
        print("  [%s] %s" % ("PASS" if ok else "FAIL", n))
    print("(saida detalhada: data/parallel/logistics_ai/finishing/manual_collection/saida_testes%s.txt; offline: nao prova nada do jogo)" % SFX)
    sys.exit(1 if bad else 0)
