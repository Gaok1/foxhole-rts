# MANUAL COLLECTION — report (candidate v3)

Delivery of the COLETA_MANUAL agent. Everything in this folder; `main.lua`, shared docs and other agents' folders **were not edited**.
Offline (lupa Lua 5.4 and 5.5): **nothing here proves Unreal physics, a real route, animation, input or balance** — see "What requires the lab".

- Base read (read-only): `data/parallel/integration_rehearsal/candidate_v2/main.lua`, SHA256 `a93c1531588ea4534a7791dbb2e9578654ad0fa4a87373be1cbed569cbc3eda6` (unchanged before/after the build).
- Output: `candidate_v3/main.lua` (CRLF), SHA256 **`9b89b1136509d9e4416a8f80dd3aa6b3ed2a491df61bcb7c0afec35cb34d63e6`** (6644 lines, 337,990 bytes).
- Patch: `manual_collection.patch` (CRLF, applies to `candidate_v2/main.lua` with `patch -p1`/`git apply`; +359/-14) and `manual_collection_lf.patch` (for reading).
- The mod's real `main.lua`: SHA256 `33d6c7e5920a…` intact (checked at the start and at the end of the stack, step 99).

## 1. Problem and the user's decision

With the resource truck destroyed, `bmat = 0` and `salvage = 0`, the factory has nowhere to get the 100 bmat for the rebuild and the chain freezes
forever (`test_truck_bmat.py`, "known limit"). Decision: **slow manual collection** — soldiers collect salvage on foot; nothing is born from
nothing and no truck is free. Widened in three messages: manual collection is the **normal start of the match** (RTS villager style), the
worker is a soldier without a rifle spawned at the base for 1 shirt, and the spawn uses the common interface of `forward_bases/SPEC.md` §4.3.

## 2. Origin of the numbers (read this before balancing)

| Value | Where it comes from |
|---|---|
| truck costs **100 bmat**; ratio **2 salvage : 1 bmat**; truck load 100 | already in the mod (`CFG.LOGI.truckCost`, `ratio`, `trip`) and in `data/game_costs.txt` |
| deployment **1000** (refinery 400 + factory 400 + 2 supply trucks 100) | sum of the real costs above; it was 1100 with the resource truck |
| **`rate = 0.5` salvage/s, `cap = 40`, `workers = 3`, `bmat0 = 40`** | **My design PROPOSALS.** There is no manual collection value in `data/` nor in `MECHANICS_STUDY.md` (the game has no on-foot collection of this kind in this copy) |
| radii/times (`fieldR 1000`, `refR 1500`, `stand 600`, `quiet 60`, `pause 60`, `leg 180`…) | engineering choices, adjustable in `CFG.COLETA` |
| `bmat0 = 40` | `CFG.LOGI.bmat0 = 240` would buy the truck on the 1st tick and collection would never happen; 40 keeps the factory poor on purpose |
| `startRifles = 10` | indicated by the spawn interface (§4.3) for the main base; only applies in the manual match |

## 3. Design

Everything in `CFG.COLETA`/`CFG.SPAWN` and in the `logi` table (**no new top-level local**: 175 by the `check_globals` counter, the same as v2; 22 of headroom to the 200 limit).

1. **Start without a resource truck.** `CFG.COLETA.manualStart = true`. `Alt+L` deploys refinery + factory + **2** supply trucks (budget 1000, 4 actors).
   `logi.start` creates the resource truck already "dead" (`state="dead"`, no actor), `bmat = 40`, base with `max(shirts0, workers)` shirts and 10 rifles.
   `logi.trucksNeeded()` replaces the fixed "supply+1" in `scan`/`deployPlan`/`infraPlan`.
2. **The factory builds the truck** through the rebuild that already existed (`logi.truckStep`, 100 bmat, reserve `reserva_bmat`), now with **automatic
   priority** (`resFirst`): the resource truck is rebuilt before the supply trucks and the crates. Since there is no actor, `logi.spawnTruck` creates it in the field (visual; the cost was already debited).
3. **Workers** = real soldiers, `role="worker"`, weapon `CFG.WEAPONS.worker` (`grip=0`, range 0: never fires).
   `logi.colMaintain` keeps up to `workers` (3) alive **while collection is needed**, replacing the dead, one shirt each.
