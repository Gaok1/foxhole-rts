# Foxhole RTS — diário do projeto

## 2026-10-11 — Repositório público no GitHub

- Pasta virou repositório git e foi publicada em github.com/Gaok1/foxhole-rts (público, MIT) para chamar
  colaboradores da comunidade de Foxhole. Subiu tudo, inclusive `dados/paralel/`.
- `README.md` da raiz em inglês (aviso de não afiliação à Siege Camp, sem arquivos do jogo, nunca online).
- `PROGRESS.md`: checklist pública por fase ([x] = 1, [~] = 0,5, [ ] = 0); `tools/progress.py` recalcula
  as barras do README. Ponto de partida: fase 1 65%, fase 2 71%, fase 3 54%, fase 4 20%, fase 5 0%, MVP 62%.
- `.gitattributes` com `* -text` preserva os bytes dos patches e candidatos com SHA256.

## 2026-10-11 — Oracle estendido ao produtor nativo da lista

- Executadas offline as cinco funções reais produtor → bridge → virtual do
  controlador → encaminhamento → helper. Fixtures fornecem mundo/classes/PS;
  getters/destrutor/comparador são shims explícitos, nenhuma execução Unreal.
- Dois PlayerStates com objeto de identificador nulo produzem oito entradas em
  quatro ticks, com bVoiceChatEnabled false. Sem PlayerSaveGame também acumulam.
  Ao trocar uma entrada do roster por objeto não nulo, falha read0 no mesmo
  RVA b2b5f7. Controles roster vazio/PS ausente/objeto válido/deduplicação PASS.
- Evidência exclui desligar voz ou remover PlayerSaveGame como solução suficiente
  nesse fluxo emulado. Não confirma população real, controlador culpado, GC ou fix.
  Próximo passo exige contrato NPC/roster vivo, não fabricar ID nem usar RPC.
- Script/saída externos: re-agent/test_native_roster_producer.py e
  logistics2-native-producer-oracle.txt em D:/tools/foxhole-lab. Laboratório
  ausente confirmado; nenhuma mudança em main/publicação/run.

## 2026-10-11 — Crash reproduzido no helper nativo, offline

- Oracle externo executou os 303 bytes reais de 140b2b5a0 em CPU Unicorn,
  sem abrir/alterar o jogo. Oito entradas nulas acumulam; entrada não nula
  depois delas falha lendo endereço zero exatamente no RVA b2b5f7 do minidump.
- Controles positivos de comparação/deduplicação PASS com comparador fictício.
  Item válido antes de um nulo também não protege uma entrada diferente.
- Isso confirma a sequência de falha do helper, NÃO quem produziu os nulos,
  semântica do identificador real, GC ou correção Unreal. Nenhuma nova run.
- Script/saída externos: D:/tools/foxhole-lab/re-agent/test_native_null_roster.py
  e D:/tools/foxhole-lab/logistics2-native-null-oracle.txt. Unicorn em D:/tools/pylibs
  é ferramenta de pesquisa, não dependência do mod.

## 2026-10-11 — Universal-modder atualizado por pedido do usuário

- git pull --ff-only em D:/GitHub/universal-modder: 76b9c7e -> 2c22014,
  main igual a origin/main. Primeiro pull recusou sobrescrever ajustes locais.
- Backup externo em D:/tools/um-pull-backup-20261011-180446 e stash mantido.
  Ajustes um/win.py, um/ps1/WinDrive.ps1 e nota Foxhole reaplicados; conflito
  apenas no cabeçalho de comandos do WinDrive resolvido preservando min/sleep/idle.
  Alterações voltaram ao estado não staged; nenhum commit/push/PR criado.
- Nota Foxhole comparada ao backup: conteúdo idêntico, apenas CRLF/LF mudou.
  Sintaxe PowerShell/Python PASS; um kb check PASS (183 notas, antes 60).
  pytest de launch não rodou: módulo pytest ausente no Python atual; não instalar
  dependências só para este pull nem alegar bateria completa do toolkit.
- Nenhuma mudança/publicação do mod ou abertura do laboratório nesta atualização.

## 2026-10-11 — Inicialização HeadlessLocalPlayer e correção do helper RE

- Investigação estática do NPC nativo achou HeadlessLocalPlayer com inicialização
  própria de identificador tipo NULL e opções Headless. Constructor sozinho não
  executa esse init. Sem UFunctions próprias refletidas e sem prova de ligação ao
  PlayerState local; não construir LocalPlayer nem perseguir conexão/login/RPC
  como tentativa de corrigir o crash.
- Corrigido helper externo pe.vtable_of: antes seguia call de base e confundia
  LocalPlayer com derivados cujos wrappers escrevem vtable inline. Check anterior
  FAIL, sete classes PASS após correção. Slots usados no diagnóstico do crash
  foram reconferidos e permanecem os mesmos. Continua heurístico, não prova live.
- Rastro próprio em dados/rastro_crash_logistics2_20261011.txt; scripts/check e
  decompilação externos. Nenhuma mudança de main, publicação ou nova run.

## 2026-10-11 — Contrato local dos bots; sonda de roster preparada offline

- RE confirma que SimCharacter testa Controller.IsLocalController no caminho de
  voz. Headless e SimPlayerController usam o mesmo getter; bIsLocalPlayerController
  true retorna antes da consulta de NetMode. A flag ligada pelo mod para movimento
  também expõe o bot ao fluxo local. Não demonstra sozinha qual ator caiu.
- OnRep_bIsInactive remove/reinsere PlayerState em GameState.PlayerArray; adição
  recusa inactive. Sem chamar ou usar como solução: participante desconectado não
  equivale a NPC vivo, efeitos de lifecycle ainda precisam rastreamento.
- Preparada tools/probe_native_npc_roster.lua para fotografar localidade/Player/
  Pawn/PlayerState/roster de comandante, tropas e pool. Sem IDs Steam, escrita,
  RPC, spawn ou timer. Getters conferem assinatura. gs() é GameplayStatics;
  GameState vem de GetGameState(world()), não confundir helper com estado.
- tools/test_native_npc_roster_probe.py PASS: assinatura válida/divergente/extra/
  ausente, deduplicação, membro/pool fora do roster, controlador destruindo,
  GameState ausente e proxies que proíbem escrita/IDs. São mocks, não prova Unreal.
- Bateria completa: 14 scripts test_*.py e check_globals.py PASS. main.lua
  inalterado, nenhum restart, WMI sem processo do laboratório.

## 2026-10-11 — Crash: lista de UniqueId no fluxo local de participantes/voz

- Diagnóstico offline readOnly/noanalysis confirmou PlayerState.UniqueId como
  origem dos pares compartilhados que chegam ao helper do crash, via consulta de
  proximidade e GameState.PlayerArray. Metadados em
  dados/rastro_crash_logistics2_20261011.txt; código protegido apenas externo.
- PlayerSaveGame.bVoiceChatEnabled (+0x48, setter gerado confirmado) controla
  somente consulta próxima, NÃO o loop PlayerArray posterior. Desligar voz não
  resolve por evidência e pode continuar acumulando IDs vazios.
- Helper não deduplica entrada nula e compara entrada não nula dereferenciando
  item existente sem guard. IDs vazios de bots são hipótese concreta de produtor;
  não provada população inteira/identidade do controlador no heap ausente do dump.
- Próximo: contrato de controlador local (tick consulta virtual+0x690) e lifecycle
  legítimo PlayerState de NPC; preservar posse, movimento e GC. Não fabricar IDs,
  chamar RPC ou desligar bIsLocalPlayerController cegamente para esconder o crash.
- Nenhuma alteração em main.lua, publicação ou restart. Laboratório ausente.

## 2026-10-11 — Lote logístico 2: contrato RWD confirmado; partida interrompida por crash

- Preparados scripts externos t_batch_logistics2_*; sampler1s de trabalhadores/
  ameaça/carga e resumo10s, syntax/mock PASS. Treze testes offline/globals PASS.
  Uma publicação/run CallumsCape/PID4696, hashes fonte/lab iguais
  85D7EEB942704D767402F3EEE31159D80E144C6BB170A1BF90C98BD9FCEA9DEB.
- Sonda somente leitura antes/depois da logística: mesmo caminhão com ActorCollision
  true→false; root e UpdatedComponent/Primitive=VehicleCollision(BoxComponent).
  Movimento RWDVehicleMovementComponent→SimpleVehicleMovementComponent→CharacterMovement;
  flag bIgnoreNonRootComponentsDuringVehicleMovement=true em ambos estados.
  Dados em rastro_truck_movement_{before,active}_20261011.txt. Não prova estrada,
  impacto na frota, envelope/suporte nem permite alterar flag para forçar sucesso.
- Partida fresca sem save/créditos/velocidade extra interrompida por crash.
  CrashContext ProcessId4696/158s desde início; autosave próprio em60,043s/onda1,
  bmat40/sucata0/base19camisas. Relatório final NÃO obtido: amostras estavam em RAM.
  Não aprova medevac, contratação sob ameaça, entrega ou reconstrução no Unreal.
- PID ausente/WMI confirmado, canal timeout30s. Crash DE679306…/17:36:33 preservado
  externamente em logistics2-crash; UE4SSlog copiado. Stack/metadata própria
  em dados/rastro_crash_logistics2_20261011.txt, sem minidump/código protegido no repo.
- Minidump mostra RVA0xb2b5f7/Rcx0: instrução mov rax,[rcx] em140b2b5a0.
  PCallStack inicia acima com1427c66cb; não confundir retorno do caller com fault.
  RE readOnly/noanalysis exit0 liga frame ao processamento de lista compartilhada
  via1427f2a00 e tickSimCharacter140b110c0→140b141a0→140b33df0.
  Item nulo/contexto na lista comprovado; produtor/causa completa NÃO isolados.
  Nenhum patch por offset, alteração de proteção ou reinício para tentar de novo.
- Aprendizado para próximo lote: sampler logistics3 agora escreve/fecha cada linha
  em arquivo externo, syntax/write PASS, ainda NÃO executado no jogo. Isso preserva
  diagnóstico parcial se houver crash, não recupera as amostras perdidas deste lote.
- Sem segunda run. map.txt temporário removido (baseline ausente), comando pendente
  limpo; nenhum processo lab restante, Steam16104 preservado. README/ROADMAP/BATCH/
  ENVELOPE/UM atualizados; falhas e novas ideias vão ao próximo trabalho offline.

## 2026-10-11 — Reposição automática sob ameaça e gate sem caminhão fantasma (offline)

- Fluxo rastreado: colMaintain contratava a cada3s até3vivos; spawnSite só decide
  estoque/local/saída. colFree recusava trabalhador em perigo DEPOIS do nascimento.
  Lote vivo anterior mostrou reposição esgotando camisas, mas não amostrou ameaça
  na saída: não afirmar que esse guard sozinho explica/resolverá todas as mortes.
- colThreat centraliza a distância3500cm já usada por colCalm. Contratação automática
  verifica saída escolhida antes de criar/debitar; inimigo vivo perto bloqueia e
  avisa "proteja a base". Não bloqueia contratação manual de combatentes, não muda
  dano/ondas/imunidade/estoque. Mortos/atores destruindo não seguram contratação.
  Limite3, intervalo3s, autoridade e rollback permanecem. spawnBlocked no estado
  registra motivo; retomada limpa após ameaça sumir.
- test_worker_spawn_threat executa funções reais: fronteira/distância da saída,
 30s sem gasto, retomada, cadáver/destruição, autoridade, falta de estoque,
  falha de spawn/commit e limite. Falha com colMaintain anterior, passa no candidato.
- check_mvp_batch_trace antes aprovava "reconstrução" quando faltava PLAYER_TRUCK res.
  Agora exige registro único/estado conhecido/HP finito positivo/PAWNtrue; ausência
  não vira prova. test_mvp_batch_checker usa rastros SINTÉTICOS rotulados e recusa
  ausente/morto/HP0/inf/semator/duplicado/semcleanup. Não comprova transação ou estrada.
- Treze test_*.py/globals PASS. Fonte85D7EEB942704D767402F3EEE31159D80E144C6BB170A1BF90C98BD9FCEA9DEB.
  Backup externo main-before-worker-spawn-threat.lua; sem publicação/run/entrada.
  Gates vivos continuam negativos; lote seguinte precisa registrar ameaça/saída,
  camisas, trabalhadores/carga/medevac e provar cadeia fresca em combate.

## 2026-10-11 — Rifle: referências completas distinguem trace/efeito de impacto

- Retomada offline com UM/reverse-engineering/oráculos/playbook Unreal e ponytail.
  Quatro jobs Ghidra headless readOnly/noanalysis concluídos exit0; sem jogo/GUI,
  nenhum offset executado, sem RPC/inventário. Decomp protegida permanece externa.
- Listadas todas referências diretas conhecidas do projeto, sem cap6: helper
  1409dcd30 tem dois callers(HMG e1409a71f0); query1409e9860 tem oito callers.
  Rifle140a691f0 não aparece como caller direto de dano. Não prova ausência de
  chamadas indiretas nem impossibilidade de executor local.
- Dois consumidores são FighterWeaponTrace/AirTargetingTrace, outro HitScanMount;
  não generalizar para rifle. Seguidos callbacks de dois ramos até helpers que
  gerenciam objeto/posição, sem dano conhecido nos corpos examinados.
- Guard142407030 não lê Role como142405420: resolve contexto/world e encaminha
  helper que retorna3 ou1/2. Não chamar timer guardado por3 de Authority sem prova;
  consistente com apresentação/NetMode, ainda sem validação dinâmica.
- dados/rastro_disparo_investigacao.md atualizado com endereços/limites e próximo
  recorte autoritativo. Sem mudança/publicação de main.lua ou outra sessão de jogo.
  Executor local de rifle segue pendente; não substituir por DPS/ApplyDamage temporal.

## 2026-10-11 — Retomada das estradas: contrato de movimento antes de religar colisão

- Consultados UM/roadmap/Como retomar e artefatos de estradas. Grafo real Callums
  405controles/431segmentos/4013nós está disponível, mas sem prova física de arestas.
  roads/adapter/snapshot testes PASS. Não integrar reta, cápsula de soldado ou
  Box450/210/230 como se comprovassem envelope/suporte de caminhão.
- Recuperada evidência existente: VehicleCollision400/162/140; scan de raios
  atingiu CharacterMesh0 fora dessa caixa. Root/UpdatedComponent ainda não
  identificados; sweep do ator sozinho não comprova abrangência desses corpos.
- Nova tools/probe_native_truck_movement.lua somente leitura: assinatura de
  getter confirmada antes de raiz/movement; UpdatedComponent/Primitive/flag só
  por schema específico. Lista funções e parâmetros de input/movimento sem chamar.
  Não muda colisão, não escreve física/estoque e não usa campos perigosos de mesh.
- test_native_truck_movement_probe PASS, inclusive recusas de schema/scan. Sonda
  NÃO executada no Unreal. main.lua não alterado nesta etapa; correção offline de
  medevac permanece candidata. ENVELOPE_GATE/BATCH/README atualizados.
- Laboratório mantido fechado, sem nova publicação/run. Próximo lote deve obter
  contrato nativo e integrar caminho físico, não declarar estradas prontas pelo grafo.

## 2026-10-11 — Coleta: medevac automático não é ordem do jogador (offline)

- Causa isolada no log externo native-batch-ue4ss.log, linhas866–867 e890–891:
  "trabalhador ferido recua sozinho" precede imediatamente as perdas35,8/34,3
  por "ordem do jogador". rts.medevacStep escreve medevac/retreat, não orderT;
  colStep antes descartava qualquer retreat/medevac como intervenção humana.
- Correção em colStep conserva vínculo/carga enquanto medevac está ativo,
  não coleta/entrega nem substitui rota de evacuação, suspende timeout do trecho.
  Ao curar retoma campo/refinaria. Mudança de orderT/hold/focus/area/fila/recuo
  explícito continua cancelando; morte continua perdendo carga uma única vez.
- test_collection_medevac.py executa funções reais, falha na fonte anterior e
  passa na candidata: recuo70s, cura/retomada em coleta ou retorno, entrega única
  na refinaria, morte/ordens explícitas e conservação. Navegação/engine mockados.
  Dez test_*.py e check_globals PASS. Backup externo main-before-collection-medevac.lua.
- Sem publicação/restart/entrada injetada. Próximo lote precisa provar conservação
  e entrega em combate no Unreal; NÃO resolve/prova toda reposição ou cadeia fresca.
  ROADMAP/README/BATCH atualizados; sem tecla nova. Conhecimento UM registrado local.

## 2026-10-11 — Batch integrado único; granadas funcionam, MVP logístico falhou

- Preparadas offline 13 cenas e regressão fresca, sintaxe/máquina mock PASS;
  nove test_*.py/globals PASS. Uma publicação pelo restart.sh e uma única run
  CallumsCapeHex/PID19324, sem teclado/mouse/RPC/inventário/HPwrite/ApplyDamage de teste.
  SHA256 fonte/lab iguais ACB6ADFD3AE05828AB50C3D26CC3970673B09184E8FCD4BBCB3D010042CEFA64.
- Granadas integradas: Owner/Instigator e fuse4 PASS. WcollisionOn900→788,
  WcollisionOff900→900, CcollisionOn900→883; classes simultâneas900→771.
  Reset impediu dano; remover lançador não impediu explosão (não prova morte em
  combate). Contexto emprestado/trocado preservado; GC refletido em voo PASS.
  Todas as leases encerradas; sem crash observado durante lote, não estabilidade geral.
- Soldados hostil E aliado100→1: friendlyfire nativo observado; morte não ocorreu.
  Não desligar proteção/debug nem afirmar causa do piso1HP sem rastrear.
- Gate truck_loss FAIL: 16 granadas Colonial deixaram900→850; LOST_DELTA0,
  sem morte/TTL/carga perdida comprovados. Fixtures explícitas, não equilíbrio.
  Verificador check_native_batch_trace.py retorna1 corretamente por esse gate.
- MVP fresco sem save/créditos/velocidade extra: 352,96s,35amostras, derrota onda3,
  22abates/34perdas, reabastecimento18; inimigo4entregas/15camisas consumidas.
  Coleta entregou0/perdeu110,0199, bmat permaneceu40, recurso não reconstruído.
  Auditorias C/E PASS em todas as amostras. Log:35,8+34,3 perdidas por "ordem do
  jogador",39,9 por morte; reposição esgotou camisas. Causa completa não isolada.
  check_mvp_batch_trace.py retorna1 para coleta/refino/reconstrução, não exige
  derrota nem dá PASS ao MVP só porque houve combate. Falhas vão ao próximo lote.
- Rastros próprios em dados/rastro_batch_{nativo,mvp}_integrado.txt. Scripts e
  log completo externos D:/tools/foxhole-lab/t_batch_*.lua/native-batch-ue4ss.log.
  Relatórios/fixtures limpos entre cenários. Check final: squad0/enemies0/logi false/
  context false/settings false/sem relatório pendente. PID19324 encerrado;
  após3s WMI/processos confirmam nenhum processo do laboratório, Steam16104 mantido.
  map.txt temporário removido (baseline ausente). Não houve segundo restart.
- ROADMAP atualizado com prioridade real: coleta fresca, colisão/estradas e executor
  nativo de tiro/perda. Build publicada experimental, não estável. README/BATCH e
  universal-modder atualizados com evidência/limites; sem PR.

## 2026-10-11 — Granadas por facção e contrato do lançador; batch parcial preparado

- Progresso anterior confirmado na fonte: HP logístico real e remoção do DPS de
  veículos. Continuada integração, sem reduzir o objetivo a testes verdes.
- Conferidos offline getter Instigator1422d9d90 e Controller1422d9da0 no binário;
  PostInitialize WarProjectile140dbe460 ignora Instigator e deriva MyController;
  BeginPlay140da4a70 ignora Owner/peças. Contrato próprio (sem fonte protegida)
  em dados/contrato_granada_nativa.md. Nenhum offset executado.
- Corrigido uso de granada Warden para todo mundo: lançador Colonial usa Grenade_C,
  identidade GrenadeC e seus próprios limites (max1200 vs1100 Warden), cache por
  identidade. Equipe desconhecida/row ausente recusam sem gastar lease/cooldown.
  Owner real é passado ao deferred e Instigator escrito antes FinishSpawning;
  não escrever MyController fraco. Friendlyfire/atribuição vivos ainda pendentes.
- Granada24cenários PASS; contexto inclui duas classes simultâneas/explosão parcial/
  cleanup sem destruir granada estrangeira. Todos os nove test_*.py + globals PASS.
- Canal expõe throwGrenadeFrom (mesma função real) para oráculo com ator exclusivo,
  sem inserir caminhão na lista de personagens. Comandos externos t_batch_native_start.lua
  e t_batch_native_report.lua syntaxPASS (sem BOM), NÃO executados. Quatro casos
  WcollisionOn/Off, CcollisionOn, resetFlight numa sequência ~80s, espera nativa12s,
  lançador trabalhador/controller real e cleanup entre casos; sem HPwrite/ApplyDamage.
- BATCH_NATIVO/README atualizados. Sequência é PARCIAL: não cobre ainda morte do
  lançador/soldado/friendlyfire/GC/borrowed-context vivo ou regressão MVP no hex.
  Não publicar/abrir laboratório antes de preparar esses cenários; sem outra run
  por descoberta. Frota continua sem colisão até comparação A/B integrada.
- Universal-modder consultado no início; Gotcha acrescentada e kb check local PASS.
  Laboratório não iniciado, Steam preservado, sem entrada de teclado/mouse ou PR.

## 2026-10-11 — HP nativo na logística; lote ainda offline

- Retomada: relidos Como retomar/topo/ROADMAP, skills reverse-engineering e
  mod-any-game/playbook Unreal; `um kb search foxhole` consultado. Sem entrada
  injetada, publicação/restart ou laboratório aberto (Steam preservado).
- Removido `logi.hit`, DPS abstrato de emboscada e multiplicador de morteiro em
  caminhões. Não encaminhado dano inventado a ApplyDamage. Fuzis próximos agora
  não cortam comboios: executor nativo continua pendente, regressão funcional
  deliberada para não manter o sistema rejeitado pelo usuário.
- `logi.syncHealth` observa Health real antes de drive/truckStep/convoyTick e save.
  HP parcial atualiza espelho/painel. HP0/perda de ator cancela rota/movimento e
  debita carga uma vez, agenda reconstrução própria e retira referência ao casco.
  Não chama OnRep, FX, ocultação ou destruição no observador: TTL do jogo preservado.
  Ator desaparecido não concede bounty; HP inválido suspende sem inventar morte.
- Save antigo tinha HP abstrato: não escreve esse valor no ator; estado/carga
  continuam restaurados, ferimentos nativos ainda NÃO persistem. Morto mostra HP0.
- Nove `tools/test_*.py` PASS + check_globals; novo test_native_truck_health executa
  helper real e cobre perda única/HP parcial-zero/schema/destruição/ausência/gates.
  test_orders atualizado: ator mock com Health, sem expectativa de DPS fictício.
  Logs externos em D:/tools/foxhole-lab/offline-test_*.log. Backup fonte antes desta
  alteração: D:/tools/foxhole-lab/main-before-native-health.lua.
- `BATCH_NATIVO.md` atualizado: colisão dos caminhões está DESLIGADA pelo transporte;
  não presumir overlap explosivo funcional. Instigator antes FinishSpawning já
  consta no candidato de granada, mas equipe/atribuição/colisão exigem gate vivo.
  Não considerar lote pronto/publicado/estável; próxima etapa resolve esse contrato
  e prepara comandos sequenciais antes da única publicação/run integrada.
- README/ROADMAP atualizados; sem tecla nova. Gotcha local acrescentada no
  universal-modder e `um kb check` executado; sem PR.

## 2026-10-11 — Integração offline de granada/contexto; sem publicação

- main.lua agora substitui granada mesh/arco/shell próprios por deferred BPGrenadeW,
  fuse4 dos dados reais antes BeginPlay, solver CustomArc/MovementComp e dano/FX nativos.
  Fire só abandona o tiro normal se throwGrenade tiver sucesso; falha não gasta recarga.
- Helpers rts.native* ancoram settings imediatamente em GI.ServerSettings, controlam
  reservas e rastreiam classe/fullname (sem cache de projétil morto). Tick mantém lease
  até última granada; reset destrói apenas próprias e restore respeita troca externa.
- Corrigida falha do candidato: GrenadeRangeLimit0 REAL não significa alcance zero.
  Valida velocidades/fuse positivos; range0 não acrescenta teto ao limite do mod.
- tools/test_native_context.py PASS e tools/test_native_grenade.py20cenários PASS
  na fonte ATUAL; test_orders/globals PASS. Nenhum teste vivo/publicação neste lote.
  Backup externo main-before-native-grenades.lua; alterações ainda sem gate integrado.
- BATCH_NATIVO.md reúne critérios/cenários numa única sessão futura. Antes dela faltam
  Instigator/Owner/colisão do lançador e reação logística ao HP real. Sub-agente estuda
  esse contrato offline; não confundir oráculos anteriores com teste desse main.
- README atualizado; métrica antiga de dano da granada não imprime zero enganoso.
  Fuzil/morteiro/DPS de comboio continuam dívida a remover, não combate nativo entregue.

## 2026-10-11 — Usuário cobrou novamente testes em batch

- Fluxo recente fragmentou excessivamente os testes; usuário pediu avançar pesquisa/
  desenvolvimento offline e só depois executar todos os cenários numa única run.
  Regra reforçada em AGENTS.md: sem restart por sonda/helper/descoberta, cenários e
  critérios preparados antes, uma publicação e sessão compartilhada, cleanup entre
  cenários. Ideias novas vão ao próximo lote; exceções somente por impedimento concreto.
- Cenário já em andamento concluiu restore/cleanup; laboratório encerrado. Sem
  novos testes ao vivo agora. Trajetória nativa registrada em dados/rastro_trajetoria_granada_nativa.txt;
  integração e seus cenários deverão ser desenvolvidos offline antes do próximo lote.

## 2026-10-11 — Granada nativa explodiu e causou dano pelo próprio timer

- Laboratório PID18148 HomeRegionW, caminhão exclusivo900HP/Team0/Authoritytrue.
  SpawnActor BPGrenadeW a180cm do centro, FuseTimer default20, bExplodedfalse.
  Settings fresca mantida por GI.ServerSettings durante espera; sem ownerpatch.
- Após27s: caminhãoHealth780, granada não presente entre atores vivos; restore
  original nulo/cleanup PASS. dados/rastro_granada_nativa_inicio.txt e fim.txt.
  NENHUMA ApplyDamage/manual, HPwrite, HitInfoLua, RPC, fórmula ou debugtoggle.
  Timer do próprio projétil construiu impacto e executou dano/FX nativos.
- Isso prova explosivo local independente de inventário, não lançamento pelo
  soldado, trajeto/alcance, fusível real de arremesso ou atribuição ao atirador.
  Próximo: contrato local de MovementComp e tempo real de fuse para integração
  throwGrenade, sem substituir disparo de fuzil por outra coisa. main.lua inalterado.
- Laboratório encerrado pelo PID/caminho confirmado, Steam preservado.

## 2026-10-11 — Projéteis explosivos nativos: schema e CDOs confirmados

- tools/probe_native_projectiles.lua syntaxPASS e leitura viva PID22020 HomeRegionW.
  dados/esquema_projectiles_nativos.txt. Sem spawn/detonar/RPC/escrita de CDO.
- WarProjectile.Detonate e ApplyExplosiveDamageAndSpawnFx recebem HitResult
  StructProperty (estático ProjectileHitInfo_NetQuantize, NÃO montar tabela Lua).
  MyController WeakObjectProperty, ExplosiveCodeName NameProperty; templates reais.
- Grenade/BPGrenadeW/BPHELaunchedGrenade derivam TimedProjectile, FuseTimer20,
  ProjectileLife0/AutoDetonateTime0. Identidades GrenadeC/GrenadeW/HELaunchedGrenade.
  BPHEGrenade deriva diretamente WarProjectile, sem fuse, identidade HEGrenade.
  CDO e template não provam initialization ou explosão: timer/owner ainda rastreados.
- Sub-agente de explosivos investiga initializer local para não inventar HitInfo,
  fuse/velocidade/fórmula. main.lua inalterado; laboratório fechado PID/caminho
  conferido ao retornar offline, Steam preservado.

## 2026-10-11 — Lifecycle nativo explica casco ainda válido após HP zero

