# Render pipeline and technical pitfalls

## How it works

1. `infographic.html` is one self-contained file, exactly 1080x1350 CSS px
   (`html, body { width:1080px; height:1350px; overflow:hidden }`).
2. It exposes `window.seek(ms)`, which freezes the whole page at any timestamp. That
   makes rendering deterministic. Two harnesses, pick by style:

   **CSS harness (styles 1-3).** All motion is CSS `@keyframes` on ONE shared
   timeline (same duration, `linear`/`ease`, `infinite`, keyframe percentages as
   windows), and seek pauses every animation at the same time:

```html
<script>
  window.seek = function (ms) {
    document.getAnimations().forEach(function (a) {
      a.pause();
      a.currentTime = ms;
    });
  };
</script>
```

   **JS harness (style 4).** The motion is a pure function of time: `seek(ms)` sets
   every style from `t` and nothing else (no timers, no state carried between
   frames). Counting numbers, typing, springs and a ring that follows the cards are
   all easy this way. Measure the layout once after the fonts are in, then flag it:

```js
window.seek = ms => seekT(((ms / 1000) % DUR + DUR) % DUR);   // wrap into one loop
window.READY = false;
document.fonts.ready.then(() => { measureLayout(); window.seek(0); window.READY = true; });
```

   Helpers the template uses: an ease-out `eo`, an ease-in-out `eio`, a damped spring
   `spr(dt, stiffness, damping)`, and `track(keys, t)` that moves a value from key to
   key with that spring (the walking ring).
3. `scripts/render.py` opens the file headless with Playwright (viewport 1080x1350,
   `device_scale_factor=2` for crisp text), waits for `document.fonts.ready` and for
   `window.READY` if the page sets it, then loops `seek(i / 30 * 1000)` + screenshot
   for every frame at 30 fps. Cover PNG = `seek(0)`, which is the complete poster.
4. ffmpeg assembles four files:
   - **LinkedIn GIF**: 1080x1350, `fps = min(20, 250 / seconds)` so it never goes over
     LinkedIn's 250 frames, `palettegen=max_colors=256:stats_mode=diff` +
     `paletteuse=dither=bayer:bayer_scale=4:diff_mode=rectangle`, `-loop 0`.
   - **MP4**: 30 fps, `libx264 -crf 18 -pix_fmt yuv420p -movflags +faststart`.
   - **Email GIF**: 12 fps, 720 wide, 160 colours, same diff palette. Target ~1 MB.
   - **Cover PNG** at 2x.
5. It prints a seam check (mean pixel difference between the last and the first
   frame), the LinkedIn GIF's frame count and every file size.

```bash
python3 render.py --slug my-poster --duration 5000              # calm accent poster
python3 render.py --slug my-poster --duration 12000 --out ./renders
python3 render.py --slug my-poster --duration 5000 --keep-frames   # keep _frames/ for QA
```

Loop lengths: 5 s for about 4 sections and 6.5 s for about 8 items (calm accent);
12 s for a full motion cheat sheet (240 frames in the LinkedIn GIF).

## Fonts and assets

- Google Fonts via `<link>` (Playwright has network access): Poppins (titles),
  Inter (body), JetBrains Mono (chips, mono labels). Wait for `document.fonts.ready`.
- Local images (`mascot.png`, `author.jpeg`, `shot_*.png`) via relative paths in
  the same folder.

## Visual QA (never skip)

- Read the cover PNG at full size. Checklist: canvas filled to the bottom (footer
  pill visible, no empty band), nothing clipped, no overlapping text, title accent
  word in the brand colour.
- Read 2-3 frames in the middle of animation windows. Crop with PIL:

```python
from PIL import Image
Image.open('frames/frame_0050.png').crop((x1, y1, x2, y2)).save('check.png')
```

- The seam check render.py prints must say OK. A calm-accent poster should even be
  pixel-identical between the last and the first frame:

```python
from PIL import Image, ImageChops
a = Image.open('_frames/frame_0000.png'); b = Image.open('_frames/frame_0149.png')
print(ImageChops.difference(a, b).getbbox())   # None = identical
```

  A poster with ambient motion (a breathing dot) is never pixel-identical; there the
  mean difference under 1 is the test.
- Downscale the cover to 555x694 and read it again (feed size).
- Afterwards: delete `_frames/` (render.py does it unless `--keep-frames`) and the check PNGs.

## Technical pitfalls (all met in practice)

1. **Dash-pattern wrap-around.** A dash travelling a path via `stroke-dashoffset`
   repeats every `dasharray` period. If the gap is shorter than the path you see a
   ghost dash at the path end before the pulse has started. Fix: make the gap
   LONGER than the path (`pathLength="100"` + `stroke-dasharray: 14 186`).
2. **Round linecap dot.** With `stroke-linecap: round` and `dashoffset == dasharray`
   a round cap dot still renders at the path start. Fix: overshoot the resting
   offset slightly (e.g. `100.8`, or rest at 15 for a 14-dash) so the dash sits
   fully outside the path.
3. **Leftover inline `animation-delay`s.** When converting a poster from entrance
   animations to a shared-timeline loop, REMOVE inline `style="animation-delay:..."`
   from elements that get a loop animation. The delay shifts their keyframe
   windows and desynchronises the cycle.
4. **Transforms on inline elements do nothing.** `<span>`s need
   `display:inline-block` (flex and grid items are already fine).
5. **Transforms on SVG child elements** need `transform-box: fill-box` plus a
   `transform-origin`, otherwise they rotate or scale around the SVG origin.
6. **Responsive SVG overlay** (marching-ants rect over a card): give the SVG
   `position:absolute; inset:-6px` and set the rect geometry via CSS. `x`, `y`,
   `rx` and `width/height: calc(100% - 3px)` are animatable CSS geometry
   properties in Chromium.
7. **Seamless offset maths.** Per loop, `stroke-dashoffset` must shift an EXACT
   multiple of the dash period (period 15 → `to { stroke-dashoffset: -75px }` is
   5 periods), otherwise the loop hitches.
8. **GIF weight.** Continuous whole-poster motion (mascot idle etc.) roughly
   doubles the GIF because every frame differs. The calm single-highlight concept
   keeps GIFs around 0.4-0.6 MB.
9. **Odd dimensions break yuv420p.** Keep width and height even (1080x1350 is fine).
10. **GIFs on LinkedIn: frames, not megabytes.** LinkedIn takes GIFs up to 250
    frames. A 30 fps GIF of a 12 s loop has 360 and fails; render.py caps the
    LinkedIn GIF at 250. Some URL importers also sum the megapixels of every frame
    (often a 40 MP cap), so upload the file directly. Check the first live post
    (see `publishing.md`).
11. **Grid rows equalise card heights.** In a 2x2 grid the shorter card gets dead
    space at the bottom. Either balance the text per row or make the card a flex
    column with the visual on `flex: 1`.
12. **`object-fit: cover` crops screenshots.** Use `contain` on a white background
    for UI screenshots; the letterboxing is invisible on a white panel.
13. **Springs and the loop seam.** A spring that is still settling at the loop
    point makes a visible jump. Let every per-card animation finish, and fade the
    walking ring out, at least 0.35 s before the end of the loop. The style-4
    template warns in the console when the timeline runs too long.
14. **Measure after the fonts.** Card positions measured before the web fonts load
    are off by a few pixels, and the ring then sits next to its card. Measure in
    `document.fonts.ready`, and let render.py wait for `window.READY`.
15. **Ambient periods must divide the loop.** A breathing dot with a 1.2 s period
    fits a 12 s loop ten times; a 1.3 s period jumps at the seam.
