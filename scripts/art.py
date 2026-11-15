#!/usr/bin/env python3
"""
art.py — draw the profile's static graphics in the banner's navy & pink.

Outputs (all in art/):
    typing.svg              rotating "typed" tagline under the banner
    stack.svg               tech-stack tiles
    connect-<name>.svg      link buttons
    wave.svg                footer wave

Brand marks in art/icons/ are from Simple Icons (CC0). Power BI and Excel are
drawn here as simple geometric marks. No API calls; edit the constants below
and re-run to change anything.
"""
import re
from pathlib import Path

ART = Path(__file__).resolve().parent.parent / "art"

SANS = "Montserrat, -apple-system, 'Segoe UI', Helvetica, Arial, sans-serif"
MONO = "'JetBrains Mono', ui-monospace, SFMono-Regular, Menlo, Consolas, monospace"

# light first, dark under the media query (the README sanitiser keeps <style> inside SVGs)
STYLE = """<style>
.fg{fill:#1f2328}.mu{fill:#59636e}.ac{fill:#dd2d51}.acs{stroke:#dd2d51}
.cd{fill:#f6f8fa;stroke:#d1d9e0}.bgs{stroke:#f6f8fa}
@media(prefers-color-scheme:dark){
.fg{fill:#f0f6fc}.mu{fill:#9198a1}.ac{fill:#e04060}.acs{stroke:#e04060}
.cd{fill:#151b23;stroke:#30363d}.bgs{stroke:#151b23}}
</style>"""

TAGLINES = [
    "Professional Hobby-collector",
    "Finance × AI",
    "Dashboards that get read",
    "Hyrox, boxing & live-coded music",
]

STACK = ["python", "pytorch", "r", "powerbi", "excel", "git"]
LABELS = {"python": "Python", "pytorch": "PyTorch", "r": "R",
          "powerbi": "Power BI", "excel": "Excel", "git": "Git"}

CONNECT = [("linkedin", "LinkedIn"), ("instagram", "Instagram"), ("email", "Email")]


def svg(w, h, inner, label):
    return (f'<svg xmlns="http://www.w3.org/2000/svg" viewBox="0 0 {w} {h}" width="{w}" '
            f'height="{h}" role="img" aria-label="{label}">{STYLE}{inner}</svg>')


def icon_path(name):
    """24×24 path data for a mark."""
    f = ART / "icons" / f"{name}.svg"
    if f.exists():
        return re.search(r' d="([^"]+)"', f.read_text()).group(1)
    return None


def mark(name, x, y, size):
    """A 24-unit icon placed at (x, y) and scaled to `size` px, in the accent colour."""
    s = size / 24
    head = f'<g transform="translate({x} {y}) scale({s:.4f})">'
    if name == "powerbi":   # three rising bars
        body = ('<rect class="ac" x="2.5" y="12" width="5" height="10" rx="1.4"/>'
                '<rect class="ac" x="9.5" y="7" width="5" height="15" rx="1.4"/>'
                '<rect class="ac" x="16.5" y="2" width="5" height="20" rx="1.4"/>')
    elif name == "excel":   # sheet with a cross
        body = ('<rect class="ac" x="2" y="2" width="20" height="20" rx="4"/>'
                '<path class="bgs" d="M8 7l8 10M16 7L8 17" stroke-width="2.6" '
                'stroke-linecap="round" fill="none"/>')
    elif name == "email":   # envelope
        body = ('<rect class="acs" x="2.5" y="5" width="19" height="14" rx="2.5" '
                'fill="none" stroke-width="2"/>'
                '<path class="acs" d="M3.5 7l8.5 6 8.5-6" fill="none" stroke-width="2" '
                'stroke-linejoin="round" stroke-linecap="round"/>')
    else:
        body = f'<path class="ac" d="{icon_path(name)}"/>'
    return head + body + "</g>"


