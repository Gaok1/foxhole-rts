"""COLETA_MANUAL: gera candidato_v3/main.lua = candidato_v2/main.lua (pilha ECONOMIA > IA v2 > reserva_bmat > INTERFACE v2 >
PERSISTENCIA v2, SOMENTE LEITURA) + coleta manual. Ancoras exatas e unicas (fail-closed). CRLF como o original.

  cd /d/GitHub/foxhole-rts && PYTHONPATH=D:/tools/pylibs PYTHONDONTWRITEBYTECODE=1 \
      python dados/paralel/ia_logistica/acabamento/coleta_manual/build_coleta.py

Saidas (so nesta pasta): candidato_v3/main.lua, candidato_v3/SHA256.txt, coleta_manual.patch (CRLF, aplica em
candidato_v2/main.lua com `git apply -p1`/`patch -p1`; caminhos a/main.lua b/main.lua) e coleta_manual_lf.patch (leitura).
Importavel: apply(texto_LF) -> texto_LF, usado pelos testes.
"""
import sys

sys.dont_write_bytecode = True

import difflib  # noqa: E402
import hashlib  # noqa: E402
from pathlib import Path  # noqa: E402

HERE = Path(__file__).resolve().parent
ROOT = HERE.parents[4]
V2 = ROOT / "dados/paralel/ensaio_integracao/candidato_v2/main.lua"
OUT = HERE / "candidato_v3"


def sha256(b):
    return hashlib.sha256(b).hexdigest()


def read_v2():
    raw = V2.read_bytes()
    assert raw.count(b"\r\n") == raw.count(b"\n") == raw.count(b"\r"), "candidato_v2 nao e CRLF consistente"
    return raw.decode("utf-8").replace("\r\n", "\n"), sha256(raw)


def lua(name):
    return HERE.joinpath(name).read_text(encoding="utf-8").replace("\r\n", "\n")


def once(s, old, new, what):
    n = s.count(old)
    assert n == 1, "ancora %s: %d ocorrencias (esperado 1): %r" % (what, n, old[:80])
    return s.replace(old, new, 1)


