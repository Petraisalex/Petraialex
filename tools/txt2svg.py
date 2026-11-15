#!/usr/bin/env python3
"""
txt2svg.py — turn a character-grid .txt (from portrait-tool.html) into portrait.svg.

    python3 tools/txt2svg.py ~/Downloads/portrait.txt portrait.svg [--rows A:B]

Blank margins are trimmed. --rows keeps only lines A..B (1-based, inclusive) of
the trimmed grid, e.g. --rows 1:70 for head and shoulders. Glyphs are placed on
an exact grid (one x per character) in the banner pink, theme-aware.
"""
import sys

FONT = "ui-monospace, SFMono-Regular, Menlo, Consolas, 'DejaVu Sans Mono', monospace"
PX = 10
CW, CH = PX * 0.6, PX * 1.18
STYLE = ("<style>text{fill:#dd2d51;font-family:%s;font-size:%spx;text-anchor:middle}"
         "@media(prefers-color-scheme:dark){text{fill:#e04060}}</style>") % (FONT, PX)


def esc(s):
    return s.replace("&", "&amp;").replace("<", "&lt;").replace(">", "&gt;")


def main(src, dst, rows=None):
    lines = [l.rstrip("\n").replace("⠀", " ") for l in open(src, encoding="utf-8")]
    while lines and not lines[0].strip():
        lines.pop(0)
    while lines and not lines[-1].strip():
        lines.pop()
    if rows:
        a, b = (int(v) for v in rows.split(":"))
        lines = lines[a - 1:b]
    left = min(len(l) - len(l.lstrip()) for l in lines if l.strip())
    lines = [l[left:].rstrip() for l in lines]
    cols = max(len(l) for l in lines)
    W, H = round(cols * CW, 1), round(len(lines) * CH, 1)
    out = []
    for y, line in enumerate(lines):
        xs, chars = [], ""
        for x, c in enumerate(line):
            if c != " ":
                xs.append(f"{x * CW + CW / 2:.1f}")
                chars += c
        if chars:
            out.append(f'<text y="{y * CH + CH / 2 + PX * 0.36:.1f}" x="{" ".join(xs)}">{esc(chars)}</text>')
    svg = (f'<svg xmlns="http://www.w3.org/2000/svg" viewBox="0 0 {W} {H}" width="{W}" height="{H}" '
           f'role="img" aria-label="Character-art portrait">{STYLE}{"".join(out)}</svg>')
    open(dst, "w", encoding="utf-8").write(svg)
    print(f"wrote {dst}: {cols}×{len(lines)} cells, {len(svg) // 1024} KB")


if __name__ == "__main__":
    args = sys.argv[1:]
    rows = None
    if "--rows" in args:
        i = args.index("--rows")
        rows = args[i + 1]
        del args[i:i + 2]
    main(*args, rows=rows)
