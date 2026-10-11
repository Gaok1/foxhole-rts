# Foxhole RTS — project diary

## 2026-10-11 — Published on GitHub; repository translated to English; agent skills

- The user asked to publish the project to invite collaborators from the Foxhole community: public repository,
  everything uploaded, MIT license, README in English, roadmap with completion percentages (`ROADMAP.md`, `PROGRESS.md`).
- Docs, reports in `data/parallel/` and this diary translated to English; from now on docs, the diary,
  comments and commits are written in English (chat with the user stays in Portuguese).
- What was NOT translated, on purpose: in-game UI strings and log messages (quoted as they appear, e.g.
  "modo RTS ligado"), and the contents of `data/trace_*.txt` (raw recorded output). Older entries keep their
  measurements and hashes unchanged; only the prose was translated.
- Agent content modeled on universal-modder: `AGENTS.md` (shared by Claude/Codex/Gemini), skills under
  `.claude/skills/` (`resume-work`, `wrap-up`, ...), `CONTRIBUTING.md`.
- Known limit for outside contributors: `CFG.CMD_FILE` in `main.lua` is still hardcoded to `D:/tools/foxhole-lab`,
  and the lab scripts (`restart.sh`, `run.sh`, `botloop.sh`) live outside the repository.
- No change to mod behavior in this entry; no lab session.

## 2026-10-11 — Save: unknown HP refuses writing, does not resurrect old state

- Extending the real test reproduced a FAIL: the observer suspends transport with
  NaN/infinite/text HP, but the snapshots ignored the refusal and saved old HP/cargo.
- Friendly/enemy snapshots now require known HP or an already resolved death.
  sv.save catches the collection failure and returns false with a log, before validating/writing;
  the previous file is kept. A schema error is not turned into death/loss/credit.
- The widened test covers both sides, NaN/±infinity/text, intact stock and a spy
  that forbids writing/validating the incomplete snapshot. FAIL before/PASS after;
  all 15 test_*.py and check_globals PASS. No proof of Unreal bindings/continue.
- Candidate A36E9052562BBB52CAE97304D80CC6742C66EB32B031BE07AC0BE10C7B23205B,
  not published. External backup main-before-snapshot-schema-gate.lua. WMI without the lab.
- Debt identified while reviewing persistence: unitData does not keep the manual cargo
  in m.col; colReset discards the cargo on continue. The next implementation needs to
  keep the cargo on the worker and replan the physical delivery, not credit the refinery.

## 2026-10-11 — Save: convoy death observed before saving cargo/wallet

- Defect reproduced offline: eSnapshot turned the cargo of an actor with Health 0 into
  pending/free fleet when the death had not yet gone through the logistics tick.
  New regression FAILs on source 85D7EEB9; uses the real eLose/eSnapshot/syncHealth/sv.collect.
- eSnapshot now observes native HP before accounting each convoy. sv.collect
  resolves snapshots before copying manpower: the reward of that observation goes into
  the same write, not only into memory after saving. No damage/fictitious actor.
- Tests HP0, invalid/destroying actor, wounded alive, repeated save and copies PASS;
  single loss/cargo/rebuild/credit. All 15 test_*.py and check_globals PASS.
  Mocks do not prove lifecycle/TTL or Unreal save/continue; wounds still do not persist.
- Candidate source 01AE83482408D760C9FF22E8BA3226616A4F67016A1077BFCBD702AB22A5E547,
  external backup main-before-enemy-snapshot-health.lua. Not published, no restart.
  Live gate accumulated in NATIVE_BATCH for the next integrated session.

## 2026-10-11 — Movement: the no-controller flag does not replace locality

- Traced the native property bRunPhysicsWithNoController: generated setter
  142a314d0 sets bit 4/+1f1. In flow 140ae1d60, a non-local character WITH a
  Controller goes to the remote branch before consulting that flag. Do not turn off
  bIsLocalPlayerController assuming this option keeps the current simulation.
- A CPU oracle runs the real fragment 140ae1e16..140ae1e85 and the pawn's locality getter
  142778b00: six possession/locality/flag combinations PASS. With possession,
  flag false/true does not change the branch; without a Controller it does. The controller getter
  and root motion are shims; it does not prove displacement, possession, GC or an Unreal fix.
- Alternative discarded offline without touching main or unpossessing NPCs. Scripts/
  output/decomp external; no run. Keep PlayerState/possession to avoid
  the historical regression of the pawn being collected after about 20 s.

## 2026-10-11 — Public repository on GitHub

- The folder became a git repository and was published at github.com/Gaok1/foxhole-rts (public, MIT) to invite
  collaborators from the Foxhole community. Everything went up, including `data/parallel/`.
- Root `README.md` in English (notice of no affiliation with Siege Camp, no game files, never online).
- `PROGRESS.md`: public checklist per phase ([x] = 1, [~] = 0.5, [ ] = 0); `tools/progress.py` recomputes
  the README bars. Starting point: phase 1 65%, phase 2 71%, phase 3 54%, phase 4 20%, phase 5 0%, MVP 62%.
- `.gitattributes` with `* -text` keeps the bytes of patches and SHA256-tracked candidates.

## 2026-10-11 — Oracle extended to the list's native producer

- Ran offline the five real functions producer → bridge → controller virtual
  → forwarding → helper. Fixtures provide world/classes/PS;
  getters/destructor/comparator are explicit shims, no Unreal execution.
- Two PlayerStates with a null identifier object produce eight entries in
  four ticks, with bVoiceChatEnabled false. Without PlayerSaveGame they also accumulate.
  When one roster entry is swapped for a non-null object, read 0 fails at the same
  RVA b2b5f7. Controls empty roster/missing PS/valid object/deduplication PASS.
- The evidence rules out turning off voice or removing PlayerSaveGame as a sufficient fix
  in that emulated flow. It does not confirm the real population, the guilty controller, GC or a fix.
  The next step requires a live NPC/roster contract, not fabricating IDs nor using RPC.
- External script/output: re-agent/test_native_roster_producer.py and
  logistics2-native-producer-oracle.txt in D:/tools/foxhole-lab. Lab
  absence confirmed; no change to main/publish/run.

## 2026-10-11 — Crash reproduced in the native helper, offline

- An external oracle ran the 303 real bytes of 140b2b5a0 on a Unicorn CPU,
  without opening/changing the game. Eight null entries accumulate; a non-null entry
  after them fails reading address zero exactly at the minidump's RVA b2b5f7.
- Positive comparison/deduplication controls PASS with a fictitious comparator.
  A valid item before a null also does not protect a different entry.
- This confirms the helper's failure sequence, NOT who produced the nulls,
  the real identifier's semantics, GC or an Unreal fix. No new run.
- External script/output: D:/tools/foxhole-lab/re-agent/test_native_null_roster.py
  and D:/tools/foxhole-lab/logistics2-native-null-oracle.txt. Unicorn in D:/tools/pylibs
  is a research tool, not a mod dependency.

## 2026-10-11 — Universal-modder updated at the user's request

- git pull --ff-only in D:/GitHub/universal-modder: 76b9c7e -> 2c22014,
  main equal to origin/main. The first pull refused to overwrite local adjustments.
- External backup at D:/tools/um-pull-backup-20261011-180446 and the stash kept.
  Adjustments to um/win.py, um/ps1/WinDrive.ps1 and the Foxhole note reapplied; conflict
  only in the WinDrive command header, resolved keeping min/sleep/idle.
  Changes went back to the unstaged state; no commit/push/PR created.
- Foxhole note compared to the backup: identical content, only CRLF/LF changed.
  PowerShell/Python syntax PASS; um kb check PASS (183 notes, before 60).
  The launch pytest did not run: pytest module missing in the current Python; do not install
  dependencies just for this pull nor claim the toolkit's full battery.
- No change/publish of the mod nor opening of the lab in this update.

## 2026-10-11 — HeadlessLocalPlayer initialization and RE helper fix

- Static investigation of the native NPC found HeadlessLocalPlayer with its own
  initialization of a NULL-type identifier and Headless options. The constructor alone does not
  run that init. No own reflected UFunctions and no proof of a link to the
  local PlayerState; do not construct a LocalPlayer nor chase connection/login/RPC
  as an attempt to fix the crash.
- Fixed the external helper pe.vtable_of: before, it followed the base call and confused
  LocalPlayer with derived classes whose wrappers write the vtable inline. The earlier check
  FAILED, seven classes PASS after the fix. The slots used in the crash diagnosis
  were rechecked and stay the same. Still heuristic, not a live proof.
- Own trace in data/trace_crash_logistics2_20261011.txt; scripts/check and
  decompilation external. No change to main, publish or new run.

## 2026-10-11 — Local contract of the bots; roster probe prepared offline

- RE confirms SimCharacter tests Controller.IsLocalController on the voice
  path. Headless and SimPlayerController use the same getter; bIsLocalPlayerController
  true returns before querying NetMode. The flag the mod turns on for movement
  also exposes the bot to the local flow. It does not show by itself which actor crashed.
- OnRep_bIsInactive removes/reinserts the PlayerState in GameState.PlayerArray; adding
  refuses inactive. Not called nor used as a solution: a disconnected participant is not
  a live NPC, lifecycle effects still need tracing.
- Prepared tools/probe_native_npc_roster.lua to photograph locality/Player/
  Pawn/PlayerState/roster of the commander, troops and pool. No Steam IDs, writes,
  RPC, spawn or timer. Getters check their signature. gs() is GameplayStatics;
  GameState comes from GetGameState(world()), do not confuse the helper with the state.
- tools/test_native_npc_roster_probe.py PASS: valid/divergent/extra/
  missing signature, deduplication, member/pool outside the roster, controller being destroyed,
  missing GameState and proxies that forbid writes/IDs. They are mocks, not Unreal proof.
- Complete battery: 14 test_*.py scripts and check_globals.py PASS. main.lua
  unchanged, no restart, WMI without a lab process.

## 2026-10-11 — Crash: UniqueId list in the local participants/voice flow

- Offline readOnly/noanalysis diagnosis confirmed PlayerState.UniqueId as the
  origin of the shared pairs that reach the crash helper, through the
  proximity query and GameState.PlayerArray. Metadata in
  data/trace_crash_logistics2_20261011.txt; protected code only external.
- PlayerSaveGame.bVoiceChatEnabled (+0x48, generated setter confirmed) controls
  only the nearby query, NOT the later PlayerArray loop. Turning off voice does not
  solve it per the evidence and may keep accumulating empty IDs.
- The helper does not deduplicate a null entry and compares a non-null entry by dereferencing
  an existing item without a guard. Empty bot IDs are a concrete producer hypothesis;
  the whole population/controller identity in the heap missing from the dump is not proven.
- Next: the local controller contract (tick queries virtual +0x690) and the legitimate
  PlayerState lifecycle of an NPC; keep possession, movement and GC. Do not fabricate IDs,
  call RPC or blindly turn off bIsLocalPlayerController to hide the crash.
- No change to main.lua, publish or restart. Lab absent.

## 2026-10-11 — Logistics batch 2: RWD contract confirmed; match interrupted by a crash

- Prepared external scripts t_batch_logistics2_*; a 1 s sampler of workers/
  threat/cargo and a 10 s summary, syntax/mock PASS. Thirteen offline tests/globals PASS.
  One publish/run CallumsCape/PID4696, source/lab hashes equal
  85D7EEB942704D767402F3EEE31159D80E144C6BB170A1BF90C98BD9FCEA9DEB.
- Read-only probe before/after logistics: the same truck with ActorCollision
  true→false; root and UpdatedComponent/Primitive=VehicleCollision(BoxComponent).
  Movement RWDVehicleMovementComponent→SimpleVehicleMovementComponent→CharacterMovement;
  flag bIgnoreNonRootComponentsDuringVehicleMovement=true in both states.
  Data in trace_truck_movement_{before,active}_20261011.txt. It does not prove the road,
  impact on the fleet, envelope/support nor allow changing the flag to force success.
- A fresh match without save/credits/extra speed interrupted by a crash.
  CrashContext ProcessId 4696/158 s since start; own autosave at 60.043 s/wave 1,
  bmat 40/salvage 0/base 19 shirts. Final report NOT obtained: the samples were in RAM.
  It does not approve medevac, hiring under threat, delivery or rebuild in Unreal.
- PID absent/WMI confirmed, channel timeout 30 s. Crash DE679306…/17:36:33 kept
  externally in logistics2-crash; UE4SS log copied. Own stack/metadata
  in data/trace_crash_logistics2_20261011.txt, with no minidump/protected code in the repo.
- The minidump shows RVA 0xb2b5f7/Rcx 0: instruction mov rax,[rcx] in 140b2b5a0.
  PCallStack starts above with 1427c66cb; do not confuse the caller's return with the fault.
  RE readOnly/noanalysis exit 0 ties the frame to processing a shared list
  through 1427f2a00 and tickSimCharacter 140b110c0→140b141a0→140b33df0.
  A null item/context in the list proven; producer/complete cause NOT isolated.
  No patch by offset, protection change or restart to try again.
- Lesson for the next batch: the logistics3 sampler now writes/closes each line
  to an external file, syntax/write PASS, still NOT run in the game. This keeps
  a partial diagnosis if there is a crash, it does not recover the samples lost in this batch.
- No second run. Temporary map.txt removed (baseline absent), pending command
  cleared; no lab process left, Steam 16104 kept. README/ROADMAP/BATCH/
  ENVELOPE/UM updated; failures and new ideas go to the next offline work.

## 2026-10-11 — Automatic replacement under threat and a gate without a phantom truck (offline)

- Flow traced: colMaintain hired every 3 s up to 3 alive; spawnSite only decides
  stock/location/exit. colFree refused a worker in danger AFTER spawning.
  The earlier live batch showed replacement draining shirts, but did not sample the threat
  at the exit: do not claim this guard alone explains/will solve all deaths.
- colThreat centralizes the 3500 cm distance already used by colCalm. Automatic hiring
  checks the chosen exit before creating/debiting; a live enemy nearby blocks and
  warns "proteja a base". It does not block manual hiring of combatants, does not change
  damage/waves/immunity/stock. The dead/actors being destroyed do not hold back hiring.
  Limit 3, 3 s interval, authority and rollback stay. spawnBlocked in the state
  records the reason; resumption clears after the threat disappears.
- test_worker_spawn_threat runs real functions: boundary/distance of the exit,
  30 s without spending, resumption, corpse/destruction, authority, lack of stock,
  spawn/commit failure and limit. Fails with the earlier colMaintain, passes on the candidate.
- check_mvp_batch_trace used to approve a "rebuild" when PLAYER_TRUCK res was missing.
  Now it requires a single record/known state/finite positive HP/PAWN true; absence
  does not become proof. test_mvp_batch_checker uses labeled SYNTHETIC traces and refuses
  missing/dead/HP0/inf/no actor/duplicate/no cleanup. It does not prove a transaction or road.
- Thirteen test_*.py/globals PASS. Source 85D7EEB942704D767402F3EEE31159D80E144C6BB170A1BF90C98BD9FCEA9DEB.
  External backup main-before-worker-spawn-threat.lua; no publish/run/input.
  Live gates stay negative; the next batch needs to record threat/exit,
  shirts, workers/cargo/medevac and prove a fresh chain in combat.

## 2026-10-11 — Rifle: complete references tell trace/impact effect apart

- Resumed offline with UM/reverse-engineering/oracles/the Unreal playbook and ponytail.
  Four headless readOnly/noanalysis Ghidra jobs finished exit 0; no game/GUI,
  no offset run, no RPC/inventory. Protected decomp stays external.
- Listed all known direct references of the project, without the cap of 6: helper
  1409dcd30 has two callers (HMG and 1409a71f0); query 1409e9860 has eight callers.
  Rifle 140a691f0 does not appear as a direct caller of damage. It does not prove the absence of
  indirect calls nor the impossibility of a local executor.
- Two consumers are FighterWeaponTrace/AirTargetingTrace, another HitScanMount;
  do not generalize to the rifle. Followed callbacks of two branches down to helpers that
  manage object/position, with no known damage in the bodies examined.
- Guard 142407030 does not read Role like 142405420: it resolves context/world and forwards to a
  helper that returns 3 or 1/2. Do not call a timer guarded by Authority's 3 without proof;
  consistent with presentation/NetMode, still without dynamic validation.
- data/trace_firing_investigation.md updated with addresses/limits and the next
  authoritative cut. No change/publish of main.lua nor another game session.
  The rifle's local executor stays pending; do not replace it with temporal DPS/ApplyDamage.

## 2026-10-11 — Roads resumed: movement contract before turning collision back on

- Consulted UM/roadmap/How to resume and the roads artifacts. The real Callums graph
  405 controls/431 segments/4013 nodes is available, but without physical proof of the edges.
  roads/adapter/snapshot tests PASS. Do not integrate a straight line, a soldier's capsule or
  Box 450/210/230 as if they proved a truck's envelope/support.
- Recovered existing evidence: VehicleCollision 400/162/140; a ray scan
  hit CharacterMesh0 outside that box. Root/UpdatedComponent not yet
  identified; the actor's sweep alone does not prove it covers those bodies.
- New read-only tools/probe_native_truck_movement.lua: the getter's signature
  confirmed before root/movement; UpdatedComponent/Primitive/flag only
  through a specific schema. Lists input/movement functions and parameters without calling them.
  Does not change collision, does not write physics/stock and does not use dangerous mesh fields.
- test_native_truck_movement_probe PASS, including schema/scan refusals. Probe
  NOT run in Unreal. main.lua not changed at this step; the offline medevac
  fix stays a candidate. ENVELOPE_GATE/BATCH/README updated.
- Lab kept closed, no new publish/run. The next batch must obtain the
  native contract and integrate a physical path, not declare roads ready from the graph.

## 2026-10-11 — Collection: automatic medevac is not a player order (offline)

- Cause isolated in the external log native-batch-ue4ss.log, lines 866–867 and 890–891:
  "trabalhador ferido recua sozinho" immediately precedes the losses 35.8/34.3
  by "ordem do jogador". rts.medevacStep writes medevac/retreat, not orderT;
  colStep used to discard any retreat/medevac as human intervention.
- The fix in colStep keeps the link/cargo while medevac is active,
  does not collect/deliver nor replace the evacuation route, suspends the stretch timeout.
  On healing it resumes field/refinery. A change of orderT/hold/focus/area/queue/explicit
  retreat still cancels; death still loses the cargo a single time.
- test_collection_medevac.py runs real functions, fails on the earlier source and
  passes on the candidate: 70 s retreat, healing/resumption while collecting or returning, single delivery
  at the refinery, death/explicit orders and conservation. Navigation/engine mocked.
  Ten test_*.py and check_globals PASS. External backup main-before-collection-medevac.lua.
- No publish/restart/injected input. The next batch needs to prove conservation
  and delivery in combat in Unreal; it does NOT solve/prove all replacement or a fresh chain.
  ROADMAP/README/BATCH updated; no new key. UM knowledge recorded locally.

## 2026-10-11 — Single integrated batch; grenades work, the logistics MVP failed

- Prepared offline 13 scenes and a fresh regression, syntax/mock machine PASS;
  nine test_*.py/globals PASS. One publish through restart.sh and a single run
  CallumsCapeHex/PID19324, with no keyboard/mouse/RPC/inventory/HP write/test ApplyDamage.
  SHA256 source/lab equal ACB6ADFD3AE05828AB50C3D26CC3970673B09184E8FCD4BBCB3D010042CEFA64.
- Integrated grenades: Owner/Instigator and fuse 4 PASS. W collision on 900→788,
  W collision off 900→900, C collision on 900→883; simultaneous classes 900→771.
  Reset prevented damage; removing the thrower did not prevent the explosion (does not prove a death in
  combat). Borrowed/swapped context kept; reflected GC in flight PASS.
  All leases closed; no crash observed during the batch, not general stability.
- Hostile AND allied soldiers 100→1: native friendly fire observed; death did not happen.
  Do not turn off protection/debug nor claim the cause of the 1 HP floor without tracing.
- Gate truck_loss FAIL: 16 Colonial grenades left 900→850; LOST_DELTA 0,
  no death/TTL/lost cargo proven. Explicit fixtures, not balance.
  The checker check_native_batch_trace.py correctly returns 1 for that gate.
- Fresh MVP without save/credits/extra speed: 352.96 s, 35 samples, defeat at wave 3,
  22 kills/34 losses, resupply 18; enemy 4 deliveries/15 shirts consumed.
  Collection delivered 0/lost 110.0199, bmat stayed 40, resource not rebuilt.
  Audits C/E PASS in all samples. Log: 35.8+34.3 lost by "ordem do
  jogador", 39.9 by death; replacement drained shirts. Complete cause not isolated.
  check_mvp_batch_trace.py returns 1 for collection/refining/rebuild, does not require
  defeat nor give the MVP a PASS just because there was combat. Failures go to the next batch.
- Own traces in data/trace_native_batch_integrated.txt and data/trace_batch_mvp_integrated.txt. Scripts and the
  complete log external D:/tools/foxhole-lab/t_batch_*.lua/native-batch-ue4ss.log.
  Reports/fixtures cleared between scenarios. Final check: squad 0/enemies 0/logi false/
  context false/settings false/no pending report. PID19324 closed;
  after 3 s WMI/processes confirm no lab process, Steam 16104 kept.
  Temporary map.txt removed (baseline absent). There was no second restart.
- ROADMAP updated with the real priority: fresh collection, collision/roads and the native
  firing/loss executor. Published build is experimental, not stable. README/BATCH and
  universal-modder updated with evidence/limits; no PR.

## 2026-10-11 — Grenades per faction and the thrower's contract; partial batch prepared

- Earlier progress confirmed in the source: real logistics HP and removal of the vehicle
  DPS. Integration continued, without reducing the goal to green tests.
- Checked offline the getters Instigator 1422d9d90 and Controller 1422d9da0 in the binary;
  PostInitialize WarProjectile 140dbe460 ignores Instigator and derives MyController;
  BeginPlay 140da4a70 ignores Owner/parts. Own contract (without protected source)
  in data/contract_native_grenade.md. No offset run.
- Fixed the use of the Warden grenade for everyone: the Colonial thrower uses Grenade_C,
  identity GrenadeC and its own limits (max 1200 vs 1100 Warden), cache by
  identity. Unknown team/missing row refuse without spending a lease/cooldown.
  The real Owner is passed to the deferred spawn and Instigator written before FinishSpawning;
  do not write a weak MyController. Live friendly fire/attribution still pending.
- Grenade 24 scenarios PASS; context includes two simultaneous classes/partial explosion/
  cleanup without destroying a foreign grenade. All nine test_*.py + globals PASS.
- The channel exposes throwGrenadeFrom (the same real function) for an oracle with an exclusive actor,
  without inserting a truck into the character list. External commands t_batch_native_start.lua
  and t_batch_native_report.lua syntax PASS (no BOM), NOT run. Four cases
  W collision on/off, C collision on, resetFlight in a ~80 s sequence, native wait 12 s,
  real worker/controller thrower and cleanup between cases; no HP write/ApplyDamage.
- NATIVE_BATCH/README updated. The sequence is PARTIAL: it does not yet cover the death of the
  thrower/soldier/friendly fire/GC/live borrowed context or the MVP regression in the hex.
  Do not publish/open the lab before preparing those scenarios; no other run
  per discovery. The fleet stays without collision until an integrated A/B comparison.
- Universal-modder consulted at the start; Gotcha added and local kb check PASS.
  Lab not started, Steam kept, no keyboard/mouse input or PR.

## 2026-10-11 — Native HP in logistics; batch still offline

- Resumed: reread How to resume/top/ROADMAP, the skills reverse-engineering and
  mod-any-game/Unreal playbook; `um kb search foxhole` consulted. No injected
  input, publish/restart or open lab (Steam kept).
- Removed `logi.hit`, the abstract ambush DPS and the mortar multiplier on
  trucks. No invented damage forwarded to ApplyDamage. Nearby rifles now
  do not cut convoys: the native executor stays pending, a deliberate functional
  regression so as not to keep the system rejected by the user.
- `logi.syncHealth` observes real Health before drive/truckStep/convoyTick and save.
  Partial HP updates the mirror/panel. HP 0/actor loss cancels route/movement and
  debits the cargo once, schedules its own rebuild and drops the reference to the hull.
  Does not call OnRep, FX, hiding or destruction in the observer: the game's TTL is kept.
  A vanished actor does not grant a bounty; invalid HP suspends without inventing a death.
- An old save had abstract HP: that value is not written to the actor; state/cargo
  are still restored, native wounds do NOT persist yet. The dead show HP 0.
- Nine `tools/test_*.py` PASS + check_globals; the new test_native_truck_health runs the
  real helper and covers single loss/partial-zero HP/schema/destruction/absence/gates.
  test_orders updated: mock actor with Health, no expectation of fictitious DPS.
  External logs in D:/tools/foxhole-lab/offline-test_*.log. Source backup before this
  change: D:/tools/foxhole-lab/main-before-native-health.lua.
- `NATIVE_BATCH.md` updated: truck collision is OFF because of transport;
  do not presume a working explosive overlap. Instigator before FinishSpawning is already
  in the grenade candidate, but team/attribution/collision require a live gate.
  Do not consider the batch ready/published/stable; the next step resolves that contract
  and prepares sequential commands before the single integrated publish/run.
- README/ROADMAP updated; no new key. Local Gotcha added to
  universal-modder and `um kb check` run; no PR.

## 2026-10-11 — Offline grenade/context integration; no publish

- main.lua now replaces the own grenade mesh/arc/shell with a deferred BPGrenadeW,
  fuse 4 from the real data before BeginPlay, the CustomArc/MovementComp solver and native damage/FX.
  Fire only abandons the normal shot if throwGrenade succeeds; a failure does not spend the reload.
