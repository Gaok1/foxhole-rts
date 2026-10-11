# BASES_AVANCADAS (forward bases) — specification (stage 1, no patch code)

Agent BASES_AVANCADAS, 2026-10-09. Read-only on the repository. This folder contains this file and four
**read-only** probes for LABORATORIO (`probes/A1..A4`, syntax checked with Lua 5.4, **not run**).
Nothing was touched in `main.lua`, shared docs, other folders, the lab or the game.
In-game messages are quoted in Portuguese, as they appear on screen.

## 0. Base, scope and legend

- **Code read:** `data/parallel/integration_rehearsal/candidate_v2/main.lua` (SHA256 `a93c1531…eda6`, the stack
  ECONOMIA > IA_LOGISTICA v2 > bmat reserve > INTERFACE v2 > PERSISTENCIA v2, **not yet applied to the real `main.lua`**).
  All lines cited are from that candidate. Stage 2 only makes sense **after** the stack is integrated
  (it depends on `rifle`/`medical` in the depots, on `logi.rebuildReserve`, on `sv.validate` v2 and on `logi.hudLine` v2).
- **Match design decision** (ROADMAP, "where soldiers come from"): soldiers spawn at spawn structures;
  main base + forward bases (`ForwardBase1`, 300 bmat); recruiting spends 1 shirt + the role's weapon from the
  structure's own stock; trucks carry shirts/weapons; abstract manpower only in Assault. Workers
  (manual collection) belong to another agent: here only the "where it spawns" interface exists (§4.3).
- **Confidence legend.** `[DATA]` read from the client (`data/`); `[OBS]` observed in a probe of an earlier batch;
  `[INF]` inference (name, analogy, pak path) **not verified on a loaded actor**; `[PROP]` design proposal of
  this document; `[?]` unknown, depends on a probe.
- bmat = `Cloth` (`MECHANICS_STUDY.md`). "Shirt" = `SoldierSupplies`; in the mod's depot it is counted in
  **units**, and a crate holds 10 (`CFG.LOGI.recipes.shirts.units`); rifle: crate of 20; bandage: crate of 50.

---

## 1. Data inventory

### 1.1 What the columns say

The `BPStructureDynamicData` table was exported with only 5 columns (`tools/export_costs.lua`): `MaxHealth` (health),
`ResourceAmounts`/`AltResourceAmounts` (cost), `RepairCost` (repair) and **`StoredItemCapacity` (stock)**.
No "spawn" column was read: **we do not know whether the table has one** (probe A1 lists the column catalog).

**Interpretation of `StoredItemCapacity = 15` `[INF]`.** The value is a capacity of **stored items**, in the same
family as the vehicles' `ItemHolderCapacity` (`BPVehicleDynamicData.carga`: TruckW = 15, which the mod already treats as 15
**crates** in `CFG.LOGI.cap`) and as `StorageBox = 15` (a storage box). The most coherent reading is
**15 crate positions (slots)**, not "15 soldiers" nor "15 shirts". It is not verified on a loaded actor
(probe A3 + rehearsal B1 read the real `ItemHolder`, if any). Mod convention `[PROP]`: **capacity = 15 crate
slots**; a slot holds 1 closed crate, so shirts take `ceil(units/10)`, rifles `ceil(/20)`,
bandages `ceil(/50)`, ammo `ceil(crates)`. This is compatible with the current targets: `want` = ammo 6 + shirts
2 crates + rifles 1 + bandages 1 = 10 slots ≤ 15 (`CFG.LOGI.want`, line 2456).

### 1.2 Relevant classes (all `[DATA]` from `data/game_costs.txt`, unless noted)

Health = `MaxHealth`; stock = `StoredItemCapacity`; cost in bmat unless noted. "BP" = path present in
`data/pak_files.txt` (existence of the asset, not of an instance).

| Class (CodeName) | Cost | Health | Stock | Build site (health/stock) | Ruin (health) | BP in pak | Note |
|---|---|---|---|---|---|---|---|
| **ForwardBase1** | 300 | 1725 | 15 | ForwardBase1BuildSite 2000/15 | DestroyedForwardBase1 4000 | `Bases/BPForwardBase1`, `…BuildSite`, `BPDestroyedForwardBase1` | target of the decision; repair 300 |
| BorderBase | 100 | 2500 | 15 | — | DestroyedBorderBase 1e8 | `Bases/BPBorderBase` | cheap candidate, role `[?]` |
| FrontierBase | 50 | 1250 | 15 | …BuildSite 2000/0 | — | **not found** | cheapest; active class not listed in the pak |
| StaticBase1/2/3 | 300/200/200 | 2000/6000/7500 | 15 | …BuildSite 500/15 | Destroyed… 1e8 | **icon only** (`MapIconStaticBase1`) | possibly the "bunker base" `[INF]` |
| TownBase1/2/3 | 200 | 7000/5000/4000 | 15 | TownBaseBuildSite 500/15 | DestroyedTownBase* 1e8 | `Bases/BPTownBase1..3` | the map's town bases |
| RelicBase1/2/3 (+RelicBaseBase) | 200/250/300 (300) | 4450/5150/5850 (1250) | 15 | …BuildSite 500/0 | DestroyedRelicBase* 1e8 | `Bases/BPRelicBase*` | |
| HomeRegionBase | — | 1e8 | 15 | — | — | `Bases/BPHomeRegionBase` | unreachable base of the home regions |
| FortBaseT1/T2/T3 | 300 / 100 / 25 concrete | 1500/2500/3500 | 15 | FortForwardBaseBuildSite 1000/15 | DestroyedFortForwardBaseT1/2/3 4000/20000/40000 | `Bases/BPFortBaseT1..3` | facilities branch (concrete is not produced) |
| GarrisonStation / 1 / 2 | 250 | 2000 | 15 | — | — | `Forts/BPFortGarrisonStation` (concrete variant: 10000, 125 concrete) | role `[?]` |
| Hospital | 400 | 2000 | 15 | — | DestroyedHospital 1e8 | `Structures/BPHospital` | |
| FieldHospital | 200 | 500 | 6 | — | — | `Structures/BPFieldHospital` | |
| SafeHouse | — | — | 0 (ruin only: `DestroyedSafeHouse`) | — | 1e8 | only `BPDestroyedSafeHouse` + icon | active row **does not exist in the table** |
| TroopShipBase | 100 | 5000 | 12 | — | — | — | phase 4 (ships) |
| Seaport / StorageFacility / StorageBox | 400 / 400 / 25 | 2000 / 2000 / 400 | 15 / 15 / 15 | …BuildSite | Destroyed… | `BPStorageFacility`… | depots, not spawn |

