---
name: logo-design
license: MIT
description: |
  Use when someone wants a logo, wordmark, monogram, brand mark, symbol, app icon or favicon designed,
  redesigned, critiqued or compared, needs logo concepts, a design brief, lockups, logo guidelines or an
  identity system, or is naming and branding a new company, product or project, even without the word
  "logo". Runs discovery and the brief, category research, concepts across mark types, clean geometric
  SVG construction, optical refinement, colour and typography, testing (16 px, one colour, reversed, shelf
  test), a concept checkpoint, then the delivery kit: lockups, favicon and app-icon sets, export
  variants and a usage guide. Dependency-free scripts audit SVGs, render PNGs and build test and concept sheets.
triggers:
  - logo-design
  - logo
  - wordmark
  - brand mark
  - favicon
---

# Logo design

Act as a senior identity designer. A logo is an **identifier, not an explanation**: a simple,
distinctive, relevant mark that works at 16 px and on a building, in one colour, for decades. Find one
clear idea, build it with craft, prove it works, present it so it's judged on the right criteria. Reply
in the user's language; keep the process visible but light.

## Pick the mode

| The user wants… | Mode | Start with |
| --- | --- | --- |
| A new logo | **Design** (full or fast track) | Phase 1 |
| Feedback on a logo | **Critique** | [references/critique.md](references/critique.md) |
| To modernise or replace a logo | **Redesign** | [references/redesign.md](references/redesign.md), then the Design phases |
| Guidelines, sub-brands, patterns, motion | **System** | [references/identity-system.md](references/identity-system.md) |
| Favicon, app icon or variants of an existing mark | **Assets** | `scripts/export_variants.py` |

**Fast track** (results now, or little information): ask at most five questions in one message
(discovery-brief.md §2), or state your assumptions and go straight to three concepts.

**Concept checkpoint.** Every Design and Redesign run stops after the concepts are built and tested
(Phase 6): show the concept sheet, one line per concept and a recommendation, offer the full kit, and
wait. Build the kit (Phase 7) only after the user picks a direction and says yes. Skip the pause only when
the user says not to check in; if they can't reply, stop anyway and describe what the kit would hold.

## Scripts

Dependency-free Python 3 in `scripts/` next to this file; run them with `python3` and the full path
(on Windows, often `python` or `py -3`).

| Script | Use it to |
| --- | --- |
| `concept_sheet.py` | The checkpoint image: mark, lockup, true 64/32/16 px, name, idea, recommendation |
| `svg_audit.py` | Live text, rasters, filters, colours, strokes, near-miss angles, tiny details, centring, complexity |
| `preview_sheet.py` | HTML test sheet: sizes, 16 px pixels, backgrounds, one colour, blur, mirror, contexts, shelf test (`--refs`) |
| `render_png.py` | SVG → transparent PNG at exact sizes; screenshots HTML sheets; `favicon.ico`; `--which` lists renderers |
| `export_variants.py` | Black, white, mono, square, favicon, app-icon SVGs; `--png`; `--web-icons` (ico, PNGs, manifest) |

**Look at your work.** Drawing in SVG code is drawing blind. After every change:
`python3 scripts/render_png.py a.svg b.svg --out-dir renders --size 512`, then open the PNGs and look.
It picks the best renderer available; don't call `qlmanage` directly. If you can't render, say so.

## Design workflow

1. **Discovery → brief.** Exact name, what they do, audience, 3–5 brand adjectives, competitors,
   constraints, decision-maker. A short brief (discovery-brief.md §5) with your assumptions.
   Adjectives become visual cues.
2. **Research and strategy.** Study the category from your own knowledge and a web search for its
   leading brands: dominant mark types, colours, techniques. List its **clichés** (fintech: blue,
   arrows, shields; coffee: beans, steam, cups) and treat them as off-limits without a fresh form. Word
   map (discovery-brief.md §6). Choose at least two mark types (mark-types.md §12).
3. **Concepts.** 8–12 one-sentence concepts across mark types, each with an ownable twist. Score them
   (clarity, distinction, simplicity, relevance, small size); keep the **three strongest and most
   different**. Check none recreates an existing mark you know of, or find with a web or reverse image
   search. One-liners are cheap; build only the three.
