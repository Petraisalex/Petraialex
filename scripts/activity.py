#!/usr/bin/env python3
"""
activity.py: count real activity across every repo you can reach (private
included), leaving out repos that only inflate the numbers (this profile repo).

Counts, per day (Europe/Amsterdam), over the last 365 days:
    commits         you authored on each repo's default branch
    pull requests   you opened
    issues          you opened
    code reviews    you submitted on other people's pull requests

Writes:
    activity.json       {calendar, totals, repos}  (read by generate_stats.py)
    art/activity.svg    "contributed to" list + four-axis activity chart

Env: ACTIVITY_TOKEN, else PROFILE_TOKEN, else GITHUB_TOKEN; GH_LOGIN optional.
If the token cannot read some repo, nothing is written: the last full snapshot
stays, so a weaker token never makes the profile look emptier than it is.
"""
import os
import sys
import json
import datetime
import urllib.request
import urllib.error
from zoneinfo import ZoneInfo

API = "https://api.github.com/graphql"
# read-only keys, tried in order; each may see a different set of repos
# (PROFILE_TOKEN: your own repos; VCM_TOKEN: made on the vcmaastricht account)
TOKENS = [t for t in (os.environ.get(k, "").strip()
                      for k in ("ACTIVITY_TOKEN", "PROFILE_TOKEN", "VCM_TOKEN")) if t]
TOKENS = TOKENS or [os.environ["GITHUB_TOKEN"]]
LOGIN = os.environ.get("GH_LOGIN", "").strip()
TZ = ZoneInfo("Europe/Amsterdam")
EXCLUDE = {"Petraisalex/Petraisalex"}     # the profile repo: README edits, not work

ROOT = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))


class NoAccess(Exception):
    pass


def gql(query, variables, token=None):
    body = json.dumps({"query": query, "variables": variables}).encode()
    req = urllib.request.Request(API, data=body, headers={
        "Authorization": f"bearer {token or TOKENS[0]}", "Content-Type": "application/json",
        "User-Agent": "profile-activity"})
    try:
        with urllib.request.urlopen(req) as r:
            out = json.load(r)
    except urllib.error.HTTPError as e:
        raise NoAccess(f"HTTP {e.code}: {e.read().decode()[:300]}")
    if out.get("errors"):
        msg = json.dumps(out["errors"])[:300]
        if any(e.get("type") in ("FORBIDDEN", "NOT_FOUND") or "not accessible" in e.get("message", "")
               for e in out["errors"]):
            raise NoAccess(msg)
        raise SystemExit("GraphQL error: " + msg)        # a bug, not a permission gap
    return out["data"]


def day_of(ts):
    t = datetime.datetime.fromisoformat(ts.replace("Z", "+00:00"))
    return t.astimezone(TZ).date().isoformat()


