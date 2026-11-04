# Plan — setting up the research agent

> **Status note (2026-10-13):** this is the original staged plan, kept as a record. Two things it
> describes have since moved on: the per-request report archive was folded into per-subject logs under
> `logs/` (there is no `research/` folder), and `skills/research-agent/scripts/archive.sh` was never
> built — the agent appends the entry itself, per `AGENTS.md` rule 5.
>
> **Update (2026-10-21):** under PenguPool nothing is written into this folder. `MEMORY.md`,
> `memory.py`, `library.py` and their tests are gone; memory and reusable findings live in PenguPool
> memory (`AGENTS.md`), and the old `LIBRARY.md` and `logs/` archive has been removed.

Staged, smallest-useful-first. Each phase lists deliverables, acceptance, and anything that must
be decided. P0 is this bootstrap and is done in the same turn.

## P0 — Foundation (done)
**Deliverables**: `README.md`, `docs/orchestration.md` (how PenguPool routes + summon patterns),
`docs/survey.md` (landscape of existing research agents + tooling), `docs/persona.md` (the
engineering-scout persona), `docs/design.md` (the contract + playbooks), `docs/plan.md` (this file).
**Acceptance**: a new reader can explain how to summon this agent and what a research request /
report must contain.
**Status**: complete.

## P1 — Make it loadable and consistent
**Deliverables**
- The skill folders under `skills/`, which any agent can read (PenguPool's context lists them).
- `skills/research-agent/SKILL.md` — routing description + condensed methodology; loads when a
  research task arrives.
- `skills/research-agent/references/methodology.md` and `references/report-format.md`.
- `templates/request.md`, `templates/report.md`, `templates/trade-study.md`.
- The **owner-memory mechanism**: gitignored `MEMORY.md` + committed `templates/memory.md`, the
  protocol in `docs/memory.md`, the always-on ritual in `AGENTS.md` and the skill, and the
  concurrency-safe editor `skills/research-agent/scripts/memory.py` with `tests/test_memory.py`.
- `research/INDEX.md` (archive table) and `.gitignore`.

**Acceptance**
- A fresh agent session told to read `skills/research-agent/SKILL.md` follows it.
- A dry run: a sample request in `templates/request.md` shape produces a report in
  `templates/report.md` shape with sources and confidence labels.

## P2 — Register and install
**Deliverables**
- No install step: PenguPool loads the helper through its session context.
- Keep the session's role current (`pengupool ctl describe 01a0e364… --summary … --keywords …`)
  and verify placement with `pengupool ctl tree 01a0e364…`.
- Commit the repo and push to a remote (owner to confirm remote/name).

**Acceptance**: the skill appears in a new session's available-skills list; the role shows in the
pengupool tree; the repo has a first commit.

## P3 — Operationalize summoning
**Deliverables**
- A paste-ready **summon block** for requesters (choose pattern in `docs/orchestration.md` §6).
- A documented hub shape for long-lived use: one research child per domain, hub keeps keywords
  current so `route_match` routes correctly.
- One end-to-end test: a real request from a sibling/parent via `intercom ask`, answered and
  archived, with the reply path intact.

**Acceptance**: a requester that has never read this repo can get an answer with the summon block
alone; the exchange shows correctly in PenguPool's log/map.

## P4 — Harden the method
**Deliverables**
- Helper scripts under `skills/research-agent/scripts/`: `new-request.sh` (stamp a request file),
  `archive.sh` (move a finished report into `research/` and append to `INDEX.md`).
- A short self-check list (claims sourced? confidence stated? unknowns named? archived?).
- Optional: a template for datasource evaluation matrices.

**Acceptance**: scripts are idempotent, shellcheck-clean, and covered by a one-shot smoke test.

## P5 — Operate and improve
**Deliverables**
- Run real requests; log turnaround, rework and unanswered questions per request.
- Refine playbooks where rework clusters.
- Prune/rotate the archive; refresh keywords as domains change.

**Acceptance**: after N requests, a short retro names what to change; no research is repeated
because the archive was not consulted first.

## Decisions needed
1. **Remote**: where should this repo live (GitHub owner/name, private?) — needed for P2.
2. **Default pattern**: confirm @tag + spawn-per-request as the default, hub as the long-lived
   shape — affects P3's summon block.
3. **Edits to other repos**: confirm research stays read-only unless a request explicitly asks for
   changes (assumed in `design.md` §1).

## Risks
- **Re-parenting is user-only** (`docs/orchestration.md` §4): if a caller expects the agent to
  attach itself, it cannot. Mitigation: the summon block states who does the attach.
- **One parent at a time**: parallel demand needs spawn-per-request or the hub shape.
  Mitigation: documented in `design.md` §6.
- **Context bloat in the requester**: send TL;DR + path, not the full report.
- **Stale sources**: every time-sensitive claim is date-stamped and re-checked on reuse.
