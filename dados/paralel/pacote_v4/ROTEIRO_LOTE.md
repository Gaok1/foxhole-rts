# ROTEIRO_LOTE — uma sessão de laboratório para a pilha v4 (para a task LABORATORIO)

Preparado offline pelo agente PACOTE_V4 (2026-10-10). **Nada abaixo foi executado no jogo.** Junta, sem perder itens, os roteiros de
`ia_logistica/`, `ia_logistica/acabamento/coleta_manual/`, `persistencia/`, `bases_avancadas/` (etapa 1 e 2), `interface/`, `economia/` e
`estabilidade/` (rastreio no fim, §13). Quem executa é o dono do laboratório (Codex coordenador); este arquivo não abre o jogo.

## 0. Regras do lote (valem para todos os passos)

- Steam aberto e logado; cópia em `D:\FoxholeLab\Foxhole`; **nenhum** `botloop.sh` junto do canal de comandos (as respostas se misturam):
  `Get-CimInstance Win32_Process | Where-Object { $_.CommandLine -match 'botloop' }` tem de vir vazio antes de cada bloco com canal.
- Publicar só por `bash D:/tools/foxhole-lab/restart.sh` (sintaxe + `check_globals` + cópia + reinício + espera de "modo RTS ligado", 240 s).
  Nunca Ctrl+R do UE4SS. Primeira carga ~3 min de tela preta "Not responding": **não** é travamento; confirme por log/processo.
- **Sem injeção de teclado ou mouse.** O que precisa de entrada real está em `TESTE_MANUAL_RASCUNHO.md` (não aqui). Os scripts `pv4_cmd_*.lua`
  chamam as mesmas funções do mod que as teclas chamam (`newGame`, `logi.deploy`, `recruit`, `logi.fwdKey`, `sv.save`, …) pelo canal
  `sh D:/tools/foxhole-lab/run.sh <arquivo.lua>`; isso testa a lógica, **não** o registro da tecla nem o `plain()` do J.
- A saída do canal vem só de `out(...)`. Mensagens do mod (`notify`) vão para `UE4SS.log` com o prefixo `[FoxholeRTS]` (leia-o para o texto exato).
- Cada passo grava: hora, hash do `main.lua` publicado (`sha256sum`), PID do jogo, saída do canal (`sh run.sh X > saida_X.txt`) e, quando
  indicado, captura (`cd D:/GitHub/universal-modder && UM_HOME=D:/tools/um-home python -m um win shot --title '^War' --scale 0.5 <png>`).
- Qualquer queda UE4SS/jogo: parar, preservar `UE4SS.log`, `Saved\Crashes` e o PID; **não** reiniciar por reflexo. Registrar no MODLOG como
  falha, não como "ajuste".
- Ao final: encerrar **só** o PID da cópia (`D:\FoxholeLab\Foxhole`); Steam e firewall ficam como estão; remover `map.txt` temporário.
- Valores de `CFG` que o roteiro compara foram lidos no candidato a integrar, **v4.1** (SHA `62245d23…598f`; a v4 `025e3b80…aab0` tem os mesmos valores de `CFG`). Se o main publicado for outro, pare no S2.

## 1. Duração estimada

| Bloco | O que é | Min (estimado, não medido) |
|---|---|---|
| P | Pré-voo, backups, cópia das sondas | 15 |
| G | Gate de estabilidade: registrar B1 + cargas B2 e A2 (cada uma ~5 min de carga + 3 min de janela + checagens) | 25 |
| S | Publicar a v4.1 em HomeRegionW, sondas só leitura (A1–A3, io/os, estado), partida de fumaça e ensaio B1 (cria 1 ator) | 45 |
| H0–H1 | Trocar para CallumsCapeHex (`map.txt`) e reiniciar; A3/estado no hex; implantar (Alt+L pelo canal) | 10 |
| C | Partida manual: trabalhadores, caminhão de recurso, perda, combate; economia (fuzis/bandagens/prioridade/escassez) | 35 |
| I | Cadeia inimiga e interdição (L1–L12) + I15 (onda com trabalhadores, v4.1) na mesma partida | 35 |
| K | Bases avançadas: elegibilidade, construção, pedido, entrega, recrutamento, perda, Assalto | 45 |
| V | Persistência: save/continue com 2 reinícios do jogo, recusas, elogi corrompido | 50 |
| T | 10 min com 3 bases (estabilidade + custo por quadro) | 15 |
| Z | Encerramento, restauração, relatório | 10 |
| **Soma** | | **~285 min (4 h 45)** |
| Com 20% de imprevistos | | **~5 h 40** |
| R (opcional) | Regressão prolongada com o robô: mínimo 4 partidas (1 por célula B0–B3) | +70 a +90 |
| R completo | 3 partidas por célula + 1 fácil + 1 difícil | +3 h 30 |

Cargas limpas do jogo no núcleo: 2 (gate) + 1 (v4 em HomeRegionW) + 1 (hex) + 2 (persistência) = 6. Cada uma custa ~5 min; é o que mais pesa.

## 2. Arquivos a levar para `D:/tools/foxhole-lab/` (cópia, nada é editado nos originais)

```
cd /d/GitHub/foxhole-rts/dados/paralel
cp pacote_v4/sondas/*.lua                                  D:/tools/foxhole-lab/
cp bases_avancadas/sondas/A1_colunas_estrutura.lua bases_avancadas/sondas/A2_classes_base.lua bases_avancadas/sondas/A3_mundo_bases.lua bases_avancadas/sondas/A4_chao_dos_pontos.lua D:/tools/foxhole-lab/
cp ia_logistica/t_ia_logistica.lua persistencia/lab/t_persist_estado.lua D:/tools/foxhole-lab/
# já existem lá: t_crash_control_start.lua / _check.lua (A) e t_crash_B1_prepare.lua / _start.lua / _check.lua (B)
```
Legenda dos arquivos novos (`pacote_v4/sondas/`; mais `ler_save.py` e `bateria_pos_integracao.py` fora do jogo): `pv4_estado` e `pv4_perfil` (só leitura), `pv4_bases_cena` (só leitura, traços), `pv4_io_os`
(cria e apaga 2 arquivos temporários), `pv4_B1_forwardbase` + `pv4_B1_limpar` (cria 1 ator nativo), `pv4_cmd_*` (chamam funções do mod; alteram estado,
editar as variáveis do topo antes de rodar). Todos tiveram a **sintaxe** conferida (Lua 5.4 e 5.5); `pv4_estado`, `pv4_bases_cena`, `pv4_io_os` e vários
`pv4_cmd_*` foram executados contra o candidato no harness offline (mock do mundo), o que prova que não há erro de nome/campo, não que o jogo responde igual.

