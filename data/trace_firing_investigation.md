# Native firing investigation — 2026-10-10

Offline study and metadata only; did not change main.lua, did not call RPCs, did not touch the inventory nor control the game.

## Existing evidence and discovery
- `data/schema_combat_native.txt`: `Character_C.PlayerFire` is a ParticleSystemComponent, not a weapon. `SimCharacter.ServerSyncLastWeaponInvoke` is a path with an RPC name, not an approved local solution.
- `D:/tools/foxhole-lab/re-agent/class_natives.txt` and `props_HitScanWeaponComponent.txt`: native class **HitScanWeaponComponent** (SC 1411e0fd0); ItemComponent, ProjectileItemComponent and HeavyMachineGunItemComponent also exist. A rifle does not necessarily require a projectile actor: there is a hitscan pipeline.
- HitScan fields: ShotSoundCue/MuzzleFlashPS/WeaponFireFXClass, SimulatedHitNotify, BurstFiringRate. `data/schema_classes_firing.txt`, just produced by the root agent, confirms class/HitNotify in the live reflection.
- Old dump + static Capstone reading of the lab executable: candidate HitScan vtable `1434fd998`. Reflected wrapper `1411e2d50` (ServerStartInvoke) validates slot 508 and calls slot 510 = `140a65fa0`; this forwards to slot 518 = `140a68dd0`. This is a static discovery, **not an authorization to call an RPC or a raw offset**.
- Decompilation already available `D:/tools/foxhole-lab/re-agent/d5/140a68dd0.c`: checks the SimCharacter owner, finds the entry associated with the component through `140a55860`, requires the short field +1A to be non-zero, rejects an active timer, calls the activity, schedules a burst when applicable and calls `140a691f0`.
- `.../d7/140a691f0.c`: checks the owner is alive/state; decrements that short; gets the weapon parameters; builds the shot data in `1409d5ca0`; calls `1409e9860`; converts the result with `140a5cb90` and fills SimulatedHitNotify +9A8; invokes effects `140a69dd0` under a mode condition. The subsequent call `140aec820` changes the character's state (no proven semantic name).
- `.../d7/140a55860.c` finds the entry whose component pointer matches in the owner's storage: creating a component without a valid link is not enough. Do not implement the inventory by hand.

## What was NOT proven
- Exact C++ name/contract of `140a68dd0` and `140a691f0`; the decompiler shows arguments partially and can lose registers.
- The context that originally builds the components, sets owner/equip/muzzle and provides WeaponInvoke; a live equipped object with ammunition.
- `1409e9860` as final damage or only a trace: investigation continues, do not name it yet. No dynamic proof of shot→impact→vehicle HP obtained in this investigation.
- OnRep_SimulatedHitNotify is not proof of damage: it could just play an effect. The TotalShotsFired byte is not a validated dynamic count.
- GhidraMCP 127.0.0.1:8089 refused the connection; no GUI started. The old project/decompilation was reused, not reopened.

## Next minimal oracle
Trace local calls and the component's legitimate context before an attempt. Correlate an authorized shot in the offline lab with native consumption, HitNotify and vehicle health; compare a free/occluded target. Do not announce integration while there is only name/reflection/decompilation.

The external helper probe `D:/tools/foxhole-lab/t_disparo_classes_metadata.lua` only did a filtered FindAllOf(Class/ScriptStruct) and returned zero in the root agent's run; an inadequate enumeration, **not absence of the classes**. StaticFindObject by the proven name worked in the root agent's probe.

## Continuation: trace/bridge
- `.../d8/1409e9860.c` initializes the output with a default HitResult (Time=1), resolves the world, runs queries (`1409f4e30` and `142408380`) and returns a flag/result. **Static evidence suggests a query/trace, not direct damage application.** Follow the HitResult's consumer before declaring damage proven.
- `.../d8/1409d5ca0.c` fills the query structure and calls `1409e1cf0` for geometry; the decompiled signature has 12 parameters even though the earlier call was summarized as 4. This shows that signatures inferred by the decompiler are not enough for a safe invoke.
- An instance/owner-only probe prepared in `D:/tools/foxhole-lab/t_disparo_instancias_owner.lua`: FindAllOf(HitScanWeaponComponent), name and GetOwner via pcall; it does not read the inventory/struct instance nor fire. The root agent is the channel's only owner.
- A spot search found no Frida helper in foxhole-lab nor an available import (`PYTHONPATH=D:/tools/pylibs`, find_spec(frida)=None). The UE4SS Mods present are the usual Lua ones; no specific C++ bridge for a local invoke was found. `D:/tools/ue4ss` has ZIP files, it is not an installed bridge. No installation started.

