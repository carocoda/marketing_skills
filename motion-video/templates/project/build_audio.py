"""The soundtrack: a music loop cut to the video grid, the voice-over lines on their beats, and a UI sound on
every event in the page. Everything is mixed modulo the loop length, so tails run across the seam and the
audio loops as cleanly as the picture.

  python3 build_audio.py            -> audio/mix.wav (48 kHz stereo, -14 LUFS) + audio/mix_log.json
  python3 build_audio.py --table    only print where every line and word lands (seconds and beats)

Inputs
  motion.html   T, BEATS and window.SFX (the page is the single source of truth for timing)
  project.json  music (file, measured grid, segments), voice lines (vo/<name>.wav, "at" = the beat where the
                words start), mix targets
  vo/<name>.words.json   word times per chosen take (vo_check.py writes them), used for the word table
  assets/sfx/   click, key-press, pop, whoosh-short, impact-bass-1, chime (.wav or .mp3): placeholder.py sfx makes
                synthesised ones; drop in your own files with the same names to change the sound
Missing pieces don't stop the mix: a line without vo/<name>.wav is left out (with a warning), and "music.file": null
makes a video without music. qa.py reports what is missing.
Outputs
  audio/mix.wav, audio/mix_log.json, audio/tmp/stems_*.wav and mix_raw.wav (not for git)
"""
import argparse
import json

import numpy as np
from scipy.signal import resample

from common import HERE, SR, load, page_info, project, save, speech_bounds

db = lambda d: 10 ** (d / 20)
VO_CHAIN = ('highpass=f=75,acompressor=threshold=-22dB:ratio=3:attack=5:release=90:makeup=2,'
            'equalizer=f=3200:t=q:w=1.2:g=1.5')


def add_wrapped(buf, x, start):
    """Add x into buf from sample `start`, modulo the loop length (so a tail past the end lands at the start)."""
    idx = (np.arange(len(x)) + start) % len(buf)
    np.add.at(buf, idx, x)


# ---------------------------------------------------------------- music
def music_loop(m, n_out, beats):
    """Cut the song into the loop: every segment [a, b) is in song beats. At every seam, the continuation of the
    previous segment's end runs xfade_beats into the start of the next (equal-power), including the loop seam
    (last -> first). Then the whole loop is resampled to exactly n_out samples, a tiny tempo change (typically 0.02%)
    that puts the music exactly on the video grid."""
    if not m.get('file'):
        return np.zeros((n_out, 2))
    if not (HERE / m['file']).exists():
        raise SystemExit(f"{m['file']} is missing: python3 placeholder.py music (a placeholder loop), add your own "
                         'track and measure it with beats.py, or set "music": {"file": null} for no music.')
    song = load(HERE / m['file'], ch=2)
    at = lambda b: int(round((m['first_beat'] + b * m['period']) * SR))
    segs = m['segments']
    total = sum(b - a for a, b in segs)
    if abs(total - beats) > 1e-6:
        raise SystemExit(f'music segments add up to {total} beats, the page has BEATS = {beats}')
    xf = int(round(m.get('xfade_beats', 1) * m['period'] * SR))
    f = np.linspace(0, 1, xf)[:, None]
    parts = [song[at(a):at(b)].copy() for a, b in segs]
    for i in range(len(segs)):
        prev_end = segs[i - 1][1]
        cont = song[at(prev_end):at(prev_end) + xf]
        if len(cont) < xf:
            raise SystemExit(f'segment {segs[i - 1]} ends too close to the end of the song for a crossfade')
        parts[i][:xf] = parts[i][:xf] * np.sin(f * np.pi / 2) + cont * np.cos(f * np.pi / 2)
    loop = resample(np.concatenate(parts), n_out, axis=0)      # FFT resample: periodic, so the seam stays clean
    if not np.any(loop):
        return loop
    return loop * db(m.get('rms_db', -21)) / np.sqrt(np.mean(loop ** 2))


