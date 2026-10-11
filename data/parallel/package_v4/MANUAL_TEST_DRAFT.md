# MANUAL_TEST_DRAFT — new and changed items for real input (v4 stack)

Draft for the INTEGRACAO task to merge into `MANUAL_TEST.md` **after** the lab. Nothing was applied there. Text, keys and messages checked against the candidate
(candidate **v4.1** `62245d23…598f` = `candidate_v4` `025e3b80…aab0` + `v4_1/v4_1.patch`). As in `AGENTS.md`, the agent does **not** inject keyboard or mouse: everything below belongs to the user. The lab already covers through the channel
(`BATCH_SCRIPT.md`) the logic behind each item; here is what only real input shows (key, cursor, mouse, camera, appearance, real game time).
In-game messages are quoted in Portuguese, as they appear on screen.

How to read the columns: **Expected** is what should appear; **Fails if** is what counts as a defect (note the exact panel message and the time; the log is in
`D:\FoxholeLab\Foxhole\War\Binaries\Win64\ue4ss\UE4SS.log`, lines `[FoxholeRTS]`; every `notify` message also goes to the log). What is a **balance decision** (and not a defect) is in
`OPEN_DECISIONS.md`.

## Preparation added to the top of the file (REPLACES the "Preparation" paragraph)

Open the lab copy (Steam open). The mod enters the map and turns RTS mode on by itself; the key help appears in the bottom-left corner for 40 s (F5).
The chain tests use HomeRegionW; the forward bases and Continue with paid installations use CallumsCapeHex (the lab swaps the map with `map.txt`; ask for the right map
before starting). In a hex without active installations, Alt+L deploys refinery, factory and the 2 supply trucks; Shift+F6/Alt+F6 refuse the match without it
("Partida não iniciada: …"), which does **not** mean the buildings do not exist as ruins.

**What changed at the start of the match:** the logistics match (Shift+F6) **no longer** has a resource truck. It starts with bmat 40, 30 shirts, 10 rifles and 6 ammo crates, and
**3 unarmed workers** (from ~5 s on) collect salvage on foot until the factory gathers 100 bmat and builds the truck. **Manpower** only pays for mortar, barrier, trench,
crate, aid post and wire (and recruiting **in Assault**). Recruiting in a logistics match costs a shirt (and a rifle, for the rifleman).

Real time: a match starting at 40 bmat takes **several minutes** until the 1st resource truck, and a forward base (300 bmat) takes longer; set aside ~15 min just to reach items 11c–11h
without help. If the lab already prepared a state (credited bmat), the note says so.

---

## A. Existing items that CHANGE (each row REPLACES the row with the same number in `MANUAL_TEST.md`)

