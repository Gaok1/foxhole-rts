# COMO_INTEGRAR — pilha v4 (para a task INTEGRACAO)

Preparado offline pelo agente PACOTE_V4 (2026-10-10). Nada foi aplicado: `mod/FoxholeRTS/Scripts/main.lua` continua com
SHA256 `33d6c7e5920a3b5e00b7f3bafbc7b8a86c984db810217241a567afe0901ee679` (conferido no começo e no fim do trabalho).
Tudo o que está aqui foi conferido contra o texto do candidato (Grep/Read) e, onde diz "reproduzido", executado em cópia
no scratchpad do agente. O que não foi visto no jogo está marcado como tal.

## 1. O que é a v4.1 (o candidato a integrar) e a v4 (a base)

**Candidato a integrar: v4.1** = v4 + 4 trocas (decisão do orquestrador: trabalhadores da coleta **não** contam no tamanho das ondas nem no centro do esquadrão). Um único arquivo:
`dados/paralel/pacote_v4/v4_1/candidato/main.lua` (CRLF, 7323 linhas, SHA256 `62245d23af36160f589707fe422b6fb167abaa58482ef7f58a49cd39021b598f`),
gerado por `v4_1/build_v4_1.py` a partir do `candidato_v4` e descrito por `v4_1/v4_1.patch` (`patch --binary` sobre o `candidato_v4`). O que muda, só em `waveTick`
e `logi.noReinforce` (nenhum local de topo novo, `rts.combatCount()` já existia): (1) o tamanho da onda usa `rts.combatCount()` em vez de `#squad`; (2) o aviso
"próxima onda em … (esquadrão N …)" mostra o esquadrão de combate; (3) a derrota por falta de tropa no Assalto/legado também usa `rts.combatCount()` (sem isso, 3 trabalhadores vivos
impediam a derrota no Assalto; o ramo logístico já usava). Teste de contraste `v4_1/test_v4_1.py`: no v4 as 5 expectativas novas falham (6 soldados + 3 trabalhadores dão onda 7, contra 6 sem eles),
no v4.1 passam. (4) `squadCenter()` (que decide onde ficam os pontos iniciais, de onde vêm ondas e reforço, arame inimigo e orientação das fortificações) passa a usar só os combatentes vivos; sem combatente vivo cai no centro de todos os vivos, sem ninguém `nil` (3 linhas viram 14, nenhum local de topo novo; folga de locais continua 22).

**Base: v4** — `dados/paralel/bases_avancadas/etapa2/candidato_v4/main.lua` (CRLF, 7320 linhas, SHA256 `025e3b80f76c5f13c4f2ed5ea83e04acfa7de79873c4308642badc5d072aaab0`); o resto desta seção vale para os dois.
Ordem da pilha: **ECONOMIA > IA_LOGISTICA v2 > reserva_bmat > INTERFACE v2 (painel rebaseado) > PERSISTENCIA v2 >
COLETA_MANUAL > BASES_AVANCADAS**. Estabilidade (o código atual do main) e ESTRADAS: ESTRADAS **não** está na pilha.
O diff entre o main real e o candidato v4 (105 hunks; a v4.1 soma 4 trocas pequenas) não toca o contorno/seleção, o hook de animação nem a câmera: os
hunks caem em `spawnSquad`, `queueMove`, `recruit`, `medicTick`, `pointsTick`, `dropCrate`, `ai.tick`, `waveTick`,
`rts.newAssault`, `sv.load`, `plain`/teclas e no bloco da logística (conferido com `diff` por função).
Locais de topo: 178 ativos pelo compilador (folga 22, igual ao main real), 175 pela contagem do `check_globals.py`
(`rc=0`). Nenhum local de topo novo; tudo entrou em `CFG`, `S`, `logi`, `sv`, `rts`.

## 2. Pré-condição: gate de estabilidade (decisão do coordenador, não minha)

