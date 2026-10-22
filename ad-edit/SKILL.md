---
name: ad-edit
description: Edit a talking-head phone recording (someone speaking straight to camera, a selfie video, a founder or creator take, an .MOV or IMG_xxxx file) into a paid social video ad for Meta Reels, Stories and feed, TikTok or Shorts. Cuts the "uhs" and false starts without audible hiccups, turns a phone voice into a warm, dry studio voice, adds a punch-in zoom on every cut, big word-by-word captions, branded graphics that land on the spoken words (logos, photos, date, price, poll, checklist, arrow, end card), a music bed with UI sounds, in 9:16 and 4:5, in several versions (short/long, with or without an offer). Asks for brand colours, fonts, logo, CTA and music first, plans the cut and gets approval before it builds, reviews its own stills, and handles feedback rounds. Use whenever someone wants a recording, take, selfie video, talking head, UGC clip or founder video turned into an ad, reel or social video, or wants an existing video ad changed (cut, voice, captions, graphics, a new version), even if they don't say "edit" or "ad". Needs ffmpeg, Python and Playwright on the computer; in a plain chat it does the planning and copy only.
---

# Ad edit: talking-head video ads from real recordings

One recording of someone talking straight into the camera becomes a tight ad: the "uhs" out without a cut you can
hear, a warm voice, a punch-in on every cut, big captions, and graphics that land exactly on the words. The same
recording gives several versions (short and long, with and without an offer) in 9:16 and 4:5.

Reply in the user's language. All text on screen follows the brand's own tone and the language of the take.

## Where this runs

The render needs ffmpeg, Python, Playwright and Whisper on the user's computer (Claude Code, Codex, or another agent
that can run scripts). In a plain chat, do steps 0 and 1 (setup and plan: cut list, versions, graphics per sentence,
on-screen copy) and say that the render needs an agent that can run scripts, with a pointer to the README.

## The layout

`template/` holds a shared **engine** and a worked **example ad**. In the user's project it looks like this:

```
<ads>/                 for example ads/ or marketing/video-ads/ in their project
  _engine/             build.py, overlay.html, voice.py, the helper scripts, assets/sfx   (one per project)
  brand.json           colours, fonts, logo, CTA, URL                                  (from the setup interview)
  01-intro/            edit.json, notes.md, assets/ (photos, logos)                    (one per ad)
  02-.../
```

The engine holds no times, words or facts; everything for one ad lives in its `edit.json`
(`references/edit-json.md`). Run every command from `<ads>/`, with the ad folder as the first argument of `build.py`.
`<skill>` below means this skill's folder.

## The process

```
  0 SETUP ──── brand profile (once per brand): read it, or ask and write it
  1 PLAN ───── GATE: cut list + versions + graphics per sentence + voice + music + facts, in the chat. Wait for a yes.
      │
  2 PREPARE ── ad folder (and engine), prep (SDR, face, audio), voice, words
  3 CUT ────── segments, every filler proven, audit, audio, verify
  4 BUILD ──── shots, events, end card, plan without WARNING, stills
  5 SELF-REVIEW ── look at the contact sheet, run the checklist, only then render
  6 RENDER ─── build.py <ad> all → mp4s, send vN + changelog
      │
      └──◄── FEEDBACK ROUND: every remark word for word in notes.md → smallest change → redo only what depends on
             it (table below) → self-review → vN+1. Stop when they say it is done.
```

### 0. Setup: the brand profile

