"""Does removing [x0,x1] lose a word? Transcribes the window a..b with and without that stretch (8 ms fades, like
build.py), and prints the level of the removed part. All words still in "cut"? Then the cut is safe.

  python3 splice_probe.py voice.wav a:x0:x1:b ... [--lang en] [--model large-v3]"""
import sys

import numpy as np

from _whisper import load16, model, opts, usage

SR = 16000
args, LANG, MODEL, PROMPT = opts(sys.argv[1:])
if len(args) < 2:
    usage(__doc__)
x = load16(args[0])
m = model(MODEL)
pad = np.zeros(4000, np.float32)


def tx(c):
    s, _ = m.transcribe(np.concatenate([pad, c, pad]), language=LANG, beam_size=5, condition_on_previous_text=False,
                        initial_prompt=PROMPT)
    return ''.join(q.text for q in s).strip()


for spec in args[1:]:
    a, x0, x1, b = map(float, spec.split(':'))
    f = int(0.008 * SR)
    p1, p2 = x[int(a * SR):int(x0 * SR)].copy(), x[int(x1 * SR):int(b * SR)].copy()
    p1[-f:] *= np.linspace(1, 0, f)
    p2[:f] *= np.linspace(0, 1, f)
    seg = x[int(x0 * SR):int(x1 * SR)]
    lv = 20 * np.log10(np.sqrt(np.mean(seg ** 2)) + 1e-9)
    print(f'{spec}  (cut part {lv:.1f} dBFS)\n   full: {tx(x[int(a * SR):int(b * SR)])}\n   cut : {tx(np.concatenate([p1, p2]))}', flush=True)
