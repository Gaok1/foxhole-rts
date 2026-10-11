# IA_LOGISTICA: cadeia inimiga e interdição estratégica (proposta isolada, 2026-10-09)

Agente: CLAUDE_IA_LOGISTICA. Trabalho todo offline. Não editei o `main.lua`, nenhuma doc compartilhada, o
laboratório nem o universal-modder. Esta pasta tem um módulo que entra no `main.lua` por um gerador com âncoras
únicas, os testes que executam o `main.lua` candidato **inteiro** em memória (lupa), o roteiro do laboratório e
os gotchas propostos.

**Estado honesto:** auditoria, design, conservação e efeito rastreável estão provados **offline**. Nada foi
validado ao vivo: o caminhão BPTruckC real, a rota, o desempenho, o equilíbrio de combate e o save no jogo
continuam como gates do LABORATORIO (`LAB_SCRIPT.md`). A task fica `[ . ]`.

## 1. Auditoria do main.lua atual: estoque real ou bônus abstrato

A auditoria pode ser executada: `test_base_audit.py` roda o `main.lua` atual, sem patch, e confirma
A1 a A6.

| # | O que existe hoje (linha do main.lua atual) | Classificação |
|---|---|---|
| A1 | `logi.convoyTick` (3029-3066): o caminhão inimigo chega à frente e soma `combat.cargo + 1`. O caminhão não carrega nada e nenhum estoque é debitado. Não há retaguarda, produção nem custo. `logi.convoySpawn` (2981) cria um comboio a cada `ECONVOY.every` = 35 s, sem condição. | **Abstrato**: carga criada do nada. Destruir o comboio só impede um +1 futuro. |
| A2 | `logi.waveCut` (3069-3079), chamado em `waveTick` (4205): cada onda gasta até `perWave`=2 cargas; cada carga que falta tira `cut`=2 soldados; o piso é 3. | **Abstrato**: é um contador. O efeito máximo é −4 soldados por onda. |
| A3 | `logi.start` (2681) faz `combat.cargo = cargo0 = 2`. `logi.snapshot` (3081) não grava `combat.cargo` nem comboio em trânsito. No continue, `logi.restore`→`start` devolve sempre 2 cargas. | **Abstrato, com bug**: o save/continue dá carga de presente ou apaga carga. |
| A4 | Tiro inimigo: `fire` e `areaStep` só descontam munição com `if ours` (1649, 1967). | **Abstrato**: munição inimiga infinita. **Não alterado** por esta entrega. |
| A5 | `spawnEnemies` (3480) não cobra nada. O tamanho da onda sai de uma fórmula (4201-4204). `ai.tick` (4121): `ai.mp` regenera 0,6/s por ponto inimigo e cada reforço custa 20 mp, sem material. | **Abstrato**. Esta entrega passa a exigir material para os soldados pagos (seção 3). `ai.mp` continua como mão de obra abstrata, como a do jogador (1399). |
| A6 | Morteiro inimigo sem custo (3152-3181). Trincheira e arame inimigos grátis (2179, 2400, 3689). | **Abstrato**. Não alterado. |
| R1 | Do lado do jogador: sucata, refinaria (2859), receitas com custo real (`CFG.LOGI`, 2438), caminhões com carga, depósitos, perda de carga quando o caminhão é destruído, débito de camisas e munição. Quando o inimigo captura um ponto, o depósito do ponto é zerado (2403). | **Real**. Conta como perda, nunca vai para o inimigo. |

Achado colateral, sem correção minha: a simulação da cadeia inimiga, que usa a mesma ordem do jogador
(fábrica antes da reconstrução), mostrou o seguinte. Com consumo contínuo, a fábrica gasta cada 80 bmat assim
que eles existem, e o caminhão de 100 bmat **nunca é reconstruído**. O lado do jogador tem a mesma ordem:
`logi.tick` chama `factoryStep` antes de `truckStep`, e o rebuild fica em 2792. Para o jogador isso continua
sendo **hipótese**, não testada. No inimigo, resolvi reservando bmat para o caminhão (seção 3).

## 2. Contratos com ECONOMIA e ESTRADAS (sem sistema paralelo)

- **Receitas e unidades:** o inimigo usa `CFG.LOGI.recipes` (o mesmo objeto do jogador; com a ECONOMIA
  aplicada, as mesmas entradas), `LOGI.time`, `LOGI.trip`, `LOGI.refine`, `LOGI.ratio`, `LOGI.cap`,
  `LOGI.truckCost`, `LOGI.rebuild` e `LOGI.reloads`. Os testes conferem contra `data/game_costs.txt`:
  RifleAmmo Cloth80/50 s; SoldierSupplies Cloth80, 10 un., 80 s; TruckC Cloth100, 900 HP, carga 15
  (= `ECONVOY.hp`, `LOGI.cap`, `LOGI.truckCost`). Receita sem custo ou tempo positivo, ou com `units`
  inválido, **recusa a cadeia inteira**: sem produção e sem comboio, `en.err` aparece no HUD. Erro de
  schema nunca vira custo zero.
