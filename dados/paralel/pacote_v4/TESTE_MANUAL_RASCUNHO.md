# TESTE_MANUAL_RASCUNHO — itens novos e alterados para entrada real (pilha v4)

Rascunho para a task INTEGRACAO fundir em `TESTE_MANUAL.md` **depois** do laboratório. Nada foi aplicado lá. Texto, teclas e mensagens conferidos contra o candidato
(candidato **v4.1** `62245d23…598f` = `candidato_v4` `025e3b80…aab0` + `v4_1/v4_1.patch`). Como em `AGENTS.md`, o agente **não** injeta teclado nem mouse: tudo abaixo é do usuário. O laboratório já cobre pelo canal
(`ROTEIRO_LOTE.md`) a lógica por trás de cada item; aqui fica o que só a entrada real mostra (tecla, cursor, mouse, câmera, aparência, tempo de jogo real).

Como ler as colunas: **Esperado** é o que deve aparecer; **Falha se** é o que conta como defeito (anotar a mensagem exata do painel e a hora; o log fica em
`D:\FoxholeLab\Foxhole\War\Binaries\Win64\ue4ss\UE4SS.log`, linhas `[FoxholeRTS]`; toda mensagem de `notify` também vai para o log). O que é **decisão de balanço** (e não defeito) está em
`DECISOES_EM_ABERTO.md`.

## Preparação acrescentada ao topo do arquivo (SUBSTITUI o parágrafo "Preparação")

Abra a cópia de laboratório (Steam aberto). O mod entra no mapa e liga o modo RTS sozinho; a ajuda de teclas aparece no canto inferior esquerdo por 40 s (F5).
Os testes da cadeia usam HomeRegionW; as bases avançadas e o Continuar com instalações pagas usam CallumsCapeHex (o laboratório troca o mapa com `map.txt`; peça o mapa certo
antes de começar). Num hex sem instalações ativas, Alt+L implanta refinaria, fábrica e os 2 caminhões de suprimento; Shift+F6/Alt+F6 recusam a partida sem isso
("Partida não iniciada: …"), o que **não** significa que os prédios não existam como ruínas.

**O que mudou no começo da partida:** a partida logística (Shift+F6) já **não** tem caminhão de recurso. Começa com bmat 40, 30 camisas, 10 fuzis e 6 caixas de munição, e
**3 trabalhadores desarmados** (a partir de ~5 s) coletam a sucata a pé até a fábrica juntar 100 bmat e construir o caminhão. A **mão de obra** só paga morteiro, barreira, trincheira,
caixa, posto de socorro e arame (e o recrutamento **no Assalto**). Recrutar numa partida logística custa camisa (e fuzil, para o fuzileiro).

Tempo real: a partida de estoque 40 bmat leva **vários minutos** até o 1º caminhão de recurso, e uma base avançada (300 bmat) leva mais; reserve ~15 min só para chegar aos itens 11c–11h
sem ajuda. Se o laboratório já preparou um estado (bmat creditado), a nota diz.

---

## A. Itens existentes que MUDAM (cada linha SUBSTITUI a linha de mesmo número em `TESTE_MANUAL.md`)