- Sub-agente rastreou a aplicação: Health0 despacha virtual+d60 para morte
  SimVehicle, com efeitos/ocupantes, depois programa SetLifeSpan15s nativo.
  Actor válido logo após o dano é esperado durante o TTL do casco, NÃO indicação
  de que falta chamar OnRep_Health ou outro callback manualmente.
- Explosão/drop observados pelo usuário são coerentes com essa cadeia. Não
  repetir só para forçar bActorIsBeingDestroyed imediato nem usar cleanup como
  prova. TTL15s identificado estaticamente, duração ainda sem amostragem viva.
- Rifle permanece sem executor autoritativo local demonstrado; ponte Lua expõe
  somente wrapper de invocação e callbacks de replicação. Estudo continua sem RPC.
  Novo sub-agente rastreia explosivos/projéteis locais nativos, sem inventário,
  para aproveitar mecanismo real em vez de encaminhar o DPS artificial ao engine.

## 2026-10-11 — Usuário confirmou explosão e drop do caminhão

- Após oracle nativo de HP900→0, usuário observou que o caminhão explodiu e
  deixou algo no chão. Evidência visual manual positiva da reação de destruição
  do jogo, além do Health0 registrado. Item/ator do drop ainda não identificado;
  não afirmar conteúdo, inventário ou persistência. Sem nova intervenção.

## 2026-10-11 — Três aplicações nativas, HP até zero sem crash

- tools/oracle_native_vehicle_damage.lua syntaxPASS e vivo PID12456 HomeRegionW,
  ator exclusivo900HP/Team0/Authoritytrue após12s. Settings fresca associada
  imediatamente e mantida por UProperty durante todas as chamadas.
- LightKinetic45 retornou27/HP900→873; HeavyKinetic55 retornou33/HP873→840;
  Explosive1500 (sobrecarga de TESTE, não munição/fórmula do mod) retornou1050/HP840→0.
  dados/rastro_dano_nativo_repetido.txt. Nenhuma escrita de HP, offset/RPC/debugtoggle.
- Health0 é comprovado, NÃO lifecycle completo de destruição/wreck: ator ainda
  não estava bActorIsBeingDestroyed no retorno, e cleanup removeu-o depois.
  Restore original nulo/cleanup PASS, sem crash nesse oracle. Não extrapolar rifle.
- Não converter DPS próprio em chamadas nativas e declarar integração concluída:
  faltam disparo/impacto/munição locais legítimos. Sub-agente retomou executor do rifle.
  main.lua inalterado. Laboratório encerrado pelo PID/caminho validado, Steam preservado.

## 2026-10-11 — Dano nativo de veículo comprovado com configuração fresca

- Constructor estático comprovou TMap privado inicialmente vazio/seguro. Novo
  laboratório PID20688 HomeRegionW, Steam20280; caminhão exclusivo900HP/Team0/
  Authoritytrue, espera12s sem settings guardada só em Lua.
- No mesmo chunk: baseline ApplyDamage45Explosive sem settings retornou0/HP900;
  constructor NOVO + associação imediata GI.ServerSettings + mesma chamada
  retornou31.5 e Health900→869. Não houve escrita de HP, fórmula própria, RPC,
  mudança de debug/proteção ou offsets. dados/rastro_dano_settings_fresh.txt.
- Restore original nulo PASS; ator exclusivo removido, cleanup true. Isto prova
  aplicação nativa GENÉRICA no veículo, NÃO disparo de fuzil, morte ou integração
  nas emboscadas do mod. Fonte main.lua continua inalterada.
- Resultado consistente com hipótese de GC do settings antigo; não prova sozinho
  o mecanismo exato daquele crash. Na integração, ancorar settings por referência
  nativa durante toda a vida útil, não cache Lua solto entre chamadas/quadro.
- Laboratório encerrado pelo PID20688/caminho confirmado após teste; Steam preservado.

## 2026-10-11 — Hipótese de lifetime no crash do oracle; sem desligar debug

- Investigação offline do stack chegou ao ramo nativo de debug de dano, que consulta
  um TMap em ServerSettings. Minidump mostra índice absurdamente alto, compatível com
  objeto/container inválido; NÃO é prova da causa exata. Constructor tem debug ligado.
- Hipótese: settings ficaram somente em Lua _G durante a espera de12s. Referência Lua
  não ancora UObject no GC; Outer sozinho também não certifica lifetime. Não desligar
  debug nem mudar fórmula para mascarar possível referência inválida.
- Scripts externos do oracle preparados para criar settings NOVOS no mesmo chunk
  que os associa imediatamente à UProperty GI.ServerSettings e chama ApplyDamage,
  sem guardar settings durante espera. Checkpoints log antes/depois das chamadas
  evitam perder toda evidência quando cmd.out só é escrito ao final. Sintaxe PASS;
  NÃO executados. Ainda confirmar inicialização do TMap antes de novo laboratório.
- Nenhuma nova feature/source main alterada; Steam aberto e laboratório fechado.

## 2026-10-11 — Visibilidade por distância permanece na fila

- Usuário relata que ainda há coisas sumindo pela distância e pede registro na fila.
  ROADMAP reforçado: reprodução por afastamento/zoom, separar culling/LOD de LOS/oclusão,
  identificar atores vivos/carregados e validar visibilidade no alcance do RTS.
  Sem diagnóstico novo ou correção entregue; não desviar agora da integração nativa do MVP.

## 2026-10-11 — Defaults nativos confirmados no engine; oracle de dano caiu

- Steam aberto pelo usuário, PID20280. restart.sh iniciou laboratório PID24924,
  HomeRegionW; apenas canal, sem entrada de teclado/mouse por agente.
- tools/probe_native_settings.lua PASS vivo: instância própria ServerSettings,
  todos os cinco defaults corretos e binding aninhado WarTweakables funcional.
  GI.ServerSettings permaneceu nulo. dados/rastro_settings_defaults_vivo.txt.
- Oracle separado: caminhão exclusivo900HP, Team0, Authoritytrue. Após12s,
  script comparava ApplyDamage45Explosive antes/depois de associação temporária
  dos settings, com restauração/limpeza ao fim. O processo caiu nativamente;
  pcall não protege contra isso e o buffer out não foi publicado. NÃO sabemos
  qual das duas chamadas caiu; não afirmar dano ou restauração comprovados.
- Crash UE4CC-Windows-608B38A24B507F2999BD40955C73B6EF_0000, access violation;
  stack inclui RVAs b5d5bc,b64277,d613df,d82713,d96e1c (TakeDamage),2550198.
  dados/rastro_settings_dano_crash.txt. Não repetir sem isolar callback/contexto.
  Sub-agente de dano investigando offline; decomp permanece externo.
- Laboratório ausente após crash, confirmado; Steam preservado. main.lua sem
  alteração. Configuração própria não foi persistida; não integrar combate ainda.

## 2026-10-11 — Configuração nativa local autorizada; primeiro gate preparado

- Usuário autorizou reutilizar configuração local do cliente, totalmente offline.
  Isso atualiza o limite anterior de somente observar ServerSettings; NÃO autoriza
  RPC, rede, servidor externo, inventário, bypass de proteção ou fórmulas próprias.
- Sub-agente rastreou ServerSettings como SaveGame passivo: constructor nativo
  preenche SpawnInvulnerabilityTime3 e GlobalRefineYieldModifier1; WarTweakables
  inicializa MinTankArmourMultiplier1, BallisticPenetrationMaxDistance4000 e
  BallisticPenetrationDistanceExponent1.5. Não há rede no corpo do constructor.
  Evidência estática, ainda sem confirmação em instância viva.
- tools/probe_native_settings.lua preparado: instancia própria por constructor,
  compara defaults e não associa ao GameInstance, altera CDO ou aplica dano.
  Sintaxe Lua PASS; check_mvp_trace PASS apenas para a evidência histórica.
- Continuação offline: tools/test_native_settings_probe.py executa a sonda real
  com mocks, cobrindo contexto original nulo/válido e recusas de ancestral,
  constructor inválido e default divergente. PASS; teste NÃO prova binding UE4SS
  nem dano vivo. Sonda agora também confere identidade do contexto preservado.
  test_orders.py PASS. Relatório próprio dados/rastro_contexto_local_settings.md
  registra constructor/passividade/defaults/perfis; struct aninhada ainda sem gate vivo.
- restart.sh fez check de sintaxe/locais e recusou iniciar: Steam não está aberto.
  Não abriu Steam nem realizou login. Nenhum laboratório iniciado nesta tentativa.
  Próximo: usuário abrir/logar Steam; executar primeiro gate e só então planejar
  oracle temporário de associação/dano com restauração do contexto original.
- main.lua sem nova alteração; nenhum combate nativo integrado ou dano comprovado.
  Fuzil ainda em investigação: entrada local encontrada também chama possível
  wrapper RPC, portanto NÃO executar essa entrada como atalho offline.
  Consumer posterior com dano foi rastreado, mas sem vínculo demonstrado com
  HitScan; não atribuir ao fuzil. Job headless24045 terminou exit0, artefatos externos.

## 2026-10-10 — Causa concreta de recusa do dano no laboratório

- Dois sub-agentes avançaram estático, sem canal/inventário/RPC. Proteção808 é temporária
  por timer e CDO48 é bBypassesSpawnInvulnerability comprovado; não alterar offsets nem flags.
  Conversão genérica NÃO zera dano por ID0: hipótese descartada. Interface real exige também
  WarGameInstance.ServerSettings não nulo, guarda distinta de Role/SimGameMode.
- Sonda SOMENTE leitura tools/preflight_native_damage.lua: PID22084 HomeRegionW,
  BPWarGameInstance vivo, ServerSettings nulo. Guard estático retorna0 nessa condição;
  explica recusa observada nesse laboratório, não impossibilidade geral de dano nativo.
  dados/rastro_contexto_dano_nativo.txt. Nenhum objeto de servidor/settings criado ou alterado.
- tools/export_damage_types.lua executado no engine: CDOs Types1/2/7/3/8/18 para
  light/heavy/explosive/AT/HE/fire; bypassSpawnfalse emtodos. AT Armourtrue/Penetratefalse,
  demais Armourfalse/Penetratetrue. Rastro dados/rastro_export_tipos_dano.txt; syntaxPASS.
- Correção importante no relatório disparo: ramo autoritativo localizado é HMG, NÃO fuzil.
  AuthorityRole3 -> hit válido -> DamageableActor interface com DamageAttributes -> dano;
  fallback nativo usa PointDamage/TakeDamage. ABI/instância equipada/rifle ainda pendentes.
  Ghidra headless readOnly/noanalysis terminou, decomp permanece externa. Não usar offsets.
- Fonte main.lua2F1C74D6 continua inalterada, nenhuma integração de combate nativo entregue.
  Laboratórios13208(CDO)/22084(preflight+export) encerrados apenas pelos PIDs verificados;
  ausência conferida, Steam preservado. Ler relatórios antes de repetir ApplyDamage.
- Próximo: esclarecer contexto local legítimo do cliente necessário ao dano; não construir
  servidor/RPC nem reiniciar HP artificialmente para fazer teste passar. Guard nulo é diagnóstico,
  não autorização de bypass, e não impede continuar outros estudos offline do combate.

## 2026-10-10 — Retorno ao fluxo nativo de combate, com dois sub-agentes

- Usuário corrigiu rumo: não reinventar disparos/dano já presentes. MVP grosso não autoriza
  DPS próprio no lugar do engine. Prioridade corrigida no ROADMAP; main.lua NÃO mudou neste lote.
  Usuário autorizou sub-agentes; dois investigaram offline disparo e dano, canal exclusivo do raiz.
- Disparo: HitScanWeaponComponent real, entrada local/consumo nativo/trace/HitNotify/efeitos
  identificados em decomp existente. PlayerFire é ParticleSystemComponent, NÃO arma.
  Refletidas ServerStartInvoke/OnRep_SimulatedHitNotify, mas RPC não foi invocada e callback de
  efeito não prova dano. ABI/contexto owner/equip ainda pendentes; offsets não executados.
  Relatório dados/rastro_disparo_investigacao.md, decomp protegido permanece externo.
- FindAllOf(Class/ScriptStruct) deu0; enumeração inadequada, não ausência. StaticFindObject
  por nomes comprovados achou classes e structs WeaponInvoke/HitNotify; schemas em dados/.
  FindAllOf HitScanWeaponComponent/ProjectileItemComponent/HMG deu0 instâncias no HomeRegionW.
  Não mexer em inventário/RPC para fabricar uma prova.
- Dano: fluxo estático ApplyDamage -> TakeDamage real de SimVehicle -> interface embutida,
  não UObject componente. Guards autoridade/mundo/SimDamageType e proteção adicional encontrados;
  relatório dados/rastro_dano_veiculo_investigacao.md. Receive*Damage são callbacks, não aplicação.
- PID19220 HomeRegionW: truck exclusivo900HP/bCanBeDamagedtrue. ApplyDamage45 com tipos reais
  lightkin/heavykin/explosive retornou0 e manteve900; Radial75 retornoutrue, HP900. Cada ator removido.
  setTeam foi chamado incorretamente com ator, helper espera membro; Team255 permaneceu, não contraste.
- Nova sonda corrigida TeamId direto0, HasAuthoritytrue/Role3/AuthorityGameModeSimGameMode válido.
  Após12.197s reais, ApplyDamage45/BPExplosive ainda0/HP900. Ator exclusivo destruído; callback
  seguinte marcou why ator destruído, mas linha de dano registrada. Não prova impossibilidade nativa:
  localizar guard/CDO/contexto é próximo passo. Nenhum HP escrito/offset/RPC nem entrada injetada.
- Regras Steam/firewall preservadas; apenas PID19220 encerrado após sondas. UM atualizado,
  kb check60PASS. Próximo: resolver contrato nativo em vez de calibrar interdição por DPS inventado.

## 2026-10-10 — Emboscada exclui desarmados; corte ainda não provado

- Auditoria achou dano por proximidade contando trabalhadores dmg0, tanto no ramo
  de comboio inimigo quanto no dano ao nosso caminhão. Ambos agora exigem weapon.dmg>0.
  Mantido DPS abstrato do MVP; não implementa disparo/munição/LOS individual contra veículo.
- tools/test_orders.py ganhou contraste trabalhador/armado nos dois lados: PASS;
  fonte anterior falha na asserção do worker danificando comboio. check_globals PASS.
- Publicada2F1C74D6BB205FA5610957A9B126720731CFA34DF4775329B2DDA7A82101F956 pelo restart.
  PID12944 CallumsCape: implantação nova pelo orçamento do cenário, newGame sem save antigo.
  Robô tentou perseguir comboios com combatentes, sem teleporte/crédito/dano artificial:
 148.8s,2entregas inimigas; segundo caminhão900->797.60HP, nenhuma carga perdida, audittrue.
  Perseguir caminhão rápido NÃO produziu corte; partida terminou em derrota em seguida.
- Tentativa posterior de contraste no engine recusada por falta de trabalhador vivo;
  não rodou nem substituiu listas/estoques. Portanto teste específico de worker é offline,
  publicação/compilação e marcha/dano em comboio real passaram, mas isolamento vivo não.
  dados/rastro_mvp_emboscada.txt. Não declarar interdição aprovada por esse ensaio.
- Robô terminou; apenas PID12944 encerrado, ausência conferida, map temporário removido.
  Próximo teste precisa posicionar emboscada ANTES da passagem, não perseguir caminhão.

## 2026-10-10 — MVP: ciclo logístico em combate no hex

- Sem mudar main.lua597BAF94, publicado/reiniciado CallumsCape PID19620. Save anterior usado
  apenas para recuperar infraestrutura; newGame reiniciou estoques/cadeias/ondas. Sem créditos,
  teleporte, alteração de tempo ou entrada na janela. Base começa30camisas/10fuzis, bmat40.
- Robô limitado36passos/10s reais: recruta usando estoque, marcha de combatentes ao pontoA;
  NÃO reatribui trabalhadores nem sobrepõe ordens em andamento. Sem morteiro/buff/dano artificial.
  Rastro dados/rastro_mvp_ciclo.txt; scripts externos t_mvp0/t_mvp_step/t_mvp_final.
- 403.50s: derrota na onda4,26abates/23perdas; leitura final27abates (simulação segue brevemente
  após resultado). Três trabalhadores sobreviventes não impediram derrota, como contrato v4.1.
  Coleta120 entregue/perda0; bmat40->84.69 antes de reconstrução; caminhão de recurso voltou.
  Estoque de base camisas16->20 após consumo/entrega, fábrica final3caixas de munição.
  Reabastecimento8.99,5ocorrências sem munição. Caminhão de recurso final57.45HP sob combate.
- Inimigo4entregas/13camisas consumidas; ondas pediram6/7/8/9, guarnição grátis5 + pagos1/2/3/4.
  Todas36amostras e final eAudit/colAudittrue. Sem crash nesta rodada. Nenhum comboio cortado;
  NÃO prova interdicação, vitória, equilíbrio prolongado, estradas ou estabilidade geral.
- Novo tools/check_mvp_trace.py verifica evidência registrada e explicita limites; PASS.
  Fonte da mecânica inalterada: este lote comprova integração em combate, não feature nova.
- Encerrado somente PID19620 após robô terminar; ausência conferida, map temporário removido.
  Próximo grosso: experimentar corte de abastecimento com combate e expansão/base avançada;
  chegada refinada continua adiada. MVP completo ainda não declarado.

## 2026-10-10 — Cápsula real, coleta no hex e direção MVP

- CollisionCylinder do soldado mede raio50/altura90. PATH_BODY corrigido32->50 e cápsula
  do resgate34->50; candidato livre com34 estava ocupado com50. Sem novo teleporte cego.
- Bitfield bStartPenetrating veio true em hits distantes Time0.776/Distance19400.
  rts.hitStartsInside usa escalares com resultado true/false/nil; desconhecido não autoriza resgate.
  BreakHitResult com tabela Lua devolveu escalares corrompidos: não usar como oráculo.
- Save antigo: trabalhador1HP em medevac continua preso no muro. Sweep Time0/Distance0.045
  não prova origem penetrada; cápsula da origem livre. Perfil fino falhou3nós. Caso NÃO resolvido.
- Fonte597BAF948F82EFA079A3DFA79340D2F878E75AAE84F42F494712AE2A3E73E1CC:
  bateria29/29 PASS/21mutantes. CallumsCape PID19492, nova partida na base correta:
  coleta120/entrega120/perda0, audittrue; reconstrução criou ator real900HP não destruindo.
  dados/rastro_coleta_capsula50_final.txt. Isso prova crédito por raio, NÃO chegada à porta:
  usuário observou três trabalhadores pararem no trilho; sem ordem/velocidade0 após entrega.
- Caminhão sobe estruturas: drive em reta e place sem sweep; trace central da fábrica/refinaria
  bate nos telhados Z1389/1382, não terreno600. Box candidato450/210/230 em Zatual penetra piso;
  elevar250 limpa o teste, mas NÃO certifica envelope/suporte. Não integrar essa caixa como prova.
- Refinaria tem UseAreaBox centro8477/-45794/Z856, extents750/825/256, yaw-23.49;
  TransferLocation8684/-47155/Z630. Sondas de piso/cápsula encontraram pontos exteriores e na
  área nativa, mas sem comprovar rota/porta. Dados/rastro_area_uso_refinaria.txt.
- Usuário adiou refinamento dos trabalhadores: quer MVP grosso provando conceito. Tarefa
  de chegada/espera registrada no ROADMAP; próximo lote deve avançar cadeia jogável, não polir
  esse ponto. Caminhões sem colisão continuam limitação explícita, não cadeia física aprovada.

## 2026-10-10 — VSync e olho no foco; soldados presos continuam pendentes

- Usuário descreveu linha horizontal no meio da tela ao mover câmera; captura estática não mostra.
  Oracle cvar: r.VSync0/t.MaxFPS60. Teste temporário r.VSync1: usuário confirmou que sumiu.
  rts.syncVideo agora liga VSync no RTS e restaura valor anterior ao sair, sem gravar config.
  No engine:1/antigo0 -> gfx(false)0 -> gfx(true)1/antigo0.
- Caminhão vivo900HP, meshes bVisibletrue/bHiddenInGamefalse, ator bHiddentrue e fora de S.occluders,
  com olho a~100m: ocultação nativa, não ausência. Olho no foco fez bHiddenfalse e caminhão visível
  na captura visibility-B-controlled_small.png. Algumas capturas A/B tiveram câmera movida pelo usuário:
  não tratá-las como comparação pixel a pixel. Nenhuma entrada injetada.
- eyeTick agora segue foco/chão, não soldado mais próximo. Usa tempo REAL para acompanhar câmera pausada;
  recusa focoNaN/chão ausente. Base permanece independente. Teste no engine confirmou foco/olho na pausa.
- Encontrado efeito colateral antigo: spawnSquad vazio usava pawn do olho como origem. Corrigido para
  rts.base quando S.eye; referência de esquadrão existente/spawn explícito/modo nativo preservados.
  Final PID19956: base16104/-54440, olho3123/-51134, nova partida nasceu a372cm da base, não no olho.
- Fonte final F53D35A1FEDB9BC0931EB73AE0AC11A3ACB1F0461B6FC79E0225E1F954ADE2E8 publicada.
  Bateria29/29 PASS/21mutantes + tools/test_visibility.py PASS (funções reais, VSync/base/pausa).
  Rastro dados/rastro_visibilidade_rts.txt. Visibilidade em toda tela, neve/estruturas/ângulos NÃO aprovada.
- Usuário reforçou soldados presos. Rastro atual dados/rastro_presos_atual.txt: três trabalhadores no
  trecho13k/-50k; coleta inativa/logística suspensa por nossa sonda visual, um alvo de volta à base e
  um com velocidadeZ-400. Não atribuir imobilidade dessa sonda à autonomia nem descartar relato.
  Rodada intermediária ECF06A81:120 entregue/perda0/ator900HP, porém partida nasceu no foco da câmera;
  NÃO usar essa rodada para aprovar navegação geral. Agora prioridade: reproduzir presos com origem/base
  corretas, auditar marcha comum/medevac dos workers (perfil fino hoje apenas em colGo), depois estradas.
- Laboratório final PID19956 encerrado e ausência de processos da cópia conferida; map temporário
  removido, Steam/firewall preservados. Universal-modder atualizado; kb check60notas PASS, sem PR.


## 2026-10-10 — Envelope observado e tarefa de visibilidade RTS

- Usuário pediu incluir correção de coisas ficando invisíveis: registrada em ROADMAP.md como falha
  funcional prioritária junto ao transporte; investigar LOS/oclusão/ocultação, inclusive caminhões longe
  do grupo e zoom alto. Sem mudança de visibilidade ainda; não confundir ator carregado com imagem.
- Estradas: adaptador candidato agora exige prova por aresta dirigida/from/to/segment/session;
  antes prova de um segmento autorizava todas as arestas da spline. test_adapter/roads/snapshot PASS.
  Candidato separado; main.lua não alterado neste lote.
- PID15748 CallumsCape: metadata BoxTraceSingle/GetComponentBounds confirmada. Restore para sonda,
  logística congelada, caminhão orientado yaw0 e colisão habilitada só nele; sem entrada real.
  Bounds de componentes e scan1166raios/10por quadro: hits CharacterMesh0 ultrapassam caixa400/162/140
  (X até427.70, Z até-206.22). Flags StartPenetrating em todos os hits: NÃO validar hull por esses hits.
  Rastro dados/rastro_envelope_caminhao.txt; bounds completos externos road-bounds.txt.
  Envelope integral/superfície/água/sweep continuam pendentes; nenhuma aresta autorizada.


## 2026-10-10 — Reconstrução transacional publicada e validada no hex

- Retomada pelo estado mais recente: mocks físicos já presentes nos harnesses. Bateria completa
  com sensibilidade:29/29 PASS,21mutantes; fonte E048680B41891BC16F136E4316C98334797642B1504D38D682C777A58FC00DEC.
- Publicada pelo restart.sh. Primeira carga iniciou lobby por map.txt no caminho errado; corrigido
  no diretório do mod e reiniciado deliberadamente. CallumsCape PID11924 chegou ao RTS.
- Sonda spawnTruck criou caminhão real HP900/notBeingDestroyed na vaga da fábrica sem débito;
  truckStep reutilizou o mesmo ator, debitou100 e ativou idle. Crédito100 apenas nessa sonda isolada.
- Nova partida sem ondas/crédito/intervenção: coleta120/entrega120/perda0; estoque40 inicial refinou
  até100, comprou caminhão e avançou toField/loading/toRef com ator900HP. O ator físico da sonda foi
  reaproveitado na mesma carga: NÃO prova segundo spawn limpo. Rastro em dados/rastro_reconstrucao_transacional.txt.
  Transporte continua reto/sem colisão: não aprovar estrada, equilíbrio ou cadeia regional completa.
- Encerrado somente PID11924 com caminho verificado; removidos map temporários, Steam preservado.
  Próximo lote: acesso/rota física dos caminhões pela rede nativa, sem confundir estado abstrato com percurso.


## 2026-10-10 — Reconstrução sem caminhão fantasma: candidato transacional

- spawnTruck reutiliza parking da fábrica; exige classe/ator íntegro900HP e não destruindo.
  Retorna sucesso/razão. truckStep só debita100/ativa idle depois do sucesso; falha mantém morto,
  estoque e tenta em5s. Sem vaga segura também recusa. Caminhão existente íntegro pode ser reaproveitado.
- Backup externo main-before-resource-transaction.lua. test_orders/check_globals PASS; regressões
  reais de spawn nil, IsValid porém destruindo e íntegro: duas falhas preservam100/estado morto,
  sucesso único debita100/ativa ator visível.
- Bateria completa27/29 PASS: falharam test_coleta_sobre_v4 e test_bmat_caminhao na expectativa de
  reconstrução. Não publicado. Auditar mocks antigos (transporte abstrato vs ator íntegro) e corrigir
  a cobertura sem afrouxar o novo contrato; não apresentar esses dois FAIL como PASS.
- Próximo: atualizar oráculo físico dos harnesses e validar vaga/spawn na fábrica ao vivo numa única carga.
  Laboratório permaneceu fechado neste lote offline; Steam/firewall inalterados.

## 2026-10-10 — Coleta contornou rochas:120 entregue; caminhão fantasma identificado

- Fonte F39518364CDFEDD88C7008561F1AD2576B0C9B0BDE003A77670AF573CE472F35, bateria29/29 PASS.
  PID12460, restore/nova partida/sem ondas/intervenção. Três coletores entregaram120, perda0,
  rotas reais passaram por X11666/Y-53k a-50k, não pelo vão na rocha. Sem micro-resgates.
  dados/rastro_coleta_50cm.txt e dados/rastro_rotas_50cm.txt. Caminhada até refinaria aprovada neste cenário.
- NÃO aprovar cadeia completa: recursoTruck mudou para loading/toField/toRef mas pawnfalse.
  Fabrica debitou100 antes de spawnTruck silencioso; coletores saíram porque estado abstrato parecia vivo.
  Dados confirmam risco já anotado: economia do transporte seguinte é abstrata, não prova caminhão real.
- Diagnóstico spawnTruck explícito:pcall true/nil e nenhum pawn. Sonda no local fixo campo+400/+300:
  classe válida/chão1000, SpawnActor válido porém bActorIsBeingDestroyed=true/Health300.
  Nenhum veículo íntegro criado. dados/rastro_spawn_recurso.txt; não creditar este diagnóstico como reconstrução.
- Próximo: reutilizar parking/preflight da implantação, verificar ator íntegro antes de débito/estado vivo,
  falha mantém morto/estoque e alerta, testar spawn falho e sucesso físico. Depois caminhões pela estrada real.
- Laboratório encerrado PID12460 verificado; map temporário removido; Steam/firewall mantidos.

## 2026-10-10 — Cápsula livre não resgatou; amostragem fina candidata

- Resgate revisado: anéis80/160cm, desnível90cm, rejeita floor.bStartPenetrating;
  teleporte excepcional só após sweep penetrado e CapsuleTraceSingle34/90 livre no destino.
  Corrigido cache loc por quadro após setter: teste de sucesso revelou posição antiga escondendo resgate.
- Fonte A9A4A2EB3E82...:29/29 PASS incluindo21mutantes. Tests cobrem destino ocupado recusado,
  livre com origem penetrada aceito/replanejado, carry/legT preservados.
- PID9648 carregou variante pré-cache, SEM partida/teste; reinício deliberado pela alteração de fonte,
  não por timeout. PID2368 publicou final, restore/nova partida/sem ondas. Ensaio novamente entrega40,
  fábrica60, recursoTruck morto, ZERO resgates, dois presos com6tentativas. Não resolveu o caso.
  dados/rastro_resgate_capsula_final.txt; usuário confirmou insistência nas rochas e dois presos.
