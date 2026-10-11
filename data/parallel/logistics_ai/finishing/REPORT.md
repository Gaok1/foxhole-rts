# IA_LOGISTICA + PERSISTENCIA: finishing (2026-10-09)

Finishing agent for the IA_LOGISTICA and PERSISTENCIA tasks. All work offline, **only in this folder**
(`data/parallel/logistics_ai/finishing/`). I did not edit `main.lua`, shared docs, the original files of
`logistics_ai/`, `persistence/` and `economy/`, the lab or the game (checked: no file outside this folder
changed since I started). Variants are **copies** with a diff against the original in `diffs/`.

**Honest state:** everything below is proven **offline** (lupa, the whole candidate `main.lua` in memory). Real
balance, real wave cadence, the real BPTruckC truck, a real on-disk save and the live HUD remain lab
gates. Both tasks stay `[ . ]`.

Battery result: `bash data/parallel/logistics_ai/finishing/run_all.sh` → **ALL PASS** (`TEST_OUTPUT.txt`).

| Item | Result |
|---|---|
| 1. `CFG.ECHAIN` calibration | Proposed `free` 3→**5**, `want` 6/30→**4/20**, `trip` 25→**20**; `front0`, `minLoad`, `bmat0` stay. Explicit criteria met at both cadences; only 6 of 144 combinations pass, all with `free` 5. |
| 2. bmat × the player's truck | **Hypothesis confirmed** offline, but the cause is **not the order** factory/truck: it is the threshold (recipe 80 bmat < truck 100). Isolated patch `patch_bmat_reserve.py` fixes it; the test fails before and passes after. |
| 3. `elogi` reconciliation | Single policy: **discard only the `elogi` section**, restart the enemy chain from the scenario stock with an explicit warning, keep the rest of the save. 22 new cases + adapted `test_persistencia` (54 cases). |

## 1. `CFG.ECHAIN` calibration

### 1.1 Method

