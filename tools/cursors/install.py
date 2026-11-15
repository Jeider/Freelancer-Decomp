"""Stage/install the checked vector-cursor client into FL_MOD/bin, with rollback."""
from pathlib import Path
import hashlib
import json
import sys

ROOT=Path(__file__).resolve().parents[2]
sys.path.insert(0,str(ROOT/'tools/train_courier'))
import install_local_triggers as installer

installer.__doc__=__doc__
installer.OUT=ROOT/'out/cursor_vectors'
installer.NAMES=('freelancer.exe','freelancer.pdb')
DLSS='--dlss-menu' in sys.argv
if DLSS:
    sys.argv.remove('--dlss-menu')
    installer.BUILD=ROOT/'out/base_neural/on/bin'

def stage_validation():
    digest=lambda p:hashlib.sha256(p.read_bytes()).hexdigest()
    checked={}
    for report in ('cpu_verified.json','gpu_verified.json'):
        checked.update(json.loads((ROOT/'src/obj/cursor_vectors'/report).read_text()))
    for path,sha in checked.items():
        assert digest(Path(path))==sha,'Source changed since validation: '+path
    sources=[ROOT/'src/freelancer/Client'/n for n in ('input_manager.cpp','cursor_vector_cache.h','cursor_vector_art.h','icon_vector_raster.h','base_icon_art.h','nn_icon_art.h')]
    exe=installer.BUILD/'freelancer.exe'
    assert exe.stat().st_mtime>=max(p.stat().st_mtime for p in sources),'Rebuild client before staging'
    obj=ROOT/('out/base_neural/on/obj/freelancer' if DLSS else 'src/obj/train_courier/rpg1/freelancer')
    commands=(obj/'freelancer.tlog/CL.command.1.tlog').read_text(encoding='utf-16')
    assert 'FREELANCER_RPG_WORLD' in commands and 'FREELANCER_RP9' in commands,'Unexpected build profile'
    if DLSS:assert 'FREELANCER_DLSS5' in commands,'DLSS menu support missing'
    for path in sources+[installer.BUILD/n for n in installer.NAMES]:checked[str(path)]=digest(path)
    # Refuse to apply if live dependencies change between staging and install.
    for name in ('Common.dll','Content.dll','Server.dll','RP9.dll'):
        path=installer.GAME/name;checked[str(path)]=digest(path)
    out=installer.OUT/'check';out.mkdir(parents=True,exist_ok=True)
    (out/'verified.json').write_text(json.dumps(checked,indent=2))

if __name__=='__main__':
    if '--apply' not in sys.argv:stage_validation()
    installer.main()
