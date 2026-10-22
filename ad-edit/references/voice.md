# Voice: from a phone recording to a warm studio voice

A raw phone recording usually has room echo and can sound sharp. The chain below took one take from "echoey and
shrill" to "warm and dry" in four rounds. Start from a preset, and measure when someone comments on the voice.

## The chain (`voice.py`)

```bash
python3 _engine/voice.py "<work>/audio/src48.wav" "<work>/audio" --eq warm      # --taps 18 --delay 3 are the defaults
```

1. **WPE dereverb** (`nara_wpe`): removes the room tail, learned from the recording itself. `--taps 18 --delay 3` gave
   the driest voice without artefacts; 12 taps left more room.
2. **DeepFilterNet** (the `deep-filter` binary) with `-D --pf`: full noise reduction with post-filter. A limited run
   (`-a 35`) kept some echo.
3. **EQ preset** in ffmpeg: equalisers, a dynamic EQ on 2.6 kHz, de-esser, compressor, limiter.

Result: `<work>/audio/voice_<preset>.wav`. Put that path in `edit.json` under `files.voice`.

Missing tools: without `nara_wpe` the dereverb is skipped; without `deep-filter`, ffmpeg's `afftdn` denoises (much
weaker). `voice.py` says which one it used.

## What the words mean, in numbers

`python3 _engine/voice_metrics.py <raw.wav> <preset1.wav> <preset2.wav> --win 7:53` measures per file:

- **floor:** the noise level between words (lower is quieter);
- **tail:** how many dB the level drops 100 ms after a word ends. That is the echo: the more negative, the drier;
- **centroid:** the spectral centre of gravity. High sounds thin and sharp, low sounds warm and full;
- **lo / mud / mid / pres / sib / air:** energy per band (80-250, 250-600, 600-2000, 2000-5000, 5000-9000,
  9000-16000 Hz) relative to the whole.