| # | Faça | Esperado | Falha se | OK? |
|---|---|---|---|---|
| 2 | Shift+F6 (em HomeRegionW, ou em CallumsCapeHex depois de Alt+L) | Alerta "NOVA PARTIDA (…): vença 10 ondas…" e `ondas automaticas: true` (o Shift+F6 já liga as ondas); 6 soldados selecionados com contorno amarelo; três anéis (A, B, C). Aos ~5 s aparece o **1º trabalhador** (soldado **sem arma**, perto da base) e os outros dois a cada ~3 s, cada um **gastando 1 camisa** (camisas 30 → 27 no painel). Painel: `Fábrica \| guarda 100 bmat para reconstruir caminhão (bmat 40)` e uma linha `coleta manual: N trabalhadores \| x/100 bmat para o caminhão \| y sucata em mãos` | trabalhador em T-pose, com arma, preso no chão/telhado ou sem contorno ao selecionar; mais de 3; camisas não baixam; **a partida recusa sem motivo** | |
| 8 | Ctrl+1 / Ctrl+2 / Ctrl+3 / Ctrl+4 (cursor no chão, longe de bases) | Recruta fuzileiro / metralhador / atirador / médico **na base principal**, perto da saída; o alerta diz `recrutado … em base (-1 camisa, -1 fuzil) \| camisas N, fuzis M` (o fuzil só para o fuzileiro; metralhador, atirador e médico gastam só a camisa). **A mão de obra do painel não muda.** Com 0 fuzis: Ctrl+1 recusa (`sem fuzis em base …`) e Ctrl+2/3/4 ainda funcionam | desconta mão de obra; nasce em telhado/parede; recruta sem estoque; recusa sem mensagem | |
| 9 | Ctrl+1 com o cursor dentro de um ponto seu **sem** base avançada | **Não** nasce no ponto: nasce na base principal (um ponto comum não reforça; `CFG.SPAWN.pointSpawn=false`). Mensagem de nascimento cita a base, não o ponto | o recruta nasce no ponto | |
| 11 | J com o cursor no chão livre (sem Shift) | Novo ponto de controle (anel), até 5 | não cria; cria com Shift apertado (ver 11a) | |
| 12e | Jogar ≥ 90 s (as ondas automáticas já ligam sozinhas com Shift+F6; Shift+F4 as **desliga**), com trabalhadores em campo, fechar o jogo, reabrir e apertar Ctrl+F6. **Antes do Ctrl+F6, em CallumsCapeHex, não repita Alt+L** | Alerta "há uma partida salva (…): Ctrl+F6 continua, Shift+F6 começa outra" ao ligar o RTS; Ctrl+F6 traz soldados, pontos, construções, estoques e a **infraestrutura paga** (refinaria, fábrica e caminhões voltam de graça, sem débito novo). Os trabalhadores voltam e retomam a coleta (a carga que levavam foi descartada, aparece só no log) | duplica soldados/caminhões ao repetir o Ctrl+F6; cobra bmat de novo; recusa um save bom | |
| 12s | Nova partida (Shift+F6), depois Ctrl+L várias vezes | A câmera passa por fábrica, refinaria, campo de sucata e **cada caminhão que existe**. Ao início só há os 2 de suprimento; o de recurso entra na lista quando a fábrica o constrói. Ctrl+L **não** visita bases avançadas (use Q/E, que passam pelos pontos) | câmera vai ao vazio, ou para num caminhão destruído | |
| 12t | L com o cursor num ponto seu; olhar a 2ª linha do painel; repetir com o cursor dentro de uma base avançada (11e) | Painel: "próximo caminhão vai para o ponto X"; depois `caminhão entregou em X: N munição, N camisas, N fuzis, N bandagens` e o estoque sobe. **Ponto comum recebe só munição e bandagens** (camisas e fuzis só chegam à base principal e à avançada) | camisas/fuzis aparecem num ponto sem base; estoura 15 slots numa base | |
| 12u | Shift+L (várias vezes) | Prioridade da fábrica cicla: `automático` → `munição` → `camisas` → `fuzis` → `bandagens` → `automático` (painel, linha `LOGÍSTICA \| … \| prioridade …`). O painel de estoque mostra `Fuzis: fábrica N caixas \| bandagens: fábrica N caixas` na última linha | só cicla 3 estados; produto fora da lista | |
| 12v | Nova partida (as ondas já ligam); no alerta "COMBOIO INIMIGO a caminho da frente (…)", Espaço e mandar soldados para o meio da rota | Soldados atiram no caminhão; `COMBOIO INIMIGO DESTRUÍDO (+25): …`; na onda seguinte `faltou suprimento ao inimigo: a onda vem com N a menos (…)`. O 1º comboio sai ~20 s depois do início das ondas. Ver também 12v2 | a perda é contada duas vezes; comboio sem carga; bounty repetido | |
| 12x | No laboratório em CallumsCapeHex **sem** implantar: Shift+F6 e Alt+F6 | Os dois recusam: `Partida não iniciada: … Alt+L tenta implantação nos locais nativos.` (falta de instalações/caminhões ativos); não apagam soldados existentes nem iniciam uma cadeia fictícia (o Assalto também precisa da cadeia: `logi.ready`) | apaga a partida atual; inicia sem cadeia | |
| 12y | Em CallumsCapeHex, antes da partida: Alt+L; repetir; depois Shift+F6 | `IMPLANTAÇÃO: -1000 bmat do cenário; saldo 0` (a v4 cobra **1000**, não 1100: refinaria 400 + fábrica 400 + **2** caminhões de suprimento 100; o de recurso nasce da coleta). Repetir: `Cadeia já implantada`. A partida inicia com refinaria, fábrica e 2 caminhões reais | cobra 1100, repete a cobrança, ou cria 3 caminhões | |
| 12l | Deixar um soldado cair abaixo de 30% com um posto de socorro (Ctrl+8) por perto | Alerta "ferido recua sozinho"; ele vai à barraca e volta a lutar curado. **Se não houver barraca, vai ao ponto seu mais perto** (o ponto cura 2 HP/s sem supressão) | | |