- Mudança seguinte ainda offline: kneeClear da coleta amostra chão a cada50cm, limita subida proporcional
  à distância e desvios da linha de interpolação a45cm. Antes amostrava300cm e tolerava290cm por amostra,
  inclusive nos atalhos simplificados. Perfil de combate/caminhões sem sample permanece igual.
- test_orders/check_globals PASS: rocha estreita entre amostras antigas é recusada; rampa suave aceita.
  Precisa bateria completa e validação física; NÃO declarar rota contornando muro aprovada.
- Laboratório encerrado PID2368 verificado; map temporário removido. Próximo: validar rota fina e acessos
  no chão, sem substituir cadeia concluída por mera recusa mais segura.

## 2026-10-10 — Micro-resgate ao vivo: sweep recusado por penetração

- Candidato AF6720F17189... publicado, PID13132, restore e nova partida sem ondas/intervenção.
  360 amostras: entrega40, perda80, fábrica60, recursoTruck morto/pawnfalse. Resgates zero;
  dois presos esgotaram seis tentativas. Movimento oscilante do terceiro não ativa detector imóvel.
  Auditoria fecha mas cadeia continua NÃO aprovada. dados/rastro_micro_resgate.txt.
- Oracle real: floor vizinho normal.863 com subida68.89cm; limite45 recusa. Muitos traços devolvem
  ponto igual ao início (delta135cm/normal1): começam penetrando rocha, NÃO piso seguro.
- Sonda de sweep ao destino de subida68.89: retorno false, bBlockingHit=true, bStartPenetrating=true,
  posição inalterada. Portanto aumentar só altura NÃO basta: cápsula já está penetrando geometria.
- CapsuleTraceSingle refletida funciona: raio32/halfHeight90 no destino detectou penetração.
  Scan8direções80cm rejeitou pisos iniciais penetrados; nenhum candidato seguro demonstrado.
  Arquivo dados/rastro_resgate_capsula.txt. Sem teleporte inseguro aplicado.
- Próximo: resgate curto com cápsula de destino livre e piso real, rejeitando bStartPenetrating;
  usuário aceita teleporte excepcional, mas não tratar saída ocupada como livre nem creditar carga.
  Laboratório encerrado PIDexato13132 após sondas; map temporário removido, Steam/firewall mantidos.

## 2026-10-10 — Micro-resgate autorizado, candidato offline

- Usuário autorizou transporte curto exclusivamente quando preso, devido a terreno irregular.
  Implementado logi.colRecover para trabalhadores: quatro segundos com deslocamento <=30cm,
  sem combate/planner ativo; oito direções de80cm, chão local com normalZ>=.71 e desnível<=45cm.
  K2_SetActorLocation usa sweep=true: não desliga colisão nem atravessa paredes deliberadamente.
  Seis tentativas por episódio, sem crédito de sucata e sem renovar legT; sucesso replaneja.
- tools/test_orders PASS: imobilidade/espera, sweep obrigatório/distância limitada, colisão bloqueada
  não vira sucesso, teto de tentativas, carga/prazo preservados e planner ativo cancela observação.
  Candidato ainda NÃO publicado/validado ao vivo. Não afirmar que esse resgate sai do buraco.
- Rastro anterior capturado em dados/rastro_rotas_rocha.txt: trajetórias aprovadas com waypoints
  sobre rochas Z1350–1377; trabalhadores acabaram Z790–894 no vão. Uma entrega40, cadeia incompleta.
  Instrumentação não altera ordens. Laboratório PID4328 encerrado após captura; Steam mantido.
- Próximo: bateria completa e lote único ao vivo, medir sweep/progresso real e recuperação sem crédito.

## 2026-10-10 — Chegada regional da coleta: offline PASS, percurso ainda reprovado

- Coleta busca uma célula acessível dentro da área de serviço, em vez de um ponto fixo junto à instalação.
  Reutiliza planStart/planStep/routeTo; chegada atualiza target e u.goal. Perfil exclusivo dos trabalhadores:
  célula300, margem3000, teto5000, passo290, altura1200; não muda ordens de combate.
- Fonte E5BADAF86D90F3E8343E2DCC937DADC047736878E87A623BD0E3E78A01E66CE5.
  Bateria final 29/29 PASS incluindo21 mutantes; worker-region-final-battery.txt. Teste novo cobre
  destino central bloqueado e chegada numa célula livre da região. Não prova física nativa.
- PID24092, carga limpa CallumsCape: restore carteira1000/0/1000/4 e partida sem ondas/créditos.
  Amostragem1Hz:120 colhido,40 entregue,80 perdido, fábrica60, caminhão recurso ainda morto.
  Dois retornos e uma nova ida continuaram presos. Cadeia NÃO aprovada.
- Usuário informou intervenção acidental e que uma ordem por clique contornou o muro na volta.
  Ensaio contaminado: não atribuir entrega40 a autonomia sem confirmar instante da intervenção.
  Evidência em dados/rastro_coleta_regional.txt. Próximo: comparar destino/parâmetros/replanejamento
  da ordem por clique com colGo (ambos usam routeTo), antes de outro solver ou aumentos cegos.
- Também auditar reconstrução do caminhão: spawnTruck pode deixar estado abstrato vivo após falha
  de spawn; exigir pawn real válido antes de declarar cadeia completa.
- Laboratório encerrado pelo PID verificado após coleta das amostras; map.txt temporário removido.
- Usuário pediu coleta novamente: laboratório reaberto PID4328, infraestrutura restaurada e nova partida
  sem ondas. Mantido aberto para essa validação ativa. Relatou dois presos no buraco entre muro e rocha.
  universal-modder: Gotcha atualizado, kb check PASS60 notas.

## 2026-10-10 — Coleta sem fallback cego; rastro real da navegação

- Usuário confirmou visualmente muro, disse existir fim à esquerda e desbloqueou unidades manualmente.
  Intervenção não conta como sucesso automático: leitura posterior ainda mostrou 120 colhido/0 entregue/120 perdido.
- Fonte 541B18D3...3649 adicionou planStart/planStep ao env para oráculos incrementais, sem novos locais.
  Rastro do colGo verdadeiro: três retornos falharam (1045/2500/1869 nós), todos receberam rota reta de fallback.
  Não foi apenas falta de nós: testes com faixa de altura maior/grade mais grossa/margem maior também recusaram.
- Propriedades refletidas do CharacterMovement: WalkableFloorAngle 44.765083, WalkableFloorZ .71,
  MaxStepHeight 45. Grade padrão 60/150 equivale a cerca de22°; não confundir essa regra com o limite nativo.
  Sonda de44° ampliou região alcançável, mas ainda esgotou8000 nós sem rota. NÃO integrada como solução.
- Muro atingido é um segmento modular; bounds colidindo 205.84/456/326.99 (origem13150,-50376,705.75).
  Traces de chão vizinhos acertam também pilha de carvão, outro muro e rochas; topo global não é sempre piso acessível.
  Rede de estrada mais próxima do campo fica117m distante; não autoriza ligação por proximidade.
- Alteração funcional: routeTo aceita noFallback; coleta passa true. Falha limpa target/path e marca pathBlocked.
  Replanejar o mesmo trecho não renova legT; o painel mostra quantos trabalhadores estão sem rota.
  Combate/ordens legadas não foram alterados neste lote. Parar diante da falha NÃO resolve o desvio solicitado.
- Fonte F0904D1512FCA01E6F5AE34745E5704514AD1AC9F5DAD3A1A97BF9019712BC13 publicada.
  tools/test_orders.py cobre código real: recusa sem reta, legado preservado, retry mantém prazo e troca de trecho renova.
- Bateria final sobre esse hash: 29/29 PASS, incluindo21 mutantes; saída collection-refusal-final-battery.txt.
- PID14544: após carga pronta, restaurada infraestrutura e nova partida; falha controlada com teto1 nó,
  sem carga/estoque creditados: done/failed/noFallback true, rota0, target false, blocked true, velocidade0,
  HUD '1 sem rota', auditoria coleta true. É teste de recusa, NÃO viagem natural concluída.
- Uma sonda enviada antes do fim do carregamento recusou partida e instalou callback sem logi.col;
  cancelada e corrigida com assert antes de instalar. Repetição só depois de RTS pronto passou; não reiniciar por timeout.
- Rastro numérico em dados/rastro_path_coleta.txt; scripts/logs completos em D:/tools/foxhole-lab/.
  Laboratório encerrado pelo PID exato, map.txt temporário removido, Steam/firewall mantidos.
- Próximo: achar e validar passagem contornando o fim do muro, com ponto de chegada acessível na refinaria,
  depois provar coleta→entrega→caminhão sem intervenção. Não trocar o objetivo por 'agora ficam parados'.

## 2026-10-10 — Lote v4.1 no hex: infraestrutura/save PASS; coleta bloqueada por muro real

- Fonte 236C34B9...F393, CallumsCapeHex, PID 25264: implantação 1000 bmat criou refinaria/fábrica/2 caminhões,
  carteira 0, gasto 1000, quatro registros. Repetição não alterou contagens nem cobrou de novo.
- Partida sem ondas, sem créditos/teleporte dos trabalhadores, sampler 1 Hz por 360 s: três coletores recolheram
  120 sucata. Retorno à refinaria ficou preso em IndustrialWall03Snow31; SphereTrace Camera confirmou
  o mesmo ator nos três caminhos. Após timeout, 120 entrou em perdido e zero foi entregue; razão fechou.
  Fábrica permaneceu com 40 bmat e caminhão de recurso não nasceu. COLETA NÃO APROVADA no hex.
- Prioridade funcional seguinte: rota dos trabalhadores contornando esse muro, depois caminhões pela estrada.
  routeTo usa A* compartilhado (2500 nós/margem 2000) e fallback direto; registrar falha do planner antes
  de alterar limites ou tentar rede real. Não desabilitar colisão, creditar entrega ou aumentar tempo para mascarar.
- Save isolado D:/tools/foxhole-lab/v41-hex-validation-save.txt preservou infraestrutura/carteira.
  PID 25988, carga limpa: sem ativos → continuar true (318 ms), refinaria/fábrica/2 caminhões restaurados,
  carteira 1000/0/1000/4, bmat da fábrica 40, sem degraded, auditoria inimiga fechada.
  Repetição 303 ms, sem duplicar/débito adicional. Carga em mãos de trabalhadores não persiste por desenho.
- Exportação fatiada de estradas desta região concluída: 405 CP, 431 segmentos, 391 assets de estrada,
  4013 nós com curvas, nenhuma incidência rejeitada; todas as arestas continuam NÃO validadas fisicamente.
  Snapshot e relatório em dados/paralel/estradas/callums-*.json; não reutilizar epoch/coords no lobby.
- build_snapshot.py agora aceita --input/--output/--report sem sobrescrever o snapshot do lobby.
  test_snapshot.py cobre as duas regiões; testes snapshot/roads/adapter PASS. Não é transporte integrado.
- Rastro das ações/360 amostras: dados/rastro_logistica_v41_hex.txt. Logs completos e export bruto externos
  em D:/tools/foxhole-lab/v41-hex-*.log e callums-roads-export-live.txt.
- Laboratório encerrado pelo PID exato; map.txt temporário removido, Steam/firewall mantidos.

## 2026-10-10 — Bases e save v2 validados no jogo; continuação na mesma carga corrigida

- Lote pelo canal, sem teclado/mouse injetado, HomeRegionW: PID 21456 criou base nativa com HP 1725.
  Posse e 400 bmat creditados explicitamente para isolar construção; não é teste de equilíbrio ou entrega física.
- Save isolado em D:/tools/foxhole-lab/v41-validation-save.txt: escrita 45 ms; PID 11400 restaurou após reinício
  em 226 ms, com base ativa, auditorias próprias/inimigas fechadas e sem estado degradado.
- Repetir continuação com base viva recusava: trace vertical acertava o telhado e exigia Landscape.
  parkingGround agora aceita ignore opcional; fwdPreflight ignora apenas base viva correspondente ao local salvo.
  Não ignora outros prédios, caches mortos ou atores em destruição. Backup: D:/tools/foxhole-lab/main-before-preflight-ignore.lua.
- Fonte 236C34B9F4223911B6087A36BCB514BCA29CB813ECD3F2FA2AADD43B0B5CF393:
  29/29 bateria offline PASS, 21 mutantes; tools/test_fwd_preflight_ground.py PASS adicional sobre funções reais.
- PID 27284: continuação fresca 223 ms, preflight com base viva PASS, continuação repetida 220 ms.
  Base vazia recusou recruta sem fallback; caixas creditadas deram 10 camisas/20 fuzis; recruta nasceu a 8 m,
  consumiu 1 de cada. Save e continuação preservaram 9/19, auditoria fechada; 259 ms, sem degraded.
- Duas sondas tiveram erros Lua corrigidos (nome fwd.bases em vez de fwd.list; flatDist não exportado no env).
  Não foram erros da feature; as ações interrompidas foram repetidas, sem declarar PASS da saída incompleta.
- Colisão nativa TruckW lida antes do motorista: VehicleCollision extents 400/162/140, Camera/Visibility 2/2,
  mas meshes também bloqueiam; caixa ainda não prova envelope integral. Ver dados/paralel/estradas/VALORES_CAMINHAO_20261010.md.
- Evidências externas v41-*-load*, v41-recruit-base.txt, v41-fixed-base-save-live.log em D:/tools/foxhole-lab/.
  Laboratório encerrado pelo PID exato. Falta validar implantação/carteira no hex, transporte e combate prolongado.
  Crashes/efeito amarelo continuam adiados conforme pedido do usuário; não afirmar estabilidade geral.

## 2026-10-10 — Desenvolvimento retomado: integração logística v4.1

- Por pedido explícito do usuário, crashes e amarelo residual ficam pendentes; não bloquear features pelo gate manual de 1/2.
- Integrados coleta manual, quatro suprimentos, cadeia inimiga, bases avançadas e save v2. Fila experimental de teclas preservada.
- Fonte SHA256: 2237884769733d6298db957f028f5f71fbf948634e4740aa81ddd68e7f08f83f.
  Backup anterior: D:/tools/foxhole-lab/main-before-logistics-53bdbcab.lua.
- Bateria: 29/29 PASS offline, incluindo sensibilidade com 21 mutantes. O primeiro ensaio falhou porque um harness esperava tecla síncrona; adaptado para drenar a fila como o quadro real, sem alterar a feature.
- Resultado completo: D:/tools/foxhole-lab/integrated-v41-battery.txt. Offline não prova física, equilíbrio, teclado real ou estabilidade nativa.
- Publicação e validação curta no laboratório iniciadas; resultados ao vivo serão registrados separadamente. Save anterior copiado para D:/tools/foxhole-lab/save-before-v41.
- Validação curta concluída em HomeRegionW, PID 3660: newGame iniciou, três trabalhadores nasceram,
  camisas 30→27, coleta ativa, reserva de caminhão 100, cadeia inimiga com razão fechado e primeira onda.
  Estado em D:/tools/foxhole-lab/v41-live-state.txt. Não validou viagem completa, base avançada ou retorno de save.
  Laboratório encerrado pelo PID exato; Steam mantido. universal-modder atualizado, kb check: 60 notas PASS.

## 2026-10-10 — Flicker: hipótese de stencil residual testada offline

- Fonte53BDBCAB…E543/laboratório fechado confirmados; fila ainda aguardando teste real.
  Nenhuma alteração adicional na fonte nem lançamento ocioso.
- outlineDepth(false) limpaCustomDepth mas retémstencil1. Se nativo reativaDepth,
  máscara permanece: hipótese para fill piscando relatado pelo usuário.
- test_stencil_clear.py extrai helper real e reproduz residual; troca em memória para
  stencil0ao desmarcar PASS, incluindo reseleção1/idempotência/guard. Não aplicada.
  STENCIL_PROPOSTA.md documenta candidato e gate visual/ordem de quadro.
- Não comprova shader/flicker nem resolve crash; não misturar no ensaio da fila.
  Universal-modder consultado/Gotcha52/check local, semPR.

## 2026-10-10 — Variante isolada: teclas enfileiradas no loop persistente

- Após nova reproduçãoRegistry com entrada rápida, aplicado SOMENTE experimento de ponte:
  CFG.KEYBIND_QUEUE=true; onGame enfileira funçãoLua, frameBody drena antes autoridade/menu.
  FIFO por snapshot, eventos reentrantes ficam próximo quadro, erro não impede seguintes.
  false preserva ponte original. Contorno/fill/foco/movimento não alterados.
- Backup externo main-before-keyqueue-33d6c7e5.lua. Fonte novaSHA53BDBCAB…E543;
  candidato logístico62245d23 não contém essa mudança: NÃO copiá-lo por cima sem transplantar
  e retestar a ponte após gate. Fonte realtest_queue_experiment/ordens/globals/lifetime PASS.
  Harness ordens simula fronteira de quadro após keybind; teste específico verifica adiamento.
- Publicado pelo restart.sh/PID5440/HomeRegionW.100açõesselectGroup1/2 em10rajadas enfileiradas
  pelo canal executaram no frame persistente; assert3selecionados/FIFO/fila vazia PASS.
  Isso NÃO simula teclado nem prova sincronização threadUE4SS/causa resolvida.
  Saída KEYQUEUE_20261010.txt; log externo keyqueue-live-20261010.log semRegistry/fatal observado.
- Laboratório5440fechado ao fim, Steam preservado. README/TESTE_MANUAL atualizados.
  Próximo usuário: uma tecla1, depois2, alternância parada; movimento/duplo toque separados.
  Não certificar correção antes desse teste. Flicker não tratado nesta variante.

## 2026-10-10 — Controle100grupos passou; entrada rápida caiu comRegistry

- PID23716, fonte atual:100chamadasselectGroup alternadas pelo canal concluídas,3selecionados
  por etapa. Saída externa group-channel-20261010.txt. Após controle usuário relatou troca
  rápida1/2 e fatal; processo terminal confirmado,crash401E1646…/338s/read0xffffffff.
- UE4SS.log contémRegistry Ref was not function às11:57:46,315/No traceback e logs de grupos
  até11:57:49,561. Log externo group-fast-fatal-20261010.log preservado. Não prova callback culpado,
  mas entrada rápida é reprodução candidata; taxa do canal e das teclas não é equivalente.
- Usuário também relatou preenchimento amarelo piscando em não selecionado; imagem fornecida
  mostra partes amarelas de unidade sem borda atrás de veículo. Imagem isolada não prova flicker;
  relato temporal do usuário registrado. Reativação nativa deCustomDepth já conhecida merece trace.
- Hipóteses do usuário: movimento durante troca; repetir2quando2jáselecionado. Repetir grupo
  em<=0,45s também chama focusOn (duplo toque), caminho distinto a isolar. Não atribuir culpa.
- Próximos ensaios separados: fila no loop persistente vsExecuteInGameThread; duplo toque vs
  alternância; máscara/stencil visual sem misturar correções. Sem novo teste manual agora.

## 2026-10-10 — Segunda reprodução manual: alternância1/2 caiu

- Carga limpa PID10128/HomeRegionW, mesma fonte. Usuário confirmou1selecionou3 e2também;
  ao alternar1/2 ocorreu fatal error. Últimos logsgrupo2 às11:50:13,057 egrupo1 às11:50:14,029.
  Antes houve ordens reais de movimento e roda; não chamar ensaio exclusivamente de teclas.
- Processo terminal confirmado; crashE729F1E8…/147s/read0x0b. Log preservado externamente
  manual-alternating-fatal-20261010.log; dump original emSaved/Crashes. Sem reinício automático.
- Alternância de grupos é agora candidato de reprodução;1ou2isolados funcionaram nesta carga,
  mas não certificam estabilidade. Próximo compararselectGroup pelo canal vs entrada real,
  separando movimento/câmera/contorno e ponteExecuteInGameThread; não atribuir causa ainda.
- Usuário não precisa continuar roteiro. Laboratório terminal, Steam preservado;
  sem entrada injetada pelo agente nem liberação do candidato logístico.

## 2026-10-10 — Gate manual REPROVADO: queda após selecionar grupo1

- Usuário relatou fatal error enquanto testava números e dificuldade para entender roteiro.
  Não exigir continuação; próximo roteiro será passo único, explicitando1=grupo1/2=grupo2/0=todos.
- PID20308 terminal confirmado, sem reinício. Crash95C51A… às11:42:40,317s desde partida do processo,
  EXCEPTION_ACCESS_VIOLATION/read0x75d42b59. Fonte33D6C7E5…E679 intacta.
  Último log11:42:39,524:selecionado grupo1(3); antes houve roda, seleção e ordens comA*.
  Sem mensagemRegistry no trecho novo. Proximidade temporal não prova tecla culpada.
- Stack iniciac62ea9/2c60bc/2c6d99/2c3a0d, depois ponteLua/frame repetido. MesmoPCallStackHash
  dos antigos NÃO prova mesma instrução. IdentidadeModuleList confirmouGUID/Age20/timestamp
  iguais aoPE local também no dump novo.2c6d99 está nopush_structproperty, ramo interno sem
  nome exato; não confundir com retorno2c6b92 de escrita visto noutra pilha.
- JSONs crash_manual_20261010.json/crash_manual_identities_20261010.json emestabilidade;
  UE4SS.log externo preservado manual-fatal-20261010.log; dump original preservado emSaved/Crashes.
  Gates automáticos anteriores não cobriam essa interação e não certificam a build.
- Laboratório já terminal, Steam preservado. Candidato logístico não liberado.
  Próximo: localizar instruçãoc62ea9/contexto e isolar caminho de grupo/callback numa variante
  única; só novo teste manual simples após investigação. Nenhuma entrada injetada.

## 2026-10-10 — Gate manual preparado por confirmação do usuário

- Usuário confirmou "Sim, pode preparar agora". Carga limpa pelo restart.sh, PID20308,
  HomeRegionW, fonte atual preservada. Canal confirmou6soldados selecionados/28cópias cada,
  ondas desligadas/inimigos limpos; sem entrada injetada. Log inicial externo manual-start-20261010.log.
- Laboratório mantido aberto exclusivamente para validação manual ativa solicitada.
  Resultado ainda pendente: usuário faz seleção/grupos/movimento/zoom/F10 por10min;
  ao terminar, preservar log e encerrar sóPIDLab. Não considerar preparo como teste aprovado.

## 2026-10-10 — Fonte UE4SS exata: ponte Registry e ramo de escrita de struct

- Laboratório fechado/Steam22164 confirmados; última sessão foi progresso (identidades/frames
  novos). Sem resposta ainda à confirmação de início manual; não abrir jogo ocioso.
- API públicaGitHub resolveu commit5418fa4ed9f1e8379d28ee7bbc3235c7e0c71b09. Três arquivos
  pequenos de fonte pública em D:/tools/ue4ss-source-5418fa4e; nenhum loader/binário substituído.
- get_function_ref verifica tipo no registry; process_lua_function é trampolim geral, não prova
  keybind. handle_error notifica callbacks e zera pilha antes da escolha de exceçãoC++/luaL_error:
  registrar traceback/contexto completo se erro voltar, sem atribuir corrupção por leitura estática.
- NoPE compatível,2c6b92 é retorno do ramo tabela antes de discard_value; corresponde à escrita
  tabelaLua->struct. Isso afunila uma pilha mas não identificaUProperty/UFunction/causa.
  Detalhes/links primários acrescentados em dados/paralel/estabilidade/SIMBOLOS_20261010.md.
- Nenhum patch especulativo nem expansão de feature; próxima ação útil é gate de interação real
  do usuário e/ou símbolos exatos/instrução com contexto. Universal-modder/check local, semPR.

## 2026-10-10 — RE offline: identidade dos dumps e primeiros frames nomeados

- Laboratório continua fechado, Steam22164 presente; aguardando confirmação do início manual,
  não o abrindo ocioso. Progresso anterior confirmado por arquivos/processos.
- ZIPUE4SS local semPDB. DLL3.0.1Beta#0/commit5418fa4e; extraído CodeViewRSDS comllvm-readobj.
  ModuleList dos três dumps antigos tem mesmo GUID21ad178d-4639-470e-971e-f115b4924854/Age20/
  timestamp6ac43103 do PE local: comparação de RVAs agora tem identidade verificada.
- Cruzados4353exports com intervalos RuntimeFunction:0x2c6b92/2c6d99 dentro de
  push_structproperty;0xb99c75 emLua::call_function;0xb9d34c emprocess_lua_function.
  Aceitos nomes só quando export começa exatamente no início do intervalo correspondente.
  Export anterior mais próximo NÃO identifica funções privadas (heurística descartada).
- Evidência/limites em dados/paralel/estabilidade/SIMBOLOS_20261010.md e JSONs ao lado.
  Nomes de frames não provam causa/propriedade/callback culpado; Registry continua não isolado.
  Scripts/dumps/binários externos; nenhum loader novo/download grande/fonte main alterada.
  PróximoRE: fonte do commit exato ouPDBGUID/Age compatível; não simbolizar com outra build.
- Universal-modder consultado; Gotcha50 local/check, semPR. Gate manual/feature continua pendente.

## 2026-10-10 — Contorno: 100 ciclos e 20 mortes/recriações passaram

- Carga limpa PID18872/HomeRegionW, mesma fonte33D6C7E5…E679, seis selecionados,
  ondas desligadas.240etapas pelo canal, sem callbacks novos/hotpatch/input:100ciclos
  des/reselecionar seguidos de20mortes porHealth0/remoção normal/recriação,329,256s.
- Verificado a cada etapa:0clones/fontes e CustomDepthfalse ao desmarcar;28cópias por vivo
  ao remarcar; cache de contorno/animAddr/entrada anim.units removidos antes de repor morto.
  Sem Registry/fatal no log consultado. Saída em dados/paralel/estabilidade/CYCLES_20261010.txt.
- Primeiro assert da SONDA errou ao exigir outlinePartsnil numa unidade viva desmarcada:
  setOutline chama outlineDepthfalse e repopula esse cache para impedir brilho nativo.
  Corrigida só a sonda, mantendo fonte/hash e processo; ciclo1 refeito. Não é bug do mod nem
  vazamento. Em morto retirado a exigência de cache nil permanece e passou nas20mortes.
- Antes deGC:207SkeletalMeshActor vivos/28destruindo; depois:207vivos/0destruindo,
  168rastreados. Não atribuir os39restantes a vazamento (incluem nativos). Pool6criados/
  20reutilizados/0livres. Perfil agregado com metade do tempo desmarcado NÃO é ganho de
  performance:6,72msmod/5,86stratTick; selecionados apósGC10,80msstratTick.
- Laboratório18872 fechado ao fim; Steam preservado; logs integrais externos cycles-20261010.log.
  Universal-modder Gotcha49 local/check; nenhum PR. Causa antiga/entrada real continuam pendentes.
  Usuário respondeu que pode fazer roteiro manual depois do ensaio; combinar início antes de abrir.

## 2026-10-10 — Contorno: janela limpa de dez minutos e transições repetidas

- Progresso anterior confirmado pelos arquivos/processos: fonte33D6C7E5…E679, Steam22164,
  laboratório fechado. Nova carga pelo restart.sh, PID20196/HomeRegionW; sem ondas/logística,
  entrada injetada, hotpatch ou callback extra. Universal-modder consultado antes/depois.
- Seis selecionados/168cópias mantidos em cinco checkpoints:134,483/255,032/377,482/498,375/
  620,113s. stratTick10,94/11,29/11,76/10,53/12,46ms. Janela10min completa sem queda ou
  Registry/fatal no log consultado. Fonte não alterada; custo continua gate independente.
- Depois: CollectGarbage nativo, des/reseleção, morte de um soldado, remoção/cache limpo,
  recriação PASS. Nova janela186,372s,6sel/168cópias; stratTick10,39/10,40/10,88ms.
- Saídas preservadas em dados/paralel/estabilidade/LONG_20261010.txt e LONG_TRANSITIONS_20261010.txt;
  logs integrais em D:/tools/foxhole-lab/crash-long-*.log. Nenhuma causa antiga isolada.
- TESTE_MANUAL atualizado com gate10min de seleção/grupos/zoom/teclas exclusivamente pelo usuário;
  pergunta enviada, sem presumir aprovação/execução. Próximos controles: repetição de100transições,
  20mortes/recriações e troca de equipamento, com quadros entre etapas; entrada real ainda pendente.
