# Motion numbers

Put these in the studio's `motion.js` and use only the tokens in scenes.

## Easing (cubic-bezier)

| Name | Values | Use |
| --- | --- | --- |
| ease-out-expo | 0.16, 1, 0.3, 1 | Reveals |
| ease-out-quint | 0.22, 1, 0.36, 1 | Premium entrances |
| ease-in-out-quart | 0.76, 0, 0.24, 1 | Moves and camera |
| ease-in-expo | 0.7, 0, 0.84, 0 | Exits |
| ease-out-back | 0.34, 1.56, 0.64, 1 | Playful pops |

- Exits are 40–50% shorter than entrances.
- Linear only for rotation, progress bars and loop phase.
- Entrances animate 2–3 properties together (e.g. opacity + y + scale), never opacity alone.

## Springs

- Damping ratio ζ = damping / (2·√(stiffness·mass)).
- ζ 1.0 no bounce; 0.7–0.85 premium; 0.4–0.6 playful; < 0.3 cartoonish.
- Remotion's default is ≈ 0.5; react-spring's is 1.0.
- Opacity and colour never bounce.
- Closed form (underdamped, x from 0 to 1, ω = √(k/m)):
  `x(t) = 1 − e^(−ζωt)·(cos(ω_d t) + (ζω/ω_d)·sin(ω_d t))`, with ω_d = ω·√(1 − ζ²).

## Durations

- At 30 fps one frame ≈ 33 ms; at 60 fps ≈ 17 ms.
- UI feedback 100–200 ms; UI moves 200–500 ms.
- Stagger: letters 1 frame, words 60–120 ms, list items 40–80 ms.
- Text holds 0.3 s per word + 0.5 s, with a slow 2% push during the hold.

## Hierarchy

- One hero move per shot.
- Secondary moves travel 50–70% as far and start 100–200 ms later.
- Ambient motion stays under 5% of the hero's travel.
- Something new every 2–4 s.

## Beat grid

- Frames per beat = fps × 60 / BPM (15 frames at 120 BPM, 30 fps).
- Round each beat's frame separately from its exact time, so error never accumulates.
- Cut on beats; change layouts on bars. Detect beats with librosa
  (`librosa.beat.beat_track`, then `librosa.frames_to_time`).

## Accessibility and phones

- Text contrast ≥ 4.5:1.
- No more than 3 flashes per second.
- Exaggerate key poses 10–30% for phone-sized viewing; check readability at 360 px wide.
