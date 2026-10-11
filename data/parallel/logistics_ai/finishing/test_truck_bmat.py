"""Item 2: hipotese 'fabrica gasta cada 80 bmat e o caminhao do jogador (100 bmat) nunca e reconstruido'.

  cd /d/GitHub/foxhole-rts && PYTHONPATH=D:/tools/pylibs PYTHONDONTWRITEBYTECODE=1 \
      python data/parallel/logistics_ai/finishing/test_truck_bmat.py

Executa o main candidato COMPLETO (main + ECONOMIA + IA_LOGISTICA) em memoria (lupa) e chama as funcoes reais
logi.tick / factoryStep / truckStep / hit. Substitui so fronteiras de engine (o scaffold de tools/test_orders.py).
O consumo do jogador e modelado de forma explicita: 'continuo' = os depositos sao esvaziados a cada tick (a
fabrica sempre tem o que produzir); 'folgado' = depositos cheios (a fabrica fica parada).

Resultado esperado: SEM a correcao a hipotese CONFIRMA (caminhao morto para sempre sob consumo continuo, em
qualquer ordem de fabrica/caminhao); COM patch_reserva_bmat o caminhao volta e o razao de bmat fecha.
"""
import sys
from pathlib import Path

HERE = Path(__file__).resolve().parent
sys.path.insert(0, str(HERE))
sys.dont_write_bytecode = True
from lupa import LuaRuntime  # noqa: E402
from simlib import SCAFFOLD, ROOT, IA_DIR, load_module  # noqa: E402
import patch_reserva_bmat  # noqa: E402

orig = load_module("bp_orig_bmat", IA_DIR / "build_patch.py")
v2 = load_module("bp_v2_bmat", HERE / "build_patch_v2.py")

API = '''
return {logi=logi, CFG=CFG, combat=combat, points=points, economy=economy}
'''

BODY = r'''
local A = api
local L, C = A.logi, A.CFG
NOTES = {}
print = function(...) local m = tostring((...)); if m:find("reconstruir caminhão", 1, true) then NOTES[#NOTES + 1] = m end end
local realDrive = L.drive
-- O oráculo mede reserva econômica; fronteira física explícita permite reconstrução íntegra.
LoadAsset = function() return {IsValid=function() return true end} end
require("UEHelpers").GetWorld().SpawnActor = function(_, _, p)
    return {Health=900, IsValid=function() return true end,
        K2_GetActorLocation=function(self) return self.pos or p end,
        K2_SetActorLocation=function(self,v) self.pos=v end,
        K2_SetActorRotation=function() end,
        SetActorHiddenInGame=function() end, SetActorEnableCollision=function() end}
end
local function truck(kind, n, x, y) return {kind = kind, state = "idle", hp = C.LOGI.hp, off = 0, n = n, X = x, Y = y, Z = 0} end

-- jogador: campo, refinaria e fabrica a 1000 cm uns dos outros; base a 3000 cm da fabrica
local function setup(bmat)
    L.reset()
    L.on, L.prio, L.salvage, L.bmat, L.made, L.job, L.t = true, "auto", 0, bmat or 0, 0, nil, nil
    L.fac = {ammo = 0, shirts = 0, rifle = 0, medical = 0}
    L.base = {name = "base", X = 0, Y = 0, Z = 0, ammo = 6, shirts = 20, rifle = 0, medical = 0}
    L.field, L.refinery, L.factory = {X = -5000, Y = 0, Z = 0}, {X = -4000, Y = 0, Z = 0}, {name = "fábrica", X = -3000, Y = 0, Z = 0}
    L.trucks = {truck("res", 1, -5000, 0), truck("sup", 2, -3000, 0), truck("sup", 3, -3000, 0)}
    L.drive, L.pin, L.lost, L.rebuildNoteT = realDrive, nil, 0, nil
    A.combat.auto = false
    NOTES = {}
end

-- opt: demand = "continuo" | "folgado"; kill = {n = indice do caminhao, at = s}; secs; swap = fabrica DEPOIS dos caminhoes
-- Retorna tabela de leitura: reconstruido em (s depois da morte) ou nil, jobs iniciados, bmat gasto, minimo de bmat.
function play(opt)
    setup(opt.bmat0 or 0)
    local factoryStep = L.factoryStep
    if opt.swap then
        -- mesma logi.tick, mas a fabrica roda depois dos caminhoes (prova que a ordem nao e a causa)
        L.factoryStep = function() end
    end
    local t0, killedAt, rebuiltAt, jobs, lastJob = clock, nil, nil, 0, nil
    local maxB, bad = 0, nil
    local victim = L.trucks[opt.kill.n]
    for step = 1, opt.secs * 2 do
        clock = clock + 0.5
        local rel = clock - t0
        if opt.demand == "continuo" then
            L.base.ammo, L.base.shirts, L.base.rifle, L.base.medical = 0, 0, 0, 0
            L.fac.ammo, L.fac.shirts, L.fac.rifle, L.fac.medical = 0, 0, 0, 0
        elseif opt.demand == "folgado" then
            L.base.ammo, L.base.shirts, L.base.rifle, L.base.medical = 40, 100, 20, 100
        end
        if not killedAt and rel >= opt.kill.at then
            if opt.zeroAtKill then L.bmat, L.salvage = 0, 0 end
            L.hit(victim, 1e9, clock)
            killedAt = rel
            assert(victim.state == "dead")
        end
        local jobBefore = L.job
        L.tick()
        if opt.swap then factoryStep(0.5) end
        if L.job and L.job ~= jobBefore then jobs = jobs + 1 end
        if L.bmat < -1e-9 then bad = "bmat negativo" end
        if killedAt and not rebuiltAt and L.bmat > maxB then maxB = L.bmat end   -- maior bmat visto pelo caminhao enquanto espera
        if killedAt and not rebuiltAt and victim.state ~= "dead" then rebuiltAt = rel - killedAt end
    end
    L.factoryStep = factoryStep
    return {rebuilt = rebuiltAt, jobs = jobs, bmat = L.bmat, maxB = maxB, dead = victim.state == "dead", bad = bad, notes = #NOTES,
            states = L.trucks[1].state .. "/" .. L.trucks[2].state .. "/" .. L.trucks[3].state}
end
'''


