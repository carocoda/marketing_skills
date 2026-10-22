---
name: youtube-shorts
description: Turn a finished long YouTube video (or any talking-head video, webinar, podcast or course recording) into a series of standalone shorts for YouTube Shorts, Instagram Reels, TikTok (9:16) or LinkedIn (16:9 or 1:1). Picks the parts that work on their own, gives every short its own hook from the video, a beginning and an end, cuts on pauses, reframes to the platform, adds word-by-word captions, a title card, optional animated HyperFrames graphics with moving arrows, light sound effects and a "Watch the full video on YouTube" end screen. Use whenever someone wants shorts, clips, reels, TikToks, "short videos", "snippets" or "cut-downs" from a long video, asks which parts of a video would work as standalone clips, wants captions burned into a clip, or wants an existing short re-cut, re-timed or rebuilt. Not for editing the long video itself.
---

# Long video to shorts

One long video, a handful of short ones. Each short is a small standalone explainer: a real
beginning (a title card and an opening line that makes sense without the long video), one idea
in the middle, and an end (a closing line plus an end screen that sends people to the full
video). Not news, not a random 40-second slice, not a teaser that only works if you saw the rest.

Reply in the user's language. Captions stay in the language spoken in the video.

## Where this runs

Cutting, captions and rendering need `ffmpeg`, Python 3 with Pillow, and a shell, so the build
steps run in Claude Code, Codex or another agent with a terminal. In a plain chat you can still do
step 1 and 2: read the transcript, pick the shorts, write hooks, titles and the post text. Say so
once if there is no terminal.

Two build paths:

- **Motion graphics** (HyperFrames installed): animated title card, one moving graphic per idea,
  animated end screen. Read `/hyperframes-core` before you write composition HTML and use
  `/hyperframes-cli` for check, snapshot and render.
- **Captions only** (no HyperFrames): captions, a still title card and end screen made with
  Pillow, sounds, all with plain ffmpeg. Works anywhere ffmpeg runs.

Check what is installed before step 1: `ffmpeg -version`, `python3 -c "import PIL"`,
`npx hyperframes --version` (Node 22+). If something is missing, give the install line from the
README and carry on with what works.

## Step 0: read the profile

Look for `shorts-profile.md` (or `brand-profile.md`) in the project root. If it exists, read it
and skip every question it answers. If not, step 1 asks and offers to save one, based on
`templates/shorts-profile.md`.

## Step 1: ask (one message, then wait)

Ask only what the profile, the conversation and the project files don't already answer. One
numbered message; every question has a default in brackets, so "ok" is a full answer:

