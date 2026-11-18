"""Install the client subtitle visibility fix; keep installed dependencies intact."""
import hashlib
import json
from pathlib import Path
import sys

ROOT = Path(__file__).resolve().parents[2]
OUT = ROOT / 'out/story_cutscenes/subtitles'
sys.path.insert(0, str(ROOT / 'tools/shader_startup'))
import install_animation as base
base.OUT = OUT
base.BUILD = OUT / 'build'
NAMES = ('freelancer.exe', 'freelancer.pdb')
SOURCE = ROOT / 'src/freelancer/Client/native_subtitles.cpp'
PLAN = OUT / 'install.json'


def prepare():
    exe = base.BUILD / 'bin/freelancer.exe'
    assert exe.stat().st_mtime >= SOURCE.stat().st_mtime
    dependencies, imports = base.verify_imports(('freelancer.exe',))
    for name in ('RP9.dll', 'D3D9.dll', 'dgVoodoo.conf'):
        path = base.GAME / name
        dependencies[name] = base.digest(path) if path.exists() else None
    plan = dict(
        files={name: dict(before=base.digest(base.GAME / name),
                         after=base.digest(base.BUILD / 'bin' / name)) for name in NAMES},
        dependencies=dependencies, verified_imports=imports,
        source=str(SOURCE), source_sha256=base.digest(SOURCE),
        embedded_bytes=base.verify_resource(exe))
    PLAN.write_text(json.dumps(plan, indent=2))
    print(f'Ready: client + symbols; {imports} imports checked')


def apply():
    base.idle()
    plan = json.loads(PLAN.read_text())
    assert base.digest(SOURCE) == plan['source_sha256']
    for name, expected in plan['dependencies'].items():
        path = base.GAME / name
        assert (base.digest(path) if path.exists() else None) == expected, name
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
    (OUT / 'installed.json').write_text(json.dumps(plan, indent=2))
    print('Installed and hash-verified client + symbols; build copies cleaned')


if __name__ == '__main__':
    apply() if '--apply' in sys.argv else prepare()
