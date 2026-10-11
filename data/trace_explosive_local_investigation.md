# Explosivo local nativo — investigação offline (2026-10-11)

## Contrato encontrado, ainda sem oracle de explosão

- `WarProjectile` e `TimedProjectile` são atores nativos. `BPGrenadeW` é
  candidato de SpawnActor; schema/CDO vivo foi registrado pelo agente principal
  em `esquema_projectiles_nativos.txt`: FuseTimer20, ExplosiveCodeNameGrenadeW,
  ExplosionTemplateGrenadeExplosion, AutoDetonateTime0, ProjectileLife0.
- `GrenadeItemComponent.ServerPullPin/ServerThrowGrenade/ServerOnFuseExpired`
  são RPC e NÃO são a solução proposta.
- UHT de `WarProjectile.Detonate` e `ApplyExplosiveDamageAndSpawnFx`:
  flags0x4420401, um parâmetro const/ref `ProjectileHitInfo_NetQuantize`0x38.
  Não criar uma tabela Lua imitando esse struct. Ambos são locais, não RPC,
  mas timer/colisão nativos dispensam invocação manual.

## Caminho real do timer

1. Constructor TimedProjectile140cd8210 chama WarProjectile140d9fb80;
   este cria SphereComp, ProjectileComp e ParticleComp. Nenhum actor externo
   precisa criar componentes ou fórmulas.
2. BeginPlay virtual310 de TimedProjectile140cdd570 chama BeginPlay base
   140da4a70, exige Role3, obtém TimerManager do World e agenda14296f330
   com duração FuseTimer+330. Callback140cdc028 chama virtual650=140ce28a0.
   Evidência Capstone confirma o valorFloat enviado em xmm3 à função de timer;
   o decomp simplifica o parâmetro como `(int)lVar1`, não interpretar como cast.
3. Ao expirar,140ce28a0 preenche HitResult INTERNO real+334 quando posição
   vazia: usa posição RootComponent, normal nativa e Instigator fraco (pode ser
   nulo). Então chama WarProjectile140dba940.
4.140dba940 exige Role3 e nãoExploded, converte HitResult real através140db8020
   em ProjectileHitInfo, chama virtual630=140dac5b0. Desliga movimento/áudio,
   aplica dano/FX e agenda morte usando ProjectileDeathDelay; notifica estado.
5.140dac5b0 chama virtual640=140da33d0 para dano radial, depois efeitos
   virtual638=140dc2c20/140dc2310 e marca bExploded. Não depender somente
   IsValid após callback: destruction/TTL é assíncrono.

## Defaults/dados reais e guardas

- ExplosiveCodeName é FName refletido+268; MyController é WeakObject Controller
  refletido+260; FuseTimerFloat330 só existe na classe TimedProjectile.
- Getter140dacd00 chama InitializeDynamicData140db61c0 se cache não inicializado.
  Este busca AmmoDynamicData por ExplosiveCodeName, com fallback nativo
  LoadObject `DataTable'/Game/Blueprints/Prototypes/Data/BPAmmoDynamicData.BPAmmoDynamicData'`.
  Não copiar os valores para uma fórmula Lua. Busca adicional configura perfil
  de penetração; ausência desse perfil possui fallback nativo.
- GrenadeW na tabela extraída: Damage200, Suppression20, ExplosionRadius550,
  DamageTypeBPLightKineticDamageType_C. Granada de fragmentação NÃO usa
  BPExplosiveDamageType por suposição do mod.
-140da33d0 exige Role3, damage positivo ou tipo especial, radius positivo,
  DamageTypeClass válida. Resolve MyController via weakgetter1415a2000 e passa
  resultado ao helper radial1409dc010; não há veto/nullderef explícito de
  MyController neste corpo. Owner/Instigator ausente é tratado com nullchecks
  no BeginPlay e montagem do HitResult. Isso não prova todos os filtros
  downstream de equipe/instigator nem certifica segurança global.
- ServerSettings precisa referência NATIVA forte GI.ServerSettings durante
  TODA espera/detonação (lição do oracle anterior). Não guardar apenas em Lua.

## Próxima validação alinhada ao MVP

SpawnActor BPGrenadeW sem inventário/RPC perto de caminhão exclusivo900HP,
configuração fresca ancorada imediatamente à GI, aguardar timer nativo20s e
registrar Health/bExploded/atores/FX por25s. Não alterar FuseTimer/CDO/Health,
não chamar ApplyDamage manualmente e não fabricar HitInfo. Primeiro cenário
sem MyControllerwrite testa defaults; ausência de HPdelta não autoriza fórmula
própria. Distância/exposição/LOS e filtro de equipe podem bloquear dano.

## Evidência externa (não publicar decomp)

- `D:/tools/foxhole-lab/re-agent/explosivo-props.txt`,
  `explosivo-hit-props.txt`, `explosivo-primeiro-static.txt`.
- `D:/tools/foxhole-lab/explosivo-decomp/*.c`: dois jobs headless readOnly,
  noanalysis, ambos exit0; nenhuma modificação do projeto persistida.
- Source main/canal/laboratório não foram tocados por este sub-agente.

## Atualização — oracle vivo e integração de lançamento

- Agente principal registrou oracle PID18148: SpawnActor BPGrenadeW próximo
  de caminhão900HP, GI.ServerSettings fresca ancorada27s, timer default20s,
  Health900→780, grenadegone, restore/cleanupPASS. Nenhum ApplyDamage manual,
  alteração de Owner/MyController ou HitInfo fabricado. Consultar rastro vivo
  produzido pelo principal para os detalhes e não tratar o resultado como
  arremesso/trajectory integrado.
- UHT `GrenadeDynamicData` size0x20 possui cinco Float conhecidos:
  MinTossSpeed+8, MaxTossSpeed+C, GrenadeFuseTimer+10,
  GrenadeRangeLimit+14, ArmourDamageModifier+18. Exportar apenas essas colunas.
- Lookup fallback nativo140906930 carrega exatamente
  `DataTable'/Game/Blueprints/Prototypes/Data/BPGrenadeDynamicData.BPGrenadeDynamicData'`.
  UItemComponent.InitializeGrenadeDynamicData140a5a300 copia essa row para seu
  cache. Cooker140a62a00 lê GrenadeFuseTimer+10 e agenda TimerManager. Portanto
  FuseTimer20 do CDO não prova a duração do arremesso normal do jogo.
- SetVelocityInLocalSpace é UFunction local de ProjectileMovementComponent,
  um FVector NewVelocity, flags0x4820400. A trajetória pode usar o movimento
  do engine, não K2_SetActorLocation/arco manual. Solver de balística/gravidade
  será verificado pelo principal.
- FuseTimer é capturado no BeginPlay: escrever depois de SpawnActor não
  atualiza o timer já agendado. Candidato legítimo: BeginDeferredActorSpawnFromClass,
  escrever UProperty FuseTimer com row real ANTES de FinishSpawningActor. Esse
  fluxo ainda precisa validação; não afirmar que o setter do arremesso nativo
  foi rastreado integralmente. Chamadas de GrenadeItemComponent rastreadas
  delegam activity/Blueprint/RPC e não autorizam invocá-las.
- Novos artefatos externos: `explosivo-lancamento-props.txt` e decomp das
  funções140a62a00/140a5a300/140a6bd30; sem mudança de main/canal pelo sub-agente.