# ---------------------------------------------------------------- voice-over
def voiceover(pj, n, beat):
    v = pj['voice']
    out = np.zeros(n)
    fade = int(0.008 * SR)
    placed = []
    for ln in pj['lines']:
        p = HERE / 'vo' / f"{ln['name']}.wav"
        if not p.exists():
            print(f"WARNING: vo/{ln['name']}.wav is missing, the line is left out (tts.py, placeholder.py voice, "
                  'or your own recording)')
            continue
        raw = load(p)
        s0, s1 = speech_bounds(raw)
        seg = load(p, af=VO_CHAIN).astype(np.float64)
        speech = np.abs(seg) > 1e-3
        if speech.any():
            seg *= db(v.get('rms_db', -18) + ln.get('gain_db', 0)) / np.sqrt(np.mean(seg[speech] ** 2))
        seg[:fade] *= np.linspace(0, 1, fade)
        seg[-fade:] *= np.linspace(1, 0, fade)
        start = int(round((ln['at'] * beat - s0) * SR))            # the first word starts exactly on `at`
        add_wrapped(out, seg, start)
        words = []
        wj = HERE / 'vo' / f"{ln['name']}.words.json"
        if wj.exists():
            words = [dict(w, s=round(w['s'] + start / SR, 3), e=round(w['e'] + start / SR, 3))
                     for w in json.load(open(wj, encoding='utf-8'))]
            if words:                                   # Whisper starts the first word in the silence before it
                words[0]['s'] = max(words[0]['s'], round(start / SR + s0, 3))
        placed.append(dict(name=ln['name'], start=start / SR, speech=(start / SR + s0, start / SR + s1),
                           file_len=len(seg) / SR, words=words))
    return out, placed


def check_lines(placed, T, beat):
    problems = []
    sp = sorted(placed, key=lambda p: p['speech'][0])
    for a, b in zip(sp, sp[1:]):
        gap = b['speech'][0] - a['speech'][1]
        if gap < 0.25:
            problems.append(f"{a['name']} ends {abs(gap) if gap < 0 else gap:.2f}s {'after' if gap < 0 else 'before'} "
                            f"{b['name']} starts (want at least 0.25 s of air)")
    for p in placed:
        if p['speech'][0] < 0 or p['speech'][1] > T:
            problems.append(f"{p['name']} runs outside the video (0 to {T:.2f}s): {p['speech'][0]:.2f} to {p['speech'][1]:.2f}s")
    return problems


def print_table(placed, beat):
    for p in placed:
        a, b = p['speech']
        print(f"{p['name']}: {a:6.2f}-{b:6.2f}s   beat {a / beat:6.2f}-{b / beat:6.2f}")
        if p['words']:
            print('     ' + '  '.join(f"{w['w']}@{w['s'] / beat:.2f}" for w in p['words']))
        else:
            print('     (no word times yet: python3 vo_check.py --chosen)')


# ---------------------------------------------------------------- UI sounds
def pitch(x, ratio):
    """Pitch x by `ratio` (shorter and higher above 1) by resampling."""
    n = max(8, int(round(len(x) / ratio)))
    return np.interp(np.linspace(0, len(x) - 1, n), np.arange(len(x)), x)


def pluck(freq, dur=0.9, seed=0):
    """Karplus-Strong string, soft and round: the rising notes under bars landing in a chart."""
    rng = np.random.default_rng(seed)
    p = int(SR / freq)
    buf = rng.uniform(-1, 1, p) * np.hanning(p)
    out = np.zeros(int(dur * SR))
    for i in range(len(out)):
        out[i] = buf[i % p]
        buf[i % p] = 0.4975 * (buf[i % p] + buf[(i + 1) % p])
    out += 0.35 * np.sin(2 * np.pi * freq * np.arange(len(out)) / SR) * np.exp(-np.arange(len(out)) / SR * 5)
    out *= np.minimum(1, np.arange(len(out)) / (0.002 * SR))
    return out / np.abs(out).max()


