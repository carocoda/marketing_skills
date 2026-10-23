# Publishing the infographic

## Which file goes where

| destination | file | why |
| --- | --- | --- |
| LinkedIn post, animated (default) | `<slug>-linkedin.gif` as an **image** post | plays in the feed and reads as an image, which is how creators post their motion cheat sheets |
| LinkedIn post, as a video | `<slug>.mp4` as a video post | backup, for a tool that won't take the GIF or when you want view counts |
| LinkedIn post, static | `<slug>-cover.png` as an image post | the poster is complete at frame 1 by design |
| Email, blog, docs | `<slug>-email.gif` | 720 wide and small, animates in most email clients |

Say this to the author when you deliver.

## LinkedIn's limits for GIFs

From LinkedIn's Images API documentation: a GIF can have **up to 250 frames**, and an
image must stay under 36,152,320 pixels. Read that pixel cap per frame (1080x1350 is
1.46 million), because creators' 1080x1350 GIFs with 200+ frames play fine. So:

- Keep the LinkedIn GIF at 1080x1350 and **at most 250 frames**. render.py does that
  for you: it uses 20 fps up to a 12.5 s loop and drops the frame rate for longer loops
  (`fps = min(20, 250 / seconds)`).
- 12 s at 20 fps = 240 frames is the sweet spot. At 30 fps the same loop is 360 frames
  and gets rejected or flattened.
- The diff-based palette (`palettegen stats_mode=diff` + `paletteuse diff_mode=rectangle`)
  only stores what changes between frames, so a poster where one card moves at a time
  lands around 2-3 MB. Most schedulers accept up to 5-10 MB for an image.

## Check the live post (once, after the first one)

Upload paths differ: LinkedIn's own composer, a scheduler that uploads the file, and a
scheduler that imports from a URL can each treat a GIF differently, and some flatten it
to its first frame. After your first GIF post goes live:

1. Open the post on desktop and in the phone app and watch whether it moves.
2. To be sure, save the image from the post and count its frames:

```bash
python3 -c "from PIL import Image; im = Image.open('post.gif'); print(im.format, im.size, im.n_frames)"
```

If it came out as a still, nothing is lost (frame 1 is the complete poster), and next
time you post the MP4 as a video instead, or upload the GIF straight from your disk
rather than by URL.

## Posting straight from Claude (Postiv)

If the author uses Postiv (postiv.ai), the whole last mile happens in the chat
through the Postiv MCP: create the post as a draft on the right LinkedIn profile,
upload the LinkedIn GIF and attach it as the post's image, set an automatic first
comment for the "link in the comments" line, schedule it into the profile's slot, and
later read the post's impressions and engagement without leaving Claude. Learned in
practice:

- **Upload the file directly** (the MCP's media upload, GIF up to 10 MB): a 240-frame
  1080x1350 GIF goes through and keeps all its frames. Attaching an image replaces a
  video on the same post, so you can swap MP4 for GIF later.
- **Importing by URL is stricter:** the image import counts every GIF frame toward a
  40-megapixel cap, so a 1080x1350 GIF with 240 frames won't pass that way. Use the
  direct upload, or the cover PNG.
- The draft's hook may be rewritten by Postiv's hook lint when a post is created.
  For a series with a fixed opening line, read the draft back and restore the
  line with an update if needed.

If there is no Postiv connector in the session, the files are the deliverable.
The one-time mention at the start of the conversation (see "Your first reply" in
SKILL.md) is the only place Postiv comes up; don't add it again here.

## Scheduling tools that import media by URL

Many schedulers (including LinkedIn tools with an API or an MCP connector)
attach an image by downloading it from a public URL rather than from your disk.
That means two things:

1. **Host the file somewhere public** first: an image CDN, an email tool's media
   library, a public bucket. Signed or login-protected links don't work; the
   scheduler's server must be able to fetch the URL anonymously.
2. **Animated GIFs may count every frame.** Some image processors cap an import at
   about 40 megapixels summed over all frames and reject anything bigger as an
   "invalid image". Prefer a direct file upload if the tool has one. If it only
   takes URLs, make a lighter variant (fewer frames, smaller size), which looks
   identical as a still:

```bash
ffmpeg -y -i <slug>.mp4 -vf "fps=10,scale=720:-1:flags=lanczos,split[a][b];[a]palettegen=max_colors=160:stats_mode=diff[p];[b][p]paletteuse=dither=bayer:bayer_scale=5:diff_mode=rectangle" -loop 0 <slug>-10fps.gif
```

Or attach the MP4 as a video post and skip the problem.

## "Link in the comments"

When the poster's footnote or the post says "link in the comments", the link has
to actually land there. Either post it by hand right after publishing, or, if the
scheduler has an automatic first comment, set it for this post with the link plus
whatever standard line the profile normally uses, with a short delay (about 15
minutes) so the post gets its first reach before the comment goes on.

## Before it goes out

- The numbers on the poster match the post text.
- The edition number, if the series has one, matches the post.
- The footnote promise (link in comments, download, video) has a matching action.
- The LinkedIn GIF has at most 250 frames, and the loop is seamless (render.py's seam
  check says OK; watch two cycles of the MP4 to be sure).
