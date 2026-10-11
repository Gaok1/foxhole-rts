# Lab script — MANUAL COLLECTION (candidate v3)

Only run when the user authorizes the lab session. No step was run by the agent. Real input belongs to the user.
Prerequisite: publish `candidate_v3/main.lua` (SHA256 in `candidate_v3/SHA256.txt`) as the mod's `main.lua` only after the other candidates are integrated.

1. **New match** (Alt+L, then new match): check cost 1000, 2 supply trucks, no resource truck on the map, bmat 40 in the panel.
2. **Spawn** (~5 s): 3 soldiers **without weapons** near the base; no T-pose; base shirts 30 → 27; no crash (`UE4SS.log`, `Saved\Crashes`).
3. **Walk**: they reach the salvage field, stand collecting, come back and deliver at the refinery; time of the 1st delivery and of the 1st truck (compare with 165 s at 80 m / 359 s at 470 m in the harness). Note the real field–refinery distance and whether any gets stuck.
4. **Truck**: on reaching 100 bmat the factory builds the resource truck; it appears at the field, upright on the ground, not stuck; the message "coleta manual encerrada" (manual collection ended) shows; the panel loses the collection line.
5. **Player order**: select a worker and send them elsewhere; they leave collection; 60 s later they come back by themselves.
6. **Truck loss**: destroy the resource truck with bmat/salvage at zero (command channel); collection reactivates and the truck comes back.
7. **Combat**: bring an enemy near the field; workers pause; a death is replaced for 1 shirt.
8. **Save/continue** with workers in the field: cargo in hand discarded (log), 3 workers, collection restarts.
9. Cost per frame: compare frame time with and without active collection.

Close the game again at the end (only the copy's PID in `D:\FoxholeLab\Foxhole`).
