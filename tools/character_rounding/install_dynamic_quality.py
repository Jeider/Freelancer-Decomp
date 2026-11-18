"""Install the validated dynamic character runtime; no game launch or DATA changes."""
import argparse
import hashlib
import json
from pathlib import Path
import shutil
import subprocess
import install_extra_lods as base
from contours import ROOT,GAME

OUT=ROOT/'out/character_rounding/dynamic_quality';BUILD=OUT/'runtime'
MODULES=('Common.dll','Deformable2.dll','RP9.dll','freelancer.exe')
FILES={f'bin/{n}':BUILD/'bin'/n for n in MODULES+tuple(Path(n).stem+'.pdb' for n in MODULES)}
FILES['DATA_EXTRA/SHADERS/room_material.hlsl']=ROOT/'DATA_EXTRA/SHADERS/room_material.hlsl'
base.OUT=OUT;base.BUILD=BUILD;base.MODULES=MODULES

def sha(path):return hashlib.sha256(path.read_bytes()).hexdigest()

def evidence():
    logs={'draw_scope':OUT/'check/result.txt','loader':OUT.parent/'lods/check_loader/result.txt',
          'gpu':ROOT/'src/obj/room_materials/gpu_result.log'}
    for name,path in logs.items():assert 'PASS' in path.read_text() and 'FAIL:' not in path.read_text(),name
    assert 'Character fade-to-native delta' in logs['gpu'].read_text()
    return {name:dict(path=str(path),sha256=sha(path)) for name,path in logs.items()}

def prepare():
    checks=evidence();binary=base.imports()
    records={rel:dict(source=str(source),before=sha(GAME/rel),after=sha(source)) for rel,source in FILES.items()}
    models={p.relative_to(GAME).as_posix():sha(p) for p in (GAME/'DATA/CHARACTERS').rglob('*.dfm')}
    data=dict(files=records,protected_models=models,checks=checks,**binary)
    (OUT/'install_manifest.json').write_text(json.dumps(data,indent=2))
    print('READY: 4 runtime modules, matching symbols, 1 shader;',len(models),'DFMs unchanged; imports/exports checked')

def apply():
    data=json.loads((OUT/'install_manifest.json').read_text());assert set(data['files'])==set(FILES)
    assert evidence()==data['checks']
    tasks=subprocess.run(['tasklist','/FO','CSV','/NH'],capture_output=True,check=True).stdout.lower()
    assert not any(b'"'+n+b'"' in tasks for n in (b'freelancer.exe',b'freelancer_window.exe',b'flserver.exe')),'Close game/server first'
    for rel,row in data['files'].items():assert sha(GAME/rel)==row['before'] and sha(FILES[rel])==row['after'],rel
    for row in data['dependencies'].values():assert sha(Path(row['path']))==row['sha256']
    for rel,wanted in data['protected_models'].items():assert sha(GAME/rel)==wanted,rel
    transaction=OUT/'transaction';assert not transaction.exists();transaction.mkdir()
    for rel in FILES:
        target=transaction/rel;target.parent.mkdir(parents=True,exist_ok=True);shutil.copy2(GAME/rel,target)
    try:
        for rel,source in FILES.items():shutil.copy2(source,GAME/rel)
        for rel,row in data['files'].items():assert sha(GAME/rel)==row['after'],rel
        for rel,wanted in data['protected_models'].items():assert sha(GAME/rel)==wanted,rel
    except BaseException:
        failures=[]
        for rel,row in data['files'].items():
            try:shutil.copy2(transaction/rel,GAME/rel);assert sha(GAME/rel)==row['before']
            except Exception as error:failures.append((rel,str(error)))
        (OUT/'rollback.json').write_text(json.dumps(failures,indent=2))
        if not failures:base.safe_remove(transaction)
        raise
    data.update(installed=True,verified=True,game_launched=False,rpg_world=True,dlss5=True)
    (OUT/'installed.json').write_text(json.dumps(data,indent=2))
    for module in MODULES:shutil.copy2(BUILD/'obj'/Path(module).stem/'build.log',OUT/(Path(module).stem+'_build.log'))
    for name,row in data['checks'].items():shutil.copy2(row['path'],OUT/(name+'_result.txt'))
    shutil.copy2(ROOT/'src/obj/room_materials/gpu_diagnostics.log',OUT/'gpu_diagnostics.log')
    base.safe_remove(transaction);base.safe_remove(BUILD)
    # Only task-owned standalone check products, never another running build tree.
    for root,names in [(OUT/'check',('check.exe','check.obj','build.cmd')),
          (OUT.parent/'lods/check_loader',('check.exe','check.obj','build.cmd')),
          (ROOT/'src/obj/graphics_settings_check',('check.exe','check.obj','check.lib','check.exp')),
          (ROOT/'src/obj/room_materials',('check.obj','check.cmd')),
          (ROOT/'bin',('room_material_check.exe','room_material_check.lib','room_material_check.exp'))]:
        for name in names:base.safe_remove(root/name,root)
    print('INSTALLED AND VERIFIED: Common, Deformable2, RP9, client + symbols and shader; 232 DFMs preserved. Temporary builds removed.')

if __name__=='__main__':
    p=argparse.ArgumentParser();p.add_argument('--apply',action='store_true');args=p.parse_args()
    apply() if args.apply else prepare()
