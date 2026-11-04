# Visual direction and planning a screen

DESIGN.md already fixes the palette, type and components. Use this to make the choices it leaves
open on purpose, not by habit, and to keep a new screen from drifting into generic output.

## Start from the subject

PenguPool's world is terminals, agent sessions, teams, branches and diffs. Distinct choices come
from that vocabulary: a status that reads like a process state, a log that reads like a log, a map
that reads like an ownership chart. Before designing, name in one line who uses the screen, what it
is for and the real data it shows. Design with that data, never placeholder text.

## Plan, check, then build

For a new screen or a visual change, write a plan of a few lines before any code:

- **Tokens:** which existing DESIGN.md tokens it uses, and any new one it needs, with the reason.
- **Type:** which roles appear (body, mono identifiers, `SectionTitle`) and the one place, if any,
  where type carries emphasis.
- **Layout:** one sentence plus a hand-written SVG draft; say what is aligned to what. Compare two
  drafts when the layout is not obvious.
- **The one thing:** the single element the screen should be remembered by.

Then check the plan: would it come out the same for any other developer tool? If a part would, it
is a default, not a choice. Change that part and say what changed and why. Build only after that.

## Draft, review, then build

The SVG draft is the plan made visible: the owner reviews it before any component code is written,
and the build starts only after approval.

- **Canvas and ids.** A `viewBox` canvas at the screen's real width. Give every discussable part an
  `id` (`id="card-session-list"`, `id="cta"`): feedback cites ids, and ids become component names.
- **Literal hex, token named.** Drafts use literal hex copied from `web/src/index.css`, never
  `var()`: resvg cannot resolve `var()` or `:root` and renders those fills black. Keep the token
  name on the element with `data-token="--primary"` so the build maps the colour back. Fills may
  sit inline or in a `<style>` rule: contrast is read from the rendered PNG, so either works. Type
  sizes come from the DESIGN.md scale; keep font-size and text-anchor inline or in a simple rule,
  since the check needs them for the overflow test. A magic number that matches the draft means a
  token is missing: add it to DESIGN.md.
- **Versioned.** `drafts/draft-v01.svg`, `draft-v02.svg`, … Never overwrite a round; the previous
  version stays for the side-by-side. Keep drafts outside the build tree until approved.
- **No SMIL.** Drafts are static; motion belongs in the built screen.
- **Check before showing.** Render, then check: `resvg drafts/draft-v02.svg drafts/draft-v02.png`,
  then `python3 scripts/svg_check.py drafts/draft-v02.svg > drafts/draft-v02.check.txt`. Fix every
  failure before showing the draft: overlapping parts, text overrunning its box or the frame,
  `var()` in a fill, resvg errors, SMIL. Contrast is advisory: every contrast result, including a
  text or tspan that is not visible, is a `WARN` for the owner to confirm by eye on the review
  page; it never blocks. The check does not guarantee AA: a glyph exactly matching its background
  is a known limit, and a rotated or scaled element warns that overflow and safe area were skipped.
- **Review page.** `node scripts/draft-review.mjs drafts/draft-v02.svg drafts/draft-v01.svg > drafts/review.html`
  gives one local page: the rendered PNG, the zoomable SVG and the previous version side by side,
  with a feedback box per element id and any `WARN` lines from `<draft>.check.txt` at the top. The
  owner opens it from `file://` (no server, no publishing) and pastes `feedback.md` back; each
  round starts with empty boxes.
- **Loop.** Revise the SVG only, re-render, re-check, cut a new version. Stop when the owner
  approves, or after two rounds without convergence stop and ask, showing both versions.

## Defaults that read as generated

Each is fine where DESIGN.md asks for it; elsewhere, treat it as a reflex to question:

- Identical rounded cards with the same soft grey shadow, one radius on everything, gradient washes.
- A tracked-out ALL-CAPS label over every heading. Uppercase here is only `SectionTitle`, the
  map's `LEAD` chip and `UNGROUPED`.
- One word in a heading picked out in another colour, weight or italic.
- Labels above content that only repeat what the content already says.
- Numbered markers (01 / 02 / 03) on content that is not a real sequence.
- `→` tacked onto button and link text.
- Middle-dot meta strings (`A · B · C`) beyond the map card's `harness · ctx% · repo`.
- Warm cream with a terracotta accent, or near-black with one acid-green accent: neither is ours.

Borders, dividers, numbering and labels are information. Add one only when it tells the user
something about the content.

## Restraint

- Spend boldness in one place per screen and keep the rest quiet.
- Before calling a screen done, remove one decoration and see if anything was lost.
- Prose blocks (help text, empty states, docs panels) stay under about 80 characters per line.
- Motion nobody triggered is for drawing attention only, at most one moment per screen. Motion
  that answers an action (open, expand, confirm) is welcome when it shows what changed.
- Take screenshots while building and critique them against the plan, not only at the end.
- With Tailwind, resolve clashing classes with `cn()` (tailwind-merge), never `!important` or
  extra specificity.

## Copy

- Name things the way the user thinks of them, not how the system is built: "helper agent", not
  "skill repository"; "approval", not "pending proposal row".
- Describe what a thing does; don't sell it. Clear beats clever.
- Errors state what happened and how to fix it, without apology. An empty screen invites the
  first action.
- Each piece of text does one job. Cut filler.
