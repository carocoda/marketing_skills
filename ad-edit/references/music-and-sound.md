# Music and sound

A music bed sits under the voice, every event has a UI sound, and the song's final hit lands right on the end card.
`build.py audio <variant>` makes the mix; the voice always comes first.

## The music bed

Use a track you have the rights to use in ads: your own, a royalty-free library with an ads licence, or music made
for you. Put it in `<work>/music/bed.mp3` (or set `files.music`) and add `"music": {}` to `edit.json`. Without a
`music` key, the mix has no bed.

What works under a talking head: instrumental, a steady groove around 100 to 120 BPM, soft kick, claps on 2 and 4,
warm sub bass, a sparse arrangement that leaves the midrange free for the voice, no melody, no drops. If you generate
music with an AI music tool, describe exactly that, and always measure the tempo afterwards: one asked for 112 BPM
and delivered 110.

## Two ways `build.py` uses the song

**Simple (no beat grid):** the song plays from `"start"` seconds (default 0), loops if it is too short and fades out
over the last 1.5 s.

**Synced to the end card (better):** measure the song first:

```bash
python3 _engine/beats.py "<work>/music/bed.mp3" --bpm 110
```

That writes `bed.beats.json` next to the song and suggests the `music` block:

```json
"music": {"end_beat": 292, "hit_beat": 308, "phrase": 16, "hit_after_endcard": 1.4}
```

The bed starts early in the song and is spliced, on a phrase boundary, onto the song's **own ending**, so the final
hit lands 1.4 s after the end card starts.

- `hit_beat`: the beat of the final hit. In `bar_db` in the beats file (level per bar of 4 beats), find the last loud
  bar; the bar after it is where the level drops hard. Example: bar 76 is the last loud one (-9.4 dB) and bar 77
  drops (-24.1 dB), so `hit_beat` = 77 x 4 = 308. `beats.py` suggests this; check it by ear.
- `end_beat`: the start of the closing phrase, one phrase (16 beats) earlier: 292.
- The start of the bed sits at the same place in the phrase (`end_beat` modulo 16), so you don't hear the seam. The
  transition is a one-beat crossfade.
- Fade in 30 ms, fade out 0.5 s at the end.

## Levels

| What | Level |
|---|---|
| voice (voice stem) | -16 LUFS, peak -2 dBTP |
| music under speech | -14.5 dB relative to a music stem at -16 LUFS (`mix.duck_speech`) |
| music in pauses | -9 dB (`mix.duck_gap`), with 350 ms hold after speech |
| music on the end card | -6 dB (`mix.endcard`) |
| final mix | **-14 LUFS, -1 dBTP**, 48 kHz, AAC 192k |

The first try (-19 dB under speech) was too soft on a phone speaker. At -14.5 dB you still hear the groove and the
voice stays in front. A soft-spoken voice may need -17. Always test on a phone, not only on headphones.

## UI sounds

`make_sfx.py` synthesises the default set into `_engine/assets/sfx/` (no licence question; `new_ad.py` runs it). Want
your own? Drop files with the same names (`.wav`, `.mp3`, `.m4a`) in that folder; only use sounds you may use in ads.
`SFX` in `build.py` maps a name to a file, volume and offset:

| Name | File | Volume | Use |
|---|---|---|---|
| `pop` | pop | -13 dB | something appears (the default) |
| `click` | click | -10 dB | a cursor click |
| `key` | key-press | -14 dB | a key (⌘C, ⌘V, app tiles) |
| `whoosh` | whoosh-short | -15 dB, 0.16 s early | a big move, the end card |
| `soft_whoosh` | whoosh-short | -25 dB | a small move, a punch-in |
| `impact` | impact-bass-1, cut to 0.9 s | -16 dB | the stamp in the hook |
| `slam` | impact-bass-1 (0.5 s) + click | -23 dB | date and price cards |
| `stamp` | pop + click | -10 dB | the deadline tag |
| `chime` / `ding` | chime | -17 / -15 dB | AI card, price, end card button |
| `tick` | click | -15 dB | ticks |

- A bass impact sample often lasts 2 s and fills the whole low end: always cut it (0.5 to 0.9 s). Otherwise it booms
  over the next sentence.
- Added automatically: a pop per logo and per photo, pops on the fan, keys on the app tiles, ticks on the ticks, a
  click on ⌘C, pops and a chime on the end card, and a `soft_whoosh` on every punch-in that has no other sound within
  0.25 s.
- More than one loud sound per half second gets busy. In a full opening, prefer `pop` over `whoosh`.
- A big impact under a soft last word can mask it: use the short `stamp` there instead.

## Checking

1. `python3 _engine/build.py <ad> audio <variant>` reports the length and the number of sounds.
2. `python3 _engine/build.py <ad> verify <variant>`: Whisper over the final mix, per segment next to the caption. If
   Whisper does not hear a word through the music, the bed is too loud there (or the word needs `voice_gain`).
3. Play the mp4 on a phone, with and without headphones.
