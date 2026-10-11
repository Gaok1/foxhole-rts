# Observational snapshot of the lobby, not a playable region

Export received from the coordinator: 127 CPs, 122 segments, 468 nodes with curves.
95 segments only have assets in Environment/Roads; 27 are not classified
as road. EditorLandscapeResources/SplineEditorMesh explicitly excluded.
Full incidence with two distinct CPs and different Ends, a curve compatible with
endpoints within 1 cm: no segment rejected for ambiguity in this export.

The native graph has components of 259/114/45/22/17/10/1 nodes; filtered by road,
two connected components of 259/114 remain and 95 isolated nodes. There is no invented
link between components: crossing the gap requires a validated real access/bridge.
All edges have validated=false; non-road ones also blocked=true.

`home-region-snapshot.json` keeps coordinates/IDs/asset names, without game files
nor mesh content. The epoch combines the world and the export's hash; the live adapter
must still add a session identity to reject an identical reload of the region.
Do not use this snapshot as a cache for CallumsCapeHex.

## Possible accesses, not authorized
Any CP or intermediate point of one of the two road components is a
topological candidate. There is no export yet of the field/refinery/factory stops
in this snapshot; so a connection between installations and road cannot be claimed.
Need to get real exterior parking, a strict access plan and confirm envelope,
surface, water/bridge deck and dynamic obstruction. A road asset does not prove this.

`python data/parallel/roads/build_snapshot.py` reproduces the conversion of the external output;
`python data/parallel/roads/test_snapshot.py` passed against the real snapshot.
Transport remains not integrated/not physically validated.
