# Marketing skills for Claude and ChatGPT

Hi, I'm Caro 👋

I build [Postiv.ai](https://postiv.ai) and I do a lot of my marketing with AI, in Claude and
in ChatGPT. This repo is where I share the skills I actually use, free. They're written in the
open `SKILL.md` format, so the same folder works in Claude Cowork & Code, and in ChatGPT Work & Codex. Each one is a complete package: the workflow, the rules that make the output
good, the scripts and templates it needs, and a README.

## Skills

| skill | what it does |
| --- | --- |
| [`linkedin-infographic`](linkedin-infographic/) | Turns a LinkedIn post, a how-to video or a sketch into an animated infographic: a static 1080x1350 poster with one calm accent animation, rendered to MP4 (LinkedIn), GIF (email, blog) and a cover PNG. Includes screenshot sourcing, QA at feed size and publishing notes. |
| [`linkedin-outlier-finder`](linkedin-outlier-finder/) | Finds unusually successful LinkedIn posts, checks the comparison behind the numbers, and helps you develop an original angle. Works with Postiv or supplied post data. [Download ZIP](https://github.com/carocoda/marketing_skills/releases/download/linkedin-outlier-finder-v1.0.0/linkedin-outlier-finder.zip). |
| [`linkedin-profile-check`](linkedin-profile-check/) | Checks your LinkedIn profile as a sales page. Asks a few questions first, gives feedback on your headline, banner and Featured section, writes three new headlines and image prompts for a new banner and Featured images from your own photos and logo, and can plan your first week of posts. Works in any ChatGPT plan: download the `.md` and drag it into a chat. [Download ZIP](https://github.com/carocoda/marketing_skills/releases/download/linkedin-profile-check-v1.0.0/linkedin-profile-check.zip) · [Download .md](https://github.com/carocoda/marketing_skills/releases/download/linkedin-profile-check-v1.0.0/linkedin-profile-check.md). |
| [`grill-me`](grill-me/) | Asks you 10 to 15 sharp questions before a big job, each with a suggested answer, plays the brief back and only starts after your yes. It reads your project files first, so it doesn't ask what it can already find. [Download ZIP](https://github.com/carocoda/marketing_skills/releases/download/grill-me-v1.0.0/grill-me.zip). |
| [`humanizer`](humanizer/) | Removes the signs of AI writing from any draft (30+ patterns, plus Dutch-specific tells), keeps your facts as they are, and can match your own voice from a few samples. Use it as the last step before you publish. [Download ZIP](https://github.com/carocoda/marketing_skills/releases/download/humanizer-v1.0.0/humanizer.zip). |
| [`linkedin-hook`](linkedin-hook/) | Writes 8 to 10 hooks for the two lines before "...see more", built on proven mechanics from outlier posts, counted against the mobile cut-off, with a top 3 and why each one works. [Download ZIP](https://github.com/carocoda/marketing_skills/releases/download/linkedin-hook-v1.0.0/linkedin-hook.zip). |
| [`ad-analyzer`](ad-analyzer/) | Audits your whole Meta ads campaign, from impression to sale: the numbers per ad, the setup, what the pixel really received and the sales on your own checkout or ticket platform, every creative, current benchmarks and the math on what your budget can still buy. Ends with advice in order of impact and a stop rule. Read-only, it never changes your account. Also tears down a single ad, yours or a competitor's. [Download ZIP](https://github.com/carocoda/marketing_skills/releases/download/ad-analyzer-v1.1.0/ad-analyzer.zip). |
| [`ad-edit`](ad-edit/) | Edits a talking-head phone recording into a Reels or feed ad: cuts the "uhs" without audible jumps, warms the voice, adds punch-in zooms, big captions, branded graphics on the spoken words, a music bed and UI sounds, in 9:16 and 4:5. Asks for your brand first and plans before it builds. Runs in Claude Code or Codex. [Download ZIP](https://github.com/carocoda/marketing_skills/releases/download/ad-edit-v1.0.0/ad-edit.zip). |
| [`motion-video`](motion-video/) | Makes looping UI motion videos: one shape morphs through screens, a cursor clicks every change, everything lands on the beat. Asks about your brand, format, voice and music first, gets the script and cost approved, then renders in 16:9, 9:16, 1:1 or 4:5. Works without API keys. Runs in Claude Code or Codex. [Download ZIP](https://github.com/carocoda/marketing_skills/releases/download/motion-video-v1.0.0/motion-video.zip). |
| [`youtube-packaging`](youtube-packaging/) | The upload step for a finished video: title options, two thumbnail prompts that show the payoff instead of repeating the title, and a search-friendly description with links, chapters and hashtags. Asks about your channel and style first. [Download ZIP](https://github.com/carocoda/marketing_skills/releases/download/youtube-packaging-v1.0.0/youtube-packaging.zip). |
| [`youtube-shorts`](youtube-shorts/) | Turns a long YouTube video into a series of standalone shorts for Shorts, Reels, TikTok (9:16) or LinkedIn (16:9). Each one gets its own hook from the video, cuts on pauses, word-by-word captions, a title card, sound effects and an end screen, plus optional animated graphics. Uses ffmpeg, no API keys. [Download ZIP](https://github.com/carocoda/marketing_skills/releases/download/youtube-shorts-v1.0.0/youtube-shorts.zip). |

More coming. Star the repo if you want to know when.

## Install

1. Download this repo (Code → Download ZIP) or clone it.
2. Install the skill folder you want:
   - **Claude Code:** copy it into your project's `.claude/skills/` (or `~/.claude/skills/` for
     every project) and restart Claude Code.
   - **ChatGPT:** open Skills, upload the folder as a skill, save and install it.
   - **Codex:** put it in `~/.codex/skills/`.
3. Ask for what the skill does ("make an infographic for this post") or call it by name.

Each skill's README lists what it needs. Skills that render files (like the infographic) run
scripts on your machine, so use those from Claude Code or Codex; in a plain chat they still do
the thinking and the copy.

## Find me

- YouTube, AI & marketing: [youtube.com/@CarolinaPosma](https://www.youtube.com/@CarolinaPosma)
- YouTube, all things Postiv: [youtube.com/@PostivAI](https://www.youtube.com/@PostivAI)
- Connect with me on LinkedIn: [linkedin.com/in/carolina-posma](https://www.linkedin.com/in/carolina-posma)

Let me know if you have any questions. Open an issue here or send me a message on LinkedIn.

## License

MIT, see [LICENSE](LICENSE). Use it, change it, share it.
