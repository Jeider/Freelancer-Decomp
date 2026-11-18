"""Stage/verify/publish English evacuation radio and its source integration.

DATA staging, installation, rollback and cleanup all use Pythonlancer DataFolder.
Does not launch the game or produce cutscene THNs.
"""
import argparse
import ast
import hashlib
import json
import os
from pathlib import Path
import re
import shutil
import subprocess
import sys
from evacuation_script import rows, FAMILIES
from stage_evacuation import data_class, patch_once
from install_evacuation import idle, safe_file, verify_imports, SOURCES

ROOT=Path(__file__).resolve().parents[2]
GAME=Path('D:/Games/FL_MOD')
TOPIC=ROOT/'out/train_courier/evacuation'
AUDIO=TOPIC/'audio_en'
PACKAGE=TOPIC/'audio_package'
MANIFEST=TOPIC/'audio_install.json'
GEN='Assets/Pythonlancer/'
VOICE='atc_leg_m01_new'
API='''
    def sync_train_evacuation_audio(self, files):
        """English evacuation radio, including staging and transaction rollback."""
        import re
        fixed = {'AUDIO/voices_space_male.ini', 'MISSIONS/voice_properties.ini',
                 'MISSIONS/TrainCourier/courier.ini'}
        for name in files:
            if name not in fixed and not re.fullmatch(
                    r'AUDIO/MOD_ENG/dispatcher_en01/te_[a-z0-9_]+_0[1-5]-\\.wav', name):
                raise ValueError('Unexpected evacuation audio target: ' + name)
            self.data_path(name)
        for name, content in files.items():
            if content is None:
                self.remove_data_file(name)
            else:
                self.sync_data_file(name, content)
'''

def digest(path):
    return hashlib.sha256(path.read_bytes()).hexdigest() if path.exists() else None

def read(path):
    return path.read_text(encoding='utf-8-sig')

def voice_properties(text):
    blocks=re.split(r'(?m)(?=^\[)',text)
    found=0
    for i,block in enumerate(blocks):
        if block.lower().startswith('[mvoiceprop]') and re.search(r'(?m)^voice\s*=\s*'+VOICE+r'\s*$',block):
            found+=1
            block=re.sub(r'(?mi)^permutation_count\s*=\s*te_[^\n]*\n?', '',block)
            blocks[i]=block.rstrip()+'\n'+''.join(f'permutation_count = {name}, 5\n' for name in FAMILIES)+'\n'
    assert found==1,('Expected exactly one dispatcher permutation block',found)
    return ''.join(blocks)

def sounds_ini(text,records):
    blocks=re.split(r'(?m)(?=^\[)',text);active='';out=[];inserted=False
    additions='\n'.join(sound(row,records[row['id']]['duration']) for row in rows() if row['speaker']=='dispatcher')
    for block in blocks:
        if block.lower().startswith('[voice]'):
            if active==VOICE:
                out.append(additions);inserted=True
            active=re.search(r'(?mi)^nickname\s*=\s*([^\n]+)',block)[1].strip()
        if active==VOICE and block.lower().startswith('[sound]') and re.search(r'(?mi)^msg\s*=\s*te_',block):
            continue
        out.append(block)
    if active==VOICE:out.append(additions);inserted=True
    assert inserted
    return ''.join(out)

def sound(row,duration):
    return (f"[Sound]\nmsg = {row['id']}\nduration = {duration:.6f}\nattenuation = -4\n"
            f"file = Audio\\MOD_ENG\\dispatcher_en01\\{row['id']}.wav\nPriority = -1\n\n")

def source_module(records):
    # Full sentences opt out of TempPilot's fragment-oriented leading trimmer.
    payload=[(r['id'],r['en'],records[r['id']]['duration'],r.get('delivery')) for r in rows() if r['speaker']=='dispatcher']
    return '''"""Recorded English evacuation lines; Russian script remains separate."""
from pathlib import Path
import wave
from universe.audio.pilot_line import PilotLine
from universe.audio.parse_rule import RuleDefaultNoProcess
from audio.delivery import Delivery

class EvacuationLine(PilotLine):
    trim_lead = False

    def __init__(self, code, text, duration, delivery=None):
        style = Delivery(delivery['code'], emo_vector=tuple(delivery['emo_vector']), speed=delivery['speed']) if delivery else None
        super().__init__(code, text, RuleDefaultNoProcess, delivery=style)
        self.duration = duration

    def get_sound_as_file(self, attenuation, voice):
        source = Path(__file__).resolve().parents[2].parent / 'PILOTS' / voice / 'default' / (self.code+'.wav')
        duration = self.duration
        if source.exists():
            with wave.open(str(source), 'rb') as wav:
                duration = wav.getnframes() / wav.getframerate()
        return (f'[Sound]\\nmsg = {self.code}\\nduration = {duration:.6f}\\n{attenuation}\\n'
                f'file = Audio\\\\MOD_ENG\\\\{voice}\\\\{self.code}.wav\\nPriority = -1')

def lines():
    return [EvacuationLine(*row) for row in RECORDINGS]

RECORDINGS = '''+repr(payload)+'\n'

