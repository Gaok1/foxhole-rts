"""Harness offline (lupa) da COLETA MANUAL: carrega o main candidato INTEIRO num runtime Lua e roda o codigo real
(pathTick, squadTick, logi.tick, logi.start, logi.deployPlan, sv.save/load...). So as fronteiras de engine sao falsas:
atores (campo, refinaria, fabrica, caminhoes), soldados com pawn que ANDA (AddMovementInput desloca o pawn), chao plano,
relogio. Nao prova fisica Unreal, colisao, rota real nem custo por quadro (gates do laboratorio).
"""
import importlib
import sys
from pathlib import Path

sys.dont_write_bytecode = True
HERE = Path(__file__).resolve().parent
ROOT = HERE.parents[4]
sys.path.insert(0, str(HERE))
import build_coleta  # noqa: E402

_t = (ROOT / "tools/test_orders.py").read_text(encoding="utf-8")
_a = _t.index("lua.execute('''") + len("lua.execute('''")
SCAFFOLD = _t[_a:_t.index("''')", _a)]
PERSIST_HARNESS = (ROOT / "data/parallel/persistence/harness_test.lua").read_text(encoding="utf-8")

SRC_V2, SHA_V2 = build_coleta.read_v2()
TEXT_V2 = SRC_V2
TEXT_V3 = build_coleta.apply(SRC_V2)

TAIL = '''
return {logi=logi, CFG=CFG, combat=combat, rts=rts, S=S, sv=sv, tick=tick, points=points, economy=economy,
  squad=function() return squad end, enemies=function() return enemies end,
  pathTick=pathTick, squadTick=squadTick, issueMove=issueMove, stopSelected=stopSelected, queueMove=queueMove,
  routeTo=routeTo, recruit=recruit, reap=reap, alive=alive, loc=loc, hudLine=function() return logi.hudLine() end,
  hooks={authority=function(fn) isLocalAuthority=fn end, spawnSoldier=function(fn) spawnSoldier=fn end,
         addPoint=function(fn) addPoint=fn end}}
'''

# Mundo falso + soldados que andam + passo de quadro. Executado depois do candidato.
WORLD = r'''
A = api
DT, SPEED = 0.1, 400.0
LOG = {}
print = function(...)
    local p = {}
    for i = 1, select("#", ...) do p[#p + 1] = tostring(select(i, ...)) end
    LOG[#LOG + 1] = table.concat(p, " ")
end
function saw(text) for _, l in ipairs(LOG) do if l:find(text, 1, true) then return true end end return false end
function count(text) local n = 0 for _, l in ipairs(LOG) do if l:find(text, 1, true) then n = n + 1 end end return n end

ACT = {}
FindAllOf = function(cls) return ACT[cls] end
function actor(cls, x, y, z)
    local a = {cls = cls, position = {X = x, Y = y, Z = z or 0}, rot = {Pitch = 0, Yaw = 0, Roll = 0}, hidden = false, collision = true}
    a.IsValid = function(self) return not self.gone end
    a.K2_GetActorLocation = function(self) return self.position end
    a.K2_SetActorLocation = function(self, p) self.position = {X = p.X, Y = p.Y, Z = p.Z} end
    a.K2_GetActorRotation = function(self) return self.rot end
    a.K2_SetActorRotation = function(self, r) self.rot = r end
    a.SetActorHiddenInGame = function(self, h) self.hidden = h end
    a.SetActorEnableCollision = function(self, c) self.collision = c end
    a.K2_DestroyActor = function(self) self.bActorIsBeingDestroyed = true end
    ACT[cls] = ACT[cls] or {}
    table.insert(ACT[cls], a)
    if cls == "BPTruckW_C" then a.Health = 900 end
    return a
end
-- Fronteira de engine: reconstrução exige ator íntegro, não apenas estado abstrato.
LoadAsset = function() return {IsValid=function() return true end} end
require("UEHelpers").GetWorld().SpawnActor = function(_, _, p)
    return actor("BPTruckW_C", p.X, p.Y, p.Z)
end
-- Geometria (cm): campo longe da refinaria (o raio de entrega e 1500), base a 4 km da refinaria.
function newWorld(o)
    o = o or {}
    ACT = {}
    actor("BPSalvageField_C", o.fx or -12000, o.fy or 3000)
    actor("BPRefinery_C", -4000, 0)
    actor("BPFactory_C", -3000, 600)
    for i = 1, o.trucks or 3 do actor("BPTruckW_C", -3000 + 700 * i, 1800) end
    A.rts.home = {X = 0, Y = 0, Z = 0}
    A.rts.active = true
    A.hooks.authority(function() return true end)
end

local function mkpawn(x, y)
    local p = {Health = 100, MaxHealth = 100, pos = {X = x, Y = y, Z = 0}, vel = {X = 0, Y = 0, Z = 0}, touched = 0}
    p.CharacterMovement = {MaxWalkSpeed = SPEED, StopMovementImmediately = function() p.touched = p.touched + 1 end}
    p.IsValid = function(self) return not self.gone end
    p.K2_GetActorLocation = function(self) return self.pos end
    p.GetVelocity = function(self) return self.vel end
    p.ConsumeMovementInputVector = function(self) self.touched = self.touched + 1 end
    p.AddMovementInput = function(self, dir, scale)
        self.touched = self.touched + 1
        self.pos = {X = self.pos.X + dir.X * SPEED * scale * DT, Y = self.pos.Y + dir.Y * SPEED * scale * DT, Z = 0}
    end
    p.OnRep_Health = function() end
    p.K2_DestroyActor = function(self) self.gone = true end
    return p
end
function newSoldier(role, x, y, team)
    local m = {pawn = mkpawn(x, y), hpc = {SetControlRotation = function() end, IsValid = function() return true end, UnPossess = function() end},
        team = team or A.CFG.FRIENDLY_TEAM, role = role, group = 1, sel = true, nextShot = 0}
    if team == A.CFG.ENEMY_TEAM then table.insert(A.enemies(), m) else table.insert(A.squad(), m) end
    return m
end
-- spawnSoldier falso (o real e engine): trabalhadores nascem aqui; SPAWN_FAIL = true simula falha de spawn
SPAWNED = 0
A.hooks.spawnSoldier(function(x, y, z, slot, team, role)
    if SPAWN_FAIL then return nil end
    SPAWNED = SPAWNED + 1
    return {pawn = mkpawn(x, y), hpc = {SetControlRotation = function() end, IsValid = function() return true end, UnPossess = function() end},
        slot = slot, team = team, role = role, nextShot = 0}
end)
function workers() local n = 0 for _, m in ipairs(A.squad()) do if m.role == "worker" and A.alive(m) then n = n + 1 end end return n end
-- esquadrao inicial como o newGame (START_SQUAD 6: roleFor 1..6 = rifle, rifle, mg, medic, rifle, sniper)
function startSquad()
    local roles = {"rifle", "rifle", "mg", "medic", "rifle", "sniper"}
    local out = {}
    for i, r in ipairs(roles) do out[i] = newSoldier(r, 300 + 160 * i, -200 + 100 * i) end
    return out
end
-- partida: mundo, esquadrao e logi.start reais
function newMatch(o)
    o = o or {}
    A.logi.reset()
    for i = #A.squad(), 1, -1 do table.remove(A.squad(), i) end
    newWorld(o)
    if not o.noSquad then startSquad() end
    local setup = A.logi.ready()
    assert(setup, "scan falhou")
    assert(A.logi.start(setup))
    A.logi.convoyT = 1e9       -- sem comboio inimigo: isola a cadeia do jogador
    A.combat.auto = false
    return setup
end

function stepOnce()
    clock = clock + DT
    A.tick.n = A.tick.n + 1
    A.pathTick(); A.squadTick(); A.logi.tick()
end
-- avanca ate secs ou ate cond() verdadeiro; devolve segundos decorridos (ou nil se estourou)
function runUntil(secs, cond, hook)
    local t0 = clock
    while clock - t0 < secs do
        stepOnce()
        if hook then hook() end
        if cond and cond() then return clock - t0 end
    end
    return nil
end
function resTruck() for _, tr in ipairs(A.logi.trucks) do if tr.kind == "res" then return tr end end end
function dist(a, b) return math.sqrt((a.X - b.X) ^ 2 + (a.Y - b.Y) ^ 2) end
function ledgerOK() local ok, why = A.logi.colAudit(); assert(ok, why); return true end
function units() return A.logi.col.units end
'''


