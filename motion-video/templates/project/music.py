"""A song with Google Lyria via OpenRouter (streamed). Needs OPENROUTER_API_KEY. About $0.08 for a full song (about
2 minutes), $0.04 for a 30 s clip.

  python3 music.py "<prompt>" --out audio/music/song_v1               -> song_v1.mp3 + SOURCE_song_v1.txt
  python3 music.py "<prompt>" --out audio/music/teaser --model clip   a 30 s clip
  python3 music.py "<prompt>" --out audio/music/song_v1 --dry-run     show the request and the cost only

No key? Use a track you are allowed to use commercially (your own, a licensed library, public domain), or keep the
placeholder loop from placeholder.py while you work. Then measure it: python3 beats.py <file>.

A prompt that worked first time (a feel-good promo bed): "Instrumental only, absolutely no vocals, no singing, no
spoken words. Exactly 120 BPM, 4/4 time, steady tempo from start to finish. Warm, playful, feel-good electronic pop
groove with a light house pulse, made as a bed under a friendly voice-over for a fun product promo. Soft but punchy
kick on every beat, crisp claps on beats 2 and 4, shuffling hi-hats, round bouncy bassline, warm Rhodes chords,
sunny plucked synths and a little marimba. Bright, modern, tasteful and optimistic, not cheesy, no big drops, no
dramatic build-ups, no key or tempo changes, consistent energy the whole way, leave space in the midrange for a
voice. Key of D major."
What came back: 119 s of mp3 (asked for wav), 115 BPM (asked 120), F major (asked D). Lyria ignores tempo, key and
format, so always measure with beats.py and build the grid on what you measured. If a long prompt gets blocked
(PROHIBITED_CONTENT, not billed), shorten it to genre, tempo, instruments, mood and "no vocals".
"""
import argparse
import base64
import json
import time
import urllib.error
import urllib.request
from datetime import date
from pathlib import Path

from common import HERE, api_key, openrouter_cost, urlopen

MODELS = {'pro': ('google/lyria-3-pro-preview', 0.08), 'clip': ('google/lyria-3-clip-preview', 0.04)}


def sniff(b):
    if b[:3] == b'ID3' or (len(b) > 1 and b[0] == 0xFF and b[1] & 0xE0 == 0xE0):
        return 'mp3'
    if b[:4] == b'RIFF':
        return 'wav'
    if b[:4] == b'fLaC':
        return 'flac'
    if b[:4] == b'OggS':
        return 'ogg'
    return 'bin'


def main():
    ap = argparse.ArgumentParser()
    ap.add_argument('prompt')
    ap.add_argument('--out', required=True, help='path without extension, e.g. audio/music/song_v2')
    ap.add_argument('--model', choices=list(MODELS), default='pro')
    ap.add_argument('--dry-run', action='store_true')
    a = ap.parse_args()
    model, price = MODELS[a.model]
    body = {'model': model, 'stream': True, 'modalities': ['text', 'audio'], 'audio': {'format': 'wav'},
            'messages': [{'role': 'user', 'content': a.prompt}]}
    if a.dry_run:
        print(json.dumps(body, indent=1, ensure_ascii=False))
        print(f'1 call to {model}, about ${price:.2f}')
        return
    out = Path(a.out)
    out = out if out.is_absolute() else HERE / out
    out.parent.mkdir(parents=True, exist_ok=True)
    key = api_key('OPENROUTER_API_KEY')
    req = urllib.request.Request('https://openrouter.ai/api/v1/chat/completions', data=json.dumps(body).encode(),
                                 headers={'Authorization': f'Bearer {key}', 'Content-Type': 'application/json'})
    chunks, text, gen_id, t0 = [], [], None, time.time()
    print(f'asking {model} (one to three minutes) ...', flush=True)
    try:
        with urlopen(req, timeout=600) as r:
            for raw in r:
                line = raw.decode('utf-8', 'replace').strip()
                if not line.startswith('data:'):
                    continue
                data = line[5:].strip()
                if data == '[DONE]':
                    break
                try:
                    ev = json.loads(data)
                except json.JSONDecodeError:
                    continue
                if ev.get('error'):
                    raise SystemExit(f"OpenRouter error: {ev['error']}")
                gen_id = ev.get('id', gen_id)
                for ch in ev.get('choices', []):
                    d = ch.get('delta', {}) or {}
                    au = d.get('audio') or {}
                    if au.get('data'):
                        chunks.append(au['data'])
                    if d.get('content'):
                        text.append(d['content'] if isinstance(d['content'], str) else json.dumps(d['content']))
                    if ch.get('finish_reason') and 'PROHIBITED' in str(ch['finish_reason']).upper():
                        raise SystemExit('Blocked by the content filter (free). Make the prompt shorter and plainer.')
    except urllib.error.HTTPError as e:
        raise SystemExit(f'OpenRouter said {e.code}: {e.read()[:300]!r}')
    except urllib.error.URLError as e:
        raise SystemExit(f'Could not reach OpenRouter: {e.reason}')
    if not chunks:
        raise SystemExit('No audio came back. Model text: ' + ''.join(text)[:300])
    audio = base64.b64decode(''.join(chunks))
    ext = sniff(audio)
    path = out.with_suffix('.' + ext)
    path.write_bytes(audio)
    cost = openrouter_cost(gen_id, key, tries=10) if gen_id else None
    (out.parent / f'SOURCE_{out.name}.txt').write_text(
        f'{path.name}: generated with {model} via OpenRouter on {date.today():%d %b %Y}'
        f"{f' (${cost:.3f})' if cost is not None else ''}.\nPrompt: {a.prompt}\n"
        f"Measured grid: run python3 beats.py {path.relative_to(HERE) if path.is_relative_to(HERE) else path}\n")
    print(f'{path} ({len(audio) / 1e6:.1f} MB, {ext}) in {time.time() - t0:.0f} s, '
          + (f'${cost:.3f}' if cost is not None else 'cost unknown'))
    print(f'Next: python3 beats.py {path.relative_to(HERE) if path.is_relative_to(HERE) else path}')


if __name__ == '__main__':
    main()
