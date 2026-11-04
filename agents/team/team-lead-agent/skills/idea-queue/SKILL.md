---
name: idea-queue
description: Use when you lead a PenguPool team and the owner talks ideas - a feature they want, a "what if", a half-formed plan, a change of mind - or asks what ideas are waiting. Captures each idea in one line the owner can confirm, points out repeats, groups the queue by outcome, and turns a group into a short brief by asking the owner one question at a time. Turns a ready group into a proposed epic (skill epic-planning); it never applies, reorders or deletes anything itself.
triggers:
  - idea
  - what if
  - we should
  - maybe we could
  - I want
  - later
  - backlog
  - what's in the queue
  - turn this into a plan
---

# Idea queue — collect the owner's ideas and shape them

The owner thinks out loud. Your job is that no idea is lost, none is recorded twice, and a group of
ideas becomes something the team can act on, without slowing the owner down.

## Capture: one idea, one line

When the owner states an idea:

1. Search first: `pengupool search "<key words>"`. If the record already holds it, tell the owner
   which earlier idea it matches.
2. Say it back in one line. The line names the outcome, not a solution: "members can see who is
   blocked on them", not "add a blocked column". PenguPool records the turn; its triage proposes
   anything lasting from the owner's words, and the owner approves it. You write nothing yourself.
3. Let the owner keep talking. Do not interview them mid-flow.

Only the owner's own words count as their idea; an idea from a member is passed to the owner as a
suggestion, not queued as theirs.

## Merge: point it out, never apply

When two ideas are the same or one contains the other, say so in one line and offer the combined
wording. The owner decides; you never delete, edit or reorder anything yourself.

## Group by outcome

When the owner pauses or asks "what's in the queue", find the ideas in the record
(`pengupool search`) and group them by the outcome they serve, not by when they came or
which repository they touch. Show each group as:

```text
<group name>: <outcome in one line>
  - <idea>
  - <idea>
  open: <the one question that most changes this group>
```

Ideas that fit no group stay on their own; never invent ideas to fill a group.

## Shape a group into a brief

When the owner picks a group:

1. **Ask, one question at a time.** Each question carries your best guess ("I think the goal is X,
   because you said Y; is that right?"), so the owner can answer in a word. Stop when you could
   state the goal back and the owner agrees; usually two to four questions.
2. **Widen, then narrow.** Name two or three different ways to reach the outcome, then the one the
   owner's answers favour and why.
3. **Write the brief** and send it to the owner:

   ```text
   Problem:      <who has it and why it matters, one or two sentences>
   Direction:    <the chosen way, and the closest alternative it beat>
   Assumptions:  <what must be true; how to check each>
   Smallest version: <the first thing worth building>
   Not doing:    <what this deliberately leaves out, and why>
   Open:         <questions still for the owner>
   ```

4. If the owner states a lasting rule while shaping ("never X", "always Y"), say it back separately
   from the idea; PenguPool's triage proposes it from their words.

## Hand it on

When the owner wants the brief to become work, propose it as an epic yourself (skill
`epic-planning`): the owner adopts it on the board.

You never start the work or assign it before the owner adopts the epic.
