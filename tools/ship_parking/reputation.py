"""Prepare positive-reputation sales, refusal voices and a verified engine/DATA package."""
import argparse
import datetime
import hashlib
import json
from pathlib import Path
import re
import sys

ROOT=Path(__file__).resolve().parents[2]
PROJECT=Path('D:/Games/FL_MOD/Assets/Pythonlancer')
GAME=PROJECT.parent.parent
OUT=ROOT/'out/service_reputation'
sys.dont_write_bytecode=True
sys.path.insert(0,str(ROOT/'tools/train_courier'))
sys.path.insert(0,str(PROJECT))
from owners import install, digest


def sources():
    source=ROOT/'tools/rpg_cutscenes/pythonlancer/files/rpg_reputation.py'
    scope={};exec(compile(source.read_bytes(),str(source),'exec'),scope)
    changes={'files/rpg_reputation.py':source.read_bytes()}
    data=json.loads((PROJECT/'story/rpg/rm0001.json').read_text(encoding='utf-8'))
    data['rules']['reputation'].update(enabled=True,minimum=0,strict=True)
    changes['story/rpg/rm0001.json']=(json.dumps(data,ensure_ascii=False,indent=2)+'\n').encode()
    for path in sorted((PROJECT/'story/rpg').glob('rm*.json')):
        data=json.loads(path.read_text(encoding='utf-8'))
        if 'parking' in data:
            changes['story/rpg/'+path.name]=(json.dumps(scope['parking_scenario'](data),ensure_ascii=False,indent=2)+'\n').encode()
    path='files/rpg_runtime.py';text=(PROJECT/path).read_text(encoding='utf-8')
    text=text.replace("if rep.get('enabled') and rep.get('minimum') is not None:","if 'parking' not in data and rep.get('enabled') and rep.get('minimum') is not None:")
    if 'reputation_strict = 1' not in text:
        anchor="        lines += ['reputation_faction = rh_grp', 'minimum_reputation = ' + str(rep['minimum'])]"
        assert text.count(anchor)==1
        text=text.replace(anchor,anchor+"\n        if rep.get('strict'):\n            lines.append('reputation_strict = 1')",1)
    changes[path]=text.encode()
    path='managers/parking_commandants.py';text=(PROJECT/path).read_text(encoding='utf-8')
    if 'from files.rpg_reputation import' not in text:
        text=text.replace('from story.rpg.script import RpgScript','from story.rpg.script import RpgScript\nfrom files.rpg_reputation import parking_scenario, parking_rules',1)
        text=text.replace('    data = copy.deepcopy(template)','    data = parking_scenario(template)',1)
        anchor="    files['RPG/ship_parking.ini']=config.encode('utf-8')"
        assert text.count(anchor)==1
        text=text.replace(anchor,"    config=parking_rules(config,{r['base']:r['faction'] for r in registry['bases']})\n"+anchor,1)
    changes[path]=text.encode()
    path='tools/ship_parking.py';text=(PROJECT/path).read_text(encoding='utf-8')
    if 'from files.rpg_reputation import parking_denial_ini' not in text:
        text=text.replace('def dialogue(base, seller):','def dialogue(base, seller):\n    from files.rpg_reputation import parking_denial_ini',1)
        start=text.index('def dialogue(');end=text.index('\ndef generate(',start)
        text=text[:start]+text[start:end].replace('    return text','    return parking_denial_ini(text)')+text[end:]
        text=text.replace("    files['DATA/RPG/ship_parking.ini'] = config","    from files.rpg_reputation import parking_rules\n    files['DATA/RPG/ship_parking.ini'] = parking_rules(config, factions)",1)
    changes[path]=text.encode()
    path='tools/data_folder.py';text=(PROJECT/path).read_text(encoding='utf-8')
    if 'def sync_service_reputation(' not in text:
        text=text.replace('    def get_root(self):', '''    def sync_service_reputation(self, files, backup_root):
        import re
        for name in files:
            if (name != 'RPG/ship_parking.ini' and
                    not re.fullmatch(r'RPG/(?:parking/[a-z0-9_]+|courier/[a-z0-9_]+_base_dialog|rm[0-9]{4}_dialog)\\.ini', name)):
                raise ValueError('Unexpected service reputation target: '+name)
            self.data_path(name)
        self._sync_rpg_files('service_reputation',files,{},backup_root)

    def get_root(self):''',1)
    text=text.replace('(?:parking/[a-z0-9_]+_base|courier/', '(?:parking/[a-z0-9_]+|courier/')
    changes[path]=text.encode()
    rows={}
    for name,content in changes.items():
        if name.endswith('.py'):compile(content,name,'exec')
        p=OUT/'sources'/name;p.parent.mkdir(parents=True,exist_ok=True);p.write_bytes(content)
        rows[name]={'before':digest(PROJECT/name),'after':digest(p)}
    (OUT/'sources.json').write_text(json.dumps(rows,indent=2))
    print('Staged source/scenario files:',len(rows))


