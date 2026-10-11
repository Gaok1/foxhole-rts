# Study of Foxhole's mechanics (roadmap phase 2)

Source: the lab client itself (2026-10-09). Nothing here comes from the server or the internet.

## Native combat — context observed on 10/10

SimVehicle's damage branch requires an existing `WarGameInstance.ServerSettings`. In
offline HomeRegionW that reference was null, although Role3/HasAuthority and SimGameMode
were valid; the native guard explains return 0/HP 900 in the earlier oracles.
Do not conclude native damage is impossible nor fabricate a server/change the guard.
Reproducible preflight: `tools/preflight_native_damage.lua` (read-only).
CDOs: `tools/export_damage_types.lua`; both run through the command channel.
Evidence: `data/trace_context_damage_native.txt`, `data/trace_export_types_damage.txt`.

The static authoritative flow found belongs to **HeavyMachineGunItemComponent**, not to
all weapons: trace -> authority -> DamageAttributes -> DamageableActor -> damage.
Rifle/ABI/equipped instance/dynamic proof still missing. Reports in
`data/trace_firing_investigation.md` and `data/trace_damage_vehicle_investigation.md`.

## How the data was read
- **File list:** the index of `War-WindowsNoEditor.pak` (version 8) is not encrypted; the 24,352 paths
  `.uasset/.umap` are in `data/pak_files.txt` (extracted with a regular expression over the index).
- **Tables:** `LoadAsset("/Game/Blueprints/Data/<table>.<table>")` and `DataTable:ForEachRow` through the command
  channel. Columns from the `RowStruct` (`ForEachProperty`); recipes use `ProductionResource {ItemCodeName, Quantity}`;
  structure/vehicle costs use `ResourceAmounts {Resource, OtherResources[]}`, with elements
  `CodeNameSmallQuantity {CodeName, Quantity}`. Result in `data/game_costs.txt`.
  **Batch 16 fix:** the old probe confused these schemas and swallowed the error, leaving empty costs.
  Reproducible exporter `tools/export_costs.lua`, offline test `tools/test_costs.py`; an error now stops,
  it does not become zero cost. Crate recipes did not change.
- **Caution:** a generic dump (reading every property of every row) crashed the game on the table
  `BPAirDynamicData`. Read only known columns with simple types.

