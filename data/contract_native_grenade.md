# Contrato de granada — evidência offline e gates pendentes (11/10)

## Evidência conferida nesta retomada
- Reflexão extraída: Actor.Owner em +E0; Actor.Instigator em +118;
  Pawn.Controller em +258; WarProjectile.MyController é WeakObjectProperty +260.
- Vtable WarProjectile +468 resolve função 140dbe460. Ela registra OnProjectileStop,
  obtém Instigator por 1422d9d90, inclui o pawn na lista de colisão ignorada e obtém
  seu Controller por 1422d9da0 para preencher MyController nativamente.
  Os dois getters foram conferidos nas instruções do binário do laboratório.
- BeginPlay 140da4a70 também ignora Owner com 1424435c0 e adiciona peças anexas
  do personagem à lista ignorada. Portanto Owner e Instigator não são intercambiáveis:
  ambos precisam ser o lançador antes de FinishSpawning, não o comandante invisível.
- Aplicação explosiva 140da33d0 exige autoridade, resolve atributos nativos da
  identidade explosiva e passa MyController ao helper de dano em área 1409dc010.
  Não escrever WeakObjectProperty nem montar HitInfo/fórmula em Lua.
- `trace_binding_launch.txt`: GrenadeW fuse4/min390/max1100/range0;
  GrenadeC fuse4/min390/max1200/range0. `schema_projectiles_native.txt` associa
  Grenade_C a GrenadeC e BPGrenadeW_C a GrenadeW. Candidato agora usa cada facção.

Fontes protegidas externas, não redistribuídas: D:/tools/foxhole-lab/explosivo-decomp,
D:/tools/foxhole-lab/re-agent/explosivo-owner-props.txt e explosivo-pawn-props.txt.
Nenhum offset executado; somente leitura/decompilação já existente e getters do binário.

## Ainda não comprovado no main integrado
- Atribuição/friendlyfire e reação de personagem; ler Owner/Instigator/Controller
  após FinishSpawning no gate. Configuração/team do alvo não prova equipe do impacto.
- Overlap/dano em caminhão logístico com ActorEnableCollision false. Comparar com
  true em ator exclusivo, na mesma run; não religar a frota por suposição.
- Origem dentro da cápsula, trajetória curta/longa, morte do lançador, granadas de
  classes diferentes simultâneas, reset durante voo e restauração do contexto.
- Oráculo antigo sem Instigator não certifica esse fluxo completo.
