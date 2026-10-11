# BASES_AVANCADAS — especificação (etapa 1, sem código de patch)

Agente BASES_AVANCADAS, 2026-10-09. Só leitura do repositório. Esta pasta contém este arquivo e quatro sondas
**somente-leitura** para o LABORATORIO (`probes/A1..A4`, sintaxe conferida com Lua 5.4, **não executadas**).
Nada foi tocado em `main.lua`, docs compartilhadas, outras pastas, laboratório ou jogo.

## 0. Base, escopo e legenda

- **Código lido:** `data/parallel/integration_rehearsal/candidate_v2/main.lua` (SHA256 `a93c1531…eda6`, a pilha
  ECONOMIA > IA_LOGISTICA v2 > reserva de bmat > INTERFACE v2 > PERSISTENCIA v2, **ainda não aplicada ao `main.lua`
  real**). Todas as linhas citadas são desse candidato. A etapa 2 só faz sentido **depois** da pilha integrada
  (depende de `rifle`/`medical` nos depósitos, de `logi.rebuildReserve`, de `sv.validate` v2 e do `logi.hudLine` v2).
- **Decisão de design de partida** (ROADMAP, "de onde vêm os soldados"): soldados nascem em estruturas de spawn;
  base principal + bases avançadas (`ForwardBase1`, 300 bmat); recrutar gasta 1 camisa + a arma da função do
  estoque da própria estrutura; caminhões levam camisas/armas; mão de obra abstrata só no Assalto. Trabalhadores
  (coleta manual) são de outro agente: aqui só existe a interface "onde nasce" (§4.3).
- **Legenda de confiança.** `[DADO]` lido do cliente (`data/`); `[OBS]` observado em sonda de lote anterior;
  `[INF]` inferência (nome, analogia, caminho do pak) **não verificada em ator carregado**; `[PROP]` proposta de
  design deste documento; `[?]` desconhecido, depende de sonda.
- bmat = `Cloth` (`MECHANICS_STUDY.md`). "Camisa" = `SoldierSupplies`; no depósito do mod ela é contada em
  **unidades**, e a caixa traz 10 (`CFG.LOGI.recipes.shirts.units`); fuzil: caixa de 20; bandagem: caixa de 50.

---

## 1. Inventário dos dados

### 1.1 O que as colunas dizem

A tabela `BPStructureDynamicData` foi exportada só em 5 colunas (`tools/export_costs.lua`): `MaxHealth` (vida),
`ResourceAmounts`/`AltResourceAmounts` (custo), `RepairCost` (reparo) e **`StoredItemCapacity` (estoque)**.
Nenhuma coluna de "spawn" foi lida: **não sabemos se a tabela tem uma** (a sonda A1 lista o catálogo de colunas).

**Interpretação de `StoredItemCapacity = 15` `[INF]`.** O valor é uma capacidade de **itens guardados**, na mesma
família de `ItemHolderCapacity` dos veículos (`BPVehicleDynamicData.carga`: TruckW = 15, que o mod já trata como 15
**caixas** em `CFG.LOGI.cap`) e de `StorageBox = 15` (uma caixa de armazenamento). A leitura mais coerente é
**15 posições (slots) de caixa**, não "15 soldados" nem "15 camisas". Não está verificado em um ator carregado
(sonda A3 + ensaio B1 leem o `ItemHolder` real, se existir). Convenção do mod `[PROP]`: **capacidade = 15 slots de
caixa**; um slot guarda 1 caixa fechada, então camisas ocupam `ceil(unidades/10)`, fuzis `ceil(/20)`,
bandagens `ceil(/50)`, munição `ceil(caixas)`. Isso é compatível com as metas atuais: `want` = munição 6 + camisas
2 caixas + fuzis 1 + bandagens 1 = 10 slots ≤ 15 (`CFG.LOGI.want`, linha 2456).

### 1.2 Classes relevantes (todas `[DADO]` de `data/game_costs.txt`, salvo indicação)

Vida = `MaxHealth`; estoque = `StoredItemCapacity`; custo em bmat salvo indicação. "BP" = caminho presente em
`data/pak_files.txt` (existência do asset, não de instância).

| Classe (CodeName) | Custo | Vida | Estoque | Canteiro (vida/estoque) | Ruína (vida) | BP no pak | Observação |
|---|---|---|---|---|---|---|---|
| **ForwardBase1** | 300 | 1725 | 15 | ForwardBase1BuildSite 2000/15 | DestroyedForwardBase1 4000 | `Bases/BPForwardBase1`, `…BuildSite`, `BPDestroyedForwardBase1` | alvo da decisão; reparo 300 |
| BorderBase | 100 | 2500 | 15 | — | DestroyedBorderBase 1e8 | `Bases/BPBorderBase` | candidata barata, papel `[?]` |
| FrontierBase | 50 | 1250 | 15 | …BuildSite 2000/0 | — | **não achado** | mais barata; classe ativa não listada no pak |
| StaticBase1/2/3 | 300/200/200 | 2000/6000/7500 | 15 | …BuildSite 500/15 | Destroyed… 1e8 | **só ícone** (`MapIconStaticBase1`) | possivelmente o "bunker base" `[INF]` |
| TownBase1/2/3 | 200 | 7000/5000/4000 | 15 | TownBaseBuildSite 500/15 | DestroyedTownBase* 1e8 | `Bases/BPTownBase1..3` | bases de cidade do mapa |
| RelicBase1/2/3 (+RelicBaseBase) | 200/250/300 (300) | 4450/5150/5850 (1250) | 15 | …BuildSite 500/0 | DestroyedRelicBase* 1e8 | `Bases/BPRelicBase*` | |
| HomeRegionBase | — | 1e8 | 15 | — | — | `Bases/BPHomeRegionBase` | base inatingível das regiões-casa |
| FortBaseT1/T2/T3 | 300 / 100 / 25 concreto | 1500/2500/3500 | 15 | FortForwardBaseBuildSite 1000/15 | DestroyedFortForwardBaseT1/2/3 4000/20000/40000 | `Bases/BPFortBaseT1..3` | ramo de facilities (concreto não é produzido) |
| GarrisonStation / 1 / 2 | 250 | 2000 | 15 | — | — | `Forts/BPFortGarrisonStation` (variante de concreto: 10000, 125 concreto) | papel `[?]` |
| Hospital | 400 | 2000 | 15 | — | DestroyedHospital 1e8 | `Structures/BPHospital` | |
| FieldHospital | 200 | 500 | 6 | — | — | `Structures/BPFieldHospital` | |
| SafeHouse | — | — | 0 (só ruína: `DestroyedSafeHouse`) | — | 1e8 | só `BPDestroyedSafeHouse` + ícone | linha ativa **não existe na tabela** |
| TroopShipBase | 100 | 5000 | 12 | — | — | — | fase 4 (navios) |
| Seaport / StorageFacility / StorageBox | 400 / 400 / 25 | 2000 / 2000 / 400 | 15 / 15 / 15 | …BuildSite | Destroyed… | `BPStorageFacility`… | depósitos, não spawn |