O `MODLOG.md` ("Como retomar") e a task ESTABILIDADE dizem para não ampliar features antes de isolar a queda do
contorno completo. Estado do gate no repositório e fora dele:

| Carga | Estado | Onde está o registro |
|---|---|---|
| A1 (6 sem seleção, 0 cópias, 180 s) | passou, 184 s, stratTick 0,46–0,50 ms | `MODLOG.md` topo (2026-10-09) |
| B1 (6 selecionados, 168 cópias, 180 s) | sobreviveu 184,3 s, stratTick 11,7–12,4 ms/quadro | **só** `D:/tools/foxhole-lab/crash-control-B1.txt`; o MODLOG não registra |
| B2 (nova carga, 6 selecionados) | pendente | `estabilidade/controle_crash.md` |
| A2 (nova carga, 6 sem seleção) | pendente | idem |

Uma carga curta que sobrevive não certifica (diz o próprio MODLOG). Recomendação mínima: registrar o B1 no MODLOG e
rodar B2 e A2 (passos G0.2 e G0.3 do `ROTEIRO_LOTE.md`) **antes de gravar a v4 no main real**, para o gate usar a
mesma fonte (`33d6c7e5…`) das cargas A1/B1 — `restart.sh` copia o `main.lua` do repositório, então a ordem importa.
Se o coordenador preferir integrar primeiro, o gate completo (A1/B1/B2/A2) tem de ser refeito com o hash v4.1 (`62245d23…`); isso é
legítimo porque a v4 não mexe no código do contorno (ver §1), mas o hash deixa de ser o mesmo e isso fica no registro.
A integração **offline** (copiar, rodar a bateria) não depende do gate; o que depende é publicar no laboratório e
chamar a v4.1 de pronta.

## 3. Como aplicar

**Opção A (recomendada): copiar o arquivo.**
```
cp dados/paralel/pacote_v4/v4_1/candidato/main.lua mod/FoxholeRTS/Scripts/main.lua
sha256sum mod/FoxholeRTS/Scripts/main.lua     # tem de dar 62245d23af36160f589707fe422b6fb167abaa58482ef7f58a49cd39021b598f (v4.1)
```
PowerShell: `(Get-FileHash mod\FoxholeRTS\Scripts\main.lua -Algorithm SHA256).Hash` (maiúsculas). O arquivo é CRLF
consistente (o `test_pilha_v4.py` etapa 00 confere); não passe por editor que normalize fim de linha.

**Opção B: cadeia de patches** (reproduzida por mim em cópia, com `patch --binary`; os quatro SHAs batem). Só se quiser
auditar etapa a etapa; é equivalente à A:
```
patch -p1 --binary < dados/paralel/ensaio_integracao/pilha_v2.diff                       # -> a93c1531…eda6 (candidato_v2)
patch --binary mod/FoxholeRTS/Scripts/main.lua < dados/paralel/ia_logistica/acabamento/coleta_manual/coleta_manual.patch   # -> 9b89b113…63e6 (candidato_v3)
patch --binary mod/FoxholeRTS/Scripts/main.lua < dados/paralel/bases_avancadas/etapa2/bases.patch                         # -> 025e3b80…aab0 (v4)
patch --binary mod/FoxholeRTS/Scripts/main.lua < dados/paralel/pacote_v4/v4_1/v4_1.patch                                  # -> 62245d23…598f (v4.1; reproduzido)
```
Atenção: `pilha_v2.diff` usa o caminho completo (`-p1` na raiz do repositório); `coleta_manual.patch` e `bases.patch` usam
`a/main.lua`, por isso se aplicam ao arquivo explícito. Use os `.patch`/`.diff` CRLF (os `*_lf.patch`/`pilha_v2_lf.diff` são LF
e não casam com o main CRLF). Não aplique BASES antes da COLETA nem a coleta antes da pilha v2.

Antes de sobrescrever, guarde uma cópia do main real (este diretório não é repositório git; não há histórico para desfazer).

