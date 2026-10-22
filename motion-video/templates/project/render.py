"""Render motion.html with Playwright (headless Chromium). Every frame is seek(t) + a screenshot, so any frame
renders on its own, in any order, in parallel, and comes out the same every time.

  python3 render.py beats [--offset 0.25]   one still per beat (0.25 s after it) + stills/contactsheet.png
  python3 render.py at 12.3 20.1            full-size stills at those seconds -> stills/at_*.png
  python3 render.py sheet 12 12.1 12.2 ...  a labelled contact sheet of those seconds -> stills/sheet.png
  python3 render.py strip 23.8 24.6 [--n 12]  frames between two times: check a morph halfway -> stills/strip.png
  python3 render.py preview                 30 fps, no motion blur, long side 1280 px, with audio/mix.wav -> preview.mp4
  python3 render.py full [--workers 6]      the real thing -> video_noaudio.mkv (lossless, for finish.py)
  python3 render.py full --only 5           re-render chunk 5 only (after a change late in the video) and re-join
  python3 render.py full --seconds 3        only the first 3 seconds (a quick test of the whole pipeline)

The full render takes 4 subframes per output frame, centred on the frame time and spread over one frame
(shutter 1.0), pipes them as PNG into ffmpeg, which averages them (tmix) into one frame: real motion blur on
every spring. Chunks are lossless ffv1; finish.py does the one and only lossy encode.
"""
import json
import math
import subprocess
import sys
import time
from multiprocessing import Process

from common import HERE, canvas, need, open_page, playwright, project

W, H, FPS = canvas()
C = project().get('canvas', {})
SUB, SHUTTER = C.get('subframes', 4), C.get('shutter', 1.0)
STILLS = HERE / 'stills'


def arg(name, default=None, cast=str):
    return cast(sys.argv[sys.argv.index(name) + 1]) if name in sys.argv else default


def page_numbers(pg):
    return pg.evaluate('({T: window.DURATION, beats: window.BEATS, beat: window.BEAT})')


def shoot(pg, t, kind='png', q=None):
    pg.evaluate(f'window.seek({t!r})')
    if kind == 'jpeg':
        return pg.screenshot(type='jpeg', quality=q or 90, animations='disabled', caret='initial')
    return pg.screenshot(type='png', animations='disabled', caret='initial')


def stills(times, tag):
    sync_playwright = playwright()
    STILLS.mkdir(exist_ok=True)
    for old in STILLS.glob(f'{tag}_*.png'):          # stills from an earlier run of the same kind
        old.unlink()
    paths = []
    with sync_playwright() as pw:
        br, pg = open_page(pw)
        info = page_numbers(pg)
        for i, t in enumerate(times):
            p = STILLS / f'{tag}_{i:03d}_{t:07.3f}.png'
            p.write_bytes(shoot(pg, t))
            paths.append(p)
        br.close()
    return paths, info


