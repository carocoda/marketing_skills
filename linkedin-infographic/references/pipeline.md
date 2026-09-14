# Render pipeline and technical pitfalls

## How it works

1. `infographic.html` is one self-contained file, exactly 1080x1350 CSS px
   (`html, body { width:1080px; height:1350px; overflow:hidden }`). All motion is
   CSS `@keyframes` on ONE shared timeline (same duration, `linear`/`ease`,
   `infinite`, keyframe percentages as windows).
2. A `window.seek(ms)` harness freezes the whole page at any timestamp, which makes
   rendering deterministic:

```html
<script>
  window.DURATION_MS = 5000; // must match render.py
  window.seek = function (ms) {
    document.getAnimations().forEach(function (a) {
      a.pause();
      a.currentTime = ms;
    });
  };
</script>
```

3. `render.py` (template in `scripts/render.py`) opens the file headless with
   Playwright (viewport 1080x1350, `device_scale_factor=2` for retina), waits for
   `document.fonts.ready` + 400ms, then loops `seek(i/FPS*1000)` + screenshot per
   frame. Cover PNG = `seek(0)`; the poster is static, so t=0 is the neutral poster.
4. ffmpeg assembles:
   - **GIF**: scale to 720 wide, `palettegen=max_colors=160` +
     `paletteuse=dither=bayer:bayer_scale=5`, `-loop 0`. Target under 1 MB.
   - **MP4**: full 1080x1350, `libx264 -crf 18 -pix_fmt yuv420p -movflags +faststart`.
     This is the LinkedIn upload.

Defaults: 20 fps. A 5 s loop for about 4 sections, 6.5 s for about 8 items.

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

- Frame 0 and the last frame must be identical (seamless loop):

```python
from PIL import Image, ImageChops
a = Image.open('frames/frame_0000.png'); b = Image.open('frames/frame_0099.png')
assert ImageChops.difference(a, b).getbbox() is None
```

- Downscale the cover to 555x694 and read it again (feed size).
- Afterwards: `rm -rf frames check*.png`.

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
10. **LinkedIn plays no GIFs.** Uploaded GIFs render as a still. Hand over the MP4
    for LinkedIn and say so explicitly.
11. **Grid rows equalise card heights.** In a 2x2 grid the shorter card gets dead
    space at the bottom. Either balance the text per row or make the card a flex
    column with the visual on `flex: 1`.
12. **`object-fit: cover` crops screenshots.** Use `contain` on a white background
    for UI screenshots; the letterboxing is invisible on a white panel.
