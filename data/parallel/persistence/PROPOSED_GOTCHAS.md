# Proposed gotchas (for universal-modder's note `knowledge/games/foxhole/...`; the coordinator records them)

Consulted at the start: `um kb search` for save, persistence, serialization, "atomic write", foxhole (Foxhole note,
gotchas 33–38; Minecraft note with atomic write via temp + move). Nothing was written to universal-modder.

1. **A save as `return {...}` + `load` is not safe reading.** An empty environment prevents `os`/`io`, but not an
   infinite loop nor a gigantic string; and it accepts anything that evaluates to a table. A literal parser
   (tables `[k]=v`, numbers, `%q` strings, booleans) with byte/depth/item limits solves it without a
   dependency. `sv.ser` also silently wrote NaN/inf as `0` and userdata as `nil`: validate what is going to
   be written and decode your own text before swapping the file.
2. **Windows: `os.rename` does not overwrite.** MSVCRT fails if the destination exists. Atomic write: a temporary
   checked by rereading → the previous one becomes `.bak` (or `.corrupt`, if invalid) → the temporary becomes the save; a failure
   brings back the previous one. On reading, the order is save → `.tmp` (crash between the renames) → `.bak`. The real behavior in
   UE4SS's Lua is still a lab gate.
3. **Deployed infrastructure does not survive a restart and a wallet keyed by the world's address is reborn full.**
   `S.deploy` was keyed by `GetFullName..GetAddress` (changes on every load) and did not go into the save: continuing
   asked for Alt+L again and paid once more with 1100 new. Persist what was **paid** (code, XYZ, the ruin's yaw)
   and the wallet; on a new load, redo only over the matching ruin (≤ 2 m, ≤ 1°), without charging again,
   trucks only up to the number paid. Never persist the address; it only identifies the current load.
4. **A point index as identity breaks if a point does not come back.** The save keeps depots and posts by
   index; `addPoint` may refuse (no surface, overlap, limit). Check surface/overlap
   before clearing the match and, afterwards, compare index→coordinate; a difference = logistics not restored (no
   fictitious starting stock in its place) and autosave suspended so as not to overwrite the good save.
5. **Preflight before `clearSquad`.** The old continue destroyed the current match and only then discovered
   problems. Safe order: read/validate → world/surface/ruins/wallet/logistics → redo infra (with its own
   rollback) → clear and restore → check counts.
6. **`logi.start` creates scenario stock.** Restoring by calling start and then assigning fields leaves
   fictitious stock if something fails midway; and the enemy convoy went back to `cargo0`. Validate everything first; on failure,
   `logi.reset` instead of leaving the starting stock.
7. **Routes are not saved.** The ESTRADAS graph has an epoch with the session; an old route is invalid by construction.
   Save only state/cargo/destination by identifier and replan (`route/routeDest/pathJob = nil`).
