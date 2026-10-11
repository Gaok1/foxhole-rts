# IA_LOGISTICA + PERSISTENCIA: acabamento (2026-10-09)

Agente de acabamento das tasks IA_LOGISTICA e PERSISTENCIA. Trabalho todo offline, **só nesta pasta**
(`dados/paralel/ia_logistica/acabamento/`). Não editei `main.lua`, docs compartilhadas, os arquivos originais de
`ia_logistica/`, `persistencia/` e `economia/`, o laboratório ou o jogo (conferido: nenhum arquivo fora desta pasta
mudou desde que comecei). Variantes são **cópias** com diff contra o original em `diffs/`.

**Estado honesto:** tudo abaixo está provado **offline** (lupa, `main.lua` candidato inteiro em memória). Equilíbrio
real, cadência real das ondas, caminhão BPTruckC real, save em disco real e o HUD ao vivo continuam sendo gates do
laboratório. As duas tasks seguem `[ . ]`.

Resultado da bateria: `bash dados/paralel/ia_logistica/acabamento/rodar_tudo.sh` → **TUDO PASS** (`SAIDA_TESTES.txt`).

| Item | Resultado |
|---|---|
| 1. Calibração `CFG.ECHAIN` | Propostos `free` 3→**5**, `want` 6/30→**4/20**, `trip` 25→**20**; `front0`, `minLoad`, `bmat0` ficam. Critérios explícitos atendidos nas duas cadências; só 6 de 144 combinações passam, todas com `free` 5. |
| 2. bmat × caminhão do jogador | **Hipótese confirmada** offline, mas a causa **não é a ordem** fábrica/caminhão: é o limiar (receita 80 bmat < caminhão 100). Patch isolado `patch_reserva_bmat.py` corrige; teste falha antes e passa depois. |
| 3. Reconciliação `elogi` | Política única: **descarta só a seção `elogi`**, reinicia a cadeia inimiga do estoque de cenário com aviso explícito, preserva o resto do save. 22 casos novos + `test_persistencia` adaptado (54 casos). |

## 1. Calibração de `CFG.ECHAIN`

### 1.1 Método

- `simlib.py` carrega o candidato inteiro (main + ECONOMIA + IA) num runtime Lua e roda partidas por `logi.tick` +
  `waveTick` reais; só as fronteiras de engine são falsas (mesmo harness de `test_ia_logistica.py`). `sweep_echain.py`
  varre os parâmetros (a luta de cada onda dura `fight` s e some, como no teste original).
- **Duas cadências** (luta de 45 s → onda a cada ~60 s; luta de 90 s → ~105 s). O MODLOG registra ~39–53 s por onda
  no robô, então a de 60 s é a realista para o robô e a de 105 s para um humano mais lento. Quanto vale a cadência
  real é gate do laboratório.
- Cenários: **controle** (sem corte); **T** corte total desde 0 s (todo comboio em trânsito é destruído); **M** corte
  total a partir da onda 5 (estoque da frente já no alvo); **R** corte até a onda da primeira falta e depois livre
  (recuperação); **P** corte parcial: cada comboio é destruído com probabilidade p ∈ {0,25; 0,5; 0,75}, **20
  sementes** por p; **escassez** (retaguarda sem bmat nem sucata).

### 1.2 Critérios (`sweep_echain.criteria`)

1. **Sem corte, ondas iguais às atuais** (`enviados == pedidos` nas 10 ondas, também em cadência de ~45 s).
2. **Corte total desde o início**: ondas 1–4 inteiras (a frente tem estoque para "algumas ondas"); média das ondas
   5–10 entre 40% e 65% do pedido; nunca abaixo de 33% do pedido.
