#!/usr/bin/env python3
"""Check your setup without a real video: makes a 60-second synthetic "long video" with ffmpeg
(test pattern + tone "sentences" with pauses) and a matching word list, then runs the whole
captions-only path: sentences -> snap -> cut (9:16) -> sounds -> assemble with captions,
title card and end screen -> contact sheet. Takes about a minute. No network, no API keys.

Usage: python3 selftest.py [--out selftest-output] [--aspect 9x16]
"""
import argparse
import json
import os
import subprocess
import sys

HERE = os.path.dirname(os.path.abspath(__file__))
sys.path.insert(0, HERE)
from common import need, require_pillow, run  # noqa: E402

VOCAB = ("this is how the new feature works and why it matters for your team so here is "
         "the first step you open the settings then you pick a plan and that is really all").split()


def make_inputs(out):
    """Sentences of 5-9 words, 0.38 s per word, 0.55 s pause between sentences."""
    words, t, i, s = [], 1.0, 0, 0
    tones = []
    while t < 57:
        n = 5 + (s * 3) % 5
        start = t
        for j in range(n):
            w = VOCAB[i % len(VOCAB)]
            i += 1
            if j == 0:
                w = w.capitalize()
            if j == n - 1:
                w += "."
            words.append({"text": w, "start": round(t, 3), "end": round(t + 0.32, 3)})
            t += 0.38
        tones.append((start, t - 0.06, 180 + 40 * (s % 4)))
        t += 0.55
        s += 1
    expr = "+".join(f"0.3*between(t,{a:.3f},{b:.3f})*sin(2*PI*{f}*t)" for a, b, f in tones)
    src = os.path.join(out, "long.mp4")
    run(["ffmpeg", "-y", "-f", "lavfi", "-i", "testsrc2=size=1920x1080:rate=25:duration=60",
         "-f", "lavfi", "-i", f"aevalsrc='{expr}':s=48000:d=60",
         "-c:v", "libx264", "-preset", "ultrafast", "-crf", "28", "-pix_fmt", "yuv420p",
         "-c:a", "aac", "-shortest", src])
    wp = os.path.join(out, "words_long.json")
    json.dump(words, open(wp, "w"), indent=0)
    return src, wp, words


def py(*args):
    cmd = [sys.executable, os.path.join(HERE, args[0])] + list(args[1:])
    print("\n$ " + " ".join(os.path.basename(c) if i == 1 else c for i, c in enumerate(cmd[1:], 1)))
    r = subprocess.run(cmd, text=True, capture_output=True)
    print(r.stdout.strip()[-1500:])
    if r.returncode not in (0,):
        print(r.stderr.strip()[-1500:])
        sys.exit(f"selftest failed at {args[0]}")
    return r.stdout


def main():
    ap = argparse.ArgumentParser(description=__doc__, formatter_class=argparse.RawDescriptionHelpFormatter)
    ap.add_argument("--out", default="selftest-output")
    ap.add_argument("--aspect", default="9x16")
    a = ap.parse_args()
    need("ffmpeg"); need("ffprobe"); require_pillow()
    out = os.path.abspath(a.out)
    os.makedirs(out, exist_ok=True)
    src, wp, words = make_inputs(out)
    py("find_shorts.py", "sentences", wp)
    # deliberately rough edges (mid-word) so snap has something to fix
    spec = {"fps": 30, "max_len": 30, "shorts": [
        {"id": 1, "title": "Selftest short", "windows": [
            {"role": "hook", "start": 39.0, "end": 41.6},
            {"role": "body", "start": 8.2, "end": 22.9, "punch": [15.0]}]}]}
    sp = os.path.join(out, "spec.json")
    json.dump(spec, open(sp, "w"), indent=1)
    py("find_shorts.py", "snap", sp, "--words", wp, "--video", src, "-o", os.path.join(out, "spec.snapped.json"))
    clip = os.path.join(out, "work", "clip.mp4")
    py("cut_short.py", "--src", src, "--spec", os.path.join(out, "spec.snapped.json"), "--short", "1",
       "--aspect", a.aspect, "--center", "0.5", "--words", wp, "--out", clip,
       "--words-out", os.path.join(out, "work", "words.json"))
    py("make_sfx.py", "--out", os.path.join(out, "sfx"))
    plan = {
        "src": "work/clip.mp4", "out": "Short 1 - Selftest.mp4", "work": "work",
        "captions": {"words": "work/words.json", "style": "bold", "highlight": "#FFD400"},
        "title": {"text": "How the new feature works", "sub": "Selftest", "t0": 0, "t1": 3.0},
        "sfx": [{"t": 0.2, "path": "sfx/ding.wav", "gain": 0.35}, {"t": 6.0, "path": "sfx/pop.wav", "gain": 0.3}],
        "end_screen": {"headline": "Watch the full video on YouTube", "title": "The long video title goes here",
                       "line": "youtube.com/@yourchannel", "cta": "Link in the comments", "duration": 3.0},
    }
    pp = os.path.join(out, "plan.json")
    json.dump(plan, open(pp, "w"), indent=1)
    res = py("assemble.py", pp, "--preview")
    final = os.path.join(out, "Short 1 - Selftest.mp4")
    py("contact_sheet.py", final, "--at", "0.4", "2.0", "6.1", "12.0", "19.0",
       str(round(float(res.split("frames = ")[1].split("s")[0]) - 1.0, 2)),
       "-o", os.path.join(out, "sheet.png"))
    py("captions.py", os.path.join(out, "work", "words.json"), "--burn", clip,
       os.path.join(out, "captions-only-pill.mp4"), "--style", "pill")
    print(f"\nSELFTEST OK. Open {final} and {os.path.join(out, 'sheet.png')} to look at the result.")


if __name__ == "__main__":
    main()
