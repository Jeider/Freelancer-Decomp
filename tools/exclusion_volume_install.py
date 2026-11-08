"""Stage/check/install measured Om15 shell palettes into Pythonlancer only."""
import argparse
import ast
from datetime import datetime
import hashlib
import json
from pathlib import Path
from types import SimpleNamespace

ROOT = Path('D:/games/FL_MOD/Assets/Pythonlancer')
OUT = Path('src/obj/exclusion_volume')
RELATIVE = 'templates/nebula/om15_orange_nebula.py'
SHELL = 'solar\\nebula_mod\\exclusion_walker_new.3db'


def sha(data): return hashlib.sha256(data).hexdigest()


def prepare():
    original = (ROOT / RELATIVE).read_bytes()
    text = original.decode('utf-8').replace('\r\n', '\n')
    targets = json.loads((OUT / 'targets.json').read_text())
    for name, target in targets.items():
        header = f'class {name}(SimpleTemplate):\n'
        assert text.count(header) == 1
        assert 'EXCLUSION_TINT_BY_SHELL' not in ast.get_source_segment(text, next(
            n for n in ast.parse(text).body if isinstance(n, ast.ClassDef) and n.name == name))
        tint = ', '.join(map(str, target['tint']))
        text = text.replace(header, header +
            '    # Matched to GPU-rendered walker midtones with Om15 lighting/exposure.\n'
            '    # The exclusion shell is unlit; keep max_alpha and the model unchanged.\n'
            f'    EXCLUSION_TINT_BY_SHELL = {{{SHELL!r}: {tint!r}}}\n\n')
    tree = ast.parse(text)
    ns = {}
    exec(compile((ROOT / 'templates/nebula/exclusion.py').read_bytes(), 'exclusion.py', 'exec'), ns)
    for cls in tree.body:
        if not isinstance(cls, ast.ClassDef): continue
        attrs = {t.id: ast.literal_eval(n.value) for n in cls.body if isinstance(n, ast.Assign)
                 for t in n.targets if isinstance(t, ast.Name) and t.id in ('TEMPLATE', 'EXCLUSION_TINT_BY_SHELL')}
        params = {'zone_shell': SHELL, 'shell_scalar': 1.1, 'max_alpha': .5,
                  'fog_far': 15000, 'exclusion_tint': '255, 255, 255'}
        updated = ns['match_exclusion_palette'](SimpleNamespace(**attrs), params)
        assert updated['exclusion_tint'] == ', '.join(map(str, targets[cls.name]['tint']))
        assert params['exclusion_tint'] == '255, 255, 255'
        assert all(updated[k] == params[k] for k in params if k != 'exclusion_tint')
        original_template = next(ast.literal_eval(n.value) for n in next(c for c in ast.parse(original).body
            if isinstance(c, ast.ClassDef) and c.name == cls.name).body
            if isinstance(n, ast.Assign) and n.targets[0].id == 'TEMPLATE')
        assert attrs['TEMPLATE'] == original_template
    newline = '\r\n' if b'\r\n' in original else '\n'
    data = text.replace('\n', newline).encode('utf-8')
    (OUT / 'om15_staged.py').write_bytes(data)
    (OUT / 'install_manifest.json').write_text(json.dumps({'before':sha(original), 'after':sha(data),
        'sigma8':sha((ROOT/'templates/nebula/sig8_nebula.py').read_bytes()),
        'helper':sha((ROOT/'templates/nebula/exclusion.py').read_bytes())},indent=2))
    print('PASS: four Om15 palette overrides; original INI templates, alpha, geometry and shared dictionaries preserved')


def apply():
    manifest=json.loads((OUT/'install_manifest.json').read_text())
    original=(ROOT/RELATIVE).read_bytes(); data=(OUT/'om15_staged.py').read_bytes()
    assert sha(original)==manifest['before'] and sha(data)==manifest['after']
    for file,key in [('sig8_nebula.py','sigma8'),('exclusion.py','helper')]:
        assert sha((ROOT/'templates/nebula'/file).read_bytes())==manifest[key]
    backup=OUT/('backup_'+datetime.now().strftime('%Y%m%d_%H%M%S')+'.py')
    backup.write_bytes(original)
    (ROOT/RELATIVE).write_bytes(data)
    assert sha((ROOT/RELATIVE).read_bytes())==manifest['after']
    print('Installed and verified', ROOT/RELATIVE, '; backup:', backup)


if __name__=='__main__':
    parser=argparse.ArgumentParser();parser.add_argument('--apply',action='store_true')
    apply() if parser.parse_args().apply else prepare()
