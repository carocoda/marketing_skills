# Audio cookbook: voice, checks, music, mix, costs

## Keys and providers

| Key (environment or `.env`) | Gives you | Provider |
|---|---|---|
| `OPENROUTER_API_KEY` | voice (Gemini TTS) and music (Lyria) | OpenRouter, tested in production |
| `GEMINI_API_KEY` (or `GOOGLE_API_KEY`) | voice (Gemini TTS) | Google's API directly; written to the public docs, check the first takes |
| none | scratch voice, your own recordings, your own or placeholder music | local |

`project.json` → `voice.provider` is "auto" (OpenRouter, then Gemini, then none) or one of them. The scripts read
keys themselves and never print them. Model names change: if a call says the model doesn't exist, look up the
provider's current TTS model and set `openrouter_model` or `gemini_model`.

## Without a key

- **Scratch voice**: `python3 placeholder.py voice` makes a take per line with macOS `say` (any installed voice:
  `--say-voice Samantha`), or a hum per word elsewhere. Good enough to time the picture. `qa.py` warns until it's
  replaced.
- **Your own voice**: record each line separately (a phone in a quiet room is fine), one file per line, save as
  `vo/<name>.wav`. `build_audio.py` levels, cleans (high-pass, gentle compressor, a little presence) and places them.
  Run `vo_check.py --chosen` for word times if faster-whisper is installed.
- **Another TTS tool** (any service the user already pays for): export a file per line into `vo/`, same as above.
- **Music only**: empty `lines`. Put the facts on screen and turn captions off.

## Voice: Gemini TTS (`tts.py`)

- OpenRouter: `POST /api/v1/audio/speech` with `{"model", "input": <text>, "voice", "response_format": "pcm",
  "provider": {"options": {"google-ai-studio": {"speech_metadata": {"style": <delivery>}}}}}`. The `X-Generation-Id`
  header gives the real cost.
- Gemini direct: `generateContent` with `responseModalities: ["AUDIO"]` and a prebuilt voice; the delivery is
  written as an instruction in front of the text.
- The answer is raw PCM, 24 kHz, 16-bit, mono, wrapped into a wav.
- **The delivery never goes in the spoken text field**: it gets read out loud.
- **Pick the voice by ear.** `tts.py --test "One sentence." --voices Aoede,Sulafat,Laomedeia` makes one take per
  voice for under a cent; let the user choose. Match the voice to the narrator: if the copy says "I", the voice must
  fit that person, and a synthetic voice never pretends to be a real one.
- A style that worked well: "Cheerful, warm and playful voice inviting a friend to a fun, hands-on day. Natural
  spoken [language], lively but relaxed pace, smile in the voice, no radio-announcer tone." Name the language in the
  style when it isn't English.
- **One sentence per call.** One long take of a 40 s script went robotic halfway. Separate takes per sentence fixed
  it: 7 lines, 26 takes, about $0.16.
- About $0.0009 per second of speech: a 3 s line costs a third of a cent, a 12 s line one cent.

## Checking takes (`vo_check.py`)

- faster-whisper on the CPU, about 15 s per take with large-v3. Use a multilingual model (large-v3 is best outside
  English, about 3 GB; small is about 0.5 GB). Ask before downloading one.
- Per take: what it heard, the word error rate against `text` (after `heard_as` aliases), the mean word
  confidence, words under 0.6, pauses over 0.45 s, words per second, pitch movement and pitch jumps. Best first. It
  tells you what to listen to first; your ears decide.
- **Names by sound**: Whisper is not the judge of names (one model kept hearing the -e version of a name ending in -a,
  even in good takes). Make one short reference take where the name sounds right and one where it's wrong, then
  `python3 vo_check.py compare Anna vo/takes/s2_d.wav --ref good.wav --ref bad.wav` says which one the take's word
  sounds most like (MFCC + DTW). A hint, not a verdict.
- `vo_check.py --chosen` saves every chosen take's word times; `build_audio.py --table` turns them into beats and
  `build_captions.py` into caption timing.

## Pronunciation lessons

