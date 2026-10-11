# MODLOG_RASCUNHO — entrada de topo para `MODLOG.md`

Rascunho para a task INTEGRACAO/LABORATORIO colar **no topo** do `MODLOG.md` (as entradas novas ficam no topo), **depois** de rodar o `BATCH_SCRIPT.md`. Tudo o que o texto
afirma sobre código e testes offline foi conferido contra o candidato **v4.1** (`package_v4/v4_1/candidate/main.lua`, SHA256 `62245d23…598f` = `candidate_v4` `025e3b80…aab0` + `v4_1/v4_1.patch`) ou executado na cópia de ensaio (`HOW_TO_INTEGRATE.md` §6).
Os campos `[preencher no laboratório]` são medições ao vivo que **ninguém fez**: se um não for medido, apague a frase em vez de deixar o campo, e não escreva resultado inventado.
Ajuste a data e o título ao dia da sessão. Nada daqui foi aplicado.

Instruções de preenchimento: trocar cada `[preencher no laboratório]` pelo número da saída do passo indicado entre parênteses (os passos são do `BATCH_SCRIPT.md`);
onde um passo falhou, escrever "FALHOU" e o motivo, e **não** repetir a promessa da primeira frase.

---

## 2026-10-10 — Pilha v4.1 (ECONOMIA, IA_LOGISTICA v2, reserva de bmat, INTERFACE v2, PERSISTENCIA v2, COLETA_MANUAL, BASES_AVANÇADAS, trabalhadores fora da escala das ondas): integrada e validada em lote

- **O que entrou (um único `main.lua`, v4.1, SHA256 `62245d23af36160f589707fe422b6fb167abaa58482ef7f58a49cd39021b598f`, CRLF, 7323 linhas; antes `33d6c7e5…e679`; a v4 `025e3b80…aab0` é a base).** Ordem da pilha: ECONOMIA >
  IA_LOGISTICA v2 > reserva de bmat > INTERFACE v2 (painel rebaseado) > PERSISTENCIA v2 > COLETA_MANUAL > BASES_AVANÇADAS. ESTRADAS **não** entrou. O diff por função (105 hunks) não toca contorno,
  hook de animação nem câmera. Locais de topo: 178 pelo compilador (folga 22), 175 pelo `check_globals.py`; nada novo no topo (tudo em `CFG`, `S`, `logi`, `sv`, `rts`).
- **Economia:** a partida logística tem 4 produtos na fábrica (munição 80 bmat, camisas 80 bmat/10 un, fuzis 100 bmat/20 un, bandagens 80 bmat/50 un). Recrutar custa **1 camisa**
  (o fuzileiro, também 1 fuzil) do estoque do local de nascimento; **não** gasta mão de obra (que só paga morteiro, barreira, trincheira, caixa, posto e arame, e o recrutamento
  **no Assalto**). O médico só trata com bandagem num depósito a ≤ 5 m (consome 1 por tratamento). Custos de receita/estrutura vêm das tabelas do jogo.
- **Reserva de bmat:** 100 por caminhão destruído ou ainda por construir; a fábrica não gasta essa reserva em caixas. O pedido de base avançada reserva mais 300, depois do caminhão.
- **Coleta manual:** Shift+F6 já **não** cria o caminhão de recurso. A partida começa com bmat 40, 30 camisas, 10 fuzis, 6 caixas de munição e 3 trabalhadores (soldados **sem arma**, 1 camisa
  cada; o 1º aos ~5 s, os outros a cada ~3 s) que coletam sucata a pé (0,5/s, carga 40) até a fábrica juntar 100 bmat e construir o caminhão. Ordem do jogador libera o trabalhador
  por 60 s; combate o faz pausar. A implantação (Alt+L) passou de 1100 a **1000** bmat (2 caminhões de suprimento em vez de 3).