- `simlib.py` loads the whole candidate (main + ECONOMIA + AI) into a Lua runtime and runs matches through the real `logi.tick` +
  `waveTick`; only the engine boundaries are fake (same harness as `test_logistics_ai.py`). `sweep_echain.py`
  sweeps the parameters (each wave's fight lasts `fight` s and vanishes, as in the original test).
- **Two cadences** (45 s fight → a wave every ~60 s; 90 s fight → ~105 s). The MODLOG records ~39–53 s per wave
  with the bot, so 60 s is realistic for the bot and 105 s for a slower human. What the real cadence
  is, is a lab gate.
- Scenarios: **control** (no cut); **T** total cut from 0 s (every convoy in transit is destroyed); **M** total
  cut from wave 5 (front stock already at target); **R** cut until the wave of the first shortage and then free
  (recovery); **P** partial cut: each convoy is destroyed with probability p ∈ {0.25; 0.5; 0.75}, **20
  seeds** per p; **scarcity** (rear without bmat or salvage).

### 1.2 Criteria (`sweep_echain.criteria`)

1. **Without a cut, waves equal to the current ones** (`sent == requested` in all 10 waves, also at a ~45 s cadence).
2. **Total cut from the start**: waves 1–4 whole (the front has stock for "a few waves"); the mean of waves
   5–10 between 40% and 65% of the request; never below 33% of the request.
3. **Total cut from wave 5**: must bite before wave 10 (otherwise interdicting mid-game is useless).
4. **Partial cut**: shortages monotonic in p, p = 0.25 ≤ 50% and p = 0.75 ≥ 40% of the total cut's shortages.
5. **Traceable**: ≥ 75% of the missing soldiers show up in `byCut`.
6. **Recovery**: after the cut stops, the first whole wave comes within ≤ 3 waves and ≤ 300 s.
7. Ledger (`eAudit`) closed in all runs.

These are **my** criteria, explicit and reproducible; not combat balance.

### 1.3 What the sweep showed

- **The original calibration does not meet criterion 1 at a fast cadence.** Without any cut, `v1` already reduces the waves
  (`CADENCES.txt`: at ~50 s per wave 12 soldiers are missing; at ~30 s, 32). Cause: the refinery saturates at 2 bmat/s (4
  salvage/s) and a paid soldier costs ~21 bmat (1 shirt 8 + 1/6 of an ammo crate 13); the rear sustains ~5.6
  paid soldiers per minute, and `free` 3 leaves 5–10 paid in the last waves. This is **not** interdiction (`byCut` = 0).
  With `free` 5 the control equals the current one down to ~40 s per wave.
- **`trip` is a cliff, not a dial.** At `trip` = 25 s the rear is already exactly at the refinery's
  limit; `trip` ≥ 30 reduces waves **without a cut** (`SENSITIVITY.txt`). Proposed 20 s (same result as 25,
  with margin). The real value of the resource truck belongs to the lab.
- **`free` is the floor and the main dial.** 3 and 4 drop the pressure before wave 5 and the floor to 23–31%; 6 leaves the
  total cut at 68% and the cut from wave 5 does not even bite. Only 5 meets everything.
- **`want`/`front0` define how many waves the front stock lasts** (changing one at a time, `SENSITIVITY.txt`):
  `want` 5/25 (both cadences) or 6/30 (the 105 s one) makes the cut from wave 5 not bite before wave 10;
  `front0` 3/15 likewise, and 4/20 stretches the start (mean 69%). `front0` stays 2/10 (unchanged) and `want` 4/20 (3/15 also passes).
- **`minLoad`**: 1 worsens traceability (1-crate convoys; `byCut` 56%); 3, 5 and 8 pass. It stays 3.
- I also tested a **proportional floor** (`free` 3–5 + a 0–40% fraction of the request; 96 combinations): 20 pass, but it requires
  a new parameter and a 2× larger `front0`, with no gain over `free` 5. Discarded; the exploration archive is in
  `PROPORTIONAL_FLOOR_GRID_ARCHIVE.txt` (not reproducible with the current code, the parameter was removed).

### 1.4 Proposed values (`logistics_ai_v2.lua`, diff in `diffs/logistics_ai_v2.diff`)

| Parameter | Current | Proposed | Effect |
|---|---|---|---|
| `free` (floor) | 3 | **5** | total cut goes to 5 soldiers per wave (38% of wave 10) instead of 3 (23%) |
| `want` | 6 / 30 | **4 / 20** | front stock of ~20 soldiers; interdiction from wave 5 bites at 9 |
| `trip` | 25 s | **20 s** | margin over the refinery; > 25 weakens the wave without a cut |
| `front0`, `minLoad`, `bmat0`, `stuck`, `tol` | 2/10, 3, 240, 20 s, 0.05 | same | |

Reference of the old abstract contract (maximum cut −4 per wave): mean of waves 5–10 = **63%**. `v1` = 28%, `v2` = 52%.
`free` 6 reproduces ≈ the old one (68%), but then the late cut stops biting.

### 1.5 Before/after table (~60 s cadence; format `wave:sent/requested`, `[iN]` = N attributed to interdiction)

Complete (both cadences, seeds 1–3) in `CALIBRATION_TABLE.txt`.

| Scenario | v1 (current) | v2 (proposed) |
|---|---|---|
| control | 6 6 7 8 9 10 10 11 12 13 (all whole) | identical |
| total cut from 0 s | 6 6 7 **3**[5] **3**[6] 3[7] 3[7] 3[5] 3[9] 3[1] | 6 6 7 8 **8**[1] **5**[5] 5[5] 5[6] 5[7] 5[8] |
| total cut from wave 5 | waves 1–6 whole, 7: **5**/10[5], 8–10: **3** (23%) | waves 1–8 whole, 9: **8**/12[4], 10: **5**/13[8] |
| cut until the 1st shortage, then free | 3 3 3 → wave 7 whole, 8: 6/11, 10: 4/13 | 8/9 5/10 → wave 7 whole (**2 waves / 119 s**) |
| scarcity | 3 from wave 4 | 5 from wave 6 |
| partial p = 0.25 / 0.5 / 0.75 (20 seeds) | missing 20.7 / 32 / 46.5 (40/62/89% of the total) | 5.1 / 16.1 / 22.3 (16/50/70%) |
| cargo lost in the ledger / dispatched | 29 / 53 / 85% | 22 / 62 / 77% |

~105 s cadence: the front stock absorbs small cuts (p = 0.25 no soldier missing; p = 0.5, 3.6;
p = 0.75, 17.6). The **flow** lost in the ledger follows p (21 / 50 / 77%): the effect on the wave has a threshold, the ledger
trace does not. The drops are attributed in `byCut` (≥ 75% of those missing).

After recovering, the rear emptied by the cut runs short again in the last waves at a 60 s cadence (production
does not keep up), which is the expected economic consequence of the cut.

### 1.6 Real balance

**None of this confirms balance.** The model kills every wave in 45/90 s and the player does not fight the soldiers that
arrive. Missing in the lab: (a) measure the real wave cadence (bot and human) and rerun `sweep_echain.py` with
real `FIGHTS`; (b) the real travel time of the resource truck → `trip`; (c) what the cut from wave 5
means for the bot's defeat/victory; (d) how often the player actually intercepts convoys (the bot only
ambushed by chance). Dials, in this order: `free` (±1 = ±15 points of pressure with the chain cut), `want` (stock
duration), `trip` (never above 25 s without deciding the control should be weaker).

