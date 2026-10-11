# BASES_AVANCADAS (forward bases) — decisions D1–D7 (2026-10-09)

The user delegated the design decisions to the orchestrating Claude ("do what is best for the game").
Reference: `SPEC.md` §"Open decisions" and ROADMAP.md phase 3 ("where soldiers come from").

- **D1 — Shift+J (not a double J).** Today `J` adds a control point (`addPoint`); giving it a second meaning
  by double tap is confusing and can create a point by accident. Ctrl+0..9 is fully taken. Shift+J sits next to
  `J` (bases live on points) and the spec checked it is free. The first Shift+J shows cost and site;
  the second within 4 s confirms. Requires updating `MANUAL_TEST.md` and the key test in `tools/test_orders.py`
  (at integration; in stage 2, on a copy).
- **D2 — Accepted.** In the logistics branch, a point without a base stops being a reinforcement site; `CFG.SPAWN.pointSpawn`
  restores the old behavior. That is what gives meaning to the forward base and to cutting supply.
- **D3 — Accepted.** Paid with the factory's `logi.bmat`, debited only after a validated spawn; without bmat, a pending order
  with a reservation (the factory stops spending until it gathers enough), respecting the existing truck reserve.
  Priority when there is a destroyed truck: the truck first (income comes before expansion).
- **D4 — Accepted.** v1 only on own control points.
- **D5 — Accepted.** The enemy does not build bases in v1; the enemy front stays the aggregated stock of logistics_ai v2.
- **D6 — Accepted.** Assault unchanged (no bases, abstract manpower).
- **D7 — Accepted as provisional.** 15 = crate slots until probe A3/B1 proves otherwise; everything in `CFG.FWD`.

**Early-game risk (rifles = 0 at the base):** it is the desired ramp (Age of Empires style: workers first,
production later), but without any reinforcement in the first minutes the first wave may be decisive. Decision:
`CFG.SPAWN.startRifles = 10` at the main base in a match with logistics (proposal; calibrate in the lab
together with the real wave cadence). The scenario's starting squad stays as today.

**Lab:** probes A1–A4 are read-only; rehearsal B1 (create/destroy `BPForwardBase1_C`) is normal work
for the LABORATORIO agent on the lab copy and goes into the batch script, after the stability gate.
Plan B if the class does not spawn intact: the mod's own mesh, without changing the design.
