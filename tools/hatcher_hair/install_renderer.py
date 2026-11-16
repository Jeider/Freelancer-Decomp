"""Stage/apply matching hair rendering and deformation DLLs, symbols and shader."""
import argparse,hashlib,json,subprocess,shutil
from datetime import datetime
from pathlib import Path
from build import ROOT,GAME,OUT

FILES={
    'DATA_EXTRA/ROOM_MATERIALS/juni_hair_normal.png':ROOT/'DATA_EXTRA/ROOM_MATERIALS/juni_hair_normal.png',
    'bin/Common.dll':ROOT/'out/base_neural/on/bin/Common.dll',
    'bin/Common.pdb':ROOT/'out/base_neural/on/bin/Common.pdb',
    'bin/freelancer.exe':ROOT/'out/base_neural/on/bin/freelancer.exe',
    'bin/freelancer.pdb':ROOT/'out/base_neural/on/bin/freelancer.pdb',
    'bin/Deformable2.dll':ROOT/'out/base_neural/on/bin/Deformable2.dll',
    'bin/Deformable2.pdb':ROOT/'out/base_neural/on/bin/Deformable2.pdb',
    'bin/RP9.dll':ROOT/'out/base_neural/on/bin/RP9.dll',
    'bin/RP9.pdb':ROOT/'out/base_neural/on/bin/RP9.pdb',
    'DATA_EXTRA/SHADERS/room_material.hlsl':ROOT/'DATA_EXTRA/SHADERS/room_material.hlsl',
}
hair_maps=ROOT/'tools/hatcher_hair/assets/all_hair_maps.json'
if hair_maps.exists():
    for relative in json.loads(hair_maps.read_text()):
        path='DATA_EXTRA/ROOM_MATERIALS/'+relative
        FILES[path]=ROOT/path
def digest(p):return hashlib.sha256(p.read_bytes()).hexdigest() if p.exists() else None
def copy(a,b):b.parent.mkdir(parents=True,exist_ok=True);shutil.copy2(a,b)
parser=argparse.ArgumentParser();parser.add_argument('--apply',action='store_true');args=parser.parse_args()
stage=OUT/'renderer';manifest=stage/'manifest.json'
if not args.apply:
    records={}
    for relative,source in FILES.items():
        copy(source,stage/relative)
        records[relative]={'before':digest(GAME/relative),'after':digest(stage/relative)}
    manifest.write_text(json.dumps(records,indent=2));print('Staged renderer:',manifest)
else:
    tasks=subprocess.run(['tasklist','/FO','CSV','/NH'],capture_output=True,check=True).stdout.lower()
    if any(b'"'+n+b'"' in tasks for n in (b'freelancer.exe',b'freelancer_window.exe',b'flserver.exe')):
        raise SystemExit('Renderer is ready; game/server must be closed before replacing RP9.')
    records=json.loads(manifest.read_text());assert set(records)==set(FILES)
    for relative,item in records.items():
        assert digest(GAME/relative)==item['before'],relative+' changed since staging'
        assert digest(stage/relative)==item['after'],relative+' stage mismatch'
    backup=OUT/'renderer_backups'/datetime.now().strftime('%Y%m%d_%H%M%S_%f')
    for relative,item in records.items():
        if item['before'] is not None:copy(GAME/relative,backup/relative)
    copy(manifest,backup/'manifest.json')
    try:
        for relative,item in records.items():
            copy(stage/relative,GAME/relative)
            assert digest(GAME/relative)==item['after'],relative
    except Exception:
        for relative,item in records.items():
            if item['before'] is not None:copy(backup/relative,GAME/relative)
            else:(GAME/relative).unlink(missing_ok=True)
        raise
    print('Installed and hash-verified hair renderer. Backup:',backup)
