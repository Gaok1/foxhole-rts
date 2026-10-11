# Native local damage context — static evidence

2026-10-11. The user authorized reusing the LOCAL native configuration, without network.
Offline reading only; no game/channel, RPC, inventory, offset writes or editing
main.lua. Steam being closed prevents a live oracle; do not start it/log in for the user.

## Object and initialization

`/Script/War.ServerSettings` is a **passive SaveGame**, not a network service.
Native class size 0x7f8, StaticClass 0x14121e6b0; the super thunk 0x1406f1560 points to
Engine.SaveGame 0x142b1e920. The ctor wrapper 0x14121f380 calls 0x14099d6b0.
The constructor initializes fields and calls the WarTweakables constructor 0x14099bff0 at +0x118.
WarTweakables: struct 0x5a0, 340 properties; the old exporter was limited to 80 and had left out
this schema, not because it is absent from the client.

Audit of the body 0x14099d6b0–0x14099da89: calls to base SaveGame/UObject,
empty FText/reference cleanup and the NextWarTime date/calendar; no
RPC/socket/request/server call. The WarTweakables constructor ends at 0x14099cc23 and has
no CALL at all: it writes compiled defaults and initializes containers.
WarServerSettings has no UFunctions of its own. There is no proven need
to call a GameInstance or network initializer to initialize these defaults.
This shows a passive constructor; global behavior after the association
with the GI needs to be observed, not assumed.

## Fields actually consumed in SimVehicle damage

Damage interface 0x140d81a00 gets the WarTweakables pointer through 0x14113e570.
External decomp `rifle-decomp/140d81a00.c`, confirmed with disassembly:

|WarTweakables field|Offset|Native default|Static use|
|---|---|---|---|
|MinTankArmourMultiplier|0x218|1.0|lower limit of armor wear|
|BallisticPenetrationMaxDistance|0x29c|4000.0|penetration distance when there is no override|
|BallisticPenetrationDistanceExponent|0x2a0|1.5|exponent of the distance factor|
|BallisticPenetrationMaxAngleBonus|0x2a4|≈0.4|angle bonus|
|BallisticPenetrationMaxRangeBonus|0x2a8|≈0.4|range bonus|

Defaults proven at 0x14099c421/55b/565/56f/579 (bits 3f800000,
457a0000, 3fc00000, 3ecccccd, 3ecccccd). Do NOT copy these numbers into a Lua
formula: they are evidence that creating a native instance delivers the values.
ServerSettings.SpawnInvulnerabilityTime also has a native default of 3.0 (+f4).
No cost/economy of our own appears in this list of the impact calculation.

## Damage profile already in the client

Getter 0x1408f8e80 loads and keeps the class
`/Game/Blueprints/Data/BPDamageProfiles.BPDamageProfiles_C`, returns the CDO.
DamageProfiles.DataTable is an ObjectProperty at +0x218, pointing to the tabled profile;
DTDamageProfiles and BPDamageProfiles are in the pak, lines 1785/1786.
The `DamageProfile` struct 0x58 has LightVehicle (+8), Tier1Tank (+c), Tier2Tank (+10),
structures/ships etc. Lookup 0x1409066d0 picks the row by enum DamageType and
cache 0x140912da0; application 0x140914060 picks the ArmourType column.
The cell values have NOT been exported/validated yet; the presence of the assets
and native consumption are proven, values must not be guessed.

Order of guards observed: Health>0 → valid SimDamageType CDO → actor authority/
bCanBeDamaged/world + temporary protection → friendly team/context rule →
non-null ServerSettings/WarTweakables → Engine application/callbacks → DamageType/ArmourType
profile → armor/penetration/subsystems → Health debit/death.
Non-null ServerSettings alone does not certify the other contracts.

## Minimal future oracle (not run)

1. Steam already open/logged in by the user; lab strictly offline.
2. Confirm GI.ServerSettings is still null; keep the exact original value.
3. Build **our own instance** of the native class with Outer GI (not the CDO), through the
   native StaticConstructObject supported by the UE4SS version; read class/IsValid,
   the fields above and SpawnInvulnerabilityTime. Gate: intact, non-NaN defaults.
4. Temporarily attach GI.ServerSettings to the instance. Do not change network fields,
   CDO, spawn bypass, formulas, nor call an online initializer.
5. Exclusive truck with HP 900/correct context, one application of a real damage type;
   read HP before/after and the return. Do not write HP or credit destruction by hand.
6. Ensure the original GI.ServerSettings value is restored on success OR error,
   remove only the exclusive actor and local references; check the restore.

Not implemented in the mod and no certified live result. Protected sources
outside the repo: `damage-settings-native-ctor.txt`, `damage-settings-props.txt`,
`damage-tweakables-props.txt`, `damage-profile-props.txt`, `rifle-decomp/140d81a00.c`,
all in `D:/tools/foxhole-lab/`. The previous report keeps the diagnosis of the guards.

## Crash of the first oracle: debug branch and pending lifetime

PID24924: the live gate of constructor/nested structs passed. The next oracle crashed
natively; the lost buffer prevents attributing with certainty the last completed command.
CrashContext stack `UE4CC-Windows-608B38A24B507F2999BD40955C73B6EF_0000`:
b5d5bc → b64277 → d613df → d82713 → d96e1c → 2550198 → 2a527dc.

Static branch identified: the end of damage 0x140d81a00 calls lambda 0x140d61310;
it reads `WarTweakables.bEnableDamageDebug` and calls the SimGameMode helper 0x140b68780
→ 0x140b641f0 → lookup 0x140b5d530. The lookup searches a string key in a private TMap
ServerSettings +0x80. Crash 0x140b5d5bc reads a map element, not a physical/RPC effect.
UHT setter 141272610 proves the debug flag at +0x428; constructor 14099c8b0 sets it TRUE.
Do not turn off debug to hide the cause; do not change the private map/offsets.

The constructor initializes a coherent empty TMap: this+0x80 pointer 0, +0x88 num/cap 0,
+0xa0/+0xa8 zero, +0xb0 freeindex=-1, +0xb4 freecount 0, +0xc0 hashptr 0,
+0xc8 hashsize 0. The lookup compares map+8 against map+0x34; num 0 == freecount 0 exits
BEFORE the search. A fresh constructor alone does not explain a huge index.

Reading the standard minidump, without running a process: R14 map=0x2552cacc0a0,
RCX elems=0x25509a002d8, RBX index=0x2b84f1c0. RDI=0x1051daa80 and invalid access
0x25d328d56e0. The map's heap is not captured, so it does NOT prove the
exact cause; it shows data/index inconsistent with an initially empty map.

Strong lifetime hypothesis: the probe created the settings, kept only a Lua `_G` while
GI.ServerSettings stayed null for 12 s, then attached it. Lua is not a GC root for
UObjects, a pitfall already documented for MIDs; IsValid can stay true or the address
be reused. No class/address was checked right before the
association. This is a hypothesis, not a confirmed result nor proof of native corruption.

Next minimal oracle prepared by the root agent: spawn ONLY the truck → wait 12 s →
baseline without settings → create a NEW instance in the SAME chunk as the configured rehearsal →
check class/defaults/address and attach IMMEDIATELY to the GI UPROPERTY → one
call → restore the original on success/error and remove the exclusive actor. Preload
assets before creating the settings. Do not keep loose settings in Lua _G during the wait.
Checkpoints before/after each phase, since pcall does NOT catch a native crash.
None of this was run in this offline investigation; no claim of approved damage.
