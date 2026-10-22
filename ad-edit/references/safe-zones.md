# Safe zones for 9:16 and 4:5

On Reels and Stories, Meta lays its own interface over the video: profile name at the top, buttons on the right, ad
text and the CTA button at the bottom. Whatever sits there is (partly) covered. In the feed (4:5) nothing covers the
picture, but a placement can crop it. TikTok and YouTube Shorts cover roughly the same areas as Reels.

So every variant gets two formats:

- **9x16** (1080x1920) for Reels and Stories;
- **4x5** (1080x1350) for the feed.

Pair them in Ads Manager per placement (asset customisation), so Meta does not crop a format itself.

## 9:16 (1080 x 1920)

The guideline we keep to:

| Zone | Pixels | What the platform puts there |
|---|---|---|
| top 14 % | y 0 to 270 | profile picture, name, "Sponsored" |
| bottom 35 % (Reels) | y 1250 to 1920 | ad text, CTA button, sound |
| bottom 22 % (Stories) | y 1500 to 1920 | CTA button |
| sides 6 % | x 0 to 65 and 1015 to 1080 | right: like, comment, share (Reels) |

**Important text and faces: between y 270 and 1250, and between x 65 and 1015.**

How the kit fills that in (`LAYOUTS['9x16']` in `overlay.html`):

| Element | Position | Note |
|---|---|---|
| brand tag | x 56, y 300 | just below the profile bar |
| face | around y 610 to 650 after the zoom | `face_y` 0.32 to 0.36 of the frame height |
| windows, fan, tiles (`slots`) | y 440 to 790, against the sides | stick a few pixels into the 6 % margin; picture only, no text |
| cards (`zone`) | centred on y 1110 | below the chest, above the Reels bar |
| captions (`cap`) | centred on y 1150 | well above 1250 |
| "TAP BELOW" + arrow | y 1385 | low on purpose: the arrow points at the CTA button. It falls in the Reels text zone, so check the preview |
| end card | logo y 300, heading to about y 900, button y 1195, URL y 1290 | the URL falls just inside the Reels zone; the button does not |

## 4:5 (1080 x 1350)

In the feed the name sits above and the text and button below the picture, so the whole frame is visible. Two things:

- Keep about 5 % margin (55 px) around text. Rounded corners and the previews in Ads Manager trim a little.
- Some placements show 4:5 as a square (1:1). Then 135 px drop off at the top and bottom. Keep important text between
  y 135 and 1215. In the kit: captions at y 1015, cards at y 975, end card URL at y 1100. Only the brand tag (y 44)
  drops off then, and it is decoration.

`build.py` makes the 4:5 version from the same 9:16 recording: a fixed 1080 x 1350 window around the face (the face at
40 % of the height), then the same zooms. So in a new recording, don't put the face too high in the frame.
A landscape source works too: `build.py` then cuts the sides around the face first.

## Checking

1. `python3 _engine/build.py <ad> stills <variant> 9x16 <times>` and the same for `4x5`. Check on the contact sheet that
   every card, caption and the face stay inside the zones.
2. In doubt, put a still next to a screenshot of a Reels ad on your phone.
3. After uploading: the preview per placement in Ads Manager. Whatever is covered there, move in `LAYOUTS` (per
   format), not per event.

New elements: give them a position in `LAYOUTS` for both formats and keep them inside these limits.