Measured on one take (a female voice, phone at arm's length, a bare room):

| File | Floor | Tail | Centroid | pres | Verdict |
|---|---|---|---|---|---|
| raw phone | -51.6 dB | -12.7 dB | 904 Hz | -11.6 | echoey |
| DeepFilterNet limited (`-a 35`) | -59.3 | -21.3 | 1425 Hz | -8.5 | **sharp**, still echo |
| `bright` | -65.1 | -30.6 | 1003 Hz | -11.9 | clear but too sharp |
| `warm` | -62.9 | -26.5 | 746 Hz | -13.4 | needed more warmth |
| `studio` | -73.4 | -41.5 | 724 Hz | -13.7 | dry, studio |
| `warmer` | -74.1 | -40.0 | 559 Hz | -16.2 | **approved** |

How to translate feedback:

- **"Sharp" / "shrill":** centroid above about 1000 Hz and a high `pres` band. That voice had a resonance at 1.6 kHz,
  7 dB above 1 kHz. Find the peak (a spectrum of a few sentences) and cut there, not broadly across the whole top.
- **"Warm":** body around the fundamental (+2 to +3.5 dB there; 240 Hz for that voice), the resonance out, a darker
  top. Centroid around 550 to 750 Hz. Stay intelligible: below about 500 Hz it turns dull or muddy.
- **"Studio":** dry and close. Tail of -35 dB or lower, a soft expander between words (`agate`, `range=0.18`) and 4:1
  compression. A stricter expander (`range=0.08`) made a soft hook unintelligible.
- **"Echo" / "sounds like a room":** tail above about -25 dB. First more WPE (more taps), only then the expander.

## The presets

`python3 _engine/voice.py --list` prints them.

| Preset | What it does |
|---|---|
| `bright` | highpass 80 Hz, +2.5 dB at 170 Hz, -2 dB at 380 Hz, -1.5 dB at 2.9 kHz, a little air, 2.5:1 compression |
| `warm` | +2 dB at 240 Hz, -4 dB at 1600 Hz, dynamic EQ at 2.6 kHz, highshelf -1.5 dB at 7.5 kHz, de-esser, 3.5:1 (the default) |
| `studio` | `warm` plus an expander (`agate` range 0.18), +2.5 dB at 240 Hz, 4:1 |
| `warmer` | `studio` plus lowshelf +1.5 dB at 180 Hz, +3.5 dB at 240 Hz, -5.5 dB at 1600 Hz, -2.5 dB at 2200 Hz, highshelf -3 dB at 6.5 kHz |
| `clear-warm` | for a voice that is warm and soft by itself: dry treatment, light body (+2 dB at 230 Hz), only -1.5 dB at 1600 Hz, a little air (+1 dB above 7 kHz), milder expander |
| `warm-far` | for a speaker further from the phone (dull top, same upper-mid bite): -4.5 dB at 1600 Hz, light body, a little air, milder expander |

The frequencies were tuned on specific voices. For a new speaker the resonance and fundamental sit elsewhere. Render
two or three presets, measure with `voice_metrics.py` and `frames.py` (its f0 column shows the speaking pitch), and if
needed add your own preset in `voice.py` with a comment saying who it is for and why. Don't change a preset someone
approved: add a new one.

## Working from a voice note

1. Render two or three presets on the same take.
2. Measure them with `voice_metrics.py` and put the table in `notes.md`.
3. Listen yourself to a sentence with many s-sounds and to the softest sentence (usually the hook).
4. Send one version with the numbers in plain words ("centre of gravity from 704 to 533 Hz, still clear").

The mix normalises the voice to -16 LUFS first and the final mix to -14 LUFS / -1 dBTP (see `music-and-sound.md`).

## The expander and soft consonants

The expander (`agate`) makes the voice dry, but eats soft final consonants. For a voice with many soft endings use
range 0.4 instead of 0.18 (`clear-warm` and `warm-far` do). Check the sentence ends again after every voice change.

## The denoiser can remove soft words

Soft words, especially the first one of a take, sometimes vanish completely in the clean voice while you can hear them
in the raw recording. So before the first cut, look at the raw recording too (`frames.py <work>/audio/src48.wav`).

## Repairing soft word parts: `patch_voice.py`

Did a soft stretch drop out, like a soft first word or the final syllable of a word? Then more volume alone
(`voice_gain`) does not help: the denoiser and the expander have already pushed it down. Compare the raw recording
with the clean voice in that stretch. If the clean voice is 10 dB or more lower there, rebuild the stretch:

```bash
python3 _engine/patch_voice.py "<work>/audio" <preset> "<work>/audio/voice_<preset>_fixed.wav" 46.95:47.66:4
```

This runs milder denoising (`deep-filter -a 14`) and the same EQ without the expander. The level is matched to the
clean voice, plus the dB in the third number, and the stretch goes back in with 15 ms crossfades. Then set
`files.voice` to the `_fixed` file and check the word in `verify`.

## Recording tips for the next take

- A small, soft room (curtains, a sofa, clothes) does more than any filter. You never get all the echo out.
- Phone at 40 to 60 cm, at eye level. A clip-on microphone beats the phone microphone.
- Record two or three seconds of silence before and after the text: WPE and DeepFilterNet learn the room from it.
- Say key info (date, price, times) literally. Then cards can land exactly on those words.
- Keep the face in the upper third of the frame, not too high: the 4:5 crop is cut around it.

## Dark or grainy picture

- Zooming in enlarges noise. Set `prefilter` (for example `hqdn3d=2:1.5:5:4`) in edit.json: it runs before the zoom.
- Against the light: lift shadows and mid tones in `grade` with curves, and sharpen more gently (`unsharp=3:3:0.3`).
  One that worked: `eq=contrast=1.04:saturation=1.07:gamma=1.10,curves=master='0/0 0.12/0.15 0.3/0.38 0.55/0.62 0.8/0.84 1/1',unsharp=3:3:0.30:3:3:0,vignette=angle=PI/6.5`.
- Don't zoom further than needed.
