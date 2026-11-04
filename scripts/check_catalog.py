#!/usr/bin/env python3
"""Check the helper catalog (.pengupool/catalog.json) and the helpers it lists.

The catalog is a PenguPool-only file: {name?, description?, agents: [{name, repo, path?, ref?, sha?, ...}]}.
.claude-plugin/marketplace.json is kept for installs that still read it; both files must describe the
same helpers. A helper of this repository has no `sha`: PenguPool follows its `ref` (default main), so it
is read from this checkout. An optional `sha` pins a helper kept in another repository, read through the API.

For every plugin: a unique name, a github or git-subdir source (its sha, when given, a 40-hex commit
that exists on that repo), an AGENTS.md, and skills/<name>/SKILL.md files whose
frontmatter has a description and a name equal to the directory (under source.path for
git-subdir), and a body of at most 8 KiB and 500 lines. A helper kept in this repository
must sit at agents/<category>/<name>. No harness folders (.claude/, .codex/, ...) in a helper,
no harness-only tool names in its AGENTS.md or SKILL.md files, and no harness
name in the files that instruct an agent, outside an optional addons/<harness>/ folder or a skill
named for its harness. Every `pengupool <command>` those files name must be one the app's
`pengupool help` lists. Reads a helper kept in another repo through
the GitHub API ($GH_TOKEN, optional, for its rate limit). Exits 1 and prints
every problem found.
"""
import argparse
import base64
import json
import os
import re
import subprocess
import sys
import urllib.error
import urllib.request

API = "https://api.github.com"
CATALOG = ".pengupool/catalog.json"
MARKETPLACE = ".claude-plugin/marketplace.json"
SHA = re.compile(r"^[0-9a-f]{40}$")
MAX_BODY_BYTES, MAX_BODY_LINES = 8192, 500  # a SKILL.md body's limits
THIS_REPO = "nduwork/pengupool-agent-hub"
# Helpers run in any agent harness: no harness folders, and no harness-only tool names, config
# files or model ids in AGENTS.md or SKILL.md. Say "run the command", "read the file" instead.
HARNESS_DIRS = {".claude", ".codex", ".pi", ".cursor", ".gemini", ".opencode", ".agents"}
HARNESS_FILES = {"CLAUDE.md", "GEMINI.md"}
# Possible secrets in AGENTS.md and skills/. This PR check is the only one: PenguPool does not
# check a helper again when it adds one.
SECRET = re.compile(r"(?i)(AKIA[0-9A-Z]{16}|sk-[A-Za-z0-9_-]{20,}|sk-ant-[A-Za-z0-9_-]{20,}"
                    r"|gh[pousr]_[A-Za-z0-9]{30,}|xox[abpr]-[A-Za-z0-9-]{10,}|-----BEGIN [A-Z ]*PRIVATE KEY-----"
                    r"|(api[_-]?key|secret|password|token)\s*[:=]\s*['\"]?[A-Za-z0-9_\-/+=]{16,})")
HARNESS_WORDS = re.compile(
    r"\b(?:TodoWrite|TodoRead|SendMessage|AskUserQuestion|ExitPlanMode|NotebookEdit|codex_ask"
    r"|(?:Task|Bash|Read|Edit|Write|Grep|Glob|WebFetch|WebSearch) tool|Claude Code"
    r"|claude-(?:opus|sonnet|haiku|fable)[\w.-]*)\b|CLAUDE\.md|~/\.claude|\.claude/|\.codex/")
# Any harness name in the files that tell an agent what to do. A feature only one harness has stays
# as a clearly optional add-on, named for its harness: a folder addons/<harness>/ or a skill whose
# name contains the harness. A line that points at such an add-on may name its harness.
HARNESS_NAMES = ("claude", "codex", "gemini", "copilot", "opencode", "pi", "omp")
HARNESS_NAME = re.compile(r"\b(?:" + "|".join(HARNESS_NAMES) + r")\b", re.I)
# Tools a helper operates that happen to be built on a harness (not the agent it runs in).
ENGINE_FILES = {"git-ci-agent": {"scripts/ci_triage.sh", ".github/workflows/triage.yml"}}  # local model runner
# The commands `pengupool help` lists (0.11.1), and the second word where a command takes one.
# Keep in step with the app's help so a helper is never told to run a command the app lacks.
PENGUPOOL_COMMANDS = {"daemon", "new", "ls", "attach", "kill", "web", "send", "search", "memory",
                      "team", "epic", "decide", "eval", "rpc", "bridge", "hook", "worker", "version", "help"}
