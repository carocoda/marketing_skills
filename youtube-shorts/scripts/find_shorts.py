#!/usr/bin/env python3
"""Clip selection helpers. The editorial choice (which idea makes a good short) is made by the
agent and the user in chat; this script does the mechanical part.

  sentences   print the transcript as numbered sentences with times, to read and pick from
  candidates  rough map of sentence runs that fit the target length (a starting point only)
  snap        take your chosen windows, move every edge into a pause between words,
              snap lengths to whole frames, and check the rules (max length, unique hooks,
              no mid-sentence starts or ends, optional audio silence check)

Spec file for `snap` (times in seconds of the long video):
  {"fps": 30, "max_len": 60,
   "shorts": [
     {"id": 1, "title": "How X works",
      "windows": [{"role": "hook",   "start": 12.4, "end": 19.0},
                  {"role": "body",   "start": 83.1, "end": 131.5},
                  {"role": "closer", "start": 402.0, "end": 405.8}]}]}

Usage:
  python3 find_shorts.py sentences words.json
  python3 find_shorts.py candidates words.json --min 35 --max 60
  python3 find_shorts.py snap spec.json --words words.json [--video long.mp4] -o spec.snapped.json
"""
import argparse
import json
import math
import os
import struct
import subprocess
import sys

sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
from common import die, ends_sentence, load_words, need  # noqa: E402


def sentences(words, gap=0.6):
    out, cur = [], []
    for i, w in enumerate(words):
        cur.append(w)
        following = words[i + 1] if i + 1 < len(words) else None
        if following is None or ends_sentence(w["text"]) or following["start"] - w["end"] >= gap:
            out.append({"start": cur[0]["start"], "end": cur[-1]["end"],
                        "text": " ".join(x["text"] for x in cur), "i0": i - len(cur) + 1, "i1": i})
            cur = []
    return out


def fmt(t):
    return f"{int(t // 60)}:{t % 60:05.2f}"


def cmd_sentences(a):
    words = load_words(a.words)
    for n, s in enumerate(sentences(words, a.gap), 1):
        print(f"#{n:<4} {fmt(s['start'])}-{fmt(s['end'])} ({s['end'] - s['start']:4.1f}s)  {s['text']}")


def cmd_candidates(a):
    S = sentences(load_words(a.words), a.gap)
    i, n = 0, 0
    while i < len(S):
        j = i
        while j + 1 < len(S) and S[j + 1]["end"] - S[i]["start"] <= a.max:
            j += 1
        d = S[j]["end"] - S[i]["start"]
        if d >= a.min:
            n += 1
            print(f"C{n:<3} {fmt(S[i]['start'])}-{fmt(S[j]['end'])} ({d:4.1f}s, sentences {i + 1}-{j + 1})")
            print(f"      starts: {S[i]['text'][:110]}")
            print(f"      ends:   {S[j]['text'][-110:]}")
            i = j + 1
        else:
            i += 1
    if n == 0:
        print("no runs in that range; lower --min or raise --max")


# ---------- snap ----------

def rms_db(video, t, span=0.06, sr=16000):
    """Loudness (dBFS) of the quietest 10 ms slice in [t - span, t + span]."""
    start = max(0.0, t - span)
    cmd = ["ffmpeg", "-hide_banner", "-v", "error", "-ss", f"{start:.3f}", "-t", f"{2 * span:.3f}",
           "-i", video, "-vn", "-ac", "1", "-ar", str(sr), "-f", "s16le", "-"]
    raw = subprocess.run(cmd, capture_output=True).stdout
    n = len(raw) // 2
    if n == 0:
        return None
    s = struct.unpack(f"<{n}h", raw[:n * 2])
    step = sr // 100
    best = 0.0
    for k in range(0, max(1, n - step + 1), step):
        seg = s[k:k + step]
        v = math.sqrt(sum(x * x for x in seg) / max(1, len(seg))) / 32768.0
        best = v if k == 0 else min(best, v)
    return 20 * math.log10(best) if best > 0 else -120.0


def snap_start(words, t, min_gap, reach):
    """Pick the word nearest to t that has a pause before it; cut inside that pause."""
    best = None
    for i, w in enumerate(words):
        if abs(w["start"] - t) > reach:
            continue
        gap = w["start"] - (words[i - 1]["end"] if i else 0.0)
        if gap < min_gap and i:
            continue
        d = abs(w["start"] - t)
        if best is None or d < best[0]:
            best = (d, i, gap)
    if best is None:
        return None
    _, i, gap = best
    lead = min(0.12, gap / 2) if i else min(0.12, words[0]["start"])
    return words[i]["start"] - lead, i


def snap_end(words, t, min_gap, reach):
    best = None
    for i, w in enumerate(words):
        if abs(w["end"] - t) > reach:
            continue
        gap = (words[i + 1]["start"] - w["end"]) if i + 1 < len(words) else 1.0
        if gap < min_gap:
            continue
        d = abs(w["end"] - t)
        if best is None or d < best[0]:
            best = (d, i, gap)
    if best is None:
        return None
    _, i, gap = best
    tail = min(0.3, gap * 0.6)
    return words[i]["end"] + tail, i


