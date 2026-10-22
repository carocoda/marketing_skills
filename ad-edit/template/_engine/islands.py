"""Speech islands from the cleaned voice: runs above a threshold (dB), split by gaps of at least MIN_GAP seconds.
Use them as the windows for words.py.
  python3 islands.py voice.wav [-50] [0.07]"""
import subprocess, sys, numpy as np
if len(sys.argv) < 2: raise SystemExit(__doc__)
SRC, TH, MIN_GAP = sys.argv[1], float(sys.argv[2]) if len(sys.argv)>2 else -50, float(sys.argv[3]) if len(sys.argv)>3 else 0.07
pcm = subprocess.run(['ffmpeg','-v','error','-i',SRC,'-f','f32le','-ac','1','-ar','48000','-'],capture_output=True).stdout
x = np.frombuffer(pcm, np.float32); hop = 480
db = 20*np.log10(np.sqrt(np.convolve(x**2, np.ones(hop)/hop, 'same')[::hop] + 1e-12))
on = db > TH; isl = []; i = 0
while i < len(on):
    if on[i]:
        j = i
        while j < len(on) and on[j]: j += 1
        isl.append([i/100, j/100]); i = j
    else: i += 1
merged = []
for a, b in isl:
    if merged and a - merged[-1][1] < MIN_GAP: merged[-1][1] = b
    else: merged.append([a, b])
for a, b in merged:
    if b - a >= 0.03:
        print(f'{a:6.2f} - {b:6.2f}  ({b-a:4.2f})')
