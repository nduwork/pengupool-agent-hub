# Common bottlenecks and how to confirm them

Start from the symptom, measure the layer it points at, and only then pick a fix.

## Where to look first

| What feels slow | Measure first |
| --- | --- |
| first page load | bundle size, server time to first byte, render-blocking files in the network waterfall |
| a click or keystroke | main-thread long tasks (over ~50 ms) in a browser trace, re-render counts |
| a page after navigation | API timings and request waterfalls, client render time |
| one API endpoint | its trace and the query log for that request |
| every endpoint at once | connection pool wait time, CPU, memory, a shared dependency |
| slow now and then | lock waits, garbage-collection pauses, an outside dependency's latency |

## Backend and database

- **One query per row (N+1).** Signature: query count grows with list length. Load the related
  rows in the same query or one batched query.
- **Unbounded reads.** A list endpoint with no limit. Paginate with a limit and a stable order.
- **Query not using an index.** Read the plan (`EXPLAIN ANALYZE` or the engine's equivalent)
  before and after. A full scan where an index was expected, a row estimate far from the real
  count (stale statistics: refresh them before adding anything), or a sort above the scan each
  need a different fix. Index for the query's shape: equality columns first, then range or
  sort. A plain index will not help a leading wildcard, a function on the column, or a value
  that matches most rows. Every index slows writes; an index that did not change the plan is
  removed. Creating an index on a live database is a production change for the owner.
- **Connection pool exhaustion.** Signature: everything slows at once, time is spent waiting for
  a connection, the database shows idle sessions. Find what holds connections (long
  transactions, a connection held across an outside call). Keep `instances × pool size` under
  the database's limit; with autoscaling, put a pooler in front instead of raising the size.
- **Missing or wrong cache.** Cache only what is expensive and read far more often than it
  changes. Every input that changes the answer is in the key (tenant, user permissions, locale,
  flags), or one user sees another's data. State the staleness window and the invalidation
  rule. Stop a hot key's expiry from stampeding the backend (serve stale while one request
  refreshes). Never cache what must be exact now: balances, permissions, stock at checkout.
- **Memory growth.** Compare two heap snapshots; look for caches with no bound and references
  kept after a request ends.
- **CPU spikes.** CPU profile; look for heavy synchronous work on the request path and
  pathological regular expressions.

## Frontend

- **Large layout shift.** Images and embeds without width and height, late content pushing the
  page, font swaps.
- **Slow largest paint.** An oversized hero image (serve modern formats, responsive sizes, high
  fetch priority), render-blocking CSS or scripts, slow server response.
- **Sluggish interaction.** Long tasks on the main thread, large DOM updates, objects or
  callbacks created during render that re-render every child. Memoize only what the profile
  shows is expensive.
- **Big bundle.** Split by route and lazy-load heavy, rarely used features. Check the bundle
  report before changing import styles.

Common web targets at the 75th percentile of real users: largest paint ≤ 2.5 s, interaction
delay ≤ 200 ms, layout shift ≤ 0.1. Use the project's own budgets when it has them.