- **Contabilidade:** é a mesma convenção da ECONOMIA. Caixas fechadas na retaguarda e na carga; unidades de
  produto na frente (`units` das receitas: munição = 1 caixa, camisas = 10). O débito acontece ao iniciar o
  job e a caixa só aparece ao concluir. A carga muda de dono só na chegada confirmada. Na destruição, a carga
  vira perda registrada, nunca volta ao estoque. Os produtos do inimigo são `CFG.ECHAIN.kinds = {ammo, shirts}`,
  o que a frente consome. Fuzis/bandagens da ECONOMIA não entram: a arma do inimigo é o mesh próprio do mod.
  Para ampliar, basta mexer em `kinds`/`eNeed`.
- **Rota:** o comboio anda só por `logi.drive(tr, dest, dt, speed)`, o mesmo driver do jogador, e só entrega
  quando o driver devolve `true` (chegada). Quando a ESTRADAS trocar o driver, o comboio inimigo herda a rota
  real sem mudar nada aqui. Contrato extra: o driver pode escrever `tr.routeStatus ∈ {rota_ausente, bloqueado,
  regiao_invalida}`. Depois de `ECHAIN.stuck` = 20 s nesse estado, o comboio volta carregado e a retaguarda só
  é creditada quando ele **chega** (`logi.eHome`), igual ao `returnCargo` da ESTRADAS e da ECONOMIA. Ator
  inválido ou `bActorIsBeingDestroyed` no caminho conta como perda explícita, nunca como entrega. Pendente da
  ESTRADAS: `logi.convoyRoute` ainda escolhe a retaguarda e a frente por traços de chão em reta (2949-2979).
  Essas paradas precisam virar paradas validadas do grafo.
- **Persistência:** `sv.collect` grava `elogi = logi.eSnapshot()` (v=1), aditivo, ao lado do `logi` da
  ECONOMIA. Nenhum userdata. A PERSISTENCIA precisa reconciliar esse campo no schema regional.

## 3. Design (o que o patch faz)

Tudo fica em `logi.e*` e `CFG.ECHAIN`. Os **locais de topo continuam 178**.

1. **Retaguarda fora do mapa, com as regras do jogador.** Um caminhão de recurso abstrato traz `LOGI.trip` = 100
   de sucata a cada `ECHAIN.trip` = 25 s. Refinaria a 4/s, razão 2:1, ou seja, no máximo 2 bmat/s como o
   jogador. Fábrica com um job por vez: escolhe o produto com menor estoque total sobre o alvo e para quando
   tudo passa de 2x o alvo. `bmat0` = 240, igual ao jogador.
2. **Comboio com carga real.** Só sai com caminhão livre (frota `ECHAIN.trucks` = 2 = `LOGI.supply`), com
   caixas na retaguarda e com pelo menos `minLoad` = 3 caixas (ou tudo o que a frente pede). A retaguarda só é
   debitada **depois** de o ator BPTruckC nascer válido. Spawn falho, classe ausente ou ator morrendo: nada sai
   e nada é debitado. Sem carga, tenta de novo em 5 s (`ECONVOY.retry`).
3. **Interdição.** Tiro, emboscada ou morteiro (`logi.hit` e `logi.blast` de sempre) executam `logi.eLose`.
   A carga vira perda **uma única vez** (`lostDone`), a frente não recebe nada e o caminhão entra na fila de
   reconstrução (`LOGI.rebuild` = 30 s e `LOGI.truckCost` = 100 bmat). A reconstrução **tem prioridade** sobre
   a fábrica quando não sobra caminhão livre. A recompensa de mão de obra ao jogador (+25) fica como estava.
4. **Frente.** Cada soldado **pago** leva 1 camisa e 1 carregamento (1/`LOGI.reloads` caixa de munição),
   como o recrutamento e a recarga do jogador. A onda (`logi.waveCut`) recebe `ECHAIN.free` = 3 soldados
   grátis e, além deles, só o que a frente consegue equipar. O débito (`logi.eCommit`) vem **depois** do spawn
   e cobre só os soldados pagos que nasceram. Os reforços pelos pontos (`ai.tick`) passam pelo mesmo limite
   (`eAfford`) e pelo mesmo débito (`eConsume`).
