# Foxhole RTS roadmap

Public checklist with percentages: `PROGRESS.md`. This file is the detailed working roadmap.

## Current state — after the integrated batch of 10/11

**We are in phase 3: logistics MVP in a small region, not approved yet.**
**Logistics batch 2:** adjustments published, but validation interrupted by a crash
(PID4696/158 s after start). The last autosave at 60 s had bmat 40/salvage 0; the final
report was lost. Full cause pending; do not approve chain/medevac/hiring.
The live truck contract confirmed RWDVehicleMovementComponent, root/updated
VehicleCollision(Box), ignoreNonRoot=true and collision true→false when logistics turns on.
It does not prove road/support. No second restart; diagnosis continues offline.
Diagnosis narrowed the crash down to a list of PlayerState.UniqueId in the local
participants/voice flow. Empty bot IDs are a hypothesis; turning voice off does not protect
the whole loop. The NPC/controller contract still needs fixing without breaking movement
or fabricating an identity; there is no approved fix yet.
The CPU oracle ran the real producer/bridge/controller/helper with fixtures: voice
false or missing PlayerSaveGame still allow nulls to accumulate; a later non-null object
reproduces the read 0 at the crash RVA. It does not prove who produces them in the game.
bRunPhysicsWithNoController does not replace the locality of a possessed NPC either:
native gate and CPU oracle show a present Controller skips that flag.
Do not unpossess NPCs nor publish that shortcut; possession/GC/movement are still required.
A read-only probe of locality/PlayerState/troop roster and pool is prepared for
the next integrated batch; offline test PASS, not run in Unreal yet.
Native init of HeadlessLocalPlayer partially traced; the constructor alone
does not complete the contract. Without a proven reflected local executor, do not use
connection/login/RPC or blind LocalPlayer creation as a fix.
The historical entries below do not replace the current results:

- **Implemented:** refinery/factory deployment, manual collection, refining/production,
  trucks, depots, stock-based recruitment, forward bases, enemy economy,
  orders/groups/alerts and save. Transport is still straight/without collision, not by road.
- **Grenades integrated and tested:** Warden/Colonial use native classes/data;
  Owner/Instigator, fuse 4, damage, reset in flight, simultaneous classes, borrowed/swapped
  context and GC in flight passed in the batch. Friendly fire was observed (soldier 100→1).
  Native death of the soldier/thrower and long-run general stability not proven.
- **Collision failure proven:** Warden on the truck collision-on 900→788;
  collision-off 900→900. The fleet still turns collision off, so explosives are not a
  working integration of logistics interdiction. The local rifle is still pending;
  fictitious truck DPS was removed, do not restore it to cover up this hole.
- **Fresh chain failed:** 353 s/35 samples in the hex: salvage delivered 0/lost 110.02,
  bmat 40 without growth, resource truck not produced. Combat/resupply
  and the enemy chain happened (4 deliveries/15 shirts consumed), conservation PASS;
  defeat on wave 3. Logs record losses by death and "player order"; full
  cause not isolated yet. The old cycle with 120 delivered does not approve this match.
- **Truck death/loss gate also failed:** sixteen Colonial grenades
  left the actor at 850 HP; without death/lost cargo, do not credit cleanup as proof.

### Next batch, in order
**Offline candidate — convoy save:** eSnapshot observes the native death before
converting cargo into pending; sv.collect captures the wallet after the rewards
of those observations. Regression FAIL before/PASS after, battery of 15 tests PASS.
No publish/live validation yet; it does not solve persisting wounds.
Both snapshots refuse unknown HP; the save keeps the previous file without
invented loss. Persisting the collectors' manual cargo is also missing (unitData does not
keep m.col): reattach it to the worker and replan the physical delivery, never credit
the refinery just for loading the save.
**Adjustments published, no live approval:** isolated in the log that automatic medevac discarded cargo as
"player order". The fix keeps the cargo during evacuation and resumes the route after
healing; death/explicit orders still count as loss. Ten offline tests
PASS; published in the interrupted batch, it does not approve the fresh chain.
Automatic replacement also waits for an exit without an enemy inside the danger radius
already used by collection; it does not spend a shirt on the refusal. Without live approval, it does not prove
the cause of all deaths. The rebuild gate now refuses a missing record
instead of treating silence as success. Thirteen offline tests PASS.

1. Isolate why the fresh collection does not deliver and loses cargo/consumes shirts; fix it
   without extra money, fictitious delivery or removing combat to hide the failure.
