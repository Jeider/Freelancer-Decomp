"""Stage/install the cloud jump tunnel, with hash-checked backup and restore.

Only bin and DATA_EXTRA are written. Gameplay DATA assets remain unchanged.
Run without arguments to prepare, --apply to install, --restore BACKUP to revert.
"""
import argparse
import datetime
import json
import re
import sys
from pathlib import Path

REPO = Path(__file__).resolve().parents[2]
sys.path.insert(0, str(REPO / 'tools'))
from install_hyperspace_tunnel import copy, digest, safe, stopped

STAGE = REPO / 'out/jump_travel/install'
PAYLOAD = ('bin/freelancer.exe', 'bin/freelancer.pdb',
           'bin/RP9.dll', 'bin/RP9.pdb',
           'DATA_EXTRA/SHADERS/jump_cloud.hlsl',
           'DATA_EXTRA/FX/JUMP_CLOUD/modulation.png',
           'DATA_EXTRA/FX/JUMP_CLOUD/path.dds', 'bin/port.ini')


def configure(raw):
    text = raw.decode('latin1')
    newline = '\r\n' if '\r\n' in text else '\n'
    sections = list(re.finditer(r'^\[([^\]\r\n]+)\][^\r\n]*(?:\r?\n|$)', text, re.M))
    selected = [(i, s) for i, s in enumerate(sections) if s[1].strip().lower() == 'render']
    if len(selected) != 1:
        raise ValueError('Expected exactly one [Render] section in bin/port.ini')
    i, section = selected[0]
    end = sections[i+1].start() if i+1 < len(sections) else len(text)
    body = text[section.end():end]
    for key, value in [('jump_cloud_tunnel', 1), ('jump_travel_prototype', 0)]:
        pattern = re.compile(r'^' + key + r'[ \t]*=[^\r\n]*(?:\r?\n|$)', re.M | re.I)
        body = pattern.sub('', body)
        body = key + ' = ' + str(value) + newline + body
    return (text[:section.end()] + body + text[end:]).encode('latin1')


def main():
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument('--game-root', type=Path, default=Path('D:/games/FL_MOD'))
    parser.add_argument('--binary-root', type=Path, default=REPO/'out/base_neural/on/bin',
                        help='Use the selected client build, including optional DLSS support')
    mode = parser.add_mutually_exclusive_group()
    mode.add_argument('--apply', action='store_true')
    mode.add_argument('--restore', type=Path)
    args = parser.parse_args()
    game = args.game_root.resolve(strict=True)
    if not (args.apply or args.restore):
        items = []
        for rel in PAYLOAD:
            if rel == 'bin/port.ini':
                target = safe(STAGE, rel)
                target.parent.mkdir(parents=True, exist_ok=True)
                target.write_bytes(configure(safe(game, rel).read_bytes()))
                items.append(dict(relative=rel, original=digest(safe(game, rel)), prepared=digest(target)))
                continue
            source = safe(args.binary_root, Path(rel).name) if rel.startswith('bin/') else safe(REPO, rel)
            if rel == 'bin/freelancer.exe':
                dependencies = [REPO/'src/freelancer/Client'/name for name in
                                ('gate_tunnel.cpp', 'jump_cloud.inl', 'jump_cloud_path.h')]
                if any(p.stat().st_mtime > source.stat().st_mtime for p in dependencies):
                    raise ValueError('Rebuild client before preparing installation')
            copy(source, safe(STAGE, rel))
            before, after = digest(safe(game, rel)), digest(safe(STAGE, rel))
            if before != after:
                items.append(dict(relative=rel, original=before, prepared=after))
        data = dict(game=str(game), files=items,
                    scope='cloud background for hyperspace-enabled jump gates; original flight physics, sounds and transitions')
        (STAGE / 'manifest.json').write_text(json.dumps(data, indent=2), encoding='utf8')
        print(f'Prepared {len(items)} changed files; game untouched.')
        return

    stopped()
    source = args.restore.resolve(strict=True) if args.restore else STAGE
    data = json.loads((source / 'manifest.json').read_text(encoding='utf8'))
    if Path(data['game']).resolve() != game:
        raise ValueError('Manifest game root mismatch')
    seen = set()
    for item in data['files']:
        rel = item['relative']
        if rel not in PAYLOAD or rel in seen:
            raise ValueError(f'Unexpected/duplicate target: {rel}')
        seen.add(rel)
        expected_game = item['prepared'] if args.restore else item['original']
        expected_source = item['original'] if args.restore else item['prepared']
        if digest(safe(game, rel)) != expected_game or digest(safe(source, rel)) != expected_source:
            raise ValueError(f'File changed since preparation/install: {rel}')

    def restore_from(backup):
        for item in data['files']:
            target = safe(game, item['relative'])
            if item['original'] is None:
                target.unlink(missing_ok=True)
            else:
                copy(safe(backup, item['relative']), target)
            if digest(target) != item['original']:
                raise ValueError(f'Restore verification failed: {target}')

    if args.restore:
        restore_from(source)
        print(f'Restored and verified {len(data["files"])} files from {source}')
        return
    if not data['files']:
        print('Already installed; no changes.')
        return
    backup = safe(game, 'BACKUP/codex_jump_cloud_' + datetime.datetime.now().strftime('%Y%m%d_%H%M%S_%f'))
    for item in data['files']:
        if item['original'] is not None:
            target = safe(backup, item['relative'])
            copy(safe(game, item['relative']), target)
            if digest(target) != item['original']:
                raise ValueError(f'Backup verification failed: {target}')
    copy(source / 'manifest.json', backup / 'manifest.json')
    try:
        for item in data['files']:
            rel = item['relative']
            copy(safe(source, rel), safe(game, rel))
            if digest(safe(game, rel)) != item['prepared']:
                raise ValueError(f'Installation verification failed: {rel}')
    except Exception:
        restore_from(backup)
        raise
    print(f'Installed and verified {len(data["files"])} files. Backup: {backup}')


if __name__ == '__main__':
    main()
