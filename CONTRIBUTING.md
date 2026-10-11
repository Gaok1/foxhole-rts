# Contributing

Humans and AI agents are both welcome. Most of this project was written by agents (Claude Code, Codex) steered by
one person; the repository is set up so your agent can pick up where the last one stopped.

## Before anything
- You need your own Foxhole on Steam and an **isolated copy** of the game for the lab, blocked from the network,
  with UE4SS installed only there. Never run the mod on your Steam install or online. See `README.md`.
- Read `AGENTS.md`. Its hard rules apply to humans too.
- Pick an item in `PROGRESS.md` and open an issue ("Take a roadmap item") so nobody duplicates it.

## If you are an AI agent
1. **Start with `skills/resume-work/SKILL.md`.** The skills are also in `.claude/skills` and `.agents/skills`.
2. **Trace before reinventing** (`skills/trace-before-reinvent`): the maintainer rejects hand-made imitations of
   game systems (damage, shots, vehicles) when the game's own call can be reused.
3. **Test offline first** (`skills/offline-tests`) and batch any live validation (`skills/lab-batch`). Never inject
   keyboard or mouse into the game window.
4. **Wrap up** (`skills/wrap-up`): `MODLOG.md` entry, `PROGRESS.md` + `python tools/progress.py`, docs.
5. **Ask your human before publishing.** A PR or issue is public and carries their GitHub identity.
6. Say in the PR which agent and model wrote it.

## Pull requests
- Fork, branch, one topic per PR. Fill in the template.
- All `tools/test_*.py` pass (CI runs them). New behavior comes with a test that failed before the change.
- `main.lua` has a 200-locals limit (178 used): new functions go into the existing tables. See `AGENTS.md`, Pitfalls.
- Live claims need evidence: a trace in `data/` or a described scenario with its result. `[x]` in `PROGRESS.md` only
  with live validation.
- English in the repository (docs, diary, comments, commits). Issues may be in English or Portuguese.

## Hard rules (PRs that break these are closed)
- No game files: binaries, DLLs, paks, extracted assets, maps, audio. No decompiled code; describe it in your words.
- No DRM, ownership-check or anti-cheat bypass. Nothing meant for online play.
- No tokens, keys or personal paths.
- Do not edit recorded traces (`data/trace_*`). Record a new one.

## Good places to help
See "How to help" in `README.md` and the unchecked items in `PROGRESS.md`. Reverse engineers (Ghidra, UE4SS) and
people who know Foxhole logistics well are especially welcome.