- rts.native* helpers anchor settings immediately in GI.ServerSettings, control
  reservations and track class/fullname (no cache of a dead projectile). The tick keeps the lease
  until the last grenade; reset destroys only its own and restore respects an external swap.
- Fixed a candidate failure: a REAL GrenadeRangeLimit 0 does not mean zero range.
  Validates positive speeds/fuse; range 0 adds no ceiling to the mod's limit.
- tools/test_native_context.py PASS and tools/test_native_grenade.py 20 scenarios PASS
  on the CURRENT source; test_orders/globals PASS. No live test/publish in this batch.
  External backup main-before-native-grenades.lua; changes still without an integrated gate.
- NATIVE_BATCH.md gathers criteria/scenarios into a single future session. Before it,
  the thrower's Instigator/Owner/collision and the logistics reaction to real HP are missing. A sub-agent studies
  that contract offline; do not confuse earlier oracles with a test of this main.
- README updated; the old grenade damage metric does not print a misleading zero.
  Rifle/mortar/convoy DPS remain a debt to remove, not delivered native combat.

## 2026-10-11 — The user asked again for batch testing

- The recent flow fragmented tests too much; the user asked to advance research/
  development offline and only then run all scenarios in a single run.
  Rule reinforced in AGENTS.md: no restart per probe/helper/discovery, scenarios and
  criteria prepared beforehand, one publish and a shared session, cleanup between
  scenarios. New ideas go to the next batch; exceptions only for a concrete blocker.
- The scenario already in progress finished restore/cleanup; lab closed. No
  new live tests now. Native trajectory recorded in data/trace_trajectory_native_grenade.txt;
  the integration and its scenarios must be developed offline before the next batch.

## 2026-10-11 — Native grenade exploded and dealt damage through its own timer

- Lab PID18148 HomeRegionW, exclusive truck 900 HP/Team 0/Authority true.
  SpawnActor BPGrenadeW 180 cm from the center, FuseTimer default 20, bExploded false.
  Fresh settings kept through GI.ServerSettings during the wait; no owner patch.
- After 27 s: truck Health 780, grenade not present among live actors; original
  restore null/cleanup PASS. data/trace_native_grenade_start.txt and end.txt.
  NO manual ApplyDamage, HP write, Lua HitInfo, RPC, formula or debug toggle.
  The projectile's own timer built the impact and ran native damage/FX.
- This proves a local explosive independent of inventory, not a throw by the
  soldier, trajectory/range, the real throw fuse or attribution to the thrower.
  Next: the local contract of MovementComp and the real fuse time for integrating
  throwGrenade, without replacing rifle fire with something else. main.lua unchanged.
- Lab closed by the confirmed PID/path, Steam kept.

## 2026-10-11 — Native explosive projectiles: schema and CDOs confirmed

- tools/probe_native_projectiles.lua syntax PASS and live read PID22020 HomeRegionW.
  data/schema_projectiles_native.txt. No spawn/detonate/RPC/CDO write.
- WarProjectile.Detonate and ApplyExplosiveDamageAndSpawnFx receive a HitResult
  StructProperty (static ProjectileHitInfo_NetQuantize, do NOT build a Lua table).
  MyController WeakObjectProperty, ExplosiveCodeName NameProperty; real templates.
- Grenade/BPGrenadeW/BPHELaunchedGrenade derive from TimedProjectile, FuseTimer 20,
  ProjectileLife 0/AutoDetonateTime 0. Identities GrenadeC/GrenadeW/HELaunchedGrenade.
  BPHEGrenade derives directly from WarProjectile, no fuse, identity HEGrenade.
  CDO and template do not prove initialization or explosion: timer/owner still being traced.
- An explosives sub-agent investigates the local initializer so as not to invent HitInfo,
  fuse/speed/formula. main.lua unchanged; lab closed with PID/path
  checked when going back offline, Steam kept.

## 2026-10-11 — Native lifecycle explains a hull still valid after HP zero

- A sub-agent traced the application: Health 0 dispatches virtual +d60 for the SimVehicle
  death, with effects/occupants, then schedules a native SetLifeSpan 15 s.
  An actor valid right after the damage is expected during the hull's TTL, NOT an indication
  that OnRep_Health or another callback needs to be called manually.
- The explosion/drop observed by the user are consistent with that chain. Do not
  repeat just to force an immediate bActorIsBeingDestroyed nor use cleanup as
  proof. TTL 15 s identified statically, duration still not sampled live.
- The rifle still has no demonstrated local authoritative executor; the Lua bridge exposes
  only an invocation wrapper and replication callbacks. The study continues without RPC.
  A new sub-agent traces native local explosives/projectiles, without inventory,
  to use the real mechanism instead of forwarding the artificial DPS to the engine.

## 2026-10-11 — The user confirmed the truck's explosion and drop

- After the native HP oracle 900→0, the user observed the truck exploded and
  left something on the ground. Positive manual visual evidence of the game's destruction
  reaction, besides the recorded Health 0. The drop's item/actor not yet identified;
  do not claim content, inventory or persistence. No new intervention.

## 2026-10-11 — Three native applications, HP down to zero without a crash

- tools/oracle_native_vehicle_damage.lua syntax PASS and live PID12456 HomeRegionW,
  exclusive actor 900 HP/Team 0/Authority true after 12 s. Fresh settings bound
  immediately and kept through the UProperty during all calls.