5. **Rastreabilidade.** Cada onda fica registrada em `logi.en.waves`: pedido, grátis, pagos, enviados,
   faltaram, produto limitante e **quantos faltaram por interdição** (`byCut`). O `byCut` é um contrafactual:
   o estoque perdido que ainda não foi "gasto" (`ghost`) mostra quantos soldados a frente teria equipado. O
   alerta da onda diz quantos faltaram por comboio destruído. `logi.eReport()` e `logi.eAudit()` funcionam no
   canal. O HUD mostra a frente, a retaguarda, os comboios na estrada e os perdidos. `combat.cargo` continua
   existindo como alias (= soldados que a frente equipa) para o painel da INTERFACE.
6. **Conservação.** Por produto: inicial + produzido = retaguarda + trânsito + pendente + frente + consumido +
   perdido. Também bmat0 + refinado/2 = bmat + gasto, e sucata colhida = sucata + refinada. Frota: livre +
   reconstruindo + na estrada = 2. Qualquer violação aparece em `logi.eAudit()`.
7. **Save/continue.** A carga em trânsito vira `pending`: o ator não é recriado e a carga sai no próximo
   comboio a partir da retaguarda. Caminhões na estrada voltam a ficar livres. A validação é completa (números
   finitos ≥ 0, frota, job e o **próprio razão do save fechando**) e a restauração **substitui**, nunca soma.
   O `sv.ser` grava 3 casas decimais, por isso a tolerância é `ECHAIN.tol` = 0,05 e a sobra entra nos termos
   de origem. Save inválido ou legado (sem `elogi`) recomeça do estoque de cenário com aviso; é o mesmo
   comportamento antigo do `cargo0`, mas agora registrado no razão como "inicial".
8. **Inalterado de propósito:** assalto (`combat.mode == "assault"`) e partidas sem logística (`logi.on`
   falso) mantêm o comportamento abstrato antigo, sem consumo. Onda manual F4, guarnição do assalto, munição
   no tiro, morteiro e fortificações inimigas também continuam abstratos (A4-A6).

**Bônus abstratos que restam, todos explícitos:** guarnição de 3 grátis por onda; fórmula do tamanho pedido
da onda; `ai.mp`; munição inimiga no tiro; morteiro e fortificações inimigas; retaguarda fora do mapa, que não
pode ser atacada; e o estoque de cenário inicial da frente (2 caixas de munição, 10 camisas), que está no razão.

## 4. Testes offline: comandos e resultado (saída completa em `TEST_OUTPUT.txt`)

Da raiz do repositório (PowerShell):

```powershell
$env:PYTHONPATH='D:/tools/pylibs'
python data/parallel/logistics_ai/build_patch.py          # gera patches + main_candidate.lua; main.lua intacto
python data/parallel/logistics_ai/test_logistics_ai.py    # PASS nos 2 candidatos
python data/parallel/logistics_ai/test_orders_candidate.py  # PASS: 4 execuções
python data/parallel/logistics_ai/test_base_audit.py  # PASS: A1-A6 no main atual
python tools/check_globals.py data/parallel/logistics_ai/main_candidate.lua  # sem saída = OK
```

- `test_logistics_ai.py` executa o `main.lua` candidato inteiro duas vezes: main+IA e main+ECONOMIA+IA.
  Cobre custos do jogo; estoque de cenário; recusa por schema (custo 0 e tempo ausente); produção com débito
  no início; fábrica parando em 2x; comboio sem caminhão, sem carga, com spawn falho ou com ator morrendo, sem
  fantasma e sem débito; entrega única; perda única com tiro e morteiro em seguida; reconstrução que espera
  bmat; ator inválido no caminho; rota ausente (volta carregado, crédito só na chegada); onda via `waveTick`
  real com spawn falso; spawn recusado sem débito; reforço via `ai.tick` real; assalto e partida sem
  logística; save via `sv.ser`/`sv.parse` e `sv.collect`/`sv.load` reais; repetir restore sem duplicar;
  save adulterado ou legado; **25 sementes × 600 passos aleatórios** com `eAudit` depois de cada passo
  (conservação, sem negativo, frota constante); e quatro partidas completas por `waveTick`.
- Partidas determinísticas (luta de 45 s por onda, 6 soldados nossos; formato `onda:enviados/pedidos`,
  `[iN]` = N atribuídos à interdição):

```
controle                 1:6/6 2:6/6 3:7/7 4:8/8 5:9/9 6:10/10 7:10/10 8:11/11 9:12/12 10:13/13   (5 comboios, 0 perdidos)
interdição total         1:6/6 2:6/6 3:7/7 4:3/8[i5] 5:3/9[i6] 6:3/10[i7] 7:3/10[i7] 8:3/11[i5] 9:3/12[i9] 10:3/13[i1]  (4 de 4 destruídos)
interdição 0-420 s       ... 8:3/11[i5] 9:3/12 10:13/13   (recuperação depois que o corte para)
escassez (sem bmat)      1:6/6 2:6/6 3:7/7 4..10: 3 (piso)   (a partida continua até o fim, razão OK)
```

  Leitura: o corte reduz de forma rastreável os soldados que a onda recebe (alerta + `byCut` + perdas no
  razão), não só um contador. O "venceu=true" dessas linhas **não diz nada de equilíbrio**, porque o modelo
  de luta mata toda onda em 45 s.
