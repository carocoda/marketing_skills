# Graphics kit: what `overlay.html` can draw

`overlay.html` draws every graphic on top of the video. It is a pure function of time: `seek(t)` sets every style from
`t` alone (no CSS animations, no timers, no `Math.random()`). That is why Playwright can render the frames in six
workers at once. `build.py plan` turns every event into output seconds (`t0`, `t1`) and hands them to the page.

## The look comes from the brand

Colours, fonts, the logo or brand name, the CTA and the URL come from `brand.json` (next to the ad folders) and
`edit.json` "brand" (see `edit-json.md`). The default look is bold and graphic:

- **Colour tokens:** `bg` (end card background), `ink` (text, borders, shadows), `paper` (white cards), `accent`
  (highlights, date card, active caption word, end card button), `accent2` (ticks, price, time chip), `accent3`
  (stamp, title highlight, arrow), `accent4` (soft cards). An event's `color` takes a token name or a hex code.
- **Fonts:** a `display` font for headings and captions and a `label` font for small caps labels. Google Fonts by
  name, or a local file.
- **Style:** `border` 4 px, `shadow` 8 px (hard, offset), `radius` 18 px. Set border and shadow to 0 for a flat,
  softer look.
- Everything enters with a spring (`pop`); nothing slides in linearly.
- The brand tag (logo or name) sits top left for the whole video, until the end card. `"tag": false` hides it.

## Rules from the feedback rounds

- **Visual, not textual.** An opening made of text blocks was "too textual". Show what the speaker says: real
  windows, files, app tiles, logos.
- **Real logos of the tools or partners that are named.** When the speaker names a tool, its logo pops up
  (`logos` in edit.json; use only logos you may use). An anonymous chat bubble said nothing.
- **Real photos, no text on them.** No AI images of people. Photos in their own aspect ratio, popping up one after
  another. The client picks the photos.
- **Text below the chest.** Cards sit in the zone under the face (`zone`, y 1110 in 9:16), never over the face.
  "Tap below" sits even lower (y 1385) so the arrow does not fall over the chest.
- **Cards with key info replace the captions** while they are on screen (date, price, poll, card, stamp, name tag,
  photos, arrow, end card). Chips and windows next to the head leave the captions on.
- **A big hook.** Until the end of `hookbig` the captions are bigger and build up word by word.
- **Facts are right.** Date, time, place and price come from the client or their landing page. A price only shows
  in the variants with the matching flag (`"flag": "offer"`).
- **One thing at a time early on.** In the first five seconds something happens every 0.4 to 0.8 s.

## Event types

Every event lives in `edit.json` under `events`. Start it on a word (`word` + `near`: the word closest to that source
second) or on a time (`from` / `at`). End it with `to` (source second) or `to_word` + `to_near`. `sfx` picks sounds
(see `music-and-sound.md`); some types add their own extra sounds.

| Type | What you see | Fields |
|---|---|---|
| `hookbig` | no picture: big captions that build up | `from`, `to` |
| `logos` | tiles with the logos from `logos`, left and right of the head (more than two: a row lower) | `word`, `to_word` |
| `stamp` | big stamped word that slams in; the font size fits the word length | `text`, `to` |
| `win` | mini window; `role: copy` selects a line (⌘C), `role: paste` gets it flown in on an arc (⌘V) | `id`, `slot`, `role`, `rot` |
| `files` | fan of three documents (XLS, PDF, DOC) | `id`, `slot`, `rot` |
| `apps` | six wobbling app tiles (too many tools) | `id`, `slot`, `rot` |
| `trycard` | white card with icon and label next to the head; gets a tick on `check_word` | `id`, `slot`, `glyph`, `label`, `color`, `rot`, `check_word`, `check_near`, `check_sfx` |
| `bubble` | white speech bubble with an icon tile and a short line (what customers say); can be gathered | `id`, `slot` or `pos` per format (`{"9x16": [x, y, ax], "4x5": [...]}`), `glyph`, `color`, `text`, `maxw`, `rot` |
| `gather` | sucks the windows, files, tiles, trycards and bubbles with these `ids` to the centre | `ids` |
| `aicard` | card with a spark, a title and three mini icons that get ticked | `title`, `to_word` |
| `chat` | avatar with a typing chat bubble | `to` |
| `checklist` | card with a title and rows that get ticked on their word (faded until then) | `title`, `rows` (`[text, word, near]`), `to` |
| `card` | card with a title and a subtitle in a brand colour | `title`, `sub`, `color`, `rot`, `to` |
| `strike` | big word on a white card, crossed out on `check_word`; a `stamp` fits after it | `text`, `check_word`, `check_near`, `check_sfx`, `to_word` |
| `post` | a mock, anonymous feed post with a like counter running up; optional stamp on `stamp_word` | `text`, `likes`, `comments`, `stamp`, `stamp_word`, `stamp_near`, `stamp_sfx`, `to` |
| `date` | big date card that slams in | `kicker`, `title`, `sub`, `to` |
| `timechip` | pill next to the date | `text`, `to` |
| `photos` | the photos from `photos` pop up one after another as a collage (up to four spots) | `to_word` or `to` |
| `nametag` | name tag that slides in from the left | `name`, `role`, `to` |
| `sticker` | a cut-out image (the people, a product) with a label | `image`, `label`, `width`, `pos`, `rot`, `to` |
| `logo` | the brand mark, big, with a small sticker line | `sub`, `to` |
| `poll` | a question with YES/NO; a cursor clicks YES on `tap_word` | `q`, `yes`, `no`, `sub`, `tap_word`, `tap_near`, `tap_sfx`, `to` |
| `price` | price card; a tag with the deadline on `tag_word`, a small tap on `ding_word` | `kicker`, `value`, `tag`, `tag_word`, `ding_word`, `flag`, `to` |
| `arrow` | a label with a bouncing arrow down to the platform's CTA button | `text`, `to` |

