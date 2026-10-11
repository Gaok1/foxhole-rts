# Foxhole RTS — local prototype v0.9 (fully offline)

Lua mod developed with AI assistance, using UE4SS and Universal Modder.
Characters and effects belong to the game and are not included here.
In-game texts (alerts, panel, key help) are still in Portuguese; they are quoted here as they appear.

**Logistics batch v4.1 in development:** manual collection, forward bases, wider economy, enemy chain and save v2. Offline tests passed; base creation/recruitment and save/restore passed in HomeRegionW. Transport, hex and balance still pending. The key crash and the flicker remain open by the user's decision.

## Requirements and installation in the lab

- Your own copy of Foxhole; build tested previously: Steam 25730371 / UE 4.24.
- Steam open and authenticated; do not modify ownership checks.
- A separate copy of the game with network isolation checked before running.
- UE4SS already configured for that copy and engine version.
- Back up `%LOCALAPPDATA%\Foxhole` before each modified launch.

With the process closed, copy `FoxholeRTS` to
`War\Binaries\Win64\ue4ss\Mods` **of the lab copy**. `enabled.txt`
enables the mod. Never install it on the official client nor connect the copy to the official
servers. There is no guarantee of compatibility or account safety.
Do not distribute the game copy, its DLLs or extracted assets.

F9 opens the local session; F10 turns on the RTS camera. The autostart and the command channel
are optional development features, enabled by `FoxholeRTS/autostart.txt`;
the channel runs arbitrary local Lua, it is not a sandbox.

**Quick start:** with RTS mode on, Shift+F6 starts a match (squad of 6, three control
points, automatic waves). Capture the points, recruit with Ctrl+1–4 and win 10 waves — or hold the three points for 90 s. F5 shows the keys.
In a hex without an active chain, Alt+L tries the initial deployment described in **Logistics**, then Shift+F6.

## Controls

| Key | Action |
|---|---|
| F6 | Create a free mixed squad (sandbox; up to 12) |
| Ctrl+1 / 2 / 3 / 4 / 0 | Recruit rifleman (20) / machine gunner (35) / sniper (45) / medic (30) / officer (40, only one) with manpower in Assault; in logistics it uses shirts and, for the rifleman, a rifle |
| 1–5 / 0 | Selects the group (two quick taps = the camera goes to it) / all |
| Alt+1–5 | Puts the selected soldiers in the group (one group per front; each soldier spawns in 1 or 2) |
| Space | Camera goes to the latest alert; again (within 4 s) = previous alerts |
| Q / E | Camera on the previous / next control point |
| L | The next supply truck goes to the depot under the cursor (base or one of your points); outside them = automatic |
| Shift+L | Factory priority: automatic → ammunition → shirts → rifles → bandages |
| Ctrl+L | Camera goes through the factory, refinery, salvage field and trucks |
| Alt+L | Deploy refinery/factory at the native sites and the missing trucks, with the scenario's starting budget |
| Left button | Select soldier; drag = box; Shift adds (bright yellow outline = selected) |
| Right button / F7 | Move the selected soldiers in formation; over an enemy = attack that target |
| Shift+right button / Shift+F7 | Queue the destination (they go through the points in sequence) |
| Ctrl+right button / Ctrl+F7 | Area suppressive fire for 20 s (without line of sight it only suppresses; uses ammunition) |
| K | Raise a concrete barrier under the cursor (15 manpower, up to 30; low cover; F11 removes) |
| Ctrl+5 | Mortar fire under the cursor (40 manpower, 20 s reload; 3 shells after 2.5 s; only hurt the enemy) |
| J | Create a control point under the cursor (up to 5) |
| Home | Retreat: the selected soldiers run to your nearest point (or to the commander) without shooting and take half the hits |
| End | Hold position: they stop and do not look for cover; they keep shooting; a new order releases them |
| Shift+F6 | New match: clears everything, squad of 6, automatic waves and three control points |
| Alt+F6 | Assault: the enemy starts owning the three points, dug in and with wire; take them all |
| Ctrl+F6 | Continue the saved match (saved automatically every 30 s during automatic waves) |
| F4 / Shift+F4 | Create a wave / toggle automatic waves |
| F11 | Clear soldiers, enemies, bodies, barriers and points |
| F2 / WASD or arrows / mouse wheel or PageUp, PageDown | Center / pan / zoom |
| Pause or Ctrl+Space | Tactical pause: the game stops, but camera, selection and orders work |
| Insert | Speed 1x / 2x / 3x (turning the RTS off goes back to 1x) |
| F3 | Toggle edge pan (off by default) |
| F5 | Show/hide the key help on screen (it appears by itself for 40 s when the RTS turns on) and log the status |
| Shift+F5 | Difficulty: easy / normal / hard (enemy accuracy, wave size, manpower); saved in `settings.txt` |
| Ctrl+6 | Supply crate under the cursor (−25): reloads ammunition within 4.5 m for 60 s (max. 3) |
| Ctrl+7 | Trench under the cursor (−20): up to 4 soldiers inside; shots hit 60% less and suppress half as much (grenade and mortar do not) |
| Ctrl+8 | First aid post under the cursor (−30, up to 2): your soldiers within 6 m, out of heavy fire, heal 4 HP/s and stop bleeding |
| Ctrl+9 | Barbed wire under the cursor (−10, up to 10): a 6 m strip across the threat; whoever crosses (both sides) walks at 35% |

