#!/usr/bin/env python3
"""Cut one short from the long video: hook + body (+ closer) in ONE ffmpeg run, reframed to the
target format, with a hidden punch-in zoom on every join. Also writes the short's own word list
(times shifted to the short).

Why one run: encoding each window separately and joining the files drifts the audio against the
picture. trim/atrim + concat inside one filter graph keeps them locked.

Usage:
  python3 cut_short.py --src long.mp4 --spec spec.snapped.json --short 1 --aspect 9x16 \
      --center 0.55 --words words.json --out work/clip.mp4 --words-out work/words.json

Reframe:
  --center X        horizontal centre of the crop as a fraction of the source width (0.5 = middle).
                    Measure where the speaker's face is on a few stills first.
  --zoom Z          punch-in used on every other segment (default 1.08; 1.0 turns it off)
  --anchor AX,AY    where a zoom pulls towards inside the crop (default 0.5,0.35: the face, not the belly)
A window may also carry "zoom": 1.12 (forces that value) and "punch": [t, ...] (absolute source
times of hidden cuts inside the window; each one starts a new segment with the other zoom).
"""
import argparse
import json
import os
import sys

sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
from common import ASPECTS, count_frames, die, load_words, need, probe, run, save_words  # noqa: E402


def even(x):
    return max(2, int(round(x / 2.0)) * 2)


def main():
    ap = argparse.ArgumentParser(description=__doc__, formatter_class=argparse.RawDescriptionHelpFormatter)
    ap.add_argument("--src", required=True, help="the long video (use the cleanest master you have)")
    ap.add_argument("--spec", required=True, help="output of find_shorts.py snap")
    ap.add_argument("--short", required=True, help="id of the short in the spec")
    ap.add_argument("--aspect", default="9x16", choices=sorted(ASPECTS))
    ap.add_argument("--center", type=float, default=0.5)
    ap.add_argument("--zoom", type=float, default=1.08)
    ap.add_argument("--anchor", default="0.5,0.35")
    ap.add_argument("--words", help="word list of the long video")
    ap.add_argument("--words-out")
    ap.add_argument("--out", required=True)
    ap.add_argument("--crf", type=int, default=16)
    ap.add_argument("--preset", default="fast")
    a = ap.parse_args()
    need("ffmpeg")

    spec = json.load(open(a.spec, encoding="utf-8"))
    fps = float(spec.get("fps", 30))
    sh = next((s for s in spec["shorts"] if str(s.get("id")) == str(a.short)), None)
    if sh is None:
        die(f"short {a.short} not in {a.spec}")
    bad = [w.get("role", "?") for w in sh["windows"] if "frames" not in w]
    if "frames" not in sh or bad:
        die("these windows are not snapped to pauses and frames yet: " + ", ".join(bad or ["all"]) +
            ". Fix the edges in the spec and run `find_shorts.py snap` again.")

    info = probe(a.src)
    if not info["audio"]:
        die("the source has no audio track")
    W, H = info["w"], info["h"]
    TW, TH = ASPECTS[a.aspect]
    ax, ay = (float(x) for x in a.anchor.split(","))

    # base crop: the largest rectangle of the target shape that fits the source
    ar = TW / TH
    if W / H > ar:
        bh, bw = H, even(H * ar)
    else:
        bw, bh = W, even(W / ar)
    bx = min(max(0, int(a.center * W - bw / 2)), W - bw)
    by = (H - bh) // 2
    if bw < TW * 0.75:
        print(f"note: the crop is {bw}x{bh} px and gets scaled up to {TW}x{TH}. "
              f"Use a higher-resolution master if you have one.", file=sys.stderr)

    # segments: windows split on punch points, alternating zoom
    segs = []
    for win in sh["windows"]:
        cuts = [win["start"]] + sorted(t for t in win.get("punch", []) if win["start"] < t < win["end"]) + [win["end"]]
        for k in range(len(cuts) - 1):
            segs.append({"start": cuts[k], "end": cuts[k + 1], "zoom": win.get("zoom") if k == 0 else None})
    zoom_now = 1.0
    for i, s in enumerate(segs):
        if s["zoom"] is None:
            s["zoom"] = zoom_now if i == 0 else (a.zoom if zoom_now == 1.0 else 1.0)
        zoom_now = s["zoom"]

    def frame(t):
        return round(t * fps)

    n = len(segs)
    parts = [f"[0:v]fps={fps:g},split={n}" + "".join(f"[s{i}]" for i in range(n)) if n > 1
             else f"[0:v]fps={fps:g}[s0]"]
    for i, s in enumerate(segs):
        z = float(s["zoom"])
        cw, ch = even(bw / z), even(bh / z)
        cx = bx + int((bw - cw) * ax)
        cy = by + int((bh - ch) * ay)
        f0, f1 = frame(s["start"]), frame(s["end"])
        parts.append(f"[s{i}]trim=start_frame={f0}:end_frame={f1},setpts=PTS-STARTPTS,"
                     f"crop={cw}:{ch}:{cx}:{cy},scale={TW}:{TH}:flags=lanczos,setsar=1[v{i}]")
        parts.append(f"[0:a]atrim=start={f0 / fps:.6f}:end={f1 / fps:.6f},asetpts=PTS-STARTPTS[a{i}]")
    parts.append("".join(f"[v{i}][a{i}]" for i in range(n)) + f"concat=n={n}:v=1:a=1[v][a]")
    os.makedirs(os.path.dirname(os.path.abspath(a.out)), exist_ok=True)
    run(["ffmpeg", "-y", "-i", a.src, "-filter_complex", ";".join(parts), "-map", "[v]", "-map", "[a]",
         "-c:v", "libx264", "-preset", a.preset, "-crf", str(a.crf), "-pix_fmt", "yuv420p", "-r", f"{fps:g}",
         "-c:a", "aac", "-b:a", "192k", "-ar", "48000", "-movflags", "+faststart", a.out])

    want = sum(frame(s["end"]) - frame(s["start"]) for s in segs)
    got = count_frames(a.out)
    status = "ok" if got == want else "MISMATCH"
    print(f"clip {a.out}: {TW}x{TH}, {got} frames ({got / fps:.2f}s), expected {want}: {status}")
    print("segments: " + ", ".join(f"{s['start']:.2f}-{s['end']:.2f}@{s['zoom']:.2f}" for s in segs))

    if a.words:
        words = load_words(a.words)
        out, off = [], 0.0
        for win in sh["windows"]:
            st, en = frame(win["start"]) / fps, frame(win["end"]) / fps
            for w in words:
                if st <= w["start"] < en:
                    out.append({"text": w["text"], "start": round(w["start"] - st + off, 3),
                                "end": round(min(w["end"], en) - st + off, 3)})
            off += en - st
        wo = a.words_out or os.path.splitext(a.out)[0] + "_words.json"
        save_words(out, wo)
        print(f"words {wo}: {len(out)} words. Read them as prose before you build captions:")
        print("  " + " ".join(w["text"] for w in out))
    if got != want:
        sys.exit(2)


if __name__ == "__main__":
    main()