| # | Do | Expected | Fails if | OK? |
|---|---|---|---|---|
| 2 | Shift+F6 (in HomeRegionW, or in CallumsCapeHex after Alt+L) | Alert "NOVA PARTIDA (…): vença 10 ondas…" and `ondas automaticas: true` (Shift+F6 already turns the waves on); 6 soldiers selected with a yellow outline; three rings (A, B, C). At ~5 s the **1st worker** appears (a soldier **without a weapon**, near the base) and the other two every ~3 s, each **spending 1 shirt** (shirts 30 → 27 in the panel). Panel: `Fábrica \| guarda 100 bmat para reconstruir caminhão (bmat 40)` and a line `coleta manual: N trabalhadores \| x/100 bmat para o caminhão \| y sucata em mãos` | worker in T-pose, with a weapon, stuck in the ground/on a roof or without an outline when selected; more than 3; shirts do not go down; **the match refuses without a reason** | |
| 8 | Ctrl+1 / Ctrl+2 / Ctrl+3 / Ctrl+4 (cursor on the ground, far from bases) | Recruits rifleman / machine gunner / marksman / medic **at the main base**, near the exit; the alert says `recrutado … em base (-1 camisa, -1 fuzil) \| camisas N, fuzis M` (the rifle only for the rifleman; machine gunner, marksman and medic spend only the shirt). **The panel's manpower does not change.** With 0 rifles: Ctrl+1 refuses (`sem fuzis em base …`) and Ctrl+2/3/4 still work | deducts manpower; spawns on a roof/wall; recruits without stock; refuses without a message | |
| 9 | Ctrl+1 with the cursor inside one of your points **without** a forward base | Does **not** spawn at the point: spawns at the main base (a plain point does not reinforce; `CFG.SPAWN.pointSpawn=false`). The spawn message mentions the base, not the point | the recruit spawns at the point | |
| 11 | J with the cursor on free ground (without Shift) | New control point (ring), up to 5 | does not create; creates with Shift pressed (see 11a) | |
| 12e | Play ≥ 90 s (automatic waves already turn on by themselves with Shift+F6; Shift+F4 turns them **off**), with workers in the field, close the game, reopen and press Ctrl+F6. **Before Ctrl+F6, in CallumsCapeHex, do not repeat Alt+L** | Alert "há uma partida salva (…): Ctrl+F6 continua, Shift+F6 começa outra" when RTS turns on; Ctrl+F6 brings back soldiers, points, constructions, stocks and the **paid infrastructure** (refinery, factory and trucks come back for free, with no new debit). The workers come back and resume collection (the cargo they carried was discarded, shown only in the log) | duplicates soldiers/trucks when repeating Ctrl+F6; charges bmat again; refuses a good save | |
| 12s | New match (Shift+F6), then Ctrl+L several times | The camera goes through factory, refinery, salvage field and **every truck that exists**. At the start there are only the 2 supply ones; the resource one enters the list when the factory builds it. Ctrl+L does **not** visit forward bases (use Q/E, which go through the points) | camera goes to empty space, or stops on a destroyed truck | |
| 12t | L with the cursor on one of your points; look at the 2nd panel line; repeat with the cursor inside a forward base (11e) | Panel: "próximo caminhão vai para o ponto X"; then `caminhão entregou em X: N munição, N camisas, N fuzis, N bandagens` and the stock rises. **A plain point receives only ammo and bandages** (shirts and rifles only reach the main base and the forward one) | shirts/rifles show up at a point without a base; overflows 15 slots at a base | |
| 12u | Shift+L (several times) | The factory priority cycles: `automático` → `munição` → `camisas` → `fuzis` → `bandagens` → `automático` (panel, line `LOGÍSTICA \| … \| prioridade …`). The stock panel shows `Fuzis: fábrica N caixas \| bandagens: fábrica N caixas` on the last line | only cycles 3 states; a product outside the list | |
| 12v | New match (waves already on); at the alert "COMBOIO INIMIGO a caminho da frente (…)", Space and send soldiers to the middle of the route | Soldiers fire at the truck; `COMBOIO INIMIGO DESTRUÍDO (+25): …`; on the next wave `faltou suprimento ao inimigo: a onda vem com N a menos (…)`. The 1st convoy leaves ~20 s after the waves start. See also 12v2 | the loss is counted twice; convoy without cargo; repeated bounty | |
| 12x | In the lab in CallumsCapeHex **without** deploying: Shift+F6 and Alt+F6 | Both refuse: `Partida não iniciada: … Alt+L tenta implantação nos locais nativos.` (missing active installations/trucks); they do not erase existing soldiers nor start a fictitious chain (Assault also needs the chain: `logi.ready`) | erases the current match; starts without a chain | |
| 12y | In CallumsCapeHex, before the match: Alt+L; repeat; then Shift+F6 | `IMPLANTAÇÃO: -1000 bmat do cenário; saldo 0` (v4 charges **1000**, not 1100: refinery 400 + factory 400 + **2** supply trucks 100; the resource one is born from collection). Repeat: `Cadeia já implantada`. The match starts with refinery, factory and 2 real trucks | charges 1100, repeats the charge, or creates 3 trucks | |
| 12l | Let a soldier drop below 30% with an aid post (Ctrl+8) nearby | Alert "ferido recua sozinho"; they go to the tent and come back to fight healed. **If there is no tent, they go to your nearest point** (the point heals 2 HP/s without suppression) | | |

---

## B. NEW items

### B1. Shift+J: forward base (11a–11h; same columns as above)

Precondition: a logistics match in CallumsCapeHex with **one of your points ≥ 30 m from the main base** (or ≤ 40 m from an enemy point) and no enemy in the point's ring. To
get here, capture one of the points (item 7). "Inside" a point or a base = ≤ 5 m from the center (`CFG.POINT_RADIUS` 500 cm). Construction uses **two presses within 4 s of real clock** (pausing the game does **not** stop that clock).

