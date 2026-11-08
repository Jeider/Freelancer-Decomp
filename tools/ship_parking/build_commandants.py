"""Prepare, record, verify and install every Pythonlancer shipdealer commandant."""
import argparse
import datetime
import hashlib
import importlib.util
import json
import re
from pathlib import Path
import shutil
import subprocess
import sys

ROOT=Path(__file__).resolve().parents[2]
PROJECT=Path('D:/Games/FL_MOD/Assets/Pythonlancer')
GAME=PROJECT.parent.parent
OUT=ROOT/'src/obj/ship_parking/commandants'
sys.path.insert(0,str(PROJECT))
sys.dont_write_bytecode=True


def sha(path): return hashlib.sha256(path.read_bytes()).hexdigest()


def sources():
    changes={'managers/parking_commandants.py':Path(__file__).with_name('commandants.py').read_bytes(),
             'managers/parking_rooms.py':Path(__file__).with_name('parking_rooms.py').read_bytes(),
             'managers/parking_ui.py':Path(__file__).with_name('parking_ui.py').read_bytes()}
    def patch(relative,anchor,new,marker):
        raw=(PROJECT/relative).read_bytes(); nl='\r\n' if b'\r\n' in raw else '\n'
        text=raw.decode('utf-8-sig').replace('\r\n','\n')
        if marker not in text:
            if text.count(anchor)!=1: raise ValueError('Review changed source: '+relative)
            text=text.replace(anchor,new,1)
        changes[relative]=text.replace('\n',nl).encode('utf-8')
    method=Path(__file__).with_name('commandants_data.inc').read_text(encoding='utf-8')
    patch('tools/data_folder.py','    def get_root(self):',method+'    def get_root(self):','def sync_parking_commandants(')
    # Update this API alone while retaining unrelated DataFolder extensions.
    raw=changes['tools/data_folder.py']; nl='\r\n' if b'\r\n' in raw else '\n'
    text=raw.decode('utf-8').replace('\r\n','\n')
    text,count=re.subn(r'(?ms)^    def sync_parking_commandants\(.*?(?=^    def |\Z)',
                       lambda _:method.rstrip()+'\n\n',text)
    assert count==1
    changes['tools/data_folder.py']=text.replace('\n',nl).encode('utf-8')
    ui_method=Path(__file__).with_name('ui_data.inc').read_text(encoding='utf-8')
    text=changes['tools/data_folder.py'].decode('utf-8').replace('\r\n','\n')
    if 'def sync_parking_ui(' not in text:
        text=text.replace('    def get_root(self):',ui_method+'    def get_root(self):',1)
    else:
        text,count=re.subn(r'(?ms)^    def sync_parking_ui\(.*?(?=^    def |\Z)',
                          lambda _:ui_method.rstrip()+'\n\n',text)
        assert count==1
    changes['tools/data_folder.py']=text.replace('\n',nl).encode('utf-8')
    anchor='            data_folder.sync_interior_room(room.get_name(), content)'
    patch('managers/universe.py',anchor,anchor+'\n\n        from managers.parking_commandants import sync_from_universe\n        sync_from_universe(self, data_folder)\n','sync_from_universe(self, data_folder)')
    anchor='        authored = getattr(sequence, GESTURE_SEQUENCE)'
    seated='''        # Seated commandants keep the chair pose throughout their gesture track.
        if fragment['role'] == 'vendor' and script.data.get('vendor_posture') == 'sit':
            seated = ['Sc_MLBODY_CHRB_SHRG_SHLDRS_SMALL_000LV_XA_03',
                      'Sc_MLBODY_CHRB_IDLE_SMALL_000LV_XA_07',
                      'Sc_MLBODY_CHRB_IDLE_MED_000LV_XA_07',
                      'Sc_MLBODY_CHRB_IDLE_000LV_XA_05']
            authored = [[{'anim': seated[i % len(seated)], 'time_scale': .6, 'trans_time': .8}]
                        for i in range(GESTURE_COUNT)]
        else:
            authored = getattr(sequence, GESTURE_SEQUENCE)'''
    patch('story/rpg/scene.py',anchor,seated,'# Seated commandants keep')
    backup=OUT/'source_backups'/datetime.datetime.now().strftime('%Y%m%d_%H%M%S_%f')
    for name,content in changes.items():
        compile(content,name,'exec')
        target=PROJECT/name
        if target.exists() and target.read_bytes()==content: continue
        if target.exists():
            saved=backup/name; saved.parent.mkdir(parents=True,exist_ok=True); saved.write_bytes(target.read_bytes())
        target.parent.mkdir(parents=True,exist_ok=True); target.write_bytes(content)
    print('Installed Pythonlancer commandant generator and automatic universe hook',flush=True)


