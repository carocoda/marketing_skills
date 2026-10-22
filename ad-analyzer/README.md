# Ad analyzer

A skill for Claude and ChatGPT that tells you why an ad works or doesn't. It does two things:

**A. Tear down one ad.** Your own or a competitor's: a video file, an image, a screenshot or a Meta Ad Library link.
- Scores stopping power, hook, offer, proof, visuals and CTA from 1 to 10, with one line each
- Lists 3 things worth borrowing (the idea, not the words) and 3 concrete fixes
- Writes 3 test variants that each change one thing, so the test tells you something
- For video, pulls out frames (every second, plus the first 3 seconds up close) and a timestamped transcript

**B. Crunch your Ads Manager export.** A CSV or Excel file at ad level.
- Calculates hook rate, hold rate, CTR, CPM, CPC, frequency and cost per result, and shows the formulas
- Ranks the ads, and keeps ads with too little data apart instead of calling them winners
- Names the weak link per ad (the opening, the middle, the landing page, the audience)
- Says what to turn off, what to scale and what to test next

For your own ads it first asks a few short questions (the result that counts, a good cost per result, your audience, your landing page, your house rules), each with a default so "ok" works. It can save the answers to `ad-profile.md` so it doesn't ask again. It replies in your language.

## Use it

**Claude Code or Codex (full version, including video).** Copy the `ad-analyzer` folder into `.claude/skills/` (or `~/.claude/skills/`) and restart; for Codex use `~/.codex/skills/`. Then say "analyse this ad: ~/Downloads/ad.mp4" or "which of my ads works best?" with your export.

**ChatGPT or Claude in the browser.** Upload the folder as a skill (ChatGPT: Plugins > Skills > Create > Upload; Claude: Settings > Capabilities > Code execution on, then Customize > Skills > Upload a skill, as a ZIP). Share a screenshot, image or export and ask for an analysis. Video files may not work there: send screenshots of the opening, key moments and the end card instead, plus the spoken text.

## What it needs

- **For exports (mode B):** Python with `pandas` (`pip install pandas`, plus `openpyxl` for Excel files). Most code environments already have it.
- **For video files (mode A):** `ffmpeg`
  - macOS: `brew install ffmpeg`
  - Ubuntu/Debian: `sudo apt install ffmpeg`
  - Windows: `winget install ffmpeg`
- **For transcripts (optional):** `pip install faster-whisper` (preferred). The `openai-whisper` CLI works too. Without either, the skill works from the frames and says so. The first run downloads a speech model (the default `small` is about 0.5 GB; `large-v3`, best for non-English, is about 3 GB).

No API keys. Nothing is sent anywhere: transcription runs on your machine.

The helper script on its own:

```bash
python3 scripts/extract.py ad.mp4 --out ./ad-analysis/my-ad            # language detected from the ad
python3 scripts/extract.py ad.mp4 --out ./ad-analysis/my-ad --lang nl --model large-v3
python3 scripts/extract.py --help
```

## Good to know

- The hook rate and fatigue thresholds are rules of thumb. Your own account history is the better benchmark, so the skill compares ads within your export first.
- Ads with under ~1,000 impressions or fewer than 5 results are shown as "not proof yet".
- Export column names differ per account and language. The skill maps what it finds and tells you what's missing.
- For competitor ads it takes the idea, never the copy or the visuals.
- Speech-to-text gets brand names wrong now and then. The skill checks them against what's on screen.

## License

MIT, see [LICENSE](LICENSE).