2. Make trucks reachable by native impacts without destroying transport; road,
   obstacles/water/bridges remain part of the requirement, not a simple visual tweak.
3. Complete the local rifle/impact executor and native logistics death/loss;
   the mortar still being our own is debt. Do not change protections/debug to force a result.
   Offline research widened the trace callers and ruled out confusion with air/mount
   queries and presentation callbacks; still no proven rifle executor.
4. Repeat the integrated cycle with criteria for collection/refining/production/transport/
   consumption/cutting/expansion. More UI, polish and the world only after the core works.

Evidence: `data/trace_native_batch_integrated.txt` and
`data/trace_batch_mvp_integrated.txt`; strict checkers return 1 for the
unapproved gates. One publish/run, no crash observed; lab closed and
Steam preserved. Published source SHA256 ACB6ADFD3AE05828AB50C3D26CC3970673B09184E8FCD4BBCB3D010042CEFA64.

## Current direction — MVP first (10/10)

**Offline candidate 10/11 — native logistics HP:** `logi.syncHealth` observes the
actor's Health before transporting/delivering; HP 0/actor loss ends the trip
and counts the lost cargo once, without hiding/destroying the hull early.
Abstract ambush DPS and the mortar's own damage against vehicles removed.
Not delivered as complete combat: local rifle, grenade collision with trucks
and persisting wounds pending. Nine offline test scripts PASS;
no publish. Live gates accumulated in `NATIVE_BATCH.md`, one single future session.

**Explicit correction by the user:** a rough MVP does NOT authorize reinventing damage,
shots and vehicles that already exist in the game. Priority before calibrating ambushes:
trace native firing/projectile/impact/vehicle damage, prove local execution and
reuse the flow. Our own AI/orders/economy continue; the game's engine systems
must not be replaced by abstract DPS without demonstrating it is impossible.
The current logi.hit/logi.blast/convoyTick branch is implementation debt, not an accepted direction.

**Authorization 10/11:** reuse the client's local native configuration, keeping everything
offline. `ServerSettings` derives from `SaveGame`; the native constructor fills the
tweakables. First gate: `tools/probe_native_settings.lua` compares our own instance
with the traced defaults, without attaching it to the GameInstance nor applying damage.
Probe run with defaults/binding confirmed; Steam open/logged in by the user.
Do not create network/RPC, change a CDO, turn off a protection or invent formulas.

**Live gate 10/11:** defaults and binding PASS; ApplyDamage 45 Explosive on an exclusive truck
returned 31.5/HP 900→869 with settings freshly created/attached immediately,
versus 0/900 without settings. Restore and cleanup PASS. Generic damage proven; still missing:
anchored integration/lifetime, death and native firing. Trace `data/trace_damage_settings_fresh.txt`.
A later oracle (`data/trace_damage_native_repeated.txt`) proved Light/Heavy/Explosive
and HP down to 0 without a crash, with restore/cleanup. Wreck/full destruction and rifle not proven yet;
the test actor was removed by hand only in cleanup, do not credit that as a native death.
The user visually confirmed an explosion and something dropped in that test; record it as an
observed native visual reaction, with the drop's identity/content still unknown.
Static lifecycle: Health 0 triggers native death and SetLifeSpan 15 s; the hull still being valid
right away is expected. Do not call OnRep/death by hand to anticipate the timer.
**Local explosive proven:** SpawnActor BPGrenadeW and the native 20 s timer caused
Health 900→780 on the truck without manual ApplyDamage nor inventory/RPC. Restore/cleanup
PASS. Integration of launch/real fuse/attribution still pending; it is not proof of the rifle.

**New evidence:** 403 s cycle in CallumsCape with the mod's real waves/stocks:
120 salvage delivered/0 lost, truck rebuild, production/delivery at the base,
resupply in combat, 4 enemy deliveries/13 shirts consumed and defeat on wave 4
with only 3 workers alive. Conservation checked in 36 samples.
`tools/check_mvp_trace.py` checks `data/trace_mvp_cycle.txt`.
Convoy cutting, expansion/forward base in combat and victory not proven yet in that cycle.

The user asked to prove the concept, accepting a rough and unpolished implementation.
Prioritize a playable chain in the small region: resource -> refining -> factory -> transport ->
supply -> combat/expansion. Do not spend the next batch polishing arrival/animation.
Transport going through structures remains a functional limitation of the prototype, not proof of
physical road access. Crashes and visibility problems that prevent playing are not mere cosmetics.

