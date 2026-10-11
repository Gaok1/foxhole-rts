# TruckW collision — live reading, before starting logistics

HomeRegionW, PID 21456, main 223788476973. External probe `t_truck_collision_values.lua`,
full output `D:/tools/foxhole-lab/truck-collision-values-v41-live.txt`.
No physics change and before newGame: this is not the state with collision turned off by the driver.

- VehicleCollision: BoxComponent, profile VehicleRoot, CollisionEnabled 3, ObjectType 6.
  Local and scaled extents equal: 400/162/140 cm; scale 1. Camera/Visibility response: 2/2.
- CollisionCylinder: CapsuleComponent, radius 34 and half height 200; profile VehicleCapsule,
  CollisionEnabled 1, Camera/Visibility 1/1.
- CharacterMesh0 and the CabinMesh/TrailerMesh meshes also respond 2 to both channels.
  So the VehicleCollision box alone does not prove the full envelope yet.

Next: relate box/meshes to trace impacts and get a conservative envelope in the vehicle's
coordinates. Do not use render bounds as the physical hull nor authorize edges with these extents alone.
Still missing: real curves, access to the installations, water/bridge deck, sweep and dynamic obstruction.
