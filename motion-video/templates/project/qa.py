"""Automatic checks. Run after every change, before anyone sees a render.

  python3 qa.py                             checks on the page, the voice lines and the mix (about 20 s)
  python3 qa.py --video ../name-16x9.mp4    the same, plus checks on a finished file (finish.py runs these)

Page
  fonts      the BRAND fonts really loaded (Google Fonts need internet: offline = fallback fonts, the wrong look)
  grid       T is a whole number of frames, BEATS x beat = T, the music grid and segments fit BEATS
  sounds     every window.SFX event is inside the video and has a sound in build_audio.py
  loop       the last frame flows into the first (pixels) and the cursor is home and at rest at the seam
  facts      every string in project.json "facts" is on screen somewhere (date, place, price, url)
  copy       no em-dash and none of project.json copy.banned on screen or in the voice-over; no spoken price
  price      a price only shows up in the last 40% of the video (copy.price_late; opening on the price put people off)
Voice and mix
  voice      every line has vo/<name>.wav (scratch takes are a warning), no overlaps, all words inside the video
  mix        audio/mix.wav is newer than motion.html, project.json and the takes
Video (--video)
  frames     frame count = T x fps, audio at least as long as the picture
  loudness   integrated loudness on target, true peak under the ceiling
  seam       the file's last frame flows into its first
  colour     matrix, primaries and transfer tagged bt709
"""
import argparse
import io
import json
import re
import subprocess

import numpy as np

from common import HERE, canvas, open_page, project

RES = []
DEFAULT_BANNED = ['game changer', 'game-changer', 'unlock', 'supercharge', 'elevate', 'revolutionize', 'next level']


def report(name, ok, msg, warn=False):
    RES.append((name, 'PASS' if ok else ('WARN' if warn else 'FAIL'), msg))


def print_results():
    w = max(len(r[0]) for r in RES)
    for name, st, msg in RES:
        print(f'{st:4s}  {name:{w}s}  {msg}')
    fails = sum(st == 'FAIL' for _, st, _ in RES)
    print('\nAll checks pass.' if not fails else f'\n{fails} check(s) failed.')
    return fails


def copy_problems(text):
    cp = project().get('copy', {})
    out = []
    if '—' in text:
        out.append('an em-dash (—)')
    low = text.lower()
    out += [f'"{b}"' for b in cp.get('banned', DEFAULT_BANNED) if b.lower() in low]
    out += [f'pattern /{r}/' for r in cp.get('banned_patterns', []) if re.search(r, low)]
    return out


