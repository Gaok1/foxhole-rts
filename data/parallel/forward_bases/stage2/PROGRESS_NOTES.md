# PROGRESS_NOTES (stage 2 of BASES_AVANCADAS / forward bases) - to resume if the session drops
State (2026-10-10): reading/design done; writing bases_cfg.lua, bases_funcs.lua, build_bases.py.
Plan: build_bases.py reads manual_collection/candidate_v3/main.lua (read-only) -> candidate_v4/main.lua + bases.patch + SHA256.txt.
Then: harness_bases.py, test_*.py, test_stack_v4.py (adapted copy of test_stack_v3), test_orders_v4.py (+Shift+J), REPORT.md, run_all.sh, TEST_OUTPUT.txt.
CAREFUL: do not run the original test_stack_v3.py (it writes test_output_v3.txt in the collection folder; it already ran once by mistake, same size).
Done: (update below)
- bases_cfg.lua and bases_funcs.lua written (fwd* functions, new spawnSite/Commit, logistics recruit). Missing: build_bases.py (anchors), then tests.
- build_bases.py written and runs (v4 generated, compiles). Missing: harness_bases.py + tests + stack v4 + REPORT.
- harness_bases.py and test_construction.py written (debugging)
- test_construction.py PASS (debugged). Next: test_recruitment, test_loss (cut/destruction/capture/defeat), test_workers, test_persistence_bases, test_key_panel, test_stack_v4, test_orders_v4, collection over v4, REPORT
- test_recruitment.py PASS
- test_loss.py written (debugging)
- test_loss.py PASS (fwdAudit adjusted for dead). Missing: test_workers, test_persistence_bases, test_key_panel, stack_v4 etc.
- test_workers PASS; test_persistence_bases written (debugging)
- test_persistence_bases PASS. Missing: test_key_panel, test_orders_v4 (copy), test_stack_v4, collection over v4, REPORT, run_all, OUTPUT
- test_orders_v4.py and test_collection_over_v4.py PASS. Missing: test_key_panel, test_stack_v4, REPORT, run_all, OUTPUT
- test_key_panel PASS (9/9). Missing: test_stack_v4 (copy of test_stack_v3 -> candidate_v4, its own log), REPORT, run_all, OUTPUT
- test_stack_v4.py PASS 22/22 (spawnCapable now honors pointSpawn=true; V4 adaptations in 05/08/09). Missing: run_all.sh, TEST_OUTPUT.txt, REPORT.md, SubagentHandback
- sensitivity_bases.py 17/17 mutants caught; extra tests in construction/loss. Missing: run_all.sh (run), REPORT.md, SubagentHandback
- DONE: run_all.sh rc=0, TEST_OUTPUT.txt generated, REPORT.md written. SHA v4 025e3b80...aaab0. Only the SubagentHandback is missing.