Vizinhos úteis: `BPMedicalRoomSpawnPoints` (`Forts/Templates`, template de pontos de nascimento da sala médica das
facilities) e `PlayerStart` (23 em Deadlands, 0 em CallumsCape: `trace_regions.txt`). Em `HomeRegionW` o estudo
registra uma "base avançada" em ~(19557, 12293) (`MECHANICS_STUDY.md` §bancada) **sem a classe**: é a melhor
instância nativa para ler `ItemHolder`/componentes (sonda A3).

### 1.3 O que se sabe e o que é desconhecido

| Pergunta | Estado | Efeito na especificação |
|---|---|---|
| Custo, vida, capacidade, canteiro, ruína do ForwardBase1 | `[DADO]` | parâmetros de `CFG.FWD` |
| Caminho da classe ativa | `[INF]` `/Game/Blueprints/Structures/Bases/BPForwardBase1.BPForwardBase1_C` (padrão do pak + sufixo `_C`) | A2 confirma |
| A classe carrega no hex (CallumsCape/Deadlands)? | `[?]` | A2 carrega a classe; B1 instancia |
| Pode ser **spawnada pronta** como a refinaria do lote 17 (vida = máx., `CodeName`, `BaseStructureClass`)? | `[?]` Refinaria/fábrica: `[OBS]` sim. Esta classe: nunca instanciada | B1; **plano B** abaixo |
| Tem componente/UFunction de **spawn** nativo? | `[?]` | **Irrelevante para o design**: o mod nasce soldados com `RestartPlayerAtTransform` (`spawnSoldier`, linha 743), não pela estrutura. Só importa para riscos (§4.4 R1) |
| Tem `ItemHolder`/estoque nativo (e quantos slots)? | `[?]` | o estoque é **do mod** (`dep`), como nos pontos; o nativo só calibra a leitura do "15" |
| Footprint (bounds somente-colidindo)? | `[?]` Bounds totais incluem volumes gigantes (fábrica: extent 10594, lote 16) — inúteis | `CFG.FWD.half` provisório (600 cm) até A3/B1 |
| `TeamId` de um ator ativo recém-nascido | `[OBS]` CDO de Factory/Refinery = 255; lote 17 escreveu `TeamId = 1` sem efeito colateral visto | B1 testa 255 vs 1 (R1) |
| Aceita escrita em `Health` sem disparar destruição/visual? | `[?]` | por padrão **não escrever**: a vida da base é do mod (§3.9) |
| Existem ruínas de base nativas nos hexes? | Callums: 30 `DestroyedStructure`, só as de fábrica/refinaria/oficina foram nomeadas; **outras não enumeradas** | A3 enumera (ruínas de base/hospital) |
| Papel de Garrison/Hospital/Relic/Border/Frontier como pontos de spawn | `[?]` | fora de escopo; só entram depois de rastreadas (decisão de partida) |

**Plano B (visual) `[PROP]`.** Se a classe ativa não nascer íntegra, o design não muda: o que importa para o jogo é o
**registro do mod** (`fb`), não o ator. Plano B: `CFG.FWD.visual = "mesh"`, ator = `meshActor(...)` com uma malha já
usada pelo mod (a barraca de `CFG.TENT.mesh`, escalada) + estandarte do dono (`CFG.POINT_BANNER`). Custo/vida/capacidade
continuam os do dado do jogo. Escolha automática: `visual = "native"` só se B1 passou.

### 1.4 Sondas de laboratório

**Grupo A — só-leitura** (arquivos em `probes/`, saída só por `out(...)`, rodar **uma por vez**, sem o robô):

| Sonda | Quando | O que fecha | Cuidado |
|---|---|---|---|
| `A1_structure_columns.lua` | qualquer mapa | catálogo de colunas da `RowStruct` e valores das colunas **simples** de 14 linhas (ForwardBase1, BuildSite, Destroyed, BorderBase, FrontierBase, StaticBase1, TownBase1, RelicBase1, HomeRegionBase, Garrison, Hospital, FieldHospital, StorageBox, Factory); procura coluna de spawn/capacidade/tier | só tipos simples e 14 chaves (um dump genérico derrubou o jogo em `BPAirDynamicData`) |
| `A2_base_classes.lua` | qualquer mapa | classe carrega? (3 diretórios candidatos), cadeia de pais, CDO (`TeamId`, `MaxHealth`, `Health`, `CodeName`, `BaseStructureClass`), nomes de propriedades e UFunctions que sugerem spawn/estoque/dano; **sem SpawnActor** | `LoadAsset` traz a classe à memória; não instancia |
| `A3_world_bases.lua` | **HomeRegionW** (base avançada nativa), **CallumsCapeHex** e **DeadLandsHex**, uma carga cada | atores de base/hospital/garrison/spawn/ruína presentes, posição, time, vida, bounds (todos e só-colidindo), **classes e nomes** dos componentes | não ler propriedades de componente (MasterPose/AnimClass derrubou o UE4SS); histograma do `FindAllOf("Actor")` já é padrão (`inspect_region.lua`) |
| `A4_ground_at_points.lua` | hex, **com partida** (pontos criados) | quantos lugares de cada ponto passam no predicado de colocação do §3.3 e quantas saídas têm; saídas ao redor da base principal | tracos de linha/esfera; `HALF` provisório = 600 cm |

Critério de leitura: A1 e A2 definem se o catálogo/CDO sustenta o `visual="native"`; A3 dá footprint e instância
real (HomeRegionW); A4 diz se há lugar para uma base **em cada ponto** do hex e quantos candidatos sobram.

**Grupo B — escrita temporária (não é só-leitura; precisa de autorização do usuário como as sondas dos lotes 16/17).**
`B1`, ensaio de spawn do `BPForwardBase1_C` (descrito no roteiro do §5.2; sem código aqui por ser etapa 2).

---

## 2. O que o mod já tem e serve, e o que muda em `recruit()`

### 2.1 Já existe (candidate_v2)

| Peça | Onde | Serve para |
|---|---|---|
| Pontos de controle, dono, captura | `points`, `addPoint` (2240), `pointStep` (2290), `pointsTick` (2395); `CFG.POINT_RADIUS=500`, `POINT_MAX=5`, afastamento 2×raio; `setupPoints` usa `flatSpot` (chão plano ±80 cm no anel) | local da base; o anel já é chão plano validado |
| Depósito por ponto | `logi.depotOf(pt)` (2739): `{ammo, shirts, rifle, medical, pt}`; `logi.depots()` | estoque da base avançada **é** o depósito do ponto |
| Entrega por caminhão | `logi.truckStep` estado `toDep` (2919); destino perdido → `returnCargo` (2921); `L` fixa destino (`logi.sendTo`, 2971); `logi.needs/pickDest/nextKind` | abastecer a base com camisas/fuzis |
| Estoque perdido na captura inimiga | `pointsTick` linha 2416: `pt.dep[kind]=0` quando o dono vira inimigo | base avançada perde o estoque uma vez ao ser capturada |
| Recusa sem estoque | `recruit` (1441–1447) | "sem camisas / sem fuzis" |
| Débito só depois do spawn | `recruit` (1448–1453) | contrato transacional que o design mantém |
| Spawn num ponto | `deployPoint()` (1409: cursor dentro de ponto nosso) + `spawnSquad(1, role, at)` (766) | seleção explícita do local |
| Piso validado | `logi.parkingGround` (2553, só Landscape, nunca telhado), `logi.parking` (2564, anel + 4 cantos + esfera), `flatSpot` (4232) | colocação e saídas |
| Implantação com rollback | `logi.applyPlan` (2639): valida contrato, desfaz tudo em falha | molde da construção da base |
| Persistência v2 | `sv.collect/validate/preflight/infraPlan/load` (5113–5712): preflight sem mutação → aplica com rollback → restaura | molde do save da base |
| Alerta e painel | `rts.alert` (495), `logi.hudLine` (3015) com linha por depósito | alertas e linha da base |
| Dano em área inimigo | `logi.blast(hit, radius, dmg, team)` (3150), único ponto de chamada (3923) | dano à base por morteiro |

