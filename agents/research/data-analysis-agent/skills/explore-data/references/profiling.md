# Profiling queries

All of these return aggregates. Replace `t`, `col`, `key_cols` and `ts` with real names. Syntax is
ANSI-ish; dialect differences are in the write-query skill's `references/dialects.md`.

## Catalog

```sql
-- tables and approximate sizes (most engines)
SELECT table_schema, table_name, table_type
FROM information_schema.tables
WHERE table_schema NOT IN ('information_schema', 'pg_catalog')
ORDER BY table_schema, table_name;

-- columns, in order, with comments where the engine keeps them
SELECT column_name, data_type, is_nullable
FROM information_schema.columns
WHERE table_schema = 'sch' AND table_name = 't'
ORDER BY ordinal_position;
```

Snowflake also has `SHOW TABLES IN SCHEMA db.sch` (row counts included); BigQuery has
`` `proj.ds.INFORMATION_SCHEMA.TABLES` `` and `__TABLES__` for sizes; DuckDB has `DESCRIBE t` and
`SUMMARIZE t` (SUMMARIZE prints min/max values, so do not run it on tables with personal columns).

## Size, range, freshness

```sql
SELECT COUNT(*)            AS n_rows,
       MIN(ts)             AS first_ts,
       MAX(ts)             AS last_ts,
       SUM(CASE WHEN ts > CURRENT_TIMESTAMP THEN 1 ELSE 0 END) AS n_future
FROM t;

-- volume by month: gaps, spikes, partial last month
SELECT DATE_TRUNC('month', ts) AS month, COUNT(*) AS n
FROM t
GROUP BY 1
ORDER BY 1;
```

## Grain

```sql
-- key is unique when n_rows = n_keys
SELECT COUNT(*) AS n_rows,
       COUNT(DISTINCT key_col) AS n_keys            -- composite: COUNT(DISTINCT k1 || '|' || k2) or a subquery
FROM t;

-- how bad are the repeats (no key values returned)
SELECT copies, COUNT(*) AS n_keys
FROM (SELECT key_col, COUNT(*) AS copies FROM t GROUP BY key_col) g
GROUP BY copies
ORDER BY copies;
```

## One column at a time

```sql
-- any column
SELECT COUNT(*) - COUNT(col)             AS n_null,
       COUNT(DISTINCT col)               AS n_distinct,
       MIN(LENGTH(CAST(col AS VARCHAR))) AS min_len,
       MAX(LENGTH(CAST(col AS VARCHAR))) AS max_len
FROM t;

-- measure
SELECT MIN(col), MAX(col), AVG(col), STDDEV(col),
       PERCENTILE_CONT(0.05) WITHIN GROUP (ORDER BY col) AS p05,
       PERCENTILE_CONT(0.50) WITHIN GROUP (ORDER BY col) AS p50,
       PERCENTILE_CONT(0.95) WITHIN GROUP (ORDER BY col) AS p95,
       SUM(CASE WHEN col = 0 THEN 1 ELSE 0 END) AS n_zero,
       SUM(CASE WHEN col < 0 THEN 1 ELSE 0 END) AS n_negative
FROM t;
-- BigQuery has no PERCENTILE_CONT aggregate: use APPROX_QUANTILES(col, 20)[OFFSET(k)].
-- A measure that is a date of birth or similar personal value is personal: skip it.

-- dimension (never run on a personal column)
SELECT CASE WHEN COUNT(*) < 10 THEN '<10 (merged)' ELSE CAST(col AS VARCHAR) END AS value,
       COUNT(*) AS n
FROM t
GROUP BY col
ORDER BY n DESC;
-- merge the '<10' rows afterwards, or wrap in an outer GROUP BY on value with SUM(n)

-- shape of an identifier or code (not personal): digits -> 9, letters -> A
SELECT REGEXP_REPLACE(REGEXP_REPLACE(col, '[0-9]', '9'), '[A-Za-z]', 'A') AS shape,
       COUNT(*) AS n
FROM t
GROUP BY 1
HAVING COUNT(*) >= 10
ORDER BY n DESC;

-- personal column: format match share only
SELECT AVG(CASE WHEN REGEXP_LIKE(col, '^[^@ ]+@[^@ ]+\.[^@ ]+$') THEN 1.0 ELSE 0 END) AS share_email_like
FROM t;
-- Postgres: col ~ '…'; BigQuery: REGEXP_CONTAINS(col, r'…')

-- hygiene in a text dimension
SELECT SUM(CASE WHEN col <> TRIM(col) THEN 1 ELSE 0 END)   AS n_padded,
       SUM(CASE WHEN col = '' THEN 1 ELSE 0 END)           AS n_empty,
       COUNT(DISTINCT col) - COUNT(DISTINCT LOWER(TRIM(col))) AS n_case_or_space_variants
FROM t;
```

## Joins

```sql
-- match rate and fan-out of a.x -> b.y
WITH b_per_key AS (
  SELECT y, COUNT(*) AS n_b FROM b GROUP BY y
)
SELECT COUNT(*)                                         AS a_rows,
       SUM(CASE WHEN k.y IS NULL THEN 1 ELSE 0 END)     AS a_unmatched,
       MAX(k.n_b)                                       AS max_fanout,
       AVG(COALESCE(k.n_b, 0))                          AS avg_fanout
FROM a
LEFT JOIN b_per_key k ON a.x = k.y;
```

Run it in both directions. A max fan-out above 1 means `COUNT(*)` and `SUM` after the join will be
inflated unless you aggregate `b` to `a`'s grain first.

## Sampling

- Snowflake: `FROM t SAMPLE (1)`; BigQuery: `FROM t TABLESAMPLE SYSTEM (1 PERCENT)`;
  Postgres: `FROM t TABLESAMPLE SYSTEM (1)`; DuckDB: `FROM t USING SAMPLE 1%`.
- A recent partition is often a better sample than a random one for freshness questions.
- Say in the answer that a profile was sampled, and at what rate.
