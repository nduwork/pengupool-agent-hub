---
name: performance-pass
description: Finds and fixes a performance problem with numbers — takes a baseline, locates the real bottleneck (page load, interaction, API, database query, connection pool, cache), changes one thing, re-measures the same way, and keeps the change only if it beats the noise; then adds a budget or monitor so it does not come back. Use when users or monitoring report slowness, when a change may have caused a regression, or when a latency or load-time target must be met.
triggers:
  - this is slow
  - performance regression
  - speed this up
  - p95 latency
  - slow query
  - page load time
  - profile this
  - core web vitals
---

# Performance pass

No measurement, no optimization. A fix is a guess until the same measurement, taken the same
way, shows it moved past the noise.

## 1. Pin the target

Write down what is slow, for whom, and the number that would count as fixed ("p95 of
`GET /reports` under 300 ms", "LCP under 2.5 s on a mid-range phone"). If the owner has no
number, propose one from the SLO or from current traffic and get it agreed.

## 2. Baseline

Choose one repeatable measurement and record it with its conditions:

- the exact command or tool (load test, benchmark, profiler, browser trace, query plan);
- the environment, data size, warm or cold cache, and a fixed budget (runs, requests or
  seconds);
- several runs, so you know the run-to-run spread, not just one number.

Use field data (real-user metrics, production latency histograms) to confirm the problem is
real, and the synthetic measurement to iterate. Never load-test production without the owner's
go-ahead.

## 3. Find the bottleneck

Follow the symptom to the layer, and let the profile, trace or plan point at the code. The
common shapes and how to confirm each:
[references/bottlenecks.md](references/bottlenecks.md). Do not fix a suspect the measurement did
not point at.

## 4. Change one thing

Make the smallest change that addresses the bottleneck you found. One change per measurement:
three changes landed together give one number you cannot attribute. Keep behaviour the same; an
"optimization" that skips a validation or serves stale data that must be fresh is a bug.

## 5. Re-measure and decide

Re-run the baseline exactly: same command, same conditions, same budget. Then:

| Result | Decision |
| --- | --- |
| Beyond the run-to-run spread, tests green | keep; put before/after numbers in the commit message |
| Within the spread | revert |
| Worse | revert |
| Faster but a test went red | revert |

A neutral change is a revert. Code that bought nothing still costs upkeep.

## 6. Record every attempt

Keep a short ledger in the PR description (or the repository's existing perf notes), reverted
attempts included, so nobody retries a dead idea:

| Change | Before → after | Kept? | Why |
| --- | --- | --- | --- |

## 7. Guard it

Protect the metric that justified the work, not every number available: a budget check in CI
that compares a median over several runs (so noise does not make it flaky), and a production
monitor or alert on the user-facing percentile (see `instrument-service`). When a guard fires,
start again from step 2 with a fresh baseline.

## Report

The target, the baseline with its command and spread, the bottleneck and the evidence that
located it, each attempt with before/after and the decision, the guard added, and the files or
commits. Production-side changes (an index on a live database, pool size, cache config, CDN
settings) go to the owner as commands with how to verify and how to undo.
