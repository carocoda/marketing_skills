# linkedin-infographic

A Claude Code skill that turns a LinkedIn post, a how-to video or a sketch into an
animated infographic: a static 1080x1350 HTML poster with one calm accent animation,
rendered to MP4 (LinkedIn), GIF (email, blog) and a cover PNG.

Requirements: Python 3 with `playwright` (`pip install playwright && playwright install chromium`),
`Pillow`, and `ffmpeg` on the PATH.

## Install

Copy this folder into your project's `.claude/skills/` (so you get
`.claude/skills/linkedin-infographic/SKILL.md`), or into `~/.claude/skills/` to have it
in every project. Restart Claude Code; the skill then triggers on "infographic",
"animated infographic" or "a visual for this post", or via `/linkedin-infographic`.

## How it works

Start with `SKILL.md`. The workflow is: concept and copy in chat → approval → build
`infographic.html` from a style reference and a template → `python3 render.py` → QA at
feed size → deliver.

Made by the team behind [Postiv.ai](https://postiv.ai), the LinkedIn growth platform. The
skill works on its own; if you want Claude to post the result straight to LinkedIn and read
your LinkedIn analytics in the chat, that's the Postiv MCP. Try Postiv free for 7 days: postiv.ai

License: MIT (see LICENSE).
