# OPEN_DECISIONS — what remains to decide or calibrate in stack v4

Only what depends on the user or on live measurement. "Where" = name in `CFG` and line in the candidate to integrate (v4.1; the lines are the same as v4, v4.1 swaps 3 lines without changing the count; the `main.lua` when integrating). The values are **design proposals**
(except structure cost/health/capacity, which come from the game's tables). Already decided and outside this list: workers outside the wave scale, the squad center and Assault defeat (v4.1, orchestrator's decision), the restart stock of the enemy chain (a discardable `elogi` restarts from the scenario stock),
the stack order, deployment at 1000 bmat.

| # | Decision | Current value | Where | What informs the decision |
|---|---|---|---|---|
| 1 | Factory starting bmat | `bmat0 = 40` (40 + 60 from 120 salvage = 100 for the 1st truck); 240 removes collection | `CFG.COLETA.bmat0` 2475 | C3: real time until the truck |
| 2 | Collection pace | `rate 0.5` salvage/s, `cap 40`, `workers 3`, `quiet 60` s, `leg 180` s | `CFG.COLETA` 2477–2489 | C3: ~6 min at 470 m (harness) vs 2 min 45 s at 80 m; real distance in the hex |
| 3 | Starting rifles | `startRifles = 10` (only in the manual match) | `CFG.SPAWN.startRifles` 2503 | C11: when they run out and how long the 1st batch takes |
| 4 | Minimum shirt floor | None. The reserve only protects worker replacement while collection is needed; without shirts and without workers collection stops | `logi.workerReserve` 3116; `CFG.LOGI.shirts0` 30 | Whether the base runs out of shirts during collection (C7) |
| 5 | Free floor of the enemy wave | `free 5`/wave; `trip 20`, `front0 m2/c10`, `want 4/20`, `trucks 2`, `minLoad 3` | `CFG.ECHAIN` 3540–3546 | I14: real wave cadence (the table only holds ≥ ~55 s); R (bot) |
| 6 | Enemy convoy | first at 20 s, then every 35 s, bounty +25 manpower | `CFG.ECONVOY` 3457–3458 | I2–I5 |
| 7 | Forward bases: quantity, cost, capacity | `max 3`, `cost 300` (game data), `cap 15` slots (interpretation of `StoredItemCapacity`, provisional) | `CFG.FWD` 2521 | K3–K5, T1 (10 min with 3 bases) |
| 8 | The base's pending order | cancels after 180 s of game time; the factory keeps 300 bmat (after the 100 per truck) | `CFG.FWD.pending` 2523 | K4: ammo starvation during the order |
| 9 | Shift+J confirmation | 4 s of **real time**: pause does not extend the deadline | `CFG.FWD.confirm` 2522 | Item 11i of the manual; K10 |
| 10 | `strict` contract and the base's `TeamId` | `strict = true` (refuses if `Health ≠ MaxHealth ≠ 1725` or `CodeName ≠ ForwardBase1`); `teamId = nil` (the mod does not write it) | `CFG.FWD.strict` 2519, `teamId` 2520 | S11 (B1 of the class): relax `strict` if a good base is refused; decide 255 × 1 |
| 11 | Ruin when losing the base and visual plan B | `ruin = false` (does not create a ruin); `visual = "native"`; `"mesh"` declared, **not implemented** | `CFG.FWD.ruin` 2518, `visual` 2515 | S11. If `ForwardBase1` does not spawn: plan B (mesh) is a new task, K does not run |
| 12 | The base's footprint and eligibility | `half 600`, `clear 150`, `maxSlope 60`, `maxHeight 250`, `minExits 3`, `exitR 800`, `minFromBase 3000`, `maxToEnemyPoint 4000` (cm) | `CFG.FWD` 2524–2525 | K1: is there ≥ 1 eligible point per match in the hex? |
| 13 | Does a control point without a base reinforce? | No (the recruit spawns at the main base). `true` restores the old behavior | `CFG.SPAWN.pointSpawn` 2508 | K7 and items 9/11f of the manual |
| 14 | Manpower in the logistics branch | Only pays for mortar, barrier, trench, crate, post and wire; recruiting uses a shirt (and a rifle) | `recruit` 1423 | Game: balance becomes clear in manual 8 and in the waves |
| 15 | Regression bot | `t_bot.lua` outdated (recruits with manpower, assumes a resource truck, does not use `L` nor Shift+J) | `tools/lab/` (was outside the repository) | R0 of the script; without the adaptation cells B0–B3 measure the bot |
| 16 | Stability gate | A1 and B1 done with source 33d6c7e5; B2 and A2 pending; v4 changes the hash | `stability/crash_control.md`, `HOW_TO_INTEGRATE.md` §2 | Coordinator's decision: gate before or after writing v4 |

Items 1–4, 7–9 and 13 are balance and only the user closes them. Items 10–12 are technical and the lab closes them with S11/K1. Items 5–6 and 15 depend on the real cadence. Item 16 is about process.
