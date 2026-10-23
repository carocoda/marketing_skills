---
name: ad-analyzer
description: Audits a whole Meta ads campaign and tells you why it does or doesn't sell, then what to change first. Reads the numbers in Ads Manager (read-only, in the browser or from an export), the campaign and ad set settings, the pixel events in Events Manager and the sales on your checkout or ticket platform, checks every creative, compares it all with current benchmarks, does the funnel math (cost per sale, break-even, what the budget can still buy) and ends with advice in order of impact, including a stop rule. Also tears down a single ad, yours or a competitor's from the Ad Library. Use whenever someone types /ad-analyzer, asks to check, analyse, audit or review their Meta, Facebook or Instagram ads or campaign, asks why ads get clicks but no sales, wants advice on ads for an event, webinar, workshop, course or product launch, shares an Ads Manager link, export or screenshot, or wants a competitor ad broken down. Replies in the user's language.
---

# Ad analyzer

Most campaigns don't fail on the ad. They fail on the setup (wrong optimisation event, too few placements, a pixel that never fired), on the math (the budget can't buy enough visitors to sell anything) or on the offer. So this skill looks at the whole chain, from impression to sale, before it says anything about the creative.

There are two modes:

- **Campaign audit** (the default): everything below, step 1 to 7.
- **Single ad teardown**: only step 5, for one ad or a competitor's ad. Use it when that's all the person asks for.

Never change anything in an ad account. Read, don't click Publish, Save, Turn off, Delete or Duplicate. If you notice unpublished drafts or changes you didn't make, report them and leave them alone.

## Step 1: the brief (one message, then wait)

If `ad-profile.md` exists in the project, read it and only ask what's missing. Skip anything already answered in the conversation. Ask in one numbered message, each with a default in brackets so "ok" is a valid answer:

