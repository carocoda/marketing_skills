"""Shared helpers for the project scripts: paths, project.json, the page, audio I/O, API keys, HTTPS and Whisper.
Every script in this folder imports this, so they all work no matter which folder you run them from.
"""
import json
import os
import shutil
import ssl
import subprocess
import time
import urllib.request
from pathlib import Path

HERE = Path(__file__).resolve().parent
PAGE = HERE / 'motion.html'
SR = 48000
CHROME_ARGS = ['--force-color-profile=srgb', '--font-render-hinting=none', '--disable-lcd-text']


def need(*tools):
    """Stop with a clear message when a command-line tool is missing."""
    missing = [t for t in tools if not shutil.which(t)]
    if missing:
        raise SystemExit(f'Missing: {", ".join(missing)}. Install ffmpeg (macOS: brew install ffmpeg, '
                         'Ubuntu: sudo apt install ffmpeg, Windows: winget install ffmpeg), then run this again.')


def project():
    """project.json: the brief, the music grid and loop, the voice lines and the mix settings."""
    return json.load(open(HERE / 'project.json', encoding='utf-8'))


def canvas():
    c = project().get('canvas', {})
    return c.get('width', 1920), c.get('height', 1080), c.get('fps', 60)


# ---------------------------------------------------------------- the page
def open_page(pw, query='?still'):
    """Headless Chromium with motion.html loaded and ready. Raises on the first JavaScript error."""
    w, h, _ = canvas()
    br = pw.chromium.launch(args=CHROME_ARGS)
    pg = br.new_page(viewport={'width': w, 'height': h}, device_scale_factor=1)
    errors = []
    pg.on('pageerror', lambda e: errors.append(str(e)))
    sep = '&' if '?' in query else '?'
    pg.goto(PAGE.as_uri() + query + f'{sep}w={w}&h={h}')
    try:
        pg.wait_for_function('window.__ready === true', timeout=60000)
    except Exception:
        raise SystemExit('motion.html never got ready' + (f': {errors[0]}' if errors else ' (fonts or images did not load?)'))
    if errors:
        raise SystemExit('motion.html has a JavaScript error: ' + errors[0])
    return br, pg


def playwright():
    try:
        from playwright.sync_api import sync_playwright
        return sync_playwright
    except ImportError:
        raise SystemExit('Missing the playwright package: pip3 install playwright && python3 -m playwright install chromium')


def page_info():
    """The grid and the sound events, read from the page itself. The page is the single source of truth for
    timing: T (window.DURATION), BEATS and window.SFX."""
    with playwright()() as pw:
        br, pg = open_page(pw)
        info = pg.evaluate('({T: window.DURATION, beats: window.BEATS, beat: window.BEAT, sfx: window.SFX})')
        br.close()
    return info


# ---------------------------------------------------------------- audio
def load(path, sr=SR, ch=1, af=None):
    """Any audio file -> float32 numpy array (mono, or frames x ch)."""
    import numpy as np
    need('ffmpeg')
    cmd = ['ffmpeg', '-v', 'error', '-i', str(path)]
    if af:
        cmd += ['-af', af]
    cmd += ['-ac', str(ch), '-ar', str(sr), '-f', 'f32le', '-']
    x = np.frombuffer(subprocess.run(cmd, capture_output=True, check=True).stdout, np.float32).copy()
    return x.reshape(-1, ch) if ch > 1 else x


def save(path, x, sr=SR):
    """float array -> 24-bit wav."""
    import numpy as np
    need('ffmpeg')
    x = np.ascontiguousarray(np.asarray(x, np.float32))
    ch = 1 if x.ndim == 1 else x.shape[1]
    Path(path).parent.mkdir(parents=True, exist_ok=True)
    subprocess.run(['ffmpeg', '-v', 'error', '-y', '-f', 'f32le', '-ar', str(sr), '-ac', str(ch), '-i', '-',
                    '-c:a', 'pcm_s24le', str(path)], input=x.tobytes(), check=True)


