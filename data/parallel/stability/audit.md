# Initial outline audit — 2026-10-09

Static reading, not a diagnosis of the native cause. No fix applied and no new live validation.

## Evidence from the current code

- `destroyMarker` calls `anim.untrack` and `rts.clearOutline` before removing the other markers.
- `clearOutline` destroys the copies, erases `outlineSources` and clears `outlineParts`.
- `updateOutline` calls UFunctions on stored sources and copies without revalidating their lifetime on each use.
  The source may stay `IsValid` until GC; that test alone does not prove safety.
- `outlineDepth` keeps the component list until `clearOutline`; equipment replaced while
  the unit stays selected deserves a specific reproduction.
- `setOutline` protects creation with pcall, but pcall does not protect native failures. Its rollback is not
  evidence of safety against GC/component replacement.
- The fill MID is anchored through `AddOrUpdateBlendable` before configuration; the copies' MIDs
  are tied to the components. Do not attribute the crashes to MIDs without showing loss of these references.
- The main loop uses `LoopInGameThreadAfterFrames`; the batch 17 Registry error requires separating
  the mod's persistent callback from the probes' temporary callbacks. Do not repeat a hotpatch as clean proof.

## Proposed reproduction for the lab owner

1. Clean load; record hash, PID, map and start/end of each step in a file outside the repo.
2. Control without selection; then one selected soldier, without extra sampling callbacks.
3. Toggle selection and clear/recreate soldiers; record copy and source counts per step.
4. Death of the selected one through the mod's own system: check reference removal before the health
   notification, without accessing the AnimInstance/body after the transition.
5. Test components separately in isolated experimental variants, keeping the approved source.
6. Test garbage collection only with a previously confirmed reflected call and in a separate step.
7. Only then increase selection and measure per-frame cost; stability and appearance are separate gates.

Criterion: record which transition fails and reproduce on a clean load before concluding a cause or fixing.
No absence of a crash in a short test proves long-term stability.


## Complementary audit — stability agent, 2026-10-09

### Defect proven offline and proposal delivered

`updateOutline` (main.lua:3800) does not test pawn/clone being destroyed nor source validity before calling
UFunctions. `test_lifetime.py` runs the real function extracted from the source: the three cases keep accessing
components/actors in the current version. The replacement `update_outline.before.lua` → `update_outline.after.lua`
clears the set before any access in those states. Live case preserved. Result: OK on 2026-10-09.
The proposal does not change main.lua. A live gate is mandatory before saying it fixed the crashes.

Limits: a source still IsValid during destruction is not caught; components replaced but alive are also
not detected. `bActorIsBeingDestroyed` is an actor property, it must not be invented on the component.
Do not read MasterPoseComponent/AnimClass. This defense covers observable states, it does not show native safety.

### Callers and cleanup order

- `setMarker` calls `setOutline`; `stratTick` repeats per frame for allies/enemies and clears CustomDepth of the eye.
- `reap`: `destroyMarker` → `clearOutline` → `anim.retire` → `OnRep_Health` → body TTL. Correct order
  on the common path; `anim.retire` has only that caller. The existing death test covers the order.
- `resetCombat`/session cleanup and enemy removal: `destroyMarker` before `K2_DestroyActor`.
- `corpseTick` destroys bodies already removed from lists and without an outline; save/continue calls OnRep_Health for live HP.
- Medic, tents and points notify OnRep_Health with positive HP. It was not shown that they replace meshes.
- `clearOutline` captures clones in a list, destroys them with pcall and zeroes sources, then clears depth. If a clone's
  destruction fails in Lua, the reference is discarded anyway; a clone may remain. A native failure is not contained.
- `outlineDepth` reuses components until cleanup. An equipment swap while selected may leave old
  copies/depth: a functional hypothesis to reproduce, not an attributed cause of the crashes.
- `outlineFill`: MID referenced by the volume's blendable; the clone's MID by the component's material.
  A Lua cache does not guarantee a GC root, but there is engine anchoring in the code. Do not attribute GC without a test.
- Creation tests IsValid but not bActorIsBeingDestroyed on the clone spawn's return; similar to the documented
  truck problem. Requires a probe/simulated failure before widening the patch.

### Persistent callbacks

There is a main loop `LoopInGameThreadAfterFrames(1, ...)`, an animation hook per ABP, controller hooks,
the channel loop `LoopInGameThreadWithDelay(1000, ...)` and the keys' ExecuteInGameThread callbacks.
No per-clone callback is created by the outline functions. So the number of clones does not show
growth of callback references. `Lua::Registry::get_function_ref` still has no isolated origin.
A hotpatch/probe with an extra callback is not a clean control for the main loop.

## Probe matrix for the coordinator (not run here)

All on a clean load, hash/PID/map/log at start and end, no botloop, no hotpatch, no injected input.
Temporary variants through a copy of the preserved source; only the lab owner publishes.

| Step | Variant / transition | Minimum evidence | Gate |
|---|---|---|---|
| A | No selection, 10 min, no new callback | live frame log/start-end, crash/log | control |
| B | 1 selected, 28 clones, 10 min | part/source count, frame/prof, capture | base reproduction |
| C | Same as B + proposed patch | same times/state | compare, do not conclude from a short absence |
| D | 100 select/deselect in a frame state machine | clones created/destroyed and nil after cleanup | zero residual reference |
| E | 20 death/recreation by the mod | cleanup before OnRep_Health, no later access | lifetime |
| F | 1 part per run: coat, weapon, head, hands, legs, back, helmet | 4 clones/part and variant hash | isolate the part |
| G | Skinned clone without MasterPose vs with MasterPose in separate runs | actors/time/stack | MasterPose hypothesis, appearance only diagnostic |
| H | Equipment replaced while selected | real list before/after, current clone source | stale cache |
| I | Reflected GC only after confirming the call in the game data | before/after and stack/log | GC hypothesis |
| J | 1/3/10/25 selected, high zoom, 60 s per step | profile stratTick ms/frame, 28*N actors, capture | cost |

Measurement probes use the existing per-frame state, not dozens of temporary UE4SS callbacks.
Do not automate F/G/I until the reflected contract is confirmed. Every failure repeats a clean load on the same hash before
attributing a cause. Separate stability, appearance, real input and performance.

### Suggested Gotcha for universal-modder (integration by the coordinator)

The outline update called UFunctions even with a pawn/clone bActorIsBeingDestroyed or source IsValid=false;
a mock reproduces it and a preflight blocks it. This does NOT explain the batch 17 UE4SS crashes; a source IsValid=true during
removal/swap still needs a real trace. pcall protects Lua errors, not native lifetime.

Coordinator's review: the guard was also applied in outlineDepth so cleanup of a pawn being destroyed does not touch sources. The test passed using the REAL clearOutline/outlineDepth extracted, not a cleanup stub. Apply the two blocks separated by a blank line, do not replace the whole document.