1. **What you sell.** Product, event, course or lead magnet, the price and any price step (early bird, launch discount). (my guess from the ads)
2. **The result that counts.** Sale, ticket, sign-up or lead. And the date or deadline that matters. (default: the result Ads Manager optimises for)
3. **Target.** How many sales you need from ads, or a cost per sale you can live with. (default: I'll calculate break-even)
4. **Where the sale happens.** Your own site, a checkout tool, a ticket platform (Luma, Eventbrite, Tito), a form. (default: the landing page in the ads)
5. **Access.** How can I see the numbers?
   a. I'm logged in to Ads Manager in the browser you can use (read-only)
   b. an export (CSV or Excel) at ad level
   c. screenshots
   (default: a, falling back to b)
6. **Budget and dates.** Daily budget and end date, or what's left to spend. (default: from the campaign settings)
7. **House rules.** Words, claims, names or logos your ads must always or never use. (default: none)

Offer to save the answers to `ad-profile.md` (or as text to paste next time in a chat-only setup).

## Step 2: collect the numbers

Work through `references/campaign-audit.md`. In short:

- **Ads Manager, per ad:** spend, impressions, reach, frequency, CPM, link clicks, CTR (link), CPC, landing page views, results and cost per result, and for video: 3-second plays, ThruPlays. Plus the quality, engagement and conversion rankings.
- **Breakdowns:** placement, age, gender, region or country. Placement is the one that most often explains a high CPM.
- **Settings (open the edit screen, read only):** objective, optimisation event, conversion location, attribution window, audience and locations, Advantage+ audience on or off, placements, budget, schedule and end date, ads that are on or off, unpublished drafts.
- **Events Manager:** which events the pixel received (PageView, InitiateCheckout, Purchase or Lead), when it last saw each, diagnostics warnings, domains.
- **Where the sale happens:** sales or sign-ups in the period, by source or UTM if the platform shows it, discount codes used, the last sale date. This is the source of truth; Ads Manager only counts what it can attribute.

Exports: map the columns with `references/ads-manager-columns.md`. Calculate with pandas and show the formulas. Never make up a number. If you can't see something, say so and say how to get it.

## Step 3: check the setup

Go through the checklist in `references/campaign-audit.md`. The usual suspects:

- **Optimising for an event that never happens.** A campaign optimised for Purchase with zero purchases on the pixel can't learn. Meta needs roughly 50 optimisation events per ad set per week to leave the learning phase. Small sales volumes never get there.
- **Placements too narrow.** Stories or Reels only, or a single platform, usually means a much higher CPM.
- **Tracking not proven.** No test purchase seen in Events Manager, the checkout platform's domain not allowed, the pixel shared with another site.
- **Schedule.** End date before the deadline, or the budget runs out before the moment people buy (for events: the last two weeks).
- **Budget spread thin.** Several ad sets that each get too little to learn.
- **Small samples.** Under ~1,000 impressions or under 5 results per ad is not proof. Say "not proof yet" instead of naming a winner.
- **Bot traffic.** Visits from cities with Meta data centres (Luleå, Clonee, Fort Worth, Forest City and the like) on the landing page are link checks, not people.

## Step 4: benchmarks and research

Compare with `references/benchmarks.md`. Those figures are dated and mostly from vendors: if you can search the web, check for newer numbers for this industry, country and product type, and label every figure:

- **[O]** official, from Meta or the platform's own docs
- **[P]** practice: agencies, vendors, marketers (often with a commercial interest)
- **[R]** your own calculation

The person's own history beats any benchmark. When there's no reliable benchmark (often the case for niche B2B offers), say so.

## Step 5: the creatives

For each ad (or the one the person asked about):

- **Get it in.** Video file: run `python3 scripts/extract.py "<ad.mp4>" --out "<work>/<ad-name>"`. It writes `info.json`, one frame per second, the first 3 seconds at 4 frames per second and a timestamped transcript (faster-whisper, or the openai-whisper CLI, or frames only if neither is installed). Options: `--lang`, `--model`, `--no-transcript`. In Ads Manager: open the ad preview. Ad Library link: read text, headline, CTA, start date and number of versions (long-running ads with many versions are likely winners). No tools: ask for screenshots of the first frame, key frames and the end card.
- Check brand names in the transcript against the screen ("Cloud" for "Claude" is a classic).
- **Score 1 to 10, one line each:** stopping power (first 3 seconds, sound off too), hook, offer (what, for whom, price, why now), proof, visuals and pace (captions, safe zones, brand max ~25% of the time), CTA and match with the landing page, format fit for the placement.
- Tie it to the numbers: low hook rate = the opening; good hook, low hold = the middle; good CTR, no sales = landing page, offer or tracking; high CPM = placement, audience or a low quality ranking.
- **Single ad teardown output:** the scores, 3 things worth borrowing (the idea, never the words), 3 fixes, 3 test variants that each change one thing.

## Step 6: the math

Do it in a small table, and show it:

- Cost per landing page visit now, and at a normal CPM for this market.
- Expected sales = visits x conversion rate (use the person's own rate if known, otherwise a range from the benchmarks, say 1 to 3%).
- Cost per sale now and after the fixes.
- Break-even or target: the price, minus costs, or the agency rule of thumb of 15 to 25% of the price per sale for events.
- What the remaining budget can still buy before the deadline.

If the numbers say ads alone can't hit the target, say it plainly and point to the channels that can (email list, past buyers, partners, direct outreach).

## Step 7: the report

Advice first, details below. Short, with headings and tables.

1. **Verdict in 3 to 5 lines.** What's going on, in plain words.
2. **The numbers.** One table per ad, plus totals.
3. **Advice in order of impact**, each with the reason and the exact place to change it in Ads Manager:
   - the fastest route to sales (often warm channels before a deadline)
   - setup fixes (optimisation event, placements, schedule, budget)
   - creatives (what to cut, what to add: real variety in angle, person and format, not just a new first line)
   - retargeting (who, when, budget, exclude buyers)
   - the landing page or checkout
   - measurement (source of truth, test purchase, UTMs)
4. **A stop rule.** For example: "No sale with source = Meta after €X spend: stop prospecting, keep retargeting only."
5. **Open points.** Drafts you saw, data you couldn't reach, what you assumed.

Offer to write it as a page or document the team can read.

## Rules

- Read-only in every account. Never publish, save, pause, delete or edit. Logging in is the person's job; never type passwords.
- Never make up numbers. Label benchmarks with their source and date, and say when a sample is too small.
- For competitor ads: take the idea, never their words or visuals.
- Apply the house rules from step 1 to every suggestion.
- Write in the person's language. No hype words or AI phrases.