PENGUPOOL_SUBCOMMANDS = {"memory": {"search"}, "team": {"request"}, "epic": {"propose", "milestone"}}
PENGUPOOL_CALL = re.compile(r"\bpengupool +([a-z][\w-]*)(?: +([a-z][\w-]*))?")


def get(path):
    req = urllib.request.Request(API + path, headers={"Accept": "application/vnd.github+json"})
    if os.environ.get("GH_TOKEN"):
        req.add_header("Authorization", "Bearer " + os.environ["GH_TOKEN"])
    try:
        with urllib.request.urlopen(req) as r:
            return json.load(r)
    except urllib.error.HTTPError as e:
        if e.code in (404, 422):  # 422: unknown commit
            return None
        raise


def frontmatter(text):
    m = re.match(r"^---\n(.*?)\n---", text, re.S)
    if not m:
        return {}
    out = {}
    for line in m.group(1).splitlines():
        k, sep, v = line.partition(":")
        if sep and not line.startswith((" ", "\t")):
            out[k.strip()] = v.strip().strip("\"'")
    return out


def skill_problems(dirname, text):
    fm = frontmatter(text)
    probs = []
    if fm.get("name") != dirname:
        probs.append(f"skills/{dirname}/SKILL.md: frontmatter name {fm.get('name')!r} must be {dirname!r}")
    if not fm.get("description"):
        probs.append(f"skills/{dirname}/SKILL.md: no description in frontmatter")
    body = re.sub(r"^---\n.*?\n---", "", text, count=1, flags=re.S)
    size, lines = len(body.encode()), body.count("\n")
    if size > MAX_BODY_BYTES or lines > MAX_BODY_LINES:
        probs.append(f"skills/{dirname}/SKILL.md: body is {size} bytes, {lines} lines; the limit is "
                     f"{MAX_BODY_BYTES} bytes and {MAX_BODY_LINES} lines (move detail to references/)")
    return probs


def layout_problems(p):
    # A helper kept in this repository lives at agents/<category>/<name>: the catalog's category is
    # the source of truth for its group, and the folder mirrors it.
    src = p.get("source") or {}
    if not (isinstance(src, dict) and src.get("source") == "git-subdir"
            and re.match(r"^https://github\.com/" + re.escape(THIS_REPO) + r"(\.git)?$", src.get("url", ""))):
        return []
    want = f"agents/{p.get('category', '<category>')}/{p.get('name', '?')}"
    if not p.get("category"):
        return [f"no category; set one and keep the folder at {want}"]
    if src.get("path", "").strip("/") != want:
        return [f"source.path {src.get('path')!r} must be {want!r} (its category and name)"]
    return []


def harness_problems(fname, text):
    return [f"{fname}: names {w!r}, which only one agent harness has; say what to do instead"
            for w in sorted(set(m.group(0) for m in HARNESS_WORDS.finditer(text)))]


def harness_dir_problems(base, paths):
    hits = sorted({p for p in paths if p.startswith(base)
                   and (HARNESS_DIRS & set(p[len(base):].split("/"))
                        or p[len(base):] in HARNESS_FILES
                        or (p[len(base):].startswith("skills/") and p.rsplit("/", 1)[-1] in HARNESS_FILES))})
    return [f"{h}: harness-specific folder; a helper is AGENTS.md + skills/ only" for h in hits[:5]]


def scanned(rel):
    # The files that tell an agent what to do, install it or run it. History (logs/, CHANGELOG.md),
    # research notes and tests are about harnesses, not instructions to use one.
    return (rel in ("AGENTS.md", "README.md", "package.json", "pyproject.toml")
            or rel.startswith(("skills/", "scripts/", ".github/workflows/")) or rel.endswith(".sh"))


