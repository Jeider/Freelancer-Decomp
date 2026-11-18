"""Install the checked object-only fog client. Cloud shaders/configs are immutable guards."""
import json
import os
from pathlib import Path
import sys

ROOT = Path(__file__).resolve().parents[2]
GAME = Path('D:/Games/FL_MOD')
OUT = ROOT / 'out/graphics_settings/nebula_object_fog/object_volume'
BUILD = OUT / 'build'
PLAN = OUT / 'install.json'
sys.path.insert(0, str(ROOT / 'tools/shader_startup'))
import install_animation as base
base.OUT, base.BUILD = OUT, BUILD
FILES = ('freelancer.exe', 'freelancer.pdb')


def optional(path):
    return base.digest(path) if path.exists() else None


def prepare():
    checks = json.loads((OUT / 'checks.json').read_text())
    assert checks['passed'] and not checks['shader_changes'] and not checks['profile_changes']
    assert base.digest(BUILD / 'bin/freelancer.exe') == checks['binary']
    for name, expected in checks['sources'].items():
        assert base.digest(ROOT / name) == expected, name
    for name, expected in checks['guards'].items():
        assert base.digest(Path(name)) == expected, name
    dependencies, count = base.verify_imports(('freelancer.exe',))
    guards = {**checks['guards'], **{str(GAME / 'bin' / name): optional(GAME / 'bin' / name)
              for name in ('RP9.dll', 'RP9.pdb', 'Server.dll', 'Content.dll', 'Common.dll',
                           'D3D9.dll', 'dgVoodoo.conf', 'port.ini')}}
    plan = {'files': {name: {'before': base.digest(GAME / 'bin' / name),
                            'after': base.digest(BUILD / 'bin' / name)} for name in FILES},
            'sources': checks['sources'], 'checks': base.digest(OUT / 'checks.json'),
            'dependencies': dependencies, 'guards': guards, 'verified_imports': count,
            'embedded_bytes': base.verify_resource(BUILD / 'bin/freelancer.exe'),
            'profile_changes': False, 'shader_changes': False, 'shader_cache_cleared': False,
            'game_launched': False, 'scope': checks['scope']}
    PLAN.write_text(json.dumps(plan, indent=2), encoding='utf-8')
    print(f'Ready: client + current symbols, {count} imports; cloud shaders/configs and asteroid population protected')


def apply():
    base.idle()
    plan = json.loads(PLAN.read_text())
    assert base.digest(OUT / 'checks.json') == plan['checks']
    for name, expected in plan['sources'].items():
        assert base.digest(ROOT / name) == expected, name
    for name, expected in plan['dependencies'].items():
        assert base.digest(GAME / 'bin' / name) == expected, name
    for name, expected in plan['guards'].items():
        assert optional(Path(name)) == expected, name
    prior = {}
    for name in FILES:
        target = base.safe(GAME / 'bin' / name, GAME / 'bin')
        assert base.digest(target) == plan['files'][name]['before'], name
        assert base.digest(BUILD / 'bin' / name) == plan['files'][name]['after'], name
        prior[name] = target.read_bytes()
    written = []
    try:
        for name in FILES:
            written.append(name)
            (GAME / 'bin' / name).write_bytes((BUILD / 'bin' / name).read_bytes())
        for name in FILES:
            assert base.digest(GAME / 'bin' / name) == plan['files'][name]['after'], name
        for name, expected in plan['guards'].items():
            assert optional(Path(name)) == expected, name
        base.verify_resource(GAME / 'bin/freelancer.exe')
    except BaseException:
        for name in reversed(written):
            (GAME / 'bin' / name).write_bytes(prior[name])
        raise
    prior.clear()
    plan['installed'] = True
    installed = OUT / 'installed.json'
    installed.write_text(json.dumps(plan, indent=2), encoding='utf-8')
    removed = base.cleanup()
    probe = base.safe(OUT / 'probe', OUT)
    candidates = []
    for directory, children, files in os.walk(probe, followlinks=False):
        for child in children:
            base.safe(Path(directory) / child, probe)
        for name in files:
            path = base.safe(Path(directory) / name, probe)
            if path.suffix.lower() in ('.exe', '.dll', '.obj', '.bin', '.pdb', '.ilk', '.exp', '.lib'):
                info = path.stat()
                candidates.append((path, info.st_size, info.st_mtime_ns))
    for path, size, modified in candidates:
        info = path.stat()
        assert (info.st_size, info.st_mtime_ns) == (size, modified), path
        path.unlink()
        removed += size
    plan['removed_build_bytes'] = removed
    installed.write_text(json.dumps(plan, indent=2), encoding='utf-8')
    print(f'Installed and verified client + symbols; all fog profiles/shaders unchanged; removed {removed/1024**2:.1f} MiB build/probe binaries; game not launched')


if __name__ == '__main__':
    apply() if '--apply' in sys.argv else prepare()
