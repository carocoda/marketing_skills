# Humanizer

A skill for ChatGPT and Claude that takes a draft and removes the things that make it read as AI-written: the "crucial" and "seamless", the em dashes, the "it's not X, it's Y", the groups of three, the "I hope this helps". Then it checks that a person is still audible in the text, because writing with no AI patterns and no voice is just as easy to spot.

Use it as the last step before you publish or send anything.

**What it does**

- Finds more than 30 common AI writing patterns and rewrites them in plain words
- Keeps your facts, names, numbers and links exactly as they were
- Never makes up anecdotes, quotes or numbers to sound more human; it asks you instead
- Runs a second check ("what still gives this away?") and fixes what's left
- Can match your own voice: give it 2 or 3 things you wrote and it copies your habits, not just the absence of AI ones
- Works in any language, with an extra list of Dutch-specific tells

## Use it

**ChatGPT, any plan (Free included)**
1. Download `SKILL.md` from this folder.
2. Open a new chat, drag the file in and type: "Use this skill to humanize the text below," then paste your text.

On a Business, Enterprise or Edu plan you can also install it: Plugins > Skills > Create > Upload, and upload the folder as a ZIP.

**Claude** (web, desktop or mobile)
1. Download this folder as a ZIP.
2. Go to Settings > Capabilities and switch on **Code execution and file creation**.
3. Go to Customize > Skills > **+** > Create skill > **Upload a skill**, and choose the ZIP.
4. Open a new chat, paste your text and say: "Humanize this."

**Claude Code:** copy the `humanizer` folder into `.claude/skills/` (or `~/.claude/skills/`) and restart. **Codex:** put the folder in `~/.codex/skills/`.

Other skills can call it as their final step. In that case it edits the file in place and gives you a short list of what it changed, without asking questions.

## Your voice

The first time, it asks three optional questions: a few samples of your writing, words you never want to see, and whether to keep any em dashes. Say "skip" and it uses a plain, natural voice.

If you answer, it offers to save your answers as `voice.md` in your project. Next time it reads that file and doesn't ask again. In a chat without files, it gives you a short block to paste at the start of a new chat.

## Good to know

- No scripts, packages or API keys needed.
- It won't add detail it doesn't have. If a paragraph needs a real example, it will tell you and ask for one.
- AI detectors are unreliable. This skill aims at text that reads well to people, not at beating a detector score.

## Credits and license

The pattern list is based on [Wikipedia: Signs of AI writing](https://en.wikipedia.org/wiki/Wikipedia:Signs_of_AI_writing), maintained by WikiProject AI Cleanup and shared under CC BY-SA 4.0. The descriptions and examples in this skill are written fresh.

The skill itself is MIT. See [LICENSE](LICENSE).
