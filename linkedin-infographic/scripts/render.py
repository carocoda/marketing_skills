#!/usr/bin/env python3
"""
Render an animated infographic to a cover PNG, an MP4 and two GIFs.

Copy this next to infographic.html (any template from this skill) and run:

  python3 render.py --slug my-poster --duration 12000
  python3 render.py --slug my-poster --duration 5000 --out ./renders --html poster.html

The page must expose window.seek(ms) (both harnesses in references/pipeline.md do). If it also sets
window.READY, the render waits until it is true (the motion cheat sheet uses this).

What you get (in --out):
  <slug>-cover.png       seek(0) at 2x: the complete poster, also the still fallback
  <slug>.mp4             30 fps, 1080x1350: a LinkedIn video post, or a backup
  <slug>-linkedin.gif    1080x1350, 20 fps, never more than 250 frames: a LinkedIn IMAGE post that plays
                         (LinkedIn's image API takes GIFs up to 250 frames)
  <slug>-email.gif       720 wide, 12 fps, small: email, blog, docs
It also prints a seam check (first frame vs last frame) so you know the loop is seamless.
"""
import argparse
import shutil
import subprocess
from pathlib import Path

from playwright.sync_api import sync_playwright

ROOT = Path(__file__).parent
WIDTH, HEIGHT, SCALE = 1080, 1350, 2          # render at 2x for crisp text, scale down at the end
MP4_FPS, GIF_FPS, EMAIL_FPS = 30, 20, 12
LINKEDIN_MAX_FRAMES = 250

ap = argparse.ArgumentParser()
ap.add_argument("--slug", default="my-infographic")
ap.add_argument("--duration", type=int, default=5000, help="one seamless loop in ms; must match the HTML")
ap.add_argument("--html", default="infographic.html")
ap.add_argument("--out", default=".", help="output folder (video files can get big: keep them out of git)")
ap.add_argument("--keep-frames", action="store_true")
a = ap.parse_args()

HTML = (ROOT / a.html).resolve()
OUT = Path(a.out).expanduser().resolve()
OUT.mkdir(parents=True, exist_ok=True)
FRAMES = OUT / "_frames"
cover, mp4, gif_li, gif_mail = (OUT / f"{a.slug}{s}" for s in ("-cover.png", ".mp4", "-linkedin.gif", "-email.gif"))


def capture():
    if FRAMES.exists():
        shutil.rmtree(FRAMES)
    FRAMES.mkdir(parents=True)
    n = round(a.duration / 1000 * MP4_FPS)
    with sync_playwright() as pw:
        browser = pw.chromium.launch()
        page = browser.new_page(viewport={"width": WIDTH, "height": HEIGHT}, device_scale_factor=SCALE)
        page.goto(HTML.as_uri())
        page.wait_for_load_state("networkidle")
        page.evaluate("document.fonts.ready.then(() => true)")
        page.wait_for_function("typeof window.READY === 'undefined' || window.READY === true", timeout=30000)
        page.wait_for_timeout(300)
        for i in range(n):
            page.evaluate(f"window.seek({i / MP4_FPS * 1000})")
            page.screenshot(path=str(FRAMES / f"frame_{i:04d}.png"))
            if i % 60 == 0:
                print(f"  frame {i}/{n}")
        page.evaluate("window.seek(0)")
        page.screenshot(path=str(cover))
        browser.close()
    return n


def ffmpeg(*args):
    subprocess.run(["ffmpeg", "-y", "-loglevel", "error", *args], check=True)


def assemble(n):
    src = ["-framerate", str(MP4_FPS), "-i", str(FRAMES / "frame_%04d.png")]
    ffmpeg(*src, "-vf", f"scale={WIDTH}:{HEIGHT}:flags=lanczos", "-c:v", "libx264", "-crf", "18",
           "-pix_fmt", "yuv420p", "-movflags", "+faststart", str(mp4))
    # LinkedIn GIF: full size, at most 250 frames; diff-based palette keeps a mostly static poster small
    fps = min(GIF_FPS, int(LINKEDIN_MAX_FRAMES / (a.duration / 1000)))
    ffmpeg(*src, "-vf", f"fps={fps},scale={WIDTH}:{HEIGHT}:flags=lanczos,split[a][b];[a]palettegen=max_colors=256:stats_mode=diff[p];"
           "[b][p]paletteuse=dither=bayer:bayer_scale=4:diff_mode=rectangle", "-loop", "0", str(gif_li))
    ffmpeg(*src, "-vf", f"fps={EMAIL_FPS},scale=720:-1:flags=lanczos,split[a][b];[a]palettegen=max_colors=160:stats_mode=diff[p];"
           "[b][p]paletteuse=dither=bayer:bayer_scale=5:diff_mode=rectangle", "-loop", "0", str(gif_mail))
    try:
        from PIL import Image, ImageChops, ImageStat
        first, last = (Image.open(FRAMES / f"frame_{i:04d}.png").convert("L") for i in (0, n - 1))
        diff = ImageStat.Stat(ImageChops.difference(first, last)).mean[0]   # the last frame flows into the first
        frames = Image.open(gif_li).n_frames
        print(f"seam: mean pixel diff last -> first frame {diff:.2f} ({'OK' if diff < 1 else 'check the loop: something is not back at its start state'})")
        print(f"linkedin gif: {frames} frames at {fps} fps" + ("" if frames <= LINKEDIN_MAX_FRAMES else "  !! over 250 frames"))
    except ImportError:
        pass
    for f in (cover, mp4, gif_li, gif_mail):
        print(f"{f.name}: {f.stat().st_size / 1024 / 1024:.2f} MB")


if __name__ == "__main__":
    n = capture()
    assemble(n)
    if not a.keep_frames:
        shutil.rmtree(FRAMES)
    print("done")
