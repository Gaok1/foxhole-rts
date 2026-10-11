# Repeated stability control — proposal, not run

Goal: tell selection/clones apart from common callbacks/anim. No agent input; ask the user
not to operate the game/console during each window. Do not automate that restriction nor use keyboard/mouse.
Exclusive lab, botloop off, Steam/DRM/firewall preserved.

## Common preparation

- Keep the current source/hash and the UE4SS binary/hash, map HomeRegionW, PID/log/crash baseline.
- Publish only through restart.sh; wait for RTS/live log, not an isolated timeout. Do not use a hotpatch or Ctrl+R.
- Same map/camera/home, no enemies/waves/logistics; 6 live soldiers standing still.
- Experimental queue NOT integrated (the original bridge stays), anim.hooked current fix documented.
- Confirm the m.sel state of all 6, hp/retired, number of clones/sources and anim.units. Only properties
  already verified; do not read MasterPoseComponent/AnimClass.
- Change sel through a direct mod command, no fake keybind nor temporary callback.
- Start the window only after 5 s of settling and a profile reset; keep the gameRealTime timestamp and an external
  monotonic one, so as not to confuse time since the group with the profile's duration.

## Sequence per clean load, 4 independent runs

| Run | State | Window | Requirements |
|---|---|---|---|
| A1 | 6 not selected; anim active; 0 clones | 180 s | the minimum exceeds the 111 s crash; log before/after |
| B1 | 6 selected; anim active; 168 clones | 180 s | same 6 classes/camera/state |
| B2 | new load, 6 selected | 180 s | repeat in reversed order |
| A2 | new load, 6 not selected | 180 s | repeat the control |

Never turn A→B in the same process to compare a baseline: earlier creation/destruction confuses it.
Inside the window, no GC/reselection/death command nor capture/callback probe; three checkpoints through the
direct channel at 60/120/180 s for profile/count, applied equally to A/B. Each profile reset
identifies the phase/timestamp. Final capture only after the window. Do not restart because of one timeout observation:
confirm terminal/crash/process; the game Not Responding while loading is not proof of a freeze.

## Collection at checkpoint/end

PID, process status/log timestamp, frame count, profile stratTick/total, selected/tracked and total live/
being destroyed/untracked actors. Registry errors: timestamp and context 50 lines before/after; keep the complete
stack XML if it crashes. Wheel/selection logs reported as observed events, not an attributed cause.
If the process dies before 111 s, keep the real end; do not call the window completed. If it survives 180 s,
the result is a PASS of that window, not a stable build.

## Decisions

- Failure A with 0 clones: the outline is not needed to reproduce this failure; investigate common callbacks/anim.
- Failure B and both A survived: selection/clones are associated, not yet the cause; the next variant isolates source/part.
- Failure A/B: the common bridge deserves symbols/trace; do not mix the queue toggle into the current control.
- No failure: widen repetition/duration and GC/death transitions in a later batch; the cause remains not isolated.
- Compare queue false/true only later, with two equivalent loads with the user doing authorized real input
  and an identical script; the agent does not inject. The toggle must be the only factor. Input compatibility is the user's gate.

When ending a test/bot or going back offline: close only the verified PID of the lab copy; preserve Steam.