3. **Corte total a partir da onda 5**: precisa morder antes da onda 10 (senão interditar no meio do jogo não serve de nada).
4. **Corte parcial**: faltas monotônicas em p, p = 0,25 ≤ 50% e p = 0,75 ≥ 40% das faltas do corte total.
5. **Rastreável**: ≥ 75% dos soldados que faltaram aparecem em `byCut`.
6. **Recuperação**: depois que o corte para, a primeira onda inteira vem em ≤ 3 ondas e ≤ 300 s.
7. Razão (`eAudit`) fechado em todas as execuções.

São critérios **meus**, explícitos e reprodutíveis; não equilíbrio de combate.

### 1.3 O que a varredura mostrou

- **A calibração original não cumpre o critério 1 em cadência rápida.** Sem nenhum corte, `v1` já reduz as ondas
  (`CADENCIAS.txt`: ~50 s por onda faltam 12 soldados; ~30 s faltam 32). Causa: a refinaria satura em 2 bmat/s (4
  sucata/s) e um soldado pago custa ~21 bmat (1 camisa 8 + 1/6 de caixa de munição 13); a retaguarda sustenta ~5,6
  soldados pagos por minuto, e `free` 3 deixa 5–10 pagos nas últimas ondas. Isso **não** é interdição (`byCut` = 0).
  Com `free` 5 o controle é igual ao atual até ~40 s por onda.
- **`trip` é um despenhadeiro, não um dial.** Em `trip` = 25 s a retaguarda já está exatamente no limite da
  refinaria; `trip` ≥ 30 reduz as ondas **sem corte** (`SENSIBILIDADE.txt`). Proposto 20 s (mesmo resultado que 25,
  com margem). O valor real do caminhão de recurso é do laboratório.
- **`free` é o piso e o dial principal.** 3 e 4 derrubam a pressão antes da onda 5 e o piso para 23–31%; 6 deixa o
  corte total em 68% e o corte a partir da onda 5 nem morde. Só 5 atende tudo.
- **`want`/`front0` definem quantas ondas o estoque da frente dura** (mudando um por vez, `SENSIBILIDADE.txt`):
  `want` 5/25 (as duas cadências) ou 6/30 (a de 105 s) faz o corte a partir da onda 5 não morder antes da onda 10;
  `front0` 3/15 idem, e 4/20 estica o início (média 69%). Fica `front0` 2/10 (inalterado) e `want` 4/20 (3/15 também passa).
- **`minLoad`**: 1 piora a rastreabilidade (comboios de 1 caixa; `byCut` 56%); 3, 5 e 8 passam. Fica 3.
- Testei também um **piso proporcional** (`free` 3–5 + fração 0–40% do pedido; 96 combinações): passa em 20, mas exige
  parâmetro novo e `front0` 2× maior, sem ganho sobre `free` 5. Descartado; arquivo da exploração em
  `GRADE_PISO_PROPORCIONAL_ARQUIVO.txt` (não reproduzível com o código atual, o parâmetro foi removido).

### 1.4 Valores propostos (`ia_logistica_v2.lua`, diff em `diffs/ia_logistica_v2.diff`)

| Parâmetro | Atual | Proposto | Efeito |
|---|---|---|---|
| `free` (piso) | 3 | **5** | corte total vai a 5 soldados por onda (38% da onda 10) em vez de 3 (23%) |
| `want` | 6 / 30 | **4 / 20** | estoque da frente de ~20 soldados; interdição a partir da onda 5 morde na 9 |
| `trip` | 25 s | **20 s** | margem sobre a refinaria; > 25 enfraquece a onda sem corte |
| `front0`, `minLoad`, `bmat0`, `stuck`, `tol` | 2/10, 3, 240, 20 s, 0,05 | iguais | |

Referência do contrato abstrato antigo (corte máximo −4 por onda): média das ondas 5–10 = **63%**. `v1` = 28%, `v2` = 52%.
`free` 6 reproduz ≈ o antigo (68%), mas aí o corte tardio deixa de morder.

### 1.5 Tabela antes/depois (cadência ~60 s; formato `onda:enviados/pedidos`, `[iN]` = N atribuídos à interdição)

