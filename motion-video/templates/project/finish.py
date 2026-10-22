"""The final file: encode video_noaudio.mkv with audio/mix.wav into an mp4, make thumbnails, optionally a light
720p copy for chat apps, then run the video checks from qa.py.

  python3 finish.py --out ../<name>-16x9.mp4
  python3 finish.py --out ../<name>-16x9.mp4 --thumb 3.9 --thumb 9.8    thumbnails (cursor hidden) at those seconds
  python3 finish.py --out ../<name>-16x9.mp4 --review                   also <name>_720p.mp4

The audio is padded and the file cut to exactly frames / fps, so the loop point stays exact. Never use
-shortest: it drops the last frames. setparams tags the primaries and transfer as bt709 too; with only the
matrix tagged, players guess the colours.
"""
import argparse
import subprocess
from pathlib import Path

import qa
from common import HERE, canvas, need, open_page, playwright

ap = argparse.ArgumentParser()
ap.add_argument('--out', required=True)
ap.add_argument('--thumb', type=float, action='append', default=[])
ap.add_argument('--review', action='store_true')
ap.add_argument('--crf', type=int, default=16)
a = ap.parse_args()

W, H, FPS = canvas()
need('ffmpeg', 'ffprobe')
src, mix = HERE / 'video_noaudio.mkv', HERE / 'audio' / 'mix.wav'
for f, how in [(src, 'python3 render.py full'), (mix, 'python3 build_audio.py')]:
    if not f.exists():
        raise SystemExit(f'{f.name} is missing: run {how} first')
if mix.stat().st_mtime < (HERE / 'motion.html').stat().st_mtime:
    print('NOTE: motion.html changed after the last build_audio.py. If you moved or added sound events, '
          'run build_audio.py again.')
frames = int(subprocess.run(['ffprobe', '-v', 'error', '-select_streams', 'v:0', '-count_packets', '-show_entries',
                             'stream=nb_read_packets', '-of', 'csv=p=0', str(src)], capture_output=True, text=True).stdout.strip())
out = Path(a.out).expanduser()
out = out if out.is_absolute() else (Path.cwd() / out).resolve()
out.parent.mkdir(parents=True, exist_ok=True)

subprocess.run(['ffmpeg', '-loglevel', 'error', '-y', '-i', str(src), '-i', str(mix), '-map', '0:v', '-map', '1:a',
                '-c:v', 'libx264', '-preset', 'slow', '-crf', str(a.crf), '-tune', 'animation',
                '-vf', 'scale=out_color_matrix=bt709:out_range=tv,format=yuv420p,setparams=color_primaries=bt709:color_trc=bt709:colorspace=bt709:range=tv',
                '-colorspace', 'bt709', '-color_primaries', 'bt709', '-color_trc', 'bt709',
                '-af', 'apad', '-c:a', 'aac', '-b:a', '256k', '-ar', '48000', '-t', f'{frames / FPS:.6f}',
                '-movflags', '+faststart', str(out)], check=True)
print(f'{out}  ({out.stat().st_size / 1e6:.1f} MB, {frames} frames)')

stem = out.stem
for tag in ('-16x9', '_16x9', '-9x16', '_9x16', '-1x1', '_1x1', '-4x5', '_4x5'):
    stem = stem.replace(tag, '')
if a.thumb:
    with playwright()() as pw:
        br, pg = open_page(pw)
        for t in a.thumb:
            th = out.with_name(f'{stem}_thumb_{t:g}s.png')
            pg.evaluate(f"window.seek({t}); document.getElementById('cursor').style.visibility = 'hidden'")
            pg.screenshot(path=str(th))
            print(th)
        br.close()

if a.review:
    rv = out.with_name(f'{stem}_720p.mp4')
    subprocess.run(['ffmpeg', '-loglevel', 'error', '-y', '-i', str(out), '-vf', ('scale=1280:-2' if W >= H else 'scale=-2:1280') + ':flags=lanczos,setparams=color_primaries=bt709:color_trc=bt709:colorspace=bt709:range=tv',
                    '-c:v', 'libx264', '-preset', 'slow', '-crf', '23', '-pix_fmt', 'yuv420p', '-c:a', 'aac', '-b:a', '160k',
                    '-movflags', '+faststart', str(rv)], check=True)
    print(f'{rv}  ({rv.stat().st_size / 1e6:.1f} MB)')

qa.video_checks(out)
qa.print_results()
