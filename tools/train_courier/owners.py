"""Stage and install locomotive owners, using DataFolder for all DATA and rollback."""
import argparse
import ast
import contextlib
import datetime
import hashlib
import json
import os
from pathlib import Path
import re
import subprocess
import sys

ROOT=Path(__file__).resolve().parents[2]
GAME=Path('D:/Games/FL_MOD')
PROJECT=GAME/'Assets/Pythonlancer'
OUT=ROOT/'out/train_courier/owners'
sys.dont_write_bytecode=True
sys.path.insert(0,str(PROJECT))


def digest(p):return hashlib.sha256(p.read_bytes()).hexdigest() if p.exists() else None


def stage_sources():
    files={}
    for name in ('courier_owners','courier_graph'):
        files['managers/'+name+'.py']=(ROOT/'tools/rpg_cutscenes/pythonlancer/managers'/f'{name}.py').read_bytes()
    def patch(path,anchor,value,marker):
        text=(PROJECT/path).read_text(encoding='utf-8-sig')
        if marker not in text:
            if text.count(anchor)!=1:raise ValueError('Review changed source '+path)
            text=text.replace(anchor,value,1)
        files[path]=text.encode('utf-8')
    method=Path(__file__).with_name('owners_data.inc').read_text(encoding='utf-8')
    patch('tools/data_folder.py','    def get_root(self):',method+'\n    def get_root(self):','def sync_courier_owners(')
    text=files['tools/data_folder.py'].decode()
    text,count=re.subn(r'(?ms)^    def sync_courier_owners\(.*?(?=^    def |\Z)',lambda _:method+'\n',text)
    assert count==1;files['tools/data_folder.py']=text.encode()
    path='tools/rpg_voices.py'
    text=(PROJECT/path).read_text(encoding='utf-8-sig')
    if '"owners"' not in text:
        text=text.replace('"scenes", "runtime"]','"scenes", "runtime", "owners"]')
        anchor='    manager = RpgVoiceManager('
        pos=text.index(anchor)
        text=text[:pos]+'''    if args.command == 'owners':
        from core import get_core
        from tools.data_folder import DataFolder
        from managers.courier_owners import generate
        _, _, report = generate(get_core().universe, DataFolder(root=args.game_root or root.parent.parent),
                                root, output, args.dry_run)
        print(f'Locomotive owners: {len(report)} bases')
        return
'''+text[pos:]
        text=text.replace("('build', 'install-audio', 'scenes', 'runtime')","('build', 'install-audio', 'scenes', 'runtime', 'owners')")
    files[path]=text.encode('utf-8')
    patch('managers/rpg_runtime.py',"    scenes = RpgSceneManager(project, script, game_root)",
          "    if (project/'story/rpg/courier_owners.json').exists():\n        from managers.courier_owners import refresh\n        from tools.data_folder import DataFolder\n        return refresh(project, DataFolder(root=game_root or project.parent.parent), output, dry_run)\n    scenes = RpgSceneManager(project, script, game_root)",
          "from managers.courier_owners import refresh")
    patch('managers/universe.py','        sync_from_universe(self, data_folder)',
          '        sync_from_universe(self, data_folder)\n\n        from managers.courier_owners import sync_from_universe as sync_courier_owners\n        sync_courier_owners(self, data_folder)',
          'from managers.courier_owners import sync_from_universe')
    path='managers/parking_commandants.py'
    text=(PROJECT/path).read_text(encoding='utf-8-sig')
    if "owners_registry = project/'story/rpg/courier_owners.json'" not in text:
        anchor="    groups = {r['group'] for r in old['bases']}"
        assert text.count(anchor)==1
        text=text.replace(anchor,anchor+"\n    owners_registry = project/'story/rpg/courier_owners.json'\n    if owners_registry.exists():\n        groups.update(r['group'] for r in json.loads(owners_registry.read_text(encoding='utf-8'))['bases'])",1)
    anchor="    for kind,row in parse(read('RPG/contacts.ini')):"
    if anchor in text:
        text=text.replace(anchor,"    contact_catalog = read('RPG/contacts.ini')\n    owner_catalog = folder.data_path('RPG/courier_contacts.ini')\n    if owner_catalog.exists(): contact_catalog += b'\\n' + owner_catalog.read_bytes()\n    for kind,row in parse(contact_catalog):",1)
    anchor="    owner_catalog = folder.data_path('RPG/courier_contacts.ini')"
    if 'owner_catalog = assets.data_path' not in text:
        assert text.count(anchor)==1
        text=text.replace(anchor,anchor+"\n    if not owner_catalog.exists(): owner_catalog = assets.data_path('RPG/courier_contacts.ini')",1)
    files[path]=text.encode('utf-8')
    rows={}
    for name,content in files.items():
        compile(content,name,'exec')
        p=OUT/'sources'/name;p.parent.mkdir(parents=True,exist_ok=True);p.write_bytes(content)
        rows[name]={'before':digest(PROJECT/name),'after':digest(p)}
    (OUT/'sources.json').write_text(json.dumps(rows,indent=2))
    print('Staged Pythonlancer sources:',len(rows))


