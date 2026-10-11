"""The skill copies in .claude/skills and .agents/skills must match skills/, and every skill needs frontmatter."""
import pathlib
import re

ROOT = pathlib.Path(__file__).resolve().parent.parent
src = {p.relative_to(ROOT / "skills"): p.read_bytes() for p in (ROOT / "skills").rglob("*") if p.is_file()}
assert src, "no skills found"
for target in (ROOT / ".claude" / "skills", ROOT / ".agents" / "skills"):
    copy = {p.relative_to(target): p.read_bytes() for p in target.rglob("*") if p.is_file()}
    assert copy == src, f"{target.relative_to(ROOT)} differs from skills/: run python tools/sync_skills.py"
for rel, data in src.items():
    if rel.name == "SKILL.md":
        head = data.decode("utf-8")
        m = re.match(r"---\nname: ([a-z0-9-]+)\ndescription: .+?\n---\n", head, re.S)
        assert m and m.group(1) == rel.parent.name, f"{rel}: frontmatter name must match folder"
print(f"PASS: {len(src)} skill files in sync")
