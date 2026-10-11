# GOTCHAS_CONSOLIDADOS — para a nota `knowledge/games/foxhole/local-listen-server-rts-sandbox-in-foxhole-with-ue4ss.md`

Junta, sem duplicatas, `ia_logistica/GOTCHAS_PROPOSTOS.md` (7), `persistencia/GOTCHAS_PROPOSTOS.md` (7), os achados citados nos relatórios da ECONOMIA, do ensaio de integração, do acabamento da IA,
da ESTABILIDADE e da INTERFACE, e o que este pacote aprendeu. Nada foi escrito no universal-modder (fora do escopo do pacote). Quem registra é a task INTEGRACAO/LABORATORIO:
`cd D:/GitHub/universal-modder` → editar a nota → `UM_HOME=D:/tools/um-home python -m um kb check` (local; PR só com OK do usuário).

A nota atual termina no item **42**; este arquivo vai de **48** a **77** conforme o pedido (43–47 ficam para outras propostas pendentes; se a numeração real da nota for outra, renumere
só o prefixo, o texto não depende do número). Marca em cada item: **[confirmado ao vivo]** ou **[só offline]**. **Nenhum destes itens foi confirmado no jogo**: o pacote é de
preparação; o laboratório troca a marca pelo resultado do passo citado em "Verifica" (`ROTEIRO_LOTE.md`). Itens de dados/design (valores de `CFG`) não são gotchas e ficam em
`DECISOES_EM_ABERTO.md`.

---

48. **Contador de "carga" não é logística.** [só offline] O comboio inimigo somava +1 carga ao chegar, sem origem, e o save não guardava esse número (todo continuar devolvia `cargo0`).
    **Causa:** a interdição não tinha efeito rastreável porque nada era debitado de um estoque que pudesse acabar. **Correção:** o caminhão leva caixas debitadas de uma retaguarda finita
    e a perda entra num razão (inicial + produzido = estoques + trânsito + consumido + perdido) conferível pelo canal (`eAudit`/`eReport`; `auditoria=true` ao fim de toda partida). Verifica: I1–I14.

49. **Fábrica que sempre pode gastar 80 bmat nunca deixa o caminhão de 100 voltar.** [só offline] **Sintoma:** sob consumo contínuo o caminhão destruído não volta. **Causa:** a receita (80) é mais barata
    que o caminhão (100): o bmat nunca acumula 100 (0/31 voltavam no harness). **Correção:** reservar `truckCost` por caminhão destruído ou ainda não construído (`logi.rebuildReserve`) e deixar a fábrica
    esperar; o pedido de base avançada reserva mais 300 **depois** da reserva do caminhão (o caminhão tem prioridade). O painel mostra `Fábrica | guarda N bmat para …`. Vale para os dois lados; o
    efeito do lado do jogador ainda é hipótese. Verifica: C12.

50. **Comboio de uma caixa desperdiça caminhão.** [só offline] Despachar assim que existe uma caixa faz cada emboscada custar um caminhão inteiro por pouca carga, e o produto mais barato monopoliza a
    fábrica. **Correção:** carga mínima (`minLoad 3`) ou o pedido completo da frente (`trip 20`). Verifica: I2, I7.

51. **O save arredonda.** [só offline] `sv.ser` grava números não inteiros com 3 casas; um razão validado no load com tolerância 1e-6 recusa saves legítimos. **Correção:** validar com folga (0,05) e, ao
    restaurar, absorver a sobra nos termos de origem para o razão em memória fechar exato; nunca transformar a sobra em estoque. Verifica: I9, V4.

52. **Atribuir a interdição exige contrafactual.** [só offline] A carga perdida antes da onda N afeta várias ondas, não só a seguinte. **Correção:** um contador "perdas desde a última onda" subestima; use um
    estoque fantasma que se gasta como as ondas o teriam consumido (`byCut`). Verifica: I14.

53. **A calibração da cadeia inimiga só vale na cadência de onda real.** [só offline] A tabela de calibração (piso `free 5`, `want 4/20`, `trip 20`) vale em cadência de onda ≥ ~55 s; a refinaria
    (2 bmat/s) é o teto de qualquer cadeia, então mais caminhões ou piso maior não geram mais soldados. **Correção:** medir a cadência real das ondas (robô e humano) antes de mexer nos números. Verifica: I14, R.

