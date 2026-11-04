#!/usr/bin/env python3
"""Machine-health watch for the self-hosted runner box.

Detects (a) kernel panics — especially one that caused the current boot, so a
boot-time RunAtLoad check catches the reboot reason — and (b) GitHub Actions
runs that were left in_progress/queued across a reboot (orphaned: a self-hosted
job whose host died can never resume).

Writes ~/actions-runners/machine-health.json atomically and (unless NO_ALERT=1)
raises a macOS notification when there are new problems. Never re-alerts for a
panic already recorded in the state file.

Env:
  RUNNER_ROOT   default ~/actions-runners
  NO_ALERT      set 1 to suppress the macOS notification
  FORCE_ALERT   set 1 to alert even for panics already recorded (for testing)
  REDISPATCH    default 0; when 1, logs the `gh workflow run` it *would* issue
                for orphaned runs. Deliberately a no-op by default — a blind
                re-run could double-upload (e.g. a late TestFlight upload).
"""
import glob
import json
import os
import re
import shlex
import shutil
import subprocess
import sys
import tempfile
from datetime import datetime, timezone

HERE = os.path.dirname(os.path.abspath(__file__))
sys.path.insert(0, HERE)

RUNNER_ROOT = os.path.expanduser(os.environ.get("RUNNER_ROOT", "~/actions-runners"))
STATE_PATH = os.path.join(RUNNER_ROOT, "machine-health-state.json")
OUT_PATH = os.path.join(RUNNER_ROOT, "machine-health.json")
PANIC_DIRS = ["/Library/Logs/DiagnosticReports", "/Library/Logs/DiagnosticReports/Retired"]
# A panic report is flushed during the reboot that follows it, so its mtime
# lands within seconds/minutes of the new boot. Anything at/after
# boot_time - this grace is treated as "the panic that caused this boot".
PANIC_BOOT_GRACE_SECONDS = 300

# A TestFlight signing action signs via a temporary keychain named
# testflight-<run>-<attempt>-<pid>.keychain-db. Older versions made it the user
# *default*; if the host dies mid-job its cleanup trap never runs and the box is
# left broken. The action now takes a non-blocking lockf lock while it works.
KEYCHAINS_DIR = os.path.expanduser("~/Library/Keychains")
LOGIN_KEYCHAIN = os.path.join(KEYCHAINS_DIR, "login.keychain-db")
TF_KEYCHAIN_RE = re.compile(r"^testflight-.*\.keychain-db$")

# Runner jobs run under launchd, which TCC denies access to external volumes
# (/Volumes/*): a plain mkdir gets EPERM, but xcodebuild blocks in mkdirat/open
# forever. So Xcode's per-user dirs must stay on the internal disk, never be
# symlinked to an external volume (a 2026-10-08 CI hang).
XCODE_DIRS = [os.path.expanduser("~/Library/Developer/Xcode/" + d)
              for d in ("DerivedData", "Archives", "iOS DeviceSupport")]

# publish_timer.sh writes the result of its daily 06:00 workflow dispatch here.
PUBLISH_DISPATCH_PATH = os.path.join(RUNNER_ROOT, "publish-dispatch.json")

# Repos to check for orphaned runs (reuse the runner inventory mapping).
try:
    from _runner_stats_build import _CFG, OWNER, REPO_INSTANCES, REPO_OWNERS
except Exception:
    _CFG = {}
    OWNER = ""
    REPO_INSTANCES = {}
    REPO_OWNERS = {}
# The lock file the signing action holds while it works (runners.local.json "keychain_lock").
TF_LOCK = os.path.expanduser(_CFG.get("keychain_lock", ""))


def iso(ts):
    return datetime.fromtimestamp(ts, tz=timezone.utc).strftime("%Y-%m-%dT%H:%M:%SZ")


def now_iso():
    return datetime.now(timezone.utc).strftime("%Y-%m-%dT%H:%M:%SZ")


def run(cmd):
    try:
        return subprocess.run(cmd, capture_output=True, text=True, check=True).stdout
    except Exception:
        return ""


def boot_time():
    out = run(["sysctl", "-n", "kern.boottime"])
    # { sec = 1790487682, usec = 176422 } Sat ...
    if "sec = " not in out:
        return 0
    try:
        return int(out.split("sec = ")[1].split(",")[0])
    except Exception:
        return 0