def apply(s):
    """Aplica a coleta manual sobre o texto (LF) do candidato v2. Falha se uma ancora nao for unica."""
    assert "CFG.COLETA" not in s, "coleta manual ja aplicada"
    # 1. CFG.COLETA logo depois de CFG.LOGI (antes de CFG.DEPLOY, scan e start, que a leem)
    s = once(s, 'logi.on, logi.prio = false, "auto"\n', 'logi.on, logi.prio = false, "auto"\n' + lua("coleta_cfg.lua"), "CFG.COLETA")
    # 2. logi.reset reinicia a coleta (descarta carga em maos, sem tocar em pawn)
    s = once(s, "function logi.reset()\n", "function logi.reset()\n    if logi.colReset then logi.colReset() end\n", "logi.reset")
    # 3. orcamento de implantacao: so estruturas + caminhoes de suprimento (400 + 400 + 2 x 100)
    s = once(s, "CFG.DEPLOY = { budget = 1100, ", "CFG.DEPLOY = { budget = CFG.COLETA.manualStart and 1000 or 1100, ", "CFG.DEPLOY.budget")
    # 4. quantos caminhoes a implantacao/scan/continuar exigem (sem o de recurso na partida manual)
    s = once(s, '    if #setup.trucks < CFG.LOGI.supply + 1 then\n        missing[#missing + 1] = string.format("caminhões (%d/%d)", #setup.trucks, CFG.LOGI.supply + 1)\n',
             '    if #setup.trucks < logi.trucksNeeded() then\n        missing[#missing + 1] = string.format("caminhões (%d/%d)", #setup.trucks, logi.trucksNeeded())\n', "logi.scan")
    s = once(s, "    local missing = math.max(0, CFG.LOGI.supply+1-#occupied)\n", "    local missing = math.max(0, logi.trucksNeeded()-#occupied)\n", "logi.deployPlan")
    s = once(s, "    local need = math.max(0, CFG.LOGI.supply + 1 - #occupied)\n", "    local need = math.max(0, logi.trucksNeeded() - #occupied)\n", "sv.infraPlan")
    # 4b. recrutar de combate nao gasta as camisas reservadas aos trabalhadores
    s = once(s, '    if dep and (dep.shirts or 0) < 1 then\n        notify("sem camisas na base: a fábrica e os caminhões trazem (L manda um caminhão)", 3.0)\n',
             '    local keep = dep and logi.workerReserve(dep) or 0\n    if dep and (dep.shirts or 0) < 1 + keep then\n'
             '        notify(keep > 0 and string.format("camisas da base reservadas aos trabalhadores da coleta (%d, reserva %d)", dep.shirts or 0, keep)\n'
             '            or "sem camisas na base: a fábrica e os caminhões trazem (L manda um caminhão)", 3.0)\n', "recruit shirts")
    # 4c. a ordem em fila do jogador (Shift+direito) tambem marca orderT, como as demais ordens (a coleta e a evacuacao medica dependem disso)
    s = once(s, '            m.hold, m.retreat = false, nil\n            if m.target or m.pathJob or m.focus then\n',
             '            m.hold, m.retreat, m.orderT = false, nil, os.clock()\n            if m.target or m.pathJob or m.focus then\n', "queueMove orderT")
    # 5. logi.start: estoque inicial da base (camisas para os primeiros trabalhadores; fuzis iniciais so na partida manual),
    #    bmat inicial baixo e caminhao de recurso ainda nao construido
    s = once(s, "ammo = C.ammo0, shirts = C.shirts0, rifle = 0, medical = 0 }\n",
             "ammo = C.ammo0, shirts = math.max(C.shirts0, CFG.COLETA.workers),\n"
             "        rifle = CFG.COLETA.manualStart and CFG.SPAWN.startRifles or 0, medical = 0 }\n", "logi.start base")
    s = once(s, "    logi.bmat = C.bmat0\n", "    logi.bmat = CFG.COLETA.manualStart and CFG.COLETA.bmat0 or C.bmat0\n", "logi.start bmat0")
    s = once(s, '    local pool = setup.trucks\n    for i = 1, C.supply + 1 do\n        local a = pool[i]\n'
                '        local tr = { kind = (i == 1) and "res" or "sup", pawn = a, hp = C.hp, off = 0, state = "idle", n = i }\n',
             '    local pool, manual = setup.trucks, CFG.COLETA.manualStart\n    for i = 1, C.supply + 1 do\n'
             '        local a = pool[manual and (i == 1 and C.supply + 1 or i - 1) or i]  -- manual: o de recurso usa o ultimo da fila (se houver), os de suprimento os primeiros\n'
             '        local tr = { kind = (i == 1) and "res" or "sup", pawn = a, hp = C.hp, off = 0, state = "idle", n = i }\n', "logi.start trucks")
    s = once(s, "        logi.trucks[i] = tr\n    end\n    logi.on = true\n",
             '        if manual and i == 1 then  -- caminhao de recurso ainda nao construido: a fabrica o faz (reconstrucao normal, 100 bmat)\n'
             '            tr.hp, tr.state, tr.rebuildT = 0, "dead", now()\n'
             '            if a then pcall(function() a:SetActorHiddenInGame(true) end) end\n'
             '        end\n'
             "        logi.trucks[i] = tr\n    end\n    logi.on = true\n", "logi.start dead res")
    # 6. truckStep: o de recurso reconstroi antes dos de suprimento; sem ator, nasce um (visual)
    s = once(s, "        if t >= tr.rebuildT and logi.bmat >= C.truckCost then\n",
             '        if t >= tr.rebuildT and logi.bmat >= C.truckCost and (tr.kind == "res" or not CFG.COLETA.resFirst or not logi.colDown()) then\n', "truckStep rebuild")
    s = once(s, '            if tr.pawn and valid(tr.pawn) then tr.pawn:SetActorHiddenInGame(false) end\n            notify("novo caminhão',
             '            if tr.pawn and valid(tr.pawn) then tr.pawn:SetActorHiddenInGame(false) else pcall(logi.spawnTruck, tr) end\n            notify("novo caminhão', "truckStep spawn")
    # 7. logi.tick chama a coleta (pcall: um erro nunca derruba a logistica)
    s = once(s, "    pcall(logi.convoyTick, dt, t)\n",
             "    pcall(logi.convoyTick, dt, t)\n    local okc, errc = pcall(logi.colStep, dt, t)\n    if not okc then logOnce(\"colStep\", errc) end\n", "logi.tick")
    # 8. funcoes (antes de logi.tick)
    s = once(s, "function logi.tick()\n", lua("coleta_funcs.lua") + "function logi.tick()\n", "funcoes")
    # 9. painel: uma linha so quando ha coleta
    s = once(s, '    lines[#lines + 1] = "Ctrl+L: foco na cadeia | Q/E: frentes | Espaço: último alerta"\n',
             '    local colLine = logi.colHud and logi.colHud() or nil\n    if colLine then lines[#lines + 1] = colLine end\n'
             '    lines[#lines + 1] = "Ctrl+L: foco na cadeia | Q/E: frentes | Espaço: último alerta"\n', "hudLine")
    return s


def to_crlf(t):
    assert "\r" not in t
    return t.replace("\n", "\r\n").encode("utf-8")


def udiff(a, b):
    return "".join(difflib.unified_diff(a.splitlines(True), b.splitlines(True), fromfile="a/main.lua", tofile="b/main.lua"))


def main():
    src, sha_before = read_v2()
    out = apply(src)
    OUT.mkdir(exist_ok=True)
    cand = OUT / "main.lua"
    cand.write_bytes(to_crlf(out))
    d = udiff(src, out)
    HERE.joinpath("coleta_manual.patch").write_bytes(to_crlf(d))
    HERE.joinpath("coleta_manual_lf.patch").write_text(d, encoding="utf-8", newline="\n")
    assert sha256(V2.read_bytes()) == sha_before, "candidato_v2 mudou durante o build"
    OUT.joinpath("SHA256.txt").write_text(
        "candidato_v2/main.lua (antes) : %s\ncandidato_v2/main.lua (depois): %s\ncandidato_v3/main.lua (CRLF): %s\n"
        % (sha_before, sha256(V2.read_bytes()), sha256(cand.read_bytes())), encoding="utf-8", newline="\n")
    ds = d.splitlines()[2:]
    print("candidato_v3/main.lua SHA256 (CRLF): %s" % sha256(cand.read_bytes()))
    print("candidato_v2 SHA256 antes/depois: %s (iguais)" % sha_before)
    print("coleta_manual.patch: +%d/-%d linhas" % (sum(1 for l in ds if l.startswith("+")), sum(1 for l in ds if l.startswith("-"))))


if __name__ == "__main__":
    main()
