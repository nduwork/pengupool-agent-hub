---
name: ground-truth
description: Use before you relay, decide on or report a claim the team's work turns on - a member says "the code does X", a reviewer or an automated review asserts a fact, a design question turns on how data or a model behaves, or an old note is about to drive a plan. Checks the claim against sources in a fixed order (requirements and decisions, then merged code and real data, then drafts as proposals only), settles routine choices from existing precedent instead of asking, and says plainly what is verified and what is not.
triggers:
  - is that true
  - double check
  - verify
  - the code says
  - reviewer says
  - fact-check
  - source of truth
  - questions for the reviewer
  - TBD
---

# Ground truth — check a claim before it moves the team

A wrong fact relayed by the LEAD reaches every member. Check the claims the work turns on before
you pass them along, and say which ones you checked.

## The order of sources

Ground each claim in the first source that can settle it:

1. **Requirements and decisions.** The ticket, the product brief, the team's recorded decisions
   (`pengupool search "<words>"`) and the owner's latest word. The latest word wins.
2. **Merged code and real data.** The default branch, not a feature branch. For behaviour, read the
   code on the default branch. For counts, shapes, formats and how often a case happens, ask a member
   who can query the data for an aggregate.
3. **Drafts.** An open branch or PR, including one the owner wrote, is a proposal. Quote it as
   "draft, not decided". Never use a draft to answer a design question about itself: that feeds the
   proposal back to its author as if it were a decision.

When two sources disagree, report both with their evidence; do not pick one silently.

## Check against data, in aggregate

- Ask for counts, percentages and join match rates, never rows. A member with data access runs the
  query; only aggregates come back to you.
- An edge case that hits 3 of 3.5 million rows does not need a guard. An edge case that is real
  needs a structural fix, not a guard. Let the count decide which.
- A metric that looks too good is a leak until shown otherwise: check whether any input is only
  known after the outcome, and whether the time axis is the event's own date or a later one.
- When a check reverses what you said earlier, say so in one line and give the new number. Do not
  quietly swap it.

## Re-check what the record remembers

A note is true as of when it was written. Before a note drives a plan, check it still holds: a file
moved, a table was dropped, a module was split, a ticket was closed. A quick landing check (does the
path, table, endpoint or flag still exist on the default branch?) is enough. Report what moved.

## Precedent before questions

Before you or a member puts a list of questions to the owner or a reviewer:

1. For each choice, look for how a sibling module, app or earlier PR already did it.
2. Where precedent settles it, write "Decision: matches <where>" and move on.
3. Leave under "Open" only the real judgement calls, each with its evidence.

A long question list moves easy work onto the reader.

## What is not a gap

- A requirement marked "TBD" (an owner, an approver, a value): use the given or nearest placeholder
  and move on. Flag only work that contradicts a stated requirement.
- A reviewer's suggestion is a claim like any other. Verify it before the team acts on it, and
  reply with the evidence either way.

## Report it

For each claim the work turned on, one line:

```text
verified:   <claim> (<source: file:line, ticket, query aggregate>)
unverified: <claim> (<why not, who could check>)
draft:      <claim> (<branch/PR>, not decided)
```

Never present an unverified claim as fact, in a report, a PR description or a message.
