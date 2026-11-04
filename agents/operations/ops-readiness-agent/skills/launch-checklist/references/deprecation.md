# Retiring an old system

Anything people can observe, someone depends on, including its bugs and quirks. So retiring a
system means moving its users, not just announcing an end date.

## Decide first

Answer before proposing removal:

1. Does it still do something nothing else does? If yes, keep it, or build that first.
2. Who and what uses it, and how much? Measure it from logs, metrics, dependency search; do not
   guess.
3. Is there a replacement that already runs in production and covers the critical uses?
4. What does each consumer's move cost, and what does keeping the old system cost per year
   (patches, upgrades, on-call, confusion)?

## Advisory or required

| Kind | When | What it takes |
| --- | --- | --- |
| Advisory | the old system is stable and harmless | notice, docs, warnings in logs or responses; users move on their own time |
| Required | security risk, blocks other work, or upkeep is too costly | a firm date, a migration guide, tooling, and help for each consumer |

Default to advisory. A required retirement without tooling and help is a broken promise.

## The steps

1. **Replacement proven.** It runs in production and covers the critical uses.
2. **Notice.** Status, replacement, date (or "no date yet"), reason, and a migration guide with
   concrete steps.
3. **Move consumers one at a time.** For each: find every touchpoint, switch it, verify the
   behaviour matches, remove the old reference. If you own the old system, moving its users is
   your work.
4. **Measure zero.** Usage at zero for an agreed period, from logs or metrics.
5. **Remove.** Code, tests, config, docs, dashboards, alerts and the notice itself. Removal in
   production is an owner-run step.

## Ways to move traffic

- **Gradual cutover.** Old and new run side by side; route a growing share to the new one; remove
  the old one at 0%.
- **Adapter.** Keep the old interface, back it with the new implementation, and move callers
  later.
- **Per-consumer flag.** Switch consumers one at a time with a flag; flip back if one breaks.

## Schema changes: expand, migrate, contract

Data is the part a code rollback cannot undo, and during a rollout old and new code run at the
same time. Never rename or drop a column in place. Example, renaming `name` to `full_name`:

1. Add `full_name`, nullable. Deploy.
2. Write both columns on every insert and update. Deploy.
3. Backfill old rows in small throttled batches.
4. Read from `full_name`, still writing both. Deploy and let it settle.
5. Stop writing `name`. In a later, separate deploy, drop it.

Every step is deployable and reversible on its own. Each migration has a down step that was run
before merge. Build big indexes without blocking writes where the database supports it.

## Signs of trouble

- A deprecated system with no working replacement.
- A notice with no guide or tooling, or "advisory" for years with no progress.
- New features added to the system being retired.
- Removal without usage measured at zero.
- A schema change shipped in the same deploy as the code that needs it.
- Code nobody owns but others call: give it an owner or a retirement plan, not limbo.