## 4. Verificação imediata depois de aplicar (todas offline)

```
export PYTHONPATH=D:/tools/pylibs PYTHONDONTWRITEBYTECODE=1
python tools/check_globals.py                      # sem saída, rc 0 (avisa locais internos com nome de tabela de topo)
python tools/test_costs.py && python tools/test_inventory_probe.py
python dados/paralel/pacote_v4/aplicar_test_orders.py --write    # ver §5, depois:
python tools/test_orders.py
python dados/paralel/pacote_v4/bateria_pos_integracao.py         # ver §6 (inclui as suítes das outras pastas)
```
`restart.sh` repete sintaxe e `check_globals`. Contagem de locais pelo compilador: o `bateria_pos_integracao.py` mede
a folga (esperado 22 em Lua 5.4 e 5.5).

## 5. `tools/test_orders.py`: o que trocar

O `tools/test_orders.py` atual **falha** com a v4 (reproduzido: rodei-o sem troca contra o candidato; a primeira asserção que
cai é a do fluxo da fábrica, porque a partida nova começa com o caminhão de recurso "morto" e a fábrica guarda 100 bmat em
vez de iniciar a munição de 80). Depois dela caem o bloco do comboio e os números da implantação. A troca está pronta em
`aplicar_test_orders.py` (reproduzida: a versão gerada passa contra o candidato, incluindo a linha
`teclas: SHIFT+J registrada, fora de GAME_KEYS; J livre no jogo`; dry-run por padrão:
imprime o diff; `--write` grava `tools/test_orders.py`; `--out ARQ` grava em outro lugar; é idempotente e para se alguma
âncora deixar de ser única). Ele reaproveita `ADAPTACOES` de `bases_avancadas/etapa2/test_orders_v4.py` (a cópia que já
passa no candidato) e o bloco novo de `ia_logistica/acabamento/test_orders_bloco_comboio_v2.lua`. As trocas:

1. **Bloco "enemy convoy"** (entre `-- enemy convoy: missing cargo shrinks the wave…` e
   `assert(cv2.state == "dead" and api.combat.convoysCut == cut0 + 1)`): substituído pelo bloco da IA v2 (a cadeia inimiga
   não tem mais `combat.cargo`/`perWave` como estoque; é `logi.e*` com razão fechado).
2. **Implantação sem caminhão de recurso** (coleta manual): `plan.cost==1100 and #plan.parking==3` →
   `1000` e `#plan.parking==2`; carteira `1099`→`999`, `1100`→`1000` (duas ocorrências de carteira cheia e o rollback);
   `spawned==5 … spent==1100` → `spawned==4 … spent==1000` (duas vezes, inclusive a idempotência); o estacionamento
   inicial tolera o caminhão de recurso sem ator; no bloco do fluxo da fábrica o caminhão de recurso é tornado vivo
   explicitamente (a partida nova começa com ele "morto", reserva de 100 bmat).
3. **Teclas**: nova asserção de `SHIFT+J` (registrada, fora de `GAME_KEYS`, `J` continua registrada e fora de
   `GAME_KEYS`, nenhuma outra `*+J`). `J` agora vem embrulhada em `plain()` (só dispara sem modificador) e Shift+J chama
   `logi.fwdKey(cursorPoint())`. O teste de teclas só confere o registro; que o `plain()` realmente impede o `J` de
   disparar com Shift apertado depende de `S.MOD_KEYS` com as teclas Shift reais do UE4SS: é item de laboratório (L-J2).

São 9 trocas ao todo (8 da coleta + 1 de teclas) mais o bloco do comboio. Se qualquer âncora não for única o script
aborta sem gravar.

## 6. Bateria permanente depois da integração

Depois que o main real for a v4, os `test_*.py` das pastas que fazem `build(main)` (aplicam o próprio patch sobre o main)
deixam de poder rodar (as âncoras já foram consumidas) e os que chamam `harness_*` com o arquivo em disco passam a testar
o candidato antigo, não o main. Duas técnicas já provadas no repositório resolvem isso sem editar os testes originais:

