# Evidence received (HomeRegionW, 2026-10-09)

Outputs from the lab owner: `D:/tools/foxhole-lab/roads-schema-live.txt` and
`D:/tools/foxhole-lab/roads-types-live.txt`. Not run by this agent.

- Connections -> LandscapeSplineSegmentConnection: ControlPoint ObjectProperty,
  TangentLen FloatProperty, SocketName NameProperty. **Cardinality not exported.**
- SplineInfo -> InterpCurveVector: Points ArrayProperty, bIsLooped BoolProperty,
  LoopKeyOffset FloatProperty. Type of each point still unknown.
- ControlPoint.Location -> Vector(X,Y,Z floats); Rotation -> Rotator(Pitch,Yaw,Roll).
- Three control points observed: Width 1000, LocalMeshComponent absent. Does not prove
  the absence of segment or road meshes, nor a useful passable size.

Probe prepared `D:/tools/foxhole-lab/t_roads_inner.lua`, syntax OK, not run.
It finds inner types only of explicitly confirmed arrays and the immediate schemas
of the struct elements, without reading values or a recursive dump.
GetInner confirmed in the [official UE4SS documentation](https://docs.ue4ss.com/lua-api/classes/arrayproperty.html).
Compatibility of the installed version must be checked by the lab owner.

**Connections cardinality gate:** the [official Lua Property API](https://docs.ue4ss.com/dev/lua-api/classes/property.html)
consulted does not expose GetArrayDim. Do not call it by inference from the C++/UE API.
Consult a generated SDK/header or a metadata dumper that prints ArrayDim before
indexing endpoints. The schema allows studying Connections.ControlPoint of the
represented element, but a single endpoint does not define an edge; the probe deliberately
does not infer a second endpoint, offsets nor raw memory reads.

**Geometry gate:** the inner types of Points and InterpCurveVector.Points need
to be confirmed; then export up to three points of a segment. Local->world and
road/mesh classification remain requirements before creating a passable graph.

## Live INNER received: alternative route for endpoints
`D:/tools/foxhole-lab/roads-inner-live.txt` confirmed ConnectedSegments as an array
of LandscapeSplineConnection, with Segment ObjectProperty and End BoolProperty.
So **CP->segment** incidence can identify endpoints without reading Connections
of unknown cardinality. End true/false is an observed label, not an assumed
orientation. For a complete graph a full CP inventory will be needed, requiring two
distinct CPs per segment; a partial/ambiguous segment does not authorize an edge.

Points is an array of LandscapeSplineInterpPoint with a Center StructProperty. Probe
`D:/tools/foxhole-lab/t_roads_incidence.lua` prepared, syntax OK, not run:
up to three CPs (Location Vector already proven), eight incidences per CP, three segments,
three points and names of three meshes per segment. Center is only read after metadata
proves exactly CoreUObject.Vector and X/Y/Z FloatProperty. The POINT_LOCAL output
is deliberately not world. No road inference nor linking by proximity.