54. **Teste do chunk inteiro com fronteiras trocadas.** [só offline] No harness lupa, código acrescentado ao fim do mesmo chunk pode reatribuir `local function` de topo (`spawnEnemies`, `waveSpawnPoint`,
    `isLocalAuthority`), e as funções do mod enxergam isso como upvalue. **Uso:** trocar só a fronteira de engine e chamar o `waveTick`/`ai.tick`/`sv.load` reais, sem copiar a implementação nem editar o `main.lua`.

55. **Decidir, criar, debitar (nessa ordem).** [só offline] O spawn de soldado, caminhão ou base pode falhar parcialmente; ator com `IsValid` e `bActorIsBeingDestroyed` não conta como criado. **Correção:**
    decidir quantidade e local numa função **pura** (`logi.spawnSite`), criar, confirmar o ator (posição, vida, `CodeName`) e só então debitar num ponto único (`logi.spawnCommit`; o bmat da base só sai
    depois do ator validado). Em falha: nada debitado, ator desfeito. Vale para onda inimiga (`combat.wave` inalterado detecta a onda que nem abriu), recruta, trabalhador e base. Verifica: K3, K6.

56. **Save como `return {...}` + `load` não é leitura segura.** [só offline] Ambiente vazio impede `os`/`io`, mas não um laço infinito nem uma string gigante, e aceita qualquer expressão que avalie para
    tabela. **Correção:** parser de literais (tabelas `[k]=v`, números, strings `%q`, booleanos) com limites de bytes/profundidade/itens, sem dependência (`sv.decode`/`sv.parseSave`). `sv.ser` também escrevia
    NaN/inf como `0` e userdata como `nil` em silêncio: validar o que vai ser gravado e decodificar o próprio texto antes de trocar o arquivo. Fora do jogo: `ler_save.py`. Verifica: V1, V2.

57. **Windows: `os.rename` não sobrescreve.** [só offline: confirmado em Lua puro, não no Lua do UE4SS] O MSVCRT falha se o destino existe (`rename` devolve `nil, "File exists"`). **Correção:** escrita atômica
    com temporário conferido por releitura → anterior vira `.bak` (ou `.corrupt`, se inválido) → temporário vira o save; o código remove o destino antes. Falha devolve o anterior. Na leitura, ordem
    save → `.tmp` (queda entre os renames) → `.bak`. Verifica: S7 (`pv4_io_os.lua`), V1, V7.

58. **Infraestrutura implantada não sobrevive ao reinício, e a carteira chaveada por endereço renasce cheia.** [só offline] `S.deploy` era chaveado por `GetFullName..GetAddress` (muda a cada carga) e não ia
    para o save: continuar pedia Alt+L de novo e pagava outra vez. **Correção:** persistir o que foi **pago** (código, XYZ, yaw da ruína) e a carteira (`spent`); na carga nova refazer só sobre ruína
    correspondente (≤ 2 m, ≤ 1°), sem cobrar de novo, e os caminhões só até o número pago. Nunca persistir endereço (ele só identifica a carga atual). Verifica: V3–V8.

59. **Índice de ponto como identidade quebra se um ponto não volta.** [só offline] O save guarda depósitos, postos e bases por índice; `addPoint` pode recusar (sem superfície, sobreposição, limite).
    **Correção:** conferir superfície/sobreposição antes de limpar a partida e comparar índice→coordenada depois; diferença = logística não restaurada (sem estoque inicial fictício no lugar) e autosave
    suspenso (`INCOMPLETA`) para não sobrescrever o save bom. Verifica: V9, V10.

60. **Preflight antes de `clearSquad`.** [só offline] O continuar antigo destruía a partida atual e só depois descobria problemas. **Ordem segura:** ler/validar → mundo/superfície/ruínas/carteira/logística →
    refazer infra e bases (rollback próprio) → limpar e restaurar → conferir contagens. A recusa preserva a partida e o arquivo. Verifica: V9.

