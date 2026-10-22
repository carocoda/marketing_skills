"""Check voice takes with Whisper (in project.json voice.language): what was really said, how sure Whisper is per word, pauses, pace and
pitch. It ranks the takes of a line so you know which ones to listen to first. It never replaces listening.

  python3 vo_check.py s2                    every take of line s2 (vo/takes/s2_*.wav) against its text
  python3 vo_check.py --chosen              the chosen take of every line (vo/<name>.wav); writes
                                            vo/<name>.words.json, which build_audio.py uses for the word table
  python3 vo_check.py a.wav b.wav --text "Ready?"         any files against a text
  python3 vo_check.py compare Anna vo/takes/s2_d.wav --ref good.wav --ref bad.wav
                                            which reference does the take's word sound most like (MFCC + DTW)?
  --whisper large-v3|turbo|medium|small     pick a model (default: the best one already on this computer)

Columns: WER = word error rate against the text (0 is perfect), p = Whisper's mean word confidence, low = words
under 0.6, pause = gaps over 0.45 s inside the line, w/s = words per second, F0 sd = pitch movement in
semitones (under 2 sounds flat), jumps = pitch jumps over 5 semitones per second (glitches, "robot").
What real projects taught: names and brand names go wrong most ("Claude" came out as "cloud" or "Klaat", a name
ending in -a as the same name ending in -e, "ChatGPT" as "Chet GPT"). A low p on a name is the cue to listen extra
carefully. Whisper is not the judge of names: use compare, then listen.
Needs faster-whisper (pip3 install faster-whisper) and a multilingual model on disk (ask before downloading).
"""
import argparse
import json
import re
import subprocess
import sys
import unicodedata
from pathlib import Path

import numpy as np

from common import HERE, project, transcribe, whisper_model

SR16 = 16000


def norm_words(s, aliases):
    s = unicodedata.normalize('NFKD', s.lower())
    s = ''.join(c for c in s if not unicodedata.combining(c))
    s = s.replace('-', ' ').replace("'", '').replace('’', '')
    s = re.sub(r'[^a-z0-9 ]', ' ', s)
    s = ' ' + ' '.join(s.split()) + ' '
    for k in sorted(aliases, key=len, reverse=True):
        kk = ' ' + ' '.join(re.sub(r'[^a-z0-9 ]', ' ', k.lower()).split()) + ' '
        s = s.replace(kk, ' ' + aliases[k] + ' ')
    return s.split()


def wer(ref, hyp):
    d = np.zeros((len(ref) + 1, len(hyp) + 1))
    d[:, 0], d[0, :] = range(len(ref) + 1), range(len(hyp) + 1)
    for i in range(1, len(ref) + 1):
        for j in range(1, len(hyp) + 1):
            d[i, j] = min(d[i - 1, j] + 1, d[i, j - 1] + 1, d[i - 1, j - 1] + (ref[i - 1] != hyp[j - 1]))
    return d[-1, -1] / max(1, len(ref))


def load16(p):
    return np.frombuffer(subprocess.run(['ffmpeg', '-v', 'error', '-i', str(p), '-ac', '1', '-ar', str(SR16), '-f', 'f32le', '-'],
                                        capture_output=True, check=True).stdout, np.float32)


def f0_track(x):
    """Autocorrelation pitch per 10 ms (40 ms window), NaN where unvoiced."""
    n, hop, out = 640, 160, []
    for i in range(0, len(x) - n, hop):
        f = x[i:i + n] - x[i:i + n].mean()
        if np.sqrt(np.mean(f ** 2)) < 0.02:
            out.append(np.nan)
            continue
        ac = np.correlate(f, f, 'full')[n - 1:]
        ac /= ac[0] + 1e-9
        lo, hi = SR16 // 400, SR16 // 120
        k = lo + np.argmax(ac[lo:hi])
        out.append(SR16 / k if ac[k] > 0.45 else np.nan)
    return np.array(out)


