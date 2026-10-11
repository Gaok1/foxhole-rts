# CONSOLIDATED_GOTCHAS — for the note `knowledge/games/foxhole/local-listen-server-rts-sandbox-in-foxhole-with-ue4ss.md`

Merges, without duplicates, `logistics_ai/PROPOSED_GOTCHAS.md` (7), `persistence/PROPOSED_GOTCHAS.md` (7), the findings cited in the reports of ECONOMIA, the integration rehearsal, the AI finishing,
ESTABILIDADE and INTERFACE, and what this package learned. Nothing was written to universal-modder (outside the package's scope). The INTEGRACAO/LABORATORIO task records it:
`cd D:/GitHub/universal-modder` → edit the note → `UM_HOME=D:/tools/um-home python -m um kb check` (local; PR only with the user's OK).

The current note ends at item **42**; this file goes from **48** to **77** as requested (43–47 are left for other pending proposals; if the note's real numbering differs, renumber
only the prefix, the text does not depend on the number). Mark on each item: **[confirmed live]** or **[offline only]**. **None of these items was confirmed in the game**: the package is
preparation; the lab swaps the mark for the result of the step cited in "Verify" (`BATCH_SCRIPT.md`). Data/design items (`CFG` values) are not gotchas and stay in
`OPEN_DECISIONS.md`.

---

48. **A "cargo" counter is not logistics.** [offline only] The enemy convoy added +1 cargo on arrival, with no origin, and the save did not keep that number (every continue gave back `cargo0`).
    **Cause:** interdiction had no traceable effect because nothing was debited from a stock that could run out. **Fix:** the truck carries crates debited from a finite rear
    and the loss goes into a ledger (initial + produced = stocks + transit + consumed + lost) checkable through the channel (`eAudit`/`eReport`; `auditoria=true` at the end of every match). Verify: I1–I14.

49. **A factory that can always spend 80 bmat never lets the 100 truck come back.** [offline only] **Symptom:** under continuous consumption the destroyed truck does not come back. **Cause:** the recipe (80) is cheaper
    than the truck (100): bmat never accumulates 100 (0/31 came back in the harness). **Fix:** reserve `truckCost` per truck destroyed or not yet built (`logi.rebuildReserve`) and let the factory
    wait; a forward base order reserves another 300 **after** the truck's reserve (the truck has priority). The panel shows `Fábrica | guarda N bmat para …`. Holds for both sides; the
    effect on the player's side is still a hypothesis. Verify: C12.

50. **A one-crate convoy wastes a truck.** [offline only] Dispatching as soon as one crate exists makes each ambush cost a whole truck for little cargo, and the cheapest product monopolizes the
    factory. **Fix:** minimum load (`minLoad 3`) or the front's complete order (`trip 20`). Verify: I2, I7.

51. **The save rounds.** [offline only] `sv.ser` writes non-integer numbers with 3 decimal places; a ledger validated on load with a 1e-6 tolerance refuses legitimate saves. **Fix:** validate with slack (0.05) and, when
    restoring, absorb the leftover into the origin terms so the in-memory ledger closes exactly; never turn the leftover into stock. Verify: I9, V4.

52. **Attributing interdiction requires a counterfactual.** [offline only] Cargo lost before wave N affects several waves, not only the next. **Fix:** a "losses since the last wave" counter underestimates; use a
    phantom stock that is spent the way the waves would have consumed it (`byCut`). Verify: I14.

53. **The enemy chain's calibration only holds at the real wave cadence.** [offline only] The calibration table (floor `free 5`, `want 4/20`, `trip 20`) holds at a wave cadence ≥ ~55 s; the refinery
    (2 bmat/s) is the ceiling of any chain, so more trucks or a higher floor do not produce more soldiers. **Fix:** measure the real wave cadence (bot and human) before touching the numbers. Verify: I14, R.

54. **Testing the whole chunk with swapped boundaries.** [offline only] In the lupa harness, code appended at the end of the same chunk can reassign top-level `local function`s (`spawnEnemies`, `waveSpawnPoint`,
    `isLocalAuthority`), and the mod's functions see that as an upvalue. **Use:** swap only the engine boundary and call the real `waveTick`/`ai.tick`/`sv.load`, without copying the implementation nor editing `main.lua`.

55. **Decide, create, debit (in that order).** [offline only] The spawn of a soldier, truck or base can partially fail; an actor with `IsValid` and `bActorIsBeingDestroyed` does not count as created. **Fix:**
    decide quantity and location in a **pure** function (`logi.spawnSite`), create, confirm the actor (position, health, `CodeName`) and only then debit at a single point (`logi.spawnCommit`; the base's bmat only leaves
    after the validated actor). On failure: nothing debited, actor undone. Holds for the enemy wave (unchanged `combat.wave` detects the wave that did not even open), recruit, worker and base. Verify: K3, K6.

56. **A save as `return {...}` + `load` is not a safe read.** [offline only] An empty environment blocks `os`/`io`, but not an infinite loop nor a giant string, and it accepts any expression that evaluates to a
    table. **Fix:** a literal parser (tables `[k]=v`, numbers, `%q` strings, booleans) with byte/depth/item limits, no dependency (`sv.decode`/`sv.parseSave`). `sv.ser` also silently wrote
    NaN/inf as `0` and userdata as `nil`: validate what will be written and decode the text itself before swapping the file. Outside the game: `read_save.py`. Verify: V1, V2.

57. **Windows: `os.rename` does not overwrite.** [offline only: confirmed in plain Lua, not in UE4SS's Lua] MSVCRT fails if the destination exists (`rename` returns `nil, "File exists"`). **Fix:** atomic write
    with a temporary checked by rereading → the previous becomes `.bak` (or `.corrupt`, if invalid) → the temporary becomes the save; the code removes the destination first. A failure restores the previous one. On read, order
    save → `.tmp` (crash between the renames) → `.bak`. Verify: S7 (`pv4_io_os.lua`), V1, V7.

58. **Deployed infrastructure does not survive a restart, and an address-keyed wallet is reborn full.** [offline only] `S.deploy` was keyed by `GetFullName..GetAddress` (changes on every load) and did not go
    into the save: continuing required Alt+L again and paid again. **Fix:** persist what was **paid** (code, XYZ, the ruin's yaw) and the wallet (`spent`); on a new load rebuild only over a matching
    ruin (≤ 2 m, ≤ 1°), without charging again, and the trucks only up to the paid number. Never persist an address (it only identifies the current load). Verify: V3–V8.

59. **A point index as identity breaks if a point does not come back.** [offline only] The save keeps depots, posts and bases by index; `addPoint` may refuse (no surface, overlap, limit).
    **Fix:** check surface/overlap before clearing the match and compare index→coordinate afterwards; a difference = logistics not restored (no fictitious starting stock in its place) and autosave
    suspended (`INCOMPLETA`) so as not to overwrite the good save. Verify: V9, V10.

60. **Preflight before `clearSquad`.** [offline only] The old continue destroyed the current match and only then discovered problems. **Safe order:** read/validate → world/surface/ruins/wallet/logistics →
    rebuild infra and bases (own rollback) → clear and restore → check counts. The refusal keeps the match and the file. Verify: V9.

61. **`logi.start` creates scenario stock.** [offline only] Restoring by calling `start` and then assigning fields leaves fictitious stock if something fails midway; the enemy convoy went back to `cargo0`. **Fix:**
    validate everything first; on failure, `logi.reset` instead of leaving the starting stock. A regenerable and **discardable** section (the enemy chain, `elogi`): instead of refusing the save, discard only it and restart from the
    scenario with a warning ("CADEIA INIMIGA REINICIADA"). Verify: I13.

62. **Routes are not saved.** [offline only] The ESTRADAS graph has an epoch tied to the session; an old route is invalid by construction. **Fix:** save only state/cargo/destination by identifier and replan
    (`route/routeDest/pathJob = nil`). Verify: V6.

63. **A new recipe does not work by just editing `CFG.LOGI`.** [offline only] Transport, depot, priority (Shift+L), consumption and save were fixed to `ammo`/`shirts`. **Fix:** when adding a product,
    walk the whole list (recipe → factory → truck → depot → priority → recruiting/medic → save → panel → ledger). The current 4 products are in `CFG.LOGI.products`. Verify: C10.

64. **Native recipe ≠ a similar item.** [offline only] A grenade (`GrenadeW`) requires **Explosive** besides Cloth; a consumable bandage (`Bandages`) is not a `FirstAidKit`. **Fix:** read the client's real
    `ProductionResource`/recipe (see gotcha 35, `tools/export_costs.lua`) before naming a product; do not substitute a similar name.

65. **A panel that replaces the whole function does not commute with patches that anchor inside it.** [offline only] The new panel (INTERFACE) replaces the whole `logi.hudLine` by text boundaries; patches from other deliveries that
    anchor on an inner line (products, medic, collection, base) stop applying. **Fix:** rebase the panel over the stack (INTERFACE v2 was redone after v2 and the reserve) and
    order: ECONOMIA > IA_LOGISTICA > reserve > INTERFACE > PERSISTENCIA > COLETA > BASES.

66. **A `.patch` written by `write_text` on Windows comes out CRLF and does not match a main in LF (or the reverse).** [offline only] **Fix:** write with `newline="\n"`, or apply through a script (`aplicar_*.py`)
    and keep pairs `.patch` (CRLF, for the CRLF main) and `*_lf.patch`; check the result's SHA256, not only "applied without error". The repository's `main.lua` is consistently CRLF.

67. **A 2-product cargo return adapter becomes obsolete when the economy generalizes products.** [offline only] The adapter that returns cargo when coming back from a delivery (`returnCargo`, `back = {…}`) was born for ammo and shirts;
    with 4 products, any old copy only handles two. **Fix:** iterate `CFG.LOGI.products` in any cargo movement and test with all 4.

68. **The panel mixes crates and units; the selector's XY rectangle is not the screen's.** [offline only] In the panel, crates (ammo) and units (shirts, rifles, bandages) show side by side; always label
    (`camisas 3 caixas (30 unidades)`). UMG projection/DPI/border still require a probe; text clipping only shows in captures at several zooms/resolutions (C13, manual items 12ad).

69. **A lifetime/preflight guard on the outline does not explain the UE4SS crash.** [offline only] The mock reproduces calls on a pawn/clone with `bActorIsBeingDestroyed` or source `IsValid=false`, and the preflight
    blocks them, but **this does not explain** the batch 17 crashes: `pcall` protects Lua errors, not native lifetime, and a source `IsValid=true` during removal or swap still needs a real trace. Do not attribute a cause
    without repeating the clean load on the same hash. (v4 does not touch that code.) Gate: G.

70. **`notify` also writes to `UE4SS.log`.** [offline only: read in the code] `notify(msg, secs)` calls `log(msg)` (prefix `[FoxholeRTS]`) before the native alert. **Use:** every panel and alert message
    (refusals, `BASE AVANÇADA … construída`, `COMBOIO INIMIGO DESTRUÍDO`) can be audited in the log even when the capture did not catch the text; no OCR needed.

71. **A test that anchors on the old main's text needs the old main.** [offline only] After integrating v4, some tests (`test_pilha_v4` steps 06b/06b-L/06c/08/08-L) fail with "âncora não única" because
    they look for the code of the previous base. **Fix:** keep a copy of the previous main (`pre_integration_base/`, SHA `33d6c7e5…`) and redirect only the test's read to it; keep
    a negative control (a suite broken on purpose fails). The `post_integration_battery.py` battery does this without writing to disk.

72. **A probe that toggles state has to be idempotent: `newGame` already turns waves on.** [offline only] `newGame` ends in `toggleWaves()` with `combat.auto=false` before, so the new match **already has automatic
    waves**; a probe calling `toggleWaves()` blindly would turn them off (and `sv.save` requires `combat.auto`). **Fix:** `pv4_cmd_mode.lua` turns on only if off (`ondas`) and off only if
    on (`sem_ondas`). Holds for any toggle (pause, speed, edge).

73. **A keyboard confirmation clock is real time, not game time.** [offline only] The 2 presses of Shift+J use `GetRealTimeSeconds` (4 s): pausing the game between presses does **not** stretch the window. The pending
    order, on the contrary, expires in 180 s of game time. Decide by effect: UI confirmation → real; simulation → game. Verify: K10; decision in `OPEN_DECISIONS.md`.

74. **A native class that exists in the pak does not prove a whole spawn.** [offline only] `ForwardBase1` (1725 HP) shows up in the client's inventory, but **no agent instantiated it live**. **Fix:** a
    `strict` contract on spawn (`Health == MaxHealth == 1725`, `CodeName == ForwardBase1`, position and yaw as requested) before debiting the bmat; a failure undoes the actor and does not charge. `TeamId` stays unwritten
    (`FWD.teamId=nil`) until measured. Plan B (mesh) is another task if the class does not spawn. Verify: S11 (bases B1).

75. **Unarmed soldier: `grip 0` does not prove the mesh stays without a T-pose.** [offline only] The worker uses `CFG.WEAPONS.worker` with `grip=0` and range 0. Nobody saw the soldier without a weapon live; the code
    comments "confirmar no laboratório" and the risk is a T-pose or a weapon animation without a weapon. **Fix:** look at the capture in step C2 (3 workers) before approving; if a T-pose appears, give it the posture of another class without ammo.
    Verify: C2, manual item 12z.

76. **Local count: the compiler decides.** [offline only] The limit of 200 locals per Lua chunk: main has 178 by the compiler (22 headroom) and 175 by the `check_globals.py` count. The headroom (22)
    is the smaller one; new functions go into tables (`logi`, `sv`, `rts`, `CFG`, `S`). The battery checks the headroom in Lua 5.4 and 5.5.

77. **A non-combat role in the same vector as the squad contaminates every `#squad` count.** [offline only] The collection workers live in `squad` (selectable, attackable, saved like any soldier). v4
    already took them out of the cap of 12 and the logistics defeat, but the **enemy wave scale** (`floor(#squad * WAVE_SQUAD_SCALE)`), the "next wave" warning and the Assault defeat still counted everybody: 3 workers
    became ~+1 enemy per wave. **Fix (v4.1):** a single combatant function (`rts.combatCount`) in every use that **decides** something (scale, defeat, limit); `#squad` stays only for what is truly the vector
    (indexes, saving, listing). When creating a new role, `grep '#squad'` and classify each use. Also holds for position: `squadCenter()` (which decides where waves and reinforcement come from) only counts live combatants, with a fallback to everyone. Contrast test: `v4_1/test_v4_1.py`.