The keys avoid the game's default mappings (B = build, H = callouts, F8 = hide interface,
Shift+1–7 = admin commands). 1–5, 0, Space, Q and E are soldier actions in the game (weapon, gestures, climb,
mount, use), with no effect in the RTS, which turns off the commander's input.
In RTS mode the commander's input is off, so the left click (Fire in the game) does not make it attack.

## Classes and economy

The manpower costs in the table apply in Assault/outside logistics. In logistics, recruitment spends the stock of the spawn base, not these costs.

With RTS mode on, a panel in the top-left corner shows manpower, squad (selected),
wave, enemies, kills, losses and the countdown to the next automatic wave.

| Class | Cost | Range | Shot every | Damage | Base accuracy | Ammo | Notes |
|---|---|---|---|---|---|---|---|
| Rifleman | 20 | 22 m | 1.6 s | 34 | 60% | 40 | — |
| Machine gunner | 35 | 26 m | 0.35 s | 14 | 30% | 150 | walks at 75%; only fires when set up (still for 1 s): +30% hit, +50% suppression |
| Sniper | 45 | 40 m | 3.5 s | 70 | 85% | 15 | — |
| Medic | 30 | 15 m | 2 s | 20 | 40% | 24 | heals 12 HP and stops the bleeding of the most wounded within ≤3.5 m every 1.5 s; goes to wounded within ≤12 m |
| Officer | 40 | 18 m | 1.8 s | 25 | 50% | 24 | only one per squad; allies within ≤10 m hit 15% more and recover from suppression 1.8× faster; banner above the head |

**Ammunition:** each of your soldiers carries the ammunition in the table and stops shooting when it runs out (alert and "SEM MUNIÇÃO" in the panel; below 25%, "munição baixa" in the panel and a small ammo box above the head). Inside one of your points or within 5 m of the base (where the commander was when the RTS turned on; F2 centers on it), it reloads 15% per second. The enemy has no ammunition limit.