Icons for `glyph` (and the app tiles): `mail`, `chart`, `cal`, `chat`, `img`, `board`, `web`, `play`, `clock`, `bot`.

`slot` is a fixed spot next to the head: `L1`, `R1` (high), `L2`, `R2` (lower). The positions per format are in
`LAYOUTS` at the top of the script in `overlay.html`.

### An opening that worked, as a pattern

"You already do a lot with AI" (logos) → "but you still do a lot **yourself**" (stamp) → "copying, pasting, opening
files, jumping between tools" (window, window, fan, app tiles: the screen fills up) → "with AI, for real" (everything
is sucked to the centre) → "AI picks it up" (card with ticks). Make the problem visible, then let the solution land.
A new ad can open differently, but keep the rhythm.

## The end card

It does not come from `events` but from `endcard` in `edit.json`:

```json
"endcard": {"at": 53.08, "dur": 2.6, "sfx": ["whoosh"],
            "title": ["SHIP YOUR", "*FIRST*", "AI WORKFLOW", "IN 1 DAY"],
            "when": "thu 12 mar · 10:00–16:00 · leeds",
            "sticker": "early bird 149 · until 28 feb", "sticker_flag": "offer",
            "cta": "SAVE YOUR SEAT →", "url": "example.com", "image": "assets/team-cutout.png"}
```

- `at` is the source second where the card slides over the video (just after the last word), `dur` how long it stays.
  The last shot keeps running underneath. `at` must fall inside the last kept segment.
- A word between asterisks gets the highlight.
- `when`, `sticker`, `image`, `cta` and `url` are optional; `cta` and `url` fall back to the brand.
- The sticker only shows in variants with `sticker_flag` in their `flags`. Without it, the button and URL move up.
- At +1.0 s the button presses in, with a chime.

## Checking

- `python3 _engine/build.py <ad> plan <variant> <format>`: every event with its output times. `WARNING` lines mean an
  event (or its end word) falls outside the chosen segments and **silently disappears**. That is how an end card once
  vanished when the last segment got shorter. An event with a `flag` the variant does not have is skipped on purpose,
  without a warning.
- `python3 _engine/build.py <ad> stills <variant> <format> 0.5 1.2 3.3 ...`: base plus overlay at those seconds in one
  contact sheet. Per event, pick a moment in the middle of its animation and one just after it appears.

## Making a new event type

1. In `overlay.html`, inside `window.load`: `if (e.type === 'new') { const el = mk(...); ITEMS.push(t => place(el, x, y, rot, pop(t, e.t0, e.t1))); }`.
   Use only `t`, no state that depends on the previous frame. Use the colour tokens (`var(--accent)`, `col(e.color)`)
   and `INK` instead of hex codes, so the brand carries through.
2. Is it a card with key info? Add the type to the list that fills `HIDE` (captions off).
3. Extra sounds that belong to the animation: in `sfx_cues` in `build.py`.
4. Positions per format in `LAYOUTS`, inside the safe zones (`safe-zones.md`).
5. Make stills of 9:16 and 4:5 and look at them before you render.
