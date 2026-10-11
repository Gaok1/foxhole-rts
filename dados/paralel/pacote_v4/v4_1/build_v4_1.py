"""PACOTE_V4 / v4.1: trabalhadores (role "worker") NAO contam na escala das ondas inimigas (decisao do orquestrador).

Le dados/paralel/bases_avancadas/etapa2/candidato_v4/main.lua (somente leitura) e aplica 4 trocas por ancora unica:
  1. waveTick: tamanho da onda  `math.floor(#squad * CFG.WAVE_SQUAD_SCALE)`  ->  `rts.combatCount()`  (escala de dificuldade);
  2. waveTick: aviso "proxima onda em ..." mostra o esquadrao de combate, nao o total com trabalhadores;
  3. logi.noReinforce (ramo legado/Assalto): derrota por falta de tropa usa `rts.combatCount() == 0` (o ramo logistico ja usava);
     sem isso, no Assalto 3 trabalhadores vivos impediriam a derrota.
  4. squadCenter: centro so dos combatentes vivos; sem combatente vivo, de todos os vivos; sem ninguem, nil (decide onde ficam pontos iniciais,
     de onde vem onda e reforco, arame inimigo, orientacao das fortificacoes e o recrutamento sem cursor).
`rts.combatCount` ja existe (tabela rts, definida antes dos 3 usos): nenhum local de topo novo.
Escreve SO dentro de v4_1/: candidato/main.lua (CRLF), v4_1.patch (CRLF, `patch --binary` sobre o candidato_v4), SHA256.txt.

  cd /d/GitHub/foxhole-rts && PYTHONDONTWRITEBYTECODE=1 python dados/paralel/pacote_v4/v4_1/build_v4_1.py
"""
import difflib
import hashlib
import sys
from pathlib import Path

sys.dont_write_bytecode = True
HERE = Path(__file__).resolve().parent
SRC = HERE.parents[1] / "bases_avancadas/etapa2/candidato_v4/main.lua"
SHA_V4 = "025e3b80f76c5f13c4f2ed5ea83e04acfa7de79873c4308642badc5d072aaab0"

EDITS = [
    ("tamanho da onda (escala de dificuldade)",
     "            + math.floor(#squad * CFG.WAVE_SQUAD_SCALE))\n",
     "            + math.floor(rts.combatCount() * CFG.WAVE_SQUAD_SCALE))   -- v4.1: trabalhadores da coleta nao escalam a onda\n"),
    ("aviso da proxima onda",
     '            combat.broken and " (o inimigo se reagrupa)" or "", #squad, economy.manpower))\n',
     '            combat.broken and " (o inimigo se reagrupa)" or "", rts.combatCount(), economy.manpower))\n'),
    ("squadCenter: so combatentes vivos (fallback: todos os vivos)",
     "local function squadCenter()\n    local sx, sy, sz, n = 0, 0, 0, 0\n    for _, m in ipairs(squad) do\n        if alive(m) then\n            local l = loc(m)\n            sx, sy, sz, n = sx + l.X, sy + l.Y, sz + l.Z, n + 1\n        end\n    end\n    if n == 0 then return nil end\n    return { X = sx / n, Y = sy / n, Z = sz / n }\nend\n",
     "local function squadCenter()\n    -- v4.1: trabalhadores da coleta nao puxam ondas/reforco/pontos para o campo de sucata; so sem combatente vivo o centro e o de todos\n    for pass = 1, 2 do\n        local sx, sy, sz, n = 0, 0, 0, 0\n        for _, m in ipairs(squad) do\n            if alive(m) and (pass == 2 or m.role ~= \"worker\") then\n                local l = loc(m)\n                sx, sy, sz, n = sx + l.X, sy + l.Y, sz + l.Z, n + 1\n            end\n        end\n        if n > 0 then return { X = sx / n, Y = sy / n, Z = sz / n } end\n    end\n    return nil\nend\n"),
    ("derrota por falta de tropa (legado/Assalto)",
     "    return #squad == 0 and economy.manpower < CFG.WEAPONS.rifle.cost\nend\n",
     "    return rts.combatCount() == 0 and economy.manpower < CFG.WEAPONS.rifle.cost   -- v4.1: trabalhadores nao seguram a partida\nend\n"),
]


def main():
    raw = SRC.read_bytes()
    sha = hashlib.sha256(raw).hexdigest()
    if sha != SHA_V4:
        sys.exit("candidato_v4 mudou: %s (esperado %s)" % (sha, SHA_V4))
    s = raw.decode("utf-8")
    assert "\r\n" in s and s.count("\r\n") == s.count("\n"), "candidato_v4 deve ser CRLF consistente"
    t = s
    for name, old, new in EDITS:
        old, new = old.replace("\n", "\r\n"), new.replace("\n", "\r\n")
        c = t.count(old)
        if c != 1:
            sys.exit("ancora '%s' aparece %d vezes (esperado 1)" % (name, c))
        t = t.replace(old, new)
        print("ok:", name)
    # sobra de #squad como escala? (so informa; os demais usos sao contagem de tela, selecao, persistencia, indice)
    out = t.encode("utf-8")
    (HERE / "candidato").mkdir(exist_ok=True)
    (HERE / "candidato/main.lua").write_bytes(out)
    h = hashlib.sha256(out).hexdigest()
    a, b = s.splitlines(keepends=True), t.splitlines(keepends=True)
    d = difflib.unified_diff(a, b, "a/main.lua", "b/main.lua", n=3, lineterm="\r\n")
    (HERE / "v4_1.patch").write_bytes("".join(d).encode("utf-8"))
    (HERE / "SHA256.txt").write_text("%s  candidato/main.lua (v4.1)\n%s  base: candidato_v4/main.lua (v4)\n" % (h, SHA_V4), encoding="utf-8")
    print("v4.1 SHA256:", h, "| bytes", len(out), "| linhas", t.count("\n"))


if __name__ == "__main__":
    main()
