#!/usr/bin/env python3
"""Update only our top-level JSONC menu values, retaining comments/settings."""
import json
import re
import shlex
import sys
from pathlib import Path


def masked(text):
    # Mask comments without changing offsets or strings.
    token = r'"(?:\\.|[^"\\])*"|//[^\n]*|/\*[\s\S]*?\*/'
    clean = re.sub(token, lambda m: m[0] if m[0].startswith('"') else
                   ''.join('\n' if c == '\n' else ' ' for c in m[0]), text)
    # Mask trailing commas outside strings, retaining offsets.
    return re.sub(r'"(?:\\.|[^"\\])*"|,(?=\s*[}\]])',
                  lambda m: ' ' if m[0] == ',' else m[0], clean)


def update(text, bindir):
    clean = masked(text)
    parsed = json.loads(clean)
    if not isinstance(parsed, dict):
        raise ValueError('Menu must be a JSONC object')
    decoder = json.JSONDecoder()
    spans = {}
    pos = clean.index('{') + 1
    while True:
        while clean[pos].isspace() or clean[pos] == ',':
            pos += 1
        if clean[pos] == '}':
            close = pos
            break
        key, pos = decoder.raw_decode(clean, pos)
        while clean[pos].isspace(): pos += 1
        if clean[pos] != ':': raise ValueError('Expected colon')
        pos += 1
        while clean[pos].isspace(): pos += 1
        start = pos
        _, pos = decoder.raw_decode(clean, pos)
        if key in spans: raise ValueError('Duplicate menu key: ' + key)
        spans[key] = (start, pos)
    changes = []
    missing = []
    for operation in ('install', 'remove'):
        key = operation + '.flatpak'
        entry = json.dumps({
            'icon': '', 'label': 'Flatpak',
            'description': ('Search Flathub apps' if operation == 'install' else 'Remove installed Flatpak apps'),
            'action': 'xdg-terminal-exec --app-id=org.omarchy.terminal ' +
                      shlex.quote(str(bindir / ('omarchy-pkg-flatpak-' + operation)))
        }, ensure_ascii=False)
        if key in spans:
            changes.append((*spans[key], entry))
        else:
            missing.append(json.dumps(key) + ': ' + entry)
    if missing:
        # Add the separator before any trailing comment, unless already present.
        if spans:
            last = max(end for _, end in spans.values())
            if ',' not in masked(text[last:close]).strip():
                changes.append((last, last, ','))
        changes.append((close, close, '\n  ' + ',\n  '.join(missing) + '\n'))
    for start, end, value in sorted(changes, reverse=True):
        text = text[:start] + value + text[end:]
    json.loads(masked(text))
    return text


if __name__ == '__main__':
    source, destination, bindir = map(Path, sys.argv[1:])
    text = source.read_text() if source.exists() else '{}\n'
    destination.write_text(update(text, bindir))
