---
name: review-loop
description: Use when the team's change is about to go to a human reviewer, a reviewer has left comments, or the owner's ruling has to reach the code. Distils a reviewer's recurring asks from their past reviews into a checklist, has members run it before asking for review, keeps decision history and assistant-sounding wording out of code, checks the diff stays inside its fence, and drives each comment to a verified fix, a short reply and a resolved thread.
triggers:
  - ready for review
  - request review
  - review comments
  - address comments
  - reviewer
  - changes requested
  - reply and resolve
  - before push
---

# Review loop — get a change through a human reviewer

A human reviewer's "changes requested" blocks the merge whatever an automated score says, and most
reviewers ask for the same things every time. Learn those things once and check them before the
reviewer has to.

## Learn the reviewer

When a reviewer has several past reviews in the repository, ask a member or sub-agent to read them
and distil the recurring asks into a short numbered checklist, each with one example. Asks that come
up often:

- cut comments that restate the code; keep only a non-obvious why, in plain sentences;
- plain domain words in names and prose; no inflated or assistant-sounding words;
- reuse the generated client, types, cache and helpers the repository already has;
- magic strings become enums, and behaviour of an enum lives on the enum;
- tests check business logic at the right level, not that code is as written;
- link records by id, not by timestamp;
- argue with data, and do not guard near-impossible cases;
- no claim in the PR text that was not verified;
- the change survives a page refresh and a deep link.

Send the checklist with the assignment, and ask the member to run it as an adversarial pass on its
own diff before it asks for review.

## Rulings reach the code as behaviour

When you pass the owner's decision to a member, tell it what the code must do, not who decided it.
Code, comments, docstrings, test names and log text describe behaviour in domain terms. They never
mention the conversation: no names, "per the ruling", "pending X's value", option letters, session,
agent or tool names, or request ids. Decision history goes in the PR description or the ticket, and
stays factual there.

## Word sweeps cover the family

When a reviewer flags a word, the fix is a plain domain phrase, not a synonym from the same family.
Ask the member to grep the added lines of the diff (`git diff <base>...HEAD`) for the whole family
(for example watermark, cursor, grain, rail, seam, canonical, invariant, load-bearing) and replace
each.

## Stay inside the fence

When the owner fences off a module ("do not touch X"), give the member a check it can run before
every push, such as `git diff --name-only <base>...HEAD | grep -iE '<fenced paths>'` returning
nothing. Run it on the branch's own diff, not on what the base branch brings in. A need that seems to
cross the fence goes to the owner.

## Comments to resolved threads

For each review comment:

1. Verify it (skill `ground-truth`). A suggestion can be wrong; check it against the code and the
   data before acting.
2. The member fixes what holds, and the fix is verified (test, query aggregate, screenshot).
3. The member replies in one plain sentence: what changed and the commit, or, for a question, the evidence at
   file:line. No preamble, lists or thanks.
4. The member resolves the thread once the reply is posted.
5. When all are done and the repository uses an automated reviewer, ask it to review again with
   that repository's own trigger comment.

Posting a reply, resolving a thread and pushing are outward actions: they wait for the owner's
go-ahead unless the owner already gave it for this PR.

## Report

Per PR: comments fixed (commit), answered (evidence), pushed back (evidence), and still open.
