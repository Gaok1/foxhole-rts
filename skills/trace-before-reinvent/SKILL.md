---
name: trace-before-reinvent
description: Find and record the game's own flow before implementing or fixing a Foxhole mechanic (death, firing, damage, vehicles, construction, animation). Covers UE4SS UFunction hooks, recorded traces as oracles, contracts, Ghidra and when reinventing is allowed. Use before writing any code that imitates something the game already does.
---

# Trace before reinventing

The mod calls pieces of the game one by one and sometimes forgets one (a dead soldier that keeps "running"
in place). The maintainer's rule: **look for the game's own call and record the real flow first.** Rebuilding a
mechanic by hand is allowed only after showing the native path needs a server, RPC or native inventory, which
this offline mod does not use.

## 0. Ask the knowledge bases
- `um kb search <topic>` (universal-modder) and its skills `reverse-engineering` ("record real traces",
  "make it an oracle") and `mod-any-game` (`references/engines/unreal.md`).
- `grep -ril <ClassOrFunction> data/` here: many flows are already recorded.

## 1. Find the high-level call
- List the UFunctions of the classes involved (character, controller, weapon, AnimInstance, vehicle) with
  UE4SS `ForEachFunction`, and prefer the call the game itself uses (die, fire, reload, heal, build).
- Native code: Ghidra project with the GhidraMCP bridge (see `AGENTS.md`, Environment). Name what you find;
  never commit decompiled code. Describe the logic in your own words.

## 2. Record the real flow once
- Hook the UFunctions (UE4SS `RegisterHook`) and write the order of calls and the values that change when the
  action really happens: the human does it with their character, or the game does it alone (like death).
- Save the result as `data/trace_<topic>.txt` (or `.md` with the analysis). Traces are evidence: never edit
  them afterwards; record a new one instead.
- Sample per frame with `LoopInGameThreadWithDelay(100)` writing to `_G`, not with channel round trips (~1.8 s).

## 3. Write the contract
The list of what the real flow changes: animation variables, velocity, replicated flags, effects, sounds,
lifecycle (lifespan, GC). If the mod must reinvent part of it, it fulfils this contract item by item.

## 4. Test the contract
- Offline: a test in `tools/test_*.py` that fails before the change (see `offline-tests`).
- Live: a probe that reads the same values after the mod's action and compares them with the trace. It goes
  into the next lab batch (`lab-batch`), not into an ad-hoc restart.

## Worked example: death (batch 14)
`ApplyDamage` on the host zeroed HP without the ragdoll. The trace (`data/trace_death.txt`) showed
`OnRep_Health` does the native visual transition. The mod now stops movement, restores the original values,
removes the animation cache (`anim.untrack`) and then calls it. Do not touch the AnimInstance after the
notification nor the body after its TTL.

## Red lines
- Do not replace damage, shots or vehicles with abstract DPS "for now"; that branch was rejected.
- Do not call `OnRep_*` or death by hand to anticipate a native timer.
- Do not disable protections or debug checks to make a result appear.
- No RPC, login, connection or blind creation of a LocalPlayer as a fix.
- The game has no soldier AI: our soldiers are "players" without a keyboard, so deciding is always the mod's
  job. What can be reused for free is what comes after the decision (animation, death, effects, damage).
