---
name: runner-health
description: |
  Use when asked whether the self-hosted runners on this Mac are healthy, for runner status, counts or
  stats, after a job hung, died or never started on a self-hosted runner, when machine-health raises an
  alert, or to maintain the host LaunchAgents (machine-health, check-runners, runner-stats, publish-timer).
  Covers the runner-stats JSON, the machine-health checks (panics, reboot-killed runs, broken TestFlight
  keychain, Xcode dirs, publish dispatch) and diagnosing a hung job.
triggers:
  - runner-health
  - runner health
  - runner stats
  - runner status
  - how many runners
  - machine health
  - runner hang
  - job stuck on self-hosted runner
---

# runner-health

All runners and helpers run on this Mac as launchd LaunchAgents. Read the JSON
snapshots first and only call `gh api` when they are stale.

## Hard rules

- **launchd jobs cannot touch `/Volumes/*`.** macOS TCC denies them: a plain `mkdir`/`ls` gets
  `Operation not permitted`, but `xcodebuild` blocks forever in `mkdirat`/`open` at 0% CPU instead of
  failing. So:
  - LaunchAgents run this repo's scripts from the **internal deploy copy**
    `~/actions-runners/runner-agent`, never from a checkout on an external volume. Every `install` refuses a `/Volumes` path.
  - `~/Library/Developer/Xcode/{DerivedData,Archives,iOS DeviceSupport}` stay real dirs on the internal
    disk, never symlinked to an external volume. machine-health flags them (`xcode_dirs`).
- **Test runner-context behaviour from launchd, not your shell.** The interactive shell has TCC grants the
  runners lack, and `log show` / `TCC.db` return nothing here, so "nothing in the TCC log" is not evidence.
- Never kill another project's job without the owner's OK. Killing a job that holds
  the signing keychain lock (`keychain_lock` in `runners.local.json`) frees every project's TestFlight queue.

## Every task

1. Search for the owner's rules and earlier work: `pengupool search "<words>"`.
2. Do the task:
   - **Status / counts:** read `~/actions-runners/runner-stats.json` (`total_runners`, `online_runners`,
     per-repo `runners[]` from GitHub, `instances[]` = launchd health + installed version). Stale or a
     runner just changed: `./runner_stats.sh` first. Report any offline runner or
     `service_running: false`.
   - **Machine health:** read `~/actions-runners/machine-health.json` (`ok`, `problems`, `keychain`,
     `xcode_dirs`, `publish_dispatch`, panics, `orphaned_runs`, `reboot_killed_runs`). Run
     `./machine_health.sh` to refresh. A broken TestFlight keychain is repaired only by
     `./machine_health.sh repair`, which takes the action's non-blocking lock. The keychain check also
     lists the temp keychain of a TestFlight job that is *running right now*: check for a live `lockf`
     on the lock before calling it broken.
   - **Version drift / liveness:** `./check_runners.sh` (daily 09:00 agent; log `~/actions-runners/check.log`).
   - **Hung job:** `ps -axo pid,stat,etime,%cpu,command | grep -E 'xcodebuild|lockf|Runner.Worker'`, then
     `sample <pid> 2` and read the main thread. A wait in a filesystem syscall on a path outside
     `~/actions-runners` points at the `/Volumes` rule above. Reproduce with a throwaway LaunchAgent in the
     scratchpad (no `RunAtLoad`, so `launchctl kickstart` it), then `bootout` it. `gh run cancel` does not
     reach processes under `lockf`; they need `kill`.
   - **Helper LaunchAgents:** after changing any script, re-sync the deploy copy and reinstall (README,
     "Installing LaunchAgents"). Agents: `com.github.actions.{machine-health,check-runners,runner-stats,publish-timer}`.
     Their logs live in `~/actions-runners/*.log`. A line `bash: …: Operation not permitted` there means an agent
     points at `/Volumes`.
   - **Publish timer:** `publish_timer.sh` dispatches the `publish` workflow of `runners.local.json` at
     06:00 host-local time; result in `~/actions-runners/publish-dispatch.json`. It needs the active `gh`
     account to have the `workflow` scope (`gh auth status`).
3. Reply with the outcome and its evidence. PenguPool records the work; write no log.
4. If the owner stated a lasting rule, propose it (`AGENTS.md` rule 2).

## Worked example (2026-10-08)

An app's CI sat 72 min at 0% CPU. `sample` showed `IDEOnDiskLogStore … mkdirat`. DerivedData was a
symlink to an external volume. A throwaway LaunchAgent running `xcodebuild -resolvePackageDependencies` on a
scratch package hung the same way (with both `ProcessType` values), and a plain `mkdir` there got EPERM. The
same probe with an internal `-derivedDataPath` finished in 5 s. Fix: the three Xcode symlinks became
internal dirs (Archives copied back), the hung jobs were killed with the owners' OK, and the
`xcode_dirs` check was added.