def prepare():
    from managers.parking_commandants import assign_registry,plan
    from tools.data_folder import DataFolder
    rows=json.loads((OUT/'source_bases.json').read_text(encoding='utf-8'))
    rows=[{k:v for k,v in row.items() if k not in ('contact','cls','bar','story','shipdealer')}
          for row in rows if row['shipdealer']]
    for row in rows:
        row['name_ru']=row['name_ru'].replace('+','');row['name_en']=row['name_en'].replace('+','')
    registry=assign_registry(PROJECT,rows)
    files,scripts,report=plan(PROJECT,DataFolder(root=GAME),registry)
    stage=DataFolder(root=OUT/'stage')
    for name,content in files.items(): stage.sync_data_file(name,content)
    changed=[]
    for group,data in scripts.items():
        path=PROJECT/'story/rpg'/f'{group}.json'
        content=(json.dumps(data,ensure_ascii=False,indent=2)+'\n').encode('utf-8')
        if not path.exists() or path.read_bytes()!=content: changed.append(group)
        if path.exists() and path.read_bytes()!=content:
            saved=OUT/'scenario_backups'/datetime.datetime.now().strftime('%Y%m%d_%H%M%S_%f')/path.name
            saved.parent.mkdir(parents=True,exist_ok=True);saved.write_bytes(path.read_bytes())
        path.write_bytes(content)
    (PROJECT/'story/rpg/parking_commandants.json').write_text(json.dumps(registry,ensure_ascii=False,indent=2)+'\n',encoding='utf-8')
    (OUT/'coverage.json').write_text(json.dumps(report,ensure_ascii=False,indent=2),encoding='utf-8')
    (OUT/'plan.json').write_text(json.dumps({n:hashlib.sha256(c).hexdigest() for n,c in files.items()},indent=2))
    (OUT/'scenarios_changed.json').write_text(json.dumps(changed))
    print(f'Prepared {len(report)} commandants; {len(scripts)} new base scenarios; {sum(r.get("posture")=="sit" for r in report)} seated',flush=True)


def voices():
    from story.rpg.script import RpgScript
    from tools.voice_api import VoiceApi
    from tools.voicestudio import VoiceStudioClone
    from managers.rpg_audio import RpgAudioManager
    from managers.rpg_scene import RpgSceneManager
    from tools.data_folder import DataFolder
    registry=json.loads((PROJECT/'story/rpg/parking_commandants.json').read_text(encoding='utf-8'))
    cache=OUT/'voice_cache';cache.mkdir(exist_ok=True)
    source_root=PROJECT.parent/'AUDIO_CUTSCENE_EN'
    def key(sound):
        actor=sound.line.actor
        sample=VoiceStudioClone.source_file(actor.__name__,'en')
        return hashlib.sha256(json.dumps([actor.__name__,sound.line.en,sha(sample),
            str(actor.get_voice_delivery().get_instruct()) if hasattr(actor.get_voice_delivery(),'get_instruct') else str(actor.get_voice_delivery().__dict__),actor.STEOS_SPEED],ensure_ascii=False).encode()).hexdigest()
    # Deduplicate only equal text/actor/reference/delivery. Each scene still owns
    # its own stable fragment IDs, sound bank, audio manifest and THNs.
    generated=reused=0
    for index,entry in enumerate(registry['bases']):
        if entry.get('authored'): continue
        group=entry['group'];script=RpgScript.load(PROJECT/'story/rpg'/f'{group}.json')
        target=source_root/group;target.mkdir(parents=True,exist_ok=True)
        for sound in script.recording_group().get_sounds():
            signature=key(sound); cached=cache/(signature+'.wav'); dest=target/(sound.name+'.wav')
            meta=dest.with_suffix('.voice.json')
            if cached.exists():
                if not dest.exists() or sha(dest)!=sha(cached): shutil.copy2(cached,dest)
                reused+=1
            elif dest.exists() and meta.exists() and json.loads(meta.read_text())['key']==signature:
                shutil.copy2(dest,cached);reused+=1
            else:
                VoiceApi.generate_en_voice(sound=sound,file_destination=dest)
                shutil.copy2(dest,cached);generated+=1
            meta.write_text(json.dumps({'key':signature,'sha256':sha(dest)}))
        RpgAudioManager(PROJECT,script).install(('en',),OUT/'audio'/group)
        RpgSceneManager(PROJECT,script).build(('en',),OUT/'scenes'/group)
        print(f'[{index+1}/{len(registry["bases"])}] {entry["base"]}: {group}; new audio {generated}, reused {reused}',flush=True)
    print(f'English generation complete: {generated} unique recordings; {reused} identical lines reused',flush=True)


