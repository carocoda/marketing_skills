#!/usr/bin/env python3
"""
Prepare a video ad for analysis: basic info, frames and a timestamped transcript.

Writes into OUT_DIR (never next to the original):
  info.json         duration, size, aspect ratio, fps, has_audio
  frames/f_001.jpg  1 frame per second (configurable with --fps)
  hook/hook_01.jpg  the first seconds at a higher rate (--hook-seconds, --hook-fps)
  transcript.txt    "[  0.0] text" per segment, or a note why there is none

Transcription, in this order:
  1. faster-whisper (pip install faster-whisper)
  2. the openai-whisper CLI (pip install openai-whisper), if on PATH
  3. none: frames only, and transcript.txt says so

Usage:
  python3 extract.py AD.mp4 --out ./ad-analysis/my-ad
  python3 extract.py AD.mp4 --out OUT --lang nl --model large-v3
  python3 extract.py AD.mp4 --out OUT --no-transcript

Needs ffmpeg and ffprobe on PATH.
"""
import argparse
import json
import shutil
import subprocess
import sys
import tempfile
from pathlib import Path


def die(msg):
    print(f"error: {msg}", file=sys.stderr)
    sys.exit(1)


def probe(video):
    cmd = ["ffprobe", "-v", "error", "-show_entries",
           "format=duration:stream=codec_type,width,height,avg_frame_rate",
           "-of", "json", str(video)]
    res = subprocess.run(cmd, capture_output=True, text=True)
    if res.returncode != 0:
        die(f"ffprobe could not read the file: {res.stderr.strip()}")
    data = json.loads(res.stdout)
    streams = data.get("streams", [])
    v = next((s for s in streams if s.get("codec_type") == "video"), None)
    if v is None:
        die("no video stream found (is this an image? then just look at it)")
    w, h = int(v.get("width", 0)), int(v.get("height", 0))
    fps = v.get("avg_frame_rate", "0/1")
    try:
        n, d = fps.split("/")
        fps = round(float(n) / float(d), 2) if float(d) else None
    except ValueError:
        fps = None
    ratio = w / h if h else 0
    named = min({"9:16": 9 / 16, "4:5": 4 / 5, "1:1": 1.0, "16:9": 16 / 9}.items(),
                key=lambda kv: abs(kv[1] - ratio))[0] if ratio else "unknown"
    return {
        "file": str(video),
        "duration_s": round(float(data.get("format", {}).get("duration", 0)), 2),
        "width": w, "height": h,
        "aspect": f"{w}x{h} (closest to {named})",
        "fps": fps,
        "has_audio": any(s.get("codec_type") == "audio" for s in streams),
    }


def ffmpeg(args):
    res = subprocess.run(["ffmpeg", "-v", "error", "-y", *args], capture_output=True, text=True)
    if res.returncode != 0:
        die(f"ffmpeg failed: {res.stderr.strip()}")


def extract_frames(video, out, fps, hook_seconds, hook_fps, width):
    frames, hook = out / "frames", out / "hook"
    frames.mkdir(parents=True, exist_ok=True)
    hook.mkdir(parents=True, exist_ok=True)
    ffmpeg(["-i", str(video), "-vf", f"fps={fps},scale={width}:-2", str(frames / "f_%03d.jpg")])
    ffmpeg(["-ss", "0", "-t", str(hook_seconds), "-i", str(video),
            "-vf", f"fps={hook_fps},scale={width}:-2", str(hook / "hook_%02d.jpg")])
    return len(list(frames.glob("*.jpg"))), len(list(hook.glob("*.jpg")))


def fmt(segments):
    # Drop punctuation-only segments: whisper sometimes "hears" dots in music or tones.
    return "\n".join(f"[{start:5.1f}] {text.strip()}" for start, text in segments
                     if any(ch.isalnum() for ch in text))


def with_faster_whisper(video, lang, model_name):
    try:
        from faster_whisper import WhisperModel
    except ImportError:
        return None
    print(f"transcribing with faster-whisper ({model_name})...", file=sys.stderr)
    model = WhisperModel(model_name, device="cpu", compute_type="int8")
    segs, info = model.transcribe(str(video), language=lang)
    text = fmt((s.start, s.text) for s in segs)
    return text, f"faster-whisper {model_name}, language {info.language}"


