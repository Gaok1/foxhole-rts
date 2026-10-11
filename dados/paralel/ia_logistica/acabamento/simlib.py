"""Biblioteca de simulacao offline (lupa) da cadeia inimiga: carrega o main candidato inteiro em memoria e
roda partidas deterministas por waveTick/logi.tick. Reaproveita o scaffold de tools/test_orders.py e o harness de
dados/paralel/ia_logistica/test_ia_logistica.py (lido como texto, sem executar os testes dele).

Nao prova fisica Unreal, rota real, LOS, desempenho nem equilibrio de combate: o modelo de luta e 'cada onda dura
fight segundos e some'. Serve para comparar PARAMETROS entre si e conferir rastreabilidade/conservacao.
"""
from pathlib import Path
import importlib.util
import sys

from lupa import LuaRuntime

sys.dont_write_bytecode = True
HERE = Path(__file__).resolve().parent
ROOT = HERE.parents[3]
IA_DIR = ROOT / "dados/paralel/ia_logistica"


def load_module(name, path):
    spec = importlib.util.spec_from_file_location(name, path)
    mod = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(mod)
    return mod


# --- scaffold e HARNESS do original (texto) ---
_orders = (ROOT / "tools/test_orders.py").read_text(encoding="utf-8")
_a = _orders.index("lua.execute('''") + len("lua.execute('''")
SCAFFOLD = _orders[_a:_orders.index("''')", _a)]
_t = (IA_DIR / "test_ia_logistica.py").read_text(encoding="utf-8")
_h = _t.index("HARNESS = '''") + len("HARNESS = '''")
HARNESS = _t[_h:_t.index("'''", _h)]

SIM = r'''
local A = api
local L, C, combat = A.logi, A.CFG, A.combat
local E = C.ECHAIN
local function truckActor(x, y)
    return {position={X=x,Y=y,Z=0}, IsValid=function() return true end,
        K2_GetActorLocation=function(self) return self.position end,
        K2_SetActorLocation=function(self,p) self.position=p end, K2_SetActorRotation=function() end,
        SetActorHiddenInGame=function(self,h) self.hidden=h end, SetActorEnableCollision=function() end,
        K2_DestroyActor=function(self) self.destroyed=true end}
end
LoadAsset = function() return {IsValid=function() return true end} end
mockSpawnActor = function(_, p) return truckActor(p.X, p.Y) end
A.sv.clear = function() end
local realDrive = L.drive
local function setup()
    L.reset()
    L.on, L.prio, L.salvage, L.bmat, L.made, L.job, L.t = true, "auto", 0, 0, 0, nil, nil
    L.fac = {ammo=0, shirts=0, rifle=0, medical=0}
    L.base = {name="base", X=0, Y=0, Z=0, ammo=6, shirts=30, rifle=0, medical=0}
    L.factory, L.field, L.refinery = {name="fábrica", X=-3000, Y=0, Z=0}, {X=-5000, Y=0, Z=0}, {X=-4000, Y=0, Z=0}
    L.trucks, L.drive = {}, realDrive
    combat.auto, combat.mode, combat.wave, combat.convoys, combat.convoysCut = true, nil, 0, 0, 0
    combat.lastSpawn, combat.nextWaveAt, combat.won = {X=4000, Y=0, Z=0}, nil, false
    L.convoyT = 1e9
    spawnFail = 0
    for i=#A.squad,1,-1 do table.remove(A.squad,i) end
    A.clearEnemies()
    L.eReset()
end

-- opt: secs, fight, cut = nil|"all"|"frac"|"window", p, seed, cutFrom, cutTo, scarce
-- Retorna uma string: "ok|conserv|convoys|cut|lostAmmo|lostShirts;w:sent:asked:short:byCut:t:frontShirts:frontAmmo;..."
function sim(opt)
    math.randomseed(opt.seed or 7)
    setup()
    A.setSpawn(A.fakeSpawn); A.setWavePoint(function() return {X=4000, Y=0, Z=0} end)
    for _ = 1, 6 do table.insert(A.squad, {}) end
    if opt.scarce then L.en.bmat, L.en.led.bmat0, L.en.tripT = 0, 0, 1e12 end
    L.convoyT = clock + C.ECONVOY.first
    local t0, fightEnd, nW = clock, nil, 0
    local times, bad = {}, nil
    local fate, seen, carried = {}, {}, 0
    for step = 1, opt.secs * 2 do
        clock = clock + 0.5
        L.tick()
        A.waveTick()
        if #A.enemies() > 0 and not fightEnd then fightEnd = clock + opt.fight end
        if fightEnd and clock >= fightEnd then A.clearEnemies(); fightEnd = nil end
        local rel = clock - t0
        for _, tr in ipairs(L.foes) do
            if tr.state == "toFront" and tr.cargo then
                if not seen[tr] then seen[tr] = true; carried = carried + tr.cargo.ammo * L.eUnits("ammo") + tr.cargo.shirts * L.eUnits("shirts") end
                local kill = false
                if opt.cut == "all" then kill = true
                elseif opt.cut == "window" then kill = rel >= (opt.cutFrom or 0) and rel < (opt.cutTo or 1e12)
                elseif opt.cut == "frac" then
                    if fate[tr] == nil then fate[tr] = math.random() < opt.p end
                    kill = fate[tr]
                end
                if kill then L.hit(tr, 1e9, clock) end
            end
        end
        if #L.en.waves > nW then
            nW = #L.en.waves
            times[nW] = rel
        end
        local good, why = L.eAudit()
        if not good and not bad then bad = why end
        if not combat.auto then break end
    end
    local out = {}
    for i, w in ipairs(L.en.waves) do
        out[#out + 1] = string.format("%d:%d:%d:%d:%d:%.0f:%g:%g", w.wave, w.sent or -1, w.asked, w.short, w.byCut, times[i] or -1, w.front.shirts, w.front.ammo)
    end
    return string.format("%s|%s|%d|%d|%g|%g|%g;", tostring(not bad), tostring(bad or ""), A.combat.convoys or 0, A.combat.convoysCut or 0,
        L.en.led.lost.ammo, L.en.led.lost.shirts, carried) .. table.concat(out, ";")
end
'''