## Root agent's live result / closing
`data/trace_instances_weapons_native.txt` confirmed zero instances of HitScanWeaponComponent/ProjectileItemComponent/HMG in this HomeRegionW. The classes exist, but there is no live armed weapon object to observe in this scene. Do not run a redundant owner probe. The next step is still to locate the legitimate native context that creates/associates the component with the pawn, without chasing inventory/RPC. Do not integrate firing by offsets until the ABI is rebuilt and the complete dynamic flow is proven. The analysis of 1409e9860 suggests queries; badly inferred extra arguments make it especially premature to conclude whether it applies damage or not.

## Static progress: impact application located (second investigation)

The existing headless Ghidra ran `-readOnly -noanalysis`, without GUI/installation; two runs finished with exit 0. Decomp kept exclusively in `D:/tools/foxhole-lab/disparo-decomp`, logs disparo-headless[2].log.

### Scope correction — do NOT generalize to the rifle
The authoritative function found is **140a68710 of HeavyMachineGunItemComponent**, pointer 1434fcb40 in vtable 1434fc608 +538. It is not 140a691f0 of HitScanWeaponComponent. The HMG class also does hitscan, but that does not prove integration of rifles or of every weapon.

### Static native chain
- 140a68710 requires a SimCharacter owner, not dead/in a suitable state and two guards of an embedded interface; gets orientation/muzzle/attributes from the component and builds query 1409d5ca0.
- 1409e9860 produces a HitResult; the following branch requires **the owner's Role = 3 (Authority)** and a valid HitActor. Helper 142405420 reads owner+F0 directly, **not GetNetMode**. Do not confuse Role 3 with NetMode 3.
- The branch gets data through virtuals 4F8 and 528, combines attributes and calls **1409dcd30** at 140a68c68.
- 1409dcd30 computes variation/falloff/context and resolves the **DamageableActor** interface, StaticClass 1411c8220 (name extracted from the registration table itself). For a target with the interface, it builds attributes with 140a104b0 and calls interface virtual +10 at 1409dd31a.
- A target without that interface goes through the fallback **142550460** at 1409dd33c: builds a point damage event and calls **TakeDamage virtual 570** at 142550588. This slot is the same one pointed to by the SimVehicle study; on the native truck, the interface path avoids going through GenericApplyDamage first.
- Then the weapon consumes an ammunition entry, writes the HitNotify including the returned damage and plays effects. Animation/OnRepHitNotify alone does not replace native application.

### ABI / contracts not safe yet
- 1409dcd30 has arguments beyond the four registers. In the caller: RCX=owner pawn; RDX=owner+258 (controller candidate, without new reflected proof); R8D=combined attribute integer; XMM3=combined float. Stack+20 holds a float converted from an attribute; +28 class/type pointer; +30 HitResult; +38 auxiliary context; +40 additional configuration. **Do not run this signature by approximation.**
- The decomp infers 9 args but declares param4 as undefined8 even though XMM3 is a float in the caller; registers/stack prevail over the automatic prototype.
- 140a5cb90 is a HitResult→HitNotify conversion (Damage coming from the float parameter), not damage execution.
- The existing live schema confirms CharacterInvokeInfo: ImpactPoint, RenderTimestamp, MuzzleOffset, AimYawPitch and flags bHasMuzzleOffset/bHasAimYawPitch. DamageAttributes was not enumerated in that schema; a name by itself is not a proven layout/ABI.
- The equivalent authoritative path of HitScanWeaponComponent/rifle and a legitimate native armed object are still missing. Do not fabricate inventory nor call an RPC to fill the gap. The next proof includes the DamageableActor/ServerSettings context identified in parallel by the damage agent, then a properly isolated live oracle.