## 3. P — Pré-voo (15 min)

| ID | Passo | Medir / PASS | Fecha |
|---|---|---|---|
| P1 | Steam aberto/logado; sem botloop; cópia presente; `steam_appid.txt`; nenhuma `War-Win64-Shipping.exe` da cópia rodando (ou anote o PID) | PASS: tudo conferido e anotado | LABORATORIO "Conferir Steam… antes de lançar" |
| P2 | **Backup fora da cópia**: `War/Binaries/Win64/ue4ss/Mods/FoxholeRTS/save.txt*` (e `settings.txt`, `map.txt` se houver) + SHA256 de cada; lista de `%LOCALAPPDATA%\Foxhole\Saved\Crashes`; tamanho do `UE4SS.log` | PASS: SHA256 anotados (L12 do roteiro de persistência os restaura no fim) | PERSISTENCIA |
| P3 | Cópia das sondas (§2). Conferir `sha256sum mod/FoxholeRTS/Scripts/main.lua` e o que o `restart.sh` vai publicar | PASS: hash anotado = o do passo em que for usado (33d6c7e5… no gate, 62245d23… (v4.1) depois) | INTEGRACAO |
| P4 | Decidir a ordem gate × integração (`COMO_INTEGRAR.md` §2). Este roteiro assume: G (fonte 33d6c7e5…) → integração → S em diante | PASS: decisão registrada | ESTABILIDADE |

## 4. G — Gate de estabilidade (25 min; fonte 33d6c7e5…, antes de gravar a v4.1)

Base: `estabilidade/controle_crash.md`. Mesma fonte, mesmo mapa, câmera e estado; sem ondas, sem logística, 6 soldados parados; **nenhuma** entrada do
usuário nem do agente durante a janela (nem console); checkpoints por canal em 60/120/180 s, iguais em todas as cargas; não reiniciar por
"Not responding". Janela mínima 180 s (a queda histórica aconteceu antes de 111 s).

| ID | Passo / comando | Medir | PASS | FAIL (o que fazer) | Fecha |
|---|---|---|---|---|---|
| G1 | **Registrar o B1 já feito**: `D:/tools/foxhole-lab/crash-control-B1.txt` (184,3 s, 6 selecionados, 168 cópias, stratTick 11,66/11,90/12,37 ms) → entrada no MODLOG com PID/hora (o arquivo não diz) | confirmar no `UE4SS.log` do dia: sem `Registry`/fatal na janela | arquivo e log coerentes | sem log do dia: registrar "sem log de apoio" | ESTABILIDADE |
| G2 | **B2** (ordem invertida, carga nova): `restart.sh` → esperar RTS → `run.sh t_crash_B1_prepare.lua` → esperar 5 s → `run.sh t_crash_B1_start.lua` → em 60/120/180 s `run.sh t_crash_B1_check.lua` | PID vivo; `SELECTED 6 CLONES 168` nos 3 checkpoints; `stratTick`; `UE4SS.log` sem `Registry`/`Access violation` | ≥ 180 s sem queda, contagens iguais, stratTick ~12 ms (não pior que B1) | queda < 111 s: guardar log+Crashes, **parar o lote** (regra do MODLOG), decisão do coordenador | ESTABILIDADE "Distinguir hipóteses…" |
| G3 | **A2** (carga nova, sem seleção): `restart.sh` → `run.sh t_crash_control_start.lua` → 60/120/180 s `run.sh t_crash_control_check.lua` | idem; `SELECTED 0 CLONES 0`; stratTick ~0,5 ms | ≥ 180 s, 0 cópias, ~0,5 ms | queda com 0 cópias: o contorno não é necessário para reproduzir; investigar callbacks/anim comuns (decisão do `controle_crash.md`) | ESTABILIDADE |
| G4 | Tabela de decisão (`controle_crash.md`): falha só B → seleção/cópias associadas (não causa); A/B ambas sobrevivem 2× → sem reprodução, ampliar duração/transições em lote posterior; falha A+B → ponte comum merece símbolos/trace | registrar a linha da decisão no MODLOG | decisão escrita | — | ESTABILIDADE |
| G5 (opcional) | Matriz ampliada de `auditoria.md` (A: 10 min sem seleção; B: 1 selecionado/28 cópias 10 min; D: 100 selecionar/desselecionar; E: 20 morte/recriação; J: 1/3/10/25 selecionados em zoom alto, 60 s por degrau) | `profile()` por degrau; cópias = 28×N; sem residuais | só se o coordenador pedir: não é gate do lote | — | ESTABILIDADE "validação prolongada, GC, desseleção/reseleção, morte e recriação" |

Depois do G: **INTEGRACAO grava a v4** (`COMO_INTEGRAR.md` §3–§6) e a bateria offline passa 27/27 antes de seguir.

## 5. S — HomeRegionW (bancada): sondas só leitura, partida de fumaça e ensaio B1 (45 min)

Sem `map.txt` (HomeRegionW). Sem botloop. Cada sonda: `sh D:/tools/foxhole-lab/run.sh <arquivo> > saida_<arquivo>.txt`.

