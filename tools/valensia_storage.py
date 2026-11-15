"""Audit disk use and remove only generated Valensia staging after verified install."""
import argparse
from collections import defaultdict
import json
import os
from pathlib import Path
import valensia_mega as m


def main():
    parser=argparse.ArgumentParser();parser.add_argument('--clean-stage',action='store_true');args=parser.parse_args()
    sizes=defaultdict(int);backups=defaultdict(int)
    for root in (m.REPO/'out',m.REPO/'src/obj'):
        for directory,dirs,files in os.walk(root):
            dirs[:]=[d for d in dirs if not (Path(directory)/d).is_symlink()]
            relative=Path(directory).relative_to(root)
            group=str(root.relative_to(m.REPO)/relative.parts[0]) if relative.parts else str(root.relative_to(m.REPO))
            parts=relative.parts
            bucket=next((i for i,p in enumerate(parts) if 'backup' in p.lower() or p.lower() in ('baseline','rollback')),None)
            for name in files:
                size=(Path(directory)/name).stat().st_size
                sizes[group]+=size
                if bucket is not None:backups[str(root.relative_to(m.REPO)/Path(*parts[:bucket+1]))]+=size
    print('Largest working/build directories (GiB):')
    for name,size in sorted(sizes.items(),key=lambda x:-x[1])[:8]:print(round(size/2**30,3),name)
    print('Largest backup directories (GiB):')
    for name,size in sorted(backups.items(),key=lambda x:-x[1])[:12]:print(round(size/2**30,3),name)
    print('Backup total GiB:',round(sum(backups.values())/2**30,3))
    if not args.clean_stage:return
    installed=json.loads((m.OUT/'installed.json').read_text())
    for name,digest in installed['hashes'].items():
        assert m.old.sha256((m.GAME/name).read_bytes()).hexdigest()==digest,'Installed file changed: '+name
    freed=0;count=0
    # Both are disposable payload directories produced by this task. No rollback
    # set, source original or installed model is removed. DATA removal goes via API.
    for stage in (m.old.OUT/'stage',m.OUT/'stage'):
        stage=stage.resolve()
        assert stage.is_relative_to((m.REPO/'out').resolve()) and stage.name=='stage'
        folder=m.old.data_folder(m.GAME,stage)
        for path in list(stage.rglob('*')):
            if not path.is_file():continue
            assert path.resolve().is_relative_to(stage) and not path.is_symlink()
            relative=path.relative_to(stage).as_posix()
            freed+=path.stat().st_size;count+=1
            if relative.startswith('DATA/'):folder.remove_data_file(relative[5:])
            else:
                assert relative.startswith('Assets/Pythonlancer/templates/dockable/valensia') and relative.endswith('.py')
                path.unlink()
    (m.OUT/'stage_cleanup.json').write_text(json.dumps(dict(files=count,bytes_freed=freed),indent=2))
    print('Removed generated staging files:',count,'freed MiB:',round(freed/2**20,2))


if __name__=='__main__':main()