### 2.2 O que muda em `recruit(role, at)` (e o que não muda)

**Muda** (somente com `logi.on and combat.mode ~= "assault"`, chamado "ramo logístico"):

1. **Origem do soldado = uma estrutura de spawn**, sempre. Hoje, sem `at`, o recruta nasce **ao lado do esquadrão**
   ou do comandante (`spawnSquad`: `ref = squad[1]`, linha 771) e ainda assim debita a base: isso **é** o
   teletransporte que a decisão de design proíbe. No ramo logístico o local de nascimento vem de
   `logi.spawnSite` (§4.3): base principal ou base avançada, nas "saídas" validadas.
2. **Sem mão de obra abstrata**: não confere nem debita `economy.manpower` (linhas 1431, 1454). A mão de obra
   continua existindo para morteiro, trincheira, caixa, barreira, posto e arame; o painel deve rotulá-la como tal.
3. **Recusa em vez de fallback**: hoje ponto sem estoque cai para "nasce na base" (1437–1440). No ramo logístico,
   se o cursor está **dentro** de uma base (seleção explícita), a falta de estoque ali **recusa com aviso** (nunca
   troca de base em silêncio). Fora de qualquer base, escolhe-se a mais próxima com estoque (§3.6).
4. **Pontos de controle sem base deixam de ser local de nascimento** (`CFG.SPAWN.pointSpawn = false` por padrão;
   `true` reproduz o comportamento antigo). É consequência direta de "pontos de spawn = estruturas"; precisa de
   ok do usuário (§6, decisão D2).
5. **Débito**: continua só após spawn confirmado, mas passa para `logi.spawnCommit(site, role)` (uma camisa; um
   fuzil se a função é fuzileiro), com o razão da base (§3.5).
6. `spawnSquad` ganha 2 linhas: com `at.exact` o soldado nasce **na saída** (sem deslocamento de formação
   `slotFor`, que chega a 5 fileiras × 160 cm = 8 m atrás do ponto) e com `z = at.Z` (a saída já é chão Landscape).
7. Derrota (linha 4852 `#squad == 0 and economy.manpower < rifle.cost`) no ramo logístico passa a
   `#squad == 0 and not logi.canReinforce()` (nenhuma estrutura ativa com ≥ 1 camisa **e** nenhum caminhão com
   camisas a caminho).

**Não muda:** assinatura `recruit(role, at)` e as teclas Ctrl+1/2/3/4/0 (`at` sem `.name` continua sendo "cursor");
limite `SQUAD_MAX` e oficial único; o ramo **legado** inteiro (sem logística ou Assalto) — mesmo código, mesmos
números, mesmos testes de `tools/test_orders.py` (recusas por mão de obra, linhas 359–366, 513, 579–); F6
(esquadrão grátis), `newGame`/`newAssault` (`spawnSquad` sem `at`), ondas e reforços inimigos, `earn`/renda por
ponto, `CFG.WEAPONS` (custos só do ramo legado), o `env` do canal.

---

## 3. Especificação

### 3.1 Modelo

- **Sítio de nascimento** (`site`): ou a base principal (`logi.base`, depósito virtual em `rts.base()`), ou uma
  **base avançada** (`fb`) ligada a um ponto de controle próprio. Ponto de controle sem `fb` continua sendo
  depósito de **munição/bandagem** (e ponto de cura/recarga), não de reforço.
- **Base avançada** `[PROP]`: um registro do mod, mais (opcionalmente) um ator do jogo:

```
fb = { pt = <ponto>, code = "ForwardBase1", x, y, z, yaw,           -- onde foi colocada (dentro do anel do ponto)
       hp = 1725, maxHp = 1725,                                      -- DADO; vida do MOD (§3.9)
       actor = <ator|nil>,  exits = { {X,Y,Z}, ... }, exitI = 0,     -- ator nativo (ou malha); saídas de nascimento
       dead = false, led = { rx = {}, used = {}, lost = {} } }       -- razão por produto (§3.5)
pt.fb = fb ;  dep = logi.depotOf(pt) ;  dep.fb = fb                  -- o depósito do ponto É o estoque da base
```

- **Estados** (derivados, nunca guardados): `ativa` (`not fb.dead` e `pt.owner == FRIENDLY`); `inativa` (ponto
  neutralizado: sem nascimento, sem entrega, estoque preservado; reativa ao recapturar); `destruída`
  (`fb.dead`: estoque perdido, registro removido).
- **Habilitada a reforçar** = `ativa` e `dep.shirts ≥ 1` (e `dep.rifle ≥ 1` se a função é fuzileiro).

### 3.2 Como o jogador cria (sem tecla nova)

**Fluxo `[PROP]`:** com o cursor **dentro do anel de um ponto nosso**, apertar **J** (hoje: "criar ponto", recusa
com "perto demais de outro ponto" nesse caso — a recusa vira o gancho).

1. 1º J: mensagem `Base avançada em A: 300 bmat (fábrica tem 412). J de novo em 4 s para construir.`
   Se `logi.bmat − reserva < 300`: `faltam N bmat (fábrica tem X); J de novo em 4 s reserva o bmat`.
2. 2º J (mesmo ponto, ≤ `CFG.FWD.confirm` = 4 s em tempo real, `GetRealTimeSeconds`): constrói (§3.4) ou, sem bmat,
   deixa o **pedido pendente** (§3.4).
3. J fora de qualquer ponto, sem logística ou no Assalto: comportamento **inalterado** (cria ponto / mensagem).
4. J num ponto que já tem base `ativa`: informa estado e estoque (sem custo).

Por que J e confirmação: J já é a tecla de "território"; o gasto é de 300 bmat (a fábrica inteira por ~2,5 min de
refino saturado) e não pode acontecer por um clique de quem queria criar um ponto vizinho.

**Alternativa se o usuário não quiser sobrecarregar J:** **Shift+J**. Conferida: `SHIFT+J` não está em `GAME_KEYS`
(`tools/test_orders.py:863`, que lista só `SHIFT+ONE..SEVEN, E, F, Q, V, X`) nem registrada pelo mod
(`RegisterKeyBind` 6244–6300: `SHIFT+F4/F5/F6/L/RMB/F7`). Exigiria acrescentar `"SHIFT+J"` ao conjunto esperado
de `registered` (linha 874) e uma linha em `MANUAL_TEST.md`/README/ajuda F5. Não recomendo Ctrl+tecla numérica:
Ctrl+1..9,0 estão todos em uso.

