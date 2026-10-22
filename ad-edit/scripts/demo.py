"""Dry run of the whole pipeline on a generated clip, without real footage, models or internet-only services.
Use it to check a new computer, or to see every graphic type once with your brand.

  python3 scripts/demo.py <empty folder> [--brand brand.json] [--formats 9x16,4x5] [--seconds 16] [--whisper small]

It makes a test video (ffmpeg testsrc2 + a gated tone as the 'voice'), a test song, logos, photos and a sticker
(drawn with Pillow), a hand-written word list, and an edit.json that uses every event type. Then it runs
new_ad.py, voice.py, beats.py and build.py plan / audit / audio / base / stills / overlay / final.
--whisper MODEL also runs words.py with that model (it downloads it on first use; a tone has no words, so this only
tests that Whisper runs). Expect 2 to 6 minutes. Nothing leaves your computer except the Google Fonts request.
"""
import json
import subprocess
import sys
from pathlib import Path

import numpy as np
from PIL import Image, ImageDraw

SKILL = Path(__file__).resolve().parents[1]
args = sys.argv[1:]
if not args or args[0].startswith('-'):
    raise SystemExit(__doc__)
opt = lambda k, d=None: args[args.index(k) + 1] if k in args else d
root = Path(args[0]).expanduser().resolve()
if root.exists() and any(root.iterdir()):
    raise SystemExit(f'{root} is not empty; give an empty or new folder.')
fmts = opt('--formats', '9x16,4x5').split(',')
SEC = float(opt('--seconds', 16))
root.mkdir(parents=True, exist_ok=True)
PY = sys.executable


def sh(cmd, cwd=None):
    print('$', ' '.join(str(c) for c in cmd), flush=True)
    r = subprocess.run([str(c) for c in cmd], cwd=cwd, text=True, capture_output=True)
    print(r.stdout[-3000:], r.stderr[-3000:] if r.returncode else '', sep='', flush=True)
    if r.returncode:
        raise SystemExit(f'step failed: {cmd[1] if len(cmd) > 1 else cmd[0]}')
    return r.stdout


# 1. test take: 1080x1920 test pattern, 'speech' = 0.8 s of tone, 0.4 s quiet, repeated (so every cut can sit in quiet)
src = root / 'source' / 'demo-take.mov'
src.parent.mkdir()
sh(['ffmpeg', '-v', 'error', '-y', '-f', 'lavfi', '-i', f'testsrc2=size=1080x1920:rate=30:duration={SEC}',
    '-f', 'lavfi', '-i', f"aevalsrc='0.25*sin(2*PI*(190+25*sin(2*PI*3*t))*t)*lt(mod(t\\,1.2)\\,0.8)':s=48000:d={SEC}",
    '-c:v', 'libx264', '-pix_fmt', 'yuv420p', '-c:a', 'aac', '-shortest', src])

# 2. a new ad from the template
ads = root / 'ads'
sh([PY, SKILL / 'scripts' / 'new_ad.py', ads / '01-demo', '--source', src, '--name', 'demo', '--lang', 'en'])
ad = ads / '01-demo'
if opt('--brand'):
    (ads / 'brand.json').write_text(Path(opt('--brand')).read_text(encoding='utf-8'), encoding='utf-8')
else:
    b = json.loads((ads / 'brand.json').read_text(encoding='utf-8'))
    b.update(name='DEMO BRAND', url='example.com')
    (ads / 'brand.json').write_text(json.dumps(b, indent=1), encoding='utf-8')

# 3. pictures: two logos, four photos, one sticker
A = ad / 'assets'
for i, (c, ch) in enumerate([((255, 120, 90), 'A'), ((90, 140, 255), 'B')]):
    im = Image.new('RGBA', (240, 240), (0, 0, 0, 0))
    d = ImageDraw.Draw(im)
    d.ellipse((10, 10, 230, 230), fill=c)
    try:
        d.text((88, 60), ch, fill='white', font_size=110)
    except TypeError:                                   # Pillow < 10.1
        d.text((110, 110), ch, fill='white')
    im.save(A / f'logo-{i + 1}.png')
