"""Free stand-ins, made on this computer: no downloads, no keys. So the template renders and mixes out of the box,
and you can time a video before you spend anything.

  python3 placeholder.py              sfx + music (new_project.py runs this)
  python3 placeholder.py sfx          assets/sfx/: click, key-press, pop, whoosh-short, impact-bass-1, chime (.wav)
  python3 placeholder.py music        audio/music/placeholder.wav: a 120 BPM loop in F major (I-V-vi-IV, 4 bars)
  python3 placeholder.py voice        a scratch voice for every line without a take: macOS "say" if it exists,
                                      else a hum per word. Marked as scratch (qa.py warns) until you replace it.
  python3 placeholder.py voice --say-voice Samantha     pick a macOS voice (say -v '?' lists them)
  --force                             overwrite files that already exist

The synthesised UI sounds are fine to ship; swap in your own files with the same names whenever you like. The music
and the scratch voice are only for building and timing: replace them before a video goes out.
"""
import argparse
import shutil
import subprocess
import tempfile
from pathlib import Path

import numpy as np
from scipy.signal import butter, lfilter

from common import HERE, SR, load, need, project, save

rng = np.random.default_rng(11)
t_ = lambda dur: np.arange(int(dur * SR)) / SR


def norm(x, peak_db=-3.0):
    return x / (np.abs(x).max() + 1e-12) * 10 ** (peak_db / 20)


def filt(x, kind, f):
    b, a = butter(2, np.array(f) / (SR / 2), kind)
    return lfilter(b, a, x)


def fade(x, a=0.001, r=0.004):
    n_a, n_r = int(a * SR), int(r * SR)
    x = x.copy()
    if n_a:
        x[:n_a] *= np.linspace(0, 1, n_a)
    if n_r:
        x[-n_r:] *= np.linspace(1, 0, n_r)
    return x


# ---------------------------------------------------------------- UI sounds
def sfx():
    out = {}
    t = t_(0.06)
    out['click'] = fade(filt(rng.normal(0, 1, len(t)), 'highpass', 2500) * np.exp(-t / 0.004)
                        + 0.6 * np.sin(2 * np.pi * 1900 * t) * np.exp(-t / 0.006))
    t = t_(0.05)
    out['key-press'] = fade(0.7 * filt(rng.normal(0, 1, len(t)), 'bandpass', [2500, 6500]) * np.exp(-t / 0.003)
                            + np.sin(2 * np.pi * 900 * t) * np.exp(-t / 0.008))
    t = t_(0.14)
    f = 320 + 700 * np.exp(-t / 0.025)
    out['pop'] = fade(np.sin(2 * np.pi * np.cumsum(f) / SR) * np.exp(-t / 0.03) * np.minimum(1, t / 0.002))
    t = t_(0.5)
    env = np.sin(np.pi * np.clip(t / 0.5, 0, 1)) ** 2
    noise = rng.normal(0, 1, len(t))
    lo, hi = filt(noise, 'bandpass', [300, 1500]), filt(noise, 'bandpass', [1500, 5000])
    out['whoosh-short'] = fade(env * (lo * (1 - t / 0.5) + hi * (t / 0.5)), 0.01, 0.02)
    t = t_(0.6)
    f = 42 + 80 * np.exp(-t / 0.06)
    out['impact-bass-1'] = fade(np.tanh(1.6 * np.sin(2 * np.pi * np.cumsum(f) / SR)) * np.exp(-t / 0.18)
                                + 0.4 * filt(rng.normal(0, 1, len(t)), 'lowpass', 900) * np.exp(-t / 0.02), 0.001, 0.05)
    t = t_(1.4)
    bell = lambda f0, a: a * sum(k * np.sin(2 * np.pi * f0 * r * t) * np.exp(-t * d)
                                 for r, k, d in [(1, 1, 3.2), (2.76, 0.35, 6), (5.4, 0.15, 10)])
    out['chime'] = fade(bell(1318.5, 1.0) + np.concatenate([np.zeros(int(0.09 * SR)), bell(1760.0, 0.8)])[:len(t)], 0.002, 0.1)
    return {k: norm(v) for k, v in out.items()}


