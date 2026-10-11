# Investigation of the simulation environment

Date: 2026-10-06 | Local Steam build: 25730371

## Result

No public, documented and usable route was found to run the installed Foxhole as an offline/controlled simulation for the RTS mod. This is a limited result of the investigation, not proof of technical impossibility.

## Local evidence — read-only

Installation: `D:\SteamLibrary\steamapps\common\Foxhole`.

Executables found in the recursive listing:

- `War.exe`
- `War\Binaries\Win64\War-Win64-Shipping.exe`
- `Engine\Binaries\Win64\CrashReportClient.exe`
- `Engine\Binaries\Win64\UnrealCEFSubProcess.exe`
- `Engine\Extras\Redist\en-us\UE4PrereqSetup_x64.exe`

No loose files with the extensions `.bat`, `.cmd`, `.ini`, `.uproject` or `.uplugin` were found in that listing. No separate server or editor executable was identified. This does not show that all server code is absent from the client executable; that hypothesis was not tested.

In the specific folder `War\Content\Paks` there is one package: `War-WindowsNoEditor.pak`, 25,681,549,397 bytes. The count of two PAKs in the initial scan must not be read as two gameplay packages: there are auxiliary packages outside that folder, including the crash reporter's and the embedded browser's.

The NonUFS manifest identifies the Shipping executable and auxiliary libraries. The `vivoxsdk.dll` entry is the Vivox voice SDK, not a Foxhole modding SDK.

## Primary sources consulted

### Official FAQ

https://www.foxholegame.com/faq

States there is no official support for mods, single-player or bots. Mentions visual mods that give no advantage. Does not provide an offline route for an RTS simulation.

### Official War API

https://github.com/clapfoot/warapi

Documents GET queries for war state, reports and maps. Does not document commands to create units, move characters or run a server. Useful for querying/visualizing, not as an RTS control interface.

### Foxhole Data Extractor — author's documentation

https://github.com/C1ach0/fde

A tool that reads local PAKs with CUE4Parse and produces JSON catalogs and icons. The term "server-oriented" describes running the extractor on a server, not a playable Foxhole server. It was not installed or run.

### Mod creation tutorial — author yurisuika

https://steamcommunity.com/sharedfiles/filedetails/?id=3207287574

The declared scope is changing textures through extraction, editing and repacking. It does not demonstrate control of the simulation. The page shows removal/incompatibility warnings; it is not a validated recipe for our build.

## What was not done

- No injection, patch, PAK extraction or instrumentation.
- No game launch or connection to servers.
- No attempt to enable undocumented commands or bypass authentication/protection.
- No download of a leaked server/SDK and no messages sent to third parties.

## Next step that could solve the blocker

Get specific information from Siege Camp or the modding community about an authorized offline environment, SDK or legitimately provided test server. Suggested question, NOT sent yet:

> I own Foxhole on Steam and would like to try a strictly offline RTS conversion, without interacting with official servers. Is there a test environment, SDK, dedicated server or authorized procedure to run a local scene with control of the simulation? Are gameplay mods of this kind allowed in that environment?

If a candidate tool shows up, check its origin, permissions and compatibility with the build before installing. The project remains a mod for Foxhole; no change to a standalone game was made.

---

# Round 2 — deeper recon (2026-10-06)

Four agents in parallel, all read-only (nothing run, injected, extracted or changed). Tools: universal-modder's `python -m um scan`/`kb`, pefile/capstone for static analysis, WebSearch/WebFetch. Drafts and dumps stayed outside the repository (the session's scratchpad).

## Short result

1. **The client contains server code.** `War-Win64-Shipping.exe` is a *Game* target (not *Client*): login/join acceptance, `UWorld::Listen`, the `Listen` URL option, the game's ReplicationGraph and `ASimGameMode` are compiled and referenced. A local listen server is technically plausible; a dedicated server (`-server`) probably not.
2. **Likely blocker: external backend.** The game server depends on `FExternalWarService` (auth, profiles, travel reservations, war config). A local simulation should break at these points. Not measured yet — requires decompilation.
3. **No public route:** no offline mode, bots, distributed private/dedicated server, SDK, editor or Workshop (official sources).
4. **Protection:** no EAC/BattlEye/EOS/packer. There is **VAC**, the game's own time-discrepancy detection and `bAllowMods` in the server settings. PAK signing code exists but is not active (no `.sig`).
5. **Open PAK:** unencrypted index; texture/UI mods in `War\Content\Paks` are common community practice (TrenchKit, Nexus, itch.io).

## Local evidence (Sonnet — recon)

| Topic | Finding | Status |
|---|---|---|
| Anti-cheat | No EAC, BattlEye, EOS or `start_protected_game` file/string; Steam `gameprocess_log.txt` from Jan/2026 shows only `War.exe`, Shipping, CrashReportClient and CEF | Verified |
| BEService on Windows | Belongs to Rainbow Six Siege (`%LOCALAPPDATA%\BattlEye\r6s`), not Foxhole | Verified |
| Steam manifest | No `LaunchOptions`; build 25730371, depot 505461 | Verified |
| Config/logs/saves | Missing: the game never ran on this installation. It ran in Jan/2026 on an old installation in `G:\steam\...` (removed) | Verified |
| PAK `War-WindowsNoEditor.pak` | Footer v8 (UE4.24), index at 25,678,359,878 (3,189,298 bytes), SHA1 `b0693e21…8dba5b`, **unencrypted index** (flag 0, zero GUID), no `.sig`, no IoStore | Verified (only the footer was read) |
| Binaries | Shipping 80 MB; Vivox and Discord RPC plugins; `steam_api64.dll` (Steamv151) | Verified |

