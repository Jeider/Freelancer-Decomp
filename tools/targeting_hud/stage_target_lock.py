"""Update only Targeting lock/unlock captions in Pythonlancer and both language DLLs."""
import ast
import hashlib
import json
from pathlib import Path
import shutil
import stage_interface_strings as ids

repo = Path(__file__).resolve().parents[2]
game = Path('D:/games/FL_MOD')
stage = repo / 'src/obj/targeting_lock/install'
relative = 'Assets/Pythonlancer/text/static.py'
original = (game / relative).read_text(encoding='utf-8')
lines = original.splitlines(keepends=True)
changes = {}
for node in ast.walk(ast.parse(original)):
    if not (isinstance(node, ast.Call) and isinstance(node.func, ast.Name) and node.func.id == 'Static'
            and node.args and isinstance(node.args[0], ast.Constant)):
        continue
    number = node.args[0].value
    if number not in (238201, 238202):
        continue
    assert node.lineno == node.end_lineno
    old = tuple(ast.literal_eval(arg) for arg in node.args[1].args)
    name, ru, en = ids.ROWS[number - 238200]
    changes[number] = (old, (ru, en))
    lines[node.lineno - 1] = f'    Static({number}, MS({ru!r}, {en!r})),  # {name}\n'
assert len(changes) == 2
patched = ''.join(lines)
ast.parse(patched)
dest = stage / relative
dest.parent.mkdir(parents=True, exist_ok=True)
dest.write_text(patched, encoding='utf-8')
paths = [relative]
for column, relative in enumerate(('EXE/NameResources.dll', 'RESOURCES_ENG/NameResources.dll')):
    before = ids.resources(game / relative)
    expected = dict(before)
    touched = set()
    for number, (old, new) in changes.items():
        block, slot = (number & 65535) // 16 + 1, number % 16
        keys = [key for key in before if key[0] == 6 and key[1] == block]
        assert keys
        for key in keys:
            strings = ids.decode_block(expected[key])
            assert strings[slot] in (old[column], new[column]), 'Installed caption differs from Pythonlancer'
            strings[slot] = new[column]
            expected[key] = ids.encode_block(strings)
            touched.add(key)
    dest = stage / relative
    dest.parent.mkdir(parents=True, exist_ok=True)
    shutil.copy2(game / relative, dest)
    handle = ids.check(ids.begin(str(dest), False))
    try:
        for kind, block, language in touched:
            payload = expected[kind, block, language]
            buffer = ids.c.create_string_buffer(payload)
            ids.check(ids.update(handle, kind, block, language, buffer, len(payload)))
    except Exception:
        ids.end(handle, True)
        raise
    ids.check(ids.end(handle, False))
    assert ids.resources(dest) == expected, 'Unrelated resource changed'
    paths.append(relative)
digest = lambda p: hashlib.sha256(p.read_bytes()).hexdigest().upper()
(stage.parent / 'strings_manifest.json').write_text(json.dumps([
    dict(relative=p, original=digest(game/p), prepared=digest(stage/p)) for p in paths], indent=2))
print('PASS: lock/unlock captions staged in RU/EN and Pythonlancer; all other DLL resources preserved')
