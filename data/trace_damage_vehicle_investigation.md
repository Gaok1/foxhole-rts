# Offline investigation: native vehicle damage (2026-10-10)

Scope: reading local evidence; no command to the game, no RPC call,
no edit of `main.lua`. Applied: How to resume, universal-modder (kb search
foxhole), reverse-engineering/oracles, the Unreal playbook and ponytail.

## What really exists

- `data/schema_combat_native.txt:70–77`: `/Script/War.SimVehicle.Health` is an
  IntProperty; `OnRep_Health` is not an RPC and has no parameters. This authorizes investigating
  the local notification; it does not presume the death is safe or that it is the damage applier.
- `D:/tools/foxhole-lab/data_dump.txt:930`: TruckW has MaxHealth 900, TankArmour 0,
  MinorDamagePercent 0.1875 and MajorDamagePercent ≈0.7. These are data extracted from the
  BPVehicleDynamicData table, not recreated formulas.
- `re-agent/props_SimDamageType.txt`: the native SimDamageType class has Type,
  bCanPenetrateArmour, bApplyTankArmourMechanics, bApplyTankArmourAngleRangeBonuses,
  bCanDisableSubsystems, bDisableVehicleCollisionsIfKilledBy, bCanCauseLeaks etc.
  Identifying an asset does not prove its CDO values nor its behavior.

### Ammunition and DamageType mapping proven in the dump

Source `D:/tools/foxhole-lab/data_dump.txt`, section BPAmmoDynamicData:

| Line | Ammunition | Damage | DamageType |
|---|---|---:|---|
|1082|RifleAmmo|45|BPLightKineticDamageType_C|
|1083|MGAmmo|55|BPHeavyKineticDamageType_C|
|1086|ATRifleAmmo|150|BPAntiTankKineticDamageType_C|
|1091|SMGAmmo|27|BPLightKineticDamageType_C|
|1065|MortarAmmo|300|BPHighExplosiveDamageType_C|
|1074|HEGrenade|240|BPExplosiveDamageType_C|
|1077|RpgAmmo|550|BPExplosivePenetratingDamageType_C|

Matching assets listed in `pak_files.txt:1739,1754,1762,1765,1773`.
Example of a verifiable candidate path:
`/Game/Blueprints/DamageTypes/BPLightKineticDamageType.BPLightKineticDamageType_C`.
Use the real class obtained/loaded, never assume a name is enough.

## Difference from the current mod

- `logi.hit` subtracts directly from `tr.hp` and hides the pawn when it reaches zero;
  it does NOT query nor debit SimVehicle.Health. The visual explosion and the cut counter
  are also our own. This is the reinvented system, to be replaced after the oracle.
- `logi.blast` does distance and a fixed x2 multiplier, equally our own.
- Character combat already uses GameplayStatics.ApplyDamage, but passes nil
  as DamageType; this is a native Engine mechanism with the mod's decision/simulated shot,
  it does not prove native Foxhole firing nor the vehicle mitigation contract.
- ReceiveAnyDamage/ReceivePointDamage/ReceiveRadialDamage are reflected callbacks:
  do not call them as substitutes for TakeDamage. AllFire without parameters may
  be an effect/notification; metadata alone does not prove a physical shot.
- `ServerFire` and Multicast/Server/Client methods are out of the requested scope.

## Minimal oracle for the agent in charge of the lab

1. An isolated live TruckW actor, not being destroyed, outside the accounted trucks; record
   Health, bCanBeDamaged, class, position and authority. No modifying `tr.hp`.
2. Confirm the GameplayStatics.ApplyDamage schema (preflight already prepared externally),
   load the DamageType class and read its CDO Type/safe flags.
3. Apply ONE low pulse with the right ammunition type, shooter and causer alive.
   Record the return, Health before/after, the destruction flag immediately and after
   a short delay. Do not require the difference to equal the number received.
4. A/B generic Engine versus LightKinetic versus HeavyKinetic can separate the Foxhole contract
   from a simple callback, without involving the network. If Health does not change,
   follow the native trace; do not replace it with an HP write.
5. Only then validate impact/point/radial and death/subsystems. Do not repeat zero HP on an
   actor with live caches. The safety of OnRep_Health on the character does not transfer
   automatically to the vehicle.

Still missing: dynamic proof of real reduction, classification/mitigation, impact, native
destruction, accounting integration without a double debit and the native origin of the shot. This report
certifies NONE of them.

## Location for a later native investigation

`re-agent/class_natives.txt:5895`: SimVehicle size 0x12f0, StaticClass 0x141248990.
OnRep_Health wrapper 0x1412499a0. `native_tables.txt:2683` records the exec wrapper
0x141248100; do not confuse either with the virtual TakeDamage.
`strings_all.txt` has `Vehicle DamageDebug` at 0x36362b0 and a PenChance format
at 0x3636390. `DecompStrRefs.java` can look for these strings and their callers;
no existing decompilation searched proved this flow in this investigation.
Keep all decompilation outside the repository as per the reverse-engineering skill.

## Later static progress: damage flow located

Offline disassembly with the existing tools `re-agent/pe.py` (PE/Capstone), without
a game process nor injection. External evidence `D:/tools/foxhole-lab/damage-native-static.txt`.
It is not publishable decompilation nor does it authorize native calls by address.