def speech_bounds(x, sr=SR, thresh_db=-35, hop_s=0.01):
    """First and last 10 ms frame whose RMS is within `thresh_db` of the loudest frame: where the words start
    and stop inside a take (TTS takes have 0.15 to 0.5 s of silence at both ends)."""
    import numpy as np
    hop = int(hop_s * sr)
    n = max(1, len(x) // hop)
    rms = np.sqrt(np.mean(x[:n * hop].reshape(n, hop) ** 2, axis=1)) + 1e-12
    db = 20 * np.log10(rms / rms.max())
    on = np.nonzero(db > thresh_db)[0]
    if not len(on):
        return 0.0, len(x) / sr
    return on[0] * hop_s, (on[-1] + 1) * hop_s


# ---------------------------------------------------------------- keys
def api_key(name, required=True):
    """An API key from the environment, else from the first .env file found walking up from the working folder
    or from this project. Never print it, never write it into a file or a command."""
    k = os.environ.get(name, '').strip()
    if k:
        return k
    for d in [Path.cwd(), *Path.cwd().parents, HERE, *HERE.parents]:
        f = d / '.env'
        if f.is_file():
            for line in f.read_text(errors='ignore').splitlines():
                line = line.strip()
                if line.startswith('export '):
                    line = line[7:].strip()
                if line.startswith(name + '='):
                    v = line.split('=', 1)[1].strip().strip('"').strip("'")
                    if v:
                        return v
    if required:
        raise SystemExit(f'No {name} found. Export it in your shell or put {name}=... in a .env file next to the '
                         'project (keep .env out of git). No key? See "Without a key" in the skill README: scratch '
                         'voice with placeholder.py, your own recordings in vo/, or a music-only video.')
    return None


def voice_provider(pj):
    """'openrouter', 'gemini' or 'none', from voice.provider ('auto' picks by which key exists)."""
    p = pj.get('voice', {}).get('provider', 'auto')
    if p != 'auto':
        return p
    if api_key('OPENROUTER_API_KEY', required=False):
        return 'openrouter'
    if api_key('GEMINI_API_KEY', required=False) or api_key('GOOGLE_API_KEY', required=False):
        return 'gemini'
    return 'none'


def ssl_context():
    """The python.org build of Python on macOS ships without a CA bundle, so plain urllib fails with
    CERTIFICATE_VERIFY_FAILED. Use certifi's bundle, or the system one."""
    try:
        import certifi
        return ssl.create_default_context(cafile=certifi.where())
    except ImportError:
        for f in ('/etc/ssl/cert.pem', '/etc/ssl/certs/ca-certificates.crt'):
            if Path(f).exists():
                return ssl.create_default_context(cafile=f)
        return ssl.create_default_context()


def urlopen(req, timeout=180):
    return urllib.request.urlopen(req, timeout=timeout, context=ssl_context())


def openrouter_cost(gen_id, key, tries=8):
    """What one OpenRouter call cost, in dollars (the generation endpoint needs a second or two to know)."""
    for _ in range(tries):
        time.sleep(1.5)
        try:
            req = urllib.request.Request(f'https://openrouter.ai/api/v1/generation?id={gen_id}',
                                         headers={'Authorization': f'Bearer {key}'})
            d = json.load(urlopen(req, timeout=30)).get('data', {})
            if d.get('total_cost') is not None:
                return float(d['total_cost'])
        except Exception:
            pass
    return None


# ---------------------------------------------------------------- Whisper (optional, for voice checks)
HF_HUB = Path(os.environ.get('HF_HOME', Path.home() / '.cache' / 'huggingface')) / 'hub'
# multilingual models (".en" models only do English)
FW_MODELS = [('large-v3', 'Systran--faster-whisper-large-v3'),
             ('turbo', 'mobiuslabsgmbh--faster-whisper-large-v3-turbo'),
             ('large-v2', 'Systran--faster-whisper-large-v2'),
             ('medium', 'Systran--faster-whisper-medium'),
             ('small', 'Systran--faster-whisper-small'),
             ('base', 'Systran--faster-whisper-base')]


def whisper_model(name=None):
    """A faster-whisper model that is already on this computer (a first download is 0.15 to 3 GB: ask first).
    Returns (model, name)."""
    try:
        import certifi
        os.environ.setdefault('SSL_CERT_FILE', certifi.where())
    except ImportError:
        pass
    try:
        from faster_whisper import WhisperModel
    except ImportError:
        raise SystemExit('Voice checks need faster-whisper: pip3 install faster-whisper. Without it, skip the '
                         'checks (tts.py --no-check) and listen to every take yourself.')
    cached = [m for m, repo in FW_MODELS if (HF_HUB / f'models--{repo}').exists()]
    pick = name or (cached[0] if cached else None)
    if not pick:
        raise SystemExit('No multilingual Whisper model on this computer. Ask before downloading one '
                         '(large-v3 is about 3 GB and best for non-English, small about 0.5 GB), then run with '
                         '--whisper small (or large-v3) once.')
    model = WhisperModel(pick, device='cpu', compute_type='int8', cpu_threads=max(2, (os.cpu_count() or 4) - 2))
    return model, pick


def transcribe(model, path, lang=None):
    """-> (text, [{'w', 's', 'e', 'p'}]) with word times in seconds from the start of the file."""
    lang = lang or project().get('voice', {}).get('language') or None
    segs, _ = model.transcribe(str(path), language=lang, word_timestamps=True, beam_size=5)
    words = [{'w': w.word.strip(), 's': round(w.start, 3), 'e': round(w.end, 3), 'p': round(w.probability, 3)}
             for s in segs for w in s.words]
    return ' '.join(w['w'] for w in words), words
