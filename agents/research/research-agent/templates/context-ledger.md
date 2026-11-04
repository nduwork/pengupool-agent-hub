# Context ledger — <requester session> · <subject>

Working state for the current request, held in the session, never written into this folder or a
repository; not owner memory. Append-only for
**shareable (public-source)** entries: on refresh, write a new dated row rather than editing an old one,
so drift is visible. **`requester-private` entries are NOT append-only and NOT retained** — they never
enter another requester's ledger and are discarded at task end (or held only in a requester-authorized
store; see gate G6). A file in the shared checkout is not a boundary. See
`../skills/research-agent/references/context-continuity.md`.

- **Requester**: <session name / id> · **request_id**: <id> · **reply path**: <path>
- **Opened**: <YYYY-MM-DD> · **Last refresh**: <YYYY-MM-DD> · **Decision**: reuse | partial | full

## L1 — relationship (bound to the session; refresh on session change / re-parent)

| Item | Source (repo/file) | Observed | Visibility | Notes |
| --- | --- | --- | --- | --- |
| e.g. repo = `<project>`; platform = `<ios|web>`; licence posture = `<commercial|non-commercial>` | `<repo>/docs/...` | 2026-09-28 | shared | re-confirm on re-parent |

## L2 — knowledge (bound to the subject; refresh on subject/version change, expiry, contradiction)

| Finding | Source (url/command) | Access scope | Revision | Observed | Volatility | Scope / deps | Confidence |
| --- | --- | --- | --- | --- | --- | --- | --- |
| e.g. `<dataset X>` is `<licence>` | `<url>` | public | `<rev>` | 2026-09-28 | slow | licence of `<dataset X>` | High |

**Access scope**: `public` (sourceable by anyone) or `requester-private` (derived from the requester's
repo/secrets/unpublished material). **Unknown ⇒ `requester-private`** — never carry it into another
session, and never propose it as a memory.

## L3 — task scratch (always drop; never carried to another session or subject)

- <hypotheses, dead ends, raw search hits>

## Decision log (journal for replay/calibration)

| Date | Trigger (session chg / subject chg) | Features | Outcome | Reason |
| --- | --- | --- | --- | --- |
| 2026-09-28 | subject chg (`<topic A>` → `<topic B>`) | overlap=entity | partial | kept facts, rebuilt question |
