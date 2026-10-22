"""Frame view of a stretch of voice, 20 ms per row: level, pitch, spectral change. Fillers ('eh') show as a long,
voiced, steady stretch (pitch flat, low spectral change) between words.
  python3 frames.py voice.wav 30.3 34.6
Columns: time, level (dB), f0 (pitch in Hz, 0 = unvoiced or quiet), flux (how fast the sound changes), level bar."""
import subprocess, sys, numpy as np
if len(sys.argv) < 4: raise SystemExit(__doc__)
SR = 16000
x = np.frombuffer(subprocess.run(['ffmpeg','-v','error','-i',sys.argv[1],'-f','f32le','-ac','1','-ar',str(SR),'-'],capture_output=True,check=True).stdout, np.float32)
a, b = float(sys.argv[2]), float(sys.argv[3]); hop, win = 320, 640
prev = None
for i in range(int(a*SR), int(b*SR), hop):
    f = x[i:i+win] * np.hanning(win)
    lv = 10*np.log10(np.mean(f**2) + 1e-12)
    ac = np.correlate(f, f, 'full')[win-1:]; lo, hi = SR//400, SR//80
    k = lo + np.argmax(ac[lo:hi]); voiced = ac[k] / (ac[0] + 1e-9)
    f0 = SR / k if voiced > .45 and lv > -50 else 0
    S = np.log(np.abs(np.fft.rfft(f, 1024))[:256] + 1e-6)
    flux = 0 if prev is None else float(np.mean(np.abs(S - prev))); prev = S
    bar = '#' * max(0, int((lv + 60) / 2))
    print(f'{i/SR:6.2f} {lv:6.1f} f0 {f0:5.0f} flux {flux:4.2f} {bar}')