def addon_refs(rels):
    skills = {r.split("/")[1] for r in rels if r.startswith("skills/") and r.count("/") >= 2}
    named = {k for k in skills if set(k.lower().split("-")) & set(HARNESS_NAMES)}
    return named, [f"addons/{h}" for h in HARNESS_NAMES] + sorted(named)


def secret_problems(files):
    """No possible secret in AGENTS.md or anywhere under skills/."""
    probs = []
    for rel, text in sorted(files.items()):
        m = (rel == "AGENTS.md" or rel.startswith("skills/")) and SECRET.search(text)
        if m:
            probs.append(f"{rel}:{text[:m.start()].count(chr(10)) + 1}: possible secret "
                         "(use a placeholder such as <token>)")
    return probs


def cli_problems(files):
    """files: {path relative to the helper: text}. One problem per unknown `pengupool` command."""
    probs = []
    for rel, text in sorted(files.items()):
        if not (scanned(rel) or rel.startswith("skills/")):
            continue
        for m in PENGUPOOL_CALL.finditer(text):
            cmd, sub = m.groups()
            subs = PENGUPOOL_SUBCOMMANDS.get(cmd)
            if cmd not in PENGUPOOL_COMMANDS or (subs and sub not in subs):
                line = text[:m.start()].count("\n") + 1
                probs.append(f"{rel}:{line}: `{m.group(0)}` is not a command `pengupool help` lists")
    return probs


def harness_name_problems(name, files):
    """files: {path relative to the helper: text}. Returns one problem per offending file."""
    named, refs = addon_refs(files)
    probs = []
    for rel, text in sorted(files.items()):
        top = rel.split("/")
        if (not scanned(rel) or rel in ENGINE_FILES.get(name, set()) or top[0] == "addons"
                or (top[0] == "skills" and len(top) > 2 and top[1] in named)):
            continue
        bad = [i for i, line in enumerate(text.splitlines(), 1)
               if HARNESS_NAME.search(line) and not any(r in line for r in refs)]
        if bad:
            probs.append(f"{rel}:{bad[0]}: names an agent harness ({len(bad)} line(s)); keep a "
                         "harness-only feature in addons/<harness>/ or a skill named for it")
    return probs


BLOBS = {}


def blob_text(repo, sha):
    if sha not in BLOBS:
        b = get(f"/repos/{repo}/git/blobs/{sha}") or {}
        try:
            BLOBS[sha] = base64.b64decode(b.get("content", "")).decode()
        except (UnicodeDecodeError, ValueError):
            BLOBS[sha] = ""
    return BLOBS[sha]


def check_plugin(p, seen):
    name = p.get("name", "?")
    probs = layout_problems(p)
    if name in seen:
        probs.append("duplicate name")
    seen.add(name)
    src = p.get("source") or {}
    if not isinstance(src, dict):
        return probs + ["source must be an object"]
    sha, base = src.get("sha"), ""
    if src.get("source") == "github":
        repo = src.get("repo", "")
    elif src.get("source") == "git-subdir":
        m = re.match(r"^https://github\.com/([\w.-]+/[\w.-]+?)(?:\.git)?$", src.get("url", ""))
        repo, base = (m.group(1) if m else ""), src.get("path", "").strip("/") + "/"
        if base == "/" or ".." in base.split("/"):
            return probs + ["git-subdir source needs a path inside the repo"]
    else:
        repo = ""
    if not repo:
        return probs + ["source must be {source: github, repo} or {source: git-subdir, url: https://github.com/owner/name.git, path}"]
    if sha is not None and not SHA.match(str(sha)):
        return probs + [f"source.sha {sha!r} is not a full 40-character commit"]
    if repo == THIS_REPO:  # follows main: checked as this checkout has it (on a PR, the merge commit)
        top = git_out("rev-parse", "--show-toplevel", cwd=os.path.dirname(os.path.abspath(__file__)))
        listed = git_out("ls-files", "-z", "--", base or ".", cwd=top) if top else None
        if listed is None:
            return probs + ["run the check in a git checkout of this repository"]

        def read(path):
            try:
                with open(os.path.join(top, path), encoding="utf-8") as f:
                    return f.read()
            except (OSError, UnicodeDecodeError):
                return ""
        sizes = {x: os.path.getsize(os.path.join(top, x)) for x in listed.split("\0")
                 if x and os.path.isfile(os.path.join(top, x))}  # a tracked file deleted locally is missing
        return probs + files_problems(name, base, sizes, read)
    sha = sha or src.get("ref") or "HEAD"
    if get(f"/repos/{repo}/commits/{sha}") is None:
        return probs + [f"{repo}@{sha[:7]} not found (missing commit, or the token cannot read the repo)"]
    tree = get(f"/repos/{repo}/git/trees/{sha}?recursive=1") or {}
    blobs = {t["path"]: t for t in tree.get("tree", []) if t.get("type") == "blob"}
    return probs + files_problems(name, base, {x: t.get("size", 0) for x, t in blobs.items()},
                                  lambda x: blob_text(repo, blobs[x]["sha"]))


