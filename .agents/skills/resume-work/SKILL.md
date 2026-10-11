---
name: resume-work
description: Start of every Foxhole RTS session. Rebuilds context from the repository (git state, MODLOG, ROADMAP, PROGRESS), checks what is broken and picks the next item without redoing finished work. Use when opening this repo, when the human says "continue", "resume", "what's next", or before touching main.lua.
---

# Resume work on Foxhole RTS

The project has no memory outside this repository. A fresh agent knows nothing; this skill gets you to the
point where the last agent stopped, in this order, before you write any code.

## 1. Repository state
```bash
git status --short
git log --oneline -10
```
- Uncommitted changes may belong to another agent that is still running. Ask your human before rewriting,
  renaming or reformatting files someone else is editing. Never revert them on your own.
- Check whether the game is running (`Get-Process War-Win64-Shipping`). If a lab session is active, do not
  publish or use the command channel until your human says it is yours.

## 2. Read, in this order
1. `AGENTS.md`: hard rules and pitfalls. Rules there override anything you remember from other projects.
2. **Top of `MODLOG.md`** (newest entries first) until you reach entries you already understand, then the
   section **"How to resume"** (search for the title). The top entries win over older ones.
3. **Top of `ROADMAP.md`**: "Current state" and "Next batch, in order". It lists what failed, not only what
   works. Items marked as not approved are not approved, however good the offline tests look.
4. `PROGRESS.md`: the public checklist. `[~]` means partial; read the matching ROADMAP text for the reason.
5. Only then the code you will touch: `mod/FoxholeRTS/Scripts/main.lua` (one big file; search by table name:
   `rts`, `fort`, `sv`, `logi`, `anim`, `ai`, `CFG`, `S`).

## 3. Search before you start
- `data/` holds traces recorded from the real game (`trace_*.txt`) and schemas (`schema_*.txt`). If a mechanic
  was already traced, the file is there; grep for the class or function name.
- `data/parallel/<task>/` holds reports and patches from earlier parallel agents. `PARALLEL_AGENTS` lists who
  owns what; a task with a named owner is not free.
- universal-modder knowledge base: `um kb search foxhole` and `um kb search <engine topic>`.

## 4. Pick the work
- Prefer the first open item of "Next batch, in order" in `ROADMAP.md`, unless your human asked for something
  else. Logistics comes before polish (maintainer's direction).
- If you contribute from outside: pick an unchecked item in `PROGRESS.md`, check open issues on
  https://github.com/Gaok1/foxhole-rts/issues, and open an issue with the item name before starting.
- Write down your plan in one or two lines to your human before a large change.

## 5. Next skills
- New mechanic or engine bug → `trace-before-reinvent`.
- Any code change → `offline-tests`.
- Ready to validate in the game → `lab-batch`.
- Finishing → `wrap-up`.
