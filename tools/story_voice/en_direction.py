"""Offline inventory and publication of authored English story performances."""
import argparse
import ast
import hashlib
import json
from pathlib import Path
import csv
import datetime
import sys

sys.dont_write_bytecode = True

ROOT = Path(__file__).resolve().parents[2]
PROJECT = Path('D:/Games/FL_MOD/Assets/Pythonlancer')
OUT = ROOT / 'out/story_cutscenes/voice_direction_en'


def sha(raw):
    return hashlib.sha256(raw).hexdigest()


def save(path, value):
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_text(json.dumps(value, ensure_ascii=False, indent=2) + '\n', encoding='utf-8')


def scan(raw, path):
    tree = ast.parse(raw.decode('utf-8-sig'))
    rows = []
    for cls in (node for node in tree.body if isinstance(node, ast.ClassDef)):
        space = any(isinstance(base, ast.Attribute) and base.attr == 'SpaceVoiceProps'
                    for base in cls.bases)
        for call in ast.walk(cls):
            if not (isinstance(call, ast.Call) and isinstance(call.func, ast.Name)
                    and call.func.id == 'VoiceLine'):
                continue
            kw = {item.arg: item.value for item in call.keywords}
            row = dict(file=path, segment=cls.name, space=space,
                       index=ast.literal_eval(call.args[0]), actor=ast.unparse(call.args[1]),
                       line=call.lineno, end_line=call.end_lineno, end_col=call.end_col_offset,
                       delivery=ast.unparse(kw['delivery']) if 'delivery' in kw else None)
            row.update({key: ast.literal_eval(kw[key]) if key in kw else ''
                        for key in ('ru', 'en', 'comment')})
            row['key'] = f'{path}:{cls.name}:{row["index"]}'
            rows.append(row)
    return rows


def inventory():
    assert not (OUT / 'inventory.json').exists(), 'Keep the existing source baseline'
    files = sorted((PROJECT / 'story/scripts').rglob('mission*.py'))
    files += [PROJECT / name for name in ('audio/sound.py', 'audio/delivery.py',
                                         'tools/voicestudio.py')]
    hashes, rows = {}, []
    for path in files:
        relative = path.relative_to(PROJECT).as_posix()
        raw = path.read_bytes()
        hashes[relative] = sha(raw)
        snapshot = OUT / 'before' / relative
        snapshot.parent.mkdir(parents=True, exist_ok=True)
        snapshot.write_bytes(raw)
        if relative.startswith('story/scripts/'):
            rows.extend(scan(raw, relative))
    save(OUT / 'inventory.json', dict(files=hashes, lines=rows))
    for path in sorted({row['file'] for row in rows}):
        mission = Path(path).stem
        lines = [row for row in rows if row['file'] == path and row['en']]
        for space in (True, False):
            segment = None
            text = []
            for row in (r for r in lines if r['space'] == space):
                if row['segment'] != segment:
                    segment = row['segment']
                    text.append('\n' + segment)
                note = f' [direction: {row["comment"]}]' if row['comment'] else ''
                text.append(f'{row["index"]} {row["actor"]}: {row["en"]}{note}')
            target = OUT / 'review' / f'{mission}_{"space" if space else "scenes"}.txt'
            target.parent.mkdir(parents=True, exist_ok=True)
            target.write_text('\n'.join(text) + '\n', encoding='utf-8')
    print(f'Inventory: {len(rows)} active lines, {sum(bool(r["en"]) for r in rows)} EN, '
          f'{sum(bool(r["en"]) and r["space"] for r in rows)} EN space')


def authored():
    from space_direction import DIRECTION as space
    from scene_direction import DIRECTION as scenes
    result = {}
    for name, directions in [('space_direction.py', space), ('scene_direction.py', scenes)]:
        # Python accepts duplicate dict keys silently; authored reviews must not.
        for node in ast.walk(ast.parse((Path(__file__).parent / name).read_text(encoding='utf-8'))):
            if isinstance(node, ast.Dict):
                keys = [ast.literal_eval(key) for key in node.keys]
                assert len(keys) == len(set(keys)), f'Duplicate review key in {name}: {keys}'
        for segment, styles in directions.items():
            assert segment not in result, segment
            result[segment] = {}
            for style, indices in styles.items():
                for index in indices:
                    assert index not in result[segment], (segment, index)
                    result[segment][index] = style
    return result