Completa (as duas cadências, sementes 1–3) em `TABELA_CALIBRACAO.txt`.

| Cenário | v1 (atual) | v2 (proposto) |
|---|---|---|
| controle | 6 6 7 8 9 10 10 11 12 13 (todas inteiras) | idêntico |
| corte total desde 0 s | 6 6 7 **3**[5] **3**[6] 3[7] 3[7] 3[5] 3[9] 3[1] | 6 6 7 8 **8**[1] **5**[5] 5[5] 5[6] 5[7] 5[8] |
| corte total desde a onda 5 | ondas 1–6 inteiras, 7: **5**/10[5], 8–10: **3** (23%) | ondas 1–8 inteiras, 9: **8**/12[4], 10: **5**/13[8] |
| corte até a 1ª falta, depois livre | 3 3 3 → onda 7 inteira, 8: 6/11, 10: 4/13 | 8/9 5/10 → onda 7 inteira (**2 ondas / 119 s**) |
| escassez | 3 a partir da onda 4 | 5 a partir da onda 6 |
| parcial p = 0,25 / 0,5 / 0,75 (20 sementes) | faltam 20,7 / 32 / 46,5 (40/62/89% do total) | 5,1 / 16,1 / 22,3 (16/50/70%) |
| carga perdida no razão / despachada | 29 / 53 / 85% | 22 / 62 / 77% |

Cadência ~105 s: o estoque da frente absorve cortes pequenos (p = 0,25 não falta nenhum soldado; p = 0,5, 3,6;
p = 0,75, 17,6). O **fluxo** perdido no razão segue p (21 / 50 / 77%): o efeito na onda tem limiar, o rastro no
razão não. As quedas ficam atribuídas em `byCut` (≥ 75% dos que faltaram).

Depois de recuperar, a retaguarda esvaziada pelo corte volta a faltar nas últimas ondas em cadência de 60 s (a
produção não acompanha), o que é a consequência econômica esperada do corte.

### 1.6 Equilíbrio real

**Nada disto confirma equilíbrio.** O modelo mata toda onda em 45/90 s e o jogador não luta contra os soldados que
chegam. Falta no laboratório: (a) medir a cadência real de ondas (robô e humano) e repetir `sweep_echain.py` com
`FIGHTS` reais; (b) tempo real de viagem do caminhão de recurso → `trip`; (c) o que o corte a partir da onda 5
significa para a derrota/vitória do robô; (d) quantas vezes o jogador realmente intercepta comboios (o robô só
emboscou por acaso). Dials, nesta ordem: `free` (±1 = ±15 pontos de pressão com cadeia cortada), `want` (duração do
estoque), `trip` (nunca acima de 25 s sem decidir que o controle deve ser mais fraco).

## 2. Hipótese do jogador: bmat × caminhão

### 2.1 Resultado: **confirmada offline, com outra causa**

`test_bmat_caminhao.py` roda `logi.tick`, `factoryStep`, `truckStep` e `logi.hit` reais do candidato
main+ECONOMIA+IA. Consumo contínuo = os depósitos são esvaziados a cada tick (a fábrica sempre tem o que produzir).

| Situação (consumo contínuo) | Sem correção | Com `patch_reserva_bmat` |
|---|---|---|
| caminhão de suprimento destruído aos 60 s | **não volta em 900 s** (maior bmat visto enquanto esperava: **79**) | volta aos 36,5 s |
| mesma coisa com a fábrica rodando **depois** dos caminhões | **não volta** (idêntico) | volta aos 36,5 s |
| caminhão de recurso destruído aos 60 s | não volta; a economia morre | volta aos 36,5 s |
| varredura do instante da morte, 30–120 s (31 casos) | 0/31 voltam | 31/31, pior caso 49,5 s |
| fábrica parada (estoque cheio) | volta aos 30 s | volta aos 30 s, sem aviso (sem regressão) |