---

## B. Itens NOVOS

### B1. Shift+J: base avançada (11a–11h; colunas iguais às de cima)

Pré-condição: partida logística em CallumsCapeHex com **um ponto seu a ≥ 30 m da base principal** (ou a ≤ 40 m de um ponto inimigo) e nenhum inimigo no anel do ponto. Para
chegar aqui, capture um dos pontos (item 7). "Dentro" de um ponto ou de uma base = a ≤ 5 m do centro (`CFG.POINT_RADIUS` 500 cm). A construção usa **dois toques em até 4 s de relógio real** (a pausa do jogo **não** pára esse relógio).

| # | Faça | Esperado | Falha se | OK? |
|---|---|---|---|---|
| 11a | Shift+J com o cursor no chão livre, depois sobre um ponto **neutro** ou **inimigo**, depois dentro de um ponto seu | Chão livre: `Shift+J: ponha o cursor dentro de um ponto de controle seu`. Ponto neutro/inimigo: `o ponto X não é seu`. Dentro do seu: custo e instrução (11c). **Nenhum ponto novo** aparece (só J cria ponto) e o número de anéis não muda | cria um anel (o `plain()` não segurou o J); debita bmat numa recusa | |
| 11b | Shift+J em ponto seu **perto da base principal** (< 30 m) e sem ponto inimigo a ≤ 40 m | `ponto X perto demais da base (mín. 30 m) e longe de pontos inimigos (40 m)`; nada criado | cria a base | |
| 11c | Com bmat livre ≥ 300 (descontados 100 por caminhão destruído): Shift+J sobre um ponto seu longe da base (1º toque); de novo em ≤ 4 s | 1º: `Base avançada em X: 300 bmat (fábrica tem N). Shift+J de novo em 4 s para construir`. 2º: `BASE AVANÇADA X construída (-300 bmat; fábrica N). Mande caminhões com camisas e fuzis (L sobre ela)`. A construção nativa (estrutura de 1725 HP) aparece no ponto, **de pé no chão, de frente para a base ou para o ponto inimigo**, sem afundar nem flutuar. Painel ganha `base X \| camisas 0 \| fuzis 0 \| slots 0/15 \| reforça: NÃO (sem camisas)` | passados 4 s o 2º toque vale como 1º; ator torto, enterrado, sem colisão; bmat debitado sem a base; duas bases no mesmo ponto | |
| 11d | Com **pouco** bmat: Shift+J + Shift+J | `Base avançada em X: 300 bmat, faltam N …` e depois `pedido de base avançada em X registrado: …; a fábrica guarda 300 bmat (até 180 s)`. Painel: `Fábrica \| guarda 300 bmat para base avançada em X (bmat N)` (se também há caminhão destruído: `… para reconstruir caminhão e base avançada em X`; **o caminhão tem prioridade**). Constrói sozinha ao juntar 300 livres. Shift+J no mesmo ponto: `pedido pendente em X (a fábrica guarda 300 bmat). Shift+J de novo em 4 s cancela`; repetido: `pedido de base avançada cancelado: a fábrica volta a produzir`. Cancela sozinho em 180 s (tempo de jogo), se o ponto deixa de ser seu ou com inimigo no anel | a fábrica fica **sem produzir munição** durante os 180 s e a base não vem; o pedido não cancela | |
| 11e | Quando houver a base: L com o cursor sobre ela; esperar a entrega. Depois Ctrl+1 com o cursor **dentro da base** | Caminhão leva o que cabe nos 15 slots (caixa parcial = 1 slot); camisas e fuzis sobem na linha do painel. O recruta nasce **na saída da base** (não em telhado/parede), gasta 1 camisa e 1 fuzil **dela** e a linha passa a `reforça: tudo`. Shift+J sobre um ponto que **já tem** base só mostra a linha dela (`BASE AVANÇADA X: base X \| camisas … \| slots …`), sem construir | nasce longe, na base principal, com o cursor dentro da base avançada; gasta estoque de outra | |
| 11f | Com 1+ base avançada de pé: Ctrl+1 com o cursor **fora** de qualquer base; depois num ponto seu **sem** base | Fora: nasce na base **mais próxima do cursor ou do esquadrão com estoque** (principal ou avançada). Ponto sem base: nasce na principal; **o ponto não reforça**. Com o cursor **dentro** de uma base **sem estoque**: recusa com motivo (`sem camisas em base avançada X; mova o cursor para fora das bases …`), **sem cair em silêncio** noutra | cai noutra base sem avisar | |
| 11g | Perda: deixar um inimigo tomar o ponto da base avançada, ou o morteiro inimigo cair em cima | Alerta `BASE AVANÇADA X capturada: perdeu N camisas e M fuzis` (ou `destruída`) **uma vez**; a estrutura **some** (sem ruína, sem ator residual); o painel perde a linha; retomar o ponto **não** traz a base de volta. Sob morteiro antes de cair: `base avançada X sob fogo` | a estrutura fica no mapa; alerta repetido; estoque continua | |
| 11h | Com 1+ base avançada: jogar ≥ 90 s, fechar, abrir, Ctrl+F6 | Base de volta no **mesmo lugar**, mesma vida e estoque, **uma só** por ponto. Repetir Ctrl+F6: nada duplica. Se a posição não valida mais: `Continuar recusado: base avançada salva não foi refeita (…); nada mudou` e a partida atual e o save ficam | duplica a base; sobe sem estoque; recusa e apaga o que existia | |
| 11i | Pausa (Pause) entre o 1º e o 2º toque do Shift+J, esperar > 4 s, apertar o 2º | O 2º toque vale como **1º** (o relógio é de tempo real, não de jogo). Decisão aberta em `DECISOES_EM_ABERTO.md`; anotar o que preferir | | |
| 11j | Alt+F6 (Assalto), Shift+J num ponto seu | `bases avançadas só numa partida com logística (fora do Assalto)`; recrutar usa mão de obra | | |

