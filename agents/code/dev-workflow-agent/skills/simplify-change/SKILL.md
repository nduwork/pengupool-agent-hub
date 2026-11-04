---
name: simplify-change
description: Reduces a working, tested change to the fewest concepts it needs without changing what it does — removes speculative options, one-use abstractions, dead code and duplication, reuses helpers that already exist, flattens nesting and fixes misleading names — one step at a time with the tests green after each. Use after a change passes its tests and before finishing it, or when asked to simplify code the current change touched.
triggers:
  - simplify this
  - clean up the change
  - this is over-engineered
  - reduce complexity
  - make it smaller
  - before I commit, tidy it
---

# Simplify the change

Simpler means fewer things a reader must hold in their head, not fewer lines. A five-line `if`
that reads at a glance beats a one-line expression that needs a pause. Behaviour stays exactly the
same: same outputs, errors, side effects and order.

## Scope

Simplify what this change added or modified. Code outside the diff is out of scope unless the owner
asks; note it instead. Do not simplify code you do not yet understand, code about to be replaced, or
a hot path where the simpler form would be measurably slower.

## 1. Understand before you cut

For each thing you want to remove or reshape, answer:

- What is it for, who calls it, and what does it call? Search for every caller, including dynamic
  ones (registries, reflection, config, string lookups, other repositories or clients).
- Which edge cases and error paths does it handle? Which tests define its behaviour?
- Why is it written this way? Check `git log -p` or blame for the reason. If the reason still holds,
  leave it.

Never "simplify away" input validation at a trust boundary, authorization, error handling that
prevents data loss, cleanup of resources, compatibility with stored data or a published interface,
or accessibility basics. Changing those is a separate, explicitly agreed change.

## 2. Look for these

| Pattern | Simpler form |
| --- | --- |
| An option, flag or parameter nothing passes | Remove it |
| An interface, base class or factory with one implementation | Use the implementation directly |
| A wrapper that only forwards | Call the target |
| Code that re-implements a helper already in the repo, or the standard library | Use the existing one |
| The same block in three or more places | One named function |
| Deep nesting | Early returns and guard clauses |
| Chained ternaries | `if`/`else` or a lookup table |
| Boolean arguments at call sites (`f(true, false)`) | Named options or two functions |
| Unused variables, imports, unreachable branches, commented-out code | Delete |
| A name that hides what it does (`get` that also writes) | Rename to what it does |
| A comment that repeats the code | Delete; keep comments that say *why* |

Two similar blocks are often fine; do not invent an abstraction to remove them. Keep a helper whose
name explains a concept, even if it is short. Do not merge unrelated functions into one.

## 3. One step at a time

For each simplification: make it, run the tests, keep it if green, undo it if not. Never batch
several untested simplifications. Existing tests must pass **unchanged**; if you had to edit a test
to pass, you probably changed behaviour, so undo and look again. Follow the repository's own style,
even where you would choose differently.

Commit simplifications separately from the behaviour change when the history is kept, so each can
be reviewed and reverted on its own.

## 4. Step back

Read the whole diff again. Is it easier to follow than before? Did you introduce a pattern the
codebase does not use? Is anything left behind (unused import, orphaned test helper, stale doc)?
If a step made things harder to read, revert it. Ending with "nothing worth removing" is a valid
result; say so.

## Report

What you removed or merged and why each was safe (who called it, what proves the behaviour held),
anything you deliberately kept and the reason, out-of-scope candidates you noticed but did not
touch, and the test run after the last step.
