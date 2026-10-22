"""Turn a cut-out photo into a sticker: black-and-white photo, thick coloured outline, hard shadow to the bottom
right. The collage look that suits the neo-brutalist default style.

  python3 sticker.py assets/photo-cutout.png assets/photo-sticker.png
  python3 sticker.py assets/photo-cutout.png assets/photo-sticker.png --outline mint --color --width 700
  python3 sticker.py assets/photo-cutout.png assets/photo-sticker.png --outline "#FFB4A2" --ink "#1B1B1B"
  python3 sticker.py assets/photo.jpg assets/photo-sticker.png --remove-bg       cut out the background first

The cut-out needs a transparent background. --remove-bg uses the HyperFrames CLI
(npx hyperframes remove-background: runs on this computer, but the first run downloads the package and a
model, so ask before using it). A cut-out made anywhere else (Photoshop, remove.bg, the Mac's "Remove
background") works just as well.
Defaults: outline 16 px pink, shadow 11 px, grey with 12% extra contrast, measured on the full-size cut-out.
Only use photos of real people with their OK, and never a generated face of a real person.
"""
import argparse
import subprocess
import tempfile
from pathlib import Path

import numpy as np
from PIL import Image
from scipy.ndimage import distance_transform_edt

COLORS = {'pink': (248, 178, 214), 'mint': (169, 230, 196), 'yellow': (246, 231, 158), 'lilac': (228, 218, 255),
          'white': (255, 255, 255), 'cream': (241, 242, 228)}
INK = (13, 13, 13)


def colour(c):
    if c.startswith('#'):
        h = c[1:]
        return tuple(int(h[i:i + 2], 16) for i in (0, 2, 4))
    if c not in COLORS:
        raise SystemExit(f'unknown colour {c!r}: use a hex value like "#F8B2D6" or one of {", ".join(COLORS)}')
    return COLORS[c]

ap = argparse.ArgumentParser()
ap.add_argument('src')
ap.add_argument('out')
ap.add_argument('--outline', default='pink', help='a hex colour or ' + ', '.join(COLORS))
ap.add_argument('--ink', default='#0D0D0D', help='the shadow colour (hex)')
ap.add_argument('--r', type=float, default=16, help='outline thickness in px of the cut-out')
ap.add_argument('--shadow', type=int, default=11, help='shadow offset in px')
ap.add_argument('--color', action='store_true', help='keep the photo in colour')
ap.add_argument('--contrast', type=float, default=1.12)
ap.add_argument('--width', type=int, help='scale the finished sticker to this width')
ap.add_argument('--remove-bg', action='store_true')
a = ap.parse_args()
INK = colour(a.ink)

src = Path(a.src)
if a.remove_bg:
    tmp = Path(tempfile.mkdtemp()) / 'cutout.png'
    subprocess.run(['npx', 'hyperframes', 'remove-background', str(src), '-o', str(tmp)], check=True)
    src = tmp
im = np.asarray(Image.open(src).convert('RGBA')).astype(np.float64)
alpha = im[:, :, 3] / 255
ys, xs = np.nonzero(alpha > 0.5)
if not len(xs):
    raise SystemExit(f'{a.src} has no opaque pixels: is the background really cut out?')
pad = int(a.r + a.shadow + 4)
y0, y1, x0, x1 = ys.min(), ys.max() + 1, xs.min(), xs.max() + 1
crop = np.zeros((y1 - y0 + 2 * pad, x1 - x0 + 2 * pad, 4))
crop[pad:-pad, pad:-pad] = im[y0:y1, x0:x1]
rgb, al = crop[:, :, :3], crop[:, :, 3] / 255

if not a.color:
    lum = rgb @ np.array([0.299, 0.587, 0.114])
    lum = np.clip((lum - 128) * a.contrast + 128, 0, 255)
    rgb = np.repeat(lum[:, :, None], 3, axis=2)

flat = alpha[-1].max() > 0.5 and y1 == im.shape[0]         # the photo is cut off at the bottom (legs, a torso)
al_d = al.copy()
if flat:                                                   # carry the cut straight down so the outline stays flat
    al_d[pad + (y1 - y0):] = al[pad + (y1 - y0) - 1]
d = distance_transform_edt(al_d < 0.5)                     # distance from the person, in px
ring = np.clip(a.r + 0.5 - d, 0, 1)                        # the outline, anti-aliased at its outer edge
if flat:
    ring[pad + (y1 - y0) + int(round(a.r)):] = 0             # the band under the cut is as thick as the outline
body = np.maximum(ring, al)                                # person + outline = the sticker's silhouette
shadow = np.zeros_like(body)
shadow[a.shadow:, a.shadow:] = body[:-a.shadow, :-a.shadow]

out = np.zeros_like(crop)
col = np.array(colour(a.outline), float)
for layer_rgb, layer_a in [(np.broadcast_to(np.array(INK, float), rgb.shape), shadow),
                           (np.broadcast_to(col, rgb.shape), ring),
                           (rgb, al)]:
    la = layer_a[:, :, None]
    oa = out[:, :, 3:4] / 255
    na = la + oa * (1 - la)
    out[:, :, :3] = np.where(na > 0, (layer_rgb * la + out[:, :, :3] * oa * (1 - la)) / np.maximum(na, 1e-9), 0)
    out[:, :, 3:4] = na * 255
if flat:                                                   # a straight edge: outline band plus shadow under the cut
    out = out[:pad + (y1 - y0) + int(round(a.r)) + a.shadow]
ys, xs = np.nonzero(out[:, :, 3] > 1)
res = Image.fromarray(out[ys.min():ys.max() + 1, xs.min():xs.max() + 1].round().astype(np.uint8), 'RGBA')
if a.width:
    res = res.resize((a.width, round(res.height * a.width / res.width)), Image.LANCZOS)
res.save(a.out)
print(f'{a.out}: {res.width}x{res.height}')
