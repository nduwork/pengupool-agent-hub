# research-agent

On-demand research for a pool of PenguPool agent sessions: **workflow design, function/API
design, datasource discovery, repo/tooling setup, and general due-diligence**.

This folder is the operating kit for the research helper. It does not hold product code; it holds
the contract, methodology and templates that make research reproducible and routable across
sessions, plus a read-only archive of earlier findings. PenguPool keeps the helper's memory and
records every turn; nothing is written into this folder.

## What this session owns

- Answering research requests from other sessions (or the user) with **sourced, confidence-labelled
  findings** and a recommendation.
- Turning a vague ask into answerable questions, a plan, and a decision-ready report.
- Searching PenguPool's record before researching, and marking reusable findings in the report
  (the host records them), so the same question is not researched twice.

It does **not** own implementation in a requester's repo, PR merges, or product decisions.

## Layout

```
README.md                     this file
AGENTS.md                     always-on rules, the PenguPool memory model, tools
docs/orchestration.md         how PenguPool routes sessions + how to summon this agent
docs/survey.md                landscape: existing research agents + engineering tooling
docs/persona.md               the engineering-scout persona
docs/design.md                the research-agent contract, methodology, playbooks, schemas
docs/plan.md                  the original staged plan (a record)
skills/research-agent/        loads the methodology when a research task arrives
skills/research-library/      marks reusable findings so `pengupool search` finds them
templates/request.md          a research request to fill in and send
templates/report.md           the format of the report section inside a log entry
templates/trade-study.md      weighted decision matrix template
```

## Memory

PenguPool keeps it. The agent searches it with `pengupool search`. PenguPool's triage proposes the
owner's lasting preferences and restrictions from the owner's own words, and the owner approves them
in the app; reusable findings are marked in the report, which the host records. See `AGENTS.md`.

## How to summon this agent

Because PenguPool routing is **adjacent-only** and a session has **one parent**, there are four
patterns (detail in `docs/orchestration.md`):

| Pattern | When | Cost |
| --- | --- | --- |
| **@tag one-off** — `@research-agent <question>` in your prompt | a single question, right now | none; one-prompt line |
| **Re-parent** — user groups this session under you | you need it for a while, alone | user action; serial |
| **Spawn-per-request** — user starts a fresh research session under you | parallel research, isolated scope | user action; session sprawl |
| **Route-to-hub** — keep it under a shared ancestor and route hop-by-hop | long-lived shared service | multi-hop latency, intermediate triage |

Recommended default: **@tag** for one-offs, **spawn-per-request** for parallel work,
**route-to-hub** when a stable shared service is wanted.

## How it is loaded

There is nothing to install. PenguPool's session context names this folder and lists each
`skills/<name>/SKILL.md`; any agent reads `AGENTS.md` and the skill files from there. Outside
PenguPool, point your agent at `AGENTS.md` and tell it to read the skill it needs.
