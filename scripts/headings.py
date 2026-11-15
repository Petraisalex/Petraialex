#!/usr/bin/env python3
"""
headings.py — draw centred section headings as SVGs (hd-<slug>.svg).

GitHub strips CSS from README markdown, so the only way to give a heading its
own typeface and colour is to ship it as an image. Each heading is the label in
the accent pink, tracked out, with a hairline rule on either side.

No API calls, no arguments — edit LABELS to change the set.
"""
import re

LABELS = ["about me", "tech stack", "projects", "activity", "let's connect"]

W, H = 760, 40
FS = 13
CHAR_W = FS * 0.78      # uppercase sans advance incl. letter-spacing
GAP = 18
FONT = "Montserrat, -apple-system, 'Segoe UI', Helvetica, Arial, sans-serif"

STYLE = ("<style>.s{fill:#dd2d51}.r{stroke:#d1d9e0}"
         "@media(prefers-color-scheme:dark){.s{fill:#e04060}.r{stroke:#30363d}}</style>")


def slug(label):
    return re.sub(r"[^a-z0-9]+", "-", label.lower()).strip("-")


def build(label):
    text = label.upper()
    half = len(text) * CHAR_W / 2
    left, right = W / 2 - half - GAP, W / 2 + half + GAP
    return (f'<svg xmlns="http://www.w3.org/2000/svg" viewBox="0 0 {W} {H}" '
            f'width="{W}" height="{H}" role="img" aria-label="{label}" font-family="{FONT}">{STYLE}'
            f'<line class="r" x1="0" y1="20" x2="{left:.1f}" y2="20" stroke-width="1"/>'
            f'<text class="s" x="{W / 2}" y="25" font-size="{FS}" font-weight="700" '
            f'letter-spacing="3" text-anchor="middle">{text.replace("&", "&amp;")}</text>'
            f'<line class="r" x1="{right:.1f}" y1="20" x2="{W}" y2="20" stroke-width="1"/></svg>')


def main():
    for label in LABELS:
        name = f"hd-{slug(label)}.svg"
        with open(name, "w") as f:
            f.write(build(label))
        print(f"wrote {name}")


if __name__ == "__main__":
    main()