Mecanismo: a fábrica inicia a receita assim que o bmat chega a 80 (fuzil 100); o caminhão pede 100. Sob demanda
contínua o bmat nunca passa de ~79, **qualquer que seja a ordem** das chamadas. Trocar a ordem em `logi.tick` (a
sugestão do IA_LOGISTICA) não corrige. A cadeia inimiga já tinha isto resolvido; o jogador não.

### 2.2 Correção mínima (`patch_reserva_bmat.py`, `reserva_bmat.patch`)

Enquanto houver caminhão destruído, a fábrica só inicia receita se sobrar `LOGI.truckCost` (100) bmat por caminhão
destruído depois de debitá-la (`logi.rebuildReserve`, função em `logi`; sem local de topo, sem CFG novo, sem tecla,
nada no save). Reserva desde a **destruição** (não só quando vence o prazo de 30 s), assim o bmat se acumula durante
a espera. Aviso `fábrica guarda N bmat para reconstruir caminhão` (no máximo a cada 20 s). Aplica-se depois da pilha
ECONOMIA → IA (qualquer versão da IA) e **comuta** com a PERSISTENCIA e com a INTERFACE rebaseada (testado).

### 2.3 Limites e riscos

- **Não resolve a morte do caminhão de recurso com bmat = 0 e sucata = 0** (sem renda para juntar 100). Medido: segue
  destruído com e sem o patch (informativo no teste). Opções, se quiser fechar: reserva permanente de 100 bmat na
  fábrica, ou reconstruir o caminhão de recurso a custo zero (decisão de design, não incluída).
- O HUD mostra "sem bmat" enquanto a fábrica espera; o aviso cobre isso, mas a INTERFACE pode querer um rótulo.
- O consumo "contínuo" é um modelo explícito; no jogo real a fábrica para quando todos os depósitos passam de 2× o
  alvo. A frequência com que isso acontece é gate do laboratório (roteiro abaixo).

## 3. Reconciliação do `elogi` (política única)

### 3.1 Política

> A cadeia inimiga é estado **secundário e regenerável** (estoque de cenário); o resto do save é do jogador.
> Portanto um `elogi` **inválido, de versão futura, ausente, sem a logística do jogador ou lido por um mod sem o
> módulo** não recusa o save. Só **a seção** é descartada; a cadeia inimiga recomeça exatamente do estoque de
> cenário (razão com `inicial` = `front0`, `bmat0`, frota cheia, nada em trânsito) e o jogador é avisado.
> Qualquer **outro** campo inválido continua recusando o save inteiro e preservando sessão e arquivo.

Por quê, em vez de manter a recusa total: (1) a IA já fazia isso para `elogi` ausente/inválido quando lida sozinha, a
PERSISTENCIA recusava; duas políticas para a mesma seção; (2) recusar prende o jogador fora do próprio progresso
(soldados, infraestrutura paga, depósitos) por causa de um estado que o jogo sabe refazer; (3) o descarte é
explícito (notificação de 10 s `CADEIA INIMIGA REINICIADA (motivo)`, evento na cadeia, log), não silencioso.

### 3.2 Garantias testadas (`test_elogi.py`, 22 casos: Lua 5.4 e 5.5, pilha IA_v2 e pilha completa, mais o caso sem módulo)

