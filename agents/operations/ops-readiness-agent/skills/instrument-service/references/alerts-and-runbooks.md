# Alerts and runbooks

## Symptom or cause

| Pages someone (symptom) | Goes on a dashboard (cause) |
| --- | --- |
| error rate above the SLO for a sustained window | high CPU |
| p99 latency above target for a sustained window | one pod or worker restarted |
| oldest queued item older than the agreed limit | disk filling but not full |
| a scheduled job missed its run | a single slow dependency call |

A cause alert fires when users are fine and stays quiet for failures nobody predicted. A symptom
alert fires exactly when users are hurt, whatever the cause.

## Every alert

1. **Actionable.** If the honest response is "it fixes itself", it is not an alert; remove it
   or make it a dashboard panel.
2. **Threshold and window from evidence.** Take them from the SLO or from the metric's history,
   and write the reason next to the rule.
3. **Two severities only.** Page: users hurt now. Ticket: degraded, fix this week. A third
   level becomes noise.
4. **Runbook link.** Every alert points at one.
5. **Owned.** It names the team or rotation that gets it.

## Runbook

Keep it where the repository keeps runbooks (create `docs/runbooks/<alert-name>.md` only if
there is no place yet). The smallest useful runbook has three lines:

```markdown
# <alert name>
What it means: <the likely causes, most common first>
Check first: <one command or query, and how to read its result>
Escalate to: <team or rotation>
```

Add steps only when the first check is not enough to decide. Three common causes covered well
beat twenty edge cases nobody reads. After an incident that used a runbook, fix whatever step was
wrong or missing before closing it.

## Smells to flag in a review

- New retries, queues or outside calls with no new telemetry.
- Log lines built by pasting values into sentences.
- No request id, or one that is dropped at a queue or service hop.
- Metric labels holding user ids, raw paths or error text.
- Latency tracked only as an average.
- An alert that fires daily and is acknowledged without action.
- Secrets, tokens or personal data visible in actual log output.