- Laboratório20196 fechado por PID/path verificado ao encerrar, Steam preservado. Fonte/hash intactos;
  candidato v4.1 não publicado. Sem declaração de estabilidade nem liberação de features.

## 2026-10-10 — Retomada: controles B2/A2 e transições; candidato v4.1 auditado

- Fonte33D6C7E5…E679 intacta. Steam aberto; universal-modder/skills/oráculos consultados.
  Testes ordens/custos/probe/lifetime PASS. Candidato v4.1 testado sem integrar: bateria27/27,
  repetida com sensibilidade28/28 (21mutantes), SHA62245d23…598f preservado.
- B1 anterior encontrado em saída externa:184,305s/6sel/168cópias; não é teste novo.
  B2 carga limpa PID21752:195,677s/6sel/168cópias, stratTick10,67–11,63ms.
  A2 carga limpa PID11084:201,218s/6não selecionados/0cópias, stratTick0,48–0,56ms.
  Sem Registry/fatal nos logs novos consultados; checkpoints aproximados, não benchmark pareado.
- Depois de A2, seleção/desseleção/reseleção, GC nativo, morte/remoção/cache limpo e recriação PASS.
  Nova janela219,164s/6sel/168cópias, stratTick11,07–11,34ms, sem queda/Registry observado.
  Controles negativos NÃO isolam causa nem corrigem falha antiga; desempenho permanece caro.
- Evidências: dados/paralel/estabilidade/RETOMADA_20261010.md e saídas ao lado;
  bateria em dados/paralel/pacote_v4/BATERIA_20261010.txt. Logs integrais externos preservados.
  Sem hotpatch/entrada injetada/novo callback/RPC; candidato logístico não publicado.
- Laboratório fechado por PID/path verificado ao fim, Steam22164 preservado. README atualizado;
  Gotcha48 local, um kb check PASS60notas, sem PR. Próximo: duração maior/isolamento se reproduzir,
  zoom/entrada pelo usuário; estabilidade ainda impede expansão.

## 2026-10-10 — Lote offline Claude: pilha v4.1 pronta para integrar (nada no jogo)

- Subagentes Claude (Opus/Sonnet) entregaram offline, em `dados/paralel/`, sem tocar `main.lua` (33d6c7e5…e679) nem laboratório:
  cadeia logística inimiga real com interdição (IA_LOGISTICA + calibração v2), save v2 seguro (PERSISTENCIA; seção inimiga
  inválida descarta só ela), reserva de bmat para reconstruir caminhão, início estilo aldeões (sem caminhão de recurso; 3
  trabalhadores sem arma coletam sucata; a fábrica faz o caminhão), bases avançadas (Shift+J, ForwardBase1, 300 bmat; recrutar
  gasta o estoque do ponto; mão de obra só no Assalto) e v4.1 (trabalhadores fora da onda e do centro do esquadrão).
- Decisões de design (delegadas pelo usuário): ROADMAP.md fase 3 "de onde vêm os soldados" e `dados/paralel/bases_avancadas/DECISOES.md`.
- Candidato: `dados/paralel/pacote_v4/v4_1/candidato/main.lua` (62245d23…598f). Integração, rascunhos de README/TESTE_MANUAL,
  roteiro único de laboratório (~5h40, gate de estabilidade primeiro) e gotchas em `dados/paralel/pacote_v4/`. Estado por task:
  `PARALEL_AGENTS`. Tudo PASS só offline; nenhuma afirmação ao vivo. Gate de estabilidade continua bloqueando a publicação.

## 2026-10-09 — Controle A1 sem seleção: 184s completos

- PID2184/HomeRegionW, fonteSHA25633D6C7E5920A3B5E00B7F3BAFBC7B8A86C984DB810217241A567AFE0901EE679.
  Seis soldados sem seleção, cópias temporariamente0no spawn e restauradas4no mesmo comando,
  nenhum clone persistente; animação/demais sistemas mantidos, ondas desligadas, semGC/hotpatch/inputagente.
- Checkpoints61,01/122,06/184,00s:6unidades/0sel/0clones todos. Mod1,31/1,25/1,24ms,
  stratTick0,50/0,48/0,46ms. Log consultado sem Registry/fatal/roda/seleção.
  Sobrevivência de um controle curto não certifica; plano4cargas A1/B1/B2/A2 em controle_crash.md.
- Após encerrar janela, sonda de metadata collisionTruckW executada separadamente; saída externa
  truck-collision-schema-live.txt. PróximoB1 carga limpa mesmafonte,6selecionados180s sem entrada.
## 2026-10-09 — Auditoria Registry e correção independente de retry de animação

- Comparados3CrashContext no artefato dados/paralel/estabilidade/crashes_comparados.json:
  cabeçalhos diferentes apesar de PCallStackHash igual. XML97D8antigo registra read0x08,
  DF9Aread0xffffffff, novo18BCEread0x63. Não concluir mesma instrução pelo hash.
- Wheel e seleção são polling do frame, não wrapper onGame: eventos não provam culpa de keybind.
  Nenhum PDB local encontrado; offsets não simbolizados. Auditoria callback_registry.md.
- Defeito Lua separado: anim.track marcava hooked=true mesmo RegisterHook falhando. Corrigido para
  true somente se registro sucede; permite retry e não duplica após sucesso. Teste proposta reproduziu
  falha/retry/semduplicação, ordens/globals fonte integrada PASS. Não atribuir crash a esse defeito.
- Fila de keybind no callback persistente preparada e testada offline somente como experimento separado;
  NÃO integrada/não prova sincronização nativa. Próximo teste deve alterar um fator por carga.
  Laboratório fechado, nenhuma validação ao vivo nova. Economia/estradas continuam separadas.
## 2026-10-09 — Queda nativa no segundo lote: estabilidade ainda reprovada

- PID4408 terminou durante janela60s com6sel/168cópias, após descarte331quadros stratTick11,67ms.
  Não existe resultado S1 válido: teste detectou processo terminal, não reiniciou por timeout.
- Crash UE4CC-Windows-18BCE18343C03805B228B794C306C125_0000: EXCEPTION_ACCESS_VIOLATION
  lendo0x63, PCallStack UE4SS com vários frames repetidos c6cfde/c6c1e0/c77cab etc.
- UE4SS.log: roda mouse18:20:01, Lua::Registry::get_function_ref Ref was not function18:20:03,
  selecionados6 às18:20:04/06. São observações, não causalidade; nenhuma entrada foi injetada pelo agente.
  Não culpar contorno/GC/component transform/input sem isolamento. Fonte segue experimental.
- Agente estabilidade audita Registry/callbacks/input/anim e compara callstacks antigos antes nova publicação.
  Laboratório já terminal; Steam22164preservado. Sem expansão de features nem relançamento automático agora.
## 2026-10-09 — Segundo lote de otimização integrado offline

- updateOutline agora lê K2_GetComponentToWorld1x/peça, sem3getters/MakeTransform; quaternion/escala
  copiados sem cache de pose, mantendo homotetia e4cópias/peça. Oráculo42fontes PASS na carga anterior.
- outlineDepth confere bRenderCustomDepth/CustomDepthStencilValue reais por quadro e escreve só divergências,
  sem cache que esconda reativação nativa. Campos confirmados no metadata PrimitiveComponent.
- Ordens/sintaxe/globals/custos/probe PASS; transform/lifetime reais PASS antes último patchdepth.
  Testdepth proposta PASS reativação/não selecionados/olho/retirada; teste real sendo atualizado pelo agente.
  Ganho temporal/visual do novo lote ainda não validado; fonte experimental, não prometer estabilidade.
- Candidato ECONOMIA test_integracao e adaptador ESTRADAS reproduzidos PASS. Carga em retorno físico
  preservada no caminhão/restore e creditada só chegada; driver seguro/integração final seguem pendentes.
  Reservas Claude IA_LOGISTICA/PERSISTENCIA preservadas, sem Codex assumir blocos.
## 2026-10-09 — Janelas controladas; próximo lote de otimização preparado

- Duas janelas sem transições em PID2832/HomeRegionW:61,86s/2447quadros stratTick15,72ms;
  61,29s/2071quadros17,29ms. Mesmos6sel/168tracked/207ativos/39não rastreados/0emdestruição.
  Não há aumento de contagem nessas janelas;39inclui nativos, não prova vazamento. Fonte otimizada ainda cara.
- Oráculo somente leitura42fontes comparou K2_GetComponentToWorld com3getters+MakeTransform:
  PASS Translation/Scale3D/Quaternion com sinal alinhado, erro último3,58e-07. Proposta reduz57->36calls,
  ainda não integrada/publicada; não alegar ganho de ms antes medição.
- Revisão ECONOMIA pediu preservar retorno físico após destino perdido no restore; patch ainda separado.
- Reservadas exclusivamente ao Claude do usuário IA_LOGISTICA e PERSISTENCIA no PARALEL_AGENTS;
  nenhum Codex assume. Minimapa registrado futuro junto à UI, sem prioridade atual.
- Laboratório PID2832 encerrado ao passar ao trabalho offline; Steam preservado. Sem callback export ativo
  nem robô. Próximo lote: transformação por componente e guards de máscara, testes offline antes carga limpa.
## 2026-10-09 — Otimização medida em carga limpa e snapshot regional

- PID2832/HomeRegionW com fonte otimizada:6soldados/168cópias, ordem de movimento aceita,
  32,96s/1709quadros: stratTick7,91ms, mod8,94ms/quadro. Anterior6selecionados16,72ms (outro trecho17,87).
  Redução observada~53% vs16,72; não benchmark controlado de render/FPS, ainda custo importante.
- CollectGarbage e desseleção/reseleção dos seis passaram,28cópias cada; nenhum hotpatch nem input.
  Fonte/lab medição limpa, sem reduzir aparência. Prolongado/zoom alto/entrada visual permanecem gates.
- Snapshot real HomeRegionW:127CP/122segmentos/468nós;95assets estrada,27não-estrada bloqueados.
  Incidências sem ambiguidade neste snapshot; duas componentes de estrada desconectadas, sem link inventado.
  Todas arestas físicas ainda validated=false; instalações/paradas ainda não conectadas.
  Snapshot/teste/relatório em dados/paralel/estradas/; teste reproduzido PASS.
- CONTRAPROVA: apósGC/reseleção6, nova janela1873quadros mediu stratTick16,40ms/mod17,46ms,
  95,42s desde início. Ganho inicial~53% NÃO sustentado nesta repetição; investigar recriação/acúmulo
  e condições de medição antes de alegar otimização temporal. README corrigido; agente notificado.

## 2026-10-09 — Contorno: setter único integrado; exportação de estradas em andamento

- Oráculo nativo K2_SetActorTransform/MakeTransform comparou posição/rotação/escala contra3setters,
  incluindo inclinação/escala não uniforme; tabelas packed passaram, erro ~7,63e-06 no caso original.
- Integrado setter1x/cópia e conversão1x/peça mantendo homotetia/28cópias/guards. Teste offline8cópias,
  2peças/3câmeras preservou geometria; estimativa106->57 UFunctions/soldado/quadro. Ordens/globals PASS.
  Fonte nova ainda não publicada nesta medição: carga limpa/ganho em ms pendentes. Não usar hotpatch.
- Rede HomeRegionW: incidência explícita CP0/CP1 em Segment0 e primeiro ponto equivalente CP0 confirmados.
  Transformação nativa local->world e índice1 de Points verificados, num4 e diferenças zero.
  Malha EditorLandscapeResources/SplineEditorMesh não é estrada; RoadT3Gravel01Snow confirmado em outros exemplos.
- Exportador fatiado em callback16ms, um elemento por etapa, sink persistente _G.roadsExport: running589linhas
  na última consulta. Não reiniciar enquanto esse trabalho está ativo; aguardar done/failure e salvar resultado.
  Não inferir transitabilidade física do asset. Economia ampliada permanece proposta offline/teste PASS, sem integração.
## 2026-10-09 — Integração das primeiras entregas paralelas (validação ao vivo em curso)

- Agentes independentes prepararam estabilidade, estradas e interface; artefatos e estado em PARALEL_AGENTS.
- Integrados somente guards de outlineDepth/updateOutline: recusar pawn/clone/câmera em destruição,
  fontes inválidas/ausentes e limpar referências sem acessar CustomDepth do pawn em destruição.
  Não é prova da causa ou solução das quedas nativas; contorno continua experimental.
- test_lifetime.py executa helpers reais da fonte integrada; baseline em memória demonstra regressões.
  Casos de destruição/fonte ausente/inválida/câmera e vivo PASS. Ordens/sintaxe/globals/custos/probe PASS.
- Estradas: módulo/teste offline PASS, rede nativa ainda não exportada; sonda de metadados preparada.
  Interface: painel/patch/teste PASS, ainda não integrado; caixa de seleção depende de projeção/DPI.
- Publicado pelo restart.sh: PID4436, Steam preservado; desta vez janela War normal, mod carregado.
  Carregamento do mundo/RTS e matriz de estabilidade ainda em curso, sem entrada injetada.
- Atualização ao vivo PID4436/HomeRegionW: seleção28 cópias, desseleção/reseleção após30,49s,
  morte pelo Health0/reap com referências apagadas e recriação28 cópias passaram. CollectGarbage
  confirmado por metadados sem parâmetros e chamado; depois nova desseleção/reseleção passou
  aos89,53s do ensaio. Não houve erro Registry/outline no log consultado. Teste curto, não certificação.
  stratTick medido ~2,55ms/quadro para um selecionado: desempenho de grupos ainda pendente.
- Sondas de estradas exportaram metadados e três exemplos em HomeRegionW: Connections StructProperty
  de LandscapeSplineSegmentConnection (ControlPoint/TangentLen/SocketName), SplineInfo InterpCurveVector
  com Points ArrayProperty. Cardinalidade/endpoints/curvas e classificação de estrada não exportados.
  Saídas externas roads-schema-live.txt e roads-types-live.txt; não extrapolar descoberta para hex.
- Grupo ao vivo: seis selecionados/168 cópias durante32,30s e1400 quadros, sem erro imediato;
  stratTick16,72ms e mod17,70ms/quadro. Gargalo confirmado; aparência não será cortada para ocultar custo.
  Agente estabilidade prepara otimização. INNER de Points/ConnectedSegments exportado com GetInner;
  incidência ControlPoint->Segment/End pode evitar ler Connections sem cardinalidade, ainda não validada.

## 2026-10-09 — Retomada do laboratório e tentativa de delegação Claude

- Steam voltou (PID22164); restart.sh passou as travas e lançou somente a cópia PID20144.
- Carregamento ainda não chegou ao RTS: título observado `Selecionar D:\FoxholeLab\Foxhole\War\Binaries\Win64\War-Win64-Shipping.exe`, CPU2,56 sem avanço em observações sucessivas, log parado após PS Scan finished17:43:25.
  Evidência aponta seleção de texto do console/QuickEdit, não prova de crash nem falha do contorno.
  Solicitado ao usuário sair da seleção manualmente; nenhuma entrada injetada, nenhum reinício por timeout.
- Usuário autorizou CLI Claude para trabalho paralelo. Tentativa Sonnet limitada a Read/Grep/Glob,
  análise offline da navegação (sem writes/laboratório), terminou exit1: OAuth expirado e sem refresh.
  Resultado/erro em D:/tools/foxhole-lab/claude-roads-{report,stderr}.txt. Sem tarefa Claude ativa.
- Nenhuma alteração no main.lua; contorno permanece experimental. Próximo: liberar console e executar
  teste controlado de criação/desseleção/reseleção/morte; renovar login Claude pelo próprio usuário.
## 2026-10-09 — Retomada: estabilidade prioritária; laboratório bloqueado pelo Steam fechado

- Pedido confirmado: continuar até um mod profissional, seguindo o roadmap; não apenas aparência.
- Relidos Como retomar, rastro de seleção e fluxo do contorno; consultados universal-modder,
  reverse-engineering/oráculos e playbook Unreal. Nenhuma causa nativa isolada ainda.
- Testes offline executados: test_orders.py, test_costs.py e test_inventory_probe.py PASS.
  Isso não certifica estabilidade de GC/MasterPose/callbacks no engine.
- Tentativa pelo restart.sh recusada pela trava legítima: Steam fechado. Nenhum processo Steam/War
  encontrado. Não abrir/login pelo usuário nem contornar a verificação de posse.
- Neste ambiente `bash` resolve para WSL sem /bin/bash; usar C:/Program Files/Git/bin/bash.exe.
  restart.sh continua esperando log mesmo quando lab.ps1 recusa a partida (pipeline grep mascara
  a falha). Espera interrompida; nenhuma validação ao vivo e nenhuma alteração em main.lua.
- Corrigido restart.sh externo: captura o resultado de lab.ps1 antes de filtrar PID e encerra
  imediatamente em falha. bash -n PASS; recusa real por Steam fechado retornou exit1 em 1,2s,
  sem esperar os 240s nem iniciar o jogo. Não altera a trava de posse.
- Próximo passo: usuário abrir Steam e fazer login; então reproduzir/isolar contorno por componente,
  GC, desseleção/reseleção e morte. Não ampliar features antes da estabilidade pendente.
## 2026-10-09 — Lote 17: implantação no hex; contorno completo aprovado visualmente, estabilidade pendente

- **Entregue:** Alt+L implanta uma cadeia faltante nos locais nativos, com orçamento próprio de 1100 bmat,
  separado do estoque de produção. Reusa instalações existentes, substitui ruínas correspondentes na mesma
  transformação (400+400), cria três TruckW (100 cada) em terreno Landscape com relevo/folga/separação checados.
  Confere HP/maxHP/classe-base/posição/rotação. Falha destrói spawns parciais, restaura ocultação/colisão das
  ruínas e não debita nem limpa a partida. Repetir não duplica. Inicio da logística preserva estacionamento real.
- **Validação:** offline PASS (inclui terreno vs telhado, orçamento, autoridade, rollback, idempotência).
  CallumsCape: preflight 2 instalações/3 vagas/1100; falha de HP forçada reverteu e preservou dois soldados,
  saldo1100. Publicação final criou refinaria2700/fábrica2000/3 caminhões900, Team1, sem flag de destruição,
  posições/rotações conferidas e repetição sem duplicar. Nova partida iniciou com seis soldados.
  Em 65,21 s: três caixas produzidas, base recebeu duas de munição e dez camisas; três caminhões HP900.
  Estoque inicial zerado para criar demanda, ondas desligadas: NÃO teste de equilíbrio/combate/estrada.
- **Fonte da implantação validada:** SHA256 `ECDCB921424AA6374A7AA609E50B580A12A34573790A5229846ABAAFD3EA61F6`.
  Infraestrutura/orçamento só nesta carga do mundo, não persistidos no save. Facilities não implementadas.
  Caminhões continuam em reta/sem colisão: acesso por estrada/água/ponte ainda pendente.
- **Feedback do usuário:** disco verde é marcador do caminhão; malha some longe do grupo na neve.
  `rts.eyeTick` só escolhe soldados/base, nunca caminhões; isso explica a hipótese de LOS presa ao grupo,
  não prova ausência por imagem. Usuário reforçou preferência por SILHUETA brilhante, não bolinhas.
- **Seleção implementada:** contorno amarelo e preenchimento encoberto SOMENTE no aliado selecionado,
  sem discos/bolinhas. O nativo `M_OccludedOutline` preenche partes encobertas, não contorna partes visíveis.
  MID ancorado imediatamente num PostProcessVolume. Máscara/stencil reaplicados nas dez peças separadas;
  também limpa o equipamento do comandante invisível, que deixava um vulto no soldado não selecionado.
  Cópias skinned seguem cada peça via MasterPose/attach e atualização final de quadro, sem IA/colisão/sombra.
  O usuário apontou desalinhamento fora do centro: corrigido com homotetia centrada na posição REAL da câmera,
  não deslocamento pelo forward fixo. Amostrador de seguimento/projeção: 52 amostras/6s, movimento724,41cm,
  erro máximo0,000985cm. Depois do feedback "só casaco", incluídos cabeça, mãos, pernas, mochila, capacete
  e arma: quatro cópias por peça visível, 28 atores por soldado atual. Usuário confirmou "agora ficou bao".
- **Estabilidade NÃO aprovada:** sonda MID sem ancoragem caiu12:45:33/PID15468 (hipótese GC, não prova).
  Extensão ao soldado completo caiu13:22:45/PID7088 durante sonda, depois novamente13:26:51/PID9600
  após renderizar 28 cópias corretamente. Ambas acesso nativo UE4SS/read0xffffffff, sem causa isolada;
  pcall não protege. Último log também mostrou `Lua::Registry::get_function_ref: Ref was not function`.
  Não atribuir conclusivamente a MasterPose, GC ou hotpatch. Contrato e limites em `dados/rastro_selecao.txt`.
  Offline PASS não substitui teste prolongado/GC/morte/reseleção no engine. Não considerar feature estável
  nem continuar features antes de isolar essa queda numa próxima sessão autorizada.
- **Encerramento:** usuário pediu parar após aprovar aparência. Fonte final publicada, sem logs temporários,
  SHA256 `86DBED189308C449BED9DB3BCB12FD800D2C6F5430E6FCCC297BED8D00A40FFE` (fonte/laboratório iguais).
  Laboratório PID2268 encerrado por pedido; Steam preservado. Não iniciar outro lote automaticamente.
  Sondas ficam fora do repo, sem robô/amostrador rodando. Sem entrada injetada; cliques foram do usuário.
  Universal-modder consultado no começo/fim, Gotchas38–42 atualizados; `um kb check` local, sem PR.

## 2026-10-09 — Lote 16: custos corretos e oráculos de reconstrução

- **Correção de dados, não mudança de equilíbrio:** a sonda antiga lia `ItemCodeName` em custos de
  estrutura/veículo; o tipo real é `CodeNameSmallQuantity.CodeName`. O `pcall` engolia o erro e exportava
  vazio. Reexportados `dados/custos_do_jogo.txt`: 281 itens, 592 estruturas, 184 veículos, 64 munições.
  Refinaria e fábrica custam 400 bmat cada; TruckW custa 100. Receitas de caixas não mudaram.
  Exportador reproduzível `tools/export_costs.lua` (erro interrompe, não vira zero) e teste `tools/test_costs.py`.
- **Sondas temporárias em CallumsCape:** classes ativas de refinaria/fábrica nasceram nas transformações das
  ruínas, HP2700/2000, TeamId1 e BaseStructureClass correspondentes. Um canteiro cru veio com alvo `None`
  e requisitos zero: isso **não** conclui construção. Reflexão + Ghidra read-only ainda não acharam/validaram
  uma chamada pública de conclusão. Não perseguido inventário/RPC. Contrato parcial e limites em
  `dados/rastro_reconstrucao.txt`; não há ainda reconstrução jogável nem cadeia pronta no hex.
- **Falha de estacionamento medida:** trace vertical pegou telhado de armazém, não chão; outro TruckW
  retornou IsValid com HP300/posição zero e foi rejeitado pelo inventário ativo (2/3). Bounds da fábrica
  incluem volumes gigantes, não são seu footprint. Próxima construção exige orçamento explícito, rollback,
  superfície/folga verificadas e estrada; não basta spawn num offset. Três caminhões + duas instalações
  custariam 1100 bmat, separados dos 240 bmat iniciais de produção da logística.
- **Correção pequena no mod:** `logi.convoySpawn` agora rejeita `bActorIsBeingDestroyed` antes de tocar no
  pawn, contar ou alertar. Mesmo contrato que o inventário regional já usava; comentário velho de locais
  fictícios corrigido. Teste offline cobre retorno IsValid já em destruição e proíbe mexer nele.
- **Validação:** testes de custos, suite de ordens/sintaxe e globals PASS. Publicado/reiniciado pelo script;
  em HomeRegionW a logística abriu com três caminhões e o comboio colonial nasceu HP900, flag de destruição
  false. Recusa do retorno em destruição foi testada offline, não forçada neste spawn ao vivo.
  Hash fonte/lab igual: `1411C81F01ADD984272C20C698D3B21F001FC43237477A0FCFD14C264A58FEC5`.
  Sem erro do mod no log da validação; não houve nova tecla nem teste de entrada real.
- **Encerramento:** probes de CallumsCape destruídos e colisões das ruínas restauradas; PIDs996/13368 da
  cópia encerrados. `map.txt` temporário removido (padrão HomeRegionW), Steam PID1508 preservado.
  Aprendizados 35–37 locais no universal-modder; `um kb check` PASS (60 notas), sem PR.
  Conferência final: nenhum processo War; Steam PID1508 preservado. Próximo lote: implantação offline nos locais fixos,
  com orçamento próprio e estacionamento seguro; depois transporte pela rede nativa de estradas.

## 2026-10-09 — Lote 15: inventário regional, partida sem logística fictícia

- **Reconhecimento por atores, não por imagem:** Deadlands carregou com 634 segmentos de paisagem/estrada,
  596 pontos de controle, 23 PlayerStart e fábrica em ruínas; nenhuma instância ativa nas classes de campo,
  refinaria, fábrica e caminhões pesquisadas. CallumsCape carregou com 431 segmentos/405 pontos, um campo
  de sucata ativo, duas fábricas e uma refinaria em ruínas, nenhum PlayerStart ou caminhão pesquisado.
  Rastro em `dados/rastro_regioes.txt`, sonda reutilizável `tools/inspect_region.lua`. São estados locais
  carregados, **não** prova de ausência no mapa/servidor. Pesquisa incluiu histograma das classes derivadas.
- **Alerta do usuário persistido:** estruturas podem ficar invisíveis conforme ângulo/oclusão, veículos por LOS.
  Nunca transformar falta na captura em falta no inventário. Regra em AGENTS, README/estudo/roteiro atualizados.
- **Autostart regional:** comparação do caminho sem maiúsculas (`DeadlandsHex` do índice abre como
  `DeadLandsHex`); só conclui quando o RTS realmente ligou. CallumsCape não tinha âncora pesquisada;
  campo de sucata agora é último recurso depois dos PlayerStart/veículos. Sem coordenada regional hardcoded.
- **Logística (`scan`/`ready`):** retirados campo/refinaria/fábrica imaginários e caminhões sem pawn.
  Nova partida/assalto e continuar com logística checam atores ativos antes de apagar a sessão anterior.
  Ruínas ainda não funcionam como instalações; atores ocultos continuam disponíveis. Atores marcados para
  destruição não contam só porque IsValid ainda é true. Comboio sem classe/ator criado não soma contador/carga.
- **Base de navegação:** concluídos os testes do parâmetro opcional do A* (volume/chão/degrau/orçamento,
  falha estrita sem reta de emergência, job.done); quatro sondas a 12 m em Deadlands usaram UFunctions nativas
  (36–54 ms síncronos). **Caminhões continuam em reta**; faltam integração à rede, acesso externo e teste de
  água/ponte. Não confundir esta base técnica com transporte por estrada entregue.
- **Validação:** suite offline e globals PASS; publicado/reiniciado, hashes da fonte e laboratório iguais.
  CallumsCape: autostart ligado, comandante HP100 via campo, nova partida e assalto recusados preservando
  dois soldados reais. HomeRegionW: autostart, fábrica explicitamente ocultada ainda descoberta, partida com
  seis soldados/três caminhões reais; em 118 s, três caixas produzidas e uma entrega. Estoque inicial da base
  esvaziado de propósito para criar demanda, ondas desligadas: **não é teste de equilíbrio**. Comboio colonial
  criado com pawn real. Nenhum erro do mod no log desta validação; entrada real pendente (12x).
- **Encerramento:** configuração temporária de mapa removida (próxima abertura volta a HomeRegionW);
  PIDs 19896/14176 da cópia encerrados após as sondas. Conferência: nenhum processo do jogo, Steam preservado.
  Aprendizados 33–34 no universal-modder; `um kb check` PASS (60 notas), sem PR.
- **Próximo lote:** rastrear reconstrução nativa das ruínas de CallumsCape e criação de caminhões reais do
  cenário, depois ligar a rede de estradas descoberta ao transporte. Ainda não há cadeia jogável em um hex real.

## 2026-10-09 — Região real e construção: correção de escopo do usuário

- HomeRegionW é a ilha de treinamento/embarque dos Wardens, não um hex da guerra. ROADMAP e estudo
  corrigidos: continua como bancada, mas a fase 3 exige reconhecer e validar uma região `Maps/Master/*Hex`.
  Não assumir atores de guerra apenas porque o cliente contém o mapa; verificar carregamento/streaming,
  posição inicial, terreno, estradas e instalações presentes, sem coordenadas fixas do lobby.
