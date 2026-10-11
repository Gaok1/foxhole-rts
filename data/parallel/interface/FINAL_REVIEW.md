# Final offline review — inspection only, no tests run

Review in control window A1 requested by the coordinator. No CPU/generator/Lua script test run. No change to main.lua, the lab or the CLAUDE deliveries.

- The current source inspected still contains CFG.LOGI ammo/shirts, the original fac, the original logi.need/hudLine/restore. The outline optimization added neither economy nor panel. So the economy patch is still an independent proposal, not published code; do not reapply an old whole-file patch over the optimized source.
- build_patch.py does point replacements with unique assert anchors for edits, functions swapped at text boundaries. It does not touch outline/callbacks; the earlier in-memory tests do not certify **this** new source until a new run outside the controlled window.
- Future order: generate the economy against the integrator's source, apply the economy; replace hudLine with the revised panel; apply the conceptual `reconciliation_extraHud.patch` over the panel. Keep the `extraHud` function inserted by the economy. Do not run the economy generator after already applying the panel: the old return's anchor must fail, do not force the patch.
- Minimal reconciliation delivered: the panel calls extraHud only if it exists, once; keeps its enemy/convoy line outside assault; extraHud adds factory/depot stocks/rifle+bandage cargo. The returnCargo state has readable name/destination. Ammo/shirts missing from the generic cargo become zero, without a nil format.
- The reconciliation patch is a four-line unified diff over painel.lua, with numbers checked by Select-String; it was not applied nor validated in this window. Regenerate painel.patch over the current source after reconciliation.
- The UI still has no validation of clipping/height, layout and input; a long extraHud may exceed the width. Do not call it an approved professional panel. extraHud can be turned back into several lines after a visual gate, without hiding products/cargo.
- The ESTRADAS gate remains: returnCargo cannot deliver nor return stock without a physical arrival; the current straight-line driver is insufficient. The CLAUDE_PERSISTENCIA gate: IDs base0/factory-1/point index are only a local legacy, not a regional guarantee. No change to the CLAUDE blocks.

After A1 ends: repeat test_integration.py, test_existing.py and test the panel+extraHud candidate with stock/cargo/returnCargo/enemy/assault mocks, before integration. Earlier PASS tests are from a previous source, not a result of this window.