def write(root,data,name,raw):
    safe_file(root/name,root)
    if name.startswith('DATA/'):
        data.sync_train_evacuation_audio({name[5:]:raw})
    elif raw is None:
        (root/name).unlink(missing_ok=True)
    else:
        (root/name).parent.mkdir(parents=True,exist_ok=True)
        (root/name).write_bytes(raw)

def stage(runtime='client'):
    assert shutil.disk_usage(ROOT).free>1024**3
    records=json.loads(read(AUDIO/'recordings.json'))
    radio=[r for r in rows() if r['speaker']=='dispatcher']
    from voice_audio import wav_duration
    for row in radio:
        record=records[row['id']];path=AUDIO/(row['id']+'.wav')
        assert record['text']==row['en'] and digest(path)==record['sha256'],row['id']
        assert abs(wav_duration(path)-record['duration'])<.000001
        assert record.get('asr'), 'Missing radio transcription: '+row['id']
    audit=json.loads(read(AUDIO/'verification.json'))
    assert not audit['unresolved'] and audit['recordings_sha256']==digest(AUDIO/'recordings.json')
    data_source=read(GAME/GEN/'tools/data_folder.py')
    if 'def sync_train_evacuation_audio(' not in data_source:data_source=data_source.rstrip()+'\n'+API
    cls=data_class(data_source);data=cls(root=PACKAGE);files={}
    def put(name,content):
        raw=content.encode('utf-8') if isinstance(content,str) else content
        write(PACKAGE,data,name,raw)
        files[name]={'before':digest(GAME/name),'after':digest(PACKAGE/name)}
    put(GEN+'tools/data_folder.py',data_source)
    put(GEN+'universe/audio/evacuation_en.py',source_module(records))
    dispatcher=read(GAME/GEN/'universe/audio/dispatcher_en.py')
    dispatcher=patch_once(dispatcher,'from universe.audio import parse_rule as R',
        'from universe.audio import parse_rule as R\nfrom universe.audio import evacuation_en')
    dispatcher=patch_once(dispatcher,"    ATTENUATION = -4\n    def get_lines(self):",
        "    ATTENUATION = -4\n\n    def get_dynamic_lines(self):\n"
        "        # The two English identification mixins otherwise expand these twice.\n"
        "        return list({line.get_code(): line for line in self.get_lines()}.values())\n\n"
        "    def get_lines(self):")
    # Only this class's final return, before the next dispatcher declaration.
    start=dispatcher.index('class EngMaleDispatcher(')
    end=dispatcher.find('\nclass ',start+1)
    if end<0:end=len(dispatcher)
    part=patch_once(dispatcher[start:end],'        return lines',
        '        lines.extend(evacuation_en.lines())\n        return lines')
    dispatcher=dispatcher[:start]+part+dispatcher[end:]
    put(GEN+'universe/audio/dispatcher_en.py',dispatcher)
    pilot=read(GAME/GEN/'tools/audio_pilot.py')
    pilot=patch_once(pilot,'trim_lead=pilot.TRIM_LEAD,',"trim_lead=getattr(line, 'trim_lead', pilot.TRIM_LEAD),")
    put(GEN+'tools/audio_pilot.py',pilot)
    template=GEN+'templates/hardcoded_inis/static_content/voice_properties.ini'
    put(template,voice_properties(read(GAME/template)))
    for row in radio:
        raw=(AUDIO/(row['id']+'.wav')).read_bytes()
        put('DATA/AUDIO/MOD_ENG/dispatcher_en01/'+row['id']+'.wav',raw)
        put('Assets/PILOTS/dispatcher_en01/default/'+row['id']+'.wav',raw)
    put('DATA/AUDIO/voices_space_male.ini',sounds_ini(read(GAME/'DATA/AUDIO/voices_space_male.ini'),records))
    put('DATA/MISSIONS/voice_properties.ini',voice_properties(read(GAME/'DATA/MISSIONS/voice_properties.ini')))
    binaries=('Content.dll','Content.pdb') if runtime=='content' else ('freelancer.exe','freelancer.pdb')
    built=ROOT/'src/obj/train_courier/rpg1/bin' if runtime=='content' else TOPIC/'runtime/bin'
    SOURCES.update({name:GAME/'bin'/name for name in ('Common.dll','Server.dll','Content.dll','freelancer.exe')})
    SOURCES.update({name:built/name for name in binaries})
    verify_imports()
    for name in binaries:put('bin/'+name,(built/name).read_bytes())
    # Enable last; never expose a partially installed recording bank.
    config,count=re.subn(r'(?m)^evacuation_audio_enabled\s*=.*$', 'evacuation_audio_enabled = true',
                        read(GAME/'DATA/MISSIONS/TrainCourier/courier.ini'))
    assert count==1 and re.search(r'(?m)^voice\s*=\s*'+VOICE+r'\s*$',config)
    config=re.sub(r'(?m)^; (?:Enable only after the te_\* recording bank is installed\.|English evacuation bank installed:.*)$',
                  '; English radio: 13 active families; evacuation speech starts only after exit.',config)
    put('DATA/MISSIONS/TrainCourier/courier.ini',config)
    for name in files:
        if name.endswith('.py'):ast.parse(read(PACKAGE/name))
    report={'files':files,'sources':{str(p.relative_to(ROOT)):digest(p) for p in [
        Path(__file__),ROOT/'tools/train_courier/generate_evacuation_audio.py',ROOT/'tools/train_courier/evacuation_script.py',
        ROOT/'src/freelancer/Client/hud_comm.cpp',ROOT/'src/include/train_evacuation_audio.h',
        ROOT/'tools/train_courier/check_evacuation_audio_queue.py',ROOT/'tools/train_courier/check_evacuation_audio.py',
        ROOT/'tools/train_courier/check_evacuation_audio_export.py',
        ROOT/'tools/train_courier/evacuation_delivery.py',ROOT/'tools/train_courier/check_courier_failure.py',
        ROOT/'src/Content/TrainCourier.cpp',ROOT/'src/Content/TrainCourierEvacuation.inl',
        AUDIO/'recordings.json',AUDIO/'verification.json']},
        'dependencies':{p.name:digest(p) for p in (GAME/'bin').glob('*.dll')},
        'radio_lines':120,'bar_lines':'8 recorded separately; optional THN briefing not published',
        'game_launched':False,'runtime':runtime,'active_radio_families':13,'revised_radio_lines':45}
    if runtime=='content':report['dependencies']['freelancer.exe']=digest(GAME/'bin/freelancer.exe')
    for name in binaries:report['dependencies'].pop(name,None)
    suffixes={'.obj','.pch','.pdb','.dll','.exe','.lib','.exp','.res','.ilk','.idb','.iobj','.ipdb',
              '.tlog','.recipe','.lastbuildstate'}
    cleanup=[]
    build_folder=ROOT/'src/obj/train_courier/rpg1/Content' if runtime=='content' else TOPIC/'runtime'
    for folder in (build_folder,TOPIC/'imports'):
        safe_file(folder,ROOT)
        for current,dirs,names in os.walk(folder,followlinks=False):
            for name in dirs:safe_file(Path(current)/name,ROOT)
            cleanup.extend(Path(current)/name for name in names if Path(name).suffix.lower() in suffixes)
    cleanup += [TOPIC/'checks'/('evacuation_audio_queue'+ext) for ext in ('.obj','.exe')]
    cleanup += [TOPIC/'checks'/(stem+ext) for stem in ('courier_failure','evacuation','damage') for ext in ('.obj','.exe')]
    if runtime=='content':
        cleanup += [built/name for name in ('Content.dll','Content.pdb','Content.lib','Content.exp','Common.lib')]
    report['cleanup']={str(safe_file(p,ROOT).relative_to(ROOT)):digest(p) for p in cleanup if p.exists()}
    MANIFEST.write_text(json.dumps(report,indent=2),encoding='utf-8')
    verify(PACKAGE,report)
    subprocess.run([sys.executable,'-B',str(ROOT/'tools/train_courier/check_evacuation_audio_export.py')],
                   cwd=ROOT,check=True)
    print('Prepared',len(files),'files; English radio +',runtime,'fix; no live writes')

