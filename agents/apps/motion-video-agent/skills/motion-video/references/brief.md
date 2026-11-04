# Brief, story shape and ban list

## Brief template (fill every field; GOAL first, then TIME)

```
GOAL:     one sentence: what the viewer feels or does after watching
OUTPUT:   engine, width×height, formats (16:9, 9:16, 1:1, GIF)
TIME:     seconds × fps = frames; loops? (yes/no)
LOOK:     palette as hex, ONE accent colour, typeface, sizes, weights
MOTION:   cubic-beziers by name, springs as damping ratios, durations in frames
SHOTS:    frame ranges, one hero move each, transition (default: cut)
CAMERA:   for 3D: object, fov, the single camera move
IDENTITY: what may never change (logo geometry, product colours, copy)
ASSETS:   real logo, screens, numbers (paths in assets/)
BANNED:   the ban list below, plus this piece's own
QA:       stills at named frames, contact sheet, owner approval, then full render
```

## Story shape for a 16 s product film

| Seconds | Beat |
| --- | --- |
| 0–2 | Hook |
| 2–5 | Problem, shown not told |
| 5–9 | Reveal through a real interaction |
| 9–13 | Proof: one screen or one number |
| 13–16 | Logo and a readable call to action |

Scale the beats for other lengths; something new arrives every 2–4 s.

## Adjectives → numbers

| Word | Spec |
| --- | --- |
| premium | roughness 0.38, clearcoat 0.35, ease-out-quint, no overshoot on text |
| modern camera | fov 30, never parked, one push-in on ease-out-expo at 2.0 s |
| make it pop | scale 1.0 → 1.08 → 1.0 over 6 frames, peak on the beat |
| snappy | entrances 8–12 frames at 30 fps, exits 40–50% shorter |
| calm | ≤ 1 hero move per 3 s, springs at damping ratio ≥ 0.9 |

## Ban list (name the defaults; grow it after every render)

- Centred title on a gradient; everything fading in together; fade-and-slide-up on everything;
  every layout centred.
- Purple or blue gradients; glow, bloom, neon, lens flares.
- Decorative particles; corner labels and frame borders.
- Generic turntables; text that moves while it is being read; dead time.
- More than one hero-coloured or glowing element in a frame.

## Sharpness block (add for 3D or blur-heavy pieces)

- Text and UI on their own layer, drawn after depth of field and blur.
- At least 1 texel per output pixel: capture at 2× (3× for close-ups).
- Grain ≤ 0.02, chromatic aberration ≈ 0.0025, max blur ≈ 0.006.
- PNG frames; encode at crf ≤ 18 (16 default, 14 for detailed 3D). Check text at 200%.

## Assets block

- Give the product URL; capture real screens, logo and assets into `assets/` with a headless
  browser, and list them up front.
- Never redraw UI from imagination. Real metrics only.
- If a real asset is missing, stop and ask. Never draw a convincing fake.
