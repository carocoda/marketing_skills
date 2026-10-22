#!/usr/bin/env python3
"""Build the finished short from a plan: clip + graphics + captions + sounds + music + end screen.
Plain ffmpeg and Pillow. HyperFrames is only needed to make the animated graphics (.mov with
transparency); without it, the plan can use a Pillow title card and end screen instead.

Usage:
  python3 assemble.py plan.json                 # full build
  python3 assemble.py plan.json --seconds 12    # quick test of the first 12 s, no end screen
  python3 assemble.py plan.json --preview       # also write a small preview next to the output

Plan (paths are relative to the plan file; see templates/plan-9x16.json):
  {
   "src": "work/clip.mp4", "out": "Short 1 - How X works.mp4", "work": "work",
   "brand": {"primary": "#1E40AF", "secondary": "#3B6BF0", "ink": "#0B1220", "bg": "#F6F5F1", "font": null},
   "captions": {"words": "work/words.json", "style": "bold", "highlight": "#FFD400"},
   "title": {"text": "How X works", "sub": "in 60 seconds", "t0": 0, "t1": 4.5},
       or   {"movie": "hf/title/renders/title.mov", "t0": 0, "t1": 4.6, "pos": [90, 200], "w": 900},
   "elements": [{"path": "hf/steps/renders/steps.mov", "t0": 14.0, "t1": 24.0, "pos": [90, 260], "w": 900, "fade": 0.3}],
   "sfx": [{"t": 0.25, "path": "sfx/ding.wav", "gain": 0.35}],
   "music": {"path": "music/bed.mp3", "gain": 0.04},
   "end_screen": {"headline": "Watch the full video on YouTube", "title": "...", "line": "youtube.com/@you",
                  "cta": "Link in the comments", "duration": 4.0}
       or   {"movie": "hf/end-screen/renders/end.mp4"}
  }
"""
import argparse
import json
import os
import shutil
import sys
import wave

HERE = os.path.dirname(os.path.abspath(__file__))
sys.path.insert(0, HERE)
import captions as caps  # noqa: E402
import cards  # noqa: E402
from common import count_frames, die, load_words, need, probe, run  # noqa: E402

SR = 48000


def silent_wav(path, n_samples):
    with wave.open(path, "wb") as w:
        w.setnchannels(2); w.setsampwidth(2); w.setframerate(SR)
        w.writeframes(b"\x00\x00\x00\x00" * n_samples)


