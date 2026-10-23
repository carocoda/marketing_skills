# Campaign audit: what to collect and what to check

Read-only throughout. In Ads Manager you can open edit screens to read settings; close them with Cancel or Close. Never Publish, Save, Turn off, Delete or Duplicate. If a "Review and publish (n)" counter shows drafts, list what they are and leave them.

## 1. Ads Manager: the numbers

Set the date range to the full campaign (and note it). Use the Ads tab, not only Campaigns, so you get numbers per ad.

Columns to add (Columns > Customize columns), or read from an export:

| Group | Columns |
|---|---|
| Delivery | Amount spent, Impressions, Reach, Frequency, CPM |
| Clicks | Link clicks, CTR (link click-through rate), CPC (cost per link click), Landing page views |
| Results | Results, Cost per result, plus the specific event (Purchases, Leads, Registrations) |
| Video | 3-second video plays, ThruPlays, Video plays at 25/50/75/100% |
| Quality | Quality ranking, Engagement rate ranking, Conversion rate ranking |

Calculate yourself where Meta doesn't:

- Hook rate = 3-second plays / impressions
- Hold rate = ThruPlays / 3-second plays
- Cost per landing page view = spend / landing page views
- Click to landing page view = landing page views / link clicks (low = slow page or accidental clicks)

## 2. Ads Manager: breakdowns

Breakdown > By delivery: Placement, Age, Gender, Region, Country. Per row: spend, impressions, CPM, link clicks, CTR.

What to look for: one placement with a CPM several times the rest, spend going to an age group that can't be the buyer, impressions outside the intended country.

## 3. Ads Manager: settings

Campaign level:
- Objective (Sales, Leads, Traffic, Engagement, Awareness)
- Advantage+ campaign budget on or off, spending limit

Ad set level (Edit, then read):
- Conversion location (website, app, form) and the optimisation event (Purchase, Lead, Landing page views, Link clicks)
- Pixel or dataset used
- Attribution setting (default now 7-day click, 1-day engage-through, 1-day view)
- Budget and schedule, including the end date
- Audience: locations, age, Advantage+ audience on or off, custom audiences, exclusions
- Placements: Advantage+ placements or manual, and which ones are on. Meta warns when fewer than 6 placements are selected.

Ad level:
- Destination URL and UTM parameters
- Primary text, headline, CTA button
- Advantage+ creative enhancements: which are on (music, image tweaks, text variations). They are often on by default.

## 4. Events Manager

- Overview: which events came in, how many, last received. A Purchase or Lead event that was never received means the campaign optimises blind.
- Diagnostics: warnings, domains that need verifying.
- Settings > Traffic permissions: is the checkout or ticket platform's domain allowed?
- If the pixel is shared between your site and a checkout platform, check that events are not mixed up (filter by URL).
- Has anyone done a test purchase and seen it arrive? If not, put it in the advice.

## 5. Where the sale happens (source of truth)

Ask for or read: sales or sign-ups in the period, revenue, discount codes used, date of the last sale, and source per buyer if the platform keeps it (utm_source, utm_campaign, fbclid).

Platform notes:
- **Ticket platforms (Luma, Eventbrite, Tito and the like)** often send only a few fixed pixel events (for example PageView, CompleteRegistration, Purchase) and keep UTM data per guest in their export. Check their docs for the current list.
- **Own site with a checkout tool:** check the checkout tool also fires Purchase, not only your site.
- **Bot visits:** landing page visits "from Meta ads" in cities with Meta data centres (Luleå, Clonee, Fort Worth, Forest City, Altoona, Prineville and others) are Meta checking the link.

## 6. The setup checklist

| Check | Bad sign | Typical fix |
|---|---|---|
| Optimisation event vs volume | Optimising for Purchase or Lead with almost no events | Optimise for the highest funnel event that fires ~50 times a week (landing page views, or a custom conversion), or accept "Learning limited" knowingly |
| Placements | Only Stories/Reels or one platform, high CPM | Advantage+ placements, add Feed with a 4:5 version, Audience Network off for traffic objectives |
| Tracking | Purchase never received, no test done | Test purchase, allow the domain, use UTMs and the platform's source report |
| Schedule | Ends before the deadline or the key sales window | Extend; for events the last two weeks usually sell most |
| Budget | Several ad sets with a few euros each | One ad set, enough budget to learn |
| Learning phase resets | Frequent edits to targeting, placements, event, new ads, big budget jumps | Batch changes, change budgets by ~20% max per step (rule of thumb) |
| Creative variety | Ads that differ only in the first line | 3 to 5 ads with a different angle, person or format |
| Fatigue | Frequency above ~2.5 to 3 per week on cold audiences | New concepts, wider audience |
| Copy | Price, date or deadline only in the image | Put the offer and the deadline in the first line of the primary text too |
| Retargeting | None, or buyers not excluded | A small retargeting ad set once there is traffic, buyers excluded |
| Landing page | Doesn't repeat the ad's promise or deadline, unclear place, date or spots | Match the ad; show scarcity only if it's real |

## 7. Notes to keep

Write down the date range, what you couldn't see and every assumption. They go in "Open points" in the report.
