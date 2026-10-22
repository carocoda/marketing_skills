# Story and copy

The user's own tone rules (a profile, a brand guide, a `CLAUDE.md`) win over this page.

## What these videos are for

Getting the right people excited to try, join or buy. So the video shows what people make, do or get, operated by a
cursor, rather than claiming it. One promise, shown in steps, one call to action.

## Story shapes

**A. Product or feature promo (the template).** Promise → what it is in one line → three to six things it does,
each operated by the cursor → the payoff (it adds up, it repeats, it's done) → the CTA → back to the tile.

| Beats (of 64) | What happens | Voice |
|---|---|---|
| 0-7 | The click on the tile blows open the title window: bursts, ripple, the headline slams in, a sticker, doodles | the promise |
| 7-17 | Title pill, then a facts pill with chips | what it is, who it's for |
| 17-38 | Two to four product moments, each clicked, typed or dragged | what you do with it |
| 38-44 | Something that repeats or adds up | the payoff |
| 44-64 | The button asks, becomes the CTA, offer sticker, url; a click goes home | the CTA |

**B. Event promo.** Promise → hosts as photo stickers with name tags, then the date pill with chips (time, place,
tools) → three to six things you make or learn that day → the vibe of the day (the social part) → the CTA with the
price on the sticker. A 96-beat version (50 s at 115 BPM) worked well.

**C. Offer or ad (15 to 25 s, often 9:16).** A hook that speaks to the audience ("Are you a … who …?" is fine as an
audience call-out) or shows the outcome, two or three moments, the CTA. Captions on. Stay close to what the offer
really includes.

**D. Teaser (15 to 20 s).** The opening kit, one facts pill, the CTA kit. Two or three lines of voice, or none.

**E. Recap.** Real photos (only of people who agreed) as sticker or polaroid states the cursor flips through, a line
per moment, the next thing as the CTA.

## The hook

- The first line is the promise, said with energy, together with an opening animation that grabs (the opening kit).
- A question that asks the viewer whether they still do things the old way ("Still doing X by hand?") was found
  unconvincing as an opener. Lead with the promise, then show it.
- No price in the opening. It comes at the end, on the sticker.

## Writing the voice-over

- Talk to one person, as "you", warm and a bit playful, like inviting a friend.
- Concrete things people make or do, in one flowing sentence: "you cut a webinar into shorts, write the newsletter
  that goes with it, and turn your numbers into a dashboard that adds up".
- Sentences that connect ("And you…", "In the afternoon you…", "So…"). Read the joins out loud: two true sentences can
  suggest something false together.
- Invite and let people picture it. Describe what they discover, do and see. Avoid a strict imperative that lectures
  ("Learn it yourself first"); keep imperatives for the CTA.
- A "made with AI" line can be a nice proof point in a video about making things with AI, but in ads it can make
  the offer feel cheaper. Ask before using it.
- Don't name clients, partners or customers unless the user confirms it's allowed in this context (ads are stricter
  than a website).
- The CTA: one action and the url, spoken the way it should be heard.

## Copy rules (voice and screen)

- No em-dashes. On screen an en-dash only in ranges ("10:00–16:00").
- No "it's not X, it's Y", no rows of short statements, no deep-sounding metaphors.
- No hype words: game changer, unlock, supercharge, elevate, revolutionize, next level, seamless (the list lives in
  `project.json` → `copy.banned`; add the user's own banned words). `qa.py` checks screen and voice.
- English loanwords only where they're natural in the video's language.
- A price on screen with its currency sign, only on the sticker near the end, never spoken.
- Urgency is fine when it's true ("8 seats left").
- On-screen text is short: titles, labels, chips. The voice carries the sentences.

## Facts to verify before they go on screen

- Date, weekday, times, city, price, and whether an early-bird or launch price still applies: from the source the
  user names. When two sources disagree (an event page's cover image once showed a different date than its text),
  flag it and ask.
- The programme or feature list: only what will really happen or really exists.
- Tools and logos named: real names, logos only if the user may use them.
- Who stands where in a photo, before the name tags go on.
- Put the on-screen facts in `project.json` → `facts`; `qa.py` fails if one is missing from the page.
