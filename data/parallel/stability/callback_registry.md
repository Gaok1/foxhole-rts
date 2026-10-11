# Callback/Registry audit after crash PID4408

## Compared evidence (not a diagnosis)

`crashes_compared.json` was extracted from three real CrashContext.runtime-xml files.
- DF9A… batch17: read 0xffffffff.
- 97D8… batch17: the XML records read 0x08 (corrects the generic description in the old trace).
- 18BCE… PID4408: read 0x63, SecondsSinceStart 111.
All carry PCallStackHash 6341FC051FB0F3E558B68187F705D55824D754E0, but DIFFERENT stack headers;
an equal hash alone does not prove the same instruction/cause. Repeated Lua/UE4SS offsets are common:
b985c4, b9d34c, c6cfde, c6c1e0, c77cab, c6b9a9, c6c733, c6bff4, c640ac, c7c9a1.
Equal engine tail: +5220da, +52847c, +5284fa, +53265b, +32ae58e. Without symbols/PDB do not name these offsets.
The new stack and 97D8 share a very similar structure after the header; the first DF9A also goes
through the repeated sequence. This justifies investigating the Lua/callback bridge common to the variants; it does not clear
the outline nor attribute MasterPose/GC/input.

Timeline given by the coordinator: wheel 18:20:01, "Registry Ref was not function" 18:20:03,
"selecionados 6" logs 18:20:04/06. These later entries show the Registry error is not the moment
the process ended. No entry was injected by the agent; the wheel event does not show a cause.

## Flows recorded in the current source

- `onGame(f)` creates a keybind closure; each execution creates a NEW closure passed to ExecuteInGameThread.
  The inner closure captures f; the keybind registration and the engine queue must retain the Lua reference correctly.
  The source does not remove callbacks, call luaL_unref nor manipulate the Registry directly.
- `plain(f)` captures f and queries modifier keys INSIDE the queued closure; it does not need to keep
  the playerController userdata between scheduling and execution. The controller is looked up at execution time.
- The mouse wheel does not use RegisterKeyBind/onGame: `cameraTick` calls `rts.wheel`, a per-frame poll.
  Click/drag selection also comes from the frame/mouseTick, not necessarily a keybind wrapper.
  So wheel/selection logs do not identify which Registry callback failed.
- Animation: RegisterHook once per ABP, a stable callback function `anim.onUpdate` stored in the anim table.
  onUpdate takes the live AnimInstance ctx and m by address. All audited death paths remove the anim cache
  before OnRep_Health; an AnimInstance swap with a live unit is not revalidated automatically.
- `anim.track`: sets anim.hooked=true EVEN if pcall(RegisterHook) fails. Provable logic defect:
  an initial failure suppresses all later attempts. It does not directly explain an invalid Registry in a hook
  already registered. Separate minimal proposal: only set hooked=true if hk==true; do not apply without a test.
- Hook IDs are not stored, there is no unregister in the flow. This does not prove improper collection: retention must
  be guaranteed by the native API. Extra anchoring in Lua would be a hypothesis/experiment, not a root cause.
- The main AfterFrames loop has a persistent closure; the channel/autostart Delay1000 has another closure;
  respawn pre/post hooks and ServerTakePickup hooks are also callbacks. A stack without symbols does not tell them apart.
- The probes run were direct calls through the channel; they added no callback/hotpatch. This reduces
  recent contamination, but does not rule out the existing keybind/anim/loop bridge.

## Next recommended investigation without restarting here

1. Keep UE4SS.log and the crash XML/dump and binary/mod hashes. Resolve offsets with an exactly matching PDB
   if already available; do not download a build and swap the loader mid-diagnosis. Check version/hash first.
2. Find the first Registry emission in the log and all contexts before/after; mark probe boundaries.
   Do not presume the origin from the last Lua log before the message.
3. Experiments on separate clean loads: six soldiers WITHOUT selection with animation; then with selection;
   repeat without real input, asking the user not to touch (the agent never injects). The control must last
   at least the window that failed, 111 s, and repeat; isolated survival does not certify.
4. An experimental variant only for isolation keeps refs of queued callbacks until execution,
   without changing logic; compare registration+ExecInGameThread with the frame loop/channel. Do not treat Lua retention as
   a fix before reproducing the error/its disappearance. Never reuse ctx userdata outside the hook.
5. Instrumentation through `_G` counters at the start/end of preexisting callbacks, not new callbacks.
   Labeled record of keybind enqueue/start/end and updateanim start/end, engine logs kept.
   Per-frame logging must be sampled/counted so as not to change timing too much.
6. Do not turn off the outline as the final solution nor revert the appearance to discs; variants without clones are control only.
   Do not remove Steam/firewall protections, do not call native RPC to generate a reproduction.

## Conclusion

The crash persists after guards and optimizations. There is strong evidence of a recurring UE4SS/Lua path,
but no symbol/reproduction identifies the guilty function. Performance and stability remain independent
gates. I did not declare the batch stable; no main.lua or process was changed by this audit.


### Update: reduce ephemeral callbacks without claiming a cause

MODLOG.md:1320 records the v0.2 crash with LoopAsync 33 ms + ExecuteInGameThread; migration to persistent
GameThread loops. The current source keeps ExecuteInGameThread in the key wrapper. That history
justifies an isolated experiment with a Lua queue drained in the persistent loop, but the situations are not equivalent:
the earlier one was a continuous 33 ms, the current one per key event, Registry with no confirmed origin.

Minimal proposed queue: onGame(f) returns a closure that only inserts f into an S table; the persistent frame drains
before the isLocalAuthority early return (F9/session and F10 must work in the menu), by snapshot/swap
of the queue so new events do not mutate the iteration; keeps pcall/log and FIFO order. Every f runs on
the GameThread of the existing loop, no ephemeral ExecuteInGameThread. Normal events stay explicitly
behind plain(), which must query modifiers at execution time as it does today.

Caveats: synchronization between the keybind callback thread and the Lua frame depends on a UE4SS guarantee; do not presume
thread-safety just because it is a Lua table. Limiting the drain per frame avoids a freeze if an event source
floods, but do NOT silently drop orders. Do not create a timer/new callback to drain; do not change
selection/wheel polling. Run an offline FIFO/reentrancy/error test before and after and a real user input gate.
First measure whether the Registry error appears without a keypress: if so, the wrapper may not explain the observed crash.

A search for *.pdb in D:/tools/ue4ss returned no file. Without a matching symbol I did not map offsets;
no download or relaunch done.


## Separate deliveries (not applied)

- anim_hook.before.lua/after.lua + test_anim_hook.py PASS: an initial RegisterHook failure keeps cache 42
  but hooked=false, the next retry registers exactly once and later calls do not duplicate the hook.
  Independent defect, not an attributed cause of the crash.
- queue_experiment.before.txt/after.txt + test_queue_experiment.py: two blocks, wrapper and frame start.
  CFG.KEYBIND_QUEUE=false keeps the previous path; true avoids the ephemeral ExecuteInGameThread.
  Drains before the early return/menu, swaps the queue before iterating (reentrant enqueues go to the next frame),
  pcall/log per event keeps FIFO and continuity after an error. No RPC/wheel polling manipulation.
  The test does not prove native thread synchronization; it requires a clean isolated variant and real user input.
  Do not integrate together with anim_hook in an experiment meant to infer a cause: one factor per load.