| Caso | Resultado |
|---|---|
| `elogi` válido (com carga pendente e consumo) | restaura **idêntico**; 3 continuar seguidos não somam nada; sem aviso |
| 9 inválidos: ready < 0, razão não fecha (camisas a mais), bmat < 0, frota > configurada, job de receita inexistente, não-tabela, vazio, versão futura `v = 2` (motivo "versão futura v2"), versão desconhecida | Continuar **funciona**; estado do jogador (bmat, depósitos, carteira, pontos, soldados, onda, mão de obra) **idêntico ao salvo**; inimigo = cenário exato; `pending` vazio, 0 comboios, 0 perdidos, 0 de placar; autosave **não** suspenso |
| `elogi` ausente (save legado / `v` 1 sem `elogi`) | mesmo aviso explícito (antes só o log) e mesmo cenário |
| próximo autosave | grava um `elogi` válido regenerado; o continuar seguinte não avisa e restaura igual |
| estado inimigo **próprio** inválido ao gravar | grava o resto **sem** a seção (nunca um `elogi` inválido) e loga |
| mod **sem** a IA lê save feito com ela | descarta só o `elogi` ("este mod não tem a cadeia inimiga logística"); jogador intacto; inimigo abstrato = `cargo0` de partida nova |
| `squad` inválido, `logi` negativo, campo desconhecido, `infra` futura | **continuam recusando tudo** e preservando sessão e arquivo |

"Sem ganho para o jogador" fica concreto assim: nada do jogador é tocado ou creditado (carteira, bmat, depósitos,
mão de obra, placar de comboios), e a cadeia inimiga nunca volta com mais do que `front0`/`bmat0` (nenhuma carga
pendente fantasma, nenhuma duplicação). **Decisão em aberto para o coordenador:** o estoque de cenário pode ser mais
fraco que o salvo; editar o save para provocar o reinício viraria um atalho (jogo solo offline, risco baixo). Uma
alternativa neutra seria recomeçar a frente no alvo (`front = want`), mas isso cria um estoque que nunca existiu; não
adotei.

Teste de mutação: as mesmas asserções contra a `persistencia.lua` **original** (recusa total) falham em `t_invalid`,
`t_absent` e `t_save_own_invalid`, então os testes distinguem as duas políticas.

### 3.3 O que mudou (diffs em `diffs/`)

- `persistencia_v2.lua`: `sv.validate` devolve `true, nil, soft` (3º retorno = motivo do `elogi` descartado);
  `sv.parseSave` remove `elogi` e deixa `d.elogiDropped` (campo só de execução); `sv.save` grava sem a seção se o
  próprio estado estiver inválido; `sv.load` repassa o motivo a `logi.eRestore(d.elogi, d.elogiDropped)` e anexa o
  aviso ao `PARTIDA CONTINUADA`; save com `logi` mas sem `elogi` recebe o mesmo aviso.
- `ia_logistica_v2.lua`: `logi.eRestore(d, dropped)` avisa (evento + `notify`) quando recebe `nil` com motivo;
  `eValid` distingue "versão futura vN" de "versão desconhecida" e de "formato".
- `test_persistencia_v2.py` = `test_persistencia.py` com 3 pilhas e **um** bloco trocado (o `elogi` que antes
  esperava recusa); `test_ia_logistica_v2.py` = original com só caminhos (nenhuma expectativa mudou);
  `test_orders_bloco_comboio_v2.lua` lê `free`/`front0` do CFG em vez de assumir `free` 3.

Efeito colateral aceito: `sv.read` devolve o primeiro arquivo válido (`save`, `.tmp`, `.bak`). Um `save.txt` com
`elogi` ruim e jogador novo vence um `.bak` inteiro com 30 s a menos de progresso.

## 4. Arquivos

| Arquivo | O que é |
|---|---|
| `ia_logistica_v2.lua`, `build_patch_v2.py` | IA calibrada + `eRestore`/`eValid`; gerador (âncoras únicas, igual ao original) |
| `patch_reserva_bmat.py`, `reserva_bmat.patch` | item 2 |
| `persistencia_v2.lua`, `build_persistencia_v2.py` | item 3; `build`, `build_with_ia`, `build_full` (ECONOMIA → IA_v2 → reserva → PERSISTENCIA_v2) |
| `main_candidato_v2.lua`, `main_final_v2.lua`, `*_v2.patch` | só para inspeção/`check_globals`. **Não copiar sobre o main.** |
| `simlib.py`, `sweep_echain.py` | item 1; modos: sem argumento (tabela), `--sens`, `--cad`, `--grid` |
| `TABELA_CALIBRACAO.txt`, `SENSIBILIDADE.txt`, `CADENCIAS.txt`, `GRADE_RESULTADOS.txt` | saídas do item 1 |
| `test_bmat_caminhao.py` | item 2 |
| `test_elogi.py`, `test_persistencia_v2.py`, `test_ia_logistica_v2.py`, `test_regressao_v2.py` | item 3 e regressão da pilha completa |
| `diffs/` | cada variante contra o original |
| `rodar_tudo.sh`, `SAIDA_TESTES.txt` | bateria e saída |

