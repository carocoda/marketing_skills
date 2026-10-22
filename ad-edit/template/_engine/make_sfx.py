"""Synthesise the default UI sounds, so the skill ships no audio files and there is no licence question.

  python3 make_sfx.py <folder>         writes pop, click, key-press, whoosh-short, impact-bass-1, chime (.wav, 48 kHz)

Want other sounds? Drop your own files with the same names (wav, mp3, m4a) into the folder; build.py takes any of
these extensions. Only use sounds you have the rights to (your own, or a library licence that allows ads).
"""
import sys
import wave
from pathlib import Path

import numpy as np

SR = 48000
rng = np.random.default_rng(7)                       # fixed seed: the same sounds every time


def t(sec):
    return np.arange(int(sec * SR)) / SR


def env(n, attack, decay):
    x = np.arange(n) / SR
    return np.minimum(1, x / max(attack, 1e-4)) * np.exp(-x / decay)


def lowpass(x, cutoff):
    a = np.exp(-2 * np.pi * cutoff / SR)
    y = np.empty_like(x)
    acc = 0.0
    for i, v in enumerate(x):
        acc = (1 - a) * v + a * acc
        y[i] = acc
    return y


def pop():
    tt = t(0.12)
    f = 900 * np.exp(-tt * 28) + 380                 # a quick downward blip
    x = np.sin(2 * np.pi * np.cumsum(f) / SR) * env(len(tt), 0.002, 0.03)
    return x


def click():
    n = int(0.03 * SR)
    x = rng.standard_normal(n) * env(n, 0.0005, 0.004)
    return x - lowpass(x, 1500)                      # bright tick


def key_press():
    n = int(0.08 * SR)
    tick = click()
    thud = np.sin(2 * np.pi * 140 * t(0.08)) * env(n, 0.001, 0.02) * 0.6
    x = thud.copy()
    x[:len(tick)] += tick * 0.7
    return x


def whoosh():
    tt = t(0.55)
    n = len(tt)
    noise = rng.standard_normal(n)
    sweep = np.empty(n)
    acc, cut = 0.0, 300 + 4500 * np.sin(np.pi * tt / tt[-1]) ** 2   # filter opens and closes
    for i in range(n):
        a = np.exp(-2 * np.pi * cut[i] / SR)
        acc = (1 - a) * noise[i] + a * acc
        sweep[i] = acc
    return sweep * np.sin(np.pi * tt / tt[-1]) ** 1.5


def impact():
    tt = t(2.0)
    f = 55 + 70 * np.exp(-tt * 12)                   # sub drop
    body = np.sin(2 * np.pi * np.cumsum(f) / SR) * env(len(tt), 0.002, 0.45)
    hit = lowpass(rng.standard_normal(len(tt)), 900) * env(len(tt), 0.001, 0.05) * 1.5
    return body + hit


def chime():
    tt = t(1.4)
    x = np.zeros(len(tt))
    for f0, g, d in ((1318.5, 1.0, 0.5), (1975.5, 0.6, 0.35), (2637.0, 0.3, 0.25), (1760.0, 0.5, 0.4)):
        x += g * np.sin(2 * np.pi * f0 * tt) * env(len(tt), 0.002, d)
    return x


SOUNDS = {'pop': pop, 'click': click, 'key-press': key_press, 'whoosh-short': whoosh, 'impact-bass-1': impact, 'chime': chime}


def write(path, x, peak_db=-1.0):
    x = x / (np.max(np.abs(x)) + 1e-9) * 10 ** (peak_db / 20)
    fade = min(len(x), int(0.004 * SR))
    x[-fade:] *= np.linspace(1, 0, fade)
    with wave.open(str(path), 'wb') as w:
        w.setnchannels(1)
        w.setsampwidth(2)
        w.setframerate(SR)
        w.writeframes((x * 32767).astype('<i2').tobytes())


def main():
    if len(sys.argv) < 2:
        raise SystemExit(__doc__)
    out = Path(sys.argv[1])
    out.mkdir(parents=True, exist_ok=True)
    for name, fn in SOUNDS.items():
        write(out / f'{name}.wav', fn())
    print(f'{len(SOUNDS)} sounds in {out}: {", ".join(SOUNDS)}')


if __name__ == '__main__':
    main()
