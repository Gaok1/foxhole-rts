# BATCH_SCRIPT — one lab session for the v4 stack (for the LABORATORIO task)

Prepared offline by the PACOTE_V4 agent (2026-10-10). **Nothing below was run in the game.** It merges, without losing items, the scripts of
`logistics_ai/`, `logistics_ai/finishing/manual_collection/`, `persistence/`, `forward_bases/` (stages 1 and 2), `interface/`, `economy/` and
`stability/` (traceability at the end, §13). The lab owner (Codex coordinator) runs it; this file does not open the game.
In-game messages are quoted in Portuguese, as they appear in the log and on screen.

## 0. Batch rules (apply to every step)

- Steam open and logged in; copy at `D:\FoxholeLab\Foxhole`; **no** `botloop.sh` together with the command channel (the answers mix):
  `Get-CimInstance Win32_Process | Where-Object { $_.CommandLine -match 'botloop' }` must come back empty before each block that uses the channel.
- Publish only through `bash D:/tools/foxhole-lab/restart.sh` (syntax + `check_globals` + copy + restart + wait for "modo RTS ligado", 240 s).
  Never UE4SS's Ctrl+R. The first load is ~3 min of black screen "Not responding": it is **not** a freeze; confirm by log/process.
- **No keyboard or mouse injection.** What needs real input is in `MANUAL_TEST_DRAFT.md` (not here). The `pv4_cmd_*.lua` scripts
  call the same mod functions the keys call (`newGame`, `logi.deploy`, `recruit`, `logi.fwdKey`, `sv.save`, …) through the channel
  `sh D:/tools/foxhole-lab/run.sh <file.lua>`; that tests the logic, **not** the key registration nor J's `plain()`.
- The channel output comes only from `out(...)`. Mod messages (`notify`) go to `UE4SS.log` with the prefix `[FoxholeRTS]` (read it for the exact text).
- Each step records: time, hash of the published `main.lua` (`sha256sum`), game PID, channel output (`sh run.sh X > output_X.txt`) and, when
  indicated, a capture (`cd D:/GitHub/universal-modder && UM_HOME=D:/tools/um-home python -m um win shot --title '^War' --scale 0.5 <png>`).
- Any UE4SS/game crash: stop, keep `UE4SS.log`, `Saved\Crashes` and the PID; do **not** restart by reflex. Record it in MODLOG as a
  failure, not as an "adjustment".
- At the end: close **only** the copy's PID (`D:\FoxholeLab\Foxhole`); Steam and the firewall stay as they are; remove the temporary `map.txt`.
- The `CFG` values the script compares were read from the candidate to integrate, **v4.1** (SHA `62245d23…598f`; v4 `025e3b80…aab0` has the same `CFG` values). If the published main is a different one, stop at S2.

## 1. Estimated duration

| Block | What it is | Min (estimated, not measured) |
|---|---|---|
| P | Preflight, backups, copying the probes | 15 |
| G | Stability gate: record B1 + loads B2 and A2 (each ~5 min of loading + 3 min of window + checks) | 25 |
| S | Publish v4.1 in HomeRegionW, read-only probes (A1–A3, io/os, state), smoke match and rehearsal B1 (creates 1 actor) | 45 |
| H0–H1 | Switch to CallumsCapeHex (`map.txt`) and restart; A3/state in the hex; deploy (Alt+L through the channel) | 10 |
| C | Manual match: workers, resource truck, loss, combat; economy (rifles/bandages/priority/scarcity) | 35 |
| I | Enemy chain and interdiction (L1–L12) + I15 (wave with workers, v4.1) in the same match | 35 |
| K | Forward bases: eligibility, construction, order, delivery, recruiting, loss, Assault | 45 |
| V | Persistence: save/continue with 2 game restarts, refusals, corrupted elogi | 50 |
| T | 10 min with 3 bases (stability + per-frame cost) | 15 |
| Z | Closing, restoration, report | 10 |
| **Sum** | | **~285 min (4 h 45)** |
| With 20% for surprises | | **~5 h 40** |
| R (optional) | Long regression with the bot: at least 4 matches (1 per cell B0–B3) | +70 to +90 |
| R complete | 3 matches per cell + 1 easy + 1 hard | +3 h 30 |

Clean game loads in the core: 2 (gate) + 1 (v4 in HomeRegionW) + 1 (hex) + 2 (persistence) = 6. Each costs ~5 min; that is what weighs most.

## 2. Files to bring to `D:/tools/foxhole-lab/` (copy, nothing is edited in the originals)

```
cd /d/GitHub/foxhole-rts/data/parallel
cp package_v4/probes/*.lua                                  D:/tools/foxhole-lab/
cp forward_bases/probes/A1_structure_columns.lua forward_bases/probes/A2_base_classes.lua forward_bases/probes/A3_world_bases.lua forward_bases/probes/A4_ground_at_points.lua D:/tools/foxhole-lab/
cp logistics_ai/t_logistics_ai.lua persistence/lab/t_persist_state.lua D:/tools/foxhole-lab/
# already there: t_crash_control_start.lua / _check.lua (A) and t_crash_B1_prepare.lua / _start.lua / _check.lua (B)
```
Legend of the new files (`package_v4/probes/`; plus `read_save.py` and `post_integration_battery.py` outside the game): `pv4_state` and `pv4_profile` (read-only), `pv4_bases_scene` (read-only, traces), `pv4_io_os`
(creates and deletes 2 temporary files), `pv4_B1_forwardbase` + `pv4_B1_clean` (creates 1 native actor), `pv4_cmd_*` (call mod functions; they change state,
edit the variables at the top before running). All had their **syntax** checked (Lua 5.4 and 5.5); `pv4_state`, `pv4_bases_scene`, `pv4_io_os` and several
`pv4_cmd_*` were run against the candidate in the offline harness (world mock), which proves there is no name/field error, not that the game answers the same.

