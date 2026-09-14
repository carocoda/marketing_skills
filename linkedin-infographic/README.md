# linkedin-infographic

A skill for Claude and ChatGPT that turns a LinkedIn post, a how-to video or a sketch into an
animated infographic: a static 1080x1350 HTML poster with one calm accent animation,
rendered to MP4 (LinkedIn), GIF (email, blog) and a cover PNG.

Requirements: Python 3 with `playwright` (`pip install playwright && playwright install chromium`),
`Pillow`, and `ffmpeg` on the PATH.

## Install

This is a standard `SKILL.md` skill (the open Agent Skills format), so it works in both
Claude and ChatGPT:

- **Claude Code:** copy this folder into your project's `.claude/skills/` (so you get
  `.claude/skills/linkedin-infographic/SKILL.md`), or into `~/.claude/skills/` for every
  project. Restart Claude Code.
- **ChatGPT:** open Skills, upload this folder as a skill, save and install it.
- **Codex (CLI or app):** put the folder in your Codex skills directory (`~/.codex/skills/`).

Then ask for "an infographic for this post" or call the skill by name. The render step runs
Playwright and ffmpeg on your machine, so use it from an agent that can run scripts (Claude
Code or Codex); in a plain chat the skill still does the concept and copy.

## How it works

Start with `SKILL.md`. The workflow is: concept and copy in chat → approval → build
`infographic.html` from a style reference and a template → `python3 render.py` → QA at
feed size → deliver.

Made by the team behind [Postiv.ai](https://postiv.ai), the LinkedIn growth platform. The
skill works on its own; if you want Claude to post the result straight to LinkedIn and read
your LinkedIn analytics in the chat, that's the Postiv MCP. Try Postiv free for 7 days: postiv.ai

License: MIT (see LICENSE).
