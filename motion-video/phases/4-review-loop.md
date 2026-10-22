# Phase 4: The inner review loop (before anyone sees it)

You are the first viewer. Most notes a requester gives could have been caught earlier, so look at every beat before
you render, and fix it before you send it.

```
repeat, at most 3 rounds:
  python3 render.py beats                 a still per beat -> stills/contactsheet.png (8 per row)
  open the sheet (and single stills) and go through the checklist
  python3 render.py strip <t0> <t1>       12 frames across every morph and every big hit: bugs live halfway
  python3 render.py sheet <t> <t> ...     zoom in on anything doubtful
  python3 qa.py                           fonts, grid, sounds, loop, facts, copy, price, voice, mix
  fix, and write down what you fixed
then
  python3 build_audio.py && python3 render.py preview     30 fps, with sound: timing against the voice
```

Look at the images themselves. What you meant and what renders are different things, and the code won't tell you
that a label overflows or a sticker covers a face.

## Checklist

**The first four seconds**
- The click on the tile really opens something: bursts, ripple, slam, kicks. It grabs attention straight away.
- The headline reads at a glance, and no price shows yet.

**Framing**
- Every state fills the frame without touching the edges, also halfway through a big morph.
- Stickers and tags stay in frame and never cover faces or the key text.
- The logo chip and the HUD lines never collide with content or captions.
- 9:16 and 4:5: everything that matters sits inside the safe zone (`references/formats.md`).

**Legibility**
- Text is at least 13 px in world units at zoom 2 or more (about 26 px on a 1080p screen), more for anything read in
  passing. Mono labels 13 to 17 px, titles 22 to 40 px, headlines 46 to 92 px.
- Nothing overlaps: chips, tags, pills, tooltips. When a tooltip covers a title, lower the bars; don't shrink fonts.
- No text is cut off by the shape (a long typed prompt is the usual one: widen the shape or shorten the text, and
  look at the last typed frame).
- Text is centred where it should be (size a pill to its text).

**Beat and sync**
- Something happens on every beat; no dead stretches.
- Clicks, pops and ticks land on beats. The sound events sit on the same beats as the visuals (same list).
- Every word that names a thing lands within half a beat of it appearing, and the voice never describes something
  that isn't on screen yet.

**Cursor**
- On target at every click and drag start, and there at least half a beat early.
- Not parked on the text being read.
- Home on the tile and still for at least a beat before the loop point.

**Copy and facts**
- Date, time, place, price and url match `project.json` → `facts` and the user's source everywhere they appear.
- Name tags sit on the right person.
- No em-dashes, no banned words, the right language everywhere.

**Colour**
- No muddy in-between colours during a colour change: the colour spring is fast and doesn't overshoot (`SP.color`).

**Captions** (if on)
- One or two lines, never covering the content or the HUD; the highlighted word follows the voice.

**Loop**
- The last frame flows into the first (qa.py measures it), and anything that "happened" (typed text, a pressed
  toggle) is reset by then.

## When to stop

Stop when the checklist is clean and `qa.py` passes, or after three rounds. Then render and show it, and name what
you're unsure about in the changelog. The requester's eye is part of the process, not a failure of it.