1. **The video.** The file (path) and the transcript if you have one (Whisper JSON, SRT/VTT from
   YouTube Studio, or nothing and I'll transcribe it). Also the long video's title and link.
2. **Where it goes.** [YouTube Shorts, Reels and TikTok in 9:16] or LinkedIn in 16:9 or 1:1.
3. **How long.** [up to 60 seconds; 45-60 is the sweet spot] (LinkedIn: up to 90).
4. **How many.** [5 shorts] I'll propose a few extra so you can strike some.
5. **Captions.** [bold: big caps, white with an outline, the spoken word highlighted] or pill
   (dark rounded bar, a coloured box under the spoken word) or clean (calm sentence case).
6. **Brand.** Colours as hex codes and a font [navy #1E40AF, bright blue #3B6BF0, yellow
   highlight #FFD400, Inter]. A logo file if you want it on the end screen [none].
7. **Graphics.** [animated HyperFrames graphics if installed, else captions only] or captions only.
8. **Sound.** [a soft chime on the title, one pop on a key graphic, a chime on the pay-off, no
   music] Your own music or sounds are welcome if you have the rights.
9. **End screen.** [Watch the full video on YouTube + the video title + your channel handle +
   "Link in the comments"]. For Reels/TikTok "Link in bio" often fits better.

Then offer: "Shall I save these answers to `shorts-profile.md` so I don't ask next time?" Write
it only on a yes. In a chat without files, give the profile as a block they can paste next time.

## Step 2: pick the shorts (in chat, wait for approval)

1. Get a word list with timestamps. See `references/runbook.md` step 0 (HyperFrames transcribe,
   Whisper, or an SRT). Normalise it with `scripts/words.py`, then print the sentences:
   `python3 scripts/find_shorts.py sentences words.json`.
2. Read the whole thing. A good short is about **one informative idea**: how something works,
   what changed, what to do, a mistake and its fix. It can be understood by someone who never saw
   the long video. Skip pure news, intros, sponsor parts and "as I said earlier" passages.
3. Propose a table with one extra candidate: number, working title, idea in one line, hook
   sentence + its time, body window, closer (if any), length, and why it stands alone. Flag the
   ones that need the title card to do the introducing because the speaker doesn't.
4. Every short opens with a **hook cut from the video itself** (5-12 s): one or two sentences
   from anywhere in the video that set up this short's idea. **No two shorts share a hook**: a
   series where every short opens with the same line gets skipped. Show the hook column so the
   overlap is visible before anything is cut.
5. Structure: hook (5-12 s) + body (the explanation) + optional closer (3-6 s) from elsewhere
   if the body's last sentence doesn't close the thought. Total within the max length.
6. Wait. The user strikes, re-orders, asks for "more of X". Only then write `spec.json` and run
   `find_shorts.py snap`, which moves every edge into a pause, snaps to whole frames and warns
   about mid-sentence starts or ends, shared hooks, overlaps and over-length shorts.

`find_shorts.py candidates` gives a rough map of runs that fit the length. It is a starting point
for reading, not a selection.

## Step 3: build ONE short first

Follow `references/runbook.md`. In short:

1. **Find the speaker.** Contact sheet of the long video; note where the face is (for the 9:16
   crop centre and for where graphics may go).
2. **Cut.** `scripts/cut_short.py`: all windows in one ffmpeg run, reframed, with a hidden
   punch-in zoom on every join so the jump cut reads as an edit.
3. **Read the words.** Print the short's word list as prose and fix homophones, names, tense and
   dropped words in the JSON. This step is not optional; one wrong caption word is what people
   comment on.
4. **Graphics** (motion path). One HyperFrames composition per idea, from the closest template
   in `templates/graphics/`. Every element lands on the word the speaker says it, not on a round
   number (`words.py --sheet` gives `word@time`). Check, snapshot, look at the snapshots, render
   as transparent `.mov`. Details in `references/animation-recipes.md` and
   `references/gotchas.md`.
5. **Sounds.** `scripts/make_sfx.py` makes a small royalty-free kit. At most three per short:
   title card, one moment where a pair or a key card appears, the pay-off.
6. **Assemble.** Fill a plan from `templates/plan-9x16.json`, `plan-16x9.json` or
   `plan-captions-only.json` and run `scripts/assemble.py plan.json --preview`. It checks the
   frame count.
7. **Review.** `scripts/contact_sheet.py` on the result at the title, each graphic's busiest
   moment and the end screen. Look at the sheet: graphics clear of the face and hands, captions
   inside the safe zone, arrows visible, end screen text right.
8. Send the preview with what is in it and one or two concrete questions. Build the rest only
   after the verdict on the first; feedback on short 1 usually changes all of them.

## The graphics patterns

| template | pattern | use for |
| --- | --- | --- |
| `title` | brand card, words rise one by one, accent bar grows along the top | the opener of every short (first 4-5 s) |
| `feed` | a bar that fills in two colours, labels, a badge with a marching arrow | any "X of Y" split or proportion |
| `two` | two cards slide in, a double marching arrow between them | "A versus B", "two things" |
| `reader` | header with number block, pills that pop on an enumeration, a marching dashed ring, a struck-through "not this", a tag "this is what counts" | a list the speaker reads out, with a punchline |
| `post` | two columns of pills with a "+" between, footer with a marching dash | two lists that add up to something |
| `match` | card, arrows, centre badge, arrows, card, arrow down to a result; then the badge flips to "no" | any decision, if-then, match or not |
| `end-screen` | headline, video card with a play button and a cursor click, link line | the last 4.5 s of every short |

Copy a folder, change the brand block, the words and the times; keep the structure. One graphic
per idea, not one per sentence: a short with a card on screen the whole time is a slideshow.

## Rules

- **Plan first, build after approval.** The shorts table goes in chat as text and waits for a
  yes. Then one short, then the rest.
- **A beginning and an end.** Title card over the hook, a closing line before the end screen.
- **Unique hooks** across the series.
- **Cut in pauses only**, never mid-word or across a hidden edit in the long video.
- **The speaker's words are not rewritten.** Fix transcription errors, never "improve" what was
  said. Titles, hooks on the title card and post text are yours to write.
- **Nothing covers the face or the hands.** Graphics go in the free area; on 9:16 above the
  captions, inside the safe zone (`references/platforms.md`).
- **Sound supports, never competes.** The voice is always first.
- **No made-up claims** on cards: numbers and names only from the video or the user.
- **Never upload or post anything.** The user publishes. Large files stay where the user keeps
  video (ask if unsure); don't fill the repo with mp4/mov files.

## Posting notes (offer these with the first finished short)

- The YouTube link goes in the first comment (LinkedIn, Instagram) or as the related video
  (YouTube Shorts); the end screen says where.
- One idea per post, the same idea as the short. Don't stack the whole series into one post.
- The post text is read, not spoken: short, plain, no hype. The short's own captions stay the
  speaker's words.
- Space the series out (for example two or three a week) instead of posting all at once.

## Files

- `references/runbook.md`: the exact command sequence for one short.
- `references/animation-recipes.md`: the GSAP behind the graphics and how to time them to words.
- `references/gotchas.md`: known failure modes and their fixes.
- `references/platforms.md`: sizes, lengths and safe zones per platform.
- `scripts/`: `words.py`, `find_shorts.py`, `cut_short.py`, `captions.py`, `cards.py`,
  `make_sfx.py`, `assemble.py`, `contact_sheet.py`, `selftest.py` (each has `--help`).
- `templates/`: graphics, example plans, `shorts-profile.md`.
