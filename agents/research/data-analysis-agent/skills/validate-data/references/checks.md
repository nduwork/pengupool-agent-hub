# Validation checks

Every check returns counts. Replace names; adjust syntax with the write-query dialect notes.

## A check suite in one query

```sql
SELECT 'order_id not null'   AS check_name, COUNT(*) AS tested, COUNT(*) - COUNT(order_id) AS failing FROM orders
UNION ALL
SELECT 'order_id unique',     COUNT(*), COUNT(*) - COUNT(DISTINCT order_id) FROM orders
UNION ALL
SELECT 'status in set',       COUNT(*), SUM(CASE WHEN status NOT IN ('open','done','cancelled') OR status IS NULL THEN 1 ELSE 0 END) FROM orders
UNION ALL
SELECT 'done has done_at',    SUM(CASE WHEN status = 'done' THEN 1 ELSE 0 END),
                              SUM(CASE WHEN status = 'done' AND done_at IS NULL THEN 1 ELSE 0 END) FROM orders
UNION ALL
SELECT 'done_at >= created',  COUNT(done_at), SUM(CASE WHEN done_at < created_at THEN 1 ELSE 0 END) FROM orders
UNION ALL
SELECT 'created not future',  COUNT(*), SUM(CASE WHEN created_at > CURRENT_TIMESTAMP THEN 1 ELSE 0 END) FROM orders;
```

Add `1.0 * failing / NULLIF(tested, 0) AS rate` in an outer query.

## Referential integrity

```sql
SELECT
  (SELECT COUNT(*) FROM results r
    WHERE NOT EXISTS (SELECT 1 FROM orders o WHERE o.order_id = r.order_id)) AS results_without_order,
  (SELECT COUNT(*) FROM orders o
    WHERE NOT EXISTS (SELECT 1 FROM results r WHERE r.order_id = o.order_id)) AS orders_without_result;
```

The second number is often legitimate (work in progress); split it by age or status before calling
it a defect.

## Freshness and volume

```sql
SELECT MAX(loaded_at)                                  AS last_load,
       MAX(event_at)                                   AS last_event,
       SUM(CASE WHEN CAST(event_at AS DATE) = CURRENT_DATE - 1 THEN 1 ELSE 0 END) AS rows_yesterday
FROM t;

-- yesterday vs. the same weekday over the previous 4 weeks
WITH daily AS (
  SELECT CAST(event_at AS DATE) AS d, COUNT(*) AS n
  FROM t
  WHERE event_at >= CURRENT_DATE - 29 AND event_at < CURRENT_DATE
  GROUP BY 1
)
SELECT MAX(CASE WHEN d = CURRENT_DATE - 1 THEN n END)                                   AS yesterday,
       AVG(CASE WHEN d IN (CURRENT_DATE - 8, CURRENT_DATE - 15, CURRENT_DATE - 22, CURRENT_DATE - 29) THEN n END) AS same_weekday_avg
FROM daily;
```

## Reconciliation

Compare at the coarsest grain that both sides share, then drill into the segment that differs.

```sql
WITH ours AS (
  SELECT DATE_TRUNC('month', created_at) AS month, COUNT(DISTINCT order_id) AS n
  FROM orders WHERE is_test = FALSE GROUP BY 1
),
truth AS (
  SELECT month, order_count AS n FROM finance_monthly_orders
)
SELECT COALESCE(o.month, t.month) AS month,
       o.n AS ours, t.n AS truth,
       o.n - t.n AS diff,
       1.0 * (o.n - t.n) / NULLIF(t.n, 0) AS diff_pct
FROM ours o
FULL OUTER JOIN truth t ON t.month = o.month
ORDER BY 1;
```

Explain each difference by cause (definition, timing cut-off, timezone, late-arriving rows,
exclusions) before calling either side wrong. Agree the tolerance with the owner (exact for
counts of record, small % for estimates).

## Join-explosion check

```sql
SELECT (SELECT COUNT(*) FROM orders)                                  AS before_join,
       (SELECT COUNT(*) FROM orders o JOIN results r ON r.order_id = o.order_id) AS after_join,
       (SELECT COUNT(DISTINCT o.order_id) FROM orders o JOIN results r ON r.order_id = o.order_id) AS distinct_after;
```

`after_join > distinct_after` means sums and counts over that join need a reduce-first CTE.

## Pitfalls to look for in a result

| Pitfall | What it looks like | Remedy |
| --- | --- | --- |
| Fan-out join | totals too big after adding a table | aggregate the many side to the key first |
| Partial period | the current month "dropped" | complete periods, or same-number-of-days comparison |
| Shifting denominator | rate moves when a definition changed | one definition across all periods; note changes |
| Average of averages | groups of different sizes averaged equally | sum numerators and denominators, then divide |
| Survivorship | only entities that still exist are counted | include closed, churned, deleted where the question needs them |
| Selection on outcome | segment defined by the thing measured | define segments by what was known beforehand |
| Mix shift (Simpson's) | total moves opposite to every segment | show segment rates beside the total |
| Timezone mismatch | daily counts off near midnight | convert all timestamps to one zone, state it |
| Null keys in GROUP BY | a silent null group, or rows dropped by an inner join | count nulls separately and report them |
| Cherry-picked window | trend only appears with one start date | show a longer window or several starts |
| Look-ahead | uses information not known at the time | restrict features to values available then |

## Spot checks without rows

Where a reviewer would "trace a few records", trace aggregates instead: run the metric for one
small, well-understood slice (one site, one day, one category) where the owner knows the expected
count, and compare. If the slice has fewer than 10 units, widen it.
