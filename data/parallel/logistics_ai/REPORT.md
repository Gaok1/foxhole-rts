# IA_LOGISTICA: enemy chain and strategic interdiction (isolated proposal, 2026-10-09)

Agent: CLAUDE_IA_LOGISTICA. All work offline. I did not edit `main.lua`, any shared doc, the
lab nor universal-modder. This folder has a module that goes into `main.lua` through a generator with unique
anchors, the tests that run the **whole** candidate `main.lua` in memory (lupa), the lab script and
the proposed gotchas.

**Honest state:** audit, design, conservation and traceable effect are proven **offline**. Nothing was
validated live: the real BPTruckC truck, the route, performance, combat balance and the in-game save
remain LABORATORIO gates (`LAB_SCRIPT.md`). The task stays `[ . ]`.

## 1. Audit of the current main.lua: real stock or abstract bonus

The audit can be run: `test_base_audit.py` runs the current `main.lua`, without the patch, and confirms
A1 to A6.

| # | What exists today (line of the current main.lua) | Classification |
|---|---|---|
| A1 | `logi.convoyTick` (3029-3066): the enemy truck reaches the front and adds `combat.cargo + 1`. The truck carries nothing and no stock is debited. There is no rear, production nor cost. `logi.convoySpawn` (2981) creates a convoy every `ECONVOY.every` = 35 s, unconditionally. | **Abstract**: cargo created from nothing. Destroying the convoy only prevents a future +1. |
| A2 | `logi.waveCut` (3069-3079), called in `waveTick` (4205): each wave spends up to `perWave`=2 cargoes; each missing cargo removes `cut`=2 soldiers; the floor is 3. | **Abstract**: it is a counter. The maximum effect is −4 soldiers per wave. |
| A3 | `logi.start` (2681) sets `combat.cargo = cargo0 = 2`. `logi.snapshot` (3081) saves neither `combat.cargo` nor a convoy in transit. On continue, `logi.restore`→`start` always gives back 2 cargoes. | **Abstract, with a bug**: save/continue gifts cargo or erases cargo. |
| A4 | Enemy fire: `fire` and `areaStep` only deduct ammo with `if ours` (1649, 1967). | **Abstract**: infinite enemy ammo. **Not changed** by this delivery. |
| A5 | `spawnEnemies` (3480) charges nothing. The wave size comes from a formula (4201-4204). `ai.tick` (4121): `ai.mp` regenerates 0.6/s per enemy point and each reinforcement costs 20 mp, no material. | **Abstract**. This delivery now requires material for paid soldiers (section 3). `ai.mp` stays as abstract manpower, like the player's (1399). |
| A6 | Enemy mortar with no cost (3152-3181). Enemy trench and wire free (2179, 2400, 3689). | **Abstract**. Not changed. |
| R1 | On the player's side: salvage, refinery (2859), recipes with a real cost (`CFG.LOGI`, 2438), trucks with cargo, depots, cargo loss when the truck is destroyed, shirt and ammo debit. When the enemy captures a point, the point's depot is zeroed (2403). | **Real**. Counts as a loss, never goes to the enemy. |

Side finding, not fixed by me: the simulation of the enemy chain, which uses the same order as the player
(factory before rebuild), showed the following. With continuous consumption, the factory spends every 80 bmat as soon
as they exist, and the 100 bmat truck is **never rebuilt**. The player's side has the same order:
`logi.tick` calls `factoryStep` before `truckStep`, and the rebuild is at 2792. For the player this remains
a **hypothesis**, not tested. On the enemy, I solved it by reserving bmat for the truck (section 3).

## 2. Contracts with ECONOMIA and ESTRADAS (no parallel system)

- **Recipes and units:** the enemy uses `CFG.LOGI.recipes` (the same object as the player; with ECONOMIA
  applied, the same entries), `LOGI.time`, `LOGI.trip`, `LOGI.refine`, `LOGI.ratio`, `LOGI.cap`,
  `LOGI.truckCost`, `LOGI.rebuild` and `LOGI.reloads`. The tests check against `data/game_costs.txt`:
  RifleAmmo Cloth 80/50 s; SoldierSupplies Cloth 80, 10 units, 80 s; TruckC Cloth 100, 900 HP, cargo 15
  (= `ECONVOY.hp`, `LOGI.cap`, `LOGI.truckCost`). A recipe without a positive cost or time, or with invalid
  `units`, **refuses the whole chain**: no production and no convoy, `en.err` appears in the HUD. A schema
  error never becomes zero cost.