4. **Spawn interface (§4.3), only for the worker:**
   `site, why = logi.spawnSite(role, cursor, opts)` is **pure** (changes no stock and creates no actor) and returns
   `{dep, kind="base", name, at={X,Y,Z,exact=true}, need, explicit}` or `nil, reason` ("função sem receita", "ramo legado", "sem camisas em base",
   "camisas reservadas aos trabalhadores da coleta", "nenhum local de nascimento permitido");
   `ok, why = logi.spawnCommit(site, role)` runs **once, after the confirmed actor**, revalidates the stock and debits (the only assignment of `.shirts` in the new code — verified by static analysis in the test).
   If the commit refuses after the actor was created, the actor is undone (`anim.untrack`, destroy, release the controller). `recruit()` **was not migrated**: it only respects the workers' shirt reserve.
   `CFG.SPAWN.roles.worker = {shirts=1, sites={"base"}}`; `workerDepot()` is the isolated point the forward bases swap.
5. **Collection.** States `toField → gather → toRef`, route through the mod's A* (`routeTo`), movement through `squadTick`. Salvage only becomes stock (`logi.salvage`) **on arrival at the refinery**; cargo in hand is never credited.
   Ledger checked every frame: `collected = delivered + lost + in hand`. Active only with the resource truck missing/dead **and** a lack of bmat (`bmat + salvage/2 < 100`); it vanishes when the truck comes back.
6. **Cache safety (the `anim.untrack` rule).** Never keeps a pawn/userdata between frames: it keeps the soldier's record and, before any call, revalidates squad membership + `alive` + `not bActorIsBeingDestroyed`. Invalid pawn = **zero calls** (the test counts `pawn.touched`). `logi.reset` discards the collection without touching a pawn.
7. **A player order takes the worker out of collection** (march, `hold`, focus, area, retreat, evacuation, queue; the cargo is discarded and recorded). It only comes back after `quiet = 60 s` without an order. For that the queued order (`Shift+right`) now sets `orderT`, like the others (anchor 4c; it changes only that mark).
8. **Combat**: danger (enemy < 35 m, recent fire/suppression, health < 80%) prevents recruiting and pauses gathering; continuous combat > 60 s drops the collection (cargo lost). Stuck > 180 s on a stretch: drop.
9. **Persistence**: the save's v2 schema **did not change**. Cargo in hand is not saved (discard recorded in the log "descartada (reinício)"); workers come back as `role="worker"`; collection restarts on its own.
10. **Panel**: one line only when there is collection, e.g.: `coleta manual: 3 trabalhadores | 40/100 bmat para o caminhão | 25 sucata em mãos`.
11. **Old path preserved**: `manualStart=false` restores the 3-truck/1100 deployment and the old `bmat0`; collection becomes only a rescue from the freeze (back in 264.9 s).

## 4. Measured numbers (offline, harness geometry: field 80 m from the refinery, walking 400 cm/s)

| Measurement | Result |
|---|---|
| **X** — 1st resource truck in a new match | **165.5 s** (collected 120 = delivered 120, 3 trips of 40) |
| 1st crate delivery after the truck | 63.0 s later |
| **Y** — losing the truck with `bmat=0`, `salvage=0` | back in **243.2 s** |
| Old freeze (v2, same scenario, 900 s) | **never** comes back; v3 with the legacy start comes back in 264.9 s |
| Collection vs. truck | 1.00 salvage/s (3 workers) vs 6.33 for the truck: **6.3× slower** |
| Mutation `resFirst=false` | inverts the rebuild order (the test is not vacuous) |

Sensitivity (`SENSITIVITY.txt`, `sensitivity.py`; seconds until the 1st truck; 3 workers, cap 40, rate 0.5 except the varied column):

| | 80 m | 260 m | 470 m |
|---|---|---|---|
| 1 worker | 373 | 637 | 951 |
| 2 workers | 259 | 435 | 645 |
| 3 workers | 165 | 254 | 359 |
| cap 20 | 187 | 363 | 573 |
| cap 80 | 245 | 334 | 439 |
| rate 0.25 | 245 | 334 | 439 |
| rate 1.0 | 125 | 214 | 319 |

Reading: the time grows mainly with the field–refinery **distance**; 5 workers do not help the 1st truck (3 trips of 40 are enough). `cap` 80 does not help in the short run: the 1st load takes 160 s to fill (at 0.5/s) and the truck only needs 120 in total.
In HomeRegionW (field ~470 m from the refinery) the 1st truck leaves in ~6 min with 3 workers, not ~3 min.

A real bug was found by the table and fixed: accumulating `rate*dt` in floating point stopped the load at 39.999999, the delivery stayed at 119.99999 and a whole trip was missing
for the `bmat >= 100` threshold. A full load is now pinned exactly at `cap` (the `collected` ledger adds the difference).

