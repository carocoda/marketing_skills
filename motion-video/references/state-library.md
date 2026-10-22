# State library: the template's states, and recipes for more

Beats are the template's (120 BPM, 64 beats). Names in `code` are what to search for in `templates/project/motion.html`.
Shape sizes are `[x, y, w, h, radius]` in world px; zoom is `S_ZOOM`.

## The opening kit (beats 0 to 7): reuse in every promo

- **The tile.** A 120×120 tile (radius 26) in `a1` with `COPY.tile` in mono 34 (`seedLabel`), zoom 2.7. It is also
  the last state, so the video loops through it. The cursor hovers it (`S_LIFT` +1 at 63.4) and presses (0.1).
- **The click (0.25).** The shape blows open to a 700×420 window with `SP.burst`; colour to `light`; zoom 1.5 on the
  burst spring; a zoom kick of -8% and a tilt kick of -3.2°; a ripple through the dot grid; three discs (1650, 1220,
  820 px) expand behind it and collapse again (`BURSTS`). Sounds: `click` + `whoosh`.
- **The window chrome.** Three dots that bounce on the beat, a mono label (`COPY.label`), a rule.
- **The headline** (`HL1`-`HL3`, `HL_BLOCK`): the first words pop (0.6, 46 px), an accent block wipes in (1.35)
  behind the key word, which slams in from 120% (1.5, 92 px, `slam`, ripple, zoom kick +7%, tilt +1.2°), then the
  last word (3.1). All leave fast at 7.0. Keep the words short: about 9 letters fit at 92 px.
- **The sticker** (`SLAP`): slaps on at 4.75 (`stamp`, ripple, kick), then rides along to the corner of the next
  state and shrinks.
- **Doodles** (`DOODLES`): pop at 2.5, 3.5, 4.25, 5.5 around the window and float with a slow 6 px sine.

## The middle (7.25 to 43.75): replace with your own, copy the mechanics

- **Title pill** (7.25, ink 560×112, zoom 1.75): the title in canvas colour, centred; the sticker rides to its corner.
- **Info pill with chips** (11.5, light 640×134, zoom 1.6): a line of facts, then chips popping on their words
  (`ICHIPS` at 13, 14, 15). Good for date, place, time, or what's included.
- **Terminal** (17.75, ink 800×300, zoom 1.75): a header that kicks to `a1` when typing ends, a prompt typed at 14
  characters per beat with key sounds, `enter`, "● rendering" with animated dots, then a done line with a `ding`.
  Shows that something gets made. Look at the last typed frame: long prompts get cut off.
- **Tab bar → card** (25.75 and 27): the indicator grows from a dot on the first tab (`IND_*`); a click on the tab
  opens the card under it (560×460 at y 190, zoom 1.65, `S_CAM` y 190). The tabs stay at the card's top.
  - **Toggle** (click 29.4): a plain "before" slide (Arial, placeholder boxes) becomes an on-brand "after" slide
    with bars growing and a sticker popping. The knob is a two-edge pill (`DK_L`, `DK_R`) on lead and trail
    springs, so it stretches as it moves.
  - **Second tab** (click 32.5): the indicator stretches over (leading edge fast, trailing slow), a chart's bars grow
    a quarter beat apart with rising plucks, "✓ adds up" pops (34), and a tooltip appears while the cursor rests on
    the first bar (34.75).
- **Week pill** (37.75, light 640×112, zoom 2.1): a title and five day circles ticking to checks a quarter beat apart
  (`tick`). Shows something that repeats.

## The CTA kit (43.75 to 64): reuse in every promo

- **The button** (43.75, `a1` 300×84, radius 16, zoom 2.9, focus y 34): asks the question (`COPY.ask`) on the spoken
  question, swaps to the CTA with an arrow (46) on the words.
- **The offer sticker** (`STICK`, 46.75): tilted 8°, wiggles once (54.5, 55). The only place a price appears.
- **The url** (47.5, underlined mono) and the **date line** (48.5) under the button.
- **The click home**: the arrow nudges (`ARROW`), the cursor lifts the button (56.8), presses (57.38), clicks
  (57.5), and the shape turns back into the tile (57.6) with the cursor settling on it (58 to 59.3).

## Recipes for more states (built in earlier videos, not in the template)

- **Hosts or team as photo stickers**: under a title pill, a cut-out photo sticker (`sticker.py`) pops up from behind
  the shape (spring 0.4/0.7, a -2° tilt), anchored at its bottom, with name tags popping exactly on the spoken
  names. Check who stands where before the tags go on.
- **A player with play/pause**: a 480×372 card with a thumbnail, a neo-brutalist round play button that gets pressed
  while its icon morphs play → pause (two quads interpolated point by point), a timecode that runs.
- **Scrubbing (direct manipulation)**: the cursor grabs the timeline knob (`grab`), and while the press is held the
  knob's value is the cursor's position: `clamp((cursorWorld(t)[0] - x0) / w, 0, 1)`. Clips appear on the track as
  it passes, a chip counts up, release with `drop`. Then the round knob can grow into the tab indicator of the next
  state: a nice handover.
- **⌘K palette** (white 560×334): a placeholder, four rows with colour swatches and mono hints; a word is typed a key
  per quarter beat; the shape shrinks to 560×160 as the list filters and the matching row slides up; the selection
  pops; the enter key is pressed.
- **A clock with tips**: a ring fills hour by hour (`stroke-dashoffset` on an SVG circle) while the hour label swaps,
  and a "TIP" chip with three short tips swapping on the words.
- **A toast**: two glasses tilt in and clink (two inharmonic tings 14 ms apart, the `clink` sound).

## Ideas that fit the same mechanics

- A chat or community feed: messages popping in on the beat, a reaction chip, a counter ticking up.
- A photo card for recaps, swapped by clicking arrows (only photos of people who agreed).
- A calendar or agenda pill for a series of sessions.
- A form or checkout-like state ending on the same CTA kit.
- A pricing card with a toggle between monthly and yearly.

Build them from the same parts: a shape key, a content window, pops on the words, a cursor that operates it.