def collect():
    login = LOGIN or gql("{viewer{login}}", {})["viewer"]["login"]
    uid = gql("query($l:String!){user(login:$l){id}}", {"l": login})["user"]["id"]
    today = datetime.datetime.now(TZ).date()
    start = today - datetime.timedelta(days=364)
    since = datetime.datetime.combine(start, datetime.time(), TZ).isoformat()

    # every repo you own, collaborate on, or reach through an organisation
    seen = {}                        # nameWithOwner -> (repo, [tokens that list it])
    q = """query($after:String){ viewer{ repositories(first:100,after:$after,
          ownerAffiliations:[OWNER,COLLABORATOR,ORGANIZATION_MEMBER]){
          pageInfo{hasNextPage endCursor} nodes{ nameWithOwner name owner{login} isPrivate } } } }"""
    for tok in TOKENS:
        after = None
        while True:
            r = gql(q, {"after": after}, tok)["viewer"]["repositories"]
            for n in r["nodes"]:
                seen.setdefault(n["nameWithOwner"], (n, []))[1].append(tok)
            if not r["pageInfo"]["hasNextPage"]:
                break
            after = r["pageInfo"]["endCursor"]
    repos = [v[0] for v in seen.values()]

    events = {}                      # date -> count
    kinds = {"commits": 0, "pull requests": 0, "issues": 0, "code review": 0}
    per_repo = {}

    def add(date, kind, repo):
        if date < start.isoformat() or repo in EXCLUDE:
            return
        events[date] = events.get(date, 0) + 1
        kinds[kind] += 1
        per_repo.setdefault(repo, {"private": False, "commits": 0, "pull requests": 0,
                                   "issues": 0, "code review": 0})[kind] += 1

    # a weaker token may simply not list some repos; never drop one we knew about
    try:
        known = set(json.load(open(os.path.join(ROOT, "activity.json")))["repos"])
    except (OSError, ValueError, KeyError):
        known = set()
    missing = known - {r["nameWithOwner"] for r in repos}
    if missing:
        raise NoAccess("cannot see " + ", ".join(sorted(missing)))

    hq = """query($o:String!,$n:String!,$uid:ID!,$since:GitTimestamp!,$after:String){
      repository(owner:$o,name:$n){ defaultBranchRef{ target{ ... on Commit{
        history(first:100,after:$after,since:$since,author:{id:$uid}){
          pageInfo{hasNextPage endCursor} nodes{ authoredDate } } } } } } }"""
    private = {}
    for repo in repos:
        name = repo["nameWithOwner"]
        private[name] = repo["isPrivate"]
        if name in EXCLUDE:
            continue
        dates, err = None, None
        for tok in seen[name][1]:                      # first key that can read it wins
            try:
                dates, after = [], None
                while True:
                    r = gql(hq, {"o": repo["owner"]["login"], "n": repo["name"], "uid": uid,
                                 "since": since, "after": after}, tok)["repository"]
                    if not r or not r["defaultBranchRef"]:
                        break                          # empty repo
                    h = r["defaultBranchRef"]["target"]["history"]
                    dates += [n["authoredDate"] for n in h["nodes"]]
                    if not h["pageInfo"]["hasNextPage"]:
                        break
                    after = h["pageInfo"]["endCursor"]
                break
            except NoAccess as e:
                dates, err = None, e
        if dates is None:
            raise NoAccess(f"{name}: {err}")
        for ts in dates:
            add(day_of(ts), "commits", name)

    def search(query, fields):
        """Run with every key; each sees its own repos. De-duplicated by node id."""
        out = {}
        sq = """query($q:String!,$after:String){ search(type:ISSUE,query:$q,first:100,after:$after){
          pageInfo{hasNextPage endCursor} nodes{ ... on Node{ id } %s } } }""" % fields
        for tok in TOKENS:
            after = None
            while True:
                s = gql(sq, {"q": query, "after": after}, tok)["search"]
                out.update({n["id"]: n for n in s["nodes"] if n})
                if not s["pageInfo"]["hasNextPage"]:
                    break
                after = s["pageInfo"]["endCursor"]
        return list(out.values())

    window = f"created:>={start.isoformat()}"
    for n in search(f"is:pr author:{login} {window}",
                    "... on PullRequest{ createdAt repository{nameWithOwner} }"):
        add(day_of(n["createdAt"]), "pull requests", n["repository"]["nameWithOwner"])
    for n in search(f"is:issue author:{login} {window}",
                    "... on Issue{ createdAt repository{nameWithOwner} }"):
        add(day_of(n["createdAt"]), "issues", n["repository"]["nameWithOwner"])
    for n in search(f"is:pr reviewed-by:{login} -author:{login} updated:>={start.isoformat()}",
                    "... on PullRequest{ repository{nameWithOwner} "
                    "reviews(first:50,author:\"%s\"){ nodes{ submittedAt } } }" % login):
        for rv in n["reviews"]["nodes"]:
            if rv["submittedAt"]:
                add(day_of(rv["submittedAt"]), "code review", n["repository"]["nameWithOwner"])

    for name, v in per_repo.items():
        v["private"] = private.get(name, True)

    # calendar in the shape generate_stats.py already draws (weeks start on Sunday)
    first = start - datetime.timedelta(days=(start.weekday() + 1) % 7)
    weeks, d = [], first
    while d <= today:
        week = []
        for _ in range(7):
            if start <= d <= today:
                week.append({"date": d.isoformat(), "weekday": (d.weekday() + 1) % 7,
                             "contributionCount": events.get(d.isoformat(), 0)})
            d += datetime.timedelta(days=1)
        if week:
            weeks.append({"firstDay": week[0]["date"], "contributionDays": week})
    cal = {"totalContributions": sum(events.values()), "weeks": weeks}
    return {"login": login, "calendar": cal, "totals": kinds, "repos": per_repo,
            "excluded": sorted(EXCLUDE)}


# ---------------------------------------------------------------------------
# drawing
# ---------------------------------------------------------------------------
FONT = "'JetBrains Mono', ui-monospace, SFMono-Regular, monospace"
STYLE = """<style>
  .s{fill:#1f2328} .m{fill:#59636e} .a{fill:#dd2d51} .ax{stroke:#d0d7de}
  .shape{fill:#dd2d51;fill-opacity:.18;stroke:#dd2d51;stroke-width:2}
  .dot{fill:#ffffff;stroke:#dd2d51;stroke-width:2} .trk{fill:#eaeef2}
  @media(prefers-color-scheme:dark){
    .s{fill:#f0f6fc} .m{fill:#9198a1} .a{fill:#e04060} .ax{stroke:#30363d}
    .shape{fill:#e04060;stroke:#e04060} .dot{fill:#0d1117;stroke:#e04060} .trk{fill:#21262d}
  }
</style>"""


