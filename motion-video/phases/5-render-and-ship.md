# Phase 5: Render, finish, send, and take the notes

## Render and finish

```bash
python3 build_audio.py                         # the mix, with the sounds of the latest events
python3 build_captions.py                      # if captions are on
python3 render.py full --workers 6             # 60 fps, 4 subframes per frame, motion blur -> video_noaudio.mkv
python3 finish.py --out ../<name>-16x9.mp4 --thumb <s> --review
```

- `check_env.py` suggests a worker count. Each worker runs its own headless Chromium and pipes the subframes as PNG
  straight into ffmpeg, which blends them (tmix) and writes lossless ffv1 chunks. Nothing lands on disk as images.
  About 0.65 s per frame per worker on a 16 GB laptop: a 50 s video in five to six minutes with 6 workers.
- After a change late in the video, `render.py full --only 5` re-renders just that chunk and re-joins.
- `render.py full --seconds 3` renders only the start: a quick test of the whole pipeline on a new computer.
- `finish.py` does the one lossy encode (x264, crf 16, tune animation, bt709 tags), pads the audio and cuts to exactly
  frames ÷ fps (never `-shortest`: it drops frames), makes thumbnails with the cursor hidden (`--thumb` as often as
  you like), a light copy with `--review` for chat apps, and runs the video checks: frame count, audio length,
  loudness (-14 LUFS ±0.5, true peak ≤ -1.2) and the loop seam of the file.
- Fix anything that fails before you send, unless you say plainly what's off and why it's still worth a look.

Thumbnail: a frame where the promise or a person is readable at small size, never a transition.

## Send it

Send the mp4 (and the thumbnail) with absolute paths, plus a short changelog in the user's language:

```
v2 (32.0 s): what changed
- opening: the click opens the title window, colour bursts, the headline slams in
- line 3 rewritten: "…"
- the price only at the end, on the sticker
Checked: stills on every beat, loop seam, -14 LUFS, Whisper hears every line right
Still placeholder: the music (waiting for your track)
Open question: thumbnail from the title (3.9 s) or the team (5.3 s)?
Cost so far: about $0.25
```

Add a row to `notes.md`. Ask whether they want the work committed; don't commit on your own.

## The outer loop: taking notes

1. **Write every note down verbatim** in `notes.md`, one line per note.
2. **Triage each note**: words / voice / on-screen / timing / music / mix / concept. A concept note ("the start
   doesn't grab", "more energy") goes back to phase 1: send a new script and wait for a yes before you rebuild.
   Everything else goes through the rebuild map in `SKILL.md`.
3. **If a note is ambiguous, show options** (two stills, two short takes) rather than asking in the abstract. If a
   note asks for something that breaks a rule (a fact that isn't true, a real face without OK), say so and offer the
   nearest thing that works.
4. **Change the smallest thing** that answers the note, and rebuild only what depends on it. A timing change moves
   everything after it: run the inner loop on the neighbours too.
5. **Send vN+1** with its changelog.
6. **Keep the taste.** When a note is a general preference ("price only on the sticker", "no question as the hook"),
   add it to the user's `motion-video-profile.md` under "Lessons", so the next video starts from it.

When they say it's done: keep `motion.html`, `project.json`, the scripts, `vo/` (chosen takes and `takes/`),
`audio/music/`, `assets/`, `script.md`, `notes.md` and the final mp4 and thumbnails. Delete what rebuilds in minutes:
`stills/`, `chunks/`, `chunks_preview/`, `video_noaudio.mkv`, `preview*.mp4`, `audio/tmp/`. The project's
`.gitignore` already leaves those out of git. Large videos can live outside the repo; ask where the user keeps them.
