# ENSAIO_INTEGRACAO — pilha completa de patches, offline (2026-10-09)

Agente ENSAIO_INTEGRACAO. Montei a pilha ECONOMIA → IA_LOGISTICA → INTERFACE (rebaseada) → PERSISTENCIA sobre uma
**cópia** do `main.lua` e rodei toda a bateria contra ela. **Nada foi aplicado** ao `main.lua` real (SHA256
`33d6c7e5920a3b5e00b7f3bafbc7b8a86c984db810217241a567afe0901ee679` antes e depois, conferido no build e no fim dos
testes). Não toquei docs compartilhadas, pastas de outros agentes, laboratório, jogo, canal, nem entrada de teclado/mouse.
Dos builds alheios só importei as funções puras `build`/`build_on` (sem bytecode, sem executar os blocos `__main__`),
então nada foi escrito fora desta pasta.

**Estado honesto:** a pilha **compõe e passa toda a bateria offline**. Isso **não** significa pronta para jogo:
nada aqui prova física Unreal, rota, UMG, input, desempenho, equilíbrio nem save em disco real.

## 1. Ordem final e por quê

```
main.lua real (ESTABILIDADE já integrada)
 1. ECONOMIA        dados/paralel/economia/build_patch.py        build(texto)
 2. IA_LOGISTICA    dados/paralel/ia_logistica/build_patch.py    build(texto)[0]
 3. INTERFACE       painel REBASEADO (build_pilha.interface_build): troca a função logi.hudLine inteira
 4. PERSISTENCIA    dados/paralel/persistencia/build_patch.py    build_on(texto)
 (ESTRADAS: não aplicada)
```

- **ECONOMIA antes da INTERFACE.** O gerador da ECONOMIA ancora no fim de `logi.hudLine` original
  (`table.concat(deps, " | "), foe)\nend`) e injeta `logi.extraHud()` ali. O `painel.patch` original apaga essa âncora.
  Reproduzido no passo 10 do teste: `painel.patch` aplica sozinho no main atual, mas o `build` da ECONOMIA depois dele
  falha com "âncora não única ... table.concat(deps". Com a ECONOMIA primeiro, `extraHud` (inserida *antes* de
  `hudLine`) sobrevive à troca da função.
- **IA antes da PERSISTENCIA.** A IA ancora na linha original de `sv.load` (`pcall(logi.restore, d.logi)`), que a
  PERSISTENCIA remove; `build_on` já reconhece a variante da IA.
- **IA e INTERFACE comutam.** Como o painel rebaseado substitui a *função inteira* por limites de texto, a ordem
  ECONOMIA → INTERFACE → IA → PERSISTENCIA produz **exatamente o mesmo texto** (passo 11). Escolhi IA antes porque foi
  como a IA a testou e porque deixa a âncora opcional do HUD dela ser consumida (e depois descartada pela troca).
- **ESTRADAS fora.** Sem driver integrável; só confirmei que nada da pilha quebra o contrato (seção 5).

### Entregáveis nesta pasta

| Arquivo | O que é |
|---|---|
| `build_pilha.py` | monta a pilha em memória (âncoras únicas, para no primeiro erro com mensagem clara: `ETAPA <nome> FALHOU`), grava os arquivos abaixo, confere SHA256 do main real |
| `candidato/main.lua` | candidato completo, **CRLF** como o real (315 531 bytes, 6245 linhas, +1172 sobre as 5073 do real) |
| `candidato/SHA256.txt` | SHA256 do main real antes/depois (iguais) e do candidato |
| `pilha.diff` | diff unificado **main real → candidato**, em **CRLF** (aplica direto no `main.lua` real com `git apply -p1`/`patch -p1`; testado: reproduz o candidato byte a byte) |
| `pilha_lf.diff` | o mesmo diff em LF, só para leitura |
| `painel_rebase.patch` | passo INTERFACE: `main+ECONOMIA+IA` → `+painel rebaseado` (LF, 80 linhas) |
| `test_pilha.py` | bateria completa (17 etapas); saída detalhada em `saida_testes.txt` |
| `saida_testes.txt` | saída capturada da última execução |

> **Atualização:** existe também a **pilha v2** (seção "Pilha v2" no fim deste arquivo; `candidato_v2/`, `pilha_v2.diff`).
> Tudo antes dela descreve a pilha v1, que continua reproduzível.

Reproduzir (bash, raiz do repo):

```bash
PYTHONPATH=D:/tools/pylibs PYTHONDONTWRITEBYTECODE=1 python dados/paralel/ensaio_integracao/build_pilha.py
PYTHONPATH=D:/tools/pylibs PYTHONDONTWRITEBYTECODE=1 python dados/paralel/ensaio_integracao/test_pilha.py
```

Etapas do build (linhas +/- sobre o texto anterior): ECONOMIA +203/-65, IA_LOGISTICA +516/-45, INTERFACE +52/-16,
PERSISTENCIA +582/-55.

