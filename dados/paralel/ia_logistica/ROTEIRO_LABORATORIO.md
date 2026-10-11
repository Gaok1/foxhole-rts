# Roteiro de laboratório da IA_LOGISTICA (para o agente LABORATORIO)

Este roteiro foi **preparado e não executado**. O CLAUDE_IA_LOGISTICA não abriu o jogo nem usou o canal ou o
botloop. Quem executa é o dono do laboratório, depois de o coordenador integrar o lote na ordem
ESTABILIDADE → ECONOMIA → IA_LOGISTICA (ver `RELATORIO.md` §5). Cada linha é aprovada ou reprovada com
evidência (log, saída do canal, captura). Registre em cada linha o hash do `main.lua` publicado.

## Regras do lote
- Antes de lançar: Steam aberto e logado, cópia em `D:\FoxholeLab\Foxhole`, nenhum `botloop.sh` rodando
  (`Get-CimInstance Win32_Process`). Publique com `bash D:/tools/foxhole-lab/restart.sh`. Não use Ctrl+R.
- Não use o canal com o robô ligado. Sonda de leitura: copie `t_ia_logistica.lua` desta pasta para
  `D:/tools/foxhole-lab/` e rode `sh D:/tools/foxhole-lab/run.sh t_ia_logistica.lua`. Ela só lê estado.
- Sem injeção de teclado ou mouse. As teclas de partida (Shift+F6, Ctrl+F6, Alt+F6) são do usuário ou de
  comandos equivalentes no canal que o laboratório já usa. A IA_LOGISTICA não traz tecla nova.
- Região: a mesma em que a cadeia do jogador foi validada (CallumsCapeHex, lote 17), com o Alt+L já aceito.
  HomeRegionW serve só como bancada.
- Terminada a validação, encerre só o PID da cópia. Steam e firewall ficam como estão.

## Matriz técnica (curta, com canal)

| ID | Passo | Aprovação |
|---|---|---|
| L1 | Nova partida com logística. Rode a sonda logo no início. | `auditoria=true (razão fechado)`, `ativo=true`, frente m2 c10, bmat 240, frota livre 2. HUD com "INIMIGO: frente equipa 10". Nenhum erro Lua no `UE4SS.log`. |
| L2 | Espere o 1º comboio (20 s depois do início das ondas, mais o que faltar de carga). | Evento "comboio 1 saiu: N cx". O ator BPTruckC existe, `ator_ativo=true` e a carga aparece na sonda. A retaguarda caiu exatamente as caixas da carga. Alerta "COMBOIO INIMIGO ... (carga)". |
| L3 | Deixe o comboio chegar sem interferir. | Um único "entregou na frente"; a frente sobe por `units` (caixa de camisas = 10). Rode a sonda 3x seguidas: nenhuma segunda entrega. O caminhão volta e some, e a frota livre volta a 2. `auditoria=true`. |
| L4 | Emboscada: soldados nossos a menos de 15 m do comboio carregado (ordem de movimento real pelo usuário, ou posição já existente). | "comboio N perdido (destruído): -X munição, -Y camisas" **uma vez**. Alerta "COMBOIO INIMIGO DESTRUÍDO (+25): a frente perde ...". A frente não muda. "reconstruindo 1". `auditoria=true`. |
| L5 | Morteiro (Ctrl+5) sobre um comboio carregado. | O mesmo de L4. Um morteiro sobre caminhão já destruído não registra segunda perda. |
| L6 | Espere 30 s ou mais depois da perda. | "caminhão de comboio reconstruído (-100 bmat)" só quando bmat ≥ 100. A fábrica fica parada se não houver caminhão livre e houver reconstrução vencida. |
| L7 | Ondas com a frente cheia e depois vazia. Compare `#enemies` logo após cada spawn com o registro da onda. | `enviados` = soldados que nasceram de fato. Com a frente vazia: "faltou suprimento ao inimigo: a onda vem com N a menos (falta camisas/munição; K por comboios destruídos)". Onda real no piso de 3, sem soldado a mais. |
| L8 | Ponto inimigo com reforço (`ai.tick`) e frente seca, depois abastecida. | Sem material, nenhum "REFORÇO INIMIGO". Com material, reforço de 2-3 e a frente debitada pelo número que **nasceu**. |
| L9 | Save/continue com comboio na estrada: espere um save (30 s), feche e continue (Ctrl+F6). | Evento "cadeia inimiga restaurada do save (reenviar ...)". O pendente é igual à carga que estava na estrada. `auditoria=true`. O próximo comboio leva o pendente. Continuar duas vezes não duplica nada (compare inicial+produzido). |
| L10 | Ator do comboio inválido: pelo canal, `logi.foes[1].pawn:K2_DestroyActor()` (só esta linha, sonda separada e registrada). | No quadro seguinte: "perdido (ator do caminhão inválido)", sem entrega e `auditoria=true`. Nenhum crash ou erro nativo. |
| L11 | Assalto (Alt+F6). | Nenhum comboio, frente intacta, nenhum consumo (`ativo=false`). |
| L12 | Shift+F6 várias vezes e F11 no meio da partida. | Nenhum comboio sobra no mundo (contar `BPTruckC_C` ativos); `logi.en` novo; nenhum erro. |

