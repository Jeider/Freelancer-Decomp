"""Stage or install the door manager; mission files remain untouched."""
import sys
import json
from pathlib import Path
from prepare import ROOT, GAME, MODEL, SOLAR, patch_model, patch_solar
sys.path.insert(0,str(ROOT/'tools/nomad_surfaces'))
# This file also has the name install.py; load the common verified installer explicitly.
import importlib.util
spec=importlib.util.spec_from_file_location('verified_door_installer',ROOT/'tools/nomad_surfaces/install.py')
installer=importlib.util.module_from_spec(spec); spec.loader.exec_module(installer)
installer.STAGE=ROOT/'src/obj/doors/install'
CODE=tuple('bin/'+name+ext for name in ('Common','Server','Content','rpclocal','RemoteClient','RemoteServer','freelancer')
           for ext in (('.exe','.pdb') if name=='freelancer' else ('.dll','.pdb')))
installer.PAYLOAD=CODE+(MODEL,SOLAR)
installer.SCOPE='Proximity doors, finite clips, Act_Animation and synchronized server animation state; no mission edits'
# No shader sources or rendering DLLs change in this installation.
installer.warm_game=lambda game: None
def prepare():
    files=[]
    for rel in installer.PAYLOAD:
        dest=installer.STAGE/rel; dest.parent.mkdir(parents=True,exist_ok=True)
        if rel in (MODEL,SOLAR):
            dest.write_bytes((patch_model if rel==MODEL else patch_solar)((GAME/rel).read_bytes()))
        else: installer.copy(ROOT/rel,dest)
        before,after=installer.digest(GAME/rel),installer.digest(dest)
        if before!=after: files.append(dict(relative=rel,original=before,prepared=after))
    (installer.STAGE/'manifest.json').write_text(json.dumps(dict(game=str(GAME.resolve()),files=files,scope=installer.SCOPE),indent=2))
    print(f'Prepared {len(files)} changed files. No system or mission files are modified.')
if __name__=='__main__':
    if len(sys.argv)==1: prepare()
    else: installer.main()
