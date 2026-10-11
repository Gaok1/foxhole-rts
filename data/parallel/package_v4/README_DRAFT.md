# README_RASCUNHO — trechos de `mod/README.md` que mudam com a pilha v4

Rascunho para a task INTEGRACAO publicar **depois** do laboratório. Nada foi aplicado em `mod/README.md`. Cada bloco diz qual seção (ou linha de tabela) do
README atual ele substitui; o texto do bloco está escrito para colar. Tudo foi conferido contra o candidato (candidato **v4.1** = v4 + `v4_1/v4_1.patch`, SHA256
`62245d23…598f`; base `candidate_v4/main.lua` `025e3b80…aab0`); o que **nenhum teste ao vivo viu** está marcado **[laboratório]** e deve perder a marca (ou ser corrigido) com os resultados do
`BATCH_SCRIPT.md`. Números de `CFG` são valores atuais do candidato (propostas de design, exceto custos/vida/capacidade de estrutura, que vêm das
tabelas do jogo). Onde o código e um relatório divergiram, o texto segue o código (lista em `HOW_TO_INTEGRATE.md` §8 e no relatório do agente).

---

## 1. Tabela de teclas (SUBSTITUI as linhas `Ctrl+1 / 2 / 3 / 4 / 0`, `L`, `Shift+L`, `Alt+L` e `J` da tabela da seção `## Controles`; ACRESCENTA `Shift+J`)

| Tecla | Ação |
|---|---|
| Ctrl+1 / 2 / 3 / 4 / 0 | Recrutar fuzileiro / metralhador / atirador / médico / oficial (só um). **Numa partida com logística:** custa **1 camisa** do estoque de onde o soldado nasce (o fuzileiro gasta também **1 fuzil**), nasce na base principal ou numa base avançada com camisas — a mais próxima do cursor; com o cursor **dentro** de uma base, só nela — e **não** gasta mão de obra. **No Assalto** (e sem logística): mão de obra (20 / 35 / 45 / 30 / 40) |
| L | O próximo caminhão de suprimentos vai ao depósito sob o cursor (base principal, base avançada ou ponto seu); fora deles = automático |
| Shift+L | Prioridade da fábrica: automático → munição → camisas → fuzis → bandagens |
| Alt+L | Implantar refinaria/fábrica nos locais nativos e os caminhões de suprimento faltantes, com orçamento inicial do cenário (1000 bmat) |
| J | Criar ponto de controle sob o cursor (até 5). Só **sem** modificador: com Shift apertado não cria ponto |
| Shift+J | Base avançada sobre um ponto seu (300 bmat da fábrica; **dois toques em até 4 s**: o 1º mostra custo e local, o 2º constrói). Ver "Bases avançadas" |

Texto da ajuda (F5) e banner de carga já trazem `Shift+J: base avançada (300 bmat, 2 toques)` e a linha de recrutar nova (já estão no candidato).
**[laboratório]** Shift+J não dispara também o `J` puro (o `plain()` depende de `S.MOD_KEYS` com as teclas Shift reais do UE4SS).

---

## 2. `## Classes e economia` (SUBSTITUI o parágrafo "A mão de obra começa em 60 …" até o fim da seção, e acrescenta o aviso logo abaixo da tabela de classes)

> **Custo das classes (coluna "Custo"):** é mão de obra e vale no Assalto e fora da logística. Numa partida com logística (Shift+F6) recrutar custa **camisas**
> (e fuzil para o fuzileiro): ver "Logística". A mão de obra continua pagando morteiro (40), barreira (15), trincheira (20), caixa de suprimento (25),
> posto de socorro (30) e arame (10).

A mão de obra começa em 60, regenera 1/s mais 0,5/s por ponto de controle seu (máx. 200) e rende +8 por abate e +30 por onda eliminada.
Nas ondas automáticas, vence quem eliminar a 10ª onda ou segurar todos os pontos de controle por 90 s seguidos. A derrota ocorre quando o inimigo domina todos os
pontos de controle ou por **falta de tropa**: no ramo logístico, quando não resta nenhum soldado de combate **e** não há nenhuma camisa na base, nas bases avançadas,
na fábrica ou em caminhão (os trabalhadores da coleta não contam como combate); fora dele (Assalto, sem logística), quando não há soldados de combate e a mão de obra não paga um
fuzileiro. A precisão inimiga cresce 4% por onda (até +50%), e cada onda traz um inimigo a mais para cada ~2,5 soldados seus (até 16 por onda; só contam soldados de **combate**: os 3 trabalhadores da coleta não aumentam
a onda, não entram no aviso "próxima onda" e não seguram a derrota por falta de tropa, nem no Assalto).

