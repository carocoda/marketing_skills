#!/usr/bin/env python3
"""Pull stills at chosen times and tile them into one review sheet, with the time on each tile.
Use it twice: on the long video to see where the speaker sits (for --center), and on the
finished short to check that no graphic covers the face, captions read, arrows are visible and
the end screen is right. Look at the sheet; most layout mistakes only show up there.

Usage:
  python3 contact_sheet.py short.mp4 --at 0.5 6 14.2 30 -o sheet.png
  python3 contact_sheet.py long.mp4 --every 60 -o where-is-the-speaker.png
"""
import argparse
import os
import sys
import tempfile

sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
from common import die, find_font, need, pil_font, probe, require_pillow, run  # noqa: E402


def main():
    ap = argparse.ArgumentParser(description=__doc__, formatter_class=argparse.RawDescriptionHelpFormatter)
    ap.add_argument("video")
    ap.add_argument("--at", type=float, nargs="+")
    ap.add_argument("--every", type=float)
    ap.add_argument("--cols", type=int, default=0)
    ap.add_argument("--tile", type=int, default=480, help="tile width in px")
    ap.add_argument("-o", "--out", required=True)
    a = ap.parse_args()
    need("ffmpeg"); require_pillow()
    from PIL import Image, ImageDraw
    info = probe(a.video)
    if a.at:
        times = a.at
    elif a.every:
        times, t = [], a.every / 2
        while t < info["dur"]:
            times.append(round(t, 2)); t += a.every
    else:
        die("give --at or --every")
    tmp = tempfile.mkdtemp(prefix="sheet_")
    tiles = []
    for i, t in enumerate(times):
        p = os.path.join(tmp, f"{i:03d}.png")
        # -ss after -i: slower but frame-accurate, and no half-decoded (green) frames
        run(["ffmpeg", "-y", "-i", a.video, "-ss", f"{t:.3f}", "-frames:v", "1",
             "-vf", f"scale={a.tile}:-2", p])
        if os.path.exists(p):
            tiles.append((t, Image.open(p).convert("RGB")))
    if not tiles:
        die("no stills extracted")
    tw, th = tiles[0][1].size
    cols = a.cols or (4 if th < tw else 5)
    rows = (len(tiles) + cols - 1) // cols
    sheet = Image.new("RGB", (cols * (tw + 8) + 8, rows * (th + 8) + 8), (110, 110, 110))
    font = pil_font(find_font(None), 22)
    for i, (t, im) in enumerate(tiles):
        x, y = 8 + (i % cols) * (tw + 8), 8 + (i // cols) * (th + 8)
        sheet.paste(im, (x, y))
        d = ImageDraw.Draw(sheet)
        d.rectangle([x, y, x + 92, y + 32], fill=(0, 0, 0))
        d.text((x + 8, y + 4), f"{t:.2f}s", font=font, fill=(255, 255, 255))
    sheet.save(a.out)
    print(f"wrote {a.out} ({len(tiles)} stills)")


if __name__ == "__main__":
    main()