def contacts():
    from managers.parking_commandants import parse,one
    from tools.data_folder import DataFolder
    folder=DataFolder(root=GAME);result=[]
    for kind,row in parse(folder.data_path('RPG/parking_contacts.ini').read_bytes()):
        if kind!='rpgcontact' or one(row,'enabled').lower() not in ('true','1'):continue
        path=one(row,'rtc').replace('\\','/');parts=parse(folder.data_path(path).read_bytes())
        encounter=next(v for k,v in parts if k=='characterencounter')
        actor=next(v for k,v in parts if k=='char')
        npc=next(v for k,v in parts if k=='npc' and one(v,'nickname')==one(actor,'npc'))
        dialog=one(encounter,'dialog').replace('\\','/')
        group=''
        if dialog:
            header=next(v for k,v in parse(folder.data_path(dialog).read_bytes()) if k=='dialog')
            group=one(header,'scene_group')
        result.append(dict(base=one(row,'base'),faction=one(npc,'affiliation'),rtc=path,dialog=dialog,group=group))
    return result


def voices():
    from story.rpg.script import RpgScript
    from tools.voice_api import VoiceApi
    from tools.voicestudio import VoiceStudioClone
    from managers.rpg_audio import RpgAudioManager
    from managers.rpg_scene import RpgSceneManager
    cache=OUT/'voice_cache';cache.mkdir(exist_ok=True)
    groups=sorted({r['group'] for r in contacts() if r['group']})
    for group in groups:
        script=RpgScript.load(PROJECT/'story/rpg'/f'{group}.json')
        sounds=script.recording_group().get_sounds()
        row=next(r for r in script.fragments if r['pool']=='bad_reputation')
        sound=next(s for s in sounds if s.name==script.line_name(row))
        source=VoiceStudioClone.source_file(sound.line.actor.__name__,'en')
        signature=hashlib.sha256(json.dumps([sound.line.actor.__name__,row['en'],digest(source),
                                           repr(getattr(VoiceStudioClone._delivery_of(sound.line.actor, sound.line.delivery),'__dict__',None)),sound.line.actor.STEOS_SPEED]).encode()).hexdigest()
        saved=cache/(signature+'.wav')
        if not saved.exists():VoiceApi.generate_en_voice(sound,saved)
        dest=PROJECT.parent/'AUDIO_CUTSCENE_EN'/group/(sound.name+'.wav')
        if dest.exists() and dest.read_bytes()!=saved.read_bytes():raise ValueError('Existing refusal differs: '+str(dest))
        dest.parent.mkdir(parents=True,exist_ok=True);dest.write_bytes(saved.read_bytes())
        # Before publishing, preserve every earlier recording byte-for-byte.
        old=json.loads((GAME/f'DATA/AUDIO/RPG/{group}.json').read_text(encoding='utf-8'))
        for record in old['languages']['en']:
            if record['fragment']==row['id']:continue
            original=dest.parent/Path(record['file']).name
            assert digest(original)==record['sha256'],'Existing recording changed: '+str(original)
        RpgAudioManager(PROJECT,script).install(('en',),OUT/'audio'/group)
        RpgSceneManager(PROJECT,script).build(('en',),OUT/'scenes'/group)
        print(group+': refusal voice and scenes installed',flush=True)
    print('Updated voiced parking groups:',len(groups),flush=True)


