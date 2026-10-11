# MODLOG_DRAFT — top entry for `MODLOG.md`

Draft for the INTEGRACAO/LABORATORIO task to paste **at the top** of `MODLOG.md` (new entries go at the top), **after** running `BATCH_SCRIPT.md`. Everything the text
claims about code and offline tests was checked against candidate **v4.1** (`package_v4/v4_1/candidate/main.lua`, SHA256 `62245d23…598f` = `candidate_v4` `025e3b80…aab0` + `v4_1/v4_1.patch`) or run on the rehearsal copy (`HOW_TO_INTEGRATE.md` §6).
The `[fill in at the lab]` fields are live measurements **nobody has made**: if one is not measured, delete the sentence instead of leaving the field, and do not write an invented result.
Adjust the date and title to the session's day. Nothing here was applied.

Filling instructions: replace each `[fill in at the lab]` with the number from the output of the step shown in parentheses (the steps are from `BATCH_SCRIPT.md`);
where a step failed, write "FAILED" and the reason, and do **not** repeat the promise of the first sentence.

---

## 2026-10-10 — Stack v4.1 (ECONOMIA, IA_LOGISTICA v2, bmat reserve, INTERFACE v2, PERSISTENCIA v2, COLETA_MANUAL, BASES_AVANÇADAS, workers outside the wave scale): integrated and validated in a batch

- **What went in (a single `main.lua`, v4.1, SHA256 `62245d23af36160f589707fe422b6fb167abaa58482ef7f58a49cd39021b598f`, CRLF, 7323 lines; before `33d6c7e5…e679`; v4 `025e3b80…aab0` is the base).** Stack order: ECONOMIA >
  IA_LOGISTICA v2 > bmat reserve > INTERFACE v2 (rebased panel) > PERSISTENCIA v2 > COLETA_MANUAL > BASES_AVANÇADAS. ESTRADAS did **not** go in. The per-function diff (105 hunks) does not touch the outline,
  the animation hook nor the camera. Top-level locals: 178 by the compiler (22 headroom), 175 by `check_globals.py`; nothing new at the top (everything in `CFG`, `S`, `logi`, `sv`, `rts`).
- **Economy:** the logistics match has 4 products in the factory (ammo 80 bmat, shirts 80 bmat/10 units, rifles 100 bmat/20 units, bandages 80 bmat/50 units). Recruiting costs **1 shirt**
  (the rifleman, also 1 rifle) from the stock of the spawn location; it does **not** spend manpower (which only pays for mortar, barrier, trench, crate, post and wire, and recruiting
  **in Assault**). The medic only treats with bandages in a depot within ≤ 5 m (consumes 1 per treatment). Recipe/structure costs come from the game's tables.
- **bmat reserve:** 100 per truck destroyed or still to be built; the factory does not spend that reserve on crates. A forward base order reserves another 300, after the truck.
- **Manual collection:** Shift+F6 **no longer** creates the resource truck. The match starts with bmat 40, 30 shirts, 10 rifles, 6 ammo crates and 3 workers (soldiers **without a weapon**, 1 shirt
  each; the 1st at ~5 s, the others every ~3 s) who collect salvage on foot (0.5/s, load 40) until the factory gathers 100 bmat and builds the truck. A player order releases the worker
  for 60 s; combat makes them pause. Deployment (Alt+L) went from 1100 to **1000** bmat (2 supply trucks instead of 3).
- **Logistics AI v2:** the enemy has a real chain (rear → factory → `BPTruckC` convoy → front); closed ledger (`eAudit`). The wave gets the free garrison (floor 5/wave) plus what the front equips;
  a destroyed convoy yields +25 manpower. The v2 calibration (`CFG.ECHAIN`: `free 5`, `trip 20`, `front0 m2/c10`, `want 4/20`, `trucks 2`, `minLoad 3`) is a **proposal**; it holds at a wave cadence ≥ ~55 s.
- **Panel (INTERFACE v2):** several lines (logistics, factory, ready, depots, `base …`, trucks, `INIMIGO …`, `coleta manual …`, shortcuts), 12–13 lines, ≤ ~222 columns measured offline.
- **Persistence v2:** save v2 with a literal parser (never `load` of the file), atomic write `.tmp` → `.bak`/`.corrupt`, paid infrastructure and forward bases rebuilt for free and
  **all or nothing**, the `elogi` section discardable on its own ("CADEIA INIMIGA REINICIADA"), "Continuar recusado (partida atual e save preservados)", "INCOMPLETA … autosave suspenso".
  The infrastructure does **not** survive a game restart by itself (the ruins come back); only Continue rebuilds it.
- **Forward bases:** Shift+J (2 presses within 4 s of real clock), 300 bmat, native structure `ForwardBase1` (1725 HP), up to 3, 15 slots, the recruit spawns at the base's exit with the shirt and
  rifle of the base itself; a plain point does **not** reinforce (`CFG.SPAWN.pointSpawn=false`); loss by capture of the point or by enemy mortar (`blastMul` 2) erases the structure and the stock.
  `J` now only creates a point **without** a modifier.

