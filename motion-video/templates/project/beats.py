"""Measure a song's beat grid, find its loud part, and score a loop cut from it. numpy only.

  python3 beats.py audio/music/song.mp3                          tempo, first beat, downbeats, energy per bar,
                                                                  and T for a few loop lengths
  python3 beats.py audio/music/song.mp3 --segments 33-113,97-113  score a loop made of those song beats: length,
                                                                  how alike every seam is, the energy inside

How it works: spectral-flux onsets -> tempo by autocorrelation -> a comb search over tempo and phase over the
whole song -> downbeats where the kick is strong and the harmony changes (chords change on the "one").
Always measure: Lyria was asked for 120 BPM and made 115, and a grid 4% off drifts a whole beat in 12 seconds.
Writes <song>.beats.json next to the song.
"""
import argparse
import json
import shutil
import subprocess
from pathlib import Path

import numpy as np

SR, HOP, NFFT = 22050, 256, 2048
LATENCY = 0.075     # s: spectral flux peaks about 75 ms before the onset it belongs to (a window of 2048 samples
                    # sees it coming). Calibrated on a synthetic kick track: without this, beats come out 75 ms early.


def load(path):
    if not Path(path).exists():
        raise SystemExit(f'{path} does not exist')
    if not shutil.which('ffmpeg'):
        raise SystemExit('Missing ffmpeg: install it first (macOS: brew install ffmpeg).')
    raw = subprocess.run(['ffmpeg', '-v', 'error', '-i', path, '-ac', '1', '-ar', str(SR), '-f', 'f32le', '-'],
                         capture_output=True, check=True).stdout
    return np.frombuffer(raw, dtype=np.float32).copy()


def stft_mag(x):
    win = np.hanning(NFFT).astype(np.float32)
    n = 1 + (len(x) - NFFT) // HOP
    idx = np.arange(NFFT)[None, :] + HOP * np.arange(n)[:, None]
    return np.abs(np.fft.rfft(x[idx] * win, axis=1))


def analyse(x, bpm_hint):
    S = stft_mag(x)
    freqs = np.fft.rfftfreq(NFFT, 1 / SR)
    flux = np.concatenate([[0], np.maximum(0, np.diff(np.log1p(S * 10), axis=0)).sum(axis=1)])
    flux = (flux - np.convolve(flux, np.ones(16) / 16, mode='same')).clip(0)
    fps = SR / HOP
    ac = np.correlate(flux, flux, mode='full')[len(flux) - 1:]
    bpms = 60 / np.maximum(np.arange(len(ac)) / fps, 1e-9)
    cand = int(np.argmax(ac * ((bpms > 70) & (bpms < 180))))
    a, b, c = ac[cand - 1], ac[cand], ac[cand + 1]
    bpm = 60 / ((cand + 0.5 * (a - c) / (a - 2 * b + c)) / fps)
    if abs(bpm * 2 - bpm_hint) < abs(bpm - bpm_hint):
        bpm *= 2
    if abs(bpm / 2 - bpm_hint) < abs(bpm - bpm_hint):
        bpm /= 2
    best, t_env = (-1, None, None), np.arange(len(flux)) / fps + LATENCY
    for tb in np.arange(bpm - 0.6, bpm + 0.6, 0.01):
        period = 60 / tb
        for ph in np.arange(0, period, 0.005):
            sc = np.interp(np.arange(ph, t_env[-1], period), t_env, flux).sum()
            if sc > best[0]:
                best = (sc, tb, ph)
    _, bpm, phase = best
    period = 60 / bpm
    beats = np.arange(phase, len(x) / SR - 0.01, period)
    low = np.log1p(S[:, (freqs > 35) & (freqs < 130)].sum(axis=1))
    Hm = S[:, (freqs > 100) & (freqs < 4000)]
    fi = lambda t: min(max(0, int((t - LATENCY) * fps)), len(S) - 1)
    scores = []
    for k in range(4):
        nov = []
        for t in beats[k::4]:
            if fi(t + period) - fi(t) < 2 or fi(t) - fi(max(0, t - period)) < 2:
                continue                                   # the first and last beat have no full window
            before = Hm[fi(max(0, t - period)):fi(t)].mean(axis=0) + 1e-9
            after = Hm[fi(t):fi(t + period)].mean(axis=0) + 1e-9
            nov.append(1 - np.dot(before, after) / np.linalg.norm(before) / np.linalg.norm(after))
        scores.append(np.mean([low[fi(t)] for t in beats[k::4]]) * 0.2 + np.mean(nov) * 10)
    return float(bpm), float(period), float(phase), int(np.argmax(scores)), [round(float(s), 3) for s in scores]


def beat_chroma(x, first, period):
    """A 12-note chroma per beat (80 Hz to 4 kHz), minus the song's average: which chord is sounding."""
    n = int((len(x) / SR - first) / period)
    N = 16384
    f = np.fft.rfftfreq(N, 1 / SR)
    m = (f > 80) & (f < 4000)
    pc = np.round(12 * np.log2(f[m] / 440)).astype(int) % 12
    out = []
    for k in range(n):
        a, b = int((first + k * period) * SR), int((first + (k + 1) * period) * SR)
        spec = np.abs(np.fft.rfft(x[a:b] * np.hanning(b - a), n=N))[m] ** 2
        c = np.bincount(pc, weights=spec, minlength=12)
        out.append(c / (c.sum() + 1e-9))
    C = np.array(out)
    return C - C.mean(0)