### Postponed polish, does not block the MVP
- [ ] Workers reach an access/delivery point and then wait in a safe spot,
  instead of stopping on the track because they entered the 15 m delivery radius.
  Probes: data/trace_access_refinery.txt and data/trace_area_use_refinery.txt;
  native UseAreaBox/TransferLocation found, without integration nor native interaction.
- [ ] March/medevac of soldiers already stuck in old saves; do not confuse a unit without an order
  with a route failure, nor use the collection's success to declare general navigation solved.

This direction replaces the historical priorities below: working regional delivery/MVP
before polishing the workers' parking.

**Visual (10/10):** the horizontal line during movement disappeared in the user's test with VSync 1.
Published VSync in the RTS/restore on exit and the eye at the camera focus (including pause); a truck far
from the squad reappeared. Fixed the new match's origin to a base independent of the eye.
General visibility and stuck soldiers remain open: next priority is the workers' march/medevac
with the correct base, without extrapolating the 120 delivery of one route to general navigation.

**Latest update (10/10):** fine collection delivered 120/lost 0 unaided. Transactional rebuild
published: 900 HP actor at the factory and a single debit of 100 validated; a new match bought/reused the actor
after collection/refining without credits. Battery 29/29 PASS. Next: trucks on the real road; current
straight/no-collision transport does not approve a regional chain. Details at the top of MODLOG.md.

**Current priority (10/10):** the user asked to continue development and postpone crashes/the yellow effect.
Logistics batch v4.1 integrated into the source: 29/29 offline tests passed. Unreal validation still pending;
do not call it stable nor block new features with the old manual gate. Roads still pending.

**Validation of 10/10:** native base built, recruit at a supplied base and save v2 restored after a restart
and in the same load in HomeRegionW. Stock of 9 shirts/19 rifles kept; tests with lab credits,
not balance nor real transport. Infrastructure/wallet in the hex and the road network still need validation.

**Following batch of 10/10:** deployment of 1000 and restoring infrastructure/wallet passed in CallumsCape,
including a repeat without duplicating. Manual collection did NOT pass: 120 salvage collected, return blocked by
IndustrialWall03Snow31, zero delivered. Next work is the workers' navigation around the wall.
The region's network was exported (405 controls/431 segments), but surface/envelope/accesses remain pending.

**Collection navigation:** blind fallback removed only from that branch and refusal/braking validated in game.
Still need to find the real passage around the wall and complete delivery without the user's help.
Trace: data/trace_path_collection.txt. The planner's slope limit differs from the native one, but widening the limits alone did not solve it.

User's direction (2026-10-09): Foxhole's world is huge, so we start in a **small region**,
improve until it is good, and only then go to the whole world. In Foxhole **the war is the small part of the
machine**: what moves everything is logistics (resources, refining, factory, transport, front supply),
with vehicles, ships and planes. The RTS must have that at its center, not only squad combat.

## Phase 1 — Small front (now: HomeRegionW)
Squad combat, points, waves, assault, fortification, time, camera and tools for several fronts
(batches 1–11). Missing: the tests with the user's real input (`MANUAL_TEST.md`).

## Phase 2 — Study of the game's mechanics (from the game's own data)
**First reading done (2026-10-09): `MECHANICS_STUDY.md`.** HomeRegionW has fields, refineries,
a factory and trucks to prototype the chain, but it is the Wardens' training/boarding island,
not a war region. The lab does not replace validation on a `Maps/Master/*Hex` map.
Read at runtime (UE4SS) what Foxhole already defines, so the mod's numbers come from the game:
- **Items and costs:** item classes, what each crate contains, material cost (bmat, emat, rmat, fuel).
- **Production:** refinery, factory, ammunition factory, vehicle workshop, shipyard: recipes and times.
- **Resources:** salvage, component, sulfur, oil, coal fields; what the test map has.
- **Vehicles:** trucks (capacity, speed, fuel), armored cars, tanks, artillery.
- **Ships and planes:** which exist in the client version (the "Foxhole Airborne" screen points to planes), role of each one.
- **Structures:** forward base, depot, port, pillbox, bunker, trench: cost, health, function.
- **Maps:** which regions are in the client and which is a good "piece" of the world for phase 3.

## Principle: trace before reinventing (user's request, 2026-10-09)
The mod calls pieces of the game one by one and sometimes forgets one (e.g. a dead soldier that keeps "running" in place).
Before implementing or fixing a mechanic (skill: `skills/trace-before-reinvent`):
0. **Consult universal-modder:** skill `reverse-engineering` (section "Make it an oracle": record real traces
   and compare with what the mod does) and `um kb search`.
