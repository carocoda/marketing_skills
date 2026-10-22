"""Talking-head ad edit: one source take -> several cut variants x formats, with a clean voice, music bed, UI sounds,
punch-in zooms, captions and branded graphics. One engine (this folder, <ads>/_engine/) serves every ad of a project;
everything specific to one ad lives in its own folder (edit.json, notes.md, assets/). Brand colours, fonts, logo,
CTA and URL come from <ads>/brand.json and the "brand" section of edit.json. Run from <ads>/, with the ad folder as
the first argument:

  python3 _engine/build.py <ad> prep                       source -> SDR ProRes, face track, 48 kHz audio (once per take)
  python3 _engine/build.py <ad> plan <variant> <fmt>       print the timeline (pieces, shots, captions, events, warnings)
  python3 _engine/build.py <ad> audit <variant>            every audio cut must sit in quiet (< -45 dB), pauses long enough
  python3 _engine/build.py <ad> audio <variant>            voice cut + sfx + music -> mix/mix_<variant>.wav (-14 LUFS)
  python3 _engine/build.py <ad> verify <variant>           Whisper over the final mix, next to the caption text
  python3 _engine/build.py <ad> base <variant> <fmt>       graded, zoomed picture -> base_<variant>_<fmt>.mov
  python3 _engine/build.py <ad> stills <variant> <fmt> 3.2 12.5 ...   base + overlay at those seconds -> contact sheet
  python3 _engine/build.py <ad> overlay <variant> <fmt>    transparent graphics frames (Playwright)
  python3 _engine/build.py <ad> final <variant> <fmt>      base + overlay + mix -> the mp4 in "out"
  python3 _engine/build.py <ad> all [variant ...] [--formats 9x16,4x5]

Media lives in edit.json "work" and "out" (relative paths are relative to the ad folder); the ad folder holds the recipe.
Environment: AD_EDIT_TOOLS (folder with deep-filter and the macOS helpers, default ~/.local/ad-edit-tools),
AD_EDIT_WORKERS (overlay render processes, default 6).
"""
import difflib
import json
import math
import os
import shutil
import subprocess
import sys
from multiprocessing import Process
from pathlib import Path

try:
    import numpy as np
    from PIL import Image
except ImportError as _e:
    raise SystemExit(f'Missing Python package: {_e.name}. Run: pip3 install numpy pillow')

HERE = Path(__file__).resolve().parent
ARGS = sys.argv[1:] if __name__ == '__main__' else []
if __name__ == '__main__':
    if not ARGS or not (Path(ARGS[0]) / 'edit.json').is_file():
        raise SystemExit(__doc__ + '\nFirst argument: an ad folder with an edit.json, for example 01-intro.')
    AD = Path(ARGS.pop(0)).resolve()
    os.environ['AD_EDIT_AD'] = str(AD)               # the overlay workers re-import this file
else:
    AD = Path(os.environ.get('AD_EDIT_AD', HERE))
CFG = json.loads((AD / 'edit.json').read_text(encoding='utf-8'))


def ad_path(p):
    """A path from edit.json: absolute stays absolute, relative is relative to the ad folder."""
    p = Path(os.path.expanduser(str(p)))
    return p if p.is_absolute() else AD / p


WORK, OUT, FPS = ad_path(CFG.get('work', 'work')), ad_path(CFG.get('out', 'exports')), CFG.get('fps', 30)
SR = 48000
TOOLS = Path(os.environ.get('AD_EDIT_TOOLS', Path.home() / '.local/ad-edit-tools'))
LANG = CFG.get('language') or None                  # None: Whisper detects the language
WHISPER_MODEL = CFG.get('whisper_model', 'large-v3')
FILES = {'picture': 'sdr_prores.mov', 'faces': 'faces.json', 'audio': 'audio/src48.wav',
         'voice': 'audio/voice_warm.wav', 'words_whisper': 'words_whisper.json',
         'words_crisper': 'words_crisper.json', 'music': 'music/bed.mp3', **CFG.get('files', {})}
F_ = {k: WORK / v for k, v in FILES.items()}                  # an absolute path in edit.json stays absolute
CRISPER = [[WORK / f, off, keep] for f, off, keep in CFG.get('crisper', [[FILES['words_crisper'], 0, 0]])]
PICTURE, VOICE = F_['picture'], F_['voice']
MUSIC = F_['music'] if CFG.get('music') else None
PREFILTER = CFG.get('prefilter', '')       # e.g. denoise, applied before the zoom so noise isn't magnified
GRADE = CFG.get('grade', 'eq=contrast=1.06:saturation=1.05:gamma=0.98,unsharp=5:5:0.45:5:5:0,vignette=angle=PI/5.5')

# ---------------------------------------------------------------- brand

BRAND_DEFAULT = {
    'name': '',                     # text in the corner tag and on the end card; '' and no logo: no tag
    'logo': '',                     # image file (png/svg) used instead of the name
    'url': '',                      # small line under the end card button
    'cta': 'LEARN MORE →',          # end card button
    'locale': 'en-US',              # number format (like counter on the 'post' graphic)
    'colors': {'bg': '#F4F1EA', 'ink': '#111111', 'paper': '#FFFFFF', 'accent': '#FFD84D',
               'accent2': '#9BE3C3', 'accent3': '#FF9E8A', 'accent4': '#C9D3FF',
               'caption': '#FFFFFF', 'caption_active': '', 'shadow': ''},
    'fonts': {'display': {'family': 'Archivo', 'weight': 800, 'google': True},
              'label': {'family': 'JetBrains Mono', 'weight': 700, 'google': True}},
    'style': {'border': 4, 'shadow': 8, 'radius': 18},   # border 0 and shadow 0 give a flat look
}


def merge(a, b):
    out = dict(a)
    for k, v in (b or {}).items():
        out[k] = merge(out[k], v) if isinstance(v, dict) and isinstance(out.get(k), dict) else v
    return out


def load_brand():
    """Defaults < brand.json next to the ad folders (or in the ad folder) < "brand" in edit.json."""
    b = BRAND_DEFAULT
    for f in (AD.parent / 'brand.json', AD / 'brand.json'):
        if f.is_file():
            b = merge(b, {k: v for k, v in json.loads(f.read_text(encoding='utf-8')).items() if not k.startswith('_')})
    return merge(b, CFG.get('brand', {}))


BRAND = load_brand()


def asset(rel):
    """A file named in edit.json or brand.json: in the ad folder, its parent (the ads folder), the engine, or as given."""
    p = Path(os.path.expanduser(str(rel)))
    if p.is_absolute():
        return p
    return next((b / p for b in (AD, AD.parent, HERE) if (b / p).exists()), Path.cwd() / p)