def scenes_changed():
    from story.rpg.script import RpgScript
    from managers.rpg_scene import RpgSceneManager
    for group in json.loads((OUT/'scenarios_changed.json').read_text()):
        script=RpgScript.load(PROJECT/'story/rpg'/f'{group}.json')
        RpgSceneManager(PROJECT,script).build(('en',),OUT/'scenes'/group)
        print('Rebuilt changed scenario:',group,flush=True)


def install():
    from tools.data_folder import DataFolder
    from managers.parking_commandants import plan
    registry=json.loads((PROJECT/'story/rpg/parking_commandants.json').read_text(encoding='utf-8'))
    folder=DataFolder(root=GAME)
    files,scripts,report=plan(PROJECT,folder,registry)
    assert all(r.get('authored') or r['voiced']==len(scripts[r['group']]['fragments']) for r in report),'Generate every English scene first'
    # Validate complete installed scene/audio bytes using the production compiler.
    from managers.rpg_scene import RpgSceneManager
    from story.rpg.script import RpgScript
    for group,data in scripts.items():
        compiled,_=RpgSceneManager(PROJECT,RpgScript(data)).plan(('en',))
        for name,content in compiled.items():
            if folder.data_path(name).read_bytes()!=content: raise ValueError('Stale compiled scene: '+name)
    folder.sync_parking_commandants(files,OUT/'data_backups'/datetime.datetime.now().strftime('%Y%m%d_%H%M%S_%f'))
    for name,content in files.items(): assert folder.data_path(name).read_bytes()==content
    (OUT/'installed.json').write_text(json.dumps(report,ensure_ascii=False,indent=2),encoding='utf-8')
    print(f'Installed and verified {len(report)} commandants with complete English dialogue',flush=True)


def engine(client_only=False):
    names=('freelancer.exe','freelancer.pdb') if client_only else ('freelancer.exe','freelancer.pdb','Content.dll','Content.pdb')
    processes=subprocess.run(['tasklist','/FO','CSV','/NH'],capture_output=True,check=True).stdout.lower()
    if any(b'"'+n+b'"' in processes for n in (b'freelancer.exe',b'freelancer_en.exe',b'freelancer_window.exe',b'freelancer_window_en.exe',b'flserver.exe')):
        raise RuntimeError('Close the game before installing the parking window and dialogue update')
    backup=OUT/'engine_backups'/datetime.datetime.now().strftime('%Y%m%d_%H%M%S_%f');backup.mkdir(parents=True)
    before={n:(GAME/'bin'/n).read_bytes() for n in names}
    after={n:(ROOT/'src/obj/train_courier/rpg1/bin'/n).read_bytes() for n in names}
    for n in names:(backup/n).write_bytes(before[n])
    touched=[]
    try:
        for n in names:
            assert (GAME/'bin'/n).read_bytes()==before[n]
            touched.append(n);(GAME/'bin'/n).write_bytes(after[n]);assert (GAME/'bin'/n).read_bytes()==after[n]
    except BaseException:
        for n in reversed(touched):(GAME/'bin'/n).write_bytes(before[n])
        raise
    print('Installed verified '+('client' if client_only else 'client and Content.dll')+'; backup:',backup,flush=True)


def client():
    engine(client_only=True)


if __name__=='__main__':
    parser=argparse.ArgumentParser(description=__doc__)
    parser.add_argument('command',choices=['sources','prepare','voices','scenes_changed','install','engine','client'])
    args=parser.parse_args()
    globals()[args.command]()