| ID | Passo / comando | Medir | PASS | FAIL (o que fazer) | Fecha |
|---|---|---|---|---|---|
| S1 | `restart.sh` com a v4 publicada; `sha256sum` do publicado | espera do RTS ≤ 4 min; no `UE4SS.log` a linha `v0.9 carregado (... Shift+J base avançada ...)`; ausência de `Registry`/`ERRO` | RTS ligado e linha presente | falha de lançamento (`restart.sh` sai com código ≠ 0 em ~1 s = Steam fechado): abrir/logar o Steam, não esperar 240 s | LABORATORIO "Publicar… Verificar carregamento…" |
| S2 | `run.sh pv4_estado.lua` (sem partida) | seção `CFG`: `COLETA.manualStart true`, `bmat0 40`, `DEPLOY.budget 1000`, `FWD cost 300 hp 1725 cap 15 max 3 confirm 4.0 pending 180.0 strict true ruin false teamId nil visual native`, `SPAWN.pointSpawn false startRifles 10`, `ECHAIN.free 5 trip 20.0`, `PERSIST.version 2 fwdVersion 1` | todos iguais | divergência: o main publicado não é a v4; parar | INTEGRACAO |
| S3 | `run.sh pv4_perfil.lua` (zera a janela) e, 60 s depois, de novo | `mod: X ms/quadro … stratTick …` sem partida | linha de base registrada | — | custo por quadro (§7 C9) |
| S4 | `run.sh A1_colunas_estrutura.lua` | colunas de `BPStructureDynamicData` além das 5 conhecidas; valores de `ForwardBase1` (MaxHealth 1725? ResourceAmounts 300 bmat? StoredItemCapacity 15?) | sem queda; valores anotados | queda: ver §0; não repetir a sonda | BASES_AVANCADAS "Rastrear nos dados" |
| S5 | `run.sh A2_classes_base.lua` | `BPForwardBase1_C` (caminho **inferido**) carrega? pai, CDO, propriedades `TeamId/Health/CodeName`, UFunctions de spawn/estoque/dano; `DestroyedForwardBase1` | classe carrega e `CodeName/Health/MaxHealth/TeamId` aparecem | classe não carrega: o caminho de `CFG.FWD.asset` muda; sem classe, não há bases (pular K inteiro) | BASES_AVANCADAS (decide `visual="native"` e R1) |
| S6 | `run.sh A3_mundo_bases.lua` (mundo já carregado) | atores de base/spawn/hospital: onde, time, vida, componentes (só classe e nome); bounds só-colidindo → `CFG.FWD.half` (600 cm provisório); `ItemHolder` real × "15 slots" | tabela anotada | — | BASES_AVANCADAS |
| S7 | `run.sh pv4_io_os.lua` (cria/apaga 2 arquivos temporários ao lado do save) | linha `rename A -> B com B existente (DESTINO EXISTE)`; `seek end`; `remove inexistente` | todas as linhas OK; o retorno do rename é registrado (offline no Windows/lupa: `nil, "File exists"`) | `rename` devolve true sobrescrevendo: o remove prévio é inofensivo; `ERRO` em seek/write: **PERSISTENCIA reprova** (o código depende disso) | PERSISTENCIA "Medições pedidas" |
| S8 | `run.sh pv4_cmd_partida.lua` (= Shift+F6) e `run.sh pv4_estado.lua` | caminhões 3 (`res` = `dead`, 2 `sup`), `bmat 40`, camisas 30, fuzis 10, reserva 100, `COLETA ativa`; cadeia inimiga `auditoria true`, frente `m2 c10` | como descrito; painel (13 linhas) | `Partida não iniciada: <motivo>` no log: HomeRegionW tem campo, refinaria, fábrica e os caminhões do mapa (README); registrar o motivo e seguir para H0 | COLETA 1; ECONOMIA |
| S9 | ~15 s depois (trabalhadores nascem a partir de ~5 s, um a cada ~3 s): `pv4_estado.lua`; **captura** do esquadrão | 3 trabalhadores (`ESQUADRAO trabalhadores 3`), camisas 27; sem T-pose (grip 0 sem arma), sem erro no log | nascimento limpo | T-pose/queda do hook de animação: `CFG.WEAPONS.worker.grip` e `anim.untrack`; **parar** | COLETA 2 |
| S10 | Ter um ponto seu: `run.sh pv4_cmd_capturar.lua` (PONTO "A"); esperar `pv4_estado.lua` mostrar `PONTO … dono 1` | captura normal (10 s de neutro a dono por soldado) | ponto A é seu | demorou: repetir `pv4_cmd_capturar.lua` | — |
| S11 | **B1**: `run.sh pv4_B1_forwardbase.lua` (estágio 1, **cria 1 ator**); +15 s o mesmo arquivo (estágio 2); +60 s o mesmo (estágio 3); `run.sh pv4_B1_limpar.lua`; ler `UE4SS.log` do T0 ao fim | `B1 SPAWN ms`, `B1 ATOR CodeName Health MaxHealth TeamId`, `B1 CONTRATO strict` (Health==MaxHealth==1725 e CodeName==ForwardBase1), posição/yaw como pedidos, `ainda_ativo_apos_destroy false`; no log: sem `Registry`, sem `Access violation`, sem respawn nativo | nasce íntegro e some sem residual; 60 s limpos | **strict falha**: registrar o valor real (Health? CodeName?); decidir `CFG.FWD.strict=false` ou ajuste; **classe não nasce/queda**: não há base (pular K) e plano B (malha) é task nova; `TeamId`: registrar 255 × 1 (hoje o mod não escreve) | BASES_AVANCADAS "Solicitar… spawn real da classe no hex" |

## 6. H0–H1 — CallumsCapeHex: trocar de mapa e implantar (10 min)

| ID | Passo / comando | Medir | PASS | FAIL | Fecha |
|---|---|---|---|---|---|
| H0 | Gravar em `…/ue4ss/Mods/FoxholeRTS/map.txt` a linha `/Game/Maps/Master/CallumsCapeHex` (padrão do lote 17); `restart.sh`; esperar RTS (hex grande: mais lento) | `pv4_estado.lua` linha `MUNDO` mostra CallumsCape; `sv.worldPath` | RTS ligado no hex | — | PERSISTENCIA "mesma região" |
| H1a | `run.sh A3_mundo_bases.lua` de novo (no hex) | bases/hospitais nativos e ruínas; `ForwardBase1` já existe no hex? | anotado | — | BASES_AVANCADAS |
| H1b | `run.sh pv4_cmd_implantar.lua` (= Alt+L) | `ANTES/DEPOIS` com refinarias, fábricas, `BPTruckW_C`, carteira. **v4: custo 1000** (refinaria 400 + fábrica 400 + 2 caminhões de suprimento 100; **sem** o de recurso) | `IMPLANTAÇÃO: -1000 bmat do cenário; saldo 0`; 2 TruckW (Team 1, HP 900, `built` 4); repetir: `Cadeia já implantada` e contagens iguais | recusa por vaga/folga: motivo no log; falha forçada reverte sem débito | PERSISTENCIA L0 (versão v4); LABORATORIO |
| H1c | `run.sh pv4_estado.lua` | `ATORES ATIVOS` = 1 refinaria, 1 fábrica, 2 TruckW; nenhum `BPTruckC_C` | conferido | — | — |