def files_problems(name, base, sizes, read):
    """The checks on a helper's files. sizes: {repo path: bytes} of every file; read(path): its text."""
    probs = harness_dir_problems(base, list(sizes))
    mine = {x[len(base):]: x for x in sizes if x.startswith(base)}
    if "AGENTS.md" in mine:
        probs += harness_problems("AGENTS.md", read(mine["AGENTS.md"]))
    else:
        probs.append(f"{base}AGENTS.md missing")
    texts = {rel: read(x) for rel, x in mine.items()
             if sizes[x] < 200_000 and (scanned(rel) or rel.startswith("skills/"))}
    probs += harness_name_problems(name, texts) + secret_problems(texts) + cli_problems(texts)
    dirs = sorted({rel.split("/")[1] for rel in mine if rel.startswith("skills/") and rel.count("/") >= 2})
    if not dirs:
        probs.append(f"no {base}skills/<name>/ directories")
    for d in dirs:
        rel = f"skills/{d}/SKILL.md"
        if rel in mine:
            text = read(mine[rel])
            probs += skill_problems(d, text) + harness_problems(rel, text)
        else:
            probs.append(f"{base}{rel} missing")
    return probs


def plugin_to_agent(p):
    """A marketplace.json plugin as a catalog.json agent (the mapping PenguPool documents)."""
    src = p.get("source") or {}
    a = {"name": p.get("name"), "description": p.get("description"), "group": p.get("category"),
         "capabilities": p.get("keywords")}
    if src.get("source") == "github":
        a["repo"] = f"https://github.com/{src.get('repo', '')}.git"
    else:
        a["repo"], a["path"] = src.get("url"), src.get("path")
    a["ref"], a["sha"] = src.get("ref"), src.get("sha")
    a = {k: v for k, v in a.items() if v is not None}
    if "credits" in p:
        a["credits"] = p["credits"]
    return a


def agent_to_plugin(a):
    """A catalog.json agent as the plugin shape check_plugin reads."""
    m = re.match(r"^https://github\.com/([\w.-]+/[\w.-]+?)(?:\.git)?$", a.get("repo", ""))
    if a.get("path") is None and m:
        src = {"source": "github", "repo": m.group(1)}
    else:
        src = {"source": "git-subdir", "url": a.get("repo", ""), "path": a.get("path", "")}
    src.update({k: a[k] for k in ("ref", "sha") if k in a})
    plugin = {"name": a.get("name"), "description": a.get("description"), "category": a.get("group"),
              "keywords": a.get("capabilities"), "source": src}
    if "credits" in a:
        plugin["credits"] = a["credits"]
    return plugin


def credits_problems(credits):
    """Optional `credits`: the public repos a helper was distilled from, shown to people, never loaded
    into an agent's context. A non-empty list of {name, url}, url an https link."""
    if not (isinstance(credits, list) and credits):
        return ["credits must be a non-empty list of {name, url}"]
    probs = []
    for c in credits:
        if not (isinstance(c, dict) and set(c) == {"name", "url"} and isinstance(c["name"], str)
                and c["name"].strip() and isinstance(c["url"], str) and re.fullmatch(r"https://[^\s/]+\S*", c["url"])):
            probs.append(f"credits entry {c!r} must be {{name, url}}: a non-empty name and an https url")
    return probs