- **`BASES_V4_FILE`**: variável de ambiente que `bases_avancadas/etapa2/harness_bases.py` lê para trocar o arquivo-alvo.
  Aponte para o main real e rodam, sem edição, as suítes de BASES e da COLETA.
- **`__CANDIDATE`**: cópia em memória do teste com a linha que obtém o candidato trocada (`exec` com o texto do main
  real). É o que `test_pilha_v4.py` faz nos passos 05, 06, 06b, 06c, 07, 08 e 09.

`dados/paralel/pacote_v4/bateria_pos_integracao.py` junta as duas (lê o main real; não escreve nada em disco, só stdout;
`--main ARQ` aponta outro arquivo para ensaio; roda em ~30 s). Há um detalhe que não dá para contornar de outro jeito:
`test_elogi`, `test_bmat_caminhao` e `test_persistencia_v2` montam pilhas **alternativas** ("sem IA", "sem coleta") aplicando
os `build_*.py` ao main **anterior** e leem `mod/FoxholeRTS/Scripts/main.lua` direto no texto do teste. Depois da integração
esse arquivo já é a v4 e as âncoras não existem mais (reproduzido: 5 falhas `âncora não única`). Por isso esta pasta guarda a
cópia do main anterior (`base_pre_integracao/main_real_33d6c7e5.lua`, SHA256 conferido pelo script) e o script redireciona,
só em memória, as leituras do `Path.read_text` desse caminho para ela. **Não apague** `base_pre_integracao/`; guarde também
a sua própria cópia, porque este diretório não é repositório git. Cobertura:

| Suíte | Origem | Como entra na bateria | Resultado que reproduzi (candidato) |
|---|---|---|---|
| `tools/test_orders.py` (editado, §5) | `tools/` + `test_orders_v4.py` + bloco comboio v2 | direto | PASS (cópia v4) |
| `test_construcao`, `test_recrutamento`, `test_perda`, `test_trabalhadores`, `test_persistencia_bases`, `test_painel_teclas` | `bases_avancadas/etapa2/` | `BASES_V4_FILE=<main real>` | PASS |
| `test_coleta_sobre_v4` (5 suítes da coleta) | `etapa2/` + `coleta_manual/test_*.py` | `BASES_V4_FILE` | PASS 5/5 |
| economia `test_integracao`, IA `test_ia_logistica_v2` (25×600 passos), `test_elogi` (+legado `manualStart=false`), `test_bmat_caminhao`, `test_persistencia_v2` (+legado), `persistencia/test_persistencia` | `economia/`, `acabamento/`, `persistencia/` | `__CANDIDATE` (passos 05–08 do `test_pilha_v4`) | PASS no `test_pilha_v4` 22/22 |
| painel: `interface/test_interface.py` (mock próprio), `logi.hudLine` do candidato, painel integrado e v2 | `interface/` + `test_pilha_v4` 07a–07d | `__CANDIDATE` | PASS |
| contrato ESTRADAS (driver `true` só na chegada, `routeStatus`) | `test_pilha_v4` 09 | `__CANDIDATE` | PASS |
| **v4.1** `v4_1/test_v4_1.py` (contraste v4 × v4.1: onda com 3 trabalhadores = onda sem eles, aviso, centro do esquadrão, derrota no Assalto) | `pacote_v4/v4_1/` | `--so-v41 <main>` dentro da bateria; **falha no v4 puro, de propósito** | PASS 7 casos × Lua 5.4/5.5 no v4.1 |
| `sensibilidade_bases.py` (21 mutantes, cada um tem de ser pego) | `etapa2/` | opcional (lento); lê o arquivo-alvo e injeta mutantes | 21/21 (relatório) |