## 3. P — Preflight (15 min)

| ID | Step | Measure / PASS | Closes |
|---|---|---|---|
| P1 | Steam open/logged in; no botloop; copy present; `steam_appid.txt`; no `War-Win64-Shipping.exe` of the copy running (or note the PID) | PASS: everything checked and noted | LABORATORIO "Check Steam… before launching" |
| P2 | **Backup outside the copy**: `War/Binaries/Win64/ue4ss/Mods/FoxholeRTS/save.txt*` (and `settings.txt`, `map.txt` if any) + SHA256 of each; listing of `%LOCALAPPDATA%\Foxhole\Saved\Crashes`; size of `UE4SS.log` | PASS: SHA256 noted (L12 of the persistence script restores them at the end) | PERSISTENCIA |
| P3 | Copy the probes (§2). Check `sha256sum mod/FoxholeRTS/Scripts/main.lua` and what `restart.sh` will publish | PASS: hash noted = the one of the step where it is used (33d6c7e5… in the gate, 62245d23… (v4.1) afterwards) | INTEGRACAO |
| P4 | Decide the gate × integration order (`HOW_TO_INTEGRATE.md` §2). This script assumes: G (source 33d6c7e5…) → integration → S onward | PASS: decision recorded | ESTABILIDADE |

## 4. G — Stability gate (25 min; source 33d6c7e5…, before writing v4.1)

Base: `stability/crash_control.md`. Same source, same map, camera and state; no waves, no logistics, 6 soldiers standing still; **no** input from the
user nor the agent during the window (not even the console); channel checkpoints at 60/120/180 s, equal in all loads; do not restart because of
"Not responding". Minimum window 180 s (the historical crash happened before 111 s).

| ID | Step / command | Measure | PASS | FAIL (what to do) | Closes |
|---|---|---|---|---|---|
| G1 | **Record the B1 already done**: `D:/tools/foxhole-lab/crash-control-B1.txt` (184.3 s, 6 selected, 168 copies, stratTick 11.66/11.90/12.37 ms) → MODLOG entry with PID/time (the file does not say) | confirm in the day's `UE4SS.log`: no `Registry`/fatal in the window | file and log consistent | no log for the day: record "no supporting log" | ESTABILIDADE |
| G2 | **B2** (reversed order, new load): `restart.sh` → wait for RTS → `run.sh t_crash_B1_prepare.lua` → wait 5 s → `run.sh t_crash_B1_start.lua` → at 60/120/180 s `run.sh t_crash_B1_check.lua` | PID alive; `SELECTED 6 CLONES 168` in all 3 checkpoints; `stratTick`; `UE4SS.log` without `Registry`/`Access violation` | ≥ 180 s without a crash, equal counts, stratTick ~12 ms (not worse than B1) | crash < 111 s: keep log+Crashes, **stop the batch** (MODLOG rule), coordinator's decision | ESTABILIDADE "Distinguish hypotheses…" |
| G3 | **A2** (new load, no selection): `restart.sh` → `run.sh t_crash_control_start.lua` → 60/120/180 s `run.sh t_crash_control_check.lua` | same; `SELECTED 0 CLONES 0`; stratTick ~0.5 ms | ≥ 180 s, 0 copies, ~0.5 ms | crash with 0 copies: the outline is not needed to reproduce; investigate common callbacks/anim (decision in `crash_control.md`) | ESTABILIDADE |
| G4 | Decision table (`crash_control.md`): only B fails → selection/copies associated (not the cause); A/B both survive 2× → no reproduction, widen duration/transitions in a later batch; A+B fail → the common bridge deserves symbols/trace | record the decision row in MODLOG | decision written | — | ESTABILIDADE |
| G5 (optional) | Widened matrix from `audit.md` (A: 10 min without selection; B: 1 selected/28 copies 10 min; D: 100 select/deselect; E: 20 death/recreation; J: 1/3/10/25 selected at high zoom, 60 s per step) | `profile()` per step; copies = 28×N; no leftovers | only if the coordinator asks: not a batch gate | — | ESTABILIDADE "long validation, GC, deselect/reselect, death and recreation" |

After G: **INTEGRACAO writes v4** (`HOW_TO_INTEGRATE.md` §3–§6) and the offline battery passes 27/27 before going on.

## 5. S — HomeRegionW (bench): read-only probes, smoke match and rehearsal B1 (45 min)

No `map.txt` (HomeRegionW). No botloop. Each probe: `sh D:/tools/foxhole-lab/run.sh <file> > output_<file>.txt`.