| Problem | What happened | What works |
|---|---|---|
| A brand or product name | an English pronunciation hint on a non-English take made "Claude" sound like a rude word; other takes said "cloud" or "Klaat" | no hint, 4 to 9 takes, keep one Whisper hears right (1 in 9 can be the hit rate) |
| "ChatGPT" | "Chet GPT" in some takes | more takes |
| A person's name | the wrong variant of the name | compare by sound, and listen |
| A url | read letter by letter or skipped | `say`: "example dot com" (in the video's language) |
| Dates and numbers | digits are usually fine | spell out only if a take gets them wrong |
| Slang and local words | fine, but Whisper writes them oddly | add aliases in `heard_as` |
| Speeding up a line | at 1.05 a hard name went wrong again | `atempo` up to 1.07 only on easy lines, never on the hook |

## Music: Lyria (`music.py`)

- `google/lyria-3-pro-preview` via OpenRouter `/api/v1/chat/completions` with `"stream": true`,
  `"modalities": ["text", "audio"]`. The audio comes as base64 chunks. About $0.08 per song;
  `lyria-3-clip-preview` makes 30 s for about $0.04.
- It returned an mp3 although we asked for wav (`music.py` looks at the bytes and names the file right).
- It ignored tempo and key: asked 120 BPM in D, got 115 BPM in F. Measure with `beats.py`, always.
- Long prompts can get blocked (PROHIBITED_CONTENT, not billed): shorten to genre, tempo, instruments, mood and
  "no vocals".
- Songs have a quieter intro, full parts and a breakdown. Cut the loop from a full part.
- Licensed or own tracks work the same: measure them, cut the loop.

## Grid and loop (`beats.py`, `build_audio.py`)

- Tempo from spectral-flux onsets (autocorrelation, then a comb search over tempo and phase across the song);
  downbeats where the kick is strong and the harmony changes; the chord cycle from chroma. Onset times are corrected
  for the analysis window (75 ms), calibrated on a synthetic kick track.
- The loop is a list of song-beat segments. Every seam crossfades one beat of the previous segment's continuation
  into the next segment (equal power). Then the whole loop is FFT-resampled to exactly `T`: a tiny tempo change, and
  a seamless loop because the resample is periodic.
- `beats.py --segments` scores each seam by chord similarity.

## UI sounds

- `assets/sfx/`: click, key-press, pop, whoosh-short, impact-bass-1, chime. `placeholder.py sfx` synthesises them on
  the user's computer; any file with the same name (.wav, .mp3, .m4a, .ogg, .flac) replaces one. Library sounds
  (with a licence that allows use in videos) usually sound richer; check their levels.
- Synthesised in `build_audio.py`: soft plucks (Karplus-Strong, `music.pluck_notes`, default F4 A4 C5 F5) and a glass
  clink. Retune them when the song's key changes.
- Gains in dB: click -9, pop -13, tick -18 (click pitched up), grab -14, drop -16, toggle (click -9 + pop -17), enter
  (key -10 + click -15), key -13 (random pitch and ±2 dB per key), whoosh -17, slam (impact -15 + click -12), stamp
  (pop -9 + click -11), ding -16, plucks -17, clink -15. Tuned on library files; adjust to taste.
- Every sound is placed by its measured peak, so the transient lands on the frame of the event.

## The mix (`build_audio.py`)

| Stem | Level |
|---|---|
| voice | every line levelled to -18 dBFS speech RMS after high-pass 75 Hz, a gentle compressor (-22 dB, 3:1) and +1.5 dB at 3.2 kHz |
| music | -21 dBFS RMS, ducked 7.5 dB under the voice (attack 40 ms, release 350 ms) |
| UI sounds | the gains above |
| master | two-pass loudnorm to -14 LUFS, true peak -1.2 dBTP, LRA 11, 48 kHz 24-bit |

Everything is summed modulo `T`, so tails that run past the end land at the start and the loop is clean.

## Costs (a real 50 s promo)

| | |
|---|---|
| 3 test voices | $0.011 |
| 2 rounds of long takes (later replaced) | $0.047 |
| 26 takes, one per sentence | about $0.16 |
| 1 Lyria song | $0.080 |
| **total** | **about $0.30** |

`tts.py` and `music.py` print the real cost per call. Account-wide usage may include other projects on the same key,
so report the cost of your own calls.
