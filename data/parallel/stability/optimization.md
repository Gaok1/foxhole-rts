# Outline — cost and options without losing appearance

## Verified state reported by the coordinator (PID4436)

Short PASS: creation of 28 copies, deselect/reselect, death/reap with references removed,
recreation and CollectGarbage confirmed by metadata; reselection at 89 s. A test of 6 selected/168 copies
was in progress when this report was written. Cause of the original crashes not isolated; it is not a long
certification nor a result of a large selection. I did not apply optimization changes.

## Static count, not a benchmark

Per currently selected soldier (7 parts x 4): update queries the camera once, transforms sources 3 x 7,
writes clones 3 x 28 = 84 UFunctions. Update total: 106 reflected calls per frame, besides guards,
property reads and CustomDepth/stencil. For 6 soldiers: 636 update calls/frame.
`outlineDepth(true)` adds 2 per discovered component, including parts without a clone.
Unselected units and the eye keep SetRenderCustomDepth(false) per component/frame: the native code re-enables
that state, according to the real trace. The number of copies does not show GPU time nor callback cost.

## Measure before choosing

Use the already available profile(): equivalent 60 s windows with 0/1/3/6/10 selected, same units,
same map/camera/zoom, standing still; repeat while moving. Each call zeroes the accumulators. Save frames,
stratTick ms/frame and total, real clones and camera, with no extra callback. Compute:

    approximate extra cost/copy = (stratTick_N - stratTick_0)/(28*N)

This mixes CPU of depth/guards/transforms and does not measure GPU; note that limitation. Report the mean
per window and repetition, do not invent a p95 from the mean. Compare 6 unselected units with
the same 6 selected; increasing units and selection together would confuse the cost.

## Proposed optimization order

1. **Camera queried once per stratTick**, passed as an optional parameter to updateOutline.
   Saves N-1 reads/frame, keeps full geometry; small cost, test before applying.
   A direct updateOutline caller must keep working; snapshot only of the same frame, never an eternal cache.
2. **Copies' rotation/scale only when the computed transform changes.** Compare numeric values
   per part with the last transform, not table identity. Copies keep using the MasterPose pose;
   sources and camera must be queried every frame. A standing case can avoid 56 writes/soldier/frame.
   Risk: the engine also changes the transform through attachment; skipping location without measuring the effect loses the homothety.
   So the first experiment is only scale/rotation, not position; invalidate the cache on cleanup/recreation.
   Check a rotating source, moving camera, replaced equipment, high zoom and several screen positions.
3. **One emissive MID per set**, applied immediately to the copies as an engine root.
   Same color, no different appearance; reduces the creation of 28 MIDs/soldier to 1, but no continuous cost
   shown. Only useful if the selection/GC peak is measured. Do not keep a MID only in Lua userdata.
4. **Avoid rewriting the stencil when it is already 1**, only if a safe reflected read/contract is confirmed.
   Do not remove CustomDepth writes: the trace shows native re-enabling on friends/the eye.

No LOD by removing parts/copies and no updating the outline at 10 Hz: these options reduce fidelity or
tracking and do not meet the approved appearance. Do not create a new scheduler/callback per clone.

## Native alternatives actually found

`M_OccludedOutline` is a native PostProcess material already traced and anchored in the volume; it provides an occluded
fill, not an edge on visible parts. So it does not replace the 28 copies alone.
`SetMasterPoseComponent`, KeepWorld attachment and CustomDepth/stencil were used and traced; no
general native edge shader was shown in the current data. A cooked shader is a research alternative,
not a ready asset nor a proven solution. Do not try reading MasterPoseComponent/AnimClass (recorded crash).

## Gate for any proposal

Real test of the functions, reflected counter with mocks before/after, the same existing projected formula;
integration by the coordinator, clean load, comparison capture and measurement. Lifetime before performance.


## Measurement received and checked (PID4436)

`D:/tools/foxhole-lab/stability-group-live.txt`: 32.30255 s / 1400 frames; 6x28 copies;
stratTick 16.72 ms/frame, mod 17.70 ms/frame. 94.46% of the mod's measured time in that step.
It is a real bottleneck. 16.72/168 = 0.09952 ms/copy as a RAW ratio, not an incremental cost without a baseline.

Revised priority: measure the control with the same 6 unselected; then try combining the transform
into one UFunction instead of 3 per clone. Look for `K2_SetActorTransform` in the loaded metadata before
calling: if reflected and the contract is confirmed, build the FTransform correctly (quaternion, not an invented
Rotator) and compare with the three setters. It could reduce 84→28 writes/soldier/frame without sacrificing
geometry. No record of that function in the current data/tools/mod was found; it is not yet a locally
shown contract. If missing, test the existing setters with a numeric scale/rotation comparison.
Do not remove lifetime validation nor depth just to reduce time.

Architectural alternative without a visual cut: a single proxy containing 7 parts and 4 offsets rendered
in a cooked shader; removes extra actors and per-copy setters. Requires an own UE4.24 asset and proof of pose,
outline and occlusion, so it is not a safe immediate change. Only start cooking after sweeping local
materials and confirming there is no edge shader available. No downloads/installs in this analysis.


## Schema probe prepared (not run)

`D:/tools/foxhole-lab/t_outline_transform_schema.lua` enumerates the parameters of K2_SetActorTransform,
Transform/Quat/Rotator fields and KismetMathLibrary functions filtered by Quat/Rotator, MakeTransform,
BreakTransform. Metadata only; no actor change, setter/converter call or new callback.
Uses ForEachProperty/GetStruct already shown in t_sigs.lua/t_findfn2.lua. After confirmation:

