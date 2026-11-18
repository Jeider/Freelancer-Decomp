"""Install the verified evacuation package with hash guards and temporary rollback.

Never starts the game. DATA publication and rollback both use Pythonlancer's
DataFolder. The --apply step requires filesystem authorization for FL_MOD.
"""
import argparse
import hashlib
import json
import os
from pathlib import Path
import re
import shutil
import stat
import subprocess
import sys
from stage_evacuation import ROOT,GAME,OUT,PACKAGE,GEN,data_class,digest

SOURCES={
    **{name:ROOT/'src/obj/train_courier/rpg1/bin'/name for name in ('Server.dll','Server.pdb','Content.dll','Content.pdb')},
    **{name:OUT/'runtime/bin'/name for name in ('freelancer.exe','freelancer.pdb')},
}
CODE=[
 'src/Content/TrainCourier.cpp','src/Content/TrainCourierEvacuation.inl','src/Content/TrainCourier.h',
 'src/Content/FactionProps.h','src/Content/FactionProps.cpp','src/Content/DockQueues.cpp','src/Content/Content.def',
 'src/include/train_evacuation.h','src/include/train_courier_hud.h','src/include/train_courier_bridge.h',
 'src/include/player_ship_transfer.h','src/Server/player_ship_transfer.inl','src/Server/server_train_yard.cpp',
 'src/Server/server_gameobject.cpp','src/Server/server_train_courier.h',
 'src/freelancer/Client/player_spawn.cpp','src/freelancer/Client/player_train.cpp','src/freelancer/Client/player_train.h',
 'src/freelancer/Client/hud_status_core.cpp','src/freelancer/Client/hud_maneuvers.cpp',
 'src/freelancer/Client/nn_mission_message.cpp','src/freelancer/Client/nn_mission_message.h',
 'tools/train_courier/stage_evacuation.py','tools/train_courier/evacuation_texts.py',
 'tools/train_courier/evacuation_script.py','tools/train_courier/check_evacuation.py',
]

def idle():
    result=subprocess.check_output(['tasklist','/FO','CSV','/NH']).lower()
    assert not any(b'"'+name+b'"' in result for name in (b'freelancer.exe',b'flserver.exe',b'freelancer_window.exe')), 'Game/server must be closed for installation'

def verify_imports():
    sys.path.insert(0,str(ROOT/'tools/nebula_control'))
    from build_asf_hq import compiler_env
    compiler,env=compiler_env();cache={};count=0
    def dump(option,path):return subprocess.check_output([str(compiler/'dumpbin.exe'),option,str(path)],env=env,text=True)
    def exports(path):
        key=str(path)
        if key not in cache:
            cache[key]={name:int(ordinal) for ordinal,name in re.findall(
                r'^\s+(\d+)\s+[0-9A-F]+\s+(?:[0-9A-F]+\s+)?(\S+)',dump('/exports',path),re.M)}
        return cache[key]
    for name in ('Server.dll','Content.dll','freelancer.exe'):
        old,new=exports(GAME/'bin'/name),exports(SOURCES[name])
        assert all(new.get(k)==v for k,v in old.items()),'Installed exports removed/renumbered: '+name
        dependency=None
        for line in dump('/imports',SOURCES[name]).splitlines():
            match=re.match(r'^    (\S+\.dll)\s*$',line,re.I)
            if match:dependency=match[1];continue
            symbol=re.match(r'^\s+[0-9A-F]+\s+(\?\S+|[A-Za-z_]\S*)\s*$',line)
            if not symbol or not dependency:continue
            path=next((p for n,p in SOURCES.items() if n.lower()==dependency.lower()),GAME/'bin'/dependency)
            if not path.exists():continue
            assert symbol[1] in exports(path),(name,dependency,symbol[1])
            count+=1
    assert 'TrainCourierEvacuation' in exports(SOURCES['Content.dll'])
    print('PASS:',count,'imports against installed/matched DLLs; existing exports and ordinals preserved')

def stage():
    verify_imports()
    manifest=json.loads((OUT/'content.json').read_text(encoding='utf-8'))
    for name,source in SOURCES.items():
        target=PACKAGE/'bin'/name;target.parent.mkdir(parents=True,exist_ok=True);shutil.copy2(source,target)
        manifest['files']['bin/'+name]={'before':digest(GAME/'bin'/name),'after':digest(target)}
    manifest['sources']={name:digest(ROOT/name) for name in CODE}
    manifest['dependencies']={name:digest(GAME/'bin'/name) for name in ('Common.dll','RP9.dll','SoundManager.dll','SoundStreamer.dll')}
    manifest['validation']='Offline controller/damage/save/transfer/HUD checks; game never launched; audio not generated'
    (OUT/'install.json').write_text(json.dumps(manifest,indent=2),encoding='utf-8')
    print('Ready to install:',len(manifest['files']),'files into FL_MOD; matched runtime in bin/')

def safe_file(path,root):
    root=root.resolve();resolved=path.resolve()
    assert resolved.is_relative_to(root) and resolved!=root,path
    for parent in (path,*path.parents):
        if parent==root.parent:break
        if parent.exists():assert not (parent.stat(follow_symlinks=False).st_file_attributes & stat.FILE_ATTRIBUTE_REPARSE_POINT),parent
    return resolved