**Teclas conferidas:** J já registrada (6283), não colide com o jogo (`J` ∉ `GAME_KEYS`); nenhuma tecla nova na
recomendação principal ⇒ `registered` e o teste de teclas não mudam.

### 3.3 Onde pode ser colocada

Todas as condições precisam valer na hora do 2º J (e de novo ao executar um pedido pendente):

1. `logi.on`, `combat.mode ~= "assault"`, `rts.active`, autoridade local.
2. Cursor dentro do anel (`POINT_RADIUS`) de um ponto com `owner == FRIENDLY` e **sem** `fb`.
3. `#fbs ativas+inativas < CFG.FWD.max` (3; `[PROP]`, ≤ `POINT_MAX` = 5).
4. **Sem inimigo vivo dentro do anel** do ponto (`presence(enemies, pt) == 0`): não se constrói sob ataque.
5. **Mais perto da frente que da retaguarda `[PROP]`:** o ponto fica a ≥ `CFG.FWD.minFromBase` (3000 cm) da base
   principal **ou** a ≤ `CFG.FWD.maxToEnemyPoint` (4000 cm) de um ponto inimigo; evita comprar uma "base avançada" colada
   à base. (Os pontos de `setupPoints` ficam a 1400–2400 cm da base: **a regra faz o ponto inicial padrão não
   qualificar** a menos que haja ponto inimigo perto; parâmetros a calibrar no laboratório.)
6. **Superfície validada como no lote 17 (`logi.parkingGround`):** o centro e 8 pontos a `HALF` precisam ser
   **Landscape** (nunca telhado, veículo ou prop), `|dz| ≤ maxSlope` (60) em relação ao centro e `≤ maxHeight` (250)
   em relação ao ponto; varredura de esfera de raio `HALF/2` livre no canal de movimento; afastada de barreiras,
   trincheiras, postos e arames do mod (`structures`, `S.trenches`, `S.tents`, `S.wires`) por `HALF + raio deles`.
   Busca: centros em 0 / 150 / 300 cm do centro do ponto (1 + 8 + 8 candidatos), com **yaw** voltado ao inimigo mais
   perto (`fort.facing(p, enemies)`, 4324). Primeiro que passa vence. Nenhum → recusa com motivo.
7. **Saídas:** o candidato precisa de ≥ `CFG.FWD.minExits` (3) saídas válidas: pontos num anel de `half + 200` cm
   (8 ângulos), chão Landscape, `|dz| ≤ 2×maxSlope`, esfera de cápsula livre. As saídas são guardadas em `fb.exits`
   e **nunca** recalculadas com `groundZ` (o canal Visibility acerta telhado; é o erro do lote 16).
8. Orçamento (§3.4) e `fb` ainda inexistente no ponto.

`HALF` provisório 600 cm `[?]` até A3/B1 medirem o footprint do `ForwardBase1`. A sonda A4 já conta os candidatos
válidos por ponto com esse valor.

### 3.4 Custo e transação (rollback)

**Moeda `[PROP]`:** o **bmat de produção da fábrica** (`logi.bmat`), 300 por base (`[DADO]`), respeitando a reserva
de caminhões: exige `logi.bmat − logi.rebuildReserve() ≥ 300`. Não usa a carteira de implantação (`S.deploy`,
1100): ela é um orçamento de **cenário** de uso único e o save v2 exige `spent == Σ custo(built)` (`sv.validate`,
linha 5380) — acrescentar bases ali quebraria essa invariante. Usar `logi.bmat` também faz o débito **persistir
sozinho** (`logi.snapshot().bmat`). A base compete de verdade com as caixas (trade-off econômico).

**Transação (sempre nesta ordem; qualquer falha desfaz tudo e não debita):**
1. Preflight sem mutação: §3.3 inteiro + classe carregável (`LoadAsset`) quando `visual="native"`.
2. Spawn do ator (`world():SpawnActor(cls, pos, rot)`); asserts: válido, `not bActorIsBeingDestroyed`, posição
   a < 100 cm / rotação a < 1° do pedido, e (nativo) `Health == MaxHealth == 1725`, `CodeName` esperado
   `[?]` (confirma B1). Falha → `K2_DestroyActor` do que nasceu.
3. Cria `fb`, `pt.fb`, `dep.fb`; `dep` começa **vazio** (a compra é da estrutura, não do estoque).
4. **Só então** `logi.bmat = logi.bmat − 300`, contadores, alerta/aviso.
Mesma disciplina de `logi.applyPlan` (2639–2683) e do lote 17 ("não debita nem limpa a partida em falha").
Reaproveitar: extrair o núcleo comum de spawn+asserts em `logi.fwdSpawn(site)`, usado também pelo restore do save.

**Sem bmat suficiente → pedido pendente `[PROP]`** (`logi.fwdOrder = {pt, cost, t0}`; um por vez): o 2º J registra
o pedido e a fábrica **para de iniciar receitas** enquanto `logi.bmat − reserva_caminhões < cost`
(`logi.rebuildReserve()` passa a somar `cost` do pedido, o mesmo mecanismo do patch `reserva_bmat`; por isso
também aparece como `guarda N bmat` no painel). Quando o bmat chega, `logi.tick` constrói sozinho (re-valida §3.3;
se o ponto foi perdido, há inimigo no anel, ou passaram `CFG.FWD.pending` = 180 s, cancela com aviso e libera a
fábrica). Caminhão destruído tem prioridade (a reconstrução dele não depende do pedido). Motivo: sem isso a base
nunca seria comprável sob demanda contínua — o mesmo defeito de limiar (receita 80 < caminhão 100) que o
acabamento provou para os caminhões (`logistics_ai/finishing/REPORT.md` §2).

### 3.5 Estoque próprio e capacidade

- Estoque = `dep.ammo/shirts/rifle/medical` do ponto (já existente). **Capacidade `[PROP]`** = 15 slots
  (`CFG.FWD.cap`, `[DADO]` 15; interpretação em §1.1). `logi.slotsUsed(dep)` =
  `ceil(ammo) + ceil(shirts/10) + ceil(rifle/20) + ceil(medical/50)`.
- A base principal **não** tem teto (comportamento atual), `CFG.FWD.baseCap = nil`.
- **Carga do caminhão limitada pelo espaço:** em `truckStep` (estado `idle`, 2899–2911) o espaço livre do destino é
  `cap − slotsUsed(dest) − (caixas já a caminho para dest)`; `wanted` (inclusive com `L` fixando: `wanted = stock`,
  linha 2904) não passa disso. Como só caminhão acrescenta e o espaço é reservado na carga, **a chegada sempre
  cabe**; o save é validado contra o teto (§3.11).
- **Camisas/fuzis só para quem nasce soldado:** `logi.needs(dep)` zera `shirts` e `rifle` para depósito que não é
  `spawnCapable` (base principal ou `fb` ativa); ponto sem base só recebe munição/bandagem. Efeito colateral
  deliberado: a produção de camisas passa a escalar com **bases**, não com pontos. `nextKind` passa a dividir por
  quantos depósitos capazes existem para esses dois produtos (mudança em 1 linha, 2782).