## What the client has
- **Maps:** the 54 regions of the world (`Maps/Master/*Hex.umap`: Callahan's Passage, Deadlands, Westgate...) and the
  two home regions (`HomeRegionW`, `HomeRegionC`).
- **Vehicles:** trucks (cargo, resource, fuel), flatbed truck, harvester, ambulance, bus,
  armored cars, light/medium/battle/super tanks, half-track, field artillery, motorcycles and bicycles, trains
  (locomotive, cargo cars, hospital, artillery), barge, freighter, motorboat, gunboats, large ships,
  landing ship, submarine/minelayer and planes (fighter, bomber, dive bomber, torpedo bomber, paratrooper).
- **Structures:** refineries, factories (small arms, ammunition, planes, vehicles), mines, resource fields,
  depot, port, hospital, forward base, garrisons, bunkers, trenches, wire, sandbags.

## Internal material names
| Internal | In game |
|---|---|
| Metal | Salvage |
| Cloth | Basic materials (bmat) |
| Wood | Refined materials (rmat) |
| Explosive / HeavyExplosive | Explosive powder / heavy explosive powder |
| Components, Sulfur | Components, sulfur |

## Crate costs (factory)
| Crate | Cost | Quantity | Time (s) |
|---|---|---|---|
| Rifle (RifleW) | 100 bmat | 20 | 70 |
| Rifle ammo | 80 bmat | 40 | 50 |
| Machine gun (MGW) | 25 rmat | 5 | 100 |
| MG ammo | 100 bmat | 20 | 70 |
| Grenade (GrenadeW) | 100 bmat + 40 explosive | 20 | 100 |
| Bandage | 80 bmat | 50 | 40 |
| First aid kit | 60 bmat | 10 | 35 |
| Soldier supplies (shirts) | 80 bmat | 10 | 80 |
| Mortar / mortar ammo | 100 bmat + 25 rmat / 60 bmat + 70 explosive | 5 / 15 | 50 / 100 |
| Wire / sandbags (materials) | 15 bmat | 5 | 15 |
| Bunker supplies | 75 bmat | 150 | 190 |

Ammunition (`BPAmmoDynamicData`): rifle 45 damage, MG 55, SMG 27, grenade 200 (radius 5.5 m), mortar 300 (5 m),
light artillery 400 (11 m).

## Construction costs checked (batch 16)
Town factory (`Factory`): 400 bmat, 2000 HP; refinery (`Refinery`): 400 bmat, 2700 HP;
Warden truck (`TruckW`): 100 bmat, 900 HP. Facilities have their own rows/costs in the table;
they do not inherit the cost or the recipes of the town factory. These numbers come from the installed client.
The cost alone does not demonstrate a working offline construction flow.

## Vehicles (`BPVehicleDynamicData`)
| Vehicle | Health | Fuel | Use/s | Cargo |
|---|---|---|---|---|
| Truck (TruckW) | 900 | 100 | 0.025 | 15 |
| Resource truck | 1000 | 120 | 0.038 | 20 |
| Harvester | 1250 | 200 | 0.150 | 15 |
| Ambulance | 750 | 100 | 0.025 | 9 |
| Armored car (ArmoredCarW) | 1150 | 150 | 0.050 | 1 |
| Light / medium tank | 1950 / 3100 | 300 / 325 | 0.19 / 0.23 | 1 / 3 |

## Logistics test bench: HomeRegionW (not a war region)
HomeRegionW is the Wardens' training/boarding island. The actors below serve the prototype;
their coordinates, quantity and road access do not represent other regions. The `*Hex` maps
need an inventory when loaded; the files being in the client does not guarantee the actors of an offline war.
Actor count in the test map (approximate coordinates, cm):
- Fields: salvage ×3 (22525, −34725), components (−5468, 9810), sulfur (−5067, 14459), oil (3419, −37440);
  salvage/component/sulfur mines near (−7500, 12000).
- Refineries `BPRefinery_C` ×2 (10785, 11096); factory `BPFactory_C` (15643, 11428); forward base
  (19557, 12293); vehicle factory (12484, −20098); facilities (refinery, transfer) near (10000, −37500).
- Trucks `BPTruckW_C` ×7 and flatbed ×3 parked.
- The mod's base (where the commander spawns) is near (10789, −24935): the map is about 500 × 300 m.

## Next step: logistics v1 (batch 12)
The mod's chain, offline and with its own systems, using the map's buildings as places:
1. **Salvage:** a salvage field produces while a resource truck is loading (20 per trip).
2. **Refinery** (`BPRefinery_C`): salvage becomes bmat.
3. **Factory** (`BPFactory_C`): bmat becomes crates with the costs and times of the table above (production queue).
4. **Truck** (15 crates): takes crates from the factory to a depot (base or one of our points), by road, and can
   be attacked.
5. **Consumption:** recruiting spends shirts and the weapon of the depot where the soldier spawns; reloading ammunition
   spends ammo crates from the point's depot. The enemy AI has the same chain, simpler.

## Real regions: first offline inventory (2026-10-09)
Trace: `data/trace_regions.txt`; reproducible probe in `tools/inspect_region.lua`.
Deadlands and CallumsCape opened as local sessions. CallumsCape has an active salvage field and installations
in ruins at the map's sites; they need rebuilding before an operational chain. The count of
active actors differs from the lobby's. Batch 17 added explicit own deployment and real scenario
vehicles, with budget and rollback; road access still pending.
A picture is not an inventory: structures can vanish by angle/occlusion, vehicles by LOS. Search derived
classes and ruins; a zero in one class describes only the local loaded state, not the server state.

**Rebuild probes (batch 16):** `data/trace_rebuild.txt`. Active factory/refinery classes
spawned in the ruins' transformations, with HP/base class checked; they were temporary probes, not a
delivered mechanic. A construction site created directly came without a configured target/cost. A truck placed by
a vertical trace can spawn on a roof or return already being destroyed. The next implementation needs an
explicit budget, validated parking and rollback; hiding the ruin or returning IsValid is not enough.

**Deployment delivered (batch 17):** `data/trace_deployment.txt`. Alt+L debits the scenario wallet only
after validating all installations/trucks; a failure restores the ruins and keeps the soldiers. CallumsCapeHex
produced three crates in 65.21 s and delivered two of ammunition/ten shirts to the base, with three intact trucks.
Test without waves and with zero starting stock: it validates neither balance nor roads, native construction of
sites or facilities. Trucks are still moved in a straight line by the mod's own system.
