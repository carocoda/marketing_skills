# Lessons from the feedback rounds

The first ad went through five rounds in one day; later ads added a few more lessons. Read this before you make
anything: it is the fastest way to see what "good" means here.

| Round | Feedback | What changed | Rule for the next ad |
|---|---|---|---|
| v1 | (first cut: four variants, long and short, with and without the offer) | | |
| v2 | Only the short versions. The voice sounds sharp and still has echo. Take the "uhs" out. The opening is too textual. "Look below" falls over the chest. | Short variants only. WPE + full DeepFilterNet + warm EQ. Five "uhs" cut. A visual opening (windows, files, app tiles). Real event photo. Arrow lower. | **Shorter is better.** Start with the short version. The opening shows, it does not tell. Text below the chest. |
| v3 | The voice should be warmer. A cut removed half a word. | `warm` preset (the 1.6 kHz resonance out). Fillers redone with CrisperWhisper. Photos without text. | Measure the voice, find the resonance. Photos without text. |
| v4 | The cutting still sounds odd. | Found: CrisperWhisper's `[UH]` was a piece of the word. Only real fillers out (2 of 5). `build.py audit`. Breathing pauses kept. `studio` preset (dry). | **Never cut inside voice.** Prove a filler with `frames.py` (flat pitch), not with a label. Better a filler stays than a word gets hit. |
| v5 | Show the logos of the tools in the opening. The client's own photo choice. A bit warmer still. | Logo tiles when the tools are named. The client's photos in their own aspect ratio. `warmer` preset. | Name a tool, show its logo. The client picks the photos. Approve one voice preset and reuse it for that speaker. |

## What kept coming back

- **Cutting** (three rounds): the most expensive lesson. See `cutting.md`.
- **Voice** (three rounds): from sharp to warm. See `voice.md`.
- **Visuals** (two rounds): less text, more real things (logos, photos, windows). See `graphics-kit.md`.

## From later ads

- **A false start** ("And if you ... And if you just don't know"): keep only the second one.
- **A soft word disappears under the music** even when it is in the voice track: `voice_gain`, and if the denoiser
  ate it, `patch_voice.py`.
- **A soft first word can vanish in the denoiser** ("A real..." became "...real"). Compare with the raw recording
  before the first cut.
- **Fillers at the start of a sentence** never appear in a transcript. Look at the first 0.6 s of every segment.
- **Pauses between sentences of under 0.1 s** make a complete word sound clipped. Aim for 0.3 to 0.45 s.
- **The same speaker in a different room or distance needs a different preset.** One voice that was already warm went
  dull on `warmer` (centroid 464 Hz); `clear-warm` fixed it. Further from the phone: `warm-far`.
- **A smaller face in the frame needs more zoom** (1.4 / 1.7 / 1.95 instead of 1.3 / 1.58 / 1.8).
- **Backlight and phone noise:** denoise before the zoom (`prefilter`), lift shadows in `grade`.
- **A soft-spoken voice needs the music lower** under speech (`duck_speech` -17 instead of -14.5).
- **CrisperWhisper can be wrong in a whole sentence** (it heard a different word in a hook and shifted everything 0.3
  to 0.5 s early). Pin those words with `words_at` using Whisper's times.
- **When the speaker swallows a key line** (their own name, the date), take that line from another take. Two takes can
  sit back to back in one source file.
- **The end card needs a moment to land on.** If the last kept segment ends right on the last word, keep a short quiet
  tail in the segment so `endcard.at` falls inside it.
- **No swearing in ads**, even when that take is technically cleaner.

## Technical lessons

- An event timed after the end of a segment silently disappeared: the end card vanished when the last segment got
  shorter. `build.py plan` now prints a `WARNING`.
- A stray word in the transcript of the final mix gave away a left-over "uh": run `build.py verify` after every audio
  build.
- Whisper puts word starts 0.2 to 0.5 s early; CrisperWhisper is more precise but spells worse. Combine them.
- Bass impact samples are long: always cut them short.
- Exports lost 3 frames per video on the end card (and doubled them elsewhere). Cause: Chrome saves a fully opaque
  overlay frame as RGB instead of RGBA, and that switch makes ffmpeg rebuild the overlay. `build.py` now saves every
  overlay frame as RGBA. (`-reinit_filter 0` looks like a fix but reads the RGB frames wrong: don't use it.)
- Music at -19 dB under speech was too soft on a phone; -14.5 dB works.
- Some ffmpeg builds (Homebrew on macOS among them) have no `zscale`. HDR iPhone footage then needs Apple's own tone
  mapping (`hdr_to_sdr`, built by `check_env.py --build`), or an ffmpeg with libzimg.
- A newer macOS SDK can make an older `swiftc` refuse to build; `check_env.py --build` then retries with an older SDK.
