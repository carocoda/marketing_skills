"""Can this computer make motion videos? Changes nothing; prints what is missing and how to get it.

  python3 <skill>/scripts/check_env.py

MISS lines block rendering. note lines are optional: without a key you can still render (scratch voice, your own
audio, or a music-only video), and without Whisper you check the takes by ear.
"""
import importlib
import os
import platform
import shutil
import socket
import ssl
import subprocess
import sys
from pathlib import Path

ok = True
MAC = platform.system() == 'Darwin'


def line(good, what, fix='', warn=False):
    global ok
    if not good and not warn:
        ok = False
    tag = 'ok  ' if good else ('note' if warn else 'MISS')
    print(f'  {tag}  {what}' + ('' if good or not fix else f'\n          -> {fix}'))


print('Tools')
line(sys.version_info >= (3, 9), f'python {sys.version.split()[0]}', 'install Python 3.9 or newer')
ff_fix = 'brew install ffmpeg' if MAC else 'sudo apt install ffmpeg (Linux) or winget install ffmpeg (Windows)'
for tool in ('ffmpeg', 'ffprobe'):
    line(bool(shutil.which(tool)), tool, ff_fix)
if shutil.which('ffmpeg'):
    enc = subprocess.run(['ffmpeg', '-hide_banner', '-encoders'], capture_output=True, text=True).stdout
    line('libx264' in enc and 'ffv1' in enc, 'ffmpeg has libx264 and ffv1', 'install a full ffmpeg build')

print('Python packages')
for mod, pip, needed in [('numpy', 'numpy', True), ('scipy', 'scipy', True), ('PIL', 'pillow', True),
                         ('playwright', 'playwright', True), ('certifi', 'certifi', False),
                         ('faster_whisper', 'faster-whisper', False)]:
    try:
        importlib.import_module(mod)
        line(True, pip)
    except ImportError:
        why = '' if needed else ' (optional: ' + ('HTTPS on macOS python.org builds' if mod == 'certifi'
                                                  else 'checks voice takes and times captions') + ')'
        line(False, pip + why, f'pip3 install {pip}', warn=not needed)
try:
    from playwright.sync_api import sync_playwright
    with sync_playwright() as pw:
        pw.chromium.launch().close()
    line(True, 'playwright chromium')
except Exception:
    line(False, 'playwright chromium', 'python3 -m playwright install chromium')

print('Whisper model (optional, for voice checks)')
hub = Path(os.environ.get('HF_HOME', Path.home() / '.cache' / 'huggingface')) / 'hub'
models = [m for m, repo in [('large-v3', 'Systran--faster-whisper-large-v3'),
                            ('turbo', 'mobiuslabsgmbh--faster-whisper-large-v3-turbo'),
                            ('medium', 'Systran--faster-whisper-medium'), ('small', 'Systran--faster-whisper-small'),
                            ('base', 'Systran--faster-whisper-base')]
          if (hub / f'models--{repo}').exists()]
line(bool(models), f'multilingual model on disk: {", ".join(models)}' if models else 'no multilingual Whisper model',
     'ask before downloading: large-v3 is about 3 GB (best outside English), small about 0.5 GB. '
     'python3 vo_check.py --whisper small <line> downloads it on first use.', warn=True)

print('Keys (optional: paid voice and music)')
def find_key(name):
    if os.environ.get(name):
        return 'environment'
    for d in [Path.cwd(), *Path.cwd().parents]:
        f = d / '.env'
        if f.is_file() and any(l.strip().removeprefix('export ').startswith(name + '=')
                               for l in f.read_text(errors='ignore').splitlines()):
            return str(f)
    return None
for name, what in [('OPENROUTER_API_KEY', 'voice (Gemini TTS) and music (Lyria)'),
                   ('GEMINI_API_KEY', 'voice only (Gemini TTS, direct)')]:
    where = find_key(name)
    line(bool(where), f'{name} found ({where}): {what}' if where else f'{name}: {what}',
         'optional. Without a key: placeholder.py voice for a scratch track, your own recordings in vo/, '
         'and your own or the placeholder music.', warn=True)
line(bool(shutil.which('say')), 'macOS "say" (free scratch voice)' if shutil.which('say') else
     'no "say" command: placeholder.py voice makes a hum per word instead', warn=True)

print('Internet (voice, music, and Google Fonts if the page uses them)')
try:
    import certifi
    ctx = ssl.create_default_context(cafile=certifi.where())
except ImportError:
    ctx = ssl.create_default_context()
for host in ('fonts.googleapis.com', 'fonts.gstatic.com', 'openrouter.ai', 'generativelanguage.googleapis.com'):
    try:
        with socket.create_connection((host, 443), timeout=10) as sock:
            with ctx.wrap_socket(sock, server_hostname=host):
                pass
        line(True, f'{host} reachable')
    except Exception as e:
        line(False, f'{host}: {e}', 'check the connection (pip3 install certifi fixes certificate errors). '
             'Offline you can still render with local font files (BRAND.fonts src).', warn=True)

print('Machine')
free = shutil.disk_usage(Path.home()).free / 1e9
line(free > 5, f'{free:.0f} GB free disk', 'a full render needs a few GB of working space (lossless master)')
cpus = os.cpu_count() or 4
ram = 0
try:
    if MAC:
        ram = int(subprocess.run(['sysctl', '-n', 'hw.memsize'], capture_output=True, text=True).stdout) / 2 ** 30
    elif Path('/proc/meminfo').exists():
        ram = int(Path('/proc/meminfo').read_text().split()[1]) / 2 ** 20
except Exception:
    pass
workers = max(2, min(6, cpus - 2, int(ram // 2.5) if ram else 4))
line(True, f'{cpus} cores, {ram:.0f} GB RAM -> render with --workers {workers}')

print('\nAll set.' if ok else '\nFix the MISS lines, then run this again.')
sys.exit(0 if ok else 1)
