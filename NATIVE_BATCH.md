# Native batch — run on 10/11; partial gates, MVP not approved

**Later logistics batch 2:** one publish/run PID4696, source 85D7EEB9…,
RWD/root/updated before-after probe completed, fresh match interrupted by a
crash 158 s after process start. Last autosave at 60 s: bmat 40/salvage 0/base 19 shirts.
Final report lost; it does not approve medevac/hiring/chain. Evidence in
`data/trace_crash_logistics2_20261011.txt` and `data/trace_truck_movement_{before,active}_20261011.txt`.
No other restart. The next sampler (logistics3) persists lines; offline only.

One publish/run CallumsCapeHex/PID19324, completed with no crash observed.
Throw/Owner/Instigator/fuse/damage/contexts/GC passed. Collision-off prevented
damage; friendly fire 100→1 observed. truck_loss FAIL (900→850, loss 0).
Fresh MVP FAIL (353 s, delivered 0/lost 110.02, bmat 40, no resource truck),
although combat/resupply/enemy chain and conservation happened.
Traces in `data/trace_native_batch_integrated.txt` and `data/trace_batch_mvp_integrated.txt`; checkers return 1
for the missing gates. Cleanup and shutdown confirmed; no second run.
The plan below is kept as a contract/reproducer, not as an approval.

## Next batch — collection/evacuation (offline candidate)
- Candidate automatic hiring checks for a threat within 35 m of the exit BEFORE the spawn
  and the debit. Validate refusal without spending, rate-limited warning, resuming after the threat leaves,
  fighters still recruitable and real loss of workers already in the field.
  Sample coordinates/threat/stock; the previous batch did not prove danger at the exit.
- Gate check_mvp_batch_trace now requires a single terminal resource record with
  known state/finite positive HP/PAWN true. A missing record is a failure, not a
  rebuild. That record alone does not prove native debit/route/support.
- The previous batch's log confirms medevac right before the two losses by
  "player order" (17:07:04 and 17:07:19). The source now distinguishes automatic retreat.
- Regression `tools/test_collection_medevac.py`: fails on the previous source, PASS on the
  candidate; real medevac/collection functions, navigation/engine mocked.
- In the next integrated session record state/cargo/orderT/medevac per worker:
  evacuation keeps the cargo and suspends collection; healing resumes field/refinery; delivery
  only on arrival; death and explicit order lose once; conservation at every sample.
- Repeat a fresh match without credits/save/extra speed. Do not remove combat
  nor conclude that this fix solves excessive replacement, deaths or the whole chain.
- Also accumulate transport/impact scenarios before publishing. No new run
  executed for this change.

## Before the single lab session
### Convoy snapshot — offline candidate, not executed
- In the native damage scenario already planned, save right after a real death,
  before the next logistics tick. Do not zero Health just to get an approval.
- Destroyed cargo does not become pending nor a free truck; the loss enters the ledger
  once, the rebuild enters once, the reward appears in the wallet of the SAME
  save. Repeating the save duplicates nothing; disappearing without HP 0 gives no reward.
- Continue must keep the loss/queue/wallet; do not confuse returning the cargo of a
  live convoy (old policy) with resurrecting destroyed cargo. Hull/TTL
  stays with the engine, without hiding/destroying it early from the save.
- test_enemy_snapshot_health.py covers real functions with a mocked engine, FAIL
  on the previous source/PASS on the candidate; wounds do not persist yet.
- Additional offline gate: HP NaN/±infinity/unknown schema in any fleet
  refuses the snapshot/save, does not touch the previous file nor debit cargo as a death.
  Do not write invalid values into the live actor to validate this case.

### NPC contract — probe prepared, not executed
- Run tools/probe_native_npc_roster.lua before the waves, during the cycle and
  after cleanup: commander, allies, enemies and pool; record locality,
  Player/Pawn/PlayerState, roster and bot/inactive. No writes and no Steam ID.
- Reuse the same session and persist external output per step. Absence/divergent
  signature is a GATE, not an authorization to change roster/flag by offset.
- The probe does not read UniqueId and does not prove the producer of the null, stability or a fix.
  Do not mark NPCs inactive nor turn off the local controller blindly: preserving
  movement/possession/GC requires tracing the effects before publishing any patch.

### Native movement — probe prepared, not executed
- Run tools/probe_native_truck_movement.lua after deployment/before
  logistics and compare with the active state. Read-only, no movement/stock.