## Matriz de regressão prolongada (combate e equilíbrio, com robô)

Robô de sempre: `sh D:/tools/foxhole-lab/botloop.sh` em segundo plano, esperando com
`until grep -q "auto<TAB>false" botrun.log`. Com o robô ligado, não use o canal. Leia a sonda **depois** de
cada partida. Mínimo: 3 partidas por célula na dificuldade normal e 1 em fácil e 1 em difícil, se der tempo.

| Célula | Build | Interdição | Registrar |
|---|---|---|---|
| B0 | main **sem** IA_LOGISTICA (só ESTABILIDADE+ECONOMIA) | a do robô (se ele não ataca comboios, anotar) | vitória/derrota, onda final, abates/perdas, duração, comboios/destruídos |
| B1 | com IA_LOGISTICA | a do robô | o mesmo de B0 + `logi.eReport()` no fim (ondas: pedido/enviado/faltou/byCut) + `auditoria` |
| B2 | com IA_LOGISTICA | forçada: o usuário ou a ordem do robô mantém o esquadrão na rota dos comboios | o mesmo de B1; comparar o tamanho das ondas 4-10 com B1 |
| B3 | com IA_LOGISTICA, `CFG.ECHAIN.free` = 5 (via canal **antes** de ligar o robô) | como B2 | o mesmo; serve para calibrar o piso |

Aprovação técnica (vale para B1-B3): `auditoria=true` ao fim de **toda** partida; nenhum erro Lua ou crash
UE4SS em 30 min ou mais; quantidade de BPTruckC ativos ≤ 2 (frota) em qualquer amostra. Para o tempo de
quadro, amostrador `LoopInGameThreadWithDelay(100)` gravando em `_G` (não pelo canal), comparando B0 e B1.

Aprovação de efeito rastreável: em B2, a perda registrada (`perdido` no razão) > 0, há ondas com `byCut` > 0,
e as ondas 4-10 de B2 são menores que as de B1 no mesmo índice. Depois que a interdição para, alguma onda
volta a ter `faltaram 0`.

Equilíbrio (é decisão do usuário, o roteiro só mede): o resultado de B1 deve ficar perto do histórico B0
(lote 12: vitória nas 10 ondas, 111/24; lote 13: derrota na onda 10, 83/38). Se B2 ficar trivial (ondas presas
no piso desde cedo), calibrar `free`, `front0`, `want`, `trip` ou `minLoad` e repetir só a célula afetada.

## O que fica fora deste roteiro
- O trajeto por estrada do comboio depende do driver da ESTRADAS, que não existe ainda; hoje ele anda em reta
  e sem colisão, como antes.
- A legibilidade do HUD/painel e a entrada real (emboscada por clique) são validadas pelo usuário.