def main():
    ap = argparse.ArgumentParser(description=__doc__, formatter_class=argparse.RawDescriptionHelpFormatter)
    ap.add_argument("plan")
    ap.add_argument("--seconds", type=float, help="test render of the first N seconds, no end screen")
    ap.add_argument("--preview", action="store_true", help="also write a small preview mp4")
    ap.add_argument("--crf", type=int, default=17)
    ap.add_argument("--preset", default="fast")
    a = ap.parse_args()
    need("ffmpeg")

    base = os.path.dirname(os.path.abspath(a.plan))
    plan = json.load(open(a.plan, encoding="utf-8"))
    P = lambda p: p if (p is None or os.path.isabs(p)) else os.path.join(base, p)  # noqa: E731

    src = P(plan["src"])
    info = probe(src)
    if not info["audio"]:
        die("the clip has no audio")
    W, H = info["w"], info["h"]
    fps = round(info["fps"], 3)
    dur = info["dur"] if not a.seconds else min(a.seconds, info["dur"])
    nf_main = int(round(dur * fps))
    dur = nf_main / fps
    work = P(plan.get("work", "work"))
    os.makedirs(work, exist_ok=True)
    out = P(plan["out"])
    if a.seconds:
        out = os.path.splitext(out)[0] + f"_test{int(a.seconds)}s.mp4"
    os.makedirs(os.path.dirname(out) or ".", exist_ok=True)
    b = plan.get("brand", {})

    inputs = ["-i", src]
    vf, af = [], []
    cur = "0:v"
    k = 1

    # --- overlays: title + elements (movies or images), in time order
    overlays = []
    t = plan.get("title")
    if t:
        if t.get("movie"):
            overlays.append(dict(t, path=t["movie"]))
        elif t.get("text"):
            img, x, y = cards.title_card(t["text"], t.get("sub", ""), W, H, b)
            tp = os.path.join(work, "title_card.png")
            img.save(tp)
            overlays.append({"path": tp, "t0": t.get("t0", 0.0), "t1": t.get("t1", 4.5), "pos": [x, y],
                             "fade": t.get("fade", 0.25), "image": True})
    for e in plan.get("elements", []):
        overlays.append(e)
    for e in sorted(overlays, key=lambda e: e["t0"]):
        t0, t1 = float(e["t0"]), min(float(e["t1"]), dur)
        if t0 >= dur:
            continue
        path = P(e["path"])
        if not os.path.exists(path):
            die(f"element not found: {path}")
        d = t1 - t0
        fade = float(e.get("fade", 0.3))
        is_img = e.get("image") or path.lower().endswith((".png", ".jpg", ".jpeg", ".webp"))
        if is_img:
            inputs += ["-loop", "1", "-framerate", f"{fps:g}", "-t", f"{d:.4f}", "-i", path]
        else:
            inputs += ["-i", path]
        x, y = e.get("pos", [0, 0])
        chain = f"[{k}:v]fps={fps:g},format=rgba"
        if e.get("w"):
            chain += f",scale={int(e['w'])}:-2:flags=lanczos"
        # hold the last frame if the movie is shorter than the slot, then cut to the slot
        chain += f",tpad=stop_mode=clone:stop_duration={d:.3f},trim=duration={d:.4f}"
        chain += f",fade=t=in:st=0:d={fade}:alpha=1,fade=t=out:st={max(0, d - 0.5):.3f}:d=0.5:alpha=1"
        chain += f",setpts=PTS-STARTPTS+{t0:.4f}/TB[e{k}]"
        vf.append(chain)
        vf.append(f"[{cur}][e{k}]overlay={int(x)}:{int(y)}:enable='between(t,{t0:.3f},{t1:.3f})'"
                  f":eof_action=pass:format=auto[o{k}]")
        cur = f"o{k}"
        k += 1

    # --- captions on top
    c = plan.get("captions")
    if c and c.get("words"):
        words = load_words(P(c["words"]))
        lst, band_y = caps.render(words, dict(c, font=P(c.get("font"))), W, H, fps, dur,
                                  os.path.join(work, "captions"))
        inputs += ["-f", "concat", "-safe", "0", "-i", lst]
        vf.append(f"[{k}:v]fps={fps:g},format=rgba[cap]")
        vf.append(f"[{cur}][cap]overlay=0:{band_y}:eof_action=pass:format=auto[ocap]")
        cur = "ocap"
        k += 1
    vf.append(f"[{cur}]format=yuv420p,trim=duration={dur:.4f},setpts=PTS-STARTPTS[vout]")

    # --- audio: voice + sfx + music bed
    af.append(f"[0:a]aformat=sample_rates={SR}:channel_layouts=stereo,atrim=duration={dur:.4f}[voice]")
    mix = ["[voice]"]
    for s in plan.get("sfx", []):
        if float(s["t"]) >= dur:
            continue
        p = P(s["path"])
        if not os.path.exists(p):
            die(f"sound not found: {p}")
        inputs += ["-i", p]
        ms = int(round(float(s["t"]) * 1000))
        af.append(f"[{k}:a]aformat=sample_rates={SR}:channel_layouts=stereo,volume={float(s.get('gain', 0.3))},"
                  f"adelay={ms}|{ms}[s{k}]")
        mix.append(f"[s{k}]")
        k += 1
    m = plan.get("music")
    if m and m.get("path"):
        p = P(m["path"])
        if not os.path.exists(p):
            die(f"music not found: {p}")
        inputs += ["-stream_loop", "-1", "-i", p]
        fi, fo = float(m.get("fade_in", 1.5)), float(m.get("fade_out", 2.5))
        af.append(f"[{k}:a]aformat=sample_rates={SR}:channel_layouts=stereo,atrim=duration={dur:.4f},"
                  f"volume={float(m.get('gain', 0.04))},afade=t=in:d={fi},"
                  f"afade=t=out:st={max(0, dur - fo):.3f}:d={fo}[mus]")
        mix.append("[mus]")
        k += 1
    if len(mix) > 1:
        af.append("".join(mix) + f"amix=inputs={len(mix)}:duration=first:normalize=0,alimiter=limit=0.97[aout]")
    else:
        af.append("[voice]anull[aout]")

    stage = os.path.join(work, "stage.mov")
    run(["ffmpeg", "-y"] + inputs + ["-filter_complex", ";".join(vf + af), "-map", "[vout]", "-map", "[aout]",
         "-frames:v", str(nf_main), "-c:v", "libx264", "-preset", a.preset, "-crf", str(a.crf),
         "-pix_fmt", "yuv420p", "-r", f"{fps:g}", "-c:a", "pcm_s16le", "-ar", str(SR), "-ac", "2", stage])
    got_main = count_frames(stage)

    # --- end screen, appended frame-locked; audio stays PCM until the single AAC encode
    es = plan.get("end_screen")
    nf_end = 0
    if es and not a.seconds:
        ev = os.path.join(work, "end_v.mp4")
        if es.get("movie"):
            mp = P(es["movie"])
            edur = probe(mp)["dur"]
            nf_end = int(round(edur * fps))
            run(["ffmpeg", "-y", "-i", mp, "-an", "-vf",
                 f"scale={W}:{H}:force_original_aspect_ratio=decrease,pad={W}:{H}:(ow-iw)/2:(oh-ih)/2,"
                 f"fps={fps:g},fade=t=in:st=0:d=0.25,format=yuv420p",
                 "-frames:v", str(nf_end), "-c:v", "libx264", "-preset", a.preset, "-crf", str(a.crf),
                 "-pix_fmt", "yuv420p", "-r", f"{fps:g}", ev])
        else:
            img = cards.end_screen(W, H, es.get("headline", "Watch the full video on YouTube"),
                                   es.get("title", ""), es.get("line", ""), es.get("cta", "Link in the comments"),
                                   b, P(es.get("logo")))
            ep = os.path.join(work, "end_screen.png")
            img.convert("RGB").save(ep)
            nf_end = int(round(float(es.get("duration", 4.0)) * fps))
            run(["ffmpeg", "-y", "-loop", "1", "-framerate", f"{fps:g}", "-i", ep, "-vf",
                 "fade=t=in:st=0:d=0.3,format=yuv420p", "-frames:v", str(nf_end), "-c:v", "libx264",
                 "-preset", a.preset, "-crf", str(a.crf), "-pix_fmt", "yuv420p", "-r", f"{fps:g}", ev])
        nf_end = count_frames(ev)
        ew = os.path.join(work, "end_a.wav")
        silent_wav(ew, int(round(nf_end * SR / fps)))
        em = os.path.join(work, "end.mov")
        run(["ffmpeg", "-y", "-i", ev, "-i", ew, "-c:v", "copy", "-c:a", "pcm_s16le", "-ar", str(SR), "-ac", "2", em])
        lst = os.path.join(work, "join.txt")
        with open(lst, "w") as f:
            f.write(f"file '{stage}'\nfile '{em}'\n")
        run(["ffmpeg", "-y", "-f", "concat", "-safe", "0", "-i", lst, "-c:v", "copy", "-c:a", "aac",
             "-b:a", "192k", "-ar", str(SR), "-movflags", "+faststart", out])
    else:
        run(["ffmpeg", "-y", "-i", stage, "-c:v", "copy", "-c:a", "aac", "-b:a", "192k", "-ar", str(SR),
             "-movflags", "+faststart", out])

    got = count_frames(out)
    want = nf_main + nf_end
    ok = got == want and got_main == nf_main
    print(f"{'DONE' if ok else 'CHECK'} {out}: {W}x{H} {fps:g}fps, {got} frames = {got / fps:.2f}s "
          f"(clip {got_main}/{nf_main}, end screen {nf_end}){'' if ok else '  <- frame count off'}")
    if a.preview:
        pv = os.path.splitext(out)[0] + "_preview.mp4"
        scale = "scale=-2:960" if H > W else "scale=1280:-2"
        run(["ffmpeg", "-y", "-i", out, "-vf", scale, "-c:v", "libx264", "-preset", "fast", "-crf", "26",
             "-c:a", "aac", "-b:a", "128k", "-movflags", "+faststart", pv])
        print(f"preview {pv}")
    if not ok:
        sys.exit(2)


if __name__ == "__main__":
    if shutil.which("ffmpeg") is None:
        need("ffmpeg")
    main()
