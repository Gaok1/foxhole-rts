# ECONOMIA (economy) — isolated proposal, 2026-10-09

Not integrated. `economy.lua` is a pure module with three new recipes and accounting; it does not change main.lua, does not access UE4SS/RPC/inventory, does not create free starting material. `test_economy.py` runs the real Lua and compares schema/costs/content/time with the extracted data: PASS.

## Real recipes

| Own product | Native CodeName | Cost per crate | Content | Native time |
|---|---|---|---|---|
| rifle | RifleW | Cloth 100 | 20 rifles | 70 s |
| grenade | GrenadeW | Cloth 100 + Explosive 40 | 20 grenades | 100 s |
| medical | Bandages | Cloth 80 | 50 bandages | 40 s |

Source: `data/game_costs.txt`, lines 74, 12, 66. MECHANICS_STUDY maps Cloth=bmat, Wood=rmat, Explosive=explosive powder. FirstAidKit (Cloth 60/10/35 s) and TraumaKit (Cloth 80/10/50 s) are distinct tools, they do not replace the consumable bandage. BloodPlasma exists, but reviving is not implemented. Do not add tool consumption for each heal.

**Explicit block:** the current chain produces only bmat, not Explosive. Grenades stay impossible until ECONOMIA/RE maps own explosive production with explicit cost/flow and infrastructure. The module refuses start for lack of Explosive before debiting Cloth. Never cut a resource from the recipe or pretend bmat pays for everything. Do not call this a complete integrated chain.

## Proposed integration contract

- `factory.materials`: native names, integer values; reserve all costs atomically at start. One job per factory; progress receives a simulated dt, already adjusted for pause/speed by the caller. Explicit cancellation refunds a single time; destruction must not call cancellation automatically (loss is a recorded decision).
- `factory.boxes` and `truck.cargo.boxes`: closed crates. `depot.stock`: units. Delivery only at an allied depot, a single time; a lost destination keeps the cargo for a return to the factory. Destruction returns a loss record, never a crate to stock.
- The current ammo/shirts stocks have separate accounting; integration must preserve them and genericize logi.nextKind/need/load/deliver/cyclePrio/HUD/snapshot. **Do not just add recipes and expect hardcoded functions to work.** The persistence schema must cover reserved material, crates, units, cargo/losses and the job.
- Rifles: use 1 unit when recruiting a rifleman at the front, besides the current 1 shirt; reserve the resource before spawning and give it back if the spawn fails. Other roles cannot use RifleW indiscriminately. The mod's weapon stays an own mesh; do not chase the real inventory.
- Grenade: transfer units from the depot to `m.grenades`; in throwGrenade consume 1 only when the order is valid and the strike/projectile is accepted. Today the cooldown grants infinite grenades. Canceled fire does not consume; death loses the soldier's load.
- Medic: supply `m.bandages`; medicTick spends 1 per effective treatment cycle of a wounded ally, never on a full/invalid/out-of-range target. This per-cycle consumption is **the mod's own rule**, not a proven trace of native healing; pace/balance gate needed. Do not deduct one bandage per frame. Passive healing at a point/post needs an explicit material policy, otherwise it bypasses medic scarcity.
- E.consume checks all costs before debiting; the caller only runs the effect after the reservation and must revert if the application/spawn fails. The module performs no UE effect nor claims a verified engine transaction.

## Tests / gates

Offline PASS: fail-closed recipe parsing, missing explosive without partial debit, busy factory, production only on time/once, single cancellation/refund, cargo/capacity, enemy destination, return, death/loss, atomic consumption, invalid zero costs, invalid dt and conservation. Uses zero new dependencies (lupa already used in the repo).

Pending: complete integration patch; tests of the real spawn/throwGrenade/medicTick effects, conservation with multiple soldiers, restore from save and UI; lab gate of the chain without fictitious starting stock, transport cut -> scarcity -> recovery, destroyed cargo, production and combat effect. Visual/input/balance gate not run. No new key proposed.

Universal-modder consulted at the start (Foxhole note/oracles/Unreal); the coordinator records the Gotcha: GrenadeW requires Explosive besides Cloth; consumable Bandages is not FirstAidKit; a new recipe does not work by just editing CFG.LOGI because transport/depot/priority/save are hardcoded to ammo/shirts. No concurrent writing to the shared note.

## Complete integration proposed — second delivery

`build_patch.py` transforms the **current source** in memory (unique anchors, fail-closed); it generates `economy_integrated.patch`. It does not apply to main.lua. `functions.lua` and `save.lua` feed the generator, they are not a second runtime/stock. The earlier `economy.lua` is a reference prototype, **it must not be loaded together** with the integration: no accounting duplication.

### Effective flows of the candidate

