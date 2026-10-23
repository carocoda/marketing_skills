# Ad analyzer

A skill for Claude and ChatGPT that audits your Meta ads campaign the way a good media buyer would: from the first impression to the actual sale. Most campaigns don't fail on the ad itself. They fail on the setup, the tracking or the math. This skill checks all of it and tells you what to change first.

**What it does**

- Asks a few questions first: what you sell, the result that counts, your target, where the sale happens and how it can see your numbers
- Reads your numbers per ad in Ads Manager (read-only, in the browser) or from an export or screenshots
- Checks the setup: objective, optimisation event, placements, audience, budget, end date, drafts nobody published
- Checks tracking: which events the pixel actually received, and the sales on your own checkout or ticket platform as the source of truth
- Looks at every creative: stopping power, hook, offer, proof, visuals, CTA, with video frames and a transcript
- Compares with current benchmarks, labelled as official, practice or its own calculation
- Does the math: cost per visit, expected sales, cost per sale, and what your remaining budget can still buy
- Ends with advice in order of impact, the exact place to change each thing, and a stop rule

It can also tear down a single ad, yours or a competitor's from the Meta Ad Library: scores, three ideas worth borrowing, three fixes and three test variants.

It never changes anything in your ad account. It reads, and you decide.

## Use it

**Claude Code or Codex (full version, including video).** Copy the `ad-analyzer` folder into `.claude/skills/` (or `~/.claude/skills/`) and restart; for Codex use `~/.codex/skills/`. Then say "check my Meta campaign" (with Ads Manager open in a browser Claude can use, or with an export), or "analyse this ad: ~/Downloads/ad.mp4".

**ChatGPT or Claude in the browser.** Upload the folder as a skill (ChatGPT: Plugins > Skills > Create > Upload; Claude: Settings > Capabilities > Code execution on, then Customize > Skills > Upload a skill, as a ZIP). Share screenshots of Ads Manager (the Ads tab with the columns from `references/campaign-audit.md`), or an export, and ask for an audit. Video files may not work there: send screenshots of the opening, key moments and the end card instead, plus the spoken text.

## What it needs

- **For exports:** Python with `pandas` (`pip install pandas`, plus `openpyxl` for Excel files). Most code environments already have it.
- **For video files:** `ffmpeg`
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

- Benchmarks date quickly and many come from vendors. The skill labels each one and searches for newer figures when it can.
- The hook rate and fatigue thresholds are rules of thumb. Your own account history is the better benchmark, so the skill compares ads within your export first.
- Ads with under ~1,000 impressions or fewer than 5 results are shown as "not proof yet".
- Export column names differ per account and language. The skill maps what it finds and tells you what's missing.
- For competitor ads it takes the idea, never the copy or the visuals.
- Speech-to-text gets brand names wrong now and then. The skill checks them against what's on screen.

## License

MIT, see [LICENSE](LICENSE).
