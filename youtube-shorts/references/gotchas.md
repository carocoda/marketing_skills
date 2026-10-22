# Known failure modes

Each one of these cost a re-render on a real series. Check the table before you build, and again
when something looks off.

## Picking and cutting

| symptom | cause | fix |
| --- | --- | --- |
| the short "jumps straight into the explanation" | no hook; the body starts with "the most important part of that is..." | open with a hook window: one or two sentences from anywhere in the video that set up this short's idea |
| viewers of the series hear the same opening every time | several shorts share one hook | every short gets its own hook; `find_shorts.py snap` warns on overlap |
| the short feels random, no ending | the window stops mid-thought | end on a closing sentence; add a closer window (3-6 s) from elsewhere if the body doesn't close |
| a breath, a "so" or half a word at a cut | window edge between two words that run together | `snap` only cuts in pauses of at least 0.15 s; with `--video` it also checks the audio is silent there |
| a flash of a different pose right before the end | a window runs a few frames across a cut in the long video's own edit | read the long video's cut list if you have one; start or end a window ON a cut, never across one |
| audio slowly out of sync | windows encoded separately and joined | `cut_short.py` does all windows in one ffmpeg run with trim/atrim + concat; keep it that way |
| frame count off by one | window lengths not whole frames | `snap` rounds every window to whole frames; `cut_short.py` and `assemble.py` print expected vs actual |
| word times drift near the long video's own edit points | small Whisper models misplace words next to a hard cut | put window edges in clear pauses; when in doubt transcribe the cut clip again with a bigger model |
| "the green blocks" in a still | a fast seek (`-ss` before `-i`) shows a half-decoded frame | not damage. `contact_sheet.py` seeks after the input for this reason |

## Captions

| symptom | cause | fix |
| --- | --- | --- |
| wrong word in the captions ("your feet" for "your feed") | Whisper homophones, wrong tense, dropped words | read the short's word list as prose before you build anything (`words.py --prose`), fix the text in the JSON, never in the video |
| brand or product name spelled wrong | Whisper doesn't know it | search the word list for the name and every likely mishearing |
| captions over the app buttons | caption y too low for 9:16 | keep the caption centre at y 0.65-0.72 on 9:16 (see platforms.md) |
| captions stay on screen through a pause | chunk end too late | captions.py ends a chunk 0.7 s after its last word at most |
| two sentences in one caption read messy | chunk across a sentence end | captions.py starts a new chunk after every full stop |
| no text at all, or a tiny font | no bold font found | pass `--font` / `captions.font` with a .ttf or .otf file |

## HyperFrames graphics

| symptom | cause | fix |
| --- | --- | --- |
| `gsap_infinite_repeat` on check | `repeat:-1` on the dash tween | the renderer seeks to exact frames and refuses infinite repeats; use one long linear tween of K cycles |
| a state flip (MATCH to NO MATCH) never happens in the render | `tl.call()` or `.set(textContent)` | seeking skips callbacks; make two elements and crossfade their opacity |
| `text_occluded` on check | an underline that grows under a subline | put the accent on the card edge |
| contrast fail on a red word | red text on a light background | a red pill with white text |
| contrast fails on text that looks fine | a CSS variable that points at itself (`--brand:var(--brand)`) or an unresolved variable | define every variable in `:root` with a literal colour |
| labels overlap | two absolutely placed labels too close | move the second; you only see this on the snapshot sheet, not in the code |
| arrows barely visible | too little gap between card and badge | at least 100 px gap, arrow svg at least 110 px wide |
| last row cut off in the render | canvas shorter than the card | canvas height = card height + 40 (and times the zoom if you scale with CSS zoom) |
| a pop sound on an empty screen | the comp's first card enters 3 s into its own timeline | shift the timeline so the first card is at 0.1 s and set the element's `t0` to the word |
| the old graphic shows after a re-render | renders are timestamped and the plan points at the previous file | point the plan at the newest `renders/*.mov` after every render |
| a tall card with one line in it looks empty | fixed card height | start at the height of what is visible and tween `height` just before each new row appears |
| inline highlight adds visible spaces ("20 .") | `padding:0 5px` on an inline span | cancel it with `margin:0 -5px` |
| text soft or too small in 9:16 | a 16:9-sized design scaled up | design at the size you place it; or render with `#scene{zoom:1.2}` on a wider root (heights x 1.2, rounded to even) |
| `snapshot --at 2.0` file not found | whole-second times are named `frame-00-at-2s.png` | copy with a glob after clearing `snapshots/` |

## Assembly

| symptom | cause | fix |
| --- | --- | --- |
| audio about 20 ms late after the end screen | AAC files joined with `-c copy` lose the encoder delay | assemble.py keeps audio as PCM through the join and encodes AAC once |
| end screen plays too fast or too slow | it was rendered at another frame rate | assemble.py conforms it by duration, not by frame count |
| graphic covers the face or hands | the speaker sits somewhere else in this video | measure on a contact sheet of the clip; move the column |
| sound effects drown the voice | too many, too loud | three per short at most (title, one pair, the pay-off), gain 0.25-0.35; music bed around 0.03-0.05 |
