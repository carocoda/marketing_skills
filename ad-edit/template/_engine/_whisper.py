"""Shared bits for the Whisper tools: options, audio loading and a friendly error when faster-whisper is missing.
Options every tool takes: --lang xx (default: $AD_EDIT_LANG, else auto-detect) and --model name (default large-v3).
The first run of a model downloads it into the Hugging Face cache (large-v3 and CrisperWhisper are about 3 GB each)."""
import os
import subprocess
import sys

import numpy as np


def opts(args, default_model='large-v3'):
    """Pull --lang, --model and --prompt out of an argument list; returns (rest, lang, model, prompt)."""
    args = list(args)
    pick = lambda k, d: (args.pop(args.index(k) + 1), args.remove(k))[0] if k in args else d
    lang = pick('--lang', os.environ.get('AD_EDIT_LANG') or None)
    model = pick('--model', os.environ.get('AD_EDIT_WHISPER_MODEL', default_model))
    prompt = pick('--prompt', None)
    return args, (lang or None), model, prompt


def model(name):
    try:
        from faster_whisper import WhisperModel
    except ImportError:
        raise SystemExit('faster-whisper is missing: pip3 install faster-whisper')
    return WhisperModel(name, device='cpu', compute_type='int8')


def load16(path, sr=16000):
    raw = subprocess.run(['ffmpeg', '-v', 'error', '-i', str(path), '-f', 'f32le', '-ac', '1', '-ar', str(sr), '-'],
                         capture_output=True, check=True).stdout
    return np.frombuffer(raw, np.float32)


def usage(doc):
    print(doc)
    sys.exit(1)
