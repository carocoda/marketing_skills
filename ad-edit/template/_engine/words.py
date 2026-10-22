"""Words with Whisper large-v3, one window per sentence or shot: each [a,b] window is transcribed on its own (Whisper
aligns much better on short clips that start at a speech onset) and shifted back to source time. Prints words, writes JSON.

  python3 words.py voice.wav out.json 7.74:11.20 11.81:16.32 ... [--prompt "Brand, Name, jargon."] [--lang en] [--model large-v3]

The prompt lists names and jargon from this take, so Whisper spells them right. Windows under ~2.5 s make Whisper
hallucinate; use islands.py to find the speech blocks."""
import json
import sys

import numpy as np

from _whisper import load16, model, opts, usage

args, LANG, MODEL, PROMPT = opts(sys.argv[1:])
if len(args) < 3:
    usage(__doc__)
SRC, OUT = args[0], args[1]
x = load16(SRC)
m = model(MODEL)
res = []
for w in args[2:]:
    a, b = map(float, w.split(':'))
    pad = 0.3
    clip = np.concatenate([np.zeros(int(pad * 16000), np.float32), x[int(a * 16000):int(b * 16000)], np.zeros(int(pad * 16000), np.float32)])
    segs, _ = m.transcribe(clip, language=LANG, beam_size=5, word_timestamps=True, condition_on_previous_text=False,
                           initial_prompt=PROMPT)
    ws = [{'w': q.word.strip(), 's': round(a + q.start - pad, 3), 'e': round(a + q.end - pad, 3)} for s in segs for q in s.words]
    res.append({'win': [a, b], 'words': ws})
    print(f'[{a:.2f}-{b:.2f}] ' + ' '.join(f"{q['w']}@{q['s']:.2f}" for q in ws), flush=True)
json.dump(res, open(OUT, 'w', encoding='utf-8'), ensure_ascii=False, indent=1)