| ID | Step / command | Measure | PASS | FAIL (what to do) | Closes |
|---|---|---|---|---|---|
| S1 | `restart.sh` with v4 published; `sha256sum` of the published file | RTS wait ≤ 4 min; in `UE4SS.log` the line `v0.9 carregado (... Shift+J base avançada ...)`; absence of `Registry`/`ERRO` | RTS on and the line present | launch failure (`restart.sh` exits with code ≠ 0 in ~1 s = Steam closed): open/log into Steam, do not wait 240 s | LABORATORIO "Publish… Check loading…" |
| S2 | `run.sh pv4_state.lua` (no match) | `CFG` section: `COLETA.manualStart true`, `bmat0 40`, `DEPLOY.budget 1000`, `FWD cost 300 hp 1725 cap 15 max 3 confirm 4.0 pending 180.0 strict true ruin false teamId nil visual native`, `SPAWN.pointSpawn false startRifles 10`, `ECHAIN.free 5 trip 20.0`, `PERSIST.version 2 fwdVersion 1` | all equal | divergence: the published main is not v4; stop | INTEGRACAO |
| S3 | `run.sh pv4_profile.lua` (zeroes the window) and, 60 s later, again | `mod: X ms/quadro … stratTick …` without a match | baseline recorded | — | per-frame cost (§7 C9) |
| S4 | `run.sh A1_structure_columns.lua` | columns of `BPStructureDynamicData` beyond the 5 known ones; values of `ForwardBase1` (MaxHealth 1725? ResourceAmounts 300 bmat? StoredItemCapacity 15?) | no crash; values noted | crash: see §0; do not repeat the probe | BASES_AVANCADAS "Trace in the data" |
| S5 | `run.sh A2_base_classes.lua` | does `BPForwardBase1_C` (**inferred** path) load? parent, CDO, properties `TeamId/Health/CodeName`, spawn/stock/damage UFunctions; `DestroyedForwardBase1` | the class loads and `CodeName/Health/MaxHealth/TeamId` show up | the class does not load: the `CFG.FWD.asset` path changes; without the class, there are no bases (skip all of K) | BASES_AVANCADAS (decides `visual="native"` and R1) |
| S6 | `run.sh A3_world_bases.lua` (world already loaded) | base/spawn/hospital actors: where, team, health, components (class and name only); collision-only bounds → `CFG.FWD.half` (600 cm provisional); real `ItemHolder` × "15 slots" | table noted | — | BASES_AVANCADAS |
| S7 | `run.sh pv4_io_os.lua` (creates/deletes 2 temporary files next to the save) | line `rename A -> B com B existente (DESTINO EXISTE)`; `seek end`; `remove inexistente` | all lines OK; the rename's return is recorded (offline on Windows/lupa: `nil, "File exists"`) | `rename` returns true overwriting: the prior remove is harmless; `ERRO` in seek/write: **PERSISTENCIA fails** (the code depends on it) | PERSISTENCIA "Measurements requested" |
| S8 | `run.sh pv4_cmd_match.lua` (= Shift+F6) and `run.sh pv4_state.lua` | trucks 3 (`res` = `dead`, 2 `sup`), `bmat 40`, shirts 30, rifles 10, reserve 100, `COLETA ativa`; enemy chain `auditoria true`, front `m2 c10` | as described; panel (13 lines) | `Partida não iniciada: <motivo>` in the log: HomeRegionW has field, refinery, factory and the map's trucks (README); record the reason and go on to H0 | COLETA 1; ECONOMIA |
| S9 | ~15 s later (workers spawn from ~5 s on, one every ~3 s): `pv4_state.lua`; **capture** of the squad | 3 workers (`ESQUADRAO trabalhadores 3`), shirts 27; no T-pose (grip 0 without a weapon), no error in the log | clean spawn | T-pose/animation hook crash: `CFG.WEAPONS.worker.grip` and `anim.untrack`; **stop** | COLETA 2 |
| S10 | Get a point of yours: `run.sh pv4_cmd_capture.lua` (POINT "A"); wait for `pv4_state.lua` to show `PONTO … dono 1` | normal capture (10 s from neutral to owner per soldier) | point A is yours | took long: repeat `pv4_cmd_capture.lua` | — |
| S11 | **B1**: `run.sh pv4_B1_forwardbase.lua` (stage 1, **creates 1 actor**); +15 s the same file (stage 2); +60 s the same (stage 3); `run.sh pv4_B1_clean.lua`; read `UE4SS.log` from T0 to the end | `B1 SPAWN ms`, `B1 ATOR CodeName Health MaxHealth TeamId`, `B1 CONTRATO strict` (Health==MaxHealth==1725 and CodeName==ForwardBase1), position/yaw as requested, `ainda_ativo_apos_destroy false`; in the log: no `Registry`, no `Access violation`, no native respawn | spawns whole and vanishes without residue; 60 s clean | **strict fails**: record the real value (Health? CodeName?); decide `CFG.FWD.strict=false` or an adjustment; **class does not spawn/crash**: no base (skip K) and plan B (mesh) is a new task; `TeamId`: record 255 × 1 (today the mod does not write it) | BASES_AVANCADAS "Request… real spawn of the class in the hex" |

## 6. H0–H1 — CallumsCapeHex: switch map and deploy (10 min)

| ID | Step / command | Measure | PASS | FAIL | Closes |
|---|---|---|---|---|---|
| H0 | Write to `…/ue4ss/Mods/FoxholeRTS/map.txt` the line `/Game/Maps/Master/CallumsCapeHex` (batch 17 pattern); `restart.sh`; wait for RTS (large hex: slower) | the `MUNDO` line of `pv4_state.lua` shows CallumsCape; `sv.worldPath` | RTS on in the hex | — | PERSISTENCIA "same region" |
| H1a | `run.sh A3_world_bases.lua` again (in the hex) | native bases/hospitals and ruins; does `ForwardBase1` already exist in the hex? | noted | — | BASES_AVANCADAS |
| H1b | `run.sh pv4_cmd_deploy.lua` (= Alt+L) | `ANTES/DEPOIS` with refineries, factories, `BPTruckW_C`, wallet. **v4: cost 1000** (refinery 400 + factory 400 + 2 supply trucks 100; **without** the resource one) | `IMPLANTAÇÃO: -1000 bmat do cenário; saldo 0`; 2 TruckW (Team 1, HP 900, `built` 4); repeat: `Cadeia já implantada` and equal counts | refusal for spot/clearance: reason in the log; a forced failure reverts without a debit | PERSISTENCIA L0 (v4 version); LABORATORIO |
| H1c | `run.sh pv4_state.lua` | `ATORES ATIVOS` = 1 refinery, 1 factory, 2 TruckW; no `BPTruckC_C` | checked | — | — |

## 7. C — Manual match, collection and economy (35 min)

