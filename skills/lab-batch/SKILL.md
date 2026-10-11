---
name: lab-batch
description: Validate a batch of Foxhole RTS changes live in the isolated lab copy of the game. One publish, scenarios with pass criteria run in sequence in the same game session, cleanup between them, then close the game. Covers the safety checks, restart.sh, the command channel, the regression bot and crash collection. Use only when an offline-tested batch is ready.
---

# Lab batch

Restarting the game costs minutes (the first load sits ~3 min on a black "Not responding" screen). The
maintainer asked, more than once, for **one** lab session per batch, not one per finding.

## Before opening the game
- Offline tests all pass (`offline-tests`).
- Write the scenarios down first, in the batch section of `MODLOG.md` or in `NATIVE_BATCH.md`: what you run,
  what you read, and the **pass criterion** for each. Example: "truck HP 900 → < 900 after grenade; cleanup
  leaves 0 test actors".
- Safety: `powershell -File tools/lab.ps1 check` (UE4SS absent from the Steam install, lab copy present, Steam
  open). Back up `%LOCALAPPDATA%\Foxhole` before a modded launch. The lab copy stays blocked from the network.
- Paths: `tools/lab/env.sh` (override in `tools/lab/env.local.sh`, which git ignores).

## Run
```bash
sh tools/lab/restart.sh              # syntax + globals check, copy main.lua, kill lab PID, launch, wait for RTS mode
sh tools/lab/run.sh probe.lua        # one command-channel script; only out(...) comes back
```
- Probes are small Lua files using the channel `env` (`CFG`, `S`, `logi`, `rts`, `combat`, `squad()`,
  `enemies()`, `out(...)`). Keep reusable probes in `tools/` (`probe_*.lua`); throwaway ones stay outside
  the repo.
- Run the scenarios **in sequence in the same session**, with cleanup between them (F11 equivalent or the
  scenario's own cleanup), and record each result as it comes, even partial.
- Never inject keyboard or mouse into the game window. Real-input checks go to the human (`MANUAL_TEST.md`).
- Never use the channel while the regression bot runs (answers get mixed).

## Regression bot
```bash
sh tools/lab/botloop.sh &            # plays waves until the match ends or 25 min; log botrun.log
```
Wait with `until grep -q "auto<TAB>false" botrun.log` (grep -P does not work in Git Bash). Stopping the agent
task does not kill `sh.exe`; find it with `Get-CimInstance Win32_Process` filtered by `botloop.sh`.

## If it crashes
- Collect: `UE4SS.log`, `%LOCALAPPDATA%\Foxhole\Saved\Crashes\<newest>`, the last channel output, time since
  start, what was running. Save the summary as `data/trace_crash_<topic>_<date>.txt`.
- Record the cause hypothesis in `MODLOG.md` **before** restarting. A crash is the only reason to restart mid-batch.
- New ideas found during validation go to the next batch. Do not start another run right away.

## After
- Close the lab copy by exact PID (never by process name, which could hit the Steam install). Do not close Steam.
- Then `wrap-up`. Mark `[x]` in `PROGRESS.md` only for items whose live criterion passed.