for i in range(4):
    w, h = [(800, 600), (600, 800), (700, 700), (900, 600)][i]
    g = np.linspace(0, 1, w)[None, :, None] * np.array([[[40 + 50 * i, 120, 200 - 40 * i]]]) + 30
    Image.fromarray(np.repeat(g, h, 0).astype(np.uint8)).save(A / f'photo-{i + 1}.jpg')
st = Image.new('RGBA', (400, 400), (0, 0, 0, 0))
ImageDraw.Draw(st).rounded_rectangle((20, 20, 380, 380), 60, fill=(255, 216, 77), outline=(17, 17, 17), width=12)
st.save(A / 'sticker.png')

# 4. test song: 120 BPM, 24 loud bars, then a hit and a quiet tail (so beats.py finds an ending)
SR, bpm = 48000, 120.0
beat = 60 / bpm
n_beats = 4 * 28
song = np.zeros(int((n_beats * beat + 2) * SR), np.float32)
tt = np.arange(int(0.25 * SR)) / SR
kick = np.sin(2 * np.pi * (50 + 80 * np.exp(-tt * 30)) * tt) * np.exp(-tt * 12)
for k in range(n_beats):
    loud = 1.0 if k < 4 * 24 else 0.08
    i = int((0.5 + k * beat) * SR)
    song[i:i + len(kick)] += loud * 0.8 * kick
    if k % 4 == 0:
        tp = np.arange(int(4 * beat * SR)) / SR
        pad = 0.12 * loud * np.sin(2 * np.pi * [220, 247, 196, 262][(k // 4) % 4] * tp) * np.exp(-tp * 0.6)
        song[i:i + len(pad)] += pad[:len(song) - i]
mus = ad / 'work' / 'music'
mus.mkdir(parents=True)
subprocess.run(['ffmpeg', '-v', 'error', '-y', '-f', 'f32le', '-ar', str(SR), '-ac', '1', '-i', '-', '-ac', '2',
                '-b:a', '192k', mus / 'bed.mp3'], input=np.clip(song, -1, 1).tobytes(), check=True)
sh([PY, ads / '_engine' / 'beats.py', mus / 'bed.mp3', '--bpm', '120'])
bj = json.loads((mus / 'bed.beats.json').read_text())
bar, k0 = bj['bar_db'], bj['downbeat_phase']
loud = max(bar)
hit = next((k0 + 4 * (i + 1) for i in range(len(bar) - 2, -1, -1) if bar[i] > loud - 6 and bar[i + 1] < bar[i] - 8), None)
music = {'end_beat': hit - 16, 'hit_beat': hit, 'phrase': 16, 'hit_after_endcard': 1.4} if hit else {'start': 0}

# 5. word list by hand (what words.py would write), one window per segment, words on the tone bursts
segs = [(round(1.2 * k - 0.15, 2), round(1.2 * (k + 1) + 0.95, 2)) for k in range(0, int(SEC / 1.2) - 2, 2)]
segs[0] = (0.0, segs[0][1])
text = ('You already use AI a lot but you still do it yourself copying pasting files tools what if AI took it '
        'over I run this studio join us on March 12 early bird until Friday tap below now thanks').split()
win, wi = [], 0
for a, b in segs:
    ws = []
    for k in range(int(np.ceil(a / 1.2)), int(b / 1.2) + 1):
        for off in (0.02, 0.42):
            t0 = 1.2 * k + off
            if a <= t0 < b - 0.2 and t0 + 0.3 < 1.2 * k + 0.8 + 1e-6:
                ws.append({'w': text[wi % len(text)], 's': round(t0, 3), 'e': round(t0 + 0.35, 3)})
                wi += 1
    win.append({'win': [a, b], 'words': ws})
(ad / 'work').mkdir(exist_ok=True)
(ad / 'work' / 'words_whisper.json').write_text(json.dumps(win, indent=1))
W = [w for x in win for w in x['words']]
ids = [f's{i + 1}' for i in range(len(segs))]
mid = lambda i: (segs[i][0] + segs[i][1]) / 2
end_at = segs[-1][1] - 0.1

# 6. edit.json with every event type
cfg = json.loads((ad / 'edit.json').read_text(encoding='utf-8'))
cfg.update({
    'files': dict(cfg['files'], voice='audio/voice_warm.wav'),
    'music': music,
    'segments': [{'id': i, 'a': a, 'b': b, 'note': 'test'} for i, (a, b) in zip(ids, segs)],
    'variants': {'A-offer': {'segments': ids, 'flags': ['offer']},
                 'B-short': {'segments': [ids[0], ids[-1]], 'flags': []}},
    'shots': [[segs[0][0], 2, 'intro']] + [[a, 1 + i % 3] for i, (a, b) in enumerate(segs[1:])],
    'logos': ['assets/logo-1.png', 'assets/logo-2.png'],
    'photos': [f'assets/photo-{i}.jpg' for i in range(1, 5)],
    'endcard': {'at': end_at, 'dur': 2.0, 'sfx': ['whoosh'], 'title': ['THIS IS', '*A DEMO*', 'END CARD'],
                'when': 'thu 12 mar · 10:00–16:00', 'sticker': 'early bird · until friday', 'sticker_flag': 'offer',
                'image': 'assets/sticker.png'},
})
s = segs
ev = [
    {'type': 'hookbig', 'from': s[0][0], 'to': s[0][1] - 0.1},
    {'type': 'logos', 'word': W[1]['w'], 'near': W[1]['s'], 'to': s[0][1] - 0.6, 'sfx': ['pop']},
    {'type': 'stamp', 'from': s[0][1] - 0.55, 'text': 'YOURSELF.', 'to': s[0][1] - 0.05, 'sfx': ['whoosh', 'impact']},
    {'type': 'win', 'id': 'w1', 'from': s[1][0] + 0.1, 'slot': 'L1', 'role': 'copy', 'rot': -5, 'sfx': ['pop', 'key']},
    {'type': 'win', 'id': 'w2', 'from': s[1][0] + 0.5, 'slot': 'R1', 'role': 'paste', 'rot': 4, 'sfx': ['soft_whoosh', 'key']},
    {'type': 'files', 'id': 'f1', 'from': s[1][0] + 0.9, 'slot': 'L2', 'rot': -4, 'sfx': ['pop']},
    {'type': 'apps', 'id': 'a1', 'from': s[1][0] + 1.3, 'slot': 'R2', 'rot': 3},
    {'type': 'bubble', 'id': 'b1', 'from': s[1][0] + 1.6, 'slot': 'L1', 'glyph': 'clock', 'color': 'accent2',
     'text': 'Where do I start?', 'rot': -3, 'pos': {'9x16': [1030, 980, 1], '4x5': [1036, 700, 1]}},
    {'type': 'gather', 'from': s[1][1] - 0.5, 'ids': ['w1', 'w2', 'f1', 'a1', 'b1'], 'sfx': ['whoosh']},
    {'type': 'aicard', 'from': s[2][0] + 0.1, 'title': 'AI HANDLES IT', 'to': s[2][0] + 1.2, 'sfx': ['chime']},
    {'type': 'strike', 'from': s[2][0] + 1.3, 'text': 'BUSYWORK', 'check_word': W[0]['w'], 'check_near': s[2][0] + 1.6,
     'to': s[2][1] - 0.2, 'sfx': ['pop']},
]
# a word inside s3 for the strike-through
w3 = [w for w in W if s[2][0] + 1.4 < w['s'] < s[2][1] - 0.3]
if w3:
    ev[-1].update(check_word=w3[0]['w'], check_near=w3[0]['s'], check_sfx=['click'])
else:
    ev[-1].pop('check_word'), ev[-1].pop('check_near')
if len(s) > 3:
    ev += [
        {'type': 'nametag', 'from': s[3][0] + 0.05, 'name': 'SAM', 'role': 'founder', 'to': s[3][0] + 0.9, 'sfx': ['pop']},
        {'type': 'sticker', 'from': s[3][0] + 0.2, 'image': 'assets/sticker.png', 'label': 'THE TEAM', 'to': s[3][0] + 0.9},
        {'type': 'date', 'from': s[3][0] + 1.0, 'kicker': 'thursday', 'title': '12 MAR', 'sub': 'one-day workshop', 'to': s[3][0] + 1.8, 'sfx': ['slam']},
        {'type': 'timechip', 'from': s[3][0] + 1.2, 'text': '10:00–16:00', 'to': s[3][0] + 1.8, 'sfx': ['pop']},
    ]
if len(s) > 4:
    ev += [
        {'type': 'photos', 'from': s[4][0] + 0.05, 'to': s[4][0] + 1.2, 'sfx': ['whoosh']},
        {'type': 'price', 'flag': 'offer', 'from': s[4][0] + 1.3, 'kicker': 'early bird', 'value': '149', 'tag': 'until friday',
         'to': s[4][1] - 0.1, 'sfx': ['slam']},
    ]
if len(s) > 5:
    ev += [
        {'type': 'checklist', 'from': s[5][0] + 0.05, 'title': 'YOU LEAVE WITH', 'to': s[5][0] + 1.2,
         'rows': [['a working workflow', w['w'], w['s']] for w in W if s[5][0] < w['s'] < s[5][0] + 1.1][:2], 'sfx': ['pop']},
        {'type': 'post', 'from': s[5][0] + 1.25, 'text': 'Everyone is building AI agents now. Should I?', 'likes': 2431,
         'comments': '312 comments', 'to': s[5][1] - 0.1, 'sfx': ['pop']},
    ]
ev += [
    {'type': 'card', 'from': s[-1][0] + 0.05, 'title': 'HANDS-ON', 'sub': 'bring your laptop', 'color': 'accent4', 'rot': -3,
     'to': s[-1][0] + 0.5, 'sfx': ['pop']},
    {'type': 'logo', 'from': s[-1][0] + 0.55, 'sub': 'THE COMMUNITY', 'to': s[-1][0] + 0.95, 'sfx': ['pop']},
    {'type': 'poll', 'from': s[-1][0] + 1.0, 'q': 'ARE YOU IN?', 'sub': 'seats are limited', 'tap_word': W[-1]['w'],
     'tap_near': W[-1]['s'], 'tap_sfx': ['click'], 'to': s[-1][0] + 1.75},
    {'type': 'arrow', 'from': s[-1][0] + 1.8, 'text': 'TAP BELOW', 'to': end_at, 'sfx': ['whoosh']},
]
# the poll taps on a word inside the last segment
lw = [w for w in W if s[-1][0] + 1.05 < w['s'] < s[-1][0] + 1.7] or [w for w in W if s[-1][0] <= w['s']]
ev[-2].update(tap_word=lw[0]['w'], tap_near=lw[0]['s'])
cfg['events'] = [e for e in ev if not (e['type'] == 'checklist' and not e['rows'])]
(ad / 'edit.json').write_text(json.dumps(cfg, indent=1, ensure_ascii=False), encoding='utf-8')

# 7. the pipeline
E = ads / '_engine'
sh([PY, E / 'build.py', '01-demo', 'prep'], cwd=ads)
sh([PY, E / 'voice.py', ad / 'work/audio/src48.wav', ad / 'work/audio', '--eq', 'warm'], cwd=ads)
if opt('--whisper'):
    sh([PY, E / 'words.py', ad / 'work/audio/voice_warm.wav', ad / 'work/words_whisper_test.json',
        f'0:{min(SEC, 6)}', '--model', opt('--whisper'), '--lang', 'en'], cwd=ads)
for v in ('A-offer', 'B-short'):
    sh([PY, E / 'build.py', '01-demo', 'plan', v, fmts[0]], cwd=ads)
    sh([PY, E / 'build.py', '01-demo', 'audit', v], cwd=ads)
sh([PY, E / 'build.py', '01-demo', 'audio', 'A-offer'], cwd=ads)
for f in fmts:
    sh([PY, E / 'build.py', '01-demo', 'base', 'A-offer', f], cwd=ads)
    times = [round(x, 2) for x in np.linspace(0.3, 0.97 * SEC, 12)]
    sh([PY, E / 'build.py', '01-demo', 'stills', 'A-offer', f, *times], cwd=ads)
    sh([PY, E / 'build.py', '01-demo', 'overlay', 'A-offer', f], cwd=ads)
    sh([PY, E / 'build.py', '01-demo', 'final', 'A-offer', f], cwd=ads)
print(f'\nDone. Exports in {ad / "exports"}, contact sheets in {ad / "work" / "stills"}')