def apply_sources():
    rows=json.loads((OUT/'sources.json').read_text())
    install(rows,OUT/'sources',PROJECT,OUT/'source_backups',False)


def install(rows,payload,target,backups,game_files):
    from tools.data_folder import DataFolder
    for name,r in rows.items():
        assert (target/name).resolve().is_relative_to(target.resolve())
        assert digest(target/name)==r['before'],'Changed target: '+name
        assert digest(payload/name)==r['after'],'Changed payload: '+name
    if game_files:
        processes=subprocess.run(['tasklist','/FO','CSV','/NH'],capture_output=True,check=True).stdout.lower()
        assert not any(b'"'+n+b'"' in processes for n in (b'freelancer.exe',b'freelancer_en.exe',b'freelancer_window.exe',b'freelancer_window_en.exe',b'flserver.exe')),'Close Freelancer before installing'
    backup=backups/datetime.datetime.now().strftime('%Y%m%d_%H%M%S_%f')
    def put(root,name,data):
        if name.startswith('DATA/'):
            DataFolder(root=root).sync_data_file(name[5:],data)
        else:
            p=root/name;p.parent.mkdir(parents=True,exist_ok=True);p.write_bytes(data)
    for name,r in rows.items():
        if r['before'] is not None:
            put(backup,name,(target/name).read_bytes());assert digest(backup/name)==r['before']
    backup.mkdir(parents=True,exist_ok=True)
    (backup/'manifest.json').write_text(json.dumps(rows,indent=2))
    touched=[]
    try:
        for name,r in rows.items():
            assert digest(target/name)==r['before'],'Concurrent edit: '+name
            touched.append(name);put(target,name,(payload/name).read_bytes())
            assert digest(target/name)==r['after']
    except BaseException:
        for name in reversed(touched):
            if rows[name]['before'] is not None:put(target,name,(backup/name).read_bytes())
            elif name.startswith('DATA/'):DataFolder(root=target).remove_data_file(name[5:])
            else:(target/name).unlink(missing_ok=True)
        raise
    print('Installed and verified',len(rows),'files. Backup:',backup)


