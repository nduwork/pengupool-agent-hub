---
name: peer-review-rereview
description: Use when a PR you already reviewed has new commits. Delta-only re-review since the last reviewed head, never repeating old findings, capped at 3 rounds.
---

# Re-review

Called from `peer-review`. Same read-only rules.

1. Take the last reviewed head from your previous report; pin the new head.
2. Read the delta only through the filter: `python3 ../../scripts/preflight.py prepare <pr> --since <old>`
   (the same secret and personal-data filter as `prepare`). Never run a raw `git diff` or `gh pr diff`.
   Review only that delta plus the behaviour the fix affects (trace the readers of any
   state the fix touches, as in `peer-review` step 2).
3. Never repeat an old finding. Say which were fixed and which remain; a fix that did not hold is a
   new finding against the new head.
4. Report in the usual format with `round <n>`. After round 3, hand what remains to the owner
   instead of reviewing again.