def stripped_tree(raw):
    tree = ast.parse(raw.decode('utf-8-sig'))
    tree.body = [node for node in tree.body if not (
        isinstance(node, ast.ImportFrom) and node.module == 'audio' and
        any(alias.name == 'story_delivery' and alias.asname == 'performance' for alias in node.names))]
    for node in ast.walk(tree):
        if isinstance(node, ast.Call) and isinstance(node.func, ast.Name) and node.func.id == 'VoiceLine':
            node.keywords = [kw for kw in node.keywords if kw.arg != 'delivery_en']
    return ast.dump(tree, include_attributes=False)


def stage():
    from space_direction import CONTEXT
    baseline = json.loads((OUT / 'inventory.json').read_text(encoding='utf-8'))
    directions = authored()
    rows = baseline['lines']
    eligible = {row['segment'] for row in rows if row['en']}
    assert set(directions) == eligible, ('Unreviewed EN segment', eligible - set(directions))
    marked, updates = [], {}
    for segment, index_styles in directions.items():
        available = {row['index']: row for row in rows if row['segment'] == segment and row['en']}
        assert set(index_styles) <= set(available), (segment, set(index_styles) - set(available))
        for index, style in index_styles.items():
            row = available[index]
            assert row['actor'] not in ('Neuralnet', 'LogosRobot')
            marked.append(dict(row, style=style))
    for relative in sorted({row['file'] for row in marked}):
        raw = (OUT / 'before' / relative).read_bytes()
        assert sha(raw) == baseline['files'][relative]
        assert sha((PROJECT / relative).read_bytes()) == sha(raw), 'Source changed: ' + relative
        newline = b'\r\n' if b'\r\n' in raw else b'\n'
        lines = raw.splitlines(keepends=True)
        offsets = [0]
        for line in lines:
            offsets.append(offsets[-1] + len(line))
        calls = {(node.end_lineno, node.end_col_offset): node
                 for node in ast.walk(ast.parse(raw.decode('utf-8-sig')))
                 if isinstance(node, ast.Call) and isinstance(node.func, ast.Name)
                 and node.func.id == 'VoiceLine'}
        inserts = []
        for row in (r for r in marked if r['file'] == relative):
            end = row['end_line'] - 1
            col = row['end_col'] - 1
            assert lines[end][col:col + 1] == b')'
            before = lines[end][:col]
            marker = ('delivery_en=performance.' + row['style']).encode('ascii')
            if not before.strip():
                call = calls[(row['end_line'], row['end_col'])]
                last = max([*call.args, *(item.value for item in call.keywords)],
                           key=lambda node: (node.end_lineno, node.end_col_offset))
                last_end = offsets[last.end_lineno - 1] + last.end_col_offset
                if not raw[last_end:offsets[end] + col].lstrip().startswith(b','):
                    inserts.append((last_end, b','))
                inserts.append((offsets[end], before + b'    ' + marker + b',' + newline))
            else:
                prefix = b' ' if before.rstrip().endswith(b',') else b', '
                inserts.append((offsets[end] + col, prefix + marker))
        changed = raw
        for offset, addition in sorted(inserts, reverse=True):
            changed = changed[:offset] + addition + changed[offset:]
        changed = b'from audio import story_delivery as performance' + newline + changed
        assert stripped_tree(changed) == stripped_tree(raw), 'Non-performance change: ' + relative
        updates[relative] = changed

    relative = 'audio/sound.py'
    raw = (OUT / 'before' / relative).read_bytes()
    newline = '\r\n' if b'\r\n' in raw else '\n'
    source = raw.decode('utf-8').replace('\r\n', '\n')
    signature = "comment='', cinematic=False, delivery=None):"
    assert source.count(signature) == 1
    source = source.replace(signature, "comment='', cinematic=False, delivery=None, delivery_en=None):")
    anchor = '        self.delivery = delivery\n'
    assert source.count(anchor) == 1
    source = source.replace(anchor, anchor + '''        self.delivery_en = delivery_en

    def get_delivery(self, language):
        """EN acting direction overlays voice traits; RU retains legacy delivery."""
        if language != 'en' or self.delivery_en is None:
            return self.delivery
        from audio.delivery import Delivery
        base = self.delivery
        if base is None:
            getter = getattr(self.actor, 'get_voice_delivery', None)
            base = getter() if getter else getattr(self.actor, 'VOICE_DELIVERY', None)
        override = self.delivery_en
        return Delivery(
            override.code,
            instruct=override.instruct if override.instruct is not None else getattr(base, 'instruct', None),
            emo_text=override.emo_text,
            emo_alpha=override.emo_alpha,
            emo_vector=override.emo_vector,
            speed=override.speed if override.speed is not None else getattr(base, 'speed', None),
        )
''')
    updates[relative] = source.replace('\n', newline).encode('utf-8')
    relative = 'tools/voicestudio.py'
    raw = (OUT / 'before' / relative).read_bytes()
    start = raw.index(b'    def generate_en_voice(')
    end = raw.index(b'    def generate_ru_voice_simple(', start)
    method = raw[start:end]
    assert method.count(b'delivery=sound.line.delivery,') == 1
    updates[relative] = raw[:start] + method.replace(
        b'delivery=sound.line.delivery,', b"delivery=sound.line.get_delivery('en'),") + raw[end:]
    updates['audio/story_delivery.py'] = (Path(__file__).parent / 'story_delivery.py').read_bytes()
    assert not (PROJECT / 'audio/story_delivery.py').exists(), 'Review existing preset source'
    for relative, raw in updates.items():
        ast.parse(raw.decode('utf-8-sig'))
        target = OUT / 'stage' / relative
        target.parent.mkdir(parents=True, exist_ok=True)
        target.write_bytes(raw)
    plan = {'language': 'en', 'reviewed_en_lines': sum(bool(row['en']) for row in rows),
            'reviewed_space_lines': sum(bool(row['en']) and row['space'] for row in rows),
            'marked_lines': len(marked), 'marked_space_lines': sum(row['space'] for row in marked),
            'untranslated_lines_untouched': sum(not row['en'] for row in rows),
            'mission_context': CONTEXT, 'annotations': marked,
            'files': {name: {'before': baseline['files'].get(name), 'after': sha(raw)}
                      for name, raw in updates.items()},
            'audio_generated': False, 'data_written': False}
    save(OUT / 'plan.json', plan)
    with (OUT / 'direction.tsv').open('w', encoding='utf-8-sig', newline='') as stream:
        fields = ['file', 'segment', 'index', 'actor', 'space', 'style', 'en', 'comment']
        writer = csv.DictWriter(stream, fields, delimiter='\t', extrasaction='ignore')
        writer.writeheader()
        writer.writerows(sorted(marked, key=lambda row: (row['file'], row['line'])))
    print(f'Staged {len(updates)} source files: {len(marked)} EN markers '
          f'({plan["marked_space_lines"]} space); all {plan["reviewed_en_lines"]} EN lines reviewed.')