## Static analysis of the executable (Opus)

PE: `Foxhole4.24.3: 87680`, ProductVersion 1.64.6.1, embedded build "Oct 5 2026". No packer, no Authenticode, PDB missing, strings and reflection names intact (3049 native classes).

| Evidence | Strength |
|---|---|
| *Game* target (name `War-Win64-Shipping`, not `WarClient`) → WITH_SERVER_CODE | Strong (inference from UBT convention) |
| Server-side `UWorld::NotifyControlMessage` (VA 0x1429de920): "Login request…", "PreLogin failure", "Join succeeded" | Strong |
| `UWorld::Listen` (VA 0x1429dc8e0), "IpNetDriver listening on port %i"; `UEngine::LoadMap` tests `Listen` | Strong |
| `UWarReplicationGraph` and its own nodes (Rail/Air vehicle, GridSpatialization2D) — server-only logic | Strong |
| `ASimGameMode`, `AWarGameMode`, `AWarGameSession`, `UPlayerProfileManager`, `UWarSaveGame` | Strong |
| `UServerSettings`: `NextWarMapOverride`, `WarTweakables`, `IsCommunityServer`, `bAllowMods`, `bFriendlyFire`… | Strong |
| `EWarServerType::Skirmish/WorldConquest/Event/Training/HomeRegion*` | Medium |
| `"?listen"` built by game code (VA 0x141150223, probably `UWarGameInstance`) — purpose not identified | Medium |
| `-server` as a standalone string: absent | Inference: dedicated unavailable |
| Backend: `FExternalWarService::SendAuthMessage/OnAuthResponse/MapDataResponse/OnNextWarConfigMessage`, `FailureWarServiceUnavailable`; remote config at `s3.amazonaws.com/foxhole-updates/config/client_config*.json` | Strong (dependency) |
| AI/navigation: AIModule, BehaviorTree, EQS, Recast/Detour, Crowd compiled; the game uses AI only in turrets (`UAITurretComponent`…) | Engine strong / use by the game weak |
| Console/cheats: `UConsole`, `UCheatManager` compiled; activation in Shipping unlikely; the game's own cheats are regiment/squad admin requests | Classes strong / active console unknown |
| `Mods/` in the FPaths table = UE's default `ProjectModsDir`, not a Foxhole loader | Inference |
| VAC: "VAC ban detected - kicking…", `ETimeDiscrepancyType::AntiCheat` | Strong |
| UE4SS: FNamePool/GUObjectArray locatable → technical compatibility likely, not tested | Inference |

## Public research (Sonnet — web)

- **Servers:** shards are central (Live1, Live2, Dev Branch via Steam Betas). No distributed private/dedicated server, no emulator. Sources: https://foxhole.wiki.gg/wiki/Shard, https://foxhole.wiki.gg/wiki/Development_Branch. Medium-high confidence (absence of evidence; Discord/devblogs not read).
- **Offline/bots:** nonexistent — official FAQ. "Modbox for Foxhole" in searches is SEO spam; discarded.
- **Anti-cheat and policy:** "VAC integration and other behind the scenes tools" — https://www.foxholegame.com/moderation-faq. Code of Conduct (Siege Camp, 2020): forbids modifying the client to gain an unfair advantage. No documented case of a ban for a visual mod.
- **Community:** active texture/UI pak mods; TrenchKit (MIT, https://github.com/Tapawingo/TrenchKit) manages the load order by prefix. Nothing on UE4SS, gameplay mods, bots or emulators.
- **Official tools:** only the War API (queries) and Dev Branch. No SDK/editor/Workshop.

## Toolkit knowledge base (Haiku)

No previous Foxhole note. Toolkit rule (`skills/mod-any-game/references/safety.md`): stop if online-only without a server of the user's or with active anti-cheat, unless an offline mode disables it. Accepted route for server-authoritative games: own server + original client. Examples: AzerothCore, Project Zomboid dedicated.

## Combined reading

- The executable contains the simulation's authority. It is the only concrete lead to a "simulation under our control" with the official binary.
- Two unknowns decide feasibility:
  1. **Technical:** do the `?listen` path and `ASimGameMode` work without `FExternalWarService`? This is measured by decompilation, and Ghidra is being prepared.
  2. **Normative:** replacing or simulating Siege Camp's auth/backend service, even offline, may amount to bypassing an ownership/authentication check. This is forbidden by the toolkit's rules and needs an explicit decision before any step.
- VAC: any injection (UE4SS, proxy DLL) would only be acceptable in an isolated copy that never connects to official servers. Even then, there is account risk, to be assessed.

## Pending

- [ ] Decompile in Ghidra the function that builds `?listen` (VA ~0x141150070–0x141150380) and the `ASimGameMode` ↔ `FExternalWarService` flow. Measure what blocks without a backend.
- [ ] Check in the PAK index whether the maps have a generated NavMesh (`RecastNavMesh`). Read only the index, without extracting.
- [ ] Decide the normative route with the user before any modified run.
