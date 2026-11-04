# Isolation techniques

## Failures you cannot reproduce on demand

| Suspect | Make it show |
| --- | --- |
| Timing or a race | Timestamped logs around the area; widen the window with a deliberate delay; run many times or in parallel |
| Environment | Compare runtime and tool versions, OS, environment variables, data (empty vs full); try a clean checkout or container |
| Leftover state | Run the failing test alone, then after the suite; look for globals, singletons, caches, temp files, shared databases |
| Test order | Run in reverse or random order; bisect the list of tests that ran before it to find the one that pollutes state |
| Truly rare | Add logging that captures the inputs at the suspect point, note the conditions, and wait for the next occurrence |

Replace fixed sleeps in tests with waiting for the condition itself (poll until ready, with a timeout).

## Finding the commit

```bash
git bisect start
git bisect bad                 # current commit fails
git bisect good <sha>          # a commit that passed
git bisect run <focused test command>
git bisect reset
```

The test command must exit non-zero on failure and zero on success. Use a copy of the reproduction
that does not depend on files the bisect will change.

## Finding the layer

Check each hand-off once, with one run:

- what the caller sends, what the callee receives;
- which configuration or environment values each step actually sees;
- the state at each stage (rows written, files present, cache contents).

The first boundary where the value is already wrong is where to look next.

## Triage by kind

- **Test fails after a change:** did the change touch what the test covers? Then decide whether the
  test is outdated or the code is wrong. Touched something unrelated? Look for shared state and side
  effects. Already flaky? Treat the flakiness as the bug.
- **Build fails:** read the first error, not the last. Type, import, config, dependency and
  toolchain-version errors each point to a different file.
- **Runtime error:** a null where a value was expected means trace where the value comes from; no
  error but the wrong result means log the data at each step and find where it diverges.
- **Slow:** measure before changing anything; profile, find the hot spot, change one thing,
  measure again.

## When stuck, check the boring things

Spelling and case in names and paths, off-by-one, null or empty values, async ordering, a stale
build or cache, a wrong working directory, relative vs absolute paths, an environment variable that
is unset in this shell, and a dependency version that differs from the lockfile.
