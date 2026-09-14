#!/usr/bin/env python3
"""
Render an animated infographic to GIF + MP4 + cover PNG.
Copy this into content/animated-infographics/<slug>/ next to infographic.html,
then set SLUG and DURATION_MS (must match window.DURATION_MS in the HTML).

Pipeline: static HTML poster + seek(ms) accent loop -> Playwright frames -> ffmpeg.
Usage: python3 render.py
"""
import subprocess, shutil
from pathlib import Path
from playwright.sync_api import sync_playwright

ROOT = Path(__file__).parent
HTML = ROOT / "infographic.html"
FRAMES = ROOT / "frames"

SLUG = "my-infographic"   # <-- output basename
DURATION_MS = 5000        # <-- one seamless loop; must match the HTML
FPS = 20
WIDTH, HEIGHT = 1080, 1350
SCALE = 2                 # retina render for crisp text

OUT_GIF = ROOT / f"{SLUG}.gif"
OUT_MP4 = ROOT / f"{SLUG}.mp4"
OUT_PNG = ROOT / f"{SLUG}-cover.png"

def capture_frames():
    if FRAMES.exists():
        shutil.rmtree(FRAMES)
    FRAMES.mkdir()
    n_frames = int(DURATION_MS / 1000 * FPS)
    with sync_playwright() as pw:
        browser = pw.chromium.launch()
        page = browser.new_page(
            viewport={"width": WIDTH, "height": HEIGHT},
            device_scale_factor=SCALE,
        )
        page.goto(HTML.as_uri())
        page.wait_for_load_state("networkidle")
        page.evaluate("document.fonts.ready.then(() => true)")
        page.wait_for_timeout(400)
        for i in range(n_frames):
            t = i / FPS * 1000
            page.evaluate(f"window.seek({t})")
            page.screenshot(path=str(FRAMES / f"frame_{i:04d}.png"))
            if i % 40 == 0:
                print(f"  frame {i}/{n_frames}")
        page.evaluate("window.seek(0)")  # poster is static; t=0 = neutral cover
        page.screenshot(path=str(OUT_PNG))
        browser.close()
    print(f"captured {n_frames} frames + cover")

def assemble():
    subprocess.run([
        "ffmpeg", "-y", "-framerate", str(FPS), "-i", str(FRAMES / "frame_%04d.png"),
        "-vf", "scale=720:-1:flags=lanczos,split[a][b];[a]palettegen=max_colors=160[p];[b][p]paletteuse=dither=bayer:bayer_scale=5",
        "-loop", "0", str(OUT_GIF),
    ], check=True, capture_output=True)
    subprocess.run([
        "ffmpeg", "-y", "-framerate", str(FPS), "-i", str(FRAMES / "frame_%04d.png"),
        "-vf", f"scale={WIDTH}:{HEIGHT}:flags=lanczos",
        "-c:v", "libx264", "-crf", "18", "-pix_fmt", "yuv420p", "-movflags", "+faststart",
        str(OUT_MP4),
    ], check=True, capture_output=True)
    for f in (OUT_GIF, OUT_MP4, OUT_PNG):
        print(f"{f.name}: {f.stat().st_size / 1024 / 1024:.2f} MB")

if __name__ == "__main__":
    capture_frames()
    assemble()
    print("done")
