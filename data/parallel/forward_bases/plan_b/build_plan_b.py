"""PLANO_B_BASE: visual "mesh"/"auto" da base avancada (Shift+J) sobre a pilha v4.1.

Le data/parallel/package_v4/v4_1/candidate/main.lua (SOMENTE LEITURA, SHA 62245d23...598f) e aplica edicoes por ancora unica
(falha fechado se uma ancora nao for unica). Os blocos novos vem de planob_cfg.lua e planob_funcs.lua (fragmentos desta pasta).
Escreve SO dentro de plan_b/: candidate/main.lua (CRLF), plan_b.patch (CRLF, `patch --binary` sobre o v4.1), SHA256.txt.
Nenhum local de topo novo: tudo em CFG.FWD / logi / S.

  cd /d/GitHub/foxhole-rts && PYTHONDONTWRITEBYTECODE=1 python data/parallel/forward_bases/plan_b/build_plan_b.py
"""
import difflib
import hashlib
import sys
from pathlib import Path

sys.dont_write_bytecode = True
HERE = Path(__file__).resolve().parent
SRC = HERE.parents[1] / "package_v4/v4_1/candidate/main.lua"
SHA_V41 = "62245d23af36160f589707fe422b6fb167abaa58482ef7f58a49cd39021b598f"


def frag(name):
    return (HERE / name).read_text(encoding="utf-8")


EDITS = [
    ("CFG.FWD.visual: default auto",
     '    code = "ForwardBase1", visual = "native",     -- visual "mesh" (plano B) esta DECLARADO mas NAO implementado\n',
     '    code = "ForwardBase1", visual = "auto",       -- "class" | "mesh" | "auto" (ver CFG.FWD.mesh, plano B); "native" = "class"\n'),
    ("CFG.FWD.mesh (malhas do plano B)",
     "S.fwdStage, S.fwdRuins = {}, {}\nlogi.fwd = {}\n",
     lambda: frag("planob_cfg.lua") + "S.fwdStage, S.fwdRuins = {}, {}\nlogi.fwd = {}\n"),
    ("fwdMake: partes extras e tipo do visual",
     "function logi.fwdMake(pt, x, y, z, yaw, hp, actor, exits)\n",
     "function logi.fwdMake(pt, x, y, z, yaw, hp, actor, exits, parts, kind)\n"),
    ("fwdMake: campos parts/kind",
     "maxHp = CFG.FWD.hp, actor = actor,\n        exits = exits, exitI = 0, dead = false,\n",
     'maxHp = CFG.FWD.hp, actor = actor,\n        parts = parts, kind = kind or "class", exits = exits, exitI = 0, dead = false,\n'),
    ("funcoes novas antes de fwdCheck",
     "-- Condicoes de construcao que nao dependem de bmat (valem de novo ao executar um pedido pendente). nil = pode; senao o motivo.\n",
     lambda: frag("planob_funcs.lua") +
     "-- Condicoes de construcao que nao dependem de bmat (valem de novo ao executar um pedido pendente). nil = pode; senao o motivo.\n"),
    ("fwdCheck: modo de visual valido",
     "    if F.visual ~= \"native\" then return \"visual '\" .. tostring(F.visual) .. \"' (plano B) não implementado\" end\n",
     "    if not logi.fwdMode() then return \"visual '\" .. tostring(F.visual) .. \"' desconhecido (class, mesh ou auto)\" end\n"),
    ("fwdBuild: classe so no modo class; criacao pelo visual",
     "    local cls = LoadAsset(F.asset)\n    if not valid(cls) then return false, \"classe da base avançada não carregou\", \"fail\" end\n"
     "    local plan, w = logi.fwdPlace(pt)\n    if not plan then return false, \"sem lugar: \" .. tostring(w), \"fail\" end\n"
     "    local a, err = logi.fwdSpawn(cls, plan.x, plan.y, plan.z, plan.yaw)\n"
     "    if not a then return false, \"ator recusado, nada debitado: \" .. tostring(err), \"fail\" end\n"
     "    logi.fwdMake(pt, plan.x, plan.y, plan.z, plan.yaw, F.hp, a, plan.exits)\n",
     "    local cls = nil\n    if logi.fwdMode() == \"class\" then   -- modo class: identico ao v4.1\n"
     "        cls = LoadAsset(F.asset)\n        if not valid(cls) then return false, \"classe da base avançada não carregou\", \"fail\" end\n    end\n"
     "    local plan, w = logi.fwdPlace(pt)\n    if not plan then return false, \"sem lugar: \" .. tostring(w), \"fail\" end\n"
     "    local a, parts, kind, err = logi.fwdCreate(plan.x, plan.y, plan.z, plan.yaw, cls)\n"
     "    if not a then return false, \"ator recusado, nada debitado: \" .. tostring(err), \"fail\" end\n"
     "    logi.fwdMake(pt, plan.x, plan.y, plan.z, plan.yaw, F.hp, a, plan.exits, parts, kind)\n"
     "    log(string.format(\"base avançada %s: visual %s\", pt.name, kind))\n"),
    ("fwdLose: destroi partes; sem ruina nativa para malha",
     "    local a = fb.actor\n    fb.actor = nil\n"
     "    if a and valid(a) and not a.bActorIsBeingDestroyed then pcall(function() a:K2_DestroyActor() end) end\n"
     "    if CFG.FWD.ruin then pcall(logi.fwdRuin, fb) end\n",
     "    local a, parts = fb.actor, fb.parts\n    fb.actor, fb.parts = nil, nil\n"
     "    logi.fwdKill(a, parts)\n"
     "    if CFG.FWD.ruin and fb.kind ~= \"mesh\" then pcall(logi.fwdRuin, fb) end\n"),
    ("fwdReset: destroi partes",
     "        local a = fb.actor\n        fb.actor, fb.dead = nil, true\n"
     "        if a and valid(a) and not a.bActorIsBeingDestroyed then pcall(function() a:K2_DestroyActor() end) end\n",
     "        local a, parts = fb.actor, fb.parts\n        fb.actor, fb.parts, fb.dead = nil, nil, true\n"
     "        logi.fwdKill(a, parts)\n"),
    ("fwdPreflight: visual pronto (class/mesh/auto)",
     "    local cls = LoadAsset(F.asset)\n    if not valid(cls) then return nil, \"classe da base avançada não carregou\" end\n"
     "    for i, r in ipairs(d.fwd.list) do\n        local gz",
     "    local okV, whyV = logi.fwdVisualReady()\n    if not okV then return nil, whyV end\n"
     "    for i, r in ipairs(d.fwd.list) do\n        local gz"),
    ("fwdStageClear: destroi partes",
     "        local a = st.actor\n"
     "        if a and valid(a) and not a.bActorIsBeingDestroyed then pcall(function() a:K2_DestroyActor() end) end\n    end\n    S.fwdStage = {}\n",
     "        logi.fwdKill(st.actor, st.parts)\n    end\n    S.fwdStage = {}\n"),
    ("fwdStage: classe so no modo class",
     "    local cls = LoadAsset(F.asset)\n    if not valid(cls) then return false, \"classe da base avançada não carregou\" end\n    local made, adopt = {}, {}\n",
     "    local cls = nil\n    if logi.fwdMode() == \"class\" then   -- modo class: identico ao v4.1\n"
     "        cls = LoadAsset(F.asset)\n        if not valid(cls) then return false, \"classe da base avançada não carregou\" end\n"
     "    elseif not logi.fwdMode() then return false, \"visual '\" .. tostring(F.visual) .. \"' desconhecido (class, mesh ou auto)\" end\n"
     "    local made, adopt = {}, {}\n"),
    ("fwdStage: criacao pelo visual e rollback com partes",
     "            local a, why = logi.fwdSpawn(cls, r.x, r.y, r.z, r.yaw)\n            if not a then\n"
     "                for _, x in ipairs(made) do pcall(function() x:K2_DestroyActor() end) end\n                return false, why\n            end\n"
     "            made[#made + 1] = a\n            S.fwdStage[i] = { actor = a }\n",
     "            local a, parts, kind, why = logi.fwdCreate(r.x, r.y, r.z, r.yaw, cls)\n            if not a then\n"
     "                for _, x in ipairs(made) do logi.fwdKill(x.actor, x.parts) end\n                return false, why\n            end\n"
     "            made[#made + 1] = { actor = a, parts = parts }\n            S.fwdStage[i] = { actor = a, parts = parts, kind = kind }\n"),
    ("fwdStage: adocao leva as partes",
     "        S.fwdStage[i] = { actor = old.actor }\n        old.actor = nil\n",
     "        S.fwdStage[i] = { actor = old.actor, parts = old.parts, kind = old.kind }\n        old.actor, old.parts = nil, nil\n"),
    ("fwdBind: partes e tipo para a base refeita",
     "logi.fwdMake(pt, r.x, r.y, r.z, r.yaw, r.hp, st.actor, exits); st.actor = nil end\n",
     "logi.fwdMake(pt, r.x, r.y, r.z, r.yaw, r.hp, st.actor, exits, st.parts, st.kind); st.actor, st.parts = nil, nil end\n"),
]


