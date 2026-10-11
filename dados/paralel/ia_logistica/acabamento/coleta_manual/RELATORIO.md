# COLETA MANUAL — relatório (candidato v3)

Entrega do agente COLETA_MANUAL. Tudo nesta pasta; `main.lua`, docs compartilhados e pastas de outros agentes **não foram editados**.
Offline (lupa Lua 5.4 e 5.5): **nada aqui prova física Unreal, rota real, animação, entrada nem equilíbrio** — ver "O que exige o laboratório".

- Base lida (somente leitura): `dados/paralel/ensaio_integracao/candidato_v2/main.lua`, SHA256 `a93c1531588ea4534a7791dbb2e9578654ad0fa4a87373be1cbed569cbc3eda6` (inalterado antes/depois do build).
- Saída: `candidato_v3/main.lua` (CRLF), SHA256 **`9b89b1136509d9e4416a8f80dd3aa6b3ed2a491df61bcb7c0afec35cb34d63e6`** (6644 linhas, 337 990 bytes).
- Patch: `coleta_manual.patch` (CRLF, aplica em `candidato_v2/main.lua` com `patch -p1`/`git apply`; +359/-14) e `coleta_manual_lf.patch` (leitura).
- `main.lua` real do mod: SHA256 `33d6c7e5920a…` intacto (conferido no início e no fim da pilha, etapa 99).

## 1. Problema e decisão do usuário

Com o caminhão de recurso destruído, `bmat = 0` e `sucata = 0`, a fábrica não tem de onde tirar os 100 bmat da reconstrução e a cadeia trava
para sempre (`test_bmat_caminhao.py`, "limite conhecido"). Decisão: **coleta manual lenta** — soldados coletam sucata a pé; nada nasce do
nada e nenhum caminhão é grátis. Ampliada em três mensagens: a coleta manual é o **começo normal da partida** (estilo aldeões de RTS), o
trabalhador é um soldado sem fuzil nascido na base por 1 camisa, e o nascimento usa a interface comum de `bases_avancadas/ESPECIFICACAO.md` §4.3.

## 2. Origem dos números (leia isto antes de equilibrar)

| Valor | De onde vem |
|---|---|
| caminhão custa **100 bmat**; razão **2 sucata : 1 bmat**; carga de caminhão 100 | já no mod (`CFG.LOGI.truckCost`, `ratio`, `trip`) e em `dados/custos_do_jogo.txt` |
| implantação **1000** (refinaria 400 + fábrica 400 + 2 caminhões de suprimento 100) | soma dos custos reais acima; era 1100 com o caminhão de recurso |
| **`rate = 0,5` sucata/s, `cap = 40`, `workers = 3`, `bmat0 = 40`** | **PROPOSTAS de design minhas.** Não existe valor de coleta manual em `dados/` nem em `ESTUDO_MECANICAS.md` (o jogo não tem coleta a pé desse tipo nesta cópia) |
| raios/tempos (`fieldR 1000`, `refR 1500`, `stand 600`, `quiet 60`, `pause 60`, `leg 180`…) | escolhas de engenharia, ajustáveis em `CFG.COLETA` |
| `bmat0 = 40` | `CFG.LOGI.bmat0 = 240` compraria o caminhão no 1º tick e a coleta nunca aconteceria; 40 deixa a fábrica pobre de propósito |
| `startRifles = 10` | indicado pela interface de nascimento (§4.3) para a base principal; só vale na partida manual |

## 3. Design

Tudo em `CFG.COLETA`/`CFG.SPAWN` e na tabela `logi` (**nenhum local de topo novo**: 175 pelo contador do `check_globals`, o mesmo do v2; folga 22 até o limite de 200).

1. **Início sem caminhão de recurso.** `CFG.COLETA.manualStart = true`. `Alt+L` implanta refinaria + fábrica + **2** caminhões de suprimento (orçamento 1000, 4 atores).
   `logi.start` cria o de recurso já "morto" (`state="dead"`, sem ator), `bmat = 40`, base com `max(shirts0, workers)` camisas e 10 fuzis.
   `logi.trucksNeeded()` substitui o "supply+1" fixo em `scan`/`deployPlan`/`infraPlan`.
