# Manual test script (real keyboard and mouse) — FoxholeRTS v0.9

In-game texts (alerts, panel) are still in Portuguese; they are quoted here exactly as they appear.

## Visual — update of 10/10
- [x] Horizontal line/flicker while moving: the user reported it went away after a temporary VSync.
- [ ] Published build: repeat vertical/horizontal movement with low/high zoom; check the line is gone.
- [ ] Eye follows the focus: visit a truck far from the squad, also during pause, and check the mesh.
- [ ] Visibility at the screen edges, snow and installations at various angles (not approved globally).
- Stuck soldiers are still pending; one approved collection route does not certify general navigation.

## Logistics batch v4.1 — pending in game

The user postponed the crashes and the residual yellow. Do not repeat the quick 1/2 rehearsal now.
The old list below contains historical values; for the new logistics, check:

- Shift+F6: besides the starting squad, three unarmed workers appear in the first collection ticks.
- Ctrl+1–4: logistics recruitment spends a shirt and a rifle at the eligible base; a common point is not a spawn.
- Alt+L: deployment of 1000 bmat, refinery, factory and two supply trucks.
  The resource truck is produced later; transport is still in a straight line.
- Shift+J: forward base on an eligible own point, 300 bmat; confirm within 4 s, at most three bases.
  J without Shift still creates a control point.
- Shift+L: production/delivery of ammunition, shirts, rifles and bandages.
- Ctrl+F6: continue the v2 save, including wallet and infrastructure.

Still no approval of real keyboard, appearance or balance for this batch.

The routines were verified through the command channel; keyboard/mouse integration and appearance at all
angles/zooms still need this manual confirmation. Tick what worked
and note what did not. To send the result, just paste this list with your ticks.

Preparation: open the lab copy (Steam open). The mod enters the map and turns RTS mode on by itself;
the key help appears in the bottom-left corner for 40 s.
The chain tests below use HomeRegionW. In a hex without active installations/enough trucks,
Shift+F6/Alt+F6 refuse the match with a diagnosis; this does not mean the buildings do not exist as ruins
or are not just hidden in the picture. The inventory comes from the loaded actors.