## 5. What was tested (all PASS; full output in `TEST_OUTPUT.txt`)

General command: `cd /d/GitHub/foxhole-rts && bash data/parallel/logistics_ai/finishing/manual_collection/run_all.sh` (rebuilds the candidate and runs everything; `rc_final=0`).
Each individual command: `cd /d/GitHub/foxhole-rts && PYTHONPATH=D:/tools/pylibs PYTHONDONTWRITEBYTECODE=1 python data/parallel/logistics_ai/finishing/manual_collection/<file>.py`.

| File | Cases | Covers |
|---|---|---|
| `test_manual_match.py` | 14 (7 × 2 Lua) | new match without a truck → X; manual → truck → crates; losing the truck → Y; no bmat/salvage without collection (spawn failure, no shirts, frozen workers, full squad, commanded); `resFirst` priority (+ mutation); `manualStart=false`; deployment 1000/4 actors (v2: 1100/5) |
| `test_collection_core.py` | 18 | a healthy chain **never** activates collection (4 scenarios); collector dies with cargo; player order removes from collection; combat; revalidation of an invalid pawn; slower than the truck; panel; shirt reserve; **fuzz** 20+5 seeds × 600 s with ledger and delivery checked every frame |
| `test_freeze.py` | 4 | the old deadlock: v2 freezes, v3 solves it; manual match under continuous consumption |
| `test_persistence_collection.py` | 10 | save/continue during collection (identical bmat/salvage, nothing credited); 4 identical cycles; the same session discards and records; save with a v3 deployment; a v2 save opens in v3; v2 refuses a v3 save |
| `test_spawn_interface.py` | 9 | pure `spawnSite`; refusals with a reason; `spawnCommit` debits only after a confirmed spawn and revalidates; a refused commit undoes the actor; starting stock (10 rifles, shirts ≥ 3) and legacy intact; only `spawnCommit` assigns `.shirts` |
| `test_orders_v3.py` | mod suite | `tools/test_orders.py` against v3 (in-memory copy), with the adaptations below |
| `test_stack_v3.py` | 22 steps | adapted copy of `integration_rehearsal/test_stack.py` pointing at v3: reproducible build, syntax 5.4/5.5, 200-local limit (175), clean `check_globals`, test_orders, costs, economy, AI, elogi, bmat_caminhao, panel, persistence v2, roads, patches in sequence, alternative orders, intact at the end. **22 PASS, 0 FAIL** |

Also: `tools/check_globals.py` against the candidate: no output, rc 0.

### Changed expectations (each one documented in the code)

`test_orders_v3.py` (`ADAPTACOES`, printed on each run): (1) `start()` leaves the resource truck to be built — the factory flow block makes it alive; (2) deployment plan 1100/3 spots → 1000/2;
(3) wallet 1099 → 999 and 1100 → 1000; (4) rollback keeps 1000; (5) deployment creates 4 actors (not 5) and spends 1000, twice; (6) the starting parking tolerates the resource truck without an actor.

`test_stack_v3.py` runs the stack's persistence suite in **two** variants: the new-numbers one (`V3_PERSIST_ADAPT`, conditional on the candidate stack through `_v3()`, because the same suite also runs the stack **without** collection, which stays at 1100/5):
actors 5→4, wallet `0/1100/5`→`0/1000/4`, live trucks 3→2, balance 300→200. And `V3_ELOGI_ADAPT`: in `t_no_module` the load world gains 1 native truck, because a mod **without** collection requires 3 trucks and the v3 save paid for 2.
Steps **06b-L** and **08-L** run the same suites **without any change** with `manualStart=false`: the old path is intact. `diffs/test_stack_v3.diff` shows everything that changed relative to the original `test_stack.py`.

## 6. What requires the lab (none of this was seen)

- **Real movement of the workers**: collision, getting stuck on an obstacle/snow, the real A* from the field to the refinery, arrival within `fieldR`/`refR` (the harness uses a flat world).
- Whether the salvage field and the refinery are **actually** reachable on foot on the map (HomeRegionW) and at what distance; adjust `fieldR`/`refR`/`stand`.
- **Animation without a weapon** (`grip=0`): the soldier spawns without a rifle without breaking `ABP_Male_C` (no T-pose, no animation hook crash). `spawnSoldier` with `role="worker"` and the new `CFG.WEAPONS` entry.
- **Visual of the spawned resource truck** (`logi.spawnTruck`, in the field): valid actor, position on the ground, not being destroyed, not stuck on a roof.
- **Per-frame cost**: `colStep` runs every `logi.tick`; it is O(collectors) plus, every 0.5 s per collector, a sweep of the enemies. Measure in a real match.
- Human flow: select/give an order to a worker, see them leave collection and come back 60 s later; panel; messages; save/continue with workers in the field.
- Enemy vehicles/terrain: whether the workers survive a wave on the way to the field.

