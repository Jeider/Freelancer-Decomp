"""Install the checked Omega-15 fog trial into bin and DATA_EXTRA. Never launches the game."""
import argparse
import json
import os
from pathlib import Path
import sys

ROOT = Path(__file__).resolve().parents[2]
OUT = ROOT / 'out/graphics_settings/nebula_object_fog'
BUILD = OUT / 'build'
GAME = Path('D:/Games/FL_MOD')
sys.path.insert(0, str(ROOT / 'tools/shader_startup'))
import install_animation as base
base.OUT, base.BUILD = OUT, BUILD
MANIFEST = OUT / 'install.json'
SHADER = 'DATA_EXTRA/SHADERS/surface_material.hlsl'
FILES = {**{'bin/' + n: BUILD / 'bin' / n for n in base.FILES}, SHADER: ROOT / SHADER}


def optional_digest(path):
    return base.digest(path) if path.exists() else None


def prepare():
    checks = json.loads((OUT / 'checks.json').read_text())
    assert checks['route'] == checks['manifest'] == 'PASS'
    for name, expected in checks['sources'].items():
        assert base.digest(ROOT / name) == expected, 'Checked source changed: ' + name
    for name, expected in checks['binaries'].items():
        assert base.digest(BUILD / 'bin' / name) == expected, 'Checked build changed: ' + name
    dependencies, count = base.verify_imports()
    resource_size = base.verify_resource(BUILD / 'bin/freelancer.exe')
    guards = {name: optional_digest(GAME / 'bin' / name) for name in ('D3D9.dll', 'dgVoodoo.conf', 'port.ini')}
    manifest = {'files': {name: {'before': optional_digest(GAME / name), 'after': base.digest(source)}
                          for name, source in FILES.items()},
                'checks': base.digest(OUT / 'checks.json'), 'dependencies': dependencies,
                'guards': guards, 'verified_imports': count, 'embedded_animation_bytes': resource_size,
                'system': 'om15', 'shader_cache_cleared': False, 'game_launched': False,
                'cache_directory': str(base.cache_path()), 'cache_files': checks['cache_files']}
    MANIFEST.write_text(json.dumps(manifest, indent=2), encoding='utf-8')
    print(f'Ready: {len(FILES)} files; {count} imports verified; Omega-15 only')


def apply():
    base.idle()
    manifest = json.loads(MANIFEST.read_text())
    assert base.digest(OUT / 'checks.json') == manifest['checks']
    for name, expected in manifest['dependencies'].items():
        assert base.digest(GAME / 'bin' / name) == expected, 'Dependency changed: ' + name
    for name, expected in manifest['guards'].items():
        assert optional_digest(GAME / 'bin' / name) == expected, 'Protected setting changed: ' + name
    prior = {}
    for name, source in FILES.items():
        target = base.safe(GAME / name, GAME)
        assert optional_digest(target) == manifest['files'][name]['before'], 'Target changed: ' + name
        assert base.digest(source) == manifest['files'][name]['after'], 'Prepared source changed: ' + name
        prior[name] = target.read_bytes() if target.exists() else None
    cache = base.safe(Path(manifest['cache_directory']), base.cache_path())
    cached = []
    for name, expected in manifest['cache_files'].items():
        source = base.safe(OUT / 'probe/manifest_cache' / name, OUT / 'probe/manifest_cache')
        assert base.digest(source) == expected, 'Validated shader bytecode changed: ' + name
    written = []
    try:
        for name, source in FILES.items():
            written.append(name)
            (GAME / name).write_bytes(source.read_bytes())
        for name in FILES:
            assert base.digest(GAME / name) == manifest['files'][name]['after'], name
        for name, expected in manifest['guards'].items():
            assert optional_digest(GAME / 'bin' / name) == expected, name
        base.verify_resource(GAME / 'bin/freelancer.exe')
        cache.mkdir(parents=True, exist_ok=True)
        for name, expected in manifest['cache_files'].items():
            target = base.safe(cache / name, cache)
            # Existing entries are immutable here. Keys include the expanded source
            # and compiler identity; unchanged shaders need no rewrite or deletion.
            if target.exists():
                continue
            cached.append(target)
            with target.open('xb') as stream:
                stream.write((OUT / 'probe/manifest_cache' / name).read_bytes())
            assert base.digest(target) == expected
    except BaseException:
        for target in reversed(cached):
            base.safe(target, cache).unlink(missing_ok=True)
        for name in reversed(written):
            target = base.safe(GAME / name, GAME)
            if prior[name] is None:
                target.unlink(missing_ok=True)
            else:
                target.write_bytes(prior[name])
        raise
    prior.clear()
    # Installed current symbols are kept. Only this task's verified build/probe is removed.
    removed = base.cleanup()
    probe = base.safe(OUT / 'probe', OUT)
    for directory, children, files in os.walk(probe, followlinks=False):
        for child in children:
            base.safe(Path(directory) / child, probe)
        for name in files:
            path = base.safe(Path(directory) / name, probe)
            before = path.stat()
            assert path.stat().st_mtime_ns == before.st_mtime_ns
            removed += before.st_size
            path.unlink()
    manifest.update(installed=True, removed_build_bytes=removed, warmed_shader_entries=len(cached))
    (OUT / 'installed.json').write_text(json.dumps(manifest, indent=2), encoding='utf-8')
    print(f'Installed and verified {len(FILES)} files; warmed {len(cached)} missing shader entries; removed {removed / 1024**2:.1f} MiB of build/probe artifacts')


if __name__ == '__main__':
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument('--apply', action='store_true')
    args = parser.parse_args()
    apply() if args.apply else prepare()