Riflemen try to throw a grenade (18 s reload) at low cover, up to 18 m and within
the speed limits of the game's data. **Offline batch of 10/11, not published yet:**
projectile BPGrenadeW (Warden) or Grenade_C (Colonial), each faction's data,
real 4 s fuse, native ballistics/collision/damage/effects; no teleported
arc or our own grenade damage. If the solver/spawn refuses, it does not spend the reload and
normal fire continues. Local context anchored until the projectiles finish; a reset cancels
only our own projectiles. Team/attribution/damage on soldiers and logistics integration
wait for the live batch. Rifle shots and the mortar still use our own prototype — explicit
debt, not equivalent to complete native combat.
**Death:** allies and enemies stop and fall with the game's own ragdoll. The mod removes the body from the
animation control before triggering the native death; the body stays on the ground for 20 s and is then removed (it does not keep running).
Veterancy: every 2 kills the soldier goes up one level (up to 3), with +10% accuracy per level; it also applies to the enemy.
Accuracy drops to half at maximum range. Every shot suppresses the target (the MG faster): a suppressed soldier misses more and walks slowly,
and a heavily suppressed enemy gets pinned in place. A target behind low cover (wall, barrier) takes half the hits.
Soldiers standing without an order (allies and enemies) look for cover within 4 m by themselves when exposed; a trench with a free slot within 4.5 m is preferred. Moving into a trench fits 4 in it and the rest in a line behind. Manpower starts at 60,
regenerates 1/s plus 0.5/s per control point of yours (max. 200) and gives +8 per kill and +30 per wave eliminated.
In automatic waves, whoever eliminates the 10th wave or holds all control points for 90 s in a row wins; defeat happens with no soldiers and no manpower
for a rifleman, or when the enemy owns all control points. Enemy accuracy grows 4% per wave (up to +50%), and each wave brings one more enemy for every ~2.5 of your soldiers (up to 16 per wave).

## Evacuation of the wounded

One of your soldiers below 30% health, standing and without an order from you for 15 s, retreats by itself (without shooting, like Home) to
the nearest first aid post; without a post, to one of your points; without a point, to the medic. At 80% it is released.
Any order from you cancels the evacuation.

## Enemy morale

A wave of 6 or more that drops to a quarter of its size breaks: the survivors flee back the way they came
(without shooting and taking half the hits) and vanish on arrival, without counting as kills. The death of an enemy officer
also shakes (suppresses) those near him. In Assault the garrisons do not flee.

## Enemy officer and enemy machine gun

From wave 3, each wave arrives with an officer (green banner above the head) who gives the enemies near
him the same aura as your officer; killing him gives +20 manpower. In Assault, the garrison of the front point
has an officer. An enemy machine gun that loses sight of you keeps suppressing for 8 s the place where it last
saw you: hiding behind a wall is not enough, you need to leave the area or flank it.

## Enemy mortar

From wave 4, about 40% of waves arrive as a pincer (two groups from different sides). From wave 4 the enemy fires mortar (2 shells, 3 s warning with sound and an orange ring) at
groups of 3 or more of your soldiers. Soldiers under the warning run out of the ring by themselves, except
those holding position (End) or heavily suppressed: those take the fire.

## Control points

Turning on automatic waves (Shift+F4) without points creates three around the squad (front and flanks),
on flat ground free of vehicles; J creates others under the cursor. Each point is an orange dotted ring
5 m in radius with the owner's banner in the center (blue = yours, green = enemy, none = neutral).

- Capture: have soldiers inside the ring without enemies. One soldier takes 10 s from neutral to owner; up to three speed it up.
  Both sides inside = contested (stops). To take the point from its owner you first need to bring it back to neutral.
- Each of your points gives +0.5 manpower per second.
- On taking a point, the enemy digs a free trench in its center; it serves whoever is inside, so retaking it calls for a grenade or mortar.
  It also lays a strip of wire 9 m from the center, on your squad's side: go around it or cross under suppressive fire.
- Your point is a first aid post and a depot: soldiers inside the ring reload 15% of their ammunition per second and, without suppression, recover 2 HP/s.
- Enemies out of combat march to the nearest point they do not own yet and hold it.
- An enemy point far from your squad (>15 m) becomes the entry of the next waves: retake it to push them away.
- In Assault, recruiting (Ctrl+1..4) inside one of your points makes the soldier spawn there. In logistics, only the main base or a supplied forward base is a recruitment site.
- The panel shows `pontos 1/3 [A+ Bx Co]`: `+` yours, `x` enemy, `o` neutral (with % during capture).