def panics():
    found = []
    for d in PANIC_DIRS:
        if not os.path.isdir(d):
            continue
        for fn in os.listdir(d):
            if not fn.endswith(".panic") or fn.startswith("."):
                continue
            p = os.path.join(d, fn)
            try:
                st = os.stat(p)
            except OSError:
                continue
            summary = ""
            try:
                with open(p, "r", errors="ignore") as f:
                    head = f.read(4000)
                marker = '"panicString"'
                if marker in head:
                    seg = head.split(marker, 1)[1]
                    seg = seg.split(":", 1)[1].strip().lstrip('"')
                    summary = seg.split("\\n")[0][:300]
            except Exception:
                pass
            found.append({"file": p, "mtime": int(st.st_mtime), "mtime_iso": iso(st.st_mtime),
                          "panic_string": summary})
    found.sort(key=lambda x: x["mtime"])
    return found


RUN_FIELDS = "databaseId,name,workflowName,status,conclusion,createdAt,updatedAt,url,headBranch"


def repo_runs(repo):
    """Recent runs for a repo, or [] if gh is unavailable."""
    owner = REPO_OWNERS.get(repo, OWNER)
    raw = run(["gh", "run", "list", "-R", f"{owner}/{repo}", "--json", RUN_FIELDS, "--limit", "50"])
    if not raw.strip():
        return []
    try:
        return json.loads(raw)
    except Exception:
        return []


def orphaned_runs(boot_ts):
    """Runs GitHub still reports as in_progress but which started before this
    boot — impossible on a rebooted host."""
    orphaned = []
    for repo, _dirs in REPO_INSTANCES.items():
        owner = REPO_OWNERS.get(repo, OWNER)
        for r in repo_runs(repo):
            if r.get("status") != "in_progress":
                continue
            created = r.get("createdAt", "")
            if parse_ts(created) and parse_ts(created) < boot_ts:
                orphaned.append({"repo": f"{owner}/{repo}", "run_id": r.get("databaseId"),
                                 "name": r.get("name"), "branch": r.get("headBranch"),
                                 "started_at": created, "url": r.get("url")})
    return orphaned


def parse_ts(s):
    try:
        return datetime.strptime(s, "%Y-%m-%dT%H:%M:%SZ").replace(tzinfo=timezone.utc).timestamp()
    except Exception:
        return 0


def reboot_killed_runs(boot_ts):
    """Runs that started before this boot and were updated (failed) after it.
    GitHub auto-fails a job whose runner lost communication, so a job killed by
    a panic reboot shows as `completed/failure` *spanning* the reboot rather
    than lingering in_progress. A later successful run of the same workflow in
    the same repo marks the killed run as resolved (it no longer looks
    outstanding)."""
    killed = []
    for repo, _dirs in REPO_INSTANCES.items():
        owner = REPO_OWNERS.get(repo, OWNER)
        runs = repo_runs(repo)
        for r in runs:
            if r.get("conclusion") != "failure":
                continue
            c = parse_ts(r.get("createdAt", ""))
            u = parse_ts(r.get("updatedAt", ""))
            # Spanning the boot means the runner restarted mid-run. Require the
            # failure to land near boot so a long-queued run is not misattributed.
            if not (c and u and c < boot_ts < u and (u - boot_ts) <= 1800):
                continue
            wf = r.get("workflowName") or r.get("name")
            # Resolution: a later successful run of the same workflow after the
            # failure means the work was re-done, so it is no longer outstanding.
            resolved_by = None
            for other in runs:
                if other.get("conclusion") != "success":
                    continue
                if (other.get("workflowName") or other.get("name")) != wf:
                    continue
                if parse_ts(other.get("createdAt", "")) > u:
                    resolved_by = {"run_id": other.get("databaseId"), "url": other.get("url")}
                    break
            killed.append({"repo": f"{owner}/{repo}", "run_id": r.get("databaseId"),
                           "name": r.get("name"), "workflow": wf, "branch": r.get("headBranch"),
                           "started_at": r.get("createdAt"), "failed_at": r.get("updatedAt"),
                           "url": r.get("url"), "resolved": resolved_by is not None,
                           "resolved_by": resolved_by})
    return killed


def unquote(s):
    s = s.strip()
    if len(s) >= 2 and s[0] == '"' and s[-1] == '"':
        s = s[1:-1]
    return s


