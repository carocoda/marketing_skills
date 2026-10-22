---
name: ad-analyzer
description: Analyses ads, your own or a competitor's. (A) Tears down a single ad (video file, image, screenshot or Meta Ad Library link) on stopping power, hook, offer, proof, visuals and CTA, with scores, what to borrow, what to fix and three test variants. (B) Crunches an Ads Manager export (CSV or Excel) into hook rate, hold rate, CTR, CPM, CPC, frequency and cost per result, says which ads win and why, names the weak link per ad and what to test next. Use whenever someone types /ad-analyzer, asks to analyse, break down, review, score or roast an ad or a creative, shares a Meta Ads Manager export or ad report, asks which ad works best or why an ad isn't performing, or wants to dissect a competitor ad from the Ad Library. Replies in the user's language.
---

# Ad analyzer

Pick the mode from the input. Have both the creatives and the results? Do mode B first, then mode A for the winner and the biggest loser.

## Step 0: context (own ads only, keep it short)

If a file called `ad-profile.md` exists in the project, read it and skip these questions. Also skip anything already answered in the conversation or project files. For a competitor teardown, skip this step and only ask what the person wants to learn from the ad if that isn't clear.

For the person's own ads, ask in one numbered message, with a default in brackets so "ok" is a valid answer, then wait:

1. **The result that counts.** What should the ad get people to do? (my guess: from the export's result column)
2. **Target cost.** What cost per result is good for you? (default: rank within the account, no fixed target)
3. **Audience.** Cold, warm (visitors, followers) or a mix? (default: cold)
4. **Landing page.** Link to where the ad sends people, so I can check it matches. (default: skip)
5. **House rules.** Anything your ads must always or never do: words, claims, names, logos, subtitles? (default: none)

Offer to save the answers to `ad-profile.md` in their project (or as text they can paste next time, in a chat-only setup), so the next run doesn't ask again.

## Mode A: tear down one ad

### Get the input in

**Video file.** Run the helper script from this skill's folder (`scripts/extract.py`). It writes everything to an output folder, never next to the original:

```bash
python3 scripts/extract.py "<ad.mp4>" --out "<work-folder>/<ad-name>"
```

It writes `info.json` (duration, size, aspect ratio, audio yes/no), `frames/` (1 frame per second), `hook/` (the first 3 seconds at 4 frames per second) and `transcript.txt` with timestamps. Options: `--lang en|nl|de|...` to force a language (default: detected from the ad), `--model small|medium|large-v3` (default `small`; `large-v3` is more accurate for non-English speech but a large download), `--no-transcript`.

Transcription uses faster-whisper if installed (`pip install faster-whisper`), otherwise the openai-whisper CLI (`pip install openai-whisper`). If neither is installed, the script still makes the frames and `transcript.txt` says so: work from the frames only, read any on-screen captions yourself, and say clearly in the report that you had no audio transcript. Offer the install command, don't insist.

No script available (plain chat)? Ask for screenshots of the first frame, a few key frames and the end card, plus the spoken text if there is any.

Then:
- Look at **all** hook frames, and a representative selection of the rest (every scene change, the offer, the end card).
- Fix transcription errors yourself: brand and product names often come out wrong (like "Cloud" for "Claude"). Check them against what's on screen.
- English-only models (`*.en`) can't transcribe other languages. If the transcript looks like nonsense for a non-English ad, rerun with `--lang` and a multilingual model.

**Image or screenshot.** Just look at it.

**Ad Library link.** Open it in the browser if you can and read it: primary text, headline, CTA button, start date, platforms, number of versions. An ad that has run for a long time with many versions is likely a winner for that advertiser. If you can't open it, ask for a screenshot.

### Analysis (in this order)

1. **Stopping power (0 to 3 seconds, or the image itself):** what do you see and hear first? Would a thumb stop? With the sound off, does it still make sense?
2. **Hook:** the first line spoken or shown. Which mechanic: pain, curiosity, result, recognition, contrarian?
3. **Offer:** what you get, for whom, for what price, and why now (deadline, limited spots)?
4. **Proof:** real people, numbers, logos, demo, testimonials. What's missing?
5. **Visuals and pace:** subtitles, scene changes, safe zones (the Reels and Stories interface covers the top and bottom), brand recognition.
6. **CTA:** is it clear what to do next? Does the ad match the landing page?
7. **Format:** 9:16, 4:5 or 1:1, length, and does it fit the placement?

### Output
- A score from 1 to 10 for each part (stopping power, hook, offer, proof, visuals, CTA), with one line of explanation.
- **Borrow:** 3 things that work and that you can use in your own ads (the idea, not the words).
- **Fix:** 3 concrete changes.
- **Test variants:** 3 variants that each change one thing only (only the hook, only the visual, only the offer), so the test tells you something.

## Mode B: results from Ads Manager

### Input
A CSV or Excel export at ad level. Useful columns: impressions, reach, amount spent, link clicks, results and cost per result, 3-second video plays, ThruPlays, video plays at 25/50/75/100%.

Column names differ per account, preset and language. Read the header row, map whatever is there using `references/ads-manager-columns.md`, and list what you found, what you guessed and what's missing. Calculate with what's there. Watch for totals rows, numbers stored as text, decimal commas and daily breakdowns (see the reference).

No code available? Ask the person to paste the table, and calculate by hand for the top ads only.

### Calculate (with pandas, show the formulas)
- **CTR (link)** = link clicks / impressions
- **CPM** = spend / impressions x 1000
- **CPC** = spend / link clicks
- **Hook rate** = 3-second plays / impressions (rule of thumb: under 25% is weak, over 35% is strong)
- **Hold rate** = ThruPlays / 3-second plays
- **Cost per result** and **frequency** (impressions / reach; above ~3 on cold audiences hints at fatigue)

### Verdict
- Rank on cost per result, within one result type. An ad with fewer than ~1,000 impressions or fewer than 5 results is **not proof yet**: put it in a separate group instead of calling it a winner or loser.
- Name the weak link per ad: low hook rate = the opening; good hook but low hold = the middle; good CTR but expensive results = the landing page or the offer; high CPM = the audience or the placement.
- Add short advice: what to turn off, what to scale, what to test next week.

## Rules
- Never make up numbers. Only calculate with what's in the export, and say when a sample is too small.
- For a competitor's ad: take the idea, never copy their words or visuals.
- For the person's own ads: apply their house rules from step 0 to every suggestion and test variant.
- Keep the report short, with headings and tables. Advice first, details below.
- Write in the person's language. No hype words or AI phrases.
