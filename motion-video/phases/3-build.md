# Phase 3: Build the page (motion.html)

`motion.html` is the whole picture: one page where `seek(t)` computes every style from the time `t`. Rendering means
calling `seek(t)` and taking a screenshot, over and over, in parallel. Keep it that way.

Open it in a browser to watch it play (no sound): `motion.html?w=1920&h=1080`. Add `&t=12.3` for a still, `&debug`
for the beat and bar counter. The look is in `references/default-style.md`, the numbers in
`references/motion-rules.md`, every template state and more recipes in `references/state-library.md`.

## Anatomy

The comment at the top of the script lists the names; search for them.

| Block | What it is | For a new video |
|---|---|---|
| `BRAND` | colours by role, fonts, border, shadow, corner scale, logo text, dot grid | set from the profile |
| `COPY` | every word on screen | rewrite |
| `BEATS`, `T`, `B(n)` | the grid: `B(9)` is beat 9 in seconds. `T` = whole frames | set from `beats.py` |
| `stepResp`, `SP`, `Track`, `vis` | closed-form springs, named spring settings, multi-key tracks, layer windows | keep |
| `S_SHAPE` | the one shape: `[beat, [x, y, w, h, radius], spring?]` in world px | rewrite |
| `S_BG`, `S_ZOOM`, `S_CAM` | its colour, the camera zoom, the camera focus point per state | rewrite |
| `S_KICK`, `S_ROT` | zoom kicks and tilt kicks on big hits (the opening) | adjust |
| `S_LIFT` | the whole shape hovering (+1) and pressed (−1) when the cursor clicks it | rewrite |
| `RIPPLES`, `BURSTS`, `HL*`, `SLAP`, `DOODLES` | the opening kit | keep, change the words |
| `ICHIPS` … `DAY_ON` | the middle states of the template | replace with yours |
| `STICK`, `ARROW` | the CTA kit: offer sticker, arrow nudge | keep, change texts |
| `window.SFX` | every UI sound as `[beat, kind]` | one per visible event |
| `buildCursor` | `MOVES` `[b0, b1, x, y, arc]` and the click beats | rewrite |
| `init()` | fills the copy, builds lists, chips and tabs, measures text after the fonts load | extend |
| `seek(t)` | camera, dots, shape, then one block per state in story order, then captions and the cursor | rewrite the middle |

All times in the tracks are **beats**, not seconds. `Track` sorts its keys and wraps them modulo `T`, so a key at
beat 63.4 keeps acting at beat 0.1: that's what makes every value loop perfectly.

## Brand first

Set `BRAND` from the profile before you build states: fonts change every text width, and a layout tuned in one font
overflows in another. Colours are roles (`canvas`, `ink`, `light`, `a1` to `a4`), so a brand with one strong colour
puts it in `a1` and quieter tints in the others. A local font file goes in `assets/fonts/` with `src` instead of
`google` (no internet needed to render). See `references/default-style.md` for shape languages.

## Placement

- Content **inside the shape** (clipped by it) is a `.c` child of `#shape`, positioned with
  `place(el, x, y, {ax, ay, s, rot})` in world px, with the origin at the centre of the stage. A window 700 wide has
  its left edge at x = -350.
- Things **on top of or outside the shape** (stickers, tags, doodles, the url) are `.w` children of `#world`,
  positioned with `placeW` in the same world px. They move with the camera but aren't clipped.
- `show(el, v, blur)` sets opacity `v` and a blur of `(1 - v) × blur` px. `swap(v)` is the matching scale
  (0.965 → 1). `popShow(el, s)` is the opacity for a pop spring.
- `pressOff(l)` and `pressShadow(l)` are the hover and press: hover lifts up-left and grows the shadow, press pushes
  down-right into it. The far corner of the shadow never moves.

## Add a state (the recipe)

1. **The shape.** A key in `S_SHAPE`: `[37.75, [0, 0, 640, 112, 56]]`. Pick the size so the camera can make it 820
   to 1400 px wide and at most about 760 px tall on a 1080p screen: zoom ≈ target width / w. (The page also caps the
   zoom so the shape never leaves the frame in 9:16 or 1:1.) Shift x, y to make room for stickers or to line up with
   the next state.
2. **Colour and camera.** Keys in `S_BG` (light for cards, ink for terminals and title pills, an accent for moments),
   `S_ZOOM`, and `S_CAM` when the focus isn't the shape's centre.
3. **The content.** Elements in the HTML (`class="c …"`) or made in `init()` for lists. CSS classes at the top, using
   the tokens (`var(--a3)`, `var(--bw)`, `var(--sh)`).
4. **Its window.** In `seek(t)`, in story order:
   `const v = vis(t, 38, 43.75, 0.22, 0.12, 0.06); show(EL.x, v); place(EL.x, -286, 0, { ax: 0, s: swap(v) });`
   The layer comes in a hair after the morph key (0.05 to 0.3 beat) and leaves on the next morph key, so text never
   swaps inside a shape that's still moving.
5. **Choreography.** Chips pop (`popTrack`), values move (`Track`), lists tick, text types: keyed on the beats of the
   words from `build_audio.py --table`.
6. **The cursor.** A move in `MOVES` that arrives at least half a beat before the click, the click beat in `clicks`
   (the press starts 0.15 beat before). Clicking the shape itself: `S_LIFT` keys (hover 0.8 about half a beat before,
   press -1 at 0.12 before, 0 on the beat). A drag: a held press `[start, end]` and a value computed from
   `cursorWorld(t)` while it's held (recipe in `state-library.md`). Park the cursor within about 300 world px of the
   centre so it stays on screen in 9:16.
7. **Sound.** A `[beat, kind]` in `window.SFX` for every visible event: `click`, `pop`, `key`, `tick`, `toggle`,
   `grab`/`drop`, `enter`, `ding`, `slam`, `stamp`, `whoosh`, `pluck0-3`, `clink`. New kinds go in the bank in
   `build_audio.py`.
8. **Look.** `python3 render.py sheet 31 31.2 31.5 32` and `python3 render.py strip 30.9 31.4` (the morph halfway),
   then `python3 qa.py`.

## Photos and logos

A real photo of a person: cut it out (any tool), `python3 sticker.py assets/x-cutout.png assets/x-sticker.png
--outline "#F8B2D6"`, put it in the page as `<img class="w" id="…">` inside `#world`, add its id to `DECODE` in the
boot code (so it has loaded before the first frame), and pop it with a spring. A tool or partner logo: an inline SVG
or an `<img>` in a small white chip with the name next to it. Only logos the user may use.

## Another format

Set `canvas` in `project.json` (or start with `new_project.py --format 9:16`). The page scales the camera to the
format and caps the zoom so the shape fits, moves the logo and HUD, and places captions. That gets you a working
first pass, but the template's layouts were drawn for 16:9: look at every beat again, and read
`references/formats.md` for safe zones.

## Before you call it built

- `python3 render.py beats` runs without JavaScript errors (it stops on the first one).
- `python3 build_audio.py` has placed the sounds of your new events.
- `python3 qa.py` passes. Then go to phase 4.