- LightKinetic 45 returned 27/HP 900→873; HeavyKinetic 55 returned 33/HP 873→840;
  Explosive 1500 (a TEST overload, not the mod's ammo/formula) returned 1050/HP 840→0.
  data/trace_damage_native_repeated.txt. No HP write, offset/RPC/debug toggle.
- Health 0 is proven, NOT the complete destruction/wreck lifecycle: the actor was still
  not bActorIsBeingDestroyed on return, and cleanup removed it afterwards.
  Original restore null/cleanup PASS, no crash in this oracle. Do not extrapolate to the rifle.
- Do not convert the own DPS into native calls and declare the integration finished:
  legitimate local firing/impact/ammo are missing. A sub-agent resumed the rifle executor.
  main.lua unchanged. Lab closed by the validated PID/path, Steam kept.

## 2026-10-11 — Native vehicle damage proven with fresh settings

- A static constructor proved the private TMap initially empty/safe. New
  lab PID20688 HomeRegionW, Steam 20280; exclusive truck 900 HP/Team 0/
  Authority true, a 12 s wait without settings kept only in Lua.
- In the same chunk: baseline ApplyDamage 45 Explosive without settings returned 0/HP 900;
  a NEW constructor + immediate binding to GI.ServerSettings + the same call
  returned 31.5 and Health 900→869. There was no HP write, own formula, RPC,
  debug/protection change or offsets. data/trace_damage_settings_fresh.txt.
- Original restore null PASS; exclusive actor removed, cleanup true. This proves a
  GENERIC native application on the vehicle, NOT rifle fire, death or integration
  into the mod's ambushes. The main.lua source stays unchanged.
- Result consistent with the GC hypothesis for the old settings; it does not prove by itself
  the exact mechanism of that crash. In the integration, anchor the settings by a native
  reference during its whole lifetime, not a loose Lua cache between calls/frames.
- Lab closed by PID20688/path confirmed after the test; Steam kept.

## 2026-10-11 — Lifetime hypothesis for the oracle's crash; no turning off debug

- Offline investigation of the stack reached the native damage debug branch, which queries
  a TMap in ServerSettings. The minidump shows an absurdly high index, consistent with an
  invalid object/container; it is NOT proof of the exact cause. The constructor has debug on.
- Hypothesis: the settings stayed only in Lua _G during the 12 s wait. A Lua reference
  does not anchor a UObject against GC; Outer alone does not certify lifetime either. Do not turn off
  debug nor change a formula to mask a possible invalid reference.
- External oracle scripts prepared to create NEW settings in the same chunk
  that binds them immediately to the UProperty GI.ServerSettings and calls ApplyDamage,
  without keeping settings during the wait. Log checkpoints before/after the calls
  avoid losing all evidence when cmd.out is only written at the end. Syntax PASS;
  NOT run. Still confirm the TMap's initialization before a new lab.
- No new feature/main source changed; Steam open and lab closed.

## 2026-10-11 — Visibility by distance stays in the queue

- The user reports things still disappearing with distance and asks to record it in the queue.
  ROADMAP reinforced: reproduce by moving away/zoom, separate culling/LOD from LOS/occlusion,
  identify live/loaded actors and validate visibility within the RTS range.
  No new diagnosis or fix delivered; do not deviate now from the MVP's native integration.

## 2026-10-11 — Native defaults confirmed in the engine; the damage oracle crashed

- Steam opened by the user, PID20280. restart.sh started lab PID24924,
  HomeRegionW; only the channel, no keyboard/mouse input by the agent.
- tools/probe_native_settings.lua PASS live: own ServerSettings instance,
  all five defaults correct and the nested WarTweakables binding working.
  GI.ServerSettings stayed null. data/trace_settings_defaults_live.txt.
- Separate oracle: exclusive truck 900 HP, Team 0, Authority true. After 12 s,
  the script compared ApplyDamage 45 Explosive before/after a temporary binding
  of the settings, with restore/cleanup at the end. The process crashed natively;
  pcall does not protect against that and the out buffer was not published. We do NOT know
  which of the two calls crashed; do not claim damage or restore proven.
- Crash UE4CC-Windows-608B38A24B507F2999BD40955C73B6EF_0000, access violation;
  stack includes RVAs b5d5bc, b64277, d613df, d82713, d96e1c (TakeDamage), 2550198.
  data/trace_settings_damage_crash.txt. Do not repeat without isolating callback/context.
  The damage sub-agent is investigating offline; decomp stays external.
- Lab absent after the crash, confirmed; Steam kept. main.lua without
  change. The own settings were not persisted; do not integrate combat yet.

## 2026-10-11 — Local native settings authorized; first gate prepared

- The user authorized reusing the client's local settings, fully offline.
  This updates the earlier limit of only observing ServerSettings; it does NOT authorize
  RPC, network, an external server, inventory, protection bypass or own formulas.
- A sub-agent traced ServerSettings as a passive SaveGame: the native constructor
  fills SpawnInvulnerabilityTime 3 and GlobalRefineYieldModifier 1; WarTweakables
  initializes MinTankArmourMultiplier 1, BallisticPenetrationMaxDistance 4000 and
  BallisticPenetrationDistanceExponent 1.5. No network in the constructor body.
  Static evidence, still without confirmation on a live instance.
- tools/probe_native_settings.lua prepared: own instance through the constructor,
  compares defaults and does not bind to the GameInstance, change a CDO or apply damage.
  Lua syntax PASS; check_mvp_trace PASS only for the historical evidence.
- Offline continuation: tools/test_native_settings_probe.py runs the real probe
  with mocks, covering an original null/valid context and refusals of ancestor,
  invalid constructor and divergent default. PASS; the test does NOT prove UE4SS binding
  nor live damage. The probe now also checks the identity of the kept context.
  test_orders.py PASS. Own report data/trace_context_local_settings.md
  records constructor/passivity/defaults/profiles; nested struct still without a live gate.
- restart.sh ran the syntax/locals check and refused to start: Steam is not open.
  Did not open Steam nor log in. No lab started in this attempt.
  Next: the user opens/logs into Steam; run the first gate and only then plan a
  temporary binding/damage oracle restoring the original context.
- main.lua without a new change; no native combat integrated or damage proven.
  Rifle still under investigation: the local entry found also calls a possible
  RPC wrapper, so do NOT run that entry as an offline shortcut.
  A later consumer with damage was traced, but without a demonstrated link to
  HitScan; do not attribute it to the rifle. Headless job 24045 finished exit 0, external artifacts.

## 2026-10-10 — Concrete cause of the damage refusal in the lab

- Two sub-agents advanced statically, with no channel/inventory/RPC. Protection 808 is temporary
  by timer and CDO 48 is bBypassesSpawnInvulnerability, proven; do not change offsets nor flags.
  The generic conversion does NOT zero damage by ID 0: hypothesis discarded. The real interface also requires
  a non-null WarGameInstance.ServerSettings, a guard distinct from Role/SimGameMode.
- READ-ONLY probe tools/preflight_native_damage.lua: PID22084 HomeRegionW,
  BPWarGameInstance alive, ServerSettings null. The static guard returns 0 under that condition;
  it explains the refusal observed in that lab, not a general impossibility of native damage.
  data/trace_context_damage_native.txt. No server/settings object created or changed.
- tools/export_damage_types.lua run in the engine: CDOs Types 1/2/7/3/8/18 for
  light/heavy/explosive/AT/HE/fire; bypassSpawn false in all. AT Armour true/Penetrate false,
  the others Armour false/Penetrate true. Trace data/trace_export_types_damage.txt; syntax PASS.
- Important correction in the firing report: the authoritative branch located is the HMG, NOT the rifle.
  AuthorityRole 3 -> valid hit -> DamageableActor interface with DamageAttributes -> damage;
  the native fallback uses PointDamage/TakeDamage. ABI/equipped instance/rifle still pending.
  Headless Ghidra readOnly/noanalysis finished, decomp stays external. Do not use offsets.
- main.lua source 2F1C74D6 stays unchanged, no native combat integration delivered.
  Labs 13208 (CDO)/22084 (preflight+export) closed only by the verified PIDs;
  absence checked, Steam kept. Read the reports before repeating ApplyDamage.
- Next: clarify the client's legitimate local context needed for damage; do not build a
  server/RPC nor reset HP artificially to make a test pass. A null guard is a diagnosis,
  not authorization for a bypass, and it does not prevent continuing other offline combat studies.

## 2026-10-10 — Back to the native combat flow, with two sub-agents

- The user corrected the course: do not reinvent firing/damage already present. A rough MVP does not authorize
  an own DPS in place of the engine. Priority corrected in ROADMAP; main.lua did NOT change in this batch.
  The user authorized sub-agents; two investigated firing and damage offline, the channel exclusive to the root agent.
- Firing: the real HitScanWeaponComponent, local entry/native consumption/trace/HitNotify/effects
  identified in an existing decomp. PlayerFire is a ParticleSystemComponent, NOT a weapon.
  ServerStartInvoke/OnRep_SimulatedHitNotify are reflected, but the RPC was not invoked and an effect
  callback does not prove damage. ABI/owner/equip context still pending; offsets not run.
  Report data/trace_firing_investigation.md, protected decomp stays external.
- FindAllOf(Class/ScriptStruct) gave 0; an inadequate enumeration, not absence. StaticFindObject
  by proven names found classes and structs WeaponInvoke/HitNotify; schemas in data/.
  FindAllOf HitScanWeaponComponent/ProjectileItemComponent/HMG gave 0 instances in HomeRegionW.
  Do not touch inventory/RPC to fabricate a proof.
- Damage: static flow ApplyDamage -> SimVehicle's real TakeDamage -> embedded interface,
  not a component UObject. Authority/world/SimDamageType guards and extra protection found;
  report data/trace_damage_vehicle_investigation.md. Receive*Damage are callbacks, not application.
- PID19220 HomeRegionW: exclusive truck 900 HP/bCanBeDamaged true. ApplyDamage 45 with the real types
  lightkin/heavykin/explosive returned 0 and kept 900; Radial 75 returned true, HP 900. Each actor removed.
  setTeam was called incorrectly with an actor, the helper expects a member; Team 255 stayed, not a contrast.
- New corrected probe TeamId directly 0, HasAuthority true/Role 3/AuthorityGameMode SimGameMode valid.
  After 12.197 real seconds, ApplyDamage 45/BPExplosive still 0/HP 900. Exclusive actor destroyed; the following
  callback marked why actor destroyed, but the damage line was recorded. It does not prove a native impossibility:
  locating the guard/CDO/context is the next step. No HP written/offset/RPC nor injected input.
- Steam/firewall rules kept; only PID19220 closed after the probes. UM updated,
  kb check 60 PASS. Next: resolve the native contract instead of calibrating interdiction with an invented DPS.

## 2026-10-10 — Ambush excludes the unarmed; cut still not proven

- An audit found proximity damage counting workers with dmg 0, both in the enemy convoy
  branch and in the damage to our truck. Both now require weapon.dmg>0.
  The MVP's abstract DPS was kept; it does not implement individual firing/ammo/LOS against a vehicle.
- tools/test_orders.py gained a worker/armed contrast on both sides: PASS;
  the earlier source fails on the assertion of the worker damaging a convoy. check_globals PASS.
- Published 2F1C74D6BB205FA5610957A9B126720731CFA34DF4775329B2DDA7A82101F956 through restart.
  PID12944 CallumsCape: new deployment from the scenario budget, newGame without an old save.
  The bot tried to chase convoys with combatants, without teleport/credit/artificial damage:
  148.8 s, 2 enemy deliveries; second truck 900->797.60 HP, no cargo lost, audit true.
  Chasing a fast truck did NOT produce a cut; the match ended in defeat right after.
- A later contrast attempt in the engine refused for lack of a live worker;
  it did not run nor replace lists/stocks. So the worker-specific test is offline;
  publish/compile and the march/damage on a real convoy passed, but live isolation did not.
  data/trace_mvp_ambush.txt. Do not declare interdiction approved by this rehearsal.
- The bot finished; only PID12944 closed, absence checked, temporary map removed.
  The next test needs to set up the ambush BEFORE the passage, not chase the truck.

## 2026-10-10 — MVP: logistics cycle in combat in the hex

- Without changing main.lua 597BAF94, published/restarted CallumsCape PID19620. The earlier save was used
  only to recover infrastructure; newGame reset stocks/chains/waves. No credits,
  teleport, time change or input to the window. The base starts with 30 shirts/10 rifles, bmat 40.
- Bot limited to 36 steps/10 real s: recruits using stock, marches combatants to point A;
  does NOT reassign workers nor override orders in progress. No mortar/buff/artificial damage.
  Trace data/trace_mvp_cycle.txt; external scripts t_mvp0/t_mvp_step/t_mvp_final.
- 403.50 s: defeat at wave 4, 26 kills/23 losses; final reading 27 kills (the simulation keeps going briefly
  after the result). Three surviving workers did not prevent defeat, as per the v4.1 contract.
  Collection 120 delivered/loss 0; bmat 40->84.69 before the rebuild; the resource truck came back.
  Base shirt stock 16->20 after consumption/delivery, final factory 3 ammo crates.
  Resupply 8.99, 5 occurrences without ammo. Final resource truck 57.45 HP under combat.
- Enemy 4 deliveries/13 shirts consumed; waves asked for 6/7/8/9, free garrison 5 + paid 1/2/3/4.
  All 36 samples and the final eAudit/colAudit true. No crash in this round. No convoy cut;
  it does NOT prove interdiction, victory, long balance, roads or general stability.
- New tools/check_mvp_trace.py checks the recorded evidence and states the limits; PASS.
  Mechanics source unchanged: this batch proves integration in combat, not a new feature.
- Only PID19620 closed after the bot finished; absence checked, temporary map removed.
  Next rough step: try a supply cut with combat and expansion/forward base;
  refined arrival stays postponed. Complete MVP not yet declared.

## 2026-10-10 — Real capsule, collection in the hex and MVP direction

- The soldier's CollisionCylinder measures radius 50/height 90. PATH_BODY fixed 32->50 and the rescue capsule
  34->50; a free candidate at 34 was occupied at 50. No new blind teleport.
- The bitfield bStartPenetrating came back true on distant hits Time 0.776/Distance 19400.
  rts.hitStartsInside uses scalars with a true/false/nil result; unknown does not authorize a rescue.
  BreakHitResult with a Lua table returned corrupted scalars: do not use it as an oracle.
- Old save: a 1 HP worker in medevac is still stuck on the wall. Sweep Time 0/Distance 0.045
  does not prove a penetrated origin; the origin's capsule is free. The fine profile failed 3 nodes. Case NOT solved.
- Source 597BAF948F82EFA079A3DFA79340D2F878E75AAE84F42F494712AE2A3E73E1CC:
  battery 29/29 PASS/21 mutants. CallumsCape PID19492, new match at the correct base:
  collection 120/delivery 120/loss 0, audit true; the rebuild created a real 900 HP actor not being destroyed.
  data/trace_collection_capsule50_final.txt. This proves credit by radius, NOT arrival at the door:
  the user observed three workers stopping on the track; no order/speed 0 after delivery.
- The truck climbs structures: straight drive and place without sweep; the central trace of the factory/refinery
  hits the roofs Z 1389/1382, not the terrain 600. Candidate box 450/210/230 at the current Z penetrates the floor;
  raising 250 clears the test, but does NOT certify envelope/support. Do not integrate that box as proof.
- The refinery has a UseAreaBox center 8477/-45794/Z 856, extents 750/825/256, yaw -23.49;
  TransferLocation 8684/-47155/Z 630. Floor/capsule probes found exterior points and points in the
  native area, but without proving a route/door. data/trace_area_use_refinery.txt.
- The user postponed refining the workers: they want a rough MVP proving the concept. The task
  of arrival/waiting is recorded in ROADMAP; the next batch must advance a playable chain, not polish
  that point. Trucks without collision remain an explicit limitation, not an approved physical chain.

## 2026-10-10 — VSync and the eye at the focus; stuck soldiers stay pending

- The user described a horizontal line in the middle of the screen when moving the camera; a static capture does not show it.
  Cvar oracle: r.VSync 0/t.MaxFPS 60. Temporary test r.VSync 1: the user confirmed it disappeared.
  rts.syncVideo now turns VSync on in RTS and restores the previous value on exit, without writing config.
  In the engine: 1/old 0 -> gfx(false) 0 -> gfx(true) 1/old 0.
- Live truck 900 HP, meshes bVisible true/bHiddenInGame false, actor bHidden true and outside S.occluders,
  with the eye ~100 m away: native hiding, not absence. The eye at the focus made bHidden false and the truck visible
  in the capture visibility-B-controlled_small.png. Some A/B captures had the camera moved by the user:
  do not treat them as a pixel-by-pixel comparison. No injected input.
- eyeTick now follows the focus/ground, not the nearest soldier. Uses REAL time to follow a paused camera;
  refuses a NaN focus/missing ground. The base stays independent. The engine test confirmed focus/eye during pause.
- Found an old side effect: an empty spawnSquad used the eye's pawn as the origin. Fixed to
  rts.base when S.eye; existing squad reference/explicit spawn/native mode kept.
  Final PID19956: base 16104/-54440, eye 3123/-51134, the new match spawned 372 cm from the base, not at the eye.
- Final source F53D35A1FEDB9BC0931EB73AE0AC11A3ACB1F0461B6FC79E0225E1F954ADE2E8 published.
  Battery 29/29 PASS/21 mutants + tools/test_visibility.py PASS (real functions, VSync/base/pause).
  Trace data/trace_visibility_rts.txt. Visibility across the whole screen, snow/structures/angles NOT approved.
- The user insisted on the stuck soldiers. Current trace data/trace_stuck_current.txt: three workers in the
  stretch 13k/-50k; collection inactive/logistics suspended by our visual probe, one target back to the base and
  one with speed Z -400. Do not attribute that probe's immobility to autonomy nor dismiss the report.
  Intermediate round ECF06A81: 120 delivered/loss 0/actor 900 HP, but the match spawned at the camera's focus;
  do NOT use that round to approve general navigation. Now the priority: reproduce the stuck ones with the correct origin/base,
  audit the common march/medevac of the workers (the fine profile today only in colGo), then roads.
- Final lab PID19956 closed and absence of the copy's processes checked; temporary map
  removed, Steam/firewall kept. Universal-modder updated; kb check 60 notes PASS, no PR.


## 2026-10-10 — Envelope observed and the RTS visibility task

- The user asked to include fixing things going invisible: recorded in ROADMAP.md as a priority functional
  failure together with transport; investigate LOS/occlusion/hiding, including trucks far
  from the group and high zoom. No visibility change yet; do not confuse a loaded actor with the image.
- Roads: the candidate adapter now requires proof per directed edge/from/to/segment/session;
  before, proof of one segment authorized all the spline's edges. test_adapter/roads/snapshot PASS.
  Separate candidate; main.lua not changed in this batch.
- PID15748 CallumsCape: BoxTraceSingle/GetComponentBounds metadata confirmed. Restore for the probe,
  logistics frozen, truck oriented yaw 0 and collision enabled only on it; no real input.
  Component bounds and a scan of 1166 rays/10 per frame: CharacterMesh0 hits exceed the box 400/162/140
  (X up to 427.70, Z down to -206.22). StartPenetrating flags on all hits: do NOT validate the hull through these hits.
  Trace data/trace_envelope_truck.txt; complete bounds external road-bounds.txt.
  Complete envelope/surface/water/sweep stay pending; no edge authorized.


## 2026-10-10 — Transactional rebuild published and validated in the hex

- Resumed from the most recent state: physical mocks already present in the harnesses. Complete battery
  with sensitivity: 29/29 PASS, 21 mutants; source E048680B41891BC16F136E4316C98334797642B1504D38D682C777A58FC00DEC.
- Published through restart.sh. The first load started the lobby because map.txt was at the wrong path; fixed
  in the mod's directory and deliberately restarted. CallumsCape PID11924 reached RTS.
- The spawnTruck probe created a real truck HP 900/not being destroyed at the factory's spot without a debit;
  truckStep reused the same actor, debited 100 and activated idle. A 100 credit only in that isolated probe.
- New match without waves/credit/intervention: collection 120/delivery 120/loss 0; the starting stock of 40 refined
  up to 100, bought the truck and advanced toField/loading/toRef with a 900 HP actor. The probe's physical actor was
  reused in the same load: it does NOT prove a second clean spawn. Trace in data/trace_rebuild_transactional.txt.
  Transport stays straight/without collision: do not approve road, balance or a complete regional chain.
- Only PID11924 closed with a verified path; temporary maps removed, Steam kept.
  Next batch: physical access/route of the trucks along the native network, without confusing abstract state with a path.


## 2026-10-10 — Rebuild without a phantom truck: transactional candidate

- spawnTruck reuses the factory's parking; requires a class/whole actor 900 HP and not being destroyed.
  Returns success/reason. truckStep only debits 100/activates idle after success; a failure keeps it dead,
  the stock, and retries in 5 s. Without a safe spot it also refuses. An existing whole truck can be reused.
- External backup main-before-resource-transaction.lua. test_orders/check_globals PASS; real regressions
  of spawn nil, IsValid but being destroyed, and whole: two failures keep 100/the dead state,
  a single success debits 100/activates a visible actor.
- Complete battery 27/29 PASS: test_coleta_sobre_v4 and test_bmat_caminhao failed on the expectation of a
  rebuild. Not published. Audit old mocks (abstract transport vs whole actor) and fix
  the coverage without loosening the new contract; do not present those two FAILs as PASS.
- Next: update the harnesses' physical oracle and validate the spot/spawn at the factory live in a single load.
  The lab stayed closed in this offline batch; Steam/firewall unchanged.

## 2026-10-10 — Collection went around the rocks: 120 delivered; phantom truck identified

- Source F39518364CDFEDD88C7008561F1AD2576B0C9B0BDE003A77670AF573CE472F35, battery 29/29 PASS.
  PID12460, restore/new match/no waves/intervention. Three collectors delivered 120, loss 0,
  real routes went through X 11666/Y -53k to -50k, not through the gap in the rock. No micro-rescues.
  data/trace_collection_50cm.txt and data/trace_routes_50cm.txt. Walking to the refinery approved in this scenario.
- Do NOT approve the complete chain: resourceTruck changed to loading/toField/toRef but pawn false.
  The factory debited 100 before a silent spawnTruck; the collectors left because the abstract state looked alive.
  The data confirm a risk already noted: the economy of the next transport is abstract, it does not prove a real truck.
- Explicit spawnTruck diagnosis: pcall true/nil and no pawn. Probe at the fixed spot field+400/+300:
  valid class/ground 1000, SpawnActor valid but bActorIsBeingDestroyed=true/Health 300.
  No whole vehicle created. data/trace_spawn_resource.txt; do not credit this diagnosis as a rebuild.
- Next: reuse the deployment's parking/preflight, check a whole actor before the debit/live state,
  a failure keeps it dead/the stock and alerts, test a failed spawn and a physical success. Then trucks along the real road.
- Lab closed PID12460 verified; temporary map removed; Steam/firewall kept.

## 2026-10-10 — A free capsule did not rescue; fine sampling candidate

- Rescue revised: rings 80/160 cm, height difference 90 cm, rejects floor.bStartPenetrating;
  an exceptional teleport only after a penetrated sweep and a free CapsuleTraceSingle 34/90 at the destination.
  Fixed the per-frame loc cache after the setter: the success test revealed an old position hiding the rescue.
- Source A9A4A2EB3E82...: 29/29 PASS including 21 mutants. Tests cover an occupied destination refused,
  a free one with a penetrated origin accepted/replanned, carry/legT kept.
- PID9648 loaded a pre-cache variant, WITHOUT a match/test; a deliberate restart because of the source change,
  not because of a timeout. PID2368 published the final, restore/new match/no waves. The rehearsal again delivers 40,
  factory 60, resourceTruck dead, ZERO rescues, two stuck with 6 attempts. It did not solve the case.
  data/trace_rescue_capsule_final.txt; the user confirmed the insistence on the rocks and two stuck.
- The next change still offline: collection's kneeClear samples the ground every 50 cm, limits the climb proportionally
  to the distance and deviations from the interpolation line to 45 cm. Before, it sampled 300 cm and tolerated 290 cm per sample,
  including on the simplified shortcuts. The combat/truck profile without sampling stays the same.
- test_orders/check_globals PASS: a narrow rock between the old samples is refused; a gentle ramp accepted.
  Needs the complete battery and physical validation; do NOT declare a route around the wall approved.
- Lab closed PID2368 verified; temporary map removed. Next: validate the fine route and accesses
  on the ground, without replacing a finished chain with a mere safer refusal.

## 2026-10-10 — Live micro-rescue: sweep refused for penetration

- Candidate AF6720F17189... published, PID13132, restore and a new match without waves/intervention.
  360 samples: delivery 40, loss 80, factory 60, resourceTruck dead/pawn false. Zero rescues;
  two stuck exhausted six attempts. The third's oscillating movement does not trigger the immobile detector.
  The audit closes but the chain stays NOT approved. data/trace_micro_rescue.txt.
- Real oracle: neighboring floor normal .863 with a climb of 68.89 cm; the limit of 45 refuses. Many traces return
  a point equal to the start (delta 135 cm/normal 1): they start penetrating rock, NOT a safe floor.
- Sweep probe to the destination with a 68.89 climb: return false, bBlockingHit=true, bStartPenetrating=true,
  position unchanged. So raising only the height is NOT enough: the capsule is already penetrating geometry.
- The reflected CapsuleTraceSingle works: radius 32/halfHeight 90 at the destination detected penetration.
  A scan of 8 directions at 80 cm rejected initially penetrated floors; no safe candidate shown.
  File data/trace_rescue_capsule.txt. No unsafe teleport applied.
- Next: a short rescue with a free destination capsule and a real floor, rejecting bStartPenetrating;
  the user accepts an exceptional teleport, but do not treat an occupied exit as free nor credit cargo.
  Lab closed at the exact PID 13132 after the probes; temporary map removed, Steam/firewall kept.

## 2026-10-10 — Micro-rescue authorized, offline candidate

- The user authorized short transport exclusively when stuck, due to uneven terrain.
  Implemented logi.colRecover for workers: four seconds with displacement <=30 cm,
  no combat/active planner; eight directions of 80 cm, local ground with normalZ>=.71 and a height difference <=45 cm.
  K2_SetActorLocation uses sweep=true: does not turn off collision nor go through walls deliberately.
  Six attempts per episode, no salvage credit and no renewal of legT; success replans.
- tools/test_orders PASS: immobility/waiting, mandatory sweep/limited distance, blocked collision
  does not become success, attempt cap, cargo/deadline kept and an active planner cancels the observation.
  Candidate NOT yet published/validated live. Do not claim this rescue gets out of the hole.
- Earlier trace captured in data/trace_routes_rock.txt: approved trajectories with waypoints
  over rocks Z 1350–1377; workers ended up Z 790–894 in the gap. One delivery of 40, incomplete chain.
  The instrumentation does not change orders. Lab PID4328 closed after the capture; Steam kept.
- Next: the complete battery and a single live batch, measure the sweep/real progress and recovery without credit.

## 2026-10-10 — Regional arrival of collection: offline PASS, path still failing

- Collection looks for an accessible cell inside the service area, instead of a fixed point next to the installation.
  Reuses planStart/planStep/routeTo; arrival updates target and u.goal. A profile exclusive to workers:
  cell 300, margin 3000, ceiling 5000, step 290, height 1200; does not change combat orders.
- Source E5BADAF86D90F3E8343E2DCC937DADC047736878E87A623BD0E3E78A01E66CE5.
  Final battery 29/29 PASS including 21 mutants; worker-region-final-battery.txt. The new test covers
  a blocked central destination and arrival at a free cell of the region. It does not prove native physics.
- PID24092, clean load CallumsCape: restore wallet 1000/0/1000/4 and a match without waves/credits.
  1 Hz sampling: 120 collected, 40 delivered, 80 lost, factory 60, resource truck still dead.
  Two returns and a new trip stayed stuck. Chain NOT approved.
- The user reported an accidental intervention and that a click order went around the wall on the way back.
  Contaminated rehearsal: do not attribute the delivery of 40 to autonomy without confirming the moment of the intervention.
  Evidence in data/trace_collection_regional.txt. Next: compare destination/parameters/replanning
  of the click order with colGo (both use routeTo), before another solver or blind increases.
- Also audit the truck rebuild: spawnTruck may leave an abstract state alive after a spawn
  failure; require a valid real pawn before declaring a complete chain.
- Lab closed by the verified PID after collecting the samples; temporary map.txt removed.
- The user asked for collection again: lab reopened PID4328, infrastructure restored and a new match
  without waves. Kept open for that active validation. They reported two stuck in the hole between wall and rock.
  universal-modder: Gotcha updated, kb check PASS 60 notes.

## 2026-10-10 — Collection without blind fallback; real navigation trace

- The user visually confirmed a wall, said it ends on the left, and unblocked units manually.
  The intervention does not count as automatic success: a later reading still showed 120 collected/0 delivered/120 lost.
- Source 541B18D3...3649 added planStart/planStep to env for incremental oracles, with no new locals.
  Trace of the real colGo: three returns failed (1045/2500/1869 nodes), all received a straight fallback route.
  It was not just a lack of nodes: tests with a larger height band/coarser grid/larger margin also refused.
- Reflected CharacterMovement properties: WalkableFloorAngle 44.765083, WalkableFloorZ .71,
  MaxStepHeight 45. The default grid 60/150 is about 22°; do not confuse that rule with the native limit.
  A 44° probe enlarged the reachable region, but still exhausted 8000 nodes without a route. NOT integrated as a solution.
- The wall hit is a modular segment; colliding bounds 205.84/456/326.99 (origin 13150,-50376,705.75).
  Neighboring floor traces also hit a coal pile, another wall and rocks; the global top is not always accessible floor.
  The road network nearest the field is 117 m away; it does not authorize a link by proximity.
- Functional change: routeTo accepts noFallback; collection passes true. A failure clears target/path and marks pathBlocked.
  Replanning the same stretch does not renew legT; the panel shows how many workers have no route.
  Combat/legacy orders were not changed in this batch. Stopping on failure does NOT solve the requested detour.
- Source F0904D1512FCA01E6F5AE34745E5704514AD1AC9F5DAD3A1A97BF9019712BC13 published.
  tools/test_orders.py covers real code: refusal without a straight line, legacy preserved, retry keeps the deadline and a stretch change renews it.
- Final battery on this hash: 29/29 PASS, including 21 mutants; output collection-refusal-final-battery.txt.
- PID14544: after the load was ready, infrastructure restored and a new match; controlled failure with a 1-node ceiling,
  no cargo/stock credited: done/failed/noFallback true, route 0, target false, blocked true, speed 0,
  HUD '1 sem rota', collection audit true. It is a refusal test, NOT a completed natural trip.
- A probe sent before the load finished refused the match and installed a callback without logi.col;
  cancelled and fixed with an assert before installing. Repeating only after RTS was ready passed; do not restart on timeout.
- Numeric trace in data/trace_path_collection.txt; full scripts/logs in D:/tools/foxhole-lab/.
  Lab closed by the exact PID, temporary map.txt removed, Steam/firewall kept.
- Next: find and validate a passage around the end of the wall, with an accessible arrival point at the refinery,
  then prove collection→delivery→truck without intervention. Do not swap the goal for 'now they stand still'.

## 2026-10-10 — v4.1 batch in the hex: infrastructure/save PASS; collection blocked by a real wall

- Source 236C34B9...F393, CallumsCapeHex, PID 25264: deployment of 1000 bmat created refinery/factory/2 trucks,
  wallet 0, spent 1000, four records. Repeating did not change counts nor charge again.
- Match without waves, without credits/teleport of the workers, 1 Hz sampler for 360 s: three collectors gathered
  120 salvage. The return to the refinery got stuck on IndustrialWall03Snow31; a Camera SphereTrace confirmed
  the same actor on all three paths. After the timeout, 120 went to lost and zero was delivered; the ratio closed.
  The factory stayed with 40 bmat and the resource truck did not spawn. COLLECTION NOT APPROVED in the hex.
- Next functional priority: the workers' route around that wall, then trucks along the road.
  routeTo uses a shared A* (2500 nodes/margin 2000) and a direct fallback; record the planner failure before
  changing limits or trying the real network. Do not disable collision, credit delivery or increase time to mask it.
- Isolated save D:/tools/foxhole-lab/v41-hex-validation-save.txt preserved infrastructure/wallet.
  PID 25988, clean load: no assets → continue true (318 ms), refinery/factory/2 trucks restored,
  wallet 1000/0/1000/4, factory bmat 40, no degraded, enemy audit closed.
  Repeat 303 ms, without duplicating/extra debit. Cargo in workers' hands does not persist by design.
- Sliced export of this region's roads finished: 405 CPs, 431 segments, 391 road assets,
  4013 nodes with curves, no incidence rejected; all edges remain NOT physically validated.
  Snapshot and report in data/parallel/roads/callums-*.json; do not reuse epoch/coords in the lobby.
- build_snapshot.py now accepts --input/--output/--report without overwriting the lobby snapshot.
  test_snapshot.py covers both regions; snapshot/roads/adapter tests PASS. It is not integrated transport.
- Trace of the actions/360 samples: data/trace_logistics_v41_hex.txt. Full logs and raw export external
  in D:/tools/foxhole-lab/v41-hex-*.log and callums-roads-export-live.txt.
- Lab closed by the exact PID; temporary map.txt removed, Steam/firewall kept.

## 2026-10-10 — Bases and save v2 validated in the game; continuation in the same load fixed

- Batch through the channel, no injected keyboard/mouse, HomeRegionW: PID 21456 created a native base with HP 1725.
  Ownership and 400 bmat credited explicitly to isolate construction; not a balance or physical delivery test.
- Isolated save in D:/tools/foxhole-lab/v41-validation-save.txt: write 45 ms; PID 11400 restored after restart
  in 226 ms, with an active base, own/enemy audits closed and no degraded state.
- Repeating the continuation with a live base refused: the vertical trace hit the roof and required Landscape.
  parkingGround now accepts an optional ignore; fwdPreflight ignores only the live base matching the saved spot.
  It does not ignore other buildings, dead caches or actors being destroyed. Backup: D:/tools/foxhole-lab/main-before-preflight-ignore.lua.
- Source 236C34B9F4223911B6087A36BCB514BCA29CB813ECD3F2FA2AADD43B0B5CF393:
  29/29 offline battery PASS, 21 mutants; tools/test_fwd_preflight_ground.py additional PASS on real functions.
- PID 27284: fresh continuation 223 ms, preflight with a live base PASS, repeated continuation 220 ms.
  An empty base refused recruiting without fallback; credited crates gave 10 shirts/20 rifles; the recruit spawned 8 m away,
  consumed 1 of each. Save and continuation preserved 9/19, audit closed; 259 ms, no degraded.
- Two probes had Lua errors fixed (name fwd.bases instead of fwd.list; flatDist not exported in env).
  They were not feature errors; the interrupted actions were repeated, without declaring PASS from incomplete output.
- Native TruckW collision read before the driver: VehicleCollision extents 400/162/140, Camera/Visibility 2/2,
  but meshes also block; the box still does not prove the full envelope. See data/parallel/roads/TRUCK_VALUES_20261010.md.
- External evidence v41-*-load*, v41-recruit-base.txt, v41-fixed-base-save-live.log in D:/tools/foxhole-lab/.
  Lab closed by the exact PID. Still to validate: deployment/wallet in the hex, transport and prolonged combat.
  Crashes/yellow effect remain postponed as the user asked; do not claim general stability.

## 2026-10-10 — Development resumed: logistics integration v4.1

- At the user's explicit request, crashes and residual yellow stay pending; do not block features on the manual 1/2 gate.
- Integrated manual collection, four supplies, the enemy chain, forward bases and save v2. Experimental key queue preserved.
- Source SHA256: 2237884769733d6298db957f028f5f71fbf948634e4740aa81ddd68e7f08f83f.
  Previous backup: D:/tools/foxhole-lab/main-before-logistics-53bdbcab.lua.
- Battery: 29/29 PASS offline, including sensitivity with 21 mutants. The first rehearsal failed because a harness expected a synchronous key; adapted to drain the queue like the real frame, without changing the feature.
- Full result: D:/tools/foxhole-lab/integrated-v41-battery.txt. Offline does not prove physics, balance, real keyboard or native stability.
- Publishing and a short validation in the lab started; live results will be recorded separately. Previous save copied to D:/tools/foxhole-lab/save-before-v41.
- Short validation finished in HomeRegionW, PID 3660: newGame started, three workers spawned,
  shirts 30→27, collection active, truck reserve 100, enemy chain with a closed ratio and the first wave.
  State in D:/tools/foxhole-lab/v41-live-state.txt. It did not validate a complete trip, forward base or save return.
  Lab closed by the exact PID; Steam kept. universal-modder updated, kb check: 60 notes PASS.

## 2026-10-10 — Flicker: residual stencil hypothesis tested offline

- Source 53BDBCAB…E543/lab closed confirmed; the queue is still waiting for a real test.
  No further change to the source nor an idle launch.
- outlineDepth(false) clears CustomDepth but keeps stencil 1. If native code re-enables Depth,
  the mask remains: a hypothesis for the flickering fill reported by the user.
- test_stencil_clear.py extracts the real helper and reproduces the residue; an in-memory swap to
  stencil 0 on deselect PASS, including reselect 1/idempotence/guard. Not applied.
  STENCIL_PROPOSAL.md documents the candidate and the visual/frame-order gate.
- It does not prove the shader/flicker nor solve the crash; do not mix it into the queue rehearsal.
  Universal-modder consulted/Gotcha 52/local check, no PR.

## 2026-10-10 — Isolated variant: queued keys in the persistent loop

- After a new Registry reproduction with fast input, applied ONLY a bridge experiment:
  CFG.KEYBIND_QUEUE=true; onGame queues a Lua function, frameBody drains before authority/menu.
  FIFO by snapshot, reentrant events go to the next frame, an error does not block the following ones.
  false preserves the original bridge. Outline/fill/focus/movement not changed.
- External backup main-before-keyqueue-33d6c7e5.lua. New source SHA 53BDBCAB…E543;
  the logistics candidate 62245d23 does not contain this change: do NOT copy it over without transplanting
  and retesting the bridge after the gate. Real source test_queue_experiment/orders/globals/lifetime PASS.
  The orders harness simulates a frame boundary after a keybind; a specific test verifies the deferral.
- Published through restart.sh/PID5440/HomeRegionW. 100 selectGroup 1/2 actions in 10 queued bursts
  through the channel executed in the persistent frame; assert 3 selected/FIFO/empty queue PASS.
  This does NOT simulate the keyboard nor prove UE4SS thread sync/a solved cause.
  Output KEYQUEUE_20261010.txt; external log keyqueue-live-20261010.log, no Registry/fatal observed.
- Lab 5440 closed at the end, Steam preserved. README/MANUAL_TEST updated.
  Next for the user: one key 1, then 2, stopped alternation; movement/double tap separately.
  Do not certify a fix before that test. Flicker not handled in this variant.

## 2026-10-10 — 100-group control passed; fast input crashed with Registry

- PID23716, current source: 100 alternating selectGroup calls through the channel completed, 3 selected
  per step. External output group-channel-20261010.txt. After the control, the user reported fast switching
  1/2 and a fatal; terminal process confirmed, crash 401E1646…/338s/read 0xffffffff.
- UE4SS.log contains "Registry Ref was not function" at 11:57:46,315/No traceback and group logs
  until 11:57:49,561. External log group-fast-fatal-20261010.log preserved. It does not prove the guilty callback,
  but fast input is a candidate reproduction; the channel rate and the key rate are not equivalent.
- The user also reported a flickering yellow fill on an unselected unit; the image provided
  shows yellow parts of a unit without an outline behind a vehicle. An isolated image does not prove flicker;
  the user's temporal report recorded. The already-known native reactivation of CustomDepth deserves a trace.
- User hypotheses: movement during switching; repeating 2 when 2 is already selected. Repeating a group
  within <=0.45 s also calls focusOn (double tap), a distinct path to isolate. Do not assign blame.
- Next separate rehearsals: queue in the persistent loop vs ExecuteInGameThread; double tap vs
  alternation; visual mask/stencil without mixing fixes. No new manual test now.

## 2026-10-10 — Second manual reproduction: 1/2 alternation crashed

- Clean load PID10128/HomeRegionW, same source. The user confirmed 1 selected 3 and 2 as well;
  when alternating 1/2 a fatal error occurred. Last logs group 2 at 11:50:13,057 and group 1 at 11:50:14,029.
  Before that there were real move orders and the wheel; do not call it an exclusively key rehearsal.
- Terminal process confirmed; crash E729F1E8…/147s/read 0x0b. Log preserved externally
  manual-alternating-fatal-20261010.log; original dump in Saved/Crashes. No automatic restart.
- Group alternation is now a reproduction candidate; 1 or 2 alone worked in this load,
  but do not certify stability. Next compare selectGroup through the channel vs real input,
  separating movement/camera/outline and the ExecuteInGameThread bridge; do not assign a cause yet.
- The user does not need to continue the script. Lab terminal, Steam preserved;
  no input injected by the agent nor release of the logistics candidate.

## 2026-10-10 — Manual gate FAILED: crash after selecting group 1

- The user reported a fatal error while testing numbers and difficulty understanding the script.
  Do not require continuing; the next script will be a single step, spelling out 1=group 1/2=group 2/0=all.
- PID20308 terminal confirmed, no restart. Crash 95C51A… at 11:42:40, 317 s since the process start,
  EXCEPTION_ACCESS_VIOLATION/read 0x75d42b59. Source 33D6C7E5…E679 intact.
  Last log 11:42:39,524: selected group 1 (3); before that there was the wheel, selection and A* orders.
  No Registry message in the new stretch. Temporal proximity does not prove the guilty key.
- Stack starts c62ea9/2c60bc/2c6d99/2c3a0d, then the Lua bridge/repeated frame. The same PCallStackHash
  as the old ones does NOT prove the same instruction. ModuleList identity confirmed GUID/Age 20/timestamp
  equal to the local PE also in the new dump. 2c6d99 is in push_structproperty, an internal branch without
  an exact name; do not confuse it with the write return 2c6b92 seen in another stack.
- JSONs crash_manual_20261010.json/crash_manual_identities_20261010.json in stability;
  external UE4SS.log preserved manual-fatal-20261010.log; original dump preserved in Saved/Crashes.
  Earlier automatic gates did not cover this interaction and do not certify the build.
- Lab already terminal, Steam preserved. Logistics candidate not released.
  Next: locate instruction c62ea9/context and isolate the group/callback path in a single
  variant; only a new simple manual test after investigation. No injected input.

## 2026-10-10 — Manual gate prepared on the user's confirmation

- The user confirmed "Sim, pode preparar agora". Clean load through restart.sh, PID20308,
  HomeRegionW, current source preserved. The channel confirmed 6 soldiers selected/28 copies each,
  waves off/enemies cleared; no injected input. Initial external log manual-start-20261010.log.
- Lab kept open exclusively for the requested active manual validation.
  Result still pending: the user does selection/groups/movement/zoom/F10 for 10 min;
  when finished, preserve the log and close only the Lab PID. Do not count the preparation as an approved test.

## 2026-10-10 — Exact UE4SS source: Registry bridge and struct write branch

- Lab closed/Steam 22164 confirmed; the last session made progress (new identities/frames).
  No answer yet to the manual start confirmation; do not open the game idle.
- The public GitHub API resolved commit 5418fa4ed9f1e8379d28ee7bbc3235c7e0c71b09. Three small
  public source files in D:/tools/ue4ss-source-5418fa4e; no loader/binary replaced.
- get_function_ref checks the type in the registry; process_lua_function is a general trampoline, it does not prove
  a keybind. handle_error notifies callbacks and clears the stack before choosing a C++ exception/luaL_error:
  record a full traceback/context if the error returns, without attributing corruption from a static reading.
- In the compatible PE, 2c6b92 is the return of the table branch before discard_value; it matches the
  Lua table->struct write. This narrows one stack but does not identify the UProperty/UFunction/cause.
  Details/primary links added in data/parallel/stability/SYMBOLS_20261010.md.
- No speculative patch nor feature expansion; the next useful action is a real-interaction gate
  by the user and/or exact symbols/instruction with context. Universal-modder/local check, no PR.

## 2026-10-10 — Offline RE: dump identity and first named frames

- Lab still closed, Steam 22164 present; waiting for confirmation of the manual start,
  not opening it idle. Earlier progress confirmed by files/processes.
- Local UE4SS ZIP without a PDB. DLL 3.0.1 Beta #0/commit 5418fa4e; extracted CodeView RSDS with llvm-readobj.
  The ModuleList of the three old dumps has the same GUID 21ad178d-4639-470e-971e-f115b4924854/Age 20/
  timestamp 6ac43103 as the local PE: the RVA comparison now has a verified identity.
- Crossed 4353 exports with RuntimeFunction ranges: 0x2c6b92/2c6d99 inside
  push_structproperty; 0xb99c75 in Lua::call_function; 0xb9d34c in process_lua_function.
  Names accepted only when an export starts exactly at the start of the corresponding range.
  The nearest previous export does NOT identify private functions (heuristic discarded).
- Evidence/limits in data/parallel/stability/SYMBOLS_20261010.md and JSONs beside it.
  Frame names do not prove the cause/property/guilty callback; Registry still not isolated.
  External scripts/dumps/binaries; no new loader/large download/main source changed.
  Next RE: source of the exact commit or a compatible PDB GUID/Age; do not symbolize with another build.
- Universal-modder consulted; local Gotcha 50/check, no PR. Manual gate/feature still pending.

## 2026-10-10 — Outline: 100 cycles and 20 deaths/recreations passed

- Clean load PID18872/HomeRegionW, same source 33D6C7E5…E679, six selected,
  waves off. 240 steps through the channel, no new callbacks/hotpatch/input: 100 cycles of
  de/reselecting followed by 20 deaths by Health 0/normal removal/recreation, 329.256 s.
- Verified at each step: 0 clones/sources and CustomDepth false on deselect; 28 copies per living unit
  on reselect; outline cache/animAddr/anim.units entry removed before replacing a dead one.
  No Registry/fatal in the log checked. Output in data/parallel/stability/CYCLES_20261010.txt.
- The PROBE's first assert was wrong to require outlineParts nil on a living deselected unit:
  setOutline calls outlineDepth false and repopulates that cache to prevent native glow.
  Only the probe fixed, keeping source/hash and process; cycle 1 redone. Not a mod bug nor
  a leak. For a removed dead unit the nil-cache requirement stays and passed in the 20 deaths.
- Before GC: 207 SkeletalMeshActors alive/28 being destroyed; after: 207 alive/0 being destroyed,
  168 tracked. Do not attribute the remaining 39 to a leak (they include native ones). Pool 6 created/
  20 reused/0 free. An aggregate profile with half the time deselected is NOT a performance
  gain: 6.72 ms mod/5.86 stratTick; selected after GC 10.80 ms stratTick.
- Lab 18872 closed at the end; Steam preserved; full logs external cycles-20261010.log.
  Universal-modder local Gotcha 49/check; no PR. Old cause/real input remain pending.
  The user answered they can do a manual script after the rehearsal; agree on the start before opening.

## 2026-10-10 — Outline: a clean ten-minute window and repeated transitions

- Earlier progress confirmed by files/processes: source 33D6C7E5…E679, Steam 22164,
  lab closed. New load through restart.sh, PID20196/HomeRegionW; no waves/logistics,
  injected input, hotpatch or extra callback. Universal-modder consulted before/after.
- Six selected/168 copies kept across five checkpoints: 134.483/255.032/377.482/498.375/
  620.113 s. stratTick 10.94/11.29/11.76/10.53/12.46 ms. Full 10 min window without a crash or
  Registry/fatal in the log checked. Source not changed; cost remains an independent gate.
- After: native CollectGarbage, de/reselection, death of one soldier, removal/clean cache,
  recreation PASS. New window 186.372 s, 6 sel/168 copies; stratTick 10.39/10.40/10.88 ms.
- Outputs preserved in data/parallel/stability/LONG_20261010.txt and LONG_TRANSITIONS_20261010.txt;
  full logs in D:/tools/foxhole-lab/crash-long-*.log. No old cause isolated.
- MANUAL_TEST updated with a 10 min gate of selection/groups/zoom/keys exclusively by the user;
  question sent, without presuming approval/execution. Next controls: a repeat of 100 transitions,
  20 deaths/recreations and equipment swap, with frames between steps; real input still pending.
- Lab 20196 closed by verified PID/path at the end, Steam preserved. Source/hash intact;
  candidate v4.1 not published. No stability claim nor feature release.

## 2026-10-10 — Resumed: B2/A2 controls and transitions; candidate v4.1 audited

- Source 33D6C7E5…E679 intact. Steam open; universal-modder/skills/oracles consulted.
  Tests orders/costs/probe/lifetime PASS. Candidate v4.1 tested without integrating: battery 27/27,
  repeated with sensitivity 28/28 (21 mutants), SHA 62245d23…598f preserved.
- Earlier B1 found in external output: 184.305 s/6 sel/168 copies; not a new test.
  B2 clean load PID21752: 195.677 s/6 sel/168 copies, stratTick 10.67–11.63 ms.
  A2 clean load PID11084: 201.218 s/6 not selected/0 copies, stratTick 0.48–0.56 ms.
  No Registry/fatal in the new logs checked; approximate checkpoints, not a paired benchmark.
- After A2, selection/deselection/reselection, native GC, death/removal/clean cache and recreation PASS.
  New window 219.164 s/6 sel/168 copies, stratTick 11.07–11.34 ms, no crash/Registry observed.
  Negative controls do NOT isolate the cause nor fix the old failure; performance stays expensive.
- Evidence: data/parallel/stability/RESUME_20261010.md and outputs beside it;
  battery in data/parallel/package_v4/BATTERY_20261010.txt. Full logs preserved externally.
  No hotpatch/injected input/new callback/RPC; logistics candidate not published.
- Lab closed by verified PID/path at the end, Steam 22164 preserved. README updated;
  local Gotcha 48, um kb check PASS 60 notes, no PR. Next: longer duration/isolation if it reproduces,
  zoom/input by the user; stability still blocks expansion.

## 2026-10-10 — Claude offline batch: v4.1 stack ready to integrate (nothing in the game)

- Claude sub-agents (Opus/Sonnet) delivered offline, in `data/parallel/`, without touching `main.lua` (33d6c7e5…e679) or the lab:
  a real enemy logistics chain with interdiction (logistics AI + calibration v2), a safe save v2 (persistence; an invalid enemy
  section discards only itself), a bmat reserve to rebuild a truck, a villager-style start (no resource truck; 3
  unarmed workers collect salvage; the factory makes the truck), forward bases (Shift+J, ForwardBase1, 300 bmat; recruiting
  spends the point's stock; manpower only in Assault) and v4.1 (workers outside the wave and the squad's center).
- Design decisions (delegated by the user): ROADMAP.md phase 3 "where soldiers come from" and `data/parallel/forward_bases/DECISIONS.md`.
- Candidate: `data/parallel/package_v4/v4_1/candidate/main.lua` (62245d23…598f). Integration, README/MANUAL_TEST drafts,
  a single lab script (~5h40, stability gate first) and gotchas in `data/parallel/package_v4/`. Status per task:
  `PARALLEL_AGENTS`. Everything PASS offline only; no live claims. The stability gate still blocks publication.

## 2026-10-09 — Control A1 without selection: a full 184 s

- PID2184/HomeRegionW, source SHA256 33D6C7E5920A3B5E00B7F3BAFBC7B8A86C984DB810217241A567AFE0901EE679.
  Six soldiers without selection, copies temporarily 0 at spawn and restored to 4 in the same command,
  no persistent clone; animation/other systems kept, waves off, no GC/hotpatch/agent input.
- Checkpoints 61.01/122.06/184.00 s: 6 units/0 sel/0 clones in all. Mod 1.31/1.25/1.24 ms,
  stratTick 0.50/0.48/0.46 ms. Log checked without Registry/fatal/wheel/selection.
  Survival of a short control does not certify; plan of 4 loads A1/B1/B2/A2 in crash_control.md.
- After closing the window, a TruckW collision metadata probe ran separately; external output
  truck-collision-schema-live.txt. Next B1: clean load, same source, 6 selected, 180 s without input.
## 2026-10-09 — Registry audit and an independent animation retry fix

- Compared 3 CrashContexts in the artifact data/parallel/stability/crashes_compared.json:
  different headers despite an equal PCallStackHash. The old XML 97D8 records read 0x08,
  DF9A read 0xffffffff, the new 18BCE read 0x63. Do not conclude the same instruction from the hash.
- Wheel and selection are frame polling, not an onGame wrapper: events do not prove a keybind is to blame.
  No local PDB found; offsets not symbolized. Audit callback_registry.md.
- Separate Lua defect: anim.track set hooked=true even when RegisterHook failed. Fixed to
  true only if the registration succeeds; allows a retry and does not duplicate after success. The proposal test reproduced
  failure/retry/no duplication, orders/globals on the integrated source PASS. Do not attribute the crash to this defect.
- Keybind queue in the persistent callback prepared and tested offline only as a separate experiment;
  NOT integrated/does not prove native sync. The next test must change one factor per load.
  Lab closed, no new live validation. Economy/roads remain separate.
## 2026-10-09 — Native crash in the second batch: stability still failing

- PID4408 ended during a 60 s window with 6 sel/168 copies, after discarding 331 frames, stratTick 11.67 ms.
  There is no valid S1 result: the test detected a terminal process, it did not restart on timeout.
- Crash UE4CC-Windows-18BCE18343C03805B228B794C306C125_0000: EXCEPTION_ACCESS_VIOLATION
  reading 0x63, UE4SS PCallStack with several repeated frames c6cfde/c6c1e0/c77cab etc.
- UE4SS.log: mouse wheel 18:20:01, Lua::Registry::get_function_ref Ref was not function 18:20:03,
  6 selected at 18:20:04/06. These are observations, not causality; no input was injected by the agent.
  Do not blame outline/GC/component transform/input without isolation. The source stays experimental.
- The stability agent audits Registry/callbacks/input/anim and compares old callstacks before a new publication.
  Lab already terminal; Steam 22164 preserved. No feature expansion nor automatic relaunch now.
## 2026-10-09 — Second optimization batch integrated offline

- updateOutline now reads K2_GetComponentToWorld 1x/part, without 3 getters/MakeTransform; quaternion/scale
  copied without a pose cache, keeping the homothety and 4 copies/part. Oracle of 42 sources PASS in the earlier load.
- outlineDepth checks the real bRenderCustomDepth/CustomDepthStencilValue every frame and writes only divergences,
  without a cache that would hide a native reactivation. Fields confirmed in the PrimitiveComponent metadata.
- Orders/syntax/globals/costs/probe PASS; real transform/lifetime PASS before the last depth patch.
  The proposed depth test PASS on reactivation/not selected/eye/retire; the real test being updated by the agent.
  The new batch's time/visual gain not yet validated; experimental source, do not promise stability.
- ECONOMY candidate test_integracao and ROADS adapter reproduced PASS. Cargo on a physical return
  preserved in the truck/restore and credited only on arrival; a safe driver/final integration still pending.
  Claude reservations for logistics AI/PERSISTENCE preserved, without Codex taking over the blocks.
## 2026-10-09 — Controlled windows; next optimization batch prepared

- Two windows without transitions in PID2832/HomeRegionW: 61.86 s/2447 frames stratTick 15.72 ms;
  61.29 s/2071 frames 17.29 ms. Same 6 sel/168 tracked/207 active/39 untracked/0 being destroyed.
  No count increase in these windows; the 39 include native ones, it does not prove a leak. Optimized source still expensive.
- A read-only oracle on 42 sources compared K2_GetComponentToWorld with 3 getters+MakeTransform:
  PASS Translation/Scale3D/Quaternion with aligned sign, last error 3.58e-07. The proposal cuts 57->36 calls,
  not yet integrated/published; do not claim a ms gain before measuring.
- The ECONOMY review asked to preserve the physical return after a lost destination on restore; patch still separate.
- Reserved exclusively for the user's Claude: logistics AI and PERSISTENCE in PARALLEL_AGENTS;
  no Codex takes them. Minimap recorded as future work with the UI, no current priority.
- Lab PID2832 closed when moving to offline work; Steam preserved. No active export callback
  nor bot. Next batch: per-component transform and mask guards, offline tests before a clean load.
## 2026-10-09 — Optimization measured in a clean load and regional snapshot

- PID2832/HomeRegionW with the optimized source: 6 soldiers/168 copies, move order accepted,
  32.96 s/1709 frames: stratTick 7.91 ms, mod 8.94 ms/frame. Previously 6 selected 16.72 ms (another stretch 17.87).
  Observed reduction ~53% vs 16.72; not a controlled render/FPS benchmark, still an important cost.
- CollectGarbage and deselecting/reselecting the six passed, 28 copies each; no hotpatch nor input.
  Source/lab clean measurement, without reducing the look. Prolonged/high zoom/visual input remain gates.
- Real HomeRegionW snapshot: 127 CPs/122 segments/468 nodes; 95 road assets, 27 non-road blocked.
  Incidences unambiguous in this snapshot; two disconnected road components, no invented link.
  All physical edges still validated=false; installations/stops not yet connected.
  Snapshot/test/report in data/parallel/roads/; test reproduced PASS.
- COUNTERPROOF: after GC/reselecting 6, a new window of 1873 frames measured stratTick 16.40 ms/mod 17.46 ms,
  95.42 s since the start. The initial ~53% gain was NOT sustained in this repeat; investigate recreation/accumulation
  and measurement conditions before claiming a time optimization. README fixed; agent notified.

## 2026-10-09 — Outline: single setter integrated; road export in progress

- A native K2_SetActorTransform/MakeTransform oracle compared position/rotation/scale against 3 setters,
  including tilt/non-uniform scale; packed tables passed, error ~7.63e-06 in the original case.
- Integrated setter 1x/copy and conversion 1x/part keeping homothety/28 copies/guards. Offline test 8 copies,
  2 parts/3 cameras preserved geometry; estimate 106->57 UFunctions/soldier/frame. Orders/globals PASS.
  The new source not yet published in this measurement: clean load/ms gain pending. Do not use a hotpatch.
- HomeRegionW network: explicit incidence CP0/CP1 in Segment0 and the first point equivalent to CP0 confirmed.
  Native local->world transform and Points index 1 verified, num 4 and zero differences.
  The EditorLandscapeResources/SplineEditorMesh mesh is not a road; RoadT3Gravel01Snow confirmed in other examples.
- Sliced exporter in a 16 ms callback, one element per step, persistent sink _G.roadsExport: running 589 lines
  at the last query. Do not restart while this work is active; wait for done/failure and save the result.
  Do not infer physical traversability from the asset. Expanded economy remains an offline proposal/test PASS, not integrated.
## 2026-10-09 — Integration of the first parallel deliveries (live validation in progress)

- Independent agents prepared stability, roads and interface; artifacts and status in PARALLEL_AGENTS.
- Integrated only the outlineDepth/updateOutline guards: refuse a pawn/clone/camera being destroyed,
  invalid/missing sources and clear references without touching the CustomDepth of a pawn being destroyed.
  It is not proof of the cause or a fix for the native crashes; the outline stays experimental.
- test_lifetime.py runs real helpers of the integrated source; an in-memory baseline demonstrates regressions.
  Cases of destruction/missing/invalid source/camera and alive PASS. Orders/syntax/globals/costs/probe PASS.
- Roads: offline module/test PASS, native network not yet exported; metadata probe prepared.
  Interface: panel/patch/test PASS, not yet integrated; the selection box depends on projection/DPI.
- Published through restart.sh: PID4436, Steam preserved; this time a normal War window, mod loaded.
  World/RTS load and the stability matrix still in progress, no injected input.
- Live update PID4436/HomeRegionW: selection 28 copies, deselect/reselect after 30.49 s,
  death by Health 0/reap with references cleared and recreation of 28 copies passed. CollectGarbage
  confirmed by metadata with no parameters and called; then a new deselect/reselect passed
  at 89.53 s into the rehearsal. No Registry/outline error in the log checked. A short test, not certification.
  stratTick measured ~2.55 ms/frame for one selected: group performance still pending.
- Road probes exported metadata and three examples in HomeRegionW: Connections StructProperty
  of LandscapeSplineSegmentConnection (ControlPoint/TangentLen/SocketName), SplineInfo InterpCurveVector
  with Points ArrayProperty. Cardinality/endpoints/curves and road classification not exported.
  External outputs roads-schema-live.txt and roads-types-live.txt; do not extrapolate the finding to a hex.
- Live group: six selected/168 copies for 32.30 s and 1400 frames, no immediate error;
  stratTick 16.72 ms and mod 17.70 ms/frame. Bottleneck confirmed; the look will not be cut to hide the cost.
  The stability agent prepares an optimization. INNER of Points/ConnectedSegments exported with GetInner;
  ControlPoint->Segment/End incidence may avoid reading Connections without cardinality, not yet validated.

## 2026-10-09 — Lab resumed and a Claude delegation attempt

- Steam came back (PID22164); restart.sh passed the locks and launched only the copy PID20144.
- The load has not reached RTS yet: observed title `Selecionar D:\FoxholeLab\Foxhole\War\Binaries\Win64\War-Win64-Shipping.exe`, CPU 2.56 with no progress over successive observations, log stopped after PS Scan finished 17:43:25.
  The evidence points to console text selection/QuickEdit, not proof of a crash nor an outline failure.
  Asked the user to leave the selection manually; no injected input, no restart on timeout.
- The user authorized the Claude CLI for parallel work. A Sonnet attempt limited to Read/Grep/Glob,
  offline navigation analysis (no writes/lab), ended exit 1: OAuth expired and no refresh.
  Result/error in D:/tools/foxhole-lab/claude-roads-{report,stderr}.txt. No active Claude task.
- No change to main.lua; the outline stays experimental. Next: free the console and run a
  controlled creation/deselect/reselect/death test; the user renews the Claude login themselves.
## 2026-10-09 — Resumed: stability first; lab blocked because Steam was closed

- Request confirmed: continue toward a professional mod, following the roadmap; not just the look.
- Reread How to resume, the selection trace and the outline flow; consulted universal-modder,
  reverse-engineering/oracles and the Unreal playbook. No native cause isolated yet.
- Offline tests run: test_orders.py, test_costs.py and test_inventory_probe.py PASS.
  This does not certify GC/MasterPose/callback stability in the engine.
- An attempt through restart.sh refused by the legitimate lock: Steam closed. No Steam/War process
  found. Do not open/log in for the user nor bypass the ownership check.
- In this environment `bash` resolves to WSL without /bin/bash; use C:/Program Files/Git/bin/bash.exe.
  restart.sh kept waiting for the log even when lab.ps1 refused the start (the grep pipeline masks
  the failure). Wait interrupted; no live validation and no change to main.lua.
- Fixed the external restart.sh: captures lab.ps1's result before filtering the PID and exits
  immediately on failure. bash -n PASS; a real refusal because Steam was closed returned exit 1 in 1.2 s,
  without waiting the 240 s nor starting the game. It does not change the ownership lock.
- Next step: the user opens Steam and logs in; then reproduce/isolate the per-component outline,
  GC, deselect/reselect and death. Do not widen features before the pending stability.
## 2026-10-09 — Batch 17: deployment in the hex; full outline approved visually, stability pending

- **Delivered:** Alt+L deploys a missing chain at native spots, with its own budget of 1100 bmat,
  separate from the production stock. Reuses existing installations, replaces matching ruins with the same
  transform (400+400), creates three TruckW (100 each) on Landscape terrain with relief/clearance/separation checked.
  Checks HP/maxHP/base class/position/rotation. A failure destroys partial spawns, restores hiding/collision of the
  ruins and neither debits nor clears the match. Repeating does not duplicate. Logistics start preserves the real parking.
- **Validation:** offline PASS (includes terrain vs roof, budget, authority, rollback, idempotence).
  CallumsCape: preflight 2 installations/3 slots/1100; a forced HP failure rolled back and preserved two soldiers,
  balance 1100. The final publication created refinery 2700/factory 2000/3 trucks 900, Team 1, no destruction flag,
  positions/rotations checked and a repeat without duplicating. A new match started with six soldiers.
  In 65.21 s: three crates produced, the base received two ammo and ten shirts; three trucks HP 900.
  Starting stock zeroed to create demand, waves off: NOT a balance/combat/road test.
- **Validated deployment source:** SHA256 `ECDCB921424AA6374A7AA609E50B580A12A34573790A5229846ABAAFD3EA61F6`.
  Infrastructure/budget only in this world load, not persisted in the save. Facilities not implemented.
  Trucks still go straight/without collision: access by road/water/bridge still pending.
- **User feedback:** the green disc is the truck's marker; the mesh disappears far from the group in the snow.
  `rts.eyeTick` only picks soldiers/base, never trucks; that explains the hypothesis of LOS stuck to the group,
  it does not prove absence from an image. The user restated a preference for a bright SILHOUETTE, not dots.
- **Selection implemented:** yellow outline and occluded fill ONLY on the selected ally,
  no discs/dots. The native `M_OccludedOutline` fills occluded parts, it does not outline visible parts.
  MID anchored immediately in a PostProcessVolume. Mask/stencil reapplied on the ten separate parts;
  also clears the invisible commander's equipment, which left a ghost on the unselected soldier.
  Skinned copies follow each part via MasterPose/attach and an end-of-frame update, without AI/collision/shadow.
  The user pointed out misalignment off center: fixed with a homothety centered on the camera's REAL position,
  not an offset along a fixed forward. Following/projection sampler: 52 samples/6 s, movement 724.41 cm,
  max error 0.000985 cm. After the "only the coat" feedback, added head, hands, legs, backpack, helmet
  and weapon: four copies per visible part, 28 actors per current soldier. The user confirmed "agora ficou bao".
- **Stability NOT approved:** the MID probe without anchoring crashed 12:45:33/PID15468 (GC hypothesis, not proof).
  Extending to the full soldier crashed 13:22:45/PID7088 during a probe, then again 13:26:51/PID9600
  after rendering 28 copies correctly. Both native UE4SS access/read 0xffffffff, no cause isolated;
  pcall does not protect. The last log also showed `Lua::Registry::get_function_ref: Ref was not function`.
  Do not conclusively blame MasterPose, GC or a hotpatch. Contract and limits in `data/trace_selection.txt`.
  Offline PASS does not replace a prolonged/GC/death/reselect test in the engine. Do not consider the feature stable
  nor continue features before isolating this crash in a next authorized session.
- **Closing:** the user asked to stop after approving the look. Final source published, no temporary logs,
  SHA256 `86DBED189308C449BED9DB3BCB12FD800D2C6F5430E6FCCC297BED8D00A40FFE` (source/lab equal).
  Lab PID2268 closed on request; Steam preserved. Do not start another batch automatically.
  Probes stay outside the repo, no bot/sampler running. No injected input; the clicks were the user's.
  Universal-modder consulted at the start/end, Gotchas 38–42 updated; `um kb check` local, no PR.

## 2026-10-09 — Batch 16: correct costs and rebuild oracles

- **Data fix, not a balance change:** the old probe read `ItemCodeName` in structure/vehicle
  costs; the real type is `CodeNameSmallQuantity.CodeName`. The `pcall` swallowed the error and exported
  empty. Re-exported `data/game_costs.txt`: 281 items, 592 structures, 184 vehicles, 64 ammo types.
  Refinery and factory cost 400 bmat each; TruckW costs 100. Crate recipes did not change.
  Reproducible exporter `tools/export_costs.lua` (an error stops, it does not become zero) and test `tools/test_costs.py`.
- **Temporary probes in CallumsCape:** active refinery/factory classes spawned at the ruins'
  transforms, HP 2700/2000, TeamId 1 and matching BaseStructureClass. A raw construction site came with target `None`
  and zero requirements: this does **not** complete construction. Reflection + read-only Ghidra have not yet found/validated
  a public completion call. Inventory/RPC not pursued. Partial contract and limits in
  `data/trace_rebuild.txt`; there is no playable rebuild nor a ready chain in the hex yet.
- **Parking failure measured:** the vertical trace hit a warehouse roof, not the ground; another TruckW
  returned IsValid with HP 300/zero position and was rejected by the active inventory (2/3). The factory's bounds
  include giant volumes, they are not its footprint. The next construction requires an explicit budget, rollback,
  verified surface/clearance and a road; a spawn at an offset is not enough. Three trucks + two installations
  would cost 1100 bmat, separate from the logistics' 240 starting production bmat.
- **Small fix in the mod:** `logi.convoySpawn` now rejects `bActorIsBeingDestroyed` before touching the
  pawn, counting or alerting. Same contract the regional inventory already used; an old comment about fictitious
  spots fixed. The offline test covers an IsValid return already being destroyed and forbids touching it.
- **Validation:** cost tests, the orders/syntax suite and globals PASS. Published/restarted through the script;
  in HomeRegionW logistics opened with three trucks and the colonial convoy spawned HP 900, destruction flag
  false. Refusing a return being destroyed was tested offline, not forced in this live spawn.
  Source/lab hash equal: `1411C81F01ADD984272C20C698D3B21F001FC43237477A0FCFD14C264A58FEC5`.
  No mod error in the validation log; no new key nor real input test.
- **Closing:** CallumsCape probes destroyed and ruin collisions restored; PIDs 996/13368 of the
  copy closed. Temporary `map.txt` removed (default HomeRegionW), Steam PID1508 preserved.
  Learnings 35–37 local in universal-modder; `um kb check` PASS (60 notes), no PR.
  Final check: no War process; Steam PID1508 preserved. Next batch: offline deployment at the fixed spots,
  with its own budget and safe parking; then transport along the native road network.

## 2026-10-09 — Batch 15: regional inventory, match without fictitious logistics

- **Recognition by actors, not by image:** Deadlands loaded with 634 landscape/road segments,
  596 control points, 23 PlayerStarts and a ruined factory; no active instance in the field,
  refinery, factory and truck classes searched. CallumsCape loaded with 431 segments/405 points, one active
  salvage field, two factories and a refinery in ruins, no PlayerStart or truck searched.
  Trace in `data/trace_regions.txt`, reusable probe `tools/inspect_region.lua`. These are local loaded
  states, **not** proof of absence on the map/server. The search included a histogram of derived classes.
- **User warning persisted:** structures may become invisible depending on angle/occlusion, vehicles by LOS.
  Never turn something missing in a capture into something missing in the inventory. Rule in AGENTS, README/study/script updated.
- **Regional autostart:** case-insensitive path comparison (`DeadlandsHex` from the index opens as
  `DeadLandsHex`); it only finishes when RTS really turned on. CallumsCape had no searched anchor;
  the salvage field is now the last resort after PlayerStarts/vehicles. No hardcoded regional coordinate.
- **Logistics (`scan`/`ready`):** removed the imaginary field/refinery/factory and trucks without a pawn.
  New match/assault and continue with logistics check active actors before clearing the previous session.
  Ruins do not work as installations yet; hidden actors remain available. Actors marked for
  destruction do not count just because IsValid is still true. A convoy without a created class/actor does not add to the counter/cargo.
- **Navigation base:** finished the tests of the A*'s optional parameter (volume/floor/step/budget,
  strict failure without an emergency straight line, job.done); four probes at 12 m in Deadlands used native UFunctions
  (36–54 ms synchronous). **Trucks still go straight**; missing integration with the network, external access and a test of
  water/bridge. Do not confuse this technical base with delivered road transport.
