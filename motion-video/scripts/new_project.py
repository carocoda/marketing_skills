"""Start a new motion video: copy the template project into a folder and set the format.

  python3 <skill>/scripts/new_project.py videos/spring-launch
  python3 <skill>/scripts/new_project.py videos/spring-reel --format 9:16
  python3 <skill>/scripts/new_project.py <folder> --force               into a folder that already has files
  python3 <skill>/scripts/new_project.py <folder> --no-placeholders     skip making the free stand-in sounds

Formats: 16:9 (1920x1080, the default), 9:16 (1080x1920, Reels/TikTok/Shorts/Stories), 1:1 (1080x1080), 4:5 (1080x1350).
The copy is a 32 s example video that renders as-is, so you can check the setup straight away. It gets free
stand-in UI sounds and music (placeholder.py), made on this computer. Then replace it piece by piece: BRAND and
COPY in motion.html, project.json (brief, facts, music, lines), the states, the sound.
"""
import json
import shutil
import subprocess
import sys
from datetime import date
from pathlib import Path

SKILL = Path(__file__).resolve().parents[1]
TEMPLATE = SKILL / 'templates' / 'project'
SKIP = {'__pycache__', 'stills', 'chunks', 'chunks_preview', 'tmp', 'takes', 'tests', '.DS_Store'}
GENERATED = {'video_noaudio.mkv', 'preview.mp4', 'preview_noaudio.mp4', 'mix.wav', 'mix_log.json'}
FORMATS = {'16:9': (1920, 1080), '9:16': (1080, 1920), '1:1': (1080, 1080), '4:5': (1080, 1350)}

args = [a for a in sys.argv[1:] if not a.startswith('--')]
if not args or '--help' in sys.argv or '-h' in sys.argv:
    raise SystemExit(__doc__)
fmt = '16:9'
if '--format' in sys.argv:
    fmt = sys.argv[sys.argv.index('--format') + 1]
    args = [a for a in args if a != fmt]
    if fmt not in FORMATS:
        raise SystemExit(f'unknown format {fmt}: use one of {", ".join(FORMATS)}')
dest = Path(args[0]).expanduser().resolve()
if dest.exists() and any(dest.iterdir()) and '--force' not in sys.argv:
    raise SystemExit(f'{dest} is not empty. Pick a new folder, or add --force to copy into it anyway.')
dest.mkdir(parents=True, exist_ok=True)

for src in TEMPLATE.iterdir():
    if src.name in SKIP or src.name in GENERATED:
        continue
    target = dest / src.name
    if src.is_dir():
        shutil.copytree(src, target, dirs_exist_ok=True, ignore=shutil.ignore_patterns(*SKIP, *GENERATED))
    else:
        shutil.copy2(src, target)
for d in ('assets/sfx', 'audio/music', 'vo/takes'):
    (dest / d).mkdir(parents=True, exist_ok=True)

pj_path = dest / 'project.json'
pj = json.loads(pj_path.read_text(encoding='utf-8'))
w, h = FORMATS[fmt]
pj['canvas'].update(width=w, height=h)
pj_path.write_text(json.dumps(pj, indent=2, ensure_ascii=False) + '\n', encoding='utf-8')

(dest / 'script.md').rename(dest / 'script.example.md')
(dest / 'script.md').write_text(f"""# Script

Format {fmt} ({w}x{h}), length, BPM, beats. Approved on: (date, by whom)

## Voice-over (one line per take)

| # | Text | Start (beat) |
|---|---|---|

## Picture on the beat grid

| Beats | The shape becomes | On screen | Synced to |
|---|---|---|---|

## Music

## Cost estimate
""", encoding='utf-8')
(dest / 'notes.md').write_text(f"""# Notes and versions

Started on {date.today():%Y-%m-%d} from the motion-video template ({fmt}).
One row per version you send. Copy the feedback word for word, then what you changed and how you checked it.

| version | date | feedback | what changed | checked | cost |
|---|---|---|---|---|---|
""", encoding='utf-8')
(dest / '.gitignore').write_text('__pycache__/\nstills/\nchunks/\nchunks_preview/\naudio/tmp/\n'
                                 'video_noaudio.mkv\npreview.mp4\npreview_noaudio.mp4\n.env\n', encoding='utf-8')

made = ''
if '--no-placeholders' not in sys.argv:
    if shutil.which('ffmpeg'):
        r = subprocess.run([sys.executable, str(dest / 'placeholder.py'), 'sfx', 'music'], cwd=dest)
        made = '' if r.returncode else 'Free stand-in UI sounds and music are in assets/sfx/ and audio/music/.\n'
    else:
        made = 'ffmpeg is missing, so no stand-in sounds yet: install it, then python3 placeholder.py\n'

note = '' if fmt == '16:9' else (f'\nFormat {fmt}: the page scales the camera to the format, but look at every beat: '
                                 'the layouts were drawn for 16:9 (phase 3, "Another format").\n')
print(f"""New project: {dest}
{made}{note}
Check the setup:
  cd "{dest}"
  python3 placeholder.py voice   # optional: a scratch voice so the mix has words in it
  python3 build_audio.py         # the soundtrack
  python3 render.py beats        # a still per beat -> stills/contactsheet.png (look at it)
  python3 qa.py                  # the automatic checks

Then follow the skill: script, beat grid and cost estimate first (phase 1, wait for a yes), then sound, then build.""")