def verify(root,manifest):
    from export import sections,one
    records=json.loads(read(AUDIO/'recordings.json'))
    active='';sounds={};counts={}
    for kind,values in sections(root/'DATA/AUDIO/voices_space_male.ini'):
        if kind=='voice':active=one(values,'nickname')
        elif kind=='sound' and active==VOICE and one(values,'msg').startswith('te_'):
            name=one(values,'msg');assert name not in sounds,name;sounds[name]=values
    for kind,values in sections(root/'DATA/MISSIONS/voice_properties.ini'):
        if kind=='mvoiceprop' and one(values,'voice')==VOICE:
            for value in values.get('permutation_count',[]):
                name,n=map(str.strip,value.split(','))
                if name.startswith('te_'):assert name not in counts;counts[name]=int(n)
    radio=[r for r in rows() if r['speaker']=='dispatcher']
    assert set(sounds)=={r['id'] for r in radio} and counts==dict.fromkeys(FAMILIES,5)
    for row in radio:
        record=records[row['id']];values=sounds[row['id']]
        assert int(one(values,'priority'))==-1
        assert abs(float(one(values,'duration'))-record['duration'])<.000001
        assert digest(root/'DATA'/one(values,'file').replace('\\','/'))==record['sha256']
    for name,record in manifest['files'].items():assert digest(root/name)==record['after'],name
    print('PASS 120 WAV hashes, measured durations, unique sound IDs, 24 x 5 permutations, installed/source hashes')

