# Cutting: fillers out without hiccups

The biggest lesson from the first ads: a cut you can hear is worse than a filler that stays. Early versions cut off
bits of words ("fo the team", "with ...arah") and that sounded exactly as odd as the reviewer said. Everything on this
page is there so that does not happen again.

## Order of work

Run every command from the ads folder; `<ad>` is the ad folder (for example `02-launch`), `<work>` its work folder.

1. **Speech blocks:** `python3 _engine/islands.py <voice.wav> -50 0.07` lists the stretches of speech and the gaps.
2. **Words:** `python3 _engine/words.py <voice.wav> <work>/words_whisper.json 7.74:11.20 11.20:16.32 ... --prompt "Brand, Name, jargon." --lang en`.
   Whisper large-v3, one window per sentence or shot, each window starting at a speech onset. This gives the **text**.
3. **Times (optional, recommended):** `python3 _engine/crisper.py <voice.wav> <work>/words_crisper.json` with
   CrisperWhisper in windows of about 7 s. This gives the **times**. `build.py` joins the two with difflib.
4. **Choose segments** in `edit.json`: one `segment` per sentence with `a` and `b` in source seconds and a `note`
   with the text and what was taken out. Shorter is better: every sentence that is not needed goes (see `variants`).
5. **Find candidates:** `python3 _engine/filler_scan.py <voice.wav> 4.0:8.0 13.1:15.8 ...` looks for voiced stretches of
   at least 0.22 s with a flat pitch. Every hit is a candidate, not proof.
6. **Check every filler** with `frames.py`, `probe.py` and `splice_probe.py` (below).
7. `python3 _engine/build.py <ad> audit <variant>`: every cut point must sit in quiet (under -45 dB), and every join
   needs a pause.
8. `python3 _engine/build.py <ad> audio <variant>`, then `python3 _engine/build.py <ad> verify <variant>`: Whisper over
   the final mix.

## Recognising a filler

Don't look at the transcript, look at the signal. `python3 _engine/frames.py <voice.wav> 14.38 14.92` prints level,
pitch (f0) and spectral change (flux) every 20 ms. This is a real "uh" between two words in a first take:

```
 14.46  -87.7 f0     0 flux 1.16                      <- silence after the word before
 14.48  -48.2 f0   327 flux 3.69 #####
 14.52  -31.6 f0   182 flux 0.75 ##############       <- from here: f0 flat at 178-184 Hz,
 14.58  -29.6 f0   184 flux 0.65 ###############         flux low (0.6-0.8): "uh"
 14.64  -34.0 f0   182 flux 0.66 ############
 14.68  -27.8 f0   178 flux 0.71 ################
 14.72  -46.3 f0   182 flux 0.85 ######
 14.80  -59.1 f0     0 flux 0.87                      <- silence
 14.86  -41.2 f0   163 flux 0.76 #########            <- the next word starts
```

The cut was 14.47-14.74 (one segment ends at 14.30, the next begins at 14.84).

A filler is:

- **long:** more than 0.2 s;
- **voiced** (f0 is on) with a **flat pitch**, around the speaker's own low speaking tone;
- **low flux:** the sound barely changes, because no word is being formed;
- **between two words:** a real word before and after.

A word has a moving pitch and high flux at every vowel and consonant change.

Then confirm it two ways:

- `python3 _engine/probe.py <voice.wav> 13.9:14.5 13.9:14.8 13.9:15.1`: growing windows. Where does the next word join?
  Keep windows at least 2.5 s long; shorter ones make Whisper hallucinate.
- `python3 _engine/splice_probe.py <voice.wav> 13.9:14.47:14.74:15.6`: transcribes the window with and without the stretch
  `14.47-14.74`. Are all words still there in "cut"? Then the cut is safe. The level of the removed part is printed too.

Only when all three agree does the filler go. In one take, only two of the five "uhs" in the transcript were real.

## Never cut inside voice

- `build.py audit` measures the level at every start and end of a segment. Anything above -45 dB gets
  `CUT IN VOICE`. `build.py all` refuses to render while such a cut exists.
- Word endings ring out longer than Whisper says. Words like "november" or "now!" fade 0.1 to 0.3 s after Whisper's
  end time. End a segment only where `energy.py` shows quiet: `python3 _engine/energy.py <voice.wav> 43.30` shows 0.5 s
  around that point and the quietest spot.
- `build.py` puts an 8 ms fade on every cut. That hides a click, not half a word.

## Keep the breathing pauses

- Leave a natural pause of about 0.15 to 0.25 s when you take out a filler or a long silence inside a sentence.
  Words glued together sound rushed.
- A fluent stretch stays whole, even with a tiny stumble in it. A cut in the middle of a fluent sentence is always heard.
- Is a filler very short, or glued to a word? Leave it. Captions and graphics pull the eye; nobody notices a mini "uh".

