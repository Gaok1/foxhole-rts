"""Harness offline (lupa) das BASES AVANCADAS: carrega o main candidato INTEIRO (candidato_v4 por padrao) e roda o codigo real
(recruit, spawnSquad, logi.*, sv.*). So as fronteiras de engine sao falsas: atores (campo, refinaria, fabrica, caminhoes, a
ForwardBase1), soldados com pawn, terreno (terrainZ/terrainClass do scaffold de tools/test_orders.py), relogio, controlador de
jogador. Nao prova fisica Unreal, colisao, rota real, classe real BPForwardBase1_C nem custo por quadro (gates do laboratorio).
"""
import importlib
import os
import sys
from pathlib import Path

sys.dont_write_bytecode = True
HERE = Path(__file__).resolve().parent
ROOT = HERE.parents[3]
sys.path.insert(0, str(HERE))

_t = (ROOT / "tools/test_orders.py").read_text(encoding="utf-8")
_a = _t.index("lua.execute('''") + len("lua.execute('''")
SCAFFOLD = _t[_a:_t.index("''')", _a)]
PERSIST_HARNESS = (ROOT / "dados/paralel/persistencia/harness_test.lua").read_text(encoding="utf-8")

V3_FILE = ROOT / "dados/paralel/ia_logistica/acabamento/coleta_manual/candidato_v3/main.lua"
V4_FILE = Path(os.environ["BASES_V4_FILE"]) if os.environ.get("BASES_V4_FILE") else HERE / "candidato_v4/main.lua"   # sensibilidade_bases.py injeta mutantes


def read_lf(p):
    return Path(p).read_bytes().decode("utf-8").replace("\r\n", "\n")


TEXT_V3 = read_lf(V3_FILE)
TEXT_V4 = read_lf(V4_FILE)

TAIL = '''
return {logi=logi, CFG=CFG, combat=combat, rts=rts, S=S, sv=sv, fort=fort, tick=tick, economy=economy, ai=ai, anim=anim,
  points=function() return points end, squad=function() return squad end, enemies=function() return enemies end,
  structures=function() return structures end,
  pathTick=pathTick, squadTick=squadTick, recruit=recruit, spawnSquad=spawnSquad, waveTick=waveTick, pointsTick=pointsTick,
  pointStep=pointStep, newGame=newGame, clearSquad=clearSquad, reap=reap, alive=alive, loc=loc, supplyTick=supplyTick,
  addPoint=function(x, y) return addPoint(x, y) end, hudLine=function() return logi.hudLine() end, status=status,
  callMortar=callMortar, sizeof=function() return #squad end, help=function() return CFG.HELP_TEXT end,
  hooks={authority=function(fn) isLocalAuthority=fn end, spawnSoldier=function(fn) spawnSoldier=fn end,
         addPoint=function(fn) addPoint=fn end}}
'''

# Mundo falso + soldados + controlador + ForwardBase1 falsa + passo de quadro. Executado depois do candidato.
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
function lastlog(text) for i = #LOG, 1, -1 do if LOG[i]:find(text, 1, true) then return LOG[i] end end end

ACT = {}
FindAllOf = function(cls) return ACT[cls] end
function actor(cls, x, y, z, yaw)
    local a = {cls = cls, position = {X = x, Y = y, Z = z or 0}, rot = {Pitch = 0, Yaw = yaw or 0, Roll = 0}, hidden = false, collision = true}
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
    return a
end
function live(cls) local n = 0 for _, a in ipairs(ACT[cls] or {}) do if not a.bActorIsBeingDestroyed then n = n + 1 end end return n end

-- controlador do jogador com pawn (spawnSquad exige ensureCommander); o cursor vem de CURSOR = {X, Y, Z} ou nil
CURSOR = nil
FName = FName or function(n) return n end
local UE = require("UEHelpers")
PCPAWN = {Health = 100, IsValid = function() return true end, K2_GetActorLocation = function() return {X = 0, Y = 0, Z = 0} end,
    CharacterMovement = {IsMovingOnGround = function() return true end}}
PC = {IsValid = function() return true end, Pawn = PCPAWN, ClientAlertMessage = function() end,
    IsInputKeyDown = function() return false end,
    GetHitResultUnderCursorByChannel = function(self, _, _, hit)
        if not CURSOR then return false end
        hit.ImpactPoint = {X = CURSOR.X, Y = CURSOR.Y, Z = CURSOR.Z or 0}
        return true
    end}
GS = {GetTimeSeconds = function() return clock end, GetRealTimeSeconds = function() return clock end,
      GetPlayerController = function() return PC end}
UE.GetGameplayStatics = function() return GS end

-- ForwardBase1 falsa. FWD_FAIL: "nil" | "destroying" | "health" | "shifted" | "yaw" | "code" | nil
FWD_FAIL, LOAD_FAIL, SPAWNED_FWD = nil, nil, 0
LoadAsset = function(path)
    if LOAD_FAIL then return nil end
    return {IsValid = function() return true end, path = path}
