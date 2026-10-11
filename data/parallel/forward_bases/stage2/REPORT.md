# BASES_AVANÇADAS — etapa 2 (implementação offline) — relatório

Entrega: `candidate_v4/main.lua` = `candidate_v3` (coleta manual, SHA256 `9b89b113…63e6`, **somente leitura**) + um patch por âncoras
únicas (`build_bases.py`). Nada foi aplicado ao `mod/FoxholeRTS/Scripts/main.lua` nem aos docs compartilhados; não houve laboratório,
jogo, nem entrada de teclado/mouse. Tudo abaixo é **offline** (lupa, Lua 5.4 = UE4SS e 5.5): prova a lógica e os contratos, não a física,
a classe real `BPForwardBase1_C`, a rota nem o desempenho.

SHA256 do `candidate_v4/main.lua` (CRLF): ver `candidate_v4/SHA256.txt` (a última linha é a do v4; o v3 aparece antes/depois e é igual).

## 1. O que muda para o jogador (para README / TESTE_MANUAL)

- **Shift+J com o cursor dentro de um ponto de controle seu**: 1º toque mostra custo e local ("Base avançada em A: 300 bmat (fábrica tem N).
  Shift+J de novo em 4 s para construir"); o 2º toque em até 4 s constrói. Fica ao lado do `J` (que continua criando ponto).
- A base avançada custa **300 bmat da fábrica**, debitados **só depois** de o ator nascer validado. Se o ator for recusado/nascer errado,
  é desfeito e nada é debitado. Falta bmat: o 2º toque registra um **pedido pendente** — a fábrica passa a **guardar 300 bmat**
  (painel: "Fábrica | guarda 300 bmat para base avançada em B (bmat N)"), depois da reserva de um caminhão destruído (o caminhão tem
  prioridade). Constrói sozinha quando junta; cancela em 180 s, se o ponto deixar de ser seu, se aparecer inimigo no anel, ou com
  Shift+J de novo em 4 s sobre o ponto do pedido.
- Condições: ponto **seu**, sem inimigo no anel, longe da base principal (≥ 30 m) **ou** perto de ponto inimigo (≤ 40 m), chão
  Landscape plano e livre (não em telhado/obra do mod), ≥ 3 saídas livres, no máximo 3 bases. Só com logística ligada e fora do Assalto.
- **Estoque de 15 slots** por base (caixa parcial = 1 slot). Caminhões (`L` sobre a base) levam só o que cabe; **camisas e fuzis só vão a
  quem pode reforçar** (base principal ou base avançada ativa). Ponto de controle sem base passa a receber só munição e bandagens.
- **Recrutar (Ctrl+1/2/3/4/0) na logística**: o soldado nasce na base principal **ou** na base avançada ativa com camisas (e fuzil, para o
  fuzileiro) **mais próxima do cursor**; com o cursor **dentro** de uma base, só nela (recusa clara, sem cair noutra). Ponto sem base **não**
  reforça mais (`CFG.SPAWN.pointSpawn=true` restaura). A mão de obra (`economy.manpower`) **não limita** mais o ramo logístico; limites
  são camisas/fuzis. Cada recruta gasta 1 camisa (+1 fuzil o fuzileiro); mg/atirador/médico/oficial só camisa.
- **Perda**: ponto capturado ou base destruída (morteiro inimigo, dano ×2) → a base some uma única vez, o estoque se perde (mensagem
  "BASE AVANÇADA B capturada: perdeu N camisas e M fuzis"), o ator é destruído. Recapturar o ponto **não** traz a base de volta;
  reconstruir custa 300 de novo. Base com ponto neutralizado fica **inativa** (estoque preservado, não reforça nem recebe).
- **Derrota por falta de tropa** (ramo logístico): sem soldado de combate **e** sem nenhuma camisa em base, fábrica ou caminhão.
- **Trabalhadores da coleta não contam no limite de 12** do esquadrão (`CFG.SQUAD_MAX`); o limite deles é `CFG.COLETA.workers` (3).
  Antes, esquadrão de combate cheio impedia trabalhadores.
- **Save/Continuar (Ctrl+F6)**: seção `fwd` v1 dentro do save v2 (índice do ponto, XYZ, yaw, vida, estoque pelo depósito do ponto; nunca
  endereço de ator). Ao continuar, as bases são refeitas (tudo ou nada, revalidando chão/classe/saídas); posição que não valida mais =
  Continuar recusado com a partida e o arquivo preservados. Pedido pendente **não** é salvo. O v3 recusa um save com `fwd` ("campo
  desconhecido: fwd"); o v4 abre saves do v3; o v4 sem bases grava um save que o v3 lê.
- **Painel**: uma linha por base: `base | camisas N | fuzis N | slots —  | reforça: tudo|só sem fuzil (sem fuzis)|NÃO (sem camisas)` e
  `base A | camisas 12 | fuzis 3 | slots 3/15 | reforça: tudo` / `INATIVA (ponto neutro)`. O painel ganha +1 linha (base principal) + 1 por
  base avançada (medido: 12x222 → 13x222 no cenário do teste 07c; ≤ 96 caracteres por linha de base).
- Partida com logística: 10 fuzis na base principal (`CFG.SPAWN.startRifles = 10`, já do v3).

### Texto para o `MANUAL_TEST.md` (linhas novas; só depois do laboratório)

| # | Faça | Esperado | OK? |
|---|---|---|---|
| 11b | Shift+J com o cursor no chão livre / num ponto neutro ou inimigo | Mensagem "ponha o cursor dentro de um ponto de controle seu" / "não é seu"; nada criado; **não** cria ponto (só J cria) | |
| 11c | Com bmat ≥ 300 acima da reserva: Shift+J sobre um ponto seu longe da base (1º toque), de novo em 4 s | 1º: custo e local; 2º: "BASE AVANÇADA A construída (-300 bmat…)", a base aparece no ponto, painel ganha a linha "base A \| camisas 0 \| fuzis 0 \| slots 0/15" | |
| 11d | Shift+J com pouco bmat, 2 toques | "pedido registrado"; painel "guarda 300 bmat para base avançada em A"; constrói sozinha quando junta; Shift+J sobre o ponto do pedido avisa e, repetido em 4 s, cancela | |
| 11e | L sobre a base avançada (caminhão), esperar a entrega; Ctrl+1 com o cursor dentro da base | Estoque sobe até 15 slots; o recruta nasce **na saída da base**, gasta 1 camisa e 1 fuzil dela | |
| 11f | Ctrl+1 com o cursor num ponto seu **sem** base | Recusa/nasce na base principal; o ponto não reforça | |
| 11g | Inimigo toma o ponto da base (ou morteiro a destrói) | Alerta "BASE AVANÇADA A capturada/destruída: perdeu N camisas e M fuzis"; ator some; sem ator residual | |
| 11h | Com 1+ base avançada: salvar 30 s, fechar, abrir, Ctrl+F6 | Base de volta no mesmo lugar, estoque e vida iguais, uma só | |

### `HELP_TEXT` (já no patch)

- Linha de recrutar: `Ctrl+1/2/3/4/0: recrutar fuzileiro/metralhador/atirador/médico/oficial (logística: nasce na base ou numa base avançada com camisas; cursor numa base = só nela)`
- Linha de construção: `… K: barreira   J: ponto   Shift+J: base avançada (300 bmat, 2 toques)`
- A mensagem final de carga (`log("v0.9 carregado …")`) cita "Shift+J base avançada".

## 2. Teclas

`Shift+J` não está em `GAME_KEYS` (55 teclas) nem colide com tecla do mod: a única tecla `*+J` é `SHIFT+J`. No v3 `J` disparava também com
modificador apertado; no v4 o `J` está embrulhado em `plain()` (o mesmo helper que outras teclas do mod já usam, com `S.MOD_KEYS`), então
Shift+J **não** cria ponto. Cópia do teste de teclas: `test_orders_v4.py` (a suíte `tools/test_orders.py` **não** foi editada).

## 3. Implementação

Tudo em tabelas (`CFG.FWD`, `CFG.SPAWN`, `S.fwdStage/S.fwdRuins`, `logi.*`, `rts.combatCount`): **nenhum local de topo novo**
(check_globals: 175 antes e depois; o compilador aceita 22 locais a mais ⇒ **178 ativos**, igual ao main real). O bloco de funções
(`bases_funcs.lua`, 622 linhas) fica **depois de `local structures = {}`** porque usa `squadCenter`, `structures`, `presence`, `flatSpot`…
(declarados depois de `logi.tick`); por isso o `spawnSite/spawnCommit` do v3 foram **removidos de onde estavam e recriados nesse bloco**
(com a mesma interface). `build_bases.py` aplica ~40 edições por âncora única (falha fechado se a âncora não for única).

Funções novas: `rts.combatCount`, `logi.slotsUsed/spawnCapable/fwdFree/fwdReserve/fwdAudit`, `logi.fwdMake/Exits/Fits/Place/Spawn/Check/Build/Key/Tick`,
`logi.fwdLose` (perda idempotente: captura e morteiro), `fwdRuin/fwdBlast/fwdReset`, `logi.fwdLine`, `logi.canReinforce/noReinforce`,
`logi.spawnSite` (pura) → `spawnSquad` → `logi.spawnCommit` (único débito), `logi.recruit`, e a persistência `fwdSnapshot/fwdValid/fwdPreflight/
fwdStage/fwdStageClear/fwdBind`. Edições em lugares existentes: `colMaintain` (sem SQUAD_MAX para trabalhadores), `needs/nextKind`,
`moveCargo`, `factoryStep` (reserva), `truckStep` (carga por slots; devolve camisas/fuzis à fábrica se a base some), `logi.tick`,
`hudLine`, `logi.blast`, `pointsTick` (`fwdLose` antes do zeramento legado), `spawnSquad` (teto só de combate; `at.exact`), `recruit`
(`if logi.on and combat.mode ~= "assault" then return logi.recruit(role, at) end`; ramos legado/Assalto/F6/newGame intactos),
`waveTick` (derrota por `logi.noReinforce()`), `sv.collect/validate/preflight/load`, teclas e `HELP_TEXT`.

Ordem do `sv.load` (tudo-ou-nada): validar `fwd` → preflight sem mutação → estagiar (spawna todas as bases ou nenhuma; adota ator vivo na
mesma posição) → `applyPlan` da infra → `sv.restore` → `logi.restore` → ligar bases aos depósitos. Falha em qualquer passo desfaz as bases.

## 4. Ordem da pilha v4

`main real` → ECONOMIA → IA_LOGÍSTICA v2 → reserva_bmat → INTERFACE v2 (painel rebaseado) → PERSISTÊNCIA v2 → COLETA MANUAL (v3) →
**BASES AVANÇADAS (v4)**. O `bases_lf.patch` (LF, `a/main.lua b/main.lua`) aplica sobre o candidato v3 em LF; o `bases.patch` (CRLF) aplica
sobre o `candidate_v3/main.lua` em disco e reproduz `candidate_v4/main.lua` byte a byte (conferido no teste 10). As 4 ordens alternativas
das camadas anteriores dão texto idêntico depois de `build_coleta.apply` + `build_bases.apply` (teste 11). **Não** aplicar BASES antes da COLETA.

## 5. Testes (todos PASS; saída completa em `TEST_OUTPUT.txt`, roda com `bash run_all.sh`, ~50 s)

| Suíte | Casos (Lua 5.4 + 5.5) | Cobre |
|---|---|---|
| `test_construction.py` | 12 PASS | 2 toques, janela de 4 s, débito só após spawn, 15 recusas (neutro/inimigo/fora de ponto/perto da base/inimigo no anel/sem logística/Assalto/telhado/inclinado/obra do mod/sem saídas/classe/plano B/teto), rollback de spawn (nil, em destruição, vida, deslocado, rotação, CodeName; `strict=false` relaxa), pedido pendente + reserva (um por vez, constrói sozinho, cancelamentos), caminhão destruído tem prioridade (também pelo Shift+J), razão de bmat |
| `test_recruitment.py` | 14 PASS | base principal (anel, 1 camisa, +1 fuzil só fuzileiro, sem mão de obra, falha de spawn não debita), `spawnSite` pura, base mais próxima do cursor com estoque, saída em rodízio exata, cursor dentro da base = só ela (sem fallback), base inativa, ponto sem base/`pointSpawn`, teto de combate e reserva dos trabalhadores, ramo legado/Assalto idênticos ao v3 |
| `test_loss.py` | 18 PASS | corte de abastecimento, destruição/captura/recaptura (uma vez, razão fecha, reconstruir cobra de novo), morteiro, caminhão em trânsito, 15 slots, `needs/nextKind`, defesa em profundidade, derrota por `canReinforce`, fuzz 25 sementes × 600 passos (razão por base fecha; atores vivos == bases vivas) |
| `test_workers.py` | 8 PASS | trabalhadores fora do SQUAD_MAX em `recruit`, `spawnSquad` e `colMaintain`; limite = `COLETA.workers`; comparação v3 × v4 |
| `test_persistence_bases.py` | 16 PASS | ida e volta (XYZ/yaw/hp/estoque por índice, 1 ator, saídas recalculadas), repetição 3× + 3 cargas novas sem duplicar, posição/classe que não valida mais, falha de spawn com rollback conjunto, 21 adulterações do save, compatibilidade v3/v4, inativa/destruída, pedido não salvo |
| `test_key_panel.py` | 9 PASS | `fwdLine` (4 estados, ≤ 96, pura), `hudLine` só leitura, Shift+J fim-a-fim pelo `bindings`, J ignora modificador, `HELP_TEXT`, análise estática dos únicos lugares que gravam camisas |
| `test_orders_v4.py` | PASS | cópia adaptada de `tools/test_orders.py` + Shift+J registrada/fora de `GAME_KEYS` |
| `test_collection_over_v4.py` | 5 suítes PASS | as 5 suítes da coleta (partida_manual, coleta_nucleo, travamento, persistencia_coleta, spawn_interface) rodando em memória contra o v4 |
| `test_stack_v4.py` | 22 etapas PASS | cópia adaptada de `test_stack_v3.py` (check_globals, orders, custos, economia, IA 25×600, elogi (+legado), bmat, interface 07a–d, persistência (+legado), contrato ESTRADAS, patches em sequência, ordens alternativas, resíduos, **locais ≤ 178 pelo compilador**, main real e `candidate_v3` com SHA intacto) |
| `sensitivity_bases.py` | 21/21 mutantes pegos | débito antes do spawn, custo, reserva do caminhão, idempotência de `fwdLose`, estoque não zerado, `canReinforce`, SQUAD_MAX, ponto sem base, `spawnCommit`, ramo legado, 6 recusas do save, `bActorIsBeingDestroyed`, teto de slots, `exact`, tecla J |

Mutante deixado de fora de propósito: NaN/inf em x/y/z/yaw/hp do `fwd` — o validador genérico do save ("tabela de dados") recusa antes de
`fwdValid`, então o `fin()` de lá é defesa em profundidade (mutante equivalente).

### Expectativas alteradas (nenhuma regressão escondida; cada uma marcada no código)

1. **Trabalhadores fora do SQUAD_MAX** (decisão nova). `test_coleta_sobre_v4`: em `test_partida_manual` a asserção "esquadrão cheio: sem vaga
   para trabalhador" virou "`workers() == COLETA.workers` e `#squad == SQUAD_MAX + workers`". `test_trabalhadores` mostra o v3 (0 trabalhadores com
   12 de combate) contra o v4 (3).
2. `test_coleta_sobre_v4`, `test_spawn_interface`: o fim da fatia da análise estática passou de `function logi.tick()` para o marcador
   "Persistência: extensão `fwd` v1" porque `spawnSite/spawnCommit/recruit` agora ficam depois (escopo de `squadCenter`/`structures`).
3. `test_orders_v4.py`: as 8 adaptações da coleta (implantação 1000/2 vagas/4 atores, caminhão de recurso por construir) **mais** a asserção
   nova de `SHIFT+J` (registrada, fora de `GAME_KEYS`, sem outra `*+J`). O arquivo original `tools/test_orders.py` não foi tocado.
4. `test_stack_v4.py` (diff em `diffs/test_stack_v4.diff`, marcas `V4`):
   - **`CFG.SPAWN.pointSpawn=true` nas suítes antigas que entregam camisas/fuzis em depósito de ponto sem base**: etapa 05 (economia),
     08/08-L e 06b/06b-L (persistência v2 e elogi, via `new_load`) e contrato 09 (b)/(c). O que elas testam (driver só entrega na chegada,
     caminhão a caminho, razão) não depende de camisas/fuzis chegarem a um ponto sem base, e o interruptor restaura exatamente o comportamento
     antigo. O comportamento **novo** (default `false`) é testado a parte: etapa 09 (a0), `test_perda`, `test_recrutamento`. Por isso
     `spawnCapable` honra `pointSpawn` (com `true`, todo depósito de ponto volta a ser capaz) — correção feita durante esta etapa.
   - Nomes de 06b-L/08-L: deixaram de ser "sem NENHUMA alteração" (têm só a adaptação acima).
   - 00: também confere `candidate_v3` em disco (bytes e SHA `9b89b113…`); 01: limite de 178 pelo compilador; 10: confere `bases_lf.patch`/`bases.patch`;
     11: `build_bases.apply(build_coleta.apply(...))`; 06: rótulo do arquivo corrigido.
5. Observado (não é expectativa de teste): painel 12 → 13 linhas no cenário 07c.

## 6. Gates de laboratório (nada disto foi visto; o jogo não foi aberto)

Sondas só-leitura (`probes/A1…A4`, sintaxe conferida na etapa 1, **nunca executadas**) e o ensaio B1 continuam pendentes e **decidem**
os valores provisórios de `CFG.FWD`:

- **A1/A2 (HomeRegionW):** colunas do catálogo e CDO de `BPForwardBase1_C` carregam? `LoadAsset("/Game/Blueprints/Structures/Bases/BPForwardBase1.BPForwardBase1_C")`
  (caminho **inferido**); há coluna/UFunction de spawn nativo? Decide `visual="native"` e se há risco de respawn nativo (R1).
- **A3 (HomeRegionW, CallumsCapeHex, DeadLandsHex):** base avançada nativa existente, componentes, bounds só-colidindo (→ `CFG.FWD.half`
  = 600 cm provisório), ruínas de base/hospital, `ItemHolder` real vs "15 slots" (R10: interpretação provisória em `CFG.FWD.cap`).
- **A4 (partida):** quantos lugares/saídas por ponto passam no predicado (`half`, `clear`, `maxSlope`, `maxHeight`, `minExits=3`, `exitR`).
- **B1 (L3 do roteiro, com autorização):** spawnar `BPForwardBase1_C` num XYZ validado: nasce íntegro (Health = MaxHealth = 1725, `CodeName = "ForwardBase1"`
  — o `strict=true` do mod **recusa** se divergir)? `TeamId` 255 vs 1 (`CFG.FWD.teamId=nil` hoje: o mod não escreve nada); `K2_DestroyActor`; ruína
  `BPDestroyedForwardBase1_C` (`CFG.FWD.ruin=false` até o B1); 60 s de `UE4SS.log` sem `Registry`/respawn nativo/ator residual; ms do spawn.
  Se não nascer íntegra: **plano B** (malha do mod) — está **declarado (`visual="mesh"`) mas NÃO implementado**; hoje cai em "classe não carregou".
- **L2:** conferir `minFromBase=3000`/`maxToEnemyPoint=4000` (cm) com a geometria real do hex (há ponto elegível em cada partida?).
- **L4–L10 do roteiro:** nascer na saída (não em telhado/parede), `J`/`Shift+J` sem engasgo, caminhão até a base respeitando 15 slots, pedido pendente
  sem fome de munição, perda por captura/morteiro sem ator residual, save → fechar → Ctrl+F6 em carga nova, 10 min com 3 bases (estabilidade).
  O gate de estabilidade do `MODLOG` ("não ampliar features antes de isolar a queda") continua valendo.
- **Calibração:** `startRifles = 10` (já do v3) com a cadência real das ondas; `FWD.max = 3`; custo de bmat × ritmo da fábrica; largura do painel
  com 3 bases + pedido pendente (+4 linhas no máximo) na tela real.
- **Confirmar:** Shift+J não dispara também o `J` puro (o `plain()` cuida; o campo `S.MOD_KEYS` precisa conter as teclas Shift reais do UE4SS).

## 7. Riscos

1. **Classe/spawn nunca vistos** (maior risco): `BPForwardBase1_C` nunca foi instanciada; caminho inferido; `strict=true` pode recusar uma base
   que na prática funciona (relaxar para `false` no B1) ou aceitar uma que o jogo trata como ponto de respawn nativo (R1).
2. **Plano B não implementado** e **ruína desligada**: se o B1 reprovar a classe, não há base visual até implementar a malha.
3. **15 slots** é interpretação (`StoredItemCapacity`); se for outra, só muda `CFG.FWD.cap`, mas o save de um valor antigo é validado contra o `cap` atual.
4. **Save com `fwd` não abre no v3** (recusa "campo desconhecido: fwd" por desenho; o jogador perde Continuar ao voltar de versão com bases salvas).
   Pedido pendente não é salvo (cancela ao carregar).
5. **Camisas/fuzis deixam de ir a ponto sem base** (decisão D2): saves/partidas do v3 com estoque nesses pontos mantêm o estoque, mas ele não é
   usado para nascer; a partir daí a logística só reabastece a base principal e as avançadas. Ordem de caminhão fixada (`L`) num ponto sem base
   leva só munição/bandagens.
6. **Mão de obra não limita mais o ramo logístico**: a taxa de recrutamento passa a ser só camisas/fuzis (e o ritmo de cliques); equilíbrio a validar.
7. **Derrota** muda no ramo logístico (`canReinforce`): a partida só termina sem tropa e sem camisa em lugar nenhum (nem em caminhão).
8. **Painel** cresce até +4 linhas (principal + 3 bases) além do pedido; em tela pequena pode cobrir mais da visão.
9. **`J` embrulhado em `plain()`**: com Ctrl/Alt/Shift apertado, J puro deixa de criar ponto (comportamento anterior disparava). Depende do
   `keyDown` real do UE4SS (`S.MOD_KEYS`).
10. **Locais**: 178 ativos pelo compilador (folga de 22, igual ao main real); nada de topo novo. Qualquer feature futura deve continuar em tabelas.
11. Escopo de leitura fora do que o mod controla: um ator `BPForwardBase1_C` vivo na posição salva é **adotado** no Continuar (não duplica).
12. `Shift+J` usa `GetRealTimeSeconds` (tempo real) para os 4 s: com o jogo pausado a janela continua correndo (a confirmar no laboratório que é o desejado).

## 8. Incidente a registrar

Por engano, uma vez, rodei `data/parallel/logistics_ai/finishing/manual_collection/test_stack_v3.py` (o original), que **regrava**
`manual_collection/test_output_v3.txt` (mesmo tamanho, 23848 bytes). Nenhum outro arquivo fora de `forward_bases/stage2/` foi tocado;
o `test_stack_v4.py` grava só `test_output_v4.txt` aqui e não importa/executa o original. `mod/.../main.lua` (SHA `33d6c7e5…e679`) e o `candidate_v3`
(SHA `9b89b113…63e6`) estão intactos antes e depois (conferido por `run_all.sh` e pela etapa 99).

## 9. Arquivos

`build_bases.py` (gera tudo), `bases_cfg.lua`, `bases_funcs.lua` (fragmentos aplicados), `candidate_v4/main.lua` + `SHA256.txt`, `bases.patch` (CRLF),
`bases_lf.patch` (LF), `harness_bases.py`, `test_construction.py`, `test_recruitment.py`, `test_loss.py`, `test_workers.py`,
`test_persistence_bases.py`, `test_key_panel.py`, `test_orders_v4.py`, `test_collection_over_v4.py`, `test_stack_v4.py` + `diffs/test_stack_v4.diff`,
`sensitivity_bases.py`, `run_all.sh`, `TEST_OUTPUT.txt`, `test_output_v4.txt`, `PROGRESS_NOTES.md`.

Reproduzir: `cd /d/GitHub/foxhole-rts && bash data/parallel/forward_bases/stage2/run_all.sh` (usa `PYTHONPATH=D:/tools/pylibs`).