def build(src_bytes):
    s = src_bytes.decode("utf-8")
    assert "\r\n" in s and s.count("\r\n") == s.count("\n"), "v4.1 deve ser CRLF consistente"
    t = s
    for name, old, new in EDITS:
        new = new() if callable(new) else new
        old, new = old.replace("\n", "\r\n"), new.replace("\r\n", "\n").replace("\n", "\r\n")
        c = t.count(old)
        if c != 1:
            raise SystemExit("ancora '%s' aparece %d vezes (esperado 1)" % (name, c))
        t = t.replace(old, new)
    return s, t


def main():
    raw = SRC.read_bytes()
    sha = hashlib.sha256(raw).hexdigest()
    if sha != SHA_V41:
        sys.exit("v4.1 mudou: %s (esperado %s)" % (sha, SHA_V41))
    s, t = build(raw)
    for name, _, _ in EDITS:
        print("ok:", name)
    out = t.encode("utf-8")
    (HERE / "candidato").mkdir(exist_ok=True)
    (HERE / "candidate/main.lua").write_bytes(out)
    h = hashlib.sha256(out).hexdigest()
    a, b = s.splitlines(keepends=True), t.splitlines(keepends=True)
    d = difflib.unified_diff(a, b, "a/main.lua", "b/main.lua", n=3, lineterm="\r\n")
    (HERE / "plan_b.patch").write_bytes("".join(d).encode("utf-8"))
    (HERE / "SHA256.txt").write_text("%s  candidate/main.lua (v4.1 + plano B)\n%s  base: v4_1/candidate/main.lua\n" % (h, SHA_V41),
                                     encoding="utf-8")
    print("plano B SHA256:", h, "| bytes", len(out), "| linhas", t.count("\n"))
    assert hashlib.sha256(SRC.read_bytes()).hexdigest() == SHA_V41, "o v4.1 foi alterado!"


if __name__ == "__main__":
    main()
