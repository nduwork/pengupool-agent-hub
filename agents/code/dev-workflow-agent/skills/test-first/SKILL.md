---
name: test-first
description: Builds behaviour changes red, green, refactor — a failing test first, watched failing for the expected reason, then the least code to pass it, then cleanup with the suite green — and decides which tests are worth adding, keeping, merging or removing for the risk the change carries. Use when adding or changing behaviour, fixing a bug, or reviewing the tests in a change before committing.
triggers:
  - write a test first
  - TDD
  - red green refactor
  - add a regression test
  - is this test worth keeping
  - which tests should I add
---

# Test first

The point of a test written first is that you saw it fail. A test that has never failed has not
shown it can catch anything.

## Before the first test

Find how this repository tests: the framework, where tests live, how files are named, the command
for one test and the command for the full suite. Prefer checked-in wrappers and the commands CI
runs. Never assume a default like `npm test`.

## The loop

1. **Red.** Write one small test for one behaviour, named for what should happen. Use the public
   interface you wish existed. Run it.
   - It must **fail**, not error, and fail because the behaviour is missing, not because of a typo
     or a broken import. Fix the test until it fails for the right reason.
   - It passes at once? It tests something that already works, or nothing. Change the test.
2. **Green.** Write the least code that makes it pass. No options, flags or generality the test
   does not ask for. Run the test, then the rest of the suite; all green, output clean.
   - The test still fails: fix the code, not the test.
   - Another test broke: fix it now, before anything else.
3. **Refactor.** With everything green, remove duplication and improve names. Run the tests after
   each step. Add no behaviour here.
4. Next behaviour, next failing test.

Before you report the change, run the **full** suite, not only the file you touched. Name every
failure it shows, including ones you did not cause.

If you wrote code before its test, set the code aside and write the test against the behaviour you
want; do not shape the test around code that already exists.

## Bug fixes

Reproduce the bug as a failing test first, then fix. The test is the proof the bug was real and is
now gone. If you cannot reproduce it in a test, say so and describe the check you used instead.

## What makes a test worth having

Before you add or change a test, answer three questions (in your head or one line in the report):

1. **What mistake makes it fail**, and what would that mistake cost a user or maintainer?
2. **Would a correct refactor, or an equally valid result, also fail it?** If so it is pinned to
   implementation, not to the contract. Assert outcomes, state and errors instead.
3. **Does something already catch this?** An existing test, a type check, a schema. Extend that
   instead of building a parallel fixture.

Prefer, in order: the real code, an in-memory fake, a stub, and only then a mock. Mock at slow or
non-deterministic boundaries (network, clock, email), never the thing under test. Keep each test
readable on its own; repetition in tests is fine when it keeps the story in one place.

The judgment calls — add, adapt, merge, retire, and how to tell a real regression from an obsolete
assertion — are in `references/test-value.md`.

## Not every edit needs a new test

Pure copy changes, config with no behaviour, generated code and mechanical renames covered by
existing tests may need none. Say why in the report instead of adding a test that protects nothing.

## Check before reporting

- Every new behaviour has a test, and you saw each one fail first for the expected reason.
- The full suite ran with the repository's own command, and you read the counts: the tests you
  meant to run were actually collected and executed, not filtered or skipped.
- Nothing was skipped, disabled, loosened or re-snapshotted to get green.
- Test names say what behaviour they check.