def contact(paths, labels, out, cols=6, tw=480):
    from PIL import Image, ImageDraw, ImageFont
    th = tw * H // W
    rows = math.ceil(len(paths) / cols)
    sheet = Image.new('RGB', (cols * tw, rows * (th + 28)), (255, 255, 255))
    d = ImageDraw.Draw(sheet)
    font = None
    for f in ('/System/Library/Fonts/Supplemental/Arial Bold.ttf', '/Library/Fonts/Arial Bold.ttf',
              '/usr/share/fonts/truetype/dejavu/DejaVuSans-Bold.ttf'):
        try:
            font = ImageFont.truetype(f, 17)
            break
        except Exception:
            pass
    for i, (p, lab) in enumerate(zip(paths, labels)):
        x, y = (i % cols) * tw, (i // cols) * (th + 28)
        sheet.paste(Image.open(p).convert('RGB').resize((tw, th), Image.LANCZOS), (x, y + 28))
        d.text((x + 6, y + 5), lab, fill=(0, 0, 0), font=font)
    sheet.save(out)
    return out


# ---------------------------------------------------------------- video
def preview_size():
    k = 1280 / max(W, H)
    return int(round(W * k / 2) * 2), int(round(H * k / 2) * 2)


def worker(idx, f0, f1, fps, sub, shutter, out, preview):
    sync_playwright = playwright()
    if preview:
        pw_, ph_ = preview_size()
        cmd = ['ffmpeg', '-y', '-loglevel', 'error', '-f', 'image2pipe', '-framerate', str(fps), '-c:v', 'mjpeg',
               '-i', '-', '-vf', f'scale={pw_}:{ph_}:flags=lanczos,scale=out_color_matrix=bt709:out_range=tv,format=yuv420p,'
               'setparams=color_primaries=bt709:color_trc=bt709:colorspace=bt709:range=tv',
               '-c:v', 'libx264', '-preset', 'veryfast', '-crf', '23', str(out)]
    else:
        vf = f"tmix=frames={sub},select='eq(mod(n\\,{sub})\\,{sub - 1})',setpts=N/({fps}*TB)" if sub > 1 else 'null'
        cmd = ['ffmpeg', '-y', '-loglevel', 'error', '-f', 'image2pipe', '-framerate', str(fps * sub), '-c:v', 'png',
               '-i', '-', '-vf', vf, '-r', str(fps), '-c:v', 'ffv1', '-level', '3', '-pix_fmt', 'rgb24', str(out)]
    ff = subprocess.Popen(cmd, stdin=subprocess.PIPE)
    with sync_playwright() as pw:
        br, pg = open_page(pw)
        T = pg.evaluate('window.DURATION')
        t0 = time.time()
        for f in range(f0, f1):
            tc = f / fps
            if preview:
                ff.stdin.write(shoot(pg, tc % T, 'jpeg', 88))
            else:
                for j in range(sub):
                    ts = tc + ((j + 0.5) / sub - 0.5) * shutter / fps      # subframes centred on the frame time
                    ff.stdin.write(shoot(pg, ts % T))
            if idx == 0 and (f - f0) % 120 == 0 and f > f0:
                done = f - f0
                print(f'  worker 0: {done}/{f1 - f0} frames, {(time.time() - t0) / done:.2f} s per frame', flush=True)
        br.close()
    ff.stdin.close()
    ff.wait()
    if ff.returncode:
        raise SystemExit(f'ffmpeg failed in worker {idx}')


def render_video(preview=False):
    need('ffmpeg')
    sync_playwright = playwright()
    with sync_playwright() as pw:
        br, pg = open_page(pw)
        T = pg.evaluate('window.DURATION')
        br.close()
    fps = 30 if preview else FPS
    total = int(round(T * fps))
    if abs(total - T * fps) > 1e-6:
        raise SystemExit(f'T = {T}s is not a whole number of frames at {fps} fps: fix T in motion.html')
    if '--seconds' in sys.argv:                     # a quick test: only the first N seconds
        total = min(total, int(round(arg('--seconds', 3, float) * fps)))
    folder = HERE / ('chunks_preview' if preview else 'chunks')
    folder.mkdir(exist_ok=True)
    plan_f = folder / 'plan.json'
    only = [int(x) for x in arg('--only', '').split(',') if x] if '--only' in sys.argv else None
    if only is not None and plan_f.exists():
        n = json.load(open(plan_f))['workers']
    else:
        n = arg('--workers', 6, int)
    ext = 'mp4' if preview else 'mkv'
    chunk = math.ceil(total / n)
    jobs = [(i, i * chunk, min(total, (i + 1) * chunk)) for i in range(n) if i * chunk < total]
    json.dump({'workers': n, 'frames': total, 'fps': fps, 'T': T}, open(plan_f, 'w'))
    t0 = time.time()
    procs = []
    for i, f0, f1 in jobs:
        if only is not None and i not in only:
            continue
        pr = Process(target=worker, args=(i, f0, f1, fps, 1 if preview else SUB, SHUTTER,
                                          folder / f'chunk_{i:02d}.{ext}', preview))
        pr.start()
        procs.append(pr)
    print(f'{total} frames at {fps} fps, {"no blur" if preview else f"{SUB} subframes"}, '
          f'{len(procs)} of {len(jobs)} chunks in parallel', flush=True)
    for pr in procs:
        pr.join()
    if any(pr.exitcode for pr in procs):
        raise SystemExit('a render worker failed (see above)')
    missing = [i for i, _, _ in jobs if not (folder / f'chunk_{i:02d}.{ext}').exists()]
    if missing:
        raise SystemExit(f'chunks {missing} are missing: run without --only')
    (folder / 'list.txt').write_text(''.join(f"file 'chunk_{i:02d}.{ext}'\n" for i, _, _ in jobs))
    out = HERE / ('preview_noaudio.mp4' if preview else 'video_noaudio.mkv')
    subprocess.run(['ffmpeg', '-y', '-loglevel', 'error', '-f', 'concat', '-safe', '0', '-i', str(folder / 'list.txt'),
                    '-c', 'copy', str(out)], check=True)
    print(f'rendered in {time.time() - t0:.0f} s -> {out.name}')
    if preview:
        mix, final = HERE / 'audio' / 'mix.wav', HERE / 'preview.mp4'
        if mix.exists():
            subprocess.run(['ffmpeg', '-y', '-loglevel', 'error', '-i', str(out), '-i', str(mix), '-map', '0:v',
                            '-map', '1:a', '-c:v', 'copy', '-af', 'apad', '-c:a', 'aac', '-b:a', '160k',
                            '-t', f'{total / fps:.6f}', '-movflags', '+faststart', str(final)], check=True)
            out.unlink()
            print(f'with sound -> {final.name}')
        else:
            out.replace(final)
            print('(no audio/mix.wav yet, so the preview is silent: run build_audio.py)')


if __name__ == '__main__':
    cmd = sys.argv[1] if len(sys.argv) > 1 else ''
    if cmd == 'beats':
        with playwright()() as pw:
            br, pg = open_page(pw)
            info = page_numbers(pg)
            br.close()
        off = arg('--offset', 0.25, float)
        times = [k * info['beat'] + off for k in range(int(info['beats']))]
        paths, _ = stills(times, 'beat')
        out = contact(paths, [f"b{k}  {t:.2f}s" for k, t in enumerate(times)], STILLS / 'contactsheet.png',
                      cols=8, tw=320)
        print(f'{len(paths)} stills -> {out}')
    elif cmd == 'at':
        paths, _ = stills([float(x) for x in sys.argv[2:]], 'at')
        print('\n'.join(str(p) for p in paths))
    elif cmd == 'sheet':
        ts = [float(x) for x in sys.argv[2:]]
        paths, info = stills(ts, 'sh')
        print(contact(paths, [f"{t:.2f}s  b{t / info['beat']:.2f}" for t in ts], STILLS / 'sheet.png', cols=4, tw=480))
    elif cmd == 'strip':
        a, b, n = float(sys.argv[2]), float(sys.argv[3]), arg('--n', 12, int)
        ts = [a + (b - a) * i / (n - 1) for i in range(n)]
        paths, info = stills(ts, 'strip')
        print(contact(paths, [f"{t:.3f}s  b{t / info['beat']:.2f}" for t in ts], STILLS / 'strip.png', cols=4, tw=480))
    elif cmd == 'preview':
        render_video(preview=True)
    elif cmd == 'full':
        render_video(preview=False)
    else:
        print(__doc__)
