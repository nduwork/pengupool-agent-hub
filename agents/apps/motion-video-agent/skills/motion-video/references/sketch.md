# The cheap sketch (step 2)

Do this before any scene code. It is the owner's approval gate for pacing and story, and the
drawn poses the scene build reuses.

## Write

- **`shots.json`** — one shot per frame range with its beat, hero move, transition, and labelled
  boxes moving x0,y0 → x1,y1 with a named ease. The format is at the top of `scripts/sketch.mjs`.
- **One SVG key frame per shot** — `shot-<id>.svg` beside `shots.json`: the midpoint pose at the
  piece's real aspect, on a canvas with a `viewBox`, each moving part drawn with an `id` that
  carries into the scene code. Use literal hex copied from the design tokens, never `var()` (resvg
  renders it black); keep the token name on the element with `data-token="--primary"`. Fills may
  sit inline or in a `<style>` rule: contrast is read from the rendered PNG. Keep font-size and
  text-anchor inline or in a simple rule, since the check needs them for the overflow test.
- **No SMIL.** Drafts are static; motion belongs in the built scene.

Keep each round in its own folder (`draft-v01/`, `draft-v02/`, …). Never overwrite a round: the
previous one stays for comparison. Keep drafts outside the build tree until approved.

## Check before showing

For each shot, render and check, and fix every failure before showing the frame:

```
resvg shot-<id>.svg shot-<id>.png
python3 scripts/svg_check.py shot-<id>.svg --video > shot-<id>.check.txt
```

Fix every failure before showing the frame: overlap, text overflow, a safe-area breach, `var()`
in a fill, resvg errors, SMIL. Contrast is advisory: every contrast result, including a text or
tspan that is not visible, is a `WARN` for the owner to confirm by eye on the review page; it
never blocks. Video safe area is exact: nothing within 60 px of an edge, and for portrait key text
inside the middle 75 % vertically. The check does not guarantee AA: a glyph that exactly matches
its background is a known limit, and a rotated or scaled element warns that overflow and safe area
were skipped.

## Review

```
node scripts/sketch.mjs draft-v02/shots.json > sketch.html
```

`sketch.html` inlines the key frames into the shot cards. The owner opens it locally (no server,
no publishing), plays or scrubs the wireframe, writes feedback per shot and pastes back or
downloads `feedback.md`; each round starts with empty boxes. Revise `shots.json` and the SVGs
only, never the page, until the owner approves pacing and story — stop at approval, or after two
rounds without convergence ask, showing both versions.

`sketch.html?stage` works with `render.mjs` for a low-res animatic (pass `--width`/`--height` in
the piece's aspect ratio).
