# Workspace map canvas

- **Semantic shape first.** The map is ownership (team → lead → helpers) plus state, not a
  scatter. Choose positions; never ship an auto-layout's default spacing.
- **Complexity budget.** Past roughly 9 sessions or 12 connectors in one view, cluster
  (collapse a team to one node with a count) or split overview and detail. Owner decision:
  the exact threshold.
- **Focus.** Teal accent on 1-2 elements (the selected session, the anchor). Status colours
  are meaning, not accent, and stay on the border + symbol + word.
- **Cards.** Border-only, `rx` 6-8, opaque fill so connectors never show through. Type tags
  (`LEAD`) are rectangular (`rounded-sm`), not pills. Size differences must mean something.
- **Type.** DESIGN.md keeps the canvas mono, as in v1. The alternative puts names in
  sans and keeps mono for identifiers (`harness · ctx% · repo`, paths). Owner decision.
- **Connectors.** Orthogonal with rounded elbows (r≈8). No two lines share an attach point on
  one edge; no line runs behind a box that isn't its endpoint; labels sit on an opaque chip
  6-10px off the stroke. If the relation is obvious from layout, drop the line.
- **Deletion test.** Merge nodes that never appear apart. Stop when removing anything would lose
  meaning. Aim for a sparse canvas, roughly 4 on a 10-point density scale.
- **Pan and drag.** 1:1 with the pointer, pointer capture, grab offset kept, rubber-band at the
  edges, `transform` only. No zoom or pan animation from keyboard shortcuts.
- **Accessibility.** If SVG: `role="img"` with `<title>` + `<desc>`, plus a keyboard-reachable
  list of the same sessions (the canvas alone is not accessible).