end
local W = UE.GetWorld()
W.SpawnActor = function(self, cls, l, r)
    if cls and cls.path and cls.path:find("ForwardBase1", 1, true) then
        if FWD_FAIL == "nil" then return nil end
        local ruin = cls.path:find("Destroyed", 1, true)
        SPAWNED_FWD = SPAWNED_FWD + 1
        local a = actor(ruin and "BPDestroyedForwardBase1_C" or "BPForwardBase1_C", l.X, l.Y, l.Z, r and r.Yaw or 0)
        a.Health, a.MaxHealth = 1725, 1725
        a.CodeName = {ToString = function() return "ForwardBase1" end}
        if not ruin then
            if FWD_FAIL == "destroying" then a.bActorIsBeingDestroyed = true
            elseif FWD_FAIL == "health" then a.Health = 1
            elseif FWD_FAIL == "shifted" then a.position = {X = l.X + 500, Y = l.Y, Z = l.Z}
            elseif FWD_FAIL == "yaw" then a.rot.Yaw = a.rot.Yaw + 30
            elseif FWD_FAIL == "code" then a.CodeName = {ToString = function() return "Other" end} end
        end
        return a
    end
    return nil
end
function fwdActors() return ACT["BPForwardBase1_C"] or {} end
function fwdLive() return live("BPForwardBase1_C") end

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
    p.K2_DestroyActor = function(self) self.gone = true; self.bActorIsBeingDestroyed = true end
    return p
end
function newSoldier(role, x, y, team)
    local m = {pawn = mkpawn(x, y), hpc = {SetControlRotation = function() end, IsValid = function() return true end, UnPossess = function() end},
        team = team or A.CFG.FRIENDLY_TEAM, role = role, group = 1, sel = true, nextShot = 0}
    if team == A.CFG.ENEMY_TEAM then table.insert(A.enemies(), m) else table.insert(A.squad(), m) end
    return m
