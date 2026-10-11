# Batch nativo — executado em 11/10; gates parciais, MVP não aprovado

**Lote logístico 2 posterior:** uma publicação/run PID4696, fonte85D7EEB9…,
sonda RWD/root/updated antes-depois concluída, partida fresca interrompida por
crash158s desde processo. Último autosave60s bmat40/sucata0/base19camisas.
Relatório final perdido; não aprova medevac/contratação/cadeia. Evidência em
dados/rastro_crash_logistics2_20261011.txt e rastro_truck_movement_{before,active}.
Sem outro restart. Próximo sampler logistics3 persiste linhas; somente offline.

Uma publicação/run CallumsCapeHex/PID19324, concluída sem crash observado.
Arremesso/Owner/Instigator/fuse/dano/contextos/GC passaram. Collision-off impediu
dano; friendlyfire100→1 observado. truck_loss FAIL (900→850, perda0).
MVP fresco FAIL (353s, entrega0/perda110,02, bmat40, sem caminhão de recurso),
embora combate/reabastecimento/cadeia inimiga e conservação tenham ocorrido.
Rastros em dados/rastro_batch_{nativo,mvp}_integrado.txt; verificadores retornam1
pelos gates faltantes. Cleanup e encerramento confirmados; sem segunda run.
Plano abaixo preservado como contrato/reprodutor, não como aprovação.

## Próximo lote — coleta/evacuação (candidato offline)
- Contratação automática candidata verifica ameaça a35m da saída ANTES do spawn
  e débito. Validar recusa sem gasto, aviso limitado, retomada após ameaça sumir,
  combatentes ainda recrutáveis e perda real dos trabalhadores já em campo.
  Amostrar coordenadas/ameaça/estoque; lote anterior não provou perigo na saída.
- Gate check_mvp_batch_trace agora exige registro terminal único de recurso com
  estado conhecido/HP finito positivo/PAWNtrue. Registro ausente é falha, não
  reconstrução. Não basta esse registro para provar débito/rota/suporte nativos.
- Log do lote anterior confirma medevac imediatamente antes das duas perdas por
  "ordem do jogador" (17:07:04 e 17:07:19). Fonte agora distingue recuo automático.
- Regressão `tools/test_collection_medevac.py`: falha na fonte anterior, PASS na
  candidata; funções reais de medevac/coleta, navegação/engine mockados.
- Na próxima sessão integrada registrar estado/carga/orderT/medevac por trabalhador:
  evacuação conserva carga e suspende coleta; cura retoma campo/refinaria; entrega
  apenas ao chegar; morte e ordem explícita perdem uma vez; conservação a cada amostra.
- Repetir partida fresca sem créditos/save/velocidade extra. Não retirar combate
  nem concluir que essa correção resolve reposição excessiva, mortes ou toda a cadeia.
- Acumular também cenários de transporte/impacto antes de publicar. Nenhuma run nova
  executada para esta alteração.

## Antes da única sessão no laboratório
### Snapshot de comboio — candidato offline, não executado
- No cenário de dano nativo já previsto, salvar imediatamente após morte real,
  antes do próximo tick logístico. Não zerar Health só para obter aprovação.
- A carga destruída não vira pending nem caminhão livre; perda entra no razão
  uma vez, reconstrução entra uma vez, recompensa aparece na carteira do MESMO
  save. Repetir save não duplica nada; desaparecimento sem HP0 não dá recompensa.
- Continue deve manter a perda/fila/carteira; não confundir retorno da carga de
  comboio vivo (política antiga) com ressurreição de carga destruída. Casco/TTL
  continua a cargo do engine, sem esconder/destruir antecipadamente pelo save.
- test_enemy_snapshot_health.py cobre funções reais com engine mockado, FAIL
  na fonte anterior/PASS na candidata; ferimentos ainda não persistem.
- Gate offline adicional: HP NaN/±infinito/schema desconhecido em qualquer frota
  recusa snapshot/save e não toca arquivo anterior nem debita carga como morte.
  Não escrever valores inválidos no ator vivo para validar esse caso.

### Contrato NPC — sonda preparada, não executada
- Executar tools/probe_native_npc_roster.lua antes das ondas, durante ciclo e
  após cleanup: comandante, aliados, inimigos e pool; registrar localidade,
  Player/Pawn/PlayerState, roster e bot/inactive. Nenhuma escrita ou ID Steam.
- Reusar a mesma sessão e persistir saída externa por etapa. Ausência/assinatura
  divergente é GATE, não autorização para alterar roster/flag por offset.
- Sonda não lê UniqueId e não prova produtor do nulo, estabilidade ou correção.
  Não marcar NPC inactive nem desligar controlador local cegamente: preservar
  movimento/posse/GC exige rastrear efeitos antes de publicar qualquer patch.

### Movimento nativo — sonda preparada, não executada
- Executar tools/probe_native_truck_movement.lua após implantação/antes da
  logística e comparar com estado ativo. Somente leitura, sem movimento/estoque.
- Registrar raiz, classe do MovementComponent, UpdatedComponent/Primitive e flag
  bIgnoreNonRootComponentsDuringVehicleMovement após confirmação do schema.
  Funções/input apenas enumerados, não chamados.