def keychain_state():
    """Inspect the runner user's keychain for the host-death breakage the shared
    signing action's trap cannot clean up. Read-only."""
    out = run(["security", "default-keychain", "-d", "user"])
    default = ""
    default_missing = False
    if not out.strip():
        default_missing = True
    else:
        lines = [l for l in out.splitlines() if l.strip()]
        default = unquote(lines[-1]) if lines else ""
        if not default or "could not be found" in out.lower():
            default_missing = True
    if default and not os.path.exists(default):
        default_missing = True
    default_basename = os.path.basename(default) if default else ""
    default_is_ours = bool(TF_KEYCHAIN_RE.match(default_basename))

    sl_out = run(["security", "list-keychains", "-d", "user"])
    search = [unquote(l) for l in sl_out.splitlines() if l.strip()]
    search_ours = [p for p in search if TF_KEYCHAIN_RE.match(os.path.basename(p))]

    orphans = sorted(glob.glob(os.path.join(KEYCHAINS_DIR, "testflight-*.keychain-db")))

    problem = default_is_ours or default_missing or bool(orphans) or bool(search_ours)
    reasons = []
    if default_is_ours:
        reasons.append("user default keychain is {}".format(default_basename))
    if default_missing:
        reasons.append("user default keychain missing/nonexistent")
    if search_ours:
        reasons.append("search list has {}".format(", ".join(os.path.basename(p) for p in search_ours)))
    if orphans:
        reasons.append("orphan keychain file(s): {}".format(", ".join(os.path.basename(p) for p in orphans)))
    return {
        "default": default,
        "default_missing": default_missing,
        "default_is_ours": default_is_ours,
        "search_list": search,
        "search_ours": search_ours,
        "orphans": orphans,
        "problem": problem,
        "reasons": reasons,
        "signature": "{}|{}|{}".format(default_basename, ",".join(orphans), ",".join(search_ours)),
    }


def keychain_repair(state):
    """Reset the default to login.keychain-db, drop our entries from the search
    list, and delete orphan testflight keychains. Takes the SAME non-blocking
    lockf lock the action holds, so it never races a live signing job. Returns
    a dict describing what happened."""
    result = {"attempted": True, "repaired": False, "skipped": None, "output": ""}
    if not shutil.which("lockf"):
        result["skipped"] = "lockf unavailable; refusing to repair unlocked"
        return result
    if not TF_LOCK:
        result["skipped"] = "no keychain_lock in runners.local.json; refusing to repair unlocked"
        return result

    cmds = ['security default-keychain -d user -s ' + shlex.quote(LOGIN_KEYCHAIN)]
    keep = [p for p in state["search_list"] if not TF_KEYCHAIN_RE.match(os.path.basename(p))
            and os.path.exists(p)]
    if LOGIN_KEYCHAIN not in keep:
        keep.insert(0, LOGIN_KEYCHAIN)
    cmds.append("security list-keychains -d user -s " + " ".join(shlex.quote(p) for p in keep))
    for o in state["orphans"]:
        cmds.append("security delete-keychain " + shlex.quote(o) + " >/dev/null 2>&1 || true")

    script = "set -e\n" + "\n".join(cmds) + "\n"
    fd, path = tempfile.mkstemp(prefix="machine-health-repair-", suffix=".sh")
    try:
        with os.fdopen(fd, "w") as f:
            f.write(script)
        # -t 0: fail immediately if the action holds the lock (a signing job is
        # live) instead of blocking or racing it.
        p = subprocess.run(["lockf", "-t", "0", TF_LOCK, "/bin/bash", path],
                           capture_output=True, text=True)
        result["output"] = (p.stdout + p.stderr).strip()
        if p.returncode == 0:
            result["repaired"] = True
        else:
            low = result["output"].lower()
            if "resource temporarily unavailable" in low or "lock" in low:
                result["skipped"] = "lock busy (a signing job may be live); not repairing"
            else:
                result["skipped"] = "repair command failed (rc={})".format(p.returncode)
    finally:
        try:
            os.unlink(path)
        except OSError:
            pass
    return result


def xcode_dirs_state():
    """Flag Xcode dirs runner jobs cannot reach. This check itself runs as a
    LaunchAgent, so a listdir failure here is the same denial the runners hit."""
    reasons = []
    for d in XCODE_DIRS:
        real = os.path.realpath(d)
        if real.startswith("/Volumes/"):
            reasons.append("{} -> {} (external volume; launchd jobs hang)".format(d, real))
            continue
        try:
            os.listdir(real)
        except FileNotFoundError:
            pass  # Xcode creates it on first use
        except OSError as e:
            reasons.append("{}: {}".format(d, e.strerror))
    return reasons


def publish_dispatch_state():
    try:
        with open(PUBLISH_DISPATCH_PATH) as f:
            return json.load(f)
    except (OSError, ValueError):
        return None  # timer not installed or never fired


