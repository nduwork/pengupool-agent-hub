---
name: launch-checklist
description: Prepares a release for production and checks it is ready — tests and review, migrations with a tested undo, feature flags, a staged rollout with advance/hold/roll-back thresholds, monitoring, a written rollback plan and docs — and plans the retirement of an old system or API (replacement first, usage measured, consumers migrated, schema changes in expand/contract phases). Writes the checklist and the exact commands; the owner deploys. Use before shipping a release, opening a feature to users, running a data or schema migration, or removing an old system.
triggers:
  - deploy checklist
  - ready to ship
  - launch plan
  - rollout plan
  - rollback plan
  - feature flag rollout
  - deprecate
  - migrate off
  - remove the old
---

# Launch checklist

A launch is safe when it is reversible, watched and incremental. You produce a checklist filled
with evidence and the exact commands; the owner runs the deploy and every step that touches
production.

## 1. Scope the release

Read the diff or release notes, the deploy config and the CI status. Write down:

- what changes for users, and which services, jobs and data stores it touches;
- whether it has a schema or data migration, a feature flag, a breaking API change, new
  config or secrets, or a new outside dependency;
- the risk level (routine / notable / high) and why.

These answers decide which parts of the checklist apply. Drop sections that do not; never
pad.

## 2. Fill the checklist with evidence

Use the template in [references/checklist.md](references/checklist.md). Each item is checked
with what proves it (a CI run link, a command and its output, a file path) or left open with
the reason. Items you cannot verify are open, not assumed.

## 3. Decide the triggers before the deploy

Agree with the owner, before anything ships, the numbers that mean advance, hold or roll back
at each stage. Default starting points, measured against the pre-deploy baseline:

| Signal | Advance | Hold and look | Roll back |
| --- | --- | --- | --- |
| error rate | within ~10% | 10% to 2× | above 2× |
| p95 latency | within ~20% | 20–50% higher | more than 50% higher |
| new error types | none | rare | spreading |
| key user flow | works | degraded | broken, or any data integrity issue |

If the service has an error budget and it is nearly spent, recommend only slow, low-risk
rollouts; if it is spent, recommend holding feature releases.

## 4. Rollout and rollback plan

Write the order of steps and the command for each, for the owner to run:

1. Deploy to staging; run the tests and a smoke test of the key flows.
2. Deploy to production with the flag off (when there is one); check health and errors.
3. Turn it on for the team, then a small share of users, then larger steps; watch the
   triggers for an agreed window at each step.
4. Full rollout; keep watching for the agreed period; schedule removal of the flag and the old
   code path.

The rollback plan names how to undo each step (flag off, redeploy the previous version, the
migration's down step), how long each takes, how to confirm it worked, and what happens to data
written by the new version. A migration without a tested down step is a deploy that cannot be
rolled back: flag it as a blocker.

## 5. After the deploy

Hand the owner a short first-hour list: health check, error and latency against the triggers,
the key user flow by hand, logs flowing and readable, and the rollback path confirmed ready.
Then the wrap-up: release notes or changelog, stakeholders told, tickets closed, flag removal
scheduled.

## Retiring an old system

Retiring an API, service, library, feature or column follows its own plan:
[references/deprecation.md](references/deprecation.md). In short: build and prove the
replacement first, measure who still uses the old one, migrate consumers one at a time (you own
that work if you own the old system), change schemas in additive phases, and remove the old one
only when usage is measured at zero.

## Report

The filled checklist with evidence, the open items and what blocks each, the agreed triggers,
the rollout and rollback commands (marked "owner runs"), and anything that should stop the
launch.