- Se root/updated for cápsula, sweep de ator não prova caixa/meshes; mesmo raiz
  Box não comprova suporte de ponte/envelope. Rastrear caminho nativo primeiro.
- Grafo Callums405/431/4013 existe; nenhuma aresta fisicamente autorizada.
  Scan anterior atingiu CharacterMesh0 fora da caixa400/162/140, sem provar hull.
- test_native_truck_movement_probe.py PASS para schema válido/divergente/extra/
  ausente e scan recusado. Não é motorista integrado nem prova de estrada.

- Terminar integração de granada, contexto/lifetime e reação logística ao HP nativo.
- Resolver contrato Instigator/Owner/colisão com o lançador e atribuição de equipe.
- Verificar colisão dos caminhões: o transporte atual desliga ActorEnableCollision;
  não presumir que o overlap da explosão encontre esses atores. Não religar sem
  ensaio de movimento/impacto no mesmo lote.
- Passar `tools/test_orders.py`, `tools/test_native_context.py`, `tools/test_native_grenade.py`
  e `tools/check_globals.py`. Mocks não substituem o engine.
- Passar também `tools/test_native_truck_health.py`: observador integrado; HP0,
  perda única, ausência de ator e schema inválido; sem DPS fictício de veículos.
- Preparar comandos e saída de cada cenário fora do repo, sem robô concorrente.

### Sequência ampliada preparada (sintaxe/máquina mock PASS; NÃO executada)
`D:/tools/foxhole-lab/t_batch_native_start.lua` exige cena ociosa/tempo normal,
cria lançador trabalhador real + caminhão exclusivo, espera 12s de proteção nativa,
chama o caminho integrado e verifica Owner/Instigator. Treze casos: recusas/cooldown,
W colisão ligada/desligada, C ligada, reset em voo, soldado hostil/friendlyfire,
remoção do lançador, classes simultâneas, contexto emprestado/trocado, perda logística
por explosivos reais e GC refletido em voo. Cleanup entre casos. Sem HPwrite,
ApplyDamage manual, inventário/RPC ou entrada injetada. Duração ~5 min.
`t_batch_native_report.lua` lê andamento/resultados; limpa somente o relatório
depois do término. Dano dos casos collision-on é gate, collision-off é comparação
A/B, não PASS presumido. Friendlyfire é observação da regra nativa, não promessa
de ausência de dano. Remover lançador NÃO prova morte por combate. Caso de perda
logística usa 16 lançadores reais/exclusivos, não uma sobrecarga de ApplyDamage;
a carga de teste é fixture explícita, não progresso econômico do MVP.
`t_batch_mvp_start.lua` e `t_batch_mvp_report.lua`: cadeia fresca no hex, 1x,
sem carregar save/créditos, amostras10s, ordens/recrutamento pelos caminhos reais,
até resultado ou420s, auditorias e cleanup. Não exige derrota para declarar ciclo.
Preparação cobre os seis grupos, mas o resultado vivo decidirá os gates; não
confundir preparação com aprovação. Crash/pré-requisito impede continuar, registrar
antes de qualquer restart. Falha funcional sem crash não autoriza outra run.

## Uma publicação; cenários sequenciais na mesma run
1. **Arremesso:** aliado e inimigo, fonte real do soldado; solver/movimento nativos,
   FuseTimer4 antes de BeginPlay, colisão/bounce, sem dano/FX/teleporte duplicados.
2. **Limites/falhas:** curto/longo, alvo morto, solver recusado, spawn/finish inválidos;
   nenhum cooldown/contador debitado sem sucesso, nenhuma reserva/contexto vazando.
3. **Dano/equipe:** HP nativo de personagem e caminhão; comportamento friendlyfire,
   morte e animação/cache seguros. Não chamar morte/OnRep de veículo manualmente.
4. **Logística:** HP exibido/contabilidade acompanham ator real; carga perdida uma vez,
   sem caminhar depois de HP0, sem morte fictícia por DPS abstrato de comboio.
   Amostrar HP parcial/zero, conferir casco por 15s sem destruição/ocultação pelo mod,
   razao inimiga/reconstrução/carteira, e provar que rifle próximo não altera HP.
   Save antigo não reaplica seu HP abstrato: restaura estado/carga, usa Health do
   ator carregado. Persistência de ferimentos nativos fica para lote próprio.
5. **Lifetime:** várias granadas simultâneas, morte do lançador, reset durante voo,
   contexto emprestado e troca externa; restaurar somente a configuração própria
   depois da última granada, cancelar apenas atores próprios.
6. **Regressão MVP:** coleta/refino/produção/entrega/recrutamento/abastecimento e combate
   no hex pequeno; carteira/carga conservadas. Sem aceleração/crédito para maquiar resultado.

Registrar PASS/FAIL e evidência por cenário, limpar entre eles e fechar só o PID do
laboratório ao terminar. Não abrir outra run por ideia nova: entra no próximo lote.
Crash/pré-requisito impeditivo é exceção registrada, não autorização para sondas avulsas.
