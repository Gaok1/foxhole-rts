# Native grenade — offline candidate, NOT published

Base SHA256 `2F1C74D6BB205FA5610957A9B126720731CFA34DF4775329B2DDA7A82101F956`.
Assemble: `python data/parallel/native_grenade/assemble.py`.
Mocks: `PYTHONPATH=D:/tools/pylibs python data/parallel/native_grenade/test_grenade.py`.

Replaces the mesh grenade/manual arc/our own damage shell with a deferred BPGrenadeW,
FuseTimer from the real row BEFORE FinishSpawning, the CustomArc solver and ProjectileMovement.
It schedules no strikes, ApplyDamage, logi.blast or artificial explosion FX. The mortar
stays abstract and explicitly separated as debt. Cooldown/counter/animation
only confirm after the actor is finished and tracking accepted; failures clean up only the
actor created by the flow itself and release the reservation. `fire` keeps normal fire if
the grenade is refused, instead of silently losing the action.

## Dependency to be integrated by the main agent

- `rts.nativeAcquire()` → bool, reserves a pending slot and anchors a fresh ServerSettings.
- `rts.nativeRelease()` undoes the reservation on failure, restores only our own context.
- `rts.nativeTrack(actor)` → bool, transfers the reservation to tracking by name/class.
- The main agent's tick/clear/reset must keep the context while grenades are
  alive, not write into a dead UObject's cache; restore the original only if the GI
  still points to our own settings. This candidate does NOT implement another lifetime.
- The weak MyController is not written: binding/instigator attribution remain a
  gate. Owner m.pawn is passed through the native parameter already proven with playerPawn;
  this does not prove the right team against soldiers nor the granting of kill credit.

## Later live batch — still pending

1. Integrate the lifetime helpers and the candidate together with the rest of the batch, without launching
   the lab just for this helper. Validate one single publish/restart.
2. Real throw from a soldier, allies/enemies, cover, short/long
   range. Do not replace a refused solver with a teleport/manual arc.
3. Record the 4 s timer, trajectory/collision/bounce and the targets' native HP; confirm
   native damage/effect on the soldier too, death/cleanup/animation through the existing flow.
4. Confirm team/friendly fire/Owner/MyController/kill credit; the old `gdmg` counter
   does not measure native damage automatically and does NOT certify absence of damage.
5. Reset/exit/death of the thrower with a projectile in flight, several simultaneous grenades,
   spawn/solver/Finish failure and an external context swapped while the lease is active.
6. Validate GI settings restored only when all pending ones finish, without a crash;
   close only the lab PID after the batch. No automated mouse/keyboard.

17 mocks PASS prove decisions/cleanup, not Unreal. Earlier live evidence proves
only the isolated launch oracle, not this integrated `throwGrenade`.