class Sim:
    """Um runtime com o candidato carregado; sim() muda CFG.ECHAIN por chamada e restaura depois."""

    def __init__(self, source_transform):
        self.lua = LuaRuntime()
        self.lua.execute(SCAFFOLD)
        src = (ROOT / "mod/FoxholeRTS/Scripts/main.lua").read_text(encoding="utf-8")
        candidate = source_transform(src)
        api = self.lua.execute(candidate + HARNESS)
        self.lua.globals().api = api
        self.lua.execute(SIM)
        self.lua.execute('print = function() end')  # silencia log/notify do mod
        self.sim = self.lua.globals().sim
        self.cfg = api.CFG.ECHAIN
        self.defaults = self._snapshot()

    def _snapshot(self):
        d = {}
        for k in ("free", "trip", "minLoad", "bmat0", "stuck"):
            d[k] = self.cfg[k]
        d["front0"] = dict(self.cfg.front0.items())
        d["want"] = dict(self.cfg.want.items())
        return d

    def set_params(self, p):
        for k, v in p.items():
            if k in ("front0", "want"):
                for kk, vv in v.items():
                    self.cfg[k][kk] = vv
            else:
                self.cfg[k] = v

    def run(self, params, **opt):
        self.set_params(self.defaults)
        self.set_params(params or {})
        o = self.lua.table_from(opt)
        raw = self.sim(o)
        self.set_params(self.defaults)
        head, _, rest = raw.partition(";")
        ok, why, conv, cut, la, ls, car = head.split("|")
        waves = []
        for row in rest.split(";"):
            if not row:
                continue
            n, sent, asked, short, bycut, t, fs, fa = row.split(":")
            waves.append(dict(wave=int(n), sent=int(sent), asked=int(asked), short=int(short), byCut=int(bycut),
                              t=int(t), shirts=float(fs), ammo=float(fa)))
        return dict(ok=ok == "true", why=why, convoys=int(conv), cut=int(cut), lostAmmo=float(la), lostShirts=float(ls), carried=float(car), waves=waves)
