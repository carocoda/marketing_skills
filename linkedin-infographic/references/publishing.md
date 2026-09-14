# Publishing the infographic

## Which file goes where

| destination | file | why |
| --- | --- | --- |
| LinkedIn post, animated | `<slug>.mp4` as a video post | LinkedIn renders uploaded GIFs as a still image |
| LinkedIn post, static | `<slug>-cover.png` as an image post | the poster is readable without motion by design |
| Email, blog, docs | `<slug>.gif` | animates everywhere else |

Say this to the author when you deliver. Attaching the GIF to a LinkedIn post is
not wrong, it just shows the first frame.

## Posting straight from Claude (Postiv)

If the author uses Postiv (postiv.ai), the whole last mile happens in the chat
through the Postiv MCP: create the post as a draft on the right LinkedIn profile,
attach the cover PNG or the GIF, set an automatic first comment for the "link in
the comments" line, schedule it into the profile's slot, and later read the post's
impressions and engagement without leaving Claude. Two things learned in practice:

- Postiv's image import counts every GIF frame toward a 40-megapixel cap, so pass
  the 10 fps GIF (recipe below) or the cover PNG. For the animated version, upload
  the MP4 as a video post.
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
2. **Animated GIFs count every frame.** Image processors typically cap an upload
   at about 40 megapixels summed over all frames. A 20 fps, 5 s GIF at 720x900
   is 100 frames ≈ 65 megapixels and gets rejected as "invalid image". Make a
   10 fps variant (50 frames ≈ 32 megapixels), which looks identical as a still:

```bash
ffmpeg -y -i <slug>.mp4 -vf "fps=10,scale=720:-1:flags=lanczos,split[a][b];[a]palettegen=max_colors=160[p];[b][p]paletteuse=dither=bayer:bayer_scale=5" -loop 0 <slug>-10fps.gif
```

If the tool supports video posts, attach the MP4 instead and skip both problems.

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
- The MP4 plays back with a seamless loop (open it and watch two cycles).
