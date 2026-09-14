# Style 2: warm editorial (cream poster)

Warm, editorial-minimal, flat. No grid paper, no heavy shadows; thin outlines and
soft pastel tints on cream. Centred composition (playbook is left-aligned). Suits
"marketplace", "directory" and "capabilities" posters with many small items.

## Tokens

```css
:root {
  --paper: #f6f0e7;       /* cream background */
  --ink: #57504a;         /* warm dark grey, headings and body */
  --muted: #948b81;
  --terracotta: #a4623f;  /* bold part of the title */
  --orange: #e8963c;      /* section 1 and label pills */
  --mustard: #c2a23d;     /* section 2 */
  --sage: #8ba385;        /* section 3 and feature card 1 */
  --lavender: #978ab5;    /* feature card 2 */
  --rose: #c47f9b;        /* feature card 3, mega-card outline */
  --tint-peach: #f3ddc8;  --tint-khaki: #eae3bb;  --tint-sage: #dde4d4;
  --tint-lavender: #e3ddef;  --tint-rose: #f2dde6;
}
```

- **Background:** `--paper` plus a subtle paper grain. Grain recipe without
  external assets: 2-3 stacked `radial-gradient` speckles on 3-5px tiles with very
  low alpha, or an inline SVG `feTurbulence` noise as a data URI at `opacity: .04`.
  It must be almost invisible, only felt.
- **Typography:** Inter (headings 600/700 with a two-tone title; body 400/500),
  JetBrains Mono for tool and API names and mono lists. Signature: **small-caps
  letter-spaced labels** (11-12px, `letter-spacing: 2px`, uppercase) in solid pills.
- Outlines: 1.5px in the section colour, radius 16-20. Almost no shadow (at most
  `0 1px 2px rgba(87,80,74,.06)`).

## Fixed components

- **Header, centred:** small logo and name at the top, next to it a solid
  small-caps pill (a category label). Big title in two tones: the first words in
  `--ink` regular, the rest bold in the accent colour. Under it a **search-bar
  chip**: outline pill with an icon and one core claim (reuse this motif for the
  key stat).
- **Main columns (2-3):** white cards with a thin coloured outline. Head = outline
  icon tile + big title in the card colour; **dashed divider** under it; body =
  mono lines with mini icons. UNDER each card a stack of **chevron pills**: fully
  tinted pills (`›` + short benefit, dark text on the tint of the same hue).
- **Feature row:** 2-3 softly tinted cards (sage, lavender, rose) with a solid
  small-caps label pill, bold coloured heading and a small grey body text. One card
  may carry a small mascot accent in the corner.
- **Mega card / directory grid (optional):** one big outline container with a
  large word plus a count on the left, and inside it a masonry grid of small white
  mini-cards with a bold mini-title and rows of icon + name at 10-11px. For
  "many items" content (tools, providers, integrations).
- **Footer:** centred pill with round photo, name and site. Choose between the
  warm brown of this palette and your brand colour; a saturated blue can look hard
  on cream, so decide explicitly at the first example. Same choice for the title
  accent word (brand colour vs terracotta).

## Default animation for this style

Recipe 1 (marching dashed outline), cycling over the main columns in their own hue
(orange → mustard → sage), then optionally one round along the feature row. Thin
dashes (stroke-width 2.5) fit the thin outlines. Nothing else moves.

## Checklist

- [ ] Cream plus grain, no grid paper (that is playbook)
- [ ] Centred header with small-caps pill, two-tone title and search-bar chip
- [ ] Thin outlines, dashed dividers, chevron pills under the columns
- [ ] Mono lists for tools and features
- [ ] Mascot small as a corner accent, author pill at the bottom
- [ ] Accent-colour choice (brand vs terracotta) made explicitly
