# Benchmarks and rules of thumb (checked October 2026)

These figures date quickly and most come from vendors. Search for newer numbers for the person's country, industry and product type when you can, and always label: **[O]** official (Meta or platform docs), **[P]** practice (agencies, vendors, marketers, often with a commercial interest), **[R]** your own calculation. The person's own history beats every number here.

## Learning phase and optimisation

- An ad set needs about 50 optimisation events within 7 days after the last significant edit, or it stays "Learning limited". Edits that reset it: targeting, placements, optimisation event, bid strategy, adding a new ad, a pause of more than 7 days, a large budget change. [O, via secondary source] https://ppc.land/learning-phase/
- Lower thresholds ("10 in 3 days", "25 purchases for Advantage+ Sales") circulate but aren't documented by Meta. [P]
- The algorithm works best on conversions and worst on link clicks and landing page views; turn off Audience Network on traffic objectives. [P] https://www.jonloomer.com/meta-ads-algorithm/
- With low purchase volume, a common route is optimising for the highest funnel event that fires often enough, knowing Meta then finds people who do that event, not necessarily buyers. [P]

## Targeting

- Advantage+ audience: Meta claims roughly 7 to 10% lower median cost per result in its own tests. [O, Meta measuring Meta]
- An independent test (2024, $2,250 spend, lead gen): Advantage+ audience 5% better than detailed targeting and 25% better than lookalikes, with identical ad sets differing up to 25%. At small volume much of the difference is noise. Broad targeting spent 25 to 35% on warm people on its own. [P] https://www.jonloomer.com/5-meta-ads-tests-targeting/
- Detailed targeting exclusions were removed in 2026 and interests are now suggestions under Advantage+; location, language, minimum age and custom audience exclusions are still hard limits. [O, via news source]
- Lookalikes need at least ~100 source people, preferably 1,000+. [P]
- Meta prefers audiences of 2 to 10 million; very small audiences can double the cost per result. [P]

## Costs (CPM, CPC, CTR)

| Market / segment | CPM | CPC | CTR | Source |
|---|---|---|---|---|
| Netherlands, average (range) | €9.40 (€5-15) | €0.72 | | [P] Searchlab, March 2026 |
| Netherlands, B2B services | €14 | €1.10 | | [P] Searchlab |
| Netherlands, education/training | €8 | €0.65 | | [P] Searchlab |
| Education (traffic, likely US) | | $0.70 | 1.50% | [P] LocaliQ/WordStream, Sep 2026 |
| Business services (traffic, likely US) | | $0.70 | 1.64% | [P] LocaliQ/WordStream |

- CPMs peak in November and December. [P]
- Website conversion from Meta traffic: often 1 to 3%. [P]

## Video

- Hook rate (3-second plays / impressions): under 25% fix the opening, 30 to 39% good, 35 to 45% top. Meta publishes no official benchmark. [P] https://billo.app/blog/hook-rate-to-hold-rate
- Hold rate (ThruPlays / 3-second plays): compare with your own 90-day average. [P]
- More than 75 to 80% of Reels views are with sound on: build for sound, add captions. [O]
- Meta's own creative study (December 2025): brand on screen max ~25% of the time, the product shown more than once, the CTA in picture and/or audio, speech plus music all link to higher purchase intent. [O] https://www.facebook.com/business/news/reels-creative-strategies
- 9:16 with audio and the message inside the safe zone: 34.5% lower cost per result than image ads on Reels. [O]
- Safe zone for 9:16 (third party, not confirmed by Meta): keep the top ~14%, bottom ~20 to 35% and ~6% at the sides free. [P]

## Creative variety

- Since 2025 Meta's ranking rewards creative diversification: different angles, people and formats. Near-identical ads are treated as one. [O, quoted via Jon Loomer] [P]
- The old "max 6 ads per ad set" guidance is gone; a few truly different ads beat many lookalikes at small budgets. [P]
- Fatigue signals: frequency of 2.5 to 3 per week on prospecting, 4 to 5 on retargeting; small audiences can tire in 3 to 5 days. [P]

## Events, workshops and launches

- Per ticket, aim for 15 to 25% of the ticket price as ad cost. [P] Webtonic (no source given)
- Phasing for events: start ~6 weeks out; roughly 20% announcement, 40% cold conversion, 25% retargeting in the last 2 weeks, 15% in the last 72 hours; exclude buyers everywhere. One burst in the last week overpays. [P]
- In the last week, concentrate on retargeting with "last spots" copy. [P]
- A retargeting audience needs at least ~100 people, better 1,000. [P]
- Formats that tend to work for events: short video with the hook in the first 2 seconds, name, date, place and CTA on screen; 2 to 3 variants that differ in hook; a short testimonial for people who already consider buying. [P]

## Attribution and tracking

- Default attribution: 7-day click, 1-day engage-through, 1-day view. Since March 2026 likes and saves count as engage-through. Keep 7-day click for purchases; view-through inflates results, especially on retargeting. [P] https://www.jonloomer.com/meta-ads-attribution-2026/
- Without the Conversions API, vendors claim 25 to 60% of conversions go missing. Those vendors sell CAPI. [P]
- Linking ads straight to the checkout platform keeps the click ID on the domain where Purchase fires; via your own site it gets lost unless you pass it on. [O] https://developers.facebook.com/docs/marketing-api/conversions-api/parameters/fbp-and-fbc