4. **Build in SVG, black first.** Describe the construction in words (primitives, radii, angles, grid),
   then write it (svg-construction.md): `viewBox="0 0 256 256"` for symbols, height 256 for lockups;
   few anchors, arcs for circles, exact angles, consistent strokes, real holes (`fill-rule="evenodd"`).
   No `<text>` in a finished mark. Save each iteration (`-v1`, `-v2`).
5. **Test and refine, at least twice.** `svg_audit.py`, then `preview_sheet.py … -o preview.html`; look,
   fix, re-run: scale (16–24 px), optical corrections, balance, readings (mirror, 180°), distinction
   (shelf, familiarity), and a craft pass: letters still read, clean junctions, as resolved as good
   published marks, not merely the product drawn (visual-techniques.md, testing-checklist.md).
6. **Show the concepts, then stop.**
   `python3 scripts/concept_sheet.py a.svg b.svg c.svg --lockups a-l.svg b-l.svg c-l.svg --names A B C
   --notes "…" "…" "…" --recommend 1 --greyscale -o concepts.png`. View it yourself, then show it
   (greyscale first: colour starts taste debates) in the format below, and wait.
7. **Build the kit, after a yes.** Refine the direction and its small-size cut (`--favicon-source`); colour, 1–2
   ideally, with one-colour and greyscale versions that still work (color.md); type and lockups,
   horizontal, stacked, symbol-only (typography.md); a presentation with industry mockups
   (presentation-delivery.md); `export_variants.py` for the file set; a usage guide from
   `templates/brand-guidelines-template.md`; the final checklist in process.md §7.

## Red flags: fix before showing anything

- Clip-art literalism (a tooth for a dentist) or category clichés with no twist.
- Initials in an unmodified stock font; a default geometric sans with nothing ownable.
- More than three colours without a reason; gradients or shadows rescuing a weak form.
- Details under ~1/48 of the mark, hairlines, gaps that close when small.
- Near-miss angles, lumpy curves, inconsistent stroke weights.
- Live `<text>`, embedded rasters, filters or masks in a "final" file.
- A concept that needs a paragraph; anything that looks like an existing logo.

## The checkpoint message

```markdown
<concept sheet image>

### A — <Name> · <mark type>   ← recommended
**Idea:** <one sentence>
**Why it fits:** <2–3 bullets tied to the brief's adjectives, audience, competition>

### B — … / ### C — … (same shape)

**My recommendation:** <one or two sentences, one honest risk per concept if relevant>
**Next:** pick a direction (or say what you like in each). Want the full logo kit for it? It holds the
palette with one-colour and reversed versions, lockups, a small-size cut, favicon, app-icon and web-icon
set, a presentation with mockups for your industry, and a one-page usage guide.
```

## Honesty

- You can't guarantee trademark clearance: recommend a professional search and a reverse image search.
- Font licences must allow logo use; name the fonts you assumed.
- Never claim a test you didn't run.

## References

| Read | When |
| --- | --- |
| [principles.md](references/principles.md) | Justifying decisions, resolving debates, deep critique |
| [discovery-brief.md](references/discovery-brief.md) | Questions, brief template, word map |
| [mark-types.md](references/mark-types.md) | Choosing the type of mark |
| [visual-techniques.md](references/visual-techniques.md) | Grids, balance, optical corrections, negative space |
| [color.md](references/color.md) | Palette strategy, reproduction, accessibility |
| [typography.md](references/typography.md) | Type study, custom letters, spacing, lockups, licensing |
| [process.md](references/process.md) | Stage by stage, vector development, final checklist |
| [svg-construction.md](references/svg-construction.md) | Clean SVG logos, recipes, what to avoid |
| [testing-checklist.md](references/testing-checklist.md) | Everything to test before presenting or delivering |
| [presentation-delivery.md](references/presentation-delivery.md) | Presenting, feedback, deliverables |
| [identity-system.md](references/identity-system.md) | Kit of parts, sub-brands, patterns, motion, rollout |
| [redesign.md](references/redesign.md) | Refresh or rebrand, equity audit |
| [critique.md](references/critique.md) | Structured critique with a scorecard |

## Credits

Adapted from logo-design-skill by Kaan Kiziltug (github.com/kaankiziltug/logo-design-skill), MIT
License, Copyright (c) 2026 kaankiziltug. References, scripts and template are adapted copies.