- **Validation:** offline suite and globals PASS; published/restarted, source and lab hashes equal.
  CallumsCape: autostart on, commander HP 100 via the field, new match and assault refused preserving
  two real soldiers. HomeRegionW: autostart, an explicitly hidden factory still discovered, a match with
  six soldiers/three real trucks; in 118 s, three crates produced and one delivery. The base's starting stock
  emptied on purpose to create demand, waves off: **not a balance test**. Colonial convoy
  created with a real pawn. No mod error in this validation's log; real input pending (12x).
- **Closing:** temporary map configuration removed (the next start goes back to HomeRegionW);
  copy PIDs 19896/14176 closed after the probes. Check: no game process, Steam preserved.
  Learnings 33–34 in universal-modder; `um kb check` PASS (60 notes), no PR.
- **Next batch:** trace the native rebuild of the CallumsCape ruins and the creation of the scenario's real trucks,
  then link the discovered road network to transport. There is still no playable chain in a real hex.

## 2026-10-09 — Real region and construction: the user's scope correction

- HomeRegionW is the Wardens' training/boarding island, not a war hex. ROADMAP and the study
  fixed: it remains a test bench, but phase 3 requires recognizing and validating a `Maps/Master/*Hex` region.
  Do not assume war actors just because the client contains the map; check loading/streaming,
  starting position, terrain, roads and present installations, without fixed lobby coordinates.