| # | Do | Expected | OK? |
|---|---|---|---|
| 1 | F5 | The help disappears; F5 again, it comes back | |
| 1b | Shift+F5 (three times) | Panel switches "RTS (difícil)", "(fácil)", "(normal)" (hard/easy/normal); the help does **not** disappear | |
| 2 | Shift+F6 | Alert "NOVA PARTIDA" (new match); 6 soldiers selected with a yellow outline; three dotted rings (points A, B, C) | |
| 3 | Left click on a soldier | Only that one gets a bright yellow outline and a fill of the hidden parts; the commander does **not** attack | |
| 3b | Move the selected one, rotate the view; deselect by clicking the ground; select another; F10 twice | The outline follows the whole body, weapon, helmet, hands and animation, with no still ghost or disc; the fill also disappears when deselecting and outside the RTS. Weapons/hands of NON-selected soldiers do not turn yellow. Appearance approved in this session; long-run stability still pending | |
| 4 | Drag with the left button over the group | The box selects the soldiers inside; Shift+drag adds | |
| 5 | 1, 2, 3, 0 | Selects group 1, 2, 3 (empty), all | |
| 6 | Right click on the ground | Selected soldiers march in formation there (avoiding trucks and buildings) | |
| 6b | Shift+right click in two or three places | Selected soldiers go through the points in sequence | |
| 7 | Right click inside a ring | On arrival, the panel shows the point rising in %, then "A+" and a blue banner | |
| 8 | Ctrl+1 / Ctrl+2 / Ctrl+3 / Ctrl+4 | Recruits rifleman / machine gunner / sniper / medic (spends manpower) | |
| 9 | Ctrl+1 with the cursor inside one of your points | The recruit spawns at the point (alert "no ponto A") | |
| 10 | K with the cursor on the ground | A concrete barrier appears (−15) | |
| 11 | J with the cursor on free ground | New control point (ring) | |
| 12 | Wait for the wave; Ctrl+5 over the enemies | Artillery sound, warning ring, 3 explosions after ~2.5 s | |
| 12b | Ctrl+6 with the cursor next to the squad | An ammo crate appears (−25); panel "caixas 1"; disappears after 60 s | |
| 12c | Ctrl+7 on the ground; then right click inside the hole with 6 selected | A foxhole appears (−20); 4 get in, 2 stay in a line behind | |
| 12d | Ctrl+right click on an empty spot ahead | Alert "fogo de supressão" (suppressive fire); selected soldiers (except the medic) aim and fire there; dirt kicks up at the spot | |
| 12e | Play 30 s with automatic waves, close the game, reopen and press Ctrl+F6 | Alert "há uma partida salva" (there is a saved match) when the RTS turns on; Ctrl+F6 brings back soldiers, points and constructions | |
| 12f | Ctrl+8 next to the squad; bring a wounded soldier to the tent | A canvas tent appears (−30); the wounded soldier recovers health | |
| 12g | Ctrl+9 on the path; send a soldier through | A wire trestle appears (−10); the soldier slows down while crossing | |
| 12h | Alt+F6 | Alert "ASSALTO" (assault); three green points with trench, wire and garrison; panel "ASSALTO: pontos inimigos 3/3" | |
| 12i | Ctrl+0 (and again) | Officer recruited (−40) with a blue banner above the head; the 2nd is refused | |
| 12j | Let the squad take fire | Health bar above the wounded (green → yellow → red); disappears when healed | |
| 12w | Watch an ally and an enemy die while moving | They stop and fall to the ground; they do not run in place; the body is removed after 20 s | |
| 12x | In the lab configured for CallumsCapeHex, try Shift+F6 and Alt+F6 | Alert about missing active installations/trucks; does not delete existing soldiers nor start a fictitious chain | |
| 12y | In CallumsCapeHex, before the match, Alt+L; repeat; then Shift+F6 | Deployment alert: −1100 bmat of the scenario, balance 0; repeating does not duplicate; the match can start with refinery/factory and three real trucks. Transport is still a straight-line prototype | |
| 12k | Listen to a firefight | Rifle, machine gun, sniper and pistol with different sounds; the enemy sounds different from your side | |
| 12m | Pause; move the camera, select and give an order; Pause again | Panel "PAUSADO" (paused); everything stopped, but camera and orders respond; on resume, the order is carried out | |
| 12n | Insert three times | Panel "2x", "3x" and back to normal | |
| 12o | Select a few, Alt+4; then 4, and 4 twice quickly | "N soldados no grupo 4"; 4 selects only them; a double tap takes the camera to them | |
| 12p | With a wave coming ("Espaço: ver" in the alert), press Space, and again | The camera goes to the wave; then to the previous alert; the "! N alertas" disappears from the panel | |
| 12q | Q and E with 3 points | The camera goes from point to point with "ponto A (nosso) [1/3]" | |
| 12s | New match (Shift+F6), Ctrl+L a few times | The camera goes to the factory, refinery, field and trucks; the resource truck moves by itself | |
| 12t | L with the cursor on one of your points; look at the 2nd line of the panel | "próximo caminhão vai para o ponto X" (next truck goes to point X); then "caminhão entregou em ponto X" and the point's stock rises | |
| 12u | Shift+L | "fábrica: munição", "camisas", "automático" (factory: ammo, shirts, automatic) | |
| 12v | New match; on the alert "COMBOIO INIMIGO", Space and send soldiers to the middle of the route | Soldiers shoot the truck; "COMBOIO INIMIGO DESTRUÍDO (+25)"; on the next wave "faltou suprimento ao inimigo" (the enemy ran out of supplies) | |
| 12r | Select 6–12 soldiers; mouse wheel to the maximum (160 m); move the group | Outline only on the selected ones, no dots; judge readability/performance and follow the movement. Check LOS without concluding structures are absent from the picture | |
| 12l | Let a soldier drop below 30% with a first aid post (Ctrl+8) nearby | Alert "ferido recua sozinho" (wounded retreats alone); they go to the tent and come back to fight healed | |
| 13 | Right click on an enemy | Selected soldiers focus on it | |
| 14 | Home with wounded selected | They run to your nearest point without shooting; they recover health there | |
| 15 | End | Selected soldiers stop and hold position | |
| 16 | Arrows, PageUp/PageDown, F2, F3 | Camera moves, zooms, centers, edge pan on/off | |
| 16b | Listen when raising a barrier (K) and when winning/losing | Construction sound; the game's victory/defeat sound | |
| 17 | F11 | Removes soldiers, enemies, barriers and points | |

If something freezes or the panel stops updating, the log is in
`<lab copy>\War\Binaries\Win64\ue4ss\UE4SS.log` (lines with `[FoxholeRTS]`).

## Stability gate with real input — pending (10/10/2026)

**Failed on 10/10:** fatal error during the number keys test; the last log line selected group 1.
Do not repeat the full script until investigated. In the next joint rehearsal we will do
one step at a time: `1` selects group 1, `2` group 2, `0` all; there is no need to
play a match, recruit or win waves. Report immediately if it crashes.
Queue variant prepared after reproducing the Registry error: in the next joint test, first
one tap of 1, then 2; only after confirming both, alternate 1/2 standing still. Movement and double tap
go to separate steps. Do not operate the game while the agent's automatic control runs.

Separate from the key matrix: the agent spent more than ten minutes with six selected
standing still, without real input. This does not validate the key callbacks nor wheel/click/zoom.
Arrange a session with the agent before starting; the lab stays closed when idle.

1. Start from a clean load in HomeRegionW, with six soldiers and waves turned off through the channel.
2. For ten minutes, alternate click/drag/Shift+drag, groups 1/2/0, movement on the ground,
   stop (H), arrows, wheel and PageUp/PageDown. Vary the zoom and the group's position on screen.
3. Deselect/reselect and toggle F10 twice; check every piece of the outline,
   with no ghosts on the commander nor glow on non-selected soldiers. Do not use Ctrl+R.
4. Report here whether there was a freeze, crash, misaligned outline or lost commands and
   roughly when. The agent keeps the log/PID/hash before restarting.

Surviving this script is evidence of integration, not proof of the cause of the old crash.
Long repetition, larger groups and acceptable performance are still missing.