---

## 3. `## Pontos de controle` (SUBSTITUI duas linhas da lista)

- (linha "Ponto seu é posto de socorro e depósito …") → **Ponto seu é posto de socorro e depósito:** soldados dentro do anel recarregam 15% da munição por segundo e, sem
  supressão, recuperam 2 HP/s. Na logística o depósito do ponto recebe **munição e bandagens**; camisas e fuzis só chegam a quem pode reforçar (base principal e base avançada
  ativa), e o ponto perdido perde o estoque.
- (linha "Recrutar (Ctrl+1..4) com o cursor dentro de um ponto seu faz o soldado nascer nele.") → **No Assalto e fora da logística**, recrutar (Ctrl+1..4) com o cursor dentro de um
  ponto seu faz o soldado nascer nele. **Na logística** um ponto de controle comum **não reforça**: o recruta nasce na base principal ou numa base avançada (ver "Bases avançadas").
  `CFG.SPAWN.pointSpawn = true` restaura o comportamento antigo.

---

## 4. `## Assalto (Alt+F6)` (ACRESCENTA ao fim da seção)

No Assalto o recrutamento continua sendo por **mão de obra** (e gasta também a camisa do depósito, como antes); não há comboios inimigos nem bases avançadas
(Shift+J responde "bases avançadas só numa partida com logística (fora do Assalto)"). **[laboratório]** I11/K9 do roteiro.

---

## 5. `## Salvar e continuar` (SUBSTITUI a seção inteira)

Durante as ondas automáticas a partida é gravada sozinha a cada 30 s em `FoxholeRTS/save.txt` (formato **v2**): onda, placar, mão de obra, dificuldade, pontos e donos,
barreiras, trincheiras, cada soldado vivo dos dois lados (classe, posição, vida, abates e munição) e, numa partida com logística, também: estoques e produção da
**logística do jogador** (fábrica, caminhões, depósitos, coleta), a **infraestrutura implantada e a carteira** (o que foi pago com Alt+L: código, posição e rotação da
ruína), a **cadeia inimiga** (seção `elogi`: estoque da retaguarda, frente, pedido pendente) e as **bases avançadas** (seção `fwd`: ponto, posição, vida e estoque).
Nunca grava endereço de ator. Caixas de suprimento, morteiros em voo, rotas, comboios na estrada e o pedido pendente de base avançada não são gravados (o comboio volta
como carga pendente na retaguarda; o pedido é cancelado ao carregar; a carga em mãos dos trabalhadores é descartada).

- **Gravação:** vai para um temporário conferido por releitura; o save anterior vira `save.txt.bak` (ou `.corrupt`, se estava inválido); só então o temporário vira o
  save. Se a sessão cair entre os dois passos, o Continuar lê `save.txt`, depois `save.txt.tmp`, depois `save.txt.bak`.
- **Ctrl+F6 (continuar):** ao abrir o jogo um alerta avisa que há partida salva; Ctrl+F6 continua, Shift+F6 começa outra. Antes de apagar qualquer coisa o mod valida o
  arquivo (formato, mundo, superfície, ruínas, carteira, logística). **Se algo não confere, o Continuar é recusado** ("Continuar recusado (partida atual e save
  preservados): motivo") e a partida atual e o arquivo ficam como estão. A infraestrutura paga e as bases avançadas são refeitas sobre o mesmo lugar, de graça e
  **tudo ou nada** (posição que não valida mais = recusa). Numa carga nova do hex não é preciso repetir Alt+L antes de continuar. **[laboratório]**
- **Continuação incompleta:** se algo do estado não pôde ser refeito (um ponto que não voltou, por exemplo), a partida abre com o aviso "INCOMPLETA: …; autosave suspenso"
  e o autosave **não** sobrescreve o save bom até você decidir (Ctrl+F6 tenta de novo; Shift+F6 começa outra).
