"""FERRAMENTA do trabalhador: marreta do jogo (SledgeHammer) na mao do trabalhador da coleta manual de sucata.

Le dados/paralel/pacote_v4/v4_1/candidato/main.lua (v4.1, SOMENTE LEITURA) e aplica 5 trocas por ancora unica:
  1. CFG.WEAPONS.worker: meshW/meshC = SledgeHammer_SK (SkeletalMesh do BPSledgeHammerComponent) e grip = 51 (TwoHandItem, o
     EquippedGripType do proprio item no jogo). range/dmg/ammo/hit/supp continuam 0: o trabalhador nao atira nem gasta municao.
  2. anim.onUpdate: ferramenta nunca mira (aiming exige weapon.range > 0): uma ordem de area dada ao trabalhador nao poe a marreta
     "no ombro" (bIsInScopeMode/canEnter*Scoping).
  3. anim.onUpdate: ActivityState DoWork (15) enquanto m.workAnimUntil esta no futuro (sinal visual de trabalho; desliga com
     CFG.COLETA.workAnim = nil).
  4. CFG.COLETA.workAnim = 15 (ECharacterActivityState::DoWork).
  5. logi.colUnit, ramo "gather" calmo: m.workAnimUntil = os.clock() + 0.6.
Nenhum local de topo novo (o candidato v4.1 tem 178; limite 200). Nenhuma tecla nova.
Escreve SO dentro de ferramenta/: candidato/main.lua (CRLF), ferramenta.patch (CRLF), SHA256.txt.

  cd /d/GitHub/foxhole-rts && PYTHONDONTWRITEBYTECODE=1 python dados/paralel/ia_logistica/acabamento/coleta_manual/ferramenta/build_ferramenta.py
"""
import difflib
import hashlib
import sys
from pathlib import Path

sys.dont_write_bytecode = True
HERE = Path(__file__).resolve().parent
SRC = HERE.parents[3] / "pacote_v4/v4_1/candidato/main.lua"
SHA_V41 = "62245d23af36160f589707fe422b6fb167abaa58482ef7f58a49cd39021b598f"

MESH = "/Game/Meshes/Weapons/SledgeHammer_SK.SledgeHammer_SK"
GRIP = 51   # EEquippedWeaponGripType::TwoHandItem (tabela do enum no exe + BPSledgeHammerComponent no pak; ver RELATORIO.md)

EDITS = [
    ("CFG.WEAPONS.worker: marreta + grip TwoHandItem",
     "-- Trabalhador: soldado SEM fuzil (sem malha de arma, alcance 0: nunca atira), nasce na base (logi.workerDepot), custa 1 camisa\n"
     "-- do estoque desse deposito, debitada so apos o spawn confirmado. Fica no esquadrao (inimigo o enxerga e o ataca, morte,\n"
     "-- marcadores e save/continuar funcionam como em qualquer soldado). grip 0 = sem arma equipada (confirmar no laboratorio).\n"
     'CFG.WEAPONS.worker = { name = "trabalhador", cost = 0, range = 0.0, interval = 9.0, hit = 0.0, dmg = 0.0, supp = 0.0, pitch = 1.0, ammo = 0, grip = 0 }\n',
     "-- Trabalhador: soldado SEM tiro (alcance 0, dmg 0, ammo 0: nunca atira nem gasta municao) com a FERRAMENTA do jogo, a marreta\n"
     "-- (BPSledgeHammerComponent: ItemMesh SledgeHammer_SK, EquippedGripType TwoHandItem = 51, TaskActivityState DoWork). Mesma\n"
     "-- malha dos dois lados. Nasce na base (logi.workerDepot), custa 1 camisa do estoque desse deposito, debitada so apos o spawn\n"
     "-- confirmado. Fica no esquadrao (inimigo o enxerga e o ataca, morte, marcadores e save/continuar funcionam como em qualquer\n"
     "-- soldado). Se a marreta der T-pose no laboratorio: grip = 2 (pistola, validado ao vivo) ou, sem malha, grip = 0.\n"
     'CFG.WEAPONS.worker = { name = "trabalhador", cost = 0, range = 0.0, interval = 9.0, hit = 0.0, dmg = 0.0, supp = 0.0, pitch = 1.0, ammo = 0,\n'
     '    grip = %d, meshW = "%s", meshC = "%s" }\n' % (GRIP, MESH, MESH)),
    ("anim.onUpdate: ferramenta nunca mira",
     "    local aiming = c < (m.aimUntil or 0) and m.stillSince ~= nil\n",
     "    local aiming = c < (m.aimUntil or 0) and m.stillSince ~= nil and w.range > 0   -- ferramenta (range 0) nunca poe a arma no ombro\n"),
    ("anim.onUpdate: DoWork enquanto coleta",
     "    elseif c < (m.fireAnimUntil or 0) then a.ActivityState = 3 end\nend\n",
     "    elseif c < (m.fireAnimUntil or 0) then a.ActivityState = 3\n"
     "    elseif c < (m.workAnimUntil or 0) and CFG.COLETA.workAnim then a.ActivityState = CFG.COLETA.workAnim end   -- DoWork 15: trabalhador na coleta\nend\n"),
    ("CFG.COLETA.workAnim",
     "    retry = 3.0,          -- s entre reenvios da rota\n}\n",
     "    retry = 3.0,          -- s entre reenvios da rota\n"
     "    workAnim = 15,        -- ECharacterActivityState::DoWork enquanto o trabalhador junta sucata (nil = sem sinal visual)\n}\n"),
    ("logi.colUnit: sinal de trabalho no ramo gather",
     "        elseif u.calm then\n            local take = math.min(C.rate * dt, C.cap - u.carry)\n",
     "        elseif u.calm then\n            m.workAnimUntil = os.clock() + 0.6   -- anim.onUpdate: ActivityState DoWork\n            local take = math.min(C.rate * dt, C.cap - u.carry)\n"),
]


def main():
    raw = SRC.read_bytes()
    sha = hashlib.sha256(raw).hexdigest()
    if sha != SHA_V41:
        sys.exit("candidato v4.1 mudou: %s (esperado %s)" % (sha, SHA_V41))
    s = raw.decode("utf-8")
    assert "\r\n" in s and s.count("\r\n") == s.count("\n"), "v4.1 deve ser CRLF consistente"
    t = s
    for name, old, new in EDITS:
        old, new = old.replace("\n", "\r\n"), new.replace("\n", "\r\n")
        c = t.count(old)
        if c != 1:
            sys.exit("ancora '%s' aparece %d vezes (esperado 1)" % (name, c))
        t = t.replace(old, new)
        print("ok:", name)
    out = t.encode("utf-8")
    (HERE / "candidato").mkdir(exist_ok=True)
    (HERE / "candidato/main.lua").write_bytes(out)
    h = hashlib.sha256(out).hexdigest()
    a, b = s.splitlines(keepends=True), t.splitlines(keepends=True)
    d = difflib.unified_diff(a, b, "a/main.lua", "b/main.lua", n=3, lineterm="\r\n")
    (HERE / "ferramenta.patch").write_bytes("".join(d).encode("utf-8"))
    (HERE / "SHA256.txt").write_text("%s  candidato/main.lua (ferramenta)\n%s  base: pacote_v4/v4_1/candidato/main.lua (v4.1)\n" % (h, SHA_V41), encoding="utf-8")
    print("ferramenta SHA256:", h, "| bytes", len(out), "| linhas", t.count("\n"))


if __name__ == "__main__":
    main()
