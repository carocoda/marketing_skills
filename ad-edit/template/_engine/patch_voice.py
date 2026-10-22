"""Re-make a stretch of the clean voice where the denoiser or the expander ate soft speech (a soft first word, a soft
last syllable): milder denoising on the dereverbed take, the same EQ without the expander, matched in level, and
spliced back with 15 ms crossfades. Needs the files voice.py left in <work>/audio (wpe.wav, voice_<preset>.wav).

  python3 patch_voice.py <work/audio> <preset> <out.wav> a:b[:+dB] ...   (times in source seconds)

Then point edit.json files.voice at <out.wav>."""
import subprocess
import sys
from pathlib import Path

import numpy as np

sys.path.insert(0, str(Path(__file__).parent))
from voice import EQ, SR, denoise, load  # noqa: E402

if len(sys.argv) < 5:
    raise SystemExit(__doc__)
aud, preset, out = Path(sys.argv[1]), sys.argv[2], Path(sys.argv[3])
src = aud / f'voice_{preset}.wav'
if not src.exists() or not (aud / 'wpe.wav').exists():
    raise SystemExit(f'{src} or {aud / "wpe.wav"} missing: run voice.py with --eq {preset} first')
mild_dir = aud / 'df_mild'
if not (mild_dir / 'wpe.wav').exists():
    denoise(aud / 'wpe.wav', mild_dir, atten=14)
chain = ','.join(c for c in EQ[preset].split(',') if not c.startswith('agate'))
mild = aud / f'voice_{preset}_mild.wav'
subprocess.run(['ffmpeg', '-v', 'error', '-y', '-i', str(mild_dir / 'wpe.wav'), '-af', chain, '-c:a', 'pcm_s24le', str(mild)],
               check=True)
v, m = load(src).copy(), load(mild)
n = min(len(v), len(m))
v, m = v[:n], m[:n]
x = int(0.015 * SR)
for spec in sys.argv[4:]:
    parts = spec.split(':')
    a, b = float(parts[0]), float(parts[1])
    extra = float(parts[2]) if len(parts) > 2 else 0.0
    i0, i1 = int(a * SR), int(b * SR)
    # level match on the loud quarter of the stretch, then the extra lift
    q = max(1, (i1 - i0) // 4)
    rv = np.sqrt(np.mean(np.sort(v[i0:i1] ** 2)[-q:]) + 1e-12)
    rm = np.sqrt(np.mean(np.sort(m[i0:i1] ** 2)[-q:]) + 1e-12)
    g = (rv / rm) * 10 ** (extra / 20)
    seg = m[i0:i1] * g
    w = np.ones(i1 - i0, np.float32)
    w[:x] = np.linspace(0, 1, x)
    w[-x:] = np.linspace(1, 0, x)
    v[i0:i1] = v[i0:i1] * (1 - w) + seg * w
    print(f'{a:.2f}-{b:.2f}: level match {20 * np.log10(rv / rm):+.1f} dB, extra {extra:+.1f} dB')
subprocess.run(['ffmpeg', '-v', 'error', '-y', '-f', 'f32le', '-ar', str(SR), '-ac', '1', '-i', '-', '-c:a', 'pcm_s24le',
                str(out)], input=np.clip(v, -1, 1).astype(np.float32).tobytes(), check=True)
print(out)
