# Screenshots on the poster

Real screenshots make a how-to infographic believable and clear. Four sources, in
order of preference, plus cropping and privacy rules.

## 1. Frames from a screen recording (best for "this is how" videos)

If the infographic belongs to a video, the recording already contains every screen
in the right state. Pull frames with ffmpeg; no re-recording needed.

**Find the moments first.** Make a contact sheet, one frame every 4 seconds, and
look at it:

```bash
mkdir -p frames && ffmpeg -loglevel error -y -i video.mp4 -vf "fps=1/4,scale=426:-1" frames/f_%03d.png
```

```python
from PIL import Image, ImageDraw
import glob
fs = sorted(glob.glob('frames/f_*.png'))
w, h = Image.open(fs[0]).size
cols = 6; rows = (len(fs) + cols - 1) // cols
sheet = Image.new('RGB', (cols * w, rows * (h + 18)), 'white')
d = ImageDraw.Draw(sheet)
for i, f in enumerate(fs):
    x = (i % cols) * w; y = (i // cols) * (h + 18)
    sheet.paste(Image.open(f), (x, y + 18)); d.text((x + 4, y + 2), f'{i*4}s', fill='black')
sheet.save('contact.png')
```

**Then grab the exact frames at full resolution:**

```bash
ffmpeg -loglevel error -y -ss 45 -i video.mp4 -frames:v 1 frame_45.png
```

Rules that came out of real builds:
- Prefer the **clean cut** (no captions, no callout overlays, no presenter bubble)
  when you have one. If only the finished video exists, pick timestamps where no
  caption or overlay sits on the region you need, and crop around the bubble.
- Zoomed-in moments (screen recorders often zoom on clicks) give crisper crops
  than the full-screen view.
- A frame taken mid-zoom or mid-transition has blur rectangles and UI offset from
  each other. Take one from a stable moment.
- If the recording already has a privacy blur on names and emails, use THAT
  version for those screens; the clean cut is unblurred.

## 2. Web pages (public)

Playwright renders a page at a fixed viewport and saves a PNG. For a specific
panel, screenshot the element or crop afterwards.

```python
from playwright.sync_api import sync_playwright
with sync_playwright() as pw:
    b = pw.chromium.launch(); p = b.new_page(viewport={'width': 1440, 'height': 900}, device_scale_factor=2)
    p.goto('https://example.com/page'); p.wait_for_load_state('networkidle')
    p.screenshot(path='page.png', full_page=True); b.close()
```

Pages behind a login (account settings, dashboards) can't be reached headless.
Take those by hand, or from a screen recording (source 1), or with a browser
extension that can screenshot the logged-in tab.

## 3. Mock UI in HTML (when no screenshot exists or the real one is too empty)

An empty chat window or a blank editor tells the reader nothing. Build the essence
of the screen as a small HTML component inside the card instead: a chat box with
an attached-file pill and a prompt chip with a send button, a settings toggle, a
table with three rows. Use the style's tokens (mono font for prompts, soft grey
chip background, accent send button). Say in the concept that this card is a mock,
not a screenshot.

## 4. Illustrative lists (results, lead lists, rankings)

When the real result contains personal data, draw the result with fictional
entries instead: names, roles and companies that don't exist, in the poster's own
style (avatar circle with initials, bold name, role · company, a status pill).
It reads clearer at feed size than a blurred screenshot and it can never leak a
real person. Mention in the concept that the entries are fictional.

## Cropping

Crop tight around the panel the reader needs (the dialog, the sheet header plus
a dozen rows, the button with the cursor on it). Remove browser chrome, sidebars
and empty canvas.

```python
from PIL import Image
Image.open('frame_45.png').crop((655, 210, 1430, 625)).save('shot_settings.png')  # (left, top, right, bottom)
```

- Aim for crops that are 1.6-2.0 times wider than tall; they sit well in a card
  visual box of about 450x230 on the 1080 canvas.
- Put them in the visual box with `object-fit: contain` on a white background.
  `cover` crops the UI and cuts labels off.
- Text in the screenshot will be small. That's fine; the instruction line under
  it does the reading. The screenshot proves where the button is.
- A cursor on the button you want people to click is a plus. Keep it.

## Privacy

Never let a real name, email address, profile URL or private number reach the
poster. Options, in order:
1. Use the frames from a recording that was already blurred.
2. Blur the region yourself before cropping:

```python
from PIL import Image, ImageFilter
im = Image.open('frame.png')
box = (120, 280, 400, 600)  # the columns with names and emails
im.paste(im.crop(box).filter(ImageFilter.GaussianBlur(14)), box)
im.save('frame_blurred.png')
```

3. Replace the whole thing with fictional entries (source 4).

Company names and job titles in a spreadsheet are usually fine to keep readable;
people are not. When in doubt, blur.
