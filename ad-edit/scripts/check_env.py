"""Can this computer edit talking-head ads? Changes nothing (unless --build); prints what is missing and how to fix it.

  python3 scripts/check_env.py            check
  python3 scripts/check_env.py --build    macOS: also build the two Swift helpers (HDR to SDR, face tracking)

MISS = needed, the pipeline stops without it. note = optional, the pipeline falls back to something weaker.
"""
import importlib
import os
import platform
import shutil
import subprocess
import sys
from pathlib import Path

SKILL = Path(__file__).resolve().parents[1]
ENGINE = SKILL / 'template' / '_engine'
TOOLS = Path(os.environ.get('AD_EDIT_TOOLS', Path.home() / '.local/ad-edit-tools'))
HUB = Path(os.environ.get('HF_HOME', Path.home() / '.cache' / 'huggingface')) / 'hub'
MAC = platform.system() == 'Darwin'
ok = True


def line(good, what, fix='', warn=False):
    global ok
    if not good and not warn:
        ok = False
    tag = 'ok  ' if good else ('note' if warn else 'MISS')
    print(f'  {tag}  {what}' + ('' if good or not fix else f'\n          -> {fix}'))


def out(cmd, timeout=60):
    try:
        r = subprocess.run([str(c) for c in cmd], capture_output=True, text=True, timeout=timeout)
        return r.returncode, (r.stdout + r.stderr).strip()
    except Exception as e:
        return 1, str(e)


def swift_build(name):
    """Build with the default SDK; if this swiftc refuses the newest SDK, retry with an older one that is installed."""
    TOOLS.mkdir(parents=True, exist_ok=True)
    src, exe = ENGINE / f'{name}.swift', TOOLS / name
    code, msg = out(['swiftc', '-O', src, '-o', exe], timeout=600)
    if code:
        sdks = sorted(Path('/Library/Developer/CommandLineTools/SDKs').glob('MacOSX1*.sdk'), reverse=True)
        for sdk in sdks:
            code, msg = out(['swiftc', '-O', '-sdk', sdk, src, '-o', exe], timeout=600)
            if code == 0:
                break
    return code, msg


print('Tools')
line(sys.version_info >= (3, 9), f'python {sys.version.split()[0]}', 'install Python 3.9 or newer')
ff = {'Darwin': 'brew install ffmpeg', 'Linux': 'sudo apt install ffmpeg (or your package manager)'}.get(
    platform.system(), 'winget install ffmpeg, or download from ffmpeg.org')
for t in ('ffmpeg', 'ffprobe'):
    line(bool(shutil.which(t)), t, ff)
if shutil.which('ffmpeg'):
    enc = out(['ffmpeg', '-hide_banner', '-encoders'])[1]
    line(all(e in enc for e in ('libx264', 'prores_ks', ' aac ')), 'ffmpeg encoders libx264, prores_ks, aac',
         'install a full ffmpeg build (the Homebrew and most Linux builds have these)')
    flt = out(['ffmpeg', '-hide_banner', '-filters'])[1]
    need = ['perspective', 'loudnorm', 'deesser', 'adynamicequalizer', 'agate', 'acompressor', 'alimiter',
            'vignette', 'unsharp', 'tpad', 'afftdn']
    miss = [f for f in need if f' {f} ' not in flt]
    line(not miss, 'ffmpeg filters for picture and voice' + (f' (missing: {", ".join(miss)})' if miss else ''),
         'update ffmpeg (adynamicequalizer needs ffmpeg 6 or newer)')
    line(' zscale ' in flt, 'ffmpeg zscale (HDR phone video to SDR)',
         'only matters for HDR footage when the macOS helper is not built: use an ffmpeg build with libzimg', warn=True)

print('Python packages')
for mod, pip, need_it in [('numpy', 'numpy', True), ('PIL', 'pillow', True), ('playwright', 'playwright', True),
                          ('faster_whisper', 'faster-whisper', True), ('nara_wpe', 'nara_wpe', False),
                          ('cv2', 'opencv-python', False)]:
    try:
        importlib.import_module(mod)
        line(True, pip)
    except ImportError:
        why = {'nara_wpe': ' (dereverb; without it room echo stays in)',
               'cv2': ' (face tracking when the macOS helper is not built; without it the crop sits on a fixed spot)'}
        line(False, pip + why.get(mod, ''), f'pip3 install {pip}', warn=not need_it)
try:
    from playwright.sync_api import sync_playwright
    with sync_playwright() as pw:
        pw.chromium.launch().close()
    line(True, 'playwright chromium')
except Exception:
    line(False, 'playwright chromium', 'python3 -m playwright install chromium')

print('Speech models (local, in the Hugging Face cache; the first run downloads them)')
for name, repo, size, need_it in [('Whisper large-v3 (words)', 'Systran--faster-whisper-large-v3', 'about 3 GB', True),
                                  ('CrisperWhisper (sharper word times, optional)', 'nyrahealth--faster_CrisperWhisper',
                                   'about 3 GB', False)]:
    snap = list((HUB / f'models--{repo}' / 'snapshots').glob('*/model.bin'))
    line(bool(snap), name, f'not downloaded yet ({size}); words.py / crisper.py fetch it on first run. '
         'A smaller model for a quick test: --model small', warn=True)

print(f'Voice tools (in {TOOLS} or on the PATH)')
df = TOOLS / 'deep-filter' if (TOOLS / 'deep-filter').is_file() else shutil.which('deep-filter')
code, v = out([df, '--version']) if df else (1, '')
line(code == 0, f'deep-filter (DeepFilterNet) {v if code == 0 else "not found"}',
     'download the binary for your system from github.com/Rikorose/DeepFilterNet/releases (e.g. '
     f'deep-filter-0.5.6-aarch64-apple-darwin), save it as {TOOLS}/deep-filter and chmod +x it. '
     'Without it voice.py falls back to ffmpeg afftdn, which is much weaker.', warn=True)

if MAC:
    print(f'macOS helpers in {TOOLS} (best HDR tone mapping and face tracking for iPhone footage)')
    have_swiftc = bool(shutil.which('swiftc'))
    line(have_swiftc, 'swiftc', 'xcode-select --install', warn=True)
    for name in ('hdr_to_sdr', 'face_track'):
        if '--build' in sys.argv and have_swiftc:
            code, msg = swift_build(name)
            line(code == 0, f'{name} built', msg[-300:])
        exe = TOOLS / name
        line(exe.is_file() and os.access(exe, os.X_OK), name, f'python3 {Path(__file__).name} --build', warn=True)

print('Default UI sounds')
sfx = ENGINE / 'assets' / 'sfx'
names = ('pop', 'click', 'key-press', 'whoosh-short', 'impact-bass-1', 'chime')
line(all(any((sfx / f'{n}{e}').exists() for e in ('.wav', '.mp3')) for n in names), f'sounds in {sfx}',
     f'new_ad.py makes them, or: python3 {ENGINE / "make_sfx.py"} "{sfx}"', warn=True)

print('Internet (Google Fonts for the overlay, unless your brand uses local font files)')
code, _ = out(['curl', '-sS', '-o', '/dev/null', '-m', '10', 'https://fonts.googleapis.com/css2?family=Archivo'])
line(code == 0, 'fonts.googleapis.com reachable', 'offline the overlay renders in a fallback font; '
     'set "file" for each font in brand.json to work offline', warn=True)

print('\nReady.' if ok else '\nFix the MISS lines and run this again.')
sys.exit(0 if ok else 1)
