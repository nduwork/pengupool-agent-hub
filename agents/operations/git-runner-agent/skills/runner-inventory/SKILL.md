---
name: runner-inventory
description: |
  Use after a self-hosted runner on this Mac was added, removed or moved to another repo, or when the
  runner-stats JSON and the inventory disagree. Keeps the local inventory, runners.local.json (gitignored, in
  the format of runners.example.json), in sync with the runners registered on GitHub and
  ~/actions-runners/runner-stats.json.
triggers:
  - runner-inventory
  - add runner to inventory
  - runner inventory
  - remove runner from inventory
---

# runner-inventory

The inventory is what runner-stats, machine-health (orphaned and reboot-killed runs) and every other session
read to know which runner serves which repo. A runner that is missing from it is invisible to both checks.
It is local data, `runners.local.json` beside the scripts, never committed: it names private repos.

## Every task

1. Search for the owner's rules and earlier work: `pengupool search "<words>"`.
2. Do the task in the deploy copy's `runners.local.json` (`~/actions-runners/runner-agent/`), the one the
   LaunchAgents read. Nothing is committed.
   1. Add `"<repo>": ["<instance>", …]` to `repo_instances`. Instance dirs are relative to
      `~/actions-runners/instances`; a standalone runner takes an absolute path.
   2. Add `"<repo>": "<owner>"` to `repo_owners` only if the repo is not under `owner`.
   3. A runner installed with `svc.sh` instead of `git_runners.sh` gets its launchd label in
      `launchd_labels`.
   4. **Verify:** run `./runner_stats.sh`. `total_runners` must equal the runners registered on GitHub
      (`gh api repos/<owner>/<repo>/actions/runners`), and each new instance must show `online` and
      `service_running: true`.
3. Reply with the outcome and its evidence. PenguPool records the work; write no log.
4. If the owner stated a lasting rule, propose it (`AGENTS.md` rule 2).

## Worked example

Adding one runner `<host>-<repo>` for a repo whose CI cannot use GitHub-hosted minutes:
- One line in `repo_instances`: `"<repo>": ["<host>-<repo>"]`. No `repo_owners` line, because the repo is
  under `owner`.
- `./runner_stats.sh` then reported one more runner, online.
