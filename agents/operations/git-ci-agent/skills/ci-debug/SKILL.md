---
name: ci-debug
description: |
  Use when a GitHub Actions run failed and it should be troubleshot: "why did CI fail", "the daily
  publish failed again", "set up auto-triage for repo X", "triage run 123". Covers diagnosing a failed
  run, triaging it with a local model runner on the runner Mac, and wiring a repository to the reusable
  triage workflow.
triggers:
  - ci-debug
  - ci failed
  - workflow failed
  - triage run
---

# ci-debug

## Every task

1. Search for the owner's rules and earlier work: `pengupool search "<words>"`.
2. Do the task (below).
3. Reply with the outcome and its evidence. PenguPool records the work; write no log.
4. If the owner stated a lasting rule, propose it (`AGENTS.md` rule 2).

## Diagnose a failed run

1. `gh run list -R <owner/repo> --limit 6` to find the run and whether it is one failure or a streak.
2. `gh run view <id> -R <owner/repo> --log-failed | tail -n 80`. The real error is usually the last
   `##[error]` line, and the line before it often says which input caused it.
3. Read the code the failing step runs before guessing. Trace the cause back to the change that
   introduced it (`git log -S '<string>'`), then fix it at that source.
4. Add one test that would have failed, so the same thing cannot return.
5. The fix goes in a pull request in that repository. Follow its own `AGENTS.md`: usually you open
   the PR and stop.

Causes seen before:

- **`Invalid format '<text>'` in "Unable to process file command 'output'".** A step appends a
  script's stdout to `$GITHUB_OUTPUT`, and the script, or a module it imports, printed something
  else to stdout. Send progress to stderr. Assert that stdout is exactly the `key=value` lines.
- **`$(cat <<EOF ...)` "unexpected EOF" on a Mac runner.** macOS `/bin/bash` 3.2 misparses a heredoc
  inside `$()`. Use `read -r -d '' var <<EOF || true`.
- **An outage, an expired credential, or a runner that is offline.** Nothing in the code needs to
  change. Say so, and do not edit code to hide it.

## Triage with the script

`scripts/ci_triage.sh` hands the failed log to a local model runner on the runner Mac (which one,
and which model, is set at the top of the script; `CI_DEBUG_MODEL` overrides the model). The runner
reads the log, traces the cause and may edit the working tree, then writes a report. The engine is
part of the script, not your agent: any agent runs the script and reads what it prints.
`.github/workflows/triage.yml` does the same automatically and opens a PR (if the runner changed
code) or an issue (if it did not).

Rules that are never broken:

- **The runner never holds credentials.** `GH_TOKEN`, `GITHUB_TOKEN` and API keys are removed from
  its environment. Only the workflow's own steps use `gh`.
- **Nothing is merged automatically.** A triage fix is a PR for the owner to review.
- **The runner does not edit `.github/`.** Its changes there are discarded.
- **A `triage/*` branch never triggers another triage.** The caller's `if:` must check this.
- **Use local models only.** The prompt and the log stay on the runner Mac. Use a model that runs on
  the machine, never a hosted one.

A local 27B model is slow (about 2 minutes for a trivial prompt) and can be wrong. Its report is a
lead, not a verdict, so check the diff before merging.

## Wire a repository to auto-triage

1. Its workflows must run on the self-hosted runner that has the local model runner installed (default labels
   `self-hosted, macOS, ARM64`; pass `runner:` for others). Never on a public repository.
2. The private repo holding `triage.yml` must allow access from the owner's other private repos. This is
   set once: `gh api -X PUT repos/<owner>/<repo>/actions/permissions/access -f access_level=user`.
3. Add `.github/workflows/ci-failure-triage.yml` to that repository's default branch, using the
   caller snippet at the top of `triage.yml`. List the workflow names to watch in `workflows:`, and
   pass `checks:` (for example `cd host && python -m pytest -q`). `workflow_run` triggers only fire
   from the default branch.

## Worked example (2026-10-09)

1. Both scheduled "Publish public briefing" runs failed with
   `Invalid format 'water-quality: San Diego: 2 postings at our sites'`.
2. `briefing_covers_today.py`'s stdout goes to `$GITHUB_OUTPUT`, and the new `water_quality.collect`
   printed its progress there. The fix moved that line to stderr and added a test that stdout is only
   `skip=...`. A manual run with `require_freshness=true` then succeeded.
3. In the same session, that repo's in-repo triage workflow was moved here as the reusable
   `triage.yml`.
