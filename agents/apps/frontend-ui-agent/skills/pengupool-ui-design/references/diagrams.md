# Documentation diagrams

Static diagrams for READMEs and help pages. The live Workspace map has its own rules in
[map.md](map.md); nothing here applies to it.

## Choose the tool

| Diagram | Tool |
| --- | --- |
| Architecture, nested subsystems, labelled relationships that gain from automatic layout | D2 |
| A simple flowchart or sequence diagram that GitHub renders natively | Mermaid |
| Exact artwork: logo, hero art, branded geometry | Hand SVG |

GitHub does not render D2 source. A `.d2` fence shows as code, so commit the `.d2` file and
its rendered SVG, and embed the SVG.

## Content

- Start from the reader's question, and draw only relationships you checked in the code.
  Never invent architecture.
- One idea per diagram. Short labels, stable node IDs. Group only real boundaries.
- Never use colour alone to carry meaning.

## Files

- Follow the repository's existing asset layout. If it has none, keep source and outputs
  side by side under `assets/diagrams/`, with descriptive kebab-case basenames:
  `muse-loop.d2`, `muse-loop.light.svg`, `muse-loop.dark.svg`.
- Never hand-edit a generated SVG. Change the source and render again.
- Commit the source and its exports in the same change.

## Toolchain

- Use D2 v0.9.0 for a new render workflow. If the repository already pins a version, keep it.
- Check the installed version first (`d2 --version`). If D2 is missing, follow the
  dependency policy in [SKILL.md](../SKILL.md) (add only with the owner's yes). Never install a
  package silently, and never fall back to a browser or WASM renderer.
- Install from the official tagged release binaries, and verify them against the release's
  checksums. `brew install d2` is not a version pin, and neither is `@latest`.
- Dagre is the default layout engine. Try ELK (`--layout=elk`) for hard nested graphs. Never
  require TALA: it is a separately licensed engine.

## Rendering

- Put the layout, theme, fonts and padding explicitly in the repository's render command.
- Use the bundled fonts first. A custom font adds files, licensing and pinning work.
- Pick a restrained palette with `d2 themes`, matching PenguPool's documentation style.
- `--pad=24` is a starting point, not a fixed rule. D2's default pad is 100.
- Use sketch mode (`--sketch`) only for an intentionally informal illustration.
- Light and dark: render separate `.light.svg` and `.dark.svg` files, and embed them the way
  the repository already does. Alternatively, `--dark-theme` makes one SVG follow the
  browser's dark mode; confirm that in the real viewer before relying on it. Any explicit
  colour in the source must work in both modes.
- PNG export is native and needs no extra dependency, so it is the fallback when a viewer
  mishandles SVG. Never add Playwright or Chromium for it.

```sh
d2 fmt assets/diagrams/muse-loop.d2
d2 validate assets/diagrams/muse-loop.d2
d2 --layout=elk --theme=0 --pad=24 assets/diagrams/muse-loop.d2 assets/diagrams/muse-loop.light.svg
d2 --layout=elk --theme=200 --pad=24 assets/diagrams/muse-loop.d2 assets/diagrams/muse-loop.dark.svg
# Or one SVG that follows the browser's theme:
d2 --layout=elk --theme=0 --dark-theme=200 --pad=24 assets/diagrams/muse-loop.d2 assets/diagrams/muse-loop.svg
```

The example uses ELK; drop `--layout` to get the Dagre default. Theme 200 (Dark Mauve) only
shows how the flags work; it is not a palette choice. Pick the
real palette by looking at the result.

## Check before delivery

1. Format and validate the source, then render.
2. A nonzero exit from the renderer is a failure, even if it left an output file behind.
3. View the result at its intended size (README width), in both themes. Fix text that is
   too small, crossed or ambiguous edges, overlaps and clipping.
4. Check every relationship against the implementation. Write meaningful alt text.

## Repeatability

- When the first real diagram lands, add one repeatable render command or a small script
  with it. Don't add a script or CI before then.
- `d2 fmt --check` checks formatting only; it can't detect stale exports. A CI freshness
  check has to regenerate with the same pinned renderer, fail on a diff in the tracked
  outputs, and also catch expected outputs that are missing or untracked.

Sources: https://d2lang.com/tour/install/ · https://d2lang.com/tour/layouts/ ·
https://d2lang.com/tour/themes/ · https://d2lang.com/tour/fonts/ ·
https://d2lang.com/tour/exports/ · https://github.com/d2lang/d2/releases/tag/v0.9.0
