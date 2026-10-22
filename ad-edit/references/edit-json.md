# `edit.json` and `brand.json`: every field

Everything that belongs to one ad lives in its `edit.json`. The code holds no times, words, paths or facts. Times are
**source seconds** in the recording (as `frames.py` and `probe.py` show them), not output seconds.
`template/example-ad/edit.json` is a worked example to read. Never point two ads at the same `work` folder.

## Basics

| Field | Example | Meaning |
|---|---|---|
| `title` | "Workshop invite, founder to camera" | for people |
| `name` | "workshop-invite" | start of the export file names |
| `version` | "v3" | end of the export file names; raise it every feedback round |
| `source` | path to the `.mov` | the raw recording |
| `work` | `work` or `/Volumes/Drive/ads/01/work` | all intermediate files (relative = inside the ad folder) |
| `out` | `exports` | the mp4s |
| `fps` | 30 | output frame rate |
| `language` | "en" | language of the take, for Whisper; empty = auto-detect |
| `whisper_model` | "large-v3" | model for `verify`; `small` for a quick test |
| `whisper_prompt` | "Brand, Name, jargon." | names and jargon for `verify` |
| `face_fallback` | [0.5, 0.33] | face position (part of width, height) when no face tracker is available |

Exports are named `<name>_<variant>_<format>_<version>.mp4`.

## `files` (relative to `work`; an absolute path is fine too)

| Key | Default | Made by |
|---|---|---|
| `picture` | `sdr_prores.mov` | `build.py prep` |
| `faces` | `faces.json` | `build.py prep` |
| `audio` | `audio/src48.wav` | `build.py prep` |
| `voice` | `audio/voice_warm.wav` | `voice.py` (or `patch_voice.py`: `voice_<preset>_fixed.wav`) |
| `words_whisper` | `words_whisper.json` | `words.py` |
| `words_crisper` | `words_crisper.json` | `crisper.py` (optional) |
| `music` | `music/bed.mp3` | you; `.beats.json` next to it from `beats.py` |

`crisper` (optional): several CrisperWhisper runs as `[[file, seconds to add, keep words from], ...]`, for example
`[["words_crisper.json", 0, 30.4], ["words_crisper_p1.json", 7.0, 0]]`. Without it: only `files.words_crisper`.

`assets` (optional): `{"sfx": "path/to/sounds"}`, default `_engine/assets/sfx`.
`prefilter` (optional): an ffmpeg filter before the zoom, for example a denoise `hqdn3d=2:1.5:5:4`.
`grade` (optional): the ffmpeg colour correction; default light contrast, saturation, sharpening and vignette.

## Cutting

- `segments`: list of `{"id", "a", "b", "note"}`. A piece from `a` to `b` (source seconds). `note` holds the text and
  what was taken out, so anyone can read the recipe.
- `variants`: per variant `{"segments": [ids in order], "flags": [...]}`. A flag turns parts on, like `offer` for the
  price card and the end card sticker. Name them like `A-offer`, `B-evergreen`: letter, then what is different.
- `formats`: per format `w`, `h`, `zoom` per level (`"1"`, `"2"`, `"3"`) and `face_y` (where the face sits
  vertically, as part of the height). A face that is small in the frame needs higher zooms (1.4 / 1.7 / 1.95).
- `shots`: list `[source second, zoom level]` or `[source second, zoom level, "intro"]`. From that second on that
  level applies, until the next one.
- `captions` (optional): `{"words": 3, "chars": 17, "uppercase": true}`: the maximum per caption block, and whether
  captions are in capitals.

## Words (corrections to the transcript)

| Field | Form | When |
|---|---|---|
| `words_fix` | `[heard, meant]` or `[heard, meant, near time]` | Whisper spelled it wrong |
| `words_at` | `[word, near time, real start]` | the time is wrong and something lands on this word |
| `words_drop` | `[word, near time]` | Whisper invented a word |
| `words_add` | `[word, start time]` | Whisper missed a word |

`build.py` keeps the result in `work/words_final.json` and rebuilds it whenever `edit.json`, `build.py` or a word file
is newer.

## Picture and sound

- `events`: see `graphics-kit.md`. Every event can take `"flag"`: then it only shows in variants with that flag.
- `logos`, `photos`: file paths, looked up in the ad folder, then the ads folder, then the engine.
- `endcard`: see `graphics-kit.md`. Leave it out for a video without an end card.
- `music`: `{}` for the simple bed, `{"start": 12.0}` to start later in the song, or
  `{"end_beat", "hit_beat", "phrase", "hit_after_endcard"}` for the synced ending; see `music-and-sound.md`.
- `mix`: `{"duck_speech": -14.5, "duck_gap": -9.0, "endcard": -6.0}`.
- `voice_gain`: `[[from, to, dB], ...]` in source seconds, to lift a soft word the music would cover.

## The brand (`brand.json`, and `"brand"` in edit.json)

`brand.json` sits next to the ad folders and holds the brand for every ad; the setup interview fills it in.
A `"brand"` section in one `edit.json` overrides single fields for that ad (for example another CTA).

| Field | Default | Meaning |
|---|---|---|
| `name` | "" | brand name, shown as a text tag when there is no logo |
| `logo` | "" | logo image (PNG or SVG, transparent background works best); replaces the name |
| `tag` | true | the brand tag in the top corner during the video |
| `url` | "" | small line under the end card button |
| `cta` | "LEARN MORE →" | end card button text (the end card's own `cta` wins) |
| `locale` | "en-US" | number format, for example the like counter on `post` |
| `colors` | neutral palette | `bg`, `ink`, `paper`, `accent`, `accent2`, `accent3`, `accent4` (see `graphics-kit.md`); `caption` (caption fill, default white), `caption_active` (the word being spoken, default `accent`), `shadow` (default `ink`) |
| `fonts.display` | Archivo 800 | headings and captions: `{"family", "weight", "google": true}` or `{"family", "weight", "file": "fonts/Brand.woff2"}` |
| `fonts.label` | JetBrains Mono 700 | small capital labels; same form |
| `style` | `{"border": 4, "shadow": 8, "radius": 18}` | border width, hard shadow offset and corner radius in px; 0 / 0 gives a flat look |

Google Fonts need internet while rendering. For offline renders, or a font that is not on Google Fonts, use `file`
with a font file you are licensed to use. `build.py` warns when a font did not load.

## Empty start

`scripts/new_ad.py` writes an `edit.json` with the paths filled in and empty lists. Fill it in this order:
`segments` and `variants` (after the cut plan), `shots`, the word fixes (after `build.py plan`), `events`, `endcard`,
`music`. `build.py plan` shows after every step whether it holds together.
