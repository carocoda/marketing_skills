# Accent-animation recipes

All recipes share one rule: the poster is static, the animation only points at it.
One shared timeline, keyframe percentages as windows, seamless loop. Pick ONE
primary recipe per poster. Default = recipe 1.

## Timeline maths

For N sections on a T-second loop with a rest beat at the end:
- window length ≈ (0.80 × 100%) / N, fades about 2.5% on each side
- proven timings: 4 sections on 5 s → windows 4-19 / 23-38 / 42-57 / 61-76, rest
  79.5-100. 8 items on 6.5 s → start 2.3% + i×11, window about 6% wide.
- Always end with 10-20% where nothing is highlighted (breathing room and a clear
  loop boundary).

## Recipe 1: marching dashed outline (DEFAULT, calm)

A coloured dashed outline slowly circles the active section, then hands off to the
next. Reads as a selection marquee.

```css
.card { position: relative; }
.ants {
  position: absolute; inset: -6px;
  width: calc(100% + 12px); height: calc(100% + 12px);
  overflow: visible; pointer-events: none;
}
.ants rect {
  x: 1.5px; y: 1.5px;
  width: calc(100% - 3px); height: calc(100% - 3px);
  rx: 22px; fill: none;
  stroke: transparent; stroke-width: 3;
  stroke-linecap: round;
  stroke-dasharray: 7 8; /* period 15 */
}
.c1 .ants rect { animation: march 5s linear infinite, ants1 5s linear infinite; }
/* ...c2..cN with ants2..antsN */

@keyframes march { from { stroke-dashoffset: 0; } to { stroke-dashoffset: -75px; } } /* 5 × period */
@keyframes ants1 {
  0%, 1.5%    { stroke: rgba(47,127,224,0); }
  4%, 19%     { stroke: rgba(47,127,224,1); }
  22.5%, 100% { stroke: rgba(47,127,224,0); }
}
```

Markup: `<svg class="ants"><rect/></svg>` as the first child of each card.
Speed: about 1 period per second reads calm; halve the offset for calmer still.

## Recipe 2: card glow cycle (bolder, use sparingly)

Border + soft coloured ring + shadow per active card. Optionally a 4px lift
(`transform: translateY(-4px)` in the same keyframes). Bolder than recipe 1; only
when more emphasis is wanted.

```css
@keyframes glow1 {
  0%, 1.5%    { border-color: #e3e8ee; box-shadow: 0 10px 26px rgba(22,35,56,.09); }
  4%, 19%     { border-color: #2f7fe0; box-shadow: 0 0 0 3px rgba(47,127,224,.45), 0 18px 36px rgba(47,127,224,.26); }
  22.5%, 100% { border-color: #e3e8ee; box-shadow: 0 10px 26px rgba(22,35,56,.09); }
}
```

## Recipe 3: chip cycle with send pulse (prompt and listicle posters)

Each chip lights up in its own colour; the send button of the active chip pulses
(as if the prompt is being sent). For 8 items use a 6.5 s loop with glow1..8 and
pulse1..8.

```css
@keyframes pulse1 { 0%, 4.5%, 10.5%, 100% { transform: translateY(-50%) scale(1); }
                    7.5% { transform: translateY(-50%) scale(1.3); } }
```

## Recipe 4: rail comet (loop and cycle concepts)

Static rail (soft accent colour) plus a brighter dash that shoots along it once per
loop, with an arrowhead or label pulse on arrival.

```css
.rail .comet {
  stroke-dasharray: 14 186; /* gap > pathLength: no wrap ghost */
  stroke-dashoffset: 15;    /* rest just outside the path (linecap dot) */
  animation: comet 5s linear infinite;
}
@keyframes comet { 0%, 78% { stroke-dashoffset: 15; } 95%, 100% { stroke-dashoffset: -100; } }
```

## Recipe 5: travelling dot on a track (loop and cycle posters)

Steps as a ring with a line between them and a dot that drives the loop, so the
cycle is unmistakable.

Layout: 2x3 card grid in clockwise order (row 1 [1][2], row 2 [6][3], row 3 [5][4]),
a dotted track as a rounded rectangle through the MARGINS around the grid
(channels about 34px left/right, 30px top/bottom) so the dot never disappears
behind a card. Numbered nodes (one hue per step) on the track at each card's
height; small chevrons give the direction; the dot drives through the nodes
(higher z-index).

```css
.runner {
  position: absolute; width: 13px; height: 13px; border-radius: 50%;
  background: var(--accent);
  box-shadow: 0 0 0 5px rgba(164,98,63,.16), 0 0 16px rgba(164,98,63,.5);
  offset-path: path('M 17 150 L 17 43 A 28 28 0 0 1 45 15 L 939 15 A 28 28 0 0 1 967 43 L 967 785 A 28 28 0 0 1 939 813 L 45 813 A 28 28 0 0 1 17 785 Z');
  offset-rotate: 0deg;
  animation: travel 6s linear infinite;
}
@keyframes travel { from { offset-distance: 0%; } to { offset-distance: 100%; } }
```

- The path starts at node 1 and closes with `Z`, so 0% == 100% == seamless loop.
- `offset-distance` is a regular CSS animation, so the seek harness works.
- The track itself: an SVG `<rect rx>` with `stroke-dasharray` (static, sand colour).
- 6 s per round reads calm.

### Recipe 5b: connector variant (lines BETWEEN the blocks)

Often nicer than a ring around the grid: short dotted SVG connectors in the gaps
between adjacent cards (drawn in flow direction, with an arrowhead), all with
`stroke-dasharray` + shared `flow` keyframes (dashoffset exactly N periods per
loop, so the dashes visibly stream along). The travelling dot gets a rectangular
`offset-path` circuit through the card CENTRES with z-index BELOW the cards: it is
visible on every connector and dives under the blocks. Needs generous gaps (row
gap about 56px, column gutter about 64px) so connectors and dot stay legible. Less
text per card plus one thin-line SVG illustration per card keeps it light.

## Micro-accent library (max 1-2, only on request)

A poster with the whole set at once reads as busy. These exist only for when more
motion is explicitly wanted:

- icon-scan: icons in a list pop one after another (scale 1→1.4→1, staggered windows)
- stat-bump: a big number springs up (scale 1.08)
- bar-flex: chart bar `scaleY 1.06`, `transform-origin: bottom` (fill-box)
- bubble-wobble: quote bubble rotate ±0.8°
- key-turn: key icon rotates 32° and back (climax moment)
- hl-flash: marker highlight briefly saturates
- mascot-idle: mascot translateY ±5px (doubles the GIF size)
- dot-beat: accent dot scale 1.65 just before the loop boundary