- Separated the two branches in the plan: fixed urban structures (factory/refinery) and facilities built
  by players. External context explicitly cited in ROADMAP, separate from data extracted from the client
  in MECHANICS_STUDY. Construction/recipes need a local trace before an offline implementation.
- **Unpublished draft:** the A* in `main.lua` accepts optional navigation limits (volume, floor,
  step, cell and budget), without a straight-line return on strict failure; jobs signal `done`.
  Existing offline tests and globals passed, but specific tests and live validation are missing.
  Trucks do not use it yet nor follow the native network: do not consider the feature delivered.
  Pre-draft backup: `D:/tools/foxhole-lab/main-before-roads.lua`.
- Documentation only in this scope correction; the game was not published/restarted. The lab stays closed
  (no `War-Win64-Shipping.exe` in the check). Universal-modder consulted; gotcha 32 recorded;
  `um kb check`: **PASS, 60 notes**, no PR.

## 2026-10-09 — Lab closed when idle (user's request)

- New rule persisted in `AGENTS.md`: close the copy when the validation ends or when moving to offline work;
  leave it open only during active tests or at the user's request. Never close Steam nor the official client.
- With no bot or active test, closed only PID **13112**, checked as
  `D:/FoxholeLab/Foxhole/War/Binaries/Win64/War-Win64-Shipping.exe`, via `um win kill`.
- Road investigation already preserved outside the repository: `D:/tools/foxhole-lab/road_graph.tsv`,
  `t_road_*.lua`, `road_inspect.py`. HomeRegionW has 122 `LandscapeSplineSegment`s, 95 of them with a mesh
  in `/Roads/`; the other 27 use `SplineEditorMesh` (do not treat as a road). `Points.Center` and the
  `ControlPoint.ConnectedSegments` allow rebuilding real curves/connections; 595 nodes, 563 edges,
  two networks (397 and 166 nodes). Coordinates are local: apply `KismetMathLibrary:TransformLocation` with
  the `LandscapeSplinesComponent`'s transform. `Connection.End` is a bool (not an integer).
- Next step: traversable accesses from the installations to the network and truck movement along that network.
  The refinery/factory are far from the road nodes (more than 100 m): replacing the straight line with
  "nearest node" is not enough; check access, bridge and an external load/unload point before publishing.

## 2026-10-09 (morning, 15) — Batch 14: native death; no more running on the corpse

- **Bug reproduced and cause measured:** a soldier killed while marching kept `Health=0`, velocity and
  `AnimInstance.Speed=500 cm/s`, until disappearing at 20 s. `ApplyDamage` on the host did not trigger `OnRep_Health`.
  A probe of the native and the RTS character, a list of UFunctions and the activity enum preceded the fix.
- **Flow found:** `SimCharacter:OnRep_Health` → native ragdoll. Ghidra confirmed the wrapper
  `0x141227ed0` → `0x140b04440` → `0x140b107f0` (profile `Ragdoll`, mesh physics); `BPCinematicDeath`
  alone did not make the tested transition. No RPC, inventory, keyboard/mouse or isolation/Steam change.
- **Fix (`anim.retire`, in the `reap` shared by both sides):** remove markers/cache before the
  native notification; consume input, zero velocity, restore friction/braking/acceleration saved at
  spawn, leave aiming and call `OnRep_Health` once. `postureTick` ignores the dead. `untrack` zeroes
  `animAddr` and does not remove the new owner of a recycled address. The body stays 20 s; the controller goes to the pool.
- **Validation:** offline tests + `check_globals.py` passed; published through `restart.sh`. Live, a dead soldier
  marching at 500 cm/s went to zero velocity, original movement values, empty cache, mesh physics
  active and an invalid AnimInstance. Capture `D:/tools/foxhole-lab/death-fixed_small.png` checked: body on the ground.
  Contract persisted in `data/trace_death.txt`; probes/traces and decompilation stay outside the repository.
- **Care in the probes:** never query the pawn after the TTL nor the AnimInstance after enabling the ragdoll; `IsValid`
  may lie until GC. A sampling loop needs an `active` guard (the `return true` did not end the probe).
  A late probe without that protection left the channel unresponsive; recovered with a restart, not Ctrl+R.
- README, ROADMAP and manual test 12w updated. **Regression finished:** bot at 3x, a step every 3 real s,
  6:32 of game, defeat at wave 6, **36 kills / 26 losses**, no crash or cache error. The cache check
  passed in all 31 steps, including deaths on both sides and controller reuse. Do not compare this balance
  result directly with batches 12–13 (1x/another cadence); 2–3 matches at 1x remain pending.
  Bot stopped; lab left at 1x, six soldiers and automatic waves off, ready for testing.
- Universal-modder consulted at the start (`kb search foxhole/death/unreal`, RE and Unreal skills); gotcha 21
  fixed and gotchas 28–29 added locally. `um kb check`: **PASS, 60 notes**; no PR.

## 2026-10-09 (morning, 14) — Batch 13: enemy convoy

- `CFG.ECONVOY`, `logi.convoy*`: with automatic waves, every 35 s a colonial truck (`BPTruckC_C`, created
  with `LoadAsset` + `SpawnActor`: works) goes from the rear (90–200 m) to the front (45 m); on arrival it adds
  `combat.cargo`; each wave spends up to 2 loads (`logi.waveCut`) and each missing one removes 2 soldiers (min. 3).
  Our soldiers within 15 m damage it (visible fire); mortar/grenade hit trucks of both sides
  (`logi.blast` in `shell`); destroyed, it yields 25 manpower. `logi.hit` unifies truck damage.
- A straight route went over a cliff (b13_conv.png): `logi.routeOk` samples the ground every 10 m (step
  ≤ 4 m, height difference ≤ 15 m). Live: 5/5 valid routes found.
