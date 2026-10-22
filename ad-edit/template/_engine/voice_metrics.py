"""Compare voice files: noise floor, reverb tail after word ends, spectral balance and centroid (references/voice.md).
  python3 voice_metrics.py ref.wav other.wav ... [--win 8:30]
--win limits the measurement to the spoken part (default: all)."""
import subprocess, sys, numpy as np
from pathlib import Path
SR = 48000
args = sys.argv[1:]
if not args: raise SystemExit(__doc__)
win = args.pop(args.index('--win') + 1) if '--win' in args else None
args = [a for a in args if a != '--win']
def load(p):
    return np.frombuffer(subprocess.run(['ffmpeg','-v','error','-i',p,'-f','f32le','-ac','1','-ar',str(SR),'-'],capture_output=True,check=True).stdout, np.float32)
ref = load(args[0])
a, b = map(float, win.split(':')) if win else (0.0, len(ref) / SR)
hop = 480
def lev(x): return 20*np.log10(np.sqrt(np.convolve(x**2, np.ones(hop)/hop, 'same')[::hop]+1e-12))
def tail_db(l):
    """Reverb tail: level 100 ms after a word end, relative to the last 150 ms of that word (median over all ends)."""
    seg = l[int(a*100):int(b*100)]; on = seg > max(np.percentile(seg, 95) - 30, np.percentile(seg, 5) + 15)
    ends = [i for i in range(20, len(on) - 12) if on[i-20:i].all() and not on[i:i+10].any()]
    return np.median([seg[i+10] - np.median(seg[i-15:i-2]) for i in ends]) if ends else float('nan')
for p in args:
    x = load(p); l = lev(x)
    floor = np.percentile(l[int(a*100):int(b*100)], 5)
    seg = x[int(a*SR):int(b*SR)]
    X = np.abs(np.fft.rfft(seg))**2; f = np.fft.rfftfreq(len(seg), 1/SR)
    band = lambda lo, hi: 10*np.log10(X[(f>=lo)&(f<hi)].sum()+1e-9)
    tot = band(80, 16000)
    cen = (f*X)[(f>80)&(f<16000)].sum()/X[(f>80)&(f<16000)].sum()
    print(f"{'/'.join(Path(p).parts[-2:]):32s} floor {floor:6.1f} dB  tail {tail_db(l):6.1f} dB/100ms  centroid {cen:5.0f} Hz  "
          + ' '.join(f"{n}:{band(lo,hi)-tot:5.1f}" for n,lo,hi in [('lo',80,250),('mud',250,600),('mid',600,2000),('pres',2000,5000),('sib',5000,9000),('air',9000,16000)]))
