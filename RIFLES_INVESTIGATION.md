# Real rifles — evidence and next diagnosis

2026-10-07. **Not implemented yet.** Static analysis of the local copy, without
running the game in this round. Addresses below are VAs of the investigated build;
they are not a stable API. Decompilations stay outside this repository.

## Path confirmed in the local material

1. Reflected thunk `ServerTakePickup` at `0x14122a630`: validates through slot
   `+0xc18` and dispatches the implementation through slot `+0xc20`.
2. Slot `+0xc20` points to `0x140b0bb00`: checks the object and calls slot `+0x9d0`.
3. Slot `+0x9d0` points to `0x140b10e50`: reads `ItemInstance`, checks the activity
   state, another condition through the controller and the holders' capacity; on the
   success branch it calls `0x141225a20`, which dispatches a UFunction through ProcessEvent.
4. Therefore, on this path the flag `bIsLocalPlayerController` does not appear as a
   direct condition in the wrapper or in the examined body. This is consistent with the
   t_pk3 attempt having failed; it does not prove the flag is unused in called functions.
5. The activity test uses the byte at `+0x12e0`, identified in the reflection dump
   as `CharacterActivityStateInternal`; a non-zero value returns before the pickup
   path. Do not change this state blindly: observe first.

Local sources: `D:\tools\foxhole-lab\re-agent\d11\14122a630.c`,
`re-agent\d5\140b0bb00.c`, `decomp12\140b10e50.c`,
`re-agent\d1\141225a20.c`, `re-agent\props_SimCharacter.txt`, all under
`D:\tools\foxhole-lab` (maintainer's machine, not in the repository).

## Pitfall found in the RE tool

The local helper `re-agent/pe.py:vtable_of` follows the constructor's first call
and looks for a table in the base constructor. It returned `0x143528bf8` for both
SimCharacter and PlayerCharacter, but the PlayerCharacter constructor
`0x141201dc0` later writes **`0x143751bf8`** into `[rbx]`.

Confirmed by reading the instructions and the PE pointers with pefile/capstone, without
opening a process. In the two relevant slots (`+0x9d0`, `+0xc20`) the targets are
the same in both tables, so this difference **does not explain** the empty pickup.
Do not generalize the equality to other methods or to the Blueprint vtable
at runtime. The helper has not been fixed yet: check the final write by hand.

Another caution: pseudocode of the holder functions shows parameters that look
unused. Before concluding that the holder is ignored, check the assembly/prototype;
Ghidra can lose arguments with internal conventions/optimizations.

### Update: holder argument confirmed in the assembly

At `0x140a5c3e0`, RCX (first argument, the holder) is not overwritten before the
`call 0x140a622d0` at `0x140a5c43f`. RDX comes to point to the local result
and R8 to the item copy. Therefore the holder **is passed on**: the pseudocode that
showed `local_68` as the first argument was wrong at that point.
The return compares the resulting quantity with zero; it does not prove acquisition yet.
Confirmed by static reading with the pefile/capstone helper, not by execution.

Next information needed: the real state of the soldier's holders/activity.
Do not add another RPC breaker nor zero the activity without that measurement.

## Next test: measure before changing

`tools/probe_inventory.lua` observes each soldier: class,
HP, activity, controller, PlayerState, local flag, holders and item arrays.
It does not call the pickup RPC, does not create items and does not change state.

After confirming isolation and opening the copy with the local channel enabled:

1. Create a soldier with F6 and wait for it to settle.
2. Publish the diagnosis to the channel through a temporary copy and rename, to avoid
   reading a partially written file:

   ```powershell
   # Run only when there is no other pending command in the channel.
   $lab = 'D:\tools\foxhole-lab'
   if (Test-Path "$lab\cmd.lua") { throw 'Previous command pending' }
   Copy-Item tools\probe_inventory.lua "$lab\probe.pending"
   Move-Item -LiteralPath "$lab\probe.pending" -Destination "$lab\cmd.lua"
   ```

3. Read `cmd.out` only after a new write that ends with this probe's `FIM` line.
   Old output does not count as success. A single operator should use the channel.
4. If the activity is not zero or required objects are missing, investigate
   that precondition before trying more RPC flags/hooks.
5. After any future acquisition attempt, measure **inventory and equipment**,
   not just a return without exception or the pickup disappearing.

Probe syntax checked offline; in-game execution and results still pending.