- **Cadeia inimiga:** se a seção `elogi` estiver ausente, inválida, de versão futura ou sem logística, **só ela** é descartada: a cadeia inimiga recomeça do estoque do
  cenário, com o aviso "CADEIA INIMIGA REINICIADA (motivo): estoque de cenário" por 10 s; o resto do jogador é restaurado. Qualquer outro campo inválido recusa tudo.
- **Compatibilidade:** a v4 abre saves das versões anteriores; **o inverso não vale** — um save com bases avançadas ou com trabalhadores não abre numa versão sem a
  coleta/as bases (campo desconhecido). Vitória ou derrota apagam `save.txt`, `.tmp`, `.bak` e `.corrupt`.

---

## 6. `## Logística` (SUBSTITUI a seção inteira)

**Estado atual:** protótipo; HomeRegionW é a ilha de treinamento/embarque dos Wardens, não a guerra. Estradas, campos e instalações mudam conforme a região. A implantação
inicial em `CallumsCapeHex` usa locais nativos e atores reais; o transporte ainda anda em reta, sem colisão, não pela estrada. Construir facilities ainda não está implementado.
Nova partida/assalto requerem campo de sucata, refinaria e fábrica ativos carregados e **dois caminhões de suprimento** do mapa (o de recurso é construído pela fábrica, ver
"Início da partida"). Se faltar algum, o mod avisa e não apaga a partida atual; não cria lugares ou caminhões invisíveis para fingir uma cadeia. Ruínas não são instalações
operacionais. A checagem não depende de aparecer na tela. O comboio rejeita retorno de spawn já marcado para destruição, mesmo se `IsValid` ainda for true. Custos de
estruturas/veículos vêm da reexportação do lote 16.

**Implantação inicial (Alt+L, antes da partida):** sistema próprio do mod, instantâneo, não o canteiro nem o inventário do Foxhole. Há **1000 bmat** de orçamento do cenário:
refinaria 400, fábrica 400 e 100 por TruckW (**dois** caminhões de suprimento; o de recurso não é implantado). Só preenche o que falta; usa campo de sucata ativo, ruínas
correspondentes próximas e suas posições/rotações originais. Os caminhões nascem em terreno Landscape próximo à fábrica, com relevo/folga/separação checados, não em
telhados. Confere HP/classe/posição dos atores. Falha desfaz os spawns, restaura as ruínas e não debita nem limpa os soldados existentes. Repetir não duplica uma cadeia já
pronta; o saldo dura nesta carga do mundo, separado do bmat de produção. Não reconstrói livremente facilities nem gasta mão de obra. Instalações implantadas permanecem neste mundo
ao reiniciar a partida. A infraestrutura paga e a carteira **são gravadas no save** (ver "Salvar e continuar").

**Início da partida (coleta manual):** Shift+F6 começa **sem caminhão de recurso**. A base tem 40 bmat na fábrica, 6 caixas de munição, 30 camisas e 10 fuzis. A partir de ~5 s
nascem **3 trabalhadores** (um a cada ~3 s) — soldados sem arma, 1 camisa cada — que vão a pé ao campo de sucata, coletam (0,5 sucata/s cada, até 40 em mãos) e entregam na refinaria
(2 sucata = 1 bmat). Quando junta 100 bmat a fábrica constrói o caminhão de recurso (antes dos de suprimento e das caixas; ela **guarda** esses 100 bmat desde o começo); ele aparece
no campo, a coleta manual acaba e o painel perde a linha dela. Se o caminhão de recurso for destruído sem bmat nem sucata, a coleta **reativa**. Uma ordem sua a um trabalhador o tira
da coleta (a carga em mãos se perde) e ele volta sozinho depois de 60 s sem ordem; em combate (inimigo a menos de 35 m, tiro recente ou vida abaixo de 80%) eles pausam, e preso
por mais de 180 s o trabalhador larga a coleta. Trabalhadores mortos são repostos (1 camisa) enquanto a coleta for necessária; **não contam no limite de 12 do esquadrão** (o limite
deles é 3) e, enquanto não há caminhão de recurso, as camisas reservadas a eles não são gastas por Ctrl+1…4. Salvar durante a coleta descarta a sucata em mãos. Os números da coleta
são **proposta de design** (`CFG.COLETA`); não há dado do jogo para coleta a pé. `CFG.COLETA.manualStart = false` volta ao começo antigo (3 caminhões, 1100 bmat, 240 bmat de fábrica).
**[laboratório]** caminhada real, animação sem arma, spawn do caminhão no campo.

