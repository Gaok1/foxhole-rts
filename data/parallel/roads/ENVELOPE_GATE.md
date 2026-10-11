# TruckW envelope: probe prepared, not run

`D:/tools/foxhole-lab/t_truck_collision_schema.lua` picks the first live truck
through logi.scan and enumerates PrimitiveComponents using an API already used in the mod. Only
names/classes/metadata of collision getters, extents and transform. No total
actor bounds, MasterPoseComponent, AnimClass or physics modification.

After the metadata output, prepare reading the confirmed getters for **each** component,
do not assume the first BoxComponent is the body: it may be an interaction or another volume.
Relate CollisionEnabled, ObjectType/profile, position/rotation/scale and extents.
A candidate envelope must enclose the physical components that really block Camera;
that last semantics requires a reproducible trace and is not proven by the component's name.

Local BoxExtent + transform gives an OBB; GetScaledBoxExtent already includes scale, do not apply
the scale twice. Sphere/Capsule or a mesh body requires its own physical geometry; render
bounds are not a collision hull. Use a conservative shape enclosing the physical body to
sweep stretches, including length in the curves and width in the accesses. A SphereTrace
with a soldier's radius does not prove a truck's clearance. On a bridge, support samples at the wheels
and the deck are a gate separate from the envelope; a central groundZ alone is not enough.

This document defines the next step after the metadata, it does not authorize validated=true routes.

## Live metadata received
`D:/tools/foxhole-lab/truck-collision-schema-live.txt`: Truck_2 has
CollisionCylinder CapsuleComponent, VehicleCollision BoxComponent, several meshes,
particles and SeatTrigger/TowHitch. None chosen by name as the authorized body.
Box getters scaled/unscaled return a struct; CapsuleRadius/HalfHeight floats;
collision profile/enabled/objecttype and transform getters confirmed.

Prepared `D:/tools/foxhole-lab/t_truck_collision_values.lua`, syntax OK, not run:
all PrimitiveComponents with collision settings/transform; Box extents and capsule
local dimensions only for exact classes. GetCollisionResponseToChannel first
confirmed through Channel/ReturnValue ByteProperty metadata and then reading Camera 1 and
Visibility 0. Does not change collision. Instance values may reflect collision turned off
by the current driver: tell the native profile apart from a state changed by the mod before
concluding that Camera does not block the body.

## Resumed 10/11 — trace the native driver before integrating
Collision values were read (TRUCK_VALUES_20261010.md); a ray scan in
data/trace_envelope_truck.txt hit CharacterMesh0 outside the 400/162/140 box.
Penetration flags are not proof of the full hull; no edge authorized.

New read-only probe: tools/probe_native_truck_movement.lua. It confirms
the signatures of the RootComponent/MovementComponent getters before calling, reads
UpdatedComponent/UpdatedPrimitive only if they are ObjectProperty and the flag
bIgnoreNonRootComponentsDuringVehicleMovement only if BoolProperty. It enumerates
movement/input signatures, does not run those functions. Offline test PASS;
NOT run in Unreal. Keep the output before/after logistics in the next batch.
An identified Root or UpdatedComponent does not prove a full sweep by itself: the
34/200 capsule, the box and the meshes have different roles. No moving/turning off collision
to force success; first trace the already existing movement path.

## Probe run in logistics batch 2 (10/11)
The same TruckW observed before/after: root VehicleCollision (BoxComponent),
UpdatedComponent/UpdatedPrimitive equal; RWDVehicleMovementComponent inherits
SimpleVehicleMovementComponent and CharacterMovementComponent. Flag
bIgnoreNonRootComponentsDuringVehicleMovement=true in both states, ActorCollision
true before/false active. Own traces in data/trace_truck_movement_*_20261011.txt.
This tells the native choice of root apart from visual bounds, it does not prove clearance/support
nor authorize a flag/route. A later match crashed; the next development stays
offline, without restarting for this finding.
