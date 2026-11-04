# Branches, commits and worktrees

## Branches

- Branch from the repository's default branch (or the base the owner names). Keep branches short-lived;
  integrate within days, not weeks.
- Use the repository's naming convention. Without one: `feat/<short-name>`, `fix/<short-name>`,
  `refactor/<short-name>`, `chore/<short-name>`.
- Prefer a feature flag that defaults off over a long-lived branch when unfinished work must land.

## Commits

- One logical change per commit: a slice, a fix with its test, a simplification. Formatting,
  refactoring and behaviour changes go in separate commits.
- Message: `<type>: <what, in a few words>` then, after a blank line, why. Types: feat, fix,
  refactor, test, docs, chore, unless the repository uses another scheme.
- Aim for commits a reviewer can read in one sitting, around a hundred lines; split anything near a
  thousand.
- Commit generated files only when the project expects them (lockfiles, migrations). Never commit
  build output, environment files, local editor settings or credentials.

### Splitting a messy working tree

1. `git status` and `git diff` to list what changed and why.
2. Group the hunks by purpose.
3. Stage one group at a time with `git add <paths>` or `git add -p` where your agent allows
   interactive staging; otherwise stage whole files, or write a temporary patch with
   `git diff <file> > <scratch>/part.patch`, edit it, and `git apply --cached <scratch>/part.patch`.
4. Run the tests on each commit's content when the groups depend on each other.

### Undoing safely

- Undo an uncommitted edit: `git restore <path>`.
- Undo the last local commit and keep the changes: `git reset --soft HEAD~1`.
- Undo a pushed commit: `git revert <sha>`; never rewrite shared history.
- Before anything that discards work, list what would be lost and get the owner's yes.

## Worktrees

A worktree gives the change its own directory and branch so it cannot disturb other work.

1. **Check first.** If `git rev-parse --git-dir` and `git rev-parse --git-common-dir` resolve to
   different paths (and `git rev-parse --show-superproject-working-tree` prints nothing, so it is
   not a submodule), you are already in a worktree: use it.
2. **Use your agent's own worktree command** if it has one; it tracks and cleans up what it creates.
3. **Otherwise** create one with git, in the place the owner or the repository prefers, defaulting
   to `.worktrees/` at the repository root. Confirm the directory is ignored
   (`git check-ignore -q .worktrees`) before you create it there; if it is not ignored, ask before
   changing `.gitignore`.

   ```bash
   git worktree add .worktrees/<branch> -b <branch>
   ```
4. **Set up and take a baseline.** Install dependencies the way the repository says, then run the
   suite. If the baseline already fails, report it and ask before building on it: later failures
   are otherwise ambiguous.
5. **Clean up only what you made.** Remove a worktree you created after its branch is merged or
   discarded (`git worktree remove <path>`, then `git worktree prune`). Leave worktrees your agent
   or another session made. If removal is refused because of uncommitted files, show them to the
   owner and ask whether to commit, move or delete them.

The stash is shared by every worktree of a repository. Prefer a temporary work-in-progress commit;
if you must stash, give it a unique message and apply it by its SHA rather than popping the top.

## Integration choices in detail

| Choice | Push | Merge | Keep worktree | Delete branch |
| --- | --- | --- | --- | --- |
| Pull request | yes | no | yes, for review fixes | no |
| Merge locally | no | yes, then test the merged result | no, if you created it | yes, after a green merged run |
| Keep as is | no | no | yes | no |
| Discard (only on explicit request) | no | no | no | yes, after confirmation |

For a pull request, use the forge's CLI if available (for example `gh pr create`) or the creation
URL the push prints, follow the repository's template, and give the owner the URL. If a push is
rejected, the remote moved: fetch, look, and ask; do not force-push.
