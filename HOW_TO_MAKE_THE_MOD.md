# How to make Foxhole RTS: route, architecture, limitations and tests

Updated on 2026-10-06, based on Steam build 25730371 (PE 1.64.6.1, `DefaultGame.ini` 1.67.10.1).

The user made three decisions: solo mode against AI, squad control and the approved normative design (see "Lab rules").

The evidence is in `ENVIRONMENT_RECON.md`. This document is the "how to". Sections 1–8 came from static analysis (2026-10-06). **Section 0** records what was validated with the game running and **prevails** when there is a conflict.

---

## 0. Validated at runtime (2026-10-07) — the recipe that works

Running in the copy `D:\FoxholeLab\Foxhole` with UE4SS + `mod/FoxholeRTS` v0.3. Details and logs in `MODLOG.md`.

| Step | How | Pitfall found |
|---|---|---|
| Launch | `tools\lab.ps1 run` with **Steam open and logged in** + `steam_appid.txt` | Without Steam open, `SteamAPI_Init` fails |
| Open a local session | `GameplayStatics:OpenLevel(world, "/Game/Maps/HomeRegionW", true, "listen")` from the mod | Shipping **ignores** the map on the command line |
| Not crashing | Hook on `SimPlayerController:ClientStartRespawnTimer`: in the nested call, `Role` goes to AutonomousProxy | The RPC recurses on the host (stack overflow) |
| Commander (player) | `GameMode:RestartPlayerAtTransform(pc, transform)` on solid ground | `RestartPlayer` spawns over the void and dies in the fall; **no profile stub needed** |
| Seeing the world | `PlayerCameraManager:StopCameraFade()` + `SetManualCameraFade(0)` | The black fade is never undone: black screen with visible HUD |
| RTS camera | `CameraActor` as view target (pitch -60), edge/arrow pan, zoom | Foxhole's camera sits inside the character (zoom not initialized) |
| Soldiers | `SpawnActor(HeadlessPlayerController)` + `PlayerInput` + `bIsLocalPlayerController=true` + `RestartPlayerAtTransform` | `CreatePlayer` crashes (per-player options UI); an `AIController`'s pawn is pulled to (0,0,0) after ~20 s |
| Moving soldiers | `AddMovementInput` every 33 ms, with `BrakingDecelerationWalking=0`, `GroundFriction=0`, `MaxAcceleration=20000`; `StopMovementImmediately` on arrival | Without zero braking, spaced pulses barely move |
| Click order | `GetHitResultUnderCursorByChannel(0, false, hit)` → `hit.ImpactPoint` | UE4SS out parameters: pass an empty table |
| Teams | `PlayerState.TeamId` directly + `pawn.TeamId` + `OnRep_TeamIdNotify` + `BPSetTeamVisuals` (Colonials=0, Wardens=1) | `ServerJoinWar(0)` on the HPC did not change the PlayerState |
| Combat (v0.3) | `ApplyDamage` + game effects (`RifleMF`, `BloodSplat`, `SimpleRifleImpact`, `RifleShot_Cue`) + line of sight by trace | No real weapon yet: `ServerTakePickup` recurses on the host (a recursion breaker avoids the crash, the item does not go in) |
| Messages | `SimPlayerController:ClientAlertMessage(str, s)` | — |
| Reloading the mod | restart the game (`tools/lab/restart.sh`) | UE4SS Ctrl+R froze the game thread |