Useful neighbors: `BPMedicalRoomSpawnPoints` (`Forts/Templates`, a template of spawn points of the facilities' medical
room) and `PlayerStart` (23 in Deadlands, 0 in CallumsCape: `trace_regions.txt`). In `HomeRegionW` the study
records a "forward base" at ~(19557, 12293) (`MECHANICS_STUDY.md` §bench) **without the class**: it is the best
native instance to read `ItemHolder`/components (probe A3).

### 1.3 What is known and what is unknown

| Question | State | Effect on the specification |
|---|---|---|
| Cost, health, capacity, build site, ruin of ForwardBase1 | `[DATA]` | `CFG.FWD` parameters |
| Path of the active class | `[INF]` `/Game/Blueprints/Structures/Bases/BPForwardBase1.BPForwardBase1_C` (pak pattern + `_C` suffix) | A2 confirms |
| Does the class load in the hex (CallumsCape/Deadlands)? | `[?]` | A2 loads the class; B1 instantiates |
| Can it be **spawned ready** like the batch 17 refinery (health = max., `CodeName`, `BaseStructureClass`)? | `[?]` Refinery/factory: `[OBS]` yes. This class: never instantiated | B1; **plan B** below |
| Does it have a native **spawn** component/UFunction? | `[?]` | **Irrelevant for the design**: the mod spawns soldiers with `RestartPlayerAtTransform` (`spawnSoldier`, line 743), not through the structure. It only matters for risks (§4.4 R1) |
| Does it have a native `ItemHolder`/stock (and how many slots)? | `[?]` | the stock belongs **to the mod** (`dep`), as at the points; the native one only calibrates the reading of "15" |
| Footprint (collision-only bounds)? | `[?]` Total bounds include giant volumes (factory: extent 10594, batch 16) — useless | provisional `CFG.FWD.half` (600 cm) until A3/B1 |
| `TeamId` of a freshly spawned active actor | `[OBS]` CDO of Factory/Refinery = 255; batch 17 wrote `TeamId = 1` with no side effect seen | B1 tests 255 vs 1 (R1) |
| Does it accept writing to `Health` without triggering destruction/visuals? | `[?]` | by default **do not write**: the base's health belongs to the mod (§3.9) |
| Are there native base ruins in the hexes? | Callums: 30 `DestroyedStructure`, only the factory/refinery/workshop ones were named; **others not enumerated** | A3 enumerates (base/hospital ruins) |
| Role of Garrison/Hospital/Relic/Border/Frontier as spawn points | `[?]` | out of scope; they only come in after being traced (match decision) |

**Plan B (visual) `[PROP]`.** If the active class does not spawn whole, the design does not change: what matters to the game is the
**mod's record** (`fb`), not the actor. Plan B: `CFG.FWD.visual = "mesh"`, actor = `meshActor(...)` with a mesh already
used by the mod (the tent from `CFG.TENT.mesh`, scaled) + the owner's banner (`CFG.POINT_BANNER`). Cost/health/capacity
stay those of the game data. Automatic choice: `visual = "native"` only if B1 passed.

### 1.4 Lab probes

**Group A — read-only** (files in `probes/`, output only through `out(...)`, run **one at a time**, without the bot):

| Probe | When | What it closes | Caution |
|---|---|---|---|
| `A1_structure_columns.lua` | any map | the `RowStruct` column catalog and the values of the **simple** columns of 14 rows (ForwardBase1, BuildSite, Destroyed, BorderBase, FrontierBase, StaticBase1, TownBase1, RelicBase1, HomeRegionBase, Garrison, Hospital, FieldHospital, StorageBox, Factory); looks for a spawn/capacity/tier column | only simple types and 14 keys (a generic dump crashed the game on `BPAirDynamicData`) |
| `A2_base_classes.lua` | any map | does the class load? (3 candidate directories), parent chain, CDO (`TeamId`, `MaxHealth`, `Health`, `CodeName`, `BaseStructureClass`), names of properties and UFunctions that suggest spawn/stock/damage; **no SpawnActor** | `LoadAsset` brings the class into memory; does not instantiate |
| `A3_world_bases.lua` | **HomeRegionW** (native forward base), **CallumsCapeHex** and **DeadLandsHex**, one load each | base/hospital/garrison/spawn/ruin actors present, position, team, health, bounds (all and collision-only), **classes and names** of the components | do not read component properties (MasterPose/AnimClass crashed UE4SS); the `FindAllOf("Actor")` histogram is already standard (`inspect_region.lua`) |
| `A4_ground_at_points.lua` | hex, **with a match** (points created) | how many places of each point pass the placement predicate of §3.3 and how many exits they have; exits around the main base | line/sphere traces; provisional `HALF` = 600 cm |

Reading criterion: A1 and A2 define whether the catalog/CDO supports `visual="native"`; A3 gives the footprint and a real
instance (HomeRegionW); A4 says whether there is room for a base **at each point** of the hex and how many candidates remain.

