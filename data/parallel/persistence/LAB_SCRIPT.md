# PERSISTENCIA (persistence) — request to LABORATORIO (prepared, NOT run)

Responsible for running it: the LABORATORIO agent (Codex coordinator). CLAUDE_PERSISTENCIA did not open the game,
did not use the channel nor touch `D:\FoxholeLab` or real saves. Everything below is a script.

## Preconditions
- Steam open and logged in; no botloop; lab firewall intact (rules in `AGENTS.md`).
- Candidate integrated by the coordinator (order in `REPORT.md`: ECONOMIA → [IA_LOGISTICA] → PERSISTENCIA),
  syntax + `check_globals.py` + `test_orders.py` + `data/parallel/persistence/test_*.py` PASS.
- Region: the same as batch 17 (CallumsCapeHex: active field, refinery/factory ruins, no native trucks).
- **First of all, copy out** the existing files `War/Binaries/Win64/ue4ss/Mods/FoxholeRTS/save.txt*`
  of the lab copy (they belong to the lab, not to the user) and record SHA256. `restart.sh` only copies
  `main.lua`; the save survives the restart (checked by reading the script, not running it).
- Read-only probe: copy `data/parallel/persistence/lab/t_persist_state.lua` to `D:/tools/foxhole-lab/`.
  Calls that change state go through the channel (`sv.save()`, `sv.load()`, `logi.deploy()`), never by keyboard.

## Matrix

| # | Step | Expected | Evidence |
|---|---|---|---|
| L0 | Load 1: `logi.deploy()` (Alt+L through the channel), new match, let waves and logistics run ≥ 90 s | 2 installations + 3 TruckW; wallet 0/1100 with 5 `built` records | probe before; screenshot |
| L1 | With a loaded truck in `toDep` and a job running: `sv.save()` | `true`; `save.txt` starts with `return {`, ASCII, no `function`/`load`; `.bak` only from the 2nd save | probe; SHA256 of the files; size; ms of `sv.save` (`os.clock` sampler) |
| L2 | Read the file outside the game: `python -c` with `sv.decode` via lupa (or the suite) | decodes and `sv.validate` accepts; `world` = CallumsCape's path; no address/actor | command output |
| L3 | **Restart the game** (`restart.sh`), same region, no Alt+L | ruins visible again, no active refinery/factory/TruckW (proof that the infra does not survive by itself) | probe (actors) |
| L4 | `sv.load()` | `true`; 5 spawns (refinery 2700, factory 2000, 3 TruckW 900, Team 1); ruins hidden/without collision; wallet 0/1100 (no new debit); stocks, job, cargo in transit, points/owners, soldiers, fortifications equal to L1 | probe after = probe L1 (except truck positions, which return to the validated parking) |
| L5 | `sv.load()` again, same load | no new spawn, same actor count, stocks do not double | probe |
| L6 | Let it run 60 s: the truck saved in `toDep` replans and delivers once; the factory finishes the job without debiting bmat again | single delivery; bmat only drops on a new job | delivery log; probe |
| L7 | Autosave (30 s) and `sv.save()`; check `.bak` = previous save | rotation ok; `.tmp` absent | listing and SHA256 |
| L8 | Restart; **before** continuing, `logi.deploy()` (Alt+L) and then `sv.load()` | Alt+L charges the new wallet; `sv.load` recognizes an identical deployment, creates nothing, the wallet goes back to the save's (0/1100) | probe |
| L9 | Refusals with a live session (new match running): (a) save from another region (copy the HomeRegionW save), (b) `save.txt` truncated in half without `.bak`, (c) `["v"]=3`, (d) moved ruin is not possible live — skip | `false`, message "Continuar recusado (partida atual e save preservados)", live session's soldiers/stocks equal, files with the same SHA256 | probe before/after; SHA256 |
| L10 | A post-preflight failure live is hard to provoke without a hotpatch: do **not** force it. Only record it if "INCOMPLETA … autosave suspenso" appears spontaneously | — | log |
| L11 | Victory/defeat (or `sv.clear()` through the channel at the end) | `save.txt`, `.tmp`, `.bak`, `.corrupt` removed | listing |
| L12 | End: restore the save files copied at the start; close only the copy's PID | — | SHA256 equal to the initial one |

## Measurements requested
- Time of `sv.save()` and `sv.load()` on the game thread (offline: ~11 ms for 120 units in lupa; live is a gate).
- `os.rename`/`os.remove`/`io.open("wb")`/`f:seek` in UE4SS's Lua on Windows: the code assumes `os.rename`
  does **not** overwrite (MSVCRT) and removes the destination first; record the real return.
- `World:GetFullName()` in the hex (format `World /Game/Maps/Master/<Hex>.<Hex>`) and after a restart (equal).
- Identical ruin/rotation between loads (restoring requires a ruin within ≤ 2 m and yaw ≤ 1° of the saved one).

## Not validated by this script
Road routes (the ESTRADAS driver is not integrated yet; trucks still go straight), balance, the enemy
chain live (IA_LOGISTICA), a process crash exactly between the two renames (offline only), UI/real keyboard.
