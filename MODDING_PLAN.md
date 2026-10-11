# Foxhole RTS — initial recon

> Update 2026-10-07: the planning below keeps historical hypotheses.
> The executed state is in the MODLOG: v0.3 validated earlier; v0.3.1 adds
> per-group stop (H), with offline tests passed and in-game test pending.
> Use and evaluation of the toolkit: UNIVERSAL_MODDER_NOTES.md. Real rifles pending.
> Update 2026-10-07 (night): decision to stay fully offline with our own model.
> v0.4 validated in game: H stop fixed, classes with weapons in hand, recruitment and economy.
> Rifles through inventory/RPC left the critical path.

Date: 2026-10-06. Status: investigation; no RTS route demonstrated.

Update (round 2): the client executable contains server code (listen server via `?listen`, `ASimGameMode`, ReplicationGraph). The likely blocker is the dependency on the `FExternalWarService` backend. There is no public route (offline, private server, SDK). Details in `ENVIRONMENT_RECON.md` (section Round 2). Next step: measure that dependency by decompiling in Ghidra, without running the game.

## Verified installation

- Path: `D:\SteamLibrary\steamapps\common\Foxhole`.
- Store: Steam; App ID `505460`; installed build `25730371`, according to the local manifest.
- Engine detected by the scanner: Unreal, signature `UE4+Release-4.24`. It does not determine all engine customizations.
- Project: `War`; main executable: `War\Binaries\Win64\War-Win64-Shipping.exe`.
- The scanner found two PAK files, no IoStore, and no installed loader.
- No EAC/BattlEye/EOS/packer (checked in files, strings and process history). There is VAC, the game's own time-discrepancy detection and `bAllowMods` on the server: treat the online client as protected.
- Main PAK with an unencrypted index, no `.sig`, no IoStore.
- Config/logs/saves missing: the game never ran on this installation. They will only be created after the first launch.

## Route and limitations

The official FAQ does not support gameplay mods or single-player with bots. It only mentions visual mods without competitive advantage: https://www.foxholegame.com/faq.

The scanner suggests UE4SS/PAK because it recognizes Unreal. That suggestion is generic, NOT confirmed compatibility with Foxhole, and will NOT be applied to the online client.

History: the initial route was read-only recon. It was replaced by the route below, with the normative design approved on 2026-10-06. UE4SS goes **only** into the lab copy, never into the online client.

## Chosen route: isolated local listen server (technical feasibility pending)

"Isolated local listen server": use the server code already present in the client to host a local session, without connecting to the official servers. The RTS layer (camera, selection, orders) comes later, through UE4SS/Lua or pak.

Conditions, none satisfied yet:
1. **Technical:** `?listen` and `ASimGameMode` work without `FExternalWarService`, or with a dependency that can be worked around without faking authentication. Measured by decompilation.
2. **Normative (approved by the user on 2026-10-06):**
   - Keep the Steam ownership check intact (`steam_api64`, no touching DRM or tickets).
   - The modified session never contacts Siege Camp services. `FExternalWarService` calls get local answers only inside the local session.
   - The local server runs without VAC (insecure mode, to be confirmed).
   - The mod stays inactive outside the local RTS mode.
   - Rejected: "authenticate online and then go offline", because it exposes a modified client to the official backend (VAC/ban risk).
3. **Isolation:** lab copy that never connects to official servers (VAC). Backup and authorization before installing a loader.

Alternatives, if the route falls:
- (a) visual/UI-only mod through pak, tolerated but without simulation;
- (b) RTS-like dashboard over the War API, read-only;
- (c) ask Siege Camp (draft in `ENVIRONMENT_RECON.md`).

## Next checks

The operational document is now `HOW_TO_MAKE_THE_MOD.md`: architecture, limitations and test protocol T0–T9. Summary of the state:

1. **Done (static):**
   - direct boot into the map from the command line;
   - no Steam server/VAC in a client;
   - the only host blocker is the profile in `PostLogin`;
   - soldiers = extra local players, `-headless` template;
   - maps without NavMesh.
2. **To run with the user:** T0–T3 (launches of the client and the copy, `?listen`, VAC check in the log).
3. **Later:** UE4SS in the copy (T4–T5), C++ profile stub (T6), first soldier (T7), navigation (T8), squad milestone (T9).

## Verification performed

- Round 2: local recon, static PE/strings/xrefs analysis, web research and KB sweep, all read-only. Ghidra 12.1.2 + GhidraMCP 5.14.2 installed in `D:\tools`; project `D:\tools\ghidra-projects\Foxhole`, outside the repo.

- `python -m um scan "Foxhole" --json` — static inspection, 43 files indexed, no truncation reported.
- Reading the Steam manifest and a shallow listing of executables.
- Local KB search for Foxhole with no results; the Unreal notes found do not prove support for this game.
- No game opened, process instrumented, installation file changed or package extracted.
