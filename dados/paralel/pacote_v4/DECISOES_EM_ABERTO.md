# DECISOES_EM_ABERTO — o que falta decidir ou calibrar na pilha v4

Só o que depende do usuário ou de medição ao vivo. "Onde" = nome no `CFG` e linha no candidato a integrar (v4.1; as linhas são as mesmas da v4, a v4.1 troca 3 linhas sem mudar a contagem; o `main.lua` ao integrar). Os valores são **propostas de design**
(exceto custo/vida/capacidade de estrutura, que vêm das tabelas do jogo). Já decidido e fora desta lista: trabalhadores fora da escala das ondas, do centro do esquadrão e da derrota no Assalto (v4.1, decisão do orquestrador), o estoque de recomeço da cadeia inimiga (`elogi` descartável reinicia do estoque de cenário),
a ordem da pilha, a implantação em 1000 bmat.

| # | Decisão | Valor atual | Onde | O que informa a decisão |
|---|---|---|---|---|
| 1 | bmat inicial da fábrica | `bmat0 = 40` (40 + 60 de 120 sucata = 100 para o 1º caminhão); 240 elimina a coleta | `CFG.COLETA.bmat0` 2475 | C3: tempo real até o caminhão |
| 2 | Ritmo da coleta | `rate 0,5` sucata/s, `cap 40`, `workers 3`, `quiet 60` s, `leg 180` s | `CFG.COLETA` 2477–2489 | C3: ~6 min a 470 m (harness) vs 2 min 45 s a 80 m; distância real no hex |
| 3 | Fuzis de partida | `startRifles = 10` (só na partida manual) | `CFG.SPAWN.startRifles` 2503 | C11: quando acabam e quanto leva o 1º lote |
| 4 | Piso mínimo de camisas | Nenhum. Reserva só protege a reposição de trabalhadores enquanto a coleta é necessária; sem camisas e sem trabalhadores a coleta para | `logi.workerReserve` 3116; `CFG.LOGI.shirts0` 30 | Se a base fica sem camisas no meio da coleta (C7) |
| 5 | Piso grátis da onda inimiga | `free 5`/onda; `trip 20`, `front0 m2/c10`, `want 4/20`, `trucks 2`, `minLoad 3` | `CFG.ECHAIN` 3540–3546 | I14: cadência real das ondas (a tabela só vale ≥ ~55 s); R (robô) |
| 6 | Comboio inimigo | primeiro aos 20 s, depois a cada 35 s, bounty +25 de mão de obra | `CFG.ECONVOY` 3457–3458 | I2–I5 |
| 7 | Bases avançadas: quantidade, custo, capacidade | `max 3`, `cost 300` (dado do jogo), `cap 15` slots (interpretação de `StoredItemCapacity`, provisório) | `CFG.FWD` 2521 | K3–K5, T1 (10 min com 3 bases) |
| 8 | Pedido pendente da base | cancela em 180 s de tempo de jogo; a fábrica guarda 300 bmat (depois dos 100 por caminhão) | `CFG.FWD.pending` 2523 | K4: fome de munição durante o pedido |
| 9 | Confirmação do Shift+J | 4 s em **tempo real**: a pausa não estica o prazo | `CFG.FWD.confirm` 2522 | Item 11i do manual; K10 |
| 10 | Contrato `strict` e `TeamId` da base | `strict = true` (recusa se `Health ≠ MaxHealth ≠ 1725` ou `CodeName ≠ ForwardBase1`); `teamId = nil` (o mod não escreve) | `CFG.FWD.strict` 2519, `teamId` 2520 | S11 (B1 da classe): relaxar `strict` se a base boa for recusada; decidir 255 × 1 |
| 11 | Ruína ao perder a base e plano B visual | `ruin = false` (não cria ruína); `visual = "native"`; `"mesh"` declarado, **não implementado** | `CFG.FWD.ruin` 2518, `visual` 2515 | S11. Se `ForwardBase1` não nascer: plano B (malha) é task nova, K não roda |
| 12 | Footprint e elegibilidade da base | `half 600`, `clear 150`, `maxSlope 60`, `maxHeight 250`, `minExits 3`, `exitR 800`, `minFromBase 3000`, `maxToEnemyPoint 4000` (cm) | `CFG.FWD` 2524–2525 | K1: há ≥ 1 ponto elegível por partida no hex? |
| 13 | Ponto de controle sem base reforça? | Não (recruta nasce na base principal). `true` restaura o comportamento antigo | `CFG.SPAWN.pointSpawn` 2508 | K7 e itens 9/11f do manual |
| 14 | Mão de obra no ramo logístico | Só paga morteiro, barreira, trincheira, caixa, posto e arame; recrutar usa camisa (e fuzil) | `recruit` 1423 | Jogo: o equilíbrio fica claro no manual 8 e nas ondas |
| 15 | Robô de regressão | `t_bot.lua` defasado (recruta por mão de obra, assume caminhão de recurso, não usa `L` nem Shift+J) | `D:/tools/foxhole-lab/` (fora do repositório) | R0 do roteiro; sem a adaptação as células B0–B3 medem o robô |
| 16 | Gate de estabilidade | A1 e B1 feitos com a fonte 33d6c7e5; B2 e A2 pendentes; a v4 muda o hash | `estabilidade/controle_crash.md`, `COMO_INTEGRAR.md` §2 | Decisão do coordenador: gate antes ou depois de gravar a v4 |

Itens 1–4, 7–9 e 13 são equilíbrio e só o usuário fecha. Itens 10–12 são técnicos e o laboratório fecha com S11/K1. Itens 5–6 e 15 dependem de cadência real. O 16 é de processo.