def publish():
    plan = json.loads((OUT / 'plan.json').read_text(encoding='utf-8'))
    checked = json.loads((OUT / 'checked.json').read_text(encoding='utf-8'))
    assert checked['plan_sha256'] == sha((OUT / 'plan.json').read_bytes())
    assert checked['passed']
    updates = []
    for relative, hashes in plan['files'].items():
        target = PROJECT / relative
        assert target.resolve().is_relative_to(PROJECT.resolve())
        before = target.read_bytes() if target.exists() else None
        assert (sha(before) if before is not None else None) == hashes['before'], 'Source changed: ' + relative
        raw = (OUT / 'stage' / relative).read_bytes()
        assert sha(raw) == hashes['after']
        updates.append((target, before, raw))
    touched = []
    try:
        for target, before, raw in updates:
            touched.append((target, before))
            target.write_bytes(raw)
        for target, _, raw in updates:
            assert target.read_bytes() == raw, target
    except Exception:
        for target, before in reversed(touched):
            if before is None:
                target.unlink(missing_ok=True)
            else:
                target.write_bytes(before)
        raise
    save(OUT / 'installed.json', dict(
        timestamp=datetime.datetime.now().isoformat(), files=plan['files'],
        marked_lines=plan['marked_lines'], marked_space_lines=plan['marked_space_lines'],
        ru_unchanged=True, audio_generated=False, data_written=False))
    print(f'Published {len(updates)} Pythonlancer source files; RU and existing audio untouched.')


if __name__ == '__main__':
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument('action', choices=['inventory', 'stage', 'publish'])
    args = parser.parse_args()
    globals()[args.action]()