## Assault (Alt+F6)

Another way to play: you start with 8 soldiers and 120 manpower, and the enemy already owns the three points
(26–36 m ahead and on the flanks), each with a trench, a strip of wire on your side and 4 garrison
soldiers. There are no waves: the enemy only gets reinforcements from the income of the points it still holds, and each point
you take triggers a counterattack within a few seconds. You win by taking the three points with no enemy left
alive, or by holding them for 60 s. You lose with no soldiers and no manpower for a rifleman. Area
suppressive fire, grenades and mortar are the tools to get the garrison out of the trench.

## Save and continue

**Integrated validation of 10/11:** native grenades per faction, Owner/Instigator,
reset/contexts and GC in flight passed in a single batch. Friendly fire happened.
A truck without collision took no damage; the fleet stays that way, so native
interdiction is not delivered yet. The fresh chain failed (0 salvage delivered, ~110
lost, no resource truck), despite combat/resupply. Experimental
build; details and next priority in the ROADMAP. The offline notes below are historical.

**Offline candidate of 10/11:** truck HP comes from the game's actor and appears in the
panel. HP 0 or an invalid actor stops transport and records the cargo loss once;
the engine keeps explosion/hull/TTL. Removed the abstract ambush DPS and our own
mortar damage against trucks. **Rifles do not cut convoys yet in this
candidate**: native local executor pending; grenades against vehicles also need
the collision gate. No publish/integrated validation yet. An old save does not apply
fictitious HP to the actor; native wounds are not persisted for now.

Save **v2**, every 30 s during automatic waves: combat state, stocks/production/collection, paid infrastructure/wallet, enemy chain and forward bases. No actor addresses; routes/actions in flight do not persist. The workers' manual cargo is discarded on continue.

Ctrl+F6 validates file/world/positions before wiping the current match. Paid infrastructure is rebuilt without a new debit, all or nothing. An invalid save refuses while keeping the state; an invalid enemy section discards only itself and warns that the scenario stock restarts. An incomplete restore suspends autosave.

It writes a temporary file with a reread and a backup; recovery tries save, tmp, bak. Old saves are accepted; the previous version of the mod does not accept new fields. Victory/defeat clear the files. Save/restore of forward bases and stocks passed in HomeRegionW. In CallumsCape, paid infrastructure and wallet were restored after a restart, with no new debit or duplication when repeating.

## Area suppressive fire

Ctrl+right button (or Ctrl+F7) makes the selected soldiers fire for 20 s into a 4.5 m circle under the cursor;
medics stay out. Those out of range walk into it. Without line of sight there is no damage: each shot suppresses
every enemy inside the circle (a set-up MG suppresses more), which pins whoever is behind a wall or in a
trench while another group flanks. An enemy that shows up in sight takes normal fire. Uses ammunition;
any new order cancels it. A ring of orange dots marks the circle while the order lasts.

## Enemy reinforcements

Each point the enemy holds gives it manpower (0.6/s). During a wave, every 20 s, it sends
2 or 3 reinforcements (up to 6 per wave), which appear behind its point nearest your squad. The panel shows
"reforço inimigo N". Retaking the points cuts that income.

## Animation

Soldiers hold the weapon with both hands and, standing still in combat, bring the rifle to the shoulder and aim at the target,
with recoil on each shot. When walking, they carry the weapon at rest.
Inside a trench, or under heavy fire, they crouch; when retreating (Home), they run hunched. The medic
plays the first aid animation when healing, and the rifleman the throwing one when throwing a grenade.
Each class fires with the sound of its own weapon from the game, and the two sides sound different (Warden rifle x Colonial
carbine, machine guns, sniper rifles, pistol).
Your wounded soldiers show a health bar above the head (green, yellow below 60%, red below
30%), which disappears when they recover. Enemies have no bar: it would reveal who the game hides for lack of vision.

