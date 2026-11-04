---
name: worktree-cleanup
description: Surveys git worktrees and removes only the provably merged, idle ones. It classifies each branch by ancestry or by a MERGED pull request whose head commit is the local tip, keeps worktrees that are dirty, locked, stashed or have a live session inside, lists unmerged branches for the owner to approve, and prints tip commits so any removal can be undone. Use when worktrees or local branches have piled up, or before deleting branches.
triggers:
  - clean up worktrees
  - delete merged branches
  - remove worktree
  - branch cleanup
  - stale branches
---

# Worktree cleanup

Remove what is provably merged; list the rest for the owner. Deleting a branch is cheap to undo
only while the reflog keeps its tip, so print the tips and never force.

The script is `scripts/worktree_cleanup.sh` next to this skill's parent folder. Run it from the
repository you are tidying.

## 1. Dry run

```sh
agents/operations/worktree-cleanup-agent/scripts/worktree_cleanup.sh
```

The default is a dry run. It prints one row per worktree:

| Column | Meaning |
| --- | --- |
| PATH | worktree directory |
| BRANCH | checked-out branch, or empty when detached |
| TIP | commit the worktree is at (keep it: this is the restore point) |
| BEH/AHD | commits the reference branch has that the branch lacks, and the reverse |
| CLASS | `auto-remove`, `ask-owner`, `keep` or `never` |
| EVIDENCE | why: ancestor of the reference, pull request number and state with its head commit, or "unmerged, N ahead" |
| GUARDS | `dirty`, `locked`, `stash`, `live-session`, `in-progress`: a bisect, rebase, merge, cherry-pick or revert is unfinished, or empty |
| ACTION | what `--apply` will do |

The reference branch is the one checked out in the main worktree, or `--ref <branch>`.

## 2. Check the evidence

- **auto-remove, ancestor** — the tip is reachable from the reference branch. The work is in main.
- **auto-remove, pull request MERGED** — the forge says the pull request merged and the local tip
  equals its head commit, so no commit landed after the merge. Say this in the evidence column
  when you report: it is the owner's rule that a merged pull request counts as merged.
- **ask-owner, "pull request MERGED but tip differs"** — work exists after the merge. Do not
  remove; list it.
- **ask-owner, "unmerged, N ahead"** — real unmerged work, including a branch that is behind the
  reference branch. List it and ask.
- **detached HEAD** — counted against the worktree's HEAD commit, not a branch name. It is
  auto-removable only when its commit is an ancestor of the reference or another local or remote
  branch holds it (the evidence names the branch); a commit no branch holds is asked.
- **keep** — a guard tripped. Never override a guard by hand; the row reappears when it clears.
- **never** — the main worktree or a branch equal to the reference.
- **prunable** — the directory is gone. The entry is pruned either way; the branch is classified
  like any other, so an unmerged branch on it is still asked, not deleted.

## 3. Apply only the safe rows

After the owner agrees with the table:

```sh
agents/operations/worktree-cleanup-agent/scripts/worktree_cleanup.sh --apply
```

`--apply` touches only `auto-remove` rows: it removes the worktree without forcing, deletes the
branch with `-d` (or `-D` only with the MERGED pull request proof), and prunes stale entries.
Nothing on an `ask-owner` or `keep` row is touched.

## 4. Report

Give the owner the table, the reference branch, the tip commit of every removed branch, and the
`ask-owner` rows with their evidence. A removed branch is restored with `git branch <name> <tip>`.

## Limits

- Merged detection uses ancestry and the forge's pull request state. A branch landed by a
  rebase or a multi-commit squash without a merged pull request shows as unmerged: it is asked,
  not removed. That is the safe direction.
- The live-session guard reads the working directories of running processes; a session that has
  not yet changed into the worktree, or runs on another machine, is not detected. Say so when the
  table comes from a machine other than the one running the sessions.
- `--ref` defaults to the main worktree's branch; pass the real trunk branch when the checkout
  there is something else.