61. **`logi.start` cria estoque de cenário.** [só offline] Restaurar chamando `start` e depois atribuindo campos deixa estoque fictício se algo falha no meio; o comboio inimigo voltava a `cargo0`. **Correção:**
    validar tudo antes; em falha, `logi.reset` em vez de deixar o estoque inicial. Seção regenerável e **descartável** (a cadeia inimiga, `elogi`): em vez de recusar o save, descarta só ela e reinicia do
    cenário com aviso ("CADEIA INIMIGA REINICIADA"). Verifica: I13.

62. **Rotas não se salvam.** [só offline] O grafo de ESTRADAS tem epoch com a sessão; rota antiga é inválida por construção. **Correção:** salvar só estado/carga/destino por identificador e replanejar
    (`route/routeDest/pathJob = nil`). Verifica: V6.

63. **Nova receita não funciona só editando `CFG.LOGI`.** [só offline] Transporte, depósito, prioridade (Shift+L), consumo e save estavam fixos em `ammo`/`shirts`. **Correção:** ao acrescentar um produto,
    percorrer a lista inteira (receita → fábrica → caminhão → depósito → prioridade → recrutamento/médico → save → painel → razão). Os 4 produtos atuais estão em `CFG.LOGI.products`. Verifica: C10.

64. **Receita nativa ≠ item parecido.** [só offline] Granada (`GrenadeW`) exige **Explosive** além de Cloth; bandagem consumível (`Bandages`) não equivale a `FirstAidKit`. **Correção:** ler o
    `ProductionResource`/receita real do cliente (ver gotcha 35, `tools/export_costs.lua`) antes de nomear um produto; não substituir por um nome parecido.

65. **Um painel que substitui a função inteira não comuta com patches que ancoram dentro dela.** [só offline] O painel novo (INTERFACE) substitui `logi.hudLine` inteira por limites de texto; patches de outras entregas que
    ancoram numa linha interna (produtos, médico, coleta, base) deixam de aplicar. **Correção:** rebasear o painel sobre a pilha (a INTERFACE v2 foi refeita depois da v2 e da reserva) e
    ordenar: ECONOMIA > IA_LOGISTICA > reserva > INTERFACE > PERSISTENCIA > COLETA > BASES.

66. **`.patch` gravado por `write_text` no Windows sai CRLF e não casa com o main em LF (ou o contrário).** [só offline] **Correção:** gravar com `newline="\n"`, ou aplicar por script (`aplicar_*.py`)
    e manter pares `.patch` (CRLF, para o main CRLF) e `*_lf.patch`; conferir SHA256 do resultado, não só "aplicou sem erro". O `main.lua` do repositório é CRLF consistente.

67. **Adaptador de retorno de carga de 2 produtos fica obsoleto quando a economia generaliza produtos.** [só offline] O adaptador que devolve a carga ao voltar da entrega (`returnCargo`, `back = {…}`) nasceu para munição e camisas;
    com 4 produtos, qualquer cópia antiga só trata dois. **Correção:** iterar `CFG.LOGI.products` em qualquer movimento de carga e testar com os 4.

68. **Painel mistura caixas e unidades; o retângulo XY do seletor não é o da tela.** [só offline] No painel, caixas (munição) e unidades (camisas, fuzis, bandagens) aparecem lado a lado; rotular sempre
    (`camisas 3 caixas (30 unidades)`). Projeção/DPI/borda do UMG ainda exigem sonda; cortes de texto só se veem em captura em vários zooms/resoluções (C13, itens 12ad do manual).

69. **Guard de lifetime/preflight no contorno não explica a queda do UE4SS.** [só offline] O mock reproduz chamadas em pawn/clone com `bActorIsBeingDestroyed` ou fonte `IsValid=false`, e o preflight as
    bloqueia, mas **isso não explica** os crashes do lote 17: `pcall` protege erro Lua, não lifetime nativo, e fonte `IsValid=true` durante retirada ou troca ainda precisa de rastro real. Não atribua causa
    sem repetir a carga limpa no mesmo hash. (A v4 não toca esse código.) Gate: G.

70. **`notify` também grava no `UE4SS.log`.** [só offline: lido no código] `notify(msg, secs)` chama `log(msg)` (prefixo `[FoxholeRTS]`) antes do alerta nativo. **Uso:** toda mensagem do painel e dos alertas
    (recusas, `BASE AVANÇADA … construída`, `COMBOIO INIMIGO DESTRUÍDO`) pode ser auditada no log mesmo quando a captura não pegou o texto; não precisa de OCR.

