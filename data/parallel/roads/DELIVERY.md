# ESTRADAS (roads) — offline delivery (2026-10-09)

## Current evidence
- `data/trace_regions.txt`: CallumsCapeHex loaded 431 LandscapeSplineSegment and 405
  LandscapeSplineControlPoint; Deadlands 634/596. Neither connections nor curves were exported.
- `tools/inspect_region.lua` enumerates names/counts, but not spline properties.
- `main.lua:2485`: logi.place uses SetActorLocation without sweep and teleport=true, ground through groundZ.
- `main.lua:2760`: logi.drive drives straight. `:2831` instantly returns the cargo to the factory
  when the destination changes owner, even far from it. Both contradict verifiable transport.
- `kneeClear`/planStart already accept strict nav and an incremental budget. A soldier's height and sphere are
  NOT proven TruckW clearance. The strict option still queries groundZ: water,
  bridge deck and roof need explicit classification.

## Code delivered and test
`roads.lua` is a pure Lua module, with no new locals in main.lua. Dijkstra over explicitly
validated connections, without linking neighbors by distance, without a straight-line fallback.
`advance` proposes a bounded step; `commit` only progresses after the adapter's confirmation.
It moves no actors nor debits/delivers resources. Routes carry an epoch to avoid the lobby's cache.
The synthetic graph tests disconnection, epoch, unknown/blocked edge, refused sweep,
destroyed vehicle, confirmation and arrival. Test passed through lupa; it does not prove Unreal physics.

## Proposed integration (NOT applied yet)
1. In the lab, export reflection/schema of the known spline classes before reading fields.
   In standard UE there are Connections/ControlPoint, Points and Location, but these names/shapes
   are HYPOTHESES in this build, not access authorized by local evidence. Also identify the
   local->world transform of LandscapeSplinesComponent. Do not treat a decorative spline as a road.
2. Export only stable IDs per snapshot, explicit connections, width and curve samples
   into a region graph. The curve needs intermediate nodes: linking only the ends cuts curves.
   A bridge requires a connection + confirmed deck support; never link banks by proximity.
3. Validate stretches through surface samples and the truck's oriented envelope (physical bounds,
   not total volume bounds). Reuse measured Camera traces and planStart/planStep in
   slices for the short parking->network access. No synchronous A* over kilometers in the tick.
4. Installations get a validated exterior stop and access to the road, not the building's center.
   Origin and destination in roads.plan are IDs of these stops, both connected only after proof of access.
5. `logi.drive`: get a route; a missing route keeps it stopped with a reason. `advance` -> sweep/confirmed
   position -> update tr -> commit. Arrival only on finishing the route at the validated stop.
   Do not call logi.place on each step: it teleports without sweep and replaces the bridge's Z with groundZ.
6. A lost destination switches to a physical return to the factory keeping tr.cargo. Return stock only
   on confirmed arrival. A missing route keeps the cargo on the truck; death loses the cargo once.
   An invalid native truck/bActorIsBeingDestroyed goes into explicit loss, never a phantom delivery.
7. A world change invalidates the epoch, jobs and references. The same region reloaded also changes
   the epoch. Rebuilding a truck needs a validated spawn/parking, not re-showing a dead pawn.
8. Export the module to env only if probes need it; reset clears routes. Blocked/missing route alerts
   must be readable without being emitted every frame.

## Matrix requested from the lab owner
- Real curve field->refinery->factory; record the path, speeds and positions at 100 ms.
- Building/barrier/vehicle between stops: no jump or delivery despite a blocked route.
- Water without a bridge: refusal; existing bridge: Z follows the deck and full clearance validated.
- Captured destination: physical return, cargo conserved; destroyed: single loss.
- Region change/reload: old graph refused; camera/LOS not used as proof of a road.
- 3 trucks, dynamic obstruction and replanning with a budget: measure ms/tick and stalls.

The task remains in progress; native discovery and live validation are real dependencies.

## Metadata probe prepared, NOT run
`D:/tools/foxhole-lab/t_roads_schema.lua`: only names/types of properties,
function names and inheritance of three already inventoried classes. Syntax validated through lupa.
ForEachProperty/GetSuperStruct APIs shown in the previous external probes
`t_rebuild_schema.lua`/`rebuild-schema.txt`; ForEachFunction used in `t_outline_schema.lua`.
There is no example of these APIs in the repository's `tools/`; the evidence is the probe and the lab's
output, not a supposed new API. It does not access Connections/Points/Location,
GetInner, array contents, instance structs nor speculative transforms.

Exact gate: the lab owner needs to run this probe and keep the output.
If connection/point properties are ArrayProperty, proven metadata of the inner type is still
missing to define a specific export; do not do a generic recursive data dump.
Fields may not be reflected in this build. In that case get the schema
through the existing reflection/SDK before accessing values. Even the schema output does not
authorize presuming road semantics, orientation/local->world or bridge.

The isolated module is preparation/contract testing, NOT an integrated transport feature.

## Evidence progress: live schema received from the coordinator
`D:/tools/foxhole-lab/roads-schema-live.txt` confirmed in HomeRegionW 122 segments,
127 control points. Segment.Connections is a **StructProperty**, not an ArrayProperty;
SplineInfo/Bounds also structs; Points/LocalMeshComponents arrays. ControlPoint
Location/Rotation structs, Width FloatProperty, ConnectedSegments/Points arrays,
LocalMeshComponent ObjectProperty. Do not reuse these counts/positions in the hex.

Next probe `D:/tools/foxhole-lab/t_roads_types.lua`, syntax OK, not run:
up to three examples of segment/control point; metadata of explicitly
confirmed structs (GetStruct already used in rebuilding), width and name of the local mesh.
A mesh has only its schema enumerated, without reading an unknown asset/content.
Connections must not be accessed as an array by standard UE inference. The gate remains the
cardinality of Connections and the inner types of Points/ConnectedSegments; network classification
and local->world transform still not proven. Prefer validating a real curved stretch
before exporting the whole map.