The warning "Falha ao baixar informações do servidor" (failed to download server information) in the menu comes from the game itself (the lab copy does not
reach the network on purpose) and cannot be closed by the mod; the autostart leaves the menu in 2 s.

## Visuals with the high camera

The game was made for a soldier's low camera. With the RTS on, the mod draws small objects and shadows
farther away (`r.ViewDistanceScale 3`, `r.Shadow.DistanceScale 2.5`) and turns off the game's line-of-sight shading
(the dark bands that radiated from the "eye"). The zoom goes up to 160 m, to watch several fronts: the
draw distance grows with height (`r.ViewDistanceScale` = height / 20 m, at least 3). Turning the RTS off
restores these changes. VSync stays on in the RTS to avoid the horizontal tear observed when moving
the camera; turning the mode off restores the previous value, without writing the game's settings.

## Logistics

**New integrated batch; live validation pending.** Our own offline systems, without the game's inventory/RPC.

- **Alt+L:** explicit deployment at the native sites, now with a wallet of **1000 bmat**: refinery 400 + factory 400 + two supply trucks at 100 each. Rollback and idempotence kept. Ruins are not active installations.
- **Start (Shift+F6):** three workers without rifles collect salvage on foot; no resource truck spawns. The refinery converts 2 salvage into 1 bmat; the factory starts with 40 bmat and reserves 100 to produce/replace the resource truck. Losing that truck reactivates manual collection.
- **CallumsCape:** the old rehearsals got stuck on the wall/rocks. With fine sampling, three workers delivered 120 salvage with no losses nor intervention. That approves this route, not the whole chain or any terrain.
- Collection refuses the straight line when the search fails, brakes and shows **sem rota** (no route). Attempts on the same stretch do not renew the deadline. It looks for a reachable arrival inside the service area.
- Experimental micro-rescue: after four seconds without moving, it tries 80/160 cm with swept collision; an exceptional teleport only to a destination with a free capsule when the origin is already penetrating. It gives no resources nor extends the trip. Passed offline, but **did not rescue the stuck ones in the real rehearsal**.
- The collection route samples the terrain every 50 cm so it does not skip narrow rocks during simplification. In the CallumsCape rehearsal, the three delivered 120 salvage without losses/rescue. The whole chain is not approved yet: rebuilding the resource truck left an active state without a physical actor.
- Transactional rebuild: looks for a safe spot at the factory and requires an intact 900 HP actor before charging 100 bmat/activating. A failure keeps the stock/dead state and retries in 5 s. Battery 29/29 PASS; a probe in the hex created a real actor and confirmed a single debit. Transport by road is still pending.
- **Workers:** a replacement costs a shirt from the base; without shirts there is no magic replacement. They do not count toward wave size nor toward the combat squad's center.
- **Production:** ammunition, shirts, rifles and bandages, with our own recipes based on the extracted data. Grenades require explosive and were not added as a free recipe. Shift+L toggles priority; stock/reserve/production appear in the panel.
- **Transport:** two trucks supply depots; L points the destination. Cargo on a return is only credited on arrival, not when losing the destination. Transport still straight/without collision; road network not integrated. Do not consider the regional scenario ready.
- **Recruitment:** spawns at the main base or at a supplied forward base; costs a shirt and, for the rifleman, a rifle. A common control point does not reinforce by default. In Assault it stays manpower.
- **Forward bases (Shift+J):** on an eligible point of yours, the first tap shows site/cost; a second within 4 s confirms 300 bmat from the factory. Up to 3 bases, class ForwardBase1. Position/terrain/actor require validation. Structure, stock and loss affect reinforcements; spawn/flow in the engine still to be validated.
- **Enemy chain:** the rear produces, trucks take supply to the front and waves consume stock; cutting transport reduces reinforcements. There is a scenario troop floor, explicit in the panel/configuration; it is not an absolute block for lack of cargo.