- CFG.LOGI includes four products ammo/shirts/rifle/medical. Rifle and bandage follow exactly the audited recipe; grenade has no recipe/production/priority because Explosive is missing. Production uses the existing fac/job/bmat; the factory deducts the cost at start and only produces the crate on completion.
- nextKind, needs, pickDest, cargo/capacity, delivery and return genericized. Content is crates in fac/cargo; product units in depot. Ammo keeps its old contract of supply crate/reloads, without pretending 40 native RifleAmmo equal the shots used by the mod. Demands rifle 4 and bandages 20 are **the mod's own** targets, not game costs.
- The need for the new products uses ceil(missing/units), without the legacy -0.5: demanding 20 bandages with a crate of 50 requires 1 crate, not zero. ammo/shirts keep the previous rule.
- Shift+L includes rifles/bandages; no new key. The HUD keeps the old/enemy text and adds the new stocks/cargo. This needs to reconcile `extraHud` with the INTERFACE multiline patch; do not inadvertently replace the panel with an earlier version.
- Manual recruiting of a **rifle** requires 1 rifle + 1 shirt; other roles keep consuming only a shirt (they do not use RifleW improperly). A failed spawn debits nothing; success debits on the synchronous game thread. The original fallback message "sem camisas" must also be adjusted by the integrator when what is missing is a rifle.
- An allied medic, with logistics active, only treats a wounded unit in range if there is an allied depot with bandages within POINT_RADIUS of the medic. Debit of 1 after an effective Health increase, respecting the cooldown. Enemy healing and matches without logistics keep the earlier behavior. There is no item userdata/inventory nor an invisible pocket duplicating bandages.
- **Explicitly limited policy:** passive healing at points/posts is still free, unlike the active medic; spawning of the starting composition/reward/F6 is free, does not go through recruit and does not consume a rifle. So this delivery does not claim "every reinforcement and every heal depends on stock". Widening that requires changing the start/waves/medevac policy and balance, not silently truncating the tutorial/match.
- An enemy capture zeroes all depot products; a destroyed truck loses the cargo of all products with no fictitious return/delivery.

### Save/restore needed by the accounting

Schema logi.version=2; accepts legacy without a version (new stocks zero). The snapshot includes fac/base/new points, the already debited job and remaining/total time, the trucks' state/HP/cargo/destination depot/salvage/wait/rebuild. Copied tables, no alias/userdata/address.

Complete pre-validation of numbers/recipe/priority/state/capacity/destination happens **before** ready/start/reset. Negative data, invalid cargo or an unknown version keep the current state. An unavailable world preflight too. Restore replaces data, it does not add; repeating restore does not duplicate crates. A lost destination keeps a closed crate on the truck in returnCargo; the factory only receives it after an arrival confirmed by the driver. A resumed job does not debit bmat again. Infrastructure is NOT rebuilt/persisted here; trucks use the start parking, not the old XY/path. Destination IDs are point indexes, like the current save; a map/points change needs the regional schema of the PERSISTENCIA task.

**Important transactional limit:** the tests prove pre-validation and preflight refusal, not rollback of a native exception after start/reset. ready/start loaded/checked the world in the existing contract; a native error/interruption in an engine spawn remains a gate. Do not present Lua validation as an engine transaction.

### Reproduce without applying

From the repository root:

```powershell
$env:PYTHONPATH='D:/tools/pylibs'
python data/parallel/economy/build_patch.py
python data/parallel/economy/test_integration.py
python data/parallel/economy/test_existing.py
```

All PASS in this delivery. Test_integracao runs **the whole candidate** main.lua chunk and replaces only engine boundaries (drive/spawn/ready/start) with spies; it calls the real functions of production, truckStep, recruit, medicTick, hit, snapshot/validateSave/restore. The whole test_orders regression run against the in-memory candidate also PASS.

Remaining gates: sequential application + panel reconciliation; globals/syntax; live test recipe -> production -> transport -> recruited rifle/treated bandage without artificial stocks; scarcity/cut/recovery contrast; save in the middle of production and cargo; engine failure after preflight; capture/new map; readability and balance. Update README/MANUAL_TEST for rifle/bandage priority and active medic/recruiting supply. Task stays [ . ].

## Mandatory physical return fix (coordinator's review)

The earlier instant return was removed from the candidate, both in truckStep and restore. The contract is the same as `data/parallel/roads/RETURN_PATCH.lua`:

- lost destination -> `tr.state="returnCargo"`, `tr.dest=logi.factory`, the cargo stays on the truck; invalidates route/routeDest/pathJob;
- the returnCargo state calls the driver to the factory; a false return (no route/blocked/still driving) keeps everything with no credit;
- only a true return (arrival **physically confirmed**) credits the crates to fac and clears cargo/dest/state; nothing in restore moves credit;
- snapshot/validateSave/restore keep returnCargo/cargo. `dest=-1` is a **serialized sentinel for the factory**, not an address. Base=0, points=legacy index >0. It is not a regional guarantee/stable IDs; reconciliation with CLAUDE_PERSISTENCIA is mandatory.

Updated tests: destination loss in the tick without credit; driver false keeps cargo/fac 0; arrival true returns once; save with a lost destination restores returnCargo/fac 0; save/restore during the return continues with cargo; only the later arrival returns. Integration suite and candidate test_orders PASS.

**Gate that cannot be bypassed:** the main's current driver still drives straight. Do not apply this patch as safe transport without integrating the ESTRADAS driver with route/sweep/arrival; the tests only replace the driver with controlled false/true. Do not use a timeout or lack of a route as arrival. No CLAUDE code/block was modified.
