# GitHub Actions Runner Setup

> **Skill repo.** Agents start from `AGENTS.md`. Method lives in `skills/<task>/SKILL.md` (`runner-health`,
> `runner-setup`, `runner-inventory`), and owner preferences and earlier work in PenguPool memory. Checks:
> `python3 -m unittest discover -s tests -v`.

This repo packages a lightweight way to run multiple self-hosted GitHub Actions runners on one macOS machine without keeping four full duplicated installs on disk.

## Layout

The setup uses one canonical runner install plus APFS copy-on-write clones for each registered runner instance:

```text
~/actions-runners/                    # everything runner-related, internal disk only (launchd can't reach /Volumes)
  template/                           # canonical runner install (setup_runners.sh re-extracts it)
  downloads/                          # cached runner tarballs
  instances/                          # one registered runner per dir (APFS clones of template/)
    <host>-1 … -9/                    #   a pool for one repo
    <host>-<repo>[-N]/                #   one group per repo
  runner-agent/                       # deploy copy of this repo; the helper LaunchAgents run from here
  *.json, *.log                       # helper outputs: runner-stats, machine-health(+state), check, publish-dispatch
```

Nothing runs from the checkout itself: the LaunchAgents run from the deploy copy (see below).

Why this works better than four separate full copies:

- Each runner still has its own real local path, which the GitHub runner binaries expect.
- `cp -cR` on APFS creates copy-on-write clones, so disk usage stays low.
- Each instance keeps its own `.runner`, `.credentials`, `_work`, and logs.

## Prerequisites

- macOS on an APFS volume
- `gh` CLI installed and authenticated
- If you see `401 Unauthorized`, re-authenticate with `gh auth login -h github.com`
- Access to administer self-hosted runners for the target repository
- Xcode command line tools

## Files

- `setup_runners.sh`: downloads the runner, prepares the template, clones the instances, and registers them
- `git_runners.sh`: starts, stops, restarts, and checks status via per-runner LaunchAgent plists
- `check_runners.sh`: daily runner liveness + version-drift check
- `runner_stats.sh`: writes a JSON snapshot of every runner (see `skills/runner-health`)
- `machine_health.sh`: boot-time/per-hour kernel-panic + reboot-killed-job watch
- `publish_timer.sh`: daily 06:00 dispatch of one repository's workflow
- `scripts/`: the Python builders behind `runner_stats.sh` and `machine_health.sh`
- `runners.example.json`: the format of `runners.local.json`, the local, never-committed list of the fleet
  (owner, repos, instance dirs, launchd labels, the publish target, the signing keychain lock)

## Quick Start

```bash
cd /path/to/this/repo
chmod +x setup_runners.sh git_runners.sh

export GITHUB_OWNER="<owner>"
export GITHUB_REPO="<repo>"
export RUNNER_LABELS="self-hosted,macOS,ARM64"

./setup_runners.sh
./git_runners.sh start
./git_runners.sh status
```

By default the setup script creates `<host>-1` … `<host>-9`, where `<host>` is `hostname -s`
(`RUNNER_PREFIX` overrides it).

You can override them with `RUNNER_NAMES="runner-a runner-b runner-c runner-d"`, or change the count with `RUNNER_COUNT=9`.

## Configuration

Environment variables supported by `setup_runners.sh`:

- `GITHUB_OWNER`: required GitHub org or user owner
- `GITHUB_REPO`: required target repository name
- `RUNNER_VERSION`: optional, defaults to `2.337.0`
- `RUNNER_ARCHIVE_URL`: optional direct archive URL override
- `RUNNER_ROOT`: optional runner root, defaults to `$HOME/actions-runners`
- `RUNNER_LABELS`: optional comma-separated labels, defaults to `self-hosted,macOS,ARM64`
- `RUNNER_GROUP`: optional runner group
- `RUNNER_WORKDIR_PREFIX`: optional work dir prefix, defaults to `_work`
- `RUNNER_NAMES`: optional space-separated runner names
- `RUNNER_COUNT`: optional number of `<host>-N` runners, defaults to `9` (ignored when `RUNNER_NAMES` is set)
- `REPLACE_EXISTING`: optional, defaults to `true`