def stage():
    from tools.data_folder import DataFolder
    from managers.courier_owners import generate
    os.chdir(PROJECT)
    OUT.mkdir(parents=True,exist_ok=True)
    with (OUT/'universe.log').open('w',encoding='utf-8') as log, contextlib.redirect_stdout(log):
        from core import get_core
        universe=get_core().universe
    class Inputs(DataFolder):
        def __init__(self):super().__init__(root=GAME);self.hashes={}
        def data_path(self,name):
            path=super().data_path(name)
            relative=path.relative_to(GAME).as_posix()
            if relative not in self.hashes:self.hashes[relative]=digest(path)
            return path
    inputs=Inputs()
    files,registry,report=generate(universe,inputs,PROJECT,OUT,dry_run=True)
    payload=OUT/'payload';folder=DataFolder(root=payload)
    folder.sync_courier_owners(files,OUT/'stage_backups')
    generated={'DATA/'+name:content for name,content in files.items()}
    generated['Assets/Pythonlancer/story/rpg/courier_owners.json']=(json.dumps(registry,ensure_ascii=False,indent=2)+'\n').encode('utf-8')
    # The return berth may now be at a station, too. Keep the existing IDS stable.
    static=(PROJECT/'text/static.py').read_text(encoding='utf-8')
    lines=static.splitlines(keepends=True)
    matches=[n for n in ast.walk(ast.parse(static)) if isinstance(n,ast.Call) and
             isinstance(n.func,ast.Name) and n.func.id=='Static' and n.args and
             isinstance(n.args[0],ast.Constant) and n.args[0].value==238274]
    assert len(matches)==1
    node=matches[0]
    raw=static.encode('utf-8'); offsets=[0]
    for line in lines:offsets.append(offsets[-1]+len(line.encode('utf-8')))
    replacement="Static(238274, MS('Припаркуйте локомотив в отмеченном месте у базы %s0.', 'Park the locomotive at the marked berth near %s0.'))".encode('utf-8')
    changed=raw[:offsets[node.lineno-1]+node.col_offset]+replacement+raw[offsets[node.end_lineno-1]+node.end_col_offset:]
    generated['Assets/Pythonlancer/text/static.py']=changed
    static_path=payload/'Assets/Pythonlancer/text/static.py';static_path.parent.mkdir(parents=True,exist_ok=True);static_path.write_bytes(changed)
    from text_resources import stage_localized
    def resource(name,content):
        if isinstance(content,str):content=content.encode('utf-8')
        generated[name]=content
        if name.startswith('DATA/'):folder.sync_data_file(name[5:],content)
    stage_localized(GAME,OUT,resource,static_path)
    for name,build in [('Content.dll','build_Release_1'),('Content.pdb','build_Release_1'),
                       ('freelancer.exe','build_Release_1_client'),('freelancer.pdb','build_Release_1_client')]:
        generated['bin/'+name]=(ROOT/'src/obj/rpg_contacts'/build/'bin'/name).read_bytes()
    rows={}
    for name,content in generated.items():
        if not name.startswith('DATA/'):
            p=payload/name;p.parent.mkdir(parents=True,exist_ok=True);p.write_bytes(content)
        before=digest(GAME/name);after=digest(payload/name)
        if before!=after:rows[name]={'before':before,'after':after}
    deps={name:value for name,value in inputs.hashes.items() if name not in rows}
    deps.update({str(p.relative_to(GAME)):digest(p) for p in [GAME/'bin/Server.dll',GAME/'bin/Common.dll']})
    for name,value in deps.items():assert digest(GAME/name)==value,'Changed input while staging: '+name
    (OUT/'manifest.json').write_text(json.dumps({'files':rows,'dependencies':deps},indent=2))
    print('Staged',len(report),'owners;',sum(r['posture']=='sit' for r in report),'seated;',len(rows),'changed files')


def main():
    p=argparse.ArgumentParser(description=__doc__)
    p.add_argument('action',choices=['sources','apply-sources','stage','apply'])
    args=p.parse_args();OUT.mkdir(parents=True,exist_ok=True)
    if args.action=='sources':stage_sources()
    elif args.action=='apply-sources':apply_sources()
    elif args.action=='stage':stage()
    else:
        manifest=json.loads((OUT/'manifest.json').read_text())
        for name,value in manifest['dependencies'].items():assert digest(GAME/name)==value,'Changed dependency: '+name
        install(manifest['files'],OUT/'payload',GAME,OUT/'backups',True)


if __name__=='__main__':main()
