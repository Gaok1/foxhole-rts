<p align="center"><img src="assets/FOXHOLE%20RTS.png" alt="Foxhole RTS" width="640"></p>

# Foxhole RTS

A fan-made **single-player, fully offline** mod that turns a local lab copy of
[Foxhole](https://www.foxholegame.com/) into a real-time strategy game against an AI:
top-down camera, box selection, squads, control groups, and above all **logistics**:
scrap fields, refinery, factory, supply trucks, depots and recruitment from stock.
The war is "the small part of the machine"; the supply chain is the game.

> **Status: early prototype (v0.9).** Combat, orders, waves and the logistics loop work in a
> small region (`HomeRegionW`), but there are open crashes and the full supply chain is not yet
> approved in live tests. See [`ROADMAP.md`](ROADMAP.md). Expect breakage.

Built with [UE4SS](https://github.com/UE4SS-RE/RE-UE4SS) (Lua, Unreal Engine 4.24),
developed with heavy AI assistance (Claude, Codex) and lots of reverse engineering.

## Roadmap

<!-- progress:start -->
| Phase | Progress | |
|---|---|---|
| Phase 1: Small front (squad combat in HomeRegionW) | `█████████████░░░░░░░` | **65%** |
| Phase 2: Study the game's mechanics (from the game's own data) | `██████████████░░░░░░` | **71%** |
| Phase 3: Logistics in one region (current phase) | `███████████░░░░░░░░░` | **54%** |
| Phase 4: Vehicles and heavy weapons | `████░░░░░░░░░░░░░░░░` | **20%** |
| Phase 5: Several regions and the world | `░░░░░░░░░░░░░░░░░░░░` | **0%** |
| **MVP (phases 1-3)** | `████████████░░░░░░░░` | **62%** |
<!-- progress:end -->

Every percentage comes from the item checklist in [`PROGRESS.md`](PROGRESS.md)
(done = 1, partial = 0.5). Pick an unchecked item, open an issue, and move a bar.

## Disclaimer

- Not affiliated with, endorsed by or supported by Siege Camp. "Foxhole" is their trademark.
- This repository contains **no game files**: no binaries, DLLs, paks or extracted assets.
  Characters, models and effects come from your own copy of the game at runtime.
- **Never install this on your real Steam install and never take a modded copy online.**
  It is meant for an isolated copy of the game, blocked from the network. Using client mods
  on official servers can get your account banned. You are responsible for your own account.
- You need to own Foxhole on Steam. The mod does not touch the Steam ownership check.

## Requirements

- Foxhole on Steam (Steam running and logged in). Last tested build: Steam 25730371 / UE 4.24.
- A **separate copy** of the game folder (the "lab copy"), with `steam_appid.txt`, and outbound
  network blocked for it (e.g. a Windows Firewall rule). The menu will show a server download
  error; that is expected.
- UE4SS installed **only in the lab copy**, matching UE 4.24.
- Back up `%LOCALAPPDATA%\Foxhole` before each modded launch.

`tools/lab.ps1` (Windows PowerShell 5.1) automates the safety checks, the copy preparation,
UE4SS install/removal and launching. Read its header and `HOW_TO_MAKE_THE_MOD.md` first;
the default paths (`D:\...`) are the author's, pass your own with `-SteamGame`, `-LabGame` and `-Ue4ssDir`.

## Install

1. Close the game.
2. Copy `mod/FoxholeRTS` to `War\Binaries\Win64\ue4ss\Mods\` **in the lab copy**.
   `enabled.txt` enables it.
3. Launch the lab copy. The first load can sit on a black "Not responding" screen for ~3 minutes.

## Quick start

- **F9** opens the local session, **F10** toggles the RTS camera, **F5** shows the key list.
- **Shift+F6** starts a match: squad of 6, three control points, automatic waves.
  Capture the points, recruit with Ctrl+1-4 and survive 10 waves, or hold all three points for 90 s.
- **Alt+L** deploys the initial refinery/factory and trucks for the logistics scenario.

Full controls and mechanics: [`mod/README.md`](mod/README.md) (Portuguese).

## Repository layout

| Path | What |
|---|---|
| `mod/FoxholeRTS/Scripts/main.lua` | The whole mod (single Lua file) |
| `mod/README.md` | Controls, mechanics, install details |
| `tools/` | Offline tests (`test_orders.py` and friends), probes, cost exporter, `lab.ps1` |
| `data/` | Data and traces recorded from the game; `data/parallel/` holds parallel agent work, patches and reports |
| `MODLOG.md` | Development diary, newest first. Read "Como retomar" before working |
| `ROADMAP.md` | Where the project is going and what is broken now |
| `AGENTS.md` | Rules and pitfalls for AI agents (and humans) working on the code |
| `MANUAL_TEST.md` | Manual test checklist |
| `MECHANICS_STUDY.md` | Game mechanics extracted from the game data |

**Most docs are in Portuguese.** Issues and PRs in English or Portuguese are both welcome.

## Running the offline tests

```bash
python tools/test_orders.py
```

Most logic is tested offline in Python against `main.lua` before going to the game.

## How to help

Foxhole players who want a logistics RTS in this world, this is for you. Useful areas right now:

- **Reverse engineering** (Ghidra/UE4SS): native rifle hit/damage path, truck collision with native
  explosives, the PlayerState/UniqueId crash for AI-controlled characters.
- **Logistics**: trucks following the native road network instead of straight lines, bridges, water.
- **AI**: enemy supply chain and front decisions.
- **Testing**: run the lab, follow `MANUAL_TEST.md`, report crashes with `UE4SS.log` and the crash folder
  from `%LOCALAPPDATA%\Foxhole\Saved\Crashes`.
- **Foxhole knowledge**: real logistics numbers, recipes, how things should feel.

Ground rules (from `AGENTS.md`): stay fully offline with the mod's own systems (no game RPC, server
or native inventory), never bypass Steam/DRM, never remove the lab's network block.
Record real traces of the game's own calls before reinventing a mechanic by hand.

Open an issue first for anything big, so work does not overlap.

## License

[MIT](LICENSE) for the code and docs in this repository. Foxhole and its assets belong to Siege Camp.
