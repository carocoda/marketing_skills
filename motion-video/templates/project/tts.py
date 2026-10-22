"""Voice-over takes with Gemini TTS, one sentence per call. A take costs well under a cent.

  python3 tts.py --dry-run                  what would be asked for every line, and what it costs (spends nothing)
  python3 tts.py s2                         2 new takes of line s2 -> vo/takes/s2_a.wav, s2_b.wav (then c, d, ...),
                                            each checked with Whisper (vo_check.py) and ranked
  python3 tts.py s2 --takes 4               more takes of one line (names, brand names and urls need them)
  python3 tts.py --missing                  2 takes of every line that has no vo/<name>.wav yet
  python3 tts.py s2 --use d                 take d becomes vo/s2.wav, the file build_audio.py uses
  python3 tts.py s2 --no-check              skip the Whisper check
  python3 tts.py --test "One sentence." --voices Aoede,Sulafat,Puck    one short take per voice, to pick a voice

Providers (project.json voice.provider; "auto" picks by which key it finds):
  openrouter  OPENROUTER_API_KEY. Gemini TTS through OpenRouter's /audio/speech; the delivery goes in
              provider.options.google-ai-studio.speech_metadata.style. Tested in production.
  gemini      GEMINI_API_KEY (or GOOGLE_API_KEY). Google's generateContent API with responseModalities AUDIO;
              the delivery is written in front of the text as an instruction. Written to the public API docs and
              not tested by the skill author: check the first takes with vo_check.py (a high WER means the model
              read the instruction out loud).
  none        no paid voice. Use placeholder.py voice (a scratch track for timing), import your own recordings as
              vo/<name>.wav, or make a music-only video.

The text sent is the line's "say" (spelled for the ear) or else its "text". The delivery is voice.style plus the
line's "style" (replaces it) and "hint" (added to it).
Lessons:
- One sentence per call. One long take of a whole 40 s script went robotic halfway.
- Delivery instructions never go in the spoken text field, or they get read out.
- The answer is raw 24 kHz 16-bit mono PCM, wrapped into a .wav here.
- Names and brand names: no phonetic hint in another language (an English hint on a Dutch take turned a name
  into a rude word). Make 4 to 9 takes and keep one Whisper hears right. Urls: spell them for the ear in "say".
"""
import argparse
import base64
import json
import shutil
import string
import subprocess
import sys
import urllib.error
import urllib.request

from common import HERE, api_key, need, openrouter_cost, project, urlopen, voice_provider

PER_SECOND = 0.0009             # dollars per second of speech, measured on Gemini TTS via OpenRouter (26 takes, 178 s)


def estimate(text):
    """Rough cost of one take: about 2.8 words per second, plus half a second of silence."""
    return PER_SECOND * (len(text.split()) / 2.8 + 0.5)


def style_of(pj, ln):
    v = pj['voice']
    return ' '.join(s for s in [ln.get('style') or v.get('style', ''), ln.get('hint', '')] if s)


def request_for(provider, pj, ln, voice=None):
    v = pj['voice']
    text, style, voice = ln.get('say', ln['text']), style_of(pj, ln), voice or v['voice']
    if provider == 'openrouter':
        body = {'model': v.get('openrouter_model', 'google/gemini-3.8-flash-tts'), 'input': text, 'voice': voice,
                'response_format': 'pcm'}
        if style:
            body['provider'] = {'options': {'google-ai-studio': {'speech_metadata': {'style': style}}}}
        return 'https://openrouter.ai/api/v1/audio/speech', body
    if provider == 'gemini':
        model = v.get('gemini_model', 'gemini-2.5-flash-preview-tts')
        prompt = (f'Read the text below aloud, exactly as written, and say nothing else. Delivery: {style}\n\n{text}'
                  if style else text)
        body = {'contents': [{'parts': [{'text': prompt}]}],
                'generationConfig': {'responseModalities': ['AUDIO'],
                                     'speechConfig': {'voiceConfig': {'prebuiltVoiceConfig': {'voiceName': voice}}}}}
        return f'https://generativelanguage.googleapis.com/v1beta/models/{model}:generateContent', body
    raise SystemExit(f'unknown voice provider {provider!r}')


def speak(provider, url, body, key, out):
    headers = {'Content-Type': 'application/json'}
    headers.update({'Authorization': f'Bearer {key}'} if provider == 'openrouter' else {'x-goog-api-key': key})
    req = urllib.request.Request(url, data=json.dumps(body).encode(), headers=headers)
    try:
        with urlopen(req, timeout=180) as r:
            raw, gen_id, ctype = r.read(), r.headers.get('X-Generation-Id'), r.headers.get('Content-Type', '')
    except urllib.error.HTTPError as e:
        raise SystemExit(f'{provider} said {e.code}: {e.read()[:300]!r}')
    except urllib.error.URLError as e:
        raise SystemExit(f'Could not reach {provider}: {e.reason}')
    if provider == 'openrouter':
        if 'json' in ctype or raw[:1] == b'{':
            raise SystemExit(f'OpenRouter sent an error instead of audio: {raw[:300]!r}')
        pcm = raw
    else:
        try:
            d = json.loads(raw)
            part = next(p for p in d['candidates'][0]['content']['parts'] if 'inlineData' in p)
            pcm = base64.b64decode(part['inlineData']['data'])
        except Exception:
            raise SystemExit(f'Gemini sent no audio: {raw[:300]!r}')
        gen_id = None
    out.parent.mkdir(parents=True, exist_ok=True)
    subprocess.run(['ffmpeg', '-y', '-loglevel', 'error', '-f', 's16le', '-ar', '24000', '-ac', '1', '-i', '-', str(out)],
                   input=pcm, check=True)
    return len(pcm) / 48000, gen_id


