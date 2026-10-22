---
name: youtube-packaging
description: Package a finished YouTube video for upload. Writes 2-3 title options, two copy-paste thumbnail prompts for an image tool (ChatGPT image generation by default) that show the payoff instead of repeating the title, and a search-friendly description with links, chapters and hashtags. Interviews the creator about their channel, audience, thumbnail style and tone first, and can save that as a channel profile. Use whenever someone has a video ready and asks for a thumbnail, thumbnail idea or thumbnail prompt, a YouTube title, a YouTube description, chapters, "the YouTube stuff", or says "package this video" or "help me upload this". This is the last step, after the video exists.
---

# YouTube packaging

A video is finished. This skill makes the three things YouTube needs before upload:

1. a **title** (2 or 3 options),
2. a **thumbnail prompt** (two concepts, to paste into an image tool together with the creator's own photo and logos),
3. a **description** (links, hook, what you'll learn, chapters, hashtags).

The title and thumbnail are one unit. The thumbnail does not repeat the title. It shows the payoff the title doesn't mention, and that gap is what earns the click.

Answer in the language the person writes in. Write the title, thumbnail text and description in the language of the video.

## Step 1: the channel profile

Look first for `youtube-channel-profile.md` in the project, or a channel description earlier in the chat. If it exists, read it, say in one line that you're using it, and go to step 2.

If not, ask these in one numbered message, then wait. Each has a default in brackets, so "ok" is a valid answer. Skip any question the conversation or project files already answer.

1. **Channel and niche.** What is the channel about, in one sentence? Link it if you like.
2. **Audience.** Who watches, and what do they want from your videos? [people searching for how-to help on this topic]
3. **Faces.** Do you put your face on thumbnails? If yes, have a headshot ready to upload with the prompt. [yes, my face plus one graphic]
4. **Thumbnail look.** Your colours (hex codes if you have them), and a font feel: bold and blocky, friendly and round, clean and minimal. [dark background, white bold text, one bright accent colour]
5. **Text on thumbnails.** Short text on the image, or none? [yes, 3 words max]
6. **Tone.** How should titles and descriptions sound: plain and helpful, playful, expert and calm, loud? [plain and helpful]
7. **Links.** What goes at the top of every description after the links mentioned in the video: your main offer, your newsletter, a way to reach you? Paste the lines. [only links mentioned in the video]
8. **Image tool.** Where do you make the thumbnail? [ChatGPT image generation]

Optional, only if they bring it up or the profile says so: a **DM word** per video for tracking (see `references/description-guide.md`).

After they answer, offer once: "Want me to save this as `youtube-channel-profile.md` so I don't ask next time?" In a chat without files, give them the profile as a block to paste into future chats. Use `templates/youtube-channel-profile.md` as the format.

## Step 2: know the video

You need:
- the topic in one sentence;
- the main search phrase someone would type to find this video;
- what the viewer ends up with (the outcome), and any real number or result the video mentions;
- every link the video says is "in the description";
- the length, and for videos of about 10 minutes or more, 4 to 8 chapter moments with timestamps.

Get these from a transcript, the script, or by asking. If you can transcribe the video file yourself, do that. If you have nothing but a title idea, ask for a transcript or a 5-line summary with timestamps. Never invent timestamps, numbers or results.

## Step 3: titles

Write 2 or 3 options:
- Main search phrase in the first ~30 characters.
- About 50 to 60 characters, 100 at most. Phones cut titles at roughly 50.
- Curiosity is fine; the promise must be true. A click followed by a quick exit hurts the video.
- At least one plain search-style title ("How to ... in ...") for tutorials.

Say which one you'd pick and why, in one sentence.

## Step 4: thumbnail prompts

Read `references/thumbnail-guide.md`. Write two concepts so the creator can A/B test them (YouTube's Test & Compare, or swap after a few days). Concept A follows their profile (usually face plus one graphic). Concept B is a real alternative (for example graphic only, or a before/after).

Before you hand over a prompt, run two checks out loud in one or two lines each:
- **Overlap test.** Put the title and the thumbnail text side by side. If someone who read the title already knows what the text says, rewrite the text.
- **Direction test.** Does the image show the viewer's wish (more, better, done), or the mechanism or a loss (a number going down, a filter, a funnel)? Draw the wish.

Write each prompt as one copy-paste block, in English (image tools follow English prompts best), for the tool from the profile. Tell the creator which images to upload with it (headshot, logos, a screenshot of the result). If you can generate images yourself in this chat, ask "Shall I make it now?" first.

## Step 5: description

Read `references/description-guide.md` and fill `templates/youtube-package.md`. In short:
1. The link block first: links mentioned in the video, in the order they come up, then the standard lines from the profile.
2. A 2 to 3 line hook with the main search phrase in the first sentence.
3. One short paragraph on what the video walks through.
4. "What you'll learn": 3 to 5 bullets (skip for videos under about 2 minutes).
5. Chapters, only for videos of about 10 minutes or more, starting at `0:00`.
6. A closing line, if the profile has one.
7. 2 or 3 exact-topic hashtags.

## Step 6: humanize and deliver

- Run the description prose through the `humanizer` skill if it's installed. If not, check it yourself: no em dashes, no "unlock", "game changer", "dive in", "in today's world", no "it's not X, it's Y", no groups of three for the sake of it. Links, chapters and hashtags don't need this.
- If you can write files, save everything as `youtube-package.md` next to the video (or in the project) and also show the blocks in chat. Otherwise show them in chat, each in its own copy-paste block.
- End with a short checklist: check the chapter timestamps against the final video, check every word on the generated thumbnail for spelling, check that the face still looks like you, look at the thumbnail at phone size, and upload videos under 3 minutes in 16:9 so YouTube doesn't treat them as a Short.

## Hard rules

- **Never make anything up.** Numbers, results, client names and timestamps come from the video or the creator.
- **Never prescribe a facial expression.** The prompt says to keep the expression from the uploaded photo. The creator picks the photo. Don't ask for "surprised" or "excited", and don't ask for "subtle" either.
- **Never invent a face.** Use the uploaded headshot, or no face.
- **Thumbnail text is not the title.** Run the overlap test every time.
- **Ask before you make.** Wait for the step 1 answers (or "ok") before writing, and ask before generating an image.
- **No overclaiming in titles.** If the video doesn't deliver it, the title doesn't promise it.

## Quick reference

- Thumbnail: 1280 x 720, 16:9, PNG, under 2 MB. 3 words is the sweet spot, 5 the ceiling. Heavy sans-serif with a stroke or a colour block behind it. One focal point, 2 or 3 elements, one arrow at most. Nothing important in the bottom-right corner (the duration stamp) or near the edges.
- Accent colour: not blue, red, white or black, which blend into YouTube's own interface. Orange, amber, yellow, teal and lime stand out.
- Title: search phrase first, about 55 characters, 100 max.
- Description: the first ~100 characters show on mobile before "more". 150 to 300 words for a normal video, 100 to 200 for a short tutorial.
- Chapters: at least 3, first one at `0:00`, each at least 10 seconds.
- Hashtags: 2 or 3 at the end. More than 60 and YouTube ignores all of them.
