#!/usr/bin/env python3
"""Word-by-word captions, drawn with Pillow and burned in with plain ffmpeg.

No libass or drawtext needed (many ffmpeg builds ship without them). Every caption state is a
transparent PNG; an ffmpeg concat list plays them at the right times as an overlay.

Styles
  bold   big caps, white with a black outline, the word being spoken in the highlight colour,
         each new chunk pops in (the classic Shorts/Reels look)
  pill   dark rounded pill, a coloured box slides under the word being spoken
  clean  sentence case, white with a soft outline, no highlight (calm, corporate-safe)

Usage (captions-only path, no HyperFrames):
  python3 captions.py words.json --burn clip.mp4 out.mp4 --style bold --highlight "#FFD400"
Other options: --font file.ttf --size 72 --y 0.70 --max-words 3 --no-caps --fill "#FFFFFF"
assemble.py imports this module and uses the plan's "captions" block instead.
"""
import argparse
import hashlib
import os
import sys

sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
from common import (count_frames, ends_sentence, find_font, hex_rgb, load_words, need, pil_font,  # noqa: E402
                    probe, require_pillow, run)

DEFAULTS = {
    # by aspect: font size, caption centre y (fraction of height), max line width (fraction of width)
    "9x16": {"size": 74, "y": 0.70, "maxw": 0.84},
    "4x5": {"size": 64, "y": 0.80, "maxw": 0.86},
    "1x1": {"size": 60, "y": 0.82, "maxw": 0.86},
    "16x9": {"size": 62, "y": 0.86, "maxw": 0.68},
}


def aspect_key(w, h):
    r = w / h
    return min(DEFAULTS, key=lambda k: abs(r - (lambda a, b: a / b)(*map(int, k.split("x")))))