def pitch_stats(x):
    f0 = f0_track(x)
    v = f0[~np.isnan(f0)]
    if len(v) < 5:
        return 0.0, 0.0
    st = 12 * np.log2(v / np.median(v))
    both = ~np.isnan(f0[1:]) & ~np.isnan(f0[:-1])
    jumps = np.abs(12 * np.log2(f0[1:][both] / f0[:-1][both]))
    return float(np.std(st)), float(np.sum(jumps > 5) / (len(x) / SR16))


def check(model, path, text, aliases):
    said, words = transcribe(model, path)
    x = load16(path)
    sd, jumps = pitch_stats(x)
    speech = (words[-1]['e'] - words[0]['s']) if words else 0
    pauses = [(words[i]['w'], round(words[i + 1]['s'] - words[i]['e'], 2)) for i in range(len(words) - 1)
              if words[i + 1]['s'] - words[i]['e'] > 0.45]
    return dict(file=Path(path).name, dur=round(len(x) / SR16, 2), said=said,
                wer=round(wer(norm_words(text, aliases), norm_words(said, aliases)), 3) if text else None,
                p=round(float(np.mean([w['p'] for w in words])), 3) if words else 0,
                low=[(w['w'], w['p']) for w in words if w['p'] < 0.6], pauses=pauses,
                wps=round(len(words) / speech, 2) if speech else 0, f0_sd=round(sd, 2), jumps=round(jumps, 2),
                words=words)


def show(rows):
    rows = sorted(rows, key=lambda r: ((r['wer'] if r['wer'] is not None else 0), -r['p'], r['jumps']))
    for i, r in enumerate(rows):
        flags = []
        if r['low']:
            flags.append('low: ' + ', '.join(f'{w} {p:.2f}' for w, p in r['low']))
        if r['pauses']:
            flags.append('pause after: ' + ', '.join(f'{w} {g}s' for w, g in r['pauses']))
        if r['f0_sd'] < 2:
            flags.append('flat pitch')
        if r['jumps'] > 1.5:
            flags.append('pitch glitches')
        w = f"WER {r['wer']:.2f}  " if r['wer'] is not None else ''
        print(f"{'>' if i == 0 else ' '} {r['file']:14s} {r['dur']:5.2f}s  {w}p {r['p']:.2f}  {r['wps']:.1f} w/s  "
              f"F0 sd {r['f0_sd']:.1f}  jumps {r['jumps']:.1f}/s")
        print(f"     heard: {r['said']}")
        if flags:
            print('     ' + ' | '.join(flags))
    return rows


# ---------------------------------------------------------------- one word, compared by sound
def mfcc(x):
    n, hop = 400, 160
    fr = np.lib.stride_tricks.sliding_window_view(x, n)[::hop] * np.hamming(n)
    P = np.abs(np.fft.rfft(fr, 512)) ** 2
    mel = lambda f: 2595 * np.log10(1 + f / 700)
    imel = lambda m: 700 * (10 ** (m / 2595) - 1)
    bins = np.floor(513 * imel(np.linspace(mel(80), mel(7600), 28)) / SR16).astype(int)
    fb = np.zeros((26, 257))
    for i in range(26):
        a, b, c = bins[i], bins[i + 1], bins[i + 2]
        fb[i, a:b] = (np.arange(a, b) - a) / max(1, b - a)
        fb[i, b:c] = (c - np.arange(b, c)) / max(1, c - b)
    E = np.log(P @ fb.T + 1e-10)
    D = np.cos(np.pi / 26 * (np.arange(26)[None, :] + 0.5) * np.arange(1, 14)[:, None])
    M = E @ D.T
    return (M - M.mean(0)) / (M.std(0) + 1e-6)


