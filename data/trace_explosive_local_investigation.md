# Native local explosive — offline investigation (2026-10-11)

## Contract found, still without an explosion oracle

- `WarProjectile` and `TimedProjectile` are native actors. `BPGrenadeW` is a
  SpawnActor candidate; the live schema/CDO was recorded by the main agent
  in `schema_projectiles_native.txt`: FuseTimer 20, ExplosiveCodeName GrenadeW,
  ExplosionTemplate GrenadeExplosion, AutoDetonateTime 0, ProjectileLife 0.
- `GrenadeItemComponent.ServerPullPin/ServerThrowGrenade/ServerOnFuseExpired`
  are RPCs and are NOT the proposed solution.
- UHT of `WarProjectile.Detonate` and `ApplyExplosiveDamageAndSpawnFx`:
  flags 0x4420401, one const/ref parameter `ProjectileHitInfo_NetQuantize` 0x38.
  Do not create a Lua table imitating that struct. Both are local, not RPC,
  but the native timer/collision make manual invocation unnecessary.

## The timer's real path

1. Constructor TimedProjectile 140cd8210 calls WarProjectile 140d9fb80;
   this one creates SphereComp, ProjectileComp and ParticleComp. No external actor
   needs to create components or formulas.
2. BeginPlay virtual 310 of TimedProjectile 140cdd570 calls the base BeginPlay
   140da4a70, requires Role 3, gets the World's TimerManager and schedules 14296f330
   with duration FuseTimer +330. Callback 140cdc028 calls virtual 650 = 140ce28a0.
   Capstone evidence confirms the float value sent in xmm3 to the timer function;
   the decomp simplifies the parameter as `(int)lVar1`, do not read it as a cast.
3. On expiry, 140ce28a0 fills the INTERNAL real HitResult +334 when the position is
   empty: uses the RootComponent position, a native normal and a weak Instigator (can be
   null). Then it calls WarProjectile 140dba940.
4. 140dba940 requires Role 3 and not Exploded, converts the real HitResult through 140db8020
   into ProjectileHitInfo, calls virtual 630 = 140dac5b0. Turns off movement/audio,
   applies damage/FX and schedules death using ProjectileDeathDelay; notifies state.
5. 140dac5b0 calls virtual 640 = 140da33d0 for radial damage, then effects
   virtual 638 = 140dc2c20/140dc2310 and marks bExploded. Do not rely only on
   IsValid after the callback: destruction/TTL is asynchronous.

## Real defaults/data and guards

- ExplosiveCodeName is a reflected FName at +268; MyController is a reflected WeakObject Controller
  at +260; FuseTimer Float 330 only exists in the TimedProjectile class.
- Getter 140dacd00 calls InitializeDynamicData 140db61c0 if the cache is not initialized.
  It looks up AmmoDynamicData by ExplosiveCodeName, with the native fallback
  LoadObject `DataTable'/Game/Blueprints/Prototypes/Data/BPAmmoDynamicData.BPAmmoDynamicData'`.
  Do not copy the values into a Lua formula. An additional lookup configures the
  penetration profile; a missing profile has a native fallback.
- GrenadeW in the extracted table: Damage 200, Suppression 20, ExplosionRadius 550,
  DamageType BPLightKineticDamageType_C. The fragmentation grenade does NOT use
  BPExplosiveDamageType by the mod's assumption.
- 140da33d0 requires Role 3, positive damage or a special type, positive radius,
  a valid DamageTypeClass. It resolves MyController through weak getter 1415a2000 and passes the
  result to the radial helper 1409dc010; there is no explicit veto/null deref of
  MyController in this body. A missing Owner/Instigator is handled with null checks
  in BeginPlay and in building the HitResult. This does not prove all the downstream
  team/instigator filters nor certify global safety.
- ServerSettings needs a strong NATIVE reference GI.ServerSettings during
  the WHOLE wait/detonation (lesson from the previous oracle). Do not keep it only in Lua.

## Next validation aligned with the MVP

SpawnActor BPGrenadeW without inventory/RPC near an exclusive 900 HP truck,
fresh configuration anchored immediately to the GI, wait for the native 20 s timer and
record Health/bExploded/actors/FX for 25 s. Do not change FuseTimer/CDO/Health,
do not call ApplyDamage by hand and do not fabricate HitInfo. The first scenario
without a MyController write tests the defaults; no HP delta does not authorize our own
formula. Distance/exposure/LOS and the team filter can block damage.

## External evidence (do not publish decomp)

- `D:/tools/foxhole-lab/re-agent/explosivo-props.txt`,
  `explosivo-hit-props.txt`, `explosivo-primeiro-static.txt`.
- `D:/tools/foxhole-lab/explosivo-decomp/*.c`: two headless readOnly jobs,
  noanalysis, both exit 0; no project modification persisted.
- Source main/channel/lab were not touched by this sub-agent.

## Update — live oracle and launch integration

- The main agent recorded oracle PID18148: SpawnActor BPGrenadeW near
  a 900 HP truck, fresh GI.ServerSettings anchored 27 s, default 20 s timer,
  Health 900→780, grenade gone, restore/cleanup PASS. No manual ApplyDamage,
  change of Owner/MyController or fabricated HitInfo. See the live trace
  produced by the main agent for details and do not treat the result as an
  integrated throw/trajectory.
- UHT `GrenadeDynamicData` size 0x20 has five known Floats:
  MinTossSpeed +8, MaxTossSpeed +C, GrenadeFuseTimer +10,
  GrenadeRangeLimit +14, ArmourDamageModifier +18. Export only these columns.
- The native fallback lookup 140906930 loads exactly
  `DataTable'/Game/Blueprints/Prototypes/Data/BPGrenadeDynamicData.BPGrenadeDynamicData'`.
  UItemComponent.InitializeGrenadeDynamicData 140a5a300 copies that row into its
  cache. Cooker 140a62a00 reads GrenadeFuseTimer +10 and schedules the TimerManager. Therefore
  the CDO's FuseTimer 20 does not prove the duration of the game's normal throw.
- SetVelocityInLocalSpace is a local UFunction of ProjectileMovementComponent,
  one FVector NewVelocity, flags 0x4820400. The trajectory can use the engine's
  movement, not K2_SetActorLocation/a manual arc. The ballistics/gravity solver
  will be checked by the main agent.
- FuseTimer is captured in BeginPlay: writing it after SpawnActor does not
  update the already scheduled timer. Legitimate candidate: BeginDeferredActorSpawnFromClass,
  write the UProperty FuseTimer with the real row BEFORE FinishSpawningActor. This
  flow still needs validation; do not claim the native throw's setter
  was fully traced. The traced GrenadeItemComponent calls
  delegate activity/Blueprint/RPC and do not authorize invoking them.
- New external artifacts: `explosivo-lancamento-props.txt` and the decomp of
  functions 140a62a00/140a5a300/140a6bd30; no change to main/channel by the sub-agent.
