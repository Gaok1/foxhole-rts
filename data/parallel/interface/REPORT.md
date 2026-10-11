# INTERFACE — offline delivery, 2026-10-09

## Existing evidence / contract

- `main.lua:4550–4684`: the native Slate HUD does not expose TextBlocks; the mod's renderer clones `CrosshairWidget_C`, uses `WidgetTree.RootWidget` (CanvasPanel), `StaticConstructObject(UMG.TextBlock)`, `AddChildToCanvas`, `SetAutoSize`, `SetPosition`, `SetText`, `SetVisibility` and `AddToViewport(50)`. Methods already used and capture recorded in the code; no new session certified by this task.
- `hudTick`: 0.25 s of **real time**, including pause; removes the widget when the RTS turns off. A map change still needs a specific gate: do not confuse IsValid of the old widget with the current owner/world.
- `logi.hudLine`: today concatenates logistics into one long line. The proposal `painel.patch` replaces only that function, reusing the existing TextBlock with lines for production, physical stock/target, crates versus units and each truck/cargo/destination. It creates no actor, new UMG API, key or stock.
- One production task (`logi.job`), not an arbitrary queue: debited at start, crate added on completion. Do not call it the player's order queue.
- `fac.ammo`, `fac.shirts`, `tr.cargo` = **crates**. `depot.ammo` = ammo supply; `depot.shirts` = individual shirts; the shirt recipe has `units=10`. `logi.need` discounts transit; the panel's indicator uses physical stock and target, it does not claim unmet scarcity.
- `logi.depots()` creates/reuses depots of allied points through `depotOf`; the proposal introduces no mutation beyond the function already used in the HUD. A destroyed transport shows lost cargo, not a fictitious pending delivery.

## Selection box: minimal solution, NOT implemented yet

`mouseTick` stores a **ground point**, and `selectBox` tests an XY rectangle in the world with a 50 cm margin. Drawing a rectangle between screen positions can diverge with terrain/camera. Trace before changing semantics. Preference: project the four corners of the same XY rectangle/margin onto the ground and render non-interactive edges on the Canvas; if projection is not available, define/test selection in screen coordinates as an explicit behavior change.

Probes required from LABORATORIO (none run by the agent):
1. Inspect **only known/reflected UFunctions** of PlayerController/WidgetLayoutLibrary for projection, viewport/DPI conversion and parameter output. `GetMousePosition` already appears in the code, with output in the first table; projection and scale are NOT proven. Do not call presumed names in main.lua.
2. Find the class and properties of UMG Image/Border and CanvasSlot: proof of constructor, tint/transparency, position/size and hit-testing. No new call of these types in this patch.
3. Oracle: the user drags in all four directions; record start/end ground points, screen coordinates, the four projected corners and the selected cast; static camera/then moved during the drag, low/high zoom, uneven terrain and different DPI/resolution.
4. The box must appear only after DRAG_MIN, vanish on release/RTS off/map change, Shift adds without blocking right click/camera, no widget capturing the mouse. Update every frame, not every 0.25 s.

## Focus and alerts

Reuse the existing Ctrl+L/Q/E/Space controls; the patch makes them explicit, it does not pretend text lines are buttons. Focus buttons for each truck/installation and deduplicated stock alerts remain open subtasks: they require a valid action/destination contract and an input gate. Do not produce repeated alerts on each refresh nor references to destroyed actors.

## Integration / visual / user gate

- Offline: `PYTHONPATH=D:/tools/pylibs python data/parallel/interface/test_interface.py` PASS: production, units, transit, destruction, targets, inactivity, stocks unchanged.
- Integrator: apply `painel.patch` only after stability; check sources/anchors and run the existing suite. Zero new top-level locals.
- Lab: panel in a match/active logistics, pause, logistics off, new map, lost depot, dead/recreated truck; record a capture and data from the same instant. Check overlap, width/height at various zooms/resolutions, F5 help and native alerts. Multiline uses the current HUD, with no proven clipping/scroll. If the cast exceeds the height: adjust the layout before approving, do not silently hide stocks/vehicles.
- User: left/Shift/right/camera/F5/Ctrl+L/Q/E/Space keep working. **No real input was tested here.** The box requires the probes above, it is not delivered.
- Overall status: tested proposal, NOT an integrated/finished feature. main.lua unchanged; game/channel/processes not accessed.

## Universal-modder

Consulted reverse-engineering (oracles/real trace), mod-any-game and the Unreal playbook. `um kb search foxhole` found the existing note; the search "foxhole widget" returned no match. The coordinator must record a Gotcha in the shared note (to avoid simultaneous writes): the panel mixes crates and units; the selector's XY rectangle is not automatically a screen rectangle; UMG projection/DPI/border calls still require a probe. Run kb check at the end of the batch.

## Functional preservation review

- Kept the enemy cargo line and the convoy warning outside the assault, equal to the previous contract. It does not claim a quantity/position the source does not provide.
- Audited all allied states: idle/res starts collection; idle/sup returns or waits for the factory (do not claim it already arrived); toField, loading, toRef, toDep, dead. Destinations derived from state when tr.dest does not exist. Point names come from pt.name -> dep.name; the base uses "base".
- job.total is always produced by factoryStep, but the current snapshot/restore do NOT persist job or total (restore calls start/reset). The proposal now shows only the remaining time when total is absent, without inventing a reconstructed duration. Incomplete persistence is another task, not fixed by the UI.
- Tests added: each allied state, point names, missing job.total, enemy cargo, convoy and hiding during the assault. PASS.
