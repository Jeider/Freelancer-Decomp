"""Fill the three missing English lines; preserve all other source bytes."""
import ast
from pathlib import Path
import sys


TARGET = Path('D:/Games/FL_MOD/Assets/Pythonlancer/story/scripts/main/mission7.py')
TRANSLATIONS = {
    160: "There's a problem. Almost all the electronics on my ship are fried. I don't even know how I made it here alive.",
    170: "(after a long silence and an eye roll) All right, I'll give you one of our ships.",
    180: "(threateningly) But if you're thinking of taking off with it, keep in mind that all our ships have tracking beacons. I'll find you wherever you go.",
}


def prepare(raw):
    text = raw.decode('utf-8')
    tree = ast.parse(text)
    scene = next(n for n in tree.body if isinstance(n, ast.ClassDef) and n.name == 'Msn7Battleship')
    lines = raw.splitlines(keepends=True)
    found = set()
    for node in ast.walk(scene):
        if not isinstance(node, ast.Call) or not isinstance(node.func, ast.Name) or node.func.id != 'VoiceLine':
            continue
        index = ast.literal_eval(node.args[0])
        if index not in TRANSLATIONS:
            continue
        keyword = next(k for k in node.keywords if k.arg == 'en')
        value = keyword.value
        existing = ast.literal_eval(value)
        if existing not in ('', TRANSLATIONS[index]):
            raise RuntimeError(f'Line {index} already has a different translation')
        if value.lineno != value.end_lineno:
            raise RuntimeError('Expected a single-line English literal')
        line = lines[value.lineno - 1]
        replacement = ('"' + TRANSLATIONS[index] + '"').encode('utf-8')
        lines[value.lineno - 1] = line[:value.col_offset] + replacement + line[value.end_col_offset:]
        found.add(index)
        print(f'{index}: {TRANSLATIONS[index]}')
    if found != set(TRANSLATIONS):
        raise RuntimeError('Missing expected voice lines')
    result = b''.join(lines)
    compile(result, str(TARGET), 'exec')
    expected = ast.parse(text)
    expected_scene = next(n for n in expected.body if isinstance(n, ast.ClassDef) and n.name == 'Msn7Battleship')
    for node in ast.walk(expected_scene):
        if isinstance(node, ast.Call) and isinstance(node.func, ast.Name) and node.func.id == 'VoiceLine':
            index = ast.literal_eval(node.args[0])
            english = next(k for k in node.keywords if k.arg == 'en')
            if index in TRANSLATIONS:
                english.value = ast.Constant(TRANSLATIONS[index])
            if not ast.literal_eval(english.value).strip():
                raise RuntimeError(f'English line {index} is still empty')
    assert ast.dump(ast.parse(result)) == ast.dump(expected), 'Unexpected source changes'
    return result


original = TARGET.read_bytes()
updated = prepare(original)
if '--apply' in sys.argv:
    if TARGET.read_bytes() != original:
        raise RuntimeError('Source changed during preparation')
    TARGET.write_bytes(updated)
    assert TARGET.read_bytes() == updated
    print('Applied and verified: only English lines 160, 170 and 180 changed.')
else:
    print('Validated; use --apply to write the translations.')
