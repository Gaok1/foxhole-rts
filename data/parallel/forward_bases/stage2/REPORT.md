# BASES_AVANÇADAS (forward bases) — stage 2 (offline implementation) — report

Delivery: `candidate_v4/main.lua` = `candidate_v3` (manual collection, SHA256 `9b89b113…63e6`, **read-only**) + a patch by unique
anchors (`build_bases.py`). Nothing was applied to `mod/FoxholeRTS/Scripts/main.lua` nor to the shared docs; there was no lab,
game, nor keyboard/mouse input. Everything below is **offline** (lupa, Lua 5.4 = UE4SS and 5.5): it proves logic and contracts, not physics,
the real class `BPForwardBase1_C`, the route nor performance.

SHA256 of `candidate_v4/main.lua` (CRLF): see `candidate_v4/SHA256.txt` (the last line is v4's; v3 shows up before/after and is equal).

## 1. What changes for the player (for README / MANUAL_TEST)

- **Shift+J with the cursor inside one of your control points**: the 1st press shows cost and location ("Base avançada em A: 300 bmat (fábrica tem N).
  Shift+J de novo em 4 s para construir"); the 2nd press within 4 s builds. It sits next to `J` (which keeps creating a point).
- The forward base costs **300 bmat from the factory**, debited **only after** the actor spawns validated. If the actor is refused/spawns wrong,
  it is undone and nothing is debited. Not enough bmat: the 2nd press records a **pending order** — the factory starts **keeping 300 bmat**
  (panel: "Fábrica | guarda 300 bmat para base avançada em B (bmat N)"), after the reserve for a destroyed truck (the truck has
  priority). It builds on its own when it has enough; it cancels in 180 s, if the point stops being yours, if an enemy appears in the ring, or with
  Shift+J again within 4 s over the order's point.
- Conditions: **your** point, no enemy in the ring, far from the main base (≥ 30 m) **or** near an enemy point (≤ 40 m), flat and
  free Landscape ground (not on a roof/mod structure), ≥ 3 free exits, at most 3 bases. Only with logistics on and outside Assault.
- **Stock of 15 slots** per base (a partial crate = 1 slot). Trucks (`L` over the base) carry only what fits; **shirts and rifles only go to
  places that can reinforce** (main base or an active forward base). A control point without a base now receives only ammo and bandages.
- **Recruit (Ctrl+1/2/3/4/0) under logistics**: the soldier spawns at the main base **or** at the active forward base with shirts (and a rifle, for the
  rifleman) **closest to the cursor**; with the cursor **inside** a base, only there (clear refusal, no falling back to another). A point without a base **no longer**
  reinforces (`CFG.SPAWN.pointSpawn=true` restores it). Manpower (`economy.manpower`) **no longer limits** the logistics branch; the limits
  are shirts/rifles. Each recruit spends 1 shirt (+1 rifle for the rifleman); mg/marksman/medic/officer only a shirt.
- **Loss**: point captured or base destroyed (enemy mortar, damage ×2) → the base vanishes a single time, the stock is lost (message
  "BASE AVANÇADA B capturada: perdeu N camisas e M fuzis"), the actor is destroyed. Recapturing the point does **not** bring the base back;
  rebuilding costs 300 again. A base on a neutralized point becomes **inactive** (stock kept, neither reinforces nor receives).
- **Defeat by lack of troops** (logistics branch): no combat soldier **and** no shirt at all in a base, factory or truck.
- **Collection workers do not count toward the squad's limit of 12** (`CFG.SQUAD_MAX`); their limit is `CFG.COLETA.workers` (3).
  Before, a full combat squad prevented workers.
- **Save/Continue (Ctrl+F6)**: section `fwd` v1 inside the v2 save (point index, XYZ, yaw, health, stock through the point's depot; never
  an actor address). On continue, the bases are rebuilt (all or nothing, revalidating ground/class/exits); a position that no longer validates =
  Continue refused with the match and the file preserved. A pending order is **not** saved. v3 refuses a save with `fwd` ("campo
  desconhecido: fwd"); v4 opens v3 saves; v4 without bases writes a save v3 reads.
- **Panel**: one line per base: `base | camisas N | fuzis N | slots —  | reforça: tudo|só sem fuzil (sem fuzis)|NÃO (sem camisas)` and
  `base A | camisas 12 | fuzis 3 | slots 3/15 | reforça: tudo` / `INATIVA (ponto neutro)`. The panel gains +1 line (main base) + 1 per
  forward base (measured: 12x222 → 13x222 in the test 07c scenario; ≤ 96 characters per base line).
- Match with logistics: 10 rifles at the main base (`CFG.SPAWN.startRifles = 10`, already from v3).

### Text for `MANUAL_TEST.md` (new rows; only after the lab)

| # | Do | Expected | OK? |
|---|---|---|---|
| 11b | Shift+J with the cursor on free ground / on a neutral or enemy point | Message "ponha o cursor dentro de um ponto de controle seu" / "não é seu"; nothing created; does **not** create a point (only J creates) | |
| 11c | With bmat ≥ 300 above the reserve: Shift+J over one of your points far from the base (1st press), again within 4 s | 1st: cost and location; 2nd: "BASE AVANÇADA A construída (-300 bmat…)", the base appears at the point, the panel gains the line "base A \| camisas 0 \| fuzis 0 \| slots 0/15" | |
| 11d | Shift+J with little bmat, 2 presses | "pedido registrado"; panel "guarda 300 bmat para base avançada em A"; builds on its own when it has enough; Shift+J over the order's point warns and, repeated within 4 s, cancels | |
| 11e | L over the forward base (truck), wait for the delivery; Ctrl+1 with the cursor inside the base | Stock rises up to 15 slots; the recruit spawns **at the base's exit**, spends 1 shirt and 1 rifle from it | |
| 11f | Ctrl+1 with the cursor on one of your points **without** a base | Refusal/spawns at the main base; the point does not reinforce | |
| 11g | The enemy takes the base's point (or a mortar destroys it) | Alert "BASE AVANÇADA A capturada/destruída: perdeu N camisas e M fuzis"; actor vanishes; no residual actor | |
| 11h | With 1+ forward base: save 30 s, close, open, Ctrl+F6 | Base back in the same place, same stock and health, only one | |

### `HELP_TEXT` (already in the patch)

- Recruit line: `Ctrl+1/2/3/4/0: recrutar fuzileiro/metralhador/atirador/médico/oficial (logística: nasce na base ou numa base avançada com camisas; cursor numa base = só nela)`
- Construction line: `… K: barreira   J: ponto   Shift+J: base avançada (300 bmat, 2 toques)`
- The final load message (`log("v0.9 carregado …")`) mentions "Shift+J base avançada".

## 2. Keys

`Shift+J` is not in `GAME_KEYS` (55 keys) nor collides with a mod key: the only `*+J` key is `SHIFT+J`. In v3 `J` also fired with
a modifier pressed; in v4 `J` is wrapped in `plain()` (the same helper other mod keys already use, with `S.MOD_KEYS`), so
Shift+J does **not** create a point. Copy of the key test: `test_orders_v4.py` (the `tools/test_orders.py` suite was **not** edited).

## 3. Implementation

Everything in tables (`CFG.FWD`, `CFG.SPAWN`, `S.fwdStage/S.fwdRuins`, `logi.*`, `rts.combatCount`): **no new top-level local**
(check_globals: 175 before and after; the compiler accepts 22 more locals ⇒ **178 active**, the same as the real main). The function block
(`bases_funcs.lua`, 622 lines) sits **after `local structures = {}`** because it uses `squadCenter`, `structures`, `presence`, `flatSpot`…
(declared after `logi.tick`); that is why v3's `spawnSite/spawnCommit` were **removed from where they were and recreated in that block**
(with the same interface). `build_bases.py` applies ~40 edits by unique anchor (fails closed if the anchor is not unique).

New functions: `rts.combatCount`, `logi.slotsUsed/spawnCapable/fwdFree/fwdReserve/fwdAudit`, `logi.fwdMake/Exits/Fits/Place/Spawn/Check/Build/Key/Tick`,
`logi.fwdLose` (idempotent loss: capture and mortar), `fwdRuin/fwdBlast/fwdReset`, `logi.fwdLine`, `logi.canReinforce/noReinforce`,
`logi.spawnSite` (pure) → `spawnSquad` → `logi.spawnCommit` (single debit), `logi.recruit`, and the persistence `fwdSnapshot/fwdValid/fwdPreflight/
fwdStage/fwdStageClear/fwdBind`. Edits in existing places: `colMaintain` (no SQUAD_MAX for workers), `needs/nextKind`,
`moveCargo`, `factoryStep` (reserve), `truckStep` (cargo by slots; returns shirts/rifles to the factory if the base vanishes), `logi.tick`,
`hudLine`, `logi.blast`, `pointsTick` (`fwdLose` before the legacy zeroing), `spawnSquad` (cap only for combat; `at.exact`), `recruit`
(`if logi.on and combat.mode ~= "assault" then return logi.recruit(role, at) end`; legacy/Assault/F6/newGame branches intact),
`waveTick` (defeat through `logi.noReinforce()`), `sv.collect/validate/preflight/load`, keys and `HELP_TEXT`.

Order of `sv.load` (all or nothing): validate `fwd` → preflight without mutation → stage (spawns all bases or none; adopts a live actor at the
same position) → infra `applyPlan` → `sv.restore` → `logi.restore` → bind bases to depots. A failure in any step undoes the bases.

## 4. Order of the v4 stack

`real main` → ECONOMIA → IA_LOGÍSTICA v2 → reserva_bmat → INTERFACE v2 (rebased panel) → PERSISTÊNCIA v2 → COLETA MANUAL (v3) →
**BASES AVANÇADAS (v4)**. `bases_lf.patch` (LF, `a/main.lua b/main.lua`) applies over the v3 candidate in LF; `bases.patch` (CRLF) applies
over `candidate_v3/main.lua` on disk and reproduces `candidate_v4/main.lua` byte for byte (checked in test 10). The 4 alternative orders
of the earlier layers give identical text after `build_coleta.apply` + `build_bases.apply` (test 11). Do **not** apply BASES before COLETA.

## 5. Tests (all PASS; full output in `TEST_OUTPUT.txt`, run with `bash run_all.sh`, ~50 s)

| Suite | Cases (Lua 5.4 + 5.5) | Covers |
|---|---|---|
| `test_construction.py` | 12 PASS | 2 presses, 4 s window, debit only after spawn, 15 refusals (neutral/enemy/outside a point/near the base/enemy in the ring/no logistics/Assault/roof/sloped/mod structure/no exits/class/plan B/cap), spawn rollback (nil, being destroyed, health, displaced, rotation, CodeName; `strict=false` relaxes), pending order + reserve (one at a time, builds on its own, cancellations), destroyed truck has priority (also through Shift+J), bmat ledger |
| `test_recruitment.py` | 14 PASS | main base (ring, 1 shirt, +1 rifle only rifleman, no manpower, spawn failure does not debit), pure `spawnSite`, base closest to the cursor with stock, exact round-robin exit, cursor inside the base = only it (no fallback), inactive base, point without a base/`pointSpawn`, combat cap and workers' reserve, legacy/Assault branches identical to v3 |
| `test_loss.py` | 18 PASS | supply cut, destruction/capture/recapture (once, ledger closes, rebuilding charges again), mortar, truck in transit, 15 slots, `needs/nextKind`, defense in depth, defeat through `canReinforce`, fuzz 25 seeds × 600 steps (per-base ledger closes; live actors == live bases) |
| `test_workers.py` | 8 PASS | workers outside SQUAD_MAX in `recruit`, `spawnSquad` and `colMaintain`; limit = `COLETA.workers`; v3 × v4 comparison |
| `test_persistence_bases.py` | 16 PASS | round trip (XYZ/yaw/hp/stock by index, 1 actor, exits recomputed), 3× repetition + 3 new loads without duplicating, position/class that no longer validates, spawn failure with joint rollback, 21 save tamperings, v3/v4 compatibility, inactive/destroyed, order not saved |
| `test_key_panel.py` | 9 PASS | `fwdLine` (4 states, ≤ 96, pure), read-only `hudLine`, Shift+J end-to-end through `bindings`, J ignores modifier, `HELP_TEXT`, static analysis of the only places that write shirts |
| `test_orders_v4.py` | PASS | adapted copy of `tools/test_orders.py` + Shift+J registered/outside `GAME_KEYS` |
| `test_collection_over_v4.py` | 5 suites PASS | the 5 collection suites (partida_manual, coleta_nucleo, travamento, persistencia_coleta, spawn_interface) running in memory against v4 |
| `test_stack_v4.py` | 22 steps PASS | adapted copy of `test_stack_v3.py` (check_globals, orders, costs, economy, AI 25×600, elogi (+legacy), bmat, interface 07a–d, persistence (+legacy), ESTRADAS contract, patches in sequence, alternative orders, leftovers, **locals ≤ 178 by the compiler**, real main and `candidate_v3` with SHA intact) |
| `sensitivity_bases.py` | 21/21 mutants caught | debit before spawn, cost, truck reserve, idempotency of `fwdLose`, stock not zeroed, `canReinforce`, SQUAD_MAX, point without a base, `spawnCommit`, legacy branch, 6 save refusals, `bActorIsBeingDestroyed`, slot cap, `exact`, J key |

Mutant left out on purpose: NaN/inf in x/y/z/yaw/hp of `fwd` — the save's generic validator ("tabela de dados") refuses before
`fwdValid`, so the `fin()` there is defense in depth (equivalent mutant).

### Changed expectations (no hidden regression; each one marked in the code)

1. **Workers outside SQUAD_MAX** (new decision). `test_coleta_sobre_v4`: in `test_partida_manual` the assertion "esquadrão cheio: sem vaga
   para trabalhador" became "`workers() == COLETA.workers` and `#squad == SQUAD_MAX + workers`". `test_trabalhadores` shows v3 (0 workers with
   12 combat) against v4 (3).
2. `test_coleta_sobre_v4`, `test_spawn_interface`: the end of the static analysis slice moved from `function logi.tick()` to the marker
   "Persistência: extensão `fwd` v1" because `spawnSite/spawnCommit/recruit` now sit after it (scope of `squadCenter`/`structures`).
3. `test_orders_v4.py`: the 8 collection adaptations (deployment 1000/2 spots/4 actors, resource truck to be built) **plus** the new
   `SHIFT+J` assertion (registered, outside `GAME_KEYS`, no other `*+J`). The original `tools/test_orders.py` was not touched.
4. `test_stack_v4.py` (diff in `diffs/test_stack_v4.diff`, marks `V4`):
   - **`CFG.SPAWN.pointSpawn=true` in the old suites that deliver shirts/rifles to a point depot without a base**: step 05 (economy),
     08/08-L and 06b/06b-L (persistence v2 and elogi, through `new_load`) and contract 09 (b)/(c). What they test (the driver only delivers on arrival,
     truck on the way, ledger) does not depend on shirts/rifles reaching a point without a base, and the switch restores exactly the old
     behavior. The **new** behavior (default `false`) is tested separately: step 09 (a0), `test_perda`, `test_recrutamento`. That is why
     `spawnCapable` honors `pointSpawn` (with `true`, every point depot becomes capable again) — a fix made during this stage.
   - Names of 06b-L/08-L: they stopped being "without ANY change" (they have only the adaptation above).
   - 00: also checks `candidate_v3` on disk (bytes and SHA `9b89b113…`); 01: limit of 178 by the compiler; 10: checks `bases_lf.patch`/`bases.patch`;
     11: `build_bases.apply(build_coleta.apply(...))`; 06: file label fixed.
5. Observed (not a test expectation): panel 12 → 13 lines in scenario 07c.

## 6. Lab gates (none of this was seen; the game was not opened)

Read-only probes (`probes/A1…A4`, syntax checked in stage 1, **never run**) and rehearsal B1 remain pending and **decide**
the provisional values of `CFG.FWD`:

- **A1/A2 (HomeRegionW):** do the catalog columns and the CDO of `BPForwardBase1_C` load? `LoadAsset("/Game/Blueprints/Structures/Bases/BPForwardBase1.BPForwardBase1_C")`
  (path **inferred**); is there a native spawn column/UFunction? Decides `visual="native"` and whether there is a risk of native respawn (R1).
- **A3 (HomeRegionW, CallumsCapeHex, DeadLandsHex):** existing native forward base, components, collision-only bounds (→ `CFG.FWD.half`
  = 600 cm provisional), base/hospital ruins, real `ItemHolder` vs "15 slots" (R10: provisional interpretation in `CFG.FWD.cap`).
- **A4 (match):** how many places/exits per point pass the predicate (`half`, `clear`, `maxSlope`, `maxHeight`, `minExits=3`, `exitR`).
- **B1 (L3 of the script, with authorization):** spawn `BPForwardBase1_C` at a validated XYZ: does it spawn whole (Health = MaxHealth = 1725, `CodeName = "ForwardBase1"`
  — the mod's `strict=true` **refuses** if it diverges)? `TeamId` 255 vs 1 (`CFG.FWD.teamId=nil` today: the mod writes nothing); `K2_DestroyActor`; ruin
  `BPDestroyedForwardBase1_C` (`CFG.FWD.ruin=false` until B1); 60 s of `UE4SS.log` without `Registry`/native respawn/residual actor; spawn ms.
  If it does not spawn whole: **plan B** (mod mesh) — it is **declared (`visual="mesh"`) but NOT implemented**; today it falls into "classe não carregou".
- **L2:** check `minFromBase=3000`/`maxToEnemyPoint=4000` (cm) against the hex's real geometry (is there an eligible point in every match?).
- **L4–L10 of the script:** spawning at the exit (not on a roof/wall), `J`/`Shift+J` without a hitch, truck to the base respecting 15 slots, pending order
  without ammo starvation, loss by capture/mortar without a residual actor, save → close → Ctrl+F6 on a new load, 10 min with 3 bases (stability).
  The `MODLOG` stability gate ("do not widen features before isolating the crash") still holds.
- **Calibration:** `startRifles = 10` (already from v3) with the real wave cadence; `FWD.max = 3`; bmat cost × factory pace; panel width
  with 3 bases + pending order (+4 lines at most) on the real screen.
- **Confirm:** Shift+J does not also fire plain `J` (`plain()` handles it; the `S.MOD_KEYS` field must contain UE4SS's real Shift keys).

## 7. Risks

1. **Class/spawn never seen** (biggest risk): `BPForwardBase1_C` was never instantiated; inferred path; `strict=true` may refuse a base
   that works in practice (relax to `false` in B1) or accept one the game treats as a native respawn point (R1).
2. **Plan B not implemented** and **ruin off**: if B1 rejects the class, there is no visual base until the mesh is implemented.
3. **15 slots** is an interpretation (`StoredItemCapacity`); if it is something else, only `CFG.FWD.cap` changes, but a save from an old value is validated against the current `cap`.
4. **A save with `fwd` does not open in v3** (refusal "campo desconhecido: fwd" by design; the player loses Continue when going back from a version with saved bases).
   A pending order is not saved (it cancels on load).
5. **Shirts/rifles stop going to a point without a base** (decision D2): v3 saves/matches with stock at those points keep the stock, but it is not
   used to spawn; from then on logistics only resupplies the main base and the forward ones. A fixed truck order (`L`) to a point without a base
   carries only ammo/bandages.
6. **Manpower no longer limits the logistics branch**: the recruiting rate becomes only shirts/rifles (and the click pace); balance to validate.
7. **Defeat** changes in the logistics branch (`canReinforce`): the match only ends without troops and without a shirt anywhere (not even in a truck).
8. **Panel** grows up to +4 lines (main + 3 bases) besides the order; on a small screen it may cover more of the view.
9. **`J` wrapped in `plain()`**: with Ctrl/Alt/Shift pressed, plain J stops creating a point (the earlier behavior fired). It depends on
   UE4SS's real `keyDown` (`S.MOD_KEYS`).
10. **Locals**: 178 active by the compiler (22 of headroom, the same as the real main); nothing new at the top. Any future feature must stay in tables.
11. Read scope beyond what the mod controls: a live `BPForwardBase1_C` actor at the saved position is **adopted** on Continue (no duplicate).
12. `Shift+J` uses `GetRealTimeSeconds` (real time) for the 4 s: with the game paused the window keeps running (to confirm in the lab that this is wanted).

## 8. Incident to record

By mistake, once, I ran `data/parallel/logistics_ai/finishing/manual_collection/test_stack_v3.py` (the original), which **rewrites**
`manual_collection/test_output_v3.txt` (same size, 23848 bytes). No other file outside `forward_bases/stage2/` was touched;
`test_stack_v4.py` writes only `test_output_v4.txt` here and does not import/run the original. `mod/.../main.lua` (SHA `33d6c7e5…e679`) and `candidate_v3`
(SHA `9b89b113…63e6`) are intact before and after (checked by `run_all.sh` and step 99).

## 9. Files

`build_bases.py` (generates everything), `bases_cfg.lua`, `bases_funcs.lua` (applied fragments), `candidate_v4/main.lua` + `SHA256.txt`, `bases.patch` (CRLF),
`bases_lf.patch` (LF), `harness_bases.py`, `test_construction.py`, `test_recruitment.py`, `test_loss.py`, `test_workers.py`,
`test_persistence_bases.py`, `test_key_panel.py`, `test_orders_v4.py`, `test_collection_over_v4.py`, `test_stack_v4.py` + `diffs/test_stack_v4.diff`,
`sensitivity_bases.py`, `run_all.sh`, `TEST_OUTPUT.txt`, `test_output_v4.txt`, `PROGRESS_NOTES.md`.

Reproduce: `cd /d/GitHub/foxhole-rts && bash data/parallel/forward_bases/stage2/run_all.sh` (uses `PYTHONPATH=D:/tools/pylibs`).
