# Progress

Public checklist of the roadmap. The detailed working roadmap (Portuguese) is [`ROADMAP.md`](ROADMAP.md).

Legend: `[x]` done and validated in the game · `[~]` partial (works offline or once, not approved live) · `[ ]` not started.
Scoring: done = 1, partial = 0.5, not started = 0. After editing this file run `python tools/progress.py`
to refresh the bars in `README.md`.

Want to pick an item? Open an issue with the item name so nobody duplicates work.

## Phase 1: Small front (squad combat in HomeRegionW)

- [x] RTS camera: pan, zoom, edge pan, centering
- [x] Selection (click, drag box, shift) and move/attack orders in formation, queued waypoints
- [x] Control groups, alerts and camera jumps between fronts
- [x] Control points, automatic waves, assault mode, difficulty levels
- [x] Fortifications: concrete barriers, trenches, barbed wire, first aid post, supply box
- [x] Tactical pause, game speed, save and continue
- [x] Native death (ragdoll through the game's own `OnRep_Health`)
- [~] Native grenades (Warden/Colonial classes, fuse and damage integrated; long-run stability not proven)
- [ ] Native rifle hit and damage path (still the mod's own; needs reverse engineering)
- [~] Yellow selection outline (looks approved; native crashes when selecting many units still open)
- [~] Units and structures stay visible at high RTS zoom
- [ ] Visible drag-selection rectangle
- [ ] Full manual test pass with real input (`TESTE_MANUAL.md`)

## Phase 2: Study the game's mechanics (from the game's own data)

- [x] Item and structure costs exported (`dados/custos_do_jogo.txt`, `tools/export_costs.lua`)
- [x] Refinery, factory and forward base classes and costs
- [x] Local recon of regions: what loads offline in Deadlands and Callum's Cape
- [x] Road network of a region exported (405 control points, 431 segments)
- [~] Vehicles: trucks traced; armor and artillery not yet
- [~] Resources: scrap fields traced; components, sulfur, oil, coal not yet
- [ ] Ships and planes present in the client

## Phase 3: Logistics in one region (current phase)

- [~] Workers collect scrap by hand (passed 120 delivered / 0 lost once; latest fresh run failed)
- [x] Refinery turns scrap into building materials
- [x] Factory turns building materials into crates (ammo, shirts, rifles, bandages)
- [x] Deploy refinery, factory and trucks at the native sites (Alt+L) with budget and rollback
- [~] Supply trucks deliver crates to depots and bases (straight line, no collision yet)
- [ ] Trucks follow the native roads, with bridges, water and collision
- [x] Recruitment spends the stock of the base (shirts + weapon), forward bases
- [x] Save v2 keeps infrastructure and wallet across restarts
- [~] Native truck damage, death and cargo loss (generic damage and explosives proven; full death not)
- [~] Enemy runs its own supply chain and can be ambushed
- [ ] Full fresh cycle approved on a real `*Hex` map (collect, refine, produce, transport, consume, expand)
- [ ] Long session without the PlayerState/UniqueId crash
- [ ] Player-built facilities

## Phase 4: Vehicles and heavy weapons

- [~] Trucks driven by the mod's AI (moving, but not by road)
- [~] Mortar fire (the mod's own, not the native weapon yet)
- [ ] Armored vehicles
- [ ] Artillery using produced ammunition
- [ ] Troop transport

## Phase 5: Several regions and the world

- [ ] Two or more linked regions
- [ ] Several real fronts at once
- [ ] Ports and transport ships
- [ ] Planes
- [ ] Campaign over the world map