| # | Do | Expected | Fails if | OK? |
|---|---|---|---|---|
| 11a | Shift+J with the cursor on free ground, then over a **neutral** or **enemy** point, then inside one of your points | Free ground: `Shift+J: ponha o cursor dentro de um ponto de controle seu`. Neutral/enemy point: `o ponto X não é seu`. Inside yours: cost and instruction (11c). **No new point** appears (only J creates a point) and the number of rings does not change | creates a ring (`plain()` did not hold J back); debits bmat on a refusal | |
| 11b | Shift+J on one of your points **near the main base** (< 30 m) and with no enemy point within ≤ 40 m | `ponto X perto demais da base (mín. 30 m) e longe de pontos inimigos (40 m)`; nothing created | creates the base | |
| 11c | With free bmat ≥ 300 (minus 100 per destroyed truck): Shift+J over one of your points far from the base (1st press); again within ≤ 4 s | 1st: `Base avançada em X: 300 bmat (fábrica tem N). Shift+J de novo em 4 s para construir`. 2nd: `BASE AVANÇADA X construída (-300 bmat; fábrica N). Mande caminhões com camisas e fuzis (L sobre ela)`. The native construction (a 1725 HP structure) appears at the point, **standing on the ground, facing the base or the enemy point**, without sinking or floating. The panel gains `base X \| camisas 0 \| fuzis 0 \| slots 0/15 \| reforça: NÃO (sem camisas)` | after 4 s the 2nd press counts as the 1st; crooked, buried actor, without collision; bmat debited without the base; two bases at the same point | |
| 11d | With **little** bmat: Shift+J + Shift+J | `Base avançada em X: 300 bmat, faltam N …` and then `pedido de base avançada em X registrado: …; a fábrica guarda 300 bmat (até 180 s)`. Panel: `Fábrica \| guarda 300 bmat para base avançada em X (bmat N)` (if there is also a destroyed truck: `… para reconstruir caminhão e base avançada em X`; **the truck has priority**). Builds on its own when 300 free are gathered. Shift+J on the same point: `pedido pendente em X (a fábrica guarda 300 bmat). Shift+J de novo em 4 s cancela`; repeated: `pedido de base avançada cancelado: a fábrica volta a produzir`. Cancels on its own in 180 s (game time), if the point stops being yours or with an enemy in the ring | the factory goes **without producing ammo** during the 180 s and the base does not come; the order does not cancel | |
| 11e | Once the base exists: L with the cursor over it; wait for the delivery. Then Ctrl+1 with the cursor **inside the base** | The truck carries what fits in the 15 slots (partial crate = 1 slot); shirts and rifles go up in the panel line. The recruit spawns **at the base's exit** (not on a roof/wall), spends 1 shirt and 1 rifle **from it** and the line turns to `reforça: tudo`. Shift+J over a point that **already has** a base only shows its line (`BASE AVANÇADA X: base X \| camisas … \| slots …`), without building | spawns far away, at the main base, with the cursor inside the forward base; spends another one's stock | |
| 11f | With 1+ forward base standing: Ctrl+1 with the cursor **outside** any base; then on one of your points **without** a base | Outside: spawns at the base **closest to the cursor or to the squad with stock** (main or forward). Point without a base: spawns at the main one; **the point does not reinforce**. With the cursor **inside** a base **without stock**: refuses with a reason (`sem camisas em base avançada X; mova o cursor para fora das bases …`), **without silently falling back** to another | falls back to another base without warning | |
| 11g | Loss: let an enemy take the forward base's point, or let the enemy mortar land on it | Alert `BASE AVANÇADA X capturada: perdeu N camisas e M fuzis` (or `destruída`) **once**; the structure **vanishes** (no ruin, no residual actor); the panel loses the line; retaking the point does **not** bring the base back. Under mortar before falling: `base avançada X sob fogo` | the structure stays on the map; repeated alert; the stock remains | |
| 11h | With 1+ forward base: play ≥ 90 s, close, open, Ctrl+F6 | Base back in the **same place**, same health and stock, **only one** per point. Repeat Ctrl+F6: nothing duplicates. If the position no longer validates: `Continuar recusado: base avançada salva não foi refeita (…); nada mudou` and the current match and the save stay | duplicates the base; comes up without stock; refuses and erases what existed | |
| 11i | Pause (Pause) between the 1st and 2nd press of Shift+J, wait > 4 s, press the 2nd | The 2nd press counts as the **1st** (the clock is real time, not game time). Open decision in `OPEN_DECISIONS.md`; note what you prefer | | |
| 11j | Alt+F6 (Assault), Shift+J on one of your points | `bases avançadas só numa partida com logística (fora do Assalto)`; recruiting uses manpower | | |