def clean(manifest,backup):
    # No directory is recursively deleted. Enumerate only topic-owned compiler
    # products and check hashes immediately before removing each individual file.
    roots=[OUT/'runtime',OUT/'imports',OUT/'checks',backup,PACKAGE,
        ROOT/'src/obj/train_courier/rpg1/Server',ROOT/'src/obj/train_courier/rpg1/Content',
        ROOT/'src/obj/train_courier/order_state',ROOT/'src/obj/train_coupling_hud/check']
    roots += [ROOT/'src/obj/train_courier/orders']
    suffixes={'.obj','.pch','.pdb','.dll','.exe','.lib','.exp','.res','.ilk','.idb','.iobj','.ipdb'}
    candidates=[]
    for folder in roots:
        if not folder.exists():continue
        safe_file(folder,ROOT)
        for current,dirs,files in os.walk(folder,followlinks=False):
            for name in dirs:safe_file(Path(current)/name,folder)
            for name in files:
                path=Path(current)/name
                if folder==backup or path.suffix.lower() in suffixes:candidates.append(path)
    for name in SOURCES:
        path=ROOT/'src/obj/train_courier/rpg1/bin'/name
        if path.exists() and name.startswith(('Server.','Content.')):candidates.append(path)
    binary=ROOT/'src/obj/train_courier/rpg1/bin'
    for name in ('Server.lib','Server.exp','Content.lib','Content.exp','Common.lib','Common.dll',
                 'space_transfer_check.exe','space_transfer_check.obj','rules.exe','rules.obj'):
        if (binary/name).exists():candidates.append(binary/name)
    for stem in ('docking','binding','hud'):
        for ext in ('.exe','.obj'):
            path=ROOT/'out/train_space_transfer/check'/(stem+ext)
            if path.exists():candidates.append(path)
    candidates += [p for p in (OUT/'courier_names_en.dll',OUT/'courier_names_ru.dll') if p.exists()]
    guards={str(safe_file(p,ROOT)):digest(p) for p in candidates}
    back=data_class((PACKAGE/GEN/'tools/data_folder.py').read_text(encoding='utf-8'))(root=backup)
    for name,expected in guards.items():
        path=Path(name);safe_file(path,ROOT);assert digest(path)==expected,'Cleanup input changed: '+name
        if path.is_relative_to(backup/'DATA'):
            back.sync_train_evacuation({path.relative_to(backup/'DATA').as_posix():None})
        else:path.unlink()
    print('Removed',len(guards),'verified staging/rollback/compiler files; installed binaries and symbols retained')

def apply():
    idle();manifest=json.loads((OUT/'install.json').read_text(encoding='utf-8'))
    assert shutil.disk_usage(GAME).free>1024**3,'Insufficient free space for installation rollback'
    for name,expected in manifest['sources'].items():assert digest(ROOT/name)==expected,'Source changed: '+name
    for name,expected in manifest['dependencies'].items():assert digest(GAME/'bin'/name)==expected,'Dependency changed: '+name
    for name,record in manifest['files'].items():
        safe_file(GAME/name,GAME);safe_file(PACKAGE/name,PACKAGE)
        assert digest(GAME/name)==record['before'],'Live file changed: '+name
        assert digest(PACKAGE/name)==record['after'],'Package changed: '+name
    source=(PACKAGE/GEN/'tools/data_folder.py').read_text(encoding='utf-8')
    cls=data_class(source);live=cls(root=GAME)
    backup=OUT/'install_backup';back=cls(root=backup)
    def write(root,folder,name,content):
        if name.startswith('DATA/'):folder.sync_train_evacuation({name[5:]:content});return
        path=root/name
        if content is None:path.unlink(missing_ok=True)
        else:path.parent.mkdir(parents=True,exist_ok=True);path.write_bytes(content)
    for name,record in manifest['files'].items():
        if record['before'] is not None:
            write(backup,back,name,(GAME/name).read_bytes());assert digest(backup/name)==record['before']
    changed=[]
    try:
        for name,record in manifest['files'].items():
            assert digest(GAME/name)==record['before'],'Concurrent live change: '+name
            changed.append(name);write(GAME,live,name,(PACKAGE/name).read_bytes())
            assert digest(GAME/name)==record['after'],'Installed hash mismatch: '+name
        for name,record in manifest['files'].items():assert digest(GAME/name)==record['after']
    except BaseException:
        for name in reversed(changed):
            record=manifest['files'][name]
            write(GAME,live,name,(backup/name).read_bytes() if record['before'] is not None else None)
            assert digest(GAME/name)==record['before'],'Rollback failed: '+name
        raise
    (OUT/'installed.json').write_text(json.dumps(manifest,indent=2),encoding='utf-8')
    clean(manifest,backup)
    print('Installed and hash-verified evacuation runtime, Pythonlancer, empathy, catalog and RU/EN strings. Game not launched.')

if __name__=='__main__':
    parser=argparse.ArgumentParser(description=__doc__);parser.add_argument('--apply',action='store_true')
    args=parser.parse_args();apply() if args.apply else stage()