## Rifle specific — local entry found, consumer still under study (2026-10-11)
- The real HitScanWeaponComponent constructor 140a43a30 installs the primary vtable 1434fd998 and an **embedded interface at +B0, vtable 1434fdef8**. It is not a separate UObject.
- Interface virtual 10 → 140a60640 validates the SimCharacter owner; calls primary virtual 518 → 140a68dd0 locally; after success it calls 1411e13c0, a ProcessEvent wrapper. Therefore **do not use this entry as a purely local invoke**: it involves an event with potential RPC forwarding. No call executed.
- Interface virtual E0 → 140a6b860 produces the shot parameter structure: queries the weapon's data, looks at the associated incoming ammunition and fills owner/origin/target; ends at 1409ff620. This is not proven damage application.
- Primary virtuals 4D0/4D8/4E0/488 handle setup/data forwarding, returning attributes, writing to the ammunition entry and the burst guard; nothing in them proved impact→damage. Full C++ semantic names still unknown.
- Headless readOnly/noanalysis decompilation of the methods finished, external results in D:/tools/foxhole-lab/rifle-decomp (rifle-headless[2].log). No changes to project/main/settings nor control of the game.
- `1409dc010` (native area/context damage helper) has caller 140a764a3. A local consumer near the weapons under investigation; do not label it rifle before a proven class/owner link.

### Result of the consumer / limit of the rifle proof
- The third headless job ended **exit 0**, log rifle-headless3.log and three external functions written. No native game process opened.
- 1409ff620 completes aim/cone/origin parameters and queries the character's context. It did not show damage application to the target; being called from the rifle does not automatically make every later helper an authoritative shot.
- Candidate caller 140a764a3 belongs to function 140a76290. Its branch requires Role Authority and two positive context values, resolves the damage type and calls 1409dc010 (area/context helper). **No vtable/owner/HitScanWeaponComponent class link was found**; therefore this candidate is NOT evidence of the rifle causing damage.
- 1409dc010 prepares queries and forwards to 1409dc270 with multiple context parameters; it may serve other weapons/explosions. Do not replace the rifle with a radial application to declare success.
- HitScan's local entry 140a60640 remains coupled to the ProcessEvent wrapper 1411e13c0 after local validation. Not executed, no chasing of RPC/inventory.
- **Native offline rifle not integrated nor demonstrated yet.** The existing proof is structure/entry/context/consumption/trace/effect; complete static damage certified only in the HMG branch described above. The local authoritative executor and the legitimate creation of the component/equip/owner still need to be identified, then a dynamic oracle. Steam being closed and a scene without a real weapon prevent a live oracle now; they do not make the negative result proof of impossibility.

## Resumed after the native damage gate PASS — without extrapolating to the rifle
- The root agent proved native application with a valid local configuration. This solves the damage context guard, **it does not prove authoritative rifle firing**.
- Precise comparison: HitScan virtual 510 = 140a65fa0 → virtual 518 = 140a68dd0 → 140a691f0; HMG virtual 510 = 140a65fc0 → virtual 540 (not the same path), virtual 518 is a trivial return. Do not swap classes/slots.
- HitScan inherits ItemComponent: helper Super 140937f50 is a thunk to StaticClass 1411e5cc0, confirmed in the executable. The native registration contains only OnRep_IsEquipped, OnRep_SimulatedHitNotify, ServerStartInvoke; ItemComponent contains only ClientSyncAmmo. **No purely local reflected shot executor in these registrations**. This evidence narrows these classes, not the whole game.
- Five extra functions decompiled in job rifle-headless4.log, terminal exit 0. Callers StaticClass 140a55fc0/140a56260 register replication of bIsEquipped/SimulatedHitNotify: they are NOT a local factory/attach/equip. 140a27ed0 finds the equipped component and writes HitNotify; it found no damage application to the target nor spawn/equip validation.
- 140a6b470 is an alternative path for building the query (forwards to 140a905c0 or 140a6b860), it does not demonstrate impact execution. 1409f3520 processes geometry/aim context/query, it did not show a direct link to the DamageAttributes/TakeDamage helpers sought.
- **Owner/equip without inventory not proven**: GetOwner/ctor/interface are not enough; current functions require a link to a native entry associated with the component. Do not write arrays/ammunition by offset to fabricate that state.
- The next investigation must link the native firing activity/shot request to the authoritative phase that consumes the rifle's data (it may be a pipeline separate from the visual trace). Until then, do not swap invented DPS for ApplyDamage per second and call it a real weapon; nor use RPC or repeat probes that were already negative.

