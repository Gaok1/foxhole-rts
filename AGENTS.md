# Foxhole RTS: instructions for agents (Claude Code, Codex, Gemini CLI, Cursor, Copilot, ...)

A UE4SS mod (Lua, UE 4.24) that turns an isolated lab copy of Foxhole into a single-player RTS against an AI,
with logistics at the center. Code: `mod/FoxholeRTS/Scripts/main.lua` (v0.9, one file). Controls and mechanics:
`mod/README.md`. Direction: `ROADMAP.md`. Public checklist: `PROGRESS.md`.

Everything an agent needs lives **in this repository**, not in private agent memory. When you learn something that
matters for the next session, write it here, in `MODLOG.md` or in `ROADMAP.md`.

## Start here
1. **Read `skills/resume-work/SKILL.md` and follow it.** In short: `git status`, the "How to resume" section of
   `MODLOG.md` (middle of the file, search for that title), the top of `ROADMAP.md`, then pick an item from
   `PROGRESS.md`. New diary entries go at the top of `MODLOG.md`.
2. **Before a new mechanic or an engine problem:** `skills/trace-before-reinvent/SKILL.md`. Find the game's own
   call and record the real flow before rebuilding anything by hand.
3. **Change code offline first:** `skills/offline-tests/SKILL.md`. Live validation in the game is batched:
   `skills/lab-batch/SKILL.md`.
4. **At the end:** `skills/wrap-up/SKILL.md` (diary, progress bars, docs, commit/PR).

Your human may be the maintainer (Gaok1) or a contributor with their own copy of the game. Rules marked
*maintainer's lab* describe the maintainer's machine; contributors adapt the paths (`tools/lab/env.sh`).

## Skills
`skills/*/SKILL.md` (Agent Skills format) are copied to `.claude/skills` (Claude Code) and `.agents/skills`
(Codex, Gemini CLI, Copilot, Cursor, OpenCode). Edit `skills/`, then run `python tools/sync_skills.py`;
`tools/test_skills_sync.py` fails while the copies differ.

| Skill | When |
|---|---|
| `resume-work` | Start of every session |
| `trace-before-reinvent` | Before implementing or fixing a game mechanic (oracles, UE4SS hooks, Ghidra) |
| `offline-tests` | Every code change: Lua harness in Python (lupa), globals check, the 200-locals limit |
| `lab-batch` | Live validation in the lab copy: one publish, scenarios in sequence, close the game |
| `wrap-up` | End of session: MODLOG, PROGRESS, README/MANUAL_TEST, universal-modder note, commit/PR |

## Hard rules
- **Fully offline**, with the mod's own systems. Do not chase the game's RPC, native inventory or server.
- **Never on the Steam install, never online.** UE4SS and the mod go only in the isolated lab copy, which is blocked
  from the network. Keep its firewall block (the menu warning "Failed to download server information" is its effect;
  the autostart leaves the menu in 2 s).
- **Steam ownership stays:** Steam open and logged in; never bypass DRM or ownership checks; never log in to Steam for
  the user.
- **No game files in commits:** binaries, DLLs, paks, extracted assets, decompiled code. The repository is public
  (MIT). No tokens or personal paths (`C:\Users\...`).
- **No injected input:** the maintainer denied computer-use on the game window. Do not send keyboard or mouse by any
  means. Real-input tests belong to the human (`MANUAL_TEST.md`); yours go through the command channel.
- **Trace before reinventing:** look for the game's own call and record the real flow before recreating a mechanic.
  Do not replace engine systems (damage, shots, vehicles) with abstract numbers without proving it is impossible.
- **Do not fake results:** no fictitious deliveries, extra money or disabled protections to make a gate pass.
  `[x]` in `PROGRESS.md` only with live validation.
- **Ask first** before publishing anything (PRs, issues, releases) and before installing loaders into game folders.

## Language
- Repository content is **English**: docs, diary, comments in new code, commit messages, PRs.
- Talk to your human in their language (the maintainer writes Portuguese).
- On-screen strings in `main.lua` and recorded traces (`data/trace_*`) are still Portuguese. Do not translate traces:
  they are evidence and checkers parse them. Localizing the UI is a roadmap item, not a drive-by change.

