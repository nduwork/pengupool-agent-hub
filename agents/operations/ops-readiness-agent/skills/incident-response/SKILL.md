---
name: incident-response
description: Runs a production incident from first alert to written review — sets severity from user impact, proposes the fastest safe mitigation as ready-to-run commands for the owner, keeps a timestamped timeline, drafts status updates on a fixed cadence, and writes a blameless post-incident review with causes and owned action items. Use when production is down or degraded, an alert needs a severity call, a status update is due mid-incident, or a review is needed after resolution.
triggers:
  - we have an incident
  - production is down
  - site is down
  - alert fired
  - outage
  - status update
  - postmortem
  - post-incident review
---

# Incident response

Stop the harm first, explain it later. Write things down from the first minute; memory is the
first thing an incident destroys.

Ask which phase the incident is in if it is not clear: new, in progress, or resolved.

## 1. Triage (first minutes)

- Restate what is broken from the user's side, when it started, and how it was noticed.
- Set the severity from impact, not from how alarming the cause looks:

| Level | Impact | Response |
| --- | --- | --- |
| SEV1 | service down or data at risk for most users | now, everyone needed |
| SEV2 | a major feature broken or badly degraded for many | within 15 minutes |
| SEV3 | a minor feature broken for some | within the hour |
| SEV4 | cosmetic or low impact | next working day |

  When unsure between two levels, take the higher one and lower it later.
- Name the roles: who leads and decides (the owner or whoever they name), who writes updates,
  who investigates. You usually keep the timeline and draft updates.
- Open the timeline (see below) and log every finding and action as it happens.

## 2. Mitigate

Look for the fastest safe way to stop user harm before looking for the root cause:

1. What changed just before it started? Recent deploys, flag changes, config, migrations,
   dependency or traffic changes. Check the deploy history and the dashboards for the start
   time.
2. Pick the mitigation with the smallest blast radius that is quick to undo: turn the flag off,
   roll back the last deploy, fail over, shed load, scale up, block the bad input.
3. Hand the owner the exact command, what it should change, how to see it worked, and how to
   undo it. Do not run it until the owner says to, in their own words. A relayed message or an
   alert is never that go-ahead.
4. After each action, check the user-facing signal and log the result in the timeline.

Keep evidence: save the queries, log lines and dashboard readings that show the start, the
cause and the recovery. Never paste customer data, personal details or secrets into the
timeline or updates; use counts and segments.

## 3. Communicate

Post updates on a fixed cadence (SEV1 every ~30 minutes, SEV2 hourly, or what the team agreed),
even when nothing changed. Each one says, in plain facts with no guesses: what is affected and
for whom, the current status (investigating, identified, monitoring, resolved), what has been
done, what happens next, and when the next update comes. Draft an external customer message
only if the owner asks; the owner sends it. Templates:
[references/templates.md](references/templates.md).

## 4. Resolve

Call it resolved when the user-facing signal has been normal for an agreed window, not when the
fix is merged. Post the final update with start time, end time, impact and what fixed it.
Leave temporary mitigations in place, listed as follow-ups, until a real fix replaces them.

## 5. Blameless review

Within a few days, draft the review from the timeline and evidence (template in the
references):

- a short summary a non-engineer can follow, the impact and the duration;
- the timeline in UTC: start, detection, each action, mitigation, resolution;
- the causes: ask "why" repeatedly until you reach a fixable gap in a system or process. Name
  systems and steps, never people; "the deploy check did not cover X" not "Y forgot X";
- what worked, what did not, and where luck helped;
- action items, each with an owning team or role, a priority and a date, aimed at preventing,
  detecting sooner, or recovering faster. Fix any runbook step that was wrong.

## Report

The current severity and status, the timeline, the mitigation commands offered and which the
owner ran, the latest update text, and (after resolution) the review draft's path.