### B2. Coleta manual e trabalhadores (C1–C8 do roteiro)

| # | Faça | Esperado | Falha se | OK? |
|---|---|---|---|---|
| 12z | Partida nova: acompanhar os 3 trabalhadores até o 1º caminhão de recurso | Eles caminham ao campo de sucata, **ficam parados coletando** (mãos vazias, sem arma), voltam à refinaria e entregam; a linha `coleta manual: …` mostra `x/100 bmat para o caminhão` subindo e `y sucata em mãos`. Quando bmat chega a 100 a fábrica **constrói o caminhão de recurso**, que aparece no campo, **no chão**, e a mensagem `caminhão de recurso pronto: coleta manual encerrada` dispara; a linha da coleta some do painel e os trabalhadores ficam soltos no esquadrão. Anote o tempo total e as distâncias reais (decide `DECISOES_EM_ABERTO.md`) | trabalhador em T-pose, com arma, parado na base, preso numa parede/neve ou em fila infinita; caminhão em telhado | |
| 12z2 | Selecionar **um trabalhador** (clique) e dar ordem de marcha (botão direito) | Ele **larga a coleta** (a carga que levava se perde; log `coleta manual: trabalhador sai da coleta (…)`), anda ao ponto e para. **Depois de ~60 s sem ordem nova** ele volta sozinho à coleta (se ela ainda for necessária) | volta antes dos 60 s e anula a ordem; fica parado para sempre | |
| 12z3 | Caixa de seleção (arrastar) que pega trabalhadores e soldados; botão direito no chão | Todos marcham; os trabalhadores saem da coleta (um aviso de perda de carga no log por quem a levava) | trabalhador atira, ou não se mexe | |
| 12z4 | Durante a coleta, deixar o 1º inimigo (F4) chegar perto do campo | Os trabalhadores **pausam** (e largam a carga após ~60 s seguidos de combate) e voltam quando a área fica calma (sem tiro há 8 s, inimigo a > 35 m). Se um morre, a base repõe outro por **1 camisa** | foge e nunca volta; mais de 3 vivos por vez | |
| 12z5 | Matar o caminhão de recurso (morteiro inimigo ou soldados; `Ctrl+5` perto dele destrói também) com bmat/sucata zerados | A coleta manual **reativa** (`COLETA MANUAL: sem caminhão de recurso; trabalhadores da base coletam sucata até a fábrica fazer o caminhão`); a fábrica reserva 100 bmat e reconstrói | a partida trava sem bmat e sem caminhão | |
| 12z6 | Ctrl+0 selecionar todos (inclui trabalhadores); olhar o contorno e o painel de seleção | Trabalhadores selecionáveis como qualquer soldado; contorno amarelo igual; ao deselecionar, apaga | contorno amarelo permanece em quem não está selecionado | |
| 12z7 | Derrota por falta de tropa: perder todos os soldados de **combate** com 0 camisas na base/fábrica/caminhões (opcional, difícil de provocar; o laboratório testa pelo canal) | Os 3 trabalhadores **não** contam como combate; `DERROTA` só quando não resta soldado de combate **e** nenhuma camisa (nenhuma base, fábrica ou caminhão). Com camisas, **não** perde | derrota com camisas na fábrica | |