# ---------------------------------------------------------------- music
def music(beats=80, bpm=120.0):
    """Kick, clap, hats, bass and soft chords. 80 beats so a 64-beat loop has room for the crossfade."""
    beat = 60 / bpm
    n = int(beats * beat * SR)
    L, R = np.zeros(n), np.zeros(n)

    def add(x, at, pan=0.0, g=1.0):
        i = int(round(at * SR))
        if i >= n:
            return
        x = x[:n - i] * g
        L[i:i + len(x)] += x * np.sqrt((1 - pan) / 2) * np.sqrt(2)
        R[i:i + len(x)] += x * np.sqrt((1 + pan) / 2) * np.sqrt(2)

    t = t_(0.25)
    kick = np.sin(2 * np.pi * np.cumsum(48 + 110 * np.exp(-t / 0.03)) / SR) * np.exp(-t / 0.12)
    kick += 0.5 * filt(rng.normal(0, 1, len(t)), 'bandpass', [1500, 6000]) * np.exp(-t / 0.004)   # the beater click
    t = t_(0.12)
    clap = filt(rng.normal(0, 1, len(t)), 'bandpass', [900, 3500]) * np.exp(-t / 0.035)
    t = t_(0.05)
    hat = filt(rng.normal(0, 1, len(t)), 'highpass', 7000) * np.exp(-t / 0.012)
    # F  C  Dm  Bb (one bar each), as MIDI notes
    chords = [[53, 57, 60], [48, 52, 55], [50, 53, 57], [46, 50, 53]]
    hz = lambda m: 440 * 2 ** ((m - 69) / 12)
    for b in range(beats):
        at = b * beat
        add(kick, at, 0, 0.9)
        if b % 2 == 1:
            add(clap, at, 0.1, 0.35)
        add(hat, at + beat / 2, -0.4, 0.07)
        add(hat, at + beat * 0.75, 0.4, 0.03)
        ch = chords[(b // 4) % 4]
        for e in (0,):                                          # bass on the beat, the root an octave down
            tt = t_(beat * 0.8)
            f0 = hz(ch[0] - 12)
            bass = np.tanh(1.5 * (np.sin(2 * np.pi * f0 * tt) + 0.3 * np.sin(4 * np.pi * f0 * tt)))
            add(fade(bass * np.exp(-tt / 0.18), 0.003, 0.02), at + e * beat, 0, 0.35)
        if b % 4 == 0:                                          # a soft chord per bar
            tt = t_(beat * 4)
            pad = sum(sum(np.sin(2 * np.pi * hz(m) * k * tt + k) / k ** 1.6 for k in (1, 2, 3)) for m in ch)
            env = np.minimum(1, tt / 0.08) * np.exp(-tt / 1.6)
            add(fade(filt(pad, 'lowpass', 2400) * env, 0.003, 0.05), at, 0, 0.12)
        if b % 2 == 0:                                          # a little pluck on the chord tones
            tt = t_(0.3)
            m = ch[(b // 2) % 3] + 12
            pl = np.sin(2 * np.pi * hz(m) * tt) * np.exp(-tt / 0.08)
            add(fade(pl, 0.002, 0.02), at, 0.25 if b % 4 else -0.25, 0.1)
    x = np.stack([L, R], axis=1)
    return x / np.abs(x).max() * 0.8


# ---------------------------------------------------------------- scratch voice
def scratch_voice(lines, say_voice=None, force=False):
    has_say = shutil.which('say') is not None
    for ln in lines:
        out = HERE / 'vo' / f"{ln['name']}.wav"
        if out.exists() and not force:
            print(f'keep  vo/{out.name} (already there; --force to replace)')
            continue
        text = ln.get('say', ln['text'])
        if has_say:
            tmp = Path(tempfile.mkdtemp()) / 'say.aiff'
            cmd = ['say', '-o', str(tmp)] + (['-v', say_voice] if say_voice else []) + [text]
            subprocess.run(cmd, check=True)
            x = np.concatenate([np.zeros(int(0.2 * SR)), load(tmp), np.zeros(int(0.2 * SR))])
            how = 'macOS say'
        else:                                                   # a hum per word, at about 2.8 words per second
            parts = [np.zeros(int(0.2 * SR))]
            for w in text.split():
                d = 0.12 + 0.045 * len(w)
                tt = t_(d)
                f0 = 190 + 25 * rng.uniform(-1, 1)
                v = sum(np.sin(2 * np.pi * f0 * k * tt) / k for k in range(1, 6))
                parts += [v * np.sin(np.pi * tt / d) ** 2 * 0.3, np.zeros(int(0.08 * SR))]
            parts.append(np.zeros(int(0.2 * SR)))
            x = np.concatenate(parts)
            how = 'hum'
        save(out, x)
        (HERE / 'vo' / f"{ln['name']}.scratch").write_text(f'scratch voice ({how}), replace before shipping\n')
        (HERE / 'vo' / f"{ln['name']}.words.json").unlink(missing_ok=True)
        print(f'made  vo/{out.name} ({how}, {len(x) / SR:.1f}s, scratch)')


def main():
    ap = argparse.ArgumentParser()
    ap.add_argument('what', nargs='*', default=['sfx', 'music'], help='sfx, music, voice')
    ap.add_argument('--force', action='store_true')
    ap.add_argument('--say-voice')
    a = ap.parse_args()
    need('ffmpeg')
    if 'sfx' in a.what:
        for name, x in sfx().items():
            p = HERE / 'assets' / 'sfx' / f'{name}.wav'
            if p.exists() and not a.force:
                continue
            save(p, x)
        print('UI sounds -> assets/sfx/ (synthesised)')
    if 'music' in a.what:
        p = HERE / 'audio' / 'music' / 'placeholder.wav'
        if not p.exists() or a.force:
            save(p, music())
        print('placeholder music -> audio/music/placeholder.wav (120 BPM, F major; replace before you ship)')
    if 'voice' in a.what:
        scratch_voice(project().get('lines', []), a.say_voice, a.force)


if __name__ == '__main__':
    main()