def with_whisper_cli(video, lang, model_name):
    exe = shutil.which("whisper")
    if not exe:
        return None
    # Unknown names (e.g. a faster-whisper-only model) fall back to a safe default.
    known = {"tiny", "base", "small", "medium", "large", "large-v1", "large-v2", "large-v3",
             "turbo", "tiny.en", "base.en", "small.en", "medium.en"}
    cli_model = model_name if model_name in known else "small"
    print(f"transcribing with the whisper CLI ({cli_model})...", file=sys.stderr)
    with tempfile.TemporaryDirectory() as tmp:
        cmd = [exe, str(video), "--model", cli_model, "--output_format", "json",
               "--output_dir", tmp, "--fp16", "False"]
        if lang:
            cmd += ["--language", lang]
        res = subprocess.run(cmd, capture_output=True, text=True)
        files = list(Path(tmp).glob("*.json"))
        if res.returncode != 0 or not files:
            print(f"whisper CLI failed: {res.stderr.strip()[-500:]}", file=sys.stderr)
            return None
        data = json.loads(files[0].read_text())
    text = fmt((s["start"], s["text"]) for s in data.get("segments", []))
    return text, f"whisper CLI {cli_model}, language {data.get('language', lang or 'auto')}"


def transcribe(video, out, lang, model_name, has_audio):
    target = out / "transcript.txt"
    if not has_audio:
        target.write_text("NO TRANSCRIPT: the video has no audio track. Work from the frames.\n")
        return "no audio track"
    for engine in (with_faster_whisper, with_whisper_cli):
        result = engine(video, lang, model_name)
        if result is not None:
            text, used = result
            body = text if text else "(no speech detected: music only, or silent)"
            target.write_text(f"# {used}\n{body}\n")
            return used
    target.write_text(
        "NO TRANSCRIPT: no transcription tool is installed.\n"
        "Install one with `pip install faster-whisper` (preferred) or `pip install openai-whisper`,\n"
        "or work from the frames only and say so in the report.\n")
    return "none installed"


def main():
    p = argparse.ArgumentParser(description="Extract info, frames and a transcript from a video ad.")
    p.add_argument("video", help="path to the video file")
    p.add_argument("--out", required=True, help="output folder (created if missing)")
    p.add_argument("--fps", type=float, default=1, help="frames per second for the overview (default 1)")
    p.add_argument("--hook-seconds", type=float, default=3, help="length of the hook segment (default 3)")
    p.add_argument("--hook-fps", type=float, default=4, help="frames per second in the hook (default 4)")
    p.add_argument("--width", type=int, default=540, help="frame width in pixels (default 540)")
    p.add_argument("--lang", default=None,
                   help="language code like en, nl, de. Default: auto-detect from the ad")
    p.add_argument("--model", default="small",
                   help="whisper model: small (default, fast), medium, large-v3 (best, big download)")
    p.add_argument("--no-transcript", action="store_true", help="skip transcription")
    a = p.parse_args()

    for tool in ("ffmpeg", "ffprobe"):
        if not shutil.which(tool):
            die(f"{tool} not found. Install ffmpeg (macOS: brew install ffmpeg, "
                "Ubuntu: sudo apt install ffmpeg, Windows: winget install ffmpeg)")
    video = Path(a.video).expanduser().resolve()
    if not video.is_file():
        die(f"file not found: {video}")
    out = Path(a.out).expanduser().resolve()
    if out == video.parent:
        die("choose an output folder that is not the folder of the original video")
    out.mkdir(parents=True, exist_ok=True)

    info = probe(video)
    n_frames, n_hook = extract_frames(video, out, a.fps, a.hook_seconds, a.hook_fps, a.width)
    info["frames"], info["hook_frames"] = n_frames, n_hook
    if a.no_transcript:
        (out / "transcript.txt").write_text("NO TRANSCRIPT: skipped on request.\n")
        info["transcript"] = "skipped"
    else:
        info["transcript"] = transcribe(video, out, a.lang, a.model, info["has_audio"])
    (out / "info.json").write_text(json.dumps(info, indent=2))
    print(json.dumps(info, indent=2))


if __name__ == "__main__":
    main()
