"""Filler candidates: voiced runs of at least MIN s with a flat pitch (an 'eh' or 'uhm' holds one note),
inside the given ranges. Words also have vowels, so every hit still needs a probe/splice check.
  python3 filler_scan.py voice.wav 4.0:8.0 13.1:15.8 ...
Misses fillers at the very start of a sentence that run straight into the word; check the first 0.6 s of every
segment in frames.py too (references/cutting.md)."""
import subprocess, sys, numpy as np
if len(sys.argv) < 3: raise SystemExit(__doc__)
SR, hop, win, MIN = 16000, 160, 640, 0.22
x = np.frombuffer(subprocess.run(['ffmpeg','-v','error','-i',sys.argv[1],'-f','f32le','-ac','1','-ar',str(SR),'-'],capture_output=True,check=True).stdout, np.float32)
def f0_at(i):
    f = x[i:i+win] * np.hanning(win)
    if 10*np.log10(np.mean(f**2)+1e-12) < -45: return 0
    ac = np.correlate(f, f, 'full')[win-1:]; lo, hi = SR//400, SR//80
    k = lo + np.argmax(ac[lo:hi]); return SR/k if ac[k]/(ac[0]+1e-9) > .5 else 0
for spec in sys.argv[2:]:
    a, b = map(float, spec.split(':'))
    f0 = np.array([f0_at(i) for i in range(int(a*SR), int(b*SR), hop)])
    i = 0
    while i < len(f0):
        if f0[i] > 0:
            j = i
            while j < len(f0) and f0[j] > 0: j += 1
            run = f0[i:j]
            if (j-i)*hop/SR >= MIN:
                # flatness over sliding 0.2 s windows
                for k in range(i, j-20, 5):
                    seg = f0[k:k+20]
                    if np.std(seg)/np.mean(seg) < 0.035:
                        print(f'{a+k*hop/SR:6.2f}-{a+(k+20)*hop/SR:6.2f}  flat {np.mean(seg):4.0f} Hz  (voiced run {a+i*hop/SR:.2f}-{a+j*hop/SR:.2f})')
                        break
            i = j
        else: i += 1