- **v4.1 (orchestrator's decision):** collection soldiers (`role="worker"`) do not count toward the enemy wave size, the "next wave" warning nor the Assault defeat by lack of troops
  (`waveTick` and `logi.noReinforce` now use `rts.combatCount()`) and `squadCenter()` uses only the live combatants (fallback: all the living; nil with nobody), so the salvage field does not pull waves, reinforcement, wire nor starting points. 4 swaps, no new top-level local.

### Offline checks (done before the lab)

- Post-integration battery (`data/parallel/package_v4/post_integration_battery.py`): with v4.1, **28/28 PASS** (the new item is `v4_1/test_v4_1.py`; with `--sensibilidade --rapido`, 26/26 with the 21 mutants caught); with pure v4 it was 27/27 and the same battery fails only on the new item. It covers (on a rehearsal copy in the scratchpad) syntax and local headroom in Lua 5.4 and 5.5, `check_globals`,
  `test_costs`, `test_inventory_probe`, the adapted `test_orders`, 7 base suites, steps 05–09 of `test_pilha_v4` and the v4 × v4.1 contrast; it has a negative control (a suite broken on purpose fails).
- `tools/test_orders.py`: 9 adaptations to the new keys/messages + the v2 convoy block (`apply_test_orders.py`); passes against the candidate.

### Lab (fill in with the steps' outputs; everything below is live measurement)

- **Stability gate** (G): A1 184 s (already at the top of MODLOG, 2026-10-09). B1 184.3 s, 168 copies, stratTick ~12 ms (file `crash-control-B1.txt`). B2 `[fill in at the lab]`;
  A2 `[fill in at the lab]`. Gate source: `[fill in: 33d6c7e5… or 62245d23…]`. Log without `Registry`/`Access violation`: `[fill in at the lab]`.
- **Read-only probes / bench (S):** UE4SS and game version `[fill in at the lab]`; `io.open`/`os.rename`/`os.remove` on Windows `[fill in at the lab]` (S7);
  world and surface `[fill in at the lab]`.
- **B1 of the `ForwardBase1` class (S11):** spawn `[fill in at the lab]` ms; `Health/MaxHealth` `[fill in at the lab]` (expected 1725/1725 by the `strict` contract);
  `CodeName` `[fill in at the lab]`; `TeamId` `[fill in at the lab]` (the mod does not write it); vanishes without residue `[fill in at the lab]`; 60 s without a crash `[fill in at the lab]`.
- **Hex (H0–H1):** map `CallumsCapeHex`; Alt+L `[fill in at the lab]` (expected `-1000 bmat do cenário; saldo 0`, 2 `BPTruckW_C`); repeating does not duplicate `[fill in at the lab]`.
- **Manual collection (C):** real field–refinery distance `[fill in at the lab]` m; 1st delivery at `[fill in at the lab]` s; 1st resource truck at `[fill in at the lab]` s
  (harness: 165 s at 80 m, 359 s at 470 m); workers' T-pose `[fill in at the lab]`; worker stuck/lost `[fill in at the lab]`; reactivation after losing the truck
  `[fill in at the lab]`; per-frame cost with and without collection `[fill in at the lab]` ms.
- **Economy (C10–C12):** the 4 products reach the depot `[fill in at the lab]`; recruiting riflemen refuses when the 10 rifles run out `[fill in at the lab]`; the 100 bmat reserve
  holds the factory and the truck comes back in `[fill in at the lab]` s.
- **Enemy chain (I1–I14):** convoy 1 left at `[fill in at the lab]` s; single delivery `[fill in at the lab]`; ambush: single loss + `+25` alert
  `[fill in at the lab]`; `auditoria` true at the end of every match `[fill in at the lab]`; active `BPTruckC` ≤ 2 `[fill in at the lab]`.
- **Forward bases (K):** eligible points in the hex `[fill in at the lab]`; construction `[fill in at the lab]` (whole actor, `bmat` debited only after the actor); recruiting at the base
  `[fill in at the lab]`; loss by capture and by mortar without a residual actor `[fill in at the lab]`; 10 min with 3 bases (T1): PID alive `[fill in at the lab]`, cost
  `[fill in at the lab]` ms/frame.
- **Persistence (V):** `sv.save` `[fill in at the lab]` ms, `sv.load` `[fill in at the lab]` ms; 4 spawns on restore; wallet `0/1000`; idempotency of the 2nd `sv.load`;
  refusals (V9) `[fill in at the lab]`; files restored to the initial SHA256 `[fill in at the lab]`.
- **Panel and keys (real user input):** see `MANUAL_TEST.md` items 2, 8, 9, 11, 11a–11j, 12s–12v, 12y, 12z*, 12aa–12am: `[fill in with the user's result]`.
- **Regression with the bot (R, optional):** `[fill in at the lab]` or "did not run in this session".
- Lab closed: only the copy's PID (`[fill in: PID]`); Steam preserved; temporary `map.txt` removed `[fill in at the lab]`.

### Decisions and findings recorded in this entry

- Report × code divergences where the integration text follows the code are in `HOW_TO_INTEGRATE.md` §8 (the list of 9 items). Decisions that depend on the user (balance): `OPEN_DECISIONS.md`.
- New gotchas (from 48 on) in `CONSOLIDATED_GOTCHAS.md`, to be taken to `knowledge/games/foxhole/…` with `UM_HOME=D:/tools/um-home python -m um kb check`.
- Pending items that do **not** close with this batch: the complete stability gate (B2/A2) if it ran with another source; the bases' visual plan B (mesh) if `ForwardBase1` did not spawn; calibration of the enemy chain
  at the real wave cadence; Shift+J during pause (real clock).
