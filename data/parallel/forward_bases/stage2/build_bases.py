"""BASES_AVANCADAS etapa 2: gera candidate_v4/main.lua = candidate_v3/main.lua (coleta manual; SOMENTE LEITURA) + bases avancadas.
Ancoras exatas e unicas (fail-closed). CRLF como o original.

  cd /d/GitHub/foxhole-rts && PYTHONPATH=D:/tools/pylibs PYTHONDONTWRITEBYTECODE=1 \
      python data/parallel/forward_bases/stage2/build_bases.py

Saidas (so nesta pasta): candidate_v4/main.lua, candidate_v4/SHA256.txt, bases.patch (CRLF, aplica em candidate_v3/main.lua com
`git apply -p1`; caminhos a/main.lua b/main.lua) e bases_lf.patch (leitura). Importavel: apply(texto_LF) -> texto_LF.
"""
import sys

sys.dont_write_bytecode = True

import difflib  # noqa: E402
import hashlib  # noqa: E402
from pathlib import Path  # noqa: E402

HERE = Path(__file__).resolve().parent
ROOT = HERE.parents[3]
V3 = ROOT / "data/parallel/logistics_ai/finishing/manual_collection/candidate_v3/main.lua"
OUT = HERE / "candidate_v4"


def sha256(b):
    return hashlib.sha256(b).hexdigest()


def read_v3():
    raw = V3.read_bytes()
    assert raw.count(b"\r\n") == raw.count(b"\n") == raw.count(b"\r"), "candidate_v3 nao e CRLF consistente"
    return raw.decode("utf-8").replace("\r\n", "\n"), sha256(raw)


def lua(name):
    return HERE.joinpath(name).read_text(encoding="utf-8").replace("\r\n", "\n")


def once(s, old, new, what):
    n = s.count(old)
    assert n == 1, "ancora %s: %d ocorrencias (esperado 1): %r" % (what, n, old[:80])
    return s.replace(old, new, 1)


def cut(s, start, end, new, what):
    """Troca o trecho [start, end) (marcadores unicos) por new."""
    assert s.count(start) == 1 and s.count(end) == 1, "marcadores %s nao unicos" % what
    a, b = s.index(start), s.index(end)
    assert a < b, "marcadores %s fora de ordem" % what
    return s[:a] + new + s[b:]


