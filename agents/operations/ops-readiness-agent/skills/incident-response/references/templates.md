# Incident templates

Use counts and segments for affected users. No names, ids, customer data or secrets anywhere.

## Timeline (keep from the first minute)

```markdown
| Time (UTC) | Who (role) | What happened or was done | Evidence |
| --- | --- | --- | --- |
| 14:02 | alerting | checkout error rate 9% (normal <1%) | <dashboard or query> |
| 14:05 | lead | declared SEV2 | |
| 14:11 | responder | last deploy at 13:58 touched payment client | <deploy log> |
| 14:14 | owner | ran rollback to previous release | <command> |
| 14:20 | responder | error rate back under 1% | <query result> |
```

## Status update

```markdown
**<title>** — SEV<n> — <Investigating | Identified | Monitoring | Resolved>
Updated <HH:MM UTC>. Next update by <HH:MM UTC>.

Impact: <what users cannot do, roughly how many or which segment, since when>
Now: <what we know, facts only>
Done: <actions taken and their effect>
Next: <what happens next>
```

## Post-incident review

```markdown
# Review: <title>
Date <date> · Duration <start–end UTC, total> · Severity SEV<n> · Status draft

## Summary
<two or three sentences: what broke, who was affected, what fixed it>

## Impact
<users or requests affected (counts), duration, any data affected, any promises missed>

## Timeline
<from the timeline above, trimmed to the moments that matter>

## Causes
<the trigger, then repeated "why" down to fixable gaps in systems or process>

## Detection and response
<how it was found, how long detection and mitigation took, what slowed them>

## What went well / what went badly / where we got lucky

## Action items
| Action | Kind (prevent / detect / recover) | Owner (team or role) | Priority | Due |
| --- | --- | --- | --- | --- |
```

A review is blameless: it describes what the system let happen and what each person knew at the
time. If a sentence names a person as the cause, rewrite it as the missing check or safeguard.