1. Confirm the order/types of the parameters and the Rotation/Translation/Scale3D layout from the real output.
2. Confirm a native Rotator→Quat converter (or MakeTransform) before forming the FTransform.
3. On an isolated and healthy probe clone, apply the current setters for known p/rot/scale and read the result.
4. Apply the single setter with the same transform and compare location/rotation/scale; include yaw 77,
   pitch -60/roll 13, non-uniform scale and negative positions. A quaternion roundtrip may change representation;
   compare the result as an effective rotator/projection, not only bytes/quaternion sign.
5. Only integrate after confirming attachment/KeepWorld and movement/camera in a real frame. Convert once
   per part, not per copy; MakeTransform+setter per copy may reduce 3→2, not 3→1, if not reused.


## Consolidated transform delivery

Coordinator's native oracles PASS: outline-transform-oracle-live.txt and
outline-transform-packed-live.txt (copied table; case 3 error 7.63e-06).
`transform.before.lua`/`transform.after.lua` replace the whole updateOutline: MakeTransform once
per part, quaternion copied into a Lua table, scale projected once/part and Translation per copy.
No manual quaternion math, no change to appearance/copies/guards. Update count:
1 camera + 21 reads + 7 MakeTransform + 28 setter = 57/soldier (before 106); 46.23% fewer calls of the function,
but no time gain claimed until a new measurement. Mathlib cache in rts, no top-level local.
`test_transform.py` PASS: 8 copies/2 parts/3 cameras, same geometry/rotation/scale; setters 72→24,
6 conversions. The mock uses marker encoding, it does not implement quaternions: the native oracle is the proof of this step.
`orders_transform.before.txt`/after.txt adapt the existing test's mocks in two blocks; I did not change
the real file. The integrator applies them and runs test_orders with the integrated function.


## Cost regression after transitions — do not claim a sustainable gain

Log `stability-optimized-after-gc-profile.txt`: 95.4164 s since the group; 1873 frames,
stratTick 16.40 ms/frame, mod 17.46 ms/frame, still 28 copies for 6 soldiers. The first optimized window at 7.91 ms
does not represent a sustainable gain. Correct geometry/setter does not prove a stable cost.

Hypotheses, NOT causes:
- The profile measures only the Lua/UFunction part of stratTick, not the general native tick/GPU. More old actors could
  slow down the engine/calls, but a MasterPose requirement/accumulated tick cannot be deduced from a mean.
- `clearOutline` erases refs even when DestroyActor fails through pcall. Live copies without a reference may
  accumulate. IsValid true for destroyed ones is expected until GC; count both separately.
- Component lists may grow/swap: 28 clones does not tell the number of sources/depth of a pawn.
- Collection/reselection creates a spawn/MID peak; the profile includes creation work in stratTick. The mean mixes
  peak and steady state if there is no reset after the transition.
- `profile()` zeroes accumulators, but external timestamps do not always follow the reset. 1873 frames do not
  prove a 95 s window duration; TIME is since the group, not the last reset.

Prepared probe `D:/tools/foxhole-lab/t_outline_phase.lua` (not run): no callback/hotpatch;
the command closes the previous window's profile, counts selected/tracked, FindAllOf SkeletalMeshActor active/being
removed/invalid and live untracked, then opens a new timestamp. The first window is discarded.
The untracked count includes possible native actors: compare against a baseline, do not call them all a leak.

Comparable protocol:
1. Clean load, 6 units standing still, unselected; start the probe, wait 60 s, probe (control).
2. Select 6; wait 5 s of settling; the probe discards the peak; wait 60 s; probe (window S1).
3. No transition, 60 s more; probe (S2); 60 s more; probe (S3). This tells degradation over time apart.
4. Deselect/reselect a single time; wait 5 s; the probe discards the peak; 60 s; probe (R1).
5. 60 s more without a transition; probe (R2). If live untracked grows, check the DestroyActor return/log.
6. Confirmed GC in a separate phase, wait 5 s, reset by probe; 60 s; probe (G1); 60 s more; probe (G2).
7. Only then death/recreation of 6; same protocol. Repeat in reversed order on a clean load to separate order effects.

Record hash, PID, map, frame count and real duration of each window. Do not capture the screen nor run
wide searches during a window. Do not repeat profiling through a temporary callback nor hide peaks:
peak reported separately, steady state in a separate window. Do not touch MasterPoseComponent/AnimClass.


## ComponentToWorld — next proposal, not integrated yet

Phase S1 reported by the coordinator: 61.86 s/2447 frames/stratTick 15.72 ms; 207 actors/168 tracked/39 native,
with no count increase. This weakens actor accumulation in that window, it does not rule out other costs.
`K2_GetComponentToWorld` returns an FTransform according to real SceneComponent metadata found
in the ESTRADAS task. A prepared oracle (not run here) compares 3 getters+MakeTransform with that return;
quaternion aligned by sign. The artifacts component_transform.before.lua/after.lua propose replacing 4 reads/
conversion with 1 read/part, without geometric/guard changes. 36 calls/soldier instead of 57 update/frame,
a 36.84% relative reduction in calls, without claiming ms. test_component_transform.py PASS on Lua/geometry decisions.
orders_component.before.txt/after.txt adapt the shared mocks in 2 blocks, without editing the real test.