2. **A fábrica constrói o caminhão** pela reconstrução que já existia (`logi.truckStep`, 100 bmat, reserva `reserva_bmat`), agora com **prioridade
   automática** (`resFirst`): o de recurso reconstrói antes dos de suprimento e das caixas. Como não há ator, `logi.spawnTruck` o cria no campo (visual; o custo já foi debitado).
3. **Trabalhadores** = soldados reais, `role="worker"`, arma `CFG.WEAPONS.worker` (`grip=0`, alcance 0: nunca atira).
   `logi.colMaintain` mantém até `workers` (3) vivos **enquanto a coleta é necessária**, repondo os mortos, uma camisa cada.
4. **Interface de nascimento (§4.3), só para o trabalhador:**
   `site, why = logi.spawnSite(role, cursor, opts)` é **pura** (não muda estoque nem cria ator) e devolve
   `{dep, kind="base", name, at={X,Y,Z,exact=true}, need, explicit}` ou `nil, motivo` ("função sem receita", "ramo legado", "sem camisas em base",
   "camisas reservadas aos trabalhadores da coleta", "nenhum local de nascimento permitido");
   `ok, why = logi.spawnCommit(site, role)` roda **uma vez, depois do ator confirmado**, revalida o estoque e debita (a única atribuição de `.shirts` no código novo — verificado por análise estática no teste).
   Se o commit recusar depois do ator criado, o ator é desfeito (`anim.untrack`, destruir, soltar controlador). `recruit()` **não foi migrado**: só respeita a reserva de camisas dos trabalhadores.
   `CFG.SPAWN.roles.worker = {shirts=1, sites={"base"}}`; `workerDepot()` é o ponto isolado que as bases avançadas trocam.
5. **Coleta.** Estados `toField → gather → toRef`, rota pelo A* do mod (`routeTo`), movimento pelo `squadTick`. A sucata só vira estoque (`logi.salvage`) **na chegada à refinaria**; carga em mãos nunca é creditada.
   Razão conferida a cada quadro: `colhido = entregue + perdido + em mãos`. Ativa só com o caminhão de recurso ausente/morto **e** falta de bmat (`bmat + sucata/2 < 100`); some quando o caminhão volta.
6. **Segurança de cache (regra do `anim.untrack`).** Nunca guarda pawn/userdata entre quadros: guarda o registro do soldado e, antes de qualquer chamada, revalida pertencer ao esquadrão + `alive` + `not bActorIsBeingDestroyed`. Pawn inválido = **zero chamadas** (teste conta `pawn.touched`). `logi.reset` descarta a coleta sem tocar em pawn.
7. **Ordem do jogador tira o trabalhador da coleta** (marcha, `hold`, foco, área, recuo, evacuação, fila; a carga é descartada e registrada). Só volta após `quiet = 60 s` sem ordem. Para isso a ordem em fila (`Shift+direito`) passou a marcar `orderT`, como as demais (âncora 4c; muda só essa marca).
8. **Combate**: perigo (inimigo a < 35 m, tiro/supressão recentes, vida < 80%) impede recrutar e pausa a colheita; combate seguido > 60 s larga a coleta (carga perdida). Preso > 180 s num trecho: larga.
9. **Persistência**: schema v2 do save **não mudou**. A carga em mãos não é salva (descarte registrado em log "descartada (reinício)"); trabalhadores voltam como `role="worker"`; a coleta recomeça sozinha.
10. **Painel**: uma linha só quando há coleta, ex.: `coleta manual: 3 trabalhadores | 40/100 bmat para o caminhão | 25 sucata em mãos`.
11. **Caminho antigo preservado**: `manualStart=false` devolve implantação de 3 caminhões/1100 e `bmat0` antigo; a coleta vira só resgate do travamento (volta em 264,9 s).

## 4. Números medidos (offline, geometria do harness: campo a 80 m da refinaria, andar 400 cm/s)

