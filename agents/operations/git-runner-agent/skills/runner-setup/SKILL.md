---
name: runner-setup
description: |
  Use when asked to set up, register, start, stop, restart or upgrade self-hosted GitHub Actions runners on
  this Mac, for example "give repo X its own runners", "add two more runners to repo Y", or
  "update the runner version". Wraps setup_runners.sh and git_runners.sh. After a new runner is up, use
  runner-inventory to record it.
triggers:
  - runner-setup
  - set up a runner
  - register runner
  - new self-hosted runner
  - start runners
  - restart runners
  - update runner version
---

# runner-setup

One canonical install (`~/actions-runners/template`) plus APFS copy-on-write clones
(`~/actions-runners/instances/<name>`), each registered to one repo and run as a KeepAlive LaunchAgent
`com.github.actions.<name>`. Details and every env var are in `README.md`.

## Hard rules

- **Always pass `RUNNER_NAMES`.** Both scripts default to `<host>-1`…`-9` (`<host>` is `hostname -s`), which
  may be a live pool. `setup_runners.sh` does `rm -rf` on each named instance dir and re-registers it
  (`--replace`), so a run without `RUNNER_NAMES` can wipe that pool. `prepare_template` also deletes and re-extracts
  `~/actions-runners/template` on every run.
- **Runners are repo-scoped** under a personal account: a runner serves exactly one repo, and repo A's
  runner can never take repo B's job. Each repo needs its own instances, named `<host>-<repo>[-N]`.
- **No self-hosted runner on a public repository**: a fork's pull request could run its code on this Mac.
- **Labels must match the workflow's `runs-on`.** Every runner gets `self-hosted,macOS,ARM64`. Add a
  repo label only if that repo's workflows ask for one.
- **Stop an instance before re-creating it** (`RUNNER_NAMES=… ./git_runners.sh stop`). Check it isn't
  running a job first: `ps -axo command | grep "<name>/bin/Runner.Worker"`.
- A runner installed with its own `svc.sh` (`./svc.sh stop|start|status`; after moving the dir,
  `./svc.sh uninstall && ./svc.sh install`) is not managed by `git_runners.sh`; its launchd label is in
  `launchd_labels` of `runners.local.json`.

## Every task

1. Search for the owner's rules and earlier work: `pengupool search "<words>"`.
2. Do the task:
   1. `gh auth status -h github.com`. You need admin on the target repo. For a `401`, run `gh auth login -h github.com`.
   2. Pick the names and check none exists yet: `ls ~/actions-runners/instances`.
   3. Register:
      ```bash
      GITHUB_OWNER=<owner> GITHUB_REPO=<repo> RUNNER_NAMES="<host>-<repo> <host>-<repo>-2" \
        RUNNER_LABELS="self-hosted,macOS,ARM64[,<label>]" ./setup_runners.sh
      ```
   4. Start: `RUNNER_NAMES="…" ./git_runners.sh start`, then `… ./git_runners.sh status`.
   5. Verify: `gh api repos/<owner>/<repo>/actions/runners -q '.runners[]|[.name,.status]|@tsv'` shows
      them `online`.
   6. **Upgrade** (check_runners reports drift): set `RUNNER_VERSION`, and for each repo's group in turn
      run stop → `setup_runners.sh` (same `RUNNER_NAMES`/labels) → start. Do it one group at a time, never
      while that group has jobs running.
   7. Record the new runners with **runner-inventory**.
3. Reply with the outcome and its evidence. PenguPool records the work; write no log.
4. If the owner stated a lasting rule, propose it (`AGENTS.md` rule 2).

## Worked example

A private repo needed its own runner because its GitHub-hosted minutes were billing-blocked:
`GITHUB_OWNER=<owner> GITHUB_REPO=<repo> RUNNER_NAMES=<host>-<repo> ./setup_runners.sh`, then
`RUNNER_NAMES=<host>-<repo> ./git_runners.sh start`. It showed `online`, and was then added to the
inventory with runner-inventory.