Tools: `um win shot --title '^War'` (GPU capture; the process's main window is the UE4SS console), `um win drive --title '^War'` (added to the toolkit on this date), channel `D:\tools\foxhole-lab\cmd.lua` → `cmd.out` (`tools/lab/run.sh`).

---

## 1. Summary on one screen

| Question | Answer | Confidence |
|---|---|---|
| Is there an official route (offline, bots, SDK, private server)? | No | High (official sources) |
| Can the client be the server? | Probably yes: server code compiled (*Game* target), `UWorld::Listen`, `IpNetDriver` fallback, maps with `DefaultGameMode = SimGameMode`. The `GameInstance` **skips the menu flow when the command line contains `/Game/Maps/`** | High for "code present", not tested at runtime |
| What could block it? | Only one point on the host path: **profile loading in `PostLogin`** (HTTP request built, but only sent on a dedicated server). Auth (`FExternalWarService`), travel and `PreLogin` are off that path | High (decompiled and validated); still to measure at runtime (T2) |
| VAC? | No EAC/BattlEye. There is VAC. On a client, the Steam server **only starts** with `bInitServerOnClient`/`OSS.SteamInitServerOnClient`, absent from the config. If it started, `bVACEnabled` (embedded = 1) would give secure mode; `lab.ps1` writes `bVACEnabled=0` to be safe | High (decompiled) |
| Accessible assets? | PAK without compression, no AES, no `.sig`, no IoStore | High (index read and verified) |
| AI and navigation? | AIModule/Recast/Detour/Crowd compiled, but the game uses no soldier AI and the maps have no NavMesh | High |
| Controllable soldiers? | Yes, in principle: the `-headless` load-test mode already creates extra local players whose controller moves the `ASimCharacter` by code (`AddMovementInput`) | High for the mechanism; not tested |
| Feasible? | **Plausible.** Depends on: (1) the map opening in `?listen` (T2), (2) a C++/UE4SS profile stub (T6), (3) extra local players as soldiers (T7) | — |

---

## 2. Chosen route: isolated local listen server + UE4SS

```
Steam (ownership checked normally)
  └─ Lab copy  D:\FoxholeLab\Foxhole   (never connects to an official server)
       ├─ War-Win64-Shipping.exe  /Game/Maps/HomeRegionW?listen  -log
       │     └─ ASimGameMode (local authority)
       │           ├─ PostLogin → UPlayerProfileManager → PROFILE STUB (C++, only in this session)
       │           ├─ extra local players = soldiers (SimPlayerController + ASimCharacter)
       │           └─ Steam game server: does not start on a client → no server VAC
       └─ UE4SS (proxy dll only in the copy)
             ├─ C++: profile stub (detour 0x1409a74f0), then selection/UI/pathfinding
             └─ Lua: create soldiers, squad orders, opposing AI
```

### Why this route
- Foxhole is **server-authoritative**. Only the server can create soldiers and really move units. The local `?listen` session makes the client itself the server, and then RTS orders are legitimate inside the simulation.
- Foxhole's camera is already isometric and top-down. The "RTS camera" is the cheapest part of the mod.
- UE4SS is the standard way to inject logic into UE4 without an editor or source code. The PAK's open index allows reading the Blueprints to find property and function names.

### Discarded routes and why

| Route | Reason |
|---|---|
| Mod on a client connected to an official server | The server is the authority, so the client commands nothing. It also violates the Code of Conduct and exposes the account to VAC |
| "Authenticate online and then go offline" | A modified process would talk to the official backend. It is the biggest ban risk |
| Dedicated server (`-server`) | There is no `-server` string nor server binary. The dedicated target is not distributed |
| Full server emulator | Does not exist; reimplementing the server is not feasible |
| Blueprint pak mod with new logic | Requires cooking assets in UE 4.24 with the `War` project, which we do not have. Only useful for one-off swaps (late phase) |

### Plan B options, if the main route falls
1. **Visual/UI pak mod:** tolerated by the community, but it does not give an RTS.
2. **RTS-like dashboard over the War API:** read-only, legitimate, but not a game.
3. **Ask Siege Camp:** there is a draft in `ENVIRONMENT_RECON.md`.

---

## 3. Mod architecture (layers)

Each layer only starts after the previous one passes its test (section 6).

### Layer 0: lab
- Full copy of the game in `D:\FoxholeLab\Foxhole` (≈25.7 GB). The Steam installation stays untouched for playing online.
- `steam_appid.txt` (content `505460`) next to the copy's exe. It is Steamworks' standard mechanism to run the binary outside the Steam folder; Steam still requires login and ownership of the game.
- UE4SS (`dwmapi.dll` + `ue4ss/` folder) **only** in `D:\FoxholeLab\Foxhole\War\Binaries\Win64`.
- Lab config: `%LOCALAPPDATA%\War\Saved\Config\WindowsNoEditor\Engine.ini`. **Caution:** this folder is shared between the copy and the Steam installation. Every tweak must also be safe for the online game, or be applied/removed by a launch script. (Later found: the real folder is `%LOCALAPPDATA%\Foxhole`, not `War`.)
- Backup: `um backup create "%LOCALAPPDATA%\War" --name foxhole-config` before each modified session.

### Layer 1: local session
- URL: `/Game/Maps/HomeRegionW?listen` (48 MB, the smallest playable map, `SimGameMode`). Alternatives: `HomeRegionC`, `LykosIsleHex` (98 MB) and `DeadlandsHex`, the `ServerDefaultMap`, as a control.
- **What the local host requires from the backend** (decompiled and validated on 2026-10-06):

| Step | Function | Depends on the backend? | Action |
|---|---|---|---|
| Boot without menu | `UWarGameInstance::StartGameInstance` 0x141150070 | No: with `/Game/Maps/` on the command line, it skips the `MainMenu` (vfunc `+0x378` = 0x141145270, loads `/Game/Maps/MainMenu`) | None |
| `PreLogin` | `ASimGameMode` 0x140b79540 | Only for remote clients | None (the host does not go through it) |
| `Login` | 0x140b6a7a0 | Does not call the WarService. Requires a reservation (`?FactionId=0/1` + queue) **only if** `WarTweakables.bCheckReservationsOnLogin` (`ServerSettings+0x5d9`) | Measure in T2. If it rejects, zero the flag or pass `?FactionId=` |
| **`PostLogin` → profile** | `UPlayerProfileManager` 0x1409a74f0, callback 0x140b6f290 | **Yes, it is the real blocker.** The profile HTTP request is built but only sent (`ProcessRequest`, vfunc `0x88`) if `GetNetMode()==1` (dedicated). In listen, the callback never runs and the character is not released. If the world/HTTP is null, the callback runs with a failure → "Unable to load Profile" (kick) | **Mandatory stub:** detour at 0x1409a74f0 that invokes the callback with success and a local profile without a ban |
| `FExternalWarService` (auth) | `SendAuthMessage` 0x14092f2c0 / `OnAuthResponse` 0x140915aa0 | Created in `UWarGameInstance::Init`, but off the Login/PostLogin path | None; it should just fail to connect (UI warning) |
| TravelManager/travel reservation | 0x140dd6850 | Only created on a dedicated server | None |

- **How to build the stub:**
  - 0x1409a74f0 is a native function, not a UFunction. Lua's `RegisterHook` cannot reach it; a **UE4SS C++ mod** with a signature (AOB) detour is needed.
  - The profile format expected by callback 0x140b6f290 still needs mapping. Next RE task: decompile 0x140b6f290 and `OnBanAndProfileLoadComplete` 0x1409bc580 to build the minimal profile.
- **Forbidden by rule 2:** letting the request go out to Siege Camp, or faking their answer on the network. The stub lives only inside the process.
- Command-line switches that exist (FParse): `adminall`, `adminnone`, `noqueue`, `RepDriverDisable`, `headless`, `headlessclients=`, `supportsheadless`, `maxsplitscreensperconnection=`, `forceloadsavefromdisk`, `BeaconPort=`, `nosteam`. `-offline`, `-nowarservice` and `-skipauth` **do not exist**.
- **VAC (solved by config, still to confirm at runtime):**
  - Chain: `FOnlineSubsystemSteam::Init` 0x140562ce0 → `InitSteamworksServer` 0x1405f8980 → 0x1405f78e0 → `SteamInternal_GameServer_Init`. On a client, **the Steam server only starts if** the cvar `OSS.SteamInitServerOnClient` ≠ 0 **or** `[OnlineSubsystemSteam] bInitServerOnClient=True`. Neither exists in the game config, so in a default `?listen` **there is no Steam server nor server VAC**.
  - If it started: `GConfig [OnlineSubsystemSteam] bVACEnabled` → `eServerMode = 2 + bVACEnabled`.
  - The embedded `BaseEngine.ini` has `bVACEnabled=1`, and War's `DefaultEngine.ini` does not override it. So `tools/lab.ps1` writes `bVACEnabled=0` to `%LOCALAPPDATA%\War\Saved\Config\WindowsNoEditor\Engine.ini` before each `run`.
  - This is harmless online, where the client is never the server.
- **Going straight into the map:** `FUN_141150070` (GameInstance) only calls the default menu flow (vfunc `+0x378`) if the command line does **not** contain `/Game/Maps/`. With `/Game/Maps/HomeRegionW?listen`, the engine opens the map directly (default Browse of `UGameInstance::StartGameInstance`).
- **The local host does not go through `PreLogin`:** a listen server's local player enters via `SpawnPlayActor` → `GameMode::Login`, not through the network handshake (`NotifyControlMessage`). The auth risk is in `Login`/`PostLogin`/profile (`UPlayerProfileManager`).

### Layer 2: controllable soldiers
- Native base class: `ASimCharacter` (Blueprint `/Game/Blueprints/Character/Character`).
- **Discarded: `AOfflineCharacter`** (the "offline character" left behind on logout). It is an `AActor`, not a Pawn: only meshes and `MulticastApplyFatalHit`, no movement nor Possess. It is also disabled in the HomeRegions (0x140b53be0). Only useful as an extra or a target.
- **Main route: soldiers = extra local players on the host.** The game already does this in the `-headless` load-test mode:
  - `UWarGameInstance::OnStart` (0x141147150) creates `-headlessclients=N` local players (`UHeadlessLocalPlayer`).
  - Each one gets an `AHeadlessPlayerController : ASimPlayerController`, whose `PlayerTick` (0x140a2deb0, validated) takes the `ASimCharacter` pawn and calls `AddMovementInput` (vfunc `0x720`). It is a native movement bot.
  - Each local player goes through the normal flow: Login → `SimPlayerController` + `PlayerState` + `ASimCharacter`. So inventory, animation and health work as for a human.
  - In the mod: `GameplayStatics:CreatePlayer(world, id, true)` through UE4SS, or `-headless -headlessclients=N` itself (assess the effect on player 0). Then the mod drives the movement (`AddMovementInput`) instead of the random pattern.
  - Requirements: the profile stub (layer 1) applies to each local player; and no splitscreen (`[/Script/EngineSettings.GameMapsSettings] bUseSplitscreen=False` in the lab's Engine.ini).
- **Route B:** `AAIController` + `Possess` directly on an `ASimCharacter`. The casts in `ASimCharacter` look conditional, but the dependency on `ASimPlayerController`/`PlayerState` was neither proven nor ruled out.
- **Navigation:** the maps have no `RecastNavMesh`. There is a `NavigationSystemConfig` with `bEnableNavigationSystem`/`bAutoSpawnMissingNavData` serialized, which suggests they are off. Options, in order:
  1. Turn on the NavigationSystem and create a dynamic `RecastNavMesh` at runtime, only around the battle area (Recast is compiled). Costs CPU; limit it with a small `NavMeshBoundsVolume`.
  2. Fallback: our own grid pathfinding (A* over heightfield/traces), with `AddMovementInput` every tick. Works without a NavMesh.
- Unit and weapon data: DataTables `BPItemDynamicData`, `BPWeaponDynamicData`, `DTDamageProfiles`, `DTArmourProfiles` (read through FModel/CUE4Parse, without extracting into the repo).

### Layer 3: squad control (player)
- **Squad:** one leader and N members (extra local players) in relative formation, with an offset per slot. The order goes to the squad; the members follow the leader.
- **Input:**
  - phase 1: keys and the UE4SS console (Lua `RegisterKeyBind`) + click for the destination (cursor raycast);
  - phase 2: rectangle selection and a squad panel (C++ mod with UE4SS's ImGui overlay).
- **Camera:** use the `ASimPlayerController`'s camera (already top-down), with a larger zoom and detached from the player's character. Option: a spectator pawn.
- **Minimal orders:** move, attack-move, hold position, retreat.

### Layer 4: opposing AI
- Two layers, both in Lua/C++, without a BehaviorTree. The game has no BT, and we have no editor to create one.
  - **Commander:** state machine over objectives (capture point, defend, reinforce).
  - **Squad:** reacts to contact (attack, cover, retreat by morale/health).
- Weapon fire must go through the character's or weapon's server functions. The game's "Server RPCs" need to be mapped in the UE4SS dump.

### Layer 5: content and scope
1. Proof: 1 squad moves by click.
2. Two infantry squads against the AI in a `HomeRegion`.
3. One tank/vehicle (`ASimVehicle`) and one objective.
4. Production, logistics and construction, only if the previous layers are stable.

---

## 4. Known limitations

- **Updates break the mod.** Each patch changes offsets, UE4SS signatures and possibly Blueprints. Mitigation: the lab copy freezes the version; keep a "supported build" table.
- **Account risk.** Protection comes from a strict rule: never open the modified copy connected to an official server, and never put UE4SS in the Steam installation. Even so, VAC belongs to Valve and there is no formal guarantee. Use at your own risk.
- **Shared config folder** (`%LOCALAPPDATA%\War`) between the copy and the official installation (see layer 0).
- **No editor/SDK:** no new cooked Blueprints, only injected logic and reuse of existing assets.
- **Soldiers were never made for AI.** Animation, inventory and health may depend on `PlayerState`/profile. This may require extra stubs.
- **No NavMesh:** pathfinding is our job (see layer 2).
- **Performance:** hexes load 100–280 MB plus proxies; the listen server runs everything in a single process.
- **Policy:** the Code of Conduct forbids modifying the client "for an unfair advantage". Local, offline use gives nobody an advantage, but there is no explicit permission from Siege Camp.
- **Distribution:** the mod distributes only our scripts and DLLs. Never game files, extracted assets or decompilation.

---

## 5. Lab rules (approved on 2026-10-06)

1. Game ownership stays verified by Steam; do not touch DRM or tickets.
2. The modified session never contacts Siege Camp services. The stubs answer only inside the local session.
3. The local server runs without VAC.
4. The mod stays inactive outside the local RTS mode, and UE4SS stays only in the lab copy.
5. Backup before each modified session; record everything in `MODLOG.md`.

---

## 6. Test protocol (to run with the user present)

Each test has an objective success criterion and the evidence to keep (log excerpt in `MODLOG.md` and a screenshot via `um win shot`). Commands from `D:\GitHub\universal-modder`.

| # | Test | How | Success | If it fails |
|---|---|---|---|---|
| T0 | Original launch | `python -m um win launch --steam 505460 -- -log` and go to the menu; close | `%LOCALAPPDATA%\War\Saved\Logs\War.log` exists. Note hosts, auth, NetDriver, profile loading | Record the error; nothing proceeds without T0 |
| T1 | Lab copy | `steam_appid.txt` = `505460` in `D:\FoxholeLab\Foxhole\War\Binaries\Win64`; launch the copy's exe with `-log` | Opens the menu from the copy (the log points to the copy's path) | If Steam relaunches the official installation, use the exe with `-log` via `um win launch "<exe>"` and investigate `RestartAppIfNecessary` |
| T2 | Listen without mod | Copy, without UE4SS, **with the process's internet blocked** (outbound firewall rule for the copy's exe): `War-Win64-Shipping.exe /Game/Maps/HomeRegionW?listen -log` | The log shows the `LoadMap` of HomeRegionW, `SimGameMode` and the driver listening (`SteamSocketsNetDriver` or `IpNetDriver`). **Expected:** host stuck waiting for the profile, or "Unable to load Profile" | If it breaks before PostLogin (Login/reservation), note the message: it defines layer 1's reservation flag |
| T3 | Local VAC | T2's log (with `-LogCmds="LogOnline Verbose"`) | **Absence** of "Initializing Steam Game Server" and of "Steam Dedicated Server API initialized" | If it appears, `bInitServerOnClient`/`OSS.SteamInitServerOnClient` was turned on somewhere: stop and investigate before going on |
| T4 | UE4SS | Copy UE4SS (experimental-latest) only into the copy; launch to the menu | `UE4SS.log` without AOB errors; Live View lists `ASimCharacter`, `ASimGameMode` | Configure the 4.24 version override / custom AOBs |
| T5 | Dump | UE4SS: object and header dump (CXX header dump) | SDK with `ASimCharacter`, `ASimPlayerController`, `FExternalWarService`, `Server*` functions | — |
| T6 | Profile stub | UE4SS C++ mod: detour at `UPlayerProfileManager` 0x1409a74f0 → callback 0x140b6f290 with success and a local profile. If `Login` rejects: `bCheckReservationsOnLogin` (`ServerSettings+0x5d9`) = 0 | `?listen` session with the host's character in the field | Back to Ghidra: profile structure in 0x140b6f290 / 0x1409bc580 |
| T7 | First soldier | Lua: `GameplayStatics:CreatePlayer(world, 1, true)` (or `-headless -headlessclients=2` in the copy) + `AddMovementInput` for 10 m | The second character walks by itself (screenshot + log) | Route B: `SpawnAIFromClass` + `AAIController` |
| T8 | Navigation | Generate a dynamic NavMesh in the area, or turn on our own pathfinding | `MoveToLocation` going around an obstacle | A* fallback |
| T9 | **Milestone** | Select the squad (key) and click the destination | **All members move to the point** | — |

---

## 7. Current state of the tools

| Tool | Where | State |
|---|---|---|
| Ghidra 12.1.2 + GhidraMCP 5.14.2 | `D:\tools\ghidra`, `D:\tools\ghidra-mcp-v5.14.2` | Auto-analysis done (57 min). Decompilation by string: `D:\tools\ghidra-scripts\DecompStrRefs.java` (output in `D:\tools\foxhole-lab\decomp*`) |
| PAK index | `D:\tools\foxhole-lab\pak-index.tsv`, `pak-config-excerpts.txt` | Ready (25,898 entries) |
| Lab copy | `D:\FoxholeLab\Foxhole` | Ready (97 files, 26,035,003,749 bytes, identical to Steam), with `steam_appid.txt` |
| Lab script | `tools/lab.ps1` | `check`/`prepare` run. `vac-off` tested in a temporary folder (4 cases). `run`/`ue4ss-*` waiting for the user |
| Mod (skeleton) | `mod/FoxholeRTS/Scripts/main.lua` | Written, **not run** (F5 status, F6 squad, F7 move, F8 clear) |
| UE4SS | — | Pending: the download was blocked by auto mode; needs to be released by the user |
| Launching the game | `um win launch` | Blocked by auto mode without the user present |

## 8. Questions to the binary: answered and open

Answered (validated decompilation; functions in `D:\tools\foxhole-lab\decomp*`):
1. **`?listen` in the code:** it is the boot of the official dedicated server (only in `NM_DedicatedServer` and `ServerType` WorldConquest/HomeRegion), which appends `?listen` to the save's map. It is not an offline training mode. Dedicated mode is unreachable in this exe: the `IsRunningDedicatedServer` branch was compiled out and `GIsClient=1`. Practical gain: a command line with `/Game/Maps/...` skips the menu.
2. **VAC:** no Steam server on a client, unless `bInitServerOnClient`/`OSS.SteamInitServerOnClient` is on; see layer 1.
3. **Backend:** the only blocker on the host path is the profile in `PostLogin`; see layer 1's table.
4. **Control:** the game moves an `ASimCharacter` by code through `AHeadlessPlayerController`. Soldiers = extra local players.

Open:
- Structure of the profile expected by 0x140b6f290 / 0x1409bc580, for the T6 stub.
- Default value of `WarTweakables.bCheckReservationsOnLogin` in a session without a backend.
- Whether `-headless` changes player 0, since `LocalPlayerClass` becomes `UHeadlessLocalPlayer`.
- Whether `ASimCharacter` works with a pure `AAIController` (route B).
