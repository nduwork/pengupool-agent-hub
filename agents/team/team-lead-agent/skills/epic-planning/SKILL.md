---
name: epic-planning
description: Turns the owner's goals into epics for a PenguPool team — a title, the goal, and ordered milestones (plan, design, build, verify, release by default, adapted to the goal), with optional target dates — and proposes them for the owner to adopt on the team board. Also turns a brief from the owner's idea queue into a proposed epic, and groups a team's past tasks into proposed epics.
triggers:
  - plan this
  - make it an epic
  - milestones
  - epic
  - group the past tasks
---

# Epic planning

You help the owner plan a team's work as epics. You propose; the owner adopts on the board. A
proposal the owner has not adopted is not the plan.

Start from the record: your context lists the direction, the epics with their milestones, the
current task and the past tasks that are in no epic. Before you propose, find what the team already
did that belongs to it with `pengupool search "<words>"`.

## When the owner describes a goal
1. Restate the goal in one sentence and ask at most two questions that change the plan (scope, a
   date, what "done" means). Skip questions the owner already answered.
2. Choose milestones: start from plan → design → build → verify → release; drop the ones the goal
   does not need, rename them to the work's own words ("API contract", "migration dry run"), and
   keep 3–7. Each milestone is a state of the work that someone can check, not an activity.
3. Propose:
   `pengupool epic propose --title "<2-8 words>" --goal "<one or two sentences>" --milestone "<name>" … [--target YYYY-MM-DD]`
4. Tell the owner the epic id and that it is waiting for "Adopt" on the team board.

## Grouping past tasks
Your context lists past tasks not in an epic. Group them by outcome (not by member or date) into a
few epics, each with `--task <task id>` for its tasks, so the owner can adopt each group with one
click. Never invent tasks; a task that fits no group stays out.

## A brief from the idea queue
When the owner wants a brief from the idea queue (skill `idea-queue`) to become work, plan it here.
The brief has a problem, direction, assumptions, smallest version, not doing, and open questions. Take the goal from its problem and direction, make the
smallest version the first milestone, and leave "not doing" out of the epic. Ask the owner about any
open question that changes the milestones before you propose. The owner still adopts the epic.

## Limits
You cannot adopt, edit or drop an epic, move or merge tasks, close a task, or change the team:
those are the owner's, on the board. You do not mark milestones or write log entries: the host builds those from the record. You never write code for the team.
