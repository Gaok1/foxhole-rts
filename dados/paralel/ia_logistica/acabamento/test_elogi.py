"""Item 3: politica unica do `elogi` (cadeia inimiga no save) entre PERSISTENCIA e IA_LOGISTICA.

  cd /d/GitHub/foxhole-rts && PYTHONPATH=D:/tools/pylibs PYTHONDONTWRITEBYTECODE=1 PYTHONIOENCODING=utf-8 \
      python dados/paralel/ia_logistica/acabamento/test_elogi.py

POLITICA (persistencia_v2.lua + ia_logistica_v2.lua): a cadeia inimiga e estado secundario e regeneravel. Um `elogi`
invalido, de versao futura, ausente do save, sem a logistica do jogador ou lido por um mod sem o modulo NAO recusa o
save inteiro: so a secao e descartada; a cadeia inimiga recomeca do estoque de CENARIO (o mesmo razao 'inicial' de
uma partida nova), com aviso explicito (notify + log + evento), e nada do jogador e tocado nem creditado. Qualquer
outro campo invalido continua recusando tudo.

Cada 'carga do jogo' e um runtime Lua novo com o candidato inteiro (como em test_persistencia); so io/os, atores,
spawn e traces sao falsos. Roda em Lua 5.4 (UE4SS) e 5.5, nas pilhas com IA (IA_v2 e completa) e sem IA.
"""
import sys
from pathlib import Path

HERE = Path(__file__).resolve().parent
sys.path.insert(0, str(HERE))
sys.dont_write_bytecode = True
import test_persistencia_v2 as tp  # noqa: E402

STACKS = tp.STACKS
NO_IA = "main+ECONOMIA+PERSISTENCIA_v2"
IA_STACKS = [k for k in STACKS if k != NO_IA]
SAVE = tp.SAVE
MUTATE = 'local P = "%s"; local d = api.sv.decode(FS.files[P]); %s; FS.files[P] = "return " .. api.sv.ser(d)'

# Estado inimigo diferente do cenario: producao da retaguarda, uma entrega, consumo e um comboio na estrada.
ENEMY_RICH = '''
local L = api.logi
for _ = 1, 400 do clock = clock + 0.5; L.eTick(0.5, clock) end
assert(L.en.fac.ammo >= 1 and L.en.fac.shirts >= 2 and L.en.led.made.ammo > 0, "a retaguarda produziu")
L.en.fac.ammo, L.en.fac.shirts = L.en.fac.ammo - 1, L.en.fac.shirts - 2
L.en.pending = { ammo = 1, shirts = 2 }                 -- carga que estava na estrada (vira pendente no save)
assert(L.eConsume(4, "teste") == 4)                      -- consumo da frente
assert(L.eAudit())
assert(L.en.led.used.shirts == 4)
'''


def rich_save(stack, version):
    """Carga A: partida rica com estado inimigo proprio; devolve (runtime, ledger, enemy_canon, disco)."""
    tp.CANDIDATE = STACKS[stack]
    a = tp.new_load(version)
    a.execute("H.newWorld(); assert(api.logi.deploy())")
    a.execute("H.richMatch()")
    a.execute(ENEMY_RICH)
    ledger = a.eval("H.ledger()")
    canon = a.eval("H.canon(api.logi.eSnapshot())")
    assert a.eval("api.sv.save()") is True
    files = tp.disk(a)
    assert "elogi" in files[SAVE]
    return a, ledger, canon, files


def split(ledger):
    """(parte do jogador, parte inimiga) do H.ledger()."""
    head, _, tail = ledger.partition(" | inimigo=")
    enemy, _, rest = tail.partition(" | pontos=")
    return head + " | pontos=" + rest, enemy


def load_in(stack, version, files, newworld="H.newWorld()", mine=False):
    tp.CANDIDATE = STACKS[stack]
    b = tp.new_load(version, files)
    b.execute(newworld)
    return b


def scenario_enemy(b):
    """O inimigo recomecou EXATAMENTE do estoque de cenario: razao inicial, sem carga em transito/pendente, sem perdas."""
    b.execute('''
local L, E = api.logi, api.CFG.ECHAIN
assert(L.eAudit())
for _, k in ipairs(E.kinds) do
    assert(L.en.front[k] == E.front0[k] and L.en.fac[k] == 0 and L.en.led.init[k] == E.front0[k], k)
    assert(L.en.led.made[k] == 0 and L.en.led.used[k] == 0 and L.en.led.lost[k] == 0, k)
    assert(L.eHave(k) == E.front0[k], "estoque total = cenario, sem duplicar nem inventar")
end
assert(L.en.pending == nil and #L.foes == 0 and L.en.seq == 0 and L.en.delivered == 0 and L.en.bmat == E.bmat0 and L.en.led.bmat0 == E.bmat0)
assert(L.en.ready == E.trucks and #L.en.rebuild == 0 and L.en.job == nil and L.en.salvage == 0)
''')