def apply(s):
    assert "CFG.FWD" not in s, "bases avancadas ja aplicadas"
    # 1. CFG.SPAWN/CFG.FWD logo depois de CFG.SPAWN.startRifles (antes de logi.reset)
    s = once(s, "CFG.SPAWN.startRifles = CFG.SPAWN.startRifles or 10\n", "CFG.SPAWN.startRifles = CFG.SPAWN.startRifles or 10\n" + lua("bases_cfg.lua"), "CFG.FWD")
    # 2. versao da extensao `fwd` do save (CFG.PERSIST e definido bem depois)
    s = once(s, "maxList = 400, maxBuilt = 16 }", "maxList = 400, maxBuilt = 16, fwdVersion = 1 }", "PERSIST.fwdVersion")
    # 3. logi.reset destroi as bases (o estagio do Continuar nao e tocado)
    s = once(s, "    if logi.colReset then logi.colReset() end\n", "    if logi.colReset then logi.colReset() end\n    if logi.fwdReset then logi.fwdReset() end\n", "logi.reset")
    # 4. spawnSite/spawnCommit antigos (so base/trabalhador) saem daqui: as versoes novas ficam no bloco depois de `structures`
    s = cut(s, '-- Interface comum de nascimento (so o local "base" e o trabalhador; ver CFG.SPAWN). PURA',
            "-- Mantem ate COLETA.workers trabalhadores vivos",
            "-- logi.spawnSite / logi.spawnCommit: ver o bloco BASES AVANCADAS (depois de `local structures`).\n\n", "spawnSite antigo")
    # 5. trabalhadores nao contam no SQUAD_MAX: o limite deles e COLETA.workers (ja conferido acima em colMaintain)
    s = once(s, '    if not site or #squad >= CFG.SQUAD_MAX then\n        if t >= (K.noteT or 0) then\n            K.noteT = t + 30.0\n'
                '            notify(site and "esquadrão cheio: não há vaga para trabalhadores" or ("sem como criar trabalhadores para a coleta: " .. tostring(why)), 4.0)\n',
             '    if not site then   -- trabalhadores NAO contam no CFG.SQUAD_MAX: o limite deles e CFG.COLETA.workers\n        if t >= (K.noteT or 0) then\n            K.noteT = t + 30.0\n'
             '            notify("sem como criar trabalhadores para a coleta: " .. tostring(why), 4.0)\n', "colMaintain SQUAD_MAX")
    # 6. camisas/fuzis so para quem nasce soldado (base principal ou base avancada ativa)
    s = once(s, "    return result\nend\nfunction logi.need(dep)\n",
             "    if not logi.spawnCapable(dep) then result.shirts, result.rifle = 0, 0 end   -- ponto sem base so recebe municao/bandagem\n    return result\nend\nfunction logi.need(dep)\n", "logi.needs")
    s = once(s, "        local r = have / (C.want[kind] * #deps)\n",
             "        local nd = #deps\n        if kind == \"shirts\" or kind == \"rifle\" then   -- a demanda escala com os locais que nascem soldado\n"
             "            nd = 0\n            for _, d in ipairs(deps) do if logi.spawnCapable(d) then nd = nd + 1 end end\n            nd = math.max(1, nd)\n        end\n"
             "        local r = have / (C.want[kind] * nd)\n", "logi.nextKind")
    # 7. razao por base: caixas que chegam
    s = once(s, "        dest[kind] = (dest[kind] or 0) + n * (unpack and (CFG.LOGI.recipes[kind].units or 1) or 1)\n",
             "        dest[kind] = (dest[kind] or 0) + n * (unpack and (CFG.LOGI.recipes[kind].units or 1) or 1)\n"
             "        if unpack and dest.fb and dest.fb.led.rx[kind] then dest.fb.led.rx[kind] = dest.fb.led.rx[kind] + n * (CFG.LOGI.recipes[kind].units or 1) end\n", "moveCargo")
    # 8. a fabrica guarda bmat do pedido de base avancada, DEPOIS da reserva do caminhao destruido
    s = once(s, "    local keep = logi.rebuildReserve()\n    if logi.bmat - rc.bmat < keep then",
             "    local keep = logi.rebuildReserve() + logi.fwdReserve()\n    if logi.bmat - rc.bmat < keep then", "factoryStep keep")
    s = once(s, '            notify(string.format("fábrica guarda %d bmat para reconstruir caminhão", keep), 3.0)\n',
             '            notify(logi.fwdReserve() > 0 and string.format("fábrica guarda %d bmat (base avançada em %s%s)", keep, logi.fwdOrder.pt.name,\n'
             '                    logi.rebuildReserve() > 0 and " e caminhão" or "")\n'
             '                or string.format("fábrica guarda %d bmat para reconstruir caminhão", keep), 3.0)\n', "factoryStep nota")
    # 9. caminhao: teto de slots da base, camisa/fuzil so para quem nasce soldado, e devolucao se a base caiu no caminho
    s = once(s, "        local needs, cargo, remaining = logi.needs(dest), {}, C.cap\n        for _, kind in ipairs(C.products) do\n"
                "            local stock = logi.fac[kind] or 0\n            local wanted = logi.pin == dest and stock or needs[kind]\n"
                "            local n = math.min(stock, wanted, remaining)\n            cargo[kind], remaining = n, remaining - n\n        end\n",
             "        local needs, cargo, remaining = logi.needs(dest), {}, C.cap\n        local slots, capable = logi.fwdFree(dest), logi.spawnCapable(dest)\n"
             "        for _, kind in ipairs(C.products) do\n            local stock = logi.fac[kind] or 0\n"
             "            local wanted = logi.pin == dest and stock or needs[kind]\n"
             "            if not capable and (kind == \"shirts\" or kind == \"rifle\") then wanted = 0 end\n"
             "            local n = math.min(stock, wanted, remaining, slots)\n            cargo[kind], remaining, slots = n, remaining - n, slots - n\n        end\n", "truckStep carga")
    s = once(s, "        if logi.drive(tr, d, dt) then\n            logi.moveCargo(tr.cargo, d, true)\n",
             "        if logi.drive(tr, d, dt) then\n            local back = nil   -- base destruida no caminho: camisas/fuzis voltam a fabrica (credito so na chegada fisica)\n"
             "            if not logi.spawnCapable(d) and ((tr.cargo.shirts or 0) > 0 or (tr.cargo.rifle or 0) > 0) then\n"
             "                back = { ammo = 0, shirts = tr.cargo.shirts or 0, rifle = tr.cargo.rifle or 0, medical = 0 }\n"
             "                tr.cargo = { ammo = tr.cargo.ammo or 0, shirts = 0, rifle = 0, medical = tr.cargo.medical or 0 }\n"
             "            end\n            logi.moveCargo(tr.cargo, d, true)\n", "truckStep chegada")
    s = once(s, "            logi.delivered = (logi.delivered or 0) + 1\n            tr.cargo, tr.dest, tr.state = nil, nil, \"idle\"\n",
             "            logi.delivered = (logi.delivered or 0) + 1\n"
             "            if back then tr.cargo, tr.dest, tr.state = back, logi.factory, \"returnCargo\"\n"
             "            else tr.cargo, tr.dest, tr.state = nil, nil, \"idle\" end\n", "truckStep chegada fim")
    # 10. pedido pendente roda dentro do tick da logistica
    s = once(s, "    if not okc then logOnce(\"colStep\", errc) end\n",
             "    if not okc then logOnce(\"colStep\", errc) end\n    local okf, errf = pcall(logi.fwdTick, dt, t)\n    if not okf then logOnce(\"fwdTick\", errf) end\n", "logi.tick")
    # 11. painel: reserva do pedido e linha por base
    s = once(s, "        local keep = logi.rebuildReserve and logi.rebuildReserve() or 0\n",
             "        local trk = logi.rebuildReserve and logi.rebuildReserve() or 0\n        local ord = logi.fwdReserve and logi.fwdReserve() or 0\n        local keep = trk + ord\n", "hudLine keep")
    s = once(s, '            fab = string.format("guarda %d bmat para reconstruir caminhão (bmat %.0f)", keep, logi.bmat)\n',
             '            if ord > 0 then\n                fab = string.format("guarda %d bmat para %sbase avançada em %s (bmat %.0f)", keep,\n'
             '                    trk > 0 and "reconstruir caminhão e " or "", logi.fwdOrder.pt.name, logi.bmat)\n'
             '            else fab = string.format("guarda %d bmat para reconstruir caminhão (bmat %.0f)", keep, logi.bmat) end\n', "hudLine guarda")
    s = once(s, '            low and " | abaixo da meta" or "")\n    end\n',
             '            low and " | abaixo da meta" or "")\n        if logi.fwdLine and (d == logi.base or d.fb) then lines[#lines + 1] = logi.fwdLine(d) end\n    end\n', "hudLine fwdLine")
    # 12. morteiro inimigo fere a base
    s = once(s, '        if tr.state ~= "dead" and flatDist(hit, tr) <= radius * 1.5 then logi.hit(tr, dmg * 2, now()) end\n    end\nend\n',
             '        if tr.state ~= "dead" and flatDist(hit, tr) <= radius * 1.5 then logi.hit(tr, dmg * 2, now()) end\n    end\n'
             '    if team == CFG.ENEMY_TEAM and logi.fwdBlast then logi.fwdBlast(hit, radius, dmg) end\nend\n', "logi.blast")
    # 13. captura do ponto pelo inimigo: perda unica da base (o zeramento legado roda sobre estoque ja zero)
    s = once(s, "                if pt.dep then for _, kind in ipairs(CFG.LOGI.products) do pt.dep[kind] = 0 end end  -- estoque perdido\n",
             "                if pt.fb then pcall(logi.fwdLose, pt.fb, \"capturada\") end\n"
             "                if pt.dep then for _, kind in ipairs(CFG.LOGI.products) do pt.dep[kind] = 0 end end  -- estoque perdido\n", "pointsTick")
    # 14. spawnSquad: teto so de combate e saida exata
    s = once(s, "    n = math.min(n or CFG.SQUAD_SIZE, CFG.SQUAD_MAX - first)\n", "    n = math.min(n or CFG.SQUAD_SIZE, CFG.SQUAD_MAX - rts.combatCount())   -- trabalhadores nao contam\n", "spawnSquad teto")
    s = once(s, "        local z = groundZ(x, y) or base.Z\n        local m = spawnSoldier(",
             "        local z = groundZ(x, y) or base.Z\n        if at and at.exact then x, y, z = at.X, at.Y, (at.ground and groundZ(at.X, at.Y) or at.Z) end   -- saida de base: sem deslocamento de formacao\n"
             "        local m = spawnSoldier(", "spawnSquad exact")
    # 15. recruit: teto so de combate e ramo logistico (fora do Assalto) pela interface comum
    s = once(s, '    if #squad >= CFG.SQUAD_MAX then notify("esquadrao no maximo (" .. CFG.SQUAD_MAX .. ")", 3.0); return false end\n    if role == "officer" then',
             '    if rts.combatCount() >= CFG.SQUAD_MAX then notify("esquadrao no maximo (" .. CFG.SQUAD_MAX .. ")", 3.0); return false end\n    if role == "officer" then', "recruit teto")
    s = once(s, '    if economy.manpower < w.cost then\n        notify(string.format("mao de obra insuficiente para %s: %.0f/%d", w.name, economy.manpower, w.cost), 3.0)\n        return false\n    end\n    at = at or deployPoint()\n',
             '    if logi.on and combat.mode ~= "assault" then return logi.recruit(role, at) end   -- ramo logistico: estoque da base, sem mao de obra\n'
             '    if economy.manpower < w.cost then\n        notify(string.format("mao de obra insuficiente para %s: %.0f/%d", w.name, economy.manpower, w.cost), 3.0)\n        return false\n    end\n    at = at or deployPoint()\n', "recruit ramo")
    # 16. derrota: ramo logistico = sem tropa de combate e sem como reforcar
    s = once(s, "    if #squad == 0 and economy.manpower < CFG.WEAPONS.rifle.cost then\n        combat.auto = false\n",
             "    if logi.noReinforce() then\n        combat.auto = false\n", "waveTick derrota")
    # 17. bloco de funcoes (depois de `structures`, que as funcoes de colocacao usam)
    s = once(s, "local structures = {}\n", "local structures = {}\n" + lua("bases_funcs.lua"), "bloco funcoes")
    # 18. persistencia: coletar, validar, preflight, estagio e bind
    s = once(s, "    d.infra, d.enemy = sv.infraSnapshot(), sv.enemySnapshot()\n    return d\n",
             "    d.infra, d.enemy = sv.infraSnapshot(), sv.enemySnapshot()\n    d.fwd = logi.fwdSnapshot()\n    return d\n", "sv.collect")
    s = once(s, "        elogi=1 }\n", "        elogi=1, fwd=1 }\n", "sv.validate known")
    s = once(s, '    local I = d.infra\n    if I ~= nil then\n        if type(I) ~= "table" then return nil, "infra" end\n',
             '    if d.fwd ~= nil then   -- bases avancadas (extensao fwd v1): erro recusa o save inteiro (como infra)\n'
             '        local okF, resF, whyF = pcall(logi.fwdValid, d)\n'
             '        if not okF then return nil, "bases avançadas inválidas" end\n'
             '        if not resF then return nil, whyF end\n    end\n'
             '    local I = d.infra\n    if I ~= nil then\n        if type(I) ~= "table" then return nil, "infra" end\n', "sv.validate fwd")
    s = once(s, '    if d.logi and not plan.apply and not logi.ready() then return nil, "cadeia logística sem atores ativos carregados" end\n',
             '    if d.fwd then\n        local okF, whyF = logi.fwdPreflight(d)\n        if not okF then return nil, whyF end\n    end\n'
             '    if d.logi and not plan.apply and not logi.ready() then return nil, "cadeia logística sem atores ativos carregados" end\n', "sv.preflight")
    s = once(s, "    if plan.apply then\n        local built, err = logi.applyPlan(plan.apply)\n",
             "    if d.fwd then   -- estagio: cria TODAS as bases salvas ou nenhuma (antes de tocar na partida atual)\n"
             "        local okS, errS = logi.fwdStage(d)\n        if not okS then\n"
             "            log(\"continuar recusado: base avançada \" .. tostring(errS))\n"
             "            notify(\"Continuar recusado: base avançada salva não foi refeita (\" .. tostring(errS) .. \"); nada mudou\", 8.0)\n            return false\n        end\n    end\n"
             "    if plan.apply then\n        local built, err = logi.applyPlan(plan.apply)\n", "sv.load estagio")
    s = once(s, '            notify("Continuar recusado: infraestrutura salva não foi refeita (" .. tostring(err) .. "); nada mudou", 8.0)\n            return false\n',
             '            notify("Continuar recusado: infraestrutura salva não foi refeita (" .. tostring(err) .. "); nada mudou", 8.0)\n            logi.fwdStageClear()\n            return false\n', "sv.load infra falha")
    s = once(s, "    if d.logi and not logi.ready() then return false end\n    local n = sv.restore(d)\n",
             "    if d.logi and not logi.ready() then logi.fwdStageClear(); return false end\n    local n = sv.restore(d)\n", "sv.load ready")
    s = once(s, "    sv.degraded = #problems > 0 and {",
             "    if d.fwd then\n        local okF, bad = pcall(logi.fwdBind, d.fwd)\n"
             "        if not okF then problems[#problems + 1] = \"bases avançadas não refeitas\"; pcall(logi.fwdStageClear)\n"
             "        else for _, p in ipairs(bad) do problems[#problems + 1] = p end end\n    end\n"
             "    sv.degraded = #problems > 0 and {", "sv.load bind")
    # 19. teclas: Shift+J constroi; J puro ignora disparo com modificador (nao sabemos se o UE4SS dispara so a combinacao)
    s = once(s, "RegisterKeyBind(Key.J, onGame(function()\n    if rts.active then local c = cursorPoint(); if c then addPoint(c.X, c.Y) end end\nend))\n",
             "RegisterKeyBind(Key.J, onGame(plain(function()\n    if rts.active then local c = cursorPoint(); if c then addPoint(c.X, c.Y) end end\nend)))\n"
             "RegisterKeyBind(Key.J, { ModifierKey.SHIFT }, onGame(function() if rts.active then logi.fwdKey(cursorPoint()) end end))\n", "teclas J")
    s = once(s, '    "Ctrl+1/2/3/4/0: recrutar fuzileiro/metralhador/atirador/médico/oficial (cursor num ponto seu = nasce lá)",\n',
             '    "Ctrl+1/2/3/4/0: recrutar fuzileiro/metralhador/atirador/médico/oficial (logística: nasce na base ou numa base avançada com camisas; cursor numa base = só nela)",\n', "HELP recrutar")
    s = once(s, '   K: barreira   J: ponto",\n', '   K: barreira   J: ponto   Shift+J: base avançada (300 bmat, 2 toques)",\n', "HELP J")
    s = once(s, "K barreira, J ponto, Home recuar", "K barreira, J ponto, Shift+J base avançada, Home recuar", "log final")
    return s


