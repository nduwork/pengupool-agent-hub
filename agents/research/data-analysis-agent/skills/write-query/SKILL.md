---
name: write-query
description: Turns a data question into correct, efficient, read-only SQL that returns aggregates — pins the grain, picks joins that cannot multiply rows, places filters and windows deliberately, uses the right dialect, keeps cost down, and proves the result with verification queries. Use when writing a new query, fixing or speeding up an existing one, or porting SQL between Snowflake, BigQuery, Postgres, Redshift, Databricks, DuckDB, MySQL or SQL Server.
triggers:
  - write a query
  - write sql
  - how many
  - fix this query
  - query is slow
  - convert this sql
---

# Write query

Correct first, then cheap, then pretty. Every query this helper runs returns aggregates; small
cells are suppressed. Dialect notes: [references/dialects.md](references/dialects.md). Patterns
(windows, cohorts, funnels, dedup, suppression): [references/patterns.md](references/patterns.md).

## 1. Pin the question

Write it as one line before any SQL:

> **measure** (e.g. distinct patients tested, median turnaround hours) **per** grain of the output
> (e.g. per site per month) **for** population (filters, exclusions) **over** time window
> (with timezone, complete periods only).

If any part is ambiguous ("active", "last month", which date column), ask, or pick the documented
definition and state it in the answer. Note the dialect; ask if you cannot tell.

## 2. Plan from the data

- Use the grain and joins from `explore-data`. If you have not profiled a table, do it now.
- Start from the table at the grain closest to the output. Bring other tables in only after
  reducing them to the join key (`GROUP BY key` or `EXISTS`), so a join cannot fan out.
- Prefer an owner-blessed view or mart over raw tables, and say which you used.
- Apply the standard exclusions (test, internal, cancelled, deleted, duplicates) the owner or team
  memory defines.

## 3. Write it

- One CTE per step, named for what it holds (`tests_in_window`, `first_result_per_order`).
- Name columns; never `SELECT *` in the final output or in a CTE over a wide table.
- Filter as early as possible and on partition or cluster columns when they exist.
- Half-open time windows: `ts >= start AND ts < end`. Never `BETWEEN` on timestamps.
- Count entities with `COUNT(DISTINCT id)` when a join could repeat them; count events with
  `COUNT(*)` only at the event grain.
- Guard division with `NULLIF(den, 0)`; compute rates as `SUM(num) / SUM(den)`, never as an
  average of per-group rates.
- `LEFT JOIN` + a `WHERE` on the right table silently becomes an inner join; put that condition
  in the `ON` clause, or use an inner join on purpose.
- `NOT IN` with a nullable subquery returns nothing; use `NOT EXISTS`.
- Window functions: give `PARTITION BY` and `ORDER BY` with a tiebreaker; set the frame
  explicitly for running or moving values.
- Make the final `SELECT` aggregate and add the small-cell guard (see patterns).
- Comment the why on any line a reader would question.

## 4. Check the cost

- Look at the table size and the plan (`EXPLAIN`, BigQuery dry run, Snowflake query profile)
  before running against anything large.
- Partition pruning happening? Joins on the right keys and types? No accidental cross join?
- Prefer `APPROX_COUNT_DISTINCT` for exploration on huge tables; switch to exact for the answer.
- Set a statement timeout or `LIMIT` on exploratory aggregate queries where the engine allows.

## 5. Verify the result

Run at least two of these before reporting a number:

- **Row and key counts** at each CTE step: did a join add rows it should not have?
- **Totals reconcile**: the sum of the parts equals the whole; the population count matches an
  independent count of the base table with the same filters.
- **Second route**: compute the headline number another way (a different join path, a known
  dashboard, last period's report) and compare.
- **Boundaries**: first and last period complete? Nulls in group keys landing in a hidden group?
- **Plausibility**: rates in [0, 1], no negative counts, magnitudes in line with the profile.

A mismatch is a finding: fix the query or carry the gap into the caveats.

## 6. Report

Give, in this order:

1. the answer in one or two sentences, with units and the time window;
2. the aggregated result table (small cells shown as `<10`);
3. the final SQL in a code block, readable on its own;
4. definitions, filters, data as-of time, and verification done;
5. caveats and what would change the answer.

## Fixing or porting a query

- Read it first and restate in one line what it computes; point out where that differs from what
  the owner wants.
- Common faults: fan-out joins, the `LEFT JOIN`/`WHERE` trap, `BETWEEN` on timestamps, timezone
  mixing, integer division, averages of averages, `NOT IN` with nulls, ungrouped columns.
- Porting: map functions with `references/dialects.md`, then compare old and new results on the
  same window before trusting the port.