- Separados no roteiro os dois ramos: estruturas urbanas fixas (fábrica/refinaria) e facilities construídas
  pelos jogadores. Contexto externo explicitamente citado no ROADMAP, separado dos dados extraídos do cliente
  em ESTUDO_MECANICAS. Construção/receitas precisam de rastro local antes de implementação offline.
- **Rascunho não publicado:** o A* em `main.lua` aceita limites opcionais de navegação (volume, chão,
  degrau, célula e orçamento), sem retorno em reta numa falha estrita; jobs sinalizam `done`.
  Testes offline existentes e globals passaram, mas faltam testes específicos e validação ao vivo.
  Caminhões ainda não usam isso nem seguem a rede nativa: não considerar feature entregue.
  Backup pré-rascunho: `D:/tools/foxhole-lab/main-before-roads.lua`.
- Apenas documentação nesta correção de escopo; não publicado/reiniciado o jogo. Laboratório continua fechado
  (nenhum `War-Win64-Shipping.exe` na conferência). Universal-modder consultado; gotcha 32 registrado;
  `um kb check`: **PASS, 60 notas**, nenhum PR.

## 2026-10-09 — Laboratório fechado quando ocioso (pedido do usuário)

- Nova regra persistida em `AGENTS.md`: fechar a cópia ao terminar a validação ou passar ao trabalho offline;
  deixar aberta só durante testes ativos ou por pedido do usuário. Nunca encerrar Steam nem o cliente oficial.
- Sem robô ou teste ativo, encerrado apenas o PID **13112**, conferido como
  `D:/FoxholeLab/Foxhole/War/Binaries/Win64/War-Win64-Shipping.exe`, via `um win kill`.
- Investigação das estradas já preservada fora do repositório: `D:/tools/foxhole-lab/road_graph.tsv`,
  `t_road_*.lua`, `road_inspect.py`. HomeRegionW tem 122 `LandscapeSplineSegment`, dos quais 95 com malha
  em `/Roads/`; os demais 27 usam `SplineEditorMesh` (não tratar como estrada). `Points.Center` e os
  `ControlPoint.ConnectedSegments` permitem reconstruir curvas/conexões reais; 595 nós, 563 arestas,
  duas redes (397 e 166 nós). Coordenadas são locais: aplicar `KismetMathLibrary:TransformLocation` com
  o transform do `LandscapeSplinesComponent`. `Connection.End` é bool (não inteiro).
- Próxima etapa: acessos transitáveis das instalações à rede e movimento de caminhões por essa rede.
  Refinaria/fábrica estão afastadas dos nós das estradas (mais de 100 m): não basta substituir a reta por
  "nó mais perto"; verificar acesso, ponte e ponto externo de carga/descarga antes de publicar.

## 2026-10-09 (manhã, 15) — Lote 14: morte nativa; fim da corrida no corpo

- **Bug reproduzido e causa medida:** soldado morto em marcha ficava com `Health=0`, velocidade e
  `AnimInstance.Speed=500 cm/s`, até sumir aos 20 s. `ApplyDamage` no host não acionava `OnRep_Health`.
  Sonda de personagem nativo e do RTS, lista de UFunctions e enum de atividades precederam a correção.
- **Fluxo encontrado:** `SimCharacter:OnRep_Health` → ragdoll nativo. Ghidra confirmou o wrapper
  `0x141227ed0` → `0x140b04440` → `0x140b107f0` (perfil `Ragdoll`, física da malha); `BPCinematicDeath`
  sozinho não fez a transição testada. Sem RPC, inventário, teclado/mouse ou mudança de isolamento/Steam.
- **Correção (`anim.retire`, no `reap` compartilhado pelos dois lados):** remover marcadores/cache antes da
  notificação nativa; consumir entrada, zerar velocidade, restaurar atrito/frenagem/aceleração guardados no
  nascimento, sair da mira e chamar `OnRep_Health` uma vez. `postureTick` ignora mortos. `untrack` zera
  `animAddr` e não remove o dono novo de um endereço reciclado. O corpo permanece 20 s; controlador vai ao pool.
- **Validação:** testes offline + `check_globals.py` passaram; publicado pelo `restart.sh`. Ao vivo, morto
  marchando a 500 cm/s passou a velocidade zero, valores originais de movimento, cache vazio, física da malha
  ativa e AnimInstance inválido. Captura `D:/tools/foxhole-lab/death-fixed_small.png` conferida: corpo caído.
  Contrato persistido em `dados/rastro_morte.txt`; sondas/rastros e decompilação ficam fora do repositório.
- **Cuidado nas sondas:** nunca consultar pawn após o TTL nem AnimInstance após ligar o ragdoll; `IsValid`
  pode mentir até o GC. Loop de amostragem precisa de guarda `active` (o `return true` não encerrou a sonda).
  Uma sonda tardia sem essa proteção deixou o canal sem resposta; recuperado com reinício, não Ctrl+R.
- README, ROADMAP e teste manual 12w atualizados. **Regressão concluída:** robô em 3x, passo a cada 3 s reais,
  6:32 de jogo, derrota na onda 6, **36 abates / 26 perdas**, sem crash ou erro de cache. A conferência do cache
  passou nos 31 passos, incluindo mortes dos dois lados e reuso de controladores. Não comparar este resultado
  de equilíbrio diretamente com os lotes 12–13 (1x/outra cadência); continuam pendentes 2–3 partidas em 1x.
  Robô encerrado; laboratório deixado em 1x, seis soldados e ondas automáticas desligadas, pronto para teste.
- Universal-modder consultado no início (`kb search foxhole/death/unreal`, skills de RE e Unreal); gotcha 21
  corrigido e gotchas 28–29 acrescentados localmente. `um kb check`: **PASS, 60 notas**; nenhum PR.

## 2026-10-09 (manhã, 14) — Lote 13: comboio inimigo

- `CFG.ECONVOY`, `logi.convoy*`: com ondas automáticas, a cada 35 s um caminhão colonial (`BPTruckC_C`, criado
  com `LoadAsset` + `SpawnActor`: funciona) vai da retaguarda (90–200 m) à frente (45 m); chegando soma
  `combat.cargo`; cada onda gasta até 2 cargas (`logi.waveCut`) e cada uma que falta tira 2 soldados (mín. 3).
  Nossos soldados a 15 m o danificam (tiro visível); morteiro/granada acertam caminhões dos dois lados
  (`logi.blast` em `shell`); destruído rende 25 de mão de obra. `logi.hit` unifica o dano dos caminhões.
- Rota em reta passava por cima de penhasco (b13_conv.png): `logi.routeOk` amostra o chão a cada 10 m (degrau
  ≤ 4 m, desnível ≤ 15 m). Ao vivo: 5/5 rotas válidas encontradas.
- Testes offline passam (corte da onda, chegada soma carga, soldados destroem). Ao vivo: comboios chegando pela
  rota validada (4 na primeira partida), caminhão no chão; ele some da tela fora da visão dos nossos soldados
  (LOS do jogo, como os soldados inimigos); o disco vermelho da vista alta aparece sempre.
- Robô (não embosca, então é o pior caso: todo comboio chega): **derrota na onda 10**, 83 abates / 38 perdas,
  9 min, sem crash. 16 comboios chegaram, 0 destruídos; mesmo assim 5 ondas vieram menores por falta de carga
  (35 s por comboio não acompanha o ritmo das ondas no fim); 7 entregas nossas, nenhum caminhão nosso perdido.
  O comboio só encolhe ondas, então a derrota é variação do robô (lote 12: vitória com 24 perdas; antes do
  lote 9: derrotas nas ondas 9–10). Próxima sessão: 2–3 partidas do robô para medir a variação.
- README (seção Logística, item 7) e TESTE_MANUAL (12v) atualizados.
- **Pedido do usuário ao fechar:** animação de morte (soldado "correndo" parado ao morrer) e o princípio
  "rastrear antes de reinventar", com o universal-modder no começo e no fim de cada sessão (`ROADMAP.md`,
  `CLAUDE.md`). A nota do Foxhole no universal-modder ganhou os gotchas 19–27 (local, `um kb check` PASS; sem PR).

## 2026-10-09 (madrugada, 13) — Lote 12: logística v1

- **Cadeia (`CFG.LOGI`, tabela `logi`):** caminhão de recurso campo de sucata → refinaria (100 por viagem); refinaria
  2:1 em bmat; fábrica faz caixas de munição (80 bmat, 50 s ×0,2) e camisas (80 bmat, 80 s ×0,2, 10 soldados),
  no automático a mais em falta (Shift+L fixa); 2 caminhões de suprimentos (15 caixas) levam ao depósito mais
  carente (base ou ponto nosso; L fixa o próximo). Recrutar gasta camisa do depósito (ponto sem camisa → base);
  `resupply` ganhou o parâmetro do depósito (1 caixa = 6 recargas; vazio não recarrega e alerta). Ponto perdido
  zera o estoque. Inimigo a 15 m de caminhão andando: 25 HP/s por inimigo; destruído some com a carga e volta em
  30 s por 100 bmat. Save guarda os estoques (`logi.snapshot/restore`). Painel: 2ª linha "LOGÍSTICA".
- **Lugares e caminhões do próprio mapa:** `FindAllOf("BPSalvageField_C"/"BPRefinery_C"/"BPFactory_C")` mais perto da
  base (sem eles, pontos fixos); `BPTruckW_C` estacionados: movimento de personagem, sem física, então
  `K2_SetActorLocation` + `groundZ` + yaw fica (medido: parado 2 s sem voltar). Sem colisão, em linha reta.
- Validado ao vivo: sucata 100 → bmat 50, 3 caixas, entrega pinada na base (munição 6 → 8), captura b12_res.png.
- `test_orders.py`: refinaria, escolha da fábrica, entrega, recarga gastando e falhando sem estoque.
- Robô: **vitória nas 10 ondas**, 111 abates / 24 perdas, sem crash; 9 entregas (todas ao ponto A), 10 recrutas
  caíram para a base por falta de camisa no ponto, 2 alertas de depósito sem munição, nenhuma emboscada.
- Pendências: estrada (caminhões cortam caminho por cima de tudo), IA inimiga com logística, veículo como unidade.

## 2026-10-09 (madrugada, 12) — Estudo das mecânicas do jogo

- Índice do pak (v8, sem criptografia) → `dados/arquivos_do_pak.txt`; tabelas de custo/vida/combustível/carga
  lidas com `DataTable:ForEachRow` → `dados/custos_do_jogo.txt`; resumo em `ESTUDO_MECANICAS.md`.
- Um dump genérico de todas as colunas derrubou o jogo em `BPAirDynamicData` (crash nativo); a leitura por colunas
  conhecidas funcionou. Regra: ler só colunas de tipo simples.
- HomeRegionW tem campos de sucata/componentes/enxofre/petróleo, refinarias, fábrica, base avançada e caminhões:
  é a região pequena da fase 3 (logística v1).

## 2026-10-09 (madrugada, 11) — Lote 11: várias frentes; roteiro