| Medida | Resultado |
|---|---|
| **X** — 1º caminhão de recurso numa partida nova | **165,5 s** (colhido 120 = entregue 120, 3 viagens de 40) |
| 1ª entrega de caixas depois do caminhão | 63,0 s depois |
| **Y** — perder o caminhão com `bmat=0`, `sucata=0` | volta em **243,2 s** |
| Travamento antigo (v2, mesmo cenário, 900 s) | **nunca** volta; v3 com início legado volta em 264,9 s |
| Coleta vs. caminhão | 1,00 sucata/s (3 trabalhadores) vs 6,33 do caminhão: **6,3× mais lenta** |
| Mutação `resFirst=false` | inverte a ordem de reconstrução (teste não é vacuoso) |

Sensibilidade (`SENSIBILIDADE.txt`, `sensibilidade.py`; segundos até o 1º caminhão; 3 trabalhadores, cap 40, rate 0,5 salvo a coluna variada):

| | 80 m | 260 m | 470 m |
|---|---|---|---|
| 1 trabalhador | 373 | 637 | 951 |
| 2 trabalhadores | 259 | 435 | 645 |
| 3 trabalhadores | 165 | 254 | 359 |
| cap 20 | 187 | 363 | 573 |
| cap 80 | 245 | 334 | 439 |
| rate 0,25 | 245 | 334 | 439 |
| rate 1,0 | 125 | 214 | 319 |

Leitura: o tempo cresce principalmente com a **distância** campo–refinaria; 5 trabalhadores não ajudam o 1º caminhão (bastam 3 viagens de 40). `cap` 80 não ajuda no curto: a 1ª carga demora 160 s para encher (a 0,5/s) e o caminhão só precisa de 120 no total.
Em HomeRegionW (campo ~470 m da refinaria) o 1º caminhão sai em ~6 min com 3 trabalhadores, não ~3 min.

Um erro real foi achado pela tabela e corrigido: o acúmulo de `rate*dt` em ponto flutuante parava a carga em 39,999999, a entrega ficava em 119,99999 e faltava uma viagem inteira
para o limiar `bmat >= 100`. A carga cheia agora é fixada exatamente em `cap` (o razão `colhido` soma a diferença).

## 5. O que foi testado (tudo PASS; saída completa em `SAIDA_TESTES.txt`)

Comando geral: `cd /d/GitHub/foxhole-rts && bash dados/paralel/ia_logistica/acabamento/coleta_manual/rodar_tudo.sh` (reconstrói o candidato e roda tudo; `rc_final=0`).
Cada comando individual: `cd /d/GitHub/foxhole-rts && PYTHONPATH=D:/tools/pylibs PYTHONDONTWRITEBYTECODE=1 python dados/paralel/ia_logistica/acabamento/coleta_manual/<arquivo>.py`.

| Arquivo | Casos | Cobre |
|---|---|---|
| `test_partida_manual.py` | 14 (7 × 2 Lua) | partida nova sem caminhão → X; manual → caminhão → caixas; perder o caminhão → Y; nada de bmat/sucata sem coleta (falha de spawn, sem camisas, trabalhadores congelados, esquadrão cheio, comandado); prioridade `resFirst` (+ mutação); `manualStart=false`; implantação 1000/4 atores (v2: 1100/5) |
| `test_coleta_nucleo.py` | 18 | cadeia saudável **nunca** ativa a coleta (4 cenários); coletor morre com carga; ordem do jogador remove da coleta; combate; revalidação de pawn inválido; mais lenta que o caminhão; painel; reserva de camisas; **fuzz** 20+5 sementes × 600 s com razão e entrega conferidos a cada quadro |
| `test_travamento.py` | 4 | o deadlock antigo: v2 trava, v3 resolve; partida manual sob consumo contínuo |
| `test_persistencia_coleta.py` | 10 | salvar/continuar durante a coleta (bmat/sucata idênticos, nada creditado); 4 ciclos idênticos; mesma sessão descarta e registra; save com implantação v3; save do v2 abre no v3; v2 recusa save de v3 |
| `test_spawn_interface.py` | 9 | `spawnSite` pura; recusas com motivo; `spawnCommit` debita só após spawn confirmado e revalida; commit recusado desfaz o ator; estoque inicial (10 fuzis, camisas ≥ 3) e legado intacto; só `spawnCommit` atribui `.shirts` |
| `test_orders_v3.py` | suite do mod | `tools/test_orders.py` contra o v3 (cópia em memória), com adaptações abaixo |
| `test_pilha_v3.py` | 22 etapas | cópia adaptada de `ensaio_integracao/test_pilha.py` apontando para o v3: build reprodutível, sintaxe 5.4/5.5, limite de 200 locais (175), `check_globals` limpo, test_orders, costs, economia, IA, elogi, bmat_caminhao, painel, persistência v2, estradas, patches em sequência, ordens alternativas, intacto no fim. **22 PASS, 0 FAIL** |