- **Razão por base** (oráculo de teste e de laboratório, `logi.fwdAudit()`): por produto,
  `recebido + inicial_do_restore == estoque + consumido + perdido`. Atualizado em `logi.moveCargo` (2788), em
  `logi.spawnCommit` e em `fwd.lose`. Não é gravado no save (reinicializa com o estoque lido).

### 3.6 Seleção do ponto de spawn

`logi.spawnSite(role, cursor, opts)` (puro, sem efeito, §4.3), no ramo logístico:

1. **Receita da função:** `CFG.SPAWN.roles[role] = {shirts=1, rifle=0|1, sites=...}`. Função sem entrada → recusa
   (fail-closed). Hoje só `rifle` consome arma (`rifle=1`); `mg`, `sniper`, `medic`, `officer` consomem **só camisa**
   — **bônus abstrato explícito**: não existe caixa de MG/rifle de precisão/pistola no mod (MGW custa 25 rmat, que a
   cadeia não produz; o ECONOMIA recusa usar RifleW para elas).
2. **Candidatos** = base principal + `fb` com estado `ativa` (+ pontos próprios com depósito, só se
   `CFG.SPAWN.pointSpawn`). Cada um precisa de `exits` (a base principal calcula as dela em `logi.start`; se não
   achar ≥ `minExits`, usa o deslocamento legado e registra o aviso).
3. **Seleção explícita:** se `cursor` está a ≤ `POINT_RADIUS` do centro de um candidato (anel da base/ponto), **só ele**
   conta. Sem camisa/arma ali → recusa: `sem camisas na base A (estoque 0); mova o cursor para fora das bases para
   o mais próximo com estoque`.
4. **Seleção automática:** caso contrário, entre os candidatos **com estoque** para a função, o de menor
   `flatDist(ref, candidato)`, com `ref = cursor` ou, sem cursor, `squadCenter()` ou, sem esquadrão, o ponto inimigo
   mais perto da base (a "frente") ou `rts.base()`. Nenhum com estoque → recusa com o motivo do mais próximo.
5. Saída: `site.at = {X,Y,Z,exact=true}` = próxima saída da base em rodízio (`exitI`).

### 3.7 Recrutar no ramo logístico (fluxo completo)

`recruit(role, at)`: autoridade → `SQUAD_MAX` → oficial único → `site, why = logi.spawnSite(role, at-or-cursor)` →
recusa com `notify(why)` se `nil` → `spawnSquad(1, role, site.at)` → se `< 1`: **nada debitado**, retorna `false` →
`logi.spawnCommit(site, role)` (re-valida o estoque; debita 1 camisa e, se fuzileiro, 1 fuzil; razão; `notify` com o
nome da base e o estoque restante) → `true`. `economy.manpower` não é tocado.

### 3.8 Logística (efeito sobre o que já existe)

Sem tecla nova: `L` sobre o anel da base manda o próximo caminhão para ela (`logi.sendTo` já testa `flatDist(c, d) ≤
1.5×POINT_RADIUS` sobre os depósitos); `Shift+L` (prioridade) cobre camisas/fuzis (ECONOMIA). `truckStep` toDep
valida destino por `d.pt.owner == FRIENDLY` (2921): **continua correto** para `fb` (inativa ⇒ caminhão volta com a carga),
porque o depósito da base é o do ponto. Base destruída com caminhão a caminho: o ponto ainda é nosso, então o
caminhão **entrega só munição/bandagem** e as caixas de camisa/fuzil que sobrarem na carga voltam à fábrica
(`returnCargo`, crédito só na chegada física, contrato ESTRADAS) — implementar como: ao chegar a depósito não
`spawnCapable`, devolver `shirts`/`rifle` do `cargo`.

### 3.9 Destruição, perda e captura

Um único ponto de entrada, `logi.fwdLose(fb, why)` (idempotente por `fb.dead`):
1. calcula e registra o que se perde (razão: `lost`); zera `dep.shirts/rifle/ammo/medical` **uma vez**;
2. destrói o ator (`K2_DestroyActor`, depois `fb.actor = nil`) e, se possível, cria a ruína
   `BPDestroyedForwardBase1_C` (best effort; falha só registra) guardada em `S.fwdRuins` (destruída em `logi.reset`);
3. `pt.fb = nil`, `dep.fb = nil`; alerta `rts.alert("perdido", pt, "BASE AVANÇADA A destruída: perdeu N camisas e M
   fuzis")`.

Fontes de dano (`fwdHit(fb, amount, why)`):
- **Captura do ponto pelo inimigo** (`pointsTick`, ramo `owner == ENEMY`, 2411–2417): chama `fwdLose(fb,"capturada")`
  *em vez* do zeramento direto (que fica como está para pontos sem base). O estoque já era zerado aqui.
- **Morteiro inimigo** (`logi.blast`, 3150): para `team == ENEMY_TEAM`, base dentro de `radius×1.5` leva
  `dmg × CFG.FWD.blastMul` (2, como o caminhão). Com `CFG.MORTAR.dmg=75` e 2 projéteis por salva: 300/salva ⇒ ~6 salvas
  para os 1725 HP. `[PROP]`, calibrar.
- **Cerco por proximidade**: fora da v1 (`CFG.FWD.siegeDps = 0`): inimigo no anel sem aliado já captura o ponto em
  ≤ 10 s, antes de qualquer dano por vida.
- A vida do ator nativo **não é escrita** (sem `OnRep_Health`, sem visual de dano) até B1 provar que é seguro.

**Ponto neutralizado** (`owner → nil`): base **inativa**, nada se perde; ao recapturar, volta a `ativa` com o estoque
que tinha. **Ponto recapturado depois de `destruída`:** sem base; o jogador pode reconstruir (J, 300 bmat de novo).
**Perdido uma vez, sem duplicar:** `fb.dead` bloqueia segundo `fwdLose`; o zeramento legado da captura roda sobre
estoque já zero; caminhão em trânsito não "ressuscita" estoque porque o crédito vai ao `dep` do ponto (sem base,
`spawnCapable` falso ⇒ camisas voltam).

### 3.10 IA inimiga

**Proposta: o inimigo NÃO constrói bases avançadas na v1; usa a mesma regra de estoque, agregada.**
Coerência com `logistics_ai` v2: o inimigo já tem a regra "soldado pago = 1 camisa + 1/6 de caixa de munição" da
**frente** (`CFG.ECHAIN`, `logi.eConsume/eAfford/waveCut`, estoque `en.front`, 2 munição + 10 camisas iniciais), e o
lugar de nascimento dos reforços já é um **ponto inimigo** (`ai.source`, 4808; ondas em `waveSpawnPoint`). Ou seja, o
equivalente inimigo de "base avançada" já existe: *ponto inimigo como saída + estoque agregado da frente como
estoque*. Cortar comboio reduz as camisas (já implementado); tomar os pontos inimigos remove os locais de saída (`ai.source`
sem ponto ⇒ sem reforço). Justificativa para não construir: a IA não tem decisão de posicionamento nem de construção
(`ai` só reforça por ponto), o ganho de equilíbrio é nulo no escopo "região pequena", e adicionar estoque por ponto
inimigo exigiria reabrir o razão fechado (`eAudit`) e o schema `elogi` v1. **Assimetria assumida e declarada:** o
jogador gasta bmat numa base e pode perdê-la; o inimigo tem saídas "gratuitas" nos pontos que segura (perde ao
perdê-los). **v2 `[PROP]`:** repartir `en.front` por ponto inimigo (cada ponto vira um estoque) e fazer o inimigo
"reconstruir" uma base ao retomar um ponto, pagando bmat da retaguarda — só depois do laboratório calibrar a v1.
Assalto: tudo abstrato, como hoje.