- **IA logística v2:** o inimigo tem cadeia real (retaguarda → fábrica → comboio de `BPTruckC` → frente); razão fechado (`eAudit`). A onda recebe a guarnição grátis (piso 5/onda) mais o que a frente equipa;
  comboio destruído rende +25 de mão de obra. Calibração v2 (`CFG.ECHAIN`: `free 5`, `trip 20`, `front0 m2/c10`, `want 4/20`, `trucks 2`, `minLoad 3`) é **proposta**; vale em cadência de onda ≥ ~55 s.
- **Painel (INTERFACE v2):** várias linhas (logística, fábrica, pronto, depósitos, `base …`, caminhões, `INIMIGO …`, `coleta manual …`, atalhos), 12–13 linhas, ≤ ~222 colunas medido offline.
- **Persistência v2:** save v2 com parser de literais (nunca `load` do arquivo), escrita atômica `.tmp` → `.bak`/`.corrupt`, infraestrutura paga e bases avançadas refeitas de graça e
  **tudo ou nada**, seção `elogi` descartável sozinha ("CADEIA INIMIGA REINICIADA"), "Continuar recusado (partida atual e save preservados)", "INCOMPLETA … autosave suspenso".
  A infraestrutura **não** sobrevive ao reinício do jogo por si só (as ruínas voltam); só o Continuar a refaz.
- **Bases avançadas:** Shift+J (2 toques em até 4 s de relógio real), 300 bmat, estrutura nativa `ForwardBase1` (1725 HP), até 3, 15 slots, o recruta nasce na saída da base com a camisa e o
  fuzil da própria base; ponto comum **não** reforça (`CFG.SPAWN.pointSpawn=false`); perda por captura do ponto ou por morteiro inimigo (`blastMul` 2) apaga a estrutura e o estoque.
  O `J` agora só cria ponto **sem** modificador.

- **v4.1 (decisão do orquestrador):** soldados da coleta (`role="worker"`) não contam no tamanho das ondas inimigas, no aviso "próxima onda" nem na derrota por falta de tropa do Assalto
  (`waveTick` e `logi.noReinforce` passam a usar `rts.combatCount()`) e `squadCenter()` usa só os combatentes vivos (fallback: todos os vivos; nil sem ninguém), para o campo de sucata não puxar ondas, reforço, arame nem pontos iniciais. 4 trocas, sem local de topo novo.

### Verificações offline (feitas antes do laboratório)

- Bateria pós-integração (`data/parallel/package_v4/post_integration_battery.py`): com a v4.1, **28/28 PASS** (o item novo é `v4_1/test_v4_1.py`; com `--sensibilidade --rapido`, 26/26 com os 21 mutantes pegos); com a v4 pura eram 27/27 e a mesma bateria falha só no item novo. Cobre (em cópia de ensaio no scratchpad) sintaxe e folga de locais em Lua 5.4 e 5.5, `check_globals`,
  `test_costs`, `test_inventory_probe`, `test_orders` adaptado, 7 suítes de bases, passos 05–09 do `test_pilha_v4` e o contraste v4 × v4.1; tem controle negativo (suíte quebrada de propósito reprova).
- `tools/test_orders.py`: 9 adaptações às teclas/mensagens novas + bloco do comboio v2 (`apply_test_orders.py`); passa contra o candidato.

### Laboratório (preencher com as saídas dos passos; tudo abaixo é medição ao vivo)

- **Gate de estabilidade** (G): A1 184 s (já no topo do MODLOG, 2026-10-09). B1 184,3 s, 168 cópias, stratTick ~12 ms (arquivo `crash-control-B1.txt`). B2 `[preencher no laboratório]`;
  A2 `[preencher no laboratório]`. Fonte do gate: `[preencher: 33d6c7e5… ou 62245d23…]`. Log sem `Registry`/`Access violation`: `[preencher no laboratório]`.
- **Sondas só leitura / bancada (S):** versão do UE4SS e do jogo `[preencher no laboratório]`; `io.open`/`os.rename`/`os.remove` no Windows `[preencher no laboratório]` (S7);
  mundo e superfície `[preencher no laboratório]`.
