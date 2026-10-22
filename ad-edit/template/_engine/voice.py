"""Studio voice from a phone recording: WPE dereverb -> DeepFilterNet (full) -> EQ preset with de-esser and compressor.

  python3 voice.py <raw48k.wav> <outdir> [--eq warm] [--taps 18 --delay 3]      -> <outdir>/voice_<eq>.wav
  python3 voice.py --list                                                         the presets

Presets (references/voice.md): bright, warm, studio, warmer, clear-warm, warm-far. Start with two or three, measure
them with voice_metrics.py, and pick by ear. Missing tools degrade gracefully:
  nara_wpe missing   -> no dereverb (pip3 install nara_wpe)
  deep-filter missing -> ffmpeg afftdn, a much weaker denoiser (see README for the DeepFilterNet binary)
deep-filter is looked up in $AD_EDIT_TOOLS (default ~/.local/ad-edit-tools) and then on the PATH.
"""
import os
import shutil
import subprocess
import sys
from pathlib import Path

import numpy as np

SR = 48000

EQ = {
    # bright: clear, but can read as too sharp on a voice with a strong upper-mid resonance
    'bright': ('highpass=f=80,equalizer=f=170:t=q:w=1.0:g=2.5,equalizer=f=380:t=q:w=1.4:g=-2,'
               'equalizer=f=2900:t=q:w=1.2:g=-1.5,highshelf=f=10000:g=1.5,'
               'deesser=i=0.6:m=0.5:f=0.45,acompressor=threshold=-24dB:ratio=2.5:attack=8:release=120:makeup=2,alimiter=limit=0.9'),
    # warm: tuned on a voice with a 1.6 kHz resonance (+7 dB over 1 kHz) that read as shrill: cut it, give body where the
    # fundamental sits (~240 Hz there), tame 2.6 kHz only when it spikes, darker top, denser compression.
    'warm': ('highpass=f=90,equalizer=f=240:t=q:w=1.0:g=2,equalizer=f=480:t=q:w=1.5:g=-1.5,'
             'equalizer=f=1600:t=q:w=1.4:g=-4,equalizer=f=2100:t=q:w=1.4:g=-1.5,'
             'adynamicequalizer=dfrequency=2600:dqfactor=1.2:tfrequency=2600:tqfactor=1.2:mode=cutabove:auto=on:ratio=3:range=6:attack=5:release=80,'
             'equalizer=f=4500:t=q:w=1.2:g=-1.5,highshelf=f=7500:g=-1.5,deesser=i=0.7:m=0.5:f=0.5,'
             'acompressor=threshold=-26dB:ratio=3.5:attack=6:release=110:makeup=3,alimiter=limit=0.9'),
    # studio: warm + a soft downward expander that dries up the room tail between words + denser compression.
    # A stricter expander (range 0.08) made a soft hook unintelligible.
    'studio': ('agate=threshold=0.005:ratio=2:range=0.18:attack=3:release=130:knee=6,' +
               'highpass=f=90,equalizer=f=240:t=q:w=1.0:g=2.5,equalizer=f=480:t=q:w=1.5:g=-1.5,'
               'equalizer=f=1600:t=q:w=1.4:g=-4,equalizer=f=2100:t=q:w=1.4:g=-1.5,'
               'adynamicequalizer=dfrequency=2600:dqfactor=1.2:tfrequency=2600:tqfactor=1.2:mode=cutabove:auto=on:ratio=3:range=6:attack=5:release=80,'
               'equalizer=f=4500:t=q:w=1.2:g=-1.5,highshelf=f=7500:g=-1.5,deesser=i=0.7:m=0.5:f=0.5,'
               'acompressor=threshold=-28dB:ratio=4:attack=5:release=100:makeup=4:knee=4,alimiter=limit=0.9'),
    # warmer: studio plus extra warmth: fuller low mids (fundamental + first harmonic), the 1.6 kHz bite cut deeper,
    # a softer top end. Can turn muddy on a voice that is already dark.
    'warmer': ('agate=threshold=0.005:ratio=2:range=0.18:attack=3:release=130:knee=6,' +
               'highpass=f=85,lowshelf=f=180:g=1.5,equalizer=f=240:t=q:w=1.0:g=3.5,equalizer=f=480:t=q:w=1.5:g=-1,'
               'equalizer=f=1600:t=q:w=1.3:g=-5.5,equalizer=f=2200:t=q:w=1.4:g=-2.5,'
               'adynamicequalizer=dfrequency=2600:dqfactor=1.2:tfrequency=2600:tqfactor=1.2:mode=cutabove:auto=on:ratio=3:range=6:attack=5:release=80,'
               'equalizer=f=4500:t=q:w=1.2:g=-2,highshelf=f=6500:g=-3,deesser=i=0.7:m=0.5:f=0.5,'
               'acompressor=threshold=-28dB:ratio=4:attack=5:release=100:makeup=4:knee=4,alimiter=limit=0.9'),
    # clear-warm: for a voice that is warm and soft-topped by itself. Same dry treatment, light body, no deep mid cuts,
    # a little air back. Milder expander (range 0.4 = -8 dB): the stricter one ate soft final consonants.
    'clear-warm': ('agate=threshold=0.005:ratio=2:range=0.4:attack=3:release=160:knee=6,' +
                   'highpass=f=90,equalizer=f=230:t=q:w=1.2:g=2,equalizer=f=450:t=q:w=1.5:g=-1.5,'
                   'equalizer=f=1600:t=q:w=1.4:g=-1.5,'
                   'adynamicequalizer=dfrequency=2600:dqfactor=1.2:tfrequency=2600:tqfactor=1.2:mode=cutabove:auto=on:ratio=3:range=6:attack=5:release=80,'
                   'highshelf=f=7000:g=1,deesser=i=0.5:m=0.5:f=0.5,'
                   'acompressor=threshold=-28dB:ratio=4:attack=5:release=100:makeup=4:knee=4,alimiter=limit=0.9'),
    # warm-far: a speaker further from the phone (dull top, same 1.6 kHz bite). The 1.6 kHz cut, light body only,
    # a little air back, mild expander so soft endings survive.
    'warm-far': ('agate=threshold=0.005:ratio=2:range=0.4:attack=3:release=160:knee=6,' +
                 'highpass=f=90,equalizer=f=240:t=q:w=1.0:g=2.5,equalizer=f=480:t=q:w=1.5:g=-1.5,'
                 'equalizer=f=1600:t=q:w=1.3:g=-4.5,equalizer=f=2200:t=q:w=1.4:g=-1.5,'
                 'adynamicequalizer=dfrequency=2600:dqfactor=1.2:tfrequency=2600:tqfactor=1.2:mode=cutabove:auto=on:ratio=3:range=6:attack=5:release=80,'
                 'highshelf=f=7000:g=0.5,deesser=i=0.5:m=0.5:f=0.5,'
                 'acompressor=threshold=-28dB:ratio=4:attack=5:release=100:makeup=4:knee=4,alimiter=limit=0.9'),
}