def apply():
    idle();manifest=json.loads(read(MANIFEST))
    assert shutil.disk_usage(GAME).free>1024**3
    for name,value in manifest['sources'].items():assert digest(ROOT/name)==value,'Source changed: '+name
    for name,value in manifest['dependencies'].items():assert digest(GAME/'bin'/name)==value,'Dependency changed: '+name
    cls=data_class(read(PACKAGE/GEN/'tools/data_folder.py'));live=cls(root=GAME)
    backup=TOPIC/'audio_backup';back=cls(root=backup)
    verify(PACKAGE,manifest)
    for name,record in manifest['files'].items():
        safe_file(GAME/name,GAME)
        assert digest(GAME/name)==record['before'],'Live file changed: '+name
        if record['before'] is not None:
            write(backup,back,name,(GAME/name).read_bytes())
            assert digest(backup/name)==record['before']
    changed=[]
    try:
        for name,record in manifest['files'].items():
            assert digest(GAME/name)==record['before'],'Concurrent live change: '+name
            changed.append(name);write(GAME,live,name,(PACKAGE/name).read_bytes())
            assert digest(GAME/name)==record['after'],name
        verify(GAME,manifest)
    except BaseException:
        for name in reversed(changed):
            expected=manifest['files'][name]['before']
            write(GAME,live,name,(backup/name).read_bytes() if expected is not None else None)
            assert digest(GAME/name)==expected,'Rollback failed: '+name
        raise
    (TOPIC/'audio_installed.json').write_text(json.dumps(manifest,indent=2),encoding='utf-8')
    # Remove exact verified package/rollback members, through DataFolder for DATA.
    staged=cls(root=PACKAGE)
    for name,record in manifest['files'].items():
        assert digest(PACKAGE/name)==record['after']
        write(PACKAGE,staged,name,None)
        if record['before'] is not None:
            assert digest(backup/name)==record['before']
            write(backup,back,name,None)
    # Delete only this task's captured outputs, never another build's new files.
    for name,expected in manifest['cleanup'].items():
        path=safe_file(ROOT/name,ROOT)
        assert digest(path)==expected,'Build cleanup input changed: '+name
        path.unlink()
    verify(GAME,manifest)
    print('Installed English evacuation voiceover. Original recordings retained. Game not launched.')

if __name__=='__main__':
    parser=argparse.ArgumentParser(description=__doc__);parser.add_argument('--apply',action='store_true')
    parser.add_argument('--runtime',choices=('client','content'),default='client')
    args=parser.parse_args();apply() if args.apply else stage(args.runtime)