def sim(C, i, j, span=4):
    """How alike the bar starting on song beat i is to the bar starting on song beat j (cosine of chroma)."""
    a, b = C[i:i + span].ravel(), C[j:j + span].ravel()
    return float(np.dot(a, b) / (np.linalg.norm(a) * np.linalg.norm(b) + 1e-9))


def chord_cycle(C, k):
    """In how many bars the chords repeat (the phrase length): the bar lag with the most alike chroma."""
    bars = np.array([C[s:s + 4].mean(0) for s in range(k, len(C) - 4, 4)])
    best = max((2, 4, 8), key=lambda L: np.mean([np.dot(bars[i], bars[i + L]) / (np.linalg.norm(bars[i]) * np.linalg.norm(bars[i + L]) + 1e-9)
                                                 for i in range(len(bars) - L)]))
    return best


def main():
    ap = argparse.ArgumentParser()
    ap.add_argument('song')
    ap.add_argument('--bpm', type=float, default=120.0, help='what you asked for (helps pick between half and double)')
    ap.add_argument('--segments', help='a loop in song beats, e.g. 33-113,97-113')
    ap.add_argument('--fps', type=int, default=60)
    a = ap.parse_args()
    x = load(a.song)
    bpm, period, first, k, scores = analyse(x, a.bpm)
    F = beat_chroma(x, first, period)
    n = len(F)
    cyc = chord_cycle(F, k)
    bar_db = [round(float(20 * np.log10(np.sqrt(np.mean(x[int((first + b * period) * SR):int((first + (b + 4) * period) * SR)] ** 2)) + 1e-9)), 1)
              for b in range(k, n - 3, 4)]
    loud = max(bar_db)
    runs = []                                              # stretches of bars within 3 dB of the loudest bar
    for i, d in enumerate(bar_db):
        if d > loud - 3:
            b0 = k + 4 * i
            if runs and runs[-1][1] == b0:
                runs[-1][1] = b0 + 4
            else:
                runs.append([b0, b0 + 4])
    json.dump(dict(bpm=round(bpm, 3), period=period, first_beat=round(first, 4), downbeat_phase=k, chord_cycle_bars=cyc,
                   downbeat_scores=scores, bar_db=bar_db, beats=n),
              open(a.song.rsplit('.', 1)[0] + '.beats.json', 'w'), indent=1)
    print(f'{bpm:.3f} BPM, beat = {period:.6f} s, first beat at {first:.3f} s, {n} beats in the song')
    print(f'downbeats ("the one") on song beats {k}, {k + 4}, {k + 8}, ... (score per position {scores})')
    print(f'the chords repeat every {cyc} bars ({4 * cyc} beats): make loop segments a multiple of {4 * cyc} beats')
    print(f'energy per bar (dB, bar starting on song beat):')
    print('   ' + '  '.join(f'{k + 4 * i}:{d}' for i, d in enumerate(bar_db)))
    if runs:
        print('loud parts (bars within 3 dB of the loudest), in song beats: '
              + ', '.join(f'{a}-{b} ({(b - a) // 4} bars)' for a, b in runs) + '. Cut the loop from these.')
    print('\nloop length -> T (whole frames at %d fps) and how much the music gets stretched to fit:' % a.fps)
    for nb in (48, 64, 80, 96, 112, 128):
        T = round(nb * period * a.fps) / a.fps
        print(f'   {nb:3d} beats = {nb // 4:2d} bars -> T = {T:.4f} s ({round(T * a.fps)} frames), stretch {100 * (T / (nb * period) - 1):+.3f}%')

    if a.segments:
        segs = [tuple(int(v) for v in s.split('-')) for s in a.segments.split(',')]
        total = sum(e - s for s, e in segs)
        print(f'\nloop {segs}: {total} beats = {total / 4:g} bars')
        for i, (s, e) in enumerate(segs):
            ns = segs[(i + 1) % len(segs)][0]
            print(f'   seam after {s}-{e}: what follows song beat {e} vs song beat {ns}: similarity {sim(F, e, ns):.3f}')
            if (s - k) % 4:
                print(f'   WARNING: {s} is not a downbeat (downbeats are {k} + 4n)')
            if (e - s) % (4 * cyc):
                print(f'   note: {e - s} beats is not a whole number of {4 * cyc}-beat phrases, so the chords will not line up')
            if e + 2 > n:
                print(f'   WARNING: {e} is too close to the end of the song for the crossfade')
        print('   (chord similarity of the bar after the cut vs the bar it jumps to: above 0.3 very alike, 0.1 to 0.3 same '
              'chords with a slightly different arrangement, around 0 or below: the chords do not line up, move the cut. '
              'a loop that scored 0.75 and 0.15 had no audible seam)')
    print('\nproject.json "music": {"period": %.6f, "first_beat": %.3f, "bpm": %.3f, "segments": [[start, end], ...]}'
          % (period, first, bpm))


if __name__ == '__main__':
    main()
