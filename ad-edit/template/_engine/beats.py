"""Measure a song's beat grid and loudness per bar, so build.py can land the song's final hit on the end card.
numpy only.

  python3 beats.py music/bed.mp3 [--bpm 110]

Writes <song>.beats.json next to the song and suggests the edit.json "music" block (end_beat, hit_beat).
How it works: spectral-flux onsets -> tempo by autocorrelation -> a comb search over tempo and phase over the whole
song -> downbeats where the kick is strong and the harmony changes. Always measure: a track sold as 112 BPM can be 110,
and a grid that is a few percent off drifts a whole beat within seconds.
"""
import argparse
import json
import subprocess

import numpy as np

SR, HOP, NFFT = 22050, 256, 2048


def load(path):
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
    den = (a - 2 * b + c) or 1e-9
    bpm = 60 / ((cand + 0.5 * (a - c) / den) / fps)
    if bpm_hint:
        if abs(bpm * 2 - bpm_hint) < abs(bpm - bpm_hint):
            bpm *= 2
        if abs(bpm / 2 - bpm_hint) < abs(bpm - bpm_hint):
            bpm /= 2
    best, t_env = (-1, None, None), np.arange(len(flux)) / fps
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
    fi = lambda t: min(int(t * fps), len(S) - 1)
    scores = []
    for k in range(4):
        nov = []
        for t in beats[k::4]:
            if fi(t + period) - fi(t) < 2 or fi(t) - fi(max(0, t - period)) < 2:
                continue
            before = Hm[fi(max(0, t - period)):fi(t)].mean(axis=0) + 1e-9
            after = Hm[fi(t):fi(t + period)].mean(axis=0) + 1e-9
            nov.append(1 - np.dot(before, after) / np.linalg.norm(before) / np.linalg.norm(after))
        scores.append(np.mean([low[fi(t)] for t in beats[k::4]]) * 0.2 + (np.mean(nov) if nov else 0) * 10)
    return float(bpm), float(period), float(phase), int(np.argmax(scores)), len(beats)


def main():
    ap = argparse.ArgumentParser(description=__doc__, formatter_class=argparse.RawDescriptionHelpFormatter)
    ap.add_argument('song')
    ap.add_argument('--bpm', type=float, default=0, help='the tempo you expect, helps pick between half and double')
    ap.add_argument('--phrase', type=int, default=16, help='beats per phrase (16 = 4 bars of 4/4)')
    a = ap.parse_args()
    x = load(a.song)
    bpm, period, first, k, n = analyse(x, a.bpm)
    bar_db = [round(float(20 * np.log10(np.sqrt(np.mean(x[int((first + b * period) * SR):int((first + (b + 4) * period) * SR)] ** 2)) + 1e-9)), 1)
              for b in range(k, n - 3, 4)]
    json.dump(dict(bpm=round(bpm, 3), period=period, first_beat=round(first, 4), downbeat_phase=k, bar_db=bar_db, beats=n),
              open(a.song.rsplit('.', 1)[0] + '.beats.json', 'w'), indent=1)
    print(f'{bpm:.3f} BPM, beat = {period:.6f} s, first beat at {first:.3f} s, {n} beats in the song')
    print(f'downbeats on song beats {k}, {k + 4}, {k + 8}, ...')
    print('energy per bar (dB, bar starting on song beat):')
    print('   ' + '  '.join(f'{k + 4 * i}:{d}' for i, d in enumerate(bar_db)))
    # the final hit: the bar after the last loud bar, where the level drops hard (the song's own ending)
    loud = max(bar_db) if bar_db else 0
    hit = next((k + 4 * (i + 1) for i in range(len(bar_db) - 2, -1, -1)
                if bar_db[i] > loud - 6 and bar_db[i + 1] < bar_db[i] - 8), None)
    if hit and hit - a.phrase >= 0:
        print(f'\nsuggested edit.json "music": {{"end_beat": {hit - a.phrase}, "hit_beat": {hit}, "phrase": {a.phrase}, '
              f'"hit_after_endcard": 1.4}}')
        print('   (hit_beat = the bar where the level falls away after the last loud bar; check it by ear)')
    else:
        print('\nno clear ending found (the song may fade out or loop). Leave end_beat/hit_beat out: build.py then '
              'uses the song from "start" and fades it out at the end.')


if __name__ == '__main__':
    main()