- `test_orders_candidate.py` roda `tools/test_orders.py` sem mudança no main puro (controle), em main+IA e
  em main+ECONOMIA+IA. Troca um único bloco, o do comboio inimigo, cujo contrato abstrato foi removido; o
  bloco novo está em `test_orders_convoy_block.lua`. Também roda `economy/test_integration.py` sobre
  main+ECONOMIA+IA: PASS.
- Sintaxe OK; 178 locais de topo nos três; `check_globals` limpo em main+IA e main+ECONOMIA+IA.

**O que NÃO foi testado (gates ao vivo):** spawn e movimento do BPTruckC com o patch; LOS e alertas;
desempenho por quadro; o efeito real na frente com soldados de verdade; equilíbrio (o piso de 3 com
interdição total pode deixar o jogo fácil demais, e a calibração é do laboratório); save/continue real no
disco com o comboio na estrada; e a integração com o driver da ESTRADAS (que ainda não existe).

## 5. Ordem de aplicação (para o coordenador)

1. ESTABILIDADE (já integrada).
2. **ECONOMIA** (`data/parallel/economy/build_patch.py`).
3. **IA_LOGISTICA**: `build_patch.build(source)` ou `logistics_ai.patch` (diff sobre main+ECONOMIA).
   Nenhuma âncora depende da ECONOMIA: `logistics_ai_base.patch` aplica sobre o main puro, e os dois caminhos
   foram testados. As âncoras são únicas e fail-closed; só a do HUD é opcional.
4. INTERFACE: testei num scratch a IA aplicada **depois** do `painel.patch`. Funciona: a âncora do HUD é
   pulada e o painel continua lendo `combat.cargo`. Recomendo o painel usar `logi.eHud()`.
   **Conflito que não é meu:** a ECONOMIA falha sobre a INTERFACE (âncora `table.concat(deps, " | "), foe)`).
5. Trocar em `tools/test_orders.py` o bloco "enemy convoy" pelo de `test_orders_convoy_block.lua` e incluir
   `test_logistics_ai.py` na bateria. Não há tecla nova, então TESTE_MANUAL e teste de teclas ficam iguais. O
   README precisa descrever a cadeia inimiga e o alerta novo.
6. Depois: o driver da ESTRADAS (com `routeStatus`) e o schema da PERSISTENCIA (`elogi`).

## 6. Riscos

- **Equilíbrio:** a interdição total leva as ondas 4 a 10 ao piso de 3 (antes o máximo era −4 por onda). Os
  parâmetros de calibração ficam em `CFG.ECHAIN` (`free`, `front0`, `want`, `trip`, `minLoad`) e são
  comparados no robô (roteiro L9).
- O comboio continua em reta e sem colisão (driver atual) até a ESTRADAS.
- `ECHAIN.trip` é um parâmetro abstrato de retaguarda fora do mapa. A retaguarda não pode ser atacada; atacar
  as instalações inimigas fica para depois.
- No continue, a carga em trânsito volta a sair da retaguarda, e não do ponto onde o caminhão estava. Isso
  conserva a carga, mas atrasa a entrega.
- Diagnóstico `byCut`: é uma atribuição contrafactual, não uma medida física.

## 7. Universal-modder

Consultei no início: `um kb search` com logistics, supply, enemy ai, conservation e foxhole; a nota Foxhole,
itens 25, 30, 32-38 (TruckC/TruckW spawn, rede de estradas, ruína × ativa, IsValid × spawn). "Rastrear antes
de reinventar": o Foxhole é só online e não tem bots nem IA de logística para rastrear. A cadeia própria usa
as **tabelas reais** do jogo (custos, carga e HP do TruckC). Gotchas propostos em `PROPOSED_GOTCHAS.md`;
não editei a nota.

## Arquivos

`logistics_ai.lua` (módulo inserido), `build_patch.py`, `logistics_ai.patch`, `logistics_ai_base.patch`,
`main_candidate.lua` (só para inspeção/check_globals; **não copiar** sobre o main), `test_logistics_ai.py`,
`test_orders_candidate.py`, `test_orders_convoy_block.lua`, `test_base_audit.py`, `TEST_OUTPUT.txt`,
`t_logistics_ai.lua` (sonda de canal para o laboratório, não executada), `LAB_SCRIPT.md`,
`PROPOSED_GOTCHAS.md`.
