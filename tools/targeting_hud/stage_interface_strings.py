"""Stage new HUD IDS in Pythonlancer and both DLLs; never modify the installed mod.

Once installed, translations live in Pythonlancer/text/static.py (managers.ids).
Only empty/new string slots are accepted. Every unrelated DLL resource is verified.
"""
import ast
import ctypes as c
from ctypes import wintypes as w
import hashlib
import json
from pathlib import Path
import re
import shutil
import struct

REPO = Path(__file__).resolve().parents[2]
GAME = Path('D:/games/FL_MOD')
STAGE = REPO / 'src/obj/hud_saved_tooltips/install'
ROWS = [
    ('TargetWindow', 'Показать/скрыть окно цели', 'Show/hide target window'),
    ('TargetLock', 'Запретить автоматическое открытие окна цели', 'Disable automatic target window opening'),
    ('TargetUnlock', 'Разрешить автоматическое открытие окна цели', 'Enable automatic target window opening'),
    ('AutoselectEnable', 'Включить выбор деталей под курсором', 'Enable subsystem selection under the cursor'),
    ('AutoselectDisable', 'Отключить выбор деталей под курсором', 'Disable subsystem selection under the cursor'),
    ('TargetVanilla', 'Цель: стандартный вид', 'Target: standard view'),
    ('TargetFit', 'Цель: вписать в окно', 'Target: fit to window'),
    ('TargetTop', 'Цель: вид сверху', 'Target: top view'),
    ('TargetRight', 'Цель: вид справа', 'Target: right view'),
    ('TargetClose', 'Закрыть окно цели', 'Close target window'),
    ('HealthWindow', 'Показать/скрыть состояние корабля', 'Show/hide ship status'),
    ('HealthLock', 'Запретить открытие окна при повреждениях', 'Disable opening on ship damage'),
    ('HealthUnlock', 'Разрешить открытие окна при повреждениях', 'Enable opening on ship damage'),
    ('WingPlay', 'Сложить/разложить крылья', 'Fold/unfold wings'),
    ('WingResume', 'Продолжить движение крыльев', 'Resume wing animation'),
    ('WingPause', 'Приостановить движение крыльев', 'Pause wing animation'),
    ('WingLock', 'Отключить автоматическое движение крыльев на круизе', 'Disable automatic cruise wing animation'),
    ('WingUnlock', 'Включить автоматическое движение крыльев на круизе', 'Enable automatic cruise wing animation'),
    ('HealthTop', 'Корабль: вид сверху', 'Ship: top view'),
    ('HealthLeft', 'Корабль: вид слева', 'Ship: left view'),
    ('HealthClose', 'Закрыть окно состояния корабля', 'Close ship status window'),
    ('WeaponGroup1', 'Группа орудий 1', 'Weapon group 1'),
    ('WeaponGroup2', 'Группа орудий 2', 'Weapon group 2'),
    ('WeaponGroup3', 'Группа орудий 3', 'Weapon group 3'),
    ('WeaponList', 'Показать список орудий', 'Show weapon list'),
]

k = c.WinDLL('kernel32', use_last_error=True)
ptr = c.c_void_p
type_cb = c.WINFUNCTYPE(w.BOOL, ptr, ptr, ptr)
name_cb = c.WINFUNCTYPE(w.BOOL, ptr, ptr, ptr, ptr)
lang_cb = c.WINFUNCTYPE(w.BOOL, ptr, ptr, ptr, w.WORD, ptr)
def api(name, args, result):
    fn = getattr(k, name)
    fn.argtypes, fn.restype = args, result
    return fn
load = api('LoadLibraryExW', [w.LPCWSTR, ptr, w.DWORD], ptr)
free = api('FreeLibrary', [ptr], w.BOOL)
types = api('EnumResourceTypesW', [ptr, type_cb, ptr], w.BOOL)
names = api('EnumResourceNamesW', [ptr, ptr, name_cb, ptr], w.BOOL)
langs = api('EnumResourceLanguagesW', [ptr, ptr, ptr, lang_cb, ptr], w.BOOL)
find = api('FindResourceExW', [ptr, ptr, ptr, w.WORD], ptr)
size = api('SizeofResource', [ptr, ptr], w.DWORD)
load_res = api('LoadResource', [ptr, ptr], ptr)
lock = api('LockResource', [ptr], ptr)
begin = api('BeginUpdateResourceW', [w.LPCWSTR, w.BOOL], ptr)
update = api('UpdateResourceW', [ptr, ptr, ptr, w.WORD, ptr, w.DWORD], w.BOOL)
end = api('EndUpdateResourceW', [ptr, w.BOOL], w.BOOL)

def check(value):
    if not value:
        raise c.WinError(c.get_last_error())
    return value

def resource_key(value):
    return value if value <= 65535 else c.wstring_at(value)

def resources(path):
    handle = check(load(str(path), None, 2))
    result, errors = {}, []
    @lang_cb
    def on_lang(h, t, n, lang, _):
        try:
            r = check(find(h, t, n, lang))
            result[(resource_key(t), resource_key(n), lang)] = c.string_at(check(lock(check(load_res(h, r)))), size(h, r))
            return True
        except Exception as e:
            errors.append(e)
            return False
    @name_cb
    def on_name(h, t, n, _):
        return langs(h, t, n, on_lang, None)
    @type_cb
    def on_type(h, t, _):
        return names(h, t, on_name, None)
    try:
        ok = types(handle, on_type, None)
        if errors:
            raise errors[0]
        check(ok)
    finally:
        check(free(handle))
    return result