## 7. C — Partida manual, coleta e economia (35 min)

Itens 1–9 de `coleta_manual/ROTEIRO_LABORATORIO.md` + a matriz de ECONOMIA. `run.sh pv4_cmd_partida.lua` inicia; `pv4_estado.lua` a cada ~30 s; **o `newGame` já liga as ondas automáticas** (como Shift+F6); para medir a coleta sem pressão (C1–C9) rode `pv4_cmd_modo.lua` com `MODO="sem_ondas"` **logo depois** da partida (a sonda só desliga se estiver ligada).

| ID | Passo / comando | Medir | PASS | FAIL | Fecha |
|---|---|---|---|---|---|
| C1 | `pv4_cmd_partida.lua` + `pv4_estado.lua` (t=0) | custo 1000, 2 caminhões de suprimento, nenhum de recurso vivo, `bmat 40`, reserva 100, painel com `Fábrica | guarda 100 bmat para reconstruir caminhão (bmat 40)`, camisas 30 | como descrito | — | COLETA 1 |
| C2 | t≈15 s (o 1º trabalhador aos ~5 s, os outros a cada ~3 s): `pv4_estado.lua` + captura | 3 soldados **sem arma** perto da base; camisas 30→27; nada de crash (`UE4SS.log`, `Saved\Crashes`) | 3 trabalhadores, T-pose ausente | — | COLETA 2 |
| C3 | Caminhada: `pv4_estado.lua` a cada 30 s (seções `COLETA`, `LUGARES`, `DISTANCIAS`) | tempo da 1ª entrega na refinaria e do 1º caminhão; distância real campo–refinaria; algum trabalhador preso? (`leg` 180 s) | eles chegam, coletam, entregam; razão da coleta `true`; tempo comparável a 165 s (80 m) / 359 s (470 m) do harness | preso/perdido: `CFG.COLETA.fieldR/refR/stand/leg`; anotar onde | COLETA 3 |
| C4 | Ordem do jogador (durante C3, ~60 s): `pv4_cmd_trabalhador_ordem.lua`; `pv4_estado.lua` logo depois e ~70 s depois | o trabalhador sai da coleta (carga em mãos descartada, log); ~60 s sem ordem (`CFG.COLETA.quiet`) volta sozinho | sai e volta | não volta: `colMaintain`/`quiet` | COLETA 5 |
| C5 | Caminhão: quando bmat chega a 100 a fábrica constrói o de recurso | ele **aparece no campo, em pé no chão**, não preso; mensagem `caminhão de recurso pronto: coleta manual encerrada`; o painel perde a linha da coleta (`COLETA_PAINEL nil`); `ATORES ATIVOS BPTruckW_C` sobe | spawn válido (`logi.spawnTruck`), não em telhado | spawn recusado: segue como caminhão abstrato (log); anotar | COLETA 4 |
| C6 | Perda do caminhão: `pv4_cmd_matar_caminhao.lua` com `KIND="res"`, `ZERAR=true` | sem bmat/sucata/caminhão a coleta **reativa** (`COLETA ativa true`, trabalhadores voltam, `COLETA MANUAL:` no log); a fábrica reconstrói o caminhão ao juntar 100 bmat | reativa e reconstrói | trava para sempre = regressão do v2 | COLETA 6; decisão do usuário |
| C7 | Combate: `pv4_cmd_inimigo.lua` (`ONDE="campo"`, `N=1`); depois `pv4_cmd_modo.lua` `MODO="limpar"` | trabalhadores pausam; se um morre, a base repõe **por 1 camisa** (`pv4_estado`: camisas −1) | pausa e reposição | — | COLETA 7 |
| C8 | Salvar/continuar com trabalhadores em campo: `pv4_cmd_modo.lua` `MODO="ondas"` (religa; `sv.save` exige `combat.auto`); `pv4_cmd_save.lua`; `pv4_cmd_load.lua`; `pv4_estado.lua` antes e depois | carga em mãos descartada (log `coleta manual: … descartada`), 3 trabalhadores, coleta recomeça; ms do save/load | `sv.save` true; `sv.load` true; mesmo esquadrão | — | COLETA 8; PERSISTENCIA |
| C9 | Custo por quadro: `pv4_perfil.lua` (zera) → 2 min **com** coleta ativa → `pv4_perfil.lua`; depois repetir **sem** coleta (após C5) | `mod X ms/quadro`, `colStep` | diferença anotada (nenhum limite fixo; coleta é O(coletores)) | — | COLETA 9; INTERFACE (custo do painel) |
| C10 | Economia (depois de C5): `pv4_cmd_prio.lua` com `VEZES=3` (fuzis) e deixar a fábrica produzir; `pv4_cmd_enviar.lua` `ONDE="base"`; ver `DEPOSITO base … fuzis`; repetir com `VEZES=1` seguidas até bandagens | receita → produção → transporte → depósito para os 4 produtos (caixa de fuzis = 20 un., bandagens = 50, camisas = 10); `Pronto | …` e `extraHud` coerentes; razão de bmat | os 4 produtos chegam ao depósito sem estoque artificial além de `startRifles 10` | produto some: `logi.moveCargo`/`returnCargo` | ECONOMIA "cadeia completa ao vivo" |
| C11 | Recrutar fuzileiros até acabar os fuzis (`pv4_cmd_recrutar.lua` `ROLE="rifle"`, `ONDE="base"`, `VEZES=11`) | os 10 primeiros gastam 1 camisa + 1 fuzil cada; o 11º é recusado (`sem fuzis em base; …`); mão de obra **não** cai; depois da produção/entrega volta a poder | recusa e retomada | recruta sem fuzil = regressão | ECONOMIA "recrutamento dependente de suprimento" |
| C12 | Escassez/corte/retomada: `pv4_cmd_matar_caminhao.lua` `KIND="sup"` com bmat baixo; observar a reserva (`Fábrica | guarda 100 bmat…`) e a volta do caminhão (< 60 s se houver bmat); matar de novo | a fábrica não gasta os 100 de reserva em caixa (hipótese bmat×caminhão: 0/31 voltavam antes da reserva) | caminhão volta; razão fecha | caminhão nunca volta = reserva não vale ao vivo | IA_LOGISTICA acabamento 3; ECONOMIA "escassez, corte, retomada" |
| C13 | Painel: **captura** com coleta ativa, depois com produção; `pv4_estado.lua` seção `PAINEL` (linhas/largura) | 12–13 linhas, largura ≤ ~222 (offline); sobreposição, altura, a ajuda F5 e alertas nativos em vários zooms/resoluções; pausa; logística desligada | legível e sem cortar estoques/veículos; nada escondido silenciosamente | cortado: layout antes de aprovar (a INTERFACE avisa que o clipping é gate visual) | INTERFACE (laboratório) |