## 2. The player's hypothesis: bmat × truck

### 2.1 Result: **confirmed offline, with another cause**

`test_truck_bmat.py` runs the candidate's real `logi.tick`, `factoryStep`, `truckStep` and `logi.hit`
(main+ECONOMIA+AI). Continuous consumption = the depots are emptied every tick (the factory always has something to produce).

| Situation (continuous consumption) | Without fix | With `patch_reserva_bmat` |
|---|---|---|
| supply truck destroyed at 60 s | **does not come back in 900 s** (highest bmat seen while waiting: **79**) | back at 36.5 s |
| same with the factory running **after** the trucks | **does not come back** (identical) | back at 36.5 s |
| resource truck destroyed at 60 s | does not come back; the economy dies | back at 36.5 s |
| sweep of the moment of death, 30–120 s (31 cases) | 0/31 come back | 31/31, worst case 49.5 s |
| idle factory (stock full) | back at 30 s | back at 30 s, no warning (no regression) |

Mechanism: the factory starts the recipe as soon as bmat reaches 80 (rifle 100); the truck asks for 100. Under continuous
demand bmat never goes past ~79, **whatever the order** of the calls. Swapping the order in `logi.tick` (the
IA_LOGISTICA suggestion) does not fix it. The enemy chain already had this solved; the player did not.

### 2.2 Minimal fix (`patch_bmat_reserve.py`, `bmat_reserve.patch`)

While there is a destroyed truck, the factory only starts a recipe if `LOGI.truckCost` (100) bmat per destroyed
truck is left after debiting it (`logi.rebuildReserve`, a function in `logi`; no top-level local, no new CFG, no key,
nothing in the save). It reserves from the **destruction** (not only when the 30 s deadline expires), so bmat accumulates during
the wait. Warning `fábrica guarda N bmat para reconstruir caminhão` (at most every 20 s). It applies after the stack
ECONOMIA → AI (any AI version) and **commutes** with PERSISTENCIA and with the rebased INTERFACE (tested).

### 2.3 Limits and risks

- **It does not solve the death of the resource truck with bmat = 0 and salvage = 0** (no income to gather 100). Measured: it stays
  destroyed with and without the patch (informative in the test). Options, if you want to close it: a permanent reserve of 100 bmat in the
  factory, or rebuild the resource truck at zero cost (design decision, not included).
- The HUD shows "sem bmat" while the factory waits; the warning covers it, but INTERFACE may want a label.
- "Continuous" consumption is an explicit model; in the real game the factory stops when all depots exceed 2× the
  target. How often that happens is a lab gate (script below).

## 3. `elogi` reconciliation (single policy)

### 3.1 Policy

> The enemy chain is **secondary and regenerable** state (scenario stock); the rest of the save belongs to the player.
> So an `elogi` that is **invalid, of a future version, missing, without the player's logistics or read by a mod without the
> module** does not refuse the save. Only **the section** is discarded; the enemy chain restarts exactly from the
> scenario stock (ledger with `inicial` = `front0`, `bmat0`, full fleet, nothing in transit) and the player is warned.
> Any **other** invalid field keeps refusing the whole save and preserving session and file.