**Group B — temporary writing (not read-only; needs the user's authorization like the probes of batches 16/17).**
`B1`, a spawn rehearsal of `BPForwardBase1_C` (described in the script of §5.2; no code here since it is stage 2).

---

## 2. What the mod already has and uses, and what changes in `recruit()`

### 2.1 Already exists (candidate_v2)

| Piece | Where | Used for |
|---|---|---|
| Control points, owner, capture | `points`, `addPoint` (2240), `pointStep` (2290), `pointsTick` (2395); `CFG.POINT_RADIUS=500`, `POINT_MAX=5`, spacing 2×radius; `setupPoints` uses `flatSpot` (flat ground ±80 cm in the ring) | the base's location; the ring is already validated flat ground |
| Depot per point | `logi.depotOf(pt)` (2739): `{ammo, shirts, rifle, medical, pt}`; `logi.depots()` | the forward base's stock **is** the point's depot |
| Delivery by truck | `logi.truckStep` state `toDep` (2919); lost destination → `returnCargo` (2921); `L` fixes the destination (`logi.sendTo`, 2971); `logi.needs/pickDest/nextKind` | supplying the base with shirts/rifles |
| Stock lost on enemy capture | `pointsTick` line 2416: `pt.dep[kind]=0` when the owner becomes the enemy | a forward base loses its stock once when captured |
| Refusal without stock | `recruit` (1441–1447) | "sem camisas / sem fuzis" |
| Debit only after the spawn | `recruit` (1448–1453) | a transactional contract the design keeps |
| Spawn at a point | `deployPoint()` (1409: cursor inside one of our points) + `spawnSquad(1, role, at)` (766) | explicit location selection |
| Validated ground | `logi.parkingGround` (2553, Landscape only, never a roof), `logi.parking` (2564, ring + 4 corners + sphere), `flatSpot` (4232) | placement and exits |
| Deployment with rollback | `logi.applyPlan` (2639): validates the contract, undoes everything on failure | template for building the base |
| Persistence v2 | `sv.collect/validate/preflight/infraPlan/load` (5113–5712): preflight without mutation → apply with rollback → restore | template for the base's save |
| Alert and panel | `rts.alert` (495), `logi.hudLine` (3015) with a line per depot | the base's alerts and line |
| Enemy area damage | `logi.blast(hit, radius, dmg, team)` (3150), a single call site (3923) | damage to the base by mortar |

### 2.2 What changes in `recruit(role, at)` (and what does not)

**Changes** (only with `logi.on and combat.mode ~= "assault"`, called the "logistics branch"):

1. **The soldier's origin = a spawn structure**, always. Today, without `at`, the recruit spawns **next to the squad**
   or the commander (`spawnSquad`: `ref = squad[1]`, line 771) and still debits the base: that **is** the
   teleportation the design decision forbids. In the logistics branch the spawn location comes from
   `logi.spawnSite` (§4.3): main base or forward base, at the validated "exits".
2. **No abstract manpower**: does not check nor debit `economy.manpower` (lines 1431, 1454). Manpower
   keeps existing for mortar, trench, crate, barrier, post and wire; the panel should label it as such.
3. **Refusal instead of fallback**: today a point without stock falls back to "spawns at the base" (1437–1440). In the logistics branch,
   if the cursor is **inside** a base (explicit selection), a lack of stock there **refuses with a warning** (never
   silently switches base). Outside any base, the closest one with stock is chosen (§3.6).
4. **Control points without a base stop being spawn locations** (`CFG.SPAWN.pointSpawn = false` by default;
   `true` reproduces the old behavior). It is a direct consequence of "spawn points = structures"; needs the
   user's ok (§6, decision D2).
5. **Debit**: still only after a confirmed spawn, but it moves to `logi.spawnCommit(site, role)` (one shirt; one
   rifle if the role is rifleman), with the base's ledger (§3.5).
6. `spawnSquad` gains 2 lines: with `at.exact` the soldier spawns **at the exit** (without the formation offset
   `slotFor`, which reaches 5 rows × 160 cm = 8 m behind the point) and with `z = at.Z` (the exit is already Landscape ground).
7. Defeat (line 4852 `#squad == 0 and economy.manpower < rifle.cost`) in the logistics branch becomes
   `#squad == 0 and not logi.canReinforce()` (no active structure with ≥ 1 shirt **and** no truck with
   shirts on the way).

**Does not change:** the `recruit(role, at)` signature and the keys Ctrl+1/2/3/4/0 (`at` without `.name` is still the "cursor");
the `SQUAD_MAX` limit and the single officer; the whole **legacy** branch (without logistics or Assault) — same code, same
numbers, same tests in `tools/test_orders.py` (manpower refusals, lines 359–366, 513, 579–); F6
(free squad), `newGame`/`newAssault` (`spawnSquad` without `at`), enemy waves and reinforcements, `earn`/income per
point, `CFG.WEAPONS` (costs only for the legacy branch), the channel's `env`.

---

## 3. Specification

### 3.1 Model

- **Spawn site** (`site`): either the main base (`logi.base`, a virtual depot at `rts.base()`), or a
  **forward base** (`fb`) tied to one of our control points. A control point without `fb` stays an
  **ammo/bandage** depot (and a healing/reload point), not a reinforcement one.
- **Forward base** `[PROP]`: a mod record, plus (optionally) a game actor:

```
fb = { pt = <point>, code = "ForwardBase1", x, y, z, yaw,           -- where it was placed (inside the point's ring)
       hp = 1725, maxHp = 1725,                                      -- DATA; the MOD's health (§3.9)
       actor = <actor|nil>,  exits = { {X,Y,Z}, ... }, exitI = 0,    -- native actor (or mesh); spawn exits
       dead = false, led = { rx = {}, used = {}, lost = {} } }       -- per-product ledger (§3.5)
pt.fb = fb ;  dep = logi.depotOf(pt) ;  dep.fb = fb                  -- the point's depot IS the base's stock
```

- **States** (derived, never stored): `active` (`not fb.dead` and `pt.owner == FRIENDLY`); `inactive` (point
  neutralized: no spawning, no delivery, stock kept; reactivates on recapture); `destroyed`
  (`fb.dead`: stock lost, record removed).
- **Able to reinforce** = `active` and `dep.shirts ≥ 1` (and `dep.rifle ≥ 1` if the role is rifleman).

### 3.2 How the player creates it (no new key)

**Flow `[PROP]`:** with the cursor **inside the ring of one of our points**, press **J** (today: "create point", it refuses
with "perto demais de outro ponto" in this case — the refusal becomes the hook).

1. 1st J: message `Base avançada em A: 300 bmat (fábrica tem 412). J de novo em 4 s para construir.`
   If `logi.bmat − reserve < 300`: `faltam N bmat (fábrica tem X); J de novo em 4 s reserva o bmat`.
2. 2nd J (same point, ≤ `CFG.FWD.confirm` = 4 s in real time, `GetRealTimeSeconds`): builds (§3.4) or, without bmat,
   leaves a **pending order** (§3.4).
3. J outside any point, without logistics or in Assault: behavior **unchanged** (creates a point / message).
4. J on a point that already has an `active` base: reports state and stock (no cost).

Why J and a confirmation: J is already the "territory" key; the spend is 300 bmat (the whole factory for ~2.5 min of
saturated refining) and must not happen through a click by someone who wanted to create a neighboring point.

**Alternative if the user does not want to overload J:** **Shift+J**. Checked: `SHIFT+J` is not in `GAME_KEYS`
(`tools/test_orders.py:863`, which lists only `SHIFT+ONE..SEVEN, E, F, Q, V, X`) nor registered by the mod
(`RegisterKeyBind` 6244–6300: `SHIFT+F4/F5/F6/L/RMB/F7`). It would require adding `"SHIFT+J"` to the expected set
of `registered` (line 874) and a line in `MANUAL_TEST.md`/README/F5 help. I do not recommend Ctrl+number key:
Ctrl+1..9,0 are all in use.

**Keys checked:** J already registered (6283), does not collide with the game (`J` ∉ `GAME_KEYS`); no new key in the
main recommendation ⇒ `registered` and the key test do not change.

### 3.3 Where it can be placed

All conditions must hold at the time of the 2nd J (and again when running a pending order):

1. `logi.on`, `combat.mode ~= "assault"`, `rts.active`, local authority.
2. Cursor inside the ring (`POINT_RADIUS`) of a point with `owner == FRIENDLY` and **without** `fb`.
3. `#fbs active+inactive < CFG.FWD.max` (3; `[PROP]`, ≤ `POINT_MAX` = 5).
4. **No live enemy inside the point's ring** (`presence(enemies, pt) == 0`): no building under attack.
5. **Closer to the front than to the rear `[PROP]`:** the point is ≥ `CFG.FWD.minFromBase` (3000 cm) from the main
   base **or** ≤ `CFG.FWD.maxToEnemyPoint` (4000 cm) from an enemy point; avoids buying a "forward base" glued
   to the base. (The `setupPoints` points sit 1400–2400 cm from the base: **the rule makes the default starting point not
   qualify** unless there is an enemy point nearby; parameters to calibrate in the lab.)
6. **Surface validated as in batch 17 (`logi.parkingGround`):** the center and 8 points at `HALF` must be
   **Landscape** (never a roof, vehicle or prop), `|dz| ≤ maxSlope` (60) relative to the center and `≤ maxHeight` (250)
   relative to the point; a sphere sweep of radius `HALF/2` free on the movement channel; away from the mod's barriers,
   trenches, posts and wires (`structures`, `S.trenches`, `S.tents`, `S.wires`) by `HALF + their radius`.
   Search: centers at 0 / 150 / 300 cm from the point's center (1 + 8 + 8 candidates), with **yaw** facing the nearest
   enemy (`fort.facing(p, enemies)`, 4324). The first that passes wins. None → refusal with a reason.
7. **Exits:** the candidate needs ≥ `CFG.FWD.minExits` (3) valid exits: points on a ring of `half + 200` cm
   (8 angles), Landscape ground, `|dz| ≤ 2×maxSlope`, free capsule sphere. Exits are stored in `fb.exits`
   and **never** recomputed with `groundZ` (the Visibility channel hits roofs; it is the batch 16 bug).
8. Budget (§3.4) and no `fb` yet at the point.

Provisional `HALF` 600 cm `[?]` until A3/B1 measure the footprint of `ForwardBase1`. Probe A4 already counts the
valid candidates per point with that value.

### 3.4 Cost and transaction (rollback)

**Currency `[PROP]`:** the **factory's production bmat** (`logi.bmat`), 300 per base (`[DATA]`), respecting the
truck reserve: requires `logi.bmat − logi.rebuildReserve() ≥ 300`. It does not use the deployment wallet (`S.deploy`,
1100): that is a single-use **scenario** budget and the v2 save requires `spent == Σ cost(built)` (`sv.validate`,
line 5380) — adding bases there would break that invariant. Using `logi.bmat` also makes the debit **persist
by itself** (`logi.snapshot().bmat`). The base really competes with the crates (an economic trade-off).

**Transaction (always in this order; any failure undoes everything and does not debit):**
1. Preflight without mutation: all of §3.3 + a loadable class (`LoadAsset`) when `visual="native"`.
2. Actor spawn (`world():SpawnActor(cls, pos, rot)`); asserts: valid, `not bActorIsBeingDestroyed`, position
   within < 100 cm / rotation within < 1° of the request, and (native) `Health == MaxHealth == 1725`, expected `CodeName`
   `[?]` (B1 confirms). Failure → `K2_DestroyActor` of whatever spawned.
3. Create `fb`, `pt.fb`, `dep.fb`; `dep` starts **empty** (the purchase is of the structure, not of the stock).
4. **Only then** `logi.bmat = logi.bmat − 300`, counters, alert/warning.
The same discipline as `logi.applyPlan` (2639–2683) and batch 17 ("does not debit nor clear the match on failure").
Reuse: extract the common spawn+asserts core into `logi.fwdSpawn(site)`, also used by the save's restore.

**Not enough bmat → pending order `[PROP]`** (`logi.fwdOrder = {pt, cost, t0}`; one at a time): the 2nd J records
the order and the factory **stops starting recipes** while `logi.bmat − truck_reserve < cost`
(`logi.rebuildReserve()` now adds the order's `cost`, the same mechanism as the `reserva_bmat` patch; that is why
it also shows as `guarda N bmat` in the panel). When the bmat arrives, `logi.tick` builds on its own (revalidates §3.3;
if the point was lost, there is an enemy in the ring, or `CFG.FWD.pending` = 180 s passed, it cancels with a warning and frees the
factory). A destroyed truck has priority (its rebuild does not depend on the order). Reason: without this the base
would never be purchasable under continuous demand — the same threshold defect (recipe 80 < truck 100) that the
finishing proved for the trucks (`logistics_ai/finishing/REPORT.md` §2).

### 3.5 Own stock and capacity

- Stock = the point's `dep.ammo/shirts/rifle/medical` (already existing). **Capacity `[PROP]`** = 15 slots
  (`CFG.FWD.cap`, `[DATA]` 15; interpretation in §1.1). `logi.slotsUsed(dep)` =
  `ceil(ammo) + ceil(shirts/10) + ceil(rifle/20) + ceil(medical/50)`.
- The main base has **no** cap (current behavior), `CFG.FWD.baseCap = nil`.
- **Truck cargo limited by space:** in `truckStep` (state `idle`, 2899–2911) the destination's free space is
  `cap − slotsUsed(dest) − (crates already on the way to dest)`; `wanted` (including with `L` fixing it: `wanted = stock`,
  line 2904) does not exceed it. Since only trucks add and the space is reserved at loading, **the arrival always
  fits**; the save is validated against the cap (§3.11).
- **Shirts/rifles only for places that spawn soldiers:** `logi.needs(dep)` zeroes `shirts` and `rifle` for a depot that is not
  `spawnCapable` (main base or an active `fb`); a point without a base only receives ammo/bandages. Deliberate side
  effect: shirt production now scales with **bases**, not with points. `nextKind` now divides by
  how many capable depots exist for these two products (a 1-line change, 2782).
- **Per-base ledger** (test and lab oracle, `logi.fwdAudit()`): per product,
  `received + initial_from_restore == stock + consumed + lost`. Updated in `logi.moveCargo` (2788), in
  `logi.spawnCommit` and in `fwd.lose`. Not written to the save (reinitializes with the stock read).

### 3.6 Selecting the spawn point

`logi.spawnSite(role, cursor, opts)` (pure, no side effect, §4.3), in the logistics branch:

1. **The role's recipe:** `CFG.SPAWN.roles[role] = {shirts=1, rifle=0|1, sites=...}`. A role without an entry → refusal
   (fail-closed). Today only `rifle` consumes a weapon (`rifle=1`); `mg`, `sniper`, `medic`, `officer` consume **only a shirt**
   — an **explicit abstract bonus**: there is no MG/precision rifle/pistol crate in the mod (MGW costs 25 rmat, which the
   chain does not produce; ECONOMIA refuses to use RifleW for them).
2. **Candidates** = main base + `fb` in state `active` (+ own points with a depot, only if
   `CFG.SPAWN.pointSpawn`). Each needs `exits` (the main base computes its own in `logi.start`; if it does not
   find ≥ `minExits`, it uses the legacy offset and records the warning).
3. **Explicit selection:** if `cursor` is ≤ `POINT_RADIUS` from a candidate's center (the base/point ring), **only it**
   counts. No shirt/weapon there → refusal: `sem camisas na base A (estoque 0); mova o cursor para fora das bases para
   o mais próximo com estoque`.
4. **Automatic selection:** otherwise, among the candidates **with stock** for the role, the one with the smallest
   `flatDist(ref, candidate)`, with `ref = cursor` or, without a cursor, `squadCenter()` or, without a squad, the enemy point
   closest to the base (the "front") or `rts.base()`. None with stock → refusal with the closest one's reason.
5. Output: `site.at = {X,Y,Z,exact=true}` = the base's next exit in round-robin (`exitI`).

### 3.7 Recruiting in the logistics branch (complete flow)

`recruit(role, at)`: authority → `SQUAD_MAX` → single officer → `site, why = logi.spawnSite(role, at-or-cursor)` →
refuse with `notify(why)` if `nil` → `spawnSquad(1, role, site.at)` → if `< 1`: **nothing debited**, returns `false` →
`logi.spawnCommit(site, role)` (revalidates the stock; debits 1 shirt and, if rifleman, 1 rifle; ledger; `notify` with the
base's name and the remaining stock) → `true`. `economy.manpower` is not touched.

### 3.8 Logistics (effect on what already exists)

No new key: `L` over the base's ring sends the next truck to it (`logi.sendTo` already tests `flatDist(c, d) ≤
1.5×POINT_RADIUS` over the depots); `Shift+L` (priority) covers shirts/rifles (ECONOMIA). `truckStep` toDep
validates the destination through `d.pt.owner == FRIENDLY` (2921): **still correct** for `fb` (inactive ⇒ the truck comes back with the cargo),
because the base's depot is the point's. A base destroyed with a truck on the way: the point is still ours, so the
truck **delivers only ammo/bandages** and the shirt/rifle crates left in the cargo go back to the factory
(`returnCargo`, credit only on physical arrival, ESTRADAS contract) — implement as: on arriving at a depot that is not
`spawnCapable`, return the `shirts`/`rifle` of the `cargo`.

### 3.9 Destruction, loss and capture

A single entry point, `logi.fwdLose(fb, why)` (idempotent through `fb.dead`):
1. computes and records what is lost (ledger: `lost`); zeroes `dep.shirts/rifle/ammo/medical` **once**;
2. destroys the actor (`K2_DestroyActor`, then `fb.actor = nil`) and, if possible, creates the ruin
   `BPDestroyedForwardBase1_C` (best effort; a failure only records) kept in `S.fwdRuins` (destroyed in `logi.reset`);
3. `pt.fb = nil`, `dep.fb = nil`; alert `rts.alert("perdido", pt, "BASE AVANÇADA A destruída: perdeu N camisas e M
   fuzis")`.

Damage sources (`fwdHit(fb, amount, why)`):
- **Point captured by the enemy** (`pointsTick`, branch `owner == ENEMY`, 2411–2417): calls `fwdLose(fb,"capturada")`
  *instead of* the direct zeroing (which stays as is for points without a base). The stock was already zeroed here.
- **Enemy mortar** (`logi.blast`, 3150): for `team == ENEMY_TEAM`, a base within `radius×1.5` takes
  `dmg × CFG.FWD.blastMul` (2, like the truck). With `CFG.MORTAR.dmg=75` and 2 shells per salvo: 300/salvo ⇒ ~6 salvos
  for the 1725 HP. `[PROP]`, calibrate.
- **Siege by proximity**: outside v1 (`CFG.FWD.siegeDps = 0`): an enemy in the ring without an ally already captures the point in
  ≤ 10 s, before any health damage.
- The native actor's health is **not written** (no `OnRep_Health`, no damage visuals) until B1 proves it is safe.

**Point neutralized** (`owner → nil`): base **inactive**, nothing is lost; on recapture, it goes back to `active` with the stock
it had. **Point recaptured after `destroyed`:** no base; the player can rebuild (J, 300 bmat again).
**Lost once, without duplicating:** `fb.dead` blocks a second `fwdLose`; the legacy capture zeroing runs over
already-zero stock; a truck in transit does not "resurrect" stock because the credit goes to the point's `dep` (without a base,
`spawnCapable` false ⇒ shirts go back).

### 3.10 Enemy AI

**Proposal: the enemy does NOT build forward bases in v1; it uses the same stock rule, aggregated.**
Coherence with `logistics_ai` v2: the enemy already has the rule "paid soldier = 1 shirt + 1/6 of an ammo crate" at the
**front** (`CFG.ECHAIN`, `logi.eConsume/eAfford/waveCut`, stock `en.front`, 2 ammo + 10 starting shirts), and the
spawn location of reinforcements is already an **enemy point** (`ai.source`, 4808; waves in `waveSpawnPoint`). That is, the
enemy equivalent of a "forward base" already exists: *enemy point as the exit + the front's aggregated stock as the
stock*. Cutting a convoy reduces the shirts (already implemented); taking enemy points removes the exit locations (`ai.source`
without a point ⇒ no reinforcement). Justification for not building: the AI has no positioning nor building decision
(`ai` only reinforces by point), the balance gain is nil in the "small region" scope, and adding stock per enemy
point would require reopening the closed ledger (`eAudit`) and the `elogi` v1 schema. **Assumed and declared asymmetry:** the
player spends bmat on a base and may lose it; the enemy has "free" exits at the points it holds (lost when
they are lost). **v2 `[PROP]`:** split `en.front` per enemy point (each point becomes a stock) and make the enemy
"rebuild" a base when retaking a point, paying bmat from the rear — only after the lab calibrates v1.
Assault: everything abstract, as today.

### 3.11 Persistence

An **additive** extension of the v2 schema (without bumping `CFG.PERSIST.version`), with its own version like `infra`/`elogi`:

```
fwd = { version = 1, list = { { pt = <index in d.points>, code = "ForwardBase1", x, y, z, yaw, hp }, ... } }
```

- Only **live** bases (active/inactive). A destroyed one is not written (the ruin is cosmetic). Never an actor, address or exit:
  exits are **recomputed** on restore, through the same predicate, in the new world.
- **Stock**: already goes in `logi.snapshot().pts[i]` (`a,s,r,m` per point index). Do not duplicate.
- **bmat**: already goes in `logi.snapshot().bmat`. A pending order is **not** saved (cancels on load; warned).
- `sv.validate`: `known.fwd = 1`; `version == CFG.PERSIST.fwdVersion`; `#list ≤ CFG.FWD.max`; each record:
  exact fields (an unknown field = refusal), `pt` an integer in `1..#d.points` and **unique**, `code == "ForwardBase1"`,
  finite coordinates `≤ maxCoord`, `0 < hp ≤ maxHp`, within ≤ `POINT_RADIUS` of the saved `pt`; and the stock of `logi.pts[pt]` ≤
  `cap` in slots. `fwd` without `logi` ⇒ refusal. **Policy:** an error in `fwd` **refuses** the whole save (like `infra`),
  unlike `elogi` (which is regenerable): discarding `fwd` would erase the player's power to reinforce.
- Read by an old mod: `campo desconhecido: fwd` ⇒ fail-closed refusal (intentional).
- `sv.preflight` (without mutation): loadable class, coherent `visual`, Landscape ground at the saved XYZ and exits ≥ `minExits`
  (same predicate, `PERSIST.tol` tolerance of 200 cm on the point's position). Failure ⇒ "Continuar recusado".
- `sv.load`: preflight → `logi.fwdSpawn` of each record into a **staging area `S.fwdStage`** (not zeroed by
  `logi.reset`) with a joint rollback with the infra's `plan.apply` → `sv.restore` (clears, recreates points) → `sv.verify` →
  `logi.restore` (stocks by index) → **`logi.fwdBind(d.fwd)`** binds each staged one to its `pt` by index and recomputes
  exits. A bind failure ⇒ destroys the stage and marks `sv.degraded` ("base avançada A não refeita"), autosave suspended
  (existing mechanism); the point's stock stays in the depot.
- `sv.collect`: `fwd = logi.fwdSnapshot()`; `clearSquad`/`newGame` clear bases through `logi.reset`.

### 3.12 Panel and alerts

One short line per base inside the depot block of `logi.hudLine` (panel v2 already prints
`"%s | munição %.0f | camisas %d%s"`, 3041–3047). A pure function `logi.fwdLine(dep)` `[PROP]` (≤ 96 characters):

```
base       | camisas 30 | fuzis 0  | slots —    | reforça: só sem fuzil (sem fuzis)
A [BASE]   | camisas 12 | fuzis 3  | slots 9/15 | reforça: tudo
B [BASE]   | camisas 0  | fuzis 0  | slots 4/15 | reforça: NÃO (sem camisas)
C [BASE]   | camisas 8  | fuzis 1  | slots 7/15 | INATIVA (ponto neutro)
```
Ammo/bandages stay on the depot's current line (do not duplicate). Pending order: `Fábrica | guarda 300 bmat para base
avançada em A (bmat 140)`. Existing alerts: "ponto sob ataque" (already covers the base), `perdido` on destruction; a refused
reinforcement goes to `notify`. Color/icon in the world: the point owner's banner (`pointVisual`) is enough in v1.

---

## 4. Contracts and risks

### 4.1 Technical limits of `main.lua`

- **Top-level locals: none new** (candidate_v2: 178 by the compiler, 175 by the regex; limit 200). Everything in
  `logi` (`logi.fwd*`, `logi.spawn*`, `logi.slotsUsed`, `logi.canReinforce`, `logi.fwdLine`), `CFG.FWD`, `CFG.SPAWN`,
  `S.fwdStage/fwdRuins/fwdConfirm`, `rts.fwdKey`. No local named `ai/sv/fort/rts/anim/S/logi`
  (`tools/check_globals.py` is scope-insensitive).
- **The channel's `env`** (6144–6169): `logi`, `rts`, `sv`, `CFG`, `S` are already there; the new functions are reachable without touching
  `runCommandFile`. **Not** in `env`: `cursorPoint`, `squadCenter`, `groundZ`, `surfaceZ`, `flatSpot`. That is why
  `logi.spawnSite` **receives the cursor as a parameter** (`recruit` passes `cursorPoint()`), and placement uses functions that
  are already reachable or internal to the module. `recruit` is already in `env`.
- **Cache by address (the `anim.untrack` rule)**: `fb.actor` is the only actor kept; always check
  `valid(a) and not a.bActorIsBeingDestroyed` before using it (`IsValid` stays true until GC); on every destruction
  `K2_DestroyActor` followed by `fb.actor = nil` in the same block; **no table indexed by actor/address**, no
  `RegisterHook` on the base's class, no per-frame writes to the actor (the health belongs to the mod). The save never writes an actor
  (`sv.pure` already refuses userdata). Soldiers spawned in the logistics branch go through the usual `spawnSoldier` (which registers
  the `anim`), so the soldiers' `untrack` rule does not change.
- **Per-frame cost:** placement does ~25 candidates × (9 ground traces + sphere) + 8 exits ≈ 250–300 UFunction
  calls, on the 2nd J (a single event). Earlier measurements: route planning 36–54 ms synchronous; **acceptable once**,
  but measure in the lab (L5). If it goes above ~60 ms, slice it into a per-frame state machine (not a coroutine:
  UFunctions do not run in coroutines).
- **GC/`Registry`:** the base creates no Lua callbacks. The pending order runs inside `logi.tick` (already per frame).

### 4.2 Likely conflicts with manual collection (another agent)

They touch `logi.deploy`/`applyPlan`, `logi.start` (starting stock, trucks that stop existing at the start)
and worker spawning (the base's shirt). Map of contact points (↔ = both edit; → = only me):

| Point | Me | Them | Rule |
|---|---|---|---|
| `recruit` legacy branch | I do not touch | must not touch | legacy branch intact; I only enter through `logi.spawnSite` |
| `logi.start` | → 2 lines: `logi.base.exits = logi.exitRing(...)`, `logi.fwd = {}` | ↔ starting stock, trucks | additive and separate lines, no reordering |
| `logi.reset` | → destroy `fb.actor`, `S.fwdRuins`, order | ↔ worker cleanup | each adds its own `pcall` block |
| `logi.base.shirts` | consumption through `spawnCommit` | worker consumption | **a single debit**: both use `spawnCommit` (single ledger) |
| `logi.deploy/applyPlan/wallet` | **I do not touch** | ↔ | bases use `logi.bmat`, not the wallet |
| `logi.needs/nextKind` | → shirts/rifle only for `spawnCapable` | ↔ if they produce "worker" as demand | the main base's shirt demand includes workers: they declare it in `CFG.SPAWN.roles.worker` |
| `CFG.WEAPONS`/`roleFor` | I do not touch | ↔ the `worker` role | they go into `CFG.SPAWN.roles`, not `CFG.WEAPONS` |
| `sv.collect/validate` | → `fwd` | ↔ worker state | each adds its own `known` key, its own validator, without touching the other's |
| `waveTick` defeat | → `canReinforce` | ↔ does a worker count as a "spent shirt"? | `canReinforce` looks only at structures with shirts; a live worker does not prevent defeat |

### 4.3 Common interface `logi.spawnSite` / `logi.spawnCommit`

```
site, why = logi.spawnSite(role, cursor, opts)
  role   : key of CFG.SPAWN.roles  (rifle|mg|sniper|medic|officer|worker|...). Missing key => nil,"função sem receita"
  cursor : {X,Y[,Z]} or nil           (the caller passes cursorPoint()/nil; the function does not read the mouse)
  opts   : { sites = {"base","fwd"}   -- restricts types (default: roles[role].sites or all)
             explicit = bool|nil }    -- nil: decides by the cursor's position (§3.6)
  returns: site = { dep = <depot>, kind = "base"|"fwd", name = <string>, fb = <fb|nil>,
                    at = {X,Y,Z,exact=true}, need = {shirts=1, rifle=0|1}, explicit = bool }
           or nil, reason (text ready for notify)
  PURE: changes neither stock, nor the exit round-robin, nor creates an actor. Calling it twice is harmless.

ok, why = logi.spawnCommit(site, role)
  called ONCE, after the confirmed spawn (synchronous on the game thread). Revalidates the stock (never negative),
  debits need.shirts/need.rifle from site.dep, advances site.fb.exitI, updates the ledger. false => did not debit (log).

logi.canReinforce() -> bool          -- there is an active structure with >=1 shirt, or a truck carrying shirts
CFG.SPAWN = { pointSpawn = false,
              roles = { rifle={shirts=1,rifle=1}, mg={shirts=1}, sniper={shirts=1}, medic={shirts=1}, officer={shirts=1} } }
              -- workers: the other agent adds  worker={shirts=1, sites={"base"}}
```
Contract for **every** caller (soldier, worker, future roles): decide with `spawnSite`, create the actor, only
then `spawnCommit`; a creation failure ⇒ nothing debited and no "half-spawn"; never debit `dep.shirts` directly.
In the legacy branch (`logi.on` false or Assault) `spawnSite` returns `nil, "ramo legado"` and the caller follows the old
path — so manual collection can use the interface without worrying about the mode.

### 4.4 Risks

| # | Risk | Evidence/state | Mitigation |
|---|---|---|---|
| R1 | An active actor with an allied `TeamId` being treated by the game as a native respawn point (soldiers are `HeadlessPlayerController` with `ClientStartRespawnTimer` hooks, lines 6046–6071) | `[?]` never instantiated; refinery/factory with TeamId 1 showed no effect, but they have no spawn | B1 tests `TeamId` 255 vs 1 and watches the log and dead soldiers for 60 s; the visual plan B (mesh) removes the risk |
| R2 | Unknown footprint ⇒ base inside a building/collision | total bounds useless (batch 16) | A3 (collision-only) + sphere sweep + exits; conservative `HALF` |
| R3 | `SpawnActor` returning `IsValid` already being destroyed | `[OBS]` batch 16 | assert `bActorIsBeingDestroyed` and position/health, like `applyPlan` |
| R4 | Ground trace hitting a roof | `[OBS]` batch 16 | Landscape-only (`parkingGround`), exits never through `groundZ` |
| R5 | Balance: without teleportation and without manpower, the start of the game (rifle = 0 at the base, ECONOMIA) may freeze reinforcement | `logi.base.rifle = 0` at start | decision of the ECONOMIA/collection owners (starting stock); the specification only guarantees a clear refusal |
| R6 | The order's bmat reserve freezing the factory for 180 s and draining ammo | new proposal | `pending` cap, explicit cancellation, panel shows `guarda 300`; test L7 |
| R7 | The `needs` change (shirts only for capable depots) altering ECONOMIA's tests | `test_integration.py` uses `L.pin` (does not depend on `needs`) | run the stack battery; adjust the affected asserts |
| R8 | J with 2 functions confusing the player | | confirmation with cost text; alternative Shift+J (§3.2) |
| R9 | Order: depends on the v2 stack being applied | | stage 2 only over an already integrated `main.lua`; build with unique fail-closed anchors |
| R10 | Wrong "15 slots" interpretation | `[INF]` | `CFG.FWD.cap` parameter; only affects the cargo cap; A3/B1 compare with `ItemHolder` |

---

## 5. Tests

### 5.1 Offline plan for stage 2 (lupa, the whole `main.lua` in memory, like the other folders)

Files expected in the folder: `build_patch.py` (unique fail-closed anchors, over the integrated stack),
`test_bases_avancadas.py`, `candidate/main.lua`. Mocks only at engine boundaries (traces, spawn, structures).

| # | Test | Coverage |
|---|---|---|
| T1 | Regression: `tools/test_orders.py`, `check_globals.py`, 36 persistence cases, `economy/test_integration.py`, `logistics_ai/test_logistics_ai_v2.py` | legacy branch unchanged; ≤ 178 locals (compiler) |
| T2 | Pure `spawnSite`: changes neither stock nor `exitI`; called 2× gives the same | contract |
| T3 | Selection: explicit (cursor in the ring) refuses without fallback; automatic picks the closest one **with stock**; tie; without a cursor uses `squadCenter`; a base without exits → legacy offset + warning | §3.6 |
| T4 | A role without a recipe (missing `worker`) refuses; `worker` with `sites={"base"}` never spawns at an `fb` | interface |
| T5 | Recruiting a rifleman: debits 1 shirt and 1 rifle only if `spawnSquad` returns 1; returns 0 ⇒ stock intact; MG/sniper/medic/officer only a shirt | transaction |
| T6 | The logistics branch does not touch `economy.manpower`; legacy and Assault identical (zero state diffs) | §2.2 |
| T7 | Construction: refusals for each condition of §3.3 (no logistics, Assault, neutral/enemy point, enemy in the ring, limit, near the base, ground = roof/vehicle, without ≥ 3 exits, overlapping order) without a debit and without an actor | §3.3 |
| T8 | Rollback: spawn returns `IsValid` being destroyed, `Health ≠ 1725`, displaced position ⇒ actor destroyed, bmat and `pt.fb` intact | §3.4 |
| T9 | Debit only at the end: bmat−300, `fb` created, depot empty; repeating J on the same point does not duplicate nor charge | §3.4 |
| T10 | Pending order: the reserve stops the factory; with continuous demand bmat reaches 300 and builds on its own; cancels by timeout/lost point/enemy; a destroyed truck has priority; the bmat ledger closes | §3.4 |
| T11 | Capacity: cargo limited by free slots minus what is on the way, including with `L`; never > 15; `slotsUsed` with partial crates | §3.5 |
| T12 | `needs`/`nextKind`: a point without a base only ammo/bandages; a base receives shirts/rifles; shirts scale with the number of bases | §3.5 |
| T13 | Destruction: enemy capture, mortar (`logi.blast` with `team=ENEMY`), a 2nd idempotent call (stock lost once, ledger `lost`), a truck in transit returns shirts to the factory only on arrival | §3.9 |
| T14 | States: neutralize ⇒ inactive (stock kept, no spawn, no delivery), recapture ⇒ active; rebuild after destroyed | §3.1/3.9 |
| T15 | Defeat: `#squad==0` with a supplied base does not lose; no shirts anywhere and no truck ⇒ defeat | §2.2 item 7 |
| T16 | The per-base ledger closes after a random sequence (like `eAudit`: 25 seeds × 600 steps) | conservation |
| T17 | Save: round trip on a new load (actors rebuilt, stock by index, exits recomputed), 3× repetition without duplicating, `fwd` with an unknown field/future version/duplicated `pt`/invalid hp/stock > cap/without `logi` ⇒ refusal keeping the match and the file; spawn failure in the preflight and after it (joint rollback with `infra`); an old mod refuses | §3.11 |
| T18 | Mutation: remove the `bActorIsBeingDestroyed` test, the debit-after-spawn, `fwdLose`'s idempotency, the slot cap, `spawnSquad`'s `exact` — the suite must fail | non-vacuous tests |
| T19 | Keys: no new key (J recommendation); with the alternative, `SHIFT+J` ∈ `registered` and ∉ `GAME_KEYS` | `test_orders` |
| T20 | Read-only `hudLine` (snapshot before/after equal); `fwdLine` ≤ 96 characters; states | §3.12 |

### 5.2 Lab script (never with the bot active; one step per load; game closed when done)

| # | Step | Type | Expected output / criterion |
|---|---|---|---|
| L0 | `A1`, `A2` in HomeRegionW | read-only | columns and CDO; decides `visual` and whether there is a spawn column |
| L1 | `A3` in HomeRegionW, CallumsCapeHex, DeadLandsHex | read-only | class of the native "forward base", components, colliding bounds → `HALF`; base ruins; **no** crash |
| L2 | Match with logistics; `A4` | read-only | ≥ 1 valid candidate with ≥ 3 exits per point (or adjust `HALF`/ring); exits of the main base |
| L3 | **B1** spawn rehearsal of `BPForwardBase1_C` (with authorization) at a validated XYZ: read `Health/MaxHealth/CodeName/TeamId/BaseStructureClass`; 255 vs 1; watch `UE4SS.log` and a dead soldier for 60 s; `K2_DestroyActor`; spawn of `BPDestroyedForwardBase1_C`; screenshot (`um win shot`); spawn ms | temporary writing, undone | spawns whole (1725) or adopts plan B; no `Registry`/native respawn; no residual actor |
| L4 | Real match in the hex: reinforcement from the main base (the actor spawns at the exit, not next to the squad), refusal without a shirt/rifle | validation | messages; ledger; soldier not on a roof |
| L5 | J, J: build a base on the point with bmat; measure ms; the soldier spawns at the base's exit; round-robin of the 3+ exits | validation | debit only after spawn; frame without a hitch; no soldier on a roof/wall |
| L6 | The truck (`L`) carries shirts/rifles to the base and it starts reinforcing; 15-slot limit | validation | cap respected |
| L7 | Pending order with continuous consumption; panel `guarda 300` | validation | builds on its own; no prolonged ammo starvation |
| L8 | The enemy takes the point: base destroyed, stock lost once, ruin/actor removed; enemy mortar | validation | no residual actor; the ledger closes |
| L9 | Save (30 s) → close → Ctrl+F6 on a new load: base rebuilt in the same place, correct stock and HP, without duplicating; a tampered save refuses | validation | `PERSIST.tol` tolerances |
| L10 | Long (≥ 10 min, 3 bases, continuous reinforcements): `UE4SS.log` without errors, stable actor memory, no native crash | stability | gate; remember that outline stability is still pending (MODLOG) |

General prerequisite: the MODLOG stability pause ("do not widen features before isolating the crash") still holds; this
specification does not authorize opening the lab nor starting stage 2.

---

## 6. Open decisions (for the user/coordinator)

- **D1.** Create the base with **J over one's own point + confirmation** (recommended, no new key) or with **Shift+J**.
- **D2.** A control point without a base **stops being a reinforcement location** in the logistics branch (consequence of the design
  decision), with `CFG.SPAWN.pointSpawn` to go back to the old behavior.
- **D3.** Pay with the **factory's `logi.bmat`** + a pending order with a reserve (recommended) or refuse when bmat is short.
- **D4.** Bases only **on one's own control points** in v1 (reuses the depot, save by index, capture); free bases
  (outside points) are left for later.
- **D5.** The enemy **does not build** bases in v1 (§3.10), with the declared asymmetry.
- **D6.** Assault without bases and with abstract manpower (kept).
- **D7.** `StoredItemCapacity = 15` read as **15 crate slots** (§1.1) until a probe proves otherwise.