### B2. Manual collection and workers (C1–C8 of the script)

| # | Do | Expected | Fails if | OK? |
|---|---|---|---|---|
| 12z | New match: follow the 3 workers until the 1st resource truck | They walk to the salvage field, **stand still collecting** (empty hands, no weapon), go back to the refinery and deliver; the line `coleta manual: …` shows `x/100 bmat para o caminhão` rising and `y sucata em mãos`. When bmat reaches 100 the factory **builds the resource truck**, which appears in the field, **on the ground**, and the message `caminhão de recurso pronto: coleta manual encerrada` fires; the collection line vanishes from the panel and the workers become free in the squad. Note the total time and the real distances (decides `OPEN_DECISIONS.md`) | worker in T-pose, with a weapon, standing at the base, stuck on a wall/snow or in an endless queue; truck on a roof | |
| 12z2 | Select **one worker** (click) and give a march order (right click) | They **drop collection** (the cargo they carried is lost; log `coleta manual: trabalhador sai da coleta (…)`), walk to the point and stop. **After ~60 s without a new order** they go back to collection on their own (if it is still needed) | comes back before 60 s and cancels the order; stays still forever | |
| 12z3 | Selection box (drag) that takes workers and soldiers; right click on the ground | All march; the workers leave collection (a cargo loss warning in the log for whoever carried it) | a worker fires, or does not move | |
| 12z4 | During collection, let the 1st enemy (F4) get close to the field | The workers **pause** (and drop the cargo after ~60 s of continuous combat) and come back when the area is calm (no fire for 8 s, enemy > 35 m away). If one dies, the base replaces them for **1 shirt** | flees and never comes back; more than 3 alive at once | |
| 12z5 | Kill the resource truck (enemy mortar or soldiers; `Ctrl+5` near it also destroys) with bmat/salvage at zero | Manual collection **reactivates** (`COLETA MANUAL: sem caminhão de recurso; trabalhadores da base coletam sucata até a fábrica fazer o caminhão`); the factory reserves 100 bmat and rebuilds | the match freezes without bmat and without a truck | |
| 12z6 | Ctrl+0 select all (includes workers); look at the outline and the selection panel | Workers selectable like any soldier; same yellow outline; when deselected, it goes away | the yellow outline remains on someone not selected | |
| 12z7 | Defeat by lack of troops: lose all **combat** soldiers with 0 shirts at the base/factory/trucks (optional, hard to provoke; the lab tests it through the channel) | The 3 workers do **not** count as combat; `DERROTA` only when no combat soldier is left **and** no shirt (no base, factory or truck). With shirts, it does **not** lose | defeat with shirts in the factory | |

### B3. The player's chain: products and medic

| # | Do | Expected | Fails if | OK? |
|---|---|---|---|---|
| 12aa | Shift+L to `fuzis`, wait for production, send the truck (L) to the base; repeat with `bandagens` | Recipe → production → transport → depot for the 4 products. Units: a rifle crate = 20, bandages = 50, shirts = 10. The panel's last line shows `Fuzis: fábrica … \| bandagens: fábrica …`, and per depot `N fuzis, M bandagens` | a product vanishes in transport; the panel does not show the stock | |
| 12ab | Ctrl+4 (medic) with **0 bandages** at the base; wound a soldier (let them take fire) and keep the medic next to them | The medic **goes to the wounded but does not treat** (no bandage). After producing/delivering bandages to a depot within ≤ 5 m of the medic (base, forward base or one of your points: `CFG.POINT_RADIUS` = 500 cm), they heal (+12 per treatment, every 1.5 s) and the panel's bandage stock **drops 1 per treatment** | heals without a bandage; heals far (> 5 m) from any depot with bandages | |
| 12ac | With the factory on `automático`, watch for 3–5 min | The factory **does not spend the 100 bmat reserve** for the destroyed truck on crates; the truck comes back when there are 100; the factory does **not** stop making ammo indefinitely because of the base order (180 s at most) | prolonged ammo starvation | |

### B4. Panel