def clink():
    """Two glasses touching: two inharmonic tings 14 ms apart (C7 and D7: retune to the song's key)."""
    t = np.arange(int(1.2 * SR)) / SR

    def ting(f0, amp):
        parts = [(1.0, 1.0, 5.5), (2.76, 0.5, 9), (5.40, 0.25, 14), (8.93, 0.12, 20)]
        return amp * sum(a * np.sin(2 * np.pi * f0 * r * t) * np.exp(-t * d) for r, a, d in parts)
    x = ting(2093.0, 1.0)
    y = np.zeros_like(x)
    k = int(0.014 * SR)
    y[k:] = ting(2349.3, 0.7)[:-k]
    out = (x + y) * np.minimum(1, t / 0.0015)
    return out / np.abs(out).max()


def sfx_file(name):
    d = HERE / 'assets' / 'sfx'
    for ext in ('.wav', '.mp3', '.m4a', '.ogg', '.flac'):
        if (d / (name + ext)).exists():
            return load(d / (name + ext))
    raise SystemExit(f'assets/sfx/{name}.wav is missing: python3 placeholder.py sfx makes synthesised UI sounds, '
                     'or add your own file with that name.')


def sfx_bank():
    """kind -> [(sound, gain dB), ...]. Kinds are what the page writes in window.SFX. The gains apply to the files
    as they are (not peak-normalised): a balance that was approved on a finished video, tuned for small UI sounds
    from a sound library. With your own, louder files, lower the gains. Add a kind here when the page needs one."""
    click, key, pop = sfx_file('click'), sfx_file('key-press'), sfx_file('pop')
    bank = {
        'click': [(click, -9)],
        'grab': [(pitch(click, 0.86), -14)],
        'drop': [(pitch(click, 0.8), -16)],
        'toggle': [(click, -9), (pitch(pop, 1.25), -17)],
        'pop': [(pop, -13)],
        'tick': [(pitch(click, 1.45), -18)],
        'enter': [(pitch(key, 0.72), -10), (pitch(click, 0.9), -15)],
        'clink': [(clink(), -15)],
        'whoosh': [(sfx_file('whoosh-short'), -17)],
        'slam': [(sfx_file('impact-bass-1'), -15), (click, -12)],
        'stamp': [(pop, -9), (pitch(click, 0.8), -11)],
        'ding': [(sfx_file('chime'), -16)],
    }
    notes = project().get('music', {}).get('pluck_notes', [349.23, 440.0, 523.25, 698.46])
    for i, f in enumerate(notes):                                # rising notes in the song's key (F4 A4 C5 F5)
        bank[f'pluck{i}'] = [(pluck(f, seed=i), -17)]
    return bank, key


def place_sfx(events, n):
    bank, key = sfx_bank()
    out = np.zeros(n)
    rng = np.random.default_rng(7)
    unknown = sorted({e['kind'] for e in events if e['kind'] != 'key' and e['kind'] not in bank})
    if unknown:
        raise SystemExit(f'the page uses sound kinds that build_audio.py does not know: {unknown}')
    for ev in events:
        layers = ([(pitch(key, rng.uniform(0.95, 1.06)), -13 + rng.uniform(-2, 1.5))] if ev['kind'] == 'key'
                  else bank[ev['kind']])
        for x, g in layers:
            pk = int(np.argmax(np.abs(x)))                      # the measured peak lands exactly on the event
            add_wrapped(out, x * db(g), int(round(ev['t'] * SR)) - pk)
    return out