end
-- spawnSoldier falso (o real e engine): SPAWN_FAIL = true simula falha; SPAWNS guarda o que nasceu (x, y, z, role)
SPAWNED, SPAWN_FAIL, SPAWNS = 0, false, {}
A.hooks.spawnSoldier(function(x, y, z, slot, team, role)
    if SPAWN_FAIL then return nil end
    SPAWNED = SPAWNED + 1
    SPAWNS[#SPAWNS + 1] = {x = x, y = y, z = z, role = role, team = team}
    return {pawn = mkpawn(x, y), hpc = {SetControlRotation = function() end, IsValid = function() return true end, UnPossess = function() end},
        slot = slot, team = team, role = role, nextShot = 0}
end)
A.hooks.addPoint(function(x, y)
    local P = A.points()
    if #P >= A.CFG.POINT_MAX then return nil end
    for _, q in ipairs(P) do
        if (q.X - x) ^ 2 + (q.Y - y) ^ 2 < (2 * A.CFG.POINT_RADIUS) ^ 2 then return nil end
    end
    local pt = {X = x, Y = y, Z = 0, name = string.char(65 + #P), owner = nil, prog = 0, dots = {}}
    P[#P + 1] = pt
    return pt
end)
function mkPoint(x, y, owner)
    local pt = A.addPoint(x, y)
    assert(pt, "ponto nao criado")
    pt.owner = owner
    pt.prog = owner == A.CFG.FRIENDLY_TEAM and 1 or (owner == A.CFG.ENEMY_TEAM and -1 or 0)
    return pt
end
function workers() local n = 0 for _, m in ipairs(A.squad()) do if m.role == "worker" and A.alive(m) then n = n + 1 end end return n end
function combatants() local n = 0 for _, m in ipairs(A.squad()) do if m.role ~= "worker" and A.alive(m) then n = n + 1 end end return n end
function startSquad()
    local roles = {"rifle", "rifle", "mg", "medic", "rifle", "sniper"}
    for i, r in ipairs(roles) do newSoldier(r, 300 + 160 * i, -200 + 100 * i) end
end
-- partida: mundo, esquadrao e logi.start reais (sem comboio inimigo, sem ondas)
function newMatch(o)
    o = o or {}
    A.logi.reset()
    for i = #A.squad(), 1, -1 do table.remove(A.squad(), i) end
    newWorld(o)
    if not o.noSquad then startSquad() end
    local setup = A.logi.ready()
    assert(setup, "scan falhou")
    assert(A.logi.start(setup))
    A.logi.convoyT = 1e9
    A.combat.auto = false
    -- sem coleta/trabalhadores por padrao: estes testes isolam a base (CFG.COLETA.workers=0 evita nascimentos de fundo)
    if o.workers ~= true then A.CFG.COLETA.workers = 0 end
    return setup
end
function stepOnce()
    clock = clock + DT
    A.tick.n = A.tick.n + 1
    A.pathTick(); A.squadTick(); A.logi.tick()
end
function runUntil(secs, cond, hook)
    local t0 = clock
    while clock - t0 < secs do
        stepOnce()
        if hook then hook() end
        if cond and cond() then return clock - t0 end
    end
    return nil
end
-- cria uma base avancada num ponto nosso longe da base (4000 cm): devolve pt, fb
function buildFwd(x, y, owner)
    local pt = mkPoint(x or 4000, y or 0, owner or A.CFG.FRIENDLY_TEAM)
    A.logi.bmat = math.max(A.logi.bmat, 300 + A.logi.rebuildReserve())
    local ok, why = A.logi.fwdBuild(pt)
    assert(ok, tostring(why))
    return pt, pt.fb
end
function stock(dep, sh, ri, am, md)
    dep.shirts, dep.rifle, dep.ammo, dep.medical = sh or 0, ri or 0, am or dep.ammo or 0, md or dep.medical or 0
end
function dist(a, b) return math.sqrt((a.X - b.X) ^ 2 + (a.Y - b.Y) ^ 2) end
function sdist(s, p) return dist({X = s.x, Y = s.y}, p) end   -- s = entrada de SPAWNS (x, y minusculos)
-- estoque inicial de uma base avancada (entra no razao como 'inicial')
function stockFwd(fb, sh, ri)
    fb.dep.shirts, fb.dep.rifle = sh, ri
    fb.led.init.shirts, fb.led.init.rifle = sh, ri
end
'''

# Persistencia: depois de PERSIST_HARNESS (que define H, FS, mundo e hooks proprios), acrescenta a ForwardBase1 falsa.
FWD_PERSIST = r'''
FWD_FAIL, LOAD_FAIL, SPAWNED_FWD, FWD_FAIL_AT = nil, nil, 0, nil
local UE2 = require("UEHelpers")
local W2 = UE2.GetWorld()
local origLoad, origSpawn = LoadAsset, W2.SpawnActor
LoadAsset = function(path)
    if path:find("ForwardBase1", 1, true) then
        if LOAD_FAIL then return nil end
        return {IsValid = function() return true end, path = path}
    end
    return origLoad(path)
end
W2.SpawnActor = function(self, cls, l, r)
    if cls and cls.path and cls.path:find("ForwardBase1", 1, true) then
        SPAWNED_FWD = SPAWNED_FWD + 1
        if FWD_FAIL_AT and SPAWNED_FWD == FWD_FAIL_AT then return nil end
        local a = H.actor("BPForwardBase1_C", l.X, l.Y, l.Z, r and r.Yaw or 0)
        a.Health, a.MaxHealth = 1725, 1725
        a.CodeName = {ToString = function() return "ForwardBase1" end}
        return a
    end
    return origSpawn(self, cls, l, r)
end
function fwdLive() return H.live("BPForwardBase1_C") end
function mkPoint(x, y, owner)
    local pt = api.addPoint(x, y)
    assert(pt, "ponto nao criado")
    pt.owner = owner
    pt.prog = owner == api.CFG.FRIENDLY_TEAM and 1 or (owner == api.CFG.ENEMY_TEAM and -1 or 0)
    return pt
end
'''


def lua_runtime(version="lua54"):
    return importlib.import_module("lupa." + version).LuaRuntime()


def new_game(text=None, version="lua54"):
    """Runtime novo com o candidato inteiro (padrao: v4) e o mundo falso. `api` e `A` globais no Lua."""
    lua = lua_runtime(version)
    lua.execute(SCAFFOLD)
    api = lua.execute((text or TEXT_V4) + TAIL)
    lua.globals().api = api
    lua.execute(WORLD)
    return lua


def persist_game(text=None, version="lua54", files=None):
    """Uma carga do jogo com o harness de persistencia (arquivos falsos, mundo falso) + ForwardBase1 falsa."""
    lua = lua_runtime(version)
    lua.execute(SCAFFOLD)
    lua.globals().api = lua.execute((text or TEXT_V4) + TAIL)
    lua.execute(PERSIST_HARNESS)
    lua.execute(FWD_PERSIST)
    for path, content in (files or {}).items():
        lua.globals().FS.files[path] = content
    return lua


SAVE_PATH = "ue4ss/Mods/FoxholeRTS/save.txt"
RESULTS = []


def case(name, fn, *args, **kw):
    try:
        note = fn(*args, **kw) or ""
        RESULTS.append((name, True))
        print("PASS  %s%s" % (name, ("  -> " + str(note)) if note else ""))
    except BaseException as e:  # noqa: BLE001
        RESULTS.append((name, False))
        print("FAIL  %s: %s: %s" % (name, type(e).__name__, str(e)[:700]))


def finish(title):
    bad = [n for n, ok in RESULTS if not ok]
    print("\n%s: %d casos, %d PASS, %d FAIL" % (title, len(RESULTS), len(RESULTS) - len(bad), len(bad)))
    if bad:
        print("FALHARAM: " + "; ".join(bad))
        sys.exit(1)
    print("PASS: %s" % title)
