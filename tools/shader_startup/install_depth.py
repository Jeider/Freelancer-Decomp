"""Install the verified shared scene-depth fix and remove hyperjump contrails; preserve the shader cache."""
import hashlib
import json
from pathlib import Path
import sys
import install_animation as base

OUT = base.OUT / 'depth'
PLAN = OUT / 'install.json'


def prepare():
    checked = json.loads((OUT / 'verified.json').read_text())
    for path, expected in checked.items():
        assert base.digest(Path(path)) == expected, 'Changed after check: ' + path
    for name, sources in {'RP9.dll': ('src/RP9/RP9.cpp', 'src/RP9/RP9Ex.cpp'),
                          'freelancer.exe': ('src/freelancer/Client/ship_warp_visual.cpp',)}.items():
        assert (base.BUILD / 'bin' / name).stat().st_mtime >= max((base.ROOT / p).stat().st_mtime for p in sources)
    dependencies, imports = base.verify_imports()
    plan = dict(files={name: dict(before=base.digest(base.GAME / name), after=base.digest(base.BUILD / 'bin' / name))
                       for name in base.FILES}, dependencies=dependencies, verified_imports=imports, checked=checked,
                embedded_bytes=base.verify_resource(base.BUILD / 'bin/freelancer.exe'), cache_policy='unchanged',
                cause='D32 preference disabled INTZ on dgVoodoo despite supported depth-texture sampling',
                change='Prefer compatible 24-bit scene depth when INTZ is supported; omit hyperjump contrail anchors')
    PLAN.write_text(json.dumps(plan, indent=2))
    print(f'Ready: RP9 + client + symbols; {imports} imports checked; shader cache unchanged')


def apply():
    base.idle()
    plan = json.loads(PLAN.read_text())
    for path, expected in plan['checked'].items():
        assert base.digest(Path(path)) == expected, 'Changed after check: ' + path
    for name, expected in plan['dependencies'].items():
        assert base.digest(base.GAME / name) == expected, 'Dependency changed: ' + name
    previous = {}
    for name in base.FILES:
        target = base.safe(base.GAME / name, base.GAME)
        source = base.safe(base.BUILD / 'bin' / name, base.BUILD)
        previous[name] = target.read_bytes()
        assert hashlib.sha256(previous[name]).hexdigest() == plan['files'][name]['before'], name
        assert base.digest(source) == plan['files'][name]['after'], name
    written = []
    try:
        for name in base.FILES:
            written.append(name)
            (base.GAME / name).write_bytes((base.BUILD / 'bin' / name).read_bytes())
        for name in base.FILES:
            assert base.digest(base.GAME / name) == plan['files'][name]['after'], name
        base.verify_resource(base.GAME / 'freelancer.exe')
    except BaseException:
        for name in written:
            (base.GAME / name).write_bytes(previous[name])
        raise
    previous.clear()
    plan['build_cleanup_bytes'] = base.cleanup()
    for name in ('probe.exe', 'check_depth_device.obj', 'policy.exe', 'policy.obj'):
        path = base.safe(OUT / name, OUT)
        if path.exists():
            path.unlink()
    (OUT / 'installed.json').write_text(json.dumps(plan, indent=2))
    print(f'Installed and hash-verified {len(base.FILES)} files; cache unchanged; cleaned {plan["build_cleanup_bytes"]} build bytes')


if __name__ == '__main__':
    apply() if '--apply' in sys.argv else prepare()