def lua_runtime(version="lua54"):
    return importlib.import_module("lupa." + version).LuaRuntime()


def new_game(text=None, version="lua54", world=True):
    """Runtime novo com o candidato inteiro (padrao: v3). Retorna o runtime; `api` e `A` globais no Lua."""
    lua = lua_runtime(version)
    lua.execute(SCAFFOLD)
    api = lua.execute((text or TEXT_V3) + TAIL)
    lua.globals().api = api
    lua.execute(WORLD)
    return lua


# ------------------------------------------------------------------------------------------------ runner
RESULTS = []


def case(name, fn, *args, **kw):
    """Executa fn; imprime PASS/FAIL e acumula. Excecoes (inclusive LuaError) viram FAIL."""
    import traceback
    try:
        note = fn(*args, **kw) or ""
        RESULTS.append((name, True))
        print("PASS  %s%s" % (name, ("  -> " + str(note)) if note else ""))
    except BaseException as e:  # noqa: BLE001
        RESULTS.append((name, False))
        print("FAIL  %s: %s: %s" % (name, type(e).__name__, str(e)[:600]))
        traceback.print_exc(limit=3)


def finish(title):
    bad = [n for n, ok in RESULTS if not ok]
    print("\n%s: %d casos, %d PASS, %d FAIL" % (title, len(RESULTS), len(RESULTS) - len(bad), len(bad)))
    if bad:
        print("FALHARAM: " + "; ".join(bad))
        sys.exit(1)
    print("PASS: %s" % title)


# ------------------------------------------------------------------------------------------------ harness de persistencia
P_TAIL = '''
return { sv=sv, logi=logi, CFG=CFG, S=S, combat=combat, economy=economy, rts=rts, fort=fort, tick=tick, squadTick=squadTick, pathTick=pathTick,
    points=function() return points end, squad=function() return squad end, enemies=function() return enemies end,
    structures=function() return structures end, addPoint=function(x, y) return addPoint(x, y) end,
    hooks={ authority=function(fn) isLocalAuthority=fn end, spawnSoldier=function(fn) spawnSoldier=fn end,
            addPoint=function(fn) addPoint=fn end } }
'''


def persist_game(text=None, version="lua54", files=None):
    """Uma carga do jogo com o harness de persistencia (arquivos falsos, mundo falso). `files` = save herdado do disco."""
    lua = lua_runtime(version)
    lua.execute(SCAFFOLD)
    lua.globals().api = lua.execute((text or TEXT_V3) + P_TAIL)
    lua.execute(PERSIST_HARNESS)
    for path, content in (files or {}).items():
        lua.globals().FS.files[path] = content
    return lua


SAVE_PATH = "ue4ss/Mods/FoxholeRTS/save.txt"