Why, instead of keeping the total refusal: (1) the AI already did this for a missing/invalid `elogi` when read alone, while
PERSISTENCIA refused; two policies for the same section; (2) refusing locks the player out of their own progress
(soldiers, paid infrastructure, depots) because of a state the game knows how to rebuild; (3) the discard is
explicit (10 s notification `CADEIA INIMIGA REINICIADA (motivo)`, an event in the chain, a log), not silent.

### 3.2 Tested guarantees (`test_elogi.py`, 22 cases: Lua 5.4 and 5.5, AI_v2 stack and complete stack, plus the case without the module)

| Case | Result |
|---|---|
| valid `elogi` (with pending cargo and consumption) | restores **identically**; 3 continues in a row add nothing; no warning |
| 9 invalid: ready < 0, ledger does not close (extra shirts), bmat < 0, fleet > configured, job of a nonexistent recipe, not a table, empty, future version `v = 2` (reason "versão futura v2"), unknown version | Continue **works**; the player's state (bmat, depots, wallet, points, soldiers, wave, manpower) **identical to the saved one**; enemy = exact scenario; `pending` empty, 0 convoys, 0 lost, 0 on the score; autosave **not** suspended |
| missing `elogi` (legacy save / `v` 1 without `elogi`) | same explicit warning (before only the log) and same scenario |
| next autosave | writes a regenerated valid `elogi`; the following continue does not warn and restores the same |
| **own** enemy state invalid when saving | writes the rest **without** the section (never an invalid `elogi`) and logs |
| a mod **without** the AI reads a save made with it | discards only `elogi` ("este mod não tem a cadeia inimiga logística"); player intact; abstract enemy = new match `cargo0` |
| invalid `squad`, negative `logi`, unknown field, future `infra` | **keep refusing everything** and preserving session and file |

"No gain for the player" becomes concrete like this: nothing of the player's is touched or credited (wallet, bmat, depots,
manpower, convoy score), and the enemy chain never comes back with more than `front0`/`bmat0` (no phantom pending
cargo, no duplication). **Open decision for the coordinator:** the scenario stock may be weaker
than the saved one; editing the save to trigger the restart would become a shortcut (offline solo game, low risk). A
neutral alternative would be restarting the front at the target (`front = want`), but that creates stock that never existed; I did not
adopt it.

Mutation test: the same assertions against the **original** `persistence.lua` (total refusal) fail in `t_invalid`,
`t_absent` and `t_save_own_invalid`, so the tests tell the two policies apart.

### 3.3 What changed (diffs in `diffs/`)

- `persistence_v2.lua`: `sv.validate` returns `true, nil, soft` (3rd return = reason for the discarded `elogi`);
  `sv.parseSave` removes `elogi` and leaves `d.elogiDropped` (runtime-only field); `sv.save` writes without the section if
  its own state is invalid; `sv.load` passes the reason to `logi.eRestore(d.elogi, d.elogiDropped)` and appends the
  warning to `PARTIDA CONTINUADA`; a save with `logi` but without `elogi` gets the same warning.
- `logistics_ai_v2.lua`: `logi.eRestore(d, dropped)` warns (event + `notify`) when it receives `nil` with a reason;
  `eValid` distinguishes "versão futura vN" from "versão desconhecida" and from "formato".
- `test_persistence_v2.py` = `test_persistence.py` with 3 stacks and **one** block swapped (the `elogi` one that used to
  expect a refusal); `test_logistics_ai_v2.py` = the original with only paths changed (no expectation changed);
  `test_orders_convoy_block_v2.lua` reads `free`/`front0` from CFG instead of assuming `free` 3.

Accepted side effect: `sv.read` returns the first valid file (`save`, `.tmp`, `.bak`). A `save.txt` with a
bad `elogi` and a new player beats a whole `.bak` with 30 s less progress.

## 4. Files