1. **Look for the high-level call** the game already uses (die, fire, reload, heal, build) and
   prefer it to assembling the effects by hand. Tools: the class's UFunction list (`ForEachFunction`),
   Ghidra for native code (project already set up, `ghidra-setup`).
2. **Trace the real flow once:** hook UE4SS onto the UFunctions of the classes involved (character,
   controller, weapon, AnimInstance) and record the order of calls and the values that change when the action
   really happens (the user does it with their character, or the game does it alone, like death).
3. **Write the contract:** the list of what the real flow changes (animation variables, velocity, replicated flags,
   effects, sounds). If the mod has to reinvent (because the game's path requires a server or inventory, which
   were left out of the offline mode), it fulfils this contract item by item.
4. **Test the contract:** a live test reads the same values after the mod's action and compares them with the trace.
Limit: the game has no soldier AI; our soldiers are "players" without a keyboard, so deciding will always
be the mod's job. What can be gained for free is what comes after the decision (animation, death, effects).

**First validated contract (batch 14): death.** `ApplyDamage` on the host zeroed HP without triggering the ragdoll;
`OnRep_Health` performs the native visual transition. The mod now stops movement, restores the original values and
removes the animation cache before that call. Before/after trace: `data/trace_death.txt`.

## Interface and visual feedback (user's requests, 2026-10-09)
Valid in any phase; it comes in when the matching mechanic is solid.
- **RTS visibility (request of 10/10):** solve soldiers, trucks and structures turning invisible.
  **Reinforced on 10/11 — pending:** the user still sees things vanishing with distance.
  Include a reproduction by distance/zoom, telling render distance (culling/LOD),
  LOS and occlusion apart; identify which actors vanish and confirm they are still alive/loaded.
  Criterion: relevant units and installations stay visible within the RTS range/zoom.
  A priority functional failure alongside transport: watching several fronts cannot depend on the proximity
  of the commander's pawn. Trace LOS, native hiding and camera occlusion separately; check actors
  alive/loaded and HiddenInGame before concluding absence. `rts.eyeTick` already follows the camera focus,
  but that did not solve all the reported disappearing. Validate the camera away from the group, focus on a convoy, high zoom, snow and installations at
  different angles; do not solve it with dots nor confuse the selection outline with normal visibility.
- **Line/flicker when moving the camera (report of 10/10):** the user describes a line across the middle of the screen,
  not drawn, similar to a rendering lag. Investigate over time; tearing is a hypothesis,
  not a diagnosis. Separate sync/presentation, camera update and LOS/post-processing.
  Compare still/active movement and VSync without permanently changing the user's settings.
- **Visible selection box:** today dragging selects an invisible area. Draw the rectangle while the button
  is held. Likely path: a semi-transparent `Border`/`Image` in the same widget as the panel (a clone of
  `CrosshairWidget_C` with a `CanvasPanel`), positioned by the mouse coordinates. Debug drawing
  (`DrawDebug*`) usually does not exist in a Shipping build.
- **Selection (batch 17):** bright yellow outline on the body ONLY when selected, no discs. The probe of
  `M_OccludedOutline` showed a fill of hidden parts, not a visible border; also kept only on
  selection. Body/head/hands/legs/equipment have separate CustomDepth. The full outline uses attached copies
  with MasterPose, without AI/physics; appearance approved, but native UE4SS crashes when extending to the parts are still NOT
  solved. Priority when resuming: stability/GC/reselection/death; then large selection/high zoom. A cooked shader is
  an alternative if the cost of the copies weighs. Do not expand the interface in this authorized wrap-up.
- **More interface, when it makes sense:** logistics panel (factory, depots, trucks) instead of a line of
  text; order icons; production bar; region minimap; clickable buttons for those who do not memorize keys.
  **Minimap confirmed by the user:** implement along with the UI's evolution, no priority in the current batch.

## Phase 3 — Logistics in one region
**In progress (2026-10-09).** Done: batch 12 (salvage-to-depot chain, consumption of shirts and ammunition,
trucks that can be destroyed) and batch 13 (enemy convoy that can be ambushed and shrinks the waves).
Batch 17 validated our chain in CallumsCapeHex: explicit deployment with budget/rollback and delivery
of crates at the base. Missing: trucks on the road (water/bridges/collision), more crate types, a more complete
enemy chain and balance/prolonged combat in the hex. Details at the top of `MODLOG.md`.