# ---------------------------------------------------------------- mix
def duck_curve(vo, n, depth_db):
    """Music gain under the voice: RMS envelope -> 0..1 speech amount -> attack 40 ms / release 350 ms, run twice
    so the filter state at the loop seam is right."""
    hop = int(0.01 * SR)
    env = np.sqrt(np.convolve(vo ** 2, np.ones(3 * hop) / (3 * hop), mode='same'))
    target = np.clip((20 * np.log10(env + 1e-9) + 50) / 12, 0, 1)
    a_up, a_dn = np.exp(-1 / (0.04 * SR)), np.exp(-1 / (0.35 * SR))
    g, out = 0.0, np.zeros(n)
    for _ in range(2):
        for i in range(0, n, hop):
            a = a_up if target[i] > g else a_dn
            g = a ** hop * g + (1 - a ** hop) * target[i]
            out[i:i + hop] = g
    return db(depth_db * out)


def loudnorm(inp, outp, mx):
    import subprocess
    args = f"I={mx.get('target_lufs', -14)}:TP={mx.get('true_peak', -1.2)}:LRA={mx.get('lra', 11)}"
    r = subprocess.run(['ffmpeg', '-hide_banner', '-i', str(inp), '-af', f'loudnorm={args}:print_format=json',
                        '-f', 'null', '-'], capture_output=True, text=True)
    js = json.loads(r.stderr[r.stderr.rindex('{'):r.stderr.rindex('}') + 1])
    af = (f"loudnorm={args}:measured_I={js['input_i']}:measured_TP={js['input_tp']}:measured_LRA={js['input_lra']}"
          f":measured_thresh={js['input_thresh']}:offset={js['target_offset']}:linear=true")
    subprocess.run(['ffmpeg', '-v', 'error', '-y', '-i', str(inp), '-af', af, '-ar', str(SR), '-c:a', 'pcm_s24le',
                    str(outp)], check=True)
    return js


def main():
    ap = argparse.ArgumentParser()
    ap.add_argument('--table', action='store_true', help='only print where the lines and words land')
    a = ap.parse_args()
    pj = project()
    info = page_info()
    T, beats, beat = info['T'], info['beats'], info['beat']
    n = int(round(T * SR))
    grid = pj['music']['period'] * beats
    if abs(grid - T) / T > 0.005:
        print(f'WARNING: {beats} music beats last {grid:.3f}s but the page says T = {T}s: '
              f'the music gets stretched {100 * (T / grid - 1):+.2f}%. Check BEATS/T in motion.html.')
    vo, placed = voiceover(pj, n, beat)
    print_table(placed, beat)
    problems = check_lines(placed, T, beat)
    for p in problems:
        print('PROBLEM:', p)
    if a.table:
        return
    music = music_loop(pj['music'], n, beats)
    sfx = place_sfx(info['sfx'], n)
    duck = duck_curve(vo, n, pj['music'].get('duck_db', -7.5))
    mix = music * duck[:, None] + vo[:, None] + sfx[:, None]
    if not np.any(mix):
        raise SystemExit('Nothing to mix: no music, no voice and no sounds.')
    tmp = HERE / 'audio' / 'tmp'
    tmp.mkdir(parents=True, exist_ok=True)
    save(tmp / 'stems_music.wav', music * duck[:, None])
    save(tmp / 'stems_vo.wav', vo)
    save(tmp / 'stems_sfx.wav', sfx)
    save(tmp / 'mix_raw.wav', mix)
    js = loudnorm(tmp / 'mix_raw.wav', HERE / 'audio' / 'mix.wav', pj.get('mix', {}))
    log = dict(T=T, beats=beats, lines=[{k: v for k, v in p.items() if k != 'words'} for p in placed],
               sfx=[(round(e['beat'], 2), e['kind']) for e in info['sfx']], loudness_in=js, problems=problems)
    json.dump(log, open(HERE / 'audio' / 'mix_log.json', 'w'), indent=1)
    print(f"{len(info['sfx'])} UI sounds, loudness in {js['input_i']} LUFS -> audio/mix.wav at "
          f"{pj.get('mix', {}).get('target_lufs', -14)} LUFS")


if __name__ == '__main__':
    main()
