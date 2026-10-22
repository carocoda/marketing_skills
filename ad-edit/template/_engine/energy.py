"""Energy probe around candidate cut points: prints a 10 ms RMS curve (dBFS) over 0.5 s and the quietest spot.
Use it to end a segment where a word has really died away (word ends ring 0.1 to 0.3 s longer than Whisper says).
  python3 energy.py voice.wav 43.30 51.12 ..."""
import subprocess, sys, numpy as np
if len(sys.argv) < 3: raise SystemExit(__doc__)
SRC = sys.argv[1]
pcm = subprocess.run(['ffmpeg','-v','error','-i',SRC,'-f','f32le','-ac','1','-ar','48000','-'],capture_output=True).stdout
x = np.frombuffer(pcm, np.float32)
hop = 480
rms = np.sqrt(np.convolve(x**2, np.ones(hop)/hop, 'same')[::hop] + 1e-12)
db = 20*np.log10(rms)
for a in sys.argv[2:]:
    t = float(a); i0, i1 = int((t-0.25)*100), int((t+0.25)*100)
    seg = db[i0:i1]; k = int(np.argmin(seg))
    bar = ''.join(' .:-=+*#%@'[min(9,max(0,int((v+70)/6)))] for v in seg)
    print(f'{t:6.2f}  min {seg[k]:6.1f} dB at {(i0+k)/100:6.2f}  |{bar}|')