## 8. I — Cadeia inimiga e interdição (35 min; L1–L12 de `ia_logistica/ROTEIRO_LABORATORIO.md`)

Mesma partida de C (ou nova com `pv4_cmd_partida.lua`). Ondas: a partida nova já as liga; `pv4_cmd_modo.lua` `MODO="ondas"` só religa se estiverem desligadas. Sonda: `run.sh t_ia_logistica.lua` (ou `pv4_estado.lua`, seção
`CADEIA_INIMIGA`/`COMBOIO`). Calibração v2: `free 5`, `trip 20`, `front0 m2 c10`, `want 4/20`, piso grátis 5/onda.

| ID | Passo | Medir | PASS | FAIL | Fecha |
|---|---|---|---|---|---|
| I1 | (L1) logo ao ligar a partida | `auditoria=true (razão fechado)`, `ativo=true`, frente `m2 c10`, retaguarda bmat 240, frota livre 2; HUD `INIMIGO: frente equipa 10`; sem erro Lua | como descrito | — | IA_LOGISTICA |
| I2 | (L2) 1º comboio (20 s após o início das ondas + carga) | evento `comboio 1 saiu: N cx`; ator `BPTruckC` existe, `ator_ativo=true`; a retaguarda caiu exatamente a carga; alerta `COMBOIO INIMIGO … (carga)` | ator real válido | spawn recusado/em destruição: log | IA_LOGISTICA "caminhão real ao vivo" |
| I3 | (L3) deixe chegar | um único `entregou na frente`; frente sobe por `units` (camisas = 10 por caixa); rodar a sonda 3× seguidas: nenhuma 2ª entrega; o caminhão some e a frota livre volta a 2; `auditoria=true` | única entrega | dupla entrega = bug | IA_LOGISTICA |
| I4 | (L4) emboscada: `pv4_cmd_emboscada.lua` com comboio carregado | `comboio N perdido (destruído): -X munição, -Y camisas` **uma** vez; alerta `COMBOIO INIMIGO DESTRUÍDO (+25)`; frente inalterada; `reconstruindo 1`; `auditoria=true` | uma perda, razão fecha | perda duplicada | IA_LOGISTICA "destruição/interdição reduz suprimento" |
| I5 | (L5) morteiro nosso sobre comboio carregado: `pv4_cmd_morteiro.lua` (= Ctrl+5, 40 de mão de obra, mira adiantada); depois, **com o comboio já destruído**, `REPETIR_NO_LUGAR = true` e rodar de novo | o mesmo de I4 (uma perda, alerta `+25`); o 2º morteiro sobre caminhão destruído **não** registra 2ª perda (`combat.convoysCut` não sobe) | uma perda só | 2ª perda = bug | IA_LOGISTICA |
| I6 | (L6) esperar ≥ 30 s após a perda | `caminhão de comboio reconstruído (-100 bmat)` só quando bmat ≥ 100; a fábrica **inimiga** fica parada se não há caminhão livre e há reconstrução vencida | como descrito | — | IA_LOGISTICA "recuperação" |
| I7 | (L7) ondas com a frente cheia e depois vazia: comparar `#enemies()` logo após cada spawn com o registro da onda (`eReport`) | `enviados` = soldados que nasceram; com a frente vazia `faltou suprimento ao inimigo: a onda vem com N a menos (…; K por comboios destruídos)`; piso de 3… **v2: piso grátis 5** | sem soldado a mais | — | IA_LOGISTICA "escassez" |
| I8 | (L8) ponto inimigo com reforço (`ai.tick`) e frente seca, depois abastecida | sem material: nenhum `REFORÇO INIMIGO`; com material: 2–3 e a frente debitada pelo número que **nasceu** | como descrito | — | IA_LOGISTICA |
| I9 | (L9) `pv4_cmd_save.lua` com comboio na estrada, `pv4_cmd_load.lua` (mesma sessão; o reinício completo é V) | evento `cadeia inimiga restaurada do save (reenviar …)`; pendente = carga que estava na estrada; `auditoria=true`; o próximo comboio leva o pendente; continuar 2× não duplica (compare inicial+produzido) | restaura sem duplicar | — | IA_LOGISTICA "continuidade"; PERSISTENCIA |
| I10 | (L10) em sonda separada e registrada: `logi.foes[1].pawn:K2_DestroyActor()` | no quadro seguinte `perdido (ator do caminhão inválido)`, sem entrega, `auditoria=true`, sem crash/erro nativo | tratado | queda nativa: **parar** | IA_LOGISTICA |
| I11 | (L11) Assalto: `pv4_cmd_modo.lua` `MODO="assalto"` | nenhum comboio; frente intacta; nenhum consumo (`ativo=false`); recrutar usa mão de obra (ramo legado) | como descrito | — | IA_LOGISTICA; BASES (K9) |
| I12 | (L12) `pv4_cmd_partida.lua` várias vezes e `MODO="limpar"` no meio | nenhum `BPTruckC_C` sobra (`ATORES ATIVOS`); `logi.en` novo; sem erro | sem resíduos | — | IA_LOGISTICA |
| I13 | Pendência 4 do acabamento: editar `save.txt` (corromper `elogi`; trocar `["v"]=2` por outro) e `pv4_cmd_load.lua` | aviso `CADEIA INIMIGA REINICIADA (…): estoque de cenário` por 10 s; jogador intacto; próximo autosave grava de novo | só a seção cai | recusa o save inteiro = regressão do v2 | PERSISTENCIA; IA acabamento 4 |
| I15 | **v4.1**: onda com trabalhadores. Com a coleta ativa (3 trabalhadores vivos), anotar `#squad`, soldados de combate (`rts.combatCount()`) e `#enemies()` logo após o spawn da 1ª onda; repetir com `CFG.COLETA.workers = 0` antes de uma partida nova (ou sem trabalhadores vivos) e o mesmo número de soldados de combate | O tamanho da onda depende só dos soldados de combate (harness: 6 de combate dão 6 com ou sem 3 trabalhadores; o aviso "próxima onda em … (esquadrão N …)" mostra os de combate; `pv4_estado.lua`/canal: o ponto de saída da onda segue o esquadrão de combate, não o campo de sucata, pois `squadCenter()` só conta combatentes vivos) | onda maior com trabalhadores = regressão | — | decisão do orquestrador (v4.1) |
| I14 | Pendência 1 do acabamento: cadência real das ondas (robô e humano) e `logi.eReport()` no fim | `byCut`, perdas, pressão por onda | números anotados para `TABELA_CALIBRACAO` | — | IA acabamento 1–2 |