## 7. Risks

- **A v3 save does not open in v2** when there are workers in the squad (unknown `worker` role) nor when the deployment paid for 2 trucks (v2 requires 3). v2 → v3 opens.
- Workers take `SQUAD_MAX` slots and are targets like any soldier; a full squad prevents spawning (warning every 30 s).
- Long collection: stretches > `leg` (180 s) are aborted and the cargo is lost; on very distant fields increase `leg` or `cap`.
- Minimal side behavior change in existing code: the queued order now sets `orderT`.
- The real `spawnSoldier` was never called with `role="worker"` (mock in the harness).
- The manual match is slower on purpose; if the balance is bad, `manualStart=false` restores the old behavior with no other code.

## 8. What the player will notice (for README / MANUAL_TEST)

- New match: the deployment (Alt+L) costs **1000**, not 1100, and brings refinery, factory and **2** supply trucks — **no resource truck**. The panel shows the resource truck as destroyed/to be built.
- The base starts with **40 bmat** (before 240), 10 rifles and shirts.
- ~5 s later **3 soldiers without weapons** appear near the base (each spends 1 shirt), go to the salvage field, collect and take it to the refinery. Panel: `coleta manual: N trabalhadores | x/100 bmat para o caminhão | y sucata em mãos`.
- The factory now **keeps 100 bmat** and builds the **resource truck** before the supply trucks and the crates; it appears in the field, collection stops on its own and the workers are free. Messages: "COLETA MANUAL: …" and "caminhão de recurso pronto: coleta manual encerrada".
- Losing the resource truck later, without bmat/salvage, **reactivates** collection (before, it froze forever).
- Any order given to a worker takes them out of collection (cargo in hand is lost); without an order for 60 s they come back on their own. Dead workers are replaced while there are shirts.
- Recruiting combat soldiers (Ctrl+1…4) does not spend the shirts reserved for the workers while there is no resource truck (its own message).
- Saving during collection: salvage in hand is not saved; on continue, collection restarts (message in the log).
- No new key.

## 9. Open balance decisions (they belong to the user)

1. `bmat0 = 40`: 40 + 60 (from 120 salvage) = 100. More starting bmat shortens the start; 240 eliminates collection.
2. Deployment budget `1000` (2 supply trucks). The resource truck could be paid separately or 1 supply truck cut.
3. `rate = 0.5`, `cap = 40`, `workers = 3`: see table; 3 already saturates the 3 trips of the 1st truck, 5 only helps replacements.
4. Workers use `SQUAD_MAX` slots (alternative: their own list, more code and persistence).
5. Workers are only kept/replaced while collection is needed (afterwards they stay as idle soldiers without a weapon, they do not vanish).
6. **Field–refinery distance**: ~470 m in HomeRegionW gives ~6 min until the 1st truck with 3 workers (2 min 45 s in the harness at 80 m). Maybe sustain more collectors, a larger `cap` or a closer field at the start.
7. `startRifles = 10` at the main base (indicated by the spawn interface); only applies in the manual match.
8. Shirts: if the base runs out of shirts and the workers die, nobody spawns and collection stops (warning in log/notify). The reserve only protects `recruit()`; new shirts come from the factory and the supply trucks. Decide whether there is a minimum shirt floor.

## 10. Files

`build_collection.py` (generates everything; unique anchors, fails if any is not), `collection_cfg.lua`, `collection_funcs.lua`, `manual_collection.patch`, `manual_collection_lf.patch`, `candidate_v3/{main.lua,SHA256.txt}`,
`harness_collection.py`, `test_manual_match.py`, `test_collection_core.py`, `test_freeze.py`, `test_persistence_collection.py`, `test_spawn_interface.py`, `test_orders_v3.py`, `test_stack_v3.py`, `diffs/test_stack_v3.diff`,
`sensitivity.py`, `SENSITIVITY.txt`, `run_all.sh`, `TEST_OUTPUT.txt`, `test_output_v3.txt` (detailed stack log), `LAB_SCRIPT.md`.
