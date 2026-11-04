# ci-debug

A task repo for one job: **Triage a failed GitHub Actions run with a local model and propose a fix**

An agent session started here loads `skills/ci-debug/SKILL.md`, follows `AGENTS.md`, and keeps its owner's
standing rules in PenguPool memory.

| Path | Purpose |
| --- | --- |
| `AGENTS.md` | always-on rules for any agent here |
| `skills/ci-debug/SKILL.md` | how to do the task |
| `.github/workflows/triage.yml` | reusable workflow: a local model runner triages a caller's failed run, opens a PR or an issue |
| `scripts/ci_triage.sh` | the same triage, run by hand on the runner Mac |