def decode_block(data):
    result, offset = [], 0
    for _ in range(16):
        length, = struct.unpack_from('<H', data, offset)
        offset += 2
        result.append(data[offset:offset + 2 * length].decode('utf-16-le'))
        offset += 2 * length
    assert not any(data[offset:]), 'Unexpected trailing string-table data'
    return result

def encode_block(strings):
    result = b''
    for s in strings:
        encoded = s.encode('utf-16-le')
        result += struct.pack('<H', len(encoded) // 2) + encoded
    return result

def stage_dll(relative, column):
    original = GAME / relative
    output = STAGE / relative
    output.parent.mkdir(parents=True, exist_ok=True)
    before = resources(original)
    blocks = {}
    for i, row in enumerate(ROWS, 238200):
        assert i >> 16 == 3, 'NameResources.dll index must match freelancer.ini'
        local = i & 65535
        block, slot = local // 16 + 1, local % 16
        keys = [key for key in before if key[0] == 6 and key[1] == block] or [(6, block, 1033)]
        for key in keys:
            strings = blocks.setdefault(key, decode_block(before.get(key, b'\0' * 32)))
            assert strings[slot] in ('', row[column]), f'IDS collision: {i} {strings[slot]!r}'
            strings[slot] = row[column]
    shutil.copy2(original, output)
    handle = check(begin(str(output), False))
    try:
        for (kind, block, lang), strings in blocks.items():
            payload = encode_block(strings)
            buffer = c.create_string_buffer(payload)
            check(update(handle, kind, block, lang, buffer, len(payload)))
    except Exception:
        end(handle, True)
        raise
    check(end(handle, False))
    after = resources(output)
    expected = dict(before)
    expected.update({key: encode_block(value) for key, value in blocks.items()})
    assert after == expected, 'Unexpected resource change'
    # Explicitly check that even neighbouring strings in the edited blocks survived.
    occupied = {i & 65535 for i in range(238200, 238200 + len(ROWS))}
    for key in blocks:
        old = decode_block(before.get(key, b'\0' * 32))
        new = decode_block(after[key])
        for slot in range(16):
            if (key[1] - 1) * 16 + slot not in occupied:
                assert old[slot] == new[slot]
    print(f'PASS: {relative}: {len(ROWS)} strings, all unrelated resources preserved ({len(before)} resources)')

def main():
    relative = 'Assets/Pythonlancer/text/static.py'
    original = (GAME / relative).read_text(encoding='utf-8')
    tree = ast.parse(original)
    ids = [node.args[0].value for node in ast.walk(tree)
           if isinstance(node, ast.Call) and isinstance(node.func, ast.Name) and node.func.id == 'Static'
           and node.args and isinstance(node.args[0], ast.Constant)]
    assert not set(ids).intersection(range(238200, 238225)), 'New IDs already used in Pythonlancer'
    header = (REPO / 'src/freelancer/Client/hud_interface_ids.h').read_text()
    block = '    # HUD: Targeting / Health. MS(Russian, English); keep numeric IDs stable.\n'
    for i, (name, ru, en) in enumerate(ROWS, 238200):
        assert re.search(rf'\b{name}\s*=\s*{i}\s*;', header), name
        assert max(len(ru), len(en)) < 128
        block += f'    Static({i}, MS({ru!r}, {en!r})),  # {name}\n'
    patched = original.replace('STATIC_NAMES = [\n', 'STATIC_NAMES = [\n' + block + '\n', 1)
    assert patched != original
    ast.parse(patched)
    output = STAGE / relative
    output.parent.mkdir(parents=True, exist_ok=True)
    output.write_text(patched, encoding='utf-8')
    # Exercise the real Pythonlancer MultiString / IDsDatabase compiler without
    # importing its world generators or producing unrelated game data.
    namespace = {}
    exec(compile((GAME / 'Assets/Pythonlancer/text/strings.py').read_text(encoding='utf-8'), 'strings.py', 'exec'), namespace)
    db = namespace['IDsDatabase']('hud', 238199)
    for i, (_, ru, en) in enumerate(ROWS, 238200):
        db.add_force(i, namespace['MultiString'](ru, en))
    for language in ('ru', 'en'):
        text = getattr(db, 'compile_' + language)()
        (STAGE.parent / f'hud_strings_{language}.ini').write_text(text, encoding='utf-8')
        assert text.count('\nNAME\n') == len(ROWS)
    stage_dll('EXE/NameResources.dll', 1)
    stage_dll('RESOURCES_ENG/NameResources.dll', 2)
    print('PASS: IDs 238200..238224 match the C++ header and compile with Pythonlancer in RU/EN')
    sources = [relative, 'EXE/NameResources.dll', 'RESOURCES_ENG/NameResources.dll']
    manifest = [{'relative': f, 'original': hashlib.sha256((GAME/f).read_bytes()).hexdigest().upper(),
                 'prepared': hashlib.sha256((STAGE/f).read_bytes()).hexdigest().upper()} for f in sources]
    (STAGE.parent / 'strings_manifest.json').write_text(json.dumps(manifest, indent=2))

if __name__ == '__main__':
    main()