SFX_DIR = asset(CFG.get('assets', {}).get('sfx', HERE / 'assets' / 'sfx'))


def need_work():
    """Stop when the drive that holds 'work' is not connected, instead of writing big files somewhere else."""
    parts = WORK.parts
    if len(parts) > 2 and parts[1] in ('Volumes', 'media', 'mnt'):
        root = Path(*parts[:3]) if parts[1] != 'media' else Path(*parts[:4])
        if not root.exists():
            raise SystemExit(f'{root} is not connected. Connect the drive that holds "work" ({WORK}); '
                             'do not create the folder by hand.')
    WORK.mkdir(parents=True, exist_ok=True)


def run(cmd, **kw):
    r = subprocess.run([str(c) for c in cmd], capture_output=True, text=True, **kw)
    if r.returncode:
        raise SystemExit(f'failed: {" ".join(map(str, cmd))[:300]}\n{r.stderr[-1500:]}')
    return r


def pcm(path, ch=1):
    raw = subprocess.run(['ffmpeg', '-v', 'error', '-i', str(path), '-f', 'f32le', '-ac', str(ch), '-ar', str(SR), '-'],
                         capture_output=True, check=True).stdout
    x = np.frombuffer(raw, np.float32).copy()
    return x.reshape(-1, ch) if ch > 1 else x


def db(x):
    return 10 ** (x / 20)


def probe_json(path, entries, stream='v:0'):
    r = run(['ffprobe', '-v', 'error', '-select_streams', stream, '-show_entries', entries, '-of', 'json', path])
    return json.loads(r.stdout)


def source_info():
    j = probe_json(PICTURE, 'stream=width,height:format=duration')
    return j['streams'][0]['width'], j['streams'][0]['height'], float(j['format']['duration']) - 0.05   # last frames can be short


# ---------------------------------------------------------------- prep

def tool(name):
    exe = TOOLS / name
    return exe if exe.is_file() and os.access(exe, os.X_OK) else None


def has_filter(name):
    r = subprocess.run(['ffmpeg', '-hide_banner', '-filters'], capture_output=True, text=True)
    return f' {name} ' in r.stdout


def to_sdr(src, dst):
    """Phone HDR (HLG / PQ) -> SDR Rec.709 ProRes 422 HQ with rotation baked in. On macOS the hdr_to_sdr helper uses
    Apple's own tone mapping (best match for iPhone footage); elsewhere ffmpeg zscale + tonemap; SDR is just converted."""
    if tool('hdr_to_sdr'):
        print(run([tool('hdr_to_sdr'), src, dst]).stdout.strip())
        return
    trc = probe_json(src, 'stream=color_transfer')['streams'][0].get('color_transfer', '')
    hdr = trc in ('arib-std-b67', 'smpte2084')
    vf = 'format=yuv422p10le'
    if hdr and has_filter('zscale'):
        vf = ('zscale=t=linear:npl=100,format=gbrpf32le,zscale=p=bt709,tonemap=tonemap=hable:desat=0,'
              'zscale=t=bt709:m=bt709:r=tv,format=yuv422p10le')
    elif hdr:
        print('WARNING: the source is HDR, but this ffmpeg has no zscale filter and the macOS hdr_to_sdr helper is not '
              'built. Colours will look flat. Fix: an ffmpeg build with zscale (libzimg), or on a Mac: check_env.py --build')
    run(['ffmpeg', '-v', 'error', '-y', '-i', src, '-an', '-vf', vf, '-c:v', 'prores_ks', '-profile:v', '3',
         '-color_primaries', 'bt709', '-color_trc', 'bt709', '-colorspace', 'bt709', dst])
    print(f'{dst} (ffmpeg, {"HDR tone mapped" if hdr else "SDR"})')