### 3.11 Persistência

Extensão **aditiva** do schema v2 (sem subir `CFG.PERSIST.version`), versionada própria como `infra`/`elogi`:

```
fwd = { version = 1, list = { { pt = <índice em d.points>, code = "ForwardBase1", x, y, z, yaw, hp }, ... } }
```

- Só bases **vivas** (ativa/inativa). Destruída não é gravada (a ruína é cosmética). Nunca ator, endereço ou saída:
  as saídas são **recalculadas** na restauração, pelo mesmo predicado, no mundo novo.
- **Estoque**: já vai em `logi.snapshot().pts[i]` (`a,s,r,m` por índice de ponto). Não duplicar.
- **bmat**: já vai em `logi.snapshot().bmat`. Pedido pendente **não** é salvo (cancela ao carregar; avisado).
- `sv.validate`: `known.fwd = 1`; `version == CFG.PERSIST.fwdVersion`; `#list ≤ CFG.FWD.max`; cada registro:
  campos exatos (campo desconhecido = recusa), `pt` inteiro em `1..#d.points` e **único**, `code == "ForwardBase1"`,
  coord finitas e `≤ maxCoord`, `0 < hp ≤ maxHp`, ponto a ≤ `POINT_RADIUS` do `pt` salvo; e o estoque de `logi.pts[pt]` ≤
  `cap` em slots. `fwd` sem `logi` ⇒ recusa. **Política:** erro em `fwd` **recusa** o save inteiro (como `infra`),
  ao contrário de `elogi` (que é regenerável): descartar `fwd` apagaria o poder de reforçar do jogador.
- Lido por mod antigo: `campo desconhecido: fwd` ⇒ recusa fail-closed (intencional).
- `sv.preflight` (sem mutação): classe carregável, `visual` coerente, chão Landscape no XYZ salvo e saídas ≥ `minExits`
  (mesmo predicado, tolerância `PERSIST.tol` 200 cm na posição do ponto). Falha ⇒ "Continuar recusado".
- `sv.load`: preflight → `logi.fwdSpawn` de cada registro para uma **área de espera `S.fwdStage`** (não zerada por
  `logi.reset`) com rollback conjunto à `plan.apply` da infra → `sv.restore` (limpa, recria pontos) → `sv.verify` →
  `logi.restore` (estoques por índice) → **`logi.fwdBind(d.fwd)`** associa cada estágio ao `pt` pelo índice e recalcula
  saídas. Falha no bind ⇒ destrói o estágio e marca `sv.degraded` ("base avançada A não refeita"), autosave suspenso
  (mecanismo existente); o estoque do ponto fica no depósito.
- `sv.collect`: `fwd = logi.fwdSnapshot()`; `clearSquad`/`newGame` limpam bases via `logi.reset`.

### 3.12 Painel e alertas

Uma linha curta por base dentro do bloco de depósitos de `logi.hudLine` (o painel v2 já imprime
`"%s | munição %.0f | camisas %d%s"`, 3041–3047). Função pura `logi.fwdLine(dep)` `[PROP]` (≤ 96 caracteres):

```
base       | camisas 30 | fuzis 0  | slots —    | reforça: só sem fuzil (sem fuzis)
A [BASE]   | camisas 12 | fuzis 3  | slots 9/15 | reforça: tudo
B [BASE]   | camisas 0  | fuzis 0  | slots 4/15 | reforça: NÃO (sem camisas)
C [BASE]   | camisas 8  | fuzis 1  | slots 7/15 | INATIVA (ponto neutro)
```
Munição/bandagem continuam na linha atual do depósito (não duplicar). Pedido pendente: `Fábrica | guarda 300 bmat para base
avançada em A (bmat 140)`. Alertas existentes: "ponto sob ataque" (já cobre a base), `perdido` na destruição; reforço
recusado vai para `notify`. Cor/ícone no mundo: estandarte do dono do ponto (`pointVisual`) basta na v1.

---

## 4. Contratos e riscos

### 4.1 Limites técnicos do `main.lua`

- **Locais de topo: nenhum novo** (candidate_v2: 178 pelo compilador, 175 pela regex; limite 200). Tudo em
  `logi` (`logi.fwd*`, `logi.spawn*`, `logi.slotsUsed`, `logi.canReinforce`, `logi.fwdLine`), `CFG.FWD`, `CFG.SPAWN`,
  `S.fwdStage/fwdRuins/fwdConfirm`, `rts.fwdKey`. Nenhum local chamado `ai/sv/fort/rts/anim/S/logi`
  (`tools/check_globals.py` é insensível a escopo).
- **`env` do canal** (6144–6169): `logi`, `rts`, `sv`, `CFG`, `S` já estão; as funções novas ficam alcançáveis sem tocar
  `runCommandFile`. **Não** estão no `env`: `cursorPoint`, `squadCenter`, `groundZ`, `surfaceZ`, `flatSpot`. Por isso
  `logi.spawnSite` **recebe o cursor por parâmetro** (o `recruit` passa `cursorPoint()`), e a colocação usa funções que
  já são alcançáveis ou internas do módulo. `recruit` já está no `env`.
- **Cache por endereço (regra `anim.untrack`)**: o `fb.actor` é o único ator guardado; checar sempre
  `valid(a) and not a.bActorIsBeingDestroyed` antes de usar (`IsValid` fica true até o GC); em toda destruição
  `K2_DestroyActor` seguido de `fb.actor = nil` no mesmo bloco; **nenhuma tabela indexada por ator/endereço**, nenhum
  `RegisterHook` na classe da base, nenhuma escrita por quadro no ator (a vida é do mod). O save nunca grava ator
  (`sv.pure` já recusa userdata). Soldados nascidos no ramo logístico passam pelo `spawnSoldier` de sempre (que registra
  o `anim`), então a regra `untrack` dos soldados não muda.
- **Custo por quadro:** a colocação faz ~25 candidatos × (9 tracos de chão + esfera) + 8 saídas ≈ 250–300 chamadas
  UFunction, no 2º J (evento único). Medidas anteriores: planejamento de rota 36–54 ms síncronos; **aceitável uma vez**,
  mas medir no laboratório (L5). Se passar de ~60 ms, fatiar em máquina de estados por quadro (não corrotina:
  UFunction não roda em corrotina).
- **GC/`Registry`:** a base não cria callbacks Lua. O pedido pendente roda dentro de `logi.tick` (já por quadro).

### 4.2 Conflitos prováveis com a coleta manual (outro agente)

Ele mexe em `logi.deploy`/`applyPlan`, em `logi.start` (estoque inicial, caminhões que deixam de existir no início)
e no nascimento de trabalhadores (camisa da base). Mapa de pontos de contato (↔ = ambos editam; → = só eu):