**Scope corrected by the user (2026-10-09):** HomeRegionW is a test bench, not phase 3's destination.
Before expanding the chain, recon a local `*Hex` map: loading/streaming, safe starting position,
terrain, roads, fields and structures really present. Having the `.umap` in the client does not prove that the whole
population of a war exists offline. Pick a region with a short chain after that inventory.
Discover the network from the loaded world, without reusing coordinates/cache from the lobby. If an installation
or access is missing, report the absence; do not consider a delivery done nor silently invent an installation.
**First local recon:** `data/trace_regions.txt`. Deadlands loaded with roads and installations
in ruins; CallumsCape has an active salvage field and ruins of a refinery/factories nearby, but no active trucks
in the probes. A candidate for the small chain **after** tracing rebuilding at the native sites and creating
real scenario vehicles. Do not conclude absence from a picture: LOS/occlusion can hide structures and vehicles.

**Batch 16 — partial contract:** `data/trace_rebuild.txt`. Fixed the costs schema:
refinery/factory 400 bmat each, TruckW 100. Spawning the active classes in the ruin's transformation validated
class/HP, but it is not a native completion of construction. A raw site came without a target; naive parking
hit a roof and an actor already being destroyed.

**Batch 17 — own deployment:** Alt+L reuses active structures or replaces ruins at the native sites,
with 1100 bmat of the scenario (400+400+3×100), Landscape parking validated and rollback without debit/clearing
the match. Repeating does not duplicate. In 65.21 s in the hex it produced three crates and delivered ammunition/shirts.
It is not a native call completing a site nor facilities; wallet/infrastructure do not persist in the save.
Road access still required before considering the scenario ready.

**Construction has two branches:** traditional factories/refineries are world structures at fixed sites;
facilities are industrial complexes built by players. Do not treat every factory as freely
buildable nor give every facility the same recipes as the town factory. Context:
[fixed and built structures](https://foxhole.wiki.gg/wiki/Structure) and
[official facilities devblog](https://www.foxholegame.com/post/devblog-foxhole-inferno).
Confirm classes, requirements and flow in the installed client before implementing; economy and AI remain
the mod's own, without server/RPC/inventory. Facility construction has not been implemented yet.

Replace the abstract "manpower" with a real, small chain:
1. **Collection:** soldiers or trucks take salvage from a field.
2. **Refining:** the refinery turns salvage into building material (bmat).
3. **Factory:** bmat becomes crates (rifle, ammunition, medical, grenade).
4. **Transport:** trucks take the crates from the base to the front by road (they can be ambushed).
5. **Consumption:** soldiers recruited and resupplied only where there are crates; a front without supply withers.
The enemy AI runs the same chain: cutting its road becomes strategy.

**Design decision (2026-10-09, delegated by the user to Claude): where soldiers come from.** In Foxhole each
soldier is a player who respawns at a spawn structure and spends shirts (Soldier Supplies) from its stock. The RTS
follows this model, without walking from the back of the map to the front (the map is too big):
- **Spawn points = structures:** the main base and **forward bases** built near the front (real class
  `ForwardBase1`, 300 bmat, stock 15, in `data/game_costs.txt`; other spawn classes only after tracing).
- **Recruiting spends the point's stock:** 1 shirt per soldier, plus the role's weapon (rifle for a rifleman etc.).
  It spawns at the supplied point nearest the cursor/front; without stock there, it refuses with a warning (no magic manpower).
  In a match with logistics the abstract manpower stops being the limit; it stays in Assault mode.
- **Logistics moves supply, not soldiers:** trucks take shirts and weapons to the forward bases; cutting a base's
  supply prevents reinforcing it. Troop transport is left for phase 4.
- **Villager-style workers (Age of Empires):** the match starts without a resource truck; soldiers without a rifle,
  spawned at the main base (1 shirt), collect salvage by hand; the factory produces the truck as an upgrade; losing the
  truck goes back to hand collection. The base keeps the number of workers in `CFG` by itself while there are shirts.

## Phase 4 — Vehicles and heavy weapons
Trucks driven by the mod's AI, armored cars, artillery with produced ammunition, forward base construction.

## Phase 5 — Several regions and the world
Two or more linked regions, real multiple fronts, ports and transport ships, planes; finally, a
campaign over the world map.

Each phase follows the project's flow: build in batches, test in the lab, record in `MODLOG.md`.
