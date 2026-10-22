# Motion Video

A skill for Claude and ChatGPT that makes looping UI motion videos: one shape morphs through screens, a cursor
clicks, types and drags every change, and everything lands on the beat of the music. With a voice-over, music, UI
sounds and captions if you want them, rendered at 60 fps with motion blur. For product demos, feature launches,
event promos, offers, teasers and ads.

**What it does**

- Asks you a few questions first: what the video is for, where it plays, your format and length, your colours,
  fonts and shape language, the voice and the music. Every question has a default, so "ok" works. It can save your
  answers to `motion-video-profile.md` so the next video skips this step
- Writes the voice-over script, a beat-by-beat plan of what's on screen and a cost estimate, and waits for your yes
  before it makes anything
- Builds the video from a working template in your brand: 16:9, 9:16, 1:1 or 4:5
- Makes the voice one sentence at a time and checks every take with Whisper, because long takes turn robotic and
  names go wrong
- Measures the beat of the music and cuts a seamless loop
- Checks every beat itself before you see it, then renders an mp4, a thumbnail and a light copy to share
- Takes your feedback round by round and changes only what the note touches

## Use it

**Claude Code** (best): copy the `motion-video` folder into `.claude/skills/` (or `~/.claude/skills/`) and restart.
Then ask: "Make a 30 second promo video for our launch."

**Codex**: put the folder in `~/.codex/skills/` and ask the same.

**Claude (web, desktop) and ChatGPT**: you can upload the folder as a skill, but rendering needs ffmpeg and a
headless browser on your own computer. In a plain chat it does the planning: the interview, the script, the beat
plan and the costs. Build and render from Claude Code or Codex.

## What it needs

On your computer, once:

```bash
pip3 install numpy scipy pillow playwright certifi
python3 -m playwright install chromium
brew install ffmpeg            # macOS. Linux: sudo apt install ffmpeg. Windows: winget install ffmpeg
python3 motion-video/scripts/check_env.py
```

Optional:

- `pip3 install faster-whisper` to check voice takes and time captions. It needs a Whisper model (0.5 to 3 GB); the
  skill asks before downloading one.
- An API key for voice and music, as an environment variable or in a `.env` file next to your project (keep `.env`
  out of git):
  - `OPENROUTER_API_KEY`: voice (Gemini TTS) and music (Google Lyria) through OpenRouter. This is the tested path.
  - `GEMINI_API_KEY`: voice only, straight from Google's Gemini API. Built to the public docs; the first takes get
    checked.

Rendering uses Google Fonts by default, so it needs internet, unless you point the skill at local font files.

**Without a key** it still works: free stand-in UI sounds and music are made on your computer, a scratch voice comes
from your Mac's built-in voice (or a hum per word elsewhere) so the timing is right, and you can drop in your own
recordings, your own track, or make a music-only video.

## What it costs

With a key, a few cents per video: a voice take costs well under a cent, a Lyria song about $0.08. A 50 second promo
with every test voice and retake came to about $0.30. The skill always gives the estimate first.

Time: a first version in one to two hours. A full render of 50 seconds takes about five minutes on a recent laptop.

## Good to know

- The default look is neo-brutalist pastel (cream background, black borders, hard shadows). Tell it your brand and
  it uses that instead.
- It only shows real people with their own photos and their OK, never generated faces of real people.
- The price goes on a sticker near the end, not in the first seconds. Say so if you want it differently.
- The stand-in music and scratch voice are for building only; the skill tells you when they're still in.
- Large video files go wherever you keep your videos; the project folder keeps everything to re-render later.

## License

MIT. Use it, change it, share it.
