# Native vehicle death — 2026-10-11

OFFLINE investigation, without channel/game, RPC, HP write, main.lua edit or calls by
offset. User's observation: the truck exploded and left something; object not identified.

## Flow proven statically

1. `SimVehicle` DamageableActor interface 0x140d81a00 debits the real Health. On reaching
   zero it calls virtual +0xd60, which in the native vtable 0x1436290f8 points to 0x140d970b0.
2. That lifecycle is already called automatically by the authoritative damage application:
   it handles DamageType flags, collision/effects, occupants/components and finishes
   in helper 0x140d6a8c0. Do not call the death callback by hand nor duplicate it.
3. The end at 0x140d973b7 loads the float constant **15.0** from 0x1433eb978 and passes it to
   helper 0x140d6a8c0. The helper calls virtual +0x378 at 0x140d6a9cb, pointing to
   Actor 0x1422e85e0. The reflected wrapper Engine.Actor.SetLifeSpan 0x1429faac0
   also calls virtual +0x378: the name is proven, not guessed from the timer.
4. SetLifeSpan writes InitialLifeSpan and registers a timer on the authority path.
   So the actor staying IsValid/not being destroyed right after HP 0 is consistent
   with a **transient hull and a native 15 s TTL**; it does not prove a missing callback.

## OnRep_Health

The SimVehicle.OnRep_Health wrapper 0x1412499a0 dispatches virtual +0xe88 → 0x140d83470,
which updates state and effects conditioned by mode/context; it calls helper 0x140d9a270.
This is a reflected local notification, not the damage applier nor a mandatory trigger
of the authoritative death. The TakeDamage path already invoked the death above.
Do not automatically carry the character's OnRep workaround over to the truck.

## Evidence and limits

Oracle PID12456 proved Health 900→873→840→0, without artificial HP, using native
types. The user confirmed explosion/drop. Cleanup removed the actor right after; **the 15 s TTL
was not observed live**, only identified statically. Unknown drop: do not
assume inventory/cargo/accounting loss; do not chase the native inventory system.

Optional later gate, in a suitable batch: exclusive actor, death by real damage,
observe GetLifeSpan, Health, class/position/Hidden and the destruction flag for >15 s WITHOUT
early cleanup; never write lifespan/Health nor call OnRep/death by hand.
Treat Health 0 as dead for cache/logic even if IsValid is still true.

Protected external disassembly: `D:/tools/foxhole-lab/vehicle-death-native-static.txt`.
Nothing integrated into the mod or announced as complete rifle/impact in this investigation.
