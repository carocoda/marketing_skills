# Style 1: playbook (grid-paper poster)

Dense, rich, "designed by hand". The quality bar: a bare or minimal data chart
looks cheap; density plus custom illustrations reads as quality. Left-aligned
composition.

## Tokens

```css
:root {
  --ink: #1b2740;        /* headings and body */
  --muted: #66738a;
  --blue: #2f7fe0;  --purple: #a855f7;  --green: #10b981;  --amber: #e8a020;
  --coral: #e87456;      /* send buttons, dots, small winks */
  --brand: #1E40AF;      /* title accent word, footer pill, author avatar */
  --card-border: #e3e8ee;
}
```

- Background (grid paper):

```css
background-color: #fdfdfd;
background-image:
  linear-gradient(rgba(216,224,235,.55) 1px, transparent 1px),
  linear-gradient(90deg, rgba(216,224,235,.55) 1px, transparent 1px),
  linear-gradient(rgba(226,232,241,.35) 1px, transparent 1px),
  linear-gradient(90deg, rgba(226,232,241,.35) 1px, transparent 1px);
background-size: 40px 40px, 40px 40px, 10px 10px, 10px 10px;
```

- Fonts: **Poppins** 700/800 (title 44-50px, card titles 21-23px, big numbers),
  **Inter** 400-800 (body 14-16.5px), **JetBrains Mono** (prompt chips, source
  tags, footnotes).
- Section colours cycle blue → purple → green → amber (repeat above 4 sections).

## Fixed components

- **Header:** optional mascot left (110-134px, pose matched to the topic), Poppins
  title with ONE accent word in `--brand`, grey subtitle 19-21px. Optional yellow
  marker highlight in the subtitle
  (`mark { background:#EFE68B; border-radius:6px; padding:1px 7px; }`).
- **Section cards:** white `rgba(255,255,255,.97)`, border 2px `--card-border`,
  radius 18, shadow `0 10px 26px rgba(22,35,56,.09)`, padding about 16-21px 20-24px.
  Card head: icon tile (40-50px, tint `rgba(colour,.12)`, radius 12-14, stroke icon
  in the card colour) + Poppins title + optional mono source-tag pill.
- **Numbered badges** (steps, lists): 30-32px rounded square in the card colour,
  white bold digit.
- **Visual box** (screenshots, mock UI, illustrative lists): fixed height 220-240px,
  radius 12, 1.5px border `#dfe5ee`, white background, `overflow: hidden`.
  Screenshots inside with `object-fit: contain`; a tall list can run past the
  bottom with a white fade so it reads as "continues".
- **Prompt chips** (prompts, quotes): `#f5f7fa` background, border 2px `#e2e8f0`,
  radius 12, JetBrains Mono 14-16px, text between real quotation marks, coral send
  button (28-30px circle, white ↑) on the right, vertically centred. Placeholders
  like `[roles]` in the section colour.
- **Chat mock** (when a card shows "hand it to the AI"): a warm off-white panel
  (`#fbfaf7`) with a small "NEW CHAT" label, an attached-file pill in mono, and the
  prompt chip. Reads as a chat window without pretending to be a specific product.
- **Instruction line** under the visual: Inter 15.5px 500, `#3f4d63`, the key
  action in bold ink.
- **Payoff lines:** `↳` in the section colour + Inter 15-16.5px `#66738a`.
- **Custom SVG illustrations** per section when there is no screenshot (inline,
  stroke 2-3.5, rounded caps). Never emoji, stock images or CSS pseudo-element
  hacks. Examples: cards → database, rubric → clipboard, docs → robot judge, loop
  arrows → bars, bar charts with chip and quote bubble (bubble: white rounded rect
  plus a rotated square tail).
- **Takeaway band:** full width under the grid, `#eef3fb` background, 2px border
  `#d6e2f5`, radius 14, a big opening quote mark in `--brand`, Inter 19px 600 ink
  with the key phrase in `--brand` 800, `text-wrap: balance`.
- **Footnote line:** coral dot + JetBrains Mono 14px grey, centred (for example
  "full walkthrough in the comments").
- **Footer pill:** `--brand` background, radius 999, shadow
  `0 10px 24px rgba(30,64,175,.35)`, author photo (38px circle, border
  `--brand-soft`) + `AUTHOR NAME` white 800 + `· yoursite.com` in `--brand-text`.

## Layout patterns

- **2x2 steps with visuals** (the default for how-to content): header, four cards
  in a 2-column grid (gap 20-22px), takeaway band, footnote, footer pill. Fits
  1080x1350 with visuals of about 230px and two text lines per card. Template:
  `templates/steps-2x2.html`.
- **Stacked steps with a rail:** four full-width cards (text left, illustration
  right, 316px column) and a vertical rail down the left margin with a comet that
  returns to step 1 (recipe 4).
- **Chip list:** 6-8 prompt chips full width, each with its own colour, chip cycle
  animation (recipe 3). Optional AI-chat sidebar frame (below).

## Variant: chat-sidebar frame (optional, "inside the assistant")

For AI-assistant topics: a 236px sidebar on the left in a warm ivory
(`#f5f3ee`, right border `#e6e2d8`) with a small logo and product-neutral name, a
white "New chat" button with a coral plus, a `RECENTS` label with about 10 items at
13.5px (active item: `#eae6dc` background; titles may wink at the content and
truncate with dots), and at the bottom the author avatar (36px circle in `--brand`)
+ author name + workspace name. The main column becomes `inset: 0 0 0 236px` with
its own padding; everything scales slightly narrower.

## Default animation for this style

Recipe 1 (marching dashed outline) from `animation-recipes.md`, in the section
colours. For chip posters: recipe 3. Nothing else moves.

## Checklist before rendering

- [ ] Canvas exactly 1080x1350 and visually filled (no empty band under the pill,
      no half-empty cards)
- [ ] One accent word in the title, in `--brand`
- [ ] Every section has its own colour, icon tile, and a visual (screenshot, mock,
      list or custom SVG)
- [ ] All numbers traceable to a source; copy read out loud
- [ ] Footer pill in `--brand` with author photo and site
- [ ] Animation is one calm concept, seamless loop, poster itself static
- [ ] Checked at feed size (555px wide); nothing under 14px on the 1080 canvas