def to_crlf(t):
    assert "\r" not in t
    return t.replace("\n", "\r\n").encode("utf-8")


def udiff(a, b):
    return "".join(difflib.unified_diff(a.splitlines(True), b.splitlines(True), fromfile="a/main.lua", tofile="b/main.lua"))


def main():
    src, sha_before = read_v3()
    out = apply(src)
    OUT.mkdir(exist_ok=True)
    cand = OUT / "main.lua"
    cand.write_bytes(to_crlf(out))
    d = udiff(src, out)
    HERE.joinpath("bases.patch").write_bytes(to_crlf(d))
    HERE.joinpath("bases_lf.patch").write_text(d, encoding="utf-8", newline="\n")
    assert sha256(V3.read_bytes()) == sha_before, "candidate_v3 mudou durante o build"
    OUT.joinpath("SHA256.txt").write_text(
        "candidate_v3/main.lua (antes) : %s\ncandidato_v3/main.lua (depois): %s\ncandidato_v4/main.lua (CRLF): %s\n"
        % (sha_before, sha256(V3.read_bytes()), sha256(cand.read_bytes())), encoding="utf-8", newline="\n")
    ds = d.splitlines()[2:]
    print("candidate_v4/main.lua SHA256 (CRLF): %s" % sha256(cand.read_bytes()))
    print("candidate_v3 SHA256 antes/depois: %s (iguais)" % sha_before)
    print("bases.patch: +%d/-%d linhas" % (sum(1 for l in ds if l.startswith("+")), sum(1 for l in ds if l.startswith("-"))))


if __name__ == "__main__":
    main()
