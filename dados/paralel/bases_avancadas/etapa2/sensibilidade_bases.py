"""BASES_AVANCADAS: sensibilidade da bateria. Cada MUTANTE (uma alteracao pequena e errada no candidato_v4, feita em memoria e gravada
num arquivo temporario) tem de ser PEGO por pelo menos uma suite (rc != 0); mutante vivo = teste fraco. O harness le o candidato
de BASES_V4_FILE quando a variavel existe. Nada e escrito no repositorio.

  cd /d/GitHub/foxhole-rts && PYTHONPATH=D:/tools/pylibs PYTHONDONTWRITEBYTECODE=1 \
      python dados/paralel/bases_avancadas/etapa2/sensibilidade_bases.py
"""
import os
import subprocess
import sys
import tempfile
from pathlib import Path

HERE = Path(__file__).resolve().parent
ROOT = HERE.parents[3]
CAND = HERE / "candidato_v4/main.lua"

# (nome, trecho original, substituto, suites que devem pegar). Fora de proposito: NaN/inf em x/y/z/yaw/hp do fwd - o validador generico
# do save (sv.validate, "tabela de dados") ja recusa antes de fwdValid; fin() la e defesa em profundidade (mutante equivalente).
MUTANTES = [
    ("debita antes de validar o spawn", "    local a, err = logi.fwdSpawn(cls, plan.x, plan.y, plan.z, plan.yaw)\n",
     "    logi.bmat = logi.bmat - F.cost\n    local a, err = logi.fwdSpawn(cls, plan.x, plan.y, plan.z, plan.yaw)\n", ["construcao"]),
    ("custo da base 300 -> 200", "cost = 300, hp = 1725", "cost = 200, hp = 1725", ["construcao"]),
    ("ignora a reserva do caminhao destruido", "local free = logi.bmat - logi.rebuildReserve()   -- caminhao destruido tem prioridade sobre a base",
     "local free = logi.bmat", ["construcao"]),
    ("fwdLose deixa de ser idempotente", "    if not fb or fb.dead then return false end\n    fb.dead = true\n",
     "    if not fb then return false end\n    fb.dead = true\n", ["perda"]),
    ("fwdLose nao zera o estoque", "    for _, kind in ipairs(CFG.LOGI.products) do dep[kind] = 0 end\n    local a = fb.actor\n",
     "    local a = fb.actor\n", ["perda"]),
    ("canReinforce conta base capturada", "if not fb.dead and fb.pt.owner == CFG.FRIENDLY_TEAM and (fb.dep.shirts or 0) >= 1 then return true end",
     "if not fb.dead and (fb.dep.shirts or 0) >= 1 then return true end", ["perda"]),
    ("trabalhadores contam no SQUAD_MAX", "    for _, m in ipairs(squad) do if m.role ~= \"worker\" then n = n + 1 end end\n",
     "    for _, m in ipairs(squad) do n = n + 1 end\n", ["trabalhadores"]),
    ("ponto sem base volta a ser capaz de reforcar", "    return fb ~= nil and not fb.dead and dep.pt ~= nil and dep.pt.owner == CFG.FRIENDLY_TEAM\nend",
     "    return true\nend", ["recrutamento", "perda"]),
    ("spawnCommit nao confere o estoque", "    if (dep.shirts or 0) < need.shirts or (dep.rifle or 0) < need.rifle then\n        log(\"spawnCommit recusado: estoque mudou",
     "    if false then\n        log(\"spawnCommit recusado: estoque mudou", ["perda", "recrutamento"]),
    ("recruit logistico volta ao ramo antigo", "if logi.on and combat.mode ~= \"assault\" then return logi.recruit(role, at) end",
     "if false then return logi.recruit(role, at) end", ["recrutamento", "trabalhadores"]),
    ("save aceita hp acima do maximo", "r.hp > 0 and r.hp <= F.hp", "r.hp > 0", ["persistencia_bases"]),
    ("save aceita base longe do ponto", "> CFG.POINT_RADIUS then return nil, \"base \" .. i .. \" longe do ponto\" end",
     "> 1e12 then return nil, \"base \" .. i .. \" longe do ponto\" end", ["persistencia_bases"]),
    ("save aceita base em ponto inimigo", "if q.owner == CFG.ENEMY_TEAM then return nil, \"base \" .. i .. \" em ponto inimigo\" end",
     "", ["persistencia_bases"]),
    ("save aceita estoque acima de 15 slots", "if slots > F.cap then return nil,", "if slots > 1e9 then return nil,", ["persistencia_bases"]),
    ("save aceita ponto duplicado", "or seen[r.pt] then return nil, \"base \" .. i .. \" ponto\" end", "then return nil, \"base \" .. i .. \" ponto\" end", ["persistencia_bases"]),
    ("save nao grava as bases", "    d.fwd = logi.fwdSnapshot()", "    d.fwd = nil", ["persistencia_bases"]),
    ("spawn da base aceita ator em destruicao", "assert(valid(a) and not a.bActorIsBeingDestroyed, \"base não nasceu ativa\")",
     "assert(valid(a), \"base não nasceu ativa\")", ["construcao"]),
    ("teto de 15 slots some da carga do caminhao", "    return math.max(0, CFG.FWD.cap - used)\nend", "    return math.huge\nend", ["perda"]),
    ("saida de base sem posicao exata", "if at and at.exact then x, y, z = at.X, at.Y,", "if false then x, y, z = at.X, at.Y,", ["recrutamento"]),
    ("tecla J deixa de ignorar modificador","RegisterKeyBind(Key.J, onGame(plain(function()", "RegisterKeyBind(Key.J, onGame((function(f) return f end)(function()", ["painel_teclas"]),
    ("derrota ignora estoque das bases", "        if not fb.dead and fb.pt.owner == CFG.FRIENDLY_TEAM and (fb.dep.shirts or 0) >= 1 then return true end\n",
     "", ["perda"]),
]


def main():
    base = CAND.read_bytes().decode("utf-8")
    env0 = dict(os.environ, PYTHONDONTWRITEBYTECODE="1", PYTHONIOENCODING="utf-8")
    alive = []
    with tempfile.TemporaryDirectory() as td:
        for i, (nome, old, new, suites) in enumerate(MUTANTES, 1):
            nl = "\r\n" if "\r\n" in base else "\n"
            o = old.replace("\n", nl)
            n = new.replace("\n", nl)
            assert base.count(o) == 1, "mutante %d (%s): trecho nao unico (%d)" % (i, nome, base.count(o))
            f = Path(td) / ("mut%d.lua" % i)
            f.write_bytes(base.replace(o, n).encode("utf-8"))
            caught = []
            for s in suites:
                r = subprocess.run([sys.executable, "-B", str(HERE / ("test_%s.py" % s))], capture_output=True, text=True,
                                   env=dict(env0, BASES_V4_FILE=str(f)), cwd=str(ROOT))
                if r.returncode != 0:
                    caught.append(s)
            status = "PEGO " if caught else "VIVO "
            print("%s mutante %2d: %-48s -> %s" % (status, i, nome, ", ".join(caught) if caught else "NENHUMA suite falhou (%s)" % ", ".join(suites)))
            if not caught:
                alive.append(nome)
    print("\n%d mutantes, %d pegos, %d vivos" % (len(MUTANTES), len(MUTANTES) - len(alive), len(alive)))
    sys.exit(1 if alive else 0)


if __name__ == "__main__":
    main()
