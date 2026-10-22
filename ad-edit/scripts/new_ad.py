"""Start a new talking-head ad in the engine + ad-folder layout:

  <ads>/_engine/        the shared engine (build.py, overlay.html, voice.py, tools, assets/sfx), one per project
  <ads>/brand.json      colours, fonts, logo, CTA, URL (from the setup interview), shared by every ad
  <ads>/<NN-name>/      this ad: edit.json, notes.md, assets/

  python3 scripts/new_ad.py <ads>/<NN-name> --source "<path to the take>" [--name my-ad] [--work DIR] [--out DIR]
                            [--lang en] [--update-engine] [--force]

--work and --out default to <ad>/work and <ad>/exports (git-ignored). Media is big (5 to 10 GB per ad with two
variants x two formats), so point them at an external drive if your disk is small.
The engine is copied from the skill only when <ads>/_engine/ does not exist yet; an existing engine is left alone
(other ads depend on it) unless you add --update-engine. Nothing is copied from the source video.
"""
import filecmp
import json
import shutil
import subprocess
import sys
from datetime import date
from pathlib import Path

SKILL = Path(__file__).resolve().parents[1]
TEMPLATE = SKILL / 'template'

args = sys.argv[1:]
if not args or args[0].startswith('-'):
    raise SystemExit(__doc__)
opt = lambda k: args[args.index(k) + 1] if k in args else None
dest = Path(args[0]).expanduser().resolve()
if dest.name.startswith('_'):
    raise SystemExit('Give the folder for the ad, not the engine folder.')
if dest.exists() and any(dest.iterdir()) and '--force' not in args:
    raise SystemExit(f'{dest} is not empty. Choose a new folder, or add --force.')
source = opt('--source')
if not source:
    raise SystemExit('Pass the recording with --source "<path to the video>".')
src = Path(source).expanduser().resolve()
if not src.is_file():
    raise SystemExit(f'source not found: {src}')

ads = dest.parent
engine, skill_engine = ads / '_engine', TEMPLATE / '_engine'
skip = shutil.ignore_patterns('__pycache__', '.DS_Store')
if not engine.exists() or '--update-engine' in args:
    note = f'Engine {"updated" if engine.exists() else "created"}: {engine}'
    shutil.copytree(skill_engine, engine, dirs_exist_ok=True, ignore=skip)
    (engine / '.gitignore').write_text('__pycache__/\n', encoding='utf-8')
else:
    differ = [f.name for f in skill_engine.iterdir() if f.is_file()
              and not ((engine / f.name).is_file() and filecmp.cmp(f, engine / f.name, shallow=False))]
    note = f'Existing engine used: {engine}' + (
        f'\nNOTE: it differs from the skill ({", ".join(differ)}). Compare first, and only update with '
        '--update-engine when the other ads still run on it.' if differ else '')
sfx = engine / 'assets' / 'sfx'
if not any(sfx.glob('*.wav')) and not any(sfx.glob('*.mp3')):
    subprocess.run([sys.executable, str(engine / 'make_sfx.py'), str(sfx)], check=True)

brand = ads / 'brand.json'
if not brand.exists():
    shutil.copy(TEMPLATE / 'brand.json', brand)
    note += f'\nBrand file created with neutral defaults: {brand} (fill it in from the setup interview)'

dest.mkdir(parents=True, exist_ok=True)
(dest / 'assets').mkdir(exist_ok=True)
ex = json.loads((TEMPLATE / 'example-ad' / 'edit.json').read_text(encoding='utf-8'))
work, out = opt('--work') or 'work', opt('--out') or 'exports'
(dest / '.gitignore').write_text('work/\nexports/\n', encoding='utf-8')   # media never goes into git
cfg = {
    "_about": "Recipe for one ad. Times are seconds in the source take. Fields: references/edit-json.md in the skill.",
    "title": f"Talking-head ad {dest.name}",
    "name": opt('--name') or dest.name,
    "version": "v1",
    "source": str(src),
    "work": work,
    "out": out,
    "fps": 30,
    "language": opt('--lang') or "",
    "files": dict(ex['files']),
    "whisper_prompt": "",
    "mix": ex['mix'],
    "segments": [],
    "variants": {},
    "formats": ex['formats'],
    "shots": [],
    "words_fix": [], "words_at": [], "words_drop": [], "words_add": [],
    "logos": [],
    "photos": [],
    "events": [],
    "endcard": {"at": 0, "dur": 2.6, "sfx": ["whoosh"], "title": ["FILL IN", "*THE*", "OFFER"],
                "when": "", "sticker": "", "sticker_flag": "offer"},
}
(dest / 'edit.json').write_text(json.dumps(cfg, ensure_ascii=False, indent=1) + '\n', encoding='utf-8')
(dest / 'notes.md').write_text(f"""# Ad: {dest.name}

Started on {date.today():%Y-%m-%d} from the ad-edit template.

- Source: `{src}`
- Exports: `{out}`
- Work files: `{work}`
- Recipe (this folder): `edit.json`, `assets/`; the code is in `../_engine/`

## Plan (approved on ...)

(cut list, variants, graphics per sentence, voice preset, music, facts)

## Versions

| version | date | feedback (word for word) | what changed | checked |
|---|---|---|---|---|
""", encoding='utf-8')

print(f"""New ad: {dest}
{note}

Next steps (see SKILL.md), from {ads}:
  python3 _engine/build.py {dest.name} prep
  python3 _engine/voice.py "<work>/audio/src48.wav" "<work>/audio" --eq warm
  python3 _engine/islands.py "<work>/audio/voice_warm.wav"
  python3 _engine/words.py "<work>/audio/voice_warm.wav" "<work>/words_whisper.json" <a:b windows> --prompt "names, jargon"
(<work> is {work if Path(work).is_absolute() else dest / work})
Music: put a track you have the rights to in <work>/music/bed.mp3, add "music": {{}} to edit.json, and measure it with
  python3 _engine/beats.py "<work>/music/bed.mp3"   (references/music-and-sound.md)""")