def t_valid(stack, v):
    a, ledger, canon, files = rich_save(stack, v)
    player, enemy = split(ledger)
    b = load_in(stack, v, files)
    assert b.eval("api.sv.load()") is True, b.eval("table.concat(H.logs, '\\n')")
    p2, e2 = split(b.eval("H.ledger()"))
    assert p2 == player and e2 == enemy, f"\nantes {ledger}\ndepois {b.eval('H.ledger()')}"
    assert not b.eval("H.saw('CADEIA INIMIGA REINICIADA')") and not b.eval("H.saw('descartada')")
    assert b.eval("api.sv.degraded") is None
    b.execute("assert(api.logi.eAudit()); assert(api.logi.en.pending.ammo == 1 and api.logi.en.pending.shirts == 2)")
    # restauracoes repetidas: substituem, nunca somam (sem duplicar a carga pendente nem o estoque)
    for _ in range(3):
        assert b.eval("api.sv.load()") is True
        assert split(b.eval("H.ledger()")) == (player, enemy)
    assert b.eval("#api.logi.foes") == 0


BAD = {
    "ready negativo": "d.elogi.ready = -1",
    "razao nao fecha (camisas criadas a mao)": "d.elogi.front.shirts = d.elogi.front.shirts + 50",
    "bmat negativo": "d.elogi.bmat = -5",
    "frota maior que a configurada": "d.elogi.ready = d.elogi.ready + 5",
    "job de receita desconhecida": "d.elogi.job = { kind = 'granada', left = 1, total = 2 }",
    "elogi nao e tabela": "d.elogi = 'lixo'",
    "elogi vazio": "d.elogi = {}",
    "versao futura (v = 2)": "d.elogi.v = 2",
    "versao desconhecida (v = 'x')": "d.elogi.v = 'x'",
}


def drop_checks(b, player, why_part):
    assert b.eval("api.sv.degraded") is None, "cadeia inimiga descartada NAO suspende o autosave (so ela recomeca)"
    assert b.eval("H.saw('CADEIA INIMIGA REINICIADA')"), "aviso explicito no PARTIDA CONTINUADA"
    assert b.eval("H.saw('descartada')"), "aviso proprio da IA (notify/evento)"
    if why_part:
        assert b.eval(f"H.saw({why_part!r})"), why_part
    p2, _ = split(b.eval("H.ledger()"))
    assert p2 == player, f"\njogador mudou:\nantes {player}\ndepois {p2}"      # nada do jogador mudou, nada creditado
    scenario_enemy(b)
    assert b.eval("api.combat.wave") == 3 and b.eval("api.economy.manpower") == 77
    assert b.eval("api.combat.convoysCut") == 0 and b.eval("api.combat.convoys") == 0, "sem bounty/placar de comboio herdado ou inventado"


def t_invalid(stack, v):
    a, ledger, canon, files = rich_save(stack, v)
    player, _ = split(ledger)
    for name, mut in BAD.items():
        tp.CANDIDATE = STACKS[stack]
        f = dict(files)
        c = tp.new_load(v, files)
        c.execute(MUTATE % (SAVE, mut))
        f = tp.disk(c)
        b = load_in(stack, v, f)
        b.execute("H.logs = {}")
        assert b.eval("api.sv.load()") is True, (name, b.eval("table.concat(H.logs, ' / ')"))
        if "futura" in name:
            drop_checks(b, player, "versão futura v2")
        else:
            drop_checks(b, player, None)
        # repetir o continuar: continua igual ao cenario (nao acumula nada)
        for _ in range(2):
            assert b.eval("api.sv.load()") is True
            scenario_enemy(b)
            assert split(b.eval("H.ledger()"))[0] == player
        # autosave seguinte grava uma cadeia valida (regenerada) e a proxima carga NAO avisa mais
        assert b.eval("api.sv.save()") is True
        b2 = load_in(stack, v, tp.disk(b))
        b2.execute("H.logs = {}")
        assert b2.eval("api.sv.load()") is True and not b2.eval("H.saw('CADEIA INIMIGA REINICIADA')"), name
        assert split(b2.eval("H.ledger()")) == split(b.eval("H.ledger()")), name
        assert b2.eval("api.logi.eAudit()")


