---
name: decision-records
description: Write short architecture decision records (ADRs) next to the code. Use when a design choice is costly to reverse (API style, versioning scheme, data store, service split, auth model, a breaking change), when superseding an earlier decision, or when someone asks why the system is built a certain way.
triggers:
  - write an ADR
  - decision record
  - architecture decision
  - record this decision
  - supersede ADR
  - why did we choose
---

# Decision records

An ADR explains why a choice was made, what else was considered and what it costs. Code shows
what was built; the ADR keeps the reasons from being lost or re-argued.

## Does it need an ADR?

Write one when the choice is expensive to undo or will puzzle a newcomer:

- an interface style, versioning scheme, error model or auth model;
- a data store, schema shape or ownership boundary;
- splitting or merging services, adding a queue or an event stream;
- a breaking change and its migration plan;
- a deliberate deviation from the repo's usual convention.

Skip it for choices one PR can reverse cheaply; put the reason in the PR description.

## Follow the repo first

Before writing, look for existing ADRs (`docs/adr/`, `docs/decisions/`, `adr/`,
`doc/architecture/decisions/`, an `.adr-dir` file) and any project instructions about them.
Match their folder, file naming, numbering, markup and headings. Continue the existing number
sequence; never start a second scheme. If you find two conflicting conventions, say so and ask.
Only with no convention at all use the default below.

## Default format

Path: `docs/adr/NNNN-short-title.md` (four-digit number, kebab-case title). Keep it to about one
page.

```markdown
# NNNN. <Decision in a short active phrase>

Status: Proposed | Accepted | Superseded by NNNN | Deprecated
Date: YYYY-MM-DD

## Context
The problem and the forces: what must be true, what limits apply, what we know and what we are
guessing. Facts with their source; no solution yet.

## Options
- **A — <name>**: what it is; what it buys; what it costs.
- **B — <name>**: …
- **Do nothing** when that is a real option.

## Decision
The chosen option in one or two sentences, and the main reason it beat the others.

## Consequences
What gets easier, what gets harder, new work it creates, risks accepted, and what would make us
revisit it.
```

## Lifecycle

- A new ADR starts as **Proposed**. The owner (or the team's agreed reviewer) moves it to
  **Accepted**; you do not accept your own.
- An accepted ADR is not edited for substance. To change course, write a new ADR that says
  "Supersedes NNNN", and change only the old one's status line to "Superseded by MMMM".
- A decision that simply stopped applying becomes **Deprecated** with one line saying why.
- Never delete an ADR; the history is the point.

## Writing well

- Lead with the decision's subject in the title ("Use cursor pagination for all list
  endpoints"), not "Pagination".
- Keep facts exact: names, numbers, limits and caveats survive editing. Mark guesses as guesses.
- Cut filler and sales language; a reader should finish in two minutes.
- Link the ADR from the contract or code it governs, and link the contract from the ADR.
- No secrets, credentials, customer data or personal details in an ADR.

## Output

The ADR file at the repo's ADR path, status Proposed, plus one line to your parent or the owner
naming the file and the decision it asks them to accept.