71. **Teste que ancora no texto do main antigo precisa do main antigo.** [só offline] Depois de integrar a v4, alguns testes (`test_pilha_v4` passos 06b/06b-L/06c/08/08-L) falham com "âncora não única" porque
    procuram o código da base anterior. **Correção:** guardar uma cópia do main anterior (`base_pre_integracao/`, SHA `33d6c7e5…`) e redirecionar só a leitura do teste para ela; manter
    um controle negativo (suíte quebrada de propósito reprova). A bateria `bateria_pos_integracao.py` faz isso sem escrever em disco.

72. **Sonda que alterna estado tem de ser idempotente: `newGame` já liga as ondas.** [só offline] `newGame` termina em `toggleWaves()` com `combat.auto=false` antes, então a partida nova **já tem ondas
    automáticas**; uma sonda que chamasse `toggleWaves()` às cegas as desligaria (e `sv.save` exige `combat.auto`). **Correção:** `pv4_cmd_modo.lua` liga só se desligada (`ondas`) e desliga só se
    ligada (`sem_ondas`). Vale para qualquer toggle (pausa, velocidade, borda).

73. **Relógio de confirmação de teclado é tempo real, não tempo de jogo.** [só offline] Os 2 toques de Shift+J usam `GetRealTimeSeconds` (4 s): pausar o jogo entre os toques **não** estica a janela. O pedido
    pendente, ao contrário, vence em 180 s de tempo de jogo. Decida por efeito: confirmação de UI → real; simulação → de jogo. Verifica: K10; decisão em `DECISOES_EM_ABERTO.md`.

74. **Classe nativa que existe no pak não prova um spawn íntegro.** [só offline] `ForwardBase1` (1725 HP) aparece no inventário do cliente, mas **nenhum agente a instanciou ao vivo**. **Correção:** contrato
    `strict` no spawn (`Health == MaxHealth == 1725`, `CodeName == ForwardBase1`, posição e yaw como pedidos) antes de debitar o bmat; falha desfaz o ator e não cobra. `TeamId` fica sem escrita
    (`FWD.teamId=nil`) até medir. Plano B (malha) é outra task se a classe não nascer. Verifica: S11 (B1 de bases).

75. **Soldado desarmado: `grip 0` não prova que o mesh fica sem T-pose.** [só offline] O trabalhador usa `CFG.WEAPONS.worker` com `grip=0` e alcance 0. Ninguém viu o soldado sem arma ao vivo; o código
    comenta "confirmar no laboratório" e o risco é T-pose ou animação de arma sem arma. **Correção:** olhar a captura no passo C2 (3 trabalhadores) antes de aprovar; se aparecer T-pose, dar a postura de outra classe sem munição.
    Verifica: C2, item 12z do manual.

76. **Contagem de locais: o compilador decide.** [só offline] O limite de 200 locais por chunk Lua: o main tem 178 pelo compilador (folga 22) e 175 pela contagem do `check_globals.py`. A folga (22)
    vale a menor; novas funções vão em tabelas (`logi`, `sv`, `rts`, `CFG`, `S`). A bateria confere a folga em Lua 5.4 e 5.5.

77. **Papel que não é combate no mesmo vetor do esquadrão contamina toda contagem `#squad`.** [só offline] Os trabalhadores da coleta moram em `squad` (selecionáveis, atacáveis, salvos como qualquer soldado). A v4
    já os tirava do teto de 12 e da derrota logística, mas a **escala da onda inimiga** (`floor(#squad * WAVE_SQUAD_SCALE)`), o aviso "próxima onda" e a derrota no Assalto ainda contavam todo mundo: 3 trabalhadores
    viravam ~+1 inimigo por onda. **Correção (v4.1):** uma função única de combatentes (`rts.combatCount`) em todo uso que **decide** algo (escala, derrota, limite); `#squad` fica só para o que é de fato o vetor
    (índices, salvar, listar). Ao criar um papel novo, `grep '#squad'` e classificar cada uso. Vale também para posição: `squadCenter()` (que decide de onde vêm ondas e reforço) só conta combatentes vivos, com fallback para todos. Teste de contraste: `v4_1/test_v4_1.py`.
