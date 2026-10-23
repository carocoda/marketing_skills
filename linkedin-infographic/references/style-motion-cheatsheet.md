# Style 4: Motion cheat sheet (app-UI poster, Dribbble-style motion)

The look of the most-saved creator infographics on LinkedIn in 2026: a light cheat sheet
that looks like a screen from an app, with numbered rule cards, score bars and a light
that walks through the poster while each card replays its own small animation. Use it
for a **playbook** (what a creator, a brand or a team does that works), a **cheat sheet**
(rules for a tool) or a **teardown** (what lands and what flops, with numbers).

Starting point: `templates/motion-cheatsheet.html`. Everything you change lives in one
`CONFIG` block at the top (colours, rail, subject, title, bar, rules, score, concepts,
source, footer); the engine below it builds the layout and the timeline from that. The
example data in it is fictional.

## Study the references first (10 minutes, worth it)

Before you write the concept, find 3-5 of the best infographics in the niche (save them
from the feed or the creator's profile) and lay them side by side:

```python
from PIL import Image
ims = [Image.open(p).convert('RGB').resize((540, 675)) for p in paths]
sheet = Image.new('RGB', (540 * len(ims), 675), 'white')
for i, im in enumerate(ims): sheet.paste(im, (540 * i, 0))
sheet.save('reference-sheet.png')
```

Read the sheet and write down what they share: the frame, the type sizes, how many cards,
what moves. Copy the level and the patterns, never a layout one to one.

## The look

- **Canvas** 1080x1350, warm off-white (`--bg`) with a faint dot grid. One sans font for
  everything (the template uses Geist), its mono sibling for labels, chips and dates.
- **It looks like an app.** A 62px rail on the left with a logo or a letter, thin line
  icons and one active icon in a soft accent pill, the author's avatar at the bottom.
  Under the title an app-style bar: a search token with the subject's name, two or three
  chips (one solid), and a meta line on the right ("42 posts · last 30 days") with a
  breathing live dot. The frame says "this came out of a tool"; the body still teaches.
- **Title:** two lines, 57px bold, tight tracking, ONE accent word. The subject's avatar
  (104px, white ring) on the left when the poster is about a person.
- **Section headers:** 25px bold in the accent colour, a 15px grey "what this is" line
  on the same baseline.
- **Rule cards** (the signature, 3-5 across): a number badge (ink circle) and a 19px
  title, a 15px body line, a mini-visual panel, a two-cell **WINS / FLOPS** split
  (green on pale green, coral on pale coral, mono labels, 18px numbers) and a bold
  punchline.
- **Score cards:** an icon tile, a label, a big number over its total ("15 /17") and a
  12px progress bar, accent for good, coral for bad.
- **Concept cards:** a thumbnail of the real post on the left, an "× usual" chip, the
  hook in quotes, a hairline, a mono "THE CONCEPT" label and the concept itself in the
  accent colour. This is the "steal it" row: the reader leaves with a template.
- **Footer:** the data line (13px grey: posts, period, metric, what "usual" means) and a
  centred accent pill with the author's photo, NAME • site, plus a follow line.

## The mini visuals (pick one per rule card)

| type | what it shows | moves |
| --- | --- | --- |
| `tiles` | 10 cells, the hits marked ("7 /10 on topic") | the cells light up one by one, the misses shake, the count ticks |
| `steps` | three numbered lines and a mono prompt chip with a caret | the lines grow and the checks tick in order |
| `compare` | two mini posts side by side, one with an image, one text-only | the image fills with colour and its icon pops, "text only" wobbles |
| `freebie` | a post opening with a marker over "(for free)" and a tag | the marker sweeps, the tag pops, the like count climbs |
| `repeat` | the same post twice with the gap and the gain | the second card flies along an arc, the gain chip pops |

Each preset has an `html()` and an `anim()` in the template's `VIS` object. A new visual
is one more entry with the same two functions.

## The motion (this style's exception to hard rules 3 and 4)

The poster is complete at t=0 (the cover is `seek(0)`) and every value is readable for
most of the loop. On one timeline:

1. **A walking glow** (a 2.5px ring in `--bright` with a soft glow) moves card to card in
   reading order with a spring, then fades out before the loop point.
2. **Each card replays its own micro-animation while the glow sits on it:** a quick dip
   (0.18 s) to the start state, then it builds back with a spring. Tiles light up, checks
   tick, score bars fill while their numbers count, a marker sweeps, a concept types
   itself with a caret.
3. **Ambient:** a breathing live dot whose period divides the loop length, and one
   shimmer across the solid chip.

The motion is a pure JS function of time, `window.seek(ms)`, not CSS keyframes:
counting, typing and springs are easier that way and exactly repeatable frame by frame.
The template sets `window.READY = true` once the fonts are in, and render.py waits for it.

Timeline (the template computes it from the number of cards):

```
step   = min(1.45, (duration - 4.4) / rule cards)   seconds per rule card
rule k = 0.55 + k * step
score k = after the last rule + 0.25 + k * 0.42
concept k = after the last score + 0.2 + k * 0.95
end    = last concept + 1.05                         must be <= duration - 0.35 (console warns)
```

With 5 rule cards, 3 score cards and 2 concepts a 12 s loop fits. More cards: raise
`duration`, but keep it at or under 12.5 s so the LinkedIn GIF stays under 250 frames
at 20 fps.

## A playbook that lands (the content pattern)

The poster is only as good as the analysis under it. The pattern that worked:

1. Pull the subject's last 30 days of posts with their engagement (reactions plus
   comments) and take the **median as "usual"**. Leave posts under a day old out.
2. Group the posts by a few honest labels (topic, format, opener, visual or not) and
   count, per group, how many beat the usual post. That gives the WINS / FLOPS numbers
   and the score bars.
3. The **flops are the juicy part.** "Her opinion posts beat her usual 3 times out of 12"
   is the line people screenshot. Give the flops their own score cards.
4. Each rule is a thing the reader can do tomorrow, in four words for the punchline
   ("Pick a lane."). No soft advice.
5. The concept row takes the two biggest posts and names the **concept** behind each,
   so the reader can reuse the idea in their own niche without copying words.

Every number on the poster comes from that analysis file. Write the data line in the
footer so the method is on the poster.

## Copy limits (or the narrow cards overflow)

- Rule title ≤ 18 characters, body ≤ 60, WINS/FLOPS label ≤ 8, value ≤ 6, punchline
  ≤ 2 lines.
- Score label ≤ 30 characters. Concept hook ≤ 60, concept ≤ 55.
- Nothing below 13px on the 1080 canvas. Check the cover at feed size (555 wide).

## Checklist

- Cover (`seek(0)`) is the complete poster: all numbers there, no card mid-animation.
- Read a frame inside each card's window (crop the row), plus the last frame.
- The seam check from render.py says OK (mean difference last vs first frame under 1).
- The LinkedIn GIF has at most 250 frames (render.py prints the count) and is under the
  scheduler's size limit (10 MB is safe).
- The data line names the period, the metric and what "usual" means.