def cmd_snap(a):
    spec = json.load(open(a.spec, encoding="utf-8"))
    words = load_words(a.words)
    fps = float(spec.get("fps", a.fps))
    max_len = float(spec.get("max_len", a.max_len))
    if a.video:
        need("ffmpeg")
    problems = 0
    hooks = []
    for sh in spec["shorts"]:
        total_frames = 0
        print(f"\nShort {sh.get('id', '?')}: {sh.get('title', '')}")
        for k, win in enumerate(sh["windows"]):
            role = win.get("role", f"w{k}")
            s = snap_start(words, win["start"], a.min_gap, a.reach)
            e = snap_end(words, win["end"], a.min_gap, a.reach)
            if s is None or e is None:
                print(f"  ! {role}: no pause of {a.min_gap}s within {a.reach}s of "
                      f"{'start' if s is None else 'end'}; pick another edge")
                problems += 1
                win.pop("frames", None)
                win["error"] = "not snapped"
                continue
            win.pop("error", None)
            (st, i0), (en, i1) = s, e
            f0 = math.floor(st * fps + 1e-6)              # start on a frame boundary
            nf = max(1, round((en - f0 / fps) * fps))     # whole frames
            st, en = f0 / fps, (f0 + nf) / fps
            # never let the frame snap push the end into the next word
            if i1 + 1 < len(words) and en > words[i1 + 1]["start"] - 0.02:
                nf -= 1
                en = (f0 + nf) / fps
            win.update(start=round(st, 4), end=round(en, 4), frames=nf)
            total_frames += nf
            text = " ".join(w["text"] for w in words[i0:i1 + 1])
            win["text"] = text
            notes = []
            if i0 > 0 and not ends_sentence(words[i0 - 1]["text"]):
                notes.append("starts mid-sentence")
            if not ends_sentence(words[i1]["text"]):
                notes.append("ends mid-sentence")
            if a.video:
                for label, t in (("start", st), ("end", en)):
                    db = rms_db(a.video, t)
                    if db is not None and db > a.silence_db:
                        notes.append(f"{label} not silent ({db:.0f} dB > {a.silence_db:.0f})")
            print(f"  {role:<7} {fmt(st)}-{fmt(en)} {nf / fps:5.2f}s  \"{text[:60]}"
                  f"{'...' if len(text) > 60 else ''}\"")
            for n in notes:
                print(f"          ! {n}")
                problems += 1
            if role == "hook":
                hooks.append((sh.get("id"), st, en, text))
        # overlap within a short
        ws = sorted(sh["windows"], key=lambda w: w["start"])
        for x, y in zip(ws, ws[1:]):
            if y["start"] < x["end"]:
                print("  ! two windows overlap; the viewer hears the same words twice")
                problems += 1
        sh["frames"] = total_frames
        sh["duration"] = round(total_frames / fps, 3)
        flag = "" if sh["duration"] <= max_len else f"  ! over the {max_len:.0f}s cap"
        if flag:
            problems += 1
        print(f"  total {sh['duration']:.2f}s ({total_frames} frames){flag}")
    # unique hooks across the series
    for i in range(len(hooks)):
        for j in range(i + 1, len(hooks)):
            a_, b_ = hooks[i], hooks[j]
            if a_[1] < b_[2] and b_[1] < a_[2]:
                print(f"\n! shorts {a_[0]} and {b_[0]} open with the same lines. Every short needs its own hook.")
                problems += 1
    spec["fps"] = fps
    spec["max_len"] = max_len
    out = a.out or a.spec.replace(".json", ".snapped.json")
    json.dump(spec, open(out, "w", encoding="utf-8"), ensure_ascii=False, indent=1)
    print(f"\n{problems} warning(s). Wrote {out}")


def main():
    ap = argparse.ArgumentParser(description=__doc__, formatter_class=argparse.RawDescriptionHelpFormatter)
    sub = ap.add_subparsers(dest="cmd", required=True)
    p = sub.add_parser("sentences"); p.add_argument("words"); p.add_argument("--gap", type=float, default=0.6)
    p = sub.add_parser("candidates"); p.add_argument("words")
    p.add_argument("--min", type=float, default=35); p.add_argument("--max", type=float, default=60)
    p.add_argument("--gap", type=float, default=0.6)
    p = sub.add_parser("snap"); p.add_argument("spec"); p.add_argument("--words", required=True)
    p.add_argument("--video", help="long video; checks that every cut sits in silence")
    p.add_argument("--fps", type=float, default=30); p.add_argument("--max-len", type=float, default=60)
    p.add_argument("--min-gap", type=float, default=0.15, help="minimum pause between words at a cut (s)")
    p.add_argument("--reach", type=float, default=1.5, help="how far an edge may move (s)")
    p.add_argument("--silence-db", type=float, default=-42.0)
    p.add_argument("-o", "--out")
    a = ap.parse_args()
    {"sentences": cmd_sentences, "candidates": cmd_candidates, "snap": cmd_snap}[a.cmd](a)


if __name__ == "__main__":
    main()
