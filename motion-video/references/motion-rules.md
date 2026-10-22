# Motion rules: the numbers behind the look

## Direction

- **One shape, never cut.** Every state is the same element morphing width, height, radius and colour. Content swaps
  with a short blur. Stickers, tags and doodles live around it, but the shape is always the stage.
- **The cursor drives every change**: it clicks (and the thing clicked is pressed), it drags (and the value follows
  it), it types, it hovers.
- **Something happens on every beat**, and the opening is over the top.
- **The camera zooms so each state fills the frame**, kicks on big hits, and breathes a little.
- **The last frame is the first frame.**

## Springs (closed form, so every value is a pure function of t)

`stepResp(age, resp, damp)` is a damped spring's step response: `resp` is the undamped period in seconds
(ω = 2π / resp), `damp` is ζ. A `Track` sums one spring per key change, sorted and wrapped modulo `T`.

| `SP.` | resp, ζ | ω | For |
|---|---|---|---|
| morph | 0.48, 0.80 | 13 | the shape's position, size, radius: a hair of overshoot |
| cam | 0.70, 0.92 | 9 | camera zoom and focus: nearly as fast as the shape, or big morphs overflow the frame |
| color | 0.18, 1.0 | 35 | colours and on/off states: fast, never overshoots (no muddy in-betweens) |
| pop | 0.36, 0.76 | 17 | chips, tags, stickers, items landing |
| slam | 0.30, 0.55 | 21 | headline words and stickers slamming in: big overshoot |
| burst | 0.52, 0.62 | 12 | the window blowing open, the zoom of the opening |
| hover | 0.26, 0.86 | 24 | lifting before a click |
| press | 0.12, 0.92 | 52 | pressing down |
| soft | 0.34, 0.90 | 18 | releases, exits, gentle returns |
| lead / trail | 0.26, 0.80 / 0.46, 0.86 | 24 / 14 | the two edges of a liquid indicator or toggle knob |
| bar | 0.44, 0.78 | 14 | chart bars growing |
| slide | 0.40, 0.82 | 16 | list rows moving up |
| snap | 0.05, 1.0 | 126 | invisible resets |
| kickIn / kickOut | 0.06, 1.0 / 0.42, 0.50 | 105 / 15 | the attack and the wobbly release of a zoom or tilt kick |

## Timing

- **Morph keys sit on quarter beats** (7.25, 17.75, 25.75) so the big motion reads on the beat. A morph caused by a
  click starts on the click (0.25, and 57.6 after the click at 57.5).
- **Content leaves fast and arrives once the shape has mostly landed**: `vis(t, bIn, bOut, 0.2-0.24, 0.12,
  0.02-0.1)` in, blurred (7 px) from 96.5% scale; out in 0.12 s. The window opens 0.05 to 0.3 beat after the morph
  key. Never swap text inside a container that's still morphing.
- **Pops land on beats or half beats**; lists land every quarter beat (days, bars).
- **Typing**: a key per quarter beat for short words; a steady 14 characters per beat for a long prompt, with a key
  sound on every quarter beat.
- **The cursor arrives 0.5 to 1.5 beats before a click.** Hover about 0.5 beat before, press starts 0.15 beat
  before, the click (and its sound) is on the beat.
- **Words and things together**: the thing appears within half a beat of the word that names it.

## Camera

- **Zoom** so the shape is 820 to 1400 px wide and at most about 760 px tall on a 1080p screen: zoom ≈ target / w.
  Template: window 700 → 1.5, pills 560 to 640 → 1.6 to 2.1, card 560×460 → 1.65, button 300 → 2.9, tile 120 → 2.7.
  The page caps the zoom at 92% of the frame width and 80% of its height, for other formats.
- **Focus** (`S_CAM`) shifts when a state sits off-centre or needs room for stickers (the card below the tabs).
- **Breathing**: the zoom is multiplied by `1 + 0.012 sin(2π t / (T/4))`.
- **Kicks** on big hits, in the opening only: zoom -8% on the click, +7% on the headline slam, +6% on the sticker;
  tilt -3.2°, +1.2°, -1°. Each with `kickIn` and back with `kickOut`.
- Never `will-change` or a scale hack on the world: text renders soft.

## The shape

- One `#shape`: a border, overflow hidden, radius clamped to half the smaller side, at least 40 px.
- Its shadow follows hover and press (`S_LIFT`): hover lifts up-left and the shadow grows, press pushes into it.

## Cursor

- `MOVES`: `[b0, b1, x, y, arc]` in world px. Minimum-jerk easing from where it was, with a sideways arc
  (`arc × distance × sin(π e)`) so it moves like a hand. Alternate positive and negative arcs.
- It is evaluated over the previous and the current loop, so a move across the loop point continues at t = 0.
- Drawn in screen space at a constant size; it presses to 86%.
- It ends on the tile and is still across the seam (`qa.py` wants under 30 px/s).

## Sound events

Every visible event gets a sound, from the same `window.SFX` list the picture is timed on:

| kind | when |
|---|---|
| `click` | a click (the tile, tabs, buttons) |
| `whoosh` | a big morph, the opening click |
| `slam` | a headline word slamming in (bass impact + click) |
| `stamp` | a sticker slapping on |
| `pop` | chips, tags, doodles, stickers, the url |
| `key` | every typed key (random pitch and level per key) |
| `tick` | small steps: days ticking off, a clock hour, a check |
| `enter` | the enter key |
| `toggle` | a switch |
| `grab` / `drop` | the start and end of a drag |
| `ding` | "done" |
| `pluck0`-`pluck3` | bars landing, rising notes in the song's key |
| `clink` | glasses touching |

## Motion blur and the loop

- 4 subframes per frame over a full-frame shutter, averaged with ffmpeg `tmix`: every spring gets real blur.
- `T` = `BEATS` × beat in whole frames. Everything wraps: tracks, windows, the cursor, the audio.
- The last state is the first (the tile, same place, size, colour and zoom); everything from the end is gone before
  the seam; the cursor is home. `qa.py` measures last frame → first frame (want < 1.5).
