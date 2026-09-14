# Style 3: pastel flowchart (peach poster with marker highlights)

Warm peach background, thick rounded display title, white flowchart columns with
thin dark outlines, pastel "marker" highlights behind text lines, connector arrows
from a hub pill. Suits "one input, three buckets" content (a content mix, a budget
split, a routing decision).

> **Cool variant:** background `#F4F8FD` (very light blue-white, radial white at the
> top), title in bright azure `#2f6fe0` with the accent word in `--brand`, all warm
> neutrals turned cool (`--ink #1b2740`, box lines `#2e3d56`, borders `#dde6f2`,
> shadows `rgba(22,35,56,.09)`). The takeaway band is optional and may go if it
> adds nothing; footnote dot in `--brand`.

## Tokens

```css
:root {
  --ink: #2b2117;        /* warm black-brown, headings and outlines */
  --orange: #F2542D;     /* title */
  --brand: #1E40AF;      /* title accent word, takeaway band, footer pill */
  --blue: #2f7fe0;  --purple: #8b5cf6;  --red: #e8564f;   /* column accents */
  --bg: #FAEEE4;         /* peach; subtle radial #fdf4ec at the top */
  --boxline: #4a3a2c;    /* thin outlines of inner boxes (1.6-1.7px) */
}
/* pastel marker fills, cycle per line: */
.p-mint{background:#d9f2e2} .p-lilac{background:#e9defa}
.p-peach{background:#ffe4cb} .p-pink{background:#fcdce9} .p-blue{background:#dbe9fc}
```

- Fonts: **Baloo 2** 800 (title about 55px, column headings, big % figures),
  **Inter** 400-800 (body), **JetBrains Mono** (kickers, footnote, mono labels).
- NO grid paper: flat peach background.

## Layout patterns

- **Title centred**, 2 lines in orange, ONE accent word in `--brand`. Subtitle in
  ink with a bold core.
- **Contrast strip** (optional): dashed-border chips ("most people get stuck here").
- **Hub pill → connectors:** white pill with a 2.5px ink border and a hard drop
  shadow (`box-shadow: 0 6px 0 rgba(43,33,23,.10)`), under it an SVG with paths
  and triangle arrowheads into the columns.
- **Columns:** white, radius 20, thin beige border, soft warm shadow. Heading
  hierarchy (category names NEVER as a tiny kicker): number badge (27px rounded
  square, white digit) + CATEGORY NAME big (Baloo 800, about 33px, column colour) →
  giant % figure (Baloo 800, about 64px, column colour) → short description (Inter
  600, about 15.5px, slate) → thin rule. Keep names on ONE line.
  Inner boxes: 1.7px `--boxline` outline, radius 13, centred, bold caption plus a
  pastel highlight line under it. Distribute boxes with
  `justify-content: space-evenly` so the column fills the canvas.
- Mascot as a **sticker** next to the hub pill (small, about 92px, slightly
  rotated), not in the header (it collides with the centred title).
- Bottom: takeaway band in `--brand` with chevrons + mono footnote + footer pill.

## Default animation

**Stream and fill**, reduced to one story concept: per connector one dot in the
column colour that travels from hub to column, one after another (cascade); on
arrival the border of the receiving column lights up in the same colour ("the
bucket fills") and fades out. Then a rest beat.

- Connectors: ORTHOGONAL with rounded elbows (`V.. Q.. H.. Q.. V..`), no S-curves
  (curved outer arrows look odd). Triangle arrowheads static at the end.
- Dots: absolute `<span>`s in a wrapper that sits exactly over the SVG;
  `offset-path` with the same path string; opacity 0 outside the travel window
  (covers the offset snap → frame 0 == last frame).
- Windows (5 s): travel 4-26 / 30-52 / 56-78; fill glow on the column border
  28-36 (fade out to 46) / 54-62 (to 72) / 80-88 (to 97); rest to 100.
- A hand-drawn wiggle over the whole poster, as some reference GIFs have: do NOT
  copy it (violates the static-poster rule and doubles the GIF).

## Checklist

- [ ] Title in orange plus one word in `--brand`; column names on one line
- [ ] Inner boxes fill the column (space-evenly), no empty bottom
- [ ] Dots travel in column colours, rest beat at the end, seamless loop
- [ ] Pastel fills cycle (not one colour per column)
- [ ] Takeaway band and footer pill in `--brand`; mascot as a sticker by the hub