Numa partida (Shift+F6, Alt+F6 ou continuar), a guerra depende de uma cadeia de suprimentos, com custos e tempos tirados das tabelas do próprio jogo (`MECHANICS_STUDY.md`). O painel
(canto superior esquerdo) é **multilinha** (12–13 linhas, até ~222 caracteres): resumo da logística, fábrica (job, tempo restante ou a reserva de bmat), caixas prontas, uma linha por
depósito (base, bases avançadas, pontos seus), uma por caminhão (estado, carga, destino), a cadeia inimiga, a coleta e uma linha final com fuzis e bandagens. **[laboratório]**
(legibilidade, altura e largura nos vários zooms são gate visual).

1. **Sucata:** no começo, os trabalhadores a pé; depois um caminhão de recurso vai e volta sozinho entre o campo de sucata e a refinaria (100 por viagem).
2. **Refinaria:** 2 de sucata viram 1 bmat.
3. **Fábrica:** gasta bmat em caixas de **quatro produtos** — munição (80 bmat), camisas (80 bmat, 10 soldados por caixa), **fuzis** (100 bmat, 20 por caixa) e **bandagens**
   (80 bmat, 50 por caixa). No automático faz o que estiver mais em falta; Shift+L fixa um tipo. Tempos do jogo ×0,2. **Reserva de bmat:** por cada caminhão seu destruído ou ainda por
   construir, a fábrica guarda 100 bmat (só inicia uma caixa se sobrar além disso), para que o caminhão sempre consiga voltar; o painel mostra "Fábrica | guarda N bmat …".
4. **Caminhões de suprimentos (2):** levam até 15 caixas da fábrica ao depósito mais carente (a base, uma base avançada ou um ponto seu); L escolhe o destino do próximo. Camisas e fuzis
   só vão a base principal e bases avançadas ativas; o ponto sem base recebe munição e bandagens.
5. **Consumo:** recrutar gasta **uma camisa** do depósito onde o soldado nasce (o fuzileiro, também **um fuzil**); o **médico** só trata aliados feridos perto de um depósito com **bandagens**
   (gasta uma por tratamento efetivo); recarregar na base ou num ponto gasta munição daquele depósito (uma caixa = 6 recargas completas). Depósito vazio não recarrega e gera alerta.
   Ponto perdido perde o estoque.
6. **Emboscada:** inimigo a 15 m de um caminhão andando o danifica (alerta "caminhão sob fogo"); destruído, perde a carga e volta em 30 s por 100 bmat (reservados, ver 3).
7. **Cadeia inimiga real e interdição:** o inimigo tem uma **retaguarda fora do mapa** que segue as mesmas regras (sucata → refinaria 2:1 → receitas reais de munição e camisas → caminhão de
   15 caixas que custa 100 bmat para reconstruir). Com ondas automáticas, quando a retaguarda tem caixas suficientes (pelo menos 3, ou o que a frente pede) sai um caminhão colonial
   (BPTruckC; 90–200 m da base, pelo lado de onde vem a onda, rota checada no chão) que leva **as caixas de verdade** à frente; a frota é de 2 caminhões. Cada onda recebe uma
   **guarnição grátis de 5 soldados** mais os que a frente consegue equipar (1 camisa e 1/6 de caixa de munição por soldado); o que falta tira soldados dela ("faltou suprimento ao
   inimigo: a onda vem com N a menos", com quantos foram por comboios destruídos). Seus soldados a 15 m do caminhão o metralham; morteiro e granada também acertam caminhões (dos dois
   lados). Destruir um comboio carregado faz a frente perder a carga, rende 25 de mão de obra e a retaguarda reconstrói o caminhão (30 s, 100 bmat do inimigo). O painel mostra
   "INIMIGO: frente equipa N …" com a retaguarda e os comboios. A conta é fechada e auditável (`logi.eAudit()`/`logi.eReport()`): inicial + produzido = retaguarda + trânsito + pendente +
   frente + consumido + perdido. Como os soldados inimigos, o caminhão só aparece quando seus soldados o veem; não há marcador que o revele fora da visão. **[laboratório]** o BPTruckC real,
   a cadência das ondas e o piso grátis (`CFG.ECHAIN.free`) são calibração.

