# LinkedIn hook

A skill for Claude and ChatGPT that writes the first two lines of your LinkedIn post: the part people see before "...see more". On mobile that's about 140 characters, and it decides whether anyone reads the rest.

**What it does**

- Asks who the post is for and what it should do (be read, saved, commented on), if you haven't said
- Writes 8 to 10 hooks using at least 5 different mechanics, like "number + result", "contrarian" and "exactly what I use"
- Counts the characters of each hook so it fits before the mobile cut-off
- Picks a top 3 and says in one sentence why each works for your audience
- Checks that the second line leads into the rest of your post

The mechanics come from outlier analyses of large AI and marketing creators: posts that opened this way did 2 to 3.5 times their author's normal results. It writes in the language of your post.

## Use it

**ChatGPT, any plan**
1. Download `linkedin-hook/SKILL.md`.
2. Open a new chat, drag the file in, paste your draft post and type: "Use this skill to write hooks for this post."

On a Business, Enterprise or Edu plan you can also install it: Plugins > Skills > Create > Upload, and upload the folder as a ZIP.

**Claude** (web, desktop or mobile)
1. Zip the `linkedin-hook` folder.
2. Go to Settings > Capabilities and switch on **Code execution and file creation**.
3. Go to Customize > Skills > **+** > Create skill > **Upload a skill**, and choose the ZIP.
4. Open a new chat, paste your post and say: "Write me a better hook."

**Claude Code:** copy the `linkedin-hook` folder into `.claude/skills/` (or `~/.claude/skills/`) and restart, then type `/linkedin-hook`. **Codex:** put the folder in `~/.codex/skills/`.

## What it needs

Nothing. No scripts, keys or packages. Bring your draft post, or at least the topic and what the reader gets out of it.

## Good to know

- A hook can only promise what the post delivers. If your post is thin, the skill will say so instead of writing clickbait.
- It never makes up numbers. Put the real numbers in your post and it can use them.
- The 140 and 210 character cut-offs are approximate: LinkedIn changes them now and then, and line breaks count.

## License

MIT, see [LICENSE](LICENSE).
