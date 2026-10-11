# Grenade contract — offline evidence and pending gates (10/11)

## Evidence checked in this session
- Extracted reflection: Actor.Owner at +E0; Actor.Instigator at +118;
  Pawn.Controller at +258; WarProjectile.MyController is a WeakObjectProperty at +260.
- WarProjectile vtable +468 resolves to function 140dbe460. It registers OnProjectileStop,
  gets the Instigator through 1422d9d90, adds the pawn to the ignored-collision list and gets
  its Controller through 1422d9da0 to fill MyController natively.
  Both getters were checked in the instructions of the lab binary.
- BeginPlay 140da4a70 also ignores the Owner with 1424435c0 and adds the character's attached
  parts to the ignored list. Therefore Owner and Instigator are not interchangeable:
  both must be the thrower before FinishSpawning, not the invisible commander.
- Explosive application 140da33d0 requires authority, resolves the native attributes of the
  explosive identity and passes MyController to the area damage helper 1409dc010.
  Do not write the WeakObjectProperty nor build HitInfo/a formula in Lua.
- `trace_binding_launch.txt`: GrenadeW fuse 4/min 390/max 1100/range 0;
  GrenadeC fuse 4/min 390/max 1200/range 0. `schema_projectiles_native.txt` maps
  Grenade_C to GrenadeC and BPGrenadeW_C to GrenadeW. The candidate now uses each faction's.

Protected external sources, not redistributed: D:/tools/foxhole-lab/explosivo-decomp,
D:/tools/foxhole-lab/re-agent/explosivo-owner-props.txt and explosivo-pawn-props.txt.
No offset executed; only reading/existing decompilation and the binary's getters.

## Not proven yet in the integrated main
- Attribution/friendly fire and character reaction; read Owner/Instigator/Controller
  after FinishSpawning in the gate. The target's configuration/team does not prove the impact's team.
- Overlap/damage on a logistics truck with ActorEnableCollision false. Compare with
  true on an exclusive actor, in the same run; do not turn the fleet back on by assumption.
- Origin inside the capsule, short/long trajectory, thrower's death, grenades of
  different classes at the same time, reset during flight and context restore.
- The old oracle without an Instigator does not certify this complete flow.