Environment variables supported by `git_runners.sh`:

- `RUNNER_ROOT`: optional runner root, defaults to `$HOME/actions-runners`
- `RUNNER_NAMES`: optional space-separated runner names
- `PROCESS_TYPE`: optional launchd `ProcessType` for `start`, defaults to `Background`, which runs jobs on
  efficiency cores with throttled I/O. Use `Standard` for runners with CPU-heavy jobs (video renders,
  builds). It is saved in the instance dir as `.process_type` and kept on later starts.
- `LAUNCHER`: optional absolute path of a program that starts the runner (`<launcher> /bin/bash -lc 'exec ./run.sh'`).
  macOS privacy grants (external drives, Full Disk Access) go to a launchd job's first non-Apple program, which
  is otherwise `bin*/Runner.Listener` and changes path on every runner update. A fixed launcher that spawns its
  arguments as a child (not exec) keeps one grant. Saved as `.launcher`; delete that file to stop using it.

## Updating The Runner Version

When GitHub releases a new runner version:

```bash
export RUNNER_VERSION="2.337.0"
./setup_runners.sh
./git_runners.sh restart
```

The script refreshes the template install and recreates instance directories from it.

## Start And Stop

```bash
./git_runners.sh start
./git_runners.sh stop
./git_runners.sh restart
./git_runners.sh status
```

`start` installs a LaunchAgent plist per runner in `~/Library/LaunchAgents/` with `RunAtLoad` and `KeepAlive`, so runners come back automatically at login and relaunch after a crash or runner self-update. `stop` removes the plist, so a stopped runner stays stopped.

Each runner writes logs to:

```text
~/actions-runners/instances/<runner-name>/runner.log
```

## Installing LaunchAgents (run from the internal deploy copy)

macOS TCC denies launchd jobs any path on an external volume (`/Volumes/*`):
`bash: …: Operation not permitted`, and the helper agents fail silently. Every
`install` therefore refuses a `/Volumes` path. Deploy a copy to the internal disk
and install from there; re-run after any change:

```bash
rsync -a --delete --exclude .git --exclude .step-status --exclude __pycache__ \
  --exclude runners.local.json ./ ~/actions-runners/runner-agent/   # the deploy copy keeps its own fleet file
cd ~/actions-runners/runner-agent
./machine_health.sh install; ./check_runners.sh install; ./runner_stats.sh install; ./publish_timer.sh install
```

## Daily publish dispatch

GitHub runs scheduled workflows hours late, so `publish_timer.sh` dispatches the
workflow named in the `publish` entry of `runners.local.json` (repository, workflow
file and `-f` inputs) at 06:00 host-local time (DST-aware; a run missed while
asleep fires on wake). Keep the workflow's own cron as a backup.
Each dispatch writes `~/actions-runners/publish-dispatch.json` (log:
`publish-dispatch.log`), and machine-health alerts on a failed one (e.g. gh auth
expired; it needs the active gh account to have the `workflow` scope).
Disable with `./publish_timer.sh uninstall`.

## Daily Health Check

`check_runners.sh` verifies every runner is alive and running the latest released version:

```bash
./check_runners.sh          # run the check now
./check_runners.sh install  # install a daily 09:00 LaunchAgent
```

It flags any stopped runner or version drift, sends a macOS notification, and logs to `~/actions-runners/check.log`. The LaunchAgent is the macOS-native cron: it catches up a missed run after sleep, which `crontab` does not. To change the time, edit `~/Library/LaunchAgents/com.github.actions.check-runners.plist` and re-run `install`.

## Machine health (kernel panics + reboot-killed jobs)

`machine_health.sh` watches the box itself, not the runners:

```bash
./machine_health.sh          # run the check now
./machine_health.sh install  # RunAtLoad + hourly LaunchAgent
```

It detects and (via macOS notification) alerts on:

- **Kernel panics** — especially the panic that caused the current boot. A panic
  report is flushed during the reboot that follows it, so a `RunAtLoad` check
  fires right after a panic reboot with the reason. Alerts once per panic.
