"""Remove the rejected full-fog trial, preserving the previous volume and asteroids."""
import hashlib
import json
from pathlib import Path
import sys

ROOT = Path(__file__).resolve().parents[2]
GAME = Path('D:/Games/FL_MOD')
OUT = ROOT / 'out/graphics_settings/nebula_object_fog/full_volume'
MESH = ROOT / 'out/graphics_settings/nebula_asteroid_mesh'
CONFIG = 'DATA_EXTRA/VOLUMETRIC/volumetric.ini'
BEGIN = b'; BEGIN Omega-15 full volume trial'
END = b'; END Omega-15 full volume trial'
PLAN = OUT / 'restore_plan.json'
STAGED = OUT / 'previous_volumetric.ini'


def sha(raw):
    return hashlib.sha256(raw).hexdigest()


def remove_trial(raw):
    assert raw.count(BEGIN) == raw.count(END) == 1
    start, end = raw.index(BEGIN), raw.index(END) + len(END)
    assert not raw[end:].strip(), 'Unexpected content after trial; review before restoring'
    newline = b'\r\n' if b'\r\n' in raw else b'\n'
    result = raw[:start].rstrip(b'\r\n') + newline
    assert b'om15_full_volume' not in result
    return result


def prepare():
    manifest = json.loads((MESH / 'omega15_installed.json').read_text())
    original = (GAME / CONFIG).read_bytes()
    restored = remove_trial(original)
    assert sha(restored) == manifest['files'][CONFIG]['before'], 'Prior config has changed'
    STAGED.write_bytes(restored)
    sources = [ROOT / CONFIG, MESH / 'stage' / CONFIG]
    for path in sources:
        path.write_bytes(remove_trial(path.read_bytes()))
    guards = {str(GAME / name): sha((GAME / name).read_bytes())
              for name in manifest['files'] if name != CONFIG}
    plan = {'target': str(GAME / CONFIG), 'before': sha(original), 'after': sha(restored),
            'matches_pre_trial_config': True, 'guards': guards,
            'local_configs': {str(p): sha(p.read_bytes()) for p in sources},
            'game_launched': False}
    PLAN.write_text(json.dumps(plan, indent=2), encoding='utf-8')
    print('Prepared exact pre-trial volume config; repository/staging restored; live game unchanged')


def apply():
    plan = json.loads(PLAN.read_text())
    target = GAME / CONFIG
    assert str(target) == plan['target']
    before, restored = target.read_bytes(), STAGED.read_bytes()
    assert sha(before) == plan['before'] and sha(restored) == plan['after']
    for name, expected in {**plan['guards'], **plan['local_configs']}.items():
        assert sha(Path(name).read_bytes()) == expected, name
    # DATA_EXTRA is a renderer configuration directory, not Pythonlancer DATA.
    try:
        target.write_bytes(restored)
        assert sha(target.read_bytes()) == plan['after']
        for name, expected in plan['guards'].items():
            assert sha(Path(name).read_bytes()) == expected, name
    except BaseException:
        target.write_bytes(before)
        raise
    plan['installed'] = True
    (OUT / 'restored.json').write_text(json.dumps(plan, indent=2), encoding='utf-8')
    print('Restored exact pre-trial volume config; client, asteroid count/fades and generator unchanged')


if __name__ == '__main__':
    apply() if '--apply' in sys.argv else prepare()