Items 1–9 of `manual_collection/LAB_SCRIPT.md` + the ECONOMIA matrix. `run.sh pv4_cmd_match.lua` starts; `pv4_state.lua` every ~30 s; **`newGame` already turns automatic waves on** (like Shift+F6); to measure collection without pressure (C1–C9) run `pv4_cmd_mode.lua` with `MODO="sem_ondas"` **right after** the match (the probe only turns them off if they are on).

| ID | Step / command | Measure | PASS | FAIL | Closes |
|---|---|---|---|---|---|
| C1 | `pv4_cmd_match.lua` + `pv4_state.lua` (t=0) | cost 1000, 2 supply trucks, no live resource truck, `bmat 40`, reserve 100, panel with `Fábrica | guarda 100 bmat para reconstruir caminhão (bmat 40)`, shirts 30 | as described | — | COLETA 1 |
| C2 | t≈15 s (the 1st worker at ~5 s, the others every ~3 s): `pv4_state.lua` + capture | 3 soldiers **without a weapon** near the base; shirts 30→27; no crash (`UE4SS.log`, `Saved\Crashes`) | 3 workers, no T-pose | — | COLETA 2 |
| C3 | Walking: `pv4_state.lua` every 30 s (sections `COLETA`, `LUGARES`, `DISTANCIAS`) | time of the 1st delivery to the refinery and of the 1st truck; real field–refinery distance; is any worker stuck? (`leg` 180 s) | they arrive, collect, deliver; collection ledger `true`; time comparable to the harness's 165 s (80 m) / 359 s (470 m) | stuck/lost: `CFG.COLETA.fieldR/refR/stand/leg`; note where | COLETA 3 |
| C4 | Player order (during C3, ~60 s): `pv4_cmd_worker_order.lua`; `pv4_state.lua` right after and ~70 s later | the worker leaves collection (cargo in hand discarded, log); ~60 s without an order (`CFG.COLETA.quiet`) they come back on their own | leaves and comes back | does not come back: `colMaintain`/`quiet` | COLETA 5 |
| C5 | Truck: when bmat reaches 100 the factory builds the resource one | it **appears in the field, standing on the ground**, not stuck; message `caminhão de recurso pronto: coleta manual encerrada`; the panel loses the collection line (`COLETA_PAINEL nil`); `ATORES ATIVOS BPTruckW_C` goes up | valid spawn (`logi.spawnTruck`), not on a roof | spawn refused: continues as an abstract truck (log); note it | COLETA 4 |
| C6 | Truck loss: `pv4_cmd_kill_truck.lua` with `KIND="res"`, `ZERAR=true` | with no bmat/salvage/truck collection **reactivates** (`COLETA ativa true`, workers come back, `COLETA MANUAL:` in the log); the factory rebuilds the truck when it gathers 100 bmat | reactivates and rebuilds | freezes forever = v2 regression | COLETA 6; user's decision |
| C7 | Combat: `pv4_cmd_enemy.lua` (`ONDE="campo"`, `N=1`); then `pv4_cmd_mode.lua` `MODO="limpar"` | workers pause; if one dies, the base replaces them **for 1 shirt** (`pv4_state`: shirts −1) | pause and replacement | — | COLETA 7 |
| C8 | Save/continue with workers in the field: `pv4_cmd_mode.lua` `MODO="ondas"` (turns them back on; `sv.save` requires `combat.auto`); `pv4_cmd_save.lua`; `pv4_cmd_load.lua`; `pv4_state.lua` before and after | cargo in hand discarded (log `coleta manual: … descartada`), 3 workers, collection restarts; save/load ms | `sv.save` true; `sv.load` true; same squad | — | COLETA 8; PERSISTENCIA |
| C9 | Per-frame cost: `pv4_profile.lua` (zero) → 2 min **with** collection active → `pv4_profile.lua`; then repeat **without** collection (after C5) | `mod X ms/quadro`, `colStep` | difference noted (no fixed limit; collection is O(collectors)) | — | COLETA 9; INTERFACE (panel cost) |
| C10 | Economy (after C5): `pv4_cmd_prio.lua` with `VEZES=3` (rifles) and let the factory produce; `pv4_cmd_send.lua` `ONDE="base"`; see `DEPOSITO base … fuzis`; repeat with `VEZES=1` in a row up to bandages | recipe → production → transport → depot for the 4 products (rifle crate = 20 units, bandages = 50, shirts = 10); `Pronto | …` and `extraHud` consistent; bmat ledger | the 4 products reach the depot without artificial stock beyond `startRifles 10` | a product vanishes: `logi.moveCargo`/`returnCargo` | ECONOMIA "complete chain live" |
| C11 | Recruit riflemen until the rifles run out (`pv4_cmd_recruit.lua` `ROLE="rifle"`, `ONDE="base"`, `VEZES=11`) | the first 10 spend 1 shirt + 1 rifle each; the 11th is refused (`sem fuzis em base; …`); manpower does **not** drop; after production/delivery it can again | refusal and recovery | recruits without a rifle = regression | ECONOMIA "supply-dependent recruiting" |
| C12 | Scarcity/cut/recovery: `pv4_cmd_kill_truck.lua` `KIND="sup"` with low bmat; watch the reserve (`Fábrica | guarda 100 bmat…`) and the truck coming back (< 60 s if there is bmat); kill it again | the factory does not spend the 100 reserve on crates (bmat×truck hypothesis: 0/31 came back before the reserve) | the truck comes back; the ledger closes | the truck never comes back = the reserve does not hold live | IA_LOGISTICA finishing 3; ECONOMIA "scarcity, cut, recovery" |
| C13 | Panel: **capture** with collection active, then with production; `pv4_state.lua` section `PAINEL` (lines/width) | 12–13 lines, width ≤ ~222 (offline); overlap, height, F5 help and native alerts at several zooms/resolutions; pause; logistics off | readable and without cutting stocks/vehicles; nothing silently hidden | cut: layout before approving (INTERFACE warns that clipping is a visual gate) | INTERFACE (lab) |

