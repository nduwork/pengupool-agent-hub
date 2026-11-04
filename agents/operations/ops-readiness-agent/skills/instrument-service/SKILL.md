---
name: instrument-service
description: Adds and reviews the telemetry a production service needs — structured logs with a request id, rate/error/latency metrics with bounded labels, traces across service hops, and alerts on what users feel, each with a short runbook — then proves the telemetry works by triggering it. Use when shipping a feature, endpoint, job or integration to production, when an incident was hard to diagnose, or when setting up or reviewing alerts.
triggers:
  - add logging
  - add metrics
  - add tracing
  - set up alerts
  - instrument this
  - observability
  - we could not tell what happened
  - write a runbook
---

# Instrument a service

Telemetry is part of the feature, written with it like tests. The goal is that the person on
call can answer "is it working, and if not, where and why" from outside, without reading the
code.

## 1. Start from the questions

Before adding anything, write down two to four questions someone on call will ask about this
feature, in plain words ("how many uploads fail, and with what error?", "is the payment
provider slower than yesterday?"). Every signal you add must help answer one of them. If you
cannot name the questions, ask the owner; do not log everything.

## 2. Pick the signal per question

| Question shape | Signal |
| --- | --- |
| How often, how fast, across all traffic | metric |
| Where did the time go across services | trace |
| What exactly happened in this one case | structured log |

Metrics raise the flag, traces locate the hop, logs explain the case.

## 3. Read what is already there

Find the repository's logger, metrics client, tracing setup, alert config and runbook folder.
Extend them. Match the existing event and metric naming. Add a new library only when the
repository has none, and name the choice for the owner.

## 4. Logs

- One event per line as structured fields with a stable event name (`upload_failed`), not a
  sentence with values pasted in.
- A request or run id on every line, created at the edge and passed on every outbound call
  and queue message. If several entry points (a scheduler, an endpoint, a CLI) write to the
  same sink, add a field naming which one started the run.
- Levels mean something: `error` someone must act, `warn` degraded but handled, `info` a
  business event, `debug` off in production.
- Allowlist fields. Never log secrets, tokens, request bodies or personal data.

## 5. Metrics

- For each endpoint and each outside dependency: request rate, error rate, and latency as a
  histogram. For pools, queues and hosts: how full, how much is waiting, errors.
- Labels come from small fixed sets (route template, status class, dependency name). User ids,
  raw URLs and error text are never labels; they go in logs and traces.
- Read latency as p50/p95/p99, never as an average.

## 6. Traces

Use the tracing the service already has, or a vendor-neutral standard if it has none. Rely on
automatic HTTP/DB instrumentation; add a manual span only around a unit of work on-call will ask
about. Carry the context across every async hop, or the trace stops there.

## 7. Alerts

Alert on what users feel (error rate, latency, a queue's oldest item), not on causes (CPU, one
restart). Each alert must be actionable, have a threshold and window justified by an SLO or past
data, use one of two severities (page now / ticket this week), and link a runbook. Details and
the runbook shape: [references/alerts-and-runbooks.md](references/alerts-and-runbooks.md).

Writing an alert rule in the repository is fine. Applying it to a live alerting system is a
production change: hand the owner the command.

## 8. Prove it works

Telemetry is code and can be wrong. Before calling it done, in a test or staging environment:

- force one failure and find it by its request id; the fields are structured and readable;
- send some traffic and see each new metric series with the expected labels and sane values;
- follow one request through the trace with no gaps;
- fire each new alert once (a temporary low threshold) and confirm it reaches the right place
  and its runbook link opens.

## Report

List the on-call questions, each signal mapped to one, the files changed, and the evidence from
step 8 (the query or command and what it returned). Name anything you could not verify and why.