def config(cfg, w, h):
    d = DEFAULTS[aspect_key(w, h)]
    style = cfg.get("style", "bold")
    mw = float(cfg.get("maxw", d["maxw"]))
    c = {
        "style": style,
        "font": find_font(cfg.get("font")),
        "size": int(cfg.get("size", d["size"])),
        "y": float(cfg.get("y", d["y"])),
        "maxw": int(mw * w) if mw <= 1 else int(mw),
        "caps": bool(cfg.get("caps", style != "clean")),
        "max_words": int(cfg.get("max_words", 3 if style != "clean" else 6)),
        "fill": hex_rgb(cfg.get("fill", "#FFFFFF")),
        "highlight": hex_rgb(cfg.get("highlight", "#FFD400")),
        "outline": int(cfg.get("outline", max(3, int(cfg.get("size", d["size"]) * 0.09)))),
        "pill_bg": hex_rgb(cfg.get("pill_bg", "#0E0F12"), 220),
        "pop": bool(cfg.get("pop", style in ("bold", "pill"))),
    }
    if style == "clean":
        c["outline"] = int(cfg.get("outline", max(2, c["size"] // 22)))
    return c


def chunks(words, c, measure):
    """Groups of at most max_words that fit max width. A new chunk starts after every sentence end:
    "WELL. SO LET'S" across two sentences reads messy."""
    groups, cur, curw = [], [], 0
    sp = measure(" ")
    for w in words:
        t = w["text"].upper() if c["caps"] else w["text"]
        add = measure(t) + (sp if cur else 0)
        endsent = bool(cur) and ends_sentence(cur[-1]["t"])
        if cur and (len(cur) >= c["max_words"] or curw + add > c["maxw"] or endsent):
            groups.append(cur)
            cur, curw, add = [], 0, measure(t)
        cur.append({"t": t, "start": w["start"], "end": w["end"]})
        curw += add
    if cur:
        groups.append(cur)
    out = []
    for i, g in enumerate(groups):
        following = groups[i + 1][0]["start"] if i + 1 < len(groups) else g[-1]["end"] + 0.6
        out.append((g[0]["start"], min(following, g[-1]["end"] + 0.7), g))   # never hang on in a pause
    return out


def draw_state(group, active, scale, c, font, band_w, band_h):
    from PIL import Image, ImageDraw
    img = Image.new("RGBA", (band_w, band_h), (0, 0, 0, 0))
    d = ImageDraw.Draw(img)
    ow = c["outline"] if c["style"] != "pill" else 0
    gap = int(c["size"] * 0.28)
    widths = [d.textlength(x["t"], font=font) for x in group]
    asc, desc = font.getmetrics()
    th = asc + desc
    total = sum(widths) + gap * (len(group) - 1)
    lay = Image.new("RGBA", (int(total + 2 * ow + 80), th + 2 * ow + 40), (0, 0, 0, 0))
    ld = ImageDraw.Draw(lay)
    x0, y0 = 40 + ow, 20 + ow
    if c["style"] == "pill":
        padx, pady = int(c["size"] * 0.35), int(c["size"] * 0.18)
        lay = Image.new("RGBA", (int(total + 2 * padx), th + 2 * pady), (0, 0, 0, 0))
        ld = ImageDraw.Draw(lay)
        ld.rounded_rectangle([0, 0, lay.width - 1, lay.height - 1], radius=int(c["size"] * 0.3), fill=c["pill_bg"])
        x0, y0 = padx, pady
    x = x0
    for i, (wd, item) in enumerate(zip(widths, group)):
        if c["style"] == "pill" and i == active:
            ld.rounded_rectangle([x - 8, y0 - 4, x + wd + 8, y0 + th + 2], radius=int(c["size"] * 0.16),
                                 fill=c["highlight"] + (255,))
        col = c["highlight"] if (c["style"] == "bold" and i == active) else c["fill"]
        if c["style"] == "pill":
            ld.text((x, y0), item["t"], font=font, fill=col + (255,))
        else:
            ld.text((x, y0), item["t"], font=font, fill=col + (255,), stroke_width=ow, stroke_fill=(0, 0, 0, 255))
        x += wd + gap
    if scale < 0.999:
        lw, lh = max(1, int(lay.width * scale)), max(1, int(lay.height * scale))
        lay = lay.resize((lw, lh), Image.BILINEAR)
    img.alpha_composite(lay, (int((band_w - lay.width) / 2), int((band_h - lay.height) / 2)))
    return img


def ease_out_back(t):
    c1, c3 = 1.70158, 2.70158
    return 1 + c3 * (t - 1) ** 3 + c1 * (t - 1) ** 2


def render(words, cfg, W, H, fps, duration, workdir):
    """Write caption PNGs and an ffmpeg concat list. Returns (list_path, band_y)."""
    require_pillow()
    from PIL import Image, ImageDraw
    c = config(cfg or {}, W, H)
    font = pil_font(c["font"], c["size"])
    meas = ImageDraw.Draw(Image.new("RGBA", (8, 8)))
    groups = chunks(words, c, lambda t: meas.textlength(t, font=font))
    band_h = int(c["size"] * 2.4)
    band_y = int(c["y"] * H - band_h / 2)
    os.makedirs(workdir, exist_ok=True)
    total_frames = int(round(duration * fps))
    blank = os.path.join(workdir, "blank.png")
    Image.new("RGBA", (W, band_h), (0, 0, 0, 0)).save(blank)

    events = []                                  # (frame, key, maker)
    pop_frames = max(1, int(round(0.22 * fps))) if c["pop"] else 0
    for (t0, t1, g) in groups:
        f0, f1 = int(round(t0 * fps)), int(round(t1 * fps))
        if f1 <= f0:
            continue
        starts = [int(round(x["start"] * fps)) for x in g]
        for f in range(f0, f1):
            active = max([i for i, s in enumerate(starts) if f >= s] or [0])
            k = (f - f0) / pop_frames if pop_frames and f - f0 < pop_frames else 1.0
            scale = 0.55 + 0.45 * ease_out_back(k) if k < 1.0 else 1.0
            key = (tuple(x["t"] for x in g), active if c["style"] != "clean" else -1, round(scale, 3))
            if events and events[-1][1] == key:
                continue
            events.append((f, key, (g, active, scale)))
        events.append((f1, None, None))
    # build the list, drop zero-length entries, fill gaps with blank
    files, cache = [], {}
    events.sort(key=lambda e: e[0])
    cleaned = []
    for e in events:
        if cleaned and cleaned[-1][0] == e[0]:
            cleaned[-1] = e                      # a later event on the same frame wins
        else:
            cleaned.append(e)
    if not cleaned or cleaned[0][0] > 0:
        cleaned.insert(0, (0, None, None))
    for i, (f, key, mk) in enumerate(cleaned):
        nf = (cleaned[i + 1][0] if i + 1 < len(cleaned) else total_frames) - f
        if nf <= 0:
            continue
        if key is None:
            path = blank
        else:
            h = hashlib.md5(repr(key).encode()).hexdigest()[:12]
            path = cache.get(h)
            if path is None:
                path = os.path.join(workdir, f"c_{h}.png")
                draw_state(*mk, c, font, W, band_h).save(path)
                cache[h] = path
        files.append((path, nf))
    lst = os.path.join(workdir, "captions.txt")
    with open(lst, "w") as fh:
        for p, nf in files:
            fh.write(f"file '{os.path.abspath(p)}'\nduration {nf / fps:.6f}\n")
        fh.write(f"file '{os.path.abspath(files[-1][0] if files else blank)}'\n")
    print(f"captions: {len(groups)} chunks, {len(cache)} images, style {c['style']}")
    return lst, band_y


def main():
    ap = argparse.ArgumentParser(description=__doc__, formatter_class=argparse.RawDescriptionHelpFormatter)
    ap.add_argument("words")
    ap.add_argument("--burn", nargs=2, metavar=("IN", "OUT"), required=True)
    ap.add_argument("--style", default="bold", choices=["bold", "pill", "clean"])
    ap.add_argument("--font"); ap.add_argument("--size", type=int); ap.add_argument("--y", type=float)
    ap.add_argument("--max-words", type=int); ap.add_argument("--fill"); ap.add_argument("--highlight")
    ap.add_argument("--no-caps", action="store_true")
    ap.add_argument("--work", default=None)
    a = ap.parse_args()
    need("ffmpeg")
    src, out = a.burn
    info = probe(src)
    fps = round(info["fps"], 3)
    cfg = {"style": a.style}
    for k in ("font", "size", "y", "fill", "highlight"):
        if getattr(a, k) is not None:
            cfg[k] = getattr(a, k)
    if a.max_words:
        cfg["max_words"] = a.max_words
    if a.no_caps:
        cfg["caps"] = False
    work = a.work or os.path.splitext(out)[0] + "_captions"
    lst, by = render(load_words(a.words), cfg, info["w"], info["h"], fps, info["dur"], work)
    run(["ffmpeg", "-y", "-i", src, "-f", "concat", "-safe", "0", "-i", lst, "-filter_complex",
         f"[1:v]fps={fps:g},format=rgba[c];[0:v][c]overlay=0:{by}:eof_action=pass:format=auto,format=yuv420p[v]",
         "-map", "[v]", "-map", "0:a?", "-c:v", "libx264", "-preset", "fast", "-crf", "17",
         "-c:a", "copy", "-movflags", "+faststart", out])
    print(f"burned {out}: {count_frames(out)} frames (source {count_frames(src)})")


if __name__ == "__main__":
    main()