def make(transform):
    lua = LuaRuntime()
    lua.execute(SCAFFOLD)
    src = ROOT.joinpath("mod/FoxholeRTS/Scripts/main.lua").read_text(encoding="utf-8")
    api = lua.execute(transform(src) + API)
    lua.globals().api = api
    lua.execute(BODY)
    return lua


def play(lua, **opt):
    t = lua.table_from({k: (lua.table_from(v) if isinstance(v, dict) else v) for k, v in opt.items()})
    r = lua.globals().play(t)
    return {k: r[k] for k in ("rebuilt", "jobs", "bmat", "maxB", "dead", "bad", "notes", "states")}


STACKS = {
    "main+ECONOMIA+IA (original)": lambda s: orig.stacked(s),
    "main+ECONOMIA+IA_v2": lambda s: v2.stacked(s),
}
FIXED = {name: (lambda f: (lambda s: patch_reserva_bmat.apply(f(s))))(f) for name, f in STACKS.items()}


def run_all(verbose=True):
    rows = []
    for name in STACKS:
        before, after = make(STACKS[name]), make(FIXED[name])
        for label, kw in (
            ("continuo, sup 2 morre em 60 s", dict(demand="continuo", kill={"n": 2, "at": 60}, secs=900)),
            ("continuo, sup 2 morre em 60 s, fabrica DEPOIS dos caminhoes", dict(demand="continuo", kill={"n": 2, "at": 60}, secs=900, swap=True)),
            ("continuo, recurso morre em 60 s", dict(demand="continuo", kill={"n": 1, "at": 60}, secs=900)),
            ("folgado (fabrica parada), sup 2 morre em 60 s", dict(demand="folgado", kill={"n": 2, "at": 60}, secs=900, bmat0=300)),
        ):
            rows.append((name, label, play(before, **kw), play(after, **kw)))
    return rows


def sweep_kill_times(verbose=True):
    """Varre o instante da destruicao (30..120 s, passo 3 s) sob consumo continuo: fracao reconstruida em 600 s."""
    name = "main+ECONOMIA+IA (original)"
    before, after = make(STACKS[name]), make(FIXED[name])
    out = {}
    for who, n in (("suprimento", 2), ("recurso", 1)):
        ok_b = ok_a = tot = 0
        worst = 0.0
        for at in range(30, 121, 3):
            kw = dict(demand="continuo", kill={"n": n, "at": at}, secs=600)
            b, a = play(before, **kw), play(after, **kw)
            tot += 1
            ok_b += not b["dead"]
            ok_a += not a["dead"]
            if a["rebuilt"] is not None:
                worst = max(worst, a["rebuilt"])
        out[who] = (ok_b, ok_a, tot, worst)
    return out