### B3. Cadeia do jogador: produtos e médico

| # | Faça | Esperado | Falha se | OK? |
|---|---|---|---|---|
| 12aa | Shift+L até `fuzis`, esperar a produção, mandar o caminhão (L) à base; repetir com `bandagens` | Receita → produção → transporte → depósito para os 4 produtos. Unidades: caixa de fuzis = 20, de bandagens = 50, de camisas = 10. A última linha do painel mostra `Fuzis: fábrica … \| bandagens: fábrica …`, e por depósito `N fuzis, M bandagens` | produto some no transporte; o painel não mostra o estoque | |
| 12ab | Ctrl+4 (médico) com **0 bandagens** na base; ferir um soldado (deixar levar tiro) e ficar com o médico ao lado | O médico **vai até o ferido mas não trata** (não há bandagem). Depois de produzir/entregar bandagens num depósito a ≤ 5 m do médico (base, base avançada ou ponto seu: `CFG.POINT_RADIUS` = 500 cm), ele cura (+12 por tratamento, a cada 1,5 s) e o estoque de bandagens do painel **cai 1 por tratamento** | cura sem bandagem; cura longe (> 5 m) de qualquer depósito com bandagens | |
| 12ac | Com a fábrica em `automático`, observar 3–5 min | A fábrica **não gasta os 100 bmat de reserva** do caminhão destruído em caixa; o caminhão volta quando há 100; a fábrica **não** para de fazer munição por tempo indefinido por causa do pedido de base (180 s no máximo) | fome de munição prolongada | |

### B4. Painel

| # | Faça | Esperado | Falha se | OK? |
|---|---|---|---|---|
| 12ad | Olhar o painel com logística ativa em vários zooms e resoluções; abrir e fechar a ajuda (F5); pausar | Painel de **várias linhas** (cerca de 12–13: logística, fábrica, pronto, um depósito por local, uma linha `base …`/`base X …` por base, caminhões, `INIMIGO …`, `coleta manual …`, atalhos), **sem cortar** estoques nem veículos, sem sobrepor a ajuda nem os alertas nativos do jogo. Pausado: prefixo `PAUSADO \|`; velocidade 2x/3x: prefixo `2x \|` | texto cortado, em cima da ajuda, ou escondido silenciosamente | |
| 12ae | Painel durante a cadeia inimiga | Linha `INIMIGO: …` mostra `frente equipa N`, carga do comboio e `piso grátis 5/onda` | linha ausente com ondas ligadas | |

### B5. Salvar e continuar, recusas (V1–V12 do roteiro)