- **Accounting:** the same convention as ECONOMIA. Closed crates in the rear and in the cargo; product
  units at the front (the recipes' `units`: ammo = 1 crate, shirts = 10). The debit happens when the
  job starts and the crate only appears on completion. The cargo changes owner only on confirmed arrival. On destruction, the cargo
  becomes a recorded loss, it never returns to stock. The enemy's products are `CFG.ECHAIN.kinds = {ammo, shirts}`,
  what the front consumes. ECONOMIA's rifles/bandages do not enter: the enemy's weapon is the mod's own mesh.
  To widen it, just change `kinds`/`eNeed`.
- **Route:** the convoy moves only through `logi.drive(tr, dest, dt, speed)`, the same driver as the player, and only delivers
  when the driver returns `true` (arrival). When ESTRADAS swaps the driver, the enemy convoy inherits the real route
  without changing anything here. Extra contract: the driver may write `tr.routeStatus ∈ {rota_ausente, bloqueado,
  regiao_invalida}`. After `ECHAIN.stuck` = 20 s in that state, the convoy returns loaded and the rear is only
  credited when it **arrives** (`logi.eHome`), like the `returnCargo` of ESTRADAS and ECONOMIA. An invalid
  actor or `bActorIsBeingDestroyed` on the way counts as an explicit loss, never as a delivery. Pending from
  ESTRADAS: `logi.convoyRoute` still picks the rear and the front through straight ground traces (2949-2979).
  Those stops need to become validated graph stops.
- **Persistence:** `sv.collect` writes `elogi = logi.eSnapshot()` (v=1), additive, next to ECONOMIA's `logi`.
  No userdata. PERSISTENCIA needs to reconcile this field in the regional schema.

## 3. Design (what the patch does)

Everything lives in `logi.e*` and `CFG.ECHAIN`. **Top-level locals stay at 178**.

1. **Off-map rear, with the player's rules.** An abstract resource truck brings `LOGI.trip` = 100
   salvage every `ECHAIN.trip` = 25 s. Refinery at 4/s, ratio 2:1, i.e. at most 2 bmat/s like the
   player. Factory with one job at a time: it picks the product with the lowest total stock over its target and stops when
   everything exceeds 2x the target. `bmat0` = 240, same as the player.
2. **Convoy with real cargo.** It only leaves with a free truck (fleet `ECHAIN.trucks` = 2 = `LOGI.supply`), with
   crates in the rear and with at least `minLoad` = 3 crates (or everything the front asks for). The rear is only
   debited **after** the BPTruckC actor spawns valid. Failed spawn, missing class or dying actor: nothing leaves
   and nothing is debited. Without cargo, it tries again in 5 s (`ECONVOY.retry`).
3. **Interdiction.** Fire, ambush or mortar (the usual `logi.hit` and `logi.blast`) run `logi.eLose`.
   The cargo becomes a loss **a single time** (`lostDone`), the front receives nothing and the truck enters the
   rebuild queue (`LOGI.rebuild` = 30 s and `LOGI.truckCost` = 100 bmat). The rebuild **has priority** over
   the factory when no free truck is left. The manpower reward to the player (+25) stays as it was.
4. **Front.** Each **paid** soldier takes 1 shirt and 1 load (1/`LOGI.reloads` ammo crate),
   like the player's recruiting and reloading. The wave (`logi.waveCut`) gets `ECHAIN.free` = 3 free
   soldiers and, beyond them, only what the front can equip. The debit (`logi.eCommit`) comes **after** the spawn
   and covers only the paid soldiers that spawned. Reinforcements through points (`ai.tick`) go through the same limit
   (`eAfford`) and the same debit (`eConsume`).
5. **Traceability.** Each wave is recorded in `logi.en.waves`: requested, free, paid, sent,
   missing, limiting product and **how many were missing due to interdiction** (`byCut`). `byCut` is a counterfactual:
   the lost stock not yet "spent" (`ghost`) shows how many soldiers the front would have equipped. The
   wave alert says how many were missing due to destroyed convoys. `logi.eReport()` and `logi.eAudit()` work through the
   channel. The HUD shows the front, the rear, the convoys on the road and the lost ones. `combat.cargo` keeps
   existing as an alias (= soldiers the front equips) for the INTERFACE panel.
6. **Conservation.** Per product: initial + produced = rear + transit + pending + front + consumed +
   lost. Also bmat0 + refined/2 = bmat + spent, and salvage collected = salvage + refined. Fleet: free +
   rebuilding + on the road = 2. Any violation shows in `logi.eAudit()`.
7. **Save/continue.** The cargo in transit becomes `pending`: the actor is not recreated and the cargo leaves on the next
   convoy from the rear. Trucks on the road become free again. Validation is complete (finite numbers
   ≥ 0, fleet, job and the **save's own ledger closing**) and the restore **replaces**, never adds.
   `sv.ser` writes 3 decimal places, so the tolerance is `ECHAIN.tol` = 0.05 and the leftover goes into the
   origin terms. An invalid or legacy save (without `elogi`) restarts from the scenario stock with a warning; it is the same
   old `cargo0` behavior, but now recorded in the ledger as "initial".
8. **Unchanged on purpose:** assault (`combat.mode == "assault"`) and matches without logistics (`logi.on`
   false) keep the old abstract behavior, without consumption. Manual wave F4, the assault garrison, ammo
   when firing, mortar and enemy fortifications also stay abstract (A4-A6).

**Abstract bonuses that remain, all explicit:** a garrison of 3 free per wave; the formula for the requested wave
size; `ai.mp`; enemy ammo when firing; enemy mortar and fortifications; the off-map rear, which cannot
be attacked; and the front's initial scenario stock (2 ammo crates, 10 shirts), which is in the ledger.

## 4. Offline tests: commands and result (full output in `TEST_OUTPUT.txt`)

From the repository root (PowerShell):

```powershell
$env:PYTHONPATH='D:/tools/pylibs'
python data/parallel/logistics_ai/build_patch.py          # generates patches + main_candidate.lua; main.lua intact
python data/parallel/logistics_ai/test_logistics_ai.py    # PASS on the 2 candidates
python data/parallel/logistics_ai/test_orders_candidate.py  # PASS: 4 runs
python data/parallel/logistics_ai/test_base_audit.py  # PASS: A1-A6 on the current main
python tools/check_globals.py data/parallel/logistics_ai/main_candidate.lua  # no output = OK
```

- `test_logistics_ai.py` runs the whole candidate `main.lua` twice: main+AI and main+ECONOMIA+AI.
  It covers game costs; scenario stock; schema refusal (cost 0 and missing time); production with debit
  at the start; factory stopping at 2x; convoy without a truck, without cargo, with a failed spawn or a dying actor, without
  a phantom and without a debit; single delivery; single loss with fire and then mortar; rebuild waiting for
  bmat; invalid actor on the way; missing route (returns loaded, credit only on arrival); wave through the real `waveTick`
  with a fake spawn; spawn refused without debit; reinforcement through the real `ai.tick`; assault and a match without
  logistics; save through the real `sv.ser`/`sv.parse` and `sv.collect`/`sv.load`; repeating restore without duplicating;
  tampered or legacy save; **25 seeds × 600 random steps** with `eAudit` after each step
  (conservation, no negatives, constant fleet); and four complete matches through `waveTick`.
- Deterministic matches (45 s fight per wave, 6 of our soldiers; format `wave:sent/requested`,
  `[iN]` = N attributed to interdiction):

```
control                  1:6/6 2:6/6 3:7/7 4:8/8 5:9/9 6:10/10 7:10/10 8:11/11 9:12/12 10:13/13   (5 convoys, 0 lost)
total interdiction       1:6/6 2:6/6 3:7/7 4:3/8[i5] 5:3/9[i6] 6:3/10[i7] 7:3/10[i7] 8:3/11[i5] 9:3/12[i9] 10:3/13[i1]  (4 of 4 destroyed)
interdiction 0-420 s     ... 8:3/11[i5] 9:3/12 10:13/13   (recovery after the cut stops)
scarcity (no bmat)       1:6/6 2:6/6 3:7/7 4..10: 3 (floor)   (the match continues to the end, ledger OK)
```

  Reading: the cut traceably reduces the soldiers the wave receives (alert + `byCut` + losses in the
  ledger), not just a counter. The "venceu=true" of these lines **says nothing about balance**, because the fight
  model kills every wave in 45 s.
- `test_orders_candidate.py` runs `tools/test_orders.py` unchanged on the pure main (control), on main+AI and
  on main+ECONOMIA+AI. It swaps a single block, the enemy convoy one, whose abstract contract was removed; the
  new block is in `test_orders_convoy_block.lua`. It also runs `economy/test_integration.py` over
  main+ECONOMIA+AI: PASS.
- Syntax OK; 178 top-level locals in all three; `check_globals` clean on main+AI and main+ECONOMIA+AI.

**What was NOT tested (live gates):** BPTruckC spawn and movement with the patch; LOS and alerts;
per-frame performance; the real effect at the front with real soldiers; balance (the floor of 3 with
total interdiction may make the game too easy, and calibration belongs to the lab); real save/continue on
disk with the convoy on the road; and integration with the ESTRADAS driver (which does not exist yet).

## 5. Application order (for the coordinator)

1. ESTABILIDADE (already integrated).
2. **ECONOMIA** (`data/parallel/economy/build_patch.py`).
3. **IA_LOGISTICA**: `build_patch.build(source)` or `logistics_ai.patch` (diff over main+ECONOMIA).
   No anchor depends on ECONOMIA: `logistics_ai_base.patch` applies over the pure main, and both paths
   were tested. The anchors are unique and fail-closed; only the HUD one is optional.
4. INTERFACE: I tested in a scratch the AI applied **after** `painel.patch`. It works: the HUD anchor is
   skipped and the panel keeps reading `combat.cargo`. I recommend the panel use `logi.eHud()`.
   **Conflict that is not mine:** ECONOMIA fails over INTERFACE (anchor `table.concat(deps, " | "), foe)`).
5. Swap in `tools/test_orders.py` the "enemy convoy" block for the one in `test_orders_convoy_block.lua` and include
   `test_logistics_ai.py` in the battery. There is no new key, so MANUAL_TEST and the key test stay the same. The
   README needs to describe the enemy chain and the new alert.
6. Then: the ESTRADAS driver (with `routeStatus`) and the PERSISTENCIA schema (`elogi`).

## 6. Risks

- **Balance:** total interdiction brings waves 4 to 10 down to the floor of 3 (before, the maximum was −4 per wave). The
  calibration parameters are in `CFG.ECHAIN` (`free`, `front0`, `want`, `trip`, `minLoad`) and are
  compared on the bot (script L9).
- The convoy keeps going straight and without collision (current driver) until ESTRADAS.
- `ECHAIN.trip` is an abstract parameter of the off-map rear. The rear cannot be attacked; attacking
  enemy installations is left for later.
- On continue, the cargo in transit leaves the rear again, not from where the truck was. This
  conserves the cargo, but delays the delivery.
- `byCut` diagnosis: it is a counterfactual attribution, not a physical measurement.

## 7. Universal-modder

Consulted at the start: `um kb search` with logistics, supply, enemy ai, conservation and foxhole; the Foxhole note,
items 25, 30, 32-38 (TruckC/TruckW spawn, road network, ruin × active, IsValid × spawn). "Trace before
reinventing": Foxhole is online only and has no bots nor logistics AI to trace. The own chain uses
the game's **real tables** (costs, TruckC cargo and HP). Gotchas proposed in `PROPOSED_GOTCHAS.md`;
I did not edit the note.

## Files

`logistics_ai.lua` (inserted module), `build_patch.py`, `logistics_ai.patch`, `logistics_ai_base.patch`,
`main_candidate.lua` (only for inspection/check_globals; **do not copy** over main), `test_logistics_ai.py`,
`test_orders_candidate.py`, `test_orders_convoy_block.lua`, `test_base_audit.py`, `TEST_OUTPUT.txt`,
`t_logistics_ai.lua` (channel probe for the lab, not run), `LAB_SCRIPT.md`,
`PROPOSED_GOTCHAS.md`.
