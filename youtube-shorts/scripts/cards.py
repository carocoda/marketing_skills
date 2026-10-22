#!/usr/bin/env python3
"""Pillow title card and end screen for the captions-only path (no HyperFrames needed).
With HyperFrames installed, use templates/graphics/title and templates/graphics/end-screen instead:
they animate. These are still images that assemble.py fades in and out.

Preview without building a short:
  python3 cards.py title "How email open rates really work" --sub "Explained in 60 seconds" --aspect 9x16 -o title.png
  python3 cards.py end --title "Your long video title" --line "youtube.com/@yourchannel" --aspect 9x16 -o end.png
"""
import argparse
import os
import sys

sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
from common import ASPECTS, find_font, hex_rgb, pil_font, require_pillow  # noqa: E402

BRAND = {"primary": "#1E40AF", "secondary": "#3B6BF0", "ink": "#0B1220", "mid": "#3A4453",
         "bg": "#F6F5F1", "card": "#FFFFFF", "on_primary": "#FFFFFF", "font": None}


def brand(b=None):
    out = dict(BRAND)
    out.update({k: v for k, v in (b or {}).items() if v is not None})
    return out


def wrap(draw, text, font, maxw):
    lines, cur = [], ""
    for word in text.split():
        t = (cur + " " + word).strip()
        if draw.textlength(t, font=font) <= maxw or not cur:
            cur = t
        else:
            lines.append(cur)
            cur = word
    if cur:
        lines.append(cur)
    return lines


def shadowed(card, radius, blur=18, alpha=70):
    from PIL import Image, ImageDraw, ImageFilter
    pad = blur * 3
    sh = Image.new("RGBA", (card.width + pad * 2, card.height + pad * 2), (0, 0, 0, 0))
    ImageDraw.Draw(sh).rounded_rectangle([pad, pad + 10, pad + card.width, pad + card.height + 10],
                                         radius=radius, fill=(15, 23, 42, alpha))
    sh = sh.filter(ImageFilter.GaussianBlur(blur))
    sh.alpha_composite(card, (pad, pad))
    return sh, pad


def title_card(text, sub, frame_w, frame_h, b=None):
    """Returns (RGBA image, x, y) to overlay on the frame."""
    require_pillow()
    from PIL import Image, ImageDraw
    b = brand(b)
    fp = find_font(b["font"])
    vertical = frame_h > frame_w
    w = int(frame_w * (0.86 if vertical else 0.47))
    size = int(frame_w * (0.066 if vertical else 0.024))
    f1, f2 = pil_font(fp, size), pil_font(fp, int(size * 0.5))
    meas = ImageDraw.Draw(Image.new("RGBA", (8, 8)))
    padx, pady = int(size * 0.9), int(size * 0.75)
    lines = wrap(meas, text, f1, w - 2 * padx)
    lh = int(size * 1.15)
    h = pady * 2 + lh * len(lines) + (int(size * 0.8) if sub else 0)
    card = Image.new("RGBA", (w, h), (0, 0, 0, 0))
    d = ImageDraw.Draw(card)
    r = int(size * 0.5)
    d.rounded_rectangle([0, 0, w - 1, h - 1], radius=r, fill=hex_rgb(b["primary"], 255))
    d.rounded_rectangle([0, 0, int(w * 0.55), int(size * 0.14)], radius=int(size * 0.07),
                        fill=hex_rgb(b["secondary"], 255))
    y = pady
    for ln in lines:
        d.text((padx, y), ln, font=f1, fill=hex_rgb(b["on_primary"], 255))
        y += lh
    if sub:
        d.text((padx, y + int(size * 0.15)), sub, font=f2, fill=hex_rgb(b["on_primary"], 235))
    img, pad = shadowed(card, r)
    x = (frame_w - w) // 2 if vertical else int(frame_w * 0.03)
    yy = int(frame_h * (0.11 if vertical else 0.05))
    return img, x - pad, yy - pad


