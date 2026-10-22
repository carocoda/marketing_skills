# Gotchas: bugs we hit, and the fix

## Picture

| Symptom | Cause | Fix |
|---|---|---|
| Muddy in-between frames between ink and a pastel | a slow or bouncy colour spring | `SP.color` (0.18, ζ 1): fast, no overshoot |
| Text in a pill off-centre | the pill wider than its text, text anchored left | size the pill to the text and centre it |
| A typed prompt cut off at the edge | text wider than the shape | a wider shape or a smaller font; look at the last typed frame |
| The headline still visible over the next state | its exit started too late | leave at the morph key with a 0.1 s fade |
| A slammed word too big | slamming in from 135% | from 120% |
| A tooltip over a chart title | bars too tall | a lower bar maximum, not a smaller font |
| An element missing in a new layout | it was never created | every element in the HTML or `init()`; look at the stills |
| The loop stutters | something visible or moving at the seam | the tile at rest and the cursor home a beat before the end; `qa.py` loop check |
| Text renders soft | `will-change` or a scale hack on the world | leave both out |
| Fonts look wrong | Google Fonts didn't load (offline) or a wrong family name | `qa.py` fonts check; render online, or use a local `src` font |
| Text widths wrong, things overlap after a font change | widths measured before the font loaded, or layout tuned for the old font | measure in `init()` (after fonts load); look at every beat after changing `BRAND.fonts` |
| A photo missing in the first frames | the image hadn't decoded | add its id to `DECODE` in the boot code |
| A value jumps when you move a key | keys are in beats, and a forgotten key still acts | `Track` sorts and wraps keys; check both neighbours with `render.py strip` |
| Big morphs overflow the frame halfway | the camera spring slower than the shape spring | `SP.cam` nearly as fast as `SP.morph` |
| The shape runs off a 9:16 frame | zoom tuned for 16:9 | the page caps zoom at 92% width / 80% height; check every beat |
| The cursor leaves the frame in 9:16 | parked too far from the centre | park within about 300 world px of the centre |
| The page crashes in the first second | a lookup that is empty at t = 0 | guard every lookup that can be empty |
| An emoji counts as two letters when typing | strings indexed per UTF-16 unit | type with `[...TEXT]` |

## Sound

| Symptom | Cause | Fix |
|---|---|---|
| The voice turns robotic halfway | one long TTS take of the whole script | one sentence per call |
| The voice reads the style out loud | the style was in the text field | the style in the provider's style/instruction field; check WER |
| A brand name comes out as another word | a pronunciation hint in another language, or bad luck | no hint, 4 to 9 takes, keep one Whisper hears right |
| A name comes out as a variant | the model's guess | more takes; compare by sound (`vo_check.py compare`) |
| Lyria returns mp3, a different tempo and key | it ignores those requests | `music.py` names the file by its bytes; `beats.py` measures |
| Lyria returns nothing (PROHIBITED_CONTENT) | a long, detailed prompt | a short prompt: genre, BPM, instruments, mood, "no vocals" |
| The picture drifts off the music | the grid built on the asked tempo, or `T` not whole frames | `T` from `beats.py`, whole frames; the music is resampled to exactly `T` |
| A seam in the music loop | cut off a phrase, or chords that don't line up | cut on downbeats in whole 16-beat phrases; check with `beats.py --segments` |
| No good seam at the length you want | the song's phrases don't fit that length | try other lengths (12 bars may work where 13 doesn't) |
| A UI sound early or late | placed by the start of the file | placed by its measured peak (automatic) |
| True peak a bit over the ceiling in the mp4 | AAC encoding overshoots a little | `qa.py` allows 0.3 dB; lower `mix.true_peak` if it fails |
| The voice level jumps between lines | takes come out at different levels | every line is levelled to the same speech RMS (automatic) |
| Lines don't fit the loop | about 3 words per second, plus silence in the files | measure speech without silence, `atempo` up to 1.07 on easy lines, or cut words |
| A caption has a wrong word | Whisper misheard | captions come from the script; Whisper only gives timing |
| The final file is short by a few frames | ffmpeg `-shortest` | `-af apad -t <frames / fps>` (finish.py does this) |

## Tools

| Symptom | Cause | Fix |
|---|---|---|
| `CERTIFICATE_VERIFY_FAILED` from Python | the python.org Python on macOS has no CA bundle | `pip3 install certifi`; the scripts use it (`common.ssl_context`) |
| faster-whisper can't download its model (SSL) | the same missing CA bundle | `SSL_CERT_FILE` = certifi's bundle (the scripts set it) |
| `timeout: command not found` | macOS has no `timeout` | leave it out |
| `npx hyperframes`: "canceled due to missing packages" | the CLI isn't installed (only `sticker.py --remove-bg` uses it) | ask first, then `npx --yes hyperframes …`, or cut out the photo elsewhere |
| The key's usage rose more than your calls cost | other projects share the key | count your own calls (the scripts print each cost) |
| A zsh command chain stops halfway | an unmatched glob, or `echo ====` | `setopt NULL_GLOB`, and quote odd strings |
| A shell command in a synced folder hangs | iCloud or Dropbox is fetching a file | stop it and retry; render in a local folder |
| The disk fills during a render | frames written as images | the renderer pipes frames into ffmpeg; nothing touches disk but the lossless chunks |
| The machine crawls during a render | too many workers for the RAM | `check_env.py` suggests a worker count; one render at a time |
| Sending a file from an agent fails | a relative path | absolute paths |