## Closing the visual consumer and the pending contract (2026-10-11)
- Jobs rifle-headless5 and rifle-headless6 finished exit 0, readOnly/noanalysis. Protected decomp stays external in D:/tools/foxhole-lab/rifle-decomp; no address executed.
- Primary slot 510 = 140a65fa0 only has an indirect call to 518 and a return: it contains no damage application nor its own RPC forwarding. 518 = 140a68dd0 starts ActivityFiring 3, requires an associated entry with ammunition and forwards to 140a691f0. There is no hidden distinct damage in 510.
- Activity start 140b10150 → 140b0fc30 triggers state/timer transitions and presentation functions conditioned on the client. SimCharacter update 140b110c0 gets the query from the weapon's interface +E0 and writes cache +1534; the consumers of that cache examined did not show DamageableActor. This is a limit of the research, not universal absence of an authoritative path.
- WeaponFireFX: helper 1409fe9b0 creates an effect actor, orients movement and emits sound/particle. The reflected OnProjectileStop 14127c5a0 forwards to 140dec880; this consumer handles overlap/ignore actors, effect clone on a contextual character, stopping components and the end of life. There was no direct call to the known damage helpers in that consumer. Do not use this class as a substitute for an authoritative native projectile.
- Local SimCharacter 140b0b9f0 copies a 40-byte CharacterInvokeInfo, updates aim/timestamp and calls interface +250 when needed. It did not show impact→TakeDamage.
- Preconditions observed for an eventual local bridge: a legitimately built HitScan object (includes the embedded interface at +B0); a live SimCharacter owner in a suitable state; resolved native attributes/configuration; a real component↔entry association in the holder and ammunition; a finite CharacterInvokeInfo with valid origin/aim; activity state/timers and an authoritative damage context. GetOwner/SpawnComponent do not establish these contracts by themselves.
- The entry interface +10 = 140a60640 follows 518 with the ProcessEvent wrapper 1411e13c0. Do not run it as a pure offline entry. Do not write holder/ammunition by offset to fabricate equip.
- **Rifle integration remains pending:** generic native damage passed in the root agent's oracle, but it is not proof of the rifle. The local authoritative executor and a legitimate init/equip outside the inventory still need to be identified; exact ABI and bridge only after that. HMG remains the only hitscan branch whose trace→DamageableActor was linked statically in this investigation. No change to main.lua or the live context.

## Resumed — complete map of direct references and callbacks (10/11)

Four headless readOnly/noanalysis jobs finished exit 0. A references script
without a quantity cutoff, external ListNativeRefs.java. Protected decomp only in
D:/tools/foxhole-lab/rifle-authority-decomp; logs rifle-{native-refs-all,
authority-consumers,authority-timers,authority-mode-effects}.log.

- In the analyzed project, 1409dcd30 has two direct callers: 1409a71f0 and
  140a68710 (HMG), plus two DATA references. No direct caller from the
  rifle's 140a691f0 appeared. This does NOT enumerate indirect calls nor prove universal absence.
- 1409e9860 has eight direct callers: 140a68710, 140a67e40, 140a691f0, 140a8cd40,
  140d06c80, 140d007c0, 140d50940, 140d51250; three DATA references. The same eight
  use 1409d5ca0, with one additional DATA reference. Avoid investigating only the
  first six returned by a limited decompilation helper.
- 140d06c80 identifies the FighterWeaponTrace query; 140d007c0 uses AirTargetingTrace.
  So do not promote these geometry consumers to the rifle's executor.
- 140d51250 identifies HitScanMount; do not confuse mount with HitScanWeaponComponent.
  140a8cd40 uses the 140a55860 association, HitNotify, WeaponFireFX and state, without a
  direct link to the known damage helpers in that function.
- 140a67e40 and 140d50940 register callbacks 140a4ae70/140d39eb0 after comparing
  142407030 with 3. Following the callbacks: they forward to 140a6d600/140d57430,
  which manage an object created by 142575160 and position 142477180; they do not call the
  known damage helpers in those bodies. C++ names of these helpers not linked yet;
  treat them as candidate presentation, not authoritative impact.
- **A distinct guard:** 142407030 resolves the owner/world context and forwards to
  1426b9a80, whose branch returns 3 or 1/2 depending on virtual 350/a global. It is not the reading
  of Role at owner+F0 done by 142405420. Do not call the timer "Authority 3" just because of the
  literal 3; an interpretation as NetMode/presentation is consistent, without new dynamic
  proof. No guard changed nor address called.

Next cut: locate the authoritative producer/consumer of the shot data beyond
the visual trace/HitNotify and link the real class/owner/init. Do not repeat FX
oracles, do not run inferred offsets/ABI, do not look for RPC/inventory and do not use
ApplyDamage over time as a substitute. The lab stayed closed.
