#!/usr/bin/env python3
"""
projects.py — rewrite the README's projects section, grouped by repo topic.

Tag a repo with one of the topics in GROUPS and it shows up under that heading
on the next run; untagged repos are left off. Public repos get a link and their
description. Private repos are listed by name and language only — no link, no
description — so nothing about their contents is published.

Rewrites only the text between the PROJECTS markers in README.md.

Env: PROFILE_TOKEN — a token that can see private repos (fine-grained,
read-only "Metadata" on all repositories). If it is not set the script exits
without touching the README, because the workflow's default GITHUB_TOKEN only
sees public repos and would silently drop the private ones.
GH_LOGIN (optional; defaults to the token owner).
"""
import os
import re
import sys
import json
import urllib.request
import urllib.error

GROUPS = [  # (heading, topics that put a repo in it)
    ("hobby &amp; business", {"hobby-project"}),
    ("quant finance", {"quant-finance"}),
    ("business intelligence &amp; ml", {"business-intelligence", "machine-learning"}),
]
START, END = "<!-- PROJECTS:START -->", "<!-- PROJECTS:END -->"
API = "https://api.github.com/graphql"

QUERY = """
query($login: String!) {
  user(login: $login) {
    repositories(first: 100, ownerAffiliations: OWNER, isFork: false,
                 orderBy: {field: PUSHED_AT, direction: DESC}) {
      nodes {
        name url description isPrivate isArchived
        primaryLanguage { name }
        repositoryTopics(first: 20) { nodes { topic { name } } }
      }
    }
  }
}"""


def gql(token, query, variables):
    body = json.dumps({"query": query, "variables": variables}).encode()
    req = urllib.request.Request(API, data=body, headers={
        "Authorization": f"bearer {token}",
        "Content-Type": "application/json",
        "User-Agent": "profile-projects",
    })
    try:
        with urllib.request.urlopen(req) as r:
            out = json.load(r)
    except urllib.error.HTTPError as e:
        raise SystemExit(f"GraphQL HTTP {e.code}: {e.read().decode()[:500]}")
    if out.get("errors"):
        raise SystemExit("GraphQL errors: " + json.dumps(out["errors"]))
    return out["data"]


def esc(s):
    return s.replace("&", "&amp;").replace("<", "&lt;").replace(">", "&gt;")


def entry(repo):
    lang = repo["primaryLanguage"]
    lang = f" &nbsp;·&nbsp; <samp>{esc(lang['name'].lower())}</samp>" if lang else ""
    if repo["isPrivate"]:
        return f"**{esc(repo['name'])}**{lang} &nbsp;·&nbsp; <samp>private</samp>"
    line = f"**[{esc(repo['name'])}]({repo['url']})**{lang}"
    desc = (repo["description"] or "").strip()
    return f"{line}  \n{esc(desc)}" if desc else line


def topics_of(r):
    return {t["topic"]["name"] for t in r["repositoryTopics"]["nodes"]}


def clusters(repos, login):
    live = [r for r in repos if not r["isArchived"] and r["name"].lower() != login.lower()]
    groups = [(h, [r for r in live if topics & topics_of(r)]) for h, topics in GROUPS]
    placed = {r["name"] for _, ms in groups for r in ms}
    loose = [r for r in live if r["name"] not in placed]
    return [(h, ms) for h, ms in groups if ms], loose


# ---------------------------------------------------------------------------
# the web: clusters of threads that drift. SMIL animation (plays in README
# images); every node and thread end shares one clock so threads stay attached.
# ---------------------------------------------------------------------------
WEB_STYLE = """<style>
.hub{fill:#dd2d51}.halo{fill:#dd2d51;opacity:.12}.pub{fill:#dd2d51}.prv{fill:#f6f8fa;stroke:#dd2d51}
.lse{fill:none;stroke:#8c959f}.t1{stroke:#dd2d51;opacity:.55}.t2{stroke:#dd2d51;opacity:.18}
.t3{stroke:#8c959f;opacity:.45}.hl{fill:#dd2d51}.nm{fill:#1f2328}.mu{fill:#59636e}
@media(prefers-color-scheme:dark){
.hub,.halo,.pub,.hl{fill:#e04060}.prv{fill:#0d1117;stroke:#e04060}.t1,.t2{stroke:#e04060}
.lse,.t3{stroke:#6e7681}.nm{fill:#e6edf3}.mu{fill:#9198a1}}
</style>"""
W_W, W_H, DUR, K = 760, 400, 16, 8
SANSF = "Montserrat, -apple-system, 'Segoe UI', Helvetica, Arial, sans-serif"
MONOF = "ui-monospace, SFMono-Regular, Menlo, Consolas, monospace"


