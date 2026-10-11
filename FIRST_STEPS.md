# First steps — Foxhole RTS

This is an investigation plan, not a confirmation that the mod is already technically feasible.

## 1. Recon after installation

- [x] Confirm with the user that the installation finished.
- [x] Confirm the desired mode: solo against AI, squad control.
- [x] Locate the installation and record store, version/build and executables.
- [x] Run the toolkit scanner in read-only mode.
- [x] Identify engine, protections, settings, logs and any local saves. Config/logs/saves only exist after the first launch.
- [x] Refresh the research on community tools and official rules.
- [x] Record evidence and questions in `MODLOG.md` and the proposed route in `MODDING_PLAN.md`.

## 2. Decisive milestone: control of the simulation

- [x] Investigate whether there is an authorized route to load an isolated scene and control its simulation. Result of this round: none found; details in `ENVIRONMENT_RECON.md`.
- [x] Check what depends on the server and what can be modified locally. Static: the only host blocker is the profile in `PostLogin`; see `HOW_TO_MAKE_THE_MOD.md`. Still to confirm at runtime (T2).
- [x] Do not assume that changing the camera or textures allows creating and commanding units. Proven at runtime on 2026-10-07 (soldiers created and commanded).
- [ ] If no usable route is found, document the blocker and discuss with the user before changing the scope.

## 3. Prepare the lab — only with a demonstrated route

- [x] Present the necessary changes and ask for authorization to install any loader. Authorized (UE4SS only in the copy).
- [x] Back up the affected files/settings and record how to restore: `tools/lab.ps1` runs `um backup` of the config before each `run`; the Steam installation is not changed.
- [x] Separate the test environment from official matches: copy in `D:\FoxholeLab\Foxhole`, with a lock that refuses a loader in the Steam installation.
- [x] Prepare logs and a repeatable test: `tools/lab/restart.sh` + `cmd.lua` channel + `um win shot`.

## 4. First playable proof

- [x] Load a scene in the isolated environment (`HomeRegionW` in listen).
- [x] Create or provide a controllable unit (`HeadlessPlayerController`).
- [x] Select a squad and give a move order by click (all members move).
- [x] Verify real execution through logs and screenshot.

Success criterion: a unit executes an RTS order in a simulation under our control. Free camera, mockup or concept video do not count as this proof.

## 5. Expand only after the proof

1. Multiple selection, RTS camera and basic orders. *(camera and per-squad orders done; multiple selection not)*
2. Navigation, combat and simple AI. *(v0.3: combat with simulated damage and game effects, wave AI, simple obstacle avoidance; real weapon pending)*
3. Small battle: two infantry groups, one tank and one objective.
4. Production, transport and supply.
5. Construction, trenches and persistence, as far as the route allows.

## Closing each session

- Update the diary with results, failures, evidence and next step.
- Clearly distinguish what was tested from what is a hypothesis.
- When there are useful findings, prepare a note for the knowledge base; publish only with authorization.
