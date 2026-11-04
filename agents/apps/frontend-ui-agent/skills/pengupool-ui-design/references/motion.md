# Motion for PenguPool

Tuned for a crisp desktop tool: few animations, all of them fast.

## Gate (every animation passes all four)

1. **Frequency.** 100+/day or keyboard-initiated: none. Tens/day: colour only. Occasional:
   standard. Rare (first run, a team finishing a job): may delight, briefly.
2. **Purpose**, named as one of: feedback, spatial consistency, state indication, preventing a
   jarring change. "Looks nice" fails.
3. **Budget.** Press 100-160ms, tooltip 120-150ms, menu/popover 150-200ms, sheet 200-250ms.
   Nothing on a UI element over 300ms.
4. **Function.** Data the user is reading (terminal, logs, map cards) does not move for style.

## Tokens to add to `web/src/index.css`

```css
@theme {
  --ease-out: cubic-bezier(0.23, 1, 0.32, 1);      /* enter/exit, press */
  --ease-in-out: cubic-bezier(0.77, 0, 0.175, 1);  /* on-screen move, panel resize */
  --duration-press: 120ms;
  --duration-pop: 160ms;
  --duration-sheet: 220ms;
}
```

Easing choice: entering/exiting → ease-out; moving on screen → ease-in-out; hover/colour → ease;
spinner/progress → linear. Never ease-in.

## Patterns

- **Popover/menu/tooltip:** `opacity 0, scale(.97)` → settled; `transform-origin` at the trigger
  (Radix exposes `--radix-popover-content-transform-origin` etc.). Exit faster than enter.
- **Sheet (modal):** centred origin, fade + `scale(.98)`, scrim fades with it.
- **Toast:** Sonner defaults; enters and leaves from the same edge.
- **Entry without JS:** `@starting-style { opacity:0; transform:scale(.97) }`.
- **Interruptible:** use transitions, not `@keyframes`, for anything triggered rapidly
  (toasts, toggles, collapse). Keyframes only for loops (status pulse, spinner).
- **Hold to confirm** (destructive, e.g. kill a session): `clip-path` fill 1.5-2s linear on
  press; letting go early returns it over 200ms ease-out. Alternative to a confirm dialog.
- **Status pulse:** opacity only, ≥1.5s period, never on more than the running dot.
- **Hover:** gate movement behind `@media (hover:hover) and (pointer:fine)`.

## Performance

Animate `transform` and `opacity` only. Don't drive child transforms through a parent CSS
variable (style recalc across every row). `will-change` only right before motion. Sash drag and
map pan update `transform` directly, 1:1 with the pointer, with pointer capture and the grab
offset preserved; rubber-band at the canvas edge instead of a hard stop.

## Reduced motion

Replace the current global kill switch with: no transforms or movement; keep opacity and colour
fades ≤150ms so state changes stay legible. Also honour `prefers-contrast: more` (solid borders)
and `prefers-reduced-transparency`.

## Review

Flag on sight: `transition: all`, `scale(0)`, `ease-in`, animation on a shortcut or palette,
UI duration over 300ms, centre origin on an anchored popover, keyframes on a rapid element,
layout-property animation, missing reduced-motion, ungated hover motion. Preferred fix order:
delete → shorten → fix easing → fix origin → make interruptible → move to GPU.
