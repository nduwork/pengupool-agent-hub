---
name: validate-data
description: Checks a dataset or an analysis result before anyone relies on it — completeness, uniqueness, referential integrity, valid ranges and formats, freshness, and reconciliation against a source of truth — and returns a verdict with counts for each failed check. Use before reporting a number, when data looks wrong, after a load or migration, or when reviewing someone else's query or analysis.
triggers:
  - validate the data
  - check data quality
  - does this number look right
  - reconcile against
  - is the data fresh
  - review this analysis
---

# Validate data

Two jobs: check the **data** (is the table fit for this question?) and check the **result** (is
this number right?). Both use aggregate queries only: a failed check reports how many rows fail,
never which ones. Ready-made checks and the pitfall list: [references/checks.md](references/checks.md).

## 1. Decide what "valid" means here

Before running anything, write the expectations for this question, from the owner, team memory,
documentation or the profile:

- the key and grain; which columns must not be null;
- allowed values or ranges (status set, 0 ≤ rate ≤ 1, dates not in the future, end ≥ start);
- which tables must join and how fully;
- how fresh the data must be (loaded within a day? a month closed?);
- the source of truth to reconcile against (a system of record, a finance report, a dashboard).

Unknown expectation → ask, or state the assumption you used.

## 2. Check the data

Run each check as one aggregate query and record `check | rows tested | rows failing | rate`.

| Dimension | Question | Typical check |
| --- | --- | --- |
| Completeness | Are required fields and periods present? | null counts; rows per period vs. expected; missing days |
| Uniqueness | One row per key? | rows vs. distinct keys; repeat-count histogram |
| Referential integrity | Do foreign keys find a parent? | orphan count each direction |
| Validity | Values in range and format? | out-of-range, not-in-set, format-mismatch counts |
| Consistency | Do related fields agree? | status "complete" with no completion date; end before start; totals ≠ sum of lines |
| Freshness | Is it current? | max load/event time vs. now; lag between event and load |
| Volume | Did the load land whole? | today's rows vs. the trailing average of the same weekday |
| Reconciliation | Does it match the source of truth? | totals and counts by period/segment, side by side, with the difference and % |

Cap thresholds by impact, not habit: a 0.1% null rate in a column that drives the answer can
matter more than 20% in one you do not use.

## 3. Check the result

For a number someone is about to rely on (yours or theirs):

1. **Question fit**: does the query answer the question as asked? Same population, window, metric
   definition the reader expects?
2. **Grain and joins**: row counts before and after each join; any fan-out?
3. **Filters**: each `WHERE` intended? Any silent exclusions (null keys, the `LEFT JOIN`/`WHERE`
   trap, timezone cut-offs)?
4. **Arithmetic**: right denominator; rates from summed parts; parts sum to the whole; no
   integer division; percentages near 100% where they should be.
5. **Periods**: equal lengths compared; partial current period dropped or flagged.
6. **Second route**: recompute the headline another way, or reconcile with the source of truth.
7. **Plausibility**: magnitude against the profile and last known values; any >50% swing, exact
   round number, exactly 0% or 100%, or identical values across groups gets explained before
   it is reported.
8. **Reasoning**: do the conclusions follow from the numbers? Bias checks: survivorship, selection
   on the outcome, mix shift (Simpson's), cherry-picked windows. Hand statistical claims to
   `statistical-analysis`.

## 4. Verdict

```
Verdict: Ready | Ready with caveats | Not ready
Checks:  <n> run, <n> passed, <n> failed
Failed:  <check> — <rows failing> of <rows tested> (<rate>) — impact on the answer — fix or caveat
Reconciled: <metric> ours <x> vs <source> <y>, diff <d> (<pct>)
Caveats for the reader: <bullets>
```

- **Ready**: all checks that bear on the answer pass and the result reconciles.
- **Ready with caveats**: issues exist but their effect is bounded and stated.
- **Not ready**: a failure could change the answer; list fixes in priority order.

When reviewing someone else's work, report first and stop; fix only what the owner picks.

## Rules

- Counts only: no failing keys, no example rows, even to "show what is wrong". Describe a failure
  by its count, share, period and segment (with small cells suppressed).
- Validation is read-only. Never clean, delete or patch data to make a check pass; report it and
  let the owner decide.
- Keep the check queries with the answer so the owner can rerun them.
