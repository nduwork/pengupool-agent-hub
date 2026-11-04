---
name: explore-data
description: Profiles an unfamiliar table, file or schema before any question is answered from it — size, grain, keys, column roles, null rates, distributions, value shapes, freshness and how tables join — using aggregate-only queries. Use when meeting a new dataset, when a question names tables you have not checked, or when a result looks off and you need to know what the data really holds.
triggers:
  - explore this table
  - profile the data
  - what is in this dataset
  - what's the grain
  - how do these tables join
  - new schema
---

# Explore data

Learn the data before you answer from it. Every query here returns aggregates; you never look at
rows. Detail and dialect-ready SQL: [references/profiling.md](references/profiling.md).

## 1. Find it

- Database: list schemas and tables from the catalog (`information_schema`, `SHOW TABLES`), then
  columns with types and comments. Prefer views or marts the owner names over raw tables.
- File: read it with `duckdb` or pandas, but print only shape, dtypes and aggregates.
- Ask the owner which 3–5 tables matter most and what the key business words mean ("customer",
  "case", "active"). Their answer beats your guess; propose lasting definitions to team memory.

## 2. Size and freshness

- Row count (or catalog estimate on very large tables), table size if the catalog has it.
- Min and max of each date/time column; the last load time if there is one.
- Rows per day/week/month across the range: gaps, spikes and a partial last period show up here.

## 3. Grain and key

Write down "one row per …" and test it: the candidate key's row count must equal its distinct
count. If not, report how many keys repeat and the max repeat count, then find the column that
completes the key (often a version, date or line number). Never list the repeating keys.

## 4. Classify every column

Give each column one role. The role decides what you may report about it.

| Role | Examples | Report |
| --- | --- | --- |
| Identifier | ids, foreign keys | nulls, distinct count, uniqueness, length/shape |
| Personal | names, emails, phones, addresses, DOB, MRN, sample/accession ids, free text | nulls, distinct count, length range, share matching the expected format |
| Dimension | status, type, region | nulls, distinct count, value counts (small cells `<10`) |
| Measure | amounts, durations, scores | nulls, min/max, mean, percentiles, zeros, negatives |
| Time | created/updated dates | nulls, range, future dates, per-period counts |
| Flag | booleans | true/false/null counts |
| Nested | JSON, arrays | null and empty counts, key presence counts |

When unsure whether a column is personal, treat it as personal.

## 5. Profile

Run one aggregate query per table where you can (a `UNION ALL` of per-column summaries, or one
wide row). Look for:

- nulls above ~5% (worth a note) or ~20% (worth a caveat);
- a dimension with thousands of values, or an id with very few;
- placeholder values (`0`, `-1`, `999999`, `N/A`, `unknown`, `test`, `1900-01-01`);
- one value carrying a surprising share (a default leaking in);
- mixed case, stray whitespace, several formats in one column (shape counts reveal these);
- measures with a long tail, where mean and median disagree;
- impossible values: negative durations, end before start, dates in the future.

On huge tables profile a sample (`TABLESAMPLE`, or a recent partition) and say so.

## 6. Relationships

For each likely join (`a.x = b.y`) measure, in counts only:

- match rate in both directions (how many `a` rows find a `b`, and the reverse);
- fan-out: max and average `b` rows per `a` key. Above 1 means a join will multiply rows;
- orphans: keys on one side with no partner.

Note hierarchies (country > region > site) and columns that duplicate or derive from others.

## 7. Write the summary

Keep a short data note for the rest of the task (not a repository file unless the owner asks):

```
<table>  — one row per <grain>, key <cols> (unique: yes/no), <n> rows, <from>–<to>, loaded <when>
Columns: <role groups with counts>
Joins:   <table>.<col> → <table>.<col>  match <x%>, fan-out <max>
Watch:   <quality issues, standard filters such as test/internal rows, timezone>
```

Tell the owner the grain, the joins you will use, the filters you will apply and the issues that
could change an answer, then move on to `write-query`.