def esc(s):
    return str(s).replace("&", "&amp;").replace("<", "&lt;").replace(">", "&gt;").replace('"', "&quot;")


def build_svg(data):
    W, H = 900, 300
    t, repos = data["totals"], data["repos"]
    total = sum(t.values()) or 1
    out = [f'<text class="m" x="20" y="34" font-size="11" letter-spacing="1.4">CONTRIBUTED TO</text>']

    # left: repos ranked by activity, with a small bar each
    ranked = sorted(repos.items(), key=lambda kv: -sum(v for k, v in kv[1].items() if k != "private"))[:7]
    top = max((sum(v for k, v in r.items() if k != "private") for _, r in ranked), default=1)
    for i, (name, r) in enumerate(ranked):
        n = sum(v for k, v in r.items() if k != "private")
        y = 70 + i * 30
        short = name.split("/", 1)[1] if name.startswith(data["login"] + "/") else name
        tag = '<tspan class="m" font-size="10"> · private</tspan>' if r["private"] else ""
        out.append(f'<text class="s" x="20" y="{y}" font-size="13">{esc(short)}{tag}</text>')
        out.append(f'<rect class="trk" x="350" y="{y - 9}" width="150" height="7" rx="3.5"/>'
                   f'<rect class="a" x="350" y="{y - 9}" width="{max(3, 150 * n / top):.1f}" height="7" rx="3.5"/>'
                   f'<text class="m" x="512" y="{y - 2}" font-size="11">{n}</text>')
    if not ranked:
        out.append('<text class="m" x="20" y="66" font-size="13">nothing yet</text>')

    # right: four-axis chart, same layout as GitHub's activity overview
    cx, cy, R = 720, 150, 108
    axes = [("code review", 0, -1), ("issues", 1, 0), ("pull requests", 0, 1), ("commits", -1, 0)]
    pts = []
    for name, dx, dy in axes:
        out.append(f'<line class="ax" x1="{cx}" y1="{cy}" x2="{cx + dx * R}" y2="{cy + dy * R}" stroke-width="1.5"/>')
        frac = t[name] / total
        r = 4 + (R - 4) * frac
        pts.append((cx + dx * r, cy + dy * r, frac, name, dx, dy))
    out.append('<polygon class="shape" points="%s"/>' % " ".join(f"{x:.1f},{y:.1f}" for x, y, *_ in pts))
    for x, y, frac, name, dx, dy in pts:
        if frac > 0:
            out.append(f'<circle class="dot" cx="{x:.1f}" cy="{y:.1f}" r="4"/>')
        pct = f"{frac * 100:.0f}%"
        lx, ly = cx + dx * (R + 14), cy + dy * (R + 14)
        anchor = "middle" if dx == 0 else ("start" if dx > 0 else "end")
        if dy < 0:
            out.append(f'<text class="m" x="{lx}" y="{ly}" font-size="11" text-anchor="middle">{name} {pct}</text>')
        elif dy > 0:
            out.append(f'<text class="m" x="{lx}" y="{ly + 10}" font-size="11" text-anchor="middle">{name} {pct}</text>')
        else:
            out.append(f'<text class="s" x="{lx}" y="{ly - 3}" font-size="13" text-anchor="{anchor}">{pct or "0%"}</text>'
                       f'<text class="m" x="{lx}" y="{ly + 13}" font-size="11" text-anchor="{anchor}">{name}</text>')
    label = ("Activity: " + ", ".join(f"{v} {k}" for k, v in t.items())
             + ". Contributed to " + ", ".join(n.split("/")[-1] for n, _ in ranked))
    return (f'<svg xmlns="http://www.w3.org/2000/svg" viewBox="0 0 {W} {H}" width="{W}" height="{H}" '
            f'role="img" aria-label="{esc(label)}" font-family="{FONT}">{STYLE}{"".join(out)}</svg>')


def main():
    try:
        data = collect()
    except NoAccess as e:
        print(f"activity: token can't read everything ({e}); keeping the last snapshot")
        return 0
    with open(os.path.join(ROOT, "activity.json"), "w") as f:
        json.dump(data, f, indent=1, sort_keys=True)
    with open(os.path.join(ROOT, "art", "activity.svg"), "w") as f:
        f.write(build_svg(data))
    print("activity:", data["totals"], "total", data["calendar"]["totalContributions"])
    return 0


if __name__ == "__main__":
    sys.exit(main())
