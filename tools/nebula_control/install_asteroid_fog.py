"""Install checked sparse-object fog repair, without changing clouds/content/cache."""
import json
import os
from pathlib import Path
import sys

ROOT = Path(__file__).resolve().parents[2]
GAME = Path('D:/Games/FL_MOD')
OUT = ROOT / 'out/graphics_settings/nebula_asteroid_mesh/fog_surface'
BUILD = OUT / 'build'
PLAN = OUT / 'install.json'
sys.path.insert(0, str(ROOT / 'tools/shader_startup'))
import install_animation as base
base.OUT, base.BUILD = OUT, BUILD
FILES = {'bin/freelancer.exe': BUILD / 'bin/freelancer.exe',
         'bin/freelancer.pdb': BUILD / 'bin/freelancer.pdb',
         'DATA_EXTRA/SHADERS/nebula_composite.hlsl': ROOT / 'DATA_EXTRA/SHADERS/nebula_composite.hlsl'}
REPORTS = ('checks.json', 'surfaces/checks.json')
SHADERS = ['nebula_composite.hlsl']
SCOPE = 'Omega-15 medium/high object volume: sparse-depth sampling only'
BINARIES = ('freelancer.exe',)


def optional(path):
    return base.digest(path) if path.exists() else None


def prepare():
    sources, guards, checks = {}, {}, {}
    for name in REPORTS:
        path = OUT / name
        report = json.loads(path.read_text())
        assert report['passed'] and not report['profile_changes']
        assert report['shader_changes'] == SHADERS
        assert base.digest(BUILD / 'bin/freelancer.exe') == report['binary']
        checks[name] = base.digest(path)
        sources.update(report['sources'])
        guards.update(report['guards'])
    # Existing native asteroid assets are read-only inputs, not installation files.
    assets = json.loads((OUT.parent / 'checks.json').read_text())['assets']
    guards.update(assets)
    for name, expected in sources.items():
        assert base.digest(ROOT / name) == expected, name
    for name, expected in guards.items():
        assert base.digest(Path(name)) == expected, name
    # The changed installed shader is checked as a transaction file below.
    for name in FILES:
        guards.pop(str(GAME / name), None)
    guards.update({str(GAME / 'bin' / name): optional(GAME / 'bin' / name)
                   for name in ('RP9.dll', 'RP9.pdb', 'Common.dll', 'Server.dll',
                                'Content.dll', 'D3D9.dll', 'dgVoodoo.conf', 'port.ini')})
    for name in FILES:
        guards.pop(str(GAME/name),None)
    dependencies, count = base.verify_imports(BINARIES)
    plan = {'files': {name: {'before': base.digest(GAME / name),
                            'after': base.digest(source)} for name, source in FILES.items()},
            'sources': sources, 'checks': checks, 'guards': guards,
            'dependencies': dependencies, 'verified_imports': count,
            'embedded_bytes': base.verify_resource(BUILD / 'bin/freelancer.exe'),
            'installer': base.digest(Path(__file__)),
            'scope': SCOPE,
            'profile_changes': False, 'shader_cache_cleared': False, 'game_launched': False}
    PLAN.write_text(json.dumps(plan, indent=2), encoding='utf-8')
    print(f'Ready: {len(FILES)} files, {count} verified imports; cloud profiles, raymarch and asteroid assets protected')


def cleanup_probes():
    candidates = []
    for folder in (OUT / 'probe', OUT / 'surfaces/probe'):
        base.safe(folder, OUT)
        for directory, children, files in os.walk(folder, followlinks=False):
            for child in children:
                base.safe(Path(directory) / child, folder)
            for name in files:
                path = base.safe(Path(directory) / name, folder)
                if path.suffix.lower() in ('.exe', '.dll', '.obj', '.bin', '.pdb', '.ilk', '.exp', '.lib', '.texture'):
                    info = path.stat()
                    candidates.append((path, info.st_size, info.st_mtime_ns))
    removed = 0
    for path, size, modified in candidates:
        info = path.stat()
        assert (info.st_size, info.st_mtime_ns) == (size, modified), path
        path.unlink()
        removed += size
    return removed


def apply():
    base.idle()
    plan = json.loads(PLAN.read_text())
    assert base.digest(Path(__file__)) == plan['installer']
    for name, expected in plan['checks'].items():
        assert base.digest(OUT / name) == expected, name
    for name, expected in plan['sources'].items():
        assert base.digest(ROOT / name) == expected, name
    for name, expected in plan['dependencies'].items():
        assert base.digest(GAME / 'bin' / name) == expected, name
    for name, expected in plan['guards'].items():
        assert optional(Path(name)) == expected, name
    prior = {}
    for name, source in FILES.items():
        target = base.safe(GAME / name, GAME)
        assert base.digest(target) == plan['files'][name]['before'], name
        assert base.digest(source) == plan['files'][name]['after'], name
        prior[name] = target.read_bytes()
    written = []
    try:
        for name, source in FILES.items():
            written.append(name)
            (GAME / name).write_bytes(source.read_bytes())
        for name in FILES:
            assert base.digest(GAME / name) == plan['files'][name]['after'], name
        for name, expected in plan['guards'].items():
            assert optional(Path(name)) == expected, name
        base.verify_resource(GAME / 'bin/freelancer.exe')
    except BaseException:
        for name in reversed(written):
            (GAME / name).write_bytes(prior[name])
        raise
    prior.clear()
    plan['installed'] = True
    installed = OUT / 'installed.json'
    installed.write_text(json.dumps(plan, indent=2), encoding='utf-8')
    plan['removed_build_bytes'] = base.cleanup() + cleanup_probes()
    installed.write_text(json.dumps(plan, indent=2), encoding='utf-8')
    print(f'Installed and hash-verified {len(FILES)} files; cloud/content guards unchanged; removed {plan["removed_build_bytes"]/1024**2:.1f} MiB staging/intermediates; no game launch, no cache reset')


if __name__ == '__main__':
    apply() if '--apply' in sys.argv else prepare()