- **Runs left in_progress across a reboot** — impossible on a rebooted host.
- **Runs that failed across the reboot** — GitHub auto-fails a job whose runner
  lost communication, so a job killed by a panic usually shows as
  `completed/failure` spanning the boot rather than lingering `in_progress`.
  A killed run is marked **resolved** (and stops counting as outstanding) once a
  **later successful run of the same workflow** in the same repo exists.
- **A keychain left broken by host death** — a TestFlight signing action's
  cleanup trap cannot run if the host dies mid-job, which can leave the
  user default keychain pointing at an orphan `testflight-*.keychain-db`. The
  check flags a default that is ours or missing/nonexistent, our entries in the
  keychain search list, and orphan `testflight-*.keychain-db` files. This is a
  generic check that consumes the action's naming and lock contract
  (`keychain_lock` in `runners.local.json`).
- **Xcode dirs on an external volume** — runner jobs run under launchd, which
  macOS TCC denies access to `/Volumes/*`; xcodebuild then hangs forever in
  `mkdirat`/`open` instead of failing. Flags `~/Library/Developer/Xcode/`
  `DerivedData`, `Archives` or `iOS DeviceSupport` resolving to `/Volumes/` or
  not listable. Keep them on the internal disk, never symlinked to an external volume.

State is kept in `~/actions-runners/machine-health-state.json` (so it never
re-alerts for a known problem); the current picture is written atomically to
`~/actions-runners/machine-health.json` (`ok`, `problems`, `panics_since_boot`,
`last_panic`, `orphaned_runs`, `reboot_killed_runs`, `unresolved_killed_runs`,
`resolved_killed_runs`, `keychain`, `xcode_dirs`, `publish_dispatch`). Logs to `~/actions-runners/machine-health.log`.

Keychain **repair** is explicit and safe:

```bash
./machine_health.sh repair   # reset default→login, drop our search-list entries, delete orphans
```

It takes the **same non-blocking `lockf` lock** the signing action holds (the
`keychain_lock` file in `runners.local.json`, `-t 0`), so it never races
a live signing job: if the lock is busy it alerts and skips. A plain `check`
(alert-only) never takes the lock.

Auto-**redispatch** of reboot-killed runs is **off by default** (`REDISPATCH=0`);
a blind re-run could double-upload (e.g. a late TestFlight `pilot`). With
`REDISPATCH=1` the check only *logs* the `gh workflow run` it would issue. Set
`NO_ALERT=1` to suppress notifications, `FORCE_ALERT=1` to alert even for
already-recorded problems (testing).

> History: the first recorded panic was
> `panic-base+socd-2026-09-26-224130.000.panic` — `apcie[2:lan-1gb]` completion
> timeout on the physical 1GbE PCIe port (`ApplePCIEBaseT8132Port`), which
> rebooted the box and killed every in-flight job (18 runners at the time). It
> is hardware/firmware-level; if it recurs, treat it as a service signal. That
> panic also left an orphan `testflight-*.keychain-db` as the user default,
> breaking the next signing job — which is why the keychain check exists.

## Cleanup

To remove all locally registered runners from GitHub and stop them:

1. Run `./git_runners.sh stop`
2. For each runner directory under `~/actions-runners/instances`, run `./config.sh remove --token <remove-token>`
3. Delete `~/actions-runners`

## Notes

- Do not commit live runner directories, `.runner`, or `.credentials` files.
- Do not symlink the entire runner install. The GitHub runner scripts resolve their real path and will break in that layout.
- If jobs queue but do not start, confirm the runner labels in your workflow match the labels passed during registration.
- If `./setup_runners.sh` fails with `401 Unauthorized`, run `gh auth status -h github.com` and re-login if the stored token is invalid.

## Runner inventory

The fleet is local data: `runners.local.json` (gitignored, in the format of
`runners.example.json`) lists the owner, each repo's instance dirs, launchd labels for a
runner installed with `svc.sh`, the publish target and the signing keychain lock.
`runner_stats.sh` and `machine_health.sh` read it. A public repository gets no self-hosted
runner. Idle runners consume ~no resources (only a keep-alive listener process), so keeping
many instances is fine.

**Repo-scoped runners:** GitHub supports shared runner *pools* (runner groups) only for
organizations. Under a personal account a runner registers **per repository**, so a repo A
runner cannot run repo B jobs.