| # | Faça | Esperado | Falha se | OK? |
|---|---|---|---|---|
| 12af | Ctrl+F6 **com a partida rodando**, mesmo save, duas vezes seguidas | Idempotente: nenhum soldado, caminhão ou base a mais; estoques não dobram | duplica | |
| 12ag | Trocar `save.txt` por um arquivo corrompido ou de outra região (peça ao laboratório, ou use o `save.txt.bak` de outro mapa) e apertar Ctrl+F6 **durante uma partida** | `Continuar recusado (partida atual e save preservados): motivo`; **nada** da partida atual muda; o arquivo continua como está | apaga a partida atual; some o save | |
| 12ah | Save com a seção `elogi` removida/adulterada (laboratório) e Ctrl+F6 | O jogo abre normalmente, com `CADEIA INIMIGA REINICIADA (motivo): estoque de cenário` por 10 s; o resto (soldados, estoques, bases) volta | recusa o save inteiro | |
| 12ai | Fechar o jogo durante um autosave não é testável à mão; em vez disso, **perder** (ou vencer) a partida e olhar a pasta `FoxholeRTS` | `save.txt`, `.tmp`, `.bak` e `.corrupt` removidos | sobra algum | |
| 12aj | Ver `INCOMPLETA: …; autosave suspenso` só se aparecer sozinho; **não provocar** | Se aparecer, Ctrl+F6 tenta de novo; Shift+F6 começa outra; o autosave não sobrescreve o save bom | o autosave grava por cima | |

### B6. Outros

| # | Faça | Esperado | Falha se | OK? |
|---|---|---|---|---|
| 12v2 | Ctrl+5 (morteiro) com o cursor sobre um **comboio inimigo carregado** | Aviso, 3 explosões após ~2,5 s; `COMBOIO INIMIGO DESTRUÍDO (+25)` **uma vez**; um 2º morteiro sobre o caminhão já destruído não conta de novo | perda dupla | |
| 12ak | Alt+F6 (Assalto, depois de Alt+L no hex) e recrutar | Recrutar usa **mão de obra** (como na v0.9; gasta também a camisa do depósito), sem comboio inimigo e sem Shift+J. A cadeia do jogador roda como na partida normal, então a **coleta manual com trabalhadores também vale no Assalto** (o código permite o trabalhador nesse modo; **[laboratório]** não visto ao vivo, anotar) | comboio inimigo no Assalto; Shift+J constrói | |
| 12al | Partida nova, deixar a 1ª onda chegar (as ondas já ligam sozinhas) e contar os inimigos | O tamanho da onda usa **só os soldados de combate** (v4.1): os 3 trabalhadores não a aumentam, e o aviso "próxima onda em … (esquadrão N …)" mostra N sem eles. Anotar quantos inimigos nasceram e quantos soldados de combate seus havia (compare com o mesmo número sem trabalhadores) | onda maior por causa dos trabalhadores; aviso conta os trabalhadores | |
| 12al2 | Com os 3 trabalhadores no campo de sucata (longe do esquadrão de combate) e o esquadrão num ponto, deixar chegar uma onda e um reforço inimigo | As ondas e o reforço vêm do lado/pontos inimigos em relação ao **esquadrão de combate** (v4.1: `squadCenter()` só conta combatentes); os trabalhadores no campo não puxam as ondas para lá. Sem nenhum combatente vivo, vale o centro de todos | ondas aparecendo sempre perto do campo de sucata | |
| 12am | F11 (limpar) com trabalhadores e uma base avançada de pé; depois Shift+F6 | F11 remove soldados, inimigos, barreiras, pontos **e** destrói a base avançada (sem ator residual no mapa); a partida nova começa sem resíduo | estrutura da base ou trabalhador sobra no mapa | |

---

## C. Itens do arquivo atual que continuam como estão

1, 1b, 3, 3b, 4, 5, 6, 6b, 7, 10, 12 (Ctrl+5 no Assalto/normal), 12b–12d, 12f–12k, 12m–12r, 12w, 13–17 (nenhum depende do que a v4 mexe). A v4 **não** altera o contorno, a animação nem a câmera
(diff por função, 105 hunks); a estabilidade de 3 ciclos de contorno **continua pendente** do gate do `COMO_INTEGRAR.md` §2, não deste arquivo.

## D. Registro

Quando cada item for executado, marque na coluna OK? e cole as mensagens exatas das falhas. O laboratório preenche também `MODLOG_RASCUNHO.md` com os números medidos.
