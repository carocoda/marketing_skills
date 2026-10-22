"""Transcribe short windows of the voice to find exactly where a word starts or ends. Use growing windows
(13.9:14.5 13.9:14.8 13.9:15.1) and see where the next word joins. Keep windows at least 2.5 s long.

  python3 probe.py voice.wav 7.3:11.0 7.3:11.2 ... [--lang en] [--model large-v3]"""
import sys

import numpy as np

from _whisper import load16, model, opts, usage

args, LANG, MODEL, PROMPT = opts(sys.argv[1:])
if len(args) < 2:
    usage(__doc__)
x = load16(args[0])
m = model(MODEL)
for w in args[1:]:
    a, b = map(float, w.split(':'))
    clip = np.concatenate([np.zeros(4000, np.float32), x[int(a * 16000):int(b * 16000)], np.zeros(4000, np.float32)])
    segs, _ = m.transcribe(clip, language=LANG, beam_size=5, condition_on_previous_text=False, vad_filter=False,
                           initial_prompt=PROMPT)
    print(f'{a:6.2f}-{b:6.2f}: ' + ''.join(s.text for s in segs).strip(), flush=True)