- **Pedido do usuário:** "para um RTS nível Foxhole, o cara vai ter que olhar muitas frentes", e depois: começar
  numa região pequena e ir para o mundo todo; estudar navios, aviões, transporte, fabricação e logística ("a
  guerra em si é a pequena parte da engrenagem"). Roteiro em `ROADMAP.md`.
- **Zoom até 160 m** (`CAM_DIST_MAX` 16000; o teto de 60 m do lote 10 saiu). `rts.zoomGfx`: `r.ViewDistanceScale`
  = altura / 20 m (mínimo 3), reaplicado a cada meio ponto. Validado: 160 m, escala 8, mapa inteiro desenhado.
- **Ícones na vista alta** (`CFG.STRAT`, `rts.icon/stratTick`): acima de 60 m, disco com material `CalloutRed`
  dinâmico (azul/laranja/vermelho), escala proporcional à altura. Inimigo só com a malha visível
  (`Mesh.bHiddenInGame`), para não revelar quem o jogo esconde. Validado por captura (b11_strat.png).
- **Alertas de frente** (`CFG.ALERTS`, `rts.alert/jumpAlert`): ponto sob ataque, ponto perdido, onda, baixa; fila
  de 8 com lugar; mesmo tipo a 15 m em 20 s não repete; Espaço vai ao mais novo e, em 4 s, aos anteriores;
  painel "! N alertas (Espaço)". Validado ao vivo (2 alertas da onda e do ponto tomado).
- **Grupos 1–5** (Alt+1–5 atribui, toque duplo centraliza), **0 = todos** (antes 3). **Q/E** passam pelos pontos.
  Espaço, Q, E, 4, 5 e 0 são ações do pawn no jogo (lidas de `InputSettings` ao vivo): aceitas no teste de teclas.
- `S` entrou no `env` do canal. `test_orders.py`: alertas (repetição, Espaço anda na fila) e grupos.
- Regressão do robô (lotes 9–11): **vitória na onda 5 por domínio** (3 pontos por 90 s), 39 abates / 17 perdas,
  sem crash; as 5 ondas quebraram e fugiram, 1 evacuação automática. Antes do reequilíbrio, derrota nas ondas 7 e 6.
  Atenção: agora pode estar fácil demais (as ondas quebradas não retomam pontos); observar nas próximas.

## 2026-10-09 (madrugada, 10) — Lote 10: tempo, câmera WASD e roda, visual

- **Pausa tática (Pause / Ctrl+Espaço) e velocidade 1x/2x/3x (Insert):** `SetGlobalTimeDilation` (pausa =
  0,0001). A câmera e o painel passaram a contar tempo real (`GetRealTimeSeconds`), senão congelavam junto.
  Desligar o RTS volta a 1x. Validado: pausado, 0,001 s de jogo em 5 s reais e a ordem dada esperou; 2x medido
  2,00 (14,2 s de jogo em 7,1 s reais); painel "PAUSADO" atualizando.
- **Pedido do usuário: WASD e roda do mouse na câmera.** WASD junto das setas (no RTS a entrada do comandante já
  está desligada). Roda: `WasInputKeyJustPressed(MouseScrollUp/Down)`; o eixo `MouseWheelAxis` não serve, guarda
  o último valor (medido: -1 parado, a câmera fugia). Validado com o usuário rolando: "roda do mouse lida".
- **Pedido do usuário: "linhas artefatuais e objetos desaparecendo".** Câmera estava a 76 m (máx. 90). `rts.gfx`:
  `r.ViewDistanceScale 3`, `r.Shadow.DistanceScale 2.5`, `LOSPostProcess` do comandante com peso 0 (as faixas
  escuras da linha de visão); zoom máximo 60 m. Aplicado ao vivo na sessão do usuário; aguardando retorno.
- Moral (lote 9) rebalanceada após o robô cair na onda 7 e depois 6 (as ondas quebradas aceleravam o contador
  de ondas: ~39 s por onda contra ~53 s antes; fugitivos não rendiam): fuga rende o bônus de abate, onda
  quebrada dá +15 s de reagrupamento, e a evacuação não puxa quem já está no ponto ou no posto. Robô pendente.

## 2026-10-09 (madrugada, 9) — Lote 9: evacuação de feridos; moral inimiga

- **Evacuação (`CFG.MEDEVAC`, `rts.medevacStep`):** nosso soldado < 30% de vida, sem ordem há 15 s (nem foco,
  área, segurar ou marcha) recua sozinho ao posto de socorro → ponto nosso → médico mais perto; libera em 80%
  (ou desiste após 45 s parado). Ordens do jogador marcam `m.orderT` (em `os.clock`: `issueMove` vem antes de
  `now()` no arquivo — o verificador pegou) e cancelam a evacuação.
- **Moral (`CFG.MORALE`, `rts.moraleCheck/fleeStep/purgeFled`):** onda de 6+ que cai a 25% do tamanho (somando
  pinça e reforços em `combat.waveSize`) quebra; os sobreviventes correm para a entrada (`e.home`), com o
  `retreat` (metade dos acertos, sem atirar) e somem ao chegar sem contar abate (`combat.fled`). O laço do
  `enemyTick` pula quem foge com `goto nextEnemy` (rótulo no fim do bloco). Oficial abatido suprime (+0,5)
  quem estava a 10 m. Não vale no assalto.
- `check_globals.py` ignora rótulos de `goto`.
- `test_orders.py`: ferido vai ao posto, ordem recente segura, curado se libera; onda quebrada foge, quem chega
  some sem contar abate.
- Robô: 1ª versão perdeu na onda 7 e depois na 6; rebalanceado (ver lote 10).

## 2026-10-09 (madrugada, 8) — Lote 8: som por arma e por lado

- Não há vozes entre os 487 `SoundCue` carregados; há tiros por arma e facção em `/Game/Audio/SFX/Weapons/`.
  `WEAPONS.*.sndW/sndC`: fuzil `RifleLongW` x `CarbineCShot` (combina com a carabina Colonial do inimigo), MG
  `MGW-RFShot` x `MGC-RFShot`, atirador `SniperShot` x `SniperShotC`, pistola `PistolLIghtWShot` (médico e
  oficial). Tom 0,95–1,05; sem o som, volta ao `FX.shot` com o tom da arma. `asset()` agora tenta `LoadAsset`
  uma vez por caminho fora da memória (`S.fxTried`). Validado: após reinício, os 10 sons carregados e 94 tiros
  sem erro; a audição fica para o teste manual (12k).

## 2026-10-09 (madrugada, 7) — Lote 7: barra de vida

- Material colorido achado listando `Material`/`MaterialInstanceConstant` carregados e lendo
  `VectorParameterValues`: `CalloutRed` é instância do `Unlit` com parâmetro `Color`. A barra é um cubo fino
  com material dinâmico dele (`CreateDynamicMaterialInstance` + `SetVectorParameterValue`), presa ao soldado
  com rotação absoluta (`SetAbsolute`), comprimento proporcional à vida, verde/amarelo (<60%)/vermelho (<30%);
  só nos nossos feridos e com o RTS ligado (`rts.hpTick`, 0,3 s; cor só muda ao trocar de faixa).
  Validado: 80 → verde longa, 45 → amarela, curado → some (`hp1c.png`, `hp2c.png`). O tom avermelhado dos
  feridos na captura é o efeito de ferimento do jogo.

## 2026-10-09 (madrugada, 6) — Lote 6: oficial; metralhadora inimiga suprime em área

- **Oficial (Ctrl+0, −40, um por esquadrão):** pistola; aliados a 10 m (ele incluso) acertam 15% mais e perdem a
  supressão 1,8× mais rápido (`CFG.OFFICER`, `rts.officerNear` com cache de 0,5 s por soldado). Marcado com o
  estandarte enrolado do lado (o dos pontos) preso sobre a cabeça: `FlagShortA/B` são planos verticais e
  sumiam vistos de cima. Inimigo: o 1º de cada onda a partir da 3 é oficial; abatê-lo rende +20
  (`rts.officerDown`); no assalto, a guarnição do ponto da frente tem um. `clearEnemies` agora chama
  `destroyMarker` (hook, estandarte e marcadores).
  Validado: oficial nosso com estandarte, 2º recusado; onda 3 com oficial à frente; abate → "+20" no log.
- **MG inimiga sem visada:** guarda onde viu o alvo pela última vez (`e.seen`) e por 8 s fica e suprime em área ali
  (`rts.enemyArea`, mesmo `rts.areaShot`, que agora serve aos dois lados; municão só conta para os nossos).
- `test_orders.py`: aura (recupera mais rápido perto, igual longe), 2º oficial recusado, MG inimiga suprime o
  escondido sem gastar munição e desiste após 8 s.
- Robô: derrota na onda 10, 114 abates e 42 perdas (mesmo padrão), 8 oficiais inimigos abatidos, sem queda.
  Granadas 0 nessa partida (antes 8–23): conferido à parte que o fuzileiro lança contra inimigo em trincheira
  (3 granadas); foi o cenário (inimigos sem cobertura a ≤18 m da posição do robô), não defeito.

## 2026-10-09 (madrugada, 5) — Lote 5: modo Assalto; robô; crash intermitente; verificador de globais

- **Modo Assalto (Alt+F6):** 8 soldados e 120 de mão de obra contra três pontos inimigos a 26–36 m
  (`CFG.ASSAULT.dist`), cada um com trincheira, arame do nosso lado e 4 de guarnição em círculo de 1,5 m (a
  formação das ondas espalhava e pôs dois no telhado do prédio ao lado do ponto A). Sem ondas; reforço só pela
  renda dos pontos (1º reforço só após 40 s); cada captura nossa libera contra-ataque em 8 s (`rts.counter`).
  Vitória: os três pontos nossos sem inimigo vivo, ou segurá-los 60 s; derrota só por esquadrão perdido (o
  inimigo dono de tudo não é derrota no assalto). Guarnição (`e.post`, `rts.holdPost`): sem alvo a tiro volta
  ao ponto e segura; ponto perdido a solta. Save grava o modo e o posto de cada guarnição.
  Validado: guarnições paradas nos pontos com o esquadrão atacando A (0 longe do ponto em 5 amostras); A
  tomado → reforço pelo ponto C 8,0 s depois; salvar/continuar no meio do assalto mantém modo, 8 guarnições
  presas e donos dos pontos (`as4.png`).
- **Bug pego no teste:** o gatilho do contra-ataque usava `ai` dentro do `pointsTick`, antes do `local ai`
  (vira global nil; o pcall do passo engoliu). O `check_globals.py` não viu porque é insensível a escopo e
  `local ok, ai = pcall(...)` em `anim.track` contava como declaração. Renomeado para `inst`, e o verificador
  agora avisa quando um nome de topo aparece antes como local interno (`SHADOW_OK` lista os conferidos).
- **Robô (balanço depois da lentidão de verdade do lote 4):** derrota na onda 10, 104 abates e 39 perdas, o
  mesmo padrão de antes; 7 min sem queda.
- **Crash intermitente (ainda aberto):** uma partida do robô caiu 9 s após `newGame`, logo depois de recrutar
  no ponto A (AV 0x3 a partir do laço por quadro, Lua → acesso a UObject). A repetição do mesmo roteiro não
  caiu. O hook de animação já não toca em pawn. Se voltar, instrumentar `recruit`/`spawnSoldier` com log antes
  e depois de cada chamada Unreal.

## 2026-10-09 (madrugada, 4) — Lote 4: posto de socorro, arame farpado, marcador de área; lentidão de verdade

- **Malhas escolhidas por vitrine:** busca em `FindAllOf("StaticMesh")` por tenda/arame/hospital (213 achados),
  `GetBounds()` para o tamanho e uma fileira lado a lado no mapa (`b4b.png`). `CanvasTent09` era só a armação;
  `CanvasTent06` (lona fechada, escala 0,6) virou o posto; `BarbedWire04` (cavalete de arame, 7,5 m, centro a
  306 cm do pivô) em escala 0,8 virou o arame (`BarbedWireFence01` parecia tela de metal).
- **Posto de socorro (Ctrl+8, −30, até 2):** nossos soldados a 6 m com supressão < 0,2 recuperam 4 HP/s e param
  de sangrar. Validado: dois fuzileiros a 40 de vida foram a 100 no posto.
- **Arame farpado (Ctrl+9, −10, até 10):** faixa de 6 m × 2,2 m atravessada à ameaça (mesma regra de giro da
  barreira, agora em `fort.facing`); quem está dentro, dos dois lados, anda a 35%. Sem colisão: o A* não desvia.
  O inimigo estende de graça uma faixa a 9 m do centro do ponto que toma, do lado do nosso esquadrão
  (`CFG.ENEMY_WIRE`, `fort.enemyWire`).
- **Lentidão de verdade (arame e supressão):** a 1ª medição (laço de 100 ms gravando a posição numa global)
  deu 58 cm/100 ms constantes atravessando o arame. Com atrito e frenagem zerados, o CMC mantém a velocidade
  quando o limite cai (`IsExceedingMaxSpeed`); a escala do `AddMovementInput` só limitava a arrancada. Ou seja,
  a lentidão por supressão (`SUPP_SLOW`) também nunca tinha valido. `fort.capSpeed` corta a velocidade
  horizontal direto quando a escala fica abaixo de 0,9. Medido de novo: 20 cm/100 ms dentro da faixa (35%),
  58 fora.
- **Marcador do fogo em área:** anel de 12 pontos laranja menores no círculo; some quando nenhum soldado vivo
  tem mais aquela ordem. A ordem agora é uma tabela única para todos os soldados.
- Save grava postos e arames (e se o ponto já tem trincheira/arame inimigo); F11 e nova partida limpam.
- `test_orders.py`: faixa do arame (dentro, ao lado, além da ponta), cura do posto (calmo cura; suprimido e
  longe não), save com postos e arames; teclas Ctrl+8/9.

## 2026-10-09 (madrugada, 3) — Lote 3: salvar/continuar, fogo de supressão em área; crash do hook

- **Salvar e continuar (Ctrl+F6):** com ondas automáticas, a partida é gravada a cada 30 s em
  `ue4ss/Mods/FoxholeRTS/save.txt` (Lua `return {...}`, lido com `load` num ambiente vazio; versão `v=1`):
  onda, placar, tempo, mão de obra (nossa e do inimigo), dificuldade, mapa, pontos (dono e progresso),
  barreiras (posição e giro), trincheiras e cada soldado vivo dos dois lados (classe, posição, vida, abates,
  munição, grupo). Vitória ou derrota apagam o save. Ao ligar o RTS sem partida, um alerta avisa que há
  partida salva. Tabela `sv` (`ser`, `parse`, `collect`, `save`, `read`, `restore`, `load`, `tick`, `map`);
  a barreira ganhou `fort.wall` para o carregamento reaproveitar.
  Validado: salvar com trincheira, barreira, pontos A nosso/B inimigo, veterano com 4 abates e MG com 55 de
  vida → limpar tudo → continuar: tudo igual (`sv1.png`); alerta ao reabrir o jogo; autosave 30 s depois do
  continuar; derrota apagou o arquivo.
- **Fogo de supressão em área (Ctrl+botão direito / Ctrl+F7):** os selecionados (menos médicos) atiram por
  20 s num círculo de 4,5 m. Fora do alcance, andam até ele. Sem visada não há dano: cada tiro suprime todo
  inimigo no círculo com 70% da supressão da arma (MG montada ×1,5) e levanta terra num ponto do círculo;
  inimigo à vista e ao alcance leva tiro normal. Gasta munição; mover, atacar, recuar ou segurar cancelam.
  `rts.areaOrder`, `rts.areaStep`, `rts.areaShot`; `rts.shotFx` (clarão e som) passou a servir aos dois tiros.
  Validado: 5 soldados mirando e atirando num ponto vazio a 15 m, 60 tiros em ~8 s (`af1.png`).
- **Crash (EXCEPTION_ACCESS_VIOLATION 0xffffffff dentro do UE4SS, 96 s após abrir):** `clearEnemies` não
  tirava os inimigos de `anim.units`; o AnimInstance da onda seguinte reaproveitou o endereço de um destruído
  e o hook gravou `bIsInScopeMode` no pawn morto (pcall não pega). Correção: `clearEnemies` chama
  `anim.untrack`, e o hook só escreve no AnimInstance que está sendo atualizado (sempre vivo); o
  `bIsInScopeMode` do pawn passou para o `postureTick` (0,3 s), que só percorre as listas de vivos.
  Validado: onda nova após continuar e 4 ciclos de nova partida → limpar com 6 inimigos vivos, sem queda.
- `test_orders.py`: save (coleta → texto → leitura, dono neutro, mortos fora, texto inválido recusado) e fogo
  em área (sem visada só suprime quem está no círculo, gasta munição, mover cancela); teclas Ctrl+F6/F7.

## 2026-10-09 (madrugada, 2) — Lote 2: posturas e ações; aviso do menu

- **Posturas pelo mesmo hook de animação:** agachado (`CharacterStance` 1 + `bStanceIsCrouched`) quando
  parado dentro de trincheira ou com supressão ≥ 0,4 (`CFG.CROUCH_SUPP`); curvado correndo (stance 3) ao
  recuar. `m.crouch` é calculado a cada 0,3 s em `anim.postureTick` (fora do hook, para não traçar por
  quadro). Validado: 4 soldados ajoelhados no buraco de raposa mirando (`c2.png`); recuo → stance 3 nos 6.
- **Ações:** `ActivityState` 6 (arremesso) por 0,8 s ao jogar granada, 20 (primeiros socorros) por 1,2 s
  quando o médico cura, 3 (tiro) por 0,2 s. Validado pelo valor no AnimInstance (médico act=20 curando);
  o arremesso usa o mesmo caminho, mas é curto demais para pegar em captura pelo canal.
- **Aviso do menu:** é Slate nativo (no menu só existe um `UserWidget`, a mira; `MainMenuPlayerController` e
  `WarGameInstance` não têm função para fechá-lo). Liberar a rede iria contra o modo offline. Mitigação: o
  autostart sai do menu em 2 s (`CFG.AUTOSTART_DELAY_S`, era 8). Validado: menu → mapa em 2 s, RTS ligado
  5 s após o menu (antes ~11 s). O caçador de widgets do lote 1 foi removido.

## 2026-10-09 (madrugada) — Lote: animação de arma e tiro, economia inimiga, aviso do menu

Primeiro lote no novo fluxo (várias features, um teste só no laboratório).

- **Animação de arma (pedido do usuário: "o tiro sai mas o soldado não mira nem segura a arma").**
  Estudo pela reflexão (guia Unreal do universal-modder: dump de classes primeiro):
  - O AnimInstance é `ABP_Male_C` (pai nativo `CharacterAnimInstance`). A pose depende de
    `EquippedWeaponGripType` (enum `EEquippedWeaponGripType`: None 0, Rifle 1, Pistol 2, Sniper 4,
    HeavyMachinegun 5, LightMachineGun 24…), `bIsScoping`, `canEnterStandScoping`, `AimOffsetYaw/Pitch`
    e `ActivityState` (`ECharacterActivityState`: Firing 3).
  - O update nativo recalcula tudo a cada quadro a partir do item equipado e do controle local, que nossos
    soldados não têm: gravar direto não fica (grip voltava a 0). Mas `BlueprintUpdateAnimation` do ABP roda
    **depois** do nativo; um `RegisterHook` nele grava os nossos valores e o grafo os usa.
  - `AimOffsetYaw` vinha −140° (rotação de controle 0 − corpo 140): o pawn gira para a rotação de controle,
    mas o aim offset não acompanha sem controle local → o hook zera o offset.
  - A arma estava no osso `hand_r` (apontando para trás). Sockets do corpo: `S_GenericGun`, `gun_r`, `gun_l`;
    `S_GenericGun` dá a pose certa. Master pose não serve (a malha da arma tem um osso só, `Root`).
  - Resultado (`cb4.png`, `cb6.png`): nossos e inimigos com fuzil no ombro, as duas mãos na arma, mirando
    para o alvo; parados em repouso, fuzil no ombro em descanso. MG com grip 5 (com 24 ficava atravessada).
  - Código: tabela `anim` (`anim.onUpdate`, `anim.track`, `anim.untrack`), `CFG.ANIM_ABP`, `CFG.AIM_HOLD`
    (1,5 s mirando após a última tentativa de tiro), `CFG.FIRE_ANIM` (0,2 s de Firing por tiro); `armWith`
    prende no `S_GenericGun` e registra o soldado; `destroyMarker` o retira; `bIsInScopeMode` só parado.
    O clarão do tiro sai do socket `S_Muzzle` da arma.
- **Economia inimiga (reforços):** validada ao vivo. Natural: o inimigo tomou C na onda 1 e mandou
  1 reforço; forçado: 3 pelo ponto A. Painel "reforço inimigo N". Plural corrigido ("1 soldado").
- Robô com o lote (reforços + animação): perdeu na onda 10 (109 abates, 34 perdas), igual às rodadas
  anteriores; a economia inimiga não desequilibrou.
- **Aviso do menu** ("Falha ao baixar informações do servidor [Erro: 1]… Atualizar / Fechar", `menu1.png`):
  o caçador por nome de classe de `UserWidget` não achou nada; a sonda pelo canal chegou depois do menu.
  Resolvido no lote 2: é Slate nativo; o autostart agora sai do menu em 2 s (ver entrada acima).

## 2026-10-08 (tarde) — Economia inimiga (reforços)

- Cada ponto que o inimigo segura rende 0,6/s de mão de obra para ele (teto 200; só com ondas automáticas).
  Durante uma onda, a cada 20 s ele gasta 20 por soldado em reforços de 2 a 3 que surgem 9 m atrás do ponto
  dele mais perto do nosso esquadrão (do lado oposto a nós), até 6 por onda. Alerta "REFORÇO INIMIGO";
  painel "reforço inimigo N" quando ele tem pontos. Perder pontos endurece as ondas; retomá-los corta a renda.
- Código na tabela `ai` (`ai.tick`, `ai.source`, `ai.reset`; `CFG.AI`); `spawnEnemies` ganhou o 4º
  parâmetro `quiet`. Teste offline: renda por ponto, teto, sem reforço sem onda viva, ponto de origem.
- Validado ao vivo no lote de 2026-10-09 (ver entrada acima).

## 2026-10-08 (manhã) — Visão a partir dos soldados ("olho" do comandante)

- **Como o jogo esconde inimigos:** o `Character_C` do comandante tem `PlayerLOSRasterComponent` +
  `LOSPostProcess`; o código nativo põe `bHiddenInGame` na malha de quem está fora da visão, e o material do
  corpo também some (desocultar a malha pelo Lua só fez aparecer os fuzis que nós anexamos). Mover o
  componente de LOS não muda nada; `AlwaysVisibleRadius` (700) alterado em tempo de execução também não.
  O que conta é a posição do **pawn**: com o comandante a 4 m os inimigos apareceram; atrás de um degrau de
  neve, a 9 m, não (LOS bloqueado pelo terreno, não falta de alcance).
- **Olho:** ao ligar o RTS o comandante vira um olho invisível (`SetActorHiddenInGame`, sem colisão,
  `MOVE_None`, então sem gravidade) e `rts.eyeTick` o leva a cada 0,2 s ao soldado vivo mais perto do foco
  da câmera (sem soldados: a base). A visão do jogo passa a sair de onde a câmera olha, a partir de um
  soldado seu. Ao desligar o RTS ele volta à base, com colisão e caminhada. `CFG.EYE = false` desliga.
- **Base fixa:** `rts.base()` = onde o comandante estava ao ligar o RTS. Depósito de munição, recuo sem
  pontos, referência de ondas/pontos/barreiras e F2 usam a base, não o pawn (que agora passeia).
- Validado: 3 inimigos no degrau de neve, invisíveis com o comandante perto (`fog1.png`), aparecem com um
  soldado ao lado e o olho ligado (`eye3.png`). Em terreno aberto a 33 m a visão da base já alcançava, então
  o ganho é atrás de prédios e relevo e em mapas maiores.

## 2026-10-08 (madrugada, 6) — Trincheiras

- **Ctrl+7 cava uma trincheira** sob o cursor (−20 de mão de obra; máx. 8; recusa encostada em outra):
  malha `pvpFoxhole01` do jogo (buraco de raposa, ~3,4 m), giro aleatório. Quem está dentro (raio 1,7 m,
  qualquer lado) leva 40% dos acertos de tiro e metade da supressão. Granada e morteiro não são
  reduzidos: são o contra. Fuzileiros jogam granada também em alvo entrincheirado.
- **O inimigo se entrincheira:** ao tomar um ponto, abre de graça uma trincheira no centro dele (uma por
  ponto; `CFG.ENEMY_DIG`). Retomar o ponto exige granada/morteiro, e depois a trincheira serve a nós.
  Validado: 4 inimigos em B → "o inimigo tomou o ponto B e cavou uma trincheira", trincheira em B.
  A criação ficou em `fort.place` (tabela `fort`, para não gastar mais locais do chunk).
- Ordem de mover com destino dentro da trincheira: os 4 primeiros ocupam vagas em anel dentro dela, o resto
  forma linha logo atrás (antes a linha centrada no buraco enfiava os 6 lá dentro).
- `seekCover`: soldado parado e exposto vai antes para uma trincheira com vaga a até 4,5 m.
- Validado ao vivo: 4 dentro, 2 atrás (`trench.png`); onda de 6 contra a trincheira: 116 tiros inimigos,
  7 acertos, 106 contidos pela cobertura; 6 abates, 1 perda; os dois de fora entraram sozinhos na vaga.
- Robô com 2 trincheiras em A (`t_bot0t.lua`, `BOT0=t_bot0t.lua sh botloop.sh`): perdeu na onda 10 (89 abates,
  33 perdas). O inimigo jogou 23 granadas (antes ~1): o contra funciona, e a trincheira não desequilibra.
- Teste offline: vagas (4 dentro com 6 selecionados), supressão pela metade, recusas sem cobrar.
  Achado: os testes de recusa da caixa passavam porque `server` ficara falso (recusa por autoridade);
  agora `server = true` antes deles.

## 2026-10-08 (madrugada, 5) — Munição e caixas de suprimento

- **Munição** (só os nossos; "comandante" abaixo virou "base" na entrada da manhã): fuzileiro 40 tiros, MG 150, atirador 15, médico 24 (`CFG.WEAPONS[..].ammo`).
  Sem munição o soldado não atira (alerta a cada 15 s: "leve-o a um ponto seu ou ao comandante");
  painel mostra "SEM MUNIÇÃO N" e "munição baixa N" (<25%). Recarga de 15%/s dentro de um ponto seu
  (que já curava) ou a até 5 m do comandante (senão perder todos os pontos travaria o esquadrão).
  Granadas não gastam munição. O inimigo não tem limite: ele ataca, não sustenta.
- Soldado com munição baixa ganha uma caixinha de munição (a mesma malha, 0,6×) flutuando 1,9 m acima
  da cabeça; some quando recarrega acima de 25% (atualiza a cada 0,5 s, só no modo RTS). A 1,15 m ela
  cobria a cabeça e não se via. Validado: 4 soldados secos → 4 caixinhas (`icon_crop.png`); recarga → ocultas.
- Robô com munição: perdeu na onda 9 (88 abates, 30 perdas; A caiu), dentro do histórico ~50%. "dry 0":
  lutando dentro do ponto A ele nunca secou (1618 tiros repostos). A munição pune avançar longe de
  suprimento, não a defesa. Canal: `CFG` agora exportado (ajuste ao vivo, ex.: `CFG.AMMO_REFILL = 0`).
- **Caixa de suprimentos (Ctrl+6)**: −25 de mão de obra, malha `AmmoCrate` do jogo sob o cursor; por 60 s
  recarrega 25%/s a até 4,5 m (sem cura); máx. 3, recarga 10 s; painel "caixas N". Some sozinha ao fim.
  Validado ao vivo: caixa ao lado do esquadrão, munição zerada → cheia em poucos segundos (`crate.png`).
- Robô de regressão (MG só atira montada, antes da munição): venceu a onda 10 com 4 soldados, 109 abates
  e 26 perdas. O equilíbrio continua apertado.
- `botloop.sh` agora para quando `combat.auto` vira falso (antes procurava "won false", que nunca casava
  por causa da tabulação).

## 2026-10-08 (madrugada, 4) — Dificuldade

- **Shift+F5** alterna fácil → normal → difícil (`CFG.DIFFICULTIES`). Cada nível sobrescreve precisão
  inimiga, crescimento das ondas, inimigos extras por soldado nosso, mão de obra por segundo e chance de
  pinça. "normal" = os valores calibrados com o robô. O painel mostra "RTS (difícil)" e o alerta da nova
  partida diz o nível. F5 sozinho agora ignora Shift (senão Shift+F5 também alternava a ajuda).
  Validado ao vivo (painel e alerta, `diff.png`); teste offline cobre o ciclo e os valores.
- A dificuldade fica salva em `Mods/FoxholeRTS/settings.txt` (`difficulty=N`) e volta ao reiniciar o jogo
  (validado: difícil → reinício → precisão inimiga 0,85; log "dificuldade salva").

## 2026-10-08 (madrugada, 3) — Vitória por domínio

- Com ondas automáticas, segurar **todos** os pontos por 90 s seguidos (`CFG.HOLD_TO_WIN`) vence
  (alerta "VITORIA POR DOMINIO", inimigos removidos, ondas desligam); perder qualquer ponto zera o
  relógio. Painel: "domínio N s". Validado: pontos forçados para nós → painel "domínio 84 s"
  (`dom1_crop.png`); relógio adiantado pelo canal → vitória. Teste offline cobre início, zerar ao
  perder um ponto e vitória.
- Resumo de fim de partida (vitória ou derrota): tempo, ondas, abates, perdas, precisão, morteiros,
  granadas, veteranos vivos e pontos (`sum_crop.png`). Contadores de tiros/granadas/morteiro agora zeram
  em `clearSquad` (antes acumulavam entre partidas). Corrigida a mensagem de derrota por pontos, que
  sobrara como "F11 + Shift+F6".
- **Fila de ordens:** Shift+botão direito / Shift+F7 acrescenta o destino à fila de cada selecionado
  (mantém a posição na formação); quem está parado parte na hora; chegar puxa o próximo; ordem nova
  (mover, atacar, End, Home) descarta a fila. Validado: 3 destinos em L percorridos em sequência em ~5 s.
- Atalhos com e sem modificador (1/Ctrl+1, F4/Shift+F4, F6/Shift+F6, F7/Shift+F7, botão direito/
  Shift+botão direito): não se sabe se o UE4SS dispara só a combinação ou as duas, e não há como testar
  sem entrada real. A versão sem modificador (`plain`) agora ignora o disparo com Shift/Ctrl/Alt
  seguro (lido por `IsInputKeyDown`; sem teclas seguras os seis leem `false`, conferido).
- **Ondas em pinça:** a partir da onda 3, com 6+ inimigos, metade das vezes a onda se divide em dois
  grupos, o segundo a 90–150° da entrada principal (`flankPoint`; `spawnEnemies(at, n, sameWave)` não
  conta onda nova). Validado: 6 ondas forçadas pelo canal → 3 em pinça, grupos em lados opostos.
  Robô com pinça a partir da onda 3 e 50%: caiu na onda 7 (3 pinças). Ajustado para onda 4 e 40%:
  caiu na 10ª, a última (1 pinça; 101 abates, 35 perdas). Placar do robô até aqui: 3 vitórias, 3 derrotas.
- Sons do jogo: `WinResultVictory_Cue`/`WinResultDefeat_Cue` (2D) no fim da partida e `StructureBuild_Cue`
  ao erguer barreira. Os três objetos existem na memória e as chamadas rodam sem erro; se tocam de fato
  só se confirma ouvindo (não há como pelo canal).
- Refactor: 15 estados pequenos (pool de controladores, cache de efeitos, oclusão, estatísticas etc.)
  viraram campos de `S` — locais no topo 172 → 158 (limite do Lua: 200). Partida do robô depois:
  sem erros; ~38 quadros/s; mod 1,8 ms/quadro.
- **Formação orientada:** a ordem de marcha monta, no destino, uma linha de até 4 (`CFG.FORM_WIDTH`)
  com fileiras para trás, girada para ficar perpendicular à direção centro do grupo → destino (última
  fileira centralizada). Antes: coluna de 2 sempre alinhada ao eixo X. Validado: 8 soldados mandados
  na diagonal → duas fileiras de 4 atravessadas à marcha (`form.png`); teste offline confere
  distância, centro e perpendicularidade.
- **Metralhadora monta:** o metralhador (dos dois lados) só atira parado há 1 s (`stillSince`, marcado em
  `halt` e apagado em `moveToward`); montado, acerto ×1,3 e supressão ×1,5. Marchando não atira (antes
  atirava andando como os fuzileiros). Validado: parado há 3 s com inimigos a 17 m → atirando.
- Pontos automáticos conferidos também em HomeRegionC (3 pontos com 24 marcadores cada). Lá a câmera
  ficou atrás de uma estrutura grande perto do início.
- **Oclusão da câmera:** a cada 0,4 s um traço (canal Camera) da câmera ao foco esconde até 4 atores no
  caminho (`SetActorHiddenInGame`), nunca paisagem, personagens ou `InstancedFoliageActor` (um ator só
  guarda toda a vegetação do nível); quem deixa de bloquear reaparece, e tudo reaparece ao sair do RTS.
  Validado em HomeRegionC: a mesma posição antes tomada pela estrutura mostra o pátio, os pontos e o
  esquadrão (`ptsC.png` → `ptsC2.png`).

## 2026-10-08 (madrugada, 2) — Desempenho: de 6 para ~30 quadros/s em combate

- Perfilador por etapa no laço (`step()` com `os.clock`, que no Windows é tempo de parede); `profile()`
  no canal e no F5 dá ms/quadro por etapa.
- Medido com 12 soldados + 15 inimigos: quadro de 150–400 ms; o mod gastava 80–180 ms
  (`pathTick` 71, `squadTick` 54, `enemyTick` 51).
- **Causa 1:** `UEHelpers.GetWorld()` faz `FindAllOf("PlayerController")` a cada chamada (0,3 ms
  medidos) e `now()`, traços e spawns o chamavam centenas de vezes por quadro. Agora `world()`,
  `now()` e `isLocalAuthority()` ficam em cache durante o quadro (`tick.inFrame`; fora do laço —
  teclas e canal — são recalculados), `loc()` também, e `playerController()` usa
  `GameplayStatics:GetPlayerController(world, 0)` (custo ~0; o `UEHelpers.GetPlayerController`
  aceitava qualquer PlayerController, inclusive os dos soldados).
- Também: busca de alvo + traço de visada só a cada 0,25 s (`CFG.SCAN_EVERY`, com variação) ou
  com a arma pronta, em vez de todo quadro; A* com orçamento de 4 ms/quadro em fatias de 4 nós.
- Resultado: mod de 80–180 → **~4 ms/quadro** na mesma cena; quadro do jogo 33–84 ms.
- **Causa 2 (vazamento):** `K2_DestroyActor` não destrói `HeadlessPlayerController` (recusado
  pelo motor; um `StaticMeshActor` destruído some na coleta, o controlador não — 180 controladores
  válidos após ~150 mortes, cada um com `SimPlayerState`, `PlayerCameraManager` e `CameraActor`).
  Após uma partida longa o quadro ia a 350 ms com só 12 soldados. Agora o controlador do morto faz
  `UnPossess` e vai para um pool que `spawnSoldier` reaproveita (com `bIsLocalPlayerController`
  desligado até a nova posse). Partida inteira do robô: 25 controladores no total, 129
  reaproveitamentos; quadro final 60 ms com 12 soldados (era 350); o mod em média 1,5 ms/quadro.
  Desligar o tick dos controladores ociosos não mudou nada: o resto é custo dos personagens do jogo.
- **Armadilha:** ler `hpc.Player` e chamar métodos nele (`GetFullName`/`GetClass`) derrubou o estado
  Lua do UE4SS (canal mudo, jogo vivo); foi preciso reiniciar.
- Balanço conferido depois das mudanças: robô venceu com 19 e 23 perdas (mesma faixa de antes).

## 2026-10-08 (madrugada) — v0.7: morteiro, granadas, veterania, recuo, ajuda, nova partida, balanço

- **Ctrl+5 = morteiro** sob o cursor: 40 de mão de obra, recarga 20 s (painel: "morteiro pronto" /
  "morteiro N s"). Som de artilharia chegando + anel de 8 discos; após 2,5 s, 3 granadas espalhadas
  até 2,5 m do alvo com o efeito `MortarBlast` e o som `ArtilleryLightExplosion_Cue` do jogo
  (achados com `FindAllOf("ParticleSystem"/"SoundCue")`, 82 e 55 candidatos). Dano 75 com queda
  linear até 30% na borda de 3,5 m, só no lado oposto (instigador do próprio lado, como no tiro);
  supressão em todos até 7 m. Validado: salva sobre 5 inimigos parados em posição de tiro → 332 de dano.
- **Morteiro inimigo** a partir da onda 4, a cada 35 s com inimigos vivos, no maior grupo de 3+
  soldados nossos (2 granadas, 3 s de aviso, alerta "MORTEIRO INIMIGO chegando").
  Balanço medido com 6 soldados em formação:
  sem reação, 3 granadas de 90 = 4 mortos; com fuga automática para fora do anel = 0 de dano
  (correm ~18 m em 3 s); quem segura posição (End) ou está suprimido não foge —
  3 granadas = 6 mortos, 2 granadas de 75 = 1 morto e 5 feridos (valor final). O papel do
  morteiro inimigo é desalojar.
- Fim da salva: quem fugiu e não recebeu ordem nova (nem foco, nem End) volta ao lugar com rota
  A* própria (`routeTo`). Em linha reta, 2 de 6 ficavam presos atrás do carro blindado; com a rota,
  desvio final de 0,6–1,9 m da posição original. Partida de 7 ondas com pontos e morteiro: sem erros no log.
- **Ajuda na tela:** segundo TextBlock no widget do painel com as teclas (6 linhas, fonte 13); aparece
  por 40 s ao ligar o RTS e F5 alterna (além de registrar o status). Validado em captura: visível
  logo após o autostart (`help1.png`) e escondida depois do prazo (`help2_crop.png`). F5 com teclado
  real ainda não testado.
- **Veterania:** o tiro que zera o HP credita o atirador (`credit`); a cada 2 abates sobe um nível
  (máx. 3), +10% de precisão por nível, nos dois lados. Alerta "fuzileiro promovido a veterano 1",
  painel "sel. 6, 1 vet.", status lista abates por soldado. Validado: onda de 5 → créditos
  1,2,1,0,0,1 (soma = 5 abates) e promoção do 2º fuzileiro.
- **Recuo (Home):** selecionados correm ao ponto nosso mais próximo do grupo (sem ponto, ao
  comandante) com rota A* própria, não param para atirar e levam metade dos acertos
  (`CFG.RETREAT_HIT`); chegar ou nova ordem encerra. Ponto nosso é posto de socorro: dentro do anel,
  sem supressão, +2 HP/s (`CFG.POINT_HEAL`). Validado: 4 feridos (50–62 HP) a ~15–19 m de A
  chegaram em ~4 s (o metralhador, mais lento, em ~6 s) e subiram ~2,4 HP/s lá. Achado no teste:
  o médico chegava e saía de novo atrás do metralhador ainda a caminho, e morria; agora o médico
  não sai atrás de quem está recuando.
- **Nova partida (Shift+F6):** limpa tudo, esquadrão de 6 (`CFG.START_SQUAD`), ondas automáticas e três
  pontos; alertas de vitória/derrota apontam para ela. Validado pelo canal duas vezes seguidas
  (6 soldados, 3 pontos, ondas ligadas, onda 0).
- **Granadas:** fuzileiro (dos dois lados) com o alvo atrás de cobertura baixa a até 18 m lança uma
  granada em vez de atirar (recarga 18 s por soldado; explode em 1,4 s a até 1,5 m do alvo; dano 55
  com queda até 3 m, sem traço — a cobertura não protege; supressão até 5 m; abate credita o
  lançador). Efeito `GrenadeBlast`, sons `GrenadePinPull_Cue` e `HELaunchedGrenadeHit_Cue` (este
  escolhido pelo nome, não conferido de ouvido). Validado: 3 barreiras com 4 inimigos atrás → 2
  granadas, 272 de dano, onda eliminada (`gr1.png`); status registra lançamentos e dano por lado.
  Granada inimiga validada: 4 soldados nossos em segurar posição atrás de 3 barreiras, 4 inimigos a
  15 m → 2 granadas, 303 de dano, 2 mortos. Sem projétil visível não há como reagir em 1,4 s; dano
  baixado de 55 para 45 (texto acima mantém o valor original do teste).
  Projétil visível: malha `/Game/FX/Mesh/Grenade01` (3×) voa em arco (2,5 m de altura) do lançador ao
  alvo durante a espoleta e some na explosão; conferido em captura com a espoleta alongada pelo canal
  (`gfly2.png`: granada e sombra deslocada no meio do caminho).
- Ajuda na tela ancorada no canto inferior esquerdo: no alto ela cobria a caixa de alertas do jogo
  (`help3.png`).
- **Jogador-robô** pelo canal (`t_bot0.lua` + `t_bot.lua` a cada 10 s: recruta com ≥45 de mão de obra
  no ponto A, morteiro no centro dos inimigos, mantém todos em A; sem barreiras, recuo ou cobertura):
  - balanço antigo: venceu as 10 ondas com 3 perdas; o morteiro inimigo **nunca disparou** (o relógio
    zerava a cada onda eliminada, antes dos 17 s iniciais) — corrigido, o relógio só zera abaixo da onda 4;
  - ondas 0,5→0,8 inimigo/onda e teto 10→14: venceu de novo com 3 perdas (12 soldados = bola de neve);
  - + `CFG.WAVE_SQUAD_SCALE` 0,4 inimigo por soldado nosso vivo, teto 16, precisão inimiga 0,6→0,7:
    perdeu na 10ª onda (108 abates, 31 perdas; o inimigo tomou os três pontos). Valor mantido: um
    jogador usando barreiras, recuo e cobertura deve ir além do robô. Nenhum erro no log nas três partidas.
- **Avanço em lances (IA):** inimigo avançando com supressão ≥ 0,25 corre para a cobertura mais
  avançada por perto (mesma busca de `seekCover`), espera 2,5 s e segue; antes avançava reto até o
  alcance. Validado: 6 barreiras no caminho, onda de 6 vinda de 38 m → 5 lances e 12 idas à cobertura
  (status mostra "lances inimigos").
  Robô com lances: venceu as 10 ondas com 108 abates e 22 perdas (12 granadas nossas contra inimigos
  abrigados nos lances). Duas partidas do robô: uma derrota (31 perdas) e uma vitória (22 perdas).
- **Bug corrigido:** `focusOn(0/0)` (teste com lista vazia) deixou a câmera em NaN e a tela preta
  para sempre — com a posição atual NaN o `K2_SetActorLocation` move por um delta NaN. Agora
  `focusOn` ignora NaN e `placeCamera` recria a câmera se a posição dela for NaN (validado:
  câmera forçada a NaN voltou a (9988,-24935,2662) com imagem). `callMortar` também recusa NaN.

## 2026-10-07 (noite, 13) — Pontos de controle (v0.6)

- Ponto = anel pontilhado laranja (24 discos pequenos, raio `CFG.POINT_RADIUS` 500) +
  estandarte enrolado do dono no centro, 3× (`BannerTWPickup` azul = jogador/Wardens,
  `BannerTCPickup` verde = Colonials; neutro sem estandarte). Testados antes: disco único
  de 10 m (cortado pelo relevo, cobria o terreno) e materiais `FlagHanging*` no disco
  (renderizam como bandeira rasgada, não como cor) — descartados.
- Captura: progresso em [-1, 1]; só um lado no anel empurra (1 soldado = 10 s de neutro a
  dono, até 3 somam); os dois lados = disputado (congela); vazio = volta devagar ao dono.
  O dono perde o ponto quando o progresso cruza 0. Cada ponto nosso rende +0,5/s de mão de
  obra. Inimigo com todos os pontos = derrota (com ondas automáticas).
- IA inimiga fora de combate vai ao ponto mais próximo que ainda não domina e segura no
  centro (60% do raio); inimigo humano mais perto que o ponto continua tendo prioridade.
- Shift+F4 sem pontos cria três (frente e flancos do esquadrão, 1400–2400 cm), em chão
  plano e livre; J cria um ponto sob o cursor (máx. 5); F11 remove. Painel:
  `pontos 1/3 [A+ Bx Co]` (+ nosso, x inimigo, o neutro; % durante a captura).
- Achados de traço: o canal Visibility (`groundZ`) **atravessa veículos** (Truck24);
  `LineTraceSingleForObjects` com tipos {WorldStatic 0, WorldDynamic 1} os acerta, mas
  também acerta volumes invisíveis `BPNoBuild_C` (BoxComponent, topo Z=4746) — `surfaceZ`
  ignora hits em Box/SphereComponent (cache `surfaceIgnore`) e refaz o traço.
- Validado no jogo: 3 pontos criados longe dos caminhões; esquadrão capturou A em ~3 s
  (6 soldados); onda 1 tomou B a caminho e engajou o esquadrão; 3 ondas com A nosso e B
  inimigo, painel e estandartes conferidos em captura (`pts6.png`).
- Cabeça de ponte: ponto dominado pelo inimigo a mais de 15 m do esquadrão vira a entrada da
  próxima onda (o mais distante; alerta "entrada pelo ponto B"). Validado: B forçado para o
  inimigo pelo canal → onda 5 nasceu em B (11529,-22835). Na mesma rodada o esquadrão caiu,
  o inimigo tomou A e C e a derrota por pontos desligou as ondas.
- Reforço avançado: Ctrl+1..4 com o cursor dentro de um ponto nosso faz o recruta nascer
  nele (`recruit(role, at)`; `spawnSquad(n, role, at)`). Validado pelo canal: recruta em B
  nasceu a ~180 cm do centro; sem ponto, ao lado do esquadrão como antes. O caminho pelo
  cursor depende do mouse real (não testado).
- Testes offline: progresso/disputa/perda/volta, objetivo do inimigo, derrota por pontos,
  entrada da onda por ponto inimigo; tecla J sem conflito.
- Balanço: regeneração base 1,5/s → 1,0/s (`CFG.MANPOWER_RATE`); com um ponto dominado volta a
  1,5/s. Na partida de teste a mão de obra passava a maior parte do tempo no teto de 200.
- A* (`kneeClear`) passou do canal Visibility (0) para `CFG.MOVE_CHANNEL` = 1 (Camera).
  Varreduras medidas: Camera acerta caminhões (BoxComponent), motos, prédios e barreiras e
  não acerta os volumes BPNoBuild; o canal 4 acerta veículos mas atravessa as barreiras;
  Visibility atravessa veículos. Rota (11000,-24900)→(11000,-27900) através da fileira de
  caminhões: antes linha reta (0 nós), agora desvio pelo vão (29 nós); 4 soldados chegaram
  em <8 s (`route1.png`). Tiro e cobertura continuam no Visibility (caminhão não para bala
  nem conta como cobertura — coerente entre si).

## 2026-10-07 (noite, 12) — Vitória e dificuldade crescente

- Ondas automáticas agora têm fim: eliminar a onda `CFG.WAVES_TO_WIN` (10) = vitória
  (alerta de 15 s, painel "VITÓRIA", +30 de mão de obra, ondas desligam). Religar as
  ondas depois de vencer começa nova campanha (onda 0).
- Precisão inimiga ×(1 + 0,04·(onda−1)), teto ×1,5 (`CFG.WAVE_ACC_GROWTH/CAP`).
- Painel mostra "onda X/10" com as ondas automáticas ligadas.
- Validado no jogo: campanha iniciada na onda 9 pelo canal; a 10ª (8 inimigos) chegou
  após o intervalo e foi eliminada → `won=true`, `auto=false`, alerta e painel
  conferidos em captura (`win_crop.png`).
- `test_orders.py`: vitória na última onda, onda intermediária só agenda a próxima,
  religar após vitória reinicia a campanha.

## 2026-10-07 (noite, 11) — Médico e limite de 200 locais

- Reflexão em `SimCharacter`: `Health`/`MaxHealth`, `bIsBleeding` (+`OnRep_IsBleeding`),
  `BleedDamagePerSecond` 1,0, `BleedMinDamageReq` 25, `ResetWoundedStateThreshold` 85,
  `OnRep_Health`. Escrever `Health` + `OnRep_Health` cura e se mantém (60→90).
  Dano com o próprio controller como instigador não aplica (tratado como fogo amigo).
- Classe médico: pistola (`PistolBasic`), 30 de mão de obra, Ctrl+4; 4º e 12º do
  esquadrão (inimigos também). A cada 1,5 s cura 12 HP e estanca o mais ferido a ≤3,5 m;
  ferido a ≤12 m e médico livre → vai até ele. No jogo: onda de 4 vencida 4×0, médico
  aliado curou 156 HP (inclusive a si mesmo 56→90), médico inimigo 38. F5 mostra o total.
- **Limite do Lua: 200 locais por chunk.** O `main.lua` chegou a exatamente 200 e o
  médico estourou ("too many local variables"). As 79 constantes MAIÚSCULAS de topo
  foram para a tabela `CFG` por transformação mecânica (código, não strings/comentários);
  sobram ~80 locais. Validado no jogo depois (autostart, câmera, combate).
- `test_orders.py`: médico cura o mais ferido, estanca, respeita o período e anda até
  ferido distante.

## 2026-10-07 (noite, 10) — v0.5: teclas sem conflito com o jogo

- Lidos os 138 mapeamentos padrão (`Default__InputSettings.ActionMappings/AxisMappings`;
  `pc.PlayerInput.ActionMappings` vem como TrivialObject). Conflitos reais do mod:
  B = Build (menu de construção), H = Open Callouts Menu, F8 = Toggle Interface,
  Shift+1–7 = AdminCommand1–7, botão esquerdo = Fire, direito = Aim, PageUp/Down =
  Spectate/Move Up (inofensivos fora de espectador/veículo), 1/2/3 = Equip.
- Teclas livres no jogo (sem modificador): F2–F7, F9–F12, J, K, Home, End, Insert,
  Delete. Novo mapa: recrutar Ctrl+1/2/3 (Ctrl+n só troca assento em veículo), barreira
  K, segurar End, limpar F11. 1/2/3 mantidos (só equipam o comandante parado).
- Modo RTS desliga a entrada do pawn do comandante (`DisableInput`; religa ao sair),
  para o clique esquerdo não disparar Fire. Não verificado com mouse real.
- `test_orders.py`: teste de regressão compara as teclas registradas pelo mod com a
  lista de mapeamentos do jogo (falha em qualquer colisão fora das aceitas).
- v0.5 carregou no laboratório com os novos nomes de tecla (banner no log).

## 2026-10-07 (noite, 9) — Construção de barreiras (tecla B)

- Candidatas medidas por perfil de traços horizontais (40–150 cm):
  `BPSandBagWallStatic_C` bloqueia até ~2,25 m (corta a visada; não serve);
  `SandbagSmallPile_C` só ~40 cm; o divisor de concreto do pátio é um
  `StaticMeshActor` com `OCourseDividers_01` (~2,7 m, topo ~1,24 m): bloqueia 40–100,
  libera 130–150 = cobertura baixa exata do modelo de tiro.
- `buildAt(p)`: `StaticMeshActor` + essa malha (Movable), virado de frente para o
  inimigo mais próximo (sem inimigos: direção esquadrão→ponto); custa 15 de mão de
  obra, máximo 30, recusa com soldado a <1,8 m; F8 remove; painel mostra "barreiras N".
  Tecla B (ainda não testada com teclado real; não sei se o jogo usa B no modo RTS).
- Validado no jogo: 3 barreiras a 3,5 m do esquadrão antes de uma onda de 4:
  mão de obra 63→18; 44 de 47 tiros inimigos barrados; 4 abates, 0 perdas; 7 rotas
  A* inimigas desviando das barreiras. Captura `build7_small.png`.
- `test_orders.py`: recusas sem mão de obra e com soldado no local, sem cobrar.

## 2026-10-07 (noite, 8) — Segundo mapa (HomeRegionC) e "Code of Conduct"

- Mapas no índice do PAK (lido só o final do arquivo, sem extrair): `HomeRegionW`,
  `HomeRegionC`, `MainMenu` e ~40 hexes em `Maps/Master/*Hex` (+ proxies).
- Mapa do laboratório configurável: 1ª linha de `Mods/FoxholeRTS/map.txt`
  (ex.: `/Game/Maps/HomeRegionC`); sem arquivo, HomeRegionW. O autostart detecta o
  carregamento pelo nome do mapa escolhido. Âncoras do comandante: +`BPArmoredCarC_C`
  e `PlayerStart` como último recurso.
- **HomeRegionC validada:** sessão local, comandante em (−7447, 15947, 230),
  recrutamento, onda de 5, combate (4 abates, 0 perdas), 5 idas à cobertura,
  6 rotas inimigas, sem erros no log. Muitos tiros barrados (145/167 aliados) porque
  havia uma barreira baixa entre os grupos (conferido na captura `mapc1_small.png`).
  `map.txt` removido depois; o laboratório voltou ao HomeRegionW.
- **"Code of Conduct":** não precisa de ação. Some sozinha ~1 min depois do
  carregamento; só aparecia em capturas tiradas logo após relançar. Reflexão no
  controller não mostrou função específica para ela.
- **Hex grande validada: `Maps/Master/DeadLandsHex`.** Carregou em ~17 s via
  `?listen` (4,2 GB de memória), comandante em (15986, 38998, 288), onda de 5
  vencida (5 abates, 0 perdas, 1 soldado com 1 HP), sem erros no log.
  Aparece o painel "Introdução ao Foxhole" (tutorial de primeira vez) por cima de
  tudo: é Slate nativo (sem UserWidget; nenhuma função/propriedade intro/tutorial
  no controller), sem flag nos `.ini`. Fecha com cliques na seta, só com mouse real.
  `map.txt` removido depois; laboratório de volta ao HomeRegionW.

## 2026-10-07 (noite, 7) — Inimigos com rota

- Inimigo que avança reavalia a cada 4 s: `planStart` só abre A* se a reta
  (linha + esfera) até o aliado mais próximo estiver bloqueada; segue os waypoints
  e o último trecho vai direto ao alvo vivo. Orçamento global de 40 nós/frame para
  todos os trabalhos; ordens do jogador entram na frente da fila.
- `enemies` passou a ser declarada antes do planejador; contador `routeStats`
  (F5: "rotas A* aliados/inimigos"). `check_globals.py` pegou um uso de `combat`
  antes da declaração nesse meio-tempo.
- Medido: inimigo do lado de fora da barreira, aliado (em H) a ~23 m dentro do
  pátio. Rotas inimigas = 1; o inimigo contornou de (8325, −27669) até
  (8969, −27360) e parou ao entrar no alcance com visada (17,6 m), com 1 waypoint
  ainda pendente. Dois testes anteriores não exigiram rota (visada livre por
  cima da barreira / por ângulo): o inimigo entrou em combate antes.

## 2026-10-07 (noite, 6) — Caminhos (A*) sem NavMesh

- Ordem de marcha planeja uma rota para o grupo: linha reta se livre; senão A*
  em grade de 1,5 m (margem 20 m, até 2500 nós), arestas testadas por varredura
  de esfera (raio 32 cm a 75 cm do chão; linha só nas arestas da origem/destino) e
  desnível ≤60 cm por célula; chegada aceita vizinha do destino com linha livre;
  rota encurtada. Cada soldado segue os mesmos waypoints (raio 70 cm) e vai ao seu
  lugar na formação. Sem rota: linha reta com o desvio antigo.
- Erros no caminho até funcionar (medidos no jogo):
  1. Traço de linha não tem a largura do corpo: rota rente à barreira passava e o
     soldado ficava na quina (raio de waypoint 120 cm piorava). → esfera + 70 cm.
  2. Com esfera, destino rente ao muro ficou sem célula alcançável. → chegada na
     vizinha com linha livre.
  3. Margem de 12 m deixava a abertura da barreira fora da busca; margem maior
     custa ~1 ms/nó. Corrotina falhou: **UE4SS não aceita UFunction dentro de
     corrotina** ("lua state has no instance inside lua_instances"). → A* em estado
     explícito (`planStart`/`planStep`), 40 nós por frame; soldado espera parado.
- Resultado: da neve (8550, −27279) ao canto interno (9000, −26500), com a barreira
  no meio: rota de 6 waypoints em 341 nós (~9 frames), chegada em ~4,5 s pela
  abertura. Antes: preso, ou chegada por sorte em ~12 s.
- `test_orders.py`: muro sintético em X=500; rota síncrona contorna com todos os
  trechos livres; fluxo assíncrono entrega waypoints após os ticks.

## 2026-10-07 (noite, 5) — Ordem de ataque e busca automática de cobertura

- **Ataque:** botão direito/F7 a até 2,5 m de um inimigo vivo = ordem de ataque
  (`m.focus`). Os selecionados avançam até ter alcance e visada, param e atiram só
  nele; no caminho atiram no mais próximo. Marcha e H cancelam. No jogo: com dois
  inimigos (12 m à frente e 18 m à direita), atacar o de 18 m o derrubou primeiro.
- **Cobertura automática:** aliado parado, sem ordem e sem H, com inimigo ao alcance
  e exposto, procura a cada 2 s, em anéis de 1,5/2,8/4 m, o ponto onde o traço do
  olho do inimigo até a cintura é bloqueado e até os olhos passa, mesmo chão (±80 cm)
  e caminho livre na altura do joelho. Sem a checagem do joelho ele escolhia o
  outro lado do muro (inalcançável). H agora segura posição (`m.hold`): sem busca.
- Validado: varredura de traços (`t_cov10.lua` no lab) achou ponto exposto com
  abrigo a ≤4 m; aliado posto em (9250, −27500) foi sozinho para (9204, −27075),
  junto à quina da barreira; o inimigo teve 3 de 4 tiros barrados, 0 acertos, e
  morreu. Captura `D:\tools\foxhole-lab\cov11_small.png`.
- Achado de geometria: a barreira de concreto de HomeRegionW é alta (impacto a
  ~1,8 m) e cobre uma faixa larga do pátio contra inimigos distantes.
- **Inimigos também buscam cobertura:** em posição de tiro e não presos pela
  supressão, a cada 2 s procuram abrigo (mesma rotina, contra o esquadrão); não
  atiram enquanto se movem para ele. Teste espelhado (aliado em H na neve, inimigo
  exposto): o inimigo foi para (9203, −27076) e os tiros do aliado passaram a ser
  barrados (4 de 6 no total; o único acerto foi antes de ele se abrigar).
- `test_orders.py`: foco só em selecionados vivos, ataque a morto ignorado,
  marcha/H cancelam foco, H liga hold e nova ordem desliga.

## 2026-10-07 (noite, 4) — Supressão e cobertura

- Supressão 0..1 por soldado: todo tiro contra ele soma `weapon.supp` (fuzil
  0,12, MG 0,20, atirador 0,30), acertando ou não; decai 0,35/s. Efeitos: precisão
  ×(1−0,6·s), velocidade ×(1−0,5·s); inimigo com s ≥ 0,7 fica preso no lugar
  (continua atirando).
- Cobertura baixa: com a visada dos olhos livre, traço do olho do atirador até a
  cintura do alvo (centro −20 cm ≈ 70 cm do chão) bloqueado = alvo coberto:
  acerto ×0,5, e o tiro perdido levanta poeira no obstáculo. Contador
  `combat.covered` no F5.
- Validado no jogo. Combate 7×6 em campo aberto: supressão do inimigo chegou a
  0,97–1,0 com ele parado; precisão inimiga sob fogo ~17%; cobertura 0 (esperado).
  Duelo com o inimigo atrás de uma barreira de concreto (achada por varredura de
  traços: S=9000,−26500 / T=8550,−27279 em HomeRegionW): o aliado exposto acertou
  1 de 9, com 8 barrados pela cobertura; o inimigo coberto, 0 barrados.
- `test_orders.py`: acúmulo, teto e decaimento da supressão com relógio falso.

## 2026-10-07 (noite, 3) — Painel de status fixo no HUD

- O HUD do Foxhole é Slate nativo: `FindAllOf("TextBlock")` = 0; o único UMG vivo é
  `CrosshairWidget_C` (cursor, fora do viewport). `ClientAlertMessage` empilha
  (mais novo em cima), não serve para status contínuo.
- Solução: `WidgetBlueprintLibrary:Create` de outra instância de
  `CrosshairWidget_C`, imagem colapsada, `TextBlock` criado com
  `StaticConstructObject(TextBlock, WidgetTree)` e `CanvasPanel:AddChildToCanvas`,
  `AddToViewport(50)`. Fonte: Roboto da engine; `tb.Font.Size = 16` aplica;
  acentos (ã, ç, á, —) renderizam. Sombra via `SetShadowOffset`.
- Linha: mão de obra, esquadrão (selecionados), onda/inimigos/abates/perdas e
  contagem da próxima onda; atualiza a cada 0,25 s só se o texto mudou; sai do
  viewport com o RTS desligado. Validado por captura durante onda.
- Globais criadas em `cmd.lua` não persistem entre comandos (env novo a cada
  execução); guardar estado de teste no próprio mod se precisar.

## 2026-10-07 (noite, 2) — Seleção por soldado com marcador

- Seleção agora é por soldado (`m.sel`). Teclas 1/2/3 continuam (grupo 1, 2,
  todos). Botão esquerdo: clique seleciona o soldado vivo mais perto (≤150 cm);
  arrastar (≥120 cm no chão) seleciona por caixa no plano X/Y; Shift soma/alterna;
  clique no vazio limpa. Sondagem de `LeftMouseButton` no loop por frame, porque
  `RegisterKeyBind` só vê o apertar. Novos soldados entram selecionados se todos
  já estavam.
- Marcador: `StaticMeshActor` com `/Engine/BasicShapes/Cylinder` achatado
  (0,9×0,9×0,02), material do jogo `BuildGhostHighlight` (disco laranja), sem
  colisão, preso ao pawn (KeepWorld). Testados e descartados: `GrenadeAimMesh`
  visível (não aparece), custom depth/stencil (sem contorno no pós-processo do jogo),
  material padrão do cilindro (cinza, some no chão).
- Validado no jogo pelo canal: caixa na 1ª fileira = 2, Shift+clique soma o 5º
  = 3; discos só nos 3 (captura); ordem move só os 3 e os discos acompanham;
  F10 desligado esconde todos e religado mostra só os selecionados; mortos têm o
  disco destruído. Clique/arrasto com mouse real **não testados** (sem acesso à
  janela).
- `tools/check_globals.py`: aponta nome usado antes do `local` (vira global nil)
  ou nunca declarado. Pegou o caso `spawnSquad`→`syncMarkers` (resolvido com
  declaração antecipada). Roda no `restart.sh` antes de publicar.
- `test_orders.py`: seleção por clique/caixa/Shift coberta.

## 2026-10-07 (noite) — Decisão: totalmente offline, modelo próprio; v0.4

- **Decisão do usuário:** nada de integração com servidor; remodelar o jogo
  offline. Na prática a sessão já é local (listen server próprio + regra de
  firewall de saída). Mantida a checagem de posse do Steam (IPC local, não é
  rede; não contornar DRM). Steam pode ficar em modo offline.
- Consequência: rifles reais via `ServerTakePickup`/inventário saem do caminho
  crítico. Armas passam a ser do nosso modelo (perfil de tiro + malha do jogo).
- **Bug da tecla H achado no jogo e corrigido.** Medido: H zerava a velocidade,
  mas 1,5 s depois os soldados tinham andado 6–10 m (vel. até 333). Causa: com
  atrito/frenagem 0 (spawnSoldier), a entrada de movimento já enfileirada
  reacelerava o pawn e `halt()` só agia uma vez (`m.halted`). Agora `halt()`
  chama `ConsumeMovementInputVector`, freia sempre que há velocidade, e o tick
  aplica `halt()` a todo soldado sem ordem. Reteste no jogo: posição idêntica por
  3 s; nova ordem retoma a marcha e para no destino. `test_orders.py` cobre a
  frenagem repetida (PASS).
- **v0.4: classes de soldado.** Tabela `WEAPONS` (fuzileiro, metralhador,
  atirador) com alcance/cadência/precisão/dano/velocidade; 3º e 7º do grupo são
  metralhadores, 6º atirador. A malha da arma vai no componente `WeaponMesh` do
  personagem (`SetSkeletalMesh`); Warden: `SK_RifleW`, `SK_MGW`, `SniperRifle`;
  Colonial: `SK_RifleCarbineC`, `SK_MGC`, `SK_SniperRifleC`. Validado no jogo:
  composição 4/2/1 e inimigos 4/1/1, metralhador a 375 (75% de 500), combate
  6x7 terminou 5 abates/5 perdas; o atirador inimigo parado a ~30 m fica fora do
  alcance dos fuzis (exige ordem de avanço).
- `p.WeaponMesh` NÃO é propriedade (UE4SS devolve TrivialObject): pegar o
  componente por nome via `K2_GetComponentsByClass`. Arrays de retorno vêm como
  tabela Lua de wrappers (`v:get()`), não TArray com `ForEach`.
- **Crash (UE4SS.dll AV 0x2ace27):** probe que lia `MasterPoseComponent`/
  `AnimClass` do `WeaponMesh` derrubou o jogo; `pcall` não pega AV. Dump em
  `D:\tools\foxhole-lab\crash-v04probe\`. Não ler essas propriedades.
- **Arma na mão:** sem reanexo o `WeaponMesh` fica na origem do corpo (rel=0,
  escondido nos pés). `K2_AttachToComponent(pawn.Mesh, "hand_r", Snap×3)` põe
  a arma na mão; validado por captura desde o spawn (fuzil e MG Warden) e por
  leitura nos inimigos (`SK_RifleCarbineC`/`SK_MGC`/`SK_SniperRifleC` em hand_r).
  (Uma leitura apressada de captura inverteu isso antes: câmera olha para +X, o
  soldado de cima é o de maior índice.)
- **Economia (v0.4):** mão de obra começa em 60, regenera 1,5/s (máx. 200),
  +8 por abate, +30 por onda eliminada (substitui os 2 soldados grátis de
  reforço). Shift+1/2/3 recruta fuzileiro (20) / metralhador (35) / atirador
  (45). Derrota nas ondas só sem soldados E sem mão de obra para um fuzileiro.
  `SQUAD_MAX` 8→12. Validado pelo canal: custos descontados, recusa sem cobrar,
  regeneração ≈1,5/s medida, bônus de 6 abates somado. `test_orders.py` cobre
  as recusas (sem mão de obra, esquadrão cheio, sem autoridade).
- Ainda não testado com teclado real: Shift+1/2/3. Não sei se o UE4SS dispara
  também a tecla 1/2/3 sem modificador (selecionaria um grupo junto; inofensivo).
- Teste de teclado real via computer-use: acesso à janela negado pelo usuário;
  teste de Shift+1/2/3 fica com o usuário (roteiro na resposta da sessão).
- Próximos candidatos (feitos depois nesta noite: seleção, painel, supressão/cobertura).
  Ataque a alvo e cobertura automática também feitos (entrada "noite, 5").
  Pendentes: teste com teclado/mouse reais (inclui fechar a introdução nas hexes).
- Inimigos fora da linha de visão do comandante não são desenhados (LOS do
  próprio jogo, `LOSRasterComponent`): já funciona como névoa de guerra.

## 2026-10-07 — Regra de saída instalada pelo usuário e conferida

- Usuário criou `FoxholeRTS Lab - Block Outbound` em PowerShell administrador.
- Conferência independente com `netsh advfirewall firewall show rule` confirmou:
  habilitada, saída, bloquear, todos os perfis, qualquer protocolo/IP, executável
  exato `D:\FoxholeLab\Foxhole\War\Binaries\Win64\War-Win64-Shipping.exe`.
- Resolvida a pendência da regra específica de rede; esta conferência não é
  teste funcional do mod. Próximos testes: probe de inventário e tecla H.

## 2026-10-07 — Isolamento reavaliado e holder confirmado

- `netsh advfirewall show allprofiles state` funcionou: três perfis ligados.
  Listagem de regras filtrada por Foxhole/War-Win64 encontrou apenas permissões
  de entrada para War.exe oficial; nenhuma regra específica bloqueando a cópia.
  Não houve lançamento. Foi solicitada ao usuário uma regra de saída para o exe
  exato do laboratório, com comando e conferência em UNIVERSAL_MODDER_NOTAS.md.
- Assembly de 0x140a5c3e0 confirmou RCX preservado até a chamada 0x140a622d0:
  o holder é repassado, ao contrário do que parecia no pseudocódigo. Não é
  evidência de aquisição do item. RIFLES_INVESTIGACAO.md atualizado.
- Próximo passo depende da medição no jogo: confirmar isolamento, executar o
  probe de inventário e validar H. Não acrescentar novos hooks por hipótese.

## 2026-10-07 — Rifles: fluxo estático e diagnóstico não destrutivo

- Retomada com foco em armas reais, sem substituir por novos efeitos simulados.
- Confirmado thunk -> slot +0xc20 -> wrapper -> slot +0x9d0 -> rotina local de
  pickup. Há guarda de atividade em +0x12e0 antes do caminho de sucesso.
- Encontrada limitação do helper de vtables: PlayerCharacter sobrescreve a tabela
  depois do construtor base; o helper retorna a base. Comparados os dois slots:
  mesmos destinos, logo isso não explica sozinho o inventário vazio.
- Criado `RIFLES_INVESTIGACAO.md` com fontes e hipóteses delimitadas, e
  `tools/probe_inventory.lua`, somente leitura, para medir pré-condições e os
  dois arrays (inventário/equipamento). Nenhuma RPC nova ou alteração de flags.
- Decompilações/PE permaneceram no laboratório; nenhum lançamento ou input.
- `test_inventory_probe.py` PASS após corrigir escape de newline no próprio teste:
  leitura dos arrays, campos indisponíveis, pawn inválido, recusa de contextos
  não locais. `publish check` continua PASS (3 arquivos, 0 falhas/avisos).
- `um kb search inventory` revelou UnicodeEncodeError em stdout cp1252; com
  PYTHONIOENCODING=utf-8 passou. Solução registrada no guia de ferramentas.

## 2026-10-07 — v0.3.1: parada por grupo e documentação do toolkit

- Nova tecla H: cancela marcha dos selecionados, zera velocidade e desvio, sem
  desativar combate automático. Exposta como `stopSelected()` no canal local.
- Novas ordens descartam o desvio anterior e ignoram pawns mortos/inválidos.
- `issueMove` e o loop por frame agora recusam cliente remoto, servidor dedicado
  e menu pelo predicado existente. Isso não substitui isolamento de rede.
- Corrigido comentário que afirmava sucesso do pickup: só evitar o crash foi observado.
- `tools/test_orders.py`: passou sintaxe, seleção, parada, retomada, tecla H com
  RTS inativo, mortos/inválidos, esquadrão vazio e travas de autoridade, via lupa 2.8.
  São mocks; física, input real e combate após parada ainda precisam de teste em jogo.
- Skills usadas: mod-any-game, reverse-engineering, game-automation e playbook Unreal.
  `um kb search foxhole` recuperou a nota; `um publish check` inicialmente apontou
  README ausente; README adicionado ao pacote.
- Guia de uso/avaliação: `UNIVERSAL_MODDER_NOTAS.md`, com comandos e limitações.
- Sem processo War encontrado. Consulta de firewall negada pelo Windows;
  isolamento não pôde ser confirmado. Não relancei, não copiei v0.3.1 para o lab
  e não usei input. Próximo passo: confirmar isolamento e seguir o teste H do guia.
- Rifles reais seguem pendentes; não repetir t_pk3 como se fosse solução.
- Check final: `um publish check` PASS (3 arquivos, 0 falhas/avisos).
  `um kb check --index` FAIL: índice global desatualizado (60 notas verificadas);
  registrado no guia sem modificar a base compartilhada.

## 2026-10-06 — Planejamento inicial

- Objetivo: investigar e desenvolver um mod que permita jogar Foxhole como RTS.
- Preferência do usuário: criar as ferramentas necessárias no próprio mod; não substituir automaticamente a proposta por um jogo independente.
- Pasta: `D:\GitHub\foxhole-rts`.
- Toolkit de apoio: `D:\GitHub\universal-modder`.
- Instalação do jogo em andamento, conforme informado pelo usuário. Caminho e versão ainda não verificados.
- Nenhum arquivo do jogo alterado, loader instalado ou teste em jogo realizado.
- Busca na base local: `python -m um kb search Foxhole` não encontrou notas.

### Evidência e limite atual

A FAQ oficial consultada informa que Foxhole é multiplayer online, não oferece single-player com bots e não tem suporte oficial a mods; menciona mods visuais sem vantagem em jogo.

Fonte: https://www.foxholegame.com/faq (consultada em 2026-10-06).

Isso não prova impossibilidade técnica de uma conversão, mas tampouco comprova uma rota para RTS. Ainda precisamos demonstrar um ambiente isolado e autorizado com controle da simulação. Não presumir que um servidor privado, SDK ou modo offline esteja disponível.

### Próxima ação

Quando o usuário confirmar que a instalação terminou, localizar e inspecionar o jogo em modo somente leitura. Seguir `PRIMEIROS_PASSOS.md`.

### Decisões em aberto

- ~~Experiência desejada~~ → **solo contra IA** (decidido em 2026-10-06).
- ~~Controle por soldado ou por esquadrão~~ → **por esquadrão** (decidido em 2026-10-06).
- Rota técnica e disponibilidade de ambiente de testes isolado.

### Limites de trabalho

- Não interferir em servidores oficiais nem contornar anti-cheat, DRM ou verificações de propriedade.
- Pedir autorização antes de instalar loaders, dirigir mouse/teclado, alterar registro ou publicar.
- Fazer backup antes de alterações e lançamentos modificados.
- Manter decompilações e assets extraídos fora do repositório; não redistribuir arquivos do jogo.

## 2026-10-06 — Instalação concluída e primeira inspeção

- Usuário confirmou o término da instalação.
- Scan somente leitura localizou `D:\SteamLibrary\steamapps\common\Foxhole` (Steam 505460).
- Build do manifesto: `25730371`; assinatura da engine: `UE4+Release-4.24`; dois PAKs detectados.
- Nenhum loader ou anti-cheat detectado pelo scan; ausência de detecção não significa ausência de proteção.
- Diretórios locais `Foxhole` e `War` em LOCALAPPDATA não encontrados; saves/config/logs não confirmados.
- Criado `MODDING_PLAN.md` com evidências, limites e próximas verificações.
- Não abrimos nem alteramos o jogo. A viabilidade da simulação RTS continua não demonstrada.

## 2026-10-06 — Pesquisa de ambiente isolado

- Inspecionados nomes de arquivos e manifesto NonUFS: nenhum executável separado de servidor/editor identificado.
- Confirmado um pacote de gameplay em `War\Content\Paks`; contagem genérica do scanner não equivale a pacotes exclusivos de gameplay.
- Consultadas fontes primárias: FAQ oficial, War API, FDE e tutorial de texturas.
- War API é de consulta; FDE extrai dados, não hospeda o jogo. Nenhuma dessas ferramentas resolve a simulação RTS.
- Resultado: rota offline/controlada ainda não encontrada. Não confundir ausência de evidência com impossibilidade.
- Detalhes e pergunta sugerida aos desenvolvedores registrados em `RECON_AMBIENTE.md`. Nenhuma mensagem enviada e nada publicado.
- Próximo passo: esclarecer disponibilidade e autorização de um ambiente isolado antes de instrumentar o cliente.

## 2026-10-06 — Rodada 2: investigação com agentes paralelos

- Quatro agentes, todos somente leitura:
  - Sonnet: recon local;
  - Opus: análise estática do executável;
  - Sonnet: pesquisa web;
  - Haiku: KB do toolkit.
- **Achado principal:** o `War-Win64-Shipping.exe` é target Game, com código de servidor compilado: login/join, `UWorld::Listen`, `?listen` montado pelo jogo, `ASimGameMode`, `UWarReplicationGraph`, `UServerSettings` (`IsCommunityServer`, `bAllowMods`), `EWarServerType::Training`.
- **Bloqueio provável:** dependência de `FExternalWarService` (auth, perfis, travel, config da guerra).
- **Proteção:** sem EAC/BattlEye/EOS. Há VAC e detecção própria. PAK com índice aberto e sem assinatura.
- **Pesquisa pública:** confirma ausência de offline, bots, servidor privado, SDK e Workshop. Pak mods visuais são prática corrente.
- **Ghidra:** não estava instalado (o setup antigo em `G:` sumiu). Com autorização do usuário, instalados:
  - Ghidra 12.1.2 em `D:\tools\ghidra`;
  - GhidraMCP 5.14.2 (extensão + bridge com venv) em `D:\tools\ghidra-mcp-v5.14.2`.
- O usuário re-registrou o MCP `ghidra-mcp` apontando para D:.
- Análise automática headless em andamento no projeto `D:\tools\ghidra-projects\Foxhole`.
- Nada executado, injetado, extraído ou alterado no jogo.
- **Próximo passo:** decompilar o caminho `?listen` e `ASimGameMode` ↔ `FExternalWarService`, e decidir a rota normativa com o usuário. Detalhes em `RECON_AMBIENTE.md` (Rodada 2) e `MODDING_PLAN.md`.

### Discussão: rota normativa (proposta pendente)

- O usuário propôs autenticar online e depois seguir offline, ou "seguir como pudermos", já que o mod é distribuído sem os arquivos do jogo.
- Proposta registrada, ainda aguardando o ok do usuário:
  - posse continua verificada pelo Steam, sem modificação;
  - a sessão modificada nunca contata a Siege Camp;
  - stub local do `FExternalWarService` só para a sessão local;
  - servidor local sem VAC;
  - mod inativo fora do modo RTS.
- Rejeitado "auth online e depois offline": cliente modificado falando com o backend oficial é o maior risco de ban.
- Primeiro item do Ghidra: confirmar onde o listen server decide Steam secure/insecure (VAC) e o que exige do `FExternalWarService`.
- Usuário aprovou a rota normativa em 2026-10-06. Próximo: decompilação no Ghidra (VAC do listen server, dependências do FExternalWarService).
- Usuário decidiu: modo solo contra IA, controle por esquadrão. Implicação: o mod precisa de uma IA adversária própria e de líderes de esquadrão que comandam soldados via AIController/BehaviorTree (runtime do UE presente no binário).

## 2026-10-06 — Rodada 3: documentação da rota e laboratório (usuário ausente)

Objetivo da rodada: documentar como fazer o mod (rota, limitações, caminhos) e testar o que fosse possível. A validação foi feita pelo agente.

### Feito e verificado
- **`COMO_FAZER_O_MOD.md`:** documento principal com rota, arquitetura em camadas 0–5, limitações, regras do laboratório, protocolo de testes T0–T9 e perguntas respondidas/abertas.
- **Índice do PAK** (agente Sonnet): 25.898 entradas, 0 comprimidas/criptografadas, SHA1 conferido.
  - 316 mapas; não há mapa de treino/teste.
  - `HomeRegionW` (48 MB) é o menor jogável.
  - Os mapas usam `DefaultGameMode = SimGameMode` (tabela de nomes lida por mim).
  - Não há `RecastNavMesh` nos mapas.
  - Não há assets de IA de soldado.
  - Saídas: `D:\tools\foxhole-lab\pak-index.tsv` e `pak-config-excerpts.txt`.
- **Ghidra:** auto-análise concluída (57 min); script `DecompStrRefs.java` para decompilar por string ou endereço.
- **Fatos decompilados e validados por mim:**
  - `UWarGameInstance::StartGameInstance` pula o `MainMenu` quando a linha de comando tem `/Game/Maps/`.
  - Init do servidor Steam: `eServerMode = 2 + bVACEnabled`. Num cliente ele só sobe com `bInitServerOnClient`/`OSS.SteamInitServerOnClient` (strings confirmadas).
  - `BaseEngine.ini` embutido: `bVACEnabled=1`.
  - Perfil em `PostLogin`: o pedido HTTP é montado, mas só é enviado (`ProcessRequest`, vfunc `0x88`) com `GetNetMode()==1`. É o bloqueio real do host num `?listen`.
  - `AHeadlessPlayerController::PlayerTick` move `ASimCharacter` com `AddMovementInput` (vfunc `0x720`). Rota de soldados = jogadores locais extras.
- **Fatos do agente Opus** (não revalidados individualmente):
  - dedicado inalcançável neste exe;
  - `AOfflineCharacter` é `AActor`, descartado;
  - `Login` só exige reserva se `bCheckReservationsOnLogin`;
  - lista de switches FParse.
- **Laboratório:**
  - cópia em `D:\FoxholeLab\Foxhole`: 97 arquivos, 26.035.003.749 bytes, idêntica;
  - `steam_appid.txt` na cópia;
  - `tools/lab.ps1` com `check` e `prepare` executados; `vac-off` testado em 4 casos numa pasta temporária;
  - instalação Steam confirmada sem loader.
- **Mod:** esqueleto `mod/FoxholeRTS/Scripts/main.lua` (rota de jogadores locais + fallback `AddMovementInput`). Escrito, **não executado**; a checagem de sintaxe Lua não foi possível.

### Bloqueado pelo modo automático (decisão do usuário)
- Lançar o jogo (`um win launch`), mesmo o cliente original: impede T0–T3.
- Baixar o UE4SS: impede T4–T5.
- Acrescentar `bInitServerOnClient=False`/`bUseSplitscreen=False` ao `lab.ps1`.
- Especificação detalhada do stub de perfil (T6).
- Editar `~/.claude.json` (o usuário re-registrou o MCP manualmente).

### Próximo passo (com o usuário presente)
T0 → T1 → T2/T3 do protocolo em `COMO_FAZER_O_MOD.md`. O log do T2 confirma se o host fica parado no perfil, como previsto. Depois decidir o stub de perfil (T6), UE4SS (T4–T5) e o primeiro soldado (T7).

## 2026-10-06 (noite) — Primeiros testes em execução

- **T0 OK:** o cliente original abriu pelo Steam e chegou ao menu.
  - Log em `D:\tools\foxhole-lab\T0-War.log`.
  - Steam SDK 1.51; "Steam User is subscribed 1" e "Steam Auth Enabled".
  - Nenhum "Initializing Steam Game Server", o que bate com a análise de VAC.
- **Correção:** a config e o log ficam em `%LOCALAPPDATA%\Foxhole\Saved\`, não em `War`. O `tools/lab.ps1` foi corrigido; `lab-ini` grava `bInitServerOnClient=False`, `bVACEnabled=False` e `bUseSplitscreen=False`.
- **T2 falhou (ainda sem conclusão sobre o `?listen`):** a cópia `D:\FoxholeLab` lançada direto com `/Game/Maps/HomeRegionW?listen -log` foi para o **menu**.
  - Causa provável: o log mostra "SteamAPI failed to initialize, conditions not met" e "[AppId: 0] Client API initialized 0". Sem Steam, o `SteamSocketsNetDriver` não escuta, o `?listen` falha e a Unreal volta ao mapa padrão (menu).
  - Também viola a regra 1 (posse verificada pelo Steam), então precisa ser resolvido de qualquer forma.
  - Tentativas que não resolveram: `steam_appid.txt` (505460) na pasta do exe; variáveis `SteamAppId`/`SteamGameId`; lançamento fora do sandbox.
  - Logs em `D:\tools\foxhole-lab\T2a-War.log` e `T2b-War.log`.
- **Próximo passo:**
  - Decompilar a origem de "SteamAPI failed to initialize, conditions not met" para ver a condição exata (saída em `D:\tools\foxhole-lab\decomp4\`).
  - Alternativas a testar:
    - lançar via Steam a instalação oficial com opções de inicialização (sem mod, só para validar o `?listen`);
    - usar o `War.exe` da cópia em vez do Shipping;
    - verificar se o Steam exige que o exe esteja na pasta instalada.
- O backup da config criado pelo toolkit ficou em `%USERPROFILE%\.universal-modder\backups` (0,1 MB); mover para `D:`.

## 2026-10-07 — Sessão local estável e primeiro personagem do host (trabalho autônomo)

- **Causa do Steam init:** a falha anterior vinha do cliente Steam fechado. Com o Steam aberto e logado e o `steam_appid.txt`, a cópia inicializa o Steam normalmente. O `lab.ps1 run` agora recusa lançar sem Steam.
- **T4 OK:** o UE4SS 4.24 carrega no Foxhole (só na cópia). O mod Lua `FoxholeRTS` roda.
- **Mapa da linha de comando é ignorado em shipping:** `UGameInstance::StartGameInstance` (0x142576600) usa uma URL vazia. A sessão é aberta pelo mod com `GameplayStatics:OpenLevel(world, "/Game/Maps/HomeRegionW", true, "listen")`, em modo autostart quando existe `autostart.txt`.
- **Crash T2c:** stack overflow em `SimPlayerController:ClientStartRespawnTimer`.
  - A impl (`FUN_140b97950`) chama a Client RPC quando `Role==Authority`; no host local isso recursa.
  - **Correção** (hook Lua): na chamada aninhada, o `Role` vai temporariamente para AutonomousProxy.
  - Validado no T2d: sem crash, sessão estável por minutos.
  - Crash reporter da cópia desativado (`CrashReportClient.exe.disabled`).
- **T2 OK:** `HomeRegionW` em listen, `IsServer=true`, `SimGameMode` local, portas 7777/15000 no SteamSockets.
- **Canal de comandos** (`D:\tools\foxhole-lab\cmd.lua` → `cmd.out`): o mod executa o arquivo no game thread a cada 1 s. Permite testar sem reiniciar o jogo e sem teclado.
- **Host sem personagem — diagnóstico real:**
  - O PC fica em `Spectating`, `bPlayerIsWaiting=true`, `TeamId=-1`, sem kick e sem "Unable to load Profile".
  - `ServerRespawnDefault` não faz nada.
  - `GameMode:RestartPlayer(pc)` cria o `Character_C`, mas num ponto sem chão: cai de Z 2373 até -14 e morre na queda.
- **T6 contornado sem stub de perfil:** `GameMode:RestartPlayerAtTransform(pc, transform)` ao lado de um veículo do mapa (blindados em ~10789,-24935,256) dá um personagem estável: HP 100, `Playing`, `PlayerCharacterMovementComponent`, MaxWalkSpeed 500.
- **Soldado por `SpawnAIFromClass(Character_C)` (rota B):** nasce sem controller (a classe não define `AIControllerClass`).
  - Com `AIControllerClass=AIController` + `SpawnDefaultController`, ele anda via `AddMovementInput`, mas devagar: o input chega a cada 50 ms e o CMC freia entre frames. Precisa de input por frame.
  - Pouco depois foi desapossado e estacionado em (0,0,0), com HP 100. O jogo parece recolher personagens sem jogador/PlayerState.
  - A rota A (jogadores locais com `SimPlayerController`) passa a ser a principal.
- **Rota A (`CreatePlayer`) crasha:** ~1 min depois, `EXCEPTION_ACCESS_VIOLATION` lendo 0x224 em 0x140f06595, dentro de `FUN_140f00b60`, que constrói o `SGeneralOptionsWidget` (UI de opções) para o novo jogador local. Cada jogador local puxa a UI inteira.
  - Rota A descartada.
  - Próxima rota: `HeadlessPlayerController` (existe em `/Script/War`) spawnado sem LocalPlayer.
  - Crash em `D:\tools\foxhole-lab\crash-T7a\`; parser novo `dmp_exc.py` (exceção + varredura da pilha).
- **Ferramentas do universal-modder em uso:**
  - `um backup` (no `lab.ps1`), `um win shot` (captura GPU), `um win drive` (input), `um win kill`.
  - `um win setup` instalava em `%LOCALAPPDATA%\universal-modder`; movido para `D:\tools\um-win` com junção no caminho antigo.
  - **Melhoria no toolkit:** `um win drive --title <regex>` e `WinDrive.ps1 -Title`, para escolher a janela do jogo quando a janela principal do processo é outra (aqui, o console do UE4SS).
- **Tela preta no host (em investigação):**
  - O HUD aparece (arma, bússola, rótulos do mundo), mas o mundo 3D não.
  - Testado sem efeito: pós-processamento (PPVs, `PostProcessComponent` da câmera, `LOSPostProcess` do personagem), câmera própria no alto, cubo da engine, foco da janela, `bDisableWorldRendering` (byte em `viewport+0x6C`, bit 4 = 0, ou seja, não está desligado).
  - O `Draw` é o da engine (vtable slot 4 = 0x142556b20).
  - O `SceneCapture2D1` ortográfico do minimapa renderiza o terreno normalmente. Um `SceneCapture2D` em perspectiva sai vazio (profundidade máxima).
- **Tela preta resolvida:** a cena era renderizada (`WasRecentlyRendered`=true; um `SceneCapture2D` mostrou a base dos Wardens com veículos e prédios). A causa era o **fade da câmera preso em preto**. Correção: `PlayerCameraManager:StopCameraFade()` + `SetManualCameraFade(0, preto, false)`.
  - Em shipping as cvars `ShowFlag.*` leem de volta mas não têm efeito; não servem de diagnóstico.
  - Numa execução a UI ficou na tela de espera ("Foxhole Airborne"); `SimPlayerController:ClientGotoScreen(0)` (`ESimScreen::HUD`) resolve.
- **Câmera RTS:** um `CameraActor` como view target, com pitch -60, mostra a base vista de cima. Validado por captura.
- **Soldados — rota que funciona:** `HeadlessPlayerController` spawnado sem LocalPlayer, mais `PlayerInput` (`StaticConstructObject`) e `RestartPlayerAtTransform`. Depois da posse: `bIsLocalPlayerController=true` e `SetMovementMode(Walking)`.
  - Se a flag local for ligada antes da posse, o pawn nasce com `MovementMode=None`.
  - O pawn de `AIController` é desapossado e estacionado em (0,0,0) após ~20 s; o do `HeadlessPlayerController` fica estável (testado por 20 s).
  - Movimento: `AddMovementInput` a cada frame (`LoopInGameThreadAfterFrames(1)`); andam a 500 u/s e chegam em formação. Validado por posição e captura.
- **Crash v0.2:** `GameThread` dentro do `UE4SS.dll` (leitura em 0xffffffff), com `LoopAsync`(33 ms) + `ExecuteInGameThread`. Todos os loops passaram para `LoopInGameThreadAfterFrames`/`LoopInGameThreadWithDelay`.
- **Mod v0.2.2** (`mod/FoxholeRTS/Scripts/main.lua`):
  - autostart → sessão local → comandante em chão firme → fade zerado → HUD → câmera RTS;
  - F6 esquadrão; botão direito/F7 move ao cursor; F8 limpa; F2 centraliza; PageUp/PageDown zoom; setas pan; F3 pan pela borda; F10 liga/desliga o RTS.
- **Times e combate (investigação):**
  - `EFactionId`: Colonials=0, Wardens=1, NoTeam=255. `SimPlayerController:ServerJoinWar(1)` põe o `PlayerState` nos Wardens; o pawn já existente continua 255.
  - Personagens nascem sem equipamento.
  - Atividades em `ECharacterActivityState` (Firing=3, Reloading=4, ...).
  - `ItemHolderComponent:ClientImportItem` é uma RPC de cliente e não altera o inventário do servidor.
  - Tentativa atual: spawnar `BPRifleWPickup_C` e chamar `SimCharacter:ServerTakePickup`.
- **Toolkit:** `um win drive` ganhou `--title` e o comando `min`; nota da base de conhecimento em `universal-modder/knowledge/games/foxhole/` (passa no `um kb check`).
- **Pegar item (`ServerTakePickup`):** recursava no host (stack overflow, crash em `crash-pickup\`). Hook quebra-recursão (na profundidade ≥ 2 o argumento vira nil) evita o crash, mas o item ainda não entra no inventário. Arma de verdade continua em estudo (agente de RE estática).
- **Combate v0.3 — validado em execução:**
  - Times: `PlayerState.TeamId` escrito direto + `pawn.TeamId` + `OnRep_TeamIdNotify` + `BPSetTeamVisuals(team)`. (`ServerJoinWar(0)` num HPC deixou o PlayerState em 1; escrita direta funciona.)
  - Tiro simulado: `GameplayStatics:ApplyDamage(alvo, 34, hpcAtirador, pawnAtirador, nil)` (HP cai; morte com HP ≤ 0), alcance 22 m, cadência ~1,6 s, chance de acerto 60 % caindo com a distância, inimigo com 75 % da precisão.
  - Efeitos do próprio jogo: `SpawnEmitterAtLocation` (8 args no 4.24: ..., bAutoDestroy, PoolingMethod, bAutoActivate) com `/Game/FX/RifleMF` (clarão), `BloodSplat` (acerto), `SimpleRifleImpact` (erro); `PlaySoundAtLocation` com `/Game/Audio/SFX/Weapons/RifleShot_Cue`.
  - Linha de visada: `LineTraceSingle` olho a olho ignorando os dois pawns.
  - IA inimiga: avança até o aliado mais próximo, para a 80 % do alcance com visada e atira; desvio lateral quando fica preso (ex.: entre as motos estacionadas).
  - Ondas automáticas (Shift+F4): 15 s entre ondas, +2 soldados de reforço por onda vencida (máx. 8), onda cresce 0,5/onda, ponto de chegada a 35 m num ângulo com chão na altura do esquadrão; derrota quando o esquadrão cai.
  - Mensagens no HUD: `SimPlayerController:ClientAlertMessage(str, segundos)` (canto superior esquerdo). `ClientAdminMessageUnformatted` escreve no chat.
  - Verificado por log e captura: onda 1 eliminada (4 abates, 1 perda), reforço para 5, onda 2 por outra direção; alerta "onda 1: 4 inimigos vindo de baixo" visível.
- **Equilíbrio (medido com contadores por lado):** o jogo segura o personagem em **1 HP** (ferido, sangrando) antes da morte; matar exige um acerto a mais. Inimigo não atira andando, leva 0,8 s para mirar ao parar, precisão 60 % da aliada. Partida típica sem micro: onda 1 aliados 35 tiros/12 acertos/381 de dano contra 17/3/97; esquadrão parado vence 2 ondas e cai na 3ª (10 abates, 8 baixas). Estável ~4 min de ondas, processo respondendo.
- **Grupos de tiro:** soldados alternam entre grupo 1 e 2 ao nascer; teclas 1/2/3 selecionam grupo 1, 2 ou todos; a ordem de mover só vale para os selecionados, em formação própria. Validado por captura (grupo 1 andou, grupo 2 ficou).
- **Proteções:** `isLocalAuthority` recusa o menu principal (o menu também é "servidor" standalone e o pawn ali não é `Character`; dava "compare number with TrivialObject").
- **Hot reload do UE4SS (Ctrl+R) travou o jogo** no 4º reload da sessão: processo "Not Responding", CPU parada, nenhum callback no game thread (nem tecla). Os três primeiros funcionaram. Passamos a reiniciar o jogo (`D:\tools\foxhole-lab\restart.sh`: checa sintaxe, publica, mata a cópia pelo PID, `lab.ps1 run`, espera o RTS; ~1 min).
- **Teste do usuário (2026-10-07):** com o botão direito no chão, os soldados andaram até o ponto clicado. A ordem de mover foi validada à mão, fora da automação.

### Como retomar (estado histórico do lote 17; prioridade atualizada em 10/10)
- **Prioridade vigente:** desenvolver logística; usuário adiou crashes/efeito amarelo. Lote v4.1 integrado,
  29/29 PASS offline, fila experimental preservada. Não repetir o gate manual de 1/2 como bloqueio de features.
  Build não é estável. Os itens antigos abaixo são contexto; consultar primeiro as entradas novas do topo.
- **Atualização 10/10:** trabalho retomado por novo pedido. Ler primeiro as entradas novas no topo:
  controles A/B repetidos,620s selecionados e100ciclos/20mortes passaram com fonte33D6C7E5.
  Causa nativa antiga não isolada; candidato logístico v4.1 continua separado/não publicado.
  Usuário pode fazer gate de entrada real depois do ensaio; laboratório fechado, combinar início.
- **Onde estamos:** `ROADMAP.md`. Fase 1 (frente pequena) pronta; fase 2 (estudo, `ESTUDO_MECANICAS.md` + `dados/`)
  com a primeira leitura feita; **fase 3 em protótipo, agora com cadeia curta validada em CallumsCapeHex**,
  não só no lobby. Alt+L implanta instalações/caminhões reais com carteira1100, valida chão/folga e rollback.
  Em65,21s produziu três caixas e entregou munição/camisas, com três caminhões íntegros; sem ondas/estoque
  inicial, NÃO teste de equilíbrio. Dados: `dados/rastro_implantacao.txt` e topo deste diário.
- **Primeiro ao retomar:** respeitar pausa; só trabalhar após novo pedido. Contorno completo foi aprovado
  visualmente, mas duas quedas UE4SS após extensão às peças e erro Lua Registry continuam pendentes.
  Ler `dados/rastro_selecao.txt`, reproduzir/isolar por componente/GC/reseleção antes de novas features.
  Fonte experimental continua com contorno ligado; não apresentar como build estável. Laboratório fechado.
- **Próximos passos da fase 3 (depois da estabilidade):** caminhões seguindo a estrada
  descoberta por região (hoje andam em reta, sem colisão, atravessam
  prédios); mais tipos de caixa (armas, granadas, médico; custos já em `dados/custos_do_jogo.txt`); cadeia
  inimiga mais completa; talvez trocar a "mão de obra" por material. Depois: fase 4 (veículos como unidades).
- **Contrato de construção:** `dados/rastro_reconstrucao.txt`. Refinaria/fábrica ativas podem nascer na transformação
  nativa com HP/classe-base corretos, mas canteiro cru não tem alvo; não foi validada conclusão nativa.
  Custos corrigidos: 400/400/100 bmat. Orçamento explícito/rollback/superfície/folga implementados no lote17:
  `groundZ` pode acertar telhado; `SpawnActor` pode retornar ator já sendo destruído; bounds totais incluem volumes.
  Não confundir implantação própria com conclusão nativa de canteiro/facilities. Nada persiste no save ainda.
- **Mod atual:** v0.9 em `mod/FoxholeRTS/Scripts/main.lua` (~4800 linhas, 178 locais no topo de 200: funções
  novas em tabelas `rts`, `fort`, `sv`, `logi`, `anim`, `ai`; constantes em `CFG`, estado em `S`). Controles e
  mecânicas em `mod/README.md`; teclas também no banner de carga. Direção: **totalmente offline**, sistemas próprios.
- **Publicar e testar:** `bash D:/tools/foxhole-lab/restart.sh` (sintaxe + `tools/check_globals.py` + cópia +
  reinício + espera do modo RTS). Não use o Ctrl+R do UE4SS.
- **Testes offline:** `PYTHONPATH=D:/tools/pylibs python tools/test_orders.py` (lupa; inclui checagem de teclas contra
  os mapeamentos do jogo, lidos de `InputSettings` ao vivo; sobreposições aceitas são ações do pawn, desligado no RTS).
  Também `tools/test_costs.py` e `tools/test_inventory_probe.py`; exportar custos ao vivo com `tools/export_costs.lua`.
- **Comandos ao vivo:** `sh D:/tools/foxhole-lab/run.sh <arquivo.lua>`; saída só pelo `out(...)` (não `return`).
  O canal enxerga a tabela `env` de `runCommandFile` (inclui `CFG`, `S`, `logi`, `rts`, `combat`, `squad()`,
  `enemies()`...). Não usar o canal com o robô rodando.
- **Robô de regressão:** `sh D:/tools/foxhole-lab/botloop.sh` em segundo plano; log `botrun.log`; esperar com
  `until grep -q "auto<TAB>false" botrun.log` (grep -P não funciona no Git Bash). TaskStop não mata o `sh.exe`:
  `Get-CimInstance Win32_Process` filtrando `botloop.sh`. Últimos resultados: lote 12 vitória nas 10 ondas
  (111/24); lote 13 derrota na onda 10 (83/38).
- **Dados do jogo:** índice do pak (lista de arquivos) e tabelas (`DataTable:ForEachRow` só em colunas conhecidas; um
  dump genérico derrubou o jogo em `BPAirDynamicData`). O cliente tem as 54 regiões do mundo (`Maps/Master/*Hex`).
- **Captura:** `cd D:/GitHub/universal-modder && UM_HOME=D:/tools/um-home python -m um win shot --title '^War' --scale 0.5 <saida.png>`
  (câmera olha para +X: topo da tela = X maior, direita = Y maior).
- **Pendências do usuário:** demais testes com teclado/mouse reais (`TESTE_MANUAL.md`); aparência completa aprovada
  nesta sessão, sem certificar integração de todas as teclas nem estabilidade prolongada.
- **Interface pedida pelo usuário** (`ROADMAP.md`, "Interface e retorno visual"): caixa de seleção visível ao
  arrastar; silhueta/contorno no selecionado (o jogo tem `M_OccludedOutline`); mais UI quando fizer sentido.
- **Morte corrigida (lote 14):** `ApplyDamage` zerava HP sem notificar a morte visual no host. O `reap` agora
  tira marcadores/cache, para e restaura movimento, então chama `OnRep_Health` (ragdoll nativo). Contrato
  medido em `dados/rastro_morte.txt`; não acessar AnimInstance após a notificação nem corpo após o TTL.

## 2026-10-07 — Retomada com universal-modder

- Consultados `mod-any-game`, `reverse-engineering`, `game-automation`, o playbook Unreal e a nota Foxhole via `python -m um kb search foxhole`.
- A segunda inicializacao chegou ao menu e depois a `HomeRegionW`, com `modo RTS ligado`, autoridade local e comandante com HP 100. Captura conferida: `D:\tools\foxhole-lab\continue-world_small.png`.
- Correcao do diagnostico inicial: `Responding=False` durante o carregamento nao provou deadlock. Nesta execucao o menu apareceu cerca de 74 s depois do inicio dos mods; o RTS ficou pronto cerca de 95 s depois. Nao reiniciar so por esse indicador.
- Executado `t_pk3.lua` pelo canal local: rifle e municao nasceram com CodeName/StackSize/PickupCDO validos. `ServerTakePickup` retornou sem erro com `bIsLocalPlayerController=false`, mas ambos os pickups permaneceram e `ItemHolderItems` ficou vazio. A hipotese da flag local nao resolveu a aquisicao; rifles reais continuam pendentes.
- Nenhuma alteracao no cliente oficial ou no codigo do mod nesta verificacao.