def deep_filter():
    tools = Path(os.environ.get('AD_EDIT_TOOLS', Path.home() / '.local/ad-edit-tools'))
    exe = tools / 'deep-filter'
    if exe.is_file() and os.access(exe, os.X_OK):
        return str(exe)
    return shutil.which('deep-filter')


def load(path):
    raw = subprocess.run(['ffmpeg', '-v', 'error', '-i', str(path), '-f', 'f32le', '-ac', '1', '-ar', str(SR), '-'],
                         capture_output=True, check=True).stdout
    return np.frombuffer(raw, np.float32)


def save(path, x, codec='pcm_s16le'):
    subprocess.run(['ffmpeg', '-v', 'error', '-y', '-f', 'f32le', '-ar', str(SR), '-ac', '1', '-i', '-', '-c:a', codec,
                    str(path)], input=np.asarray(x, np.float32).tobytes(), check=True)


def dereverb(x, taps, delay):
    try:
        from nara_wpe.wpe import wpe
        from nara_wpe.utils import stft, istft
    except ImportError:
        print('note: nara_wpe not installed, skipping dereverb (pip3 install nara_wpe). Room echo stays in.')
        return x
    x = x.astype(np.float64)
    size, shift = 1536, 384
    Y = stft(x[None], size=size, shift=shift).transpose(2, 0, 1)          # (F, D, T)
    Z = wpe(Y, taps=taps, delay=delay, iterations=3, statistics_mode='full').transpose(1, 2, 0)
    return istft(Z, size=size, shift=shift)[0][:len(x)].astype(np.float32)


def denoise(wpe_wav, out_dir, atten=None):
    """DeepFilterNet into out_dir/wpe.wav; atten limits the reduction in dB (e.g. 14 keeps soft words)."""
    out_dir.mkdir(parents=True, exist_ok=True)
    df = deep_filter()
    if df:
        cmd = [df, '-D', '--pf'] if atten is None else [df, '-D', '-a', str(atten)]
        subprocess.run(cmd + ['-o', str(out_dir), str(wpe_wav)], check=True, capture_output=True)
        return 'DeepFilterNet'
    nr = 20 if atten is None else min(12, atten)
    subprocess.run(['ffmpeg', '-v', 'error', '-y', '-i', str(wpe_wav), '-af', f'afftdn=nr={nr}:nf=-45:tn=1',
                    str(out_dir / 'wpe.wav')], check=True)
    return 'ffmpeg afftdn (install DeepFilterNet for a much cleaner result)'


def main():
    args = sys.argv[1:]
    if '--list' in args:
        for k, v in EQ.items():
            print(f'{k:11s} {v[:110]}...')
        return
    if len(args) < 2 or args[0].startswith('-'):
        raise SystemExit(__doc__)
    arg = lambda k, d: type(d)(args[args.index(k) + 1]) if k in args else d
    src, out = Path(args[0]), Path(args[1])
    out.mkdir(parents=True, exist_ok=True)
    name = arg('--eq', 'warm')
    if name not in EQ:
        raise SystemExit(f'unknown preset {name}; presets: {", ".join(EQ)}')
    x = load(src)
    z = dereverb(x, arg('--taps', 18), arg('--delay', 3))
    w = out / 'wpe.wav'
    save(w, z)
    how = denoise(w, out / 'df')
    final = out / f'voice_{name}.wav'
    subprocess.run(['ffmpeg', '-v', 'error', '-y', '-i', str(out / 'df' / 'wpe.wav'), '-af', EQ[name], '-c:a', 'pcm_s24le',
                    str(final)], check=True)
    print(f'{final}  (denoise: {how})')


if __name__ == '__main__':
    main()
