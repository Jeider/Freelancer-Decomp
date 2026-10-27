"""Stage/install automatic room materials with verified backup and rollback.

Only binaries, material shaders and generated DATA_EXTRA sidecars. No DATA or port.ini edits.
"""
import argparse
import datetime
import json
import subprocess
import sys
from pathlib import Path
sys.path.insert(0,str(Path(__file__).resolve().parents[1]))
from install_hyperspace_tunnel import copy,digest,safe,stopped

ROOT=Path(__file__).resolve().parents[2]
OUT=ROOT/'src/obj/room_materials'
ASSETS=OUT/'assets'
STAGE=OUT/'install'
FIXED=tuple('bin/'+stem+ext for stem in ('freelancer','RP9','Shading','Deformable2')
            for ext in (('.exe','.pdb') if stem=='freelancer' else ('.dll','.pdb')))+(
    'DATA_EXTRA/SHADERS/room_material.hlsl','DATA_EXTRA/SHADERS/room_contact.hlsl',
    'DATA_EXTRA/SHADERS/room_shadow.hlsl','DATA_EXTRA/SHADERS/surface_material.hlsl',
    'DATA_EXTRA/ROOM_MATERIALS/profiles.txt')

def allowed(relative):
    p=Path(relative)
    return relative in FIXED or (p.parent.as_posix()=='DATA_EXTRA/ROOM_MATERIALS' and p.suffix=='.dds'
        and len(p.stem)==32 and all(c in '0123456789abcdef' for c in p.stem))


def main():
    parser=argparse.ArgumentParser(description=__doc__)
    parser.add_argument('--game-root',type=Path,default=Path('D:/games/FL_MOD'))
    mode=parser.add_mutually_exclusive_group();mode.add_argument('--apply',action='store_true');mode.add_argument('--restore',type=Path)
    args=parser.parse_args();game=args.game_root.resolve(strict=True)
    if not (args.apply or args.restore):
        report=json.loads((OUT/'generation.json').read_text(encoding='utf8'))
        if Path(report['game']).resolve()!=game:raise ValueError('Generated assets belong to another game')
        for rel,sha in report['source_files'].items():
            if digest(safe(game,rel))!=sha:raise ValueError(f'Source changed; regenerate: {rel}')
        items=[]
        for rel in FIXED+tuple('DATA_EXTRA/ROOM_MATERIALS/'+name for name in sorted(report['maps'])):
            source=safe(ASSETS if rel.startswith('DATA_EXTRA/ROOM_MATERIALS/') else ROOT,rel)
            after=digest(source)
            if source.suffix=='.dds' and after!=report['maps'][source.name]['sha256']:raise ValueError(f'Generated map changed: {source}')
            before=digest(safe(game,rel))
            if before!=after:
                copy(source,safe(STAGE,rel))
                if digest(safe(STAGE,rel))!=after:raise ValueError(f'Staged file verification failed: {rel}')
                items.append(dict(relative=rel,original=before,prepared=after))
        data=dict(game=str(game),files=items,source_files=report['source_files'],scope='Room materials, shadows and RP9 spotlight compatibility; original DATA, authored lights, UVs and port.ini untouched')
        (STAGE/'manifest.json').write_text(json.dumps(data,indent=2),encoding='utf8')
        print(f'Prepared {len(items)} changed files; {report["profiles"]} profiles, {len(report["maps"])} maps; game untouched.',flush=True)
        return
    stopped()
    processes=subprocess.run(['tasklist','/FI','IMAGENAME eq flserver.exe','/FO','CSV','/NH'],capture_output=True,check=True)
    if b'flserver.exe' in processes.stdout.lower():raise RuntimeError('Close FLServer before installation.')
    source=args.restore.resolve(strict=True) if args.restore else STAGE
    data=json.loads((source/'manifest.json').read_text(encoding='utf8'))
    if Path(data['game']).resolve()!=game:raise ValueError('Manifest root mismatch')
    if not args.restore:
        for rel,sha in data['source_files'].items():
            if digest(safe(game,rel))!=sha:raise ValueError(f'Source changed since staging: {rel}')
    seen=set()
    for item in data['files']:
        rel=item['relative']
        if not allowed(rel) or rel in seen:raise ValueError(f'Unexpected target: {rel}')
        seen.add(rel)
        if digest(safe(game,rel))!=item['prepared' if args.restore else 'original'] or digest(safe(source,rel))!=item['original' if args.restore else 'prepared']:
            raise ValueError(f'File changed since staging/install: {rel}')
    def restore(backup):
        for item in data['files']:
            target=safe(game,item['relative'])
            if item['original'] is None:target.unlink(missing_ok=True)
            else:copy(safe(backup,item['relative']),target)
            if digest(target)!=item['original']:raise ValueError(f'Restore failed: {target}')
    if args.restore:
        restore(source);print(f'Restored {len(data["files"])} files.');return
    backup=safe(game,'BACKUP/codex_room_materials_'+datetime.datetime.now().strftime('%Y%m%d_%H%M%S_%f'))
    for item in data['files']:
        if item['original'] is not None:
            target=safe(backup,item['relative']);copy(safe(game,item['relative']),target)
            if digest(target)!=item['original']:raise ValueError(f'Backup failed: {target}')
    copy(source/'manifest.json',backup/'manifest.json')
    try:
        for item in data['files']:
            target=safe(game,item['relative']);copy(safe(source,item['relative']),target)
            if digest(target)!=item['prepared']:raise ValueError(f'Install failed: {target}')
    except Exception:
        restore(backup);raise
    print(f'Installed and verified {len(data["files"])} files. Backup: {backup}',flush=True)
    sys.path.insert(0,str(ROOT/'tools/asteroid_normals'))
    from warm import warm
    warm(game)


if __name__=='__main__':main()
