# README_DRAFT — parts of `mod/README.md` that change with the v4 stack

Draft for the INTEGRACAO task to publish **after** the lab. Nothing was applied to `mod/README.md`. Each block says which section (or table row) of the
current README it replaces; the block's text is written to be pasted. Everything was checked against the candidate (candidate **v4.1** = v4 + `v4_1/v4_1.patch`, SHA256
`62245d23…598f`; base `candidate_v4/main.lua` `025e3b80…aab0`); what **no live test saw** is marked **[lab]** and must lose the mark (or be corrected) with the results of
`BATCH_SCRIPT.md`. `CFG` numbers are the candidate's current values (design proposals, except structure costs/health/capacity, which come from the
game's tables). Where the code and a report diverged, the text follows the code (list in `HOW_TO_INTEGRATE.md` §8 and in the agent's report).
In-game messages are quoted in Portuguese, as they appear on screen.

---

## 1. Key table (REPLACES the rows `Ctrl+1 / 2 / 3 / 4 / 0`, `L`, `Shift+L`, `Alt+L` and `J` of the table in section `## Controls`; ADDS `Shift+J`)

| Key | Action |
|---|---|
| Ctrl+1 / 2 / 3 / 4 / 0 | Recruit rifleman / machine gunner / marksman / medic / officer (only one). **In a match with logistics:** costs **1 shirt** from the stock where the soldier spawns (the rifleman also spends **1 rifle**), spawns at the main base or at a forward base with shirts — the one closest to the cursor; with the cursor **inside** a base, only there — and does **not** spend manpower. **In Assault** (and without logistics): manpower (20 / 35 / 45 / 30 / 40) |
| L | The next supply truck goes to the depot under the cursor (main base, forward base or one of your points); outside them = automatic |
| Shift+L | Factory priority: automatic → ammo → shirts → rifles → bandages |
| Alt+L | Deploy refinery/factory at the native locations and the missing supply trucks, with the scenario's starting budget (1000 bmat) |
| J | Create a control point under the cursor (up to 5). Only **without** a modifier: with Shift pressed it does not create a point |
| Shift+J | Forward base over one of your points (300 bmat from the factory; **two presses within 4 s**: the 1st shows cost and location, the 2nd builds). See "Forward bases" |

The help text (F5) and the load banner already carry `Shift+J: base avançada (300 bmat, 2 toques)` and the new recruit line (already in the candidate).
**[lab]** Shift+J does not also fire plain `J` (`plain()` depends on `S.MOD_KEYS` containing UE4SS's real Shift keys).

---

## 2. `## Classes and economy` (REPLACES the paragraph "Manpower starts at 60 …" to the end of the section, and adds the note right below the class table)

> **Class cost (column "Cost"):** it is manpower and applies in Assault and outside logistics. In a match with logistics (Shift+F6) recruiting costs **shirts**
> (and a rifle for the rifleman): see "Logistics". Manpower still pays for mortar (40), barrier (15), trench (20), supply crate (25),
> aid post (30) and wire (10).

Manpower starts at 60, regenerates 1/s plus 0.5/s per control point of yours (max. 200) and yields +8 per kill and +30 per wave eliminated.
With automatic waves, you win by eliminating the 10th wave or holding all control points for 90 s in a row. Defeat happens when the enemy dominates all
control points or by **lack of troops**: in the logistics branch, when no combat soldier is left **and** there is no shirt at the base, at the forward bases,
in the factory or in a truck (collection workers do not count as combat); outside it (Assault, without logistics), when there are no combat soldiers and manpower cannot pay for a
rifleman. Enemy accuracy grows 4% per wave (up to +50%), and each wave brings one more enemy for every ~2.5 of your soldiers (up to 16 per wave; only **combat** soldiers count: the 3 collection workers do not increase
the wave, do not enter the "next wave" warning and do not hold off the defeat by lack of troops, not even in Assault).

---

## 3. `## Control points` (REPLACES two lines of the list)

- (line "Your point is an aid post and depot …") → **Your point is an aid post and depot:** soldiers inside the ring reload 15% of their ammo per second and, without
  suppression, recover 2 HP/s. Under logistics the point's depot receives **ammo and bandages**; shirts and rifles only reach places that can reinforce (main base and active forward
  base), and a lost point loses its stock.