## 9. K — Bases avançadas (45 min; ainda em CallumsCapeHex; **só se S5/S11 deixaram a classe nascer**)

Pré: partida logística ativa com ≥ 1 ponto seu longe da base (≥ 3000 cm) ou perto de ponto inimigo (≤ 4000 cm); bmat suficiente ou `CREDITAR=true` (registre).

| ID | Passo / comando | Medir | PASS | FAIL | Fecha |
|---|---|---|---|---|---|
| K1 | `run.sh A4_chao_dos_pontos.lua`; `run.sh pv4_bases_cena.lua` | por ponto: `fwdCheck`, `fwdPlace` (centro, saídas ≥ 3), `fwdPlace_ms`; `RESUMO elegiveis` | **≥ 1 ponto elegível por partida** no hex (L2: `minFromBase 3000` / `maxToEnemyPoint 4000`); ms de `fwdPlace` anotado | nenhum elegível: calibrar `half/clear/maxSlope/minExits/exitR` (A4 mede) | BASES (L2; footprint) |
| K2 | Recusas (`pv4_cmd_base_shiftj.lua`, `TOQUES=1`/`2`): cursor num ponto neutro/inimigo/perto da base/com inimigo no anel (`pv4_cmd_inimigo.lua` `ONDE=` nome) | mensagens `não é seu`, `perto demais da base`, `há inimigos no ponto X`; **nada criado, nada debitado** | recusas claras | cria algo = bug | BASES |
| K3 | Construir: `PONTO=nil`, `TOQUES=2` (com bmat real; senão `CREDITAR=true`, anotar) | `toque 1 false`, `toque 2 true`; a base aparece no ponto; `pv4_estado.lua`: `BASE … ator_vivo true classe BPForwardBase1_C hp_ator 1725/1725 saidas ≥3 razao true`; `bmat −300` **só depois** do ator validado; painel ganha `base A | camisas 0 | fuzis 0 | slots 0/15 | reforça: NÃO (sem camisas)` | íntegra, 1 ator por base | `strict` recusa (log `vida inicial/CodeName/rotação divergiu`): ver S11 | BASES "Solicitar… spawn real" |
| K4 | Pedido pendente: sem bmat, `TOQUES=2`; painel; esperar ou `TOQUES=2` de novo em 4 s para cancelar | `pedido de base avançada em X registrado`; painel `Fábrica | guarda 300 bmat para base avançada em X (bmat N)` (depois da reserva do caminhão: o caminhão tem prioridade); constrói sozinha quando junta; cancela em 180 s, se o ponto deixa de ser seu, com inimigo no anel, ou com o 2º Shift+J | como descrito; **sem fome de munição** (a fábrica não para munição indefinidamente) | fome de munição prolongada: ajustar `pending` | BASES |
| K5 | Entrega por caminhão: `pv4_cmd_enviar.lua` `ONDE="A"` (base); esperar | só o que cabe nos 15 slots (caixa parcial = 1 slot); camisas e fuzis **só** vão a base principal ou avançada ativa; ponto sem base recebe só munição e bandagens; razão por base fecha | respeita slots | estoura 15 slots = bug | BASES "entrega de camisas por caminhão" |
| K6 | Recrutar: `pv4_cmd_recrutar.lua` `ROLE="rifle"`, `ONDE="A"` (dentro da base) e depois `ONDE="longe"`; `ROLE="mg"` | nasce **na saída** da base (`saida de base A a ~0 cm`, não em telhado/parede), gasta 1 camisa + 1 fuzil (mg: só camisa), mão de obra intacta; base sem estoque dentro dela → recusa com motivo, **sem** cair noutra; fora → a base mais perto do cursor/esquadrão com estoque | como descrito | nasce em telhado/parede: `exits`/`parkingGround` | BASES |
| K7 | Ponto sem base (ainda seu): `pv4_cmd_recrutar.lua` `ONDE=` ponto sem base | **não** reforça (nasce na base principal); com `CFG.SPAWN.pointSpawn=true` voltaria ao antigo | confirmado | — | BASES |
| K8 | Perda: `pv4_cmd_base_perda.lua` `MODO="morteiro"` (8 morteiros inimigos), depois `"captura"` noutra base | alerta `BASE AVANÇADA X destruída/capturada: perdeu N camisas e M fuzis` **uma vez**; ator destruído, **sem** residual (`BPForwardBase1_C` ativos = bases vivas); estoque zerado; recapturar o ponto não traz a base; razão fecha; painel perde a linha; ponto neutralizado = `INATIVA (ponto neutro)` com estoque preservado | uma perda, sem ator residual | ator residual: `fwdLose` | BASES |
| K9 | Limites e Assalto: construir até 3, tentar a 4ª (`limite de bases avançadas (3)`); `pv4_cmd_modo.lua` `MODO="assalto"`: Shift+J recusa (`só numa partida com logística (fora do Assalto)`) e `recruit` usa mão de obra | como descrito | — | — | BASES |
| K10 | Pausa: o jogo pausado (`rts.togglePause()` via canal) durante os 4 s do 2º toque | `GetRealTimeSeconds` continua correndo (item 12 do relatório da etapa 2) | confirmar que é o desejado | decisão do usuário | BASES R12 |
| K11 | Derrota por falta de tropa (ramo logístico): sem soldados de combate **e** sem camisa em base/fábrica/caminhão | só então `DERROTA` | não perde com camisas na fábrica/caminhão | — | BASES |

## 10. V — Persistência (50 min; hex; **2 reinícios do jogo**) e T — 10 min com 3 bases (15 min)

