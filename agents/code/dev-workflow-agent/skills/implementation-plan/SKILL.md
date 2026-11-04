---
name: implementation-plan
description: Turns a request or spec for one code change into a short written plan of ordered, thin slices, each with the files it touches and the check that proves it, then works through the slices one at a time with a passing check and a commit after each. Use before a change that touches more than a couple of files or whose order is not obvious, and when picking up the next slice of an existing plan.
triggers:
  - plan this change
  - break this down
  - implementation plan
  - what order should I build this in
  - next slice
  - execute the plan
---

# Implementation plan

A plan is the list of decisions someone could not make alone from the request: which files, which
names and signatures, which values, and which check proves each step. It is not the code written out
in advance. A one-line fix needs no plan; go straight to `test-first`.

## 1. Pin down what "done" means

1. Restate the change in one sentence.
2. List the assumptions you are making (stack, scope, interfaces, data) and ask the owner about the
   ones that would change the plan. Ask at most two or three questions; do not ask what the request
   or the code already answers.
3. Turn vague goals into checkable conditions: "faster" becomes a number on a named measurement,
   "handles bad input" becomes the inputs and the expected response.
4. Note what is out of scope, so the slices do not grow into it.

If the request bundles several capabilities that could ship and be tested on their own, say so and
propose one plan per capability, in dependency order, before planning any of them.

## 2. Read the code, then map the change

- Find the repository's build, test and lint commands and how to run one test on its own.
- Find the files the change touches, the existing helpers it can reuse, and the patterns nearby code
  follows. Follow them; do not restructure the codebase as a side effect.
- Sketch what depends on what. Foundations come first, but prefer **vertical slices**: each slice
  carries one behaviour through every layer it needs and leaves the system working.
- Put the riskiest or least certain slice early, so a dead end shows up before the rest is built.
- When two sides must meet (API and client, producer and consumer), make the contract its own first
  slice.

## 3. Write the slices

Each slice gets a short title, what is true when it is done, the files it touches, the interface it
gives later slices (exact names and types), and the command that proves it plus the output that
means it passed. The format and sizing rules are in `references/slice-format.md`.

Keep a slice to one logical thing, a handful of files and a few acceptance points. A title with
"and" in it is usually two slices. Fold setup, configuration and docs into the slice that needs
them rather than making them slices of their own.

## 4. Check the plan before you start

- **Coverage:** every requirement maps to a slice; every slice serves a requirement.
- **Names:** a function, type or field is called the same thing in every slice that uses it.
- **No empty steps:** "handle edge cases", "add validation", "TBD" decide nothing. Replace each with
  the case, the rule or the question.
- **Proportion:** if the plan is longer than the code it describes, cut code bodies back to
  signatures and test names.
- **Gaps tests will not catch:** name the few inputs or failure modes a user is most likely to hit
  that no slice tests yet (empty input, very large input, a missing file, a retry), and add a test
  for each to the slice that owns the code.

Show the plan to the owner and wait for a yes before building, unless they already told you to go
ahead. Keep the plan where the owner wants it; otherwise keep it out of the repository (in the
conversation or a scratch file) and never commit it by accident.

## 5. Work the slices

For each slice, in order:

1. Re-read the slice (not your memory of it).
2. Build it test-first (`test-first`).
3. Run the slice's check and compare the output with what the plan expects.
   - Matches: go on.
   - The code is wrong: `root-cause-debugging`. Do not bend the check to fit.
   - The plan is wrong (an interface does not fit, a command cannot work): make the smallest change
     that still meets the request, write it down as a decision with its reason, and go on.
4. Run the build and the existing tests so the tree stays green between slices.
5. Commit the slice on its own, with a message that says why.

Stop and ask the owner only for something destructive or irreversible, something security-sensitive,
an action outside your worktree (push, merge, publish), or a plan so broken that every path forward
is a guess. Otherwise decide, record the decision, and keep going.

If you lose your place, trust `git log` and the plan's record of finished slices over memory, and
resume at the first slice with no commit.

When every slice is in, simplify (`simplify-change`) and finish (`verify-and-finish`). Report every
decision you made on the owner's behalf, each with what it would cost if it was wrong.
