# Phase 2: Sound (music, beat grid, loop, voice)

Sound comes before the build. The measured beat grid and the moment every word is spoken decide when everything on
screen happens. You build the picture to the audio, never the other way round.

## 1. The project folder

```bash
python3 <skill>/scripts/new_project.py videos/<name> --format 16:9
cd videos/<name>
```

The copy is the template video with stand-in sounds and renders straight away. You replace it piece by piece:
`project.json` (brief, facts, lines), the music, `vo/`, then (phase 3) `BRAND`, `COPY` and the states in
`motion.html`. Log every version in `notes.md`.

## 2. Music

Pick one, in this order of preference:

1. **A track the user supplies** with a licence for commercial use (their own, a paid library, public domain). Ask
   before downloading anything.
2. **A new Lyria song** (needs `OPENROUTER_API_KEY`, about $0.08, one to three minutes):
   `python3 music.py "<prompt>" --out audio/music/song_v1` (add `--dry-run` first to show the request). A prompt that
   worked first time is in `music.py`: instrumental, tempo, groove, instruments, mood, "leave space in the midrange
   for a voice", no drops or tempo changes. It asks for a key and a tempo, and Lyria ignores both: measure.
3. **The placeholder loop** (`audio/music/placeholder.wav`, 120 BPM, already in `project.json`) while you build. It
   never ships.

Reusing one song across several videos makes them feel like a series, and the grid is already measured.

## 3. The grid and the loop

```bash
python3 beats.py audio/music/song_v1.mp3
```

It prints the tempo, the first beat, where the downbeats are, how often the chords repeat (often every 4 bars, 16
beats), the energy of every bar with the loud parts, and T for common loop lengths. Then:

- **Pick the length in beats** (`BEATS`): a multiple of 16. T is `BEATS × beat`, rounded to whole frames at 60 fps;
  `build_audio.py` stretches the music by a hair (typically 0.02%) to fit exactly.
- **Cut the loop from the loud part**, starting on a downbeat where a phrase starts, in whole phrases. If the loud
  part is shorter than the loop, repeat its last phrase (for example song beats 33-113, then 97-113 once more).
- **Score it**: `python3 beats.py audio/music/song_v1.mp3 --segments 33-113,97-113`. Every seam gets a chord
  similarity. Above 0.3 is very alike; 0.1 to 0.3 is the same chords in a slightly different arrangement (a seam of
  0.15 went unnoticed); around 0 means the chords don't line up, so move the cut by a bar.
- Some loop lengths have no good seam in a given song (13 or 14 bars may score under 0.1 where 12 is perfect). Try
  a few lengths before you build.
- Put `period`, `first_beat`, `bpm` and `segments` in `project.json` → `music`, and `BEATS`/`T` at the top of the
  script in `motion.html`. `qa.py` checks that they agree. Retune `pluck_notes` to the song's key.

## 4. The voice-over, one sentence at a time

Every line in `project.json` → `lines`:

| field | what |
|---|---|
| `name` | `s1`, `s2`, …: the files are `vo/takes/s2_a.wav` and the chosen `vo/s2.wav` |
| `text` | the sentence as written; Whisper checks the takes against it, captions show it |
| `say` | only when the ear needs another spelling: `"… at example dot com."` |
| `cap` | caption text when it should differ from `text`; `null` for no caption on that line |
| `at` | the beat where the first word starts (fractions are fine: `8.05`); set in step 5 |
| `hint` / `style` | extra delivery instructions for this line / a replacement for `voice.style` |
| `gain_db` | a per-line level tweak, rarely needed (every line is levelled to the same speech loudness) |
| `note` | why this take, what it syncs to |

With a key (`voice.provider` "auto" picks OpenRouter, then Gemini):

```bash
python3 tts.py --test "One short sentence." --voices Aoede,Sulafat,Puck   # let the user pick a voice first
python3 tts.py --dry-run          # every request and the cost, spends nothing
python3 tts.py --missing          # 2 takes of every line without a chosen take, each checked with Whisper
python3 tts.py s2 --takes 4       # more takes of a hard line (names, brand names, the url)
python3 tts.py s2 --use d         # take d becomes vo/s2.wav
python3 vo_check.py --chosen      # check the chosen takes and save their word times
```

Without a key:

```bash
python3 placeholder.py voice      # a scratch voice (macOS "say", else a hum per word), marked as scratch
```

Or put the user's own recordings in `vo/<name>.wav` (one file per line, any format ffmpeg reads, renamed to .wav
after converting). For a music-only video, empty `lines`.

`tts.py` runs `vo_check.py` on every new take: what Whisper heard, the word error rate against `text`, the mean word
confidence, low-confidence words, pauses, pace and pitch movement, best take first. Then listen to the top takes
yourself, above all the names. What goes wrong and how to catch it is in `references/audio-cookbook.md`.

## 5. Put the lines on the beat

```bash
python3 build_audio.py --table
```

It prints every line in seconds and beats, and every word with its beat (`Anna@8.87`), and warns when lines overlap
or run out of the video. Move the `at` values until:

- every line starts on or just after a beat, with at least a quarter second between lines;
- the words that name something land where that thing will appear (you'll time the states to these beats);
- the last line ends 3 to 4 beats before the loop point, so the CTA can breathe and the cursor can go home.

If the lines don't fit: trim the silence first (the takes are measured by their speech, not the file), then speed up
lines a little with ffmpeg `atempo` (at most 1.07, never on the hook or a line with a hard name), then cut words.

Then `python3 build_audio.py` makes the full mix (`audio/mix.wav`). Sound events from the page are part of it, so
run it again whenever you move events in phase 3.

## 6. Captions

If the video gets captions (`project.json` → `captions.on`), run `python3 build_captions.py` after the lines are
placed and again after every voice change. See `references/captions.md`.