def provider_key(provider):
    if provider == 'openrouter':
        return api_key('OPENROUTER_API_KEY')
    return api_key('GEMINI_API_KEY', required=False) or api_key('GOOGLE_API_KEY', required=False) or api_key('GEMINI_API_KEY')


def next_letters(name, k):
    have = {p.stem.split('_')[-1] for p in (HERE / 'vo' / 'takes').glob(f'{name}_*.wav')}
    free = [c for c in string.ascii_lowercase if c not in have]
    if len(free) < k:
        raise SystemExit(f'too many takes of {name} already: clear out vo/takes/{name}_*.wav you do not need')
    return free[:k]


def main():
    ap = argparse.ArgumentParser()
    ap.add_argument('line', nargs='?')
    ap.add_argument('--takes', type=int, default=2)
    ap.add_argument('--use')
    ap.add_argument('--missing', action='store_true')
    ap.add_argument('--dry-run', action='store_true')
    ap.add_argument('--no-check', action='store_true')
    ap.add_argument('--test', help='one test sentence, made once in every voice of --voices')
    ap.add_argument('--voices', default='')
    a = ap.parse_args()
    pj = project()
    lines = {ln['name']: ln for ln in pj['lines']}

    if a.use:
        src = HERE / 'vo' / 'takes' / f'{a.line}_{a.use}.wav'
        if not src.exists():
            raise SystemExit(f'{src.relative_to(HERE)} does not exist')
        shutil.copy(src, HERE / 'vo' / f'{a.line}.wav')
        words = src.with_suffix('.words.json')
        if words.exists():
            shutil.copy(words, HERE / 'vo' / f'{a.line}.words.json')
        (HERE / 'vo' / f'{a.line}.scratch').unlink(missing_ok=True)
        print(f'vo/{a.line}.wav <- takes/{src.name}. Next: python3 build_audio.py --table')
        return

    provider = voice_provider(pj)
    if a.test:
        voices = [v for v in a.voices.split(',') if v] or [pj['voice']['voice']]
        if a.dry_run or provider == 'none':
            print(f'{len(voices)} test takes, about ${estimate(a.test) * len(voices):.3f} (provider: {provider})')
            return
        need('ffmpeg')
        key = provider_key(provider)
        for v in voices:
            url, body = request_for(provider, pj, {'text': a.test}, voice=v)
            p = HERE / 'vo' / 'tests' / f'{v}.wav'
            secs, _ = speak(provider, url, body, key, p)
            print(f'made {p.relative_to(HERE)} ({secs:.1f}s)')
        print('Let the person listen and pick one; put it in project.json voice.voice.')
        return

    if a.missing or (a.dry_run and not a.line):
        todo = [n for n in lines if a.dry_run or not (HERE / 'vo' / f'{n}.wav').exists()
                or (HERE / 'vo' / f'{n}.scratch').exists()]
    elif a.line:
        todo = [a.line]
    else:
        raise SystemExit(__doc__)
    for n in todo:
        if n not in lines:
            raise SystemExit(f'no line {n!r} in project.json (have {", ".join(lines)})')
    if not todo:
        print('Every line has a real take in vo/<name>.wav. To redo one: python3 tts.py <line>')
        return
    if a.dry_run:
        shown = provider if provider != 'none' else 'openrouter'
        for n in todo:
            print(n, json.dumps(request_for(shown, pj, lines[n])[1], ensure_ascii=False))
        cost = sum(estimate(lines[n].get('say', lines[n]['text'])) for n in todo) * a.takes
        print(f'\n{len(todo)} lines x {a.takes} takes = {len(todo) * a.takes} calls, about ${cost:.2f} '
              f'(provider now: {provider})')
        return
    if provider == 'none':
        raise SystemExit('No voice provider: no OPENROUTER_API_KEY or GEMINI_API_KEY found (see the skill README).\n'
                         'Without a key: python3 placeholder.py voice (a scratch track for timing), put your own '
                         'recordings in vo/<name>.wav, or make the video without a voice-over.')

    need('ffmpeg')
    key = provider_key(provider)
    made, spent = {}, 0.0
    for n in todo:
        url, body = request_for(provider, pj, lines[n])
        for letter in next_letters(n, a.takes):
            p = HERE / 'vo' / 'takes' / f'{n}_{letter}.wav'
            secs, gen_id = speak(provider, url, body, key, p)
            c = openrouter_cost(gen_id, key) if gen_id else None
            spent += c if c is not None else PER_SECOND * secs
            made.setdefault(n, []).append(p)
            print(f'made {p.relative_to(HERE)}  {secs:.1f}s  ' + (f'${c:.4f}' if c is not None else '(cost estimated)'))
    print(f'spent about ${spent:.3f}')
    if not a.no_check:
        subprocess.run([sys.executable, str(HERE / 'vo_check.py'), *made], check=False)
    print('Listen to the takes, then keep one:  python3 tts.py <line> --use <letter>')


if __name__ == '__main__':
    main()
