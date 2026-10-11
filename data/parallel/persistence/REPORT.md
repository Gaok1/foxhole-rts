# PERSISTENCIA (persistence) — save infrastructure and regional logistics safely (CLAUDE_PERSISTENCIA, 2026-10-09)

Offline delivery, not integrated. The real `main.lua` intact (SHA256 `33d6c7e5…e679` before and after). No game,
lab, channel, botloop or real saves. Universal-modder consulted at the start (`um kb search` save /
persistence / serialization / atomic write / foxhole); proposed gotchas in `PROPOSED_GOTCHAS.md`.

## 1. Audit of the current save/continue (`mod/FoxholeRTS/Scripts/main.lua`)

| # | Where | Problem |
|---|---|---|
| A1 | `sv.parse` 4397-4403 | `load(txt, "save", "t", {})`: empty environment, but it runs the file (infinite loop/memory) and accepts any expression that yields a table with `v == 1`. |
| A2 | `sv.save` 4445-4452 | `io.open(..., "w")` directly on the single file: a crash/full disk midway truncates the save; the return of `write` ignored; no backup. |
| A3 | `sv.ser` 4379-4395 | NaN/inf become `0` and userdata/functions become `nil` silently (data loss without an error). |
| A4 | `sv.load` 4514-4530, `sv.restore` 4465-4512 | Only checks the map's short name. `sv.restore` calls `clearSquad` (4466) before any world check; if `addPoint` (2227-2233) refuses a point, the indexes shift and the depots `pts[i]` (3095) and enemy posts (4499) land on the wrong point. `pcall(logi.restore)` ignores failure (4522). |
| A5 | `logi.restore` 3089-3097 | `logi.start()` (2673) recreates the scenario stock (bmat 240, starting ammo/shirts) and only then assigns; no number validation. |
| A6 | `logi.snapshot` 3081-3087 | No job (bmat already debited vanishes), no trucks/cargo in transit, no rebuild state. (Fixed by the ECONOMIA v2 schema.) |
| A7 | `logi.deployWallet` 2523-2527, `logi.deploy` 2614-2662 | Wallet keyed by `GetFullName..GetAddress` (changes on every load) and never saved; deploy does not record what it paid. After a restart, ruins come back, the wallet is reborn with 1100: continuing requires Alt+L again and pays again. **Infrastructure and budget do not persist.** |
| A8 | `logi.start` 2681 | The enemy convoy goes back to `cargo0` on every continue (enemy cargo recreated). |
| A9 | `sv.tick` 4533-4550 | Autosave after an incomplete continue overwrites the good save with the degraded match. |
| A10 | `sv.clear` 4462 | Only removes the main file. |

Already persisted (v1, by coordinate): points/owners/progress/enemy trench/wire, barriers, trenches,
posts, wires, soldiers of both sides, score, manpower, difficulty, mode.

## 2. Schema v2 (reconciled with ECONOMIA and IA_LOGISTICA)

Same `return {...}` text as v1; **read by `sv.decode`** (literal parser, no `load`). Top-level `v = 2`:

| Field | Owner | Content |
|---|---|---|
| `v, map, diff, wave, kills, losses, elapsed, mp, aimp, shots, hits, nextIn, mode, points, squad, enemies, walls, trenches, tents, wires` | v1 (unchanged) | same as v1 |
| `world` | PERSISTENCIA (new) | world path without the class prefix (`/Game/Maps/Master/CallumsCapeHex.CallumsCapeHex`); case-insensitive comparison |
| `logi` | **ECONOMIA** (`version=2`, `data/parallel/economy/save.lua`) | unchanged; validated by its `logi.validateSave`, against the points **of the save** (proxy), not the live ones |
| `infra` | PERSISTENCIA (new, `version=1`) | `budget, bmat, spent` (deployment wallet) + `built[]` = paid records `{kind="site", code="Refinery"/"Factory", x,y,z,yaw}` and `{kind="truck", x,y,z,yaw}` |
| `elogi` | **IA_LOGISTICA** (`v=1`, `logi.eSnapshot`) | accepted only if its module is integrated and `logi.eValid` approves; without the module, refusal ("campo desconhecido: elogi") |
| `enemy` | PERSISTENCIA (`version=1`, reserved) | `cargo, convoys, cut` of the current main's abstract convoy; **not written** when IA_LOGISTICA is integrated (it owns the enemy state through `elogi`) |