def t_absent(stack, v):
    a, ledger, canon, files = rich_save(stack, v)
    player, _ = split(ledger)
    c = tp.new_load(v, files)
    c.execute(MUTATE % (SAVE, "d.elogi = nil"))
    b = load_in(stack, v, tp.disk(c))
    b.execute("H.logs = {}")
    assert b.eval("api.sv.load()") is True
    drop_checks(b, player, "o save não traz a cadeia inimiga")
    # save legado v1 de um build sem IA (sem enemy nem elogi): mesma politica
    c = tp.new_load(v, files)
    c.execute(MUTATE % (SAVE, "d.elogi = nil; d.v = 1; d.world = nil; d.infra = nil"))
    b = load_in(stack, v, tp.disk(c), newworld="H.newWorld({ active = true, trucks = 3 })")
    b.execute("H.logs = {}")
    assert b.eval("api.sv.load()") is True and b.eval("H.saw('CADEIA INIMIGA REINICIADA')")
    scenario_enemy(b)


def t_no_module(v):
    """Save feito com a IA lido por um mod SEM a IA: so o elogi e descartado; o jogador volta inteiro."""
    ia = IA_STACKS[0]
    a, ledger, canon, files = rich_save(ia, v)
    player_full, _ = split(ledger)
    tp.CANDIDATE = STACKS[NO_IA]
    b = tp.new_load(v, files)
    b.execute("H.newWorld()")
    b.execute("H.logs = {}")
    assert b.eval("api.logi.eSnapshot") is None and b.eval("api.logi.eValid") is None
    assert b.eval("api.sv.load()") is True, b.eval("table.concat(H.logs, ' / ')")
    assert b.eval("H.saw('CADEIA INIMIGA REINICIADA')") and b.eval("H.saw('não tem a cadeia inimiga logística')")
    assert b.eval("api.sv.degraded") is None
    led = b.eval("H.ledger()")
    # jogador: mesmos bmat/estoques/carteira/pontos/soldados (o ledger sem IA mostra o inimigo abstrato, ignorado aqui)
    assert split(led)[0] == split(ledger)[0], f"\nantes {ledger}\ndepois {led}"
    # inimigo abstrato do build sem IA = padrao de partida nova (cargo0), nada inventado
    assert b.eval("api.combat.cargo") == b.eval("api.CFG.ECONVOY.cargo0") and b.eval("api.combat.convoys") == 0


def t_save_own_invalid(stack, v):
    """Estado inimigo proprio invalido na hora de gravar: o resto e gravado SEM a secao (nunca um elogi invalido)."""
    a, ledger, canon, files = rich_save(stack, v)
    a.execute("api.logi.en.front.shirts = api.logi.en.front.shirts + 50")   # razao quebrado em memoria (bug hipotetico)
    a.execute("H.logs = {}")
    assert a.eval("api.sv.save()") is True and a.eval("H.saw('save sem a cadeia inimiga')")
    txt = tp.disk(a)[SAVE]
    assert "elogi" not in txt and '["logi"]' in txt and '["squad"]' in txt, "grava o resto, sem elogi"
    player, _ = split(ledger)
    b = load_in(stack, v, tp.disk(a))
    b.execute("H.logs = {}")
    assert b.eval("api.sv.load()") is True and b.eval("H.saw('CADEIA INIMIGA REINICIADA')")
    scenario_enemy(b)
    assert split(b.eval("H.ledger()"))[0] == player


def t_other_fields_still_refuse(stack, v):
    """Fora do elogi nada muda: campo desconhecido/invalido continua recusando o save inteiro e preservando tudo."""
    a, ledger, canon, files = rich_save(stack, v)
    for mut, expect in (("d.squad[1].role = 'tank'", "squad 1"), ("d.logi.bmat = -9", "logística inválida"), ("d.extra = 1", "campo desconhecido"),
                        ("d.infra.version = 2", "infra de versão futura")):
        c = tp.new_load(v, files)
        c.execute(MUTATE % (SAVE, mut))
        b = tp.new_load(v, tp.disk(c))
        b.execute("H.newWorld(); H.mySession = true")
        tp.refused(b, expect)


CASES = [("elogi valido: restaura igual, 3x sem duplicar", t_valid, IA_STACKS),
         ("elogi invalido/futuro/estranho: descarta so a secao, jogador intacto, sem duplicar", t_invalid, IA_STACKS),
         ("elogi ausente / save legado: mesmo aviso e cenario", t_absent, IA_STACKS),
         ("estado inimigo proprio invalido ao gravar: grava sem a secao", t_save_own_invalid, IA_STACKS),
         ("outros campos invalidos continuam recusando tudo", t_other_fields_still_refuse, IA_STACKS)]

if __name__ == "__main__":
    n = 0
    for version in ("lua54", "lua55"):
        for name, fn, stacks in CASES:
            for stack in stacks:
                fn(stack, version)
                n += 1
                print(f"PASS {stack} / {version}: {name}")
        t_no_module(version)
        n += 1
        print(f"PASS {NO_IA} lendo save da IA / {version}: modulo ausente descarta so o elogi, jogador intacto")
    print(f"PASS: test_elogi ({n} casos)")
