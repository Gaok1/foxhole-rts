---
name: wrap-up
description: End of a Foxhole RTS session. Writes the MODLOG entry, updates PROGRESS and the README bars, mod/README and MANUAL_TEST when controls changed, shares learnings with the universal-modder knowledge base, and commits or opens a PR. Use when the work stops, before handing back to the human, or when asked to "save", "log" or "publish" the work.
---

# Wrap up

The next agent knows only what is in this repository. Leave it ready.

## 1. Diary: top of `MODLOG.md`
New entry right under the title, in English:
```markdown
## YYYY-MM-DD — <what changed, in a few words>

- What was done, with numbers (HP 900→869, 120 delivered / 0 lost, 29/29 PASS).
- How it was verified: offline tests, live scenario, trace file in data/. Say what was NOT verified.
- What failed and the current hypothesis. Never hide a failed gate.
- Next step.
```
If the priorities changed, update the top of `ROADMAP.md` ("Current state", "Next batch, in order") and,
when relevant, the "How to resume" section of `MODLOG.md`.

## 2. Progress
- Update the item in `PROGRESS.md`: `[ ]` → `[~]` (works offline or once) → `[x]` (validated live). Add an item
  if the work does not fit any.
- `python tools/progress.py` recomputes the bars in `README.md`. Commit both files together.

## 3. Docs that follow the code
- Controls or mechanics changed → `mod/README.md`.
- New key → `MANUAL_TEST.md` and the key test in `tools/test_orders.py`.
- New pitfall that cost you time → `AGENTS.md`, "Pitfalls" (symptom → cause → fix, one bullet).
- Skill text wrong or missing a step → edit `skills/<name>/SKILL.md`, then `python tools/sync_skills.py`.

## 4. universal-modder
Add Foxhole learnings as numbered gotchas to the note `knowledge/games/foxhole/...` of universal-modder and run
`um kb check <note>`. A PR there is public: only with your human's OK (`um kb pr <note> --yes`).

## 5. Commit or PR
- Run all offline tests (`offline-tests`). They must pass.
- Commit messages in English, imperative, describing the change and how it was verified.
- Maintainer working on `main`: commit only when asked. Contributors: branch, push to your fork, open a PR
  against `Gaok1/foxhole-rts` with the PR template filled in. Ask your human before publishing anything.
- Never commit game files, extracted assets, decompiled code, tokens or personal paths.

## 6. Leave the machine clean
Lab copy closed (exact PID), regression bot stopped, temporary probes outside the repo.