def main():
    rows = run_all()
    for name, label, b, a in rows:
        print("%s | %s\n    antes : reconstruido=%s jobs=%d bmat=%.0f (maior bmat enquanto esperava: %.1f) estados=%s\n    depois: reconstruido=%s jobs=%d bmat=%.0f estados=%s avisos=%d" % (
            name, label, b["rebuilt"], b["jobs"], b["bmat"], b["maxB"], b["states"], a["rebuilt"], a["jobs"], a["bmat"], a["states"], a["notes"]))
    for name, label, b, a in rows:
        assert not b["bad"] and not a["bad"], (name, label, b["bad"], a["bad"])
        if label.startswith("continuo, sup 2 morre em 60 s"):
            # a hipotese CONFIRMA: sem a correcao o caminhao nao volta em 900 s, em qualquer ordem
            assert b["dead"] and b["rebuilt"] is None, ("hipotese deveria confirmar", name, label, b)
            assert b["maxB"] < 100, ("mecanismo: o bmat nunca chega a LOGI.truckCost (100) com a fabrica gastando a cada 80", b)
            # com a correcao volta em ate 30 s (prazo) + tempo de juntar 100 bmat a 2 bmat/s (<= 60 s) e a fabrica segue
            assert not a["dead"] and a["rebuilt"] is not None and 30 <= a["rebuilt"] <= 90, (name, label, a)
            assert a["jobs"] >= 10, ("fabrica deve voltar a produzir depois", a)
        elif label.startswith("continuo, recurso morre"):
            assert b["dead"], ("sem a correcao o caminhao de recurso tambem fica morto", b)
            assert not a["dead"], ("com a correcao o bmat guardado reconstroi o caminhao de recurso", a)
        else:
            # controle: fabrica parada -> volta no prazo de 30 s com e sem correcao (sem regressao)
            assert not b["dead"] and not a["dead"] and abs(b["rebuilt"] - 30) <= 1 and abs(a["rebuilt"] - 30) <= 1, (b, a)
            assert a["notes"] == 0
    # a pilha completa (ECONOMIA+IA_v2+reserva+PERSISTENCIA_v2) ja traz a correcao
    import build_persistencia_v2 as bpp  # noqa: E402
    full = play(make(bpp.build_full), demand="continuo", kill={"n": 2, "at": 60}, secs=900)
    print("pilha completa, continuo, sup 2 morre em 60 s: reconstruido=%s jobs=%d" % (full["rebuilt"], full["jobs"]))
    assert not full["dead"] and 30 <= full["rebuilt"] <= 90 and full["jobs"] >= 10, full
    # limite conhecido (informativo): caminhao de RECURSO destruido com bmat e sucata zerados nao tem renda para juntar 100
    res_zero = {k: play(make(f), demand="continuo", kill={"n": 1, "at": 60}, secs=900, zeroAtKill=True)["dead"]
                for k, f in (("sem patch", STACKS["main+ECONOMIA+IA (original)"]), ("com patch", FIXED["main+ECONOMIA+IA (original)"]))}
    print("limite conhecido (recurso destruido com bmat=0 e sucata=0): permanece destruido? %s" % res_zero)
    sw = sweep_kill_times()
    for who, (b, a, tot, worst) in sw.items():
        print("varredura do instante da destruicao (30..120 s), caminhao de %s, consumo continuo: reconstruido em 600 s: antes %d/%d, depois %d/%d (pior caso depois: %.1f s)" % (who, b, tot, a, tot, worst))
    assert sw["suprimento"][0] == 0 and sw["suprimento"][1] == sw["suprimento"][2], sw
    assert sw["recurso"][1] >= sw["recurso"][0] and sw["recurso"][3] <= 90, sw
    print("PASS: test_bmat_caminhao (hipotese confirmada sem a correcao; com patch_reserva_bmat o caminhao volta; controle sem regressao)")


if __name__ == "__main__":
    main()
