"""Captions (captions.js) from the script's own words, timed by the voice takes.

  python3 build_captions.py        prints every phrase with its start and end time: read it through

The words on screen come from project.json: a line's "cap" if it has one (null = no caption for that line, for a
title the screen already shows), else its "text". Whisper never writes the screen (it misspells names and brands);
it only gives the timing, from vo/<name>.words.json (vo_check.py --chosen). Without word times, the words are spread
over the line's speech by length: fine for a draft, check it by eye.
Phrases: "groups" on a line (words per phrase), else about captions.words_per_phrase words, broken at punctuation.
Recurring mishearings go in captions.aliases (heard -> script word, lowercase, no punctuation).
captions.on = false writes an empty list, so the page shows nothing.
"""
import difflib
import json
import re

from common import HERE, SR, page_info, project


def norm(w, alias):
    w = re.sub(r'[^a-z0-9]', '', w.lower())
    return alias.get(w, w)


def phrases_of(words, groups, per):
    if groups:
        if sum(groups) != len(words):
            raise SystemExit(f'groups add up to {sum(groups)} words, the caption has {len(words)}')
        out, k = [], 0
        for g in groups:
            out.append(list(range(k, k + g)))
            k += g
        return out
    out, cur = [], []
    for i, w in enumerate(words):
        cur.append(i)
        if len(cur) >= per or re.search(r'[.,!?;:]$', w):
            out.append(cur)
            cur = []
    if cur:
        if out and len(cur) == 1:
            out[-1] += cur
        else:
            out.append(cur)
    return out


def main():
    import build_audio
    pj = project()
    cap = pj.get('captions', {})
    if not cap.get('on'):
        (HERE / 'captions.js').write_text('window.CAPS = [];\n')
        print('captions are off (project.json captions.on): wrote an empty captions.js')
        return
    alias = cap.get('aliases', {})
    info = page_info()
    T, beat = info['T'], info['beat']
    _, placed = build_audio.voiceover(pj, int(round(T * SR)), beat)
    by = {p['name']: p for p in placed}
    out = []
    for ln in pj['lines']:
        text = ln.get('cap', ln['text'])
        if not text or ln['name'] not in by:
            continue
        p = by[ln['name']]
        t0, t1 = p['speech']
        script = text.split()
        heard = p['words']
        times = [None] * len(script)
        if heard:
            sm = difflib.SequenceMatcher(a=[norm(s, alias) for s in script], b=[norm(h['w'], alias) for h in heard],
                                         autojunk=False)
            for a_, b_, n in sm.get_matching_blocks():
                for k in range(n):
                    times[a_ + k] = heard[b_ + k]['s']
            missed = [script[m] for m in range(len(script)) if times[m] is None]
            if len(missed) > 0.3 * len(script):
                print(f"!! {ln['name']}: Whisper matched only {len(script) - len(missed)} of {len(script)} words. "
                      f"Listen to the take or add aliases. Unmatched: {' '.join(missed)}")
        else:
            print(f"   {ln['name']}: no word times (vo_check.py --chosen), spreading the words by length")
        times[0] = max(times[0] or t0, t0)
        # fill the gaps by character count between known neighbours
        k = 0
        while k < len(script):
            if times[k] is None:
                j = k
                while j < len(script) and times[j] is None:
                    j += 1
                a_t, b_t = times[k - 1], (times[j] if j < len(script) else t1 - 0.1)
                chars = [len(script[m]) + 1 for m in range(k - 1, j)]
                tot, acc = sum(chars), 0
                for m in range(k, j):
                    acc += chars[m - k]
                    times[m] = a_t + (b_t - a_t) * acc / tot
                k = j
            k += 1
        for m in range(1, len(times)):
            times[m] = max(times[m], times[m - 1] + 0.05)
        groups = phrases_of(script, ln.get('groups'), cap.get('words_per_phrase', 4))
        for gi, g in enumerate(groups):
            last = gi == len(groups) - 1
            end = (t1 + 0.3) if last else times[groups[gi + 1][0]] - 0.01
            out.append({'s': round(times[g[0]], 3), 'end': round(min(end, T), 3),
                        'w': [[script[m], round(times[m], 3)] for m in g], 'cin': gi > 0, 'cout': not last})
    (HERE / 'captions.js').write_text('window.CAPS = ' + json.dumps(out, ensure_ascii=False) + ';\n', encoding='utf-8')
    for p in out:
        print(f"{p['s']:6.2f} {p['end']:6.2f}  " + ' '.join(w for w, _ in p['w']))
    print(f'{len(out)} phrases -> captions.js. Look at them: python3 render.py sheet <t> ...')


if __name__ == '__main__':
    main()