def page_checks():
    from PIL import Image
    from common import playwright
    sync_playwright = playwright()
    pj = project()
    W, H, FPS = canvas()
    with sync_playwright() as pw:
        br, pg = open_page(pw)
        T, beats, beat = pg.evaluate('[window.DURATION, window.BEATS, window.BEAT]')

        fonts = pg.evaluate("(window.FONT_CHECKS || []).filter(f => !document.fonts.check(f))")
        report('fonts', not fonts, 'all BRAND fonts loaded' if not fonts else
               f'not loaded: {fonts} (no internet for Google Fonts? a wrong family name or file path?)')

        frames = T * FPS
        m = pj.get('music', {})
        seg_beats = sum(b - a for a, b in m.get('segments', []))
        grid_msgs, ok = [], True
        if abs(frames - round(frames)) > 1e-6:
            ok = False
            grid_msgs.append(f'T = {T}s is {frames:.3f} frames, not a whole number')
        if abs(beats * beat - T) > 1e-6:
            ok = False
            grid_msgs.append('BEATS x BEAT != T')
        if m.get('period') and abs(m['period'] * beats - T) / T > 0.005:
            ok = False
            grid_msgs.append(f"{beats} music beats last {m['period'] * beats:.3f}s, not {T}s")
        if m.get('segments') and seg_beats != beats:
            ok = False
            grid_msgs.append(f'music segments add up to {seg_beats} beats, not {beats}')
        report('grid', ok, '; '.join(grid_msgs) if grid_msgs else
               f'{beats} beats of {beat:.4f}s = {T}s = {round(frames)} frames ({60 / beat:.2f} BPM)')

        ev = pg.evaluate('window.SFX')
        import build_audio
        try:
            kinds = set(build_audio.sfx_bank()[0]) | {'key'}
        except SystemExit as e:
            report('sounds', False, str(e))
            kinds = None
        outside = [e for e in ev if not (0 <= e['t'] < T)]
        unknown = sorted({e['kind'] for e in ev} - kinds) if kinds is not None else []
        if kinds is not None:
            report('sounds', not outside and not unknown,
                   f'{len(ev)} events, all inside the video and known' if not outside and not unknown else
                   f'{len(outside)} events outside 0..{T}s; unknown kinds: {unknown}')

        def grab(t):
            pg.evaluate(f'window.seek({t!r})')
            return np.asarray(Image.open(io.BytesIO(pg.screenshot())).convert('RGB')).astype(int)
        f0, f_end, f1 = grab(0.0), grab(T - 1 / FPS), grab(1 / FPS)
        seam = float(np.abs(f_end - f0).mean())
        step = float(np.abs(f1 - f0).mean())
        c = pg.evaluate(f'[cursorScreen({T} - 2 / {FPS}), cursorScreen({T} - 1 / {FPS}), cursorScreen(0), cursorScreen(1 / {FPS})]')
        speed = FPS * float(np.hypot(c[2][0] - c[1][0], c[2][1] - c[1][1]))
        report('loop', seam < 1.5 and speed < 30,
               f'last frame -> first frame: mean pixel change {seam:.3f} (want < 1.5; first -> second frame is {step:.3f}), '
               f'cursor moving {speed:.1f} px/s across the seam (want < 30)')

        text = pg.evaluate("document.getElementById('frame').textContent.replace(/\\s+/g, ' ')")
        missing = [f for f in pj.get('facts', []) if f.lower() not in text.lower()]
        report('facts', not missing, f"all {len(pj.get('facts', []))} facts are on screen" if not missing else
               f'not on screen anywhere: {missing}')

        problems = [f'on screen: {p}' for p in copy_problems(text)]
        cp = pj.get('copy', {})
        markers = cp.get('price_markers', ['€', '$', '£'])
        for ln in pj.get('lines', []):
            spoken = ln.get('say', ln['text'])
            problems += [f"line {ln['name']}: {p}" for p in copy_problems(ln['text'])]
            if cp.get('price_late', True) and (any(m in spoken for m in markers) or
                                                re.search(r'\d+\s*(euro|euros|dollars?|pounds?)\b', spoken.lower())):
                problems.append(f"line {ln['name']} says a price (put it on the sticker near the end instead)")
        report('copy', not problems, 'no em-dashes, no banned words, no spoken price' if not problems else '; '.join(problems))

        first = None
        mk = json.dumps(markers)
        for k in range(int(beats) * 2):
            t = k * beat / 2
            pg.evaluate(f'window.seek({t})')
            if markers and pg.evaluate("""[...document.querySelectorAll('#frame *')].some(e => e.children.length === 0 &&
                   %s.some(m => e.textContent.includes(m)) && e.checkVisibility({opacityProperty: true, visibilityProperty: true}))""" % mk):
                first = t
                break
        if first is None:
            report('price', True, 'no price on screen (fine if this video has none)')
        elif not cp.get('price_late', True):
            report('price', True, f'a price shows at {first:.1f}s (copy.price_late is off)')
        else:
            report('price', first >= 0.6 * T, f'the price first shows at {first:.1f}s = beat {first / beat:.1f} '
                   f'({100 * first / T:.0f}% in; want the last 40%)', warn=True)
        br.close()
    return T, beats, beat