Roteiro de `persistencia/ROTEIRO_LABORATORIO.md` **com os números da v4**: implantação **1000** (2 estruturas + **2** TruckW), `spent 1000`, **4** registros `built`,
**4** spawns na restauração (refinaria 2700, fábrica 2000, 2 TruckW 900, Team 1) — o roteiro original fala em 1100/3 TruckW/5 spawns (pilha sem coleta). Sonda de
estado: `pv4_estado.lua` (e `t_persist_estado.lua`, que lê o mesmo razão da persistência) **antes** e **depois**; comparar com `diff`.

| ID | Passo | Medir | PASS | FAIL | Fecha |
|---|---|---|---|---|---|
| V0 | Carga 1: `pv4_cmd_implantar.lua`, `pv4_cmd_partida.lua` (liga as ondas; `MODO="ondas"` só garante); deixar ≥ 90 s com logística e (idealmente) 1 base avançada e 1 comboio; `pv4_estado.lua` | 2 instalações + 2 TruckW; carteira `0/1000` com 4 `built` | base de comparação | — | PERSISTENCIA L0 |
| V1 | `pv4_cmd_save.lua` com caminhão em `toDep` e job em curso | `true`; `save.txt` começa com `return {`, ASCII, sem `function`/`load`; `.bak` só a partir do 2º save; SHA256, tamanho e **ms** do `sv.save` | atômico | tempo alto (> 1 quadro): anotar | PERSISTENCIA L1 |
| V2 | Ler o arquivo fora do jogo: `PYTHONPATH=D:/tools/pylibs python dados/paralel/pacote_v4/ler_save.py <cópia do save.txt>` (usa o `sv.decode`/`sv.parseSave` do main; não escreve nada) | decodifica; `world` = caminho do hex; **sem endereço de ator**; seção `fwd` com índice de ponto/XYZ/yaw/hp/estoque por depósito | aceito | — | PERSISTENCIA L2 |
| V3 | **Reiniciar o jogo** (`restart.sh`), mesmo hex, **sem** Alt+L | ruínas visíveis outra vez; nenhuma refinaria/fábrica/TruckW ativa (a infra não sobrevive sozinha); nenhuma base avançada | prova de que a infra não persiste | — | PERSISTENCIA L3 |
| V4 | `pv4_cmd_load.lua` (= Ctrl+F6) | `true`; **4 spawns** (refinaria 2700, fábrica 2000, 2 TruckW 900, Team 1) + a(s) base(s) avançada(s) refeitas no mesmo lugar; ruínas ocultas/sem colisão; carteira `0/1000` (sem débito novo); estoques, job, carga em trânsito, pontos/donos, soldados, fortificações = V1 (caminhões voltam ao estacionamento validado); ms | `pv4_estado` depois = antes | recusa: motivo no log; **a partida e o arquivo ficam** | PERSISTENCIA L4; BASES 11h |
| V5 | `pv4_cmd_load.lua` de novo | nenhum spawn novo, mesma contagem de atores, estoques não dobram, **uma** base por ponto | idempotente | duplicou = bug | PERSISTENCIA L5 |
| V6 | 60 s depois | o caminhão salvo em `toDep` replaneja e entrega **uma** vez; a fábrica conclui o job sem debitar bmat de novo | entrega única | — | PERSISTENCIA L6 |
| V7 | Autosave (30 s) e `pv4_cmd_save.lua`; listar arquivos | `.bak` = save anterior, `.tmp` ausente | rotação ok | — | PERSISTENCIA L7 |
| V8 | **Reiniciar o jogo**; **antes** de continuar, `pv4_cmd_implantar.lua` e depois `pv4_cmd_load.lua` | Alt+L cobra da carteira nova; `sv.load` reconhece a implantação idêntica, não cria nada, a carteira volta à do save (`0/1000`) | sem cobrança dupla | — | PERSISTENCIA L8 |
| V9 | Recusas com sessão viva (partida rodando): (a) save de outra região (copiar o do HomeRegionW), (b) `save.txt` truncado à metade sem `.bak`, (c) `["v"]=3`, (d) `fwd` adulterado (x do ponto fora do raio / `hp` > 1725 / código errado), (e) ruína movida: pular | `false`; `Continuar recusado (partida atual e save preservados)`; soldados/estoques da sessão iguais; arquivos com o mesmo SHA256 | nada muda | muda algo = bug grave | PERSISTENCIA L9 |
| V10 | Falha pós-preflight é difícil de provocar sem hotpatch: **não forçar**. Só registrar se aparecer `INCOMPLETA … autosave suspenso` espontâneo | log | — | — | PERSISTENCIA L10 |
| V11 | Vitória/derrota (ou `sv.clear()` pelo canal no fim) | `save.txt`, `.tmp`, `.bak`, `.corrupt` removidos | limpo | — | PERSISTENCIA L11 |
| V12 | Fim: restaurar os arquivos de save do P2 | SHA256 igual ao inicial | restaurado | — | PERSISTENCIA L12 |
| V13 | Medições: ms de `sv.save`/`sv.load` (game thread), retorno de `os.rename/remove/io.open("wb")/f:seek` (já em S7), `World:GetFullName()` no hex e após o reinício, ruína/rotação idênticas entre cargas (≤ 2 m, ≤ 1°) | números no relatório | — | — | PERSISTENCIA |
| T1 | **10 min com 3 bases**: construir 3 bases (K3, `CREDITAR` registrado), `pv4_perfil.lua` aos 0/5/10 min, ondas ligadas, `pv4_cmd_enviar.lua` alternando bases; `UE4SS.log` | PID vivo 10 min; `mod ms/quadro` vs linha de base (S3/C9); painel com principal + 3 bases + pedido (até +4 linhas); atores `BPForwardBase1_C` = 3; sem `Registry`/`Access violation` | estável, custo anotado | queda: **parar**, é achado de estabilidade, não "ajuste" | BASES (10 min com 3 bases); ESTABILIDADE |

## 11. R — Regressão prolongada com o robô (opcional; +70 a +90 min no mínimo)

`ia_logistica/ROTEIRO_LABORATORIO.md`, matriz B0–B3. **Antes de usar o robô na v4 (R0)**: `D:/tools/foxhole-lab/t_bot.lua` está defasado — recruta com `economy.manpower >= 45`
(na logística a mão de obra não limita mais), manda **todo** o esquadrão (inclusive os trabalhadores) de volta ao ponto A com `m.target`, não constrói bases nem usa `L`, e
`t_bot0.lua` usa `newGame()` (agora com 3 trabalhadores e sem caminhão de recurso). Adaptação mínima (fora do repositório, do LABORATORIO): excluir `m.role=="worker"` do laço "volta para A"
e aceitar que `recruit` pode recusar por falta de fuzil. Sem isso, B0–B3 medem o robô, não a v4. Com o robô ligado: **não** usar o canal (esperar com `until grep -q "auto<TAB>false" botrun.log`).

