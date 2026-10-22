# Captions

Most people scroll social with the sound off, so ads and social videos get captions. A website loop or an event
screen usually doesn't: there, the on-screen text carries the key facts.

## Turn them on

`project.json` → `"captions": {"on": true, "words_per_phrase": 4, "aliases": {}}`, then
`python3 build_captions.py` after the lines are placed (and after every voice change). It writes `captions.js`,
which the page loads; an empty list means no captions.

## The look (default)

- The display font, bold, sentence case, centred, about 50 px on 1920×1080 and 64 px on 1080×1920.
- Words already said in ink, the spoken word on an `a1` highlight, words still to come at 35%.
- 16:9 and 1:1: centred at about 150 px above the bottom, above the HUD. 9:16: at about 76% of the height, inside
  the 4:5 crop band and above the platform buttons.
- A phrase blurs in at the start of a line and fades at its end. Phrases that follow straight on inside a line swap
  with no fade: a blink between phrases reads as a glitch.
- Another style the user may prefer for talking-head-like ads: uppercase, white with a thick ink outline, the spoken
  word in the accent colour. Change `#cap` in the CSS and `renderCaps` in the page.
- On a light UI canvas, heavy outlined captions can look cheap; the default is quieter on purpose.

## What gets a caption

- Every spoken line, except a line whose words are already the title on screen (`"cap": null`) and non-verbal sounds.
- The words on screen come from the script (`cap` or `text`), never from Whisper: Whisper misspells names and
  brands, and the script is right by definition.

## How the timing is made

1. `vo_check.py --chosen` gives word times per take; `build_audio.py` places them on the timeline.
2. A sequence alignment matches script words to heard words. Unmatched words get times interpolated by character
   count. Recurring mishearings go in `captions.aliases` (heard → script word, lowercase, no punctuation).
3. Without word times (no Whisper), the words are spread over the line's speech by length. Fine for a draft.
4. Phrases: `groups` on a line (word counts per phrase), else about `words_per_phrase` words, broken at punctuation.
   Keep phrases at 2 to 6 words and don't let one straddle two states.

## Checks

- `build_captions.py` prints every phrase with its times. Read it as running text.
- If Whisper matched under 70% of a line's words, it warns you: listen to that take.
- Look at a few stills with captions (`render.py sheet`): they must not cover content or the HUD.
