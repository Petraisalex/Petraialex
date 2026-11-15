#!/usr/bin/env python3
"""
art.py — draw the profile's static graphics in the banner's navy & pink.

Outputs (all in art/):
    about.svg               About Me as a box-drawn text file
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

MASTERED = ["python", "n8n", "powerbi", "excel", "r", "git"]
LEARNING = ["catboost", "shap", "fastapi", "docker", "mlflow",
            "googlebigquery", "looker", "umap", "bertopic"]
LABELS = {"python": "Python", "n8n": "n8n", "powerbi": "Power BI", "excel": "Excel", "r": "R",
          "git": "Git", "catboost": "CatBoost", "shap": "SHAP", "fastapi": "FastAPI",
          "docker": "Docker", "mlflow": "MLflow", "googlebigquery": "BigQuery",
          "looker": "Looker", "umap": "UMAP", "bertopic": "BERTopic"}

CONNECT = [("linkedin", "LinkedIn"), ("instagram", "Instagram"), ("email", "Email")]


def xesc(s):
    return s.replace("&", "&amp;").replace("<", "&lt;").replace(">", "&gt;").replace('"', "&quot;")


def svg(w, h, inner, label):
    return (f'<svg xmlns="http://www.w3.org/2000/svg" viewBox="0 0 {w} {h}" width="{w}" '
            f'height="{h}" role="img" aria-label="{xesc(label)}">{STYLE}{inner}</svg>')


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
    elif name == "catboost":  # boosted trees: three stumps, growing
        body = ''.join(f'<path class="acs" d="M{x} {y0}v4M{x} {y0 + 4}l-2.6 4M{x} {y0 + 4}l2.6 4" '
                       f'fill="none" stroke-width="1.8" stroke-linecap="round"/>'
                       f'<circle class="ac" cx="{x}" cy="{y0}" r="1.9"/>'
                       for x, y0 in ((4.5, 11), (12, 7), (19.5, 3)))
        body += '<path class="acs" d="M2 22h20" stroke-width="1.8" stroke-linecap="round"/>'
    elif name == "shap":     # waterfall of +/- contributions
        body = ''.join(f'<rect class="ac" x="{x}" y="{y}" width="{w}" height="3.2" rx="1"/>'
                       for x, y, w in ((3, 3, 9), (12, 7.5, 6), (9, 12, 3), (9, 16.5, 11)))
        body += '<path class="acs" d="M3 21.5h18" stroke-width="1.4" stroke-linecap="round"/>'
    elif name == "umap":     # points falling into clusters
        pts = ((5, 6), (7.5, 4.5), (4, 9), (7, 8), (17, 5), (19.5, 7.5), (16, 8.5),
               (10, 17), (13, 19), (11.5, 15), (14.5, 16.5), (21, 19))
        body = ''.join(f'<circle class="ac" cx="{x}" cy="{y}" r="1.7"/>' for x, y in pts)
    elif name == "bertopic":  # a cluster with a topic tag
        body = (''.join(f'<circle class="ac" cx="{x}" cy="{y}" r="1.8"/>'
                        for x, y in ((5, 14), (8, 11), (7, 17.5), (10.5, 15), (4, 19)))
                + '<path class="ac" d="M13 3h7.5a1.5 1.5 0 0 1 1.5 1.5v4a1.5 1.5 0 0 1-1.5 1.5H13l-3-3.5z"/>'
                + '<path class="acs" d="M11 12.5l3-3" stroke-width="1.6" stroke-linecap="round"/>')
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
                     f'{xesc(line)}</text>')
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


ABOUT = [  # (key, wrapped lines)
    ("study", ["BSc International Business, Finance major",
               "MSc Organizational Management, 3 schools"]),
    ("work",  ["Agentic workflows (n8n) & business",
               "intelligence for SMEs and startups"]),
    ("build", ["XGBoost decision engine scoring tabular",
               "transactions in <50 ms for digital banks"]),
    ("won",   ["Junction Hackathon runner-up of 120+ teams:",
               "automated ESG scoring for SME lending"]),
    ("off",   ["Live-coding music · Hyrox & boxing ·",
               "learning Japanese"]),
]


def build_about():
    """About Me as a box-drawn text file: pink frame, pink keys, light values.
    Border runs are stretched with textLength so corners meet in any font."""
    FS, CW, LH = 13, 13 * 0.6, 22
    KEY = 8                                  # key column width, in characters
    inner = max(len(l) for _, ls in ABOUT for l in ls) + KEY + 8
    W = (inner + 2) * CW
    rows = sum(len(ls) for _, ls in ABOUT) + (len(ABOUT) - 1)   # blank row between entries
    top, H = 22, 22 + (rows + 2) * LH
    bottom = H - 14
    title = " about.txt "
    left, right = CW / 2, W - CW / 2

    def run(y, s, x1, x2, cls="ac"):
        return (f'<text class="{cls}" x="{x1:.1f}" y="{y}" textLength="{x2 - x1:.1f}" '
                f'lengthAdjust="spacingAndGlyphs">{s}</text>')

    p = [
        f'<text class="ac" x="0" y="{top}">┌─</text>',
        f'<text class="fg" x="{2 * CW:.1f}" y="{top}" font-weight="700">{title}</text>',
        run(top, "─" * (inner - len(title) - 1), (2 + len(title)) * CW, W - CW),
        f'<text class="ac" x="{W - CW:.1f}" y="{top}">┐</text>',
        f'<text class="ac" x="0" y="{bottom}">└</text>',
        run(bottom, "─" * inner, CW, W - CW),
        f'<text class="ac" x="{W - CW:.1f}" y="{bottom}">┘</text>',
    ]
    y = top + LH
    for i, (key, lines) in enumerate(ABOUT):
        for j, line in enumerate(lines):
            y += LH if (i or j) else 0
            if j == 0:
                p.append(f'<text class="ac" x="{3 * CW:.1f}" y="{y}" font-weight="700">{key}</text>')
                p.append(f'<text class="mu" x="{(3 + KEY - 2) * CW:.1f}" y="{y}">→</text>')
            p.append(f'<text class="fg" x="{(3 + KEY) * CW:.1f}" y="{y}" xml:space="preserve">'
                     f'{xesc(line)}</text>')
        if i < len(ABOUT) - 1:
            y += LH
    # side rails: one │ per text row so they read as characters
    for yy in range(top + LH // 2, bottom - LH // 2 + 1, LH // 2):
        p.append(f'<text class="ac" x="0" y="{yy + 4}">│</text>')
        p.append(f'<text class="ac" x="{W - CW:.1f}" y="{yy + 4}">│</text>')
    label = "About me. " + " ".join(f"{k}: {' '.join(ls)}." for k, ls in ABOUT)
    return svg(round(W, 1), H, f'<g font-family="{MONO}" font-size="{FS}">{"".join(p)}</g>', label)


def build_stack():
    """Two rows of tiles: what I've mastered, and what I'm learning now."""
    TW, TH, GAP, LBL, ROWGAP = 72, 84, 8, 22, 24
    W = len(LEARNING) * TW + (len(LEARNING) - 1) * GAP

    def row(names, y0, title, dashed=False):
        span = len(names) * TW + (len(names) - 1) * GAP
        x0 = (W - span) / 2
        out = [f'<text class="mu" x="{W / 2}" y="{y0 + 12}" text-anchor="middle" font-family="{SANS}" '
               f'font-size="11" font-weight="700" letter-spacing="2.5">{title}</text>']
        dash = ' stroke-dasharray="5 4"' if dashed else ""
        for i, name in enumerate(names):
            x, y = x0 + i * (TW + GAP), y0 + LBL
            out.append(f'<rect class="cd" x="{x + .5}" y="{y + .5}" width="{TW - 1}" height="{TH - 1}" rx="12"{dash}/>')
            out.append(mark(name, x + TW / 2 - 16, y + 14, 32))
            out.append(f'<text class="fg" x="{x + TW / 2}" y="{y + 68}" text-anchor="middle" '
                       f'font-family="{SANS}" font-size="11.5" font-weight="600">{LABELS[name]}</text>')
        return out

    top = row(MASTERED, 0, "MASTERED")
    y2 = LBL + TH + ROWGAP
    bottom = row(LEARNING, y2, "LEARNING NOW", dashed=True)
    H = y2 + LBL + TH
    label = ("Mastered: " + ", ".join(LABELS[n] for n in MASTERED)
             + ". Learning now: " + ", ".join(LABELS[n] for n in LEARNING) + ".")
    return svg(W, H, "".join(top + bottom), label)


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
    outputs = {"about.svg": build_about(), "typing.svg": build_typing(), "stack.svg": build_stack(), "wave.svg": build_wave()}
    for name, label in CONNECT:
        outputs[f"connect-{name}.svg"] = build_connect(name, label)
    for name, content in outputs.items():
        (ART / name).write_text(content)
        print(f"wrote art/{name} ({len(content)} bytes)")


if __name__ == "__main__":
    main()
