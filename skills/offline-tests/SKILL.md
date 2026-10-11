---
name: offline-tests
description: Change Foxhole RTS code safely without the game. Runs the real main.lua inside a Python Lua runtime (lupa) with mocks, checks globals and the 200-locals limit, and adds a failing test before a fix. Use for every edit to main.lua or tools/, before any lab session, and when reviewing a contribution.
---

# Offline tests

Most of the mod's decisions (orders, economy, logistics, saves, AI) are tested without Unreal: the tests load the
real `mod/FoxholeRTS/Scripts/main.lua` in a Lua runtime and mock the UE4SS/Unreal API. They check Lua decisions,
**not** Unreal physics, hooks or keyboard integration; a pass here never approves a live gate.

## Setup
```bash
pip install --target <pylibs> lupa      # maintainer: D:/tools/pylibs
export PYTHONPATH=<pylibs>              # PowerShell: $env:PYTHONPATH='<pylibs>'
```

## Run
```bash
python tools/test_orders.py             # main suite: orders, keys, economy, logistics, saves
for t in tools/test_*.py; do python "$t" >/dev/null 2>&1 && echo "OK $t" || echo "FAIL $t"; done
python tools/check_globals.py mod/FoxholeRTS/Scripts/main.lua
```
All `tools/test_*.py` must pass before a commit. CI runs the same loop.

## How a test is built
- `tools/test_orders.py` creates a `LuaRuntime`, defines mocks (`world`, `KismetSystemLibrary` traces against a
  synthetic terrain with a wall at X=500, `SpawnActor`, clock), loads `main.lua` and calls its tables
  (`rts`, `logi`, `sv`, ...). Copy that pattern for a new file `tools/test_<topic>.py`.
- Write the test **before** the fix and see it fail. Name the scenario in the assert message.
- Mocks must not be more forgiving than the game: if the game returns an actor already being destroyed, the mock
  should be able to as well (`bActorIsBeingDestroyed`).
- A new key needs an entry in the key test of `tools/test_orders.py`; it checks against the game's own input
  mappings (`InputSettings`) and rejects conflicts.

## Limits of main.lua
- **200 locals per chunk**: `main.lua` is at 178. Add functions to the existing tables, constants to `CFG`,
  state to `S`. Never add a top-level `local` without a strong reason.
- `check_globals.py` is scope-insensitive. Never name a local after a top-level table (`ai`, `sv`, `fort`, `rts`,
  `anim`, `S`, `logi`).
- The command channel only sees names listed in the `env` table of `runCommandFile`; add new helpers there if a
  live probe needs them.
- UFunctions cannot run inside Lua coroutines: slice long work into a per-frame state machine.

## Data-driven checks
- Costs: `tools/test_costs.py` against `data/game_costs.txt`. Recipes use `ProductionResource.ItemCodeName`;
  structures/vehicles use `ResourceAmounts` + `CodeNameSmallQuantity.CodeName`. A schema error is a failure,
  never a zero cost.
- Trace checkers (`tools/check_*_trace.py`) read recorded traces in `data/`. They return non-zero while a gate
  is not approved; that is expected and honest. Do not edit traces to make them pass.

## Before the lab
When the batch is ready offline, go to `lab-batch`. Never restart the game to "just check" one change.
