"""Approximate static check for main.lua: names read before any `local` declaration, or never declared.

Catches the bug class where a `local function f` defined further down is called from code above it,
which Lua resolves as a nil global. Scope-insensitive on purpose (cheap, no Lua tooling needed).
Usage: python tools/check_globals.py [file]
"""
import re
import sys
from pathlib import Path

KNOWN = set("""
and break do else elseif end false for function goto if in local nil not or repeat return then true until while
_G _ENV assert error ipairs next pairs pcall print rawget rawset require select setmetatable getmetatable tonumber
tostring type xpcall load os io math string table utf8 coroutine debug
RegisterKeyBind ExecuteInGameThread LoopInGameThreadAfterFrames LoopInGameThreadWithDelay LoopAsync StaticFindObject
StaticConstructObject FindAllOf FindFirstOf LoadAsset FName FText Key ModifierKey RegisterHook NotifyOnNewObject
""".split())
SHADOW_OK = {"step", "loc"}  # variavel de laco (A*) e parametro de emit; conferidos em 2026-10-09


def strip(src):
    src = re.sub(r"--\[(=*)\[.*?\]\1\]", lambda m: "\n" * m.group(0).count("\n"), src, flags=re.S)
    src = re.sub(r"--[^\n]*", "", src)
    src = re.sub(r"\[(=*)\[.*?\]\1\]", lambda m: '""' + "\n" * m.group(0).count("\n"), src, flags=re.S)
    src = re.sub(r"::\w+::|\bgoto\s+\w+", "", src)  # rotulos de goto nao sao variaveis
    return re.sub(r'"(?:\\.|[^"\\\n])*"|\'(?:\\.|[^\'\\\n])*\'', '""', src)


def main(path):
    lines = strip(Path(path).read_text(encoding="utf-8")).split("\n")
    first_decl = {}

    def declare(name, ln):
        first_decl.setdefault(name, ln)

    for ln, line in enumerate(lines, 1):
        for m in re.finditer(r"\blocal\s+function\s+(\w+)", line):
            declare(m.group(1), ln)
        for m in re.finditer(r"\blocal\s+(?!function\b)([\w\s,]+?)(?:=|$|\bin\b)", line):
            for n in m.group(1).split(","):
                if n.strip():
                    declare(n.strip(), ln)
        for m in re.finditer(r"\bfunction\b[\w.:\s]*\(([^)]*)\)", line):
            for n in m.group(1).split(","):
                n = n.strip()
                if n and n != "...":
                    declare(n, ln)
        for m in re.finditer(r"\bfor\s+([\w\s,]+?)\s*(?:=|\bin\b)", line):
            for n in m.group(1).split(","):
                declare(n.strip(), ln)
    problems = []
    depth = 0  # table-constructor nesting at the start of each line
    for ln, line in enumerate(lines, 1):
        line_depth = depth
        depth += line.count("{") - line.count("}")
        for m in re.finditer(r"(?<![.:\w])([A-Za-z_]\w*)", line):
            name = m.group(1)
            rest = line[m.end():]
            if name in KNOWN or re.match(r"\s*=[^=]", rest) and re.search(r"[{,]\s*$", line[:m.start()]):
                continue  # keyword/API, or a table-constructor key `{ name = ...`
            if re.match(r"\s*=[^=]", rest) and line[:m.start()].strip() == "" and line_depth > 0:
                continue  # key of a multi-line table constructor
            if re.match(r"\s*=[^=]", rest) and line[:m.start()].strip() == "":
                if name not in first_decl:
                    problems.append((ln, name, "global assignment"))
                continue
            d = first_decl.get(name)
            if d is None:
                problems.append((ln, name, "never declared"))
            elif d > ln:
                problems.append((ln, name, f"used before its local declaration (line {d})"))
    top = 0  # Lua allows at most 200 locals per chunk; main.lua hit it once (v0.5)
    for line in lines:
        m = re.match(r"local\s+function\s+\w+", line)
        if m:
            top += 1
            continue
        m = re.match(r"local\s+([\w\s,]+?)(?:=|$)", line)
        if m:
            top += len([n for n in m.group(1).split(",") if n.strip()])
    if top > 180:
        problems.append((0, f"{top} top-level locals", "close to Lua's 200-per-chunk limit; move constants into CFG"))
    # Aviso (nao falha): nome de topo que aparece antes como local interno/parametro. A checagem acima e
    # insensivel a escopo, entao essa declaracao interna mascara usos do nome de topo antes de ser declarado
    # (assim `local ok, ai = ...` em anim.track escondeu um `ai.sent` usado antes do `local ai`).
    top_decl = {}
    for ln, line in enumerate(lines, 1):
        m = re.match(r"local\s+(?:function\s+)?([\w\s,]+?)(?:=|$|\()", line)
        if m:
            for n in m.group(1).split(","):
                if n.strip():
                    top_decl.setdefault(n.strip(), ln)
    for name, ln in sorted(first_decl.items(), key=lambda x: x[1]):
        t = top_decl.get(name)
        if t and ln < t and name not in SHADOW_OK:
            print(f"{path}:{ln}: {name}: aviso: declarado antes como local interno; o de topo so na linha {t}")
    seen = set()
    for ln, name, why in problems:
        if (name, why) not in seen:
            seen.add((name, why))
            print(f"{path}:{ln}: {name}: {why}")
    return 1 if problems else 0


if __name__ == "__main__":
    target = sys.argv[1] if len(sys.argv) > 1 else str(Path(__file__).resolve().parents[1] / "mod/FoxholeRTS/Scripts/main.lua")
    sys.exit(main(target))
