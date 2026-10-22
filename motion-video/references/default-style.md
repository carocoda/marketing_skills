# The default style, and how to make it the user's own

The template ships with a neo-brutalist pastel look: cream canvas, ink lines, hard shadows, one pastel per moment,
stickers slapped on at an angle. Playful and sharp. It is a good default because it reads well at phone size and
looks designed rather than templated. But it is only a default: the user's brand wins. Everything below lives in
`BRAND` (and a few CSS classes) at the top of `motion.html`.

## Colour: roles, not names

| Role | Default | Used for |
|---|---|---|
| `canvas` | `#F1F2E4` cream | the background, text on ink |
| `ink` | `#0D0D0D` | text, every border, every shadow, terminals and title pills |
| `light` | `#FFFFFF` | light states (window, cards, pills) |
| `a1` | `#F6E79E` yellow | the tile, the logo chip, the CTA button, the big burst, highlights, the spoken caption word |
| `a2` | `#F8B2D6` pink | the headline block, the active tab, small accents |
| `a3` | `#A9E6C4` mint | checks, "done" states, the offer sticker |
| `a4` | `#E4DAFF` lilac | sparingly |

Mapping a brand: the strongest brand colour goes in `a1` (it is what people remember: the tile and the button), two
supporting colours in `a2` and `a3`, a quiet one in `a4`. Keep `ink` dark and `canvas` light unless the brand is a
dark theme; then swap them and check every state (terminals and title pills use ink as their fill).

Rules that hold in any palette: one dominant colour per state (light, ink or one accent) with small accents in the
others; colour changes use `SP.color` (fast, no overshoot), because a slow or bouncy colour spring shows muddy
in-between frames.

## Type

- **Display** (default Space Grotesk): 700 for headlines (uppercase, letter-spacing -0.035em, 46 to 92 px in world
  units) and titles (22 to 40 px), 500 to 600 for body and list rows.
- **Mono** (default IBM Plex Mono): the logo, tags, stickers, labels, times, urls, key caps (13 to 21 px, uppercase
  for tags, letter-spacing 0.02 to 0.08em).
- Any Google Font works through `google`; a brand font file works through `src` (put it in `assets/fonts/`, check its
  licence allows video). A brand with one family: use it for both, with weights doing the work.
- Avoid the most generic choices (Inter, Roboto, Arial) unless they are the brand: the look depends on character in
  the type. Arial appears in the template only inside the deliberately plain "before" slide.
- After changing fonts, look at every beat: widths change, and the headline must fit its 700 px window.

## Shape language

| Language | Settings | Notes |
|---|---|---|
| Neo-brutalist (default) | `border: 3, shadow: 6, radius: 1` | hard offset shadows that grow on hover and push in on press |
| Flat and soft | `border: 0, shadow: 0, radius: 1.2` | rely on colour contrast between states; give `light` states a tint against the canvas |
| Sharp | `border: 3, shadow: 6, radius: 0.3` | pills stay round, cards and windows get tight corners |
| Thin and minimal | `border: 1.5, shadow: 0, radius: 0.8` | fewer accents, more white; drop the doodles and bursts or tone them down |

Doodles (sparkle, arrow, speech bubble, blocks) are inline SVGs coloured by the tokens; swap them for brand shapes,
or remove them from `DOODLES` for a calmer opening. `dots: false` turns off the dot grid.

## The frame

- **Canvas**: the dot grid (26 world px apart, ink at 11%) is drawn in world space, so it zooms with the camera. Big
  hits send a coloured ripple through it (`RIPPLES`).
- **Logo chip**: `BRAND.logo` in mono on `a1`, top left, slightly rotated. It stays on screen the whole video. Empty
  string hides it. A real logo image can replace the text chip.
- **HUD**: two mono lines at the bottom (in 9:16 one line at the top): the title left, the url or date right.
- **Cursor**: a dark arrow with a white outline and an offset shadow, constant size on screen, pressing to 86%.

## Stickers, tags and photos

- Stickers slap on with the slam spring and a few degrees of rotation (-8° to 8°).
- Name tags: mono caps on an accent, small hard shadow, tilted a little, popping exactly on the spoken name.
- Photos of people: black-and-white cut-outs with a thick coloured outline and a hard shadow (`sticker.py`). They pop
  in from behind the shape.

## Character

Playful and snappy. Pops and slams overshoot (ζ 0.55 to 0.78), the shape itself only a hair (ζ 0.8), colours never.
Over the top in the opening, calm enough to read in the middle, a small celebration at the end.

What breaks the look in any brand: glows and soft blurred shadows on UI, gradients behind everything, stock tech
backgrounds, emoji as decoration (✓ and ● as UI glyphs are fine), em-dashes in copy.
