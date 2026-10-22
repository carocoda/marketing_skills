# Formats and safe zones

| Format | Canvas | For | Length that works |
|---|---|---|---|
| 16:9 | 1920×1080 | website, YouTube, LinkedIn, a screen at an event | 30 to 50 s promo, 15 to 20 s teaser |
| 9:16 | 1080×1920 | Reels, TikTok, Shorts, Stories, Meta ads | 15 to 25 s |
| 1:1 | 1080×1080 | feed posts | 15 to 30 s |
| 4:5 | 1080×1350 | the feed on Instagram and LinkedIn | 15 to 30 s |

Set it with `new_project.py --format 9:16` or `canvas` in `project.json`. The page reads the size from the URL
(`render.py` passes it), scales the camera (`FZ`), caps the zoom so the shape always fits (92% of the width, 80% of
the height), moves the logo and HUD and places captions. Then look at every beat: the template's layouts were drawn
for 16:9.

## 9:16

- The platform's own buttons cover the right edge and the bottom: on Reels, keep everything that matters between
  about y 270 and y 1250 (of 1920) and away from the right 120 px. The caption and the "Learn more" button area sit
  at the bottom.
- But don't push everything up to the strict zone: a layout with the bottom third empty looked unfinished. A good
  balance from a real ad: the world origin around y 890 (the template's `CY` is 0.46 × H = 883), content running to
  about y 1390, captions at about y 1455 (the template uses 0.76 × H).
- Logo and HUD at the top (about y 205), so they survive a 4:5 crop too.
- Shapes should fill about 85% of the width. Narrow states (a pill, a button) look small in 9:16: make them taller,
  stack their content, or zoom more.
- If the same video also goes out as 4:5, it is a crop of the 9:16: the band from about y 175 to 1525. Keep logo,
  content and captions inside that band.

## Loop lengths

A loop needs a seam that sounds right in the chosen song. Some lengths have none (in one song 12 bars was perfect
and 13 or 14 bars scored under 0.1). Check a few lengths with `beats.py --segments` before you settle the script.

## Speech in short formats

At about 3 words per second, a 25 s ad holds roughly 60 words with air around them. Measure speech without the
silence at both ends of each take (`speech_bounds`): takes are often half a second shorter than their files.
