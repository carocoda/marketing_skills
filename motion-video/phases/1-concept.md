# Phase 1: Concept (ends at a gate)

The goal is a script and a beat table the user has approved before anything is voiced or built. The voice, the
music grid and every state hang off them.

## 1. Calibrate

Read `references/feedback-lessons.md` and `references/story-and-copy.md`. Skim `templates/project/script.md` for the
level of detail a concept needs. If you can run scripts, render the template's contact sheet once
(`render.py beats`) so you know what the style looks like in motion.

## 2. Gather the facts yourself

Use the profile from step 0, then look things up before you ask: the user's website or landing page, the event page,
a brand guide, a `CLAUDE.md` or README in their project. Ask only about real decisions.

- **What it's for and where it plays.** That decides the format (`references/formats.md`), the length and whether it
  needs captions.
- **Length.** A promo 30 to 50 s (16 to 24 bars at 115 to 120 BPM). A teaser 15 to 20 s (8 to 10 bars). An ad for
  Reels or Stories 15 to 25 s.
- **The hook.** The promise itself, said with energy in the first second, together with an over-the-top opening
  animation (the opening kit in `state-library.md`). Not a question.
- **5 to 10 concrete moments**, one state each: things people make, do, see or get. Only what exists.
- **People.** Hosts, speakers or a team only as real photos with their OK (`sticker.py`), or as drawn characters.
- **The CTA.** One action, one url, said and shown. A price or offer on a sticker near the end.

## 3. Pick a story shape

Shapes and their beat tables are in `story-and-copy.md`: product or feature promo, event promo, offer, teaser,
recap. The template follows the product promo.

## 4. Write the voice-over

- Spoken language: warm, a bit playful, sentences that flow ("and", "so", "because"), the odd short one. Not a row
  of short statements: that reads as a list written by a machine.
- One line per sentence, 3 to 12 seconds each: every line is its own TTS call. Two short sentences that belong
  together may share a line.
- Read the joins out loud. Two true sentences next to each other can suggest something false (a line about making
  videos followed by "from one webinar you cut shorts" made it sound as if the video itself was cut from a webinar).
- Pace: about 2.7 to 3.5 words per second. A 20-word line is about 7 s, 13 to 14 beats at 115 BPM. Leave at least a
  quarter second between lines, and 3 to 4 beats of air at the end.
- Write `text` the way it's read (for Whisper and captions). Add `say` only when the ear needs another spelling (a
  url: "example dot com").
- If the user has a writing style guide or a humanizer skill, run the script through it, then check it against
  their rules (banned words, no em-dashes).

## 5. Put it on a beat grid

A table with four columns: beats | the shape becomes | on-screen text | voice (the words it syncs to). You don't
have the song yet: assume the BPM you'll ask for (and expect the real one to differ; phase 2 measures it).

- Something happens on every beat: a morph, a click, a chip popping, a key, a tick.
- Clicks and pops land on the beat. Morph keys usually sit on quarter beats (7.25, 22.75) so the big motion reads
  on the beat.
- A state lives 4 to 16 beats. If its line is longer, add detail moves (chips, typing, a drag, a tooltip).
- A word that names something lands within half a beat of it appearing.
- The first 8 beats are the loudest of the whole video. The last state flows back into the first, with the cursor
  home and still for at least a beat.

## 6. Estimate cost and time

For example: "Voice: 7 lines × 2 takes, plus 4 extra takes for names, about $0.10. Music: one Lyria song, $0.08,
maybe a second try. Around $0.20 to $0.30 in total. A first version in about two hours." A finished 50 s video with
every test voice, retake and song came to about $0.30. Without a key: $0, with a scratch voice and the user's own
or the placeholder music.

## GATE: send it, then stop

In chat, as plain text:

1. the story in three or four sentences
2. the full voice-over, line by line
3. the beat table
4. the assets you'll use and what's missing (a photo, a logo, a fact to confirm, a track)
5. the cost estimate

Then wait. Phase 2 starts after a yes. Put the approved script and table in `script.md` and the lines in
`project.json`.
