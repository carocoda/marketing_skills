# Ad Edit

A skill for Claude and Codex that edits a talking-head phone recording into a video ad for Meta Reels, Stories and
feed (and TikTok or Shorts). You record yourself talking to camera; it does the edit.

**What it does**

- Asks about your brand first: name, logo, colours, fonts, look, call to action, music. It saves the answers, so the
  next ad doesn't ask again.
- Transcribes the take and proposes a plan: which sentences stay, which versions to make, which graphic lands on
  which word. It builds nothing until you say yes.
- Cuts the "uhs" and false starts without cuts you can hear. Every filler is checked in the audio signal before it goes.
- Turns a phone voice into a warm, dry studio voice (dereverb, noise removal, EQ presets you can compare).
- Adds a punch-in zoom on every cut, big word-by-word captions, and graphics on the spoken words: logos, photos, a
  date card, price card, poll, checklist, speech bubbles, an arrow to the button, and an end card.
- Mixes a music bed under the voice (your track, with its final hit on the end card) plus UI sounds.
- Renders 9:16 (Reels, Stories) and 4:5 (feed) in several versions, for example with and without an offer.
- Checks its own work before you see it: every cut in silence, Whisper over the final mix, a contact sheet of stills.
- Handles feedback rounds and only redoes what your remark touches.

It never posts anything. You upload the mp4s yourself.

## Use it

This skill renders video, so it needs an agent that can run scripts on your computer.

**Claude Code:** copy the `ad-edit` folder into your project's `.claude/skills/` (or `~/.claude/skills/` for every
project) and restart. Then say: "Edit this recording into an ad: ~/Movies/IMG_1234.MOV".

**Codex:** put the folder in `~/.codex/skills/` and ask the same.

**Claude or ChatGPT in the browser:** you can upload the folder as a skill, but a chat can't run ffmpeg or render
video. There it does the planning: the cut list, the versions, the graphics per sentence and the on-screen copy. Do
the render in Claude Code or Codex.

First time on a computer, run the check (it changes nothing):

```bash
python3 .claude/skills/ad-edit/scripts/check_env.py
```

Want to see it work before you use your own footage? This renders a test ad from a generated clip, with every graphic
type and no downloads (2 to 6 minutes):

```bash
python3 .claude/skills/ad-edit/scripts/demo.py ~/ad-edit-demo
```

## What it needs

| What | Why | Install |
|---|---|---|
| Python 3.9+ | runs everything | python.org, or your package manager |
| ffmpeg 6+ with libx264, prores_ks, aac | cutting, picture, voice EQ, mixing, export | macOS `brew install ffmpeg` · Linux `sudo apt install ffmpeg` · Windows `winget install ffmpeg` |
| numpy, Pillow | audio and image work | `pip3 install numpy pillow` |
| Playwright + Chromium | renders the graphics layer frame by frame | `pip3 install playwright && python3 -m playwright install chromium` |
| faster-whisper | words and timing, and the final check | `pip3 install faster-whisper` |
| Whisper large-v3 model (about 3 GB) | the transcript | downloads on first use into the Hugging Face cache; the skill asks first |
| nara_wpe (recommended) | removes room echo | `pip3 install nara_wpe` |
| DeepFilterNet `deep-filter` binary (recommended) | removes noise | download from [github.com/Rikorose/DeepFilterNet/releases](https://github.com/Rikorose/DeepFilterNet/releases) for your system, save it as `~/.local/ad-edit-tools/deep-filter`, `chmod +x` it. Without it the skill uses ffmpeg's weaker denoiser. |
| CrisperWhisper model (optional, about 3 GB) | sharper word timing (English and German work best) | downloads on first use of `crisper.py` |
| OpenCV (optional) | finds the face for the crop when the macOS helper is not built | `pip3 install opencv-python` |
| macOS helpers (optional, Mac only) | Apple's own HDR tone mapping and face tracking, best for iPhone footage | `xcode-select --install`, then `python3 scripts/check_env.py --build` |
| Internet while rendering | loads your Google Fonts | or use local font files in `brand.json` |
| Disk space | 5 to 10 GB per ad (two versions x two formats) | an external drive works; point `work` and `out` at it |

No API keys and no paid services. Everything runs on your computer. Environment variables you can set:
`AD_EDIT_TOOLS` (folder with `deep-filter` and the macOS helpers, default `~/.local/ad-edit-tools`),
`AD_EDIT_WORKERS` (overlay render processes, default 6), `AD_EDIT_LANG` (default language for the Whisper tools),
`AD_EDIT_WHISPER_MODEL` (default `large-v3`).

## Good to know

- **Record well and the rest gets easier.** A small, soft room, the phone at 40 to 60 cm at eye level, a clip-on mic
  if you have one, a few seconds of silence before and after, and say key facts (date, price) literally.
- **Shorter is better.** The skill will push for the short version first.
- **Music and logos:** only use a track and logos you have the rights to use in ads. The UI sounds are generated by
  the skill, so they are free to use.
- **Big files stay out of git.** New ad folders get a `.gitignore` for the work and export folders.
- **iPhone HDR footage** looks best with the macOS helper. On other systems the skill uses ffmpeg's tone mapping if
  your ffmpeg has `zscale`, and warns you if it doesn't.
- **Languages:** captions and Whisper work in any language Whisper knows. Set `--lang` (or `"language"` in
  `edit.json`) so short clips don't get detected as the wrong language.
- The process, the cutting rules and the voice presets came out of real feedback rounds on real ads. The lessons are
  in `references/lessons.md`.

## License

MIT, see [LICENSE](LICENSE).
