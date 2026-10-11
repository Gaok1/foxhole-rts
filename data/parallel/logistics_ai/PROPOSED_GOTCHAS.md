# Proposed gotchas (IA_LOGISTICA) for the note `knowledge/games/foxhole/...`

CLAUDE_IA_LOGISTICA did not edit universal-modder. The coordinator records them; local `um kb check`, no PR
without the user's authorization.

1. **A "cargo" counter is not logistics.** The mod's enemy convoy added +1 cargo on arrival, with no origin,
   and the save did not keep that number (every continue returned `cargo0`). For interdiction to have a
   traceable effect, the truck needs to carry crates debited from a stock that can run out, and the loss needs
   to enter a ledger (initial + produced = stocks + transit + consumed + lost) that can be checked
   through the channel.
2. **Priority between the factory and rebuilding a truck.** If the factory starts an 80 bmat job whenever it
   can, a 100 bmat truck (TruckC/TruckW Cloth 100) never comes back under continuous consumption, because bmat
   never accumulates to 100. When the fleet is at zero, reserve bmat for the truck. The simulation showed this on the
   enemy side; on the player's side (same order) it is still a hypothesis.
3. **A one-crate convoy wastes a truck.** Dispatching as soon as there is one crate makes each ambush cost
   a whole truck for little cargo, and the cheapest product monopolizes the factory. Require a minimum load
   or the front's full order.
4. **The save rounds.** `sv.ser` writes non-integer numbers with 3 decimals. A ledger validated on load with
   a 1e-6 tolerance refuses legitimate saves. Validate with slack (0.05) and, when restoring, absorb the leftover in the
   origin terms so the in-memory ledger closes exactly. Never turn that leftover into stock.
5. **Attributing interdiction requires a counterfactual.** Cargo lost before wave N affects several waves, not only the
   next one. A "losses since the last wave" counter underestimates the effect; use a ghost stock that is spent
   as the waves would have consumed it.
6. **Testing the whole chunk with swapped boundaries.** In the lupa harness, code appended to the end of the same
   chunk can reassign top-level `local function`s (`spawnEnemies`, `waveSpawnPoint`, `isLocalAuthority`), and
   the mod's functions see this as an upvalue. That way you can swap only the engine boundary and call the
   real `waveTick`/`ai.tick`/`sv.load`, without copying the implementation nor editing `main.lua`.
7. **Debit after the spawn, not before.** A soldier or truck spawn can partially fail; an actor with
   `IsValid` and `bActorIsBeingDestroyed` does not count. Decide the quantity first, debit only what spawned and use
   an unchanged `combat.wave` to detect the wave that never opened.
