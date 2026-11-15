"""Install the checked Content.dll lane-type fix, with backup and rollback."""
from pathlib import Path
import hashlib
import json
import sys

ROOT = Path(__file__).resolve().parents[2]
sys.path.insert(0, str(ROOT/'tools/train_courier'))
import install_local_triggers as installer

installer.OUT = ROOT/'out/tradelane_system_types'
installer.__doc__ = __doc__


def stage_validation():
    checked = json.loads((ROOT/'src/obj/tradelane_system_types/verified.json').read_text())
    for path, expected in checked.items():
        assert installer.digest(Path(path)) == expected, 'Source changed since check: '+path
    binary = installer.BUILD/'Content.dll'
    assert binary.stat().st_mtime >= max(Path(p).stat().st_mtime for p in checked
                                       if Path(p).suffix in ('.cpp','.h')), 'Rebuild Content first'
    for path in [installer.BUILD/n for n in installer.NAMES] + [
            installer.GAME/n for n in ('Common.dll','Server.dll','freelancer.exe','RP9.dll')]:
        checked[str(path)] = hashlib.sha256(path.read_bytes()).hexdigest()
    out = installer.OUT/'check'
    out.mkdir(parents=True, exist_ok=True)
    (out/'verified.json').write_text(json.dumps(checked, indent=2))


if __name__ == '__main__':
    if '--apply' not in sys.argv:
        stage_validation()
    installer.main()