def catalog_problems(doc):
    """The format PenguPool reads: {name?, description?, agents: [{name, repo, sha?, ...}]}."""
    if not isinstance(doc, dict) or not isinstance(doc.get("agents"), list):
        return ["catalog must be an object with an `agents` list"]
    probs, seen = [], set()
    for i, a in enumerate(doc["agents"]):
        where = f"agents[{i}]"
        if not isinstance(a, dict):
            probs.append(f"{where}: must be an object")
            continue
        name = a.get("name")
        if not isinstance(name, str) or not name.strip():
            probs.append(f"{where}: name is required")
            continue
        where = f"{name}"
        if name.lower() in seen:
            probs.append(f"{where}: duplicate name (names are unique, case-insensitive)")
        seen.add(name.lower())
        if not (isinstance(a.get("repo"), str) and a["repo"].startswith("https://")):
            probs.append(f"{where}: repo is required, a https Git URL")
        if "sha" in a and isinstance(a.get("repo"), str) and re.match(
                r"^https://github\.com/" + re.escape(THIS_REPO) + r"(\.git)?$", a["repo"]):
            probs.append(f"{where}: a helper of this repository follows its ref; remove its sha")
        elif "sha" in a and not (isinstance(a["sha"], str) and SHA.match(a["sha"])):
            probs.append(f"{where}: sha, when given, is 40 hex characters")
        path = a.get("path")
        if path is not None and (not isinstance(path, str) or path.startswith("/")
                                 or {".", ".."} & set(path.split("/"))):
            probs.append(f"{where}: path must be a folder inside the repo, with no '.' or '..'")
        caps = a.get("capabilities")
        if caps is not None and not (isinstance(caps, list) and all(isinstance(c, str) for c in caps)):
            probs.append(f"{where}: capabilities must be a list of strings")
        if "credits" in a:
            probs += [f"{where}: {m}" for m in credits_problems(a["credits"])]
    return probs


def agreement_problems(agents, plugins):
    """The two catalog files must describe the same helpers."""
    mine = {a.get("name", "").lower(): a for a in agents}
    theirs = {p.get("name", "").lower(): plugin_to_agent(p) for p in plugins}
    probs = [f"{n}: in only one catalog file" for n in sorted(set(mine) ^ set(theirs))]
    for n in sorted(set(mine) & set(theirs)):
        diff = sorted(k for k in set(mine[n]) | set(theirs[n]) if mine[n].get(k, ...) != theirs[n].get(k, ...))
        if diff:
            probs.append(f"{n}: the catalog files disagree on {', '.join(diff)}")
    return probs


def git_out(*args, cwd=None):
    r = subprocess.run(["git", *args], capture_output=True, text=True, cwd=cwd)
    return r.stdout.strip() if r.returncode == 0 else None


def main(argv):
    ap = argparse.ArgumentParser(description="Check the helper catalog and the helpers it lists.")
    ap.add_argument("--catalog", default=CATALOG)
    ap.add_argument("--marketplace", default=MARKETPLACE, help="kept in step with the catalog until it is removed")
    args = ap.parse_args(argv)
    with open(args.catalog) as f:
        doc = json.load(f)
    market = args.marketplace if os.path.exists(args.marketplace) else None
    probs = {"catalog": catalog_problems(doc)}
    agents = doc.get("agents", []) if isinstance(doc.get("agents"), list) else []
    if market:
        with open(market) as f:
            probs["catalog files"] = agreement_problems(agents, json.load(f).get("plugins", []))
    failed = False
    for title, ps in probs.items():
        for pr in ps:
            print(f"FAIL {title}: {pr}")
            failed = True
    seen = set()
    for a in agents:
        ps = check_plugin(agent_to_plugin(a), seen) if isinstance(a, dict) and a.get("name") else []
        print(("FAIL " if ps else "ok   ") + str((a or {}).get("name", "?") if isinstance(a, dict) else "?"))
        for pr in ps:
            print("     - " + pr)
        failed |= bool(ps)
    return 1 if failed else 0