HomeRegionW is a test bench. The destination is a short chain in CallumsCapeHex; loading map/terrain/installations does not prove balance, a passable road or visibility from the camera. Facilities not implemented.

## Several fronts

- **Selection at any zoom:** only selected allied soldiers get a bright yellow outline,
  following position and animation. Hidden parts get a yellow fill from the native post-process.
  Deselecting, dying or leaving the RTS removes both. No circle at the feet nor dots on units/trucks.
  Includes coat, head, helmet, hands, legs, backpack and weapon. It shares the pose with four copies per visible
  part (28 actors on the current soldier). **Experimental:** appearance approved by the user, but there were native
  UE4SS crashes after extending to the parts; stability/GC/reselection/death and large selection still pending.
  The resumed work added protections for pawn/clone/camera being destroyed and an invalid source, including the
  CustomDepth cleanup. The offline regression passed; it neither identifies nor certifies the fix of the native crashes.
  Integrated optimization: one complete native transform per copy replaces three setters; rotation conversion
  once per part. Geometric equivalence verified offline and by a live oracle. In a clean load, six
  selected kept 168 copies with stratTick initially at 7.91 ms/frame (before 16.72 ms);
  after GC/reselection a new window measured 16.40 ms. Sustained gain not demonstrated yet.
  GC and reselection passed functionally; it is not a prolonged certification nor an FPS/rendering benchmark.
  The next load crashed in UE4SS with a Registry error; guards/optimizations did not solve stability.
  Registering the animation hook now allows retrying after an initial failure; an independent Lua fix,
  without evidence that it explains the native crash.
  Resumed on 10/10: a clean repeat with six selected/168 copies passed 195 s;
  a control without selection passed 201 s. The old cause was neither reproduced nor isolated;
  this does not release the candidate logistics batch. The outline measured ~11–12 ms/frame in stratTick,
  versus ~0.5 ms without selection. Evidence in `data/parallel/stability/RESUME_20261010.md`.
  Another clean load completed 620 s with six selected/168 copies, followed by GC/death/recreation
  and another 186 s without an observed crash. Real input and the old cause remain pending;
  ten-minute manual gate in `MANUAL_TEST.md`.
  **Manual gate failed on 10/10:** fatal error during the number keys test, after a group 1 log line.
  The build is still experimental; the automatic rehearsals did not cover that failure with real interaction.
  Diagnostic variant: keys now go into a Lua queue drained by the persistent loop
  before the authority gate (F9/F10 still available in the menu). It avoids creating an
  ExecuteInGameThread callback per press; FIFO/errors/reentrancy passed offline. It is not a certified
  fix of the crash: fast real input and UE4SS synchronization still need validation.
  100 de/reselection cycles and 20 deaths/recreations also passed; GC left 168 tracked copies
  and zero actors being destroyed. The component cache of a deselected live unit
  stays on purpose to clear the CustomDepth the game reactivates; on death it is removed.
  See `data/trace_selection.txt`. If it gets heavy, the next path is an edge shader, not going back to discs.
- **Front alerts:** your point under attack, point lost, wave coming and casualty go into a queue (up to 8) with the
  place; the panel shows "! N alertas (Espaço)". Space takes the camera to the newest; pressed again, to the
  previous ones. The same alert in the same place does not repeat for 20 s.
- **Groups per front:** Alt+1–5 puts the selected soldiers in a group; 1–5 selects; two taps go to it; 0 = all.
- **Points:** Q/E move the camera from point to point, with the owner in the notice.

## Vision

The game only draws enemies the commander's pawn can see (terrain and buildings block). In RTS mode the
commander becomes an invisible "eye" that follows the camera focus on the ground, including during pause.
Before, it stayed at the nearest soldier and hid trucks far from the group; focus on a truck was validated
in the hex. That still does not certify visibility across the whole screen/zoom/terrain. The base (ammo depot, F2)
stays where the commander was when the RTS turned on.

