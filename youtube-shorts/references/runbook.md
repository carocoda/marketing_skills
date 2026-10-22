# Runbook: one short, start to finish

`SK` = this skill's folder. `OUT` = the short's own folder in the user's project, for example
`shorts/<long video title>/short-01-<slug>/`. All commands run from `OUT` unless said otherwise.

```
shorts/<long video title>/
  series.md                      # table of shorts: title, hook, windows, status
  transcript/words.json          # word list of the long video
  spec.json, spec.snapped.json   # chosen windows for the whole series
  sfx/                           # make_sfx.py output (shared)
  end-screen/                    # one end screen per long video (HyperFrames path)
  short-01-<slug>/
    Short 1 - <title>.mp4        # the upload
    Short 1 - <title>_preview.mp4
    plan.json
    work/                        # clip.mp4, words.json, captions, stage files
    hf/<graphic>/                # one HyperFrames composition per idea
    sheet.png                    # review stills
```

## 0. Word list of the long video

Pick the first that applies:

```bash
# HyperFrames installed (local Whisper, downloads a model on first run)
npx hyperframes transcribe long.mp4 --model small.en            # English
npx hyperframes transcribe long.mp4 --model small --language nl # any other language: never a .en model
# openai-whisper installed (pip install openai-whisper)
whisper long.mp4 --model small --word_timestamps True --output_format json
# only subtitles (YouTube Studio > Subtitles > download .srt)
python3 $SK/scripts/words.py captions.srt -o transcript/words.json   # word times are estimated
```

Then normalise and read it: `python3 $SK/scripts/words.py <file> -o transcript/words.json`.

## 1. Pick the windows (series level)

```bash
python3 $SK/scripts/find_shorts.py sentences transcript/words.json > transcript/sentences.txt
python3 $SK/scripts/find_shorts.py candidates transcript/words.json --min 35 --max 60
```

Read the sentences, propose the table in chat, get approval, write `spec.json` (format in the
script's `--help`). Then:

```bash
python3 $SK/scripts/find_shorts.py snap spec.json --words transcript/words.json --video long.mp4
```

Fix every `!` line (move the edge, pick another hook) and run `snap` again until it says
`0 warning(s)`, or you and the user accept the remaining ones.

## 2. Find the speaker, cut the clip

```bash
python3 $SK/scripts/contact_sheet.py long.mp4 --every 90 -o ../speaker.png   # where is the face?
python3 $SK/scripts/cut_short.py --src long.mp4 --spec ../spec.snapped.json --short 1 \
   --aspect 9x16 --center 0.55 --words ../transcript/words.json \
   --out work/clip.mp4 --words-out work/words.json
python3 $SK/scripts/contact_sheet.py work/clip.mp4 --every 6 -o work/clip-sheet.png    # face in frame?
```

Add `"punch": [t, ...]` to a window for cuts inside it that need hiding (the long video's own
edit points). `--zoom 1.0` turns the punch-ins off.

## 3. Fix the words

```bash
python3 $SK/scripts/words.py work/words.json --prose     # read it. homophones, names, tense
python3 $SK/scripts/words.py work/words.json --sheet     # word@time, for timing graphics
```

Fix the `text` fields in `work/words.json`. Re-print after fixing.

## 4. Graphics (HyperFrames path; skip for captions only)

```bash
mkdir -p hf && cp -R $SK/templates/graphics/title hf/title
cp -R $SK/templates/graphics/<closest pattern> hf/<idea>
# edit index.html: brand block, words, sizes, times relative to the element's t0
cd hf/<idea>
npx hyperframes check                 # must end "Check passed"
npx hyperframes snapshot --at 2.5     # one --at per run; copy the png aside if you need several
npx hyperframes render --format mov   # transparent movie in renders/
```

Look at the snapshots tiled on one sheet before you render. End screen, once per long video:

```bash
cp -R $SK/templates/graphics/end-screen ../end-screen && cd ../end-screen
# edit the BRAND block and TEXT 1-4
npx hyperframes check && npx hyperframes render --format mp4
```

Pin the version once a series works (`npx hyperframes@<version> ...` in package.json) so later
renders look the same.

## 5. Sounds

```bash
python3 $SK/scripts/make_sfx.py --out ../sfx        # once per series
```

Or use the user's own sounds and music. Three effects per short at most.

## 6. Plan and build

Copy `$SK/templates/plan-9x16.json` (or `plan-16x9.json`) to `plan.json`, set the paths, the
title, the elements (`t0`/`t1` on words, `pos`, `w` = canvas width), the sfx times and the end
screen. Then:

```bash
python3 $SK/scripts/assemble.py plan.json --seconds 12    # fast check of the opening
python3 $SK/scripts/assemble.py plan.json --preview       # full build + small preview
```

It prints `DONE` when the frame count matches (clip frames + end screen frames).

## 7. Review

```bash
python3 $SK/scripts/contact_sheet.py "Short 1 - <title>.mp4" --at 0.5 <each graphic's busiest moment> <end screen> -o sheet.png
```

Look at the sheet: no graphic over the face or hands, captions readable and inside the safe
zone, arrows visible, end screen text right. Then send the preview to the user with what is in it
and the one or two questions you want answered. Build the next short after their verdict.

## Captions only, in one line

No graphics, no plan file needed:

```bash
python3 $SK/scripts/captions.py work/words.json --burn work/clip.mp4 "Short 1 - <title>.mp4" --style bold --highlight "#FFD400"
```

Use `assemble.py` with a plan when you also want the Pillow title card, sounds, music and the end
screen.