def end_screen(frame_w, frame_h, headline="Watch the full video on YouTube", title="", line="",
               cta="Link in the comments", b=None, logo=None):
    require_pillow()
    from PIL import Image, ImageDraw
    b = brand(b)
    fp = find_font(b["font"])
    W, H = frame_w, frame_h
    vertical = H > W
    img = Image.new("RGBA", (W, H), hex_rgb(b["bg"], 255))
    d = ImageDraw.Draw(img)
    hs = int(W * (0.085 if vertical else 0.042))
    fh = pil_font(fp, hs)
    y = int(H * (0.16 if vertical else 0.12))
    if logo and os.path.exists(logo):
        lg = Image.open(logo).convert("RGBA")
        k = (hs * 1.4) / lg.height
        lg = lg.resize((max(1, int(lg.width * k)), int(hs * 1.4)))
        img.alpha_composite(lg, ((W - lg.width) // 2, y))
        y += lg.height + int(hs * 0.6)
    for ln in wrap(d, headline, fh, W * 0.86):
        tw = d.textlength(ln, font=fh)
        d.text(((W - tw) / 2, y), ln, font=fh, fill=hex_rgb(b["ink"], 255))
        y += int(hs * 1.12)
    # video card: play button + title + line
    cw = int(W * (0.88 if vertical else 0.58))
    ts = int(W * (0.045 if vertical else 0.023))
    ft, fl = pil_font(fp, ts), pil_font(fp, int(ts * 0.62))
    pb = int(ts * 3.0)
    tlines = wrap(d, title, ft, cw - pb - ts * 3)[:3] if title else []
    ch = max(pb + ts * 2, ts * 2 + int(ts * 1.15) * len(tlines) + (int(ts) if line else 0))
    card = Image.new("RGBA", (cw, ch), (0, 0, 0, 0))
    cd = ImageDraw.Draw(card)
    cd.rounded_rectangle([0, 0, cw - 1, ch - 1], radius=int(ts * 0.7), fill=hex_rgb(b["card"], 255))
    px, py = ts, (ch - pb) // 2
    cd.ellipse([px, py, px + pb, py + pb], fill=(255, 0, 51, 255))
    tri = [(px + pb * 0.40, py + pb * 0.30), (px + pb * 0.40, py + pb * 0.70), (px + pb * 0.72, py + pb * 0.50)]
    cd.polygon(tri, fill=(255, 255, 255, 255))
    tx = px + pb + ts
    ty = (ch - (int(ts * 1.15) * len(tlines) + (int(ts) if line else 0))) // 2
    for ln in tlines:
        cd.text((tx, ty), ln, font=ft, fill=hex_rgb(b["ink"], 255))
        ty += int(ts * 1.15)
    if line:
        cd.text((tx, ty + int(ts * 0.15)), line, font=fl, fill=hex_rgb(b["mid"], 255))
    sh, pad = shadowed(card, int(ts * 0.7))
    cy = y + int(hs * 0.7)
    img.alpha_composite(sh, ((W - cw) // 2 - pad, cy - pad))
    if cta:
        fc = pil_font(fp, int(hs * 0.45))
        tw = d.textlength(cta, font=fc)
        d.text(((W - tw) / 2, cy + ch + int(hs * 0.9)), cta, font=fc, fill=hex_rgb(b["mid"], 255))
    return img


def main():
    ap = argparse.ArgumentParser(description=__doc__, formatter_class=argparse.RawDescriptionHelpFormatter)
    ap.add_argument("kind", choices=["title", "end"])
    ap.add_argument("text", nargs="?", default="")
    ap.add_argument("--sub", default="")
    ap.add_argument("--title", default="")
    ap.add_argument("--line", default="")
    ap.add_argument("--headline", default="Watch the full video on YouTube")
    ap.add_argument("--cta", default="Link in the comments")
    ap.add_argument("--aspect", default="9x16", choices=sorted(ASPECTS))
    ap.add_argument("-o", "--out", required=True)
    a = ap.parse_args()
    W, H = ASPECTS[a.aspect]
    if a.kind == "title":
        from PIL import Image
        im, x, y = title_card(a.text, a.sub, W, H)
        bg = Image.new("RGBA", (W, H), (90, 90, 90, 255))
        bg.alpha_composite(im, (max(0, x), max(0, y)))
        bg.save(a.out)
    else:
        end_screen(W, H, a.headline, a.title, a.line, a.cta).save(a.out)
    print(f"wrote {a.out}")


if __name__ == "__main__":
    main()