- **B1 da classe `ForwardBase1` (S11):** spawn `[preencher no laboratório]` ms; `Health/MaxHealth` `[preencher no laboratório]` (esperado 1725/1725 pelo contrato `strict`);
  `CodeName` `[preencher no laboratório]`; `TeamId` `[preencher no laboratório]` (o mod não escreve); some sem residual `[preencher no laboratório]`; 60 s sem queda `[preencher no laboratório]`.
- **Hex (H0–H1):** mapa `CallumsCapeHex`; Alt+L `[preencher no laboratório]` (esperado `-1000 bmat do cenário; saldo 0`, 2 `BPTruckW_C`); repetir não duplica `[preencher no laboratório]`.
- **Coleta manual (C):** distância campo–refinaria real `[preencher no laboratório]` m; 1ª entrega aos `[preencher no laboratório]` s; 1º caminhão de recurso aos `[preencher no laboratório]` s
  (harness: 165 s a 80 m, 359 s a 470 m); T-pose dos trabalhadores `[preencher no laboratório]`; trabalhador preso/perdido `[preencher no laboratório]`; reativação após perda do caminhão
  `[preencher no laboratório]`; custo por quadro com e sem coleta `[preencher no laboratório]` ms.
- **Economia (C10–C12):** os 4 produtos chegam ao depósito `[preencher no laboratório]`; recrutar fuzileiros recusa ao acabar os 10 fuzis `[preencher no laboratório]`; a reserva de 100 bmat
  segura a fábrica e o caminhão volta em `[preencher no laboratório]` s.
- **Cadeia inimiga (I1–I14):** comboio 1 saiu aos `[preencher no laboratório]` s; entrega única `[preencher no laboratório]`; emboscada: perda única + alerta `+25`
  `[preencher no laboratório]`; `auditoria` verdadeira ao fim de toda partida `[preencher no laboratório]`; `BPTruckC` ativos ≤ 2 `[preencher no laboratório]`.
- **Bases avançadas (K):** pontos elegíveis no hex `[preencher no laboratório]`; construção `[preencher no laboratório]` (ator íntegro, `bmat` só debitado depois do ator); recrutar na base
  `[preencher no laboratório]`; perda por captura e por morteiro sem ator residual `[preencher no laboratório]`; 10 min com 3 bases (T1): PID vivo `[preencher no laboratório]`, custo
  `[preencher no laboratório]` ms/quadro.
- **Persistência (V):** `sv.save` `[preencher no laboratório]` ms, `sv.load` `[preencher no laboratório]` ms; 4 spawns na restauração; carteira `0/1000`; idempotência do 2º `sv.load`;
  recusas (V9) `[preencher no laboratório]`; arquivos restaurados ao SHA256 inicial `[preencher no laboratório]`.
- **Painel e teclas (entrada real do usuário):** ver `MANUAL_TEST.md` itens 2, 8, 9, 11, 11a–11j, 12s–12v, 12y, 12z*, 12aa–12am: `[preencher com o resultado do usuário]`.
- **Regressão com o robô (R, opcional):** `[preencher no laboratório]` ou "não rodou nesta sessão".
- Laboratório encerrado: só o PID da cópia (`[preencher: PID]`); Steam preservado; `map.txt` temporário removido `[preencher no laboratório]`.

### Decisões e achados registrados nesta entrada

- Divergências relatório × código que o texto da integração segue pelo código estão em `HOW_TO_INTEGRATE.md` §8 (a lista de 9 itens). Decisões que dependem do usuário (balanço): `OPEN_DECISIONS.md`.
- Gotchas novos (de 48 em diante) em `CONSOLIDATED_GOTCHAS.md`, a levar para `knowledge/games/foxhole/…` com `UM_HOME=D:/tools/um-home python -m um kb check`.
- Pendências que **não** fecham com este lote: gate de estabilidade completo (B2/A2) se rodou com outra fonte; o plano B visual das bases (malha) se `ForwardBase1` não nasceu; calibração da cadeia inimiga
  em cadência real de ondas; Shift+J durante a pausa (relógio real).