## Pauses between sentences

- A word can be complete in the voice track and still sound cut off. That happens when the next sentence follows
  within about 0.1 s. The ear hears a clipped word and the picture seems to jump.
- Aim for 0.3 to 0.45 s of quiet at every join between two sentences.
- Take that pause from the quiet already in the recording: start the next piece earlier (in the quiet before the
  sentence), or let the previous one end later. Picture and sound stay in sync and no freeze frame is needed. Move the
  matching `shots` along.
- `build.py audit` prints the pause at every join and flags anything under 0.18 s.

## Fillers that hide from Whisper

- **A filler at the start of a sentence** ("uhh, for more info...") never shows up in a Whisper transcript. Whisper
  smooths it away, so `splice_probe.py` stays green. Look at the first 0.6 s of every segment in `frames.py`. A flat,
  voiced stretch of 0.3 to 0.5 s (pitch within about 5%) before the first word is a filler. The segment then starts at
  the word after it.
- **A filler between two words** shows the same way; `splice_probe.py` confirms no word is lost. Compare the flat tone
  with the words around it: they have pitch movement.
- **In doubt?** The reviewer will say it in the feedback. Treat their ear as the truth and find the flat tone there.
- **Sometimes a filler runs into the word without any quiet.** Cut at the deepest point (around -40 dB) and accept
  that `audit` reports it. `all` stops on it, so render that variant step by step: `audio`, `base`, `overlay`, `final`.
- **False starts:** a phrase that restarts right away ("And if you ... And if you just don't know"). Keep only the
  second one.
- **Final consonants after a small gap:** the "t" of a word can arrive 0.25 s after the vowel. `audit` passes the cut
  (quiet at the cut point), but the word is clipped. At every sentence end, look 0.45 s further for a short peak.
- **A soft word disappears under the music,** even when you can hear it in the voice track. Run Whisper over the final
  mix. Where a word drops out there, give it `voice_gain` (`[[from, to, dB]]` in source time). If the denoiser already
  ate it, rebuild that stretch with `patch_voice.py` (references/voice.md).
- **Check the take for anything off-brand** (swearing, a competitor's name, a wrong fact). A cleaner take with a curse
  in it loses to a slightly rougher one without.

## Whisper (large-v3) pitfalls

- **Word starts 0.2 to 0.5 s early.** The start of a word swallows the pause before it. Never cut on Whisper times alone.
- **Short windows hallucinate.** Under 2.5 s Whisper invents words ("Thank you.", "Grazie"). Drop them with `words_drop`.
- **Names and jargon wrong.** Fix with `words_fix` (`[heard, meant]` or `[heard, meant, near time]`) and pass names
  in `--prompt` to `words.py`.
- **Missing words** (often the first word after a cut): `words_add` with `[word, time]`.
- **A wrong time** for a word a graphic lands on: `words_at` with `[word, near, real start]`.
- **Always check the final mix.** `build.py verify` puts what Whisper hears next to what the caption says, per segment.
  A stray "of" in the transcript once gave away a left-over "uh".

## CrisperWhisper pitfalls

- Much better times (close to the real onset), but poorer text, especially outside English and German. So: times from
  Crisper, text from Whisper.
- **An `[UH]` label is not proof.** In one take the "uh" before a name was the first syllable of the name itself. Both
  cut, both wrong. Check every label with `frames.py`.
- A word with a label glued on (".Then[UH]") has an unreliable time. `build.py` leaves such a word unmatched, so it
  takes its time from its neighbours.
- Run it in windows of about 7 s (`crisper.py` does). One long run gave empty or odd output.
- Sometimes Crisper hears a real "uh" that Whisper misses. Then too: `frames.py` first.
- If CrisperWhisper is not installed, skip it. `build.py` then uses Whisper's times; check event timing in `stills`.

## Shots and zooms

Every cut is a jump cut. Don't hide it, make it a punch: `shots` in `edit.json` sets a different zoom level (`1`, `2`
or `3`, set per format in `formats`) at each cut point. `build.py` switches automatically when two shots in a row have
the same level. The first shot gets `"intro"`: a short punch-out in the hook. Inside a shot there is a slow 3.5% push-in.

## Checklist before you build the audio

- [ ] Every removed filler seen in `frames.py` and tested with `splice_probe.py`
- [ ] `build.py audit <variant>` says "all cuts in quiet" for every variant, no SHORT PAUSE
- [ ] Breathing pauses of 0.15 to 0.25 s inside sentences, 0.3 to 0.45 s between them
- [ ] `build.py plan` without `WARNING` lines (see `graphics-kit.md`)
- [ ] After `build.py audio`: `build.py verify` read, no word lost, no left-over filler