Também: `tools/check_globals.py` contra o candidato: sem saída, rc 0.

### Expectativas alteradas (cada uma documentada no código)

`test_orders_v3.py` (`ADAPTACOES`, impressas a cada execução): (1) `start()` deixa o caminhão de recurso por construir — o bloco do fluxo da fábrica o torna vivo; (2) plano de implantação 1100/3 vagas → 1000/2;
(3) carteira 1099 → 999 e 1100 → 1000; (4) rollback preserva 1000; (5) implantação cria 4 atores (não 5) e gasta 1000, duas vezes; (6) estacionamento inicial tolera o caminhão de recurso sem ator.

`test_pilha_v3.py` roda a suíte de persistência da pilha em **duas** variantes: a de números novos (`V3_PERSIST_ADAPT`, condicional à pilha candidata via `_v3()`, porque a mesma suíte também roda a pilha **sem** coleta, que continua em 1100/5):
atores 5→4, carteira `0/1100/5`→`0/1000/4`, caminhões vivos 3→2, saldo 300→200. E `V3_ELOGI_ADAPT`: em `t_no_module` o mundo de carga ganha 1 caminhão nativo, porque um mod **sem** a coleta exige 3 caminhões e o save v3 pagou 2.
As etapas **06b-L** e **08-L** rodam as mesmas suítes **sem nenhuma alteração** com `manualStart=false`: o caminho antigo está intacto. `diffs/test_pilha_v3.diff` mostra tudo o que mudou em relação ao `test_pilha.py` original.

## 6. O que exige o laboratório (nada disso foi visto)

- **Movimento real dos trabalhadores**: colisão, travar em obstáculo/neve, o A* real do campo à refinaria, chegada dentro de `fieldR`/`refR` (o harness usa mundo plano).
- Se o campo de sucata e a refinaria são **de fato** alcançáveis a pé no mapa (HomeRegionW) e a que distância; ajustar `fieldR`/`refR`/`stand`.
- **Animação sem arma** (`grip=0`): o soldado nasce sem fuzil sem quebrar `ABP_Male_C` (sem T-pose, sem crash do hook de animação). `spawnSoldier` com `role="worker"` e a nova entrada de `CFG.WEAPONS`.
- **Visual do caminhão de recurso spawnado** (`logi.spawnTruck`, no campo): ator válido, posição sobre o chão, não em destruição, não preso em telhado.
- **Custo por quadro**: `colStep` roda todo `logi.tick`; é O(coletores) mais, a cada 0,5 s por coletor, uma varredura dos inimigos. Medir na partida real.
- Fluxo humano: selecionar/dar ordem a um trabalhador, vê-lo sair da coleta e voltar 60 s depois; painel; mensagens; salvar/continuar com trabalhadores em campo.
- Veículos inimigos/terreno: se os trabalhadores sobrevivem a uma onda no caminho do campo.

## 7. Riscos

- **Save de v3 não abre em v2** quando há trabalhadores no esquadrão (papel `worker` desconhecido) nem quando a implantação paga 2 caminhões (v2 exige 3). v2 → v3 abre.
- Trabalhadores ocupam vagas de `SQUAD_MAX` e são alvos como qualquer soldado; esquadrão cheio impede o nascimento (aviso a cada 30 s).
- Coleta longa: trechos > `leg` (180 s) são abortados e a carga se perde; em campos muito distantes aumente `leg` ou `cap`.
- Mudança de comportamento colateral mínima em código existente: a ordem em fila passou a marcar `orderT`.
- `spawnSoldier` real nunca foi chamado com `role="worker"` (mock no harness).
- A partida manual é mais lenta de propósito; se o equilíbrio ficar ruim, `manualStart=false` volta o comportamento antigo sem outro código.