def catalog_selftest():
    ok = {"agents": [{"name": "a", "repo": "https://github.com/o/r.git", "sha": "a" * 40, "path": "agents/code/a"}]}
    assert catalog_problems(ok) == []
    assert catalog_problems({"agents": []}) == []
    assert len(catalog_problems([])) == 1 and len(catalog_problems({"plugins": []})) == 1
    bad = {"agents": [{"name": "A", "repo": "https://x/y.git", "sha": "a" * 40},
                      {"name": "a", "repo": "git@x:y", "sha": "abc", "path": "../x", "capabilities": "no"}, {"repo": "r"}]}
    assert len(catalog_problems(bad)) == 6
    plug = {"name": "a", "description": "d", "category": "code", "keywords": ["k"], "strict": False,
            "source": {"source": "git-subdir", "url": "https://github.com/o/r.git", "path": "agents/code/a",
                       "ref": "main", "sha": "a" * 40}}
    agent = plugin_to_agent(plug)
    assert agent == {"name": "a", "description": "d", "group": "code", "capabilities": ["k"],
                     "repo": "https://github.com/o/r.git", "path": "agents/code/a", "ref": "main", "sha": "a" * 40}
    assert agent_to_plugin(agent)["source"] == plug["source"] and agreement_problems([agent], [plug]) == []
    cred = [{"name": "o/src", "url": "https://github.com/o/src"}]
    assert catalog_problems({"agents": [{**ok["agents"][0], "credits": cred}]}) == []
    for badc in ([], [{"name": "o/src"}], [{"name": "", "url": "https://x"}], [{"name": "n", "url": "http://x"}],
                 [{"name": "n", "url": "https://x", "extra": 1}], "o/src", None,
                 [{"name": "n", "url": "https://github.com/o/r\n"}], [{"name": "n", "url": "https:///x"}]):
        assert len(catalog_problems({"agents": [{**ok["agents"][0], "credits": badc}]})) == 1, badc
    assert plugin_to_agent({**plug, "credits": cred})["credits"] == cred
    assert agent_to_plugin({**agent, "credits": cred})["credits"] == cred
    assert agreement_problems([{**agent, "credits": cred}], [plug]) == ["a: the catalog files disagree on credits"]
    assert agreement_problems([agent], [{**plug, "credits": None}]) == ["a: the catalog files disagree on credits"]
    assert agent_to_plugin({"name": "g", "repo": "https://github.com/o/g.git", "sha": "b" * 40})["source"]["source"] == "github"
    other = {**plug, "source": {**plug["source"], "sha": "b" * 40}}
    assert agreement_problems([agent], [other]) == ["a: the catalog files disagree on sha"]
    assert agreement_problems([agent], []) == ["a: in only one catalog file"]
    here = {**ok["agents"][0], "repo": f"https://github.com/{THIS_REPO}.git"}
    assert catalog_problems({"agents": [here]}) == ["a: a helper of this repository follows its ref; remove its sha"]
    assert catalog_problems({"agents": [{k: v for k, v in here.items() if k != "sha"}]}) == []
    files = {"agents/code/a/AGENTS.md": "Run the command.", "agents/code/a/skills/s/SKILL.md":
             "---\nname: s\ndescription: d\n---\nbody", "agents/code/a/skills/README.md": "x", "README.md": "pi"}
    assert files_problems("a", "agents/code/a/", {x: 1 for x in files}, files.get) == []
    assert files_problems("a", "agents/code/a/", {"agents/code/a/skills/t/x.md": 1}, lambda x: "") == [
        "agents/code/a/AGENTS.md missing", "agents/code/a/skills/t/SKILL.md missing"]
    assert files_problems("a", "agents/code/a/", {"agents/code/a/AGENTS.md": 1}, files.get) == [
        "no agents/code/a/skills/<name>/ directories"]
    unpinned = {k: v for k, v in agent.items() if k != "sha"}  # a helper of this repo follows its ref
    assert catalog_problems({"agents": [unpinned]}) == []
    assert catalog_problems({"agents": [{**unpinned, "sha": None}]}) == ["a: sha, when given, is 40 hex characters"]
    assert "sha" not in agent_to_plugin(unpinned)["source"] and plugin_to_agent(agent_to_plugin(unpinned)) == unpinned
    assert agreement_problems([unpinned], [plug]) == ["a: the catalog files disagree on sha"]


