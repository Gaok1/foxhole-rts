"""Le PROGRESS.md e reescreve o bloco de progresso do README.md.

[x] = 1, [~] = 0.5, [ ] = 0. Uso: python tools/progress.py
"""
import pathlib
import re

ROOT = pathlib.Path(__file__).resolve().parent.parent
SCORE = {"x": 1.0, "~": 0.5, " ": 0.0}
MVP_PHASES = 3  # fases 1-3 formam o MVP


def phases(text):
    out, cur = [], None
    for line in text.splitlines():
        if line.startswith("## "):
            cur = [line[3:].strip(), 0.0, 0]
            out.append(cur)
        m = re.match(r"- \[([x~ ])\] ", line)
        if m and cur:
            cur[1] += SCORE[m.group(1)]
            cur[2] += 1
    return [p for p in out if p[2]]


def bar(frac, width=20):
    n = round(frac * width)
    return "█" * n + "░" * (width - n)


def block(ps):
    rows = ["| Phase | Progress | |", "|---|---|---|"]
    for name, got, total in ps:
        rows.append(f"| {name} | `{bar(got / total)}` | **{round(100 * got / total)}%** |")
    mvp = ps[:MVP_PHASES]
    frac = sum(p[1] for p in mvp) / sum(p[2] for p in mvp)
    rows.append(f"| **MVP (phases 1-{MVP_PHASES})** | `{bar(frac)}` | **{round(100 * frac)}%** |")
    return "\n".join(rows)


def main():
    ps = phases((ROOT / "PROGRESS.md").read_text(encoding="utf-8"))
    readme = ROOT / "README.md"
    text = readme.read_text(encoding="utf-8")
    new, n = re.subn(r"(<!-- progress:start -->).*?(<!-- progress:end -->)",
                     lambda m: m.group(1) + "\n" + block(ps) + "\n" + m.group(2), text, flags=re.S)
    if n != 1:
        raise SystemExit("README.md sem o bloco <!-- progress:start/end -->")
    readme.write_text(new, encoding="utf-8", newline="\n")
    print(block(ps))


if __name__ == "__main__":
    main()