First look for an existing profile: `brand.json` in the ads folder, a `brand-profile.md` in the project, or brand
details earlier in the conversation or in project files (a style guide, a website's colours). Use what is there and
only ask what is missing. If nothing exists, send one message with these questions as a numbered list, each with a
default in brackets so "ok" is a valid answer, then stop and wait:

1. **Brand name and website** for the corner tag and the end card. [the name, no URL]
2. **Logo:** a file (PNG or SVG, transparent background works best), or show the name as text? [name as text]
3. **Colours:** your brand colours as hex codes, one dark for text and up to four accents. [neutral: off-white, near-black, yellow, mint, coral, periwinkle]
4. **Fonts:** a heading font and a label font (Google Fonts name, or a font file you own). [Archivo 800 and JetBrains Mono 700]
5. **Look:** bold (black borders, hard shadows) or flat and soft? [bold]
6. **Captions:** big capitals word by word, or sentence case? [capitals]
7. **Call to action** on the end card button, and what people should do. [LEARN MORE →]
8. **Music:** a track you have the rights to use in ads (a file), or no music? [no music, UI sounds only]
9. **Where the big files go:** video work files take 5 to 10 GB per ad. A folder or external drive? [inside the ad folder, kept out of git]
10. **Language** of the recording and captions. [the language spoken in the take]

Then write `<ads>/brand.json` (fields in `references/edit-json.md`) and offer to also save the answers as
`brand-profile.md` in their project, so the next run reads it instead of asking. In a chat-only setting, give the
answers back as a short block they can paste next time.

### 1. Plan and approval (first, always)

Transcribe the take first (steps 2 up to `words.py`), then send in plain text in the chat:

- **Cut list:** the sentences that stay, with what goes (fillers, repeats, false starts, sentences that aren't needed).
  Shorter is better: the first ad went from four versions to only the short one.
- **Versions and formats:** for example `A-offer` and `B-evergreen`, each in 9x16 and 4x5. Prices and deadlines only
  in versions that run before the deadline.
- **Graphics per sentence:** which word gets which picture (`references/graphics-kit.md`). Visual, not textual.
- **Voice:** the preset to start with (`warm`), or two to compare.
- **Music:** their track, synced to the end card or simple; or none.
- **Facts:** date, time, place, price, CTA, URL. Get them from the user or their landing page and repeat them back.
  Never guess a fact.
- **Downloads:** if the Whisper models are not on the computer yet (about 3 GB each), say what, from where and how big.

Then stop. Build nothing before a yes.

### 2. Prepare

```bash
python3 <skill>/scripts/check_env.py                     # once per computer; --build on a Mac for the HDR/face helpers
python3 <skill>/scripts/new_ad.py <ads>/<NN-name> --source "<path to the take>" --lang en
cd <ads>
python3 _engine/build.py <NN-name> prep                  # SDR ProRes, face track, 48 kHz audio
python3 _engine/voice.py "<work>/audio/src48.wav" "<work>/audio" --eq warm     # references/voice.md
python3 _engine/islands.py "<work>/audio/voice_warm.wav"                       # speech blocks
python3 _engine/words.py "<work>/audio/voice_warm.wav" "<work>/words_whisper.json" 7.7:11.2 11.2:16.3 ... --prompt "Brand, names, jargon." --lang en
python3 _engine/crisper.py "<work>/audio/voice_warm.wav" "<work>/words_crisper.json" --lang en   # optional, sharper times
```

`new_ad.py` makes the ad folder with `notes.md`, `assets/` and an empty `edit.json`, copies the engine into
`<ads>/_engine/` when it is not there yet, generates the UI sounds, and creates `brand.json` with neutral defaults if
it is missing. An existing engine stays as it is, because other ads run on it; if it differs from the skill, it says
which files. Update with `--update-engine` only when the other ads' `edit.json` still fits.

No HDR helper or face tracker? `prep` falls back to ffmpeg and OpenCV, or a fixed face position, and says so.
Check the crop in the stills.

### 3. Cut

Follow `references/cutting.md`. In short: segments in `edit.json`, every filler proven with `frames.py` (flat pitch),
`probe.py` and `splice_probe.py`, breathing pauses kept, then:

```bash
python3 _engine/build.py <ad> audit A-offer          # every cut in quiet, pauses long enough, or don't go on
python3 _engine/build.py <ad> audio A-offer          # mix: voice + music bed + UI sounds, -14 LUFS
python3 _engine/build.py <ad> verify A-offer         # Whisper over the final mix, next to the captions
```

### 4. Build

`shots` (zoom per cut), `events` (graphics on words), `endcard`, and `logos` and `photos` if used, in `edit.json`.
After every change:

```bash
python3 _engine/build.py <ad> plan A-offer 9x16      # timeline; fix WARNING lines first
python3 _engine/build.py <ad> base A-offer 9x16      # picture with zooms and grade (shots are cached)
python3 _engine/build.py <ad> stills A-offer 9x16 0.5 1.4 3.3 4.4 ...
```

### 5. Self-review (before the user sees anything)

Look at the contact sheet yourself (open the image) and go through this list:

- [ ] `audit` says "all cuts in quiet" for every version; `verify` misses no word and hears no left-over filler
- [ ] `plan` has no `WARNING` lines
- [ ] Every event lands on the right word, not too early (Whisper is often early)
- [ ] No text over the face; cards below the chest; everything inside the safe zones, in 4x5 too (`references/safe-zones.md`)
- [ ] Logos only of tools or partners that are named and that the user may show; photos real, without text, chosen by the user
- [ ] Date, time, price and deadline are right; price only in the offer versions
- [ ] Captions match word for word, names spelled right
- [ ] Brand colours and fonts came through (no font warning from `build.py`)
- [ ] On-screen copy in the brand's tone, no em dashes, nothing the user did not say or approve

### 6. Render

```bash
python3 _engine/build.py <ad> all A-offer B-evergreen --formats 9x16,4x5
```

Per version: audit (stops on a cut in voice), audio, base, overlay (Playwright, six workers) and final. Roughly three
to five minutes per version per format on a recent laptop. The mp4s (H.264 CRF 17, AAC 192k, -14 LUFS) land in `out`
as `<name>_<version>_<format>_<vN>.mp4`. Send them with a short changelog: what changed and how you checked it. Then
add a row to `notes.md`.

### Feedback round: what to redo after which remark

| The remark is about | Change | Then run |
|---|---|---|
| a cut, a filler, a hiccup | `segments` | `audit` → `audio` → `verify` → `base` → `overlay` → `final` |
| the length, a sentence out | `variants` | the same; check `plan` for `WARNING` |
| how the voice sounds | preset in `voice.py`, `files.voice` | `voice.py` → `audio` → `verify` → `final` |
| a word you can't hear | `voice_gain`, or `patch_voice.py` | `audio` → `verify` → `final` |
| music or sounds too loud/soft | `mix`, `SFX` in `build.py` | `audio` → `final` (no picture) |
| a graphic: text, place, moment | `events`, `endcard`, `LAYOUTS` in `overlay.html` | `plan` → `stills` → `overlay` → `final` (with sound changes also `audio`) |
| brand colour, font, logo | `brand.json` or `"brand"` | `stills` → `overlay` → `final` |
| zoom or crop | `shots`, `formats` | `base` → `final` |
| a caption | `words_fix`, `words_at`, `words_drop`, `words_add` | `plan` → `overlay` → `final` |

Raise `version` in `edit.json` every round. Move the previous exports to a subfolder (`old/vN/`), so only the latest
version sits on top.

## Hard rules

1. **Plan before anything.** Cut list, versions, graphics, voice, music and facts in the chat, then stop until there is a yes.
2. **Never cut inside voice.** A filler only goes when `frames.py` shows it (long, voiced, flat pitch) and
   `splice_probe.py` loses no word. A transcript label is not proof. `build.py audit` must be clean. Better a filler
   stays than a word gets hit.
3. **Whisper over the final mix.** After every `audio`: `verify`. A word Whisper does not hear is gone or unclear.
4. **Real people, real pictures.** Only recordings and photos of the people themselves, with their consent. No AI
   faces, no text on photos. Name tags on the right person. Logos only when the user may use them.
5. **Facts are right.** Every number and date on screen comes from the user or their landing page, repeated back in
   the plan.
6. **Ask before downloads.** A model or tool download (Whisper models are about 3 GB) needs an ok first: what, from
   where, how big.
7. **The overlay is a pure function of time.** `seek(t)` depends on `t` only: no CSS animations, timers or randomness.
   Otherwise the frames from the parallel workers don't match.
8. **Nothing goes out without a self-review.** Contact sheet seen, checklist done. Whatever is not right yet goes in
   the changelog.
9. **Media never goes into git.** The recipe (`edit.json`, `notes.md`, code) can; video and audio stay in `work` and
   `out`. If `work` is on an external drive that is not connected, `build.py` stops: ask the user to connect it, never
   create a stand-in folder on the internal disk.

## Files

```
SKILL.md                     this page
README.md                    install, dependencies, what it needs
references/
  cutting.md                 recognising fillers, never cutting inside voice, audit, pauses, Whisper and Crisper pitfalls, shots
  voice.md                   the chain (WPE, DeepFilterNet, EQ), the presets, sharp/warm/studio in numbers, patch_voice.py
  graphics-kit.md            the brand tokens, rules from feedback, every event type, the end card, making a new type
  safe-zones.md              9:16 and 4:5: what the platform covers and where the kit puts things
  music-and-sound.md         music bed (simple or synced to the end card), levels, UI sounds
  edit-json.md               every field of edit.json and brand.json
  lessons.md                 the feedback rounds and the rules that came out of them
scripts/
  check_env.py               can this computer edit ads? (--build makes the macOS helpers)
  new_ad.py                  new ad folder (and <ads>/_engine/, brand.json), empty edit.json
  demo.py                    dry run of the whole pipeline on a generated clip, every graphic type
template/
  _engine/                   becomes <ads>/_engine/ in the user's project
    build.py                 prep, plan, audit, audio, verify, base, stills, overlay, final, all  (ad folder first)
    overlay.html             all graphics, seek(t) → pixels, brand from brand.json
    voice.py patch_voice.py voice_metrics.py      voice chain, repair and measurements
    words.py crisper.py _whisper.py               words (Whisper large-v3) and word times (CrisperWhisper)
    frames.py probe.py splice_probe.py filler_scan.py energy.py islands.py   cutting tools
    beats.py make_sfx.py                          music beat grid, default UI sounds
    hdr_to_sdr.swift face_track.swift             macOS helpers (Apple tone mapping, Vision face tracking)
  brand.json                 the brand file with neutral defaults
  example-ad/edit.json       a worked example ad to read
```