def selftest():
    good = "---\nname: ci-debug\ndescription: Triage a failed run\n---\nbody"
    assert skill_problems("ci-debug", good) == []
    assert len(skill_problems("other", good)) == 1
    assert len(skill_problems("x", "no frontmatter")) == 2
    assert len(skill_problems("ci-debug", good + "x" * MAX_BODY_BYTES)) == 1
    assert len(skill_problems("ci-debug", good + "\n" * (MAX_BODY_LINES + 1))) == 1
    assert frontmatter("---\nname: a\ndescription: |\n  long\n---")["name"] == "a"
    here = {"source": "git-subdir", "url": f"https://github.com/{THIS_REPO}.git", "path": "agents/code/x"}
    assert layout_problems({"name": "x", "category": "code", "source": here}) == []
    assert len(layout_problems({"name": "x", "category": "team", "source": here})) == 1
    assert len(layout_problems({"name": "x", "source": here})) == 1
    assert layout_problems({"name": "x", "source": {"source": "github", "repo": "o/x"}}) == []
    assert harness_problems("AGENTS.md", "Run the command and read the file.") == []
    assert len(harness_problems("AGENTS.md", "Use the SendMessage tool, then read CLAUDE.md")) == 2
    assert harness_problems("x", "cursor pagination; a Bash script") == []
    assert len(harness_dir_problems("agents/a/", ["agents/a/.claude/skills/x", "agents/b/.pi/y"])) == 1
    assert harness_dir_problems("agents/a/", ["agents/a/skills/x/SKILL.md"]) == []
    f = {"AGENTS.md": "Message with pengupool send.", "skills/a/SKILL.md": "Run the command."}
    assert harness_name_problems("x", f) == []
    assert len(harness_name_problems("x", {**f, "README.md": "Install with pi install ./"})) == 1
    assert harness_name_problems("x", {**f, "logs/x.md": "pi", "tests/t.py": "Pi", "addons/pi/README.md": "pi"}) == []
    g = {"skills/review-codex/SKILL.md": "Codex runs it.", "AGENTS.md": "Optional: `review-codex` (Codex)."}
    assert harness_name_problems("x", g) == []
    assert len(harness_name_problems("x", {**g, "scripts/run.sh": "codex exec"})) == 1
    assert harness_name_problems("git-ci-agent", {"scripts/ci_triage.sh": "pi -p"}) == []
    assert harness_name_problems("x", {"README.md": "an API, a pip install, a pipeline"}) == []
    assert secret_problems({"AGENTS.md": "export TOKEN=<token>", "skills/a/SKILL.md": "api_key: <key>"}) == []
    assert len(secret_problems({"skills/a/references/x.md": "password = hunter2hunter2hunter2"})) == 1
    assert secret_problems({"tests/t.py": "AKIA" + "A" * 16}) == []
    assert len(harness_dir_problems("agents/a/", ["agents/a/CLAUDE.md", "agents/a/skills/x/GEMINI.md"])) == 2
    ok = {"AGENTS.md": 'Run `pengupool search "x"`, `pengupool send --to a "b"`, `pengupool team request add`.'}
    assert cli_problems(ok) == []
    assert cli_problems({"logs/x.md": "pengupool ctl describe"}) == []
    bad = {"AGENTS.md": "`pengupool memory propose --kind fact`", "skills/a/SKILL.md": "x\npengupool ctl tree"}
    assert [p.split(":")[:2] for p in cli_problems(bad)] == [["AGENTS.md", "1"], ["skills/a/SKILL.md", "2"]]
    catalog_selftest()
    print("selftest ok")


if __name__ == "__main__":
    if sys.argv[1:] == ["--selftest"]:
        selftest()
    else:
        sys.exit(main(sys.argv[1:]))