## Direction (maintainer, 2026-10-09)
- Start in a small region and only then the world. Logistics (resource, refining, factory, transport, supply) is the
  center; the war is "the small part of the machine". The RTS must work for watching several fronts (high zoom,
  alerts, groups).
- **Work in batches.** Several features with offline tests, then one single lab session (a game restart costs
  minutes). Do not open or restart the lab for every finding, probe, helper or small change. Accumulate changes, write
  scenarios with pass criteria, publish once, run them in sequence in the SAME game session with cleanup between them.
  New ideas found during validation go to the next batch. Exception: a crash or a concrete prerequisite that blocks the
  batch; record the cause before restarting.
- **Close the game when the lab is idle:** kill only the PID of the lab copy. Never close Steam.

## Workflow
- **universal-modder at the start and at the end** (the maintainer asked twice): before a new mechanic or engine
  problem, `um kb search <topic>` and the skills `reverse-engineering` ("record real traces"), `mod-any-game`
  (`references/engines/unreal.md`) and the oracle technique. At the end, add learnings as gotchas to the note
  `knowledge/games/foxhole/...` and run `um kb check` (local; PR only with the human's OK).
  Repo: https://github.com/rehan-remade/universal-modder.
- Publish and restart the game: `sh tools/lab/restart.sh` (syntax + globals check, copy, wait for RTS mode).
  Do not use UE4SS Ctrl+R (it froze the game).
- Offline tests: `PYTHONPATH=<pylibs> python tools/test_orders.py` (and the other `tools/test_*.py`).
- Live commands: `sh tools/lab/run.sh <file.lua>`; only `out(...)` comes back. Never use the channel while the bot runs.
- Regression bot: `sh tools/lab/botloop.sh` in the background. What it does and does not cover: `MODLOG.md`.
- After each change: validate live, write at the top of `MODLOG.md`, update `mod/README.md`; for a new key, also
  `MANUAL_TEST.md` and the key test in `tools/test_orders.py`.
- When a roadmap item changes state (`[ ]` → `[~]` → `[x]`), update `PROGRESS.md` and run
  `python tools/progress.py`, which recomputes the bars in `README.md`.

## Environment
- Lab copy: UE4SS in `War/Binaries/Win64/ue4ss`, log `UE4SS.log`. Needs Steam open and logged in plus
  `steam_appid.txt`. Game config/logs: `%LOCALAPPDATA%\Foxhole\Saved\` (not "War"); crashes in `Saved\Crashes`.
- The first load sits ~3 min on a black "Not responding" screen: it is loading, not frozen.
- Shipping ignores the map on the command line; the mod opens `HomeRegionW?listen` with `OpenLevel` (autostart,
  enabled by `Mods/FoxholeRTS/autostart.txt`).
- The command channel folder is `CFG.CMD_FILE` / `CFG.CMD_OUT` in `main.lua`; it must match `LAB_CHANNEL` in
  `tools/lab/env.sh`. The channel runs arbitrary local Lua: it is not a sandbox.
- *Maintainer's lab:* lab copy `D:\FoxholeLab\Foxhole`, channel and probe scripts (`t_*.lua`) in
  `D:\tools\foxhole-lab`, lupa in `D:\tools\pylibs`, large installs go to `D:\tools`. Terminal: Windows PowerShell 5.1
  (no `&&`, no `/d/` paths). Ghidra 12.1.2 in `D:\tools\ghidra\ghidra_12.1.2_PUBLIC` (JDK 21); GhidraMCP bridge in
  `D:\tools\ghidra-mcp-v5.14.2`, server on `127.0.0.1:8089` (GUI with the plugin or
  `com.xebyte.headless.GhidraMCPHeadlessServer`); project `D:\tools\ghidra-projects\Foxhole`, pre-script
  `D:\tools\ghidra-scripts\FoxPre.java`. universal-modder: `UM_HOME=D:/tools/um-home python -m um ...`.
  Agents do not edit `~/.claude.json`: hand the human `claude mcp` commands.

## Pitfalls
- Costs: recipes use `ProductionResource.ItemCodeName`; structures/vehicles use `ResourceAmounts` with
  `CodeNameSmallQuantity.CodeName`. Never swallow a schema error as zero cost. Exporter/test: `tools/export_costs.lua`,
  `tools/test_costs.py`.
- Truck spawn can return IsValid on an actor already being destroyed; a ground trace can hit a roof. Check
  `bActorIsBeingDestroyed`, position/health and surface/clearance, not just the return value or total bounds.
- Lua allows 200 locals per chunk: `main.lua` is at 178. Constants in `CFG`, state in `S`, new functions in tables
  (`rts`, `fort`, `sv`, `logi`, `anim`, `ai`).
- Git repository since 2026-10-11; earlier history does not exist. `.gitattributes` stores bytes as they are
  (`* -text`): do not convert CRLF/LF of the `_lf` patches and candidate copies (their SHA256 is recorded).
- Animation hook (`anim.onUpdate`, on `ABP_Male_C`'s `BlueprintUpdateAnimation`, runs after native) only writes to a
  live AnimInstance. Every path that destroys a soldier calls `anim.untrack` (reused address → write into a dead pawn →
  native crash that pcall cannot catch). Same rule for any cache keyed by address.
- The command channel only sees what is in the `env` table of `runCommandFile`; a new local must be added there.
- `tools/check_globals.py` is scope-insensitive: an inner `local x` before the top-level `local x` hides uses of the
  top-level one as nil globals. It warns about these; never use a top-level table name (`ai`, `sv`, `fort`, `rts`,
  `anim`, `S`, `logi`) as a local variable.
- Movement: the mod zeroes friction and braking, so the `AddMovementInput` scale only limits acceleration; to slow
  down, write `CharacterMovement.Velocity` (`fort.capSpeed`). Measure movement with a `LoopInGameThreadWithDelay(100)`
  sampler writing to `_G`, not with channel round trips (~1.8 s each).
- UE4SS: reading `MasterPoseComponent`/`AnimClass` of a SkeletalMeshComponent crashed UE4SS; non-reflected components
  are found by name with `K2_GetComponentsByClass` (`v:get()`). UFunctions cannot be called from inside a Lua
  coroutine: slice long work into a per-frame state machine. `UEHelpers.GetWorld()` / `GetPlayerController()` run
  `FindAllOf` on every call (slow): the mod caches them per frame. `K2_DestroyActor` does not destroy
  `HeadlessPlayerController` (the mod reuses it). `IsValid()` stays true on a destroyed actor until GC. Out parameters
  land in the first table (`GetMousePosition(a, b)` → `a.LocationX/Y`).
- Vision: the game hides characters and vehicles the commander's **pawn** cannot see; the mod turns the commander
  into an invisible "eye" carried to the soldier closest to the camera focus. Moving the LOS component does not help.
  Snow edges block vision.
- **A picture does not prove absence:** structures can also turn invisible depending on camera angle/occlusion.
  Check actors/classes/variants and loaded state; tell a ruin from an active installation. A zero count of one class
  does not prove the installation is missing from the map or from a server war's state.
- Traces in HomeRegionW: channel Visibility (0) goes through vehicles; Camera (1) hits trucks and buildings but not
  `BPNoBuild_C` (the A* uses it); an object-type trace hits the `BPNoBuild_C` volumes (ignore them).
- Animation: `CharacterStance` 0 standing / 1 crouched / 3 running (+ `bStanceIsCrouched`); `ActivityState` 3 firing,
  6 throwing, 20 first aid; weapon on socket `S_GenericGun`; shoulder aim with `bIsInScopeMode` +
  `canEnterStandScoping`.
- Finding assets: `FindAllOf("StaticMesh"/"SoundCue"/"Material")` + a name filter, `GetBounds()` for size, then a
  side-by-side "showcase" + screenshot to choose.
- The RTS camera looks toward +X: top of the screen = larger X, right = larger Y.