## Limitations and verification

- Fully offline, with our own combat model (the game's damage, effects and meshes).
  It does not use Foxhole's inventory nor server RPCs.
- March orders and the enemy advance use our own route (grid A*, no NavMesh), computed in
  slices per frame when the straight line is blocked.
- Tested in HomeRegionW (default) and HomeRegionC. To switch, put the map path on the 1st line of
  `FoxholeRTS/map.txt` (e.g. `/Game/Maps/HomeRegionC`). Of the large hexes in `Maps/Master`, `DeadLandsHex` was tested; there the "Introduction to Foxhole" panel
  appears on top and must be closed with the mouse (arrow).
- Each mechanic up to v0.8 was validated in game through the command channel and screenshots, and whole
  matches were played by a scripted "bot player". Keys and mouse have **not been tested with
  real input** yet: the script is in `MANUAL_TEST.md`.
- Measured performance: the mod spends ~1.5–4 ms per frame with ~25 soldiers; the rest of the cost is the
  game's own characters (with 12 soldiers, ~60 ms per frame on the test machine, window without focus).
- The automatic choice of point locations was tuned in HomeRegionW; on other maps,
  use J to put the points where you want.
- Do not use repeated UE4SS hot reload: it has frozen before. Restart the copy.
- To disable, with the game closed remove `enabled.txt` from the mod folder.
  This does not remove the loader nor make the copy suitable for playing online.

# MVP state (10/11)

Abstract truck DPS removed: HP comes from the real actor. Local rifle fire on vehicles
is still pending; grenades do not hit the fleet with collision off.
Offline tracing tells shot/HitNotify queries apart from impact application;
presentation callbacks and vehicle weapons do not prove the rifle's executor.

Experimental adjustment published: automatic evacuation of a wounded collector keeps the salvage in
hand and resumes the route after healing. It neither collects nor delivers during the retreat; death and
explicit orders still lose cargo. Offline tests PASS, validation interrupted by a crash.
Automatic replacement waits for the base exit to be free of enemies within 35 m,
without spending a shirt nor creating a worker during the refusal. The warning asks to protect
the base; fighters remain recruitable. No Unreal approval yet.

Priority: prove the playable chain in the small region; polishing the workers' arrival/waiting
was postponed. Collection delivers by proximity (15 m), not through the refinery door.
Trucks still use straight movement without collision and can go through/climb structures.
Regional graph extracted, still without physical validation or integration. A live probe
confirmed RWD movement and root/updated VehicleCollision(Box); it is not an integrated driver.
The recent batch crashed (PID4696/158 s); the last 60 s autosave without bmat growth.
Final report lost, full cause pending; do not consider the build stable.
Offline diagnosis linked the crash to the native UniqueId list of participants.
Empty bot IDs are a hypothesis, not a proven complete cause; turning voice off does not
protect the whole flow. The controller/NPC fix is still under investigation.
Candidate save fix: observes the convoy's native death before converting
live cargo into pending and records the reward in the same saved wallet. Offline tests
passed; not published/validated in the lab yet. Vehicle wounds
still have no persistence, do not consider this fix a complete save of them.
Unknown native HP also refuses the whole save and keeps the previous file,
without inventing death/loss. Offline candidate. The collectors' manual cargo in hand
is not persisted yet; continuing during collection may lose it.
An offline oracle of the native functions reproduced this flow with voice false and even
without PlayerSaveGame; fixtures do not prove the complete cause nor a fix in the game.
An NPC/roster contract probe is prepared for the next batch, without reading Steam IDs
or changing actors; an offline test does not prove stability in the game.
Creating a HeadlessLocalPlayer alone is not a proven fix either: the native
init is separate and its link to the local PlayerState remains pending.
Navigation uses the soldier's real 50 cm radius; old cases of a stuck medevac are not solved.
