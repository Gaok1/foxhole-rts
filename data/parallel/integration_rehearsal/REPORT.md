# ENSAIO_INTEGRACAO (integration rehearsal) — complete patch stack, offline (2026-10-09)

Agent ENSAIO_INTEGRACAO. I assembled the stack ECONOMIA → IA_LOGISTICA → INTERFACE (rebased) → PERSISTENCIA over a
**copy** of `main.lua` and ran the whole battery against it. **Nothing was applied** to the real `main.lua` (SHA256
`33d6c7e5920a3b5e00b7f3bafbc7b8a86c984db810217241a567afe0901ee679` before and after, checked in the build and at the end of the
tests). I did not touch shared docs, other agents' folders, the lab, the game, the channel, nor keyboard/mouse input.
From the other builds I only imported the pure functions `build`/`build_on` (no bytecode, without running the `__main__` blocks),
so nothing was written outside this folder.

**Honest state:** the stack **composes and passes the whole offline battery**. That does **not** mean ready to play:
nothing here proves Unreal physics, route, UMG, input, performance, balance nor a real on-disk save.

(The panel samples below are in-game text and stay in Portuguese, as the mod's UI is in Portuguese.)

## 1. Final order and why

```
real main.lua (ESTABILIDADE already integrated)
 1. ECONOMIA        data/parallel/economy/build_patch.py        build(text)
 2. IA_LOGISTICA    data/parallel/logistics_ai/build_patch.py    build(text)[0]
 3. INTERFACE       REBASED panel (build_pilha.interface_build): replaces the whole logi.hudLine function
 4. PERSISTENCIA    data/parallel/persistence/build_patch.py    build_on(text)
 (ESTRADAS: not applied)
```

- **ECONOMIA before INTERFACE.** ECONOMIA's generator anchors on the end of the original `logi.hudLine`
  (`table.concat(deps, " | "), foe)\nend`) and injects `logi.extraHud()` there. The original `painel.patch` erases that anchor.
  Reproduced in step 10 of the test: `painel.patch` applies alone on the current main, but ECONOMIA's `build` after it
  fails with "âncora não única ... table.concat(deps". With ECONOMIA first, `extraHud` (inserted *before*
  `hudLine`) survives the function swap.
- **AI before PERSISTENCIA.** The AI anchors on the original `sv.load` line (`pcall(logi.restore, d.logi)`), which
  PERSISTENCIA removes; `build_on` already recognizes the AI variant.
- **AI and INTERFACE commute.** Since the rebased panel replaces the *whole function* by text boundaries, the order
  ECONOMIA → INTERFACE → AI → PERSISTENCIA produces **exactly the same text** (step 11). I chose AI first because that is
  how the AI tested it and because it lets its optional HUD anchor be consumed (and then discarded by the swap).
- **ESTRADAS left out.** No integrable driver; I only confirmed nothing in the stack breaks the contract (section 5).

### Deliverables in this folder

| File | What it is |
|---|---|
| `build_stack.py` | assembles the stack in memory (unique anchors, stops at the first error with a clear message: `ETAPA <nome> FALHOU`), writes the files below, checks the real main's SHA256 |
| `candidate/main.lua` | complete candidate, **CRLF** like the real one (315,531 bytes, 6245 lines, +1172 over the real one's 5073) |
| `candidate/SHA256.txt` | SHA256 of the real main before/after (equal) and of the candidate |
| `stack.diff` | unified diff **real main → candidate**, in **CRLF** (applies directly on the real `main.lua` with `git apply -p1`/`patch -p1`; tested: reproduces the candidate byte for byte) |
| `stack_lf.diff` | the same diff in LF, for reading only |
| `painel_rebase.patch` | INTERFACE step: `main+ECONOMIA+AI` → `+rebased panel` (LF, 80 lines) |
| `test_stack.py` | complete battery (17 steps); detailed output in `test_output.txt` |
| `test_output.txt` | captured output of the last run |

> **Update:** there is also the **v2 stack** (section "Stack v2" at the end of this file; `candidate_v2/`, `stack_v2.diff`).
> Everything before it describes the v1 stack, which stays reproducible.

Reproduce (bash, repo root):

```bash
PYTHONPATH=D:/tools/pylibs PYTHONDONTWRITEBYTECODE=1 python data/parallel/integration_rehearsal/build_stack.py
PYTHONPATH=D:/tools/pylibs PYTHONDONTWRITEBYTECODE=1 python data/parallel/integration_rehearsal/test_stack.py
```

Build steps (+/- lines over the previous text): ECONOMIA +203/-65, IA_LOGISTICA +516/-45, INTERFACE +52/-16,
PERSISTENCIA +582/-55.

## 2. Conflicts found and how they were resolved

1. **ECONOMIA × `painel.patch`** (known): the anchor `table.concat(deps, " | "), foe)` disappears. Resolution: order
   (ECONOMIA first) + panel rebased by whole function, not by line context.
2. **`painel.lua` without the reconciliation.** `painel.lua` does not call `extraHud`, does not know ECONOMIA's `returnCargo` state and
   read `combat.cargo` on the enemy line. The rebase applies, with unique and fail-closed anchors, the 4 hunks of
   `interface/reconciliation_extraHud.patch` (`returnCargo` name/destination; `cargo.ammo/shirts or 0`; optional call
   to `logi.extraHud`) **and two changes of mine** (listed below for the coordinator to review):
   - INIMIGO line: if `logi.eHud` exists (AI integrated), it uses its line ("INIMIGO: frente equipa N ... comboios ...
     perdidos"); otherwise it keeps the old line `INIMIGO | carga N`. Reason: with the AI, `combat.cargo` became an alias of
     "soldiers the front equips" and the old line would show a number without its former meaning (the AI itself recommended
     using `logi.eHud()`). An empty `eHud()` (no chain) produces no line. In assault there is still no enemy line.
   - truck cargo: adds ` + N fuzis` / ` + N bandagens` when they exist (without it a truck with only rifles
     showed up as "0 munição + 0 camisas (caixas)", misleading).
3. **Mixed line endings in the delivered `.patch` files:** `economy_integrated.patch`, `logistics_ai.patch`, `painel.patch` are
   in **CRLF** (written with `write_text` on Windows); `persistencia*.patch` and `reconciliation_extraHud.patch` in LF. The
   `main.lua` is CRLF. So a direct `git apply` fails for half of them depending on the file. My test normalizes
   to LF and applies in sequence; **result byte for byte equal to the candidate** (step 10). I recommend applying through
   `stack.diff` (CRLF, applies on the real main) or copying `candidate/main.lua`, not chaining the `.patch` files by hand.
4. **`economy/test_existing.py`** runs `tools/test_orders.py` against ECONOMIA's build **without** swapping the "enemy
   convoy" block; with the AI integrated that old block no longer holds (the AI removed the abstract contract `cargo0/perWave/cut`).
   Replaced in the battery by running `test_orders.py` with the block from `logistics_ai/test_orders_convoy_block.lua`
   (step 03b). I did not run `test_existing.py` nor `economy/test_economy.py` (pure module `economy.lua`, which ECONOMIA
   itself says **not** to load together with the integration).
5. **`sv.enemySnapshot` × AI:** returns `nil` when `logi.eSnapshot` exists (the AI owns the enemy state through `elogi`).
   No conflict; but the counters `combat.convoys`/`combat.convoysCut` (display only) are **not** persisted in the
   stack with the AI and go back to 0 on continue. The source of truth (`led.lost`, ledger) is saved. Cosmetic.

No other anchor conflict between ECONOMIA, AI and PERSISTENCIA (they had already been composed by them; reconfirmed).

## 3. Top-level local count (limit 200 per chunk)

| Measure | real main | candidate |
|---|---|---|
| Compiler (Lua 5.4 = UE4SS **and** 5.5; largest number of extra locals that still compiles) | **178** active (22 headroom) | **178** active (22 headroom) |
| Regex count of `tools/check_globals.py` (warning limit: 180) | 175 | 175 |

No stack step (ECONOMIA, AI, INTERFACE, PERSISTENCIA) added a top-level local: everything in `logi`, `sv`, `CFG`.
`check_globals.py` on the candidate: **rc=0, no output at all** (not even top-level name shadowing warnings).

## 4. Keys, channel `env`, new functions and fields

- **New keys: none.** The candidate's `RegisterKeyBind` is identical to the real main's and so is `HELP_TEXT`. The panel
  only mentions existing keys (Ctrl+L, Q/E, Space). So `tools/test_orders.py` (key test) and `MANUAL_TEST.md`
  get no new key. But **README/MANUAL_TEST need to describe**: Shift+L now cycles priority also for
  rifles/bandages; recruiting a rifleman requires 1 rifle + 1 shirt; the medic only treats with bandages in a nearby allied depot;
  enemy chain (convoy alert with `byCut`); multiline panel; save v2 (infrastructure/wallet, refusals,
  autosave suspended on an incomplete continue, files `save.txt.tmp/.bak/.corrupt`).
- **`env` of `runCommandFile`: no new entry needed.** It already exports `logi`, `sv`, `CFG`, `combat`, `S`, `ai`,
  `fort`, `points`, `economy`; everything the stack adds lives in these tables and is reachable.
- **New functions** (diff of `^function X.y(` real × candidate; nothing removed):
  - `logi`: `needs`, `moveCargo`, `medicalDepot`, `extraHud`, `validateSave` (ECONOMIA); `eActive eAfford eAudit eCommit
    eConsume eDeliver eEvent eFmt eHave eHome eHud eLoad eLose eNeed eNextKind eReport eReset eRestore eSnapshot
    eSoldiers eStuck eTick eTransit eUnits eValid` (AI; `eAudit`, `eReport` are the channel ones); `walletId`, `applyPlan`
    (PERSISTENCIA).
  - `sv`: `decode parseSave pure readFile writeAtomic validate verify preflight infraPlan infraSnapshot enemySnapshot
    sameBuilt siteSpec worldPath` (PERSISTENCIA; `sv.parse` now only decodes).
  - State fields: `logi.en` (enemy chain), `logi.fac/depots` with `rifle`/`medical`, generic `tr.cargo` per
    product, `tr.state == "returnCargo"`, `S.deploy` with `budget/built`, `sv.degraded`, `sv.lastWritten`.
  - New `CFG`: `CFG.ECHAIN`, `CFG.PERSIST`; `CFG.LOGI` gains `products`, `want.rifle/medical`, `recipes.rifle/medical`;
    `CFG.ECONVOY` loses `cargo0/perWave/cut`.
- **Save format:** v2 (reads v1). `save.txt` + `.tmp/.bak/.corrupt`.

## 5. ESTRADAS contract (the driver returns `true` only on arrival; `tr.routeStatus`)

No contract change; verified on four fronts (steps 05, 06, 08 and 09):
- **Static:** `function logi.drive(` has a single definition (swap point) and the 7 uses in the candidate consume the
  return inside `if`/`elseif`; none ignores the value.
- **Player (`toDep`):** with `drive` returning `false` (and `routeStatus` in `rota_ausente`, `bloqueado`,
  `regiao_invalida`) 30 ticks each, no delivery, the cargo stays on the truck; `true` delivers a single time.
- **`returnCargo`:** destination captured → `state="returnCargo"`, `dest=logi.factory`, no credit; `false` keeps everything;
  only `true` returns the closed crates to the factory, once, without duplicating (conservation).
- **Enemy convoy (AI):** missing route for `ECHAIN.stuck` s → returns loaded (`back`), the front receives nothing; credit in
  the rear only when the driver returns `true` (`logi.eHome`); the `eAudit` ledger closes.
- **Save/restore** credits nothing during the return (ECONOMIA + PERSISTENCIA pass on the same candidate).

**Pending item on the ESTRADAS side (found here, not fixed by me):** `data/parallel/roads/native_adapter.lua`,
`adapter.returnCargo`, still credits `factory.ammo/factory.shirts` with `tr.cargo.ammo/shirts` (2-product cargo).
In the candidate the return is inline in `logi.truckStep` and credits through `logi.moveCargo(tr.cargo, logi.fac, false)` (4
products, `logi.fac`). When the ESTRADAS driver is integrated, **do not use `adapter.returnCargo` as is**: it would lose
rifles/bandages and get the credit target wrong. Same for `RETURN_PATCH.lua` (2-product version), already superseded by
ECONOMIA's patch.

## 6. Test results (final run)

`python data/parallel/integration_rehearsal/test_stack.py` → **17 steps, 17 PASS, 0 FAIL** (Python 3.14.3, lupa 2.8):

```
PASS  00 integridade: build reproduz candidate/main.lua (CRLF) e main.lua real intacto
PASS  01 sintaxe (lupa Lua 5.4 = UE4SS e 5.5) + limite de 200 locais por chunk
      -> check_globals: main real 175 -> candidato 175; compilador: 178 ativos (folga 22) em Lua 5.4 e 5.5
PASS  02 tools/check_globals.py contra o candidato -> rc=0, sem saida (main real: rc=0)
PASS  03a tools/test_orders.py no main real (controle, sem mudanca)
PASS  03b tools/test_orders.py contra o candidato (bloco 'enemy convoy' da IA)
PASS  04 tools/test_costs.py e tools/test_inventory_probe.py (independentes do main.lua)
PASS  05 economy/test_integration.py contra o candidato
PASS  06 logistics_ai/test_logistics_ai.py contra o candidato (25x600 passos aleatorios + partidas)
PASS  07a interface/test_interface.py original (painel.lua da INTERFACE, mock proprio)
PASS  07b interface/test_interface.py com o logi.hudLine do CANDIDATO (mock proprio, sem extraHud/eHud)
PASS  07c painel no candidato completo: estados, fuzis/bandagens, returnCargo, linha INIMIGO da IA, so leitura
PASS  08 persistence/test_persistence.py contra o candidato (Lua 5.4 e 5.5, 9 cenarios = 18 casos)
PASS  09 contrato ESTRADAS: driver true so na chegada / routeStatus (jogador, returnCargo, comboio inimigo)
PASS  10 conflitos e patches entregues: painel.patch x ECONOMIA reproduzido; sequencia dos .patch e stack.diff aplicam limpo
PASS  11 ordem alternativa ECONOMIA>INTERFACE>IA>PERSISTENCIA produz o MESMO texto
PASS  12 candidato nao toca o ESTRADAS e nao deixa residuos do contrato abstrato antigo
PASS  99 main.lua real intacto ao fim (SHA256 33d6c7e5920a...)
```

(This is the test script's own output, kept verbatim.)

How each other suite was pointed at the candidate (no original edited; `exec` of a copy of the code with the
line that obtains the candidate swapped, the same technique as `logistics_ai/test_orders_candidate.py` and
`persistence/test_regression.py`):

| Suite | In-memory adaptation |
|---|---|
| `tools/test_orders.py` | `source = candidate`; "enemy convoy" block swapped for `logistics_ai/test_orders_convoy_block.lua` (03b); control unchanged on the real main (03a) |
| `tools/test_costs.py`, `tools/test_inventory_probe.py` | they do not read `main.lua` (verified by text): run as they are |
| `economy/test_integration.py` | `proposal = candidate` (runs the whole chunk; `ROOT` injected) |
| `logistics_ai/test_logistics_ai.py` | `stacked = candidate`; 25 seeds × 600 random steps with `eAudit` + 4 complete matches, run on the complete stack |
| `interface/test_interface.py` | original (07a) and with the `hudLine` extracted from the candidate in place of `painel.lua` (07b); new test 07c on the complete chunk |
| `persistence/test_persistence.py` | `STACKS` reduced to 1 stack = complete candidate (9 scenarios × Lua 5.4/5.5) |

**New test 07c (integrated panel):** states (`returnCargo`, `toDep`, resource `idle`, `dead`), rifles/bandages in the
cargo and in `extraHud`, the AI's INIMIGO line (without the old line), assault without an enemy line, inactive logistics, cargo with
missing fields, and `hudLine` **does not change** state (`sv.ser` of `snapshot` + `eSnapshot` equal before/after).
The test's first rendering = **12 lines, up to 222 characters wide** (4 trucks, 2 depots); real sample:

```
LOGÍSTICA | sucata 12 | bmat 100 | prioridade auto
Fábrica | fuzis: 4 s restantes (total 70 s)
Pronto | munição 1 caixas | camisas 2 caixas (20 unidades)
base | munição 6 | camisas 30
A | munição 1 | camisas 0 | abaixo da meta
Caminhão 1 | retornando carga à fábrica | 1 munição + 2 camisas (caixas) + 1 fuzis + 1 bandagens | destino fábrica
Caminhão 2 | ao depósito | 0 munição + 0 camisas (caixas) + 2 fuzis + 1 bandagens | destino A
Caminhão 3 | iniciando coleta | 0 sucata | destino campo
Caminhão 4 | destruído | perdida | destino —
INIMIGO: frente equipa 10 (m2.0 c10) | retaguarda bmat 240, cx m0 c0 | comboios 0 na estrada, 0 perdidos
Ctrl+L: foco na cadeia | Q/E: frentes | Espaço: último alerta
Fuzis: fábrica 3 caixas | bandagens: fábrica 4 caixas | base: 2 fuzis, 5 bandagens | A: 0 fuzis, 0 bandagens | caminhão 1 -> fábrica: 1 caixas fuzis, 1 caixas bandagens | caminhão 2 -> A: 2 caixas fuzis, 1 caixas bandagens
```

**The tests are not vacuous (mutation, outside the delivery):** 6 mutations in the candidate were caught — returnCargo crediting
without arrival (05, 09); panel without `returnCargo` (07c); enemy convoy delivering without a driver (03b, 06, 09); save v=3
(08); `hudLine` writing stock (07c); ECONOMIA's `validateSave` turned off (08).

## 7. Risks and limits

- **Panel (visual gate):** worst case 12 lines and the last one (`extraHud`) is a single line of ~200 characters; the
  `hudTick` uses a TextBlock with `SetAutoSize`. No proven clipping/scroll (INTERFACE already warned). If it overflows the screen,
  turn `extraHud` back into several lines (per product) instead of hiding stocks.
- **Panel × AI:** the INIMIGO line changed shape (from "carga N" to the chain summary). My decision, described in 2.
- **Future orchestration:** after applying the stack, the `build_patch.py` of the 3 folders **stop working** on the
  new main (anchors already applied; `build_on` aborts with "persistência já aplicada"), and `test_integration.py`,
  `test_logistics_ai.py`, `test_persistence.py`, `test_orders_candidate.py` and `test_regression.py` still import those
  builds. The permanent battery must start pointing at the real `main.lua` (swap the line that obtains the candidate
  as I do here) and `tools/test_orders.py` needs the convoy block swapped permanently.
- **Convoy counters:** `combat.convoys/convoysCut` do not persist with the AI (cosmetic, see 2.5).
- **New files on disk in the lab:** `save.txt.tmp`, `.bak`, `.corrupt`; reading `.bak` may bring a save up to
  30 s older (warned on screen).
- **High-risk balance scarcity (AI):** total interdiction brings waves to the floor of 3; parameters in `CFG.ECHAIN`.
- **Accepted limitations of the deliveries (not solved by the stack):** ECONOMIA: grenade impossible (no Explosive);
  passive healing at points/posts and the starting composition/reward/F6 stay free. AI: enemy ammo when firing,
  enemy mortar and fortifications stay abstract; the off-map rear cannot be attacked. PERSISTENCIA:
  a hex layout change invalidates the save (refusal, it does not invent).
- **Transport keeps going in a straight line** until the ESTRADAS driver: the stack only guarantees that the cargo/return/
  loss logic is correct *when* the driver is reliable.

## 8. What requires the lab (open gates copied from the REPORTS)

**ECONOMIA:** real sequential application + panel reconciliation; globals/syntax (done here offline); live test
recipe → production → transport → recruited rifleman / treated bandage **without artificial stocks**; contrast
scarcity / transport cut / recovery; save in the middle of production and cargo; engine failure **after** the preflight
(transactional rollback not proven); point capture / new map; readability and balance; update README/
MANUAL_TEST (rifle/bandage priority, active medic/recruiting supply). **The current driver drives straight: do not use it
as safe transport without integrating the ESTRADAS driver with route/sweep/arrival.** Grenade stays blocked (Explosive).

**IA_LOGISTICA** (`logistics_ai/LAB_SCRIPT.md`): `BPTruckC` spawn and movement with the patch; LOS and alerts;
per-frame performance; real effect at the front with real soldiers; balance (floor of 3 with total interdiction);
real on-disk save/continue with a convoy on the road; integration with the ESTRADAS driver; `logi.convoyRoute` still
picks rear and front through straight ground traces (stops need to become validated graph stops).

**INTERFACE:** panel in a match with active logistics, pause, logistics off, new map, lost depot, dead/recreated
truck, with a capture and data from the same instant; overlap, width/height at several zooms/resolutions, F5 help
and native alerts; check whether the cast exceeds the height (adjust the layout, do not hide data); **the user** checks
left/Shift/right/camera/F5/Ctrl+L/Q/E/Space (no real input was tested). Drag selection box
**is not delivered** (needs the UMG/projection probes); per-truck focus buttons and deduplicated stock alerts
remain open. Map change: do not confuse `IsValid` of the old widget with the current world.

**PERSISTENCIA** (`persistence/LAB_SCRIPT.md`): `io.open("rb"/"wb")`, `f:seek`, `os.rename`/`os.remove` in
UE4SS's Lua/Windows; a real spawn redoing the infrastructure on a new load of the hex with identical ruin/yaw between loads
(2 m / 1° tolerances are a hypothesis); the world's `GetFullName`; cargo in transit resumed with the real driver; cost on the
game thread; IA_LOGISTICA live; a real crash between renames. Lab matrix mandatory before closing the task.

**ESTRADAS:** real driver (route, sweep, confirmed arrival, `routeStatus`) integrated and tested live; export the schema
of the splines; real curve field → refinery → factory; bridge/water; replanning; ms per tick. Adapt `adapter.returnCargo`
(see section 5) before integrating.

**Specific to this stack (lab):** load the candidate (through the coordinator's `restart.sh`, not by me) and run
a short match with logistics on: readable panel, rifle/bandage production, enemy convoy, Ctrl+F6 after
Alt+L; check `UE4SS.log` without a Lua error in the first 5 minutes; record the 12-line HUD at several zooms.

## 9. How to apply (for the coordinator, when they decide)

1. Check that the real `main.lua` still has the SHA256 above (otherwise redo `build_stack.py`).
2. Copy `candidate/main.lua` over the real one **or** apply `stack.diff` (CRLF) with `git apply -p1`/`patch -p1`
   at the root (the result is byte for byte identical, tested in a temporary directory).
3. Swap in `tools/test_orders.py` the "enemy convoy" block for the one in `logistics_ai/test_orders_convoy_block.lua`; include
   in the battery the new tests of the three deliveries pointing at the real `main.lua`.
4. Run `check_globals.py` and the battery; only then the lab.
5. Record in `MODLOG.md`; already proposed gotchas are in `logistics_ai/PROPOSED_GOTCHAS.md` and
   `persistence/PROPOSED_GOTCHAS.md`; new gotchas from this round for the note `knowledge/games/foxhole/...`:
   (a) `.patch` files written with `write_text` on Windows come out CRLF — use `newline="\n"` or apply through a script;
   (b) a panel that replaces a whole function by text boundaries commutes with patches that anchor inside it;
   (c) a 2-product cargo return adapter becomes obsolete when the economy generalizes products.

---

# Stack v2 (deliveries from `logistics_ai/finishing/`) — 2026-10-09

The v1 stack above stays reproducible and **unchanged** (`build_stack.py v1`; hash of `candidate/main.lua` equal to
before: `fe91ce776eec7f2c79a41223e1430f4bd9f37d9ba0e9d317daf2bf07b48765ed`). v2 is a new variant; nothing was applied
to the real `main.lua` (SHA256 equal before/after in build and tests) and nothing was edited in `finishing/` (read-only; the
pure functions `build`/`build_on`/`apply` were imported without bytecode).

## V2.1 Order and candidate

```
real main.lua
 1. ECONOMIA          economy/build_patch.py                       build
 2. IA_LOGISTICA v2   finishing/build_patch_v2.py                  build()[0]   (CFG.ECHAIN free 5, want 4/20, trip 20; eRestore(d, dropped))
 3. bmat reserve      finishing/patch_bmat_reserve.py              apply        (logi.rebuildReserve + guard in logi.factoryStep)
 4. INTERFACE v2      build_pilha.interface_build(s, v2=True)       rebased panel + reserve state + free floor
 5. PERSISTENCIA v2   finishing/build_persistence_v2.py           build_on     (elogi: discards only the section)
```

**SHA256 of `candidate_v2/main.lua` (CRLF): `a93c1531588ea4534a7791dbb2e9578654ad0fa4a87373be1cbed569cbc3eda6`**
(319,236 bytes, 6302 lines). Real main: `33d6c7e5920a3b5e00b7f3bafbc7b8a86c984db810217241a567afe0901ee679` (before = after).

Steps (+/- lines): ECONOMIA +203/-65, AI v2 +528/-45, reserve +16/-0, INTERFACE v2 +61/-16, PERSISTENCIA v2 +602/-55.

Commutation (step 11, text identical byte for byte in 4 orders, besides the main one): `ECO>IA>INTERFACE>reserva>PERS`,
`ECO>INTERFACE>IA>reserva>PERS`, `ECO>INTERFACE>reserva>IA>PERS`, `ECO>IA>reserva>PERS>INTERFACE`. The position of the panel and
of the reserve does not matter; only AI→PERSISTENCIA and ECONOMIA before INTERFACE are mandatory.

New files: `candidate_v2/main.lua`, `candidate_v2/SHA256.txt`, `stack_v2.diff` (CRLF, applies directly on the real main;
tested, reproduces the candidate byte for byte), `stack_v2_lf.diff`, `painel_rebase_v2.patch` (LF, step 3 → 4),
`test_output_v2.txt`. Reproduce:

```bash
PYTHONPATH=D:/tools/pylibs PYTHONDONTWRITEBYTECODE=1 python data/parallel/integration_rehearsal/build_stack.py v2     # or: all
PYTHONPATH=D:/tools/pylibs PYTHONDONTWRITEBYTECODE=1 python data/parallel/integration_rehearsal/test_stack.py v2
```

## V2.2 Test results (20 steps, 20 PASS, 0 FAIL)

| Step | Result |
|---|---|
| 00 integrity (candidate_v2 in CRLF == build; real main intact) | PASS |
| 01 syntax Lua 5.4 and 5.5 + locals: compiler **178** active (22 headroom), check_globals regex **175**, equal to the real main; no step adds a local | PASS |
| 02 `tools/check_globals.py` on candidate_v2 | PASS (rc=0, no output, no warnings) |
| 03a `tools/test_orders.py` on the real main (control) | PASS |
| 03b `tools/test_orders.py` on candidate_v2 with `test_orders_convoy_block_v2.lua` | PASS |
| 04 `tools/test_costs.py`, `tools/test_inventory_probe.py` (independent of main) | PASS |
| 05 `economy/test_integration.py` | PASS |
| 06 `finishing/test_logistics_ai_v2.py` (25×600 steps + matches, on the complete stack) | PASS |
| 06b `finishing/test_elogi.py` (Lua 5.4/5.5; candidate_v2 + "mod without AI" scenario) | PASS (12 cases) |
| 06c `finishing/test_truck_bmat.py` (hypothesis without the patch; with the patch the truck comes back; complete stack = candidate_v2) | PASS |
| 07a original `interface/test_interface.py` | PASS |
| 07b `interface/test_interface.py` with candidate_v2's `hudLine` | PASS |
| 07c integrated panel (states, returnCargo, rifles/bandages, the AI's INIMIGO line, read-only) | PASS |
| **07d panel v2 (new): bmat reserve and INIMIGO line with the `free=5` floor** | PASS |
| 08 `finishing/test_persistence_v2.py` (9 scenarios × Lua 5.4/5.5 × 2 stacks: without AI and candidate_v2) | PASS (36 cases) |
| 09 ESTRADAS contract (7 uses of `logi.drive`, all conditional; false never delivers; returnCargo; convoy) | PASS |
| 10 conflict `painel.patch`×ECONOMIA reproduced; `economia_integrada > ia_logistica_v2 > reserva_bmat > painel_rebase_v2 > persistencia_v2_sobre_ia` apply in sequence and == candidate; `stack_v2.diff` applies on the real main | PASS |
| 11 four alternative orders == candidate | PASS |
| 12 no leftovers of the abstract contract; calibration `free 5 / trip 20.0 / want 4,20`; single `rebuildReserve` | PASS |
| 99 real main intact at the end | PASS |

Notes: `test_elogi.py` and `test_persistence_v2.py` run with 2 stacks (the "without AI" one is needed for the "mod without the module" case;
the other is **the complete candidate_v2, with INTERFACE**) instead of their original 3 (the stacks with only AI and without INTERFACE
are covered by `finishing/run_all.sh`; I did not run that script nor `sweep_echain.py`, which do not depend on the panel).
I did not run `finishing/test_regression_v2.py` (coverage repeated by steps 03b/05/06/01/02/11); it imports
`interface_build` from this file, whose signature stays compatible (`interface_build(s)` = panel v1).

Mutations on candidate_v2 (outside the delivery), all caught: reserve = 0 (06c, 07d); panel without the reserve warning (07d);
`free` 5→3 (06, 07d, 12); panel without the floor (07d); `sv.validate` refusing everything for an invalid `elogi` (06b, 08).

## V2.3 Panel: new state

The v1 panel said **"aguarda bmat"** with the factory idle, which is **misleading in v2**: with a player truck destroyed the
factory stops starting recipes on purpose to gather 100 bmat, and the only indication was the toast
`fábrica guarda N bmat para reconstruir caminhão` (3 s, at most 1 every 20 s). So the rebased v2 panel gained
(only in the v2 variant; v1 stayed intact):

- **Factory line:** `Fábrica | guarda 100 bmat para reconstruir caminhão (bmat 130)` when `logi.rebuildReserve() > 0` and
  `bmat − recipe cost < reserve` (the same condition as `factoryStep`); `guarda 200` with two destroyed trucks;
  back to `aguarda bmat` (no destroyed truck) / `N s restantes` (job started with spare bmat) / `parada: demanda
  atendida`. Proven that the panel tells the truth: under that condition `factoryStep` indeed does not start a job.
- **INIMIGO line with the floor:** `INIMIGO: frente equipa 10 (m2.0 c10) | retaguarda bmat 240, cx m0 c0 | comboios 0 na
  estrada, 0 perdidos | piso grátis 5/onda`. With the chain cut and the front at zero: `frente equipa 0 (m0.0 c0) ... | piso grátis
  5/onda`, and `waveCut(13)` returns exactly 5 = the number shown. In assault, without a chain (`logi.en` nil) or without logistics
  there is no line nor floor; a refused chain shows `cadeia recusada (...)`, without an error.
- Still read-only (snapshot + eSnapshot identical before/after `hudLine`).

Recorded test caveat: `retaguarda` contains `guarda`; the panel's text assertions use `Fábrica | guarda`.

Sample (07d):

```
Fábrica | guarda 100 bmat para reconstruir caminhão (bmat 130)
INIMIGO: frente equipa 10 (m2.0 c10) | retaguarda bmat 240, cx m0 c0 | comboios 0 na estrada, 0 perdidos | piso grátis 5/onda
INIMIGO: frente equipa 0 (m0.0 c0) | retaguarda bmat 240, cx m0 c0 | comboios 0 na estrada, 0 perdidos | piso grátis 5/onda
```

The INIMIGO line now has ~125 characters; the complete panel stays at 12 lines in the worst case of test 07c (lab
visual gate, as before).

## V2.4 New conflicts (v2 relative to v1)

1. **No new anchor conflict.** `reserva_bmat` anchors inside `logi.factoryStep` (ECONOMIA's recipe line) and
   on `function logi.factoryStep(`: it does not touch the HUD nor the save; it commutes with AI v2, INTERFACE and PERSISTENCIA v2.
2. **Line endings of the `finishing/` `.patch` files:** `logistics_ai_v2.patch` in **CRLF** (the same `write_text` flaw on
   Windows); `bmat_reserve.patch`, `persistence_v2_over_ai.patch` and `painel_rebase_v2.patch` in LF. The chain only applies
   after normalizing to LF (done in the test). Use `stack_v2.diff` or `candidate_v2/main.lua`.
3. **`persistence_v2_over_ai.patch`** was generated over `ECO+IA2+reserva` (without INTERFACE) and still applies cleanly
   after INTERFACE (context far from the HUD), confirmed byte for byte.
4. **Panel × reserve:** the label `aguarda bmat` became incorrect with the reserve; solved in panel v2. The toast still
   exists (it is not persistent).
5. **Behavior decisions for the coordinator** (already pointed out by the finishing): the calibration `free 5 / want 4,20 / trip 20`
   and the policy "elogi discards only the section" (editing the save may become a shortcut to restart the enemy chain; low risk in
   an offline solo game).
6. **Inherited pending items, not solved by v2:** a destroyed **resource** truck with bmat=0 and salvage=0 still has no income
   to rebuild (`finishing/REPORT.md` 2.3); restart stock of the enemy chain after a discarded `elogi` (3.2);
   `combat.convoys/convoysCut` still not persisted (v1, item 2.5); ESTRADAS's `adapter.returnCargo` outdated (section 5).
7. **Locals, keys, `env`:** same as v1 (178 by the compiler, 175 by the regex; no new key; nothing new in `env`). The only
   new function relative to v1: `logi.rebuildReserve` (and the field `logi.rebuildNoteT`); `logi.eRestore` gains the 2nd parameter
   `dropped`. The README needs to say, besides what v1 already asked: floor/stock of the enemy chain, bmat reserve to
   rebuild a truck (line "guarda N bmat" in the panel) and the warning `CADEIA INIMIGA REINICIADA` on continue.

## V2.5 What requires the lab (addition to section 8)

The gates of section 8 still hold. Added are those of `finishing/REPORT.md` §6: measure the real wave cadence
(bot and human) and repeat `sweep_echain.py` with the real fights; real cycle time of the resource truck (`trip`);
`logi.eReport()` with the v2 calibration (`byCut`, losses, pressure); kill a supply truck under high consumption, see the toast
and the line "guarda N bmat" and the truck come back in < 60 s; edit `save.txt` (corrupt `elogi`, `v=2`), Ctrl+F6, check the
10 s warning, the player intact and the following autosave. Visual: the enlarged INIMIGO line and the factory line with the reserve
at several zooms/resolutions.
