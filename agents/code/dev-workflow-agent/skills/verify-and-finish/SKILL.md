---
name: verify-and-finish
description: Proves a change works with fresh evidence before any claim of done, fixed or passing — the full suite, build and lint on the final tree, each requirement checked against the request — then tidies the branch into clean, focused commits and offers the owner the integration choices (open a pull request, merge locally, keep the branch, or discard on explicit request). Also sets up or reuses an isolated worktree for the work. Use before claiming a change is complete, before committing or handing over, and when deciding how to integrate a finished branch.
triggers:
  - is it done
  - verify before claiming
  - finish the branch
  - ready to merge
  - open a pull request
  - set up a worktree
  - clean up my commits
---

# Verify and finish

A claim about the code is only as good as the command behind it. "Should pass", "looks right" and
"the agent said it worked" are not evidence.

## The gate before any claim

Before you say done, fixed, passing, or commit, hand over or move on:

1. **Name the command** that would prove the claim.
2. **Run it now**, in full, on the tree you are about to hand over. An earlier run proves only the
   tree it ran on.
3. **Read the output**: exit code, pass and fail counts, skipped and collected counts, warnings.
4. **Say what it shows.** If it confirms the claim, state the claim with the evidence. If not, state
   the real status with the evidence.

| Claim | Needs | Does not count |
| --- | --- | --- |
| Tests pass | The suite's output with zero failures, and the tests you meant actually ran | An earlier run; one file; "should" |
| Build works | The build command exiting 0 | A clean lint |
| Bug fixed | The original reproduction now passing | The code changed |
| Regression test works | Seen failing without the fix and passing with it | It passes |
| Requirements met | Each requirement in the request checked off against the result | Green tests alone |
| Delegated work done | The diff and a run you checked yourself | The delegate's report |

Words like "should", "probably", "seems" or a satisfied "Done!" before a run are the sign to stop and
run it.

## Before you commit

- `git status` and `git diff --staged`: only files this change owns, nothing generated, no build
  output, no `.env`, no stray debug code.
- Scan the staged diff for secrets, tokens, credentials, customer data or PII. Stop if you find any.
- Tests, build and lint (or type check) pass on what you are committing.
- Each commit does one logical thing, refactors apart from behaviour changes, with a message that
  says why. Follow the repository's message convention if it has one.

Details for branches, commit messages, splitting a messy tree and worktrees are in
`references/branch-hygiene.md`.

## Finishing the branch

1. Run the full suite on the final tree. If it fails, report the failures and stop; the choices
   below come only after a green run.
2. Confirm the base branch the work started from. Ask if it is not certain.
3. Write a short change summary: what changed and where, what you deliberately did not touch, and
   any concern the owner should weigh.
4. Offer the owner these choices and wait for one:
   1. push the branch and open a pull request against the base;
   2. merge into the base locally, then run the suite on the merged result;
   3. keep the branch as it is for later.
5. Carry out only the choice made. After a pull request, keep the worktree; review fixes happen
   there. After a local merge, delete the branch and remove the worktree only if you created it and
   the merged result is green.

Discarding work is never on the menu. Do it only when the owner asks in so many words, after listing
exactly what will be lost (branch, commits, worktree path) and getting an explicit confirmation.

In a PenguPool team you do not merge: hand your parent the branch, the commit SHAs, the worktree
path and the evidence, and stop.

## Never

- Push, force-push, merge or delete without the owner's choice.
- `--force` a worktree removal or a push that was refused: the refusal means something would be lost.
- Re-run a command on unchanged code as reassurance, or report a run you did not see.

## Report

Branch and base, commit SHAs, the commands you ran with their results (counts, exit codes), each
requirement against its evidence, anything left open, and the choice the owner made.
