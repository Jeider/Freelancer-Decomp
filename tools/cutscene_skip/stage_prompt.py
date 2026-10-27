"""Stage the skip prompt and a hash-checked installation payload; no game writes."""
import ast
import hashlib
import json
from pathlib import Path
import shutil
import sys

repo = Path(__file__).resolve().parents[2]
sys.path.insert(0, str(repo / 'tools/targeting_hud'))
import stage_interface_strings as ids

game = Path('D:/games/FL_MOD')
stage = repo / 'src/obj/cutscene_skip/install'
number = 238226
translations = ('Нажми Enter, чтобы пропустить катсцену', 'Press Enter to skip the cutscene')
assert f'CutsceneSkipPrompt = {number};' in (repo / 'src/freelancer/Client/hud_interface_ids.h').read_text()
relative = 'Assets/Pythonlancer/text/static.py'
original = (game / relative).read_text(encoding='utf-8')
tree = ast.parse(original)
used = [n.args[0].value for n in ast.walk(tree) if isinstance(n, ast.Call)
        and isinstance(n.func, ast.Name) and n.func.id == 'Static' and n.args
        and isinstance(n.args[0], ast.Constant)]
assert number not in used, 'ID already registered; review before staging again'
line = f'    Static({number}, MS({translations[0]!r}, {translations[1]!r})),  # CutsceneSkipPrompt\n'
patched = original.replace('STATIC_NAMES = [\n', 'STATIC_NAMES = [\n' + line, 1)
assert patched != original
ast.parse(patched)
output = stage / relative
output.parent.mkdir(parents=True, exist_ok=True)
output.write_text(patched, encoding='utf-8')
paths = [relative]
block, slot = (number & 65535) // 16 + 1, number % 16
for relative, caption in zip(('EXE/NameResources.dll', 'RESOURCES_ENG/NameResources.dll'), translations):
    before = ids.resources(game / relative)
    expected = dict(before)
    keys = [k for k in before if k[0] == 6 and k[1] == block] or [(6, block, 1033)]
    for key in keys:
        strings = ids.decode_block(before.get(key, b'\0' * 32))
        assert strings[slot] in ('', caption), f'Occupied IDS {number}: {strings[slot]}'
        strings[slot] = caption
        expected[key] = ids.encode_block(strings)
    output = stage / relative
    output.parent.mkdir(parents=True, exist_ok=True)
    shutil.copy2(game / relative, output)
    handle = ids.check(ids.begin(str(output), False))
    try:
        for kind, block_id, language in keys:
            payload = expected[kind, block_id, language]
            buffer = ids.c.create_string_buffer(payload)
            ids.check(ids.update(handle, kind, block_id, language, buffer, len(payload)))
    except Exception:
        ids.end(handle, True)
        raise
    ids.check(ids.end(handle, False))
    assert ids.resources(output) == expected, 'Unrelated DLL resource changed'
    paths.append(relative)

for relative in ('bin/freelancer.exe', 'bin/freelancer.pdb'):
    output = stage / relative
    output.parent.mkdir(parents=True, exist_ok=True)
    shutil.copy2(repo / relative, output)
    paths.append(relative)
digest = lambda p: hashlib.sha256(p.read_bytes()).hexdigest().upper()
dependencies = ('bin/Common.dll', 'bin/DALib.dll', 'bin/dacom.dll', 'bin/zlib.dll',
                'bin/imeui.dll', 'bin/freelancer.ini')
manifest = dict(game=str(game).replace('/', '\\'), files=[
    dict(relative=p, original=digest(game / p), prepared=digest(stage / p)) for p in paths],
    dependencies=[dict(relative=p, sha256=digest(game / p)) for p in dependencies])
(stage / 'manifest.json').write_text(json.dumps(manifest, indent=2))
installer = Path(__file__).with_name('install.ps1').read_text()
(stage / 'install.ps1').write_text(installer)
print('PASS: client, RU/EN prompt and Pythonlancer staged; unrelated resources preserved')
