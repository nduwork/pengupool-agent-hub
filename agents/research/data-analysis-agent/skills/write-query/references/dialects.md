# Dialect notes

The functions people get wrong most often, side by side. Check the engine's docs when a cell says
"varies" or the version is old.

## Dates and times

| Need | Postgres / Redshift | Snowflake | BigQuery | Databricks / Spark | DuckDB | SQL Server | MySQL |
| --- | --- | --- | --- | --- | --- | --- | --- |
| Truncate to month | `DATE_TRUNC('month', ts)` | `DATE_TRUNC('month', ts)` | `DATE_TRUNC(d, MONTH)` / `TIMESTAMP_TRUNC(ts, MONTH)` | `DATE_TRUNC('MONTH', ts)` | `DATE_TRUNC('month', ts)` | `DATETRUNC(month, ts)` (2022+) | `DATE_FORMAT(ts, '%Y-%m-01')` |
| Add 7 days | `ts + INTERVAL '7 days'` | `DATEADD(day, 7, ts)` | `DATE_ADD(d, INTERVAL 7 DAY)` | `DATE_ADD(d, 7)` | `ts + INTERVAL 7 DAY` | `DATEADD(day, 7, ts)` | `DATE_ADD(ts, INTERVAL 7 DAY)` |
| Days between | `end::date - start::date` (Redshift: `DATEDIFF(day, s, e)`) | `DATEDIFF(day, s, e)` | `DATE_DIFF(e, s, DAY)` | `DATEDIFF(e, s)` | `DATE_DIFF('day', s, e)` | `DATEDIFF(day, s, e)` | `DATEDIFF(e, s)` |
| Hours between | `EXTRACT(EPOCH FROM e - s) / 3600` | `DATEDIFF(hour, s, e)` (counts boundaries) | `TIMESTAMP_DIFF(e, s, HOUR)` | `(UNIX_TIMESTAMP(e) - UNIX_TIMESTAMP(s)) / 3600` | `DATE_DIFF('hour', s, e)` | `DATEDIFF(hour, s, e)` (boundaries) | `TIMESTAMPDIFF(HOUR, s, e)` |
| Day of week | `EXTRACT(DOW FROM ts)` 0=Sun | `DAYOFWEEK(ts)` 0=Sun by default | `EXTRACT(DAYOFWEEK FROM ts)` 1=Sun | `DAYOFWEEK(ts)` 1=Sun | `DAYOFWEEK(ts)` 0=Sun | `DATEPART(weekday, ts)` depends on `DATEFIRST` | `DAYOFWEEK(ts)` 1=Sun |
| Convert timezone | `ts AT TIME ZONE 'UTC'` | `CONVERT_TIMEZONE('UTC', 'America/New_York', ts)` | `DATETIME(ts, 'America/New_York')` | `FROM_UTC_TIMESTAMP(ts, 'America/New_York')` | `ts AT TIME ZONE 'UTC'` | `ts AT TIME ZONE 'UTC'` | `CONVERT_TZ(ts, '+00:00', 'America/New_York')` |

Boundary-counting `DATEDIFF` (Snowflake, SQL Server) returns 1 hour for 10:59 → 11:01. For true
elapsed time take seconds and divide.

## Strings, nulls, division

| Need | Notes |
| --- | --- |
| Case-insensitive match | `ILIKE` in Postgres, Snowflake, Redshift, DuckDB, Databricks; BigQuery and SQL Server use `LOWER(x) LIKE …` |
| Regex test | Postgres `x ~ 'p'`; Snowflake `REGEXP_LIKE(x, 'p')` (whole-string match); BigQuery `REGEXP_CONTAINS(x, r'p')`; Spark `x RLIKE 'p'`; DuckDB `REGEXP_MATCHES(x, 'p')` |
| Safe divide | `x / NULLIF(y, 0)` everywhere; BigQuery also `SAFE_DIVIDE(x, y)`; Snowflake `DIV0NULL(x, y)` |
| Integer division | Postgres, Redshift, SQL Server and older DuckDB truncate `int / int`; multiply by `1.0` first |
| Concatenate with nulls | `||` returns null if any part is null (not in MySQL, where `||` is OR); `CONCAT` skips nulls in most engines |
| String aggregate | Postgres `STRING_AGG`; Snowflake/Redshift `LISTAGG`; BigQuery `STRING_AGG`; Spark `ARRAY_JOIN(COLLECT_LIST(x), ',')` — never aggregate personal values this way |

## Quantiles and approximations

- Exact median: `PERCENTILE_CONT(0.5) WITHIN GROUP (ORDER BY x)` (Postgres, Snowflake, Redshift,
  DuckDB, SQL Server as a window); `MEDIAN(x)` in Snowflake, Redshift, DuckDB, Databricks.
- BigQuery: `APPROX_QUANTILES(x, 100)[OFFSET(50)]`; Spark: `PERCENTILE_APPROX(x, 0.5)`.
- Distinct counts: `APPROX_COUNT_DISTINCT` (Snowflake, BigQuery, Spark, DuckDB, Redshift via
  `APPROXIMATE COUNT(DISTINCT x)`) for exploration; exact for reported answers.

## Semi-structured data

- Snowflake: `v:field::STRING`, `LATERAL FLATTEN(input => v:items)`.
- BigQuery: `JSON_VALUE(j, '$.field')`, `UNNEST(array_col)`.
- Postgres: `j->>'field'`, `jsonb_array_elements(j->'items')`.
- Databricks: `j:field`, `EXPLODE(array_col)`; DuckDB: `j->>'$.field'`, `UNNEST(list_col)`.

Flattening multiplies rows: count the parent key with `COUNT(DISTINCT)` afterwards.

## Cost and plans

| Engine | Look at the plan | Keep it cheap |
| --- | --- | --- |
| Postgres | `EXPLAIN` (`ANALYZE` executes the query) | filter on indexed columns; `EXISTS` over large `IN` lists |
| Snowflake | `EXPLAIN`, query profile | filter on clustering columns; reuse a result with `RESULT_SCAN(LAST_QUERY_ID())` |
| BigQuery | dry run (bytes billed) | filter on partition column; select only needed columns, billing is per column scanned |
| Redshift | `EXPLAIN` | filter on sort key; join on dist key; watch for broadcast steps |
| Databricks | `EXPLAIN` | filter on partition columns; Z-ordered columns prune files |
| DuckDB | `EXPLAIN` / `EXPLAIN ANALYZE` | read Parquet with column and row-group pruning; avoid CSV re-scans |
