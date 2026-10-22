---
name: motion-video
description: Make a looping UI motion video for a product, feature, event or offer. One shape morphs through UI states, a cursor clicks and drags every change, everything lands on the beat of the music, with an optional voice-over (Gemini TTS), music (Lyria or your own track), UI sounds and captions, rendered at 60 fps with motion blur in 16:9, 9:16, 1:1 or 4:5. Interviews you first about brand colours, fonts, shape language, voice, music, format, length and what the video is for, then sends the script, beat grid and cost estimate for approval before anything is made. Works without API keys (scratch voice, your own audio, or music only). Use whenever someone asks for a motion video, promo video, product demo, feature launch video, teaser, intro, reel, animated explainer of a product, "Dribbble-style UI animation", a looping video for a website or social, or wants an existing motion video changed, re-voiced or re-rendered.
---

# Motion video

One shape, never cut. Every state is the same rounded rectangle, morphing its size, radius and colour while its
content swaps with a short blur. A cursor drives every change with real clicks and drags, something happens on every
beat, and the last frame is the first frame. On top: a voice-over, a music bed and a UI sound on every event.

`templates/project/` is a complete 32 s example video that renders as-is, with free stand-in sounds made on the
user's computer. Every new video starts as a copy of it. The default look is neo-brutalist pastel (cream canvas, ink
borders, hard shadows, four pastels); it is a starting point, not a rule. The user's brand replaces it.

Talk to the user in their language. The voice-over and on-screen copy are in the language they choose for the video.

## It's a loop, not a one-shot

```
  0 PROFILE ── read motion-video-profile.md if it exists; otherwise interview (one message), offer to save it
  1 CONCEPT ── GATE: story + voice-over script + beat table + assets + cost estimate, as plain text. Wait for a yes.
      │
  2 SOUND ──── music → measured beat grid → loop cut → voice takes per sentence → checks → lines on beats → captions
  3 BUILD ──── motion.html: brand, copy, states, camera, cursor, sound events, timed to the words
  4 REVIEW ─┐  inner loop (yours): stills per beat → mid-morph strips → checklist → qa.py → fix   (max 3 rounds)
      ▲     └─ then render
  5 SHIP ───── full render → finish.py (mp4, thumbnail, light copy, video checks) → send vN + changelog
      │
      └──◄── OUTER LOOP: feedback → triage every note → change the smallest thing → rebuild only what depends on it
             (map below) → inner loop → vN+1. Log every round in notes.md. Stop when they say it's done.
```

Plan for three to eight rounds. The notes that come back are about things you only see or hear in the result: an
opening that doesn't grab, a voice that turns robotic halfway, a price that shows too early. What keeps the rounds
cheap is that the script is approved first and every note rebuilds only the part it touches.
Read `references/feedback-lessons.md` before you write anything.

## Step 0: the profile (before anything else)

Look for `motion-video-profile.md` in the project (or a brand profile the user points to) and read it. Also look for
answers already in the conversation or the project: a brand guide, a website, a `CLAUDE.md`, an earlier video. Skip
every question that is already answered.

Then send one short message with the open questions as a numbered list, each with a default in brackets so "ok" is a
valid answer, and wait. Never answer them yourself.

1. **What is it for, and where does it play?** Product demo, feature launch, event promo, offer, teaser, recap.
   LinkedIn, Instagram or TikTok, YouTube, your website, a screen at an event. [a promo for LinkedIn and your site]
2. **Format and length.** [16:9, about 30 to 45 s; 9:16 for Reels/TikTok/Shorts/Stories, 1:1 or 4:5 for the feed;
   15 to 20 s for a teaser]
3. **Brand look.** Colours (hex), fonts, logo text, or a link or screenshot of your site so I can take them from
   there. [the default: cream canvas, ink lines, four pastels, Space Grotesk + IBM Plex Mono]
4. **Shape language.** [neo-brutalist: 3 px borders, hard offset shadows, rounded corners. Other options: flat and
   soft (no borders, no shadow), sharp corners, thin lines]