| Ponto | Eu | Eles | Regra |
|---|---|---|---|
| `recruit` ramo legado | não toco | não devem tocar | ramo legado intacto; só entro por `logi.spawnSite` |
| `logi.start` | → 2 linhas: `logi.base.exits = logi.exitRing(...)`, `logi.fwd = {}` | ↔ estoque inicial, caminhões | linhas aditivas e separadas, sem reordenar |
| `logi.reset` | → destruir `fb.actor`, `S.fwdRuins`, pedido | ↔ limpeza de trabalhadores | cada um adiciona um bloco `pcall` próprio |
| `logi.base.shirts` | consumo via `spawnCommit` | consumo dos trabalhadores | **um só débito**: ambos usam `spawnCommit` (razão único) |
| `logi.deploy/applyPlan/wallet` | **não toco** | ↔ | bases usam `logi.bmat`, não a carteira |
| `logi.needs/nextKind` | → shirts/rifle só p/ `spawnCapable` | ↔ se produzirem "trabalhador" como demanda | demanda de camisa da base principal inclui trabalhadores: eles declaram em `CFG.SPAWN.roles.worker` |
| `CFG.WEAPONS`/`roleFor` | não toco | ↔ função `worker` | entram em `CFG.SPAWN.roles`, não em `CFG.WEAPONS` |
| `sv.collect/validate` | → `fwd` | ↔ estado dos trabalhadores | cada um adiciona sua chave `known`, validador próprio, sem tocar o do outro |
| `waveTick` derrota | → `canReinforce` | ↔ trabalhador conta como "camisa gasta"? | `canReinforce` olha só estrutura com camisa; trabalhador vivo não impede derrota |

### 4.3 Interface comum `logi.spawnSite` / `logi.spawnCommit`

```
site, why = logi.spawnSite(role, cursor, opts)
  role   : chave de CFG.SPAWN.roles  (rifle|mg|sniper|medic|officer|worker|...). Chave ausente => nil,"função sem receita"
  cursor : {X,Y[,Z]} ou nil           (quem chama passa cursorPoint()/nil; a função não lê o mouse)
  opts   : { sites = {"base","fwd"}   -- restringe tipos (padrão: roles[role].sites ou todos)
             explicit = bool|nil }    -- nil: decide pela posição do cursor (§3.6)
  retorna: site = { dep = <depósito>, kind = "base"|"fwd", name = <string>, fb = <fb|nil>,
                    at = {X,Y,Z,exact=true}, need = {shirts=1, rifle=0|1}, explicit = bool }
           ou nil, motivo (texto pronto para notify)
  PURA: não altera estoque, nem rodízio de saídas, nem cria ator. Chamar duas vezes é inofensivo.

ok, why = logi.spawnCommit(site, role)
  chamada UMA vez, depois do spawn confirmado (síncrono no game thread). Re-valida estoque (nunca negativo),
  debita need.shirts/need.rifle de site.dep, avança site.fb.exitI, atualiza o razão. false => não debitou (log).

logi.canReinforce() -> bool          -- existe estrutura ativa com >=1 camisa, ou caminhão carregando camisas
CFG.SPAWN = { pointSpawn = false,
              roles = { rifle={shirts=1,rifle=1}, mg={shirts=1}, sniper={shirts=1}, medic={shirts=1}, officer={shirts=1} } }
              -- trabalhadores: o outro agente acrescenta  worker={shirts=1, sites={"base"}}
```
Contrato para **todo** chamador (soldado, trabalhador, futuros papéis): decidir com `spawnSite`, criar o ator, só
então `spawnCommit`; falha de criação ⇒ nada debitado e nada de "meio-nascimento"; nunca debitar `dep.shirts` direto.
No ramo legado (`logi.on` falso ou Assalto) `spawnSite` devolve `nil, "ramo legado"` e o chamador segue o caminho
antigo — assim a coleta manual pode usar a interface sem se preocupar com o modo.

### 4.4 Riscos

| # | Risco | Evidência/estado | Mitigação |
|---|---|---|---|
| R1 | Ator ativo com `TeamId` aliado ser tratado pelo jogo como ponto de respawn nativo (soldados são `HeadlessPlayerController` com hooks de `ClientStartRespawnTimer`, linhas 6046–6071) | `[?]` nunca instanciado; refinaria/fábrica com TeamId 1 não mostraram efeito, mas não têm spawn | B1 testa `TeamId` 255 vs 1 e observa 60 s o log e soldados mortos; plano B visual (malha) elimina o risco |
| R2 | Footprint desconhecido ⇒ base dentro de prédio/colisão | bounds totais inúteis (lote 16) | A3 (só-colidindo) + varredura de esfera + saídas; `HALF` conservador |
| R3 | `SpawnActor` devolver `IsValid` já em destruição | `[OBS]` lote 16 | assert `bActorIsBeingDestroyed` e posição/vida, como `applyPlan` |
| R4 | Trace de chão acertar telhado | `[OBS]` lote 16 | Landscape-only (`parkingGround`), saídas nunca por `groundZ` |
| R5 | Equilíbrio: sem teletransporte e sem mão de obra, o início do jogo (rifle = 0 na base, ECONOMIA) pode travar o reforço | `logi.base.rifle = 0` ao iniciar | decisão dos donos de ECONOMIA/coleta (estoque inicial); a especificação só garante a recusa clara |
| R6 | Reserva de bmat do pedido travar a fábrica por 180 s e esvaziar munição | proposta nova | teto `pending`, cancelamento explícito, painel mostra `guarda 300`; teste L7 |
| R7 | Mudança de `needs` (camisa só p/ capazes) alterar testes de ECONOMIA | `test_integration.py` usa `L.pin` (não depende de `needs`) | rodar a bateria da pilha; ajustar asserts afetados |
| R8 | J com 2 funções confundir o jogador | | confirmação com texto de custo; alternativa Shift+J (§3.2) |
| R9 | Ordem: depende da pilha v2 aplicada | | etapa 2 só sobre `main.lua` já integrado; build com âncoras únicas fail-closed |
| R10 | Interpretação "15 slots" errada | `[INF]` | parâmetro `CFG.FWD.cap`; só afeta teto de carga; A3/B1 comparam com `ItemHolder` |

---

## 5. Testes

### 5.1 Plano offline da etapa 2 (lupa, o `main.lua` inteiro em memória, como as outras pastas)

Arquivos esperados na pasta: `build_patch.py` (âncoras únicas, fail-closed, sobre a pilha integrada),
`test_bases_avancadas.py`, `candidate/main.lua`. Mocks só nas fronteiras de engine (traços, spawn, estruturas).

