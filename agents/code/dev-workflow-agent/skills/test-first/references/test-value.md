# Test value: add, keep, merge or retire

The aim is protection in proportion to risk, not a test count or a coverage number. When the same
agent writes the code and its tests, check that both do not rest on the same wrong assumption: the
expected value must come from the request, a public contract or a real failure, not from what the
new code happens to output.

## Decisions

| What you find | Do |
| --- | --- |
| A failure worth catching that nothing covers | Add one test at the cheapest layer that shows it; keep one real integration path where layers meet |
| An existing test would already fail for this mistake | Extend it rather than adding a parallel one |
| A test freezes output the contract does not promise (layout, ordering, wording, internal calls) | Assert the properties that matter, with justified tolerances |
| Several tests catch the same mistake through the same path | Keep one; name the survivor in the report |
| The same rule table is tested through every entry point | Test the rules once in shared logic, then one integration check per entry point |
| A slow test guards a risk nothing else covers | Keep it; make its fixture cheaper or run it where risk demands |
| The behaviour it protects was removed on purpose | Retire it after checking nothing else still depends on it |
| Unclear who relies on it or what it should expect | Keep it and say which fact is missing |

Never trade away protection against data loss or corruption, permission and trust-boundary failures,
promised compatibility, accessibility basics, leaks or broken recovery to make a suite faster or
greener. Skips, retries, wider tolerances and refreshed snapshots must not hide a regression.

## Proving a test discriminates

- **Regression test:** with the fix reverted, it fails; with the fix, it passes. Do the revert in
  your working tree and restore it, or reason from the red run you saw before the fix.
- **Relaxed assertion:** a valid alternative result passes; the original bad result still fails.
- **Merged or deleted test:** trace the call paths and show a surviving test fails for the same
  mistake. Similar names or shared helpers are not proof.
- **Shared fixtures:** reset mutable state; results must not depend on test order.

## When a test fails

Name what the test protects, then decide which it is:

- a real regression in the product: fix the code (`root-cause-debugging`);
- an assertion that the approved change made obsolete: update it, and say so;
- the environment (missing service, tool version): report it as a gap, not a pass;
- an unstable test (timing, order, shared state): fix the instability, do not retry it into green.

## Running the right amount

Pick the smallest set of checks that covers what the change touches during the loop; run the full
suite before you call it done. A green exit with zero relevant tests collected is not evidence.
Re-running the same command on unchanged code adds nothing. Claim a speed-up only from comparable
measurements.