Rules: no actor, userdata, function or address (`sv.pure` + decoding of the text itself before writing);
an unknown field at the top, in `infra`, in records and in `enemy` = refusal (no silent discard);
`bmat + spent == budget` and `spent == Σ cost(built)` (400/400/100 from `CFG.DEPLOY`); a single installation per code.
ESTRADAS routes are **not** saved (the epoch includes the session): the truck replans (`route/routeDest/pathJob=nil`,
already done by ECONOMIA). The truck's destination and depots stay by point index (ECONOMIA's contract), with
stabilized identity: the preflight guarantees all points come back and `sv.verify` checks index→coordinate.

**Versions/migration.** `v=1` (legacy, with or without `elogi` from a build with the AI): accepted; without `infra`, the wallet
is not touched (current behavior); `logi` without `version` = ECONOMIA legacy. `v>2`, `infra.version>1`,
`enemy.version>1`: refused with "versão futura" and the file kept. To change the schema: bump the version of the owning
block and add the migration in `sv.validate`/loading.

## 3. Revalidation before restoring (`sv.preflight`, no mutation)

1. File: the first valid one among `save.txt`, `.tmp`, `.bak` (`sv.read`); nothing is deleted on read.
2. Complete schema (`sv.validate`), incl. ECONOMIA and IA_LOGISTICA through their validators.
3. World: `world` equal to the current path (v1: short name).
4. Surface: each saved point with `surfaceZ` and without overlap (otherwise `addPoint` would refuse); ground (`groundZ`)
   for barriers, trenches and posts.
5. Infrastructure (`sv.infraPlan`): the current load's wallet read **without creating it** (`logi.walletId`).
   - Same load with an identical deployment (sites per code ≤ 2 m, same truck count): nothing to do.
   - Load with a different deployment: refusal.
   - New load: each paid installation needs an active one (not redone, not refunded) or a ruin of the right class within
     ≤ `PERSIST.tol` (200 cm) and yaw ≤ 1°; an active salvage field (never invented); missing trucks only up to the
     paid number, in validated Landscape spots (`logi.parking`); classes loaded.
6. Logistics: with an empty plan, `logi.ready()` must find the active chain.

Only then: `logi.applyPlan` (own rollback: destroys partial spawns, restores ruin hiding/collision, does not
touch the wallet) → wallet := the save's (no new debit) → `clearSquad`/`sv.restore` → `sv.verify` →
`logi.restore` (ECONOMIA, replaces, does not add) only if the points match → `logi.eRestore(d.elogi)` (AI) or
`enemy`. `logi.deploy` was split into `logi.applyPlan` (no wallet) + `logi.deploy` (debits and records
`wallet.built`); Alt+L behavior unchanged (`test_orders` suite PASS).

## 4. Error handling

- Refusal before mutation (missing/corrupted/truncated/large file/future version, another world, surface,
  missing/moved/rotated ruin, missing field, no spot, unpaid trucks, divergent deployment, spawn
  failure): `false`, warning "Continuar recusado (partida atual e save preservados)", session and files identical.
- Failure after the preflight (a soldier/point/fortification that does not come back): the match continues marked INCOMPLETA,
  logistics only comes back if the points match (otherwise `logi.reset`, no fictitious stock), **autosave suspended**
  for that match (`sv.degraded.start == combat.startT`); Ctrl+F6 tries again without recharging/duplicating
  infrastructure; Shift+F6 (new match) releases the autosave.
- Writing: temporary file reread and checked → previous one to `.bak` (or `.corrupt` if invalid) → the temporary becomes
  the save (Windows does not rename over: remove the destination first); a failure restores the previous one. `sv.save` refuses
  NaN/userdata/invalid schema and keeps the old file. Victory/defeat deletes `save.txt`, `.tmp`, `.bak`, `.corrupt`.

## 5. Tested (offline, lupa) and result

```bash
# repository root (Git Bash)
PYTHONPATH=D:/tools/pylibs python data/parallel/persistence/build_patch.py
PYTHONPATH=D:/tools/pylibs python data/parallel/persistence/test_persistence.py
PYTHONPATH=D:/tools/pylibs python data/parallel/persistence/test_regression.py
```

- `test_persistence.py`: **36/36 PASS** = 9 scenarios × Lua 5.4 (UE4SS) and 5.5 × 2 stacks
  (main+ECONOMIA+PERSISTENCIA and main+ECONOMIA+IA_LOGISTICA+PERSISTENCIA). Each game load is a new runtime
  with the whole candidate chunk; only io/os, actors/spawn/traces and soldier/point/fortification spawn are fake.
  Scenarios: parser (no `load`, no userdata, 21 malicious/corrupted inputs refused, limits); schema and
  future versions/v1 migration; **round trip** on a new load (5 spawns, wallet 0/1100 without debit, ledger
  completely identical, single delivery at the right depot, rewriting without actor/address); **repeated restore**
  (3×, without duplicating actors or stocks; same load; Alt+L before continuing); **refusals** keeping the session
  and file (wrong world, different case accepted, moved/rotated ruin, missing field, roof, point without
  surface, wall without ground, divergent deployment, future version, truncated, negative stock, missing,
  invalid `elogi`/without module, unpaid trucks; with native trucks without refund); **rollback** of a partial
  spawn; **post-preflight failure** (autosave suspended, no fictitious stock, new attempt without duplicating);
  **atomic write** (open/write/rename failing, crash between renames recovered from `.tmp`, corrupted
  goes to `.corrupt` without losing `.bak`, NaN does not write); **legacy v1**.