## 2. Conflitos encontrados e como foram resolvidos

1. **ECONOMIA × `painel.patch`** (conhecido): âncora `table.concat(deps, " | "), foe)` some. Resolução: ordem
   (ECONOMIA primeiro) + painel rebaseado por função inteira, não por contexto de linha.
2. **`painel.lua` sem a reconciliação.** `painel.lua` não chama `extraHud`, não conhece o estado `returnCargo` da ECONOMIA e
   lia `combat.cargo` na linha do inimigo. O rebase aplica, com âncoras únicas e fail-closed, os 4 hunks de
   `interface/reconciliacao_extraHud.patch` (nome/destino de `returnCargo`; `cargo.ammo/shirts or 0`; chamada opcional
   de `logi.extraHud`) **e duas mudanças minhas** (listadas abaixo para o coordenador revisar):
   - linha INIMIGO: se `logi.eHud` existe (IA integrada), usa a linha dela ("INIMIGO: frente equipa N ... comboios ...
     perdidos"); senão mantém a linha antiga `INIMIGO | carga N`. Motivo: com a IA, `combat.cargo` virou alias de
     "soldados que a frente equipa" e a linha antiga mostraria um número sem o sentido de antes (a própria IA recomendou
     usar `logi.eHud()`). `eHud()` vazio (sem cadeia) não gera linha. Em assalto continua sem linha inimiga.
   - carga do caminhão: acrescenta ` + N fuzis` / ` + N bandagens` quando existem (sem isso um caminhão só com fuzis
     aparecia como "0 munição + 0 camisas (caixas)", enganoso).
3. **Fim de linha misto nos `.patch` entregues:** `economia_integrada.patch`, `ia_logistica.patch`, `painel.patch` estão
   em **CRLF** (gravados com `write_text` no Windows); `persistencia*.patch` e `reconciliacao_extraHud.patch` em LF. O
   `main.lua` é CRLF. Por isso `git apply` direto falha para metade deles dependendo do arquivo. Meu teste normaliza
   para LF e aplica em sequência; **resultado byte a byte igual ao candidato** (passo 10). Recomendo aplicar via
   `pilha.diff` (CRLF, aplica no main real) ou copiar `candidato/main.lua`, não encadear os `.patch` à mão.
4. **`economia/test_existing.py`** roda `tools/test_orders.py` contra o build da ECONOMIA **sem** trocar o bloco "enemy
   convoy"; com a IA integrada esse bloco antigo não vale mais (a IA removeu o contrato abstrato `cargo0/perWave/cut`).
   Substituído na bateria pela execução do `test_orders.py` com o bloco de `ia_logistica/test_orders_bloco_comboio.lua`
   (passo 03b). Não executei `test_existing.py` nem `economia/test_economia.py` (módulo puro `economia.lua`, que a própria
   ECONOMIA diz **não** carregar junto da integração).
5. **`sv.enemySnapshot` × IA:** devolve `nil` quando `logi.eSnapshot` existe (a IA é dona do estado inimigo via `elogi`).
   Sem conflito; mas os contadores `combat.convoys`/`combat.convoysCut` (só exibição) **não** são persistidos na
   pilha com IA e voltam a 0 no continue. A fonte de verdade (`led.lost`, razão) é salva. Cosmético.

Nenhum outro conflito de âncora entre ECONOMIA, IA e PERSISTENCIA (já tinham sido compostas por eles; reconfirmado).

## 3. Contagem de locais de topo (limite 200 por chunk)

| Medida | main real | candidato |
|---|---|---|
| Compilador (Lua 5.4 = UE4SS **e** 5.5; maior nº de locais extras que ainda compila) | **178** ativos (folga 22) | **178** ativos (folga 22) |
| Contagem por regex de `tools/check_globals.py` (limite do aviso: 180) | 175 | 175 |

Nenhuma etapa da pilha (ECONOMIA, IA, INTERFACE, PERSISTENCIA) adicionou local de topo: tudo em `logi`, `sv`, `CFG`.
`check_globals.py` no candidato: **rc=0, sem nenhuma saída** (nem avisos de sombra de nome de topo).

## 4. Teclas, `env` do canal, funções e campos novos

- **Teclas novas: nenhuma.** `RegisterKeyBind` do candidato é idêntico ao do main real e `HELP_TEXT` também. O painel
  só cita teclas existentes (Ctrl+L, Q/E, Espaço). Logo `tools/test_orders.py` (teste de teclas) e `TESTE_MANUAL.md`
  não ganham tecla nova. Mas o **README/TESTE_MANUAL precisam descrever**: Shift+L agora cicla prioridade também para
  fuzis/bandagens; recrutar fuzileiro exige 1 fuzil + 1 camisa; médico só trata com bandagem em depósito aliado perto;
  cadeia inimiga (alerta de comboio com `byCut`); painel multilinha; save v2 (infraestrutura/carteira, recusas,
  autosave suspenso em continuação incompleta, arquivos `save.txt.tmp/.bak/.corrupt`).
- **`env` de `runCommandFile`: nenhuma entrada nova necessária.** Já exporta `logi`, `sv`, `CFG`, `combat`, `S`, `ai`,
  `fort`, `points`, `economy`; tudo que a pilha adiciona fica nessas tabelas e é acessível.
- **Funções novas** (diff de `^function X.y(` real × candidato; nada removido):
  - `logi`: `needs`, `moveCargo`, `medicalDepot`, `extraHud`, `validateSave` (ECONOMIA); `eActive eAfford eAudit eCommit
    eConsume eDeliver eEvent eFmt eHave eHome eHud eLoad eLose eNeed eNextKind eReport eReset eRestore eSnapshot
    eSoldiers eStuck eTick eTransit eUnits eValid` (IA; `eAudit`, `eReport` são as de canal); `walletId`, `applyPlan`
    (PERSISTENCIA).
  - `sv`: `decode parseSave pure readFile writeAtomic validate verify preflight infraPlan infraSnapshot enemySnapshot
    sameBuilt siteSpec worldPath` (PERSISTENCIA; `sv.parse` agora só decodifica).
  - Campos de estado: `logi.en` (cadeia inimiga), `logi.fac/depots` com `rifle`/`medical`, `tr.cargo` genérico por
    produto, `tr.state == "returnCargo"`, `S.deploy` com `budget/built`, `sv.degraded`, `sv.lastWritten`.
  - `CFG` novos: `CFG.ECHAIN`, `CFG.PERSIST`; `CFG.LOGI` ganha `products`, `want.rifle/medical`, `recipes.rifle/medical`;
    `CFG.ECONVOY` perde `cargo0/perWave/cut`.
- **Formato de save:** v2 (lê v1). `save.txt` + `.tmp/.bak/.corrupt`.

## 5. Contrato ESTRADAS (driver devolve `true` só na chegada; `tr.routeStatus`)

Sem alteração do contrato; verificado em quatro frentes (passos 05, 06, 08 e 09):
- **Estático:** `function logi.drive(` tem uma única definição (ponto de troca) e os 7 usos no candidato consomem o
  retorno dentro de `if`/`elseif`; nenhum ignora o valor.
- **Jogador (`toDep`):** com `drive` devolvendo `false` (e `routeStatus` em `rota_ausente`, `bloqueado`,
  `regiao_invalida`) 30 ticks cada, nenhuma entrega, carga fica no caminhão; `true` entrega uma única vez.
- **`returnCargo`:** destino capturado → `state="returnCargo"`, `dest=logi.factory`, sem crédito; `false` mantém tudo;
  só `true` devolve as caixas fechadas à fábrica, uma vez, sem duplicar (conservação).
- **Comboio inimigo (IA):** rota ausente por `ECHAIN.stuck` s → volta carregado (`back`), frente não recebe; crédito na
  retaguarda só quando o driver devolve `true` (`logi.eHome`); razão `eAudit` fecha.
- **Salvar/restaurar** não credita nada durante o retorno (ECONOMIA + PERSISTENCIA passam no mesmo candidato).

**Pendência do lado ESTRADAS (achada aqui, não corrigi):** `dados/paralel/estradas/native_adapter.lua`,
`adapter.returnCargo`, ainda credita `factory.ammo/factory.shirts` com `tr.cargo.ammo/shirts` (cargo de 2 produtos).
No candidato o retorno é inline em `logi.truckStep` e credita via `logi.moveCargo(tr.cargo, logi.fac, false)` (4
produtos, `logi.fac`). Quando o driver da ESTRADAS for integrado, **não usar `adapter.returnCargo` como está**: perderia
fuzis/bandagens e erraria o alvo do crédito. Idem `RETURN_PATCH.lua` (versão de 2 produtos), já superado pelo patch da
ECONOMIA.

## 6. Resultado dos testes (execução final)

`python dados/paralel/ensaio_integracao/test_pilha.py` → **17 etapas, 17 PASS, 0 FAIL** (Python 3.14.3, lupa 2.8):

```
PASS  00 integridade: build reproduz candidato/main.lua (CRLF) e main.lua real intacto
PASS  01 sintaxe (lupa Lua 5.4 = UE4SS e 5.5) + limite de 200 locais por chunk
      -> check_globals: main real 175 -> candidato 175; compilador: 178 ativos (folga 22) em Lua 5.4 e 5.5
PASS  02 tools/check_globals.py contra o candidato -> rc=0, sem saida (main real: rc=0)
PASS  03a tools/test_orders.py no main real (controle, sem mudanca)
PASS  03b tools/test_orders.py contra o candidato (bloco 'enemy convoy' da IA)
PASS  04 tools/test_costs.py e tools/test_inventory_probe.py (independentes do main.lua)
PASS  05 economia/test_integracao.py contra o candidato
PASS  06 ia_logistica/test_ia_logistica.py contra o candidato (25x600 passos aleatorios + partidas)
PASS  07a interface/test_interface.py original (painel.lua da INTERFACE, mock proprio)
PASS  07b interface/test_interface.py com o logi.hudLine do CANDIDATO (mock proprio, sem extraHud/eHud)
PASS  07c painel no candidato completo: estados, fuzis/bandagens, returnCargo, linha INIMIGO da IA, so leitura
PASS  08 persistencia/test_persistencia.py contra o candidato (Lua 5.4 e 5.5, 9 cenarios = 18 casos)
PASS  09 contrato ESTRADAS: driver true so na chegada / routeStatus (jogador, returnCargo, comboio inimigo)
PASS  10 conflitos e patches entregues: painel.patch x ECONOMIA reproduzido; sequencia dos .patch e pilha.diff aplicam limpo
PASS  11 ordem alternativa ECONOMIA>INTERFACE>IA>PERSISTENCIA produz o MESMO texto
PASS  12 candidato nao toca o ESTRADAS e nao deixa residuos do contrato abstrato antigo
PASS  99 main.lua real intacto ao fim (SHA256 33d6c7e5920a...)
```

Como cada suíte alheia foi apontada para o candidato (nenhum original editado; `exec` de uma cópia do código com a
linha de obtenção do candidato trocada, mesma técnica de `ia_logistica/test_orders_candidato.py` e
`persistencia/test_regressao.py`):

| Suíte | Adaptação em memória |
|---|---|
| `tools/test_orders.py` | `source = candidato`; bloco "enemy convoy" trocado por `ia_logistica/test_orders_bloco_comboio.lua` (03b); controle sem mudança no main real (03a) |
| `tools/test_costs.py`, `tools/test_inventory_probe.py` | não leem o `main.lua` (verificado por texto): rodados como estão |
| `economia/test_integracao.py` | `proposal = candidato` (executa o chunk inteiro; `ROOT` injetado) |
| `ia_logistica/test_ia_logistica.py` | `stacked = candidato`; 25 sementes × 600 passos aleatórios com `eAudit` + 4 partidas completas, rodadas na pilha completa |
| `interface/test_interface.py` | original (07a) e com o `hudLine` extraído do candidato no lugar de `painel.lua` (07b); teste novo 07c no chunk completo |
| `persistencia/test_persistencia.py` | `STACKS` reduzido a 1 pilha = candidato completo (9 cenários × Lua 5.4/5.5) |

**Teste novo 07c (painel integrado):** estados (`returnCargo`, `toDep`, `idle` de recurso, `dead`), fuzis/bandagens na
carga e em `extraHud`, linha INIMIGO da IA (sem a linha antiga), assalto sem linha inimiga, logística inativa, cargo com
campos ausentes, e `hudLine` **não altera** estado (`sv.ser` de `snapshot` + `eSnapshot` igual antes/depois).
Primeira renderização do teste = **12 linhas, até 222 caracteres de largura** (4 caminhões, 2 depósitos); amostra real:

```
LOGÍSTICA | sucata 12 | bmat 100 | prioridade auto
Fábrica | fuzis: 4 s restantes (total 70 s)
Pronto | munição 1 caixas | camisas 2 caixas (20 unidades)
base | munição 6 | camisas 30
A | munição 1 | camisas 0 | abaixo da meta
Caminhão 1 | retornando carga à fábrica | 1 munição + 2 camisas (caixas) + 1 fuzis + 1 bandagens | destino fábrica
Caminhão 2 | ao depósito | 0 munição + 0 camisas (caixas) + 2 fuzis + 1 bandagens | destino A
Caminhão 3 | iniciando coleta | 0 sucata | destino campo
Caminhão 4 | destruído | perdida | destino —
INIMIGO: frente equipa 10 (m2.0 c10) | retaguarda bmat 240, cx m0 c0 | comboios 0 na estrada, 0 perdidos
Ctrl+L: foco na cadeia | Q/E: frentes | Espaço: último alerta
Fuzis: fábrica 3 caixas | bandagens: fábrica 4 caixas | base: 2 fuzis, 5 bandagens | A: 0 fuzis, 0 bandagens | caminhão 1 -> fábrica: 1 caixas fuzis, 1 caixas bandagens | caminhão 2 -> A: 2 caixas fuzis, 1 caixas bandagens
```

**Os testes não são vácuos (mutação, fora da entrega):** 6 mutações no candidato foram pegas — returnCargo creditando
sem chegada (05, 09); painel sem `returnCargo` (07c); comboio inimigo entregando sem driver (03b, 06, 09); save v=3
(08); `hudLine` escrevendo estoque (07c); `validateSave` da ECONOMIA desligada (08).

## 7. Riscos e limites

- **Painel (gate visual):** pior caso 12 linhas e a última (`extraHud`) é uma linha única de ~200 caracteres; o
  `hudTick` usa um TextBlock com `SetAutoSize`. Sem clipping/scroll provados (a INTERFACE já avisava). Se estourar a tela,
  reconverter `extraHud` em várias linhas (por produto) em vez de esconder estoques.
- **Painel × IA:** a linha INIMIGO mudou de forma (de "carga N" para o resumo da cadeia). Decisão minha, descrita em 2.
- **Orquestração futura:** depois de aplicar a pilha, os `build_patch.py` das 3 pastas **deixam de funcionar** sobre o
  novo main (âncoras já aplicadas; `build_on` aborta com "persistência já aplicada"), e `test_integracao.py`,
  `test_ia_logistica.py`, `test_persistencia.py`, `test_orders_candidato.py` e `test_regressao.py` ainda importam esses
  builds. A bateria permanente deve passar a apontar para o `main.lua` real (trocar a linha de obtenção do candidato
  como faço aqui) e `tools/test_orders.py` precisa do bloco do comboio trocado de forma definitiva.
- **Contadores de comboio:** `combat.convoys/convoysCut` não persistem com IA (cosmético, ver 2.5).
- **Arquivos novos em disco no laboratório:** `save.txt.tmp`, `.bak`, `.corrupt`; leitura de `.bak` pode trazer save até
  30 s mais velho (avisado na tela).
- **Escassez de grande risco de equilíbrio (IA):** interdição total leva ondas ao piso de 3; parâmetros em `CFG.ECHAIN`.
- **Limitações assumidas das entregas (não resolvidas pela pilha):** ECONOMIA: granada impossível (falta Explosive);
  cura passiva de pontos/postos e composição inicial/recompensa/F6 continuam grátis. IA: munição inimiga no tiro,
  morteiro e fortificações inimigas continuam abstratos; retaguarda fora do mapa não pode ser atacada. PERSISTENCIA:
  mudança de layout do hex invalida o save (recusa, não inventa).
- **Transporte continua em linha reta** até o driver da ESTRADAS: a pilha só garante que a lógica de carga/retorno/
  perda é correta *quando* o driver for confiável.

## 8. O que exige laboratório (gates abertos copiados dos RELATÓRIOS)

**ECONOMIA:** aplicação sequencial real + reconciliação do painel; globals/sintaxe (feito aqui offline); teste ao vivo
receita → produção → transporte → rifle recrutado / bandagem tratada **sem estoques artificiais**; contraste
escassez / corte de transporte / retomada; save em meio a produção e carga; falha de engine **depois** do preflight
(rollback transacional não provado); captura de ponto / novo mapa; legibilidade e equilíbrio; atualizar README/
TESTE_MANUAL (prioridade fuzis/bandagens, suprimento ativo de médico/recrutamento). **Driver atual anda em reta: não usar
como transporte seguro sem integrar o driver ESTRADAS com rota/sweep/chegada.** Granada continua bloqueada (Explosive).

**IA_LOGISTICA** (`ia_logistica/ROTEIRO_LABORATORIO.md`): spawn e movimento do `BPTruckC` com o patch; LOS e alertas;
desempenho por quadro; efeito real na frente com soldados de verdade; equilíbrio (piso de 3 com interdição total);
save/continue real em disco com comboio na estrada; integração com o driver da ESTRADAS; `logi.convoyRoute` ainda
escolhe retaguarda e frente por traços de chão em reta (paradas precisam virar paradas validadas do grafo).

**INTERFACE:** painel em partida com logística ativa, pausa, logística desligada, mapa novo, depósito perdido, caminhão
morto/recriado, com captura e dados do mesmo instante; sobreposição, largura/altura em vários zooms/resoluções, ajuda F5
e alertas nativos; ver se o elenco excede a altura (ajustar layout, não esconder dados); **o usuário** confere
esquerda/Shift/direita/câmera/F5/Ctrl+L/Q/E/Espaço (nenhuma entrada real foi testada). Caixa de seleção por arrasto
**não está entregue** (precisa das sondas UMG/projeção); botões de foco por caminhão e alertas de estoque deduplicados
seguem abertos. Troca de mapa: não confundir `IsValid` do widget antigo com o mundo atual.

**PERSISTENCIA** (`persistencia/ROTEIRO_LABORATORIO.md`): `io.open("rb"/"wb")`, `f:seek`, `os.rename`/`os.remove` no Lua do
UE4SS/Windows; spawn real refazendo a infraestrutura numa carga nova do hex com ruína/yaw idênticos entre cargas
(tolerâncias 2 m / 1° são hipótese); `GetFullName` do mundo; carga em trânsito retomada com o driver real; custo no
game thread; IA_LOGISTICA ao vivo; queda real entre renames. Matriz do laboratório obrigatória antes de fechar a task.

**ESTRADAS:** driver real (rota, sweep, chegada confirmada, `routeStatus`) integrado e testado ao vivo; exportar schema
das splines; curva real campo → refinaria → fábrica; ponte/água; replano; ms por tick. Adaptar o `adapter.returnCargo`
(ver seção 5) antes de integrar.

**Específico desta pilha (laboratório):** carregar o candidato (via `restart.sh` do coordenador, não por mim) e rodar
uma partida curta com logística ligada: painel legível, produção de fuzis/bandagens, comboio inimigo, Ctrl+F6 depois de
Alt+L; conferir `UE4SS.log` sem erro de Lua nos primeiros 5 minutos; gravar HUD de 12 linhas em vários zooms.

## 9. Como aplicar (para o coordenador, quando decidir)

1. Conferir que o `main.lua` real ainda tem o SHA256 acima (senão refazer `build_pilha.py`).
2. Copiar `candidato/main.lua` por cima do real **ou** aplicar `pilha.diff` (CRLF) com `git apply -p1`/`patch -p1`
   na raiz (o resultado é idêntico byte a byte, testado em diretório temporário).
3. Trocar em `tools/test_orders.py` o bloco "enemy convoy" pelo de `ia_logistica/test_orders_bloco_comboio.lua`; incluir
   na bateria os testes novos das três entregas apontando para o `main.lua` real.
4. Rodar `check_globals.py` e a bateria; só então laboratório.
5. Registrar no `MODLOG.md`; gotchas já propostos estão em `ia_logistica/GOTCHAS_PROPOSTOS.md` e
   `persistencia/GOTCHAS_PROPOSTOS.md`; novos gotchas desta rodada para a nota `knowledge/games/foxhole/...`:
   (a) `.patch` gravados com `write_text` no Windows saem CRLF — usar `newline="\n"` ou aplicar por script;
   (b) um painel que substitui função inteira por limites de texto comuta com patches que ancoram dentro dela;
   (c) adaptador de retorno de carga de 2 produtos fica obsoleto quando a economia generaliza produtos.

---

# Pilha v2 (entregas de `ia_logistica/acabamento/`) — 2026-10-09

A pilha v1 acima continua reproduzível e **inalterada** (`build_pilha.py v1`; hash do `candidato/main.lua` igual ao de
antes: `fe91ce776eec7f2c79a41223e1430f4bd9f37d9ba0e9d317daf2bf07b48765ed`). A v2 é uma variante nova; nada foi aplicado
ao `main.lua` real (SHA256 igual antes/depois em build e testes) e nada foi editado em `acabamento/` (só leitura; as
funções puras `build`/`build_on`/`apply` foram importadas sem bytecode).

## V2.1 Ordem e candidato

```
main.lua real
 1. ECONOMIA          economia/build_patch.py                       build
 2. IA_LOGISTICA v2   acabamento/build_patch_v2.py                  build()[0]   (CFG.ECHAIN free 5, want 4/20, trip 20; eRestore(d, dropped))
 3. reserva de bmat   acabamento/patch_reserva_bmat.py              apply        (logi.rebuildReserve + guarda em logi.factoryStep)
 4. INTERFACE v2      build_pilha.interface_build(s, v2=True)       painel rebaseado + estado da reserva + piso gratis
 5. PERSISTENCIA v2   acabamento/build_persistencia_v2.py           build_on     (elogi: descarta so a secao)
```

**SHA256 do `candidato_v2/main.lua` (CRLF): `a93c1531588ea4534a7791dbb2e9578654ad0fa4a87373be1cbed569cbc3eda6`**
(319 236 bytes, 6302 linhas). Main real: `33d6c7e5920a3b5e00b7f3bafbc7b8a86c984db810217241a567afe0901ee679` (antes = depois).

Etapas (+/- linhas): ECONOMIA +203/-65, IA v2 +528/-45, reserva +16/-0, INTERFACE v2 +61/-16, PERSISTENCIA v2 +602/-55.

Comutação (passo 11, texto idêntico byte a byte nas 4 ordens, além da principal): `ECO>IA>INTERFACE>reserva>PERS`,
`ECO>INTERFACE>IA>reserva>PERS`, `ECO>INTERFACE>reserva>IA>PERS`, `ECO>IA>reserva>PERS>INTERFACE`. A posição do painel e
da reserva é indiferente; só IA→PERSISTENCIA e ECONOMIA antes da INTERFACE são obrigatórias.

Arquivos novos: `candidato_v2/main.lua`, `candidato_v2/SHA256.txt`, `pilha_v2.diff` (CRLF, aplica direto no main real;
testado, reproduz o candidato byte a byte), `pilha_v2_lf.diff`, `painel_rebase_v2.patch` (LF, etapa 3 → 4),
`saida_testes_v2.txt`. Reproduzir:

```bash
PYTHONPATH=D:/tools/pylibs PYTHONDONTWRITEBYTECODE=1 python dados/paralel/ensaio_integracao/build_pilha.py v2     # ou: all
PYTHONPATH=D:/tools/pylibs PYTHONDONTWRITEBYTECODE=1 python dados/paralel/ensaio_integracao/test_pilha.py v2
```

## V2.2 Resultado dos testes (20 etapas, 20 PASS, 0 FAIL)

| Etapa | Resultado |
|---|---|
| 00 integridade (candidato_v2 em CRLF == build; main real intacto) | PASS |
| 01 sintaxe Lua 5.4 e 5.5 + locais: compilador **178** ativos (folga 22), regex do check_globals **175**, igual ao main real; nenhuma etapa adiciona local | PASS |
| 02 `tools/check_globals.py` no candidato_v2 | PASS (rc=0, sem saída, sem avisos) |
| 03a `tools/test_orders.py` no main real (controle) | PASS |
| 03b `tools/test_orders.py` no candidato_v2 com `test_orders_bloco_comboio_v2.lua` | PASS |
| 04 `tools/test_costs.py`, `tools/test_inventory_probe.py` (independentes do main) | PASS |
| 05 `economia/test_integracao.py` | PASS |
| 06 `acabamento/test_ia_logistica_v2.py` (25×600 passos + partidas, na pilha completa) | PASS |
| 06b `acabamento/test_elogi.py` (Lua 5.4/5.5; candidato_v2 + cenário "mod sem IA") | PASS (12 casos) |
| 06c `acabamento/test_bmat_caminhao.py` (hipótese sem patch; com patch o caminhão volta; pilha completa = candidato_v2) | PASS |
| 07a `interface/test_interface.py` original | PASS |
| 07b `interface/test_interface.py` com o `hudLine` do candidato_v2 | PASS |
| 07c painel integrado (estados, returnCargo, fuzis/bandagens, linha INIMIGO da IA, só leitura) | PASS |
| **07d painel v2 (novo): reserva de bmat e linha INIMIGO com piso `free=5`** | PASS |
| 08 `acabamento/test_persistencia_v2.py` (9 cenários × Lua 5.4/5.5 × 2 pilhas: sem IA e candidato_v2) | PASS (36 casos) |
| 09 contrato ESTRADAS (7 usos de `logi.drive`, todos condicionais; false nunca entrega; returnCargo; comboio) | PASS |
| 10 conflito `painel.patch`×ECONOMIA reproduzido; `economia_integrada > ia_logistica_v2 > reserva_bmat > painel_rebase_v2 > persistencia_v2_sobre_ia` aplicam em sequência e == candidato; `pilha_v2.diff` aplica no main real | PASS |
| 11 quatro ordens alternativas == candidato | PASS |
| 12 sem resíduos do contrato abstrato; calibração `free 5 / trip 20.0 / want 4,20`; `rebuildReserve` única | PASS |
| 99 main real intacto ao fim | PASS |

Notas: `test_elogi.py` e `test_persistencia_v2.py` rodam com 2 pilhas (a "sem IA" é necessária ao caso "mod sem o módulo";
a outra é **o candidato_v2 completo, com INTERFACE**) em vez das 3 originais deles (as pilhas só com IA e sem INTERFACE
ficam cobertas por `acabamento/rodar_tudo.sh`; não rodei esse script nem `sweep_echain.py`, que não dependem do painel).
Não executei `acabamento/test_regressao_v2.py` (cobertura repetida pelos passos 03b/05/06/01/02/11); ele importa
`interface_build` deste arquivo, cuja assinatura continua compatível (`interface_build(s)` = painel v1).

Mutações no candidato_v2 (fora da entrega), todas pegas: reserva = 0 (06c, 07d); painel sem aviso de reserva (07d);
`free` 5→3 (06, 07d, 12); painel sem piso (07d); `sv.validate` recusando tudo por `elogi` inválido (06b, 08).

## V2.3 Painel: estado novo

O painel v1 dizia **"aguarda bmat"** com a fábrica parada, o que é **enganoso na v2**: com um caminhão do jogador destruído a
fábrica deixa de iniciar receita de propósito para juntar 100 bmat, e a única indicação era o toast
`fábrica guarda N bmat para reconstruir caminhão` (3 s, no máximo 1 a cada 20 s). Por isso o painel rebaseado v2 ganhou
(só na variante v2; a v1 ficou intacta):

- **Linha da fábrica:** `Fábrica | guarda 100 bmat para reconstruir caminhão (bmat 130)` quando `logi.rebuildReserve() > 0` e
  `bmat − custo da receita < reserva` (mesma condição de `factoryStep`); `guarda 200` com dois caminhões destruídos;
  volta a `aguarda bmat` (sem caminhão destruído) / `N s restantes` (job iniciado com bmat de sobra) / `parada: demanda
  atendida`. Provado que o painel diz a verdade: nessa condição `factoryStep` de fato não inicia job.
- **Linha INIMIGO com o piso:** `INIMIGO: frente equipa 10 (m2.0 c10) | retaguarda bmat 240, cx m0 c0 | comboios 0 na
  estrada, 0 perdidos | piso grátis 5/onda`. Com a cadeia cortada e a frente zerada: `frente equipa 0 (m0.0 c0) ... | piso grátis
  5/onda`, e `waveCut(13)` devolve exatamente 5 = o número mostrado. Em assalto, sem cadeia (`logi.en` nulo) ou sem logística
  não há linha nem piso; cadeia recusada mostra `cadeia recusada (...)`, sem erro.
- Continua só leitura (snapshot + eSnapshot idênticos antes/depois do `hudLine`).

Cuidado de teste registrado: `retaguarda` contém `guarda`; as asserções de texto do painel usam `Fábrica | guarda`.

Amostra (07d):

```
Fábrica | guarda 100 bmat para reconstruir caminhão (bmat 130)
INIMIGO: frente equipa 10 (m2.0 c10) | retaguarda bmat 240, cx m0 c0 | comboios 0 na estrada, 0 perdidos | piso grátis 5/onda
INIMIGO: frente equipa 0 (m0.0 c0) | retaguarda bmat 240, cx m0 c0 | comboios 0 na estrada, 0 perdidos | piso grátis 5/onda
```

A linha INIMIGO passa a ter ~125 caracteres; o painel completo continua em 12 linhas no pior caso do teste 07c (gate
visual do laboratório, como antes).

## V2.4 Conflitos novos (v2 em relação à v1)

1. **Nenhum conflito de âncora novo.** `reserva_bmat` ancora dentro de `logi.factoryStep` (linha da receita da ECONOMIA) e
   em `function logi.factoryStep(`: não toca o HUD nem o save; comuta com IA v2, INTERFACE e PERSISTENCIA v2.
2. **Fim de linha dos `.patch` de `acabamento/`:** `ia_logistica_v2.patch` em **CRLF** (mesmo vício de `write_text` no
   Windows); `reserva_bmat.patch`, `persistencia_v2_sobre_ia.patch` e `painel_rebase_v2.patch` em LF. O encadeamento só aplica
   depois de normalizar para LF (feito no teste). Use `pilha_v2.diff` ou `candidato_v2/main.lua`.
3. **`persistencia_v2_sobre_ia.patch`** foi gerado sobre `ECO+IA2+reserva` (sem INTERFACE) e mesmo assim aplica limpo
   depois da INTERFACE (contexto longe do HUD), confirmado byte a byte.
4. **Painel × reserva:** o rótulo `aguarda bmat` ficou incorreto com a reserva; resolvido no painel v2. O toast continua
   existindo (não é persistente).
5. **Decisões de comportamento para o coordenador** (já apontadas pelo acabamento): a calibração `free 5 / want 4,20 / trip 20`
   e a política "elogi descarta só a seção" (editar o save pode virar atalho de reinício da cadeia inimiga; risco baixo em
   jogo solo offline).
6. **Pendências herdadas, não resolvidas pela v2:** caminhão de **recurso** destruído com bmat=0 e sucata=0 continua sem renda
   para reconstruir (`acabamento/RELATORIO.md` 2.3); estoque de recomeço da cadeia inimiga após `elogi` descartado (3.2);
   `combat.convoys/convoysCut` seguem sem persistir (v1, item 2.5); `adapter.returnCargo` da ESTRADAS defasado (seção 5).
7. **Locais, teclas, `env`:** iguais à v1 (178 pelo compilador, 175 pela regex; nenhuma tecla nova; nada novo no `env`). Única
   função nova em relação à v1: `logi.rebuildReserve` (e o campo `logi.rebuildNoteT`); `logi.eRestore` ganha o 2º parâmetro
   `dropped`. O README precisa dizer, além do que a v1 já pedia: piso/estoque da cadeia inimiga, reserva de bmat para
   reconstruir caminhão (linha "guarda N bmat" no painel) e o aviso `CADEIA INIMIGA REINICIADA` no continue.

## V2.5 O que exige laboratório (acréscimo à seção 8)

Os gates da seção 8 continuam valendo. Acrescentam-se os de `acabamento/RELATORIO.md` §6: medir a cadência real das ondas
(robô e humano) e repetir `sweep_echain.py` com as lutas reais; tempo real do ciclo do caminhão de recurso (`trip`);
`logi.eReport()` com a calibração v2 (`byCut`, perdas, pressão); matar um caminhão de suprimento sob consumo alto, ver o toast
e a linha "guarda N bmat" e o caminhão voltar em < 60 s; editar `save.txt` (corromper `elogi`, `v=2`), Ctrl+F6, conferir o
aviso de 10 s, o jogador intacto e o autosave seguinte. Visual: a linha INIMIGO ampliada e a linha da fábrica com a reserva
em vários zooms/resoluções.
