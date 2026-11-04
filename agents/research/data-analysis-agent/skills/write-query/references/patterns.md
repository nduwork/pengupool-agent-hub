# Query patterns

Each pattern ends in an aggregate. Table and column names are placeholders.

## Small-cell suppression

Apply to every final result that counts people, samples or other units.

```sql
WITH result AS (
  SELECT site, test_type, COUNT(DISTINCT order_id) AS n_orders
  FROM orders_in_window
  GROUP BY site, test_type
)
SELECT site,
       test_type,
       CASE WHEN n_orders < 10 THEN NULL ELSE n_orders END AS n_orders,  -- shown as "<10"
       n_orders < 10                                    AS suppressed
FROM result;
```

If a row total or a "rest" group would let a reader subtract their way to a suppressed cell,
suppress a second cell or report only rounded totals. Rates whose denominator is below 10 are
suppressed too.

## Reduce before joining

```sql
-- one row per order, whatever the number of results per order
WITH result_counts AS (
  SELECT order_id, COUNT(*) AS n_results, MAX(resulted_at) AS last_result_at
  FROM results
  GROUP BY order_id
)
SELECT o.site, COUNT(*) AS n_orders, AVG(rc.n_results) AS avg_results_per_order
FROM orders o
JOIN result_counts rc ON rc.order_id = o.order_id
GROUP BY o.site;
```

## Latest record per key (inside a CTE only)

```sql
WITH latest AS (
  SELECT order_id, status,
         ROW_NUMBER() OVER (PARTITION BY order_id ORDER BY updated_at DESC, version DESC) AS rn
  FROM order_status_history
)
SELECT status, COUNT(*) AS n_orders
FROM latest
WHERE rn = 1
GROUP BY status;
```

Snowflake, BigQuery, Databricks and DuckDB also allow `QUALIFY rn = 1`.

## Rate over complete periods

```sql
WITH monthly AS (
  SELECT DATE_TRUNC('month', created_at) AS month,
         COUNT(*)                                        AS n_total,
         SUM(CASE WHEN status = 'failed' THEN 1 ELSE 0 END) AS n_failed
  FROM samples
  WHERE created_at >= DATE '2025-01-01'
    AND created_at <  DATE_TRUNC('month', CURRENT_DATE)   -- drop the partial month
  GROUP BY 1
)
SELECT month, n_total, n_failed,
       1.0 * n_failed / NULLIF(n_total, 0) AS failure_rate
FROM monthly
ORDER BY month;
```

## Running and moving values

```sql
SELECT day, n,
       SUM(n) OVER (ORDER BY day ROWS BETWEEN UNBOUNDED PRECEDING AND CURRENT ROW) AS running_n,
       AVG(n) OVER (ORDER BY day ROWS BETWEEN 6 PRECEDING AND CURRENT ROW)         AS avg_7d,
       n - LAG(n, 7) OVER (ORDER BY day)                                          AS change_vs_week_ago
FROM daily_counts;
```

Fill missing days first (join to a calendar or `GENERATE_SERIES`), or a 7-row window spans more
than 7 days.

## Share of total

```sql
SELECT category, n, 1.0 * n / SUM(n) OVER () AS share
FROM (SELECT category, COUNT(*) AS n FROM t GROUP BY category) c;
```

## Cohort retention

```sql
WITH first_seen AS (
  SELECT account_id, DATE_TRUNC('month', MIN(event_at)) AS cohort
  FROM events GROUP BY account_id
),
active AS (
  SELECT DISTINCT account_id, DATE_TRUNC('month', event_at) AS month
  FROM events
)
SELECT f.cohort,
       DATEDIFF(month, f.cohort, a.month) AS months_since,   -- dialect: see dialects.md
       COUNT(DISTINCT a.account_id)       AS n_active
FROM first_seen f
JOIN active a ON a.account_id = f.account_id
GROUP BY 1, 2;
```

Divide by the cohort size (the `months_since = 0` row) in the outer query. Recent cohorts have
not had time to reach later months; leave those cells empty, not zero.

## Funnel

```sql
WITH steps AS (
  SELECT case_id,
         MAX(CASE WHEN step = 'ordered'  THEN 1 ELSE 0 END) AS s1,
         MAX(CASE WHEN step = 'received' THEN 1 ELSE 0 END) AS s2,
         MAX(CASE WHEN step = 'reported' THEN 1 ELSE 0 END) AS s3
  FROM case_events
  GROUP BY case_id
)
SELECT SUM(s1) AS ordered,
       SUM(s1 * s2) AS received,
       SUM(s1 * s2 * s3) AS reported
FROM steps;
```

Multiplying the flags keeps the funnel strict (a later step counts only after the earlier ones).
Add timestamps and compare them if order matters.

## Missing periods as a count

```sql
-- days with no rows in the window
SELECT COUNT(*) AS missing_days
FROM calendar c
LEFT JOIN (SELECT DISTINCT CAST(ts AS DATE) AS d FROM t) x ON x.d = c.d
WHERE c.d >= DATE '2025-01-01' AND c.d < CURRENT_DATE AND x.d IS NULL;
```