def voice_checks(T, beat):
    import build_audio
    pj = project()
    missing = [ln['name'] for ln in pj.get('lines', []) if not (HERE / 'vo' / f"{ln['name']}.wav").exists()]
    if missing:
        report('voice', False, f'no take for {missing}: tts.py <line> then tts.py <line> --use <letter>; or your own '
               'recording in vo/<name>.wav; or remove the line for a music-only video')
        return
    scratch = [ln['name'] for ln in pj.get('lines', []) if (HERE / 'vo' / f"{ln['name']}.scratch").exists()]
    if scratch:
        report('scratch', False, f'scratch voice (placeholder.py) for {scratch}: fine for timing, replace before you ship',
               warn=True)
    n = int(round(T * 48000))
    _, placed = build_audio.voiceover(pj, n, beat)
    probs = build_audio.check_lines(placed, T, beat)
    report('voice', not probs, f"{len(placed)} lines placed, no overlaps, all inside the video" if not probs else '; '.join(probs))
    mix = HERE / 'audio' / 'mix.wav'
    if not mix.exists():
        report('mix', False, 'no audio/mix.wav yet: python3 build_audio.py', warn=True)
        return
    newer = [p.name for p in [HERE / 'motion.html', HERE / 'project.json', *(HERE / 'vo').glob('*.wav')]
             if p.stat().st_mtime > mix.stat().st_mtime]
    report('mix', not newer, 'audio/mix.wav is up to date' if not newer else
           f'changed after the last mix: {newer[:4]}: run python3 build_audio.py', warn=True)


def video_checks(path):
    pj = project()
    _, _, FPS = canvas()
    probe = lambda *a: subprocess.run(['ffprobe', '-v', 'error', *a, str(path)], capture_output=True, text=True).stdout
    from common import playwright
    with playwright()() as pw:
        br, pg = open_page(pw)
        T = pg.evaluate('window.DURATION')
        br.close()
    want = int(round(T * FPS))
    n = int(probe('-select_streams', 'v:0', '-count_packets', '-show_entries', 'stream=nb_read_packets', '-of', 'csv=p=0').strip())
    ad = float(probe('-select_streams', 'a:0', '-show_entries', 'stream=duration', '-of', 'csv=p=0').strip() or 0)
    if n < want:
        report('frames', False, f'partial render: {n} of {want} frames (render.py full --seconds). Loudness and the '
               'seam only mean something on a full render, so they are skipped.', warn=True)
        return
    report('frames', n == want and ad >= want / FPS - 1 / FPS, f'{n} frames (want {want}), audio {ad:.3f}s, picture {want / FPS:.3f}s')
    out = subprocess.run(['ffmpeg', '-hide_banner', '-nostats', '-i', str(path), '-af', 'ebur128=peak=true', '-f', 'null', '-'],
                         capture_output=True, text=True).stderr
    summ = out[out.rindex('Summary:'):]
    I = float(re.search(r'I:\s+(-?[\d.]+) LUFS', summ).group(1))
    pk = float(re.search(r'Peak:\s+(-?[\d.]+) dBFS', summ).group(1))
    mx = pj.get('mix', {})
    tl, tp = mx.get('target_lufs', -14), mx.get('true_peak', -1.2)
    report('loudness', abs(I - tl) <= 0.5 and pk <= tp + 0.3, f'{I:.1f} LUFS (want {tl}), true peak {pk:.1f} dBTP (ceiling {tp})')
    W, H, _ = canvas()
    fr = []
    for sel in ('eq(n\\,0)', f'eq(n\\,{n - 1})'):
        raw = subprocess.run(['ffmpeg', '-loglevel', 'error', '-i', str(path), '-vf', f"select='{sel}'", '-fps_mode', 'passthrough',
                              '-frames:v', '1', '-f', 'rawvideo', '-pix_fmt', 'rgb24', '-'], capture_output=True).stdout
        fr.append(np.frombuffer(raw, np.uint8).astype(int))
    d = float(np.abs(fr[0] - fr[1]).mean()) if len(fr[0]) == len(fr[1]) == W * H * 3 else 999
    report('seam', d < 2.0, f"the file's last frame -> first frame: mean pixel change {d:.3f} (want < 2)")
    tags = probe('-select_streams', 'v:0', '-show_entries', 'stream=color_space,color_transfer,color_primaries',
                 '-of', 'csv=p=0').strip().split(',')
    report('colour', all(t == 'bt709' for t in tags), f'colour tags {tags} (want bt709 everywhere)', warn=True)


if __name__ == '__main__':
    ap = argparse.ArgumentParser()
    ap.add_argument('--video')
    ap.add_argument('--skip-page', action='store_true')
    a = ap.parse_args()
    if not a.skip_page:
        T, beats, beat = page_checks()
        voice_checks(T, beat)
    if a.video:
        video_checks(a.video)
    raise SystemExit(1 if print_results() else 0)