| # | Do | Expected | Fails if | OK? |
|---|---|---|---|---|
| 12ad | Look at the panel with active logistics at several zooms and resolutions; open and close the help (F5); pause | **Multiline** panel (about 12–13: logistics, factory, ready, one depot per location, one `base …`/`base X …` line per base, trucks, `INIMIGO …`, `coleta manual …`, shortcuts), **without cutting** stocks or vehicles, without overlapping the help nor the game's native alerts. Paused: prefix `PAUSADO \|`; speed 2x/3x: prefix `2x \|` | text cut, on top of the help, or silently hidden | |
| 12ae | Panel during the enemy chain | The `INIMIGO: …` line shows `frente equipa N`, the convoy's cargo and `piso grátis 5/onda` | line missing with waves on | |

### B5. Save and continue, refusals (V1–V12 of the script)

| # | Do | Expected | Fails if | OK? |
|---|---|---|---|---|
| 12af | Ctrl+F6 **with the match running**, same save, twice in a row | Idempotent: no extra soldier, truck or base; stocks do not double | duplicates | |
| 12ag | Swap `save.txt` for a corrupted file or one from another region (ask the lab, or use `save.txt.bak` from another map) and press Ctrl+F6 **during a match** | `Continuar recusado (partida atual e save preservados): motivo`; **nothing** of the current match changes; the file stays as it is | erases the current match; the save vanishes | |
| 12ah | Save with the `elogi` section removed/tampered (lab) and Ctrl+F6 | The game opens normally, with `CADEIA INIMIGA REINICIADA (motivo): estoque de cenário` for 10 s; the rest (soldiers, stocks, bases) comes back | refuses the whole save | |
| 12ai | Closing the game during an autosave cannot be tested by hand; instead, **lose** (or win) the match and look at the `FoxholeRTS` folder | `save.txt`, `.tmp`, `.bak` and `.corrupt` removed | any of them left over | |
| 12aj | See `INCOMPLETA: …; autosave suspenso` only if it shows up on its own; **do not provoke it** | If it appears, Ctrl+F6 tries again; Shift+F6 starts another; the autosave does not overwrite the good save | the autosave writes over it | |

### B6. Others

| # | Do | Expected | Fails if | OK? |
|---|---|---|---|---|
| 12v2 | Ctrl+5 (mortar) with the cursor over a **loaded enemy convoy** | Warning, 3 explosions after ~2.5 s; `COMBOIO INIMIGO DESTRUÍDO (+25)` **once**; a 2nd mortar on the already destroyed truck does not count again | double loss | |
| 12ak | Alt+F6 (Assault, after Alt+L in the hex) and recruit | Recruiting uses **manpower** (as in v0.9; also spends the depot's shirt), without an enemy convoy and without Shift+J. The player's chain runs as in the normal match, so **manual collection with workers also applies in Assault** (the code allows the worker in that mode; **[lab]** not seen live, note it) | enemy convoy in Assault; Shift+J builds | |
| 12al | New match, let the 1st wave arrive (waves turn on by themselves) and count the enemies | The wave size uses **only combat soldiers** (v4.1): the 3 workers do not increase it, and the warning "próxima onda em … (esquadrão N …)" shows N without them. Note how many enemies spawned and how many combat soldiers of yours there were (compare with the same number without workers) | larger wave because of the workers; the warning counts the workers | |
| 12al2 | With the 3 workers in the salvage field (far from the combat squad) and the squad at a point, let a wave and an enemy reinforcement arrive | Waves and reinforcement come from the enemy side/points relative to the **combat squad** (v4.1: `squadCenter()` only counts combatants); the workers in the field do not pull the waves there. With no live combatant, the center of everyone applies | waves always appearing near the salvage field | |
| 12am | F11 (clear) with workers and a forward base standing; then Shift+F6 | F11 removes soldiers, enemies, barriers, points **and** destroys the forward base (no residual actor on the map); the new match starts without leftovers | the base's structure or a worker is left on the map | |

---

## C. Items of the current file that stay as they are

1, 1b, 3, 3b, 4, 5, 6, 6b, 7, 10, 12 (Ctrl+5 in Assault/normal), 12b–12d, 12f–12k, 12m–12r, 12w, 13–17 (none depends on what v4 changes). v4 does **not** change the outline, the animation nor the camera
(per-function diff, 105 hunks); the stability of 3 outline cycles **remains pending** on the gate of `HOW_TO_INTEGRATE.md` §2, not on this file.

## D. Record

When each item is run, mark the OK? column and paste the exact messages of the failures. The lab also fills in `MODLOG_DRAFT.md` with the measured numbers.