- `test_regression.py`: PASS in `tools/test_orders.py` (stack without AI and with AI, with the convoy block swapped
  for the AI's as it does), `economy/test_integration.py`, `logistics_ai/test_logistics_ai.py` (over the stack
  with persistence) and `tools/check_globals.py` on both candidates (≤ 180 top-level locals; no new local).
- Manual mutation tests (not versioned): removing the autosave suspension, infra idempotency, the ruin
  check, atomic write, the world check or the wallet restore makes the suite fail. The guard
  `pointsOk` before `logi.restore` is redundant today (ECONOMIA's `validateSave` also refuses), kept
  as a defense.
- Cost measured offline: `sv.save` with 120+ units ≈ 11 ms; read+validate ≈ 6 ms (lupa; live is a gate).

## 6. NOT tested (live gates — see `LAB_SCRIPT.md`)

`io.open("rb"/"wb")`, `f:seek`, `os.rename`/`os.remove` in UE4SS's Lua/Windows; a real spawn redoing the
infrastructure on a new load of the hex and identical ruin/yaw between loads; the world's `GetFullName`; cargo in
transit resumed with the real driver; cost on the game thread; IA_LOGISTICA live; a real crash between renames.
Transport keeps going straight until ESTRADAS integrates the driver. **The task is not finished** without the lab
matrix.

## 7. Application order

1. ESTABILIDADE (already in main) → 2. **ECONOMIA** → 3. **IA_LOGISTICA** (optional) → 4. **PERSISTENCIA**.
- Without the AI: `persistence.patch` (diff over main+ECONOMIA). With the AI: `persistence_over_ai.patch` (diff over
  main+ECONOMIA+AI). PERSISTENCIA replaces the `sv.load` line the AI anchors on, so it comes after it;
  `build_on` recognizes both variants. `persistence_complete.patch` = current main → final (reference).
- Recommended to apply through the script (`build_patch.build` / `build_with_ia`, unique anchors, fail-closed). The
  `.patch` files are LF; `main.lua` is CRLF (candidates in `candidate/` come out CRLF).
- INTERFACE: PERSISTENCIA's anchors do not touch the HUD; the ECONOMIA × INTERFACE conflict (`table.concat(deps,
  " | "), foe)`) is older and does not depend on this delivery.
- No new key (Ctrl+F6/Shift+F6 unchanged): `MANUAL_TEST.md` and the key test do not change. The README needs to
  describe: save v2 with infrastructure/wallet, refusals and autosave suspended on an incomplete continue.
- Channel: `sv`/`logi` are already in `env`; the new functions (`sv.preflight`, `sv.infraPlan`, `sv.decode`,
  `sv.validate`, `logi.applyPlan`) are reachable without changing `runCommandFile`.

## 8. Risks

- A hex/server layout change (ruin elsewhere) makes the save unrecoverable by design (refusal, it does not
  invent). The 2 m / 1° tolerance is a hypothesis to confirm live.
- An incomplete continue suspends the autosave until a successful Ctrl+F6 or a new match: it protects the save, but the
  progress of that match is not written (warned on screen).
- An installation already natively active on a new load is reused without refund (conservative).
- Fallback to `.bak`/`.tmp` loads a save up to 30 s older (warned as "[lido de save.bak]").
- `sv.parse` became only a decoder (contract used by the suite's and the AI's tests); validation of the whole save is
  `sv.parseSave`.
- Python may have used the existing `__pycache__` in `economy/` when importing its build; the build now
  turns off bytecode writing.

## Files

`persistence.lua` (module `sv`/`CFG.PERSIST`), `deployment.before.lua`/`deployment.after.lua` (deploy
split), `build_patch.py`, `persistence.patch`, `persistence_over_ai.patch`, `persistence_complete.patch`,
`candidate/main.lua`, `candidate/main_with_ai.lua`, `harness_test.lua`, `test_persistence.py`,
`test_regression.py`, `lab/t_persist_state.lua` (read-only probe, not run), `LAB_SCRIPT.md`,
`PROPOSED_GOTCHAS.md`.
