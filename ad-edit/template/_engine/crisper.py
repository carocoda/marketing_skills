"""Word times with CrisperWhisper (nyrahealth/faster_CrisperWhisper): onsets much closer to the truth than Whisper's,
but poorer text, so build.py takes its times and Whisper's words. Optional: without it build.py uses Whisper's times.
CrisperWhisper is trained mainly on English and German; on other languages the times still help, the text does not.
Runs in windows of about 7 s, split at the quietest moment between 5 and 8 s; one long run gives empty or odd output.

  python3 crisper.py voice.wav words_crisper.json [from:to] [--win 7] [--lang en]

Writes a flat list [{w, s, e}] in source seconds. "[UH]" marks are kept but are NOT proof of a filler (references/cutting.md)."""
import json
import sys

import numpy as np

from _whisper import load16, model, opts, usage

SR = 16000
args, LANG, MODEL, _ = opts(sys.argv[1:], default_model='nyrahealth/faster_CrisperWhisper')
WIN = float(args.pop(args.index('--win') + 1)) if '--win' in args else 7.0
args = [x for x in args if x != '--win']
if len(args) < 2:
    usage(__doc__)
SRC, OUT = args[0], args[1]
x = load16(SRC)
a0, b0 = map(float, args[2].split(':')) if len(args) > 2 else (0.0, len(x) / SR)
hop = SR // 100
lv = 20 * np.log10(np.sqrt(np.convolve(x ** 2, np.ones(hop) / hop, 'same')[::hop] + 1e-12))
cuts, t = [a0], a0
while b0 - t > WIN + 1:
    lo, hi = int((t + WIN - 2) * 100), int((t + WIN + 1) * 100)
    t = (lo + int(np.argmin(lv[lo:hi]))) / 100
    cuts.append(t)
cuts.append(b0)
m = model(MODEL)
pad = 0.3
res = []
for a, b in zip(cuts, cuts[1:]):
    clip = np.concatenate([np.zeros(int(pad * SR), np.float32), x[int(a * SR):int(b * SR)], np.zeros(int(pad * SR), np.float32)])
    segs, _ = m.transcribe(clip, language=LANG, beam_size=5, word_timestamps=True, condition_on_previous_text=False)
    ws = [{'w': q.word.strip(), 's': round(a + q.start - pad, 3), 'e': round(a + q.end - pad, 3)} for s in segs for q in s.words]
    res += ws
    print(f'[{a:.2f}-{b:.2f}] ' + ' '.join(f"{q['w']}@{q['s']:.2f}" for q in ws), flush=True)
json.dump(res, open(OUT, 'w', encoding='utf-8'), ensure_ascii=False, indent=1)