def drift(name, x, y, amp):
    """K points on a small wobbling loop around (x, y), phase from the name."""
    import math, zlib
    h = zlib.crc32(name.encode())
    ph, ax, ay = (h % 360) * math.pi / 180, amp * (0.6 + (h >> 8) % 40 / 100), amp * (0.6 + (h >> 16) % 40 / 100)
    pts = [(x + ax * math.cos(ph + 2 * math.pi * k / K), y + ay * math.sin(2 * ph + 2 * math.pi * k / K))
           for k in range(K)]
    return pts + [pts[0]]


def anim(attr, vals):
    return (f'<animate attributeName="{attr}" dur="{DUR}s" repeatCount="indefinite" '
            f'values="{";".join(f"{v:.1f}" for v in vals)}"/>')


def thread(a, b, cls, extra=""):
    (ax, ay), (bx, by) = a[0], b[0]
    return (f'<line class="{cls}" x1="{ax:.1f}" y1="{ay:.1f}" x2="{bx:.1f}" y2="{by:.1f}"{extra}>'
            + anim("x1", [p[0] for p in a]) + anim("y1", [p[1] for p in a])
            + anim("x2", [p[0] for p in b]) + anim("y2", [p[1] for p in b]) + "</line>")


def build_web(groups, loose):
    import math
    hubs_at = [(165, 175), (390, 120), (615, 185)]
    hubs, nodes, lines, labels = [], [], [], []
    for gi, (heading, members) in enumerate(groups):
        hx, hy = hubs_at[gi % 3]
        hp = drift(heading, hx, hy, 5)
        n = len(members)
        ups = 0
        mpaths = []
        for i, r in enumerate(members):
            ang = math.pi / 2 + (i - (n - 1) / 2) * (2.1 / max(1, n - 1) if n > 1 else 0) + (0 if gi != 1 else math.pi)
            if gi == 1:
                ang = -math.pi / 2 + (i - (n - 1) / 2) * 0.95
            rad = 92 + (i % 2) * 14
            x, y = hx + rad * math.cos(ang), hy + rad * math.sin(ang) * 0.85
            p = drift(r["name"], x, y, 8)
            mpaths.append(p)
            ups += 1 if math.sin(ang) < 0 else -1
            lines.append(thread(hp, p, "t1", ' stroke-width="1.3"'))
            cls = "prv" if r["isPrivate"] else "pub"
            nodes.append(f'<circle class="{cls}" r="4.5" stroke-width="1.6" cx="{p[0][0]:.1f}" cy="{p[0][1]:.1f}">'
                         + anim("cx", [q[0] for q in p]) + anim("cy", [q[1] for q in p]) + "</circle>")
            above = math.sin(ang) < 0
            dy = (-11 - 14 * (i % 2)) if above else (19 + 16 * (i % 2))
            half = len(r["name"]) * 3.4                     # ~half the label width at 11px mono
            shift = min(0, (W_W - 6) - (x + half)) + max(0, 6 - (x - half))
            anchor, dx = "middle", shift
            labels.append(f'<text class="nm" font-family="{MONOF}" font-size="11" text-anchor="{anchor}" '
                          f'x="{p[0][0] + dx:.1f}" y="{p[0][1] + dy:.1f}">{esc(r["name"])}'
                          + anim("x", [q[0] + dx for q in p]) + anim("y", [q[1] + dy for q in p]) + "</text>")
        hubs.append((heading, hp, 32 if ups > 0 else -24))
        for a in range(len(mpaths)):                       # the web inside a cluster
            for b in range(a + 1, len(mpaths)):
                lines.append(thread(mpaths[a], mpaths[b], "t2", ' stroke-width=".9"'))
    for a in range(len(hubs)):                             # loose ties between clusters
        for b in range(a + 1, len(hubs)):
            lines.append(thread(hubs[a][1], hubs[b][1], "t3", ' stroke-width="1" stroke-dasharray="3 6"'))
    hub_svg = []
    for heading, hp, ldy in hubs:
        hub_svg.append(f'<circle class="halo" cx="{hp[0][0]:.1f}" cy="{hp[0][1]:.1f}" r="16">'
                       + anim("cx", [q[0] for q in hp]) + anim("cy", [q[1] for q in hp])
                       + '<animate attributeName="r" values="13;19;13" dur="4s" repeatCount="indefinite"/></circle>')
        hub_svg.append(f'<circle class="hub" cx="{hp[0][0]:.1f}" cy="{hp[0][1]:.1f}" r="7">'
                       + anim("cx", [q[0] for q in hp]) + anim("cy", [q[1] for q in hp]) + "</circle>")
        title = heading.replace("&amp;", "&").upper()
        hub_svg.append(f'<text class="hl" font-family="{SANSF}" font-size="11" font-weight="700" letter-spacing="2" '
                       f'text-anchor="middle" x="{hp[0][0]:.1f}" y="{hp[0][1] + ldy:.1f}">{esc(title)}'
                       + anim("x", [q[0] for q in hp]) + anim("y", [q[1] + ldy for q in hp]) + "</text>")
    # loose threads: unclustered repos drift on their own, no connections
    lx0 = W_W / 2 - (len(loose) - 1) * 70
    for i, r in enumerate(loose):
        p = drift(r["name"], lx0 + i * 140, 330, 10)
        nodes.append(f'<circle class="lse" r="4.5" stroke-width="1.4" stroke-dasharray="2 2" '
                     f'cx="{p[0][0]:.1f}" cy="{p[0][1]:.1f}">'
                     + anim("cx", [q[0] for q in p]) + anim("cy", [q[1] for q in p]) + "</circle>")
        labels.append(f'<text class="mu" font-family="{MONOF}" font-size="11" text-anchor="start" '
                      f'x="{p[0][0] + 9:.1f}" y="{p[0][1] + 4:.1f}">{esc(r["name"])}'
                      + anim("x", [q[0] + 9 for q in p]) + anim("y", [q[1] + 4 for q in p]) + "</text>")
    legend = (f'<g font-family="{SANSF}" font-size="10.5">'
              f'<circle class="pub" cx="16" cy="{W_H - 14}" r="4"/><text class="mu" x="26" y="{W_H - 10}">public</text>'
              f'<circle class="prv" cx="86" cy="{W_H - 14}" r="4" stroke-width="1.5"/><text class="mu" x="96" y="{W_H - 10}">private</text>'
              f'<circle class="lse" cx="160" cy="{W_H - 14}" r="4" stroke-width="1.4" stroke-dasharray="2 2"/>'
              f'<text class="mu" x="170" y="{W_H - 10}">not in a cluster</text></g>')
    alt = "; ".join(f'{h.replace("&amp;", "and")}: {", ".join(r["name"] for r in ms)}' for h, ms in groups)
    if loose:
        alt += "; not in a cluster: " + ", ".join(r["name"] for r in loose)
    return (f'<svg xmlns="http://www.w3.org/2000/svg" viewBox="0 0 {W_W} {W_H}" width="{W_W}" height="{W_H}" '
            f'role="img" aria-label="Project web. {esc(alt)}">{WEB_STYLE}'
            f'{"".join(lines)}{"".join(hub_svg)}{"".join(nodes)}{"".join(labels)}{legend}</svg>'), alt