| Célula | Build | Interdição | Registrar |
|---|---|---|---|
| B0 | main **sem** IA_LOGISTICA (só estabilidade + economia): guardar a fonte 33d6c7e5… (`base_pre_integracao/`) e publicá-la só para esta célula | a do robô | vitória/derrota, onda final, abates/perdas, duração, comboios |
| B1 | v4 | a do robô | o mesmo + `logi.eReport()` no fim + `auditoria` |
| B2 | v4 | forçada: manter o esquadrão na rota dos comboios | o mesmo; comparar ondas 4–10 com B1 |
| B3 | v4 com `CFG.ECHAIN.free = 5` (já é o padrão v2; para variar: 3 ou 7 via canal **antes** de ligar o robô) | como B2 | calibrar o piso |

Mínimo: 3 partidas por célula na dificuldade normal (+1 fácil, +1 difícil). Aprovação técnica: `auditoria=true` ao fim de **toda** partida; nenhum erro Lua/crash em ≥ 30 min; `BPTruckC` ativos ≤ 2.
Efeito rastreável: em B2, perdas > 0, ondas com `byCut` > 0, ondas 4–10 menores que B1; quando a interdição cessa, alguma onda volta a `faltaram 0`.
Equilíbrio é decisão do usuário (histórico B0: lote 12 vitória 111/24; lote 13 derrota onda 10, 83/38). Amostrador de quadro: `LoopInGameThreadWithDelay(100)` gravando em `_G`, não pelo canal.

## 12. Z — Encerramento (10 min)

1. `pv4_cmd_modo.lua` `limpar` e `sv.clear()` se o save de teste não for mais necessário; **restaurar** `save.txt*` do P2 (SHA256 igual).
2. Remover `map.txt` temporário (padrão HomeRegionW).
3. Reunir as saídas (`saida_*.txt`), capturas, hashes e PIDs numa pasta fora do repositório; preencher `MODLOG_RASCUNHO.md` (`[preencher no laboratório]`).
4. **Encerrar só o PID da cópia** (`D:\FoxholeLab\Foxhole`); não fechar o Steam. Não deixar o jogo aberto "pronto para testar".

## 13. Rastreio: de onde vem cada item (nada foi descartado)

| Origem | Itens | Onde está aqui |
|---|---|---|
| `ia_logistica/ROTEIRO_LABORATORIO.md` | L1–L12 | I1–I12 (L5 pelo canal com `pv4_cmd_morteiro`; a tecla Ctrl+5 real, no TESTE_MANUAL; L9 também em V) |
| idem | B0–B3, aprovação técnica/efeito/equilíbrio | §11 R (+ R0 do robô) |
| `ia_logistica/acabamento/RELATORIO.md` §6 | 1 cadência/ciclo do caminhão; 2 `eReport`; 3 matar caminhão sob consumo + aviso `fábrica guarda…`; 4 `elogi` corrompido; 5 `io/os`, BPTruckC real, rota, desempenho | I14; I14/R; C12; I13; S7/I2 |
| `coleta_manual/ROTEIRO_LABORATORIO.md` | 1–9 | C1–C9 |
| `coleta_manual/RELATORIO.md` §6 | A* real, animação sem arma, `spawnTruck`, custo por quadro, fluxo humano, veículos/terreno | C3, S9, C5, C9, C4/TESTE_MANUAL, C7 |
| `persistencia/ROTEIRO_LABORATORIO.md` | L0–L12 + medições + "não validado" (rotas, equilíbrio, queda entre renames, UI) | V0–V12, V13; os "não validados" ficam fora (§14) |
| `bases_avancadas/etapa2/RELATORIO.md` §6 | A1/A2, A3, A4, B1, L2, L4–L10, calibração, Shift+J não dispara J | S4/S5, S6/H1a, K1, S11, K1, K2–K11/V4/T1, DECISOES, TESTE_MANUAL |
| `bases_avancadas` etapa 1 (`sondas/A1–A4`, `ESPECIFICACAO`) | sondas só leitura, R1 (respawn nativo), R10 (`ItemHolder`) | S4–S6, S11 |
| `interface/RELATORIO.md` | painel em partida ativa/pausa/logística desligada/mapa novo/depósito perdido/caminhão morto; sondas UMG da caixa de seleção | C13 + captura em cada estado; a **caixa de seleção** não faz parte do lote (§14) |
| `economia/RELATORIO.md` | cadeia completa sem estoque fictício; escassez/corte/retomada; rifle recrutado/bandagem tratada; save | C10–C12, C8/V; bandagem tratada → TESTE_MANUAL |
| `estabilidade/controle_crash.md`, `auditoria.md` | A1/B1/B2/A2; matriz A–J | G1–G4, G5 |
| `estradas/*` | rede de estradas, trajetos | **fora** (§14) |
| `COLETA`/`ECONOMIA`/`PERSIST` "medições" | `ms` de save/load, `rename`, `GetFullName` | S7, V13 |

## 14. Fora deste lote (não vale como falta)

- **ESTRADAS**: a pilha não contém o driver; caminhões continuam em reta e sem colisão. Gates próprios (schema de `Connections/Points`, cardinalidade, geometria,
  trajetos ao vivo, água/pontes) em `estradas/ENTREGA.md`, `EVIDENCIA_SCHEMA.md`, `ENVELOPE_GATE.md`. Antes de integrar o adaptador, corrigir o crédito de `factory.ammo/shirts`
  para `logi.fac` via `logi.moveCargo` (`COMO_INTEGRAR.md` §8).
- Caixa de seleção visível ao arrastar (INTERFACE): sondas UMG/projeção/DPI ainda não executadas; não está na pilha.
- Plano B visual da base avançada (malha do mod) e ruína nativa (`CFG.FWD.ruin`): só depois do S11.
- Todos os itens com **entrada real** (teclas, mouse, legibilidade, equilíbrio de jogo): `TESTE_MANUAL_RASCUNHO.md` e `DECISOES_EM_ABERTO.md`.
- Queda entre os dois `rename` do salvamento (só offline) e rotas por estrada.