Reproduzir (raiz, bash): `bash dados/paralel/ia_logistica/acabamento/rodar_tudo.sh` (≈ 2 min). A grade (`--grid`,
~25 min) fica fora; resultado em `GRADE_RESULTADOS.txt` (6 de 144 passam, todos com `free` 5 e `trip` ≤ 25).

Resultados: `test_bmat_caminhao` PASS; `test_elogi` PASS (22); `test_persistencia_v2` PASS (54 = 9 × Lua 5.4/5.5 × 3
pilhas); `test_ia_logistica_v2` PASS (2 candidatos); `test_regressao_v2` PASS 1–6 (test_orders, economia/test_integracao,
IA, globals + 178 locais de topo, comutação, composição com a INTERFACE rebaseada); `check_globals` limpo nos dois
candidatos; controle: os testes originais (`test_ia_logistica.py`, 2 candidatos; `test_persistencia.py`, 36 casos)
seguem PASS contra os módulos originais.

## 5. Propostas ao coordenador

1. **Ordem:** ECONOMIA → IA_LOGISTICA v2 → reserva de bmat → (INTERFACE) → PERSISTENCIA v2. Todos comutam onde
   testado; `build_persistencia_v2.build_full` faz a pilha sem a INTERFACE.
2. Ao integrar, substituir `ia_logistica.lua`, `persistencia.lua` pelos `_v2`, trocar o bloco do comboio de
   `tools/test_orders.py` por `test_orders_bloco_comboio_v2.lua` e incluir `test_elogi.py` e `test_bmat_caminhao.py`
   na bateria.
3. `mod/README.md` precisa dizer: piso e estoque da cadeia inimiga; reserva de bmat para reconstruir caminhão; save
   que reinicia só a cadeia inimiga (aviso `CADEIA INIMIGA REINICIADA`).
4. Gotchas propostos para a nota Foxhole (não editei): (a) a calibração do comboio inimigo só vale em cadências de onda
   ≥ ~55 s com `free` 3; a refinaria (2 bmat/s) é o teto de qualquer cadeia; (b) fábrica com receita (80) abaixo do
   preço do caminhão (100) o impede de voltar sob consumo contínuo; ordem das chamadas não adianta; (c) política de
   seção descartável no save para estado regenerável.
5. Decidir (3.2) o estoque de recomeço e (2.3) a morte do caminhão de recurso sem renda.

## 6. Pendências ao vivo (laboratório)

1. Medir a cadência real das ondas (robô e humano) e o tempo do ciclo do caminhão de recurso; refazer a varredura.
2. Ver `logi.eReport()` com a calibração v2: `byCut`, perdas e se a pressão cai como em `TABELA_CALIBRACAO.txt`.
3. Jogador: matar um caminhão de suprimento sob consumo alto (robô em `botloop`), ver o aviso `fábrica guarda...` e o
   caminhão voltar em < 60 s; checar o HUD ("sem bmat") e se o consumo real chega a deixar a fábrica sempre ocupada.
4. Editar `save.txt` (corromper o `elogi`, mudar `v` para 2) e usar Ctrl+F6: conferir o aviso de 10 s, o jogador intacto
   e o próximo autosave.
5. Tudo o que os relatórios originais já listavam (caminhão BPTruckC real, rota, desempenho, `io`/`os` no Lua do UE4SS).