- Offline tests pass (wave cut, arrival adds cargo, soldiers destroy). Live: convoys arriving by the
  validated route (4 in the first match), truck on the ground; it disappears from the screen outside our soldiers' sight
  (the game's LOS, like the enemy soldiers); the red disc of the high view always shows.
- Bot (does not ambush, so it is the worst case: every convoy arrives): **defeat at wave 10**, 83 kills / 38 losses,
  9 min, no crash. 16 convoys arrived, 0 destroyed; even so 5 waves came smaller for lack of cargo
  (35 s per convoy does not keep up with the wave pace at the end); 7 deliveries of ours, none of our trucks lost.
  The convoy only shrinks waves, so the defeat is bot variance (batch 12: victory with 24 losses; before
  batch 9: defeats at waves 9–10). Next session: 2–3 bot matches to measure the variance.
- README (Logistics section, item 7) and MANUAL_TEST (12v) updated.
- **User's request at closing:** death animation (a soldier "running" in place when dying) and the principle
  "trace before reinventing", with universal-modder at the start and end of each session (`ROADMAP.md`,
  `CLAUDE.md`). The Foxhole note in universal-modder gained gotchas 19–27 (local, `um kb check` PASS; no PR).

## 2026-10-09 (early morning, 13) — Batch 12: logistics v1

- **Chain (`CFG.LOGI`, table `logi`):** a resource truck from salvage field → refinery (100 per trip); refinery
  2:1 into bmat; the factory makes ammo crates (80 bmat, 50 s ×0.2) and shirts (80 bmat, 80 s ×0.2, 10 soldiers),
  automatically whichever is most lacking (Shift+L pins it); 2 supply trucks (15 crates) carry to the neediest
  depot (base or a point of ours; L pins the next one). Recruiting spends a shirt from the depot (a point without shirts → base);
  `resupply` gained the depot parameter (1 crate = 6 reloads; empty does not reload and alerts). A lost point
  zeroes the stock. An enemy within 15 m of a moving truck: 25 HP/s per enemy; destroyed, it disappears with the cargo and comes back in
  30 s for 100 bmat. The save keeps the stocks (`logi.snapshot/restore`). Panel: 2nd line "LOGÍSTICA".
- **Places and trucks from the map itself:** `FindAllOf("BPSalvageField_C"/"BPRefinery_C"/"BPFactory_C")` nearest the
  base (without them, fixed points); parked `BPTruckW_C`s: character movement, no physics, so
  `K2_SetActorLocation` + `groundZ` + yaw sticks (measured: stopped for 2 s without moving back). No collision, in a straight line.
- Validated live: salvage 100 → bmat 50, 3 crates, delivery pinned to the base (ammo 6 → 8), capture b12_res.png.
- `test_orders.py`: refinery, factory choice, delivery, reloading spending and failing without stock.
- Bot: **victory in the 10 waves**, 111 kills / 24 losses, no crash; 9 deliveries (all to point A), 10 recruits
  fell back to the base for lack of shirts at the point, 2 alerts of a depot without ammo, no ambush.
- Pending: roads (trucks cut across everything), enemy AI with logistics, vehicle as a unit.

## 2026-10-09 (early morning, 12) — Study of the game's mechanics

- Pak index (v8, no encryption) → `data/pak_files.txt`; cost/health/fuel/cargo tables
  read with `DataTable:ForEachRow` → `data/game_costs.txt`; summary in `MECHANICS_STUDY.md`.
- A generic dump of all columns crashed the game on `BPAirDynamicData` (native crash); reading known
  columns worked. Rule: read only simple-type columns.
- HomeRegionW has salvage/components/sulfur/oil fields, refineries, a factory, a forward base and trucks:
  it is the small region of phase 3 (logistics v1).

## 2026-10-09 (early morning, 11) — Batch 11: several fronts; roadmap

- **User request:** "para um RTS nível Foxhole, o cara vai ter que olhar muitas frentes" (an RTS at Foxhole's level means watching many fronts), and then: start
  in a small region and go to the whole world; study ships, planes, transport, manufacturing and logistics ("a
  guerra em si é a pequena parte da engrenagem" — the war itself is the small part of the machine). Plan in `ROADMAP.md`.
- **Zoom up to 160 m** (`CAM_DIST_MAX` 16000; batch 10's 60 m ceiling removed). `rts.zoomGfx`: `r.ViewDistanceScale`
  = height / 20 m (minimum 3), reapplied every half step. Validated: 160 m, scale 8, whole map drawn.
- **Icons in the high view** (`CFG.STRAT`, `rts.icon/stratTick`): above 60 m, a disc with a dynamic `CalloutRed`
  material (blue/orange/red), scale proportional to height. Enemies only with a visible mesh
  (`Mesh.bHiddenInGame`), so as not to reveal who the game hides. Validated by capture (b11_strat.png).
- **Front alerts** (`CFG.ALERTS`, `rts.alert/jumpAlert`): point under attack, point lost, wave, casualty; a queue
  of 8 with a location; the same type within 15 m in 20 s does not repeat; Space goes to the newest and, within 4 s, to the earlier ones;
  panel "! N alertas (Espaço)". Validated live (2 alerts from the wave and the captured point).
- **Groups 1–5** (Alt+1–5 assigns, double tap centers), **0 = all** (before 3). **Q/E** cycle through the points.
  Space, Q, E, 4, 5 and 0 are pawn actions in the game (read from `InputSettings` live): accepted in the key test.
- `S` entered the channel's `env`. `test_orders.py`: alerts (repetition, Space walks the queue) and groups.
- Bot regression (batches 9–11): **victory at wave 5 by domination** (3 points for 90 s), 39 kills / 17 losses,
  no crash; the 5 waves broke and fled, 1 automatic evacuation. Before the rebalance, defeat at waves 7 and 6.
  Warning: it may now be too easy (broken waves do not retake points); watch in the next ones.

## 2026-10-09 (early morning, 10) — Batch 10: time, WASD camera and wheel, visuals

- **Tactical pause (Pause / Ctrl+Space) and speed 1x/2x/3x (Insert):** `SetGlobalTimeDilation` (pause =
  0.0001). The camera and the panel now count real time (`GetRealTimeSeconds`), otherwise they froze too.
  Turning off RTS goes back to 1x. Validated: paused, 0.001 s of game in 5 real s and the given order waited; 2x measured
  2.00 (14.2 s of game in 7.1 real s); panel "PAUSADO" updating.
- **User request: WASD and mouse wheel on the camera.** WASD alongside the arrows (in RTS the commander's input is already
  off). Wheel: `WasInputKeyJustPressed(MouseScrollUp/Down)`; the `MouseWheelAxis` axis does not work, it keeps
  the last value (measured: -1 at rest, the camera ran away). Validated with the user scrolling: "roda do mouse lida".
- **User request: "linhas artefatuais e objetos desaparecendo" (artifact lines and disappearing objects).** The camera was at 76 m (max. 90). `rts.gfx`:
  `r.ViewDistanceScale 3`, `r.Shadow.DistanceScale 2.5`, the commander's `LOSPostProcess` with weight 0 (the dark
  bands of the line of sight); max zoom 60 m. Applied live in the user's session; waiting for feedback.
- Morale (batch 9) rebalanced after the bot fell at wave 7 and then 6 (broken waves sped up the wave
  counter: ~39 s per wave against ~53 s before; fleeing enemies did not count): fleeing yields the kill bonus, a broken
  wave gives +15 s of regrouping, and evacuation does not pull those already on the point or at the post. Bot pending.

## 2026-10-09 (early morning, 9) — Batch 9: casualty evacuation; enemy morale

- **Evacuation (`CFG.MEDEVAC`, `rts.medevacStep`):** our soldier < 30% health, no order for 15 s (no focus,
  area, hold or march) retreats on their own to the aid post → a point of ours → the nearest medic; released at 80%
  (or gives up after 45 s stopped). Player orders mark `m.orderT` (in `os.clock`: `issueMove` comes before
  `now()` in the file — the checker caught it) and cancel the evacuation.
- **Morale (`CFG.MORALE`, `rts.moraleCheck/fleeStep/purgeFled`):** a wave of 6+ that falls to 25% of its size (adding
  pincer and reinforcements in `combat.waveSize`) breaks; the survivors run to the entrance (`e.home`), with
  `retreat` (half the hits, no firing) and vanish on arrival without counting a kill (`combat.fled`). The
  `enemyTick` loop skips those fleeing with `goto nextEnemy` (label at the end of the block). A killed officer suppresses (+0.5)
  those within 10 m. Does not apply in assault.
- `check_globals.py` ignores `goto` labels.
- `test_orders.py`: the wounded goes to the post, a recent order holds, the healed is released; a broken wave flees, those arriving
  vanish without counting a kill.
- Bot: the 1st version lost at wave 7 and then at 6; rebalanced (see batch 10).

## 2026-10-09 (early morning, 8) — Batch 8: sound per weapon and per side

- There are no voices among the 487 loaded `SoundCue`s; there are shots per weapon and faction in `/Game/Audio/SFX/Weapons/`.
  `WEAPONS.*.sndW/sndC`: rifle `RifleLongW` x `CarbineCShot` (matches the enemy's Colonial carbine), MG
  `MGW-RFShot` x `MGC-RFShot`, sharpshooter `SniperShot` x `SniperShotC`, pistol `PistolLIghtWShot` (medic and
  officer). Pitch 0.95–1.05; without the sound, falls back to `FX.shot` with the weapon's pitch. `asset()` now tries `LoadAsset`
  once per path not in memory (`S.fxTried`). Validated: after a restart, the 10 sounds loaded and 94 shots
  without error; listening is left for the manual test (12k).

## 2026-10-09 (early morning, 7) — Batch 7: health bar

- Colored material found by listing loaded `Material`/`MaterialInstanceConstant`s and reading
  `VectorParameterValues`: `CalloutRed` is an instance of `Unlit` with a `Color` parameter. The bar is a thin cube
  with a dynamic material from it (`CreateDynamicMaterialInstance` + `SetVectorParameterValue`), attached to the soldier
  with absolute rotation (`SetAbsolute`), length proportional to health, green/yellow (<60%)/red (<30%);
  only on our wounded and with RTS on (`rts.hpTick`, 0.3 s; the color only changes when switching bands).
  Validated: 80 → long green, 45 → yellow, healed → gone (`hp1c.png`, `hp2c.png`). The reddish tone of the
  wounded in the capture is the game's wound effect.

## 2026-10-09 (early morning, 6) — Batch 6: officer; the enemy machine gun suppresses an area

- **Officer (Ctrl+0, −40, one per squad):** pistol; allies within 10 m (including him) hit 15% more and lose
  suppression 1.8× faster (`CFG.OFFICER`, `rts.officerNear` with a 0.5 s cache per soldier). Marked with the
  rolled-up banner on the side (the one from the points) attached above the head: `FlagShortA/B` are vertical planes and
  vanished seen from above. Enemy: the 1st of each wave from wave 3 is an officer; killing him yields +20
  (`rts.officerDown`); in assault, the front point's garrison has one. `clearEnemies` now calls
  `destroyMarker` (hook, banner and markers).
  Validated: our officer with a banner, a 2nd refused; wave 3 with an officer in front; kill → "+20" in the log.
- **Enemy MG without line of sight:** remembers where it last saw the target (`e.seen`) and for 8 s stays and suppresses the area there
  (`rts.enemyArea`, the same `rts.areaShot`, which now serves both sides; ammo only counts for ours).
- `test_orders.py`: aura (recovers faster nearby, the same far away), a 2nd officer refused, the enemy MG suppresses the
  hidden one without spending ammo and gives up after 8 s.
- Bot: defeat at wave 10, 114 kills and 42 losses (same pattern), 8 enemy officers killed, no crash.
  Grenades 0 in that match (before 8–23): checked separately that the rifleman throws at an enemy in a trench
  (3 grenades); it was the scenario (enemies without cover within ≤18 m of the bot's position), not a defect.

## 2026-10-09 (early morning, 5) — Batch 5: Assault mode; bot; intermittent crash; globals checker

- **Assault mode (Alt+F6):** 8 soldiers and 120 manpower against three enemy points 26–36 m away
  (`CFG.ASSAULT.dist`), each with a trench, wire on our side and a garrison of 4 in a 1.5 m circle (the
  wave formation spread out and put two on the roof of the building next to point A). No waves; reinforcement only from the
  points' income (1st reinforcement only after 40 s); each capture of ours triggers a counterattack in 8 s (`rts.counter`).
  Victory: all three points ours with no enemy alive, or hold them for 60 s; defeat only by losing the squad (the
  enemy owning everything is not a defeat in assault). Garrison (`e.post`, `rts.holdPost`): with no target in range it returns
  to the point and holds; a lost point releases it. The save records the mode and each garrison's post.
  Validated: garrisons stopped at the points with the squad attacking A (0 away from the point in 5 samples); A
  taken → reinforcement through point C 8.0 s later; saving/continuing in the middle of the assault keeps the mode, 8 garrisons
  held and the points' owners (`as4.png`).
- **Bug caught in the test:** the counterattack trigger used `ai` inside `pointsTick`, before `local ai`
  (it becomes a nil global; the step's pcall swallowed it). `check_globals.py` did not see it because it is scope-insensitive and
  `local ok, ai = pcall(...)` in `anim.track` counted as a declaration. Renamed to `inst`, and the checker
  now warns when a top-level name appears earlier as an inner local (`SHADOW_OK` lists the checked ones).
- **Bot (balance after the real slowdown of batch 4):** defeat at wave 10, 104 kills and 39 losses, the
  same pattern as before; 7 min without a crash.
- **Intermittent crash (still open):** one bot match crashed 9 s after `newGame`, right after recruiting
  at point A (AV 0x3 from the per-frame loop, Lua → UObject access). Repeating the same script did not
  crash. The animation hook no longer touches the pawn. If it comes back, instrument `recruit`/`spawnSoldier` with a log before
  and after each Unreal call.

## 2026-10-09 (early morning, 4) — Batch 4: aid post, barbed wire, area marker; real slowdown

- **Meshes chosen by showcase:** a search in `FindAllOf("StaticMesh")` for tent/wire/hospital (213 found),
  `GetBounds()` for the size and a side-by-side row on the map (`b4b.png`). `CanvasTent09` was only the frame;
  `CanvasTent06` (closed canvas, scale 0.6) became the post; `BarbedWire04` (wire trestle, 7.5 m, center
  306 cm from the pivot) at scale 0.8 became the wire (`BarbedWireFence01` looked like a metal mesh).
- **Aid post (Ctrl+8, −30, up to 2):** our soldiers within 6 m with suppression < 0.2 recover 4 HP/s and stop
  bleeding. Validated: two riflemen at 40 health went to 100 at the post.
- **Barbed wire (Ctrl+9, −10, up to 10):** a 6 m × 2.2 m strip laid across the threat (same turning rule as the
  barrier, now in `fort.facing`); anyone inside, on either side, walks at 35%. No collision: the A* does not detour.
  The enemy lays a strip for free 9 m from the center of a point it takes, on our squad's side
  (`CFG.ENEMY_WIRE`, `fort.enemyWire`).
- **Real slowdown (wire and suppression):** the 1st measurement (a 100 ms loop recording position in a global)
  gave a constant 58 cm/100 ms crossing the wire. With friction and braking zeroed, the CMC keeps its velocity
  when the limit drops (`IsExceedingMaxSpeed`); the `AddMovementInput` scale only limited the start. In other words,
  the suppression slowdown (`SUPP_SLOW`) had never worked either. `fort.capSpeed` cuts the horizontal velocity
  directly when the scale drops below 0.9. Measured again: 20 cm/100 ms inside the strip (35%),
  58 outside.
- **Area fire marker:** a ring of 12 smaller orange points on the circle; it vanishes when no living soldier
  still has that order. The order is now a single table for all soldiers.
- The save records posts and wires (and whether the point already has an enemy trench/wire); F11 and new match clear them.
- `test_orders.py`: the wire strip (inside, beside, past the tip), the post's healing (calm heals; suppressed and
  far away does not), save with posts and wires; keys Ctrl+8/9.

## 2026-10-09 (early morning, 3) — Batch 3: save/continue, area suppression fire; hook crash

- **Save and continue (Ctrl+F6):** with automatic waves, the match is written every 30 s to
  `ue4ss/Mods/FoxholeRTS/save.txt` (Lua `return {...}`, read with `load` in an empty environment; version `v=1`):
  wave, score, time, manpower (ours and the enemy's), difficulty, map, points (owner and progress),
  barriers (position and turn), trenches and each living soldier of both sides (class, position, health, kills,
  ammo, group). Victory or defeat delete the save. When turning on RTS without a match, an alert says there is a
  saved match. Table `sv` (`ser`, `parse`, `collect`, `save`, `read`, `restore`, `load`, `tick`, `map`);
  the barrier gained `fort.wall` for the loader to reuse.
  Validated: save with a trench, a barrier, points A ours/B the enemy's, a veteran with 4 kills and an MG at 55
  health → clear everything → continue: everything the same (`sv1.png`); the alert on reopening the game; autosave 30 s after
  continuing; a defeat deleted the file.
- **Area suppression fire (Ctrl+right button / Ctrl+F7):** the selected (except medics) fire for
  20 s into a 4.5 m circle. Out of range, they walk to it. Without line of sight there is no damage: each shot suppresses every
  enemy in the circle with 70% of the weapon's suppression (mounted MG ×1.5) and kicks up dirt at a point in the circle;
  an enemy in sight and in range takes a normal shot. Spends ammo; move, attack, retreat or hold cancel.
  `rts.areaOrder`, `rts.areaStep`, `rts.areaShot`; `rts.shotFx` (flash and sound) now serves both kinds of shots.
  Validated: 5 soldiers aiming and firing at an empty point 15 m away, 60 shots in ~8 s (`af1.png`).
- **Crash (EXCEPTION_ACCESS_VIOLATION 0xffffffff inside UE4SS, 96 s after opening):** `clearEnemies` did not
  remove the enemies from `anim.units`; the next wave's AnimInstance reused the address of a destroyed one
  and the hook wrote `bIsInScopeMode` to the dead pawn (pcall does not catch it). Fix: `clearEnemies` calls
  `anim.untrack`, and the hook only writes to the AnimInstance being updated (always alive); the
  pawn's `bIsInScopeMode` moved to `postureTick` (0.3 s), which only walks the lists of the living.
  Validated: a new wave after continuing and 4 cycles of new match → clear with 6 enemies alive, no crash.
- `test_orders.py`: save (collect → text → read, neutral owner, the dead left out, invalid text refused) and area
  fire (without line of sight it only suppresses those in the circle, spends ammo, moving cancels); keys Ctrl+F6/F7.

## 2026-10-09 (early morning, 2) — Batch 2: stances and actions; the menu warning

- **Stances through the same animation hook:** crouched (`CharacterStance` 1 + `bStanceIsCrouched`) when
  stopped inside a trench or with suppression ≥ 0.4 (`CFG.CROUCH_SUPP`); hunched running (stance 3) when
  retreating. `m.crouch` is computed every 0.3 s in `anim.postureTick` (outside the hook, so as not to trace every
  frame). Validated: 4 soldiers kneeling in the foxhole aiming (`c2.png`); retreat → stance 3 in all 6.
- **Actions:** `ActivityState` 6 (throwing) for 0.8 s when throwing a grenade, 20 (first aid) for 1.2 s
  when the medic heals, 3 (firing) for 0.2 s. Validated by the value in the AnimInstance (medic act=20 healing);
  the throw uses the same path, but it is too short to catch in a capture through the channel.
- **Menu warning:** it is native Slate (in the menu there is only one `UserWidget`, the crosshair; `MainMenuPlayerController` and
  `WarGameInstance` have no function to close it). Opening the network would go against the offline mode. Mitigation: the
  autostart leaves the menu in 2 s (`CFG.AUTOSTART_DELAY_S`, was 8). Validated: menu → map in 2 s, RTS on
  5 s after the menu (before ~11 s). Batch 1's widget hunter was removed.

## 2026-10-09 (early morning) — Batch: weapon and firing animation, enemy economy, menu warning

First batch in the new flow (several features, a single lab test).

- **Weapon animation (user request: "o tiro sai mas o soldado não mira nem segura a arma" — the shot comes out but the soldier neither aims nor holds the weapon).**
  Study through reflection (universal-modder's Unreal guide: dump classes first):
  - The AnimInstance is `ABP_Male_C` (native parent `CharacterAnimInstance`). The pose depends on
    `EquippedWeaponGripType` (enum `EEquippedWeaponGripType`: None 0, Rifle 1, Pistol 2, Sniper 4,
    HeavyMachinegun 5, LightMachineGun 24…), `bIsScoping`, `canEnterStandScoping`, `AimOffsetYaw/Pitch`
    and `ActivityState` (`ECharacterActivityState`: Firing 3).
  - The native update recomputes everything every frame from the equipped item and the local control, which our
    soldiers do not have: writing directly does not stick (grip went back to 0). But the ABP's `BlueprintUpdateAnimation` runs
    **after** the native one; a `RegisterHook` on it writes our values and the graph uses them.
  - `AimOffsetYaw` came out −140° (control rotation 0 − body 140): the pawn turns to the control rotation,
    but the aim offset does not follow without local control → the hook zeroes the offset.
  - The weapon was on the `hand_r` bone (pointing backward). Body sockets: `S_GenericGun`, `gun_r`, `gun_l`;
    `S_GenericGun` gives the right pose. Master pose does not work (the weapon mesh has a single bone, `Root`).
  - Result (`cb4.png`, `cb6.png`): ours and enemies with the rifle at the shoulder, both hands on the weapon, aiming
    at the target; at rest, the rifle on the shoulder at ease. MG with grip 5 (with 24 it sat crosswise).
  - Code: table `anim` (`anim.onUpdate`, `anim.track`, `anim.untrack`), `CFG.ANIM_ABP`, `CFG.AIM_HOLD`
    (1.5 s aiming after the last firing attempt), `CFG.FIRE_ANIM` (0.2 s of Firing per shot); `armWith`
    attaches to `S_GenericGun` and registers the soldier; `destroyMarker` removes it; `bIsInScopeMode` only when stopped.
    The muzzle flash comes out of the weapon's `S_Muzzle` socket.
- **Enemy economy (reinforcements):** validated live. Natural: the enemy took C in wave 1 and sent
  1 reinforcement; forced: 3 through point A. Panel "reforço inimigo N". Plural fixed ("1 soldado").
- Bot with the batch (reinforcements + animation): lost at wave 10 (109 kills, 34 losses), the same as earlier
  rounds; the enemy economy did not unbalance it.
- **Menu warning** ("Falha ao baixar informações do servidor [Erro: 1]… Atualizar / Fechar", `menu1.png`):
  the hunter by `UserWidget` class name found nothing; the probe through the channel arrived after the menu.
  Solved in batch 2: it is native Slate; the autostart now leaves the menu in 2 s (see the entry above).

## 2026-10-08 (afternoon) — Enemy economy (reinforcements)

- Each point the enemy holds yields 0.6/s of manpower for it (ceiling 200; only with automatic waves).
  During a wave, every 20 s it spends 20 per soldier on reinforcements of 2 to 3 that appear 9 m behind its
  point nearest our squad (on the side opposite us), up to 6 per wave. Alert "REFORÇO INIMIGO";
  panel "reforço inimigo N" when it has points. Losing points hardens the waves; retaking them cuts the income.
- Code in table `ai` (`ai.tick`, `ai.source`, `ai.reset`; `CFG.AI`); `spawnEnemies` gained a 4th
  parameter `quiet`. Offline test: income per point, ceiling, no reinforcement without a live wave, origin point.
- Validated live in the 2026-10-09 batch (see the entry above).

## 2026-10-08 (morning) — Vision from the soldiers (the commander's "eye")

- **How the game hides enemies:** the commander's `Character_C` has `PlayerLOSRasterComponent` +
  `LOSPostProcess`; native code sets `bHiddenInGame` on the mesh of anyone out of sight, and the body's material
  also vanishes (unhiding the mesh from Lua only made the rifles we attached appear). Moving the
  LOS component changes nothing; changing `AlwaysVisibleRadius` (700) at runtime does not either.
  What counts is the **pawn**'s position: with the commander 4 m away the enemies appeared; behind a snow
  ledge, 9 m away, they did not (LOS blocked by terrain, not a lack of range).
- **Eye:** when RTS turns on, the commander becomes an invisible eye (`SetActorHiddenInGame`, no collision,
  `MOVE_None`, so no gravity) and `rts.eyeTick` carries it every 0.2 s to the living soldier nearest the camera's
  focus (without soldiers: the base). The game's vision now comes from where the camera looks, from one
  of your soldiers. When RTS turns off it returns to the base, with collision and walking. `CFG.EYE = false` turns it off.
- **Fixed base:** `rts.base()` = where the commander was when RTS was turned on. The ammo depot, retreat without
  points, the reference for waves/points/barriers and F2 use the base, not the pawn (which now roams).
- Validated: 3 enemies on the snow ledge, invisible with the commander nearby (`fog1.png`), appear with a
  soldier beside them and the eye on (`eye3.png`). On open ground at 33 m the base's vision already reached, so
  the gain is behind buildings and relief and on larger maps.

## 2026-10-08 (early morning, 6) — Trenches

- **Ctrl+7 digs a trench** under the cursor (−20 manpower; max. 8; refuses next to another):
  the game's `pvpFoxhole01` mesh (a foxhole, ~3.4 m), random turn. Anyone inside (radius 1.7 m,
  either side) takes 40% of rifle hits and half the suppression. Grenade and mortar are not
  reduced: they are the counter. Riflemen also throw grenades at an entrenched target.
- **The enemy digs in:** when taking a point, it opens a free trench at its center (one per
  point; `CFG.ENEMY_DIG`). Retaking the point requires a grenade/mortar, and then the trench serves us.
  Validated: 4 enemies on B → "o inimigo tomou o ponto B e cavou uma trincheira", a trench on B.
  Creation lives in `fort.place` (table `fort`, so as not to spend more of the chunk's locals).
- A move order with a destination inside the trench: the first 4 take slots in a ring inside it, the rest
  form a line just behind (before, the line centered on the hole crammed all 6 inside).
- `seekCover`: a stopped and exposed soldier first goes to a trench with a free slot within 4.5 m.
- Validated live: 4 inside, 2 behind (`trench.png`); a wave of 6 against the trench: 116 enemy shots,
  7 hits, 106 stopped by the cover; 6 kills, 1 loss; the two outside entered the slot on their own.
- Bot with 2 trenches on A (`t_bot0t.lua`, `BOT0=t_bot0t.lua sh botloop.sh`): lost at wave 10 (89 kills,
  33 losses). The enemy threw 23 grenades (before ~1): the counter works, and the trench does not unbalance.
- Offline test: slots (4 inside with 6 selected), suppression halved, refusals without charging.
  Finding: the crate's refusal tests passed because `server` had stayed false (refusal by authority);
  now `server = true` before them.

## 2026-10-08 (early morning, 5) — Ammo and supply crates

- **Ammo** (ours only; "commander" below became "base" in the morning entry): rifleman 40 shots, MG 150, sharpshooter 15, medic 24 (`CFG.WEAPONS[..].ammo`).
  Without ammo the soldier does not fire (an alert every 15 s: "leve-o a um ponto seu ou ao comandante");
  the panel shows "SEM MUNIÇÃO N" and "munição baixa N" (<25%). Reload of 15%/s inside a point of yours
  (which already healed) or within 5 m of the commander (otherwise losing all points would lock the squad).
  Grenades do not spend ammo. The enemy has no limit: it attacks, it does not sustain.
- A soldier with low ammo gets a small ammo box (the same mesh, 0.6×) floating 1.9 m above
  the head; it vanishes when reloaded above 25% (updates every 0.5 s, only in RTS mode). At 1.15 m it
  covered the head and could not be seen. Validated: 4 dry soldiers → 4 boxes (`icon_crop.png`); reload → hidden.
- Bot with ammo: lost at wave 9 (88 kills, 30 losses; A fell), within the ~50% history. "dry 0":
  fighting inside point A it never ran dry (1618 shots replenished). Ammo punishes advancing far from
  supply, not defending. Channel: `CFG` now exported (live tuning, e.g. `CFG.AMMO_REFILL = 0`).
- **Supply crate (Ctrl+6)**: −25 manpower, the game's `AmmoCrate` mesh under the cursor; for 60 s
  it reloads 25%/s within 4.5 m (no healing); max. 3, cooldown 10 s; panel "caixas N". It vanishes on its own at the end.
  Validated live: a crate beside the squad, ammo at zero → full in a few seconds (`crate.png`).
- Regression bot (MG only fires mounted, before ammo): won wave 10 with 4 soldiers, 109 kills
  and 26 losses. The balance remains tight.
- `botloop.sh` now stops when `combat.auto` becomes false (before it looked for "won false", which never matched
  because of the tab).

## 2026-10-08 (early morning, 4) — Difficulty

- **Shift+F5** toggles easy → normal → hard (`CFG.DIFFICULTIES`). Each level overrides enemy
  accuracy, wave growth, extra enemies per soldier of ours, manpower per second and pincer
  chance. "normal" = the values calibrated with the bot. The panel shows "RTS (difícil)" and the new
  match alert names the level. F5 alone now ignores Shift (otherwise Shift+F5 also toggled the help).
  Validated live (panel and alert, `diff.png`); the offline test covers the cycle and the values.
- The difficulty is saved in `Mods/FoxholeRTS/settings.txt` (`difficulty=N`) and returns when the game restarts
  (validated: hard → restart → enemy accuracy 0.85; log "dificuldade salva").

## 2026-10-08 (early morning, 3) — Victory by domination

- With automatic waves, holding **all** points for 90 s in a row (`CFG.HOLD_TO_WIN`) wins
  (alert "VITORIA POR DOMINIO", enemies removed, waves turn off); losing any point resets the
  clock. Panel: "domínio N s". Validated: points forced to us → panel "domínio 84 s"
  (`dom1_crop.png`); clock advanced through the channel → victory. The offline test covers the start, resetting on
  losing a point and the victory.
- End-of-match summary (victory or defeat): time, waves, kills, losses, accuracy, mortars,
  grenades, surviving veterans and points (`sum_crop.png`). Shot/grenade/mortar counters now reset
  in `clearSquad` (before they accumulated between matches). Fixed the defeat-by-points message, which
  had been left as "F11 + Shift+F6".
- **Order queue:** Shift+right button / Shift+F7 appends the destination to each selected unit's queue
  (keeps the position in formation); those standing still leave at once; arriving pulls the next; a new order
  (move, attack, End, Home) discards the queue. Validated: 3 destinations in an L walked in sequence in ~5 s.
- Shortcuts with and without a modifier (1/Ctrl+1, F4/Shift+F4, F6/Shift+F6, F7/Shift+F7, right button/
  Shift+right button): it is unknown whether UE4SS fires only the combination or both, and there is no way to test
  without real input. The unmodified version (`plain`) now ignores the trigger while Shift/Ctrl/Alt is
  held (read via `IsInputKeyDown`; with no keys held all six read `false`, checked).
- **Pincer waves:** from wave 3, with 6+ enemies, half the time the wave splits into two
  groups, the second at 90–150° from the main entrance (`flankPoint`; `spawnEnemies(at, n, sameWave)` does not
  count a new wave). Validated: 6 waves forced through the channel → 3 pincers, groups on opposite sides.
  Bot with pincers from wave 3 and 50%: fell at wave 7 (3 pincers). Adjusted to wave 4 and 40%:
  fell at the 10th, the last one (1 pincer; 101 kills, 35 losses). Bot score so far: 3 victories, 3 defeats.
- Game sounds: `WinResultVictory_Cue`/`WinResultDefeat_Cue` (2D) at the end of the match and `StructureBuild_Cue`
  when raising a barrier. The three objects exist in memory and the calls run without error; whether they actually play
  can only be confirmed by listening (there is no way through the channel).
- Refactor: 15 small states (controller pool, effects cache, occlusion, statistics etc.)
  became fields of `S` — top-level locals 172 → 158 (Lua limit: 200). Bot match afterwards:
  no errors; ~38 frames/s; mod 1.8 ms/frame.
- **Oriented formation:** the march order builds, at the destination, a line of up to 4 (`CFG.FORM_WIDTH`)
  with rows behind, rotated to be perpendicular to the group center → destination direction (last
  row centered). Before: a column of 2 always aligned to the X axis. Validated: 8 soldiers sent
  diagonally → two rows of 4 across the march (`form.png`); the offline test checks
  distance, center and perpendicularity.
- **Machine gun sets up:** the machine gunner (on both sides) only fires after being stopped for 1 s (`stillSince`, set in
  `halt` and cleared in `moveToward`); set up, hit ×1.3 and suppression ×1.5. Marching it does not fire (before
  it fired while walking like the riflemen). Validated: stopped for 3 s with enemies at 17 m → firing.
- Automatic points also checked in HomeRegionC (3 points with 24 markers each). There the camera
  ended up behind a large structure near the start.
- **Camera occlusion:** every 0.4 s a trace (Camera channel) from the camera to the focus hides up to 4 actors in
  the way (`SetActorHiddenInGame`), never landscape, characters or `InstancedFoliageActor` (a single actor
  holds all of the level's vegetation); whoever stops blocking reappears, and everything reappears when leaving RTS.
  Validated in HomeRegionC: the same position previously taken by the structure shows the yard, the points and the
  squad (`ptsC.png` → `ptsC2.png`).

## 2026-10-08 (early morning, 2) — Performance: from 6 to ~30 frames/s in combat

- Per-step profiler in the loop (`step()` with `os.clock`, which on Windows is wall time); `profile()`
  in the channel and on F5 gives ms/frame per step.
- Measured with 12 soldiers + 15 enemies: a 150–400 ms frame; the mod spent 80–180 ms
  (`pathTick` 71, `squadTick` 54, `enemyTick` 51).
- **Cause 1:** `UEHelpers.GetWorld()` does `FindAllOf("PlayerController")` on every call (0.3 ms
  measured) and `now()`, traces and spawns called it hundreds of times per frame. Now `world()`,
  `now()` and `isLocalAuthority()` are cached during the frame (`tick.inFrame`; outside the loop —
  keys and channel — they are recomputed), `loc()` too, and `playerController()` uses
  `GameplayStatics:GetPlayerController(world, 0)` (cost ~0; `UEHelpers.GetPlayerController`
  accepted any PlayerController, including the soldiers').
- Also: target search + line-of-sight trace only every 0.25 s (`CFG.SCAN_EVERY`, with jitter) or
  when the weapon is ready, instead of every frame; A* with a budget of 4 ms/frame in slices of 4 nodes.
- Result: mod from 80–180 → **~4 ms/frame** in the same scene; game frame 33–84 ms.
- **Cause 2 (leak):** `K2_DestroyActor` does not destroy `HeadlessPlayerController` (refused
  by the engine; a destroyed `StaticMeshActor` disappears at collection, the controller does not — 180 valid
  controllers after ~150 deaths, each with a `SimPlayerState`, `PlayerCameraManager` and `CameraActor`).
  After a long match the frame went to 350 ms with only 12 soldiers. Now the dead soldier's controller does
  `UnPossess` and goes to a pool that `spawnSoldier` reuses (with `bIsLocalPlayerController`
  off until the new possession). A whole bot match: 25 controllers in total, 129
  reuses; final frame 60 ms with 12 soldiers (was 350); the mod on average 1.5 ms/frame.
  Turning off the tick of idle controllers changed nothing: the rest is the cost of the game's characters.
- **Pitfall:** reading `hpc.Player` and calling methods on it (`GetFullName`/`GetClass`) brought down UE4SS's
  Lua state (silent channel, game alive); a restart was needed.
- Balance checked after the changes: the bot won with 19 and 23 losses (same range as before).

## 2026-10-08 (early morning) — v0.7: mortar, grenades, veterancy, retreat, help, new match, balance

- **Ctrl+5 = mortar** under the cursor: 40 manpower, cooldown 20 s (panel: "morteiro pronto" /
  "morteiro N s"). Incoming artillery sound + a ring of 8 discs; after 2.5 s, 3 shells spread
  up to 2.5 m from the target with the game's `MortarBlast` effect and `ArtilleryLightExplosion_Cue` sound
  (found with `FindAllOf("ParticleSystem"/"SoundCue")`, 82 and 55 candidates). Damage 75 with a linear
  falloff down to 30% at the 3.5 m edge, only on the opposing side (instigator of one's own side, as with firing);
  suppression on everyone within 7 m. Validated: a salvo on 5 enemies stopped in firing position → 332 damage.
- **Enemy mortar** from wave 4, every 35 s with enemies alive, on the largest group of 3+
  of our soldiers (2 shells, 3 s of warning, alert "MORTEIRO INIMIGO chegando").
  Balance measured with 6 soldiers in formation:
  no reaction, 3 shells of 90 = 4 dead; with an automatic escape out of the ring = 0 damage
  (they run ~18 m in 3 s); those holding position (End) or suppressed do not flee —
  3 shells = 6 dead, 2 shells of 75 = 1 dead and 5 wounded (final value). The enemy
  mortar's role is to dislodge.
- End of the salvo: those who fled and got no new order (no focus, no End) return to their spot with their own
  A* route (`routeTo`). In a straight line, 2 of 6 got stuck behind the armored car; with the route,
  a final deviation of 0.6–1.9 m from the original position. A match of 7 waves with points and mortar: no errors in the log.
- **On-screen help:** a second TextBlock in the panel widget with the keys (6 lines, font 13); it appears
  for 40 s when RTS turns on and F5 toggles it (besides logging the status). Validated in a capture: visible
  right after the autostart (`help1.png`) and hidden after the deadline (`help2_crop.png`). F5 with a real
  keyboard not tested yet.
- **Veterancy:** the shot that zeroes HP credits the shooter (`credit`); every 2 kills goes up a level
  (max. 3), +10% accuracy per level, on both sides. Alert "fuzileiro promovido a veterano 1",
  panel "sel. 6, 1 vet.", the status lists kills per soldier. Validated: a wave of 5 → credits
  1,2,1,0,0,1 (sum = 5 kills) and promotion of the 2nd rifleman.
- **Retreat (Home):** the selected run to the point of ours nearest the group (with no point, to the
  commander) with their own A* route, do not stop to fire and take half the hits
  (`CFG.RETREAT_HIT`); arriving or a new order ends it. A point of ours is an aid post: inside the ring,
  without suppression, +2 HP/s (`CFG.POINT_HEAL`). Validated: 4 wounded (50–62 HP) ~15–19 m from A
  arrived in ~4 s (the machine gunner, slower, in ~6 s) and rose ~2.4 HP/s there. Found in the test:
  the medic arrived and went out again after the machine gunner still on the way, and died; now the medic
  does not go after someone retreating.
- **New match (Shift+F6):** clears everything, a squad of 6 (`CFG.START_SQUAD`), automatic waves and three
  points; the victory/defeat alerts point to it. Validated through the channel twice in a row
  (6 soldiers, 3 points, waves on, wave 0).
- **Grenades:** a rifleman (on both sides) with the target behind low cover within 18 m throws a
  grenade instead of firing (cooldown 18 s per soldier; explodes in 1.4 s within 1.5 m of the target; damage 55
  with falloff up to 3 m, no trace — cover does not protect; suppression up to 5 m; a kill credits the
  thrower). Effect `GrenadeBlast`, sounds `GrenadePinPull_Cue` and `HELaunchedGrenadeHit_Cue` (the latter
  chosen by name, not checked by ear). Validated: 3 barriers with 4 enemies behind → 2
  grenades, 272 damage, wave eliminated (`gr1.png`); the status records throws and damage per side.
  Enemy grenade validated: 4 of our soldiers holding position behind 3 barriers, 4 enemies at
  15 m → 2 grenades, 303 damage, 2 dead. Without a visible projectile there is no way to react in 1.4 s; damage
  lowered from 55 to 45 (the text above keeps the test's original value).
  Visible projectile: mesh `/Game/FX/Mesh/Grenade01` (3×) flies in an arc (2.5 m high) from the thrower to the
  target during the fuse and vanishes on the explosion; checked in a capture with the fuse lengthened through the channel
  (`gfly2.png`: grenade and offset shadow halfway).
- On-screen help anchored at the bottom left corner: at the top it covered the game's alert box
  (`help3.png`).
- **Bot player** through the channel (`t_bot0.lua` + `t_bot.lua` every 10 s: recruits with ≥45 manpower
  at point A, mortar at the center of the enemies, keeps everyone at A; no barriers, retreat or cover):
  - old balance: won the 10 waves with 3 losses; the enemy mortar **never fired** (the clock
    reset every time a wave was eliminated, before the initial 17 s) — fixed, the clock only resets below wave 4;
  - waves 0.5→0.8 enemies/wave and ceiling 10→14: won again with 3 losses (12 soldiers = snowball);
  - + `CFG.WAVE_SQUAD_SCALE` 0.4 enemies per living soldier of ours, ceiling 16, enemy accuracy 0.6→0.7:
    lost at the 10th wave (108 kills, 31 losses; the enemy took all three points). Value kept: a
    player using barriers, retreat and cover should go beyond the bot. No errors in the log in the three matches.
- **Advancing in bounds (AI):** an enemy advancing with suppression ≥ 0.25 runs to the most
  advanced cover nearby (the same search as `seekCover`), waits 2.5 s and continues; before, it advanced straight until
  in range. Validated: 6 barriers in the way, a wave of 6 coming from 38 m → 5 bounds and 12 trips to cover
  (the status shows "lances inimigos").
  Bot with bounds: won the 10 waves with 108 kills and 22 losses (12 grenades of ours against enemies
  sheltering in the bounds). Two bot matches: one defeat (31 losses) and one victory (22 losses).
- **Bug fixed:** `focusOn(0/0)` (a test with an empty list) left the camera at NaN and the screen black
  forever — with the current position NaN, `K2_SetActorLocation` moves by a NaN delta. Now
  `focusOn` ignores NaN and `placeCamera` recreates the camera if its position is NaN (validated:
  camera forced to NaN came back to (9988,-24935,2662) with an image). `callMortar` also refuses NaN.

## 2026-10-07 (night, 13) — Control points (v0.6)

- Point = a dotted orange ring (24 small discs, radius `CFG.POINT_RADIUS` 500) +
  the owner's rolled-up banner at the center, 3× (`BannerTWPickup` blue = player/Wardens,
  `BannerTCPickup` green = Colonials; neutral without a banner). Tried before: a single
  10 m disc (cut by the relief, covered the terrain) and `FlagHanging*` materials on the disc
  (they render as a torn flag, not as a color) — discarded.
- Capture: progress in [-1, 1]; only one side in the ring pushes (1 soldier = 10 s from neutral to
  owner, up to 3 add up); both sides = contested (freezes); empty = slowly returns to the owner.
  The owner loses the point when progress crosses 0. Each point of ours yields +0.5/s of
  manpower. The enemy with all points = defeat (with automatic waves).
- Enemy AI out of combat goes to the nearest point it does not dominate yet and holds at the
  center (60% of the radius); a human enemy closer than the point still has priority.
- Shift+F4 without points creates three (front and flanks of the squad, 1400–2400 cm), on flat,
  free ground; J creates a point under the cursor (max. 5); F11 removes. Panel:
  `pontos 1/3 [A+ Bx Co]` (+ ours, x enemy, o neutral; % during capture).
- Trace findings: the Visibility channel (`groundZ`) **goes through vehicles** (Truck24);
  `LineTraceSingleForObjects` with types {WorldStatic 0, WorldDynamic 1} hits them, but
  also hits invisible `BPNoBuild_C` volumes (BoxComponent, top Z=4746) — `surfaceZ`
  ignores hits on Box/SphereComponent (cache `surfaceIgnore`) and redoes the trace.
- Validated in the game: 3 points created away from the trucks; the squad captured A in ~3 s
  (6 soldiers); wave 1 took B on the way and engaged the squad; 3 waves with A ours and B
  the enemy's, panel and banners checked in a capture (`pts6.png`).
- Bridgehead: a point dominated by the enemy more than 15 m from the squad becomes the entrance of the
  next wave (the farthest; alert "entrada pelo ponto B"). Validated: B forced to the
  enemy through the channel → wave 5 spawned at B (11529,-22835). In the same round the squad fell,
  the enemy took A and C and the defeat by points turned off the waves.
- Forward reinforcement: Ctrl+1..4 with the cursor inside a point of ours makes the recruit spawn
  there (`recruit(role, at)`; `spawnSquad(n, role, at)`). Validated through the channel: a recruit at B
  spawned ~180 cm from the center; with no point, beside the squad as before. The path through the
  cursor depends on the real mouse (not tested).
- Offline tests: progress/contest/loss/return, the enemy's objective, defeat by points,
  wave entrance through an enemy point; key J without conflict.
- Balance: base regeneration 1.5/s → 1.0/s (`CFG.MANPOWER_RATE`); with one point dominated it goes back to
  1.5/s. In the test match manpower spent most of the time at the 200 ceiling.
- A* (`kneeClear`) moved from the Visibility channel (0) to `CFG.MOVE_CHANNEL` = 1 (Camera).
  Measured sweeps: Camera hits trucks (BoxComponent), motorcycles, buildings and barriers and
  does not hit the BPNoBuild volumes; channel 4 hits vehicles but goes through the barriers;
  Visibility goes through vehicles. Route (11000,-24900)→(11000,-27900) through the row of
  trucks: before a straight line (0 nodes), now a detour through the gap (29 nodes); 4 soldiers arrived
  in <8 s (`route1.png`). Firing and cover remain on Visibility (a truck does not stop a bullet
  nor count as cover — consistent with each other).

## 2026-10-07 (night, 12) — Victory and increasing difficulty

- Automatic waves now have an end: eliminating wave `CFG.WAVES_TO_WIN` (10) = victory
  (15 s alert, panel "VITÓRIA", +30 manpower, waves turn off). Turning the
  waves back on after winning starts a new campaign (wave 0).
- Enemy accuracy ×(1 + 0.04·(wave−1)), ceiling ×1.5 (`CFG.WAVE_ACC_GROWTH/CAP`).
- The panel shows "onda X/10" with automatic waves on.
- Validated in the game: campaign started at wave 9 through the channel; the 10th (8 enemies) arrived
  after the interval and was eliminated → `won=true`, `auto=false`, alert and panel
  checked in a capture (`win_crop.png`).
- `test_orders.py`: victory at the last wave, an intermediate wave only schedules the next,
  turning back on after a victory restarts the campaign.

## 2026-10-07 (night, 11) — Medic and the 200-local limit

- Reflection on `SimCharacter`: `Health`/`MaxHealth`, `bIsBleeding` (+`OnRep_IsBleeding`),
  `BleedDamagePerSecond` 1.0, `BleedMinDamageReq` 25, `ResetWoundedStateThreshold` 85,
  `OnRep_Health`. Writing `Health` + `OnRep_Health` heals and sticks (60→90).
  Damage with one's own controller as instigator does not apply (treated as friendly fire).
- Medic class: pistol (`PistolBasic`), 30 manpower, Ctrl+4; 4th and 12th of the
  squad (enemies too). Every 1.5 s heals 12 HP and stops the bleeding of the most wounded within ≤3.5 m;
  a wounded within ≤12 m and a free medic → goes to them. In the game: a wave of 4 beaten 4×0, the allied
  medic healed 156 HP (including themself 56→90), the enemy medic 38. F5 shows the total.
- **Lua limit: 200 locals per chunk.** `main.lua` reached exactly 200 and the
  medic blew it up ("too many local variables"). The 79 top-level UPPERCASE constants
  went into the `CFG` table by a mechanical transformation (code, not strings/comments);
  ~80 locals remain. Validated in the game afterwards (autostart, camera, combat).
- `test_orders.py`: the medic heals the most wounded, stops bleeding, respects the period and walks to a
  distant wounded.

## 2026-10-07 (night, 10) — v0.5: keys without conflicts with the game

- Read the 138 default mappings (`Default__InputSettings.ActionMappings/AxisMappings`;
  `pc.PlayerInput.ActionMappings` comes as a TrivialObject). The mod's real conflicts:
  B = Build (construction menu), H = Open Callouts Menu, F8 = Toggle Interface,
  Shift+1–7 = AdminCommand1–7, left button = Fire, right = Aim, PageUp/Down =
  Spectate/Move Up (harmless outside spectator/vehicle), 1/2/3 = Equip.
- Free keys in the game (no modifier): F2–F7, F9–F12, J, K, Home, End, Insert,
  Delete. New map: recruit Ctrl+1/2/3 (Ctrl+n only switches seats in a vehicle), barrier
  K, hold End, clear F11. 1/2/3 kept (they only equip the stopped commander).
- RTS mode turns off the commander pawn's input (`DisableInput`; back on when leaving),
  so the left click does not trigger Fire. Not verified with a real mouse.
- `test_orders.py`: a regression test compares the keys registered by the mod with the
  game's mapping list (fails on any collision outside the accepted ones).
- v0.5 loaded in the lab with the new key names (banner in the log).

## 2026-10-07 (night, 9) — Building barriers (key B)

- Candidates measured by a profile of horizontal traces (40–150 cm):
  `BPSandBagWallStatic_C` blocks up to ~2.25 m (cuts line of sight; no good);
  `SandbagSmallPile_C` only ~40 cm; the yard's concrete divider is a
  `StaticMeshActor` with `OCourseDividers_01` (~2.7 m, top ~1.24 m): blocks 40–100,
  frees 130–150 = exactly the low cover of the firing model.
- `buildAt(p)`: `StaticMeshActor` + that mesh (Movable), turned to face the
  nearest enemy (without enemies: squad→point direction); costs 15
  manpower, maximum 30, refuses with a soldier within <1.8 m; F8 removes; the panel shows "barreiras N".
  Key B (not yet tested with a real keyboard; I do not know whether the game uses B in RTS mode).
- Validated in the game: 3 barriers 3.5 m from the squad before a wave of 4:
  manpower 63→18; 44 of 47 enemy shots blocked; 4 kills, 0 losses; 7 enemy A*
  routes detouring around the barriers. Capture `build7_small.png`.
- `test_orders.py`: refusals without manpower and with a soldier on the spot, without charging.

## 2026-10-07 (night, 8) — Second map (HomeRegionC) and "Code of Conduct"

- Maps in the PAK index (only the end of the file read, without extracting): `HomeRegionW`,
  `HomeRegionC`, `MainMenu` and ~40 hexes in `Maps/Master/*Hex` (+ proxies).
- Configurable lab map: 1st line of `Mods/FoxholeRTS/map.txt`
  (e.g. `/Game/Maps/HomeRegionC`); without the file, HomeRegionW. The autostart detects the
  load by the chosen map's name. Commander anchors: +`BPArmoredCarC_C`
  and `PlayerStart` as a last resort.
- **HomeRegionC validated:** local session, commander at (−7447, 15947, 230),
  recruiting, a wave of 5, combat (4 kills, 0 losses), 5 trips to cover,
  6 enemy routes, no errors in the log. Many shots blocked (145/167 allied) because
  there was a low barrier between the groups (checked in the capture `mapc1_small.png`).
  `map.txt` removed afterwards; the lab went back to HomeRegionW.
- **"Code of Conduct":** needs no action. It disappears on its own ~1 min after
  loading; it only appeared in captures taken right after relaunching. Reflection on the
  controller showed no specific function for it.
- **Large hex validated: `Maps/Master/DeadLandsHex`.** Loaded in ~17 s via
  `?listen` (4.2 GB of memory), commander at (15986, 38998, 288), a wave of 5
  beaten (5 kills, 0 losses, 1 soldier at 1 HP), no errors in the log.
  The "Introdução ao Foxhole" panel (first-time tutorial) appears on top of
  everything: it is native Slate (no UserWidget; no intro/tutorial function/property
  in the controller), no flag in the `.ini`s. It closes with clicks on the arrow, only with a real mouse.
  `map.txt` removed afterwards; lab back to HomeRegionW.

## 2026-10-07 (night, 7) — Enemies with routes

- An advancing enemy re-evaluates every 4 s: `planStart` only opens an A* if the straight line
  (line + sphere) to the nearest ally is blocked; it follows the waypoints
  and the last stretch goes straight to the living target. A global budget of 40 nodes/frame for
  all jobs; player orders go to the front of the queue.
- `enemies` is now declared before the planner; counter `routeStats`
  (F5: "rotas A* aliados/inimigos"). `check_globals.py` caught a use of `combat`
  before its declaration in the meantime.
- Measured: an enemy outside the barrier, an ally (on H) ~23 m inside the
  yard. Enemy routes = 1; the enemy went around from (8325, −27669) to
  (8969, −27360) and stopped when entering range with line of sight (17.6 m), with 1 waypoint
  still pending. Two earlier tests did not require a route (free line of sight over
  the barrier / by angle): the enemy entered combat earlier.

## 2026-10-07 (night, 6) — Paths (A*) without a NavMesh

- A march order plans a route for the group: a straight line if free; otherwise A*
  on a 1.5 m grid (margin 20 m, up to 2500 nodes), edges tested by a sphere
  sweep (radius 32 cm at 75 cm off the ground; line only on the origin/destination edges) and
  a height difference ≤60 cm per cell; arrival accepts a neighbor of the destination with a free line;
  route shortened. Each soldier follows the same waypoints (radius 70 cm) and goes to their
  spot in the formation. Without a route: a straight line with the old detour.
- Mistakes along the way until it worked (measured in the game):
  1. A line trace does not have the body's width: a route hugging the barrier passed and the
     soldier got stuck on the corner (a 120 cm waypoint radius made it worse). → sphere + 70 cm.
  2. With the sphere, a destination hugging the wall had no reachable cell. → arrival at the
     neighbor with a free line.
  3. A 12 m margin left the barrier's opening outside the search; a larger margin
     costs ~1 ms/node. A coroutine failed: **UE4SS does not accept a UFunction inside a
     coroutine** ("lua state has no instance inside lua_instances"). → A* in an explicit
     state (`planStart`/`planStep`), 40 nodes per frame; the soldier waits standing still.
- Result: from the snow (8550, −27279) to the inner corner (9000, −26500), with the barrier
  in the middle: a route of 6 waypoints in 341 nodes (~9 frames), arrival in ~4.5 s through the
  opening. Before: stuck, or arriving by luck in ~12 s.
- `test_orders.py`: a synthetic wall at X=500; the synchronous route goes around with all
  stretches free; the asynchronous flow delivers waypoints after the ticks.

## 2026-10-07 (night, 5) — Attack order and automatic cover seeking

- **Attack:** right button/F7 within 2.5 m of a living enemy = attack order
  (`m.focus`). The selected advance until they have range and line of sight, stop and fire only
  at it; on the way they fire at the nearest. March and H cancel. In the game: with two
  enemies (12 m ahead and 18 m to the right), attacking the 18 m one brought it down first.
- **Automatic cover:** an ally stopped, without an order and without H, with an enemy in range
  and exposed, searches every 2 s, in rings of 1.5/2.8/4 m, for the spot where the trace from the
  enemy's eye to the waist is blocked and to the eyes passes, the same ground (±80 cm)
  and a free path at knee height. Without the knee check it picked the
  other side of the wall (unreachable). H now holds position (`m.hold`): no search.
- Validated: a trace sweep (`t_cov10.lua` in the lab) found an exposed spot with
  shelter within ≤4 m; an ally placed at (9250, −27500) went on their own to (9204, −27075),
  next to the barrier's corner; the enemy had 3 of 4 shots blocked, 0 hits, and
  died. Capture `D:\tools\foxhole-lab\cov11_small.png`.
- Geometry finding: HomeRegionW's concrete barrier is tall (impact at
  ~1.8 m) and covers a wide strip of the yard against distant enemies.
- **Enemies also seek cover:** in firing position and not pinned by
  suppression, every 2 s they look for shelter (the same routine, against the squad); they do not
  fire while moving to it. Mirrored test (an ally on H in the snow, an exposed
  enemy): the enemy went to (9203, −27076) and the ally's shots started being
  blocked (4 of 6 in total; the only hit was before it took shelter).
- `test_orders.py`: focus only on living selected units, attacking a dead one ignored,
  march/H cancel focus, H turns on hold and a new order turns it off.

## 2026-10-07 (night, 4) — Suppression and cover

- Suppression 0..1 per soldier: every shot against them adds `weapon.supp` (rifle
  0.12, MG 0.20, sharpshooter 0.30), hit or not; decays 0.35/s. Effects: accuracy
  ×(1−0.6·s), speed ×(1−0.5·s); an enemy with s ≥ 0.7 is pinned in place
  (keeps firing).
- Low cover: with the eye-level line of sight free, a blocked trace from the shooter's eye to the
  target's waist (center −20 cm ≈ 70 cm off the ground) = target covered:
  hit ×0.5, and the missed shot kicks up dust on the obstacle. Counter
  `combat.covered` on F5.
- Validated in the game. Combat 7×6 in the open field: the enemy's suppression reached
  0.97–1.0 with it stopped; enemy accuracy under fire ~17%; cover 0 (expected).
  A duel with the enemy behind a concrete barrier (found by a trace
  sweep: S=9000,−26500 / T=8550,−27279 in HomeRegionW): the exposed ally hit
  1 of 9, with 8 blocked by the cover; the covered enemy, 0 blocked.
- `test_orders.py`: accumulation, ceiling and decay of suppression with a fake clock.

## 2026-10-07 (night, 3) — Fixed status panel on the HUD

- Foxhole's HUD is native Slate: `FindAllOf("TextBlock")` = 0; the only live UMG is
  `CrosshairWidget_C` (cursor, outside the viewport). `ClientAlertMessage` stacks
  (newest on top), it does not work for continuous status.
- Solution: `WidgetBlueprintLibrary:Create` of another instance of
  `CrosshairWidget_C`, image collapsed, a `TextBlock` created with
  `StaticConstructObject(TextBlock, WidgetTree)` and `CanvasPanel:AddChildToCanvas`,
  `AddToViewport(50)`. Font: the engine's Roboto; `tb.Font.Size = 16` applies;
  accents (ã, ç, á, —) render. Shadow via `SetShadowOffset`.
- Line: manpower, squad (selected), wave/enemies/kills/losses and
  the next wave's countdown; updates every 0.25 s only if the text changed; leaves the
  viewport with RTS off. Validated by a capture during a wave.
- Globals created in `cmd.lua` do not persist between commands (a new env on each
  execution); keep test state in the mod itself if needed.

## 2026-10-07 (night, 2) — Per-soldier selection with a marker

- Selection is now per soldier (`m.sel`). Keys 1/2/3 remain (group 1, 2,
  all). Left button: a click selects the nearest living soldier (≤150 cm);
  dragging (≥120 cm on the ground) selects by a box in the X/Y plane; Shift adds/toggles;
  a click on empty space clears. Polling of `LeftMouseButton` in the per-frame loop, because
  `RegisterKeyBind` only sees the press. New soldiers come selected if all
  already were.
- Marker: a `StaticMeshActor` with a flattened `/Engine/BasicShapes/Cylinder`
  (0.9×0.9×0.02), the game's material `BuildGhostHighlight` (orange disc), no
  collision, attached to the pawn (KeepWorld). Tried and discarded: `GrenadeAimMesh`
  visible (does not appear), custom depth/stencil (no outline in the game's post-process),
  the cylinder's default material (gray, vanishes on the ground).
- Validated in the game through the channel: a box on the 1st row = 2, Shift+click adds the 5th
  = 3; discs only on the 3 (capture); an order moves only the 3 and the discs follow;
  F10 off hides all and back on shows only the selected; the dead have their
  disc destroyed. Click/drag with a real mouse **not tested** (no access to the
  window).
- `tools/check_globals.py`: flags a name used before its `local` (becomes a nil global)
  or never declared. It caught the `spawnSquad`→`syncMarkers` case (solved with an
  early declaration). Runs in `restart.sh` before publishing.
- `test_orders.py`: selection by click/box/Shift covered.

## 2026-10-07 (night) — Decision: fully offline, our own model; v0.4

- **User decision:** no server integration; remodel the game
  offline. In practice the session is already local (own listen server + an outbound
  firewall rule). The Steam ownership check is kept (local IPC, not
  network; do not bypass DRM). Steam may stay in offline mode.
- Consequence: real rifles via `ServerTakePickup`/inventory leave the critical
  path. Weapons now belong to our model (firing profile + the game's mesh).
- **H key bug found in the game and fixed.** Measured: H zeroed the velocity,
  but 1.5 s later the soldiers had walked 6–10 m (speed up to 333). Cause: with
  friction/braking 0 (spawnSoldier), movement input already queued
  re-accelerated the pawn and `halt()` acted only once (`m.halted`). Now `halt()`
  calls `ConsumeMovementInputVector`, brakes whenever there is velocity, and the tick
  applies `halt()` to every soldier without an order. Retest in the game: identical position for
  3 s; a new order resumes the march and stops at the destination. `test_orders.py` covers the
  repeated braking (PASS).
- **v0.4: soldier classes.** Table `WEAPONS` (rifleman, machine gunner,
  sharpshooter) with range/rate/accuracy/damage/speed; the 3rd and 7th of the group are
  machine gunners, the 6th a sharpshooter. The weapon mesh goes on the character's `WeaponMesh`
  component (`SetSkeletalMesh`); Warden: `SK_RifleW`, `SK_MGW`, `SniperRifle`;
  Colonial: `SK_RifleCarbineC`, `SK_MGC`, `SK_SniperRifleC`. Validated in the game:
  composition 4/2/1 and enemies 4/1/1, machine gunner at 375 (75% of 500), combat
  6x7 ended 5 kills/5 losses; the enemy sharpshooter stopped at ~30 m stays out of the
  rifles' range (requires an advance order).
- `p.WeaponMesh` is NOT a property (UE4SS returns a TrivialObject): get the
  component by name via `K2_GetComponentsByClass`. Return arrays come as a
  Lua table of wrappers (`v:get()`), not a TArray with `ForEach`.
- **Crash (UE4SS.dll AV 0x2ace27):** a probe reading `MasterPoseComponent`/
  `AnimClass` of the `WeaponMesh` crashed the game; `pcall` does not catch an AV. Dump in
  `D:\tools\foxhole-lab\crash-v04probe\`. Do not read those properties.
- **Weapon in hand:** without reattaching, the `WeaponMesh` stays at the body's origin (rel=0,
  hidden at the feet). `K2_AttachToComponent(pawn.Mesh, "hand_r", Snap×3)` puts
  the weapon in the hand; validated by capture from spawn (Warden rifle and MG) and by
  reading on the enemies (`SK_RifleCarbineC`/`SK_MGC`/`SK_SniperRifleC` on hand_r).
  (A hasty reading of a capture inverted this earlier: the camera looks toward +X, the
  soldier at the top is the one with the highest index.)
- **Economy (v0.4):** manpower starts at 60, regenerates 1.5/s (max. 200),
  +8 per kill, +30 per wave eliminated (replaces the 2 free reinforcement
  soldiers). Shift+1/2/3 recruits a rifleman (20) / machine gunner (35) / sharpshooter
  (45). Defeat in the waves only without soldiers AND without manpower for a rifleman.
  `SQUAD_MAX` 8→12. Validated through the channel: costs deducted, refusal without charging,
  regeneration ≈1.5/s measured, bonus for 6 kills added. `test_orders.py` covers
  the refusals (no manpower, full squad, no authority).
- Not yet tested with a real keyboard: Shift+1/2/3. I do not know whether UE4SS also fires
  key 1/2/3 without a modifier (it would select a group at the same time; harmless).
- Real keyboard test via computer-use: access to the window denied by the user;
  the Shift+1/2/3 test stays with the user (script in the session's reply).
- Next candidates (done later this night: selection, panel, suppression/cover).
  Attack on a target and automatic cover also done (entry "night, 5").
  Pending: a test with a real keyboard/mouse (includes closing the introduction in the hexes).
- Enemies outside the commander's line of sight are not drawn (the game's own
  LOS, `LOSRasterComponent`): it already works as fog of war.

## 2026-10-07 — Outbound rule installed by the user and checked

- The user created `FoxholeRTS Lab - Block Outbound` in an administrator PowerShell.
- An independent check with `netsh advfirewall firewall show rule` confirmed:
  enabled, outbound, block, all profiles, any protocol/IP, the exact executable
  `D:\FoxholeLab\Foxhole\War\Binaries\Win64\War-Win64-Shipping.exe`.
- The pending network-specific rule is resolved; this check is not a
  functional test of the mod. Next tests: inventory probe and the H key.

## 2026-10-07 — Isolation re-evaluated and holder confirmed

- `netsh advfirewall show allprofiles state` worked: three profiles on.
  A rule listing filtered by Foxhole/War-Win64 found only inbound permissions
  for the official War.exe; no specific rule blocking the copy.
  There was no launch. The user was asked for an outbound rule for the lab's exact
  exe, with the command and check in UNIVERSAL_MODDER_NOTES.md.
- The assembly at 0x140a5c3e0 confirmed RCX preserved up to the call 0x140a622d0:
  the holder is passed on, contrary to what the pseudocode suggested. It is not
  evidence of acquiring the item. RIFLES_INVESTIGATION.md updated.
- The next step depends on measurement in the game: confirm isolation, run the
  inventory probe and validate H. Do not add new hooks on a hypothesis.

## 2026-10-07 — Rifles: static flow and a non-destructive diagnosis

- Resumed with a focus on real weapons, without replacing them with new simulated effects.
- Confirmed thunk -> slot +0xc20 -> wrapper -> slot +0x9d0 -> local pickup
  routine. There is an activity guard at +0x12e0 before the success path.
- Found a limitation of the vtable helper: PlayerCharacter overwrites the table
  after the base constructor; the helper returns the base one. Compared the two slots:
  same destinations, so this alone does not explain the empty inventory.
- Created `RIFLES_INVESTIGATION.md` with sources and bounded hypotheses, and
  `tools/probe_inventory.lua`, read-only, to measure the preconditions and the
  two arrays (inventory/equipment). No new RPC or flag change.
- Decompilations/PE stayed in the lab; no launch or input.
- `test_inventory_probe.py` PASS after fixing a newline escape in the test itself:
  reading the arrays, unavailable fields, an invalid pawn, refusal of non-local
  contexts. `publish check` still PASS (3 files, 0 failures/warnings).
- `um kb search inventory` revealed a UnicodeEncodeError on cp1252 stdout; with
  PYTHONIOENCODING=utf-8 it passed. Solution recorded in the tools guide.

## 2026-10-07 — v0.3.1: per-group stop and toolkit documentation

- New H key: cancels the selected units' march, zeroes velocity and detour, without
  disabling automatic combat. Exposed as `stopSelected()` in the local channel.
- New orders discard the previous detour and ignore dead/invalid pawns.
- `issueMove` and the per-frame loop now refuse a remote client, a dedicated server
  and the menu through the existing predicate. This does not replace network isolation.
- Fixed a comment that claimed pickup success: only avoiding the crash was observed.
- `tools/test_orders.py`: passed syntax, selection, stop, resume, the H key with
  RTS inactive, dead/invalid, an empty squad and authority locks, via lupa 2.8.
  These are mocks; physics, real input and combat after a stop still need an in-game test.
- Skills used: mod-any-game, reverse-engineering, game-automation and the Unreal playbook.
  `um kb search foxhole` recovered the note; `um publish check` initially flagged a
  missing README; README added to the package.
- Usage/evaluation guide: `UNIVERSAL_MODDER_NOTES.md`, with commands and limitations.
- No War process found. The firewall query was denied by Windows;
  isolation could not be confirmed. I did not relaunch, did not copy v0.3.1 to the lab
  and did not use input. Next step: confirm isolation and follow the guide's H test.
- Real rifles remain pending; do not repeat t_pk3 as if it were a solution.
- Final check: `um publish check` PASS (3 files, 0 failures/warnings).
  `um kb check --index` FAIL: outdated global index (60 notes checked);
  recorded in the guide without modifying the shared base.

## 2026-10-06 — Initial planning

- Goal: investigate and develop a mod that lets you play Foxhole as an RTS.
- User preference: build the necessary tools in the mod itself; do not automatically replace the proposal with an independent game.
- Folder: `D:\GitHub\foxhole-rts`.
- Support toolkit: `D:\GitHub\universal-modder`.
- Game installation in progress, as the user reported. Path and version not yet verified.
- No game file changed, loader installed or in-game test performed.
- Search in the local base: `python -m um kb search Foxhole` found no notes.

### Evidence and current limit

The official FAQ consulted states that Foxhole is online multiplayer, offers no single-player with bots and has no official mod support; it mentions visual mods with no in-game advantage.

Source: https://www.foxholegame.com/faq (consulted on 2026-10-06).

This does not prove a conversion is technically impossible, but it does not prove a route to an RTS either. We still need to demonstrate an isolated, authorized environment with control of the simulation. Do not assume that a private server, SDK or offline mode is available.

### Next action

When the user confirms the installation has finished, locate and inspect the game in read-only mode. Follow `FIRST_STEPS.md`.

### Open decisions

- ~~Desired experience~~ → **solo against AI** (decided on 2026-10-06).
- ~~Per-soldier or per-squad control~~ → **per squad** (decided on 2026-10-06).
- Technical route and availability of an isolated test environment.

### Work limits

- Do not interfere with official servers nor bypass anti-cheat, DRM or ownership checks.
- Ask for authorization before installing loaders, driving mouse/keyboard, changing the registry or publishing.
- Back up before changes and modified launches.
- Keep decompilations and extracted assets outside the repository; do not redistribute game files.

## 2026-10-06 — Installation finished and first inspection

- The user confirmed the installation finished.
- A read-only scan located `D:\SteamLibrary\steamapps\common\Foxhole` (Steam 505460).
- Manifest build: `25730371`; engine signature: `UE4+Release-4.24`; two PAKs detected.
- No loader or anti-cheat detected by the scan; absence of detection does not mean absence of protection.
- Local `Foxhole` and `War` directories in LOCALAPPDATA not found; saves/config/logs not confirmed.
- Created `MODDING_PLAN.md` with evidence, limits and next checks.
- We did not open nor change the game. The feasibility of the RTS simulation remains undemonstrated.

## 2026-10-06 — Research for an isolated environment

- Inspected file names and the NonUFS manifest: no separate server/editor executable identified.
- Confirmed one gameplay package in `War\Content\Paks`; the scanner's generic count does not equal gameplay-only packages.
- Consulted primary sources: the official FAQ, War API, FDE and the texture tutorial.
- War API is for queries; FDE extracts data, it does not host the game. None of these tools solves the RTS simulation.
- Result: an offline/controlled route not found yet. Do not confuse absence of evidence with impossibility.
- Details and a suggested question to the developers recorded in `ENVIRONMENT_RECON.md`. No message sent and nothing published.
- Next step: clarify the availability and authorization of an isolated environment before instrumenting the client.

## 2026-10-06 — Round 2: investigation with parallel agents

- Four agents, all read-only:
  - Sonnet: local recon;
  - Opus: static analysis of the executable;
  - Sonnet: web research;
  - Haiku: the toolkit's KB.
- **Main finding:** `War-Win64-Shipping.exe` is a Game target, with server code compiled in: login/join, `UWorld::Listen`, `?listen` assembled by the game, `ASimGameMode`, `UWarReplicationGraph`, `UServerSettings` (`IsCommunityServer`, `bAllowMods`), `EWarServerType::Training`.
- **Likely blocker:** dependence on `FExternalWarService` (auth, profiles, travel, war config).
- **Protection:** no EAC/BattlEye/EOS. There is VAC and in-house detection. PAK with an open index and no signature.
- **Public research:** confirms no offline mode, bots, private server, SDK or Workshop. Visual pak mods are common practice.
- **Ghidra:** was not installed (the old setup on `G:` was gone). With the user's authorization, installed:
  - Ghidra 12.1.2 in `D:\tools\ghidra`;
  - GhidraMCP 5.14.2 (extension + bridge with a venv) in `D:\tools\ghidra-mcp-v5.14.2`.
- The user re-registered the `ghidra-mcp` MCP pointing at D:.
- Headless automatic analysis in progress in the project `D:\tools\ghidra-projects\Foxhole`.
- Nothing executed, injected, extracted or changed in the game.
- **Next step:** decompile the `?listen` path and `ASimGameMode` ↔ `FExternalWarService`, and decide the normative route with the user. Details in `ENVIRONMENT_RECON.md` (Round 2) and `MODDING_PLAN.md`.

### Discussion: normative route (proposal pending)

- The user proposed authenticating online and then going offline, or "seguir como pudermos" (go on as best we can), since the mod is distributed without the game's files.
- Proposal recorded, still waiting for the user's ok:
  - ownership stays verified by Steam, unmodified;
  - the modified session never contacts Siege Camp;
  - a local stub of `FExternalWarService` only for the local session;
  - local server without VAC;
  - mod inactive outside RTS mode.
- Rejected "auth online then offline": a modified client talking to the official backend is the biggest ban risk.
- First Ghidra item: confirm where the listen server decides Steam secure/insecure (VAC) and what it requires of `FExternalWarService`.
- The user approved the normative route on 2026-10-06. Next: decompilation in Ghidra (listen server VAC, FExternalWarService dependencies).
- The user decided: solo mode against AI, per-squad control. Implication: the mod needs its own opposing AI and squad leaders commanding soldiers via AIController/BehaviorTree (UE runtime present in the binary).

## 2026-10-06 — Round 3: route documentation and lab (user away)

Goal of the round: document how to make the mod (route, limitations, paths) and test whatever was possible. The validation was done by the agent.

### Done and verified
- **`HOW_TO_MAKE_THE_MOD.md`:** main document with the route, a layered architecture 0–5, limitations, lab rules, test protocol T0–T9 and answered/open questions.
- **PAK index** (Sonnet agent): 25,898 entries, 0 compressed/encrypted, SHA1 checked.
  - 316 maps; there is no training/test map.
  - `HomeRegionW` (48 MB) is the smallest playable one.
  - The maps use `DefaultGameMode = SimGameMode` (name table read by me).
  - There is no `RecastNavMesh` in the maps.
  - There are no soldier AI assets.
  - Outputs: `D:\tools\foxhole-lab\pak-index.tsv` and `pak-config-excerpts.txt`.
- **Ghidra:** auto-analysis finished (57 min); script `DecompStrRefs.java` to decompile by string or address.
- **Facts decompiled and validated by me:**
  - `UWarGameInstance::StartGameInstance` skips the `MainMenu` when the command line has `/Game/Maps/`.
  - Steam server init: `eServerMode = 2 + bVACEnabled`. On a client it only starts with `bInitServerOnClient`/`OSS.SteamInitServerOnClient` (strings confirmed).
  - Embedded `BaseEngine.ini`: `bVACEnabled=1`.
  - Profile in `PostLogin`: the HTTP request is assembled, but only sent (`ProcessRequest`, vfunc `0x88`) with `GetNetMode()==1`. This is the host's real blocker in a `?listen`.
  - `AHeadlessPlayerController::PlayerTick` moves `ASimCharacter` with `AddMovementInput` (vfunc `0x720`). Route for soldiers = extra local players.
- **Facts from the Opus agent** (not individually revalidated):
  - dedicated unreachable in this exe;
  - `AOfflineCharacter` is an `AActor`, discarded;
  - `Login` only requires a reservation if `bCheckReservationsOnLogin`;
  - list of FParse switches.
- **Lab:**
  - copy in `D:\FoxholeLab\Foxhole`: 97 files, 26,035,003,749 bytes, identical;
  - `steam_appid.txt` in the copy;
  - `tools/lab.ps1` with `check` and `prepare` run; `vac-off` tested in 4 cases in a temporary folder;
  - Steam installation confirmed without a loader.
- **Mod:** skeleton `mod/FoxholeRTS/Scripts/main.lua` (local players route + `AddMovementInput` fallback). Written, **not run**; a Lua syntax check was not possible.

### Blocked by auto mode (user's decision)
- Launching the game (`um win launch`), even the original client: blocks T0–T3.
- Downloading UE4SS: blocks T4–T5.
- Adding `bInitServerOnClient=False`/`bUseSplitscreen=False` to `lab.ps1`.
- A detailed specification of the profile stub (T6).
- Editing `~/.claude.json` (the user re-registered the MCP manually).

### Next step (with the user present)
T0 → T1 → T2/T3 of the protocol in `HOW_TO_MAKE_THE_MOD.md`. The T2 log confirms whether the host stalls on the profile, as predicted. Then decide the profile stub (T6), UE4SS (T4–T5) and the first soldier (T7).

## 2026-10-06 (night) — First tests running

- **T0 OK:** the original client opened through Steam and reached the menu.
  - Log in `D:\tools\foxhole-lab\T0-War.log`.
  - Steam SDK 1.51; "Steam User is subscribed 1" and "Steam Auth Enabled".
  - No "Initializing Steam Game Server", which matches the VAC analysis.
- **Correction:** the config and log are in `%LOCALAPPDATA%\Foxhole\Saved\`, not in `War`. `tools/lab.ps1` was fixed; `lab-ini` writes `bInitServerOnClient=False`, `bVACEnabled=False` and `bUseSplitscreen=False`.
- **T2 failed (no conclusion about `?listen` yet):** the `D:\FoxholeLab` copy launched directly with `/Game/Maps/HomeRegionW?listen -log` went to the **menu**.
  - Likely cause: the log shows "SteamAPI failed to initialize, conditions not met" and "[AppId: 0] Client API initialized 0". Without Steam, the `SteamSocketsNetDriver` does not listen, `?listen` fails and Unreal goes back to the default map (menu).
  - It also violates rule 1 (ownership verified by Steam), so it must be solved anyway.
  - Attempts that did not solve it: `steam_appid.txt` (505460) in the exe's folder; variables `SteamAppId`/`SteamGameId`; launching outside the sandbox.
  - Logs in `D:\tools\foxhole-lab\T2a-War.log` and `T2b-War.log`.
- **Next step:**
  - Decompile the origin of "SteamAPI failed to initialize, conditions not met" to see the exact condition (output in `D:\tools\foxhole-lab\decomp4\`).
  - Alternatives to test:
    - launch the official installation through Steam with launch options (no mod, only to validate `?listen`);
    - use the copy's `War.exe` instead of Shipping;
    - check whether Steam requires the exe to be in the installed folder.
- The config backup created by the toolkit ended up in `%USERPROFILE%\.universal-modder\backups` (0.1 MB); move it to `D:`.

## 2026-10-07 — Stable local session and the host's first character (autonomous work)

- **Cause of the Steam init:** the earlier failure came from the Steam client being closed. With Steam open and logged in and the `steam_appid.txt`, the copy initializes Steam normally. `lab.ps1 run` now refuses to launch without Steam.
- **T4 OK:** UE4SS 4.24 loads in Foxhole (only in the copy). The Lua mod `FoxholeRTS` runs.
- **The command-line map is ignored in shipping:** `UGameInstance::StartGameInstance` (0x142576600) uses an empty URL. The session is opened by the mod with `GameplayStatics:OpenLevel(world, "/Game/Maps/HomeRegionW", true, "listen")`, in autostart mode when `autostart.txt` exists.
- **Crash T2c:** stack overflow in `SimPlayerController:ClientStartRespawnTimer`.
  - The impl (`FUN_140b97950`) calls the Client RPC when `Role==Authority`; on the local host this recurses.
  - **Fix** (Lua hook): on the nested call, `Role` temporarily goes to AutonomousProxy.
  - Validated in T2d: no crash, session stable for minutes.
  - The copy's crash reporter disabled (`CrashReportClient.exe.disabled`).
- **T2 OK:** `HomeRegionW` in listen, `IsServer=true`, local `SimGameMode`, ports 7777/15000 on SteamSockets.
- **Command channel** (`D:\tools\foxhole-lab\cmd.lua` → `cmd.out`): the mod runs the file on the game thread every 1 s. Allows testing without restarting the game and without a keyboard.
- **Host without a character — real diagnosis:**
  - The PC stays in `Spectating`, `bPlayerIsWaiting=true`, `TeamId=-1`, without a kick and without "Unable to load Profile".
  - `ServerRespawnDefault` does nothing.
  - `GameMode:RestartPlayer(pc)` creates the `Character_C`, but at a spot without ground: it falls from Z 2373 to -14 and dies from the fall.
- **T6 worked around without a profile stub:** `GameMode:RestartPlayerAtTransform(pc, transform)` beside one of the map's vehicles (armored cars at ~10789,-24935,256) gives a stable character: HP 100, `Playing`, `PlayerCharacterMovementComponent`, MaxWalkSpeed 500.
- **Soldier via `SpawnAIFromClass(Character_C)` (route B):** spawns without a controller (the class does not define `AIControllerClass`).
  - With `AIControllerClass=AIController` + `SpawnDefaultController`, it walks via `AddMovementInput`, but slowly: input arrives every 50 ms and the CMC brakes between frames. It needs per-frame input.
  - Shortly after it was unpossessed and parked at (0,0,0), with HP 100. The game seems to collect characters without a player/PlayerState.
  - Route A (local players with `SimPlayerController`) becomes the main one.
- **Route A (`CreatePlayer`) crashes:** ~1 min later, `EXCEPTION_ACCESS_VIOLATION` reading 0x224 at 0x140f06595, inside `FUN_140f00b60`, which builds the `SGeneralOptionsWidget` (options UI) for the new local player. Each local player pulls in the whole UI.
  - Route A discarded.
  - Next route: `HeadlessPlayerController` (exists in `/Script/War`) spawned without a LocalPlayer.
  - Crash in `D:\tools\foxhole-lab\crash-T7a\`; new parser `dmp_exc.py` (exception + stack sweep).
- **universal-modder tools in use:**
  - `um backup` (in `lab.ps1`), `um win shot` (GPU capture), `um win drive` (input), `um win kill`.
  - `um win setup` installed into `%LOCALAPPDATA%\universal-modder`; moved to `D:\tools\um-win` with a junction at the old path.
  - **Toolkit improvement:** `um win drive --title <regex>` and `WinDrive.ps1 -Title`, to pick the game window when the process's main window is another one (here, the UE4SS console).
- **Black screen on the host (under investigation):**
  - The HUD appears (weapon, compass, world labels), but the 3D world does not.
  - Tested without effect: post-processing (PPVs, the camera's `PostProcessComponent`, the character's `LOSPostProcess`), our own camera up high, an engine cube, window focus, `bDisableWorldRendering` (byte at `viewport+0x6C`, bit 4 = 0, i.e. not disabled).
  - The `Draw` is the engine's (vtable slot 4 = 0x142556b20).
  - The minimap's orthographic `SceneCapture2D1` renders the terrain normally. A perspective `SceneCapture2D` comes out empty (max depth).
- **Black screen solved:** the scene was being rendered (`WasRecentlyRendered`=true; a `SceneCapture2D` showed the Wardens' base with vehicles and buildings). The cause was the **camera fade stuck on black**. Fix: `PlayerCameraManager:StopCameraFade()` + `SetManualCameraFade(0, black, false)`.
  - In shipping the `ShowFlag.*` cvars read back but have no effect; they are useless for diagnosis.
  - In one run the UI stayed on the waiting screen ("Foxhole Airborne"); `SimPlayerController:ClientGotoScreen(0)` (`ESimScreen::HUD`) solves it.
- **RTS camera:** a `CameraActor` as the view target, with pitch -60, shows the base from above. Validated by capture.
- **Soldiers — the route that works:** `HeadlessPlayerController` spawned without a LocalPlayer, plus `PlayerInput` (`StaticConstructObject`) and `RestartPlayerAtTransform`. After possession: `bIsLocalPlayerController=true` and `SetMovementMode(Walking)`.
  - If the local flag is turned on before possession, the pawn spawns with `MovementMode=None`.
  - The `AIController`'s pawn is unpossessed and parked at (0,0,0) after ~20 s; the `HeadlessPlayerController`'s stays stable (tested for 20 s).
  - Movement: `AddMovementInput` every frame (`LoopInGameThreadAfterFrames(1)`); they walk at 500 u/s and arrive in formation. Validated by position and capture.
- **Crash v0.2:** `GameThread` inside `UE4SS.dll` (read at 0xffffffff), with `LoopAsync`(33 ms) + `ExecuteInGameThread`. All loops moved to `LoopInGameThreadAfterFrames`/`LoopInGameThreadWithDelay`.
- **Mod v0.2.2** (`mod/FoxholeRTS/Scripts/main.lua`):
  - autostart → local session → commander on firm ground → fade zeroed → HUD → RTS camera;
  - F6 squad; right button/F7 moves to the cursor; F8 clears; F2 centers; PageUp/PageDown zoom; arrows pan; F3 edge pan; F10 toggles RTS.
- **Teams and combat (investigation):**
  - `EFactionId`: Colonials=0, Wardens=1, NoTeam=255. `SimPlayerController:ServerJoinWar(1)` puts the `PlayerState` with the Wardens; the already existing pawn stays 255.
  - Characters spawn without equipment.
  - Activities in `ECharacterActivityState` (Firing=3, Reloading=4, ...).
  - `ItemHolderComponent:ClientImportItem` is a client RPC and does not change the server's inventory.
  - Current attempt: spawn `BPRifleWPickup_C` and call `SimCharacter:ServerTakePickup`.
- **Toolkit:** `um win drive` gained `--title` and the `min` command; a knowledge base note in `universal-modder/knowledge/games/foxhole/` (passes `um kb check`).
- **Picking up an item (`ServerTakePickup`):** recursed on the host (stack overflow, crash in `crash-pickup\`). A recursion-breaking hook (at depth ≥ 2 the argument becomes nil) avoids the crash, but the item still does not enter the inventory. A real weapon is still under study (static RE agent).
- **Combat v0.3 — validated running:**
  - Teams: `PlayerState.TeamId` written directly + `pawn.TeamId` + `OnRep_TeamIdNotify` + `BPSetTeamVisuals(team)`. (`ServerJoinWar(0)` on an HPC left the PlayerState at 1; writing directly works.)
  - Simulated firing: `GameplayStatics:ApplyDamage(target, 34, shooterHpc, shooterPawn, nil)` (HP drops; death at HP ≤ 0), range 22 m, rate ~1.6 s, hit chance 60% falling with distance, the enemy with 75% of the accuracy.
  - The game's own effects: `SpawnEmitterAtLocation` (8 args in 4.24: ..., bAutoDestroy, PoolingMethod, bAutoActivate) with `/Game/FX/RifleMF` (flash), `BloodSplat` (hit), `SimpleRifleImpact` (miss); `PlaySoundAtLocation` with `/Game/Audio/SFX/Weapons/RifleShot_Cue`.
  - Line of sight: `LineTraceSingle` eye to eye ignoring both pawns.
  - Enemy AI: advances to the nearest ally, stops at 80% of range with line of sight and fires; sidesteps when stuck (e.g. between the parked motorcycles).
  - Automatic waves (Shift+F4): 15 s between waves, +2 reinforcement soldiers per wave won (max. 8), the wave grows 0.5/wave, arrival point 35 m away at an angle with ground at the squad's height; defeat when the squad falls.
  - HUD messages: `SimPlayerController:ClientAlertMessage(str, seconds)` (top left corner). `ClientAdminMessageUnformatted` writes to the chat.
  - Verified by log and capture: wave 1 eliminated (4 kills, 1 loss), reinforcement to 5, wave 2 from another direction; alert "onda 1: 4 inimigos vindo de baixo" visible.
- **Balance (measured with per-side counters):** the game holds the character at **1 HP** (wounded, bleeding) before death; killing requires one more hit. The enemy does not fire while walking, takes 0.8 s to aim when stopping, accuracy 60% of the allied. A typical match without micro: wave 1 allies 35 shots/12 hits/381 damage against 17/3/97; a stationary squad wins 2 waves and falls on the 3rd (10 kills, 8 casualties). Stable for ~4 min of waves, process responding.
- **Fire groups:** soldiers alternate between group 1 and 2 at spawn; keys 1/2/3 select group 1, 2 or all; the move order only applies to the selected, in their own formation. Validated by capture (group 1 walked, group 2 stayed).
- **Protections:** `isLocalAuthority` refuses the main menu (the menu is also a standalone "server" and the pawn there is not a `Character`; it gave "compare number with TrivialObject").
- **UE4SS hot reload (Ctrl+R) froze the game** on the session's 4th reload: process "Not Responding", CPU idle, no callback on the game thread (not even a key). The first three worked. We switched to restarting the game (`D:\tools\foxhole-lab\restart.sh`: checks syntax, publishes, kills the copy by PID, `lab.ps1 run`, waits for RTS; ~1 min).
- **User test (2026-10-07):** with the right button on the ground, the soldiers walked to the clicked point. The move order was validated by hand, outside the automation.

### How to resume (historical state of batch 17; priority updated on 10/10)
- **Current priority:** develop logistics; the user postponed crashes/the yellow effect. Batch v4.1 integrated,
  29/29 PASS offline, experimental queue preserved. Do not repeat the manual 1/2 gate as a feature blocker.
  The build is not stable. The old items below are context; check the new entries at the top first.
- **Update 10/10:** work resumed on a new request. Read the new entries at the top first:
  repeated A/B controls, 620 s selected and 100 cycles/20 deaths passed with source 33D6C7E5.
  The old native cause not isolated; the logistics candidate v4.1 remains separate/unpublished.
  The user may do a real-input gate after the rehearsal; lab closed, agree on the start.
- **Where we are:** `ROADMAP.md`. Phase 1 (small front) done; phase 2 (study, `MECHANICS_STUDY.md` + `data/`)
  with the first reading done; **phase 3 in prototype, now with a short chain validated in CallumsCapeHex**,
  not just in the lobby. Alt+L deploys real installations/trucks with a wallet of 1100, validates ground/clearance and rollback.
  In 65.21 s it produced three crates and delivered ammo/shirts, with three intact trucks; without waves/starting
  stock, NOT a balance test. Data: `data/trace_deployment.txt` and the top of this diary.
- **First thing when resuming:** respect the pause; only work after a new request. The full outline was approved
  visually, but two UE4SS crashes after extending it to the parts and the Lua Registry error remain pending.
  Read `data/trace_selection.txt`, reproduce/isolate by component/GC/reselection before new features.
  The experimental source still has the outline on; do not present it as a stable build. Lab closed.
- **Next steps of phase 3 (after stability):** trucks following the road
  discovered per region (today they go straight, without collision, through
  buildings); more crate types (weapons, grenades, medic; costs already in `data/game_costs.txt`); a more complete enemy
  chain; maybe replace "manpower" with material. Then: phase 4 (vehicles as units).
- **Construction contract:** `data/trace_rebuild.txt`. An active refinery/factory can spawn at the native
  transform with correct HP/base class, but a raw construction site has no target; native completion was not validated.
  Costs fixed: 400/400/100 bmat. Explicit budget/rollback/surface/clearance implemented in batch 17:
  `groundZ` may hit a roof; `SpawnActor` may return an actor already being destroyed; total bounds include volumes.
  Do not confuse our own deployment with native completion of a construction site/facilities. Nothing persists in the save yet.
- **Current mod:** v0.9 in `mod/FoxholeRTS/Scripts/main.lua` (~4800 lines, 178 top-level locals out of 200: new functions
  in tables `rts`, `fort`, `sv`, `logi`, `anim`, `ai`; constants in `CFG`, state in `S`). Controls and
  mechanics in `mod/README.md`; keys also in the load banner. Direction: **fully offline**, our own systems.
- **Publish and test:** `bash D:/tools/foxhole-lab/restart.sh` (syntax + `tools/check_globals.py` + copy +
  restart + wait for RTS mode). Do not use UE4SS's Ctrl+R.
- **Offline tests:** `PYTHONPATH=D:/tools/pylibs python tools/test_orders.py` (lupa; includes a key check against
  the game's mappings, read from `InputSettings` live; accepted overlaps are pawn actions, off in RTS).
  Also `tools/test_costs.py` and `tools/test_inventory_probe.py`; export costs live with `tools/export_costs.lua`.
- **Live commands:** `sh D:/tools/foxhole-lab/run.sh <file.lua>`; output only through `out(...)` (not `return`).
  The channel sees the `env` table of `runCommandFile` (includes `CFG`, `S`, `logi`, `rts`, `combat`, `squad()`,
  `enemies()`...). Do not use the channel with the bot running.
- **Regression bot:** `sh D:/tools/foxhole-lab/botloop.sh` in the background; log `botrun.log`; wait with
  `until grep -q "auto<TAB>false" botrun.log` (grep -P does not work in Git Bash). TaskStop does not kill `sh.exe`:
  `Get-CimInstance Win32_Process` filtering on `botloop.sh`. Latest results: batch 12 victory in the 10 waves
  (111/24); batch 13 defeat at wave 10 (83/38).
- **Game data:** pak index (file list) and tables (`DataTable:ForEachRow` only on known columns; a
  generic dump crashed the game on `BPAirDynamicData`). The client has the world's 54 regions (`Maps/Master/*Hex`).
- **Capture:** `cd D:/GitHub/universal-modder && UM_HOME=D:/tools/um-home python -m um win shot --title '^War' --scale 0.5 <output.png>`
  (the camera looks toward +X: top of the screen = larger X, right = larger Y).
- **User's pending items:** the other tests with a real keyboard/mouse (`MANUAL_TEST.md`); full look approved
  in this session, without certifying the integration of all keys nor prolonged stability.
- **Interface requested by the user** (`ROADMAP.md`, "Interface and visual feedback"): a visible selection box when
  dragging; silhouette/outline on the selected (the game has `M_OccludedOutline`); more UI when it makes sense.
- **Death fixed (batch 14):** `ApplyDamage` zeroed HP without notifying the visual death on the host. `reap` now
  removes markers/cache, stops and restores movement, then calls `OnRep_Health` (native ragdoll). Contract
  measured in `data/trace_death.txt`; do not access the AnimInstance after the notification nor the body after the TTL.

## 2026-10-07 — Resumed with universal-modder

- Consulted `mod-any-game`, `reverse-engineering`, `game-automation`, the Unreal playbook and the Foxhole note via `python -m um kb search foxhole`.
- The second startup reached the menu and then `HomeRegionW`, with `modo RTS ligado`, local authority and a commander with HP 100. Capture checked: `D:\tools\foxhole-lab\continue-world_small.png`.
- Correction of the initial diagnosis: `Responding=False` during loading did not prove a deadlock. In this run the menu appeared about 74 s after the mods started; RTS was ready about 95 s later. Do not restart based on that indicator alone.
- Ran `t_pk3.lua` through the local channel: rifle and ammo spawned with valid CodeName/StackSize/PickupCDO. `ServerTakePickup` returned without error with `bIsLocalPlayerController=false`, but both pickups remained and `ItemHolderItems` stayed empty. The local flag hypothesis did not solve the acquisition; real rifles remain pending.
- No change to the official client or the mod's code in this check.