| File | What it is |
|---|---|
| `logistics_ai_v2.lua`, `build_patch_v2.py` | calibrated AI + `eRestore`/`eValid`; generator (unique anchors, same as the original) |
| `patch_bmat_reserve.py`, `bmat_reserve.patch` | item 2 |
| `persistence_v2.lua`, `build_persistence_v2.py` | item 3; `build`, `build_with_ia`, `build_full` (ECONOMIA → AI_v2 → reserve → PERSISTENCIA_v2) |
| `main_candidate_v2.lua`, `main_final_v2.lua`, `*_v2.patch` | only for inspection/`check_globals`. **Do not copy over main.** |
| `simlib.py`, `sweep_echain.py` | item 1; modes: no argument (table), `--sens`, `--cad`, `--grid` |
| `CALIBRATION_TABLE.txt`, `SENSITIVITY.txt`, `CADENCES.txt`, `RESULTS_GRID.txt` | item 1 outputs |
| `test_truck_bmat.py` | item 2 |
| `test_elogi.py`, `test_persistence_v2.py`, `test_logistics_ai_v2.py`, `test_regression_v2.py` | item 3 and the complete stack regression |
| `diffs/` | each variant against the original |
| `run_all.sh`, `TEST_OUTPUT.txt` | battery and output |

Reproduce (root, bash): `bash data/parallel/logistics_ai/finishing/run_all.sh` (≈ 2 min). The grid (`--grid`,
~25 min) is left out; result in `RESULTS_GRID.txt` (6 of 144 pass, all with `free` 5 and `trip` ≤ 25).

Results: `test_bmat_caminhao` PASS; `test_elogi` PASS (22); `test_persistencia_v2` PASS (54 = 9 × Lua 5.4/5.5 × 3
stacks); `test_ia_logistica_v2` PASS (2 candidates); `test_regressao_v2` PASS 1–6 (test_orders, economy/test_integracao,
AI, globals + 178 top-level locals, commutation, composition with the rebased INTERFACE); `check_globals` clean on both
candidates; control: the original tests (`test_logistics_ai.py`, 2 candidates; `test_persistence.py`, 36 cases)
keep PASSing against the original modules.

## 5. Proposals to the coordinator

1. **Order:** ECONOMIA → IA_LOGISTICA v2 → bmat reserve → (INTERFACE) → PERSISTENCIA v2. All commute where
   tested; `build_persistencia_v2.build_full` builds the stack without INTERFACE.
2. When integrating, replace `logistics_ai.lua`, `persistence.lua` with the `_v2` ones, swap the convoy block of
   `tools/test_orders.py` for `test_orders_convoy_block_v2.lua` and include `test_elogi.py` and `test_truck_bmat.py`
   in the battery.
3. `mod/README.md` needs to say: floor and stock of the enemy chain; bmat reserve to rebuild a truck; a save
   that restarts only the enemy chain (warning `CADEIA INIMIGA REINICIADA`).
4. Proposed gotchas for the Foxhole note (I did not edit it): (a) the enemy convoy calibration only holds at wave cadences
   ≥ ~55 s with `free` 3; the refinery (2 bmat/s) is the ceiling of any chain; (b) a factory with a recipe (80) below the
   truck's price (100) keeps it from coming back under continuous consumption; the call order does not help; (c) a policy of a
   discardable section in the save for regenerable state.
5. Decide (3.2) the restart stock and (2.3) the death of the resource truck without income.

## 6. Live pending items (lab)

1. Measure the real wave cadence (bot and human) and the resource truck's cycle time; redo the sweep.
2. Look at `logi.eReport()` with the v2 calibration: `byCut`, losses and whether the pressure drops as in `CALIBRATION_TABLE.txt`.
3. Player: kill a supply truck under high consumption (bot in `botloop`), see the warning `fábrica guarda...` and the
   truck come back in < 60 s; check the HUD ("sem bmat") and whether real consumption actually keeps the factory always busy.
4. Edit `save.txt` (corrupt `elogi`, change `v` to 2) and use Ctrl+F6: check the 10 s warning, the player intact
   and the next autosave.
5. Everything the original reports already listed (real BPTruckC truck, route, performance, `io`/`os` in UE4SS's Lua).