O que **sai** da bateria porque só faz sentido com o main anterior: passos 00, 03a, 10, 11, 12 e 99 do `test_pilha_v4`
(reprodução do build, controle no main real, ordem dos patches, comutação, resíduos, "main intacto"). Guarde o
`test_pilha_v4.py` como prova da integração: rode-o **uma vez antes** de sobrescrever o main (22/22) e arquive a saída (prova a pilha até a v4; a v4.1 é a v4 + `v4_1.patch`, provada por `v4_1/test_v4_1.py` e pela bateria).

O que medi (num **ensaio geral**: cópia do repositório no scratchpad com o candidato no lugar do main, `aplicar_test_orders.py
--write` aplicado nela e a bateria rodada; nada nas pastas dos agentes): 27 itens, 27 PASS, ~31 s com a v4; com a **v4.1** no lugar do main, 28 itens (o novo é `v4_1/test_v4_1.py`), 28 PASS, e com `--sensibilidade --rapido` 26/26 (21 mutantes pegos). Com a v4 pura, a mesma bateria falha só nesse item novo (registro em
`ENSAIO_BATERIA.txt` nesta pasta). Controle negativo: com `cost = 301` na base avançada e `free = 4` na cadeia inimiga, a
bateria reprovou 5 itens (construcao, recrutamento, perda, painel_teclas e a calibração v2 do painel), ou seja, ela enxerga
o arquivo apontado e não passa por inércia.

## 7. O que deixa de valer depois da integração

Os geradores com âncora única no main anterior: `economia/build_patch.py`, `ia_logistica/build_patch.py` e
`acabamento/build_patch_v2.py`, `acabamento/patch_reserva_bmat.py`, `acabamento/build_persistencia_v2.py`,
`persistencia/build_patch.py`, `ensaio_integracao/build_pilha.py`, `coleta_manual/build_coleta.py`,
`bases_avancadas/etapa2/build_bases.py`. Rodá-los contra o main novo falha fechado (âncora ausente) ou, pior,
regrava candidatos em disco. **Não rode** `build_*.py`, `rodar_tudo.sh` (regrava `SAIDA_TESTES.txt` e `candidato_v4/`) nem
`coleta_manual/test_pilha_v3.py` (regrava `saida_testes_v3.txt`; já houve um incidente) depois de integrar. Os `.patch`/`.diff`
e os `candidato*/main.lua` ficam como registro; o `SHA256.txt` de cada um é a prova.
Os testes `test_regressao*.py`, `test_auditoria_base.py`, `test_existing.py` e `ensaio_integracao/test_pilha.py` leem o main real
e reaplicam patches: também deixam de valer como estão (cobertos pela bateria do §6).

## 8. Achados pendentes

1. `estradas/native_adapter.lua` (linhas 38–39) e `estradas/RETURN_PATCH.lua` (comentário das linhas 12–13) creditam
   `factory.ammo`/`factory.shirts` na devolução de carga: só dois produtos. Na v4 a fábrica guarda quatro
   (`logi.fac.ammo/shirts/rifle/medical`); o alvo correto é `logi.fac` via `logi.moveCargo`. Integrar o ESTRADAS como está
   **perde fuzis e bandagens** devolvidos.
2. Transporte continua **em reta**, sem colisão (driver `logi.drive` do main; ESTRADAS não está na pilha). A cadeia inimiga
   usa o mesmo contrato (`tr.routeStatus`, `CFG.ECHAIN.stuck = 20 s`).
3. **Plano B visual da base avançada não existe**: `CFG.FWD.visual = "mesh"` está declarado, `fwdCheck` responde
   "visual 'mesh' (plano B) não implementado". Ruína nativa desligada (`CFG.FWD.ruin = false`) até o ensaio B1.
   `BPForwardBase1_C` nunca nasceu; o caminho do asset foi inferido (`CFG.FWD.asset`).
4. O `PARALEL_AGENTS` (task PERSISTENCIA) ainda diz "elogi inválido recusa o save inteiro"; a v2 faz o contrário
   (descarta só a seção e a cadeia inimiga recomeça do estoque de cenário). O código é o que vale.
