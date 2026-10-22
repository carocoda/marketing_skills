# YouTube packaging

A skill for ChatGPT and Claude for the last step before you upload: the title, the thumbnail and the description. Your video is done; this makes sure people find it and click it.

**What it does**

- Asks about your channel first: niche, audience, faces or not, colours and fonts, text on thumbnails, tone, your standard links, and which image tool you use
- Writes 2 or 3 title options with your search phrase up front, and says which one it would pick
- Writes two thumbnail concepts as copy-paste prompts for your image tool (ChatGPT by default), to use with your own headshot and logos
- Checks that the thumbnail text adds something the title doesn't say, and that the image shows what the viewer wants, not what the video does
- Writes the description: links first, a hook with your search phrase, what you'll learn, chapters and hashtags
- Ends with a short checklist before you upload

It doesn't upload anything. You stay in charge of your channel.

## Use it

**ChatGPT, any plan (Free included)**
1. Download this folder as a ZIP, or at least `SKILL.md` and the two files in `references/`.
2. Open a new chat, drag the files in and type: "Use this skill to package my YouTube video." Add the transcript or a short summary with timestamps.
3. Answer its questions. Have your headshot and any logos ready for the thumbnail.

On a Business, Enterprise or Edu plan you can also install it: Plugins > Skills > Create > Upload, and upload the ZIP.

**Claude** (web, desktop or mobile)
1. Download this folder as a ZIP.
2. Go to Settings > Capabilities and switch on **Code execution and file creation**.
3. Go to Customize > Skills > **+** > Create skill > **Upload a skill**, and choose the ZIP.
4. Open a new chat and say: "Package this video for YouTube," with the transcript.

Claude doesn't make images, so it gives you the thumbnail prompts to paste into ChatGPT or your own image tool.

**Claude Code:** copy the `youtube-packaging` folder into `.claude/skills/` (or `~/.claude/skills/`) and restart. **Codex:** put the folder in `~/.codex/skills/`. In an agent that can read files, point it at the video folder or a transcript; it saves the result as `youtube-package.md`.

## What you need

- A transcript, the script, or a few lines on what the video covers with timestamps. Chapters and numbers only come from there.
- Your headshot (if you want your face on thumbnails) and any logos or screenshots the thumbnail should show.
- An image tool for the thumbnail. ChatGPT image generation works well with the prompts.

No scripts, packages or API keys needed.

## Your channel profile

The first time, it asks eight short questions. Each has a default, so "ok" works. Then it offers to save your answers as `youtube-channel-profile.md` in your project (or as a block to paste into future chats), so the next video goes straight to the work. A blank profile is in `templates/`.

## Good to know

- Image tools sometimes misspell words or change a face. Check every letter, and if the face doesn't look like you, add your real photo afterwards in a design tool like Canva.
- Check the chapter timestamps against your final cut.
- Videos of 3 minutes or less uploaded in vertical or square format become Shorts. Upload tutorials in 16:9.
- If you use the humanizer skill from this repo, it runs it on the description.

## License

MIT. See [LICENSE](LICENSE).
