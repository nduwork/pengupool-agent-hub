# Reviewing a PenguPool screen

## 1. First impression (2 seconds)

Where does the eye land first, and is that right? Is the screen's job obvious? Is the one primary action
the most prominent thing? Is status readable before reading any text?

## 2. Worst-case data

Feed the real boundary (fixture, mock, store), never edited markup. One dataset, failures spread
across rows. Use plausible values:

- Session name: `review-guide-second-opinion-worker-2`; repo `pengutool-wt-skill-pool`;
  path `web/src/components/ui/`.
- Model id `vendor-large-model-5-5[1m]`; branch `propose/review-guide-selfcheck-41bc754`;
  full 40-char SHA.
- Counts 0, 1, 12, 1,284; ctx% 0, 100; a 4 KiB team message; non-Latin and emoji in a name.
- Lists: empty, one, 1,000+ (logs, sessions). Missing optional fields (no repo, no model).
- Times: just now, 3 weeks ago, clock skew (future).

Check at the panel's real width, at 960×640 and wide, at 200% zoom, in dark and light. Report
each break as Broken / Ugly / Fragile with cause and fix; list judgement calls separately
(truncate or wrap, paginate or virtualize). Keep the fixture as a regression test behind a
dev-only `?data=worst` toggle.

## 3. Accessibility (WCAG 2.2 AA)

Contrast 4.5:1 text, 3:1 large text and UI parts (check status tints and `faint` text in both
themes). Keyboard-only pass: Tab order, Enter/Space, Escape, arrows in lists and tabs. Visible
focus everywhere. Names/roles on custom controls. Live region for agent state changes. 200% zoom
without sideways scroll. Automated scan (axe) catches ~30%; VoiceOver pass for the rest.

## 4. Consistency

Tokens only (no raw hex, no off-scale px). Same thing looks and behaves the same everywhere.
States covered for each component: default, hover, active, focus, disabled, loading, error, empty.

## 5. Copy

Verb-first buttons, toast reuses the verb, errors say what to do next, empty states say how to
start, no "Are you sure?", same term for the same thing across screens.

## 6. Verify in the running app

Audit the rendered UI, not the source; screenshots are the evidence for every finding.
Electron: launch with `--remote-debugging-port`, attach over CDP, pick the window by a stable
`data-*` marker. Select by role/label, one action per step, fresh snapshot after each. Use CDP
emulation for dark/light, `prefers-reduced-motion` and window sizes. Don't keep screenshots of
real repos or transcripts beyond the review.

## Grading (optional, for a whole-screen review)

Rate each area 0-10 (hierarchy, type, colour, spacing, states, motion, copy, a11y), say what a
10 would contain, give one concrete recommendation, one decision per issue, then re-rate. Never
batch "apply all" into one approval. For one overall score, weight hierarchy,
type, spacing 15% each; colour, states, responsive, copy 10% each; AI look, motion, perf 5% each.

## Output

```
| # | Severity | Location | Before | After | Why |
```
Worst first, `file:line` on each row, 5-10 well-evidenced findings over 20 vague ones. Then
"Quick wins" (3-5 fixes under 30 minutes), "Decisions for you" (one line each, with a
recommendation), then "What held up". Stop; fix only what the owner picks, one commit per fix,
CSS-first.