- (line "Recruiting (Ctrl+1..4) with the cursor inside one of your points makes the soldier spawn there.") → **In Assault and outside logistics**, recruiting (Ctrl+1..4) with the cursor inside one of
  your points makes the soldier spawn there. **Under logistics** a plain control point **does not reinforce**: the recruit spawns at the main base or at a forward base (see "Forward bases").
  `CFG.SPAWN.pointSpawn = true` restores the old behavior.

---

## 4. `## Assault (Alt+F6)` (ADDS at the end of the section)

In Assault recruiting is still paid with **manpower** (and also spends the depot's shirt, as before); there are no enemy convoys nor forward bases
(Shift+J answers "bases avançadas só numa partida com logística (fora do Assalto)"). **[lab]** I11/K9 of the script.

---

## 5. `## Save and continue` (REPLACES the whole section)

During automatic waves the match is saved on its own every 30 s to `FoxholeRTS/save.txt` (format **v2**): wave, score, manpower, difficulty, points and owners,
barriers, trenches, every live soldier of both sides (class, position, health, kills and ammo) and, in a match with logistics, also: stocks and production of the
**player's logistics** (factory, trucks, depots, collection), the **deployed infrastructure and the wallet** (what was paid with Alt+L: code, position and rotation of the
ruin), the **enemy chain** (section `elogi`: rear stock, front, pending order) and the **forward bases** (section `fwd`: point, position, health and stock).
It never writes an actor address. Supply crates, mortars in flight, routes, convoys on the road and the pending forward base order are not saved (the convoy comes back
as pending cargo in the rear; the order is canceled on load; the workers' cargo in hand is discarded).

- **Writing:** goes to a temporary file checked by rereading; the previous save becomes `save.txt.bak` (or `.corrupt`, if it was invalid); only then does the temporary become the
  save. If the session crashes between the two steps, Continue reads `save.txt`, then `save.txt.tmp`, then `save.txt.bak`.
- **Ctrl+F6 (continue):** when opening the game an alert warns there is a saved match; Ctrl+F6 continues, Shift+F6 starts another. Before erasing anything the mod validates the
  file (format, world, surface, ruins, wallet, logistics). **If something does not match, Continue is refused** ("Continuar recusado (partida atual e save
  preservados): motivo") and the current match and the file stay as they are. The paid infrastructure and the forward bases are rebuilt in the same place, for free and
  **all or nothing** (a position that no longer validates = refusal). On a new load of the hex there is no need to repeat Alt+L before continuing. **[lab]**
- **Incomplete continue:** if some of the state could not be rebuilt (a point that did not come back, for example), the match opens with the warning "INCOMPLETA: …; autosave suspenso"
  and the autosave does **not** overwrite the good save until you decide (Ctrl+F6 tries again; Shift+F6 starts another).
- **Enemy chain:** if the `elogi` section is missing, invalid, of a future version or without logistics, **only it** is discarded: the enemy chain restarts from the
  scenario stock, with the warning "CADEIA INIMIGA REINICIADA (motivo): estoque de cenário" for 10 s; the rest of the player's state is restored. Any other invalid field refuses everything.
- **Compatibility:** v4 opens saves from earlier versions; **the reverse does not hold** — a save with forward bases or with workers does not open in a version without
  collection/bases (unknown field). Victory or defeat deletes `save.txt`, `.tmp`, `.bak` and `.corrupt`.

---

## 6. `## Logistics` (REPLACES the whole section)

**Current state:** prototype; HomeRegionW is the Wardens' training/boarding island, not the war. Roads, fields and installations change by region. The starting
deployment in `CallumsCapeHex` uses native locations and real actors; transport still drives straight, without collision, not along the road. Building facilities is not implemented yet.
New match/assault require an active salvage field, refinery and factory loaded and **two supply trucks** on the map (the resource one is built by the factory, see
"Start of the match"). If anything is missing, the mod warns and does not erase the current match; it does not create invisible places or trucks to fake a chain. Ruins are not
operational installations. The check does not depend on appearing on screen. The convoy rejects a spawn return already marked for destruction, even if `IsValid` is still true. Structure/
vehicle costs come from the batch 16 re-export.

**Starting deployment (Alt+L, before the match):** the mod's own system, instantaneous, not Foxhole's construction site nor inventory. There is a **1000 bmat** scenario budget:
refinery 400, factory 400 and 100 per TruckW (**two** supply trucks; the resource one is not deployed). It only fills in what is missing; uses an active salvage field, matching
nearby ruins and their original positions/rotations. Trucks spawn on Landscape terrain near the factory, with terrain/clearance/separation checked, not on
roofs. It checks the actors' HP/class/position. A failure undoes the spawns, restores the ruins and neither debits nor clears the existing soldiers. Repeating does not duplicate a chain already
ready; the balance lasts for this load of the world, separate from the production bmat. It does not freely rebuild facilities nor spend manpower. Deployed installations stay in this world
when restarting the match. The paid infrastructure and the wallet **are written to the save** (see "Save and continue").

**Start of the match (manual collection):** Shift+F6 starts **without a resource truck**. The base has 40 bmat in the factory, 6 ammo crates, 30 shirts and 10 rifles. From ~5 s on,
**3 workers** spawn (one every ~3 s) — soldiers without a weapon, 1 shirt each — who walk to the salvage field, collect (0.5 salvage/s each, up to 40 in hand) and deliver to the refinery
(2 salvage = 1 bmat). When it gathers 100 bmat the factory builds the resource truck (before the supply trucks and the crates; it **keeps** those 100 bmat from the start); it appears
in the field, manual collection ends and the panel loses its line. If the resource truck is destroyed with no bmat or salvage, collection **reactivates**. An order of yours to a worker takes them
out of collection (the cargo in hand is lost) and they come back on their own after 60 s without an order; in combat (enemy within 35 m, recent fire or health below 80%) they pause, and stuck
for more than 180 s the worker drops collection. Dead workers are replaced (1 shirt) while collection is needed; **they do not count toward the squad limit of 12** (their
limit is 3) and, while there is no resource truck, the shirts reserved for them are not spent by Ctrl+1…4. Saving during collection discards the salvage in hand. Collection numbers
are a **design proposal** (`CFG.COLETA`); there is no game data for on-foot collection. `CFG.COLETA.manualStart = false` goes back to the old start (3 trucks, 1100 bmat, 240 factory bmat).
**[lab]** real walking, animation without a weapon, truck spawn in the field.

In a match (Shift+F6, Alt+F6 or continue), the war depends on a supply chain, with costs and times taken from the game's own tables (`MECHANICS_STUDY.md`). The panel
(top-left corner) is **multiline** (12–13 lines, up to ~222 characters): logistics summary, factory (job, remaining time or the bmat reserve), ready crates, one line per
depot (base, forward bases, your points), one per truck (state, cargo, destination), the enemy chain, collection and a final line with rifles and bandages. **[lab]**
(readability, height and width at the various zooms are a visual gate).

1. **Salvage:** at the start, the workers on foot; then a resource truck shuttles on its own between the salvage field and the refinery (100 per trip).
2. **Refinery:** 2 salvage become 1 bmat.
3. **Factory:** spends bmat on crates of **four products** — ammo (80 bmat), shirts (80 bmat, 10 soldiers per crate), **rifles** (100 bmat, 20 per crate) and **bandages**
   (80 bmat, 50 per crate). On automatic it makes whatever is most lacking; Shift+L fixes a type. Game times ×0.2. **bmat reserve:** for each of your trucks destroyed or still to be
   built, the factory keeps 100 bmat (it only starts a crate if there is enough beyond that), so the truck can always come back; the panel shows "Fábrica | guarda N bmat …".
4. **Supply trucks (2):** carry up to 15 crates from the factory to the neediest depot (the base, a forward base or one of your points); L picks the next one's destination. Shirts and rifles
   only go to the main base and active forward bases; a point without a base receives ammo and bandages.
5. **Consumption:** recruiting spends **one shirt** from the depot where the soldier spawns (the rifleman, also **one rifle**); the **medic** only treats wounded allies near a depot with **bandages**
   (spends one per effective treatment); reloading at the base or at a point spends that depot's ammo (one crate = 6 full reloads). An empty depot does not reload and raises an alert.
   A lost point loses its stock.
6. **Ambush:** an enemy within 15 m of a moving truck damages it (alert "caminhão sob fogo"); destroyed, it loses its cargo and comes back in 30 s for 100 bmat (reserved, see 3).
7. **Real enemy chain and interdiction:** the enemy has an **off-map rear** that follows the same rules (salvage → refinery 2:1 → real ammo and shirt recipes → a truck of
   15 crates that costs 100 bmat to rebuild). With automatic waves, when the rear has enough crates (at least 3, or what the front asks for) a colonial truck leaves
   (BPTruckC; 90–200 m from the base, on the side the wave comes from, route checked on the ground) carrying **real crates** to the front; the fleet is 2 trucks. Each wave gets a
   **free garrison of 5 soldiers** plus those the front can equip (1 shirt and 1/6 of an ammo crate per soldier); what is missing removes soldiers from it ("faltou suprimento ao
   inimigo: a onda vem com N a menos", with how many were due to destroyed convoys). Your soldiers within 15 m of the truck machine-gun it; mortar and grenade also hit trucks (of both
   sides). Destroying a loaded convoy makes the front lose the cargo, yields 25 manpower and the rear rebuilds the truck (30 s, 100 of the enemy's bmat). The panel shows
   "INIMIGO: frente equipa N …" with the rear and the convoys. The account is closed and auditable (`logi.eAudit()`/`logi.eReport()`): initial + produced = rear + transit + pending +
   front + consumed + lost. Like the enemy soldiers, the truck only appears when your soldiers see it; there is no marker revealing it outside vision. **[lab]** the real BPTruckC,
   the wave cadence and the free floor (`CFG.ECHAIN.free`) are calibration.

**Forward bases (Shift+J):** with the cursor inside one of **your** points, the 1st press shows cost and location ("Base avançada em A: 300 bmat (fábrica tem N). Shift+J de novo em 4 s
para construir"); the 2nd press, within 4 s of real time, builds. The base is a native `BPForwardBase1_C` (300 bmat from the factory, 1725 health, a stock of **15 slots**; a partial crate
counts as 1 slot) and the bmat is only debited **after** the actor spawns validated. Conditions: your point, no enemy in the ring, far from the main base (≥ 30 m) or near an enemy point
(≤ 40 m), flat and free Landscape ground (never a roof nor a mod structure), at least 3 free exits, at most 3 bases, only with logistics and outside Assault. Without enough bmat the
2nd press records a **pending order**: the factory starts keeping 300 bmat (after the reserve for a destroyed truck, which has priority; panel "Fábrica | guarda 300 bmat para
base avançada em B") and builds on its own when it has enough; the order cancels in 180 s, if the point stops being yours, if an enemy appears in the ring or with Shift+J again within 4 s over the order's
point. Bases receive shirts, rifles, ammo and bandages by truck (L over the base) and are the only place, besides the main base, where soldiers spawn: Ctrl+1…4/0 with the cursor
**near** a base uses the closest one with stock; with the cursor **inside** a base, only it (if a shirt/rifle is missing, it refuses with the reason, without falling back to another); the recruit spawns at an
exit of the base (round-robin). The panel gains one line per base: `base A | camisas 12 | fuzis 3 | slots 3/15 | reforça: tudo` (or `só sem fuzil (sem fuzis)`, `NÃO (sem camisas)`,
`INATIVA (ponto neutro)`). **Loss:** point captured or base destroyed (enemy mortar, damage ×2) → the base vanishes **once**, the stock is lost (alert "BASE AVANÇADA B capturada:
perdeu N camisas e M fuzis"), the actor is destroyed; recapturing the point does **not** bring it back and rebuilding costs 300 again. A neutralized point makes the base **inactive** (stock
kept, neither reinforces nor receives). The enemy does not build bases. **[lab]** the class `BPForwardBase1_C` was never instantiated in the game: path, health, `CodeName`, `TeamId`,
exits and ruin are rehearsal B1; without it the visual plan B (mod mesh) does not exist.

Places: the map's buildings closest to the base (in HomeRegionW: salvage field to the south, refinery and factory in the town to the north). Trucks: the map's own or explicitly deployed
with Alt+L, moved by the mod in a straight line, without collision. No green discs. The commander's vision follows soldiers, not isolated trucks: an invisible mesh does not prove the actor
stopped existing.

---

## 7. `## Limitations and verification` (ADDS these markers; adjust when the lab answers)

- The v4 stack (economy with 4 products, real enemy chain, bmat reserve, save v2, manual collection and forward bases) was validated **offline** (lupa, Lua 5.4 and 5.5): logic,
  accounting, save contracts. **[fill in at the lab]** what was seen in the game (date, `main.lua` hash, PID) and what stays offline only.
- Balance (collection, the enemy chain's free floor, base cost and stock, `startRifles`) is a **proposal** until the user plays; see `OPEN_DECISIONS.md`.
- The outline stability gate (skinned copies) stays open until loads B2/A2; v4 does not touch that code.