# ---------------------------------------------------------------------------
def build_typing():
    W, H, FS = 760, 56, 26
    CW = FS * 0.6                  # monospace advance
    TYPE, HOLD, ERASE, GAP = 0.07, 1.6, 0.03, 0.35   # seconds
    spans = []                     # (line, start, per-char type times...)
    t = 0.0
    for line in TAGLINES:
        n = len(line)
        dur = n * TYPE + HOLD + n * ERASE + GAP
        spans.append((line, t, dur))
        t += dur
    T = t

    clips, texts, caret_pts = [], [], []
    for i, (line, start, dur) in enumerate(spans):
        n = len(line)
        x0 = W / 2 - n * CW / 2
        pts = [(0.0, 0.0)]
        for k in range(1, n + 1):                       # typing
            pts.append((start + k * TYPE, k * CW))
        hold_end = start + n * TYPE + HOLD
        for k in range(n - 1, -1, -1):                  # erasing
            pts.append((hold_end + (n - k) * ERASE, k * CW))
        pts.append((T, 0.0))
        # de-duplicate equal times, keep order
        clean = []
        for tm, v in pts:
            tm = round(tm / T, 5)
            if clean and tm <= clean[-1][0]:
                clean[-1] = (clean[-1][0], v)
            else:
                clean.append((tm, v))
        clean[-1] = (1.0, clean[-1][1])
        kt = ";".join(f"{a:g}" for a, _ in clean)
        vals = ";".join(f"{b:.1f}" for _, b in clean)
        base = n * CW if i == 0 else 0                  # still shows line 1 if animation is off
        clips.append(
            f'<clipPath id="c{i}"><rect x="{x0:.1f}" y="0" height="{H}" width="{base:.1f}">'
            f'<animate attributeName="width" calcMode="discrete" dur="{T:.2f}s" '
            f'repeatCount="indefinite" keyTimes="{kt}" values="{vals}"/></rect></clipPath>')
        texts.append(f'<text class="fg" x="{x0:.1f}" y="37" clip-path="url(#c{i})">'
                     f'{line.replace("&", "&amp;")}</text>')
        caret_pts += [(tm, x0 + v) for tm, v in clean if 0 < tm < 1]

    caret_pts.sort()
    first_x = W / 2 + len(TAGLINES[0]) * CW / 2
    kt = "0;" + ";".join(f"{a:g}" for a, _ in caret_pts) + ";1"
    vals = f"{first_x:.1f};" + ";".join(f"{b:.1f}" for _, b in caret_pts) + f";{first_x:.1f}"
    caret = (f'<rect class="ac" x="{first_x + 3:.1f}" y="13" width="3" height="31" rx="1">'
             f'<animate attributeName="x" calcMode="discrete" dur="{T:.2f}s" repeatCount="indefinite" '
             f'keyTimes="{kt}" values="{vals}"/>'
             f'<animate attributeName="opacity" values="1;1;0;0" keyTimes="0;.5;.5;1" dur="1s" '
             f'repeatCount="indefinite"/></rect>')
    inner = (f'<defs>{"".join(clips)}</defs>'
             f'<g font-family="{MONO}" font-size="{FS}">{"".join(texts)}</g>{caret}')
    return svg(W, H, inner, " · ".join(TAGLINES))


def build_stack():
    TW, TH, GAP = 110, 112, 20
    W = len(STACK) * TW + (len(STACK) - 1) * GAP
    parts = []
    for i, name in enumerate(STACK):
        x = i * (TW + GAP)
        parts.append(f'<rect class="cd" x="{x + .5}" y=".5" width="{TW - 1}" height="{TH - 1}" rx="16"/>')
        parts.append(mark(name, x + TW / 2 - 22, 20, 44))
        parts.append(f'<text class="fg" x="{x + TW / 2}" y="92" text-anchor="middle" '
                     f'font-family="{SANS}" font-size="13" font-weight="600">{LABELS[name]}</text>')
    return svg(W, TH, "".join(parts), " · ".join(LABELS[n] for n in STACK))


def build_connect(name, label):
    W, H = 168, 44
    inner = (f'<rect class="cd" x=".5" y=".5" width="{W - 1}" height="{H - 1}" rx="22"/>'
             + mark(name, 20, 12, 20)
             + f'<text class="fg" x="52" y="27.5" font-family="{SANS}" font-size="14" '
               f'font-weight="600">{label}</text>')
    return svg(W, H, inner, label)


def build_wave():
    W, H = 1600, 140
    inner = (
        '<defs><linearGradient id="g" x1="0" x2="1" y1="0" y2="0">'
        '<stop offset="0" stop-color="#852f45"/><stop offset=".5" stop-color="#e04060"/>'
        '<stop offset="1" stop-color="#f6c6cf"/></linearGradient></defs>'
        f'<path fill="url(#g)" opacity=".35" d="M0 70 C 260 20 520 120 800 70 S 1340 20 {W} 60 V {H} H 0 Z"/>'
        f'<path fill="url(#g)" d="M0 95 C 300 55 560 135 820 95 S 1360 60 {W} 92 V {H} H 0 Z"/>'
    )
    return svg(W, H, inner, "")


def main():
    outputs = {"typing.svg": build_typing(), "stack.svg": build_stack(), "wave.svg": build_wave()}
    for name, label in CONNECT:
        outputs[f"connect-{name}.svg"] = build_connect(name, label)
    for name, content in outputs.items():
        (ART / name).write_text(content)
        print(f"wrote art/{name} ({len(content)} bytes)")


if __name__ == "__main__":
    main()
