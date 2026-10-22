#!/usr/bin/env python3
"""Turn a transcript into the word list the other scripts use: [{"text","start","end"}].

Accepts:
  * HyperFrames transcript JSON (`npx hyperframes transcribe ...`), a flat list of words
  * openai-whisper / faster-whisper JSON with word timestamps ({"segments": [{"words": [...]}]})
  * SRT or VTT subtitles (YouTube Studio export, any editor). These only have line timings,
    so word times are spread over each line by length. Good enough to pick windows; for
    word-by-word highlight captions, transcribe the short again with word timestamps.

Usage:
  python3 words.py transcript.json -o words.json          # normalise
  python3 words.py words.json --prose                      # read it as running text
  python3 words.py words.json --sheet [--from 10 --to 40]  # word@time sheet for timing graphics
"""
import argparse
import os
import re
import sys

sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
from common import die, load_words, save_words  # noqa: E402

TS = re.compile(r"(?:(\d+):)?(\d{1,2}):(\d{2})[.,](\d{1,3})")


def ts(s):
    m = TS.search(s)
    if not m:
        return None
    h, mi, se, ms = m.groups()
    return int(h or 0) * 3600 + int(mi) * 60 + int(se) + int(ms.ljust(3, "0")) / 1000


def parse_subs(path):
    text = open(path, encoding="utf-8-sig").read().replace("\r", "")
    words = []
    for block in re.split(r"\n\s*\n", text):
        lines = [l for l in block.strip().split("\n") if l.strip()]
        tl = next((i for i, l in enumerate(lines) if "-->" in l), None)
        if tl is None:
            continue
        a, b = lines[tl].split("-->")[:2]
        t0, t1 = ts(a), ts(b)
        if t0 is None or t1 is None or t1 <= t0:
            continue
        body = " ".join(lines[tl + 1:])
        body = re.sub(r"<[^>]+>", "", body)          # VTT inline tags
        toks = body.split()
        if not toks:
            continue
        total = sum(len(t) + 1 for t in toks)
        t = t0
        for tok in toks:
            d = (t1 - t0) * (len(tok) + 1) / total
            words.append({"text": tok, "start": round(t, 3), "end": round(t + d * 0.92, 3)})
            t += d
    return words


def main():
    ap = argparse.ArgumentParser(description=__doc__, formatter_class=argparse.RawDescriptionHelpFormatter)
    ap.add_argument("input", help="transcript: .json, .srt or .vtt")
    ap.add_argument("-o", "--out", help="write the normalised word list here")
    ap.add_argument("--prose", action="store_true", help="print the words as running text")
    ap.add_argument("--sheet", action="store_true", help="print word@start for timing graphics")
    ap.add_argument("--from", dest="t0", type=float, default=None)
    ap.add_argument("--to", dest="t1", type=float, default=None)
    a = ap.parse_args()

    ext = os.path.splitext(a.input)[1].lower()
    if ext in (".srt", ".vtt"):
        words = parse_subs(a.input)
        print(f"note: {a.input} has line timings only; word times are estimated.", file=sys.stderr)
    elif ext == ".json":
        words = load_words(a.input)
    else:
        die("input must be .json, .srt or .vtt")
    if not words:
        die("no words found")

    sel = [w for w in words if (a.t0 is None or w["start"] >= a.t0) and (a.t1 is None or w["start"] < a.t1)]
    if a.out:
        save_words(words, a.out)
        print(f"wrote {len(words)} words, {words[0]['start']:.2f}s to {words[-1]['end']:.2f}s -> {a.out}")
    if a.prose:
        print(" ".join(w["text"] for w in sel))
    if a.sheet:
        print(" ".join(f"{w['text']}@{w['start']:.2f}" for w in sel))
    if not (a.out or a.prose or a.sheet):
        print(f"{len(words)} words. Add -o, --prose or --sheet.")


if __name__ == "__main__":
    main()