| # | Teste | Cobertura |
|---|---|---|
| T1 | Regressão: `tools/test_orders.py`, `check_globals.py`, 36 casos de persistência, `economy/test_integration.py`, `logistics_ai/test_logistics_ai_v2.py` | ramo legado inalterado; ≤ 178 locais (compilador) |
| T2 | `spawnSite` puro: não altera estoque nem `exitI`; chamado 2× igual | contrato |
| T3 | Seleção: explícita (cursor no anel) recusa sem fallback; automática escolhe a mais próxima **com estoque**; empate; sem cursor usa `squadCenter`; base sem saídas → deslocamento legado + aviso | §3.6 |
| T4 | Função sem receita (`worker` ausente) recusa; `worker` com `sites={"base"}` nunca sai numa `fb` | interface |
| T5 | Recrutar fuzileiro: debita 1 camisa e 1 fuzil só se `spawnSquad` devolve 1; devolve 0 ⇒ estoque intacto; MG/sniper/médico/oficial só camisa | transação |
| T6 | Ramo logístico não toca `economy.manpower`; legado e Assalto idênticos (diffs de estado zero) | §2.2 |
| T7 | Construção: recusas por cada condição de §3.3 (sem logística, Assalto, ponto neutro/inimigo, inimigo no anel, limite, perto da base, chão = telhado/veículo, sem saídas ≥ 3, pedido sobreposto) sem débito e sem ator | §3.3 |
| T8 | Rollback: spawn devolve `IsValid` em destruição, `Health ≠ 1725`, posição deslocada ⇒ ator destruído, bmat e `pt.fb` intactos | §3.4 |
| T9 | Débito só no fim: bmat−300, `fb` criada, depósito vazio; repetir J no mesmo ponto não duplica nem cobra | §3.4 |
| T10 | Pedido pendente: reserva faz a fábrica parar; com demanda contínua o bmat chega a 300 e constrói sozinho; cancela por timeout/ponto perdido/inimigo; caminhão destruído tem prioridade; razão de bmat fecha | §3.4 |
| T11 | Capacidade: carga limitada por slots livres menos o que está a caminho, inclusive com `L`; nunca > 15; `slotsUsed` com caixas parciais | §3.5 |
| T12 | `needs`/`nextKind`: ponto sem base só munição/bandagem; base recebe camisa/fuzil; camisas escalam com nº de bases | §3.5 |
| T13 | Destruição: captura inimiga, morteiro (`logi.blast` com `team=ENEMY`), 2ª chamada idempotente (estoque perdido uma vez, razão `perdido`), caminhão em trânsito devolve camisas à fábrica só na chegada | §3.9 |
| T14 | Estados: neutralizar ⇒ inativa (estoque preservado, sem spawn, sem entrega), recapturar ⇒ ativa; reconstruir após destruída | §3.1/3.9 |
| T15 | Derrota: `#squad==0` com base abastecida não perde; sem camisas em lugar nenhum e sem caminhão ⇒ derrota | §2.2 item 7 |
| T16 | Razão por base fecha após sequência aleatória (como `eAudit`: 25 sementes × 600 passos) | conservação |
| T17 | Save: ida e volta em carga nova (atores refeitos, estoque por índice, saídas recalculadas), repetição 3× sem duplicar, `fwd` com campo desconhecido/versão futura/`pt` duplicado/hp inválido/estoque > teto/sem `logi` ⇒ recusa preservando partida e arquivo; falha de spawn no preflight e depois dele (rollback conjunto com `infra`); mod antigo recusa | §3.11 |
| T18 | Mutação: remover o teste de `bActorIsBeingDestroyed`, o débito-depois-do-spawn, a idempotência de `fwdLose`, o teto de slots, o `exact` do `spawnSquad` — a suíte deve falhar | testes não vácuos |
| T19 | Teclas: sem tecla nova (recomendação J); com a alternativa, `SHIFT+J` ∈ `registered` e ∉ `GAME_KEYS` | `test_orders` |
| T20 | `hudLine` só leitura (snapshot antes/depois igual); `fwdLine` ≤ 96 caracteres; estados | §3.12 |

### 5.2 Roteiro de laboratório (nunca com o robô ativo; um passo por carga; jogo fechado ao terminar)

| # | Passo | Tipo | Saída esperada / critério |
|---|---|---|---|
| L0 | `A1`, `A2` em HomeRegionW | só-leitura | colunas e CDO; decide `visual` e se há coluna de spawn |
| L1 | `A3` em HomeRegionW, CallumsCapeHex, DeadLandsHex | só-leitura | classe da "base avançada" nativa, componentes, bounds colidindo → `HALF`; ruínas de base; **sem** crash |
| L2 | Partida com logística; `A4` | só-leitura | ≥ 1 candidato válido com ≥ 3 saídas por ponto (ou ajustar `HALF`/anel); saídas da base principal |
| L3 | **B1** ensaio de spawn do `BPForwardBase1_C` (com autorização) num XYZ validado: ler `Health/MaxHealth/CodeName/TeamId/BaseStructureClass`; 255 vs 1; observar 60 s o `UE4SS.log` e um soldado morto; `K2_DestroyActor`; spawn de `BPDestroyedForwardBase1_C`; captura de tela (`um win shot`); ms do spawn | escrita temporária, desfeita | nasce íntegro (1725) ou adota o plano B; sem `Registry`/respawn nativo; sem ator residual |
| L4 | Partida real no hex: reforço da base principal (ator nasce na saída, não ao lado do esquadrão), refuse sem camisa/fuzil | validação | mensagens; razão; soldado fora de telhado |
| L5 | J, J: construir base no ponto com bmat; medir ms; soldado nasce na saída da base; rodízio das 3+ saídas | validação | débito só após spawn; quadro sem engasgo; sem soldado em telhado/parede |
| L6 | Caminhão (`L`) leva camisas/fuzis à base e ela passa a reforçar; limite de 15 slots | validação | teto respeitado |
| L7 | Pedido pendente com consumo contínuo; painel `guarda 300` | validação | constrói sozinho; sem fome de munição prolongada |
| L8 | Inimigo toma o ponto: base destruída, estoque perdido uma vez, ruína/ator removido; morteiro inimigo | validação | sem ator residual; razão fecha |
| L9 | Salvar (30 s) → fechar → Ctrl+F6 em carga nova: base refeita no mesmo lugar, estoque e HP corretos, sem duplicar; save adulterado recusa | validação | tolerâncias `PERSIST.tol` |
| L10 | Prolongado (≥ 10 min, 3 bases, reforços contínuos): `UE4SS.log` sem erro, memória de atores estável, sem queda nativa | estabilidade | gate; lembrar que a estabilidade do contorno ainda está pendente (MODLOG) |

Pré-requisito geral: a pausa de estabilidade do MODLOG ("não ampliar features antes de isolar a queda") continua valendo; esta
especificação não autoriza abrir o laboratório nem iniciar a etapa 2.

---

## 6. Decisões abertas (para o usuário/coordenador)

- **D1.** Criar a base com **J sobre ponto próprio + confirmação** (recomendado, sem tecla nova) ou com **Shift+J**.
- **D2.** Ponto de controle sem base **deixa de ser local de reforço** no ramo logístico (consequência da decisão de
  design), com `CFG.SPAWN.pointSpawn` para voltar ao antigo.
- **D3.** Pagar com **`logi.bmat` da fábrica** + pedido pendente com reserva (recomendado) ou recusar quando faltar bmat.
- **D4.** Bases só **sobre pontos de controle próprios** na v1 (reaproveita depósito, save por índice, captura); bases
  livres (fora de pontos) ficam para depois.
- **D5.** Inimigo **não constrói** bases na v1 (§3.10), com a assimetria declarada.
- **D6.** Assalto sem bases e com mão de obra abstrata (mantido).
- **D7.** `StoredItemCapacity = 15` lido como **15 slots de caixa** (§1.1) até a sonda provar outra coisa.
