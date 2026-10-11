from pathlib import Path
import difflib
ROOT=Path(__file__).resolve().parents[3]
HERE=Path(__file__).parent

def build(s):
    def replace(old,new):
        nonlocal s
        assert s.count(old)==1, ('âncora não única',old[:70],s.count(old))
        s=s.replace(old,new,1)
    def function(name,next_anchor,new):
        nonlocal s
        a=s.index('function logi.'+name+'(');b=s.index(next_anchor,a)
        s=s[:a]+new.rstrip()+'\n\n'+s[b:]
    replace('want = { ammo = 6, shirts = 20 },','want = { ammo = 6, shirts = 20, rifle = 4, medical = 20 },\n    products = { "ammo", "shirts", "rifle", "medical" },')
    replace('shirts = { name = "camisas", bmat = 80, time = 80, units = 10 } },','shirts = { name = "camisas", bmat = 80, time = 80, units = 10 },\n        rifle = { name = "fuzis", bmat = 100, time = 70, units = 20 },\n        medical = { name = "bandagens", bmat = 80, time = 40, units = 50 } },')
    replace('logi.fac = { ammo = 0, shirts = 0 }','logi.fac = { ammo = 0, shirts = 0, rifle = 0, medical = 0 }')
    replace('ammo = C.ammo0, shirts = C.shirts0 }','ammo = C.ammo0, shirts = C.shirts0, rifle = 0, medical = 0 }')
    replace('ammo = 0, shirts = 0, pt = pt }','ammo = 0, shirts = 0, rifle = 0, medical = 0, pt = pt }')
    replace('if pt.dep then pt.dep.ammo, pt.dep.shirts = 0, 0 end  -- o estoque do deposito cai junto','if pt.dep then for _, kind in ipairs(CFG.LOGI.products) do pt.dep[kind] = 0 end end  -- estoque perdido')
    blocks=HERE.joinpath('functions.lua').read_text(encoding='utf-8-sig')
    a=blocks.index('function logi.pickDest');b=blocks.index('-- Comprimento',a)
    function('pickDest','function logi.truckStep',blocks[a:b])
    a=blocks.index('function logi.needs');b=blocks.index('function logi.pickDest',a)
    function('need','function logi.factoryStep',blocks[a:b]+blocks[blocks.index('-- Comprimento'):])
    replace('local order = { "auto", "ammo", "shirts" }','local order = { "auto", "ammo", "shirts", "rifle", "medical" }')
    replace('logi.fac[logi.job.kind] = logi.fac[logi.job.kind] + 1','logi.fac[logi.job.kind] = (logi.fac[logi.job.kind] or 0) + 1')
    replace('if not rc or logi.bmat < rc.bmat then return end','if not rc or type(rc.bmat) ~= "number" or rc.bmat <= 0 or type(rc.time) ~= "number" or rc.time <= 0 or logi.bmat < rc.bmat then return end')
    replace('if logi.fac.ammo + logi.fac.shirts < 1 then return end','local ready = 0\n        for _, kind in ipairs(C.products) do ready = ready + (logi.fac[kind] or 0) end\n        if ready < 1 then return end')
    a=s.index('        local na, ns = logi.need(dest)');b=s.index('        if logi.pin == dest then logi.pin = nil end',a)
    s=s[:a]+'''        local needs, cargo, remaining = logi.needs(dest), {}, C.cap
        for _, kind in ipairs(C.products) do
            local stock = logi.fac[kind] or 0
            local wanted = logi.pin == dest and stock or needs[kind]
            local n = math.min(stock, wanted, remaining)
            cargo[kind], remaining = n, remaining - n
        end
        if remaining == C.cap then return end
        for _, kind in ipairs(C.products) do logi.fac[kind] = (logi.fac[kind] or 0) - cargo[kind] end
        tr.cargo, tr.dest, tr.state = cargo, dest, "toDep"
'''+s[b:]
    replace('logi.fac.ammo, logi.fac.shirts = logi.fac.ammo + tr.cargo.ammo, logi.fac.shirts + tr.cargo.shirts\n            tr.cargo, tr.dest, tr.state = nil, nil, "idle"',
        'tr.dest, tr.state = logi.factory, "returnCargo"\n            tr.route, tr.routeDest, tr.pathJob = nil, nil, nil')
    replace('    elseif tr.state == "toDep" then', '\n'.join([
        '    elseif tr.state == "returnCargo" then',
        '        if not tr.cargo then tr.dest, tr.state = nil, "idle"; return end',
        '        -- Crédito apenas após chegada confirmada; driver seguro de ESTRADAS é gate de integração.',
        '        if logi.drive(tr, logi.factory, dt) then',
        '            logi.moveCargo(tr.cargo, logi.fac, false)',
        '            tr.cargo, tr.dest, tr.state = nil, nil, "idle"',
        '        end',
        '    elseif tr.state == "toDep" then']))
    a=s.index('            d.ammo = (d.ammo or 0) + tr.cargo.ammo');b=s.index('            logi.delivered',a)
    s=s[:a]+'''            logi.moveCargo(tr.cargo, d, true)
            notify(string.format("caminhão entregou em %s: %d munição, %d camisas, %d fuzis, %d bandagens",
                d.name, tr.cargo.ammo or 0, (tr.cargo.shirts or 0) * C.recipes.shirts.units,
                (tr.cargo.rifle or 0) * C.recipes.rifle.units, (tr.cargo.medical or 0) * C.recipes.medical.units), 3.0)
'''+s[b:]
    replace('if dep and (dep.shirts or 0) < 1 and dep ~= logi.base then','if dep and ((dep.shirts or 0) < 1 or (role == "rifle" and (dep.rifle or 0) < 1)) and dep ~= logi.base then')
    replace('"sem camisas no ponto %s: o recruta nasce na base"', '"sem suprimento de recrutamento no ponto %s: o recruta nasce na base"')
    replace('if spawnSquad(1, role, at) < 1 then return false end\n    if dep then dep.shirts = dep.shirts - 1 end','''if dep and role == "rifle" and (dep.rifle or 0) < 1 then
        notify("sem fuzis na base: produza e entregue pela logística", 3.0); return false
    end
    -- Game thread síncrono: debitar só após spawn confirmado; falha não consome estoque.
    if spawnSquad(1, role, at) < 1 then return false end
    if dep then
        dep.shirts = dep.shirts - 1
        if role == "rifle" then dep.rifle = dep.rifle - 1 end
    end''')
    replace('local p = best.pawn\n        pcall(function() if p.bIsBleeding','''local supply = nil
        if logi.on and m.team ~= CFG.ENEMY_TEAM then
            supply = logi.medicalDepot(m)
            if not supply then return end
        end
        local p = best.pawn
        pcall(function() if p.bIsBleeding''')
    replace('m.healAnimUntil = os.clock() + 1.2','if supply and p.Health > before then supply.medical = supply.medical - 1 end\n        m.healAnimUntil = os.clock() + 1.2')
    # Preserve old HUD and append stock/cargo for newly introduced products.
    replace('table.concat(deps, " | "), foe)\nend','''table.concat(deps, " | "), foe) .. logi.extraHud()
end''')
    a=s.index('function logi.hudLine()')
    s=s[:a]+'''function logi.extraHud()
    local parts = { string.format("Fuzis: fábrica %d caixas | bandagens: fábrica %d caixas", logi.fac.rifle or 0, logi.fac.medical or 0) }
    for _, dep in ipairs(logi.depots()) do parts[#parts+1] = string.format("%s: %d fuzis, %d bandagens", dep.name, dep.rifle or 0, dep.medical or 0) end
    for i, tr in ipairs(logi.trucks) do
        if tr.cargo then parts[#parts+1] = string.format("caminhão %d -> %s: %d caixas fuzis, %d caixas bandagens", i,
            tr.dest and tr.dest.name or "—", tr.cargo.rifle or 0, tr.cargo.medical or 0) end
    end
    return "\\n" .. table.concat(parts, " | ")
end

'''+s[a:]
    function("snapshot", "-- Objetivo do inimigo", HERE.joinpath("save.lua").read_text(encoding="utf-8-sig"))
    return s

if __name__=='__main__':
    source=ROOT.joinpath('mod/FoxholeRTS/Scripts/main.lua').read_text(encoding='utf-8')
    result=build(source)
    HERE.joinpath('economy_integrated.patch').write_text(''.join(difflib.unified_diff(source.splitlines(True),result.splitlines(True),fromfile='a/mod/FoxholeRTS/Scripts/main.lua',tofile='b/mod/FoxholeRTS/Scripts/main.lua')),encoding='utf-8')
    print('Patch isolado gerado; main.lua intacto')