def notify(title, message):
    if os.environ.get("NO_ALERT") == "1":
        return
    try:
        subprocess.run(["osascript", "-e",
                        'display notification {} with title {}'.format(
                            json.dumps(message), json.dumps(title))], check=False)
    except Exception:
        pass


def main():
    boot_ts = boot_time()
    os.makedirs(RUNNER_ROOT, exist_ok=True)
    state = {}
    if os.path.exists(STATE_PATH):
        try:
            with open(STATE_PATH) as f:
                state = json.load(f)
        except Exception:
            state = {}
    reported = set(state.get("reported_panics", []))
    reported_killed = set(state.get("reported_killed_runs", []))
    reported_orphans = set(state.get("reported_orphaned_runs", []))
    reported_kc_sig = state.get("reported_keychain_signature")
    first_run = not os.path.exists(STATE_PATH)

    all_panics = panics()
    since_boot = [p for p in all_panics if p["mtime"] >= boot_ts - PANIC_BOOT_GRACE_SECONDS]
    # Panics that caused this boot: at/just after boot time.
    new_since_boot = [p for p in since_boot if p["file"] not in reported]
    unseen_ever = [p for p in all_panics if p["file"] not in reported]

    force = os.environ.get("FORCE_ALERT") == "1"
    if first_run and not force:
        # Seed without alerting so installing the watcher doesn't replay history.
        new_alerts = []
        unseen_ever = []
    else:
        new_alerts = new_since_boot

    orphaned = orphaned_runs(boot_ts)
    killed = reboot_killed_runs(boot_ts)

    # Only alert once per problem; the JSON always carries the full picture.
    # A resolved run (a later successful run of the same workflow) is not
    # outstanding, so it never counts as a problem.
    new_orphaned = [o for o in orphaned if "{}:{}".format(o["repo"], o["run_id"]) not in reported_orphans]
    unresolved_killed = [k for k in killed if not k.get("resolved")]
    resolved_killed = [k for k in killed if k.get("resolved")]
    new_killed = [k for k in unresolved_killed if "{}:{}".format(k["repo"], k["run_id"]) not in reported_killed]

    # Keychain health: the signing action's cleanup trap cannot run
    # if the host dies mid-job. Detect the breakage; repair only behind an
    # explicit flag and only while holding the action's non-blocking lock.
    kc = keychain_state()
    kc_repair = None
    if kc["problem"] and os.environ.get("KEYCHAIN_REPAIR") == "1":
        kc_repair = keychain_repair(kc)
        if kc_repair.get("repaired"):
            kc_after = keychain_state()
            kc["problem"] = kc_after["problem"]
            kc["reasons_after_repair"] = kc_after["reasons"]
    new_kc = kc["problem"] and kc["signature"] != reported_kc_sig
    xc = xcode_dirs_state()
    new_xc = bool(xc) and "; ".join(xc) != state.get("reported_xcode_dirs")
    pd = publish_dispatch_state()
    pd_failed = bool(pd) and not pd.get("ok")
    new_pd = pd_failed and pd.get("at") != state.get("reported_publish_dispatch")

    problems = []
    if new_alerts:
        problems.append("kernel panic caused a reboot")
    if new_orphaned:
        problems.append("{} run(s) left in_progress across a reboot".format(len(new_orphaned)))
    if new_killed:
        problems.append("{} run(s) failed across the reboot".format(len(new_killed)))
    if new_kc:
        problems.append("keychain left broken: {}".format("; ".join(kc["reasons"])))
    if new_pd:
        problems.append("publish dispatch failed at {}: {}".format(pd.get("at"), pd.get("output", "")[:200]))
    if new_xc:
        problems.append("Xcode dirs unreachable by runners: {}".format("; ".join(xc)))

    last_panic = all_panics[-1] if all_panics else None
    doc = {
        "generated_at": now_iso(),
        "boot_time": iso(boot_ts) if boot_ts else "",
        "boot_epoch": boot_ts,
        "uptime_seconds": int(datetime.now(timezone.utc).timestamp()) - boot_ts if boot_ts else 0,
        "panic_count_total": len(all_panics),
        "panics": all_panics,
        "panics_since_boot": since_boot,
        "new_panics": new_alerts,
        "last_panic": last_panic,
        "orphaned_runs": orphaned,
        "reboot_killed_runs": killed,
        "unresolved_killed_runs": unresolved_killed,
        "resolved_killed_runs": resolved_killed,
        "keychain": {
            "problem": kc["problem"],
            "reasons": kc["reasons"],
            "default": kc["default"],
            "default_is_ours": kc["default_is_ours"],
            "default_missing": kc["default_missing"],
            "search_list": kc["search_list"],
            "search_ours": kc["search_ours"],
            "orphans": kc["orphans"],
            "repair": kc_repair,
        },
        "xcode_dirs": xc,
        "publish_dispatch": pd,
        "problems": problems,
        "ok": not problems,
        "redispatch_enabled": os.environ.get("REDISPATCH") == "1",
        "notes": ("panics_since_boot = panic reports whose mtime is within "
                  "{}s of boot (the panic that caused this boot); new_panics = "
                  "unseen ones we alerted on; orphaned_runs = in_progress runs "
                  "started before this boot (unrecoverable on self-hosted); "
                  "reboot_killed_runs = failed runs that started before and ended "
                  "after this boot; resolved_killed_runs = those superseded by a "
                  "later successful run of the same workflow (not outstanding); "
                  "keychain = TestFlight keychain default/search-list/orphan health "
                  "(repair via KEYCHAIN_REPAIR=1, which takes the action's lockf lock).").format(
                      PANIC_BOOT_GRACE_SECONDS),
    }
    tmp = OUT_PATH + ".tmp"
    with open(tmp, "w") as f:
        json.dump(doc, f, indent=2)
        f.write("\n")
    os.replace(tmp, OUT_PATH)

    # Persist state: remember every panic we've now seen.
    state["reported_panics"] = sorted(reported | {p["file"] for p in all_panics})
    state["reported_killed_runs"] = sorted(reported_killed | {"{}:{}".format(k["repo"], k["run_id"]) for k in killed})
    state["reported_orphaned_runs"] = sorted(reported_orphans | {"{}:{}".format(o["repo"], o["run_id"]) for o in orphaned})
    if kc["problem"]:
        state["reported_keychain_signature"] = kc["signature"]
    elif not new_kc:
        # Healthy again (or repaired): clear so a future relapse re-alerts.
        state["reported_keychain_signature"] = None
    state["reported_xcode_dirs"] = "; ".join(xc) or None
    state["reported_publish_dispatch"] = pd.get("at") if pd_failed else None
    state["last_boot_epoch"] = boot_ts
    state["last_boot_iso"] = iso(boot_ts) if boot_ts else ""
    state["last_check"] = now_iso()
    with open(STATE_PATH + ".tmp", "w") as f:
        json.dump(state, f, indent=2)
        f.write("\n")
    os.replace(STATE_PATH + ".tmp", STATE_PATH)

    if problems:
        # Suppress the notification on the very first run (seeding) so installing
        # the watcher doesn't replay history; the JSON still records everything.
        if not (first_run and not force):
            notify("Runner machine health: {} problem(s)".format(len(problems)), problems[0])
        print("PROBLEMS: " + "; ".join(problems))
        for p in new_alerts:
            print("  panic: {} ({}): {}".format(p["mtime_iso"], p["file"], p["panic_string"]))
        for o in new_orphaned:
            print("  orphaned run: {} run {} ({}) {}".format(o["repo"], o["run_id"], o["started_at"], o["url"]))
        for k in new_killed:
            print("  reboot-killed run: {} run {} ({} -> {}) {}".format(
                k["repo"], k["run_id"], k["started_at"], k["failed_at"], k["url"]))
        if new_kc:
            print("  keychain: {}".format("; ".join(kc["reasons"])))
            if not kc_repair:
                print("    (repair is OFF; run './machine_health.sh repair' to fix)")
        if new_orphaned or new_killed:
            if os.environ.get("REDISPATCH") == "1":
                for o in new_orphaned + new_killed:
                    print("  [redispatch] would re-run on {} (run {})".format(o["repo"], o["run_id"]))
            else:
                print("  (redispatch is OFF; set REDISPATCH=1 to log intended re-runs)")
        for k in resolved_killed:
            print("  resolved: {} run {} was superseded by successful run {}".format(
                k["repo"], k["run_id"], (k.get("resolved_by") or {}).get("run_id")))
    else:
        print("OK: no new panics, no orphaned/reboot-killed runs, keychain healthy, Xcode dirs internal. uptime={}s last_panic={}".format(
            doc["uptime_seconds"], (last_panic or {}).get("mtime_iso", "none")))
    if kc_repair is not None:
        print("  keychain repair: " + json.dumps(kc_repair))
    return 0


if __name__ == "__main__":
    sys.exit(main())
