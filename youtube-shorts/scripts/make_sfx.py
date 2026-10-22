#!/usr/bin/env python3
"""Make a small, royalty-free sound kit with ffmpeg (no downloads, no licences to check).

  pop.wav      soft pop for a card or pill appearing
  ding.wav     two-note chime for the title card
  pair.wav     quick double tick for "two things appear together"
  success.wav  rising three-note chime for the pay-off moment
  whoosh.wav   short air sweep for a transition
  click.wav    UI click for a cursor tap

Usage: python3 make_sfx.py --out sfx/
You can also use your own sounds (any wav/mp3) in the plan's "sfx" list.
"""
import argparse
import os
import sys

sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
from common import need, run  # noqa: E402

PI = "PI"
SOUNDS = {
    "pop": ("0.12", f"0.9*sin(2*{PI}*(170*t+520/24*(1-exp(-24*t))))*exp(-30*t)", ""),
    "ding": ("0.9", f"0.55*sin(2*{PI}*880*t)*exp(-7*t)+0.45*gt(t,0.11)*sin(2*{PI}*1318.5*(t-0.11))*exp(-6*(t-0.11))", ""),
    "pair": ("0.25", f"0.7*sin(2*{PI}*1200*t)*exp(-60*t)+0.7*gt(t,0.09)*sin(2*{PI}*1500*(t-0.09))*exp(-60*(t-0.09))", ""),
    "success": ("1.0", "+".join(
        f"0.4*gt(t,{d})*sin(2*{PI}*{f}*(t-{d}))*exp(-5*(t-{d}))"
        for d, f in ((0, 659.25), (0.09, 830.6), (0.18, 987.8))), ""),
    "whoosh": ("0.5", f"(random(0)*2-1)*pow(sin({PI}*t/0.5),2)", "highpass=f=400,lowpass=f=3000,"),
    "click": ("0.05", f"0.8*sin(2*{PI}*2400*t)*exp(-140*t)", ""),
}


def main():
    ap = argparse.ArgumentParser(description=__doc__, formatter_class=argparse.RawDescriptionHelpFormatter)
    ap.add_argument("--out", default="sfx")
    a = ap.parse_args()
    need("ffmpeg")
    os.makedirs(a.out, exist_ok=True)
    for name, (dur, expr, filt) in SOUNDS.items():
        path = os.path.join(a.out, f"{name}.wav")
        run(["ffmpeg", "-y", "-f", "lavfi", "-i", f"aevalsrc='{expr}':s=48000:d={dur}",
             "-af", f"{filt}afade=t=out:st={float(dur) * 0.7:.3f}:d={float(dur) * 0.3:.3f},volume=0.9",
             "-ac", "1", "-ar", "48000", path])
        print(f"wrote {path}")


if __name__ == "__main__":
    main()
