# Flow graph format

Part of the review-guide-flowchart skill: the JSON the script takes on stdin, with a worked example.

```json
{
  "nodes": [
    {"id": "req", "label": "Checkout request", "kind": "context", "shape": "terminal"},
    {"id": "valid", "label": "Order valid?", "kind": "changed", "shape": "decision"},
    {"id": "reject", "label": "400 with reasons", "kind": "added", "shape": "terminal"},
    {"id": "enqueue", "label": "Enqueue fulfilment", "kind": "added"},
    {"id": "queue", "label": "fulfilment queue", "kind": "added", "shape": "store"},
    {"id": "ship", "label": "Worker ships order", "kind": "added"},
    {"id": "poll", "label": "Cron poller ships order", "kind": "removed"}
  ],
  "edges": [
    {"from": "req", "to": "valid"},
    {"from": "valid", "to": "reject", "label": "No", "kind": "added"},
    {"from": "valid", "to": "enqueue", "label": "Yes", "kind": "added"},
    {"from": "enqueue", "to": "queue", "kind": "added"},
    {"from": "queue", "to": "ship", "kind": "added"},
    {"from": "valid", "to": "poll", "label": "Yes", "kind": "removed"}
  ],
  "caption": "Also changed: order tests, fulfilment queue config."
}
```

- `kind` is `added`, `changed`, `removed` or `context` (unchanged, but needed to make the
  flow readable). Edge `kind` is optional (`added` becomes a thick arrow, `removed` a dotted one).
  Colour is the point of `kind`: green added, yellow changed, red removed, uncoloured context.
  The chart draws a legend with the kinds it uses.
  Mark steps that already existed (the trigger, a skill or service the change calls) as
  `context`, so the chart shows what is new against what was there.
- `caption` is optional, one line, up to 200 characters, with no links.
- The script escapes quotes, brackets, pipes, `@` and `#`, so labels never break the syntax,
  ping anyone or link an issue. It rejects any label or caption that looks like a token, email
  or SSN.
