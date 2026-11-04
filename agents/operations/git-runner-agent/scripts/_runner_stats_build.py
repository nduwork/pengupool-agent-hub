#!/usr/bin/env python3
"""Build runner-stats.json: per-repo GitHub runner status + local instance health.

Run via runner_stats.sh (which sets RUNNER_ROOT/OWNER/STATS_OUT). Idempotent,
writes atomically (tmp + os.replace). No secrets are emitted — only names,
statuses, labels, and local service/version health.
"""
import json
import os
import subprocess
import sys

RUNNER_ROOT = os.path.expanduser(os.environ.get("RUNNER_ROOT", "~/actions-runners"))
HERE = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
# The fleet (owner, repos, instance dirs) is local data, never committed: runners.local.json beside
# this helper's scripts, in the format of the tracked runners.example.json.
CONFIG = os.path.expanduser(os.environ.get("RUNNERS_CONFIG", os.path.join(HERE, "runners.local.json")))


def load_config(path=CONFIG):
    try:
        with open(path) as f:
            return json.load(f)
    except FileNotFoundError:
        return {}


_CFG = load_config()
OWNER = os.environ.get("OWNER") or _CFG.get("owner", "")
STATS_OUT = os.path.expanduser(os.environ.get("STATS_OUT", "~/actions-runners/runner-stats.json"))
INSTANCES = os.path.join(RUNNER_ROOT, "instances")
# repo -> owner, when it is not OWNER
REPO_OWNERS = _CFG.get("repo_owners", {})
# repo -> list of instance dir names (relative to INSTANCES) or absolute paths
REPO_INSTANCES = _CFG.get("repo_instances", {})
# instance -> launchd label, for a runner installed with svc.sh instead of git_runners.sh
LAUNCHD_LABELS = _CFG.get("launchd_labels", {})


def gh_runners(repo: str):
    owner = REPO_OWNERS.get(repo, OWNER)
    try:
        raw = subprocess.run(
            ["gh", "api", f"repos/{owner}/{repo}/actions/runners", "--jq",
             '[.runners[] | {name,status,labels:[.labels[].name]|join(",")}]'],
            capture_output=True, text=True, check=True).stdout
        return json.loads(raw) if raw.strip() else []
    except Exception:
        return []


def instance_health(dir_name: str):
    path = dir_name if dir_name.startswith("/") else os.path.join(INSTANCES, dir_name)
    name = os.path.basename(path)
    label = LAUNCHD_LABELS.get(name, f"com.github.actions.{name}")
    svc = subprocess.run(
        ["launchctl", "print", f"gui/{os.getuid()}/{label}"],
        capture_output=True).returncode == 0
    listener = os.path.join(path, "bin", "Runner.Listener")
    ver = "unknown"
    if os.path.exists(listener):
        try:
            ver = subprocess.run([listener, "--version"], capture_output=True,
                                 text=True).stdout.strip() or "unknown"
        except Exception:
            pass
    return {"instance": dir_name, "service_running": svc, "installed_version": ver}


def latest_runner_version():
    try:
        v = subprocess.run(["gh", "api", "repos/actions/runner/releases/latest",
                            "--jq", ".tag_name"], capture_output=True, text=True,
                           check=True).stdout.strip().lstrip("v")
        return v
    except Exception:
        return ""


def main():
    repos = []
    total = 0
    online = 0
    for repo, dirs in REPO_INSTANCES.items():
        runners = gh_runners(repo)
        owner = REPO_OWNERS.get(repo, OWNER)
        for r in runners:
            total += 1
            if r.get("status") == "online":
                online += 1
        instances = [instance_health(d) for d in dirs]
        repos.append({"repo": repo, "owner": owner, "runners": runners, "instances": instances})

    doc = {
        "generated_at": subprocess.run(["date", "-u", "+%Y-%m-%dT%H:%M:%SZ"],
                                       capture_output=True, text=True, check=True).stdout.strip(),
        "owner": OWNER,
        "latest_runner_version": latest_runner_version(),
        "total_runners": total,
        "online_runners": online,
        "offline_runners": total - online,
        "repos": repos,
        "notes": ("runners[] = GitHub-reported registration/status; "
                  "instances[] = local launchd service health + installed version"),
    }
    tmp = STATS_OUT + ".tmp"
    with open(tmp, "w") as f:
        json.dump(doc, f, indent=2)
        f.write("\n")
    os.replace(tmp, STATS_OUT)
    print(f"Wrote {STATS_OUT}: {total} runners total, {online} online")


if __name__ == "__main__":
    sys.exit(main())
