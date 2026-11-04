---
name: research-library
description: Mark reusable research findings so PenguPool's record keeps them. Use when a finding, repo, tool, dataset or idea looks reusable beyond the task at hand, when the owner says a result is interesting or useful, or after a research task yields something generalizable. Searches the record first, filters candidates, and marks each in the report, where the host records it; never marks the same finding twice and never marks requester-private material.
triggers:
  - save this
  - add to the library
  - reusable
  - reusable findings
  - keep this finding
  - that was useful
  - keep for later
  - library
  - reuse across projects
  - interesting finding
---

# Research library — reusable findings in PenguPool's record

A reusable finding is kept as a **`Reusable finding:` line in your report**. PenguPool records the
turn by itself, and `pengupool search` finds the line later. Nothing is written into this folder or any repository.

`pengupool` is the absolute CLI path your session context prints.

## When to run this

- The owner says a result, repo, dataset, tool or idea is **interesting / useful / reusable**, or hands
  you a repo or idea to research.
- **At the end of a research task**, alongside the owner-memory check, if the report holds something
  generalizable.

## What qualifies (candidate filter)

Offer a finding only when **all** hold:

1. **Shareable** — its access scope, the most restrictive of all its inputs (request, requester
   context, sources, conclusion), is `public`. A requester-private finding is never marked
   (`research-agent/references/context-continuity.md`, gates G5/G6); deliver it and keep no copy.
2. **Generalizable** — it would change how a *different* project is done, not just this one.
3. **Durable** — still true in months (a licence, an algorithm, a source landscape), not a fast-moving
   value (a price, a latest version, live status).
4. **Non-obvious** — it took real digging; it has a source and a confidence.
5. **Not already held** — `pengupool search` finds nothing that says the same.

If none qualify, stay silent: a prompt every task trains the owner to dismiss it.

## The ritual

1. **Gather** candidates as you go.
2. **Search first.** For each, `pengupool search "<key words>"` and compare by meaning. If the
   finding is already there, do not mark it again unless it materially changed (new evidence, a new
   version).
3. **Mark** each survivor in the report, one line per finding:

   ```text
   Reusable finding: <short title> — <the finding, in one line> (<source URL or path + access date>; confidence High|Medium|Low)
   ```

   Keep the line self-contained (what, where it applies, confidence); keep the requester, request id
   and anything private out of it.

## Reuse (read side)

At the **start** of a task, `pengupool search` for the subject and read the matching findings. Cite what you reuse as *(prior finding — source,
date, confidence)* and re-verify it if it can have changed. Never present a prior finding as freshly
verified. If one turns out wrong, mark a corrected finding that says what it supersedes; do not
silently work around it.

## Boundaries

| Holds | Where | Who adds |
| --- | --- | --- |
| Reusable findings | `Reusable finding:` lines in PenguPool's record | you mark them, the host records them |
| The owner's preferences and restrictions | the owner's Compass | PenguPool's triage proposes from the owner's words, the owner approves |
| Every turn and message | PenguPool's record | the host, by itself |