1. execApplyDamage 0x142a52670 calls 0x142550100, which builds an FDamageEvent and
   calls the target's virtual at offset 0x570 (slot 174).
2. The real SimVehicle constructor 0x140d5be40 installs vtable 0x1436290f8;
   slot 0x570 points to 0x140d96d80, a TakeDamage candidate shown by the caller.
3. It converts the event with 0x140a104b0 and dispatches the EMBEDDED interface at
   this+0x8f8, vtable 0x1435fb920, method +0x10 → 0x140d81a00. It is not a UObject
   component: do not search FindAllOf by the address.
4. The dispatch checks Health (original this+0xb08) > 0 and resolves the type at 0x140a257b0.
   The resolution requires the CDO IsA SimDamageType, confirmed by classdb.json for
   StaticClass 0x1411c8be0. Damage with the generic EngineDamageType may be refused.
5. Original virtual guard this+0x688 → 0x140d94b00 → 0x140dc0cb0 → 0x142781620.
   The last one requires byte Role +0xf0 >= 3, bCanBeDamaged bit +0x5a&1, dmg different
   from zero and a non-null World (vtable+0x150) +0x128 pointer. That pointer is a
   candidate AuthGameMode, still requiring reflected confirmation; its absence is a
   concrete rejection hypothesis, not the impossibility of offline damage.
6. The War guard requires this+0x808==0 OR byte CDO+0x48 != 0. It probably matches
   spawn protection and bypass, but the exact meaning is not proven.
   Do NOT change offsets directly; confirm the reflected names first.

The next safe probe is ONLY observation: reflected Role/GetLocalRole/HasAuthority, World
and AuthGameMode, a reflected invulnerability property if it exists, the real
SimDamageType CDO and Type. Do not repeat dozens of ApplyDamage before these guards.

The lab owner's oracle: ApplyDamage 45 with LightKinetic/HeavyKinetic/Explosive
returned 0, TruckW kept 900 HP; ApplyRadialDamage 75 returned true, but Health 900.
Sources `data/trace_damage_vehicle_native.txt` and `data/trace_damage_vehicle_radial.txt`.
A true radial return does NOT prove damage; Team 255 stayed 255, so it was not an A/B
between teams. No native integration delivered in this investigation.

## Offline continuation: guards delimited (2026-10-10)

- A later oracle confirmed Role 3/HasAuthority true/valid SimGameMode, TeamId 0
  and, after 12 s, HP 900/damage 0. Live CDOs Type 1/2/7/3/8/18 confirmed, all bypass false.
  So authority and the DamageType name no longer explain the result by themselves.
- The UHT setter of `bBypassesSpawnInvulnerability` proven by a native parameter
  at 0x1436e9e50: SetBit 0x1405efab0 does `CDO+0x48=1`. It is not an inference from the name.
- Actor+0x808 is NOT an exposed UProperty in the WarCharacter dump (10 properties).
  The WarCharacter constructor 0x140d9f5b0 zeroes the flag. The local setter 0x140dc3d80
  takes a positive float duration, sets 808=1, registers timer handle 800 with callback
  0x140dac120; the callback zeroes 808 and clears the timer. The only direct caller located
  is in the spawn helper 0x140b95100, call 0x140b951fb. There is no proof of the flag being active
  on the truck 12 s later nor authorization to change offsets/cancel the timer by hand.
- The `DamageAttributes` constructor 0x140a104b0 copies the received Damage directly to +0;
  keeps the FDamageEvent at +0x20. It has NO ID 0 branch that zeroes damage. Resolver
  0x140a257b0 reads DamageEvent+8 (DamageTypeClass), the CDO and IsA SimDamageType;
  it also serves the generic event. Do not declare the generic one intrinsically incapable.
- **A distinct guard not observed yet:** damage interface 0x140d81ae0 calls
  `world → SimGameMode → WarGameInstance → ServerSettings`; a null return at
  0x140d81afb jumps to the zero exit 0x140d82719 BEFORE mitigation. The context is
  resolved by 0x14113e570 → 0x141192be0 → 0x140b61090 → 0x1411409c0.
  The last one reads `WarGameInstance+0x3d0`; the UHT extraction proves the name `ServerSettings`,
  an ObjectProperty of class ServerSettings. A valid SimGameMode does not prove this
  property is non-null. External evidence `damage-gameinstance-props.txt:14`.
- This is a static discovery of a local context requirement, **not a proposal to
  implement a server, RPC, configure the network or chase online systems**.
  Limit of this investigation: observe an ALREADY existing property, without fabricating an
  object/configuration to pass the guard. If null, it is the concrete cause of the refusal;
  the decision to reuse native code must respect the user's offline scope.

Next minimal oracle recommended: record the GameInstance class and ServerSettings
IsValid, without applying damage. If valid, trace the result of the local guard/profiler
before a new oracle with impact. No PointDamage with an invented HitInfo.

Disassembly/extractions stay external: `war808-refs.txt`, `damage-waractor-props.txt`,
`damage-gameinstance-props.txt` and `damage-native-static.txt`. No game process,
channel, offset write, RPC or change to `main.lua` in this continuation.