5. O relatório da coleta (`coleta_manual/RELATORIO.md` §7) diz que trabalhadores ocupam vagas de `SQUAD_MAX`: na v4 não
   ocupam (limite deles é `CFG.COLETA.workers`). Na v4 o tamanho da onda ainda contava `#squad` inteiro (~+1 inimigo por 3
   trabalhadores); **resolvido na v4.1** por decisão do orquestrador (só soldados de combate contam: onda, aviso e derrota no
   Assalto). Também resolvido na v4.1: `squadCenter()` só com combatentes (trabalhadores no campo de sucata não puxam ondas, reforço, arame nem pontos iniciais).
6. `economia/__pycache__` e `estradas/__pycache__` aparecem nas pastas (imports sem `dont_write_bytecode`): ruído, não conteúdo.
7. O robô `D:/tools/foxhole-lab/t_bot.lua` está defasado para o fluxo da coleta (assume caminhão de recurso vivo e recruta
   por mão de obra). Antes de usar `botloop.sh` nas células B0–B3 do roteiro, ver `ROTEIRO_LOTE.md` passo R0.
8. `README`/`TESTE_MANUAL`/`HELP_TEXT`: ver os rascunhos desta pasta. O `HELP_TEXT` e a mensagem final de carga **já** estão no
   candidato (linha de Ctrl+1/2/3/4/0, linha de construção com `Shift+J: base avançada (300 bmat, 2 toques)`, banner).
9. Banner e ajuda de teclas citam `Shift+J`; `GAME_KEYS` não ganhou nada (55 teclas).

## 9. Compatibilidade de saves

- **v4 abre saves de v3 e v2**: seções ausentes são aceitas (`fwd` opcional; `elogi` ausente → "o save não traz a cadeia
  inimiga" e a cadeia recomeça do estoque de cenário, com o aviso `CADEIA INIMIGA REINICIADA (…)`).
- **O inverso não vale**: o v3 recusa um save com `fwd` ("campo desconhecido: fwd"); v3 e v2 recusam save com trabalhadores
  (`role="worker"` desconhecido) e com implantação de 2 caminhões (exigem 3). Um save v4 **sem** bases e **sem** trabalhadores
  é lido pelo v3.
- Schema: `CFG.PERSIST.version = 2`, `infraVersion = 1`, `enemyVersion = 1`, `fwdVersion = 1`.
- `elogi` inválido, de versão futura ou sem logística descarta **só a seção** (a cadeia inimiga recomeça); qualquer outro
  campo inválido recusa tudo e preserva a partida atual e o arquivo ("Continuar recusado (partida atual e save preservados)").
- Escrita: `.tmp` conferido → anterior vira `.bak` (ou `.corrupt` se inválido) → `.tmp` vira o save. Continuação incompleta
  suspende o autosave ("INCOMPLETA … autosave suspenso"). Pedido pendente de base avançada **não** é salvo.
- Não existe migração da carteira de implantação entre `1100` e `1000`: o save guarda o que foi pago (`spent`, `built`).

## 10. Fechamento sugerido (tasks)

Ao integrar: marcar em `PARALEL_AGENTS` ECONOMIA/IA_LOGISTICA/INTERFACE/PERSISTENCIA/BASES_AVANCADAS os itens de código como
feitos e deixar abertos os itens "ao vivo" até o laboratório; o `ROTEIRO_LOTE.md` indica a task que cada passo fecha.
Publicar os rascunhos (`README_RASCUNHO.md`, `TESTE_MANUAL_RASCUNHO.md`, `MODLOG_RASCUNHO.md`) **depois** do laboratório,
com as medições preenchidas; o MODLOG leva uma entrada nova no topo. Gotchas: `GOTCHAS_CONSOLIDADOS.md` para a nota
`knowledge/games/foxhole/…` e `um kb check` local (sem PR sem OK do usuário).
