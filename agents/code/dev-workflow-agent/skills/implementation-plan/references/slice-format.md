# Slice format and sizing

## Plan header

```markdown
# Plan: <change in a few words>

Goal: <one sentence>
Done when: <checkable conditions, one per line>
Out of scope: <what this change will not touch>
Commands: test <one test> / <full suite>; build <cmd>; lint <cmd>
Assumptions: <each one, marked confirmed or open>
Untested risks: <inputs or failures most likely to bite, each with the slice that now tests it>
```

## One slice

```markdown
### Slice N: <behaviour, no "and">

Done when: <1-3 checkable points>
Files: <path> (new) · <path:lines> (change) · <test path>
Uses: <names and types from earlier slices>
Gives: <names and types later slices rely on>
Check: `<command>` → <the output that means it passed>
```

A test step names the test and its assertions with real values. A code step names the signature and
the file; the body is left to the builder unless the algorithm is not obvious from the signature and
test. A check step names the command and the output that counts as passing.

## Sizing

| Size | Files | Fits in a slice? |
| --- | --- | --- |
| One function or rule | 1 | yes |
| One endpoint, component or command | 1-2 | yes |
| One behaviour end to end | 3-5 | yes, the usual slice |
| Several components | 5-8 | split it |
| Larger | 8+ | split it; it is several slices or several plans |

Split a slice when it needs more than three acceptance points, touches two subsystems that do not
need each other, or will not finish in one sitting.

## Ordering patterns

- **Vertical:** create → list → edit → delete, each through every layer, each shippable.
- **Contract first:** agree the interface, then build both sides against it, then join them.
- **Risk first:** prove the uncertain part works (a connection, a format, a library) before building
  on it.

Between groups of two or three slices, run the full suite and the build, and check the main flow
end to end.

## Recording progress and decisions

Keep one line per finished slice next to the plan:

```
Slice 2: done (commits a1b2c3d..d4e5f6a, `pytest tests/test_export.py` → 6 passed)
Slice 3: decision: kept the old column name, the client still reads it; cost if wrong: one rename later
```

Never overwrite a plan that still has unfinished slices for different work; ask the owner first.