- Record root, MovementComponent class, UpdatedComponent/Primitive and the flag
  bIgnoreNonRootComponentsDuringVehicleMovement after confirming the schema.
  Functions/input only enumerated, not called.
- If root/updated is a capsule, an actor sweep does not prove the box/meshes; even a Box
  root does not prove bridge/envelope support. Trace the native path first.
- Callums graph 405/431/4013 exists; no physically authorized edge.
  An earlier scan hit CharacterMesh0 outside the 400/162/140 box, without proving the hull.
- test_native_truck_movement_probe.py PASS for valid/divergent/extra/
  missing schema and refused scan. It is not an integrated driver nor proof of roads.

- Finish the integration of grenade, context/lifetime and the logistics reaction to native HP.
- Solve the Instigator/Owner/collision contract with the thrower and the team attribution.
- Check truck collision: current transport turns ActorEnableCollision off;
  do not assume the explosion overlap finds these actors. Do not turn it back on without
  a movement/impact rehearsal in the same batch.
- Pass `tools/test_orders.py`, `tools/test_native_context.py`, `tools/test_native_grenade.py`
  and `tools/check_globals.py`. Mocks do not replace the engine.
- Also pass `tools/test_native_truck_health.py`: integrated observer; HP 0,
  single loss, missing actor and invalid schema; no fictitious vehicle DPS.
- Prepare the commands and output of each scenario outside the repo, with no concurrent bot.

### Extended sequence prepared (syntax/mock machine PASS; NOT executed)
`D:/tools/foxhole-lab/t_batch_native_start.lua` requires an idle scene/normal time,
creates a real worker thrower + an exclusive truck, waits 12 s of native protection,
calls the integrated path and checks Owner/Instigator. Thirteen cases: refusals/cooldown,
W collision on/off, C on, reset in flight, hostile soldier/friendly fire,
thrower removal, simultaneous classes, borrowed/swapped context, logistics loss
by real explosives and reflected GC in flight. Cleanup between cases. No HP write,
manual ApplyDamage, inventory/RPC or injected input. Duration ~5 min.
`t_batch_native_report.lua` reads progress/results; it clears only the report
after the end. Damage in the collision-on cases is a gate, collision-off is an A/B
comparison, not a presumed PASS. Friendly fire is an observation of the native rule, not a promise
of no damage. Removing the thrower does NOT prove a combat death. The logistics loss
case uses 16 real/exclusive throwers, not an ApplyDamage overload;
the test cargo is an explicit fixture, not MVP economic progress.
`t_batch_mvp_start.lua` and `t_batch_mvp_report.lua`: fresh chain in the hex, 1x,
without loading a save/credits, 10 s samples, orders/recruitment through the real paths,
until a result or 420 s, audits and cleanup. It does not require a defeat to declare a cycle.
The preparation covers the six groups, but the live result will decide the gates; do not
confuse preparation with approval. A crash/prerequisite stops the batch; record it
before any restart. A functional failure without a crash does not authorize another run.

## One publish; scenarios in sequence in the same run
1. **Throw:** ally and enemy, real soldier source; native solver/movement,
   FuseTimer4 before BeginPlay, collision/bounce, no duplicated damage/FX/teleport.
2. **Limits/failures:** short/long, dead target, refused solver, invalid spawn/finish;
   no cooldown/counter debited without success, no reservation/context leaking.
3. **Damage/team:** native HP of character and truck; friendly fire behavior,
   death and safe animation/cache. Do not call vehicle death/OnRep by hand.
4. **Logistics:** displayed HP/accounting follow the real actor; cargo lost once,
   no walking after HP 0, no fictitious death by abstract convoy DPS.
   Sample partial/zero HP, check the hull for 15 s with no destruction/hiding by the mod,
   enemy ledger/rebuild/wallet, and prove that a nearby rifle does not change HP.
   An old save does not reapply its abstract HP: it restores state/cargo and uses the
   loaded actor's Health. Persisting native wounds goes to its own batch.
5. **Lifetime:** several simultaneous grenades, thrower death, reset during flight,
   borrowed context and external swap; restore only our own configuration
   after the last grenade, cancel only our own actors.
6. **MVP regression:** collection/refining/production/delivery/recruitment/supply and combat
   in the small hex; wallet/cargo conserved. No speed-up/credit to dress up the result.

Record PASS/FAIL and evidence per scenario, clean up between them and close only the
lab PID at the end. Do not open another run for a new idea: it goes into the next batch.
A blocking crash/prerequisite is a recorded exception, not an authorization for ad-hoc probes.
