# LinkedIn outlier finder

Find LinkedIn posts that performed unusually well for their authors, understand the idea behind them, and develop an original angle for your audience.

A post with 54 reactions may be worth studying when that person normally receives 6. The skill helps you find that difference and asks for your own experience before drafting anything.

## Download and use

[Download the skill ZIP](https://github.com/carocoda/marketing_skills/releases/download/linkedin-outlier-finder-v1.0.0/linkedin-outlier-finder.zip).

Install the `linkedin-outlier-finder` folder using your assistant's skill import or local skills directory. For Claude Code, place it in `.claude/skills/`; for Codex, use `~/.codex/skills/`. If your chat does not support skill installation, supply the Markdown instructions and reference file as context.

Then ask:

> Find this week's outliers in my niche. I help small B2B teams use AI in their marketing. Show what each score is based on and suggest an angle I could develop from my own experience.

The instructions are in English. You can ask for research and drafts in Dutch or another language.

## What you need

- **With Postiv:** connect the [Postiv MCP](https://postiv.ai/mcp) in your assistant's connector settings. The skill searches the inspiration library and labels returned outlier scores as Postiv-reported.
- **Without Postiv:** provide recent posts with dates and results. Include ordinary posts so the comparison is meaningful. A few selected screenshots can support idea research, but usually cannot establish someone's normal performance.

No scripts, API keys in files or additional packages are required by this skill.

## What to expect

Source links, available results, a clearly labelled score or data limitation, and a few ideas you can make your own. You decide which ideas to use and what gets published.

The skill does not promise viral reach. Postiv may return scores without exposing the underlying baseline; those remain vendor-reported rather than independently verified calculations.

## Credits and license

Adapted from the outlier research and pattern-extraction approach in [Postiv's LinkedIn client content skill](https://github.com/postiv-ai/claude-skills), with runtime tool discovery and explicit comparison rules. The original skill is MIT-licensed. See [LICENSE](LICENSE).