def dtw(A, B):
    n, m = len(A), len(B)
    C = np.full((n + 1, m + 1), np.inf)
    C[0, 0] = 0
    d = np.linalg.norm(A[:, None, :] - B[None, :, :], axis=2)
    for i in range(1, n + 1):
        for j in range(1, m + 1):
            C[i, j] = d[i - 1, j - 1] + min(C[i - 1, j], C[i, j - 1], C[i - 1, j - 1])
    return C[n, m] / (n + m)


def word_mfcc(model, path, word):
    _, words = transcribe(model, path)
    key = word.lower()[:4]
    w = next((w for w in words if w['w'].lower().startswith(key)), None)
    if not w:
        raise SystemExit(f'Whisper found no word starting with "{key}" in {path}')
    x = load16(path)
    return mfcc(x[int((w['s'] - 0.03) * SR16):int((w['e'] + 0.03) * SR16)]), w['w']


def main():
    if len(sys.argv) > 1 and sys.argv[1] == 'compare':
        ap = argparse.ArgumentParser()
        ap.add_argument('cmd')
        ap.add_argument('word')
        ap.add_argument('take')
        ap.add_argument('--ref', action='append', required=True, help='a take where the word sounds right (first) or wrong')
        ap.add_argument('--whisper')
        a = ap.parse_args()
        model, _ = whisper_model(a.whisper)
        M, heard = word_mfcc(model, a.take, a.word)
        print(f'{a.take}: Whisper hears "{heard}"')
        dists = []
        for r in a.ref:
            R, rh = word_mfcc(model, r, a.word)
            dists.append(dtw(M, R))
            print(f'  distance to {Path(r).name} ("{rh}"): {dists[-1]:.3f}')
        ds = sorted(dists)
        if len(ds) > 1 and ds[1] - ds[0] < 0.02 * ds[0]:
            print('Too close to call: listen to it.')
        else:
            print(f'Sounds most like {Path(a.ref[dists.index(ds[0])]).name}. A hint, not a verdict: listen too.')
        return

    ap = argparse.ArgumentParser()
    ap.add_argument('items', nargs='*', help='a line name, or wav files with --text')
    ap.add_argument('--text')
    ap.add_argument('--chosen', action='store_true')
    ap.add_argument('--whisper')
    a = ap.parse_args()
    pj = project()
    lines = {ln['name']: ln for ln in pj.get('lines', [])}
    aliases = pj.get('heard_as', {})
    model, name = whisper_model(a.whisper)
    print(f"(Whisper {name}, language {pj.get('voice', {}).get('language') or 'auto'})")
    if a.chosen:
        for n, ln in lines.items():
            p = HERE / 'vo' / f'{n}.wav'
            if not p.exists():
                print(f'{n}: no vo/{n}.wav yet')
                continue
            r = check(model, p, ln['text'], aliases)
            json.dump(r['words'], open(HERE / 'vo' / f'{n}.words.json', 'w'), ensure_ascii=False, indent=0)
            print(f'\n{n}: {ln["text"]}')
            show([r])
        print('\nWord times saved: python3 build_audio.py --table shows where every word lands in beats.')
        return
    if a.text is not None:
        rows = [check(model, p, a.text, aliases) for p in a.items]
        show(rows)
        return
    for n in a.items:
        if n not in lines:
            raise SystemExit(f'no line {n!r} in project.json (have {", ".join(lines)})')
        takes = sorted((HERE / 'vo' / 'takes').glob(f'{n}_*.wav'))
        if not takes:
            raise SystemExit(f'no takes for {n}: python3 tts.py {n}')
        print(f'\n{n}: {lines[n]["text"]}')
        rows = [check(model, p, lines[n]['text'], aliases) for p in takes]
        for r in rows:
            json.dump(r['words'], open(HERE / 'vo' / 'takes' / (Path(r['file']).stem + '.words.json'), 'w'),
                      ensure_ascii=False, indent=0)
        best = show(rows)[0]
        print(f"  -> listen to {best['file']} first. Keep one with:  python3 tts.py {n} --use "
              f"{Path(best['file']).stem.split('_')[-1]}")


if __name__ == '__main__':
    main()
