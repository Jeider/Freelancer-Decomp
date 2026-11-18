"""Install the verified no-INTZ corridor client; keep RP9 and the shader cache intact."""
from pathlib import Path
import hashlib
import json
import sys

ROOT = Path(__file__).resolve().parents[2]
OUT = ROOT / 'out/tradelane_depth/no_intz'
sys.path.insert(0, str(ROOT / 'tools/shader_startup'))
import install_animation as base

NAMES = ('freelancer.exe', 'freelancer.pdb')
PLAN = OUT / 'install.json'


def prepare():
    checked = json.loads((OUT / 'verified.json').read_text())
    for path, expected in checked.items():
        assert base.digest(Path(path)) == expected, 'Changed after check: ' + path
    exe = base.BUILD / 'bin/freelancer.exe'
    assert exe.stat().st_mtime >= (ROOT / 'src/freelancer/Client/tradelane_visual.cpp').stat().st_mtime
    dependencies, imports = base.verify_imports(('freelancer.exe',))
    dependencies['RP9.dll'] = base.digest(base.GAME / 'RP9.dll')
    plan = dict(files={name: dict(before=base.digest(base.GAME / name), after=base.digest(base.BUILD / 'bin' / name))
                            for name in NAMES}, dependencies=dependencies, verified_imports=imports,
                checked=checked, embedded_bytes=base.verify_resource(exe), cache_policy='unchanged')
    PLAN.write_text(json.dumps(plan, indent=2))
    print(f'Ready: client + symbols; {imports} imports checked; animation embedded; shader cache unchanged')


def apply():
    base.idle()
    plan = json.loads(PLAN.read_text())
    for path, expected in plan['checked'].items():
        assert base.digest(Path(path)) == expected, 'Changed after check: ' + path
    for name, expected in plan['dependencies'].items():
        assert base.digest(base.GAME / name) == expected, 'Dependency changed: ' + name
    previous = {}
    for name in NAMES:
        target = base.safe(base.GAME / name, base.GAME)
        source = base.safe(base.BUILD / 'bin' / name, base.BUILD)
        previous[name] = target.read_bytes()
        assert hashlib.sha256(previous[name]).hexdigest() == plan['files'][name]['before'], name
        assert base.digest(source) == plan['files'][name]['after'], name
    written = []
    try:
        for name in NAMES:
            written.append(name)
            (base.GAME / name).write_bytes((base.BUILD / 'bin' / name).read_bytes())
        for name in NAMES:
            assert base.digest(base.GAME / name) == plan['files'][name]['after'], name
        base.verify_resource(base.GAME / 'freelancer.exe')
    except BaseException:
        for name in written:
            (base.GAME / name).write_bytes(previous[name])
        raise
    previous.clear()
    plan['build_cleanup_bytes'] = base.cleanup()
    # These intermediates belong only to this regression check, not other tasks.
    for name in ('caller.obj', 'caller.exe', 'check_tradelane_render.obj', 'gpu.exe'):
        path = base.safe(OUT / name, OUT)
        if path.exists():
            path.unlink()
    (OUT / 'installed.json').write_text(json.dumps(plan, indent=2))
    print(f'Installed and hash-verified client + symbols; cache unchanged; cleaned {plan["build_cleanup_bytes"]} build bytes')


if __name__ == '__main__':
    apply() if '--apply' in sys.argv else prepare()
