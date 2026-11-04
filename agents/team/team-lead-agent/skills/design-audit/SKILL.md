---
name: design-audit
description: Use before the team presents or hands off a design, mock, spec or built screen - and when a new feature has a shipped sibling it should match. Audits every displayed field, label, status, verb and id against what already ships, compares built screens to the design side by side as images, folds in the owner's free-text notes, defaults the new feature to its shipped sibling's behaviour and flags every divergence with its reason, and keeps first versions small.
triggers:
  - audit the design
  - does it match
  - check against existing
  - mirror
  - sibling feature
  - mock
  - before the demo
  - compare screenshots
---

# Design audit — check a design against what already ships

A design that reads well can still disagree with the product around it. Check it against the code
that ships, and against the screens it claims to describe, before anyone outside the team sees it.

## Default to the shipped sibling

When a new feature has a shipped sibling (the same users, the same shape of work):

1. Start from how the sibling does it: states, tabs, counts, labels, verbs, ids, routes, audit
   trail, permissions.
2. Diverge only when the new feature's data or rules force it (for example one-to-many where the
   sibling is one-to-one).
3. Name every divergence and its reason in the report. Never diverge silently.

Reuse the sibling by importing or copying its patterns. When the owner has fenced the sibling off,
no member edits it, not even a backward-compatible option; a need that seems to require it goes to
the owner.

## Audit every item, not its face meaning

List every item the design shows and check each against the default branch: models, enums and
schemas on the backend, and the existing screens on the frontend. Check:

- ids and what each one really holds (two systems often use one word for different ids);
- column and tab titles, status names, verbs on buttons, task states;
- date and deadline formats, channels, levels, team names.

A field called "accession" or "status" can mean a different thing in each system. Read the code that
fills it. When two repositories are involved, ask a sub-agent (or a member) per repository to do
the read-only check, then spot-check their key claims yourself.

Record the result as a table the owner can scan:

```text
item | design says | shipped code says (file:line) | match / fix / divergence (reason)
```

## Compare images, not descriptions

A text audit misses layout. When a built screen is supposed to match a design:

1. Capture the design's reference images.
2. Ask the member who built it for matching screenshots of the built screens.
3. Look at both side by side before you report "matches".
4. Add the owner's free-text review notes to the checklist; requirements hide there ("sortable by
   date").
5. Re-check your own edits to the design against what the owner said they wanted.

## Keep the first version small

- Answer the request with the smallest change. No extra toggles, variants or panels unless asked;
  each one makes the page harder to read for the people who use it.
- Explanations go in a tooltip or note, not in new controls.
- Do not hide sensitive values with a UI toggle; keep that safety in the data (masked seeds,
  placeholders).

## Hand it on

Send each fix to the member who owns those files, with the row from the table as its "Done when".
Report to the owner: matches, fixes sent, divergences with reasons, and anything not checked.
