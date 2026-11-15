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


def build(repos):
    out = []
    for heading, topics in GROUPS:
        members = [r for r in repos
                   if not r["isArchived"]
                   and topics & {t["topic"]["name"] for t in r["repositoryTopics"]["nodes"]}]
        if not members:
            continue
        out.append(f"<samp><b>{heading}</b></samp>\n")
        out.extend(entry(r) + "\n" for r in members)
    return "\n".join(out)


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
    section = f"{START}\n\n{build(repos)}\n{END}"
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
