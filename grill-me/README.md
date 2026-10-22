# Grill me

A skill for Claude and ChatGPT that interviews you before it starts on a bigger job. It asks 10 to 15 sharp questions in one go, plays the brief back to you, and only starts building or writing after you say yes. You get a first draft that's close, instead of three rounds of "no, not like that".

**What it does**

- Checks the conversation and your project files first, and never asks what it can already find
- Asks all questions in one numbered message, the most important three at the top
- Gives its own suggestion with every question, so you can answer "ok" or just "3: no, 7: weekly"
- Asks at most 3 follow-up questions where your answers are vague
- Plays back a short brief (goal, audience, core message, proof, format, limits) and waits for your yes
- Keeps it to 3 questions for small jobs

Good for campaigns, videos, websites, decks, email sequences, launch plans and strategy work. It works in any language: it replies in yours.

## Use it

**ChatGPT, any plan**
1. Download `grill-me/SKILL.md`.
2. Open a new chat, drag the file in and type: "Use this skill. Grill me before you write my launch emails."

On a Business, Enterprise or Edu plan you can also install it: Plugins > Skills > Create > Upload, and upload the folder as a ZIP.

**Claude** (web, desktop or mobile)
1. Zip the `grill-me` folder.
2. Go to Settings > Capabilities and switch on **Code execution and file creation**.
3. Go to Customize > Skills > **+** > Create skill > **Upload a skill**, and choose the ZIP.
4. Open a new chat and say: "Grill me first, then write the landing page."

**Claude Code:** copy the `grill-me` folder into `.claude/skills/` (or `~/.claude/skills/`) and restart, then type `/grill-me` or "interview me first". **Codex:** put the folder in `~/.codex/skills/`.

## What it needs

Nothing. No scripts, keys or packages. It works best in a project with your brand guide, notes or earlier work, because it reads those first and asks less.

## Good to know

- Answer only the questions you care about. It goes with its own suggestions for the rest, and marks those in the brief so you can see what you didn't decide.
- It won't start until you approve the brief. Say "go" or "yes" when it looks right.

## License

MIT, see [LICENSE](LICENSE).