def track_faces(picture, out, step=0.2):
    """Face centre every `step` seconds: the macOS Vision helper, else OpenCV, else a fixed spot (edit.json
    "face_fallback": [x, y] as part of width and height, default [0.5, 0.33])."""
    if tool('face_track'):
        print(run([tool('face_track'), picture, out, str(step)]).stdout.strip())
        return
    w, h, dur = source_info()
    rows = []
    try:
        import cv2
        casc = cv2.CascadeClassifier(cv2.data.haarcascades + 'haarcascade_frontalface_default.xml')
        sw = 480
        sh = round(h * sw / w)
        raw = subprocess.run(['ffmpeg', '-v', 'error', '-i', str(picture), '-vf', f'fps={1 / step},scale={sw}:{sh},format=gray',
                              '-f', 'rawvideo', '-'], capture_output=True, check=True).stdout
        frames = np.frombuffer(raw, np.uint8).reshape(-1, sh, sw)
        k = w / sw
        for i, fr in enumerate(frames):
            faces = casc.detectMultiScale(fr, 1.1, 5, minSize=(sw // 12, sw // 12))
            if len(faces):
                x, y, fw, fh = max(faces, key=lambda f: f[2])
                rows.append({'t': round(i * step, 3), 'cx': (x + fw / 2) * k, 'cy': (y + fh / 2) * k, 'w': fw * k, 'h': fh * k})
        print(f'faces {len(rows)} (OpenCV)')
    except ImportError:
        pass
    if not rows:
        fx, fy = CFG.get('face_fallback', [0.5, 0.33])
        rows = [{'t': 0.0, 'cx': fx * w, 'cy': fy * h, 'w': 0.3 * w, 'h': 0.3 * w}]
        print(f'WARNING: no face track (no macOS helper, no OpenCV, or no face found). Using a fixed face position '
              f'{fx:.2f}, {fy:.2f} of the frame. Better: pip3 install opencv-python, or on a Mac: check_env.py --build')
    Path(out).write_text(json.dumps(rows, indent=1))


def prep():
    """Once per take: SDR Rec.709 ProRes, face positions every 0.2 s, mono 48 kHz audio.
    Then: voice.py, words.py and (optional) crisper.py (see SKILL.md)."""
    need_work()
    src = ad_path(CFG['source'])
    if not src.is_file():
        raise SystemExit(f'source not found: {src}')
    for d in (PICTURE, F_['faces'], F_['audio']):
        d.parent.mkdir(parents=True, exist_ok=True)
    if not PICTURE.exists():
        to_sdr(src, PICTURE)
    if not F_['faces'].exists():
        track_faces(PICTURE, F_['faces'])
    if not F_['audio'].exists():
        run(['ffmpeg', '-v', 'error', '-y', '-i', src, '-vn', '-ac', '1', '-ar', str(SR), '-c:a', 'pcm_s24le', F_['audio']])
    w, h, dur = source_info()
    print(f'{PICTURE}  {w}x{h}, {dur:.2f} s\n{F_["faces"]}\n{F_["audio"]}')


# ---------------------------------------------------------------- words and timeline

def silent_gaps(th=-55, min_gap=0.08):
    x = pcm(VOICE)
    hop = SR // 100
    lv = 20 * np.log10(np.sqrt(np.convolve(x ** 2, np.ones(hop) / hop, 'same')[::hop] + 1e-12))
    quiet, gaps, i = lv < th, [], 0
    while i < len(quiet):
        if quiet[i]:
            j = i
            while j < len(quiet) and quiet[j]:
                j += 1
            if (j - i) / 100 >= min_gap:
                gaps.append((i / 100, j / 100))
            i = j
        else:
            i += 1
    return gaps


def words():
    cache = WORK / 'words_final.json'
    inputs = [AD / 'edit.json', Path(__file__), F_['words_whisper'], *(c[0] for c in CRISPER)]
    if cache.exists() and cache.stat().st_mtime > max(p.stat().st_mtime for p in inputs if p.exists()):
        return json.loads(cache.read_text(encoding='utf-8'))
    if not F_['words_whisper'].exists():
        raise SystemExit(f'{F_["words_whisper"]} is missing: run words.py first (references/cutting.md)')
    fix = {f[0]: f[1] for f in CFG.get('words_fix', []) if len(f) == 2}
    tfix = [f for f in CFG.get('words_fix', []) if len(f) == 3]          # [heard, meant, near this time]
    drop = CFG.get('words_drop', [])
    out = []
    for win in json.loads(F_['words_whisper'].read_text(encoding='utf-8')):
        a = win['win'][0]
        for w in win['words']:
            if any(w['w'] == d and abs(w['s'] - t) < 0.3 for d, t in drop):
                continue
            txt = next((n for o, n, t in tfix if o == w['w'] and abs(w['s'] - t) < 0.3), fix.get(w['w'], w['w']))
            out.append({'w': txt, 's': max(w['s'], a), 'e': w['e'], 'a': a})
    out += [{'w': w, 's': t, 'e': t + 0.1, 'src': 'manual'} for w, t in CFG.get('words_add', [])]
    out.sort(key=lambda w: w['s'])
    # Text from Whisper large-v3, times from CrisperWhisper (much closer to the real onsets, poorer text):
    # match the two word sequences and take Crisper's start for every matched word.
    # CrisperWhisper runs: [file, seconds to add, keep words from]. A token with a filler mark glued on (".Then[UH]")
    # keeps it, so it stays unmatched: its times are unreliable.
    crisp = [dict(w, s=w['s'] + off, e=w['e'] + off) for f, off, keep in CRISPER if f.exists()
             for w in json.loads(f.read_text(encoding='utf-8')) if w['s'] + off >= keep]
    if crisp:
        crisp = sorted((w for w in crisp if norm(w['w']) not in ('', 'uh', 'um')), key=lambda w: w['s'])
        sm = difflib.SequenceMatcher(None, [norm(w['w']) for w in out], [norm(w['w']) for w in crisp], autojunk=False)
        for blk in sm.get_matching_blocks():
            for k in range(blk.size):
                w, c = out[blk.a + k], crisp[blk.b + k]
                if abs(c['s'] - w['s']) < 0.8 and w.get('src') != 'manual':
                    w['s0'], w['s'], w['src'] = w['s'], c['s'], 'crisp'
        # Unmatched words between two matched ones: spread them the way Whisper spaced them.
        idx = [i for i, w in enumerate(out) if w.get('src')]
        for l, r in zip(idx, idx[1:]):
            L, R = out[l], out[r]
            for w in out[l + 1:r]:
                f = (w['s'] - L.get('s0', L['s'])) / max(1e-3, R.get('s0', R['s']) - L.get('s0', L['s']))
                w['s'], w['src'] = L['s'] + min(max(f, 0.05), 0.95) * (R['s'] - L['s']), 'interp'
    for w in out:                                   # a first word 'starts' in the padding: clamp to its window
        w['s'] = max(w['s'], w.get('a', 0))
    # Unmatched words: the start may have swallowed the pause before it, move it to the end of that pause.
    gaps = silent_gaps()
    for w in out:
        if not w.get('src'):
            for ga, gb in gaps:
                if ga <= w['s'] < gb and gb < w['e']:
                    w['s'] = gb
    for word, near, t in CFG.get('words_at', []):
        min((w for w in out if w['w'] == word), key=lambda w: abs(w['s'] - near))['s'] = t
    out.sort(key=lambda w: w['s'])
    for p, w in zip(out, out[1:]):
        w['s'] = max(w['s'], p['s'] + 0.05)
    cache.write_text(json.dumps(out, ensure_ascii=False, indent=0), encoding='utf-8')
    return out


def norm(s):
    return ''.join(c for c in s.lower() if c.isalnum())


def find_word(ws, word, near):
    cands = [w for w in ws if norm(w['w']) == norm(word)]
    if not cands:
        raise SystemExit(f'word not found: {word} (near {near}); check words_fix or the word list in "plan"')
    return min(cands, key=lambda w: abs(w['s'] - near))['s']


def variant_def(variant):
    if variant not in CFG.get('variants', {}):
        raise SystemExit(f'unknown variant {variant}; edit.json has: {", ".join(CFG.get("variants", {})) or "no variants yet"}')
    return CFG['variants'][variant]


def uri(rel):
    return asset(rel).resolve().as_uri() if rel else ''


def plan(variant, fmt):
    if fmt not in CFG['formats']:
        raise SystemExit(f'unknown format {fmt}; edit.json has: {", ".join(CFG["formats"])}')
    F = CFG['formats'][fmt]
    V = variant_def(variant)
    flags = V.get('flags', [])
    seg = {s['id']: s for s in CFG['segments']}
    pieces, t = [], 0.0
    for sid in V['segments']:
        s = seg[sid]
        pieces.append({'id': sid, 'a': s['a'], 'b': s['b'], 'out': round(t, 4)})
        t += s['b'] - s['a']
    last = pieces[-1]
    E = CFG.get('endcard')
    if E:
        ec = last['out'] + E['at'] - last['a']
        T = round(round((ec + E.get('dur', 2.6)) * FPS) / FPS, 4)
    else:
        ec, T = None, round(round(t * FPS) / FPS, 4)

    def m(src):
        for p in pieces:
            if p['a'] - 1e-6 <= src <= p['b'] + 1e-6:
                return round(p['out'] + src - p['a'], 4)
        return None

    def piece_end(src):
        for p in pieces:
            if p['a'] - 1e-6 <= src <= p['b'] + 1e-6:
                return p['out'] + p['b'] - p['a']
        return None

    # shots: cut points inside the kept pieces, alternating zoom so every jump cut reads as a punch
    faces = json.loads(F_['faces'].read_text())
    defs = CFG.get('shots') or [[0, 1]]
    shots = []
    for p in pieces:
        active = ([d for d in defs if d[0] <= p['a'] + 1e-6] or [defs[0]])[-1]
        cuts = [[p['a']] + list(active[1:])] + [d for d in defs if p['a'] + 1e-6 < d[0] < p['b']]
        for i, c in enumerate(cuts):
            a = c[0]
            b = cuts[i + 1][0] if i + 1 < len(cuts) else p['b']
            if p is last and i + 1 == len(cuts):
                b = p['a'] + (T - p['out'])
            shots.append({'a': a, 'b': b, 'out': p['out'] + a - p['a'], 'z': c[1],
                          'intro': len(c) > 2 and c[2] == 'intro'})
    for prev, s in zip(shots, shots[1:]):
        if s['z'] == prev['z']:
            s['z'] = 1 if prev['z'] != 1 else 2
    for s in shots:
        fs = [f for f in faces if s['a'] <= f['t'] <= min(s['b'], s['a'] + 6)] or faces
        s['cx'] = float(np.median([f['cx'] for f in fs]))
        s['cy'] = float(np.median([f['cy'] for f in fs]))
        s['zoom'] = F['zoom'][str(s['z'])]
        s['fy'] = F['face_y'][str(s['z'])]
        s['f0'] = round(s['out'] * FPS)
    for s, n in zip(shots, shots[1:] + [None]):
        s['f1'] = n['f0'] if n else round(T * FPS)

    # captions: chunks of max 3 words / 17 characters, broken at punctuation, pauses and cuts
    C = {'words': 3, 'chars': 17, 'uppercase': True, **CFG.get('captions', {})}

    def m_word(src):                                  # a word may start a hair before its piece
        return m(src) if m(src) is not None else next((p['out'] for p in pieces if p['a'] - 0.35 <= src < p['a']), None)

    ws = [dict(w, t=m_word(w['s'])) for w in words()]
    ws = [w for w in ws if w['t'] is not None]
    cuts_out = {round(s['out'], 3) for s in shots}
    chunks, cur = [], []
    for w in ws:
        if cur:
            prev = cur[-1]
            text = ' '.join(x['w'] for x in cur + [w])
            brk = (prev['w'][-1:] in ',.?!' or len(cur) >= C['words'] or len(text) > C['chars']
                   or w['t'] - prev['t'] > 0.9 or any(prev['t'] < c <= w['t'] + 0.02 for c in cuts_out))
            if brk:
                chunks.append(cur)
                cur = []
        cur.append(w)
    if cur:
        chunks.append(cur)
    caps = []
    for i, c in enumerate(chunks):
        end = chunks[i + 1][0]['t'] if i + 1 < len(chunks) else c[-1]['t'] + 0.6
        end = min(end, c[-1]['t'] + 1.2)
        caps.append({'t0': c[0]['t'] - 0.08, 't1': end, 'words': [{'w': x['w'], 't': x['t']} for x in c]})

    # events; one whose time falls outside the kept pieces would vanish silently, so it is reported
    evs, warn = [], []
    extra = [{'type': 'endcard', 'at': E['at'], 'sfx': E.get('sfx', ['whoosh'])}] if E else []
    for e in CFG.get('events', []) + extra:
        e = dict(e)
        if e.get('flag') and e['flag'] not in flags:
            continue
        src = find_word(words(), e['word'], e['near']) if 'word' in e else e.get('from', e.get('at'))
        t0 = m_word(src)
        if t0 is None:
            warn.append(f"event {e['type']} {e.get('word', '')} @ {src:.2f} falls outside the kept pieces: not shown")
            continue
        e['t0'] = t0
        if 'to' in e:
            e['t1'] = m(e['to']) if m(e['to']) is not None else piece_end(src)
        if 'to_word' in e:
            e['t1'] = m(find_word(words(), e['to_word'], e['to_near']))
            if e['t1'] is None:
                warn.append(f"event {e['type']}: end word {e['to_word']} falls outside the kept pieces")
                e['t1'] = piece_end(src)
        if 'rows' in e:                              # checklist: [text, word, near] -> [text, output time]
            e['rows'] = [[txt, m_word(find_word(words(), w, n))] for txt, w, n in e['rows']]
        for k in ('tap', 'tag', 'ding', 'check', 'stamp'):
            if f'{k}_word' in e:
                e[f'{k}_t'] = m(find_word(words(), e[f'{k}_word'], e[f'{k}_near']))
                if e[f'{k}_t'] is None:
                    warn.append(f"event {e['type']}: {k}_word {e[f'{k}_word']} falls outside the kept pieces")
        if 'image' in e:                             # sticker: an image from the ad folder
            e['image'] = uri(e['image'])
        if e['type'] == 'endcard':
            e['t1'] = T
        evs.append(e)
    photos = [[asset(f).resolve().as_uri(), *Image.open(asset(f)).size] for f in CFG.get('photos', [])]
    end = dict(E or {})
    if end.get('image'):
        end['image'] = uri(end['image'])
    brand = dict(BRAND, logo=uri(BRAND.get('logo')))
    for k in ('display', 'label'):                   # a local font file -> file:// URI for the page
        f = brand['fonts'].get(k, {})
        if f.get('file'):
            brand['fonts'] = dict(brand['fonts'], **{k: dict(f, file=uri(f['file']))})
    return {'variant': variant, 'fmt': fmt, 'w': F['w'], 'h': F['h'], 'T': T, 'fps': FPS, 'endcard': ec,
            'flags': flags, 'end': end, 'pieces': pieces, 'shots': shots, 'captions': caps, 'events': evs,
            'warnings': warn, 'photos': photos, 'brand': brand, 'cap_style': {'uppercase': C['uppercase']},
            'logos': [uri(f) for f in CFG.get('logos', [])]}


# ---------------------------------------------------------------- audio

SFX = {  # name -> [(file, gain dB, offset s[, max length s])]; files in assets/sfx (make_sfx.py, or your own)
    'pop': [('pop', -13, 0)], 'click': [('click', -10, 0)], 'key': [('key-press', -14, 0.03)],
    'whoosh': [('whoosh-short', -15, -0.16)], 'soft_whoosh': [('whoosh-short', -25, -0.14)],
    'impact': [('impact-bass-1', -16, 0, 0.9)], 'slam': [('impact-bass-1', -23, 0, 0.5), ('click', -12, 0)],
    'stamp': [('pop', -10, 0), ('click', -12, 0)], 'chime': [('chime', -17, 0.02)], 'tick': [('click', -15, 0)],
    'ding': [('chime', -15, 0)],
}


def sfx_file(name):
    for ext in ('.wav', '.mp3', '.m4a', '.ogg', '.flac'):
        if (SFX_DIR / f'{name}{ext}').is_file():
            return SFX_DIR / f'{name}{ext}'
    raise SystemExit(f'sound "{name}" missing in {SFX_DIR}. Make the default set: python3 {HERE / "make_sfx.py"} '
                     f'"{SFX_DIR}" (or drop your own {name}.wav there)')


def sfx_cues(p):
    cues = []
    for e in p['events']:
        for n in e.get('sfx', []):
            cues.append((e['t0'], n))
        for k in ('tap', 'tag', 'check', 'stamp'):
            for n in e.get(f'{k}_sfx', []):
                if e.get(f'{k}_t') is not None:
                    cues.append((e[f'{k}_t'], n))
        if e.get('ding_t') is not None:
            cues.append((e['ding_t'], 'ding'))
        if e['type'] == 'checklist':
            cues += [(t, 'tick') for _, t in e['rows'] if t is not None]
        if e['type'] == 'logos':
            cues += [(e['t0'] + 0.14 * i, 'pop') for i in range(1, len(p['logos']))]
        if e['type'] == 'photos':
            cues += [(e['t0'] + 0.28 * i, 'pop') for i in range(len(p['photos']))]
        if e['type'] == 'files':
            cues += [(e['t0'] + 0.1 * i, 'pop') for i in (1, 2)]
        if e['type'] == 'apps':
            cues += [(e['t0'] + 0.08 * i, 'key') for i in range(1, 6)]
        if e['type'] == 'aicard':
            cues += [(e['t0'] + 0.45 + 0.2 * i, 'tick') for i in range(3)]
        if e['type'] == 'win' and e.get('role') == 'copy':
            cues.append((e['t0'] + 0.32, 'click'))
        if e['type'] == 'endcard':
            cues += [(e['t0'] + 0.45 + 0.09 * i, 'pop') for i in range(4)] + [(e['t0'] + 1.0, 'chime')]
    for prev, s in zip(p['shots'], p['shots'][1:]):
        if s['z'] > prev['z'] and not any(abs(t - s['out']) < 0.25 for t, _ in cues):
            cues.append((s['out'], 'soft_whoosh'))
    return sorted(cues)


def music_bed(T, ec):
    """With a beat grid (<song>.beats.json from beats.py) and end_beat/hit_beat in edit.json "music": the song from
    early on, spliced into its own ending so the final hit lands just after the end card starts. Without them:
    the song from "start" seconds, looped if too short, faded out at the end."""
    M = CFG['music']
    if not MUSIC.exists():
        raise SystemExit(f'{MUSIC} is missing: put a track you have the rights to there, or remove "music" from '
                         'edit.json (references/music-and-sound.md)')
    song = pcm(MUSIC, 2)
    n = int(T * SR)
    bj = MUSIC.with_suffix('.beats.json')
    synced = bj.exists() and 'end_beat' in M and 'hit_beat' in M and ec is not None
    if not synced:
        if 'end_beat' in M and not bj.exists():
            print(f'note: {bj.name} missing, so the bed is not synced to the end card. Measure it: '
                  f'python3 {HERE / "beats.py"} "{MUSIC}"')
        s0 = int(M.get('start', 0) * SR)
        body = song[s0:] if len(song) > s0 else song
        reps = int(math.ceil(n / max(1, len(body))))
        out = np.concatenate([body] * reps)[:n].copy()
    else:
        info = json.loads(bj.read_text())
        P, b0 = info['period'], info['first_beat']
        ph, end, hit = M.get('phrase', 16), M['end_beat'], M['hit_beat']
        bt = lambda k: b0 + k * P
        start = end % ph                                  # same place in the phrase as the ending: the seam is invisible
        hit_out = ec + M.get('hit_after_endcard', 1.4)
        seam_out = hit_out - (hit - end) * P
        k = math.ceil(seam_out / (ph * P))
        s0 = bt(start + ph * k) - seam_out                # song time at output 0
        while s0 < bt(start):
            s0 += ph * P
        out = np.zeros((n, 2), np.float32)
        ns = int(seam_out * SR)
        a = song[int(s0 * SR): int(s0 * SR) + ns + int(P * SR)]
        bseg = song[int(bt(end) * SR):]
        xf = int(P * SR)
        out[:min(ns, n, len(a))] = a[:min(ns, n, len(a))]
        fade = np.sqrt(np.linspace(0, 1, xf))[:, None]
        tail_a = a[ns:ns + xf]
        m = max(0, min(len(bseg), n - ns))
        out[ns:ns + m] += bseg[:m] * np.r_[fade, np.ones((max(0, m - xf), 1))][:m]
        kk = max(0, min(xf, len(tail_a), n - ns))
        out[ns:ns + kk] += tail_a[:kk] * np.sqrt(1 - np.linspace(0, 1, xf))[:kk, None]
    fi = int(0.03 * SR)
    out[:fi] *= np.linspace(0, 1, fi)[:, None]
    fo = min(int((0.5 if synced else 1.5) * SR), n)
    out[-fo:] *= np.linspace(1, 0, fo)[:, None] ** 2
    return out


def loudnorm(inp, outp, target=-14.0, tp=-1.0):
    r = subprocess.run(['ffmpeg', '-hide_banner', '-i', str(inp), '-af',
                        f'loudnorm=I={target}:TP={tp}:LRA=11:print_format=json', '-f', 'null', '-'],
                       capture_output=True, text=True)
    st = json.loads(r.stderr[r.stderr.rindex('{'):r.stderr.rindex('}') + 1])
    if st['input_i'] in ('-inf', 'inf'):                # silence: nothing to normalise
        shutil.copy(inp, outp)
        return
    run(['ffmpeg', '-v', 'error', '-y', '-i', str(inp), '-af',
         f"loudnorm=I={target}:TP={tp}:LRA=11:measured_I={st['input_i']}:measured_TP={st['input_tp']}:"
         f"measured_LRA={st['input_lra']}:measured_thresh={st['input_thresh']}:offset={st['target_offset']}:linear=true",
         '-ar', str(SR), '-c:a', 'pcm_s24le', str(outp)])


def build_audio(variant):
    need_work()
    p = plan(variant, next(iter(CFG['formats'])))
    T, n = p['T'], int(p['T'] * SR)
    d = WORK / 'mix'
    d.mkdir(exist_ok=True)
    # voice: pieces back to back, 8 ms fades at every cut
    v = pcm(VOICE)
    voice = np.zeros(n, np.float32)
    f = int(0.008 * SR)
    for pc in p['pieces']:
        seg = v[int(pc['a'] * SR):int(pc['b'] * SR)].copy()
        for ga, gb, gdb in CFG.get('voice_gain', []):      # lift a soft word that the music would mask
            i0, i1 = int((max(ga, pc['a']) - pc['a']) * SR), int((min(gb, pc['b']) - pc['a']) * SR)
            if i1 > i0:
                r = min(int(0.03 * SR), (i1 - i0) // 2)
                g = np.full(i1 - i0, db(gdb), np.float32)
                g[:r] = np.linspace(1, db(gdb), r)
                g[-r:] = np.linspace(db(gdb), 1, r)
                seg[i0:i1] *= g
        seg[:f] *= np.linspace(0, 1, f)
        seg[-f:] *= np.linspace(1, 0, f)
        i = int(pc['out'] * SR)
        voice[i:i + len(seg)] += seg[:n - i]
    tmp = d / f'voice_{variant}.wav'
    write_wav(tmp, voice)
    loudnorm(tmp, d / f'voice_{variant}_n.wav', -16.0, -2.0)
    voice = pcm(d / f'voice_{variant}_n.wav')[:n]
    voice = np.pad(voice, (0, n - len(voice)))
    # music: -16 LUFS stem, ducked under speech, up in the gaps and on the end card
    mus = np.zeros((n, 2), np.float32)
    if MUSIC:
        X = {'duck_speech': -14.5, 'duck_gap': -9.0, 'endcard': -6.0, **CFG.get('mix', {})}
        write_wav(d / 'music_tmp.wav', music_bed(T, p['endcard']))
        loudnorm(d / 'music_tmp.wav', d / 'music_tmp_n.wav', -16.0, -2.0)
        mus = pcm(d / 'music_tmp_n.wav', 2)[:n]
        mus = np.pad(mus, ((0, n - len(mus)), (0, 0)))
        hop = SR // 100
        lv = 20 * np.log10(np.sqrt(np.convolve(voice ** 2, np.ones(hop) / hop, 'same')[::hop] + 1e-12))
        talk = lv > -45
        k = 35                                                 # 350 ms hangover
        talk = np.convolve(talk.astype(float), np.ones(2 * k + 1), 'same') > 0
        gain_db = np.where(talk, X['duck_speech'], X['duck_gap'])
        if p['endcard'] is not None:
            gain_db[int(p['endcard'] * 100):] = X['endcard']
        sm = 20
        gain_db = np.convolve(np.pad(gain_db, sm, mode='edge'), np.ones(2 * sm + 1) / (2 * sm + 1), 'same')[sm:-sm]
        g = db(np.interp(np.arange(n) / SR, np.arange(len(gain_db)) / 100, gain_db)).astype(np.float32)
        mus *= g[:, None]
    # sfx
    sfx = np.zeros(n, np.float32)
    bank = {}
    cues = sfx_cues(p)
    for t, name in cues:
        if name not in SFX:
            raise SystemExit(f'unknown sound "{name}"; known: {", ".join(SFX)}')
        for fname, gdb, off, *ln in SFX[name]:
            if fname not in bank:
                bank[fname] = pcm(sfx_file(fname))
            s = bank[fname] * db(gdb)
            if ln:                                     # shorten long hits with a fade
                k = int(ln[0] * SR)
                s = s[:k] * np.linspace(1, 0, min(k, len(s))) ** 1.5
            i = int((t + off) * SR)
            if 0 <= i < n:
                sfx[i:i + len(s)] += s[:n - i]
    mix = mus + (voice + sfx)[:, None]
    write_wav(d / f'mix_{variant}_raw.wav', mix)
    loudnorm(d / f'mix_{variant}_raw.wav', d / f'mix_{variant}.wav', -14.0, -1.0)
    print(f'{d / f"mix_{variant}.wav"}  T={T:.2f}s, {len(cues)} sound cues')


def write_wav(path, x):
    x = np.asarray(x, np.float32)
    ch = 1 if x.ndim == 1 else x.shape[1]
    subprocess.run(['ffmpeg', '-v', 'error', '-y', '-f', 'f32le', '-ar', str(SR), '-ac', str(ch), '-i', '-',
                    '-c:a', 'pcm_s24le', str(path)], input=x.tobytes(), check=True)


# ---------------------------------------------------------------- picture

def zoom_expr(s, dur):
    t = f'(in/{FPS})'
    push = f'(1+0.035*{t}/{dur:.4f})'
    if s['intro']:
        e = f'(1-pow(1-min(1,{t}/0.45),3))'
        return f"({s['zoom']}*{push}*(1+0.22*(1-{e})))"
    return f"({s['zoom']}*{push})"


def shot_file(s, fmt, src):
    F = CFG['formats'][fmt]
    W, H = F['w'], F['h']
    SW, SH, sdur = src
    frames = s['f1'] - s['f0']
    dur = frames / FPS
    key = f"{fmt}_{s['a']:.3f}_{frames}_{s['z']}_{int(s['intro'])}"
    path = WORK / 'shots' / f'{key}.mov'
    if path.exists():
        return path
    path.parent.mkdir(exist_ok=True)
    # work in source pixels on a canvas with the format's shape: full width, height cut around the face
    CW, CH = SW, round(SW * H / W)
    pre = ''
    cx, cy = s['cx'], s['cy']
    if CH < SH:                                     # 4:5 from 9:16: take a fixed window around the face first
        yc = int(min(max(cy - 0.40 * CH, 0), SH - CH))
        pre = f'crop={CW}:{CH}:0:{yc},'
        cy -= yc
    elif CH > SH:                                   # a wider source than the format: cut the sides around the face
        CW, CH = round(SH * W / H), SH
        xc = int(min(max(cx - CW / 2, 0), SW - CW))
        pre = f'crop={CW}:{CH}:{xc}:0,'
        cx -= xc
    Z = zoom_expr(s, dur)
    w, h = f'({CW}/{Z})', f'({CH}/{Z})'
    x0 = f"max(0,min({CW}-{w},{cx:.1f}-{w}/2))"
    y0 = f"max(0,min({CH}-{h},{cy:.1f}-{s['fy']}*{h}))"
    persp = (f"perspective=x0='{x0}':y0='{y0}':x1='{x0}+{w}':y1='{y0}':x2='{x0}':y2='{y0}+{h}':"
             f"x3='{x0}+{w}':y3='{y0}+{h}':interpolation=cubic:eval=frame")
    scale = f',scale={W}:{H}:flags=lanczos' if (CW, CH) != (W, H) else ''
    avail = max(1, int((sdur - s['a']) * FPS))
    tpad = f',tpad=stop_mode=clone:stop={frames}' if frames > avail else ''
    pf = PREFILTER + ',' if PREFILTER else ''
    run(['ffmpeg', '-v', 'error', '-y', '-ss', f"{s['a']:.4f}", '-i', str(PICTURE), '-an',
         '-vf', f'{pre}{pf}{persp}{scale},{GRADE},fps={FPS}{tpad}', '-frames:v', str(frames),
         '-c:v', 'prores_ks', '-profile:v', '3', '-pix_fmt', 'yuv422p10le', str(path)])
    return path


def build_base(variant, fmt):
    need_work()
    p = plan(variant, fmt)
    src = source_info()
    files = [shot_file(s, fmt, src) for s in p['shots']]
    lst = WORK / f'shots_{variant}_{fmt}.txt'
    lst.write_text(''.join(f"file '{f}'\n" for f in files))
    out = WORK / f'base_{variant}_{fmt}.mov'
    run(['ffmpeg', '-v', 'error', '-y', '-f', 'concat', '-safe', '0', '-i', str(lst), '-c', 'copy', str(out)])
    print(out)
    return out


# ---------------------------------------------------------------- overlay (Playwright)

def open_page(pw, p):
    br = pw.chromium.launch()
    pg = br.new_page(viewport={'width': p['w'], 'height': p['h']}, device_scale_factor=1)
    pg.goto((HERE / 'overlay.html').as_uri())
    pg.evaluate('p => window.load(p)', p)
    pg.wait_for_function('window.READY === true', timeout=30000)
    if not pg.evaluate('window.FONTS_OK'):
        f = p['brand']['fonts']
        print(f"WARNING: fonts {f['display']['family']} / {f['label']['family']} did not load (no internet, a typo, "
              'or a local font file missing). Text renders in a fallback font.')
    return br, pg


def save_rgba(path, png):
    """Chrome saves a fully opaque frame (the end card) as RGB. A switch from RGBA to RGB inside the sequence makes
    ffmpeg rebuild the overlay graph and drop frames there, so every frame is stored as RGBA."""
    if png[25] == 6:                                   # PNG colour type 6 = RGBA
        path.write_bytes(png)
    else:
        import io
        Image.open(io.BytesIO(png)).convert('RGBA').save(path)


def ovl_worker(p, f0, f1, d):
    from playwright.sync_api import sync_playwright
    with sync_playwright() as pw:
        br, pg = open_page(pw, p)
        for f in range(f0, f1):
            pg.evaluate(f'window.seek({f / FPS})')
            save_rgba(d / f'{f:05d}.png', pg.screenshot(omit_background=True, animations='disabled'))
        br.close()


def need_playwright():
    try:
        import playwright  # noqa: F401
    except ImportError:
        raise SystemExit('Playwright is missing: pip3 install playwright && python3 -m playwright install chromium')


def build_overlay(variant, fmt, workers=None):
    need_work()
    need_playwright()
    workers = workers or int(os.environ.get('AD_EDIT_WORKERS', 6))
    p = plan(variant, fmt)
    d = WORK / f'ovl_{variant}_{fmt}'
    shutil.rmtree(d, ignore_errors=True)
    d.mkdir()
    N = round(p['T'] * FPS)
    step = math.ceil(N / workers)
    ps = [Process(target=ovl_worker, args=(p, i, min(N, i + step), d)) for i in range(0, N, step)]
    [x.start() for x in ps]
    [x.join() for x in ps]
    if any(x.exitcode for x in ps):
        raise SystemExit('overlay render failed')
    print(d, N, 'frames')


def build_final(variant, fmt):
    need_work()
    p = plan(variant, fmt)
    base, ovl, mix = WORK / f'base_{variant}_{fmt}.mov', WORK / f'ovl_{variant}_{fmt}', WORK / 'mix' / f'mix_{variant}.wav'
    for f, step in ((base, 'base'), (ovl, 'overlay'), (mix, 'audio')):
        if not f.exists():
            raise SystemExit(f'{f} is missing: run "{step}" first')
    OUT.mkdir(parents=True, exist_ok=True)
    out = OUT / f'{CFG.get("name", AD.name)}_{variant}_{fmt}_{CFG.get("version", "v1")}.mp4'
    run(['ffmpeg', '-v', 'error', '-y', '-i', str(base), '-framerate', str(FPS), '-i', str(ovl / '%05d.png'),
         '-i', str(mix), '-filter_complex', '[0:v][1:v]overlay=format=auto:shortest=1,format=yuv420p[v]',
         '-map', '[v]', '-map', '2:a', '-c:v', 'libx264', '-preset', 'slow', '-crf', '17', '-profile:v', 'high',
         '-color_primaries', 'bt709', '-color_trc', 'bt709', '-colorspace', 'bt709', '-r', str(FPS),
         '-c:a', 'aac', '-b:a', '192k', '-ar', '48000', '-t', f"{p['T']:.3f}", '-movflags', '+faststart', str(out)])
    print(out)
    return out


def stills(variant, fmt, times):
    need_playwright()
    from playwright.sync_api import sync_playwright
    p = plan(variant, fmt)
    base = WORK / f'base_{variant}_{fmt}.mov'
    d = WORK / 'stills'
    d.mkdir(parents=True, exist_ok=True)
    tiles = []
    late = [t for t in times if t >= p['T']]
    if late:
        print(f"skipped {', '.join(map(str, late))}: the video is {p['T']:.2f} s long")
    times = [t for t in times if t < p['T']]
    if not times:
        raise SystemExit('no times inside the video')
    with sync_playwright() as pw:
        br, pg = open_page(pw, p)
        for t in times:
            f = d / f'b_{t:07.3f}.png'
            f.unlink(missing_ok=True)
            if base.exists():                         # the very last frame time can fall just past the base: step back
                run(['ffmpeg', '-v', 'error', '-y', '-ss', f'{min(t, p["T"] - 2 / FPS):.3f}', '-i', str(base),
                     '-frames:v', '1', str(f)])
            if f.exists():
                im = Image.open(f).convert('RGBA')
            else:
                im = Image.new('RGBA', (p['w'], p['h']), (90, 90, 90, 255))
            pg.evaluate(f'window.seek({t})')
            o = d / f'o_{t:07.3f}.png'
            o.write_bytes(pg.screenshot(omit_background=True, animations='disabled'))
            im.alpha_composite(Image.open(o).convert('RGBA'))
            tiles.append(im.convert('RGB'))
        br.close()
    tw = 360
    th = int(tiles[0].height * tw / tiles[0].width)
    cols = min(len(tiles), 6)
    rows = math.ceil(len(tiles) / cols)
    sheet = Image.new('RGB', (cols * tw, rows * th), 'white')
    for i, im in enumerate(tiles):
        sheet.paste(im.resize((tw, th)), ((i % cols) * tw, (i // cols) * th))
    out = d / f'sheet_{variant}_{fmt}.jpg'
    sheet.save(out, quality=88)
    print(out)


# ---------------------------------------------------------------- checks

def audit(variant, th=-45.0, min_pause=0.18):
    """Every audio cut must sit in quiet: a cut inside voiced sound is the hiccup people hear. Also reports the pause
    at each join (trailing quiet of one piece + leading quiet of the next): under ~0.18 s a word sounds clipped."""
    x = pcm(VOICE)
    hop = SR // 100
    lv = 10 * np.log10(np.convolve(x ** 2, np.ones(2 * hop) / (2 * hop), 'same')[::hop] + 1e-12)
    p = plan(variant, next(iter(CFG['formats'])))
    at = lambda t: float(lv[min(max(int(t * 100), 0), len(lv) - 1)])
    bad = 0
    for pc in p['pieces']:
        for side, t in (('in', pc['a']), ('out', pc['b'])):
            v = at(t)
            flag = 'OK ' if v < th else 'CUT IN VOICE'
            bad += v >= th
            print(f"{pc['id']:11s} {side:3s} {t:6.2f}  {v:6.1f} dB  {flag}")
    short = 0
    for a, b in zip(p['pieces'], p['pieces'][1:]):
        tail = next((k / 100 for k in range(0, int((a['b'] - a['a']) * 100)) if at(a['b'] - k / 100) >= th), 0)
        head = next((k / 100 for k in range(0, int((b['b'] - b['a']) * 100)) if at(b['a'] + k / 100) >= th), 0)
        gap = tail + head
        warn = gap < min_pause
        short += warn
        print(f"pause {a['id']} -> {b['id']}: {gap:.2f} s" + ('  SHORT PAUSE (aim for 0.3-0.45 s between sentences, '
                                                                '0.15-0.25 s inside one)' if warn else ''))
    print('all cuts in quiet' if not bad else f'{bad} cut(s) inside voice', f'| {short} short pause(s)' if short else '')
    return bad


def verify(variant):
    """Whisper over the final mix, in the pieces as they play: a lost word or a left-over 'uh' shows here."""
    try:
        from faster_whisper import WhisperModel
    except ImportError:
        raise SystemExit('faster-whisper is missing: pip3 install faster-whisper')
    p = plan(variant, next(iter(CFG['formats'])))
    x16 = np.frombuffer(subprocess.run(['ffmpeg', '-v', 'error', '-i', str(WORK / 'mix' / f'mix_{variant}.wav'),
                                        '-f', 'f32le', '-ac', '1', '-ar', '16000', '-'],
                                       capture_output=True, check=True).stdout, np.float32)
    model = WhisperModel(WHISPER_MODEL, device='cpu', compute_type='int8')
    prompt = CFG.get('whisper_prompt') or None
    for pc in p['pieces']:
        a, b = pc['out'], pc['out'] + pc['b'] - pc['a']
        clip = np.concatenate([np.zeros(4000, np.float32), x16[int(a * 16000):int(b * 16000)], np.zeros(4000, np.float32)])
        segs, _ = model.transcribe(clip, language=LANG, beam_size=5, condition_on_previous_text=False,
                                   vad_filter=False, initial_prompt=prompt)
        heard = ''.join(s.text for s in segs).strip()
        meant = ' '.join(w['w'] for c in p['captions'] for w in c['words'] if a - 0.1 <= w['t'] < b - 0.05)
        print(f"{pc['id']:11s} {a:6.2f}-{b:6.2f}\n   heard  : {heard}\n   caption: {meant}", flush=True)


if __name__ == '__main__':
    a = ARGS
    if not a:
        raise SystemExit(__doc__)
    cmd = a[0]
    if cmd == 'prep':
        prep()
    elif cmd == 'plan':
        p = plan(a[1], a[2])
        print(f"T={p['T']}  endcard at {p['endcard'] if p['endcard'] is None else round(p['endcard'], 2)}  flags {p['flags']}")
        for s in p['shots']:
            print(f"shot out {s['out']:6.2f}  src {s['a']:6.2f}-{s['b']:6.2f}  z{s['z']} {s['zoom']}  face {s['cx']:.0f},{s['cy']:.0f}")
        for c in p['captions']:
            print(f"cap {c['t0']:6.2f}-{c['t1']:6.2f}  " + ' '.join(w['w'] for w in c['words']))
        for e in p['events']:
            print(f"ev  {e['t0']:6.2f}-{e.get('t1', 0) or 0:6.2f}  {e['type']}")
        for w in p['warnings']:
            print('WARNING:', w)
    elif cmd == 'audio':
        build_audio(a[1])
    elif cmd == 'base':
        build_base(a[1], a[2])
    elif cmd == 'overlay':
        build_overlay(a[1], a[2])
    elif cmd == 'final':
        build_final(a[1], a[2])
    elif cmd == 'audit':
        audit(a[1])
    elif cmd == 'verify':
        verify(a[1])
    elif cmd == 'stills':
        stills(a[1], a[2], [float(x) for x in a[3:]])
    elif cmd == 'all':
        fmts = a[a.index('--formats') + 1].split(',') if '--formats' in a else list(CFG['formats'])
        vs = [x for x in a[1:] if x in CFG['variants']] or list(CFG['variants'])
        for v in vs:
            if audit(v):
                raise SystemExit(f'{v}: a cut sits inside voice. Fix it first, or render step by step '
                                 '(audio, base, overlay, final) if you accept it (references/cutting.md)')
            build_audio(v)
            for fm in fmts:
                build_base(v, fm)
                build_overlay(v, fm)
                build_final(v, fm)
    else:
        raise SystemExit(__doc__)