## 8. I — Enemy chain and interdiction (35 min; L1–L12 of `logistics_ai/LAB_SCRIPT.md`)

Same match as C (or a new one with `pv4_cmd_match.lua`). Waves: the new match already turns them on; `pv4_cmd_mode.lua` `MODO="ondas"` only turns them back on if they are off. Probe: `run.sh t_logistics_ai.lua` (or `pv4_state.lua`, section
`CADEIA_INIMIGA`/`COMBOIO`). v2 calibration: `free 5`, `trip 20`, `front0 m2 c10`, `want 4/20`, free floor 5/wave.

| ID | Step | Measure | PASS | FAIL | Closes |
|---|---|---|---|---|---|
| I1 | (L1) right when the match starts | `auditoria=true (razão fechado)`, `ativo=true`, front `m2 c10`, rear bmat 240, free fleet 2; HUD `INIMIGO: frente equipa 10`; no Lua error | as described | — | IA_LOGISTICA |
| I2 | (L2) 1st convoy (20 s after the waves start + cargo) | event `comboio 1 saiu: N cx`; actor `BPTruckC` exists, `ator_ativo=true`; the rear dropped exactly the cargo; alert `COMBOIO INIMIGO … (carga)` | valid real actor | spawn refused/being destroyed: log | IA_LOGISTICA "real truck live" |
| I3 | (L3) let it arrive | a single `entregou na frente`; the front rises by `units` (shirts = 10 per crate); run the probe 3× in a row: no 2nd delivery; the truck vanishes and the free fleet goes back to 2; `auditoria=true` | single delivery | double delivery = bug | IA_LOGISTICA |
| I4 | (L4) ambush: `pv4_cmd_ambush.lua` with a loaded convoy | `comboio N perdido (destruído): -X munição, -Y camisas` **once**; alert `COMBOIO INIMIGO DESTRUÍDO (+25)`; front unchanged; `reconstruindo 1`; `auditoria=true` | one loss, the ledger closes | duplicated loss | IA_LOGISTICA "destruction/interdiction reduces supply" |
| I5 | (L5) our mortar on a loaded convoy: `pv4_cmd_mortar.lua` (= Ctrl+5, 40 manpower, leading aim); then, **with the convoy already destroyed**, `REPETIR_NO_LUGAR = true` and run again | the same as I4 (one loss, alert `+25`); the 2nd mortar on a destroyed truck does **not** record a 2nd loss (`combat.convoysCut` does not go up) | only one loss | 2nd loss = bug | IA_LOGISTICA |
| I6 | (L6) wait ≥ 30 s after the loss | `caminhão de comboio reconstruído (-100 bmat)` only when bmat ≥ 100; the **enemy** factory stays idle if there is no free truck and a rebuild is due | as described | — | IA_LOGISTICA "recovery" |
| I7 | (L7) waves with the front full and then empty: compare `#enemies()` right after each spawn with the wave record (`eReport`) | `enviados` = soldiers that spawned; with the front empty `faltou suprimento ao inimigo: a onda vem com N a menos (…; K por comboios destruídos)`; floor of 3… **v2: free floor 5** | no extra soldier | — | IA_LOGISTICA "scarcity" |
| I8 | (L8) enemy point with reinforcement (`ai.tick`) and a dry front, then supplied | without material: no `REFORÇO INIMIGO`; with material: 2–3 and the front debited by the number that **spawned** | as described | — | IA_LOGISTICA |
| I9 | (L9) `pv4_cmd_save.lua` with a convoy on the road, `pv4_cmd_load.lua` (same session; the complete restart is V) | event `cadeia inimiga restaurada do save (reenviar …)`; pending = the cargo that was on the road; `auditoria=true`; the next convoy carries the pending amount; continuing 2× does not duplicate (compare initial+produced) | restores without duplicating | — | IA_LOGISTICA "continuity"; PERSISTENCIA |
| I10 | (L10) in a separate and recorded probe: `logi.foes[1].pawn:K2_DestroyActor()` | on the next frame `perdido (ator do caminhão inválido)`, no delivery, `auditoria=true`, no crash/native error | handled | native crash: **stop** | IA_LOGISTICA |
| I11 | (L11) Assault: `pv4_cmd_mode.lua` `MODO="assalto"` | no convoy; front intact; no consumption (`ativo=false`); recruiting uses manpower (legacy branch) | as described | — | IA_LOGISTICA; BASES (K9) |
| I12 | (L12) `pv4_cmd_match.lua` several times and `MODO="limpar"` in the middle | no `BPTruckC_C` left (`ATORES ATIVOS`); new `logi.en`; no error | no leftovers | — | IA_LOGISTICA |
| I13 | Finishing pending item 4: edit `save.txt` (corrupt `elogi`; swap `["v"]=2` for something else) and `pv4_cmd_load.lua` | warning `CADEIA INIMIGA REINICIADA (…): estoque de cenário` for 10 s; player intact; the next autosave writes again | only the section drops | refuses the whole save = v2 regression | PERSISTENCIA; AI finishing 4 |
| I15 | **v4.1**: wave with workers. With collection active (3 live workers), note `#squad`, combat soldiers (`rts.combatCount()`) and `#enemies()` right after the 1st wave spawns; repeat with `CFG.COLETA.workers = 0` before a new match (or with no live workers) and the same number of combat soldiers | The wave size depends only on combat soldiers (harness: 6 combat give 6 with or without 3 workers; the warning "próxima onda em … (esquadrão N …)" shows the combat ones; `pv4_state.lua`/channel: the wave's exit point follows the combat squad, not the salvage field, since `squadCenter()` only counts live combatants) | larger wave with workers = regression | — | orchestrator's decision (v4.1) |
| I14 | Finishing pending item 1: real wave cadence (bot and human) and `logi.eReport()` at the end | `byCut`, losses, pressure per wave | numbers noted for `CALIBRATION_TABLE` | — | AI finishing 1–2 |

## 9. K — Forward bases (45 min; still in CallumsCapeHex; **only if S5/S11 let the class spawn**)

Pre: active logistics match with ≥ 1 point of yours far from the base (≥ 3000 cm) or near an enemy point (≤ 4000 cm); enough bmat or `CREDITAR=true` (record it).

| ID | Step / command | Measure | PASS | FAIL | Closes |
|---|---|---|---|---|---|
| K1 | `run.sh A4_ground_at_points.lua`; `run.sh pv4_bases_scene.lua` | per point: `fwdCheck`, `fwdPlace` (center, exits ≥ 3), `fwdPlace_ms`; `RESUMO elegiveis` | **≥ 1 eligible point per match** in the hex (L2: `minFromBase 3000` / `maxToEnemyPoint 4000`); `fwdPlace` ms noted | none eligible: calibrate `half/clear/maxSlope/minExits/exitR` (A4 measures) | BASES (L2; footprint) |
| K2 | Refusals (`pv4_cmd_base_shiftj.lua`, `TOQUES=1`/`2`): cursor on a neutral/enemy point/near the base/with an enemy in the ring (`pv4_cmd_enemy.lua` `ONDE=` name) | messages `não é seu`, `perto demais da base`, `há inimigos no ponto X`; **nothing created, nothing debited** | clear refusals | creates something = bug | BASES |
| K3 | Build: `PONTO=nil`, `TOQUES=2` (with real bmat; otherwise `CREDITAR=true`, note it) | `toque 1 false`, `toque 2 true`; the base appears at the point; `pv4_state.lua`: `BASE … ator_vivo true classe BPForwardBase1_C hp_ator 1725/1725 saidas ≥3 razao true`; `bmat −300` **only after** the validated actor; the panel gains `base A | camisas 0 | fuzis 0 | slots 0/15 | reforça: NÃO (sem camisas)` | whole, 1 actor per base | `strict` refuses (log `vida inicial/CodeName/rotação divergiu`): see S11 | BASES "Request… real spawn" |
| K4 | Pending order: without bmat, `TOQUES=2`; panel; wait or `TOQUES=2` again within 4 s to cancel | `pedido de base avançada em X registrado`; panel `Fábrica | guarda 300 bmat para base avançada em X (bmat N)` (after the truck's reserve: the truck has priority); builds on its own when it has enough; cancels in 180 s, if the point stops being yours, with an enemy in the ring, or with the 2nd Shift+J | as described; **no ammo starvation** (the factory does not stop ammo indefinitely) | prolonged ammo starvation: adjust `pending` | BASES |
| K5 | Delivery by truck: `pv4_cmd_send.lua` `ONDE="A"` (base); wait | only what fits in the 15 slots (partial crate = 1 slot); shirts and rifles go **only** to the main base or an active forward base; a point without a base receives only ammo and bandages; the per-base ledger closes | respects slots | overflows 15 slots = bug | BASES "delivery of shirts by truck" |
| K6 | Recruit: `pv4_cmd_recruit.lua` `ROLE="rifle"`, `ONDE="A"` (inside the base) and then `ONDE="longe"`; `ROLE="mg"` | spawns **at the base's exit** (`saida de base A a ~0 cm`, not on a roof/wall), spends 1 shirt + 1 rifle (mg: only the shirt), manpower intact; a base without stock with the cursor inside it → refusal with a reason, **without** falling back to another; outside → the base closest to the cursor/squad with stock | as described | spawns on a roof/wall: `exits`/`parkingGround` | BASES |
| K7 | Point without a base (still yours): `pv4_cmd_recruit.lua` `ONDE=` point without a base | does **not** reinforce (spawns at the main base); with `CFG.SPAWN.pointSpawn=true` it would go back to the old behavior | confirmed | — | BASES |
| K8 | Loss: `pv4_cmd_base_loss.lua` `MODO="morteiro"` (8 enemy mortars), then `"captura"` on another base | alert `BASE AVANÇADA X destruída/capturada: perdeu N camisas e M fuzis` **once**; actor destroyed, **without** residue (active `BPForwardBase1_C` = live bases); stock zeroed; recapturing the point does not bring the base back; the ledger closes; the panel loses the line; a neutralized point = `INATIVA (ponto neutro)` with stock kept | one loss, no residual actor | residual actor: `fwdLose` | BASES |
| K9 | Limits and Assault: build up to 3, try a 4th (`limite de bases avançadas (3)`); `pv4_cmd_mode.lua` `MODO="assalto"`: Shift+J refuses (`só numa partida com logística (fora do Assalto)`) and `recruit` uses manpower | as described | — | — | BASES |
| K10 | Pause: the game paused (`rts.togglePause()` through the channel) during the 4 s of the 2nd press | `GetRealTimeSeconds` keeps running (item 12 of the stage 2 report) | confirm that is what is wanted | user's decision | BASES R12 |
| K11 | Defeat by lack of troops (logistics branch): no combat soldiers **and** no shirt at a base/factory/truck | only then `DERROTA` | does not lose with shirts in the factory/truck | — | BASES |

## 10. V — Persistence (50 min; hex; **2 game restarts**) and T — 10 min with 3 bases (15 min)

Script of `persistence/LAB_SCRIPT.md` **with v4's numbers**: deployment **1000** (2 structures + **2** TruckW), `spent 1000`, **4** `built` records,
**4** spawns on restore (refinery 2700, factory 2000, 2 TruckW 900, Team 1) — the original script speaks of 1100/3 TruckW/5 spawns (stack without collection). State
probe: `pv4_state.lua` (and `t_persist_state.lua`, which reads the same persistence ledger) **before** and **after**; compare with `diff`.

| ID | Step | Measure | PASS | FAIL | Closes |
|---|---|---|---|---|---|
| V0 | Load 1: `pv4_cmd_deploy.lua`, `pv4_cmd_match.lua` (turns waves on; `MODO="ondas"` only makes sure); leave ≥ 90 s with logistics and (ideally) 1 forward base and 1 convoy; `pv4_state.lua` | 2 installations + 2 TruckW; wallet `0/1000` with 4 `built` | comparison baseline | — | PERSISTENCIA L0 |
| V1 | `pv4_cmd_save.lua` with a truck in `toDep` and a job running | `true`; `save.txt` starts with `return {`, ASCII, no `function`/`load`; `.bak` only from the 2nd save; SHA256, size and **ms** of `sv.save` | atomic | high time (> 1 frame): note it | PERSISTENCIA L1 |
| V2 | Read the file outside the game: `PYTHONPATH=D:/tools/pylibs python data/parallel/package_v4/read_save.py <copy of save.txt>` (uses the main's `sv.decode`/`sv.parseSave`; writes nothing) | decodes; `world` = the hex's path; **no actor address**; `fwd` section with point index/XYZ/yaw/hp/stock per depot | accepted | — | PERSISTENCIA L2 |
| V3 | **Restart the game** (`restart.sh`), same hex, **without** Alt+L | ruins visible again; no active refinery/factory/TruckW (the infra does not survive by itself); no forward base | proof that the infra does not persist | — | PERSISTENCIA L3 |
| V4 | `pv4_cmd_load.lua` (= Ctrl+F6) | `true`; **4 spawns** (refinery 2700, factory 2000, 2 TruckW 900, Team 1) + the forward base(s) rebuilt in the same place; ruins hidden/without collision; wallet `0/1000` (no new debit); stocks, job, cargo in transit, points/owners, soldiers, fortifications = V1 (trucks go back to the validated parking); ms | `pv4_state` after = before | refusal: reason in the log; **the match and the file stay** | PERSISTENCIA L4; BASES 11h |
| V5 | `pv4_cmd_load.lua` again | no new spawn, same actor count, stocks do not double, **one** base per point | idempotent | duplicated = bug | PERSISTENCIA L5 |
| V6 | 60 s later | the truck saved in `toDep` replans and delivers **once**; the factory finishes the job without debiting bmat again | single delivery | — | PERSISTENCIA L6 |
| V7 | Autosave (30 s) and `pv4_cmd_save.lua`; list the files | `.bak` = previous save, `.tmp` absent | rotation ok | — | PERSISTENCIA L7 |
| V8 | **Restart the game**; **before** continuing, `pv4_cmd_deploy.lua` and then `pv4_cmd_load.lua` | Alt+L charges the new wallet; `sv.load` recognizes the identical deployment, creates nothing, the wallet goes back to the save's (`0/1000`) | no double charge | — | PERSISTENCIA L8 |
| V9 | Refusals with a live session (match running): (a) save from another region (copy the HomeRegionW one), (b) `save.txt` truncated in half without `.bak`, (c) `["v"]=3`, (d) tampered `fwd` (point x outside the radius / `hp` > 1725 / wrong code), (e) moved ruin: skip | `false`; `Continuar recusado (partida atual e save preservados)`; the session's soldiers/stocks equal; files with the same SHA256 | nothing changes | something changes = serious bug | PERSISTENCIA L9 |
| V10 | A post-preflight failure is hard to provoke without a hotpatch: **do not force it**. Only record it if `INCOMPLETA … autosave suspenso` appears spontaneously | log | — | — | PERSISTENCIA L10 |
| V11 | Victory/defeat (or `sv.clear()` through the channel at the end) | `save.txt`, `.tmp`, `.bak`, `.corrupt` removed | clean | — | PERSISTENCIA L11 |
| V12 | End: restore the save files from P2 | SHA256 equal to the initial one | restored | — | PERSISTENCIA L12 |
| V13 | Measurements: ms of `sv.save`/`sv.load` (game thread), return of `os.rename/remove/io.open("wb")/f:seek` (already in S7), `World:GetFullName()` in the hex and after the restart, identical ruin/rotation between loads (≤ 2 m, ≤ 1°) | numbers in the report | — | — | PERSISTENCIA |
| T1 | **10 min with 3 bases**: build 3 bases (K3, `CREDITAR` recorded), `pv4_profile.lua` at 0/5/10 min, waves on, `pv4_cmd_send.lua` alternating bases; `UE4SS.log` | PID alive 10 min; `mod ms/quadro` vs the baseline (S3/C9); panel with main + 3 bases + order (up to +4 lines); `BPForwardBase1_C` actors = 3; no `Registry`/`Access violation` | stable, cost noted | crash: **stop**, it is a stability finding, not an "adjustment" | BASES (10 min with 3 bases); ESTABILIDADE |

## 11. R — Long regression with the bot (optional; +70 to +90 min at least)

`logistics_ai/LAB_SCRIPT.md`, matrix B0–B3. **Before using the bot on v4 (R0)**: `D:/tools/foxhole-lab/t_bot.lua` (now `tools/lab/t_bot.lua`) is outdated — it recruits with `economy.manpower >= 45`
(under logistics manpower no longer limits), sends the **whole** squad (including the workers) back to point A with `m.target`, does not build bases nor use `L`, and
`t_bot0.lua` uses `newGame()` (now with 3 workers and no resource truck). Minimal adaptation (by LABORATORIO): exclude `m.role=="worker"` from the "back to A" loop
and accept that `recruit` may refuse for lack of a rifle. Without it, B0–B3 measure the bot, not v4. With the bot on: do **not** use the channel (wait with `until grep -q "auto<TAB>false" botrun.log`).

| Cell | Build | Interdiction | Record |
|---|---|---|---|
| B0 | main **without** IA_LOGISTICA (only stability + economy): keep the 33d6c7e5… source (`pre_integration_base/`) and publish it only for this cell | the bot's | victory/defeat, final wave, kills/losses, duration, convoys |
| B1 | v4 | the bot's | the same + `logi.eReport()` at the end + `auditoria` |
| B2 | v4 | forced: keep the squad on the convoy route | the same; compare waves 4–10 with B1 |
| B3 | v4 with `CFG.ECHAIN.free = 5` (already the v2 default; to vary: 3 or 7 through the channel **before** turning the bot on) | like B2 | calibrate the floor |

Minimum: 3 matches per cell at normal difficulty (+1 easy, +1 hard). Technical approval: `auditoria=true` at the end of **every** match; no Lua error/crash in ≥ 30 min; active `BPTruckC` ≤ 2.
Traceable effect: in B2, losses > 0, waves with `byCut` > 0, waves 4–10 smaller than B1; when the interdiction stops, some wave goes back to `faltaram 0`.
Balance is the user's decision (B0 history: batch 12 victory 111/24; batch 13 defeat at wave 10, 83/38). Frame sampler: `LoopInGameThreadWithDelay(100)` writing to `_G`, not through the channel.

## 12. Z — Closing (10 min)

1. `pv4_cmd_mode.lua` `limpar` and `sv.clear()` if the test save is no longer needed; **restore** `save.txt*` from P2 (equal SHA256).
2. Remove the temporary `map.txt` (default HomeRegionW).
3. Gather the outputs (`output_*.txt`), captures, hashes and PIDs in a folder outside the repository; fill in `MODLOG_DRAFT.md` (`[fill in at the lab]`).
4. **Close only the copy's PID** (`D:\FoxholeLab\Foxhole`); do not close Steam. Do not leave the game open "ready to test".

## 13. Traceability: where each item comes from (nothing was discarded)

| Origin | Items | Where it is here |
|---|---|---|
| `logistics_ai/LAB_SCRIPT.md` | L1–L12 | I1–I12 (L5 through the channel with `pv4_cmd_mortar`; the real Ctrl+5 key, in MANUAL_TEST; L9 also in V) |
| same | B0–B3, technical/effect/balance approval | §11 R (+ the bot's R0) |
| `logistics_ai/finishing/REPORT.md` §6 | 1 cadence/truck cycle; 2 `eReport`; 3 kill a truck under consumption + warning `fábrica guarda…`; 4 corrupted `elogi`; 5 `io/os`, real BPTruckC, route, performance | I14; I14/R; C12; I13; S7/I2 |
| `manual_collection/LAB_SCRIPT.md` | 1–9 | C1–C9 |
| `manual_collection/REPORT.md` §6 | real A*, animation without a weapon, `spawnTruck`, per-frame cost, human flow, vehicles/terrain | C3, S9, C5, C9, C4/MANUAL_TEST, C7 |
| `persistence/LAB_SCRIPT.md` | L0–L12 + measurements + "not validated" (routes, balance, crash between renames, UI) | V0–V12, V13; the "not validated" stay out (§14) |
| `forward_bases/stage2/REPORT.md` §6 | A1/A2, A3, A4, B1, L2, L4–L10, calibration, Shift+J does not fire J | S4/S5, S6/H1a, K1, S11, K1, K2–K11/V4/T1, DECISIONS, MANUAL_TEST |
| `forward_bases` stage 1 (`probes/A1–A4`, `SPEC`) | read-only probes, R1 (native respawn), R10 (`ItemHolder`) | S4–S6, S11 |
| `interface/REPORT.md` | panel in an active match/pause/logistics off/new map/lost depot/dead truck; UMG probes for the selection box | C13 + a capture in each state; the **selection box** is not part of the batch (§14) |
| `economy/REPORT.md` | complete chain without fictitious stock; scarcity/cut/recovery; recruited rifleman/treated bandage; save | C10–C12, C8/V; treated bandage → MANUAL_TEST |
| `stability/crash_control.md`, `audit.md` | A1/B1/B2/A2; matrix A–J | G1–G4, G5 |
| `roads/*` | road network, paths | **out** (§14) |
| `COLETA`/`ECONOMIA`/`PERSIST` "measurements" | save/load `ms`, `rename`, `GetFullName` | S7, V13 |

## 14. Outside this batch (does not count as missing)

- **ESTRADAS**: the stack does not contain the driver; trucks keep going straight and without collision. Its own gates (schema of `Connections/Points`, cardinality, geometry,
  live paths, water/bridges) in `roads/DELIVERY.md`, `SCHEMA_EVIDENCE.md`, `ENVELOPE_GATE.md`. Before integrating the adapter, fix the `factory.ammo/shirts` credit
  to `logi.fac` through `logi.moveCargo` (`HOW_TO_INTEGRATE.md` §8).
- Selection box visible while dragging (INTERFACE): UMG/projection/DPI probes not run yet; not in the stack.
- The forward base's visual plan B (mod mesh) and native ruin (`CFG.FWD.ruin`): only after S11.
- All items with **real input** (keys, mouse, readability, game balance): `MANUAL_TEST_DRAFT.md` and `OPEN_DECISIONS.md`.
- A crash between the save's two `rename`s (offline only) and road routes.
