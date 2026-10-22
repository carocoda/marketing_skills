# Platforms, sizes and safe zones

Limits change. Check the platform's help page when a number matters; these are the working
defaults the scripts use.

| platform | format | size | length that works | notes |
| --- | --- | --- | --- | --- |
| YouTube Shorts | 9:16 | 1080x1920 | 30-60 s (Shorts can be up to 3 min) | Title card in the first second. End screen points to the long video; YouTube can also link the Short to it ("related video"). |
| Instagram Reels | 9:16 | 1080x1920 | 30-60 s | The grid crops the cover to 3:4, keep the title card in the middle. |
| TikTok | 9:16 | 1080x1920 | 30-60 s | The right edge has buttons, the bottom has the caption text. |
| LinkedIn | 16:9 or 1:1 (4:5 also works) | 1920x1080 / 1080x1080 | 45-90 s | People watch muted at their desk. 16:9 keeps the speaker where they were in the long video, no crop. Put the YouTube link in the first comment. |
| X / Facebook feed | 1:1 or 4:5 | 1080x1080 / 1080x1350 | 30-60 s | |

`cut_short.py --aspect` takes `9x16`, `16x9`, `1x1` or `4x5`.

## Safe zones on 9:16 (1080x1920)

The app draws its own buttons and text over your video. Keep anything that must be read out of:

- the top 250 px (status bar, search, "Shorts" label)
- the bottom 400 px (channel name, caption text, music line, progress bar)
- the right 140 px (like, comment, share buttons)

That leaves roughly x 60-940, y 250-1520 for graphics and captions. The default caption centre is
y = 0.70 (1344 px), which sits above the bottom UI. Graphics go in the upper half (y 220-900) so
they never meet the captions or the speaker's mouth.

## 16:9 layout

The speaker usually stands off-centre in a long video. Measure it first (contact sheet of the
long video), then put graphics in the free column on the other side, captions along the bottom
(centre y = 0.86). Keep the bottom edge of every graphic about 100 px above the captions.

## 1:1 and 4:5

Same as 9:16 but less room: graphics in the top third, captions at y 0.80-0.82.

## Reframing 16:9 to 9:16

`cut_short.py` crops a 9:16 slice out of the 16:9 source. On a 1080p source that slice is only
608 px wide and gets scaled up to 1080, so it softens. Use a 4K master when you have one. Set
`--center` to the speaker's face position (fraction of the width); check it on a contact sheet of
the cut clip before you build graphics. A screen recording with tiny UI text rarely survives a
9:16 crop; for those, make a 16:9 short or show the screen as a graphic.