## 8. O que o jogador vai notar (para README / TESTE_MANUAL)

- Partida nova: a implantação (Alt+L) custa **1000**, não 1100, e traz refinaria, fábrica e **2** caminhões de suprimento — **sem caminhão de recurso**. O painel mostra o caminhão de recurso como destruído/por construir.
- A base começa com **40 bmat** (antes 240), 10 fuzis e camisas.
- ~5 s depois surgem **3 soldados sem arma** perto da base (cada um gasta 1 camisa) que vão ao campo de sucata, coletam e levam à refinaria. Painel: `coleta manual: N trabalhadores | x/100 bmat para o caminhão | y sucata em mãos`.
- A fábrica passa a **guardar 100 bmat** e constrói o **caminhão de recurso** antes dos de suprimento e das caixas; ele aparece no campo, a coleta para sozinha e os trabalhadores ficam livres. Mensagens: "COLETA MANUAL: …" e "caminhão de recurso pronto: coleta manual encerrada".
- Perder o caminhão de recurso depois, sem bmat/sucata, **reativa** a coleta (antes, travava para sempre).
- Qualquer ordem dada a um trabalhador o tira da coleta (a carga em mãos se perde); sem ordem por 60 s ele volta sozinho. Trabalhadores mortos são repostos enquanto houver camisas.
- Recrutar soldados de combate (Ctrl+1…4) não gasta as camisas reservadas aos trabalhadores enquanto não há caminhão de recurso (mensagem própria).
- Salvar durante a coleta: a sucata em mãos não é salva; ao continuar, a coleta recomeça (mensagem no log).
- Sem tecla nova.

## 9. Decisões de equilíbrio em aberto (são do usuário)

1. `bmat0 = 40`: 40 + 60 (de 120 sucata) = 100. Mais bmat inicial encurta o começo; 240 elimina a coleta.
2. Orçamento da implantação `1000` (2 caminhões de suprimento). Pode-se pagar o de recurso à parte ou cortar 1 de suprimento.
3. `rate = 0,5`, `cap = 40`, `workers = 3`: ver tabela; 3 já satura as 3 viagens do 1º caminhão, 5 só ajuda reposições.
4. Trabalhadores usam vagas de `SQUAD_MAX` (alternativa: lista própria, mais código e persistência).
5. Trabalhadores só são mantidos/repostos enquanto a coleta é necessária (depois ficam como soldados ociosos sem arma, não somem).
6. **Distância campo–refinaria**: ~470 m em HomeRegionW dá ~6 min até o 1º caminhão com 3 trabalhadores (2 min 45 s no harness a 80 m). Talvez sustentar mais coletores, `cap` maior ou campo mais próximo no começo.
7. `startRifles = 10` na base principal (indicado pela interface de nascimento); só vale na partida manual.
8. Camisas: se a base ficar sem camisas e os trabalhadores morrerem, ninguém nasce e a coleta para (aviso no log/notify). A reserva só protege `recruit()`; novas camisas vêm da fábrica e dos caminhões de suprimento. Decidir se há piso mínimo de camisas.

## 10. Arquivos

`build_coleta.py` (gera tudo; âncoras únicas, falha se alguma não for), `coleta_cfg.lua`, `coleta_funcs.lua`, `coleta_manual.patch`, `coleta_manual_lf.patch`, `candidato_v3/{main.lua,SHA256.txt}`,
`harness_coleta.py`, `test_partida_manual.py`, `test_coleta_nucleo.py`, `test_travamento.py`, `test_persistencia_coleta.py`, `test_spawn_interface.py`, `test_orders_v3.py`, `test_pilha_v3.py`, `diffs/test_pilha_v3.diff`,
`sensibilidade.py`, `SENSIBILIDADE.txt`, `rodar_tudo.sh`, `SAIDA_TESTES.txt`, `saida_testes_v3.txt` (log detalhado da pilha), `ROTEIRO_LABORATORIO.md`.