def build(repos, login):
    groups, loose = clusters(repos, login)
    svg, alt = build_web(groups, loose)
    with open("art/projects-web.svg", "w") as f:
        f.write(svg)
    public = [r for _, ms in groups for r in ms if not r["isPrivate"]] + [r for r in loose if not r["isPrivate"]]
    links = " &nbsp;·&nbsp; ".join(f'<a href="{r["url"]}">{esc(r["name"])}</a>' for r in public)
    return (f'<p align="center">\n  <img src="art/projects-web.svg" width="100%" alt="Project web. {esc(alt)}">\n</p>\n\n'
            + (f'<p align="center"><sub>open source: &nbsp;{links}</sub></p>\n' if public else ""))


def main():
    token = os.environ.get("PROFILE_TOKEN", "").strip()
    if not token:
        print("PROFILE_TOKEN not set; leaving the projects section as it is")
        return
    login = os.environ.get("GH_LOGIN", "").strip()
    if not login:
        login = gql(token, "{ viewer { login } }", {})["viewer"]["login"]
    repos = gql(token, QUERY, {"login": login})["user"]["repositories"]["nodes"]

    with open("README.md") as f:
        readme = f.read()
    if START not in readme or END not in readme:
        sys.exit("README.md is missing the PROJECTS markers")
    section = f"{START}\n\n{build(repos, login)}\n{END}"
    new = re.sub(re.escape(START) + r".*?" + re.escape(END),
                 lambda _: section, readme, flags=re.S)
    if new != readme:
        with open("README.md", "w") as f:
            f.write(new)
        print("projects section updated")
    else:
        print("projects section unchanged")


if __name__ == "__main__":
    main()
