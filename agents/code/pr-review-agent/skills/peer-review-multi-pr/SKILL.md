---
name: peer-review-multi-pr
description: Use when several PRs are open at once and may touch the same files or state. Trial-merge them together in a temporary worktree and report conflicts and interactions.
---

# Several open PRs

Called from `peer-review`. Review each PR on its own first.

1. In a temporary worktree (or with `git merge-tree`), merge the PR heads onto the base in the order
   the owner expects to land them. Never on a shared branch, never push.
2. Report textual conflicts, and interactions that merge cleanly but break: two PRs writing the same
   state, one renaming what the other reads, a migration order.
3. Run the repo's documented checks on the merged result when they are safe to run, and report them
   separately from each PR's own findings.
4. Delete the worktree.
