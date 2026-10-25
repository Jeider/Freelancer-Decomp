"""Replace verified colour-only startup fuses with vulnerable markers in staged INIs.

Only accepts an init fuse consisting of one relative damage_group action aimed
at the same group, dealing less than its full health. All combat fuses and the
effective (post-startup) health are preserved. Source game files are never written.
"""
import argparse
import hashlib
import json
import re
from pathlib import Path

HEADER = re.compile(r'^\s*\[([^\]\r\n]+)\]', re.M)


def sections(text):
    headers = list(HEADER.finditer(text))
    for i, match in enumerate(headers):
        end = headers[i + 1].start() if i + 1 < len(headers) else len(text)
        yield match[1].lower(), match.start(), end, text[match.end():end]


def values(body):
    result = {}
    for line in body.splitlines():
        line = line.split(';', 1)[0].strip()
        if '=' in line:
            key, value = line.split('=', 1)
            result.setdefault(key.strip().lower(), []).append(value.strip())
    return result


def only(data, key):
    assert len(data.get(key, [])) == 1, f'Expected one {key}: {data}'
    return data[key][0]


def fuse_definitions(text):
    definitions = {}
    current = None
    for section, _, _, body in sections(text):
        data = values(body)
        if section == 'fuse':
            current = only(data, 'name').lower()
            assert current not in definitions
            definitions[current] = []
        elif current:
            definitions[current].append((section, data))
    return definitions


def migrate(text, definitions):
    edits, changes = [], []
    owner = None
    for section, start, end, body in sections(text):
        data = values(body)
        if section == 'ship':
            owner = only(data, 'nickname')
        if section != 'collisiongroup':
            continue
        for fuse in data.get('fuse', []):
            name = fuse.split(',')[0].strip().lower()
            if '_init_dmg_' not in name:
                continue
            actions = definitions[name]
            assert len(actions) == 1 and actions[0][0] == 'damage_group', name
            action = actions[0][1]
            group = only(data, 'obj')
            assert only(action, 'group_name').lower() == group.lower(), (name, group)
            assert only(action, 'damage_type').lower() == 'relative', name
            hp = float(only(data, 'hit_pts'))
            damage = float(only(action, 'hitpoints'))
            assert 0 < damage < hp, (name, damage, hp)
            # The removed fuse must be an immediate startup trigger, not a combat stage.
            trigger = [part.strip() for part in fuse.split(',')]
            assert len(trigger) == 3 and float(trigger[1]) == 0 and float(trigger[2]) >= hp, fuse
            assert 'vulnerable' not in data, 'Reconcile an existing marker before migration'
            block = text[start:end]
            pattern = re.compile(r'^([ \t]*)fuse\s*=\s*' + re.escape(name) + r'\s*,[^\r\n]*(\r?\n|$)', re.M | re.I)
            replacement, count = pattern.subn(lambda m: m[1] + 'vulnerable = true' + m[2], block)
            assert count == 1
            effective_hp = hp - damage
            hp_text = str(int(effective_hp)) if effective_hp.is_integer() else str(effective_hp)
            replacement, count = re.subn(r'^([ \t]*)hit_pts\s*=[^\r\n]*(\r?\n|$)',
                lambda m: m[1] + 'hit_pts = ' + hp_text + m[2], replacement, flags=re.M | re.I)
            assert count == 1
            assert not any(a == start for a, _, _ in edits), 'More than one startup fuse on a group'
            edits.append((start, end, replacement))
            changes.append(dict(ship=owner, group=group, removed_fuse=name,
                                old_hit_pts=hp, hit_pts=effective_hp, removed_damage=damage))
    for start, end, replacement in reversed(edits):
        text = text[:start] + replacement + text[end:]
    return text, changes


def main():
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument('--game', type=Path, default=Path('D:/games/FL_MOD'))
    parser.add_argument('--out', type=Path, required=True)
    args = parser.parse_args()
    assert args.game.resolve() != args.out.resolve()
    config = (args.game / 'bin/freelancer.ini').read_bytes().decode('latin1')
    ship_paths = re.findall(r'^\s*ships\s*=\s*([^;\r\n]+)', config, re.M | re.I)
    # ShiparchManager (V1) writes shiparch2.ini; V2 writes the active shiparch.ini.
    if (args.game / 'DATA/ships/shiparch2.ini').exists():
        ship_paths.append('ships/shiparch2.ini')
    definitions = fuse_definitions((args.game / 'DATA/FX/fuse_gen_capital.ini').read_bytes().decode('latin1'))
    report = []
    for path in ship_paths:
        rel = 'DATA/' + path.strip().replace('\\', '/')
        original = (args.game / rel).read_bytes()
        prepared, changes = migrate(original.decode('latin1'), definitions)
        if not changes:
            continue
        # Independent comparison: deleting only marker/startup-fuse lines leaves
        # the same sections and every original combat parameter intact. Only
        # marked groups have HP adjusted above, by exactly the removed damage.
        def strip(text):
            return re.sub(r'^[ \t]*(?:hit_pts\s*=.*|vulnerable\s*=.*|fuse\s*=\s*[^,\r\n]*_init_dmg_[^\r\n]*)\r?\n', '', text, flags=re.M | re.I)
        assert strip(prepared) == strip(original.decode('latin1'))
        assert migrate(prepared, definitions) == (prepared, [])
        target = args.out / rel
        target.parent.mkdir(parents=True, exist_ok=True)
        payload = prepared.encode('latin1')
        target.write_bytes(payload)
        report.append(dict(relative=rel, original=hashlib.sha256(original).hexdigest(),
                           prepared=hashlib.sha256(payload).hexdigest(), changes=changes))
    args.out.mkdir(parents=True, exist_ok=True)
    (args.out / 'migration.json').write_text(json.dumps(report, indent=2))
    print(f'Prepared {sum(len(r["changes"]) for r in report)} vulnerable groups in {len(report)} files; combat fuses and effective HP preserved.')


if __name__ == '__main__':
    main()