def stage():
    from files.rpg_reputation import parking_rules,parking_denial_ini
    from files.rpg_runtime import dialog_ini
    from managers.courier_owners import plan
    from managers.parking_commandants import parse,one
    from story.rpg.script import RpgScript
    from tools.data_folder import DataFolder
    folder=DataFolder(root=GAME);rows=contacts();files={}
    files['RPG/ship_parking.ini']=parking_rules(folder.data_path('RPG/ship_parking.ini').read_text(encoding='utf-8'),{r['base']:r['faction'] for r in rows}).encode()
    for row in rows:
        path=row['dialog'] or row['rtc'];text=folder.data_path(path).read_text(encoding='utf-8-sig')
        if row['group']:
            script=RpgScript.load(PROJECT/'story/rpg'/f'{row["group"]}.json')
            # Verify the newly compiled denial before exposing its fragment.
            manifest=json.loads(folder.data_path(f'SCRIPTS/RPG/{script.name}/en/manifest.json').read_text(encoding='utf-8'))
            fragment=next(r for r in manifest['fragments'] if r['id']==script.name+'_frag0023')
            assert digest(folder.data_path(fragment['path']))==fragment['sha256']
            assert digest(folder.data_path(fragment['audio']))==fragment['audio_sha256']
            old_header=next(v for k,v in parse(text) if k=='dialog')
            text=dialog_ini(script)
            new_header=next(v for k,v in parse(text) if k=='dialog')
            for key,values in old_header.items():
                if key not in new_header:
                    anchor='scene_group = '+script.name+'\n'
                    text=text.replace(anchor,anchor+''.join(f'{key} = {v}\n' for v in values),1)
        else:text=parking_denial_ini(text)
        files[path]=text.encode()
    registry=json.loads((PROJECT/'story/rpg/courier_owners.json').read_text(encoding='utf-8'))
    owner_files,report=plan(PROJECT,folder,registry,folder.data_path('MISSIONS/TrainCourier/catalog.ini').read_bytes())
    for path,content in owner_files.items():
        if path.startswith('RPG/courier/') and path.endswith('_dialog.ini'):files[path]=content
        else:assert folder.data_path(path).read_bytes()==content,'Unrelated owner output changed: '+path
    payload=OUT/'payload';DataFolder(root=payload).sync_service_reputation(files,OUT/'stage_backup')
    manifest={}
    for path in files:
        name='DATA/'+path
        if digest(GAME/name)!=digest(payload/name):manifest[name]={'before':digest(GAME/name),'after':digest(payload/name)}
    for name in ('Server.dll','Server.pdb','Content.dll','Content.pdb'):
        source=ROOT/'src/obj/train_courier/rpg1/bin'/name;path='bin/'+name
        target=payload/path;target.parent.mkdir(parents=True,exist_ok=True);target.write_bytes(source.read_bytes())
        manifest[path]={'before':digest(GAME/path),'after':digest(target)}
    dependencies={str(p.relative_to(GAME)):digest(p) for p in (GAME/'bin/Common.dll',GAME/'bin/freelancer.exe')}
    (OUT/'manifest.json').write_text(json.dumps({'files':manifest,'dependencies':dependencies},indent=2))
    print('Staged strict reputation:',len(rows),'parking sellers,',len(report),'locomotive owners;',len(manifest),'changed files')


def main():
    p=argparse.ArgumentParser();p.add_argument('action',choices=['sources','apply-sources','voices','stage','apply'])
    action=p.parse_args().action;OUT.mkdir(parents=True,exist_ok=True)
    if action=='sources':sources()
    elif action=='apply-sources':install(json.loads((OUT/'sources.json').read_text()),OUT/'sources',PROJECT,OUT/'source_backups',False)
    elif action=='voices':voices()
    elif action=='stage':stage()
    else:
        m=json.loads((OUT/'manifest.json').read_text())
        for name,value in m['dependencies'].items():assert digest(GAME/name)==value,'Changed dependency: '+name
        install(m['files'],OUT/'payload',GAME,OUT/'backups',True)


if __name__=='__main__':main()