5. **Voice-over.** Language, voice (female, male, neutral), tone; or no voice. [same language as this chat, a warm
   female voice, enthusiastic but relaxed]
6. **Music.** A mood, or your own track (with a licence for commercial use). [warm feel-good electronic pop, around
   115 to 120 BPM]
7. **The message.** The one promise for the first second, 3 to 8 concrete things to show, the call to action and
   url, and any facts (date, place, price). [I'll draft them from your site or brief for you to check]
8. **Captions?** [on for ads and social, where most people watch without sound; off for a website loop]
9. **Keys and budget.** [I'll check for an OPENROUTER_API_KEY or GEMINI_API_KEY. With one, voice and music cost a few
   cents per video. Without one: a scratch voice, your own recordings, or music only]

If they answer part of it, ask for what's missing in one line. Then offer to save the answers to
`motion-video-profile.md` in their project (template: `templates/motion-video-profile.md`), so the next video skips
this step. In a chat without files, give the profile as text they can paste next time.

## Hard rules

1. **Script before anything else.** Send the full voice-over, the beat table, the assets and the costs as plain text
   in chat (not a multiple-choice card), then stop. No voice, music or build before a yes. Changing a sentence now
   takes a minute; after the build it means new takes, new word times and re-timed states.
2. **Money.** A voice take costs well under a cent, a Lyria song about $0.08. Give the estimate before the first paid
   call and ask before anything beyond it. Keys live in the environment or a gitignored `.env`; the scripts read them
   themselves. Never print a key, never put it in a command, a file or a message.
3. **Downloads need an OK first**: a song, a font, a Whisper model, an npm package. Say what, from where, how big.
4. **Real people only with their own photos and their OK.** No generated faces of real people. A synthetic voice
   talks about people in the third person and never pretends to be one of them. Name tags sit on the right person.
5. **True copy.** Every fact (date, time, place, price, what's included) matches the source the user gave you.
   Only show what exists. No em-dashes, no hype words (the list is in `project.json` → `copy.banned`), plain
   sentences. A price goes on a sticker near the end, never in the opening and never in the voice-over (unless the
   user decides otherwise).
6. **The page is a pure function of time.** `seek(t)` sets every style from `t` alone: no CSS transitions or
   animations, no timers, no `Date.now()`, no unseeded `Math.random()`. That is what makes parallel rendering,
   motion blur and the perfect loop possible.
7. **Nothing leaves without checks.** You looked at the stills yourself, `qa.py` passes, and `finish.py`'s video
   checks pass. If something is still off, say so in the changelog.
8. **Placeholders never ship.** The stand-in music and the scratch voice are for building and timing. Replace them,
   or say plainly in the changelog that they are still in.

## Where it runs

Rendering needs Python 3.9+, ffmpeg, Playwright with Chromium, numpy, scipy and Pillow on the user's computer, so it
works from Claude Code, Codex or another agent that can run scripts. Run `python3 <skill>/scripts/check_env.py`
once. In a plain chat without code execution, do steps 0 and 1 (profile, script, beat table, costs) and say that
building and rendering need an agent that can run scripts.

## Phases

| Phase | Read | You end with |
|---|---|---|
| 1 Concept | `phases/1-concept.md` | an approved script, beat table and cost estimate (**gate**) |
| 2 Sound | `phases/2-sound.md` | a measured beat grid, a music loop, one checked take per sentence, placed on beats |
| 3 Build | `phases/3-build.md` | `motion.html` with the brand, every state, camera move, cursor move and sound event |
| 4 Review | `phases/4-review-loop.md` | a version that passes your own checklist and `qa.py` |
| 5 Ship | `phases/5-render-and-ship.md` | the mp4 and thumbnail sent with a changelog, and the notes triaged |

References: `default-style.md` (the look and how to swap it), `formats.md` (16:9, 9:16, 1:1, 4:5, safe zones),
`motion-rules.md` (springs, timing, camera, cursor, loop), `state-library.md` (every template state plus recipes for
more), `audio-cookbook.md` (providers, voice, checks, music, mix, costs, no-key options), `story-and-copy.md`,
`captions.md`, `feedback-lessons.md`, `gotchas.md`.

## Start

```bash
python3 <skill>/scripts/check_env.py                                  # once per computer
python3 <skill>/scripts/new_project.py videos/<name> --format 16:9    # or 9:16, 1:1, 4:5
cd videos/<name>
python3 build_audio.py && python3 render.py beats && python3 qa.py   # the copy works before you change anything
```

Ask once where videos should live if the project has no obvious place. Every project command runs inside the
project folder. Keep `.env` out of git.

## Rebuild map: what to re-run after a note

| The note is about | Edit | Then run |
|---|---|---|
| the words of a line | `project.json` line `text` (and `say`) | `tts.py <line>` → `tts.py <line> --use <x>` → `vo_check.py --chosen` → `build_audio.py --table` → re-time the states that sync to it → `build_audio.py` → `build_captions.py` → review → render → finish |
| how a line sounds | `voice.style`, the line's `hint`/`style`, or respell `say` | the same chain |
| when a line starts | the line's `at` (beats) | `build_audio.py --table` → re-time synced states → `build_audio.py` → `build_captions.py` |
| the brand (colours, fonts, borders) | `BRAND` in `motion.html` | `render.py beats` → look at every beat (text widths change with fonts) → `qa.py` → render → finish |
| what's on screen (text, layout) | `COPY` or the state blocks in `motion.html` | `render.py sheet <t…>` → `qa.py` → `render.py full` → `finish.py` (audio untouched) |
| when something happens on screen | the keys in `S_*`, the state tracks, `MOVES`, clicks, `window.SFX` | `render.py strip/sheet` → `qa.py` → `build_audio.py` (sounds move with events) → render → finish |
| the music | new song → `beats.py` → `music` in `project.json` | `beats.py --segments` → maybe new `BEATS`/`T` → everything from `build_audio.py` on |
| loudness or which sound where | `project.json` `mix`/`music`, the bank in `build_audio.py`, files in `assets/sfx/` | `build_audio.py` → `finish.py` (no re-render) |
| the length or the format | `BEATS` and `T`, the states; `canvas` in `project.json` | everything from `build_audio.py` on, and look at every beat again |

Rough times on a recent laptop: `build_audio.py` 10 s, `render.py beats` 20 s, `qa.py` 10 s, `render.py preview`
under a minute, `render.py full` four to six minutes for 50 s, `finish.py` one to three minutes. Show people full
renders: the motion blur is half the look.

## Files

```
SKILL.md, README.md, LICENSE
phases/1-concept.md … 5-render-and-ship.md
references/   default-style, formats, motion-rules, state-library, audio-cookbook, story-and-copy, captions,
              feedback-lessons, gotchas
scripts/      check_env.py (can this computer render?), new_project.py (copy the template, set the format)
templates/
  motion-video-profile.md    the saved answers from step 0
  project/                   the example video; every project is a copy of it
    motion.html              the whole picture: BRAND, COPY, the timeline, seek(t) → pixels, window.SFX → sounds
    project.json             brief, facts, music grid and loop, voice settings and lines, captions, copy rules, mix
    placeholder.py           free stand-ins: UI sounds, a music loop, a scratch voice
    tts.py vo_check.py       voice takes per sentence (OpenRouter or Gemini), Whisper checks and word times
    music.py beats.py        Lyria songs, beat grid, loop seams
    build_audio.py           music loop + voice on beats + UI sounds → audio/mix.wav
    build_captions.py        captions.js from the script, timed by the takes
    render.py qa.py finish.py  stills, strips, preview, full render, checks, final mp4 + thumbnails
    sticker.py               a cut-out photo → a collage sticker (outline, hard shadow)
    script.md                the example script and beat table: the level of detail the gate needs
```
