# Changelog

## 2026-11-03

- The runner fleet is local data: `runners.local.json` (gitignored; format in `runners.example.json`) holds the
  owner, repos, instance dirs, launchd labels, the publish target and the signing keychain lock, so no private
  repo or host is named here. Default runner names use `hostname -s` (`RUNNER_PREFIX` overrides it). The README's
  per-repo inventory table is gone.

## 2026-10-12

- Organized the runner folders: every instance under `~/actions-runners/instances`, and the deploy copy at
  `~/actions-runners/runner-agent`, from which the LaunchAgents run.
- Restructured into the skill-repo layout. Added the skills `runner-health` (absorbs the pi `runner-stats`
  skill), `runner-setup` and `runner-inventory`, plus `AGENTS.md`, the memory protocol, subject logs and tests.
  The top-level scripts are unchanged.

## 2026-10-08

- Helper LaunchAgents run from the internal deploy copy. Added machine-health checks `xcode_dirs` and
  `publish_dispatch`, and a daily 06:00 publish timer.