**Bases avançadas (Shift+J):** com o cursor dentro de um ponto **seu**, o 1º toque mostra o custo e o local ("Base avançada em A: 300 bmat (fábrica tem N). Shift+J de novo em 4 s
para construir"); o 2º toque, em até 4 s de tempo real, constrói. A base é uma `BPForwardBase1_C` nativa (300 bmat da fábrica, 1725 de vida, estoque de **15 slots**; caixa parcial
conta 1 slot) e o bmat só é debitado **depois** de o ator nascer validado. Condições: ponto seu, sem inimigo no anel, longe da base principal (≥ 30 m) ou perto de um ponto inimigo
(≤ 40 m), chão Landscape plano e livre (nunca telhado nem obra do mod), pelo menos 3 saídas livres, no máximo 3 bases, só com logística e fora do Assalto. Sem bmat suficiente o
2º toque registra um **pedido pendente**: a fábrica passa a guardar 300 bmat (depois da reserva de um caminhão destruído, que tem prioridade; painel "Fábrica | guarda 300 bmat para
base avançada em B") e constrói sozinha quando junta; o pedido cancela em 180 s, se o ponto deixar de ser seu, se aparecer inimigo no anel ou com Shift+J de novo em 4 s sobre o ponto
do pedido. As bases recebem camisas, fuzis, munição e bandagens por caminhão (L sobre a base) e são o único lugar, fora a base principal, onde nasce soldado: Ctrl+1…4/0 com o cursor
**perto** de uma base usa a mais próxima com estoque; com o cursor **dentro** de uma base, só nela (se faltar camisa/fuzil, recusa com o motivo, sem cair noutra); o recruta nasce numa
saída da base (rodízio). O painel ganha uma linha por base: `base A | camisas 12 | fuzis 3 | slots 3/15 | reforça: tudo` (ou `só sem fuzil (sem fuzis)`, `NÃO (sem camisas)`,
`INATIVA (ponto neutro)`). **Perda:** ponto capturado ou base destruída (morteiro inimigo, dano ×2) → a base some **uma** vez, o estoque se perde (alerta "BASE AVANÇADA B capturada:
perdeu N camisas e M fuzis"), o ator é destruído; recapturar o ponto **não** a traz de volta e reconstruir custa 300 de novo. Um ponto neutralizado deixa a base **inativa** (estoque
preservado, não reforça nem recebe). O inimigo não constrói bases. **[laboratório]** a classe `BPForwardBase1_C` nunca foi instanciada no jogo: caminho, vida, `CodeName`, `TeamId`,
saídas e ruína são o ensaio B1; sem ele o plano B visual (malha do mod) não existe.

Lugares: os prédios do mapa mais perto da base (em HomeRegionW: campo de sucata ao sul, refinaria e fábrica na cidade ao norte). Caminhões: os do mapa ou implantados explicitamente
com Alt+L, movidos pelo mod em linha reta, sem colisão. Sem discos verdes. A visão do comandante acompanha soldados, não caminhões isolados: uma malha invisível não prova que o ator
deixou de existir.

---

## 7. `## Limitações e verificação` (ACRESCENTA estes marcadores; ajustar quando o laboratório responder)

- A pilha v4 (economia com 4 produtos, cadeia inimiga real, reserva de bmat, save v2, coleta manual e bases avançadas) foi validada **offline** (lupa, Lua 5.4 e 5.5): lógica,
  contabilidade, contratos de save. **[preencher no laboratório]** o que foi visto no jogo (data, hash do `main.lua`, PID) e o que continua só offline.
- Equilíbrio (coleta, piso grátis da cadeia inimiga, custo e estoque das bases, `startRifles`) é **proposta** até o usuário jogar; ver `OPEN_DECISIONS.md`.
- O gate de estabilidade do contorno (cópias skinned) continua aberto até as cargas B2/A2; a v4 não mexe nesse código.
