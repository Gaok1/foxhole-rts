"""Copies skills/ to .claude/skills (Claude Code) and .agents/skills (Codex, Gemini CLI, Copilot, Cursor, OpenCode).

Usage: python tools/sync_skills.py. Edit skills/ only; tools/test_skills_sync.py fails while copies differ.
"""
import pathlib
import shutil

ROOT = pathlib.Path(__file__).resolve().parent.parent
TARGETS = [ROOT / ".claude" / "skills", ROOT / ".agents" / "skills"]

if __name__ == "__main__":
    for t in TARGETS:
        if t.exists():
            shutil.rmtree(t)
        shutil.copytree(ROOT / "skills", t)
        print("synced", t.relative_to(ROOT))
