"""Shared helpers for the youtube-shorts scripts. Standard library only (Pillow is imported
lazily by the scripts that draw)."""
import json
import os
import shutil
import subprocess
import sys

ASPECTS = {
    "9x16": (1080, 1920),
    "16x9": (1920, 1080),
    "1x1": (1080, 1080),
    "4x5": (1080, 1350),
}


def die(msg, code=1):
    print(f"error: {msg}", file=sys.stderr)
    sys.exit(code)


def need(tool):
    """Exit with a clear message when a command-line tool is missing."""
    if shutil.which(tool) is None:
        hints = {
            "ffmpeg": "Install ffmpeg: macOS `brew install ffmpeg`, Ubuntu `sudo apt install ffmpeg`, "
                      "Windows `winget install ffmpeg`.",
            "ffprobe": "ffprobe ships with ffmpeg. Install ffmpeg first.",
        }
        die(f"`{tool}` not found on PATH. {hints.get(tool, '')}")


def run(cmd, quiet=True):
    """Run a command, show the ffmpeg error tail if it fails."""
    if quiet and cmd and cmd[0] == "ffmpeg" and "-v" not in cmd:
        cmd = [cmd[0], "-hide_banner", "-v", "error"] + cmd[1:]
    r = subprocess.run(cmd, capture_output=True, text=True)
    if r.returncode != 0:
        tail = (r.stderr or r.stdout or "").strip().splitlines()[-15:]
        die("command failed: " + " ".join(cmd[:6]) + " ...\n" + "\n".join(tail))
    return r.stdout


def probe(path):
    """Return width, height, fps (float), duration (s), has_audio, sample_rate."""
    need("ffprobe")
    if not os.path.exists(path):
        die(f"file not found: {path}")
    out = run(["ffprobe", "-v", "error", "-show_entries",
               "stream=codec_type,width,height,r_frame_rate,sample_rate:format=duration",
               "-of", "json", path])
    j = json.loads(out)
    v = next((s for s in j.get("streams", []) if s.get("codec_type") == "video"), None)
    a = next((s for s in j.get("streams", []) if s.get("codec_type") == "audio"), None)
    if v is None:
        die(f"no video stream in {path}")
    num, den = (v.get("r_frame_rate") or "30/1").split("/")
    fps = float(num) / float(den or 1)
    return {
        "w": int(v["width"]), "h": int(v["height"]), "fps": fps,
        "dur": float(j.get("format", {}).get("duration") or 0),
        "audio": a is not None, "sr": int(a.get("sample_rate", 48000)) if a else 48000,
    }


def count_frames(path):
    out = run(["ffprobe", "-v", "error", "-count_packets", "-select_streams", "v:0",
               "-show_entries", "stream=nb_read_packets", "-of", "csv=p=0", path])
    return int(out.strip().split(",")[0])


def load_words(path):
    """Load a word list in any of the shapes the skill produces or accepts and return
    [{"text", "start", "end"}]. Accepts a flat list with text/word/w keys, or a Whisper-style
    {"segments": [{"words": [...]}]} file."""
    with open(path, encoding="utf-8") as f:
        data = json.load(f)
    if isinstance(data, dict):
        if "words" in data and isinstance(data["words"], list):
            data = data["words"]
        elif "segments" in data:
            data = [w for s in data["segments"] for w in s.get("words", [])]
        else:
            die(f"{path}: expected a list of words or a Whisper JSON with segments")
    out = []
    for w in data:
        t = w.get("text", w.get("word", w.get("w", "")))
        t = str(t).strip()
        if not t:
            continue
        out.append({"text": t, "start": float(w["start"]), "end": float(w["end"])})
    out.sort(key=lambda x: x["start"])
    return out


def save_words(words, path):
    with open(path, "w", encoding="utf-8") as f:
        json.dump(words, f, ensure_ascii=False, indent=0)


def hex_rgb(c, alpha=None):
    """'#1E40AF' or [30,64,175] -> (r, g, b[, a])."""
    if isinstance(c, (list, tuple)):
        t = tuple(int(x) for x in c)
    else:
        c = c.lstrip("#")
        if len(c) == 3:
            c = "".join(ch * 2 for ch in c)
        t = tuple(int(c[i:i + 2], 16) for i in (0, 2, 4))
    if alpha is not None:
        t = t[:3] + (alpha,)
    return t


def ends_sentence(text):
    return text.rstrip("\"'\u201d\u2019)").endswith((".", "?", "!"))


FONT_CANDIDATES = [
    # macOS
    "/System/Library/Fonts/Supplemental/Arial Bold.ttf",
    "/Library/Fonts/Arial Bold.ttf",
    "/System/Library/Fonts/Helvetica.ttc",
    # Linux
    "/usr/share/fonts/truetype/dejavu/DejaVuSans-Bold.ttf",
    "/usr/share/fonts/dejavu/DejaVuSans-Bold.ttf",
    "/usr/share/fonts/truetype/liberation/LiberationSans-Bold.ttf",
    # Windows
    "C:/Windows/Fonts/arialbd.ttf",
    "C:/Windows/Fonts/segoeuib.ttf",
]


def find_font(path=None):
    if path:
        if not os.path.exists(path):
            die(f"font not found: {path}")
        return path
    for p in FONT_CANDIDATES:
        if os.path.exists(p):
            return p
    print("warning: no bold system font found, using Pillow's default font. Pass --font "
          "or set captions.font in the plan to a .ttf/.otf file.", file=sys.stderr)
    return None


def pil_font(path, size):
    from PIL import ImageFont
    if path is None:
        try:
            return ImageFont.load_default(size=size)
        except TypeError:
            return ImageFont.load_default()
    return ImageFont.truetype(path, size)


def require_pillow():
    try:
        import PIL  # noqa: F401
    except ImportError:
        die("Pillow is not installed. Run: python3 -m pip install Pillow")
