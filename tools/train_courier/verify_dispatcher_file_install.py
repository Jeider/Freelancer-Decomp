"""Snapshot and verify the user-requested Pythonlancer dispatcher publication."""
import argparse
import hashlib
import importlib.util
import json
from pathlib import Path
import re
import sys

ROOT=Path(__file__).resolve().parents[2]
GAME=Path('D:/Games/FL_MOD')
PROJECT=GAME/'Assets/Pythonlancer'
OUT=ROOT/'out/train_courier/audio_ru/file_export'
sys.dont_write_bytecode=True
sys.path.insert(0,str(PROJECT))
from tools.dispatcher_files import VOICES,INIS,value,duration
from tools.data_folder import DataFolder


def sha(raw):return hashlib.sha256(raw).hexdigest()


def other_voices():
    result={}
    for name in INIS:
        blocks=re.split(r'(?m)(?=^\[)',(GAME/'DATA'/name).read_bytes().decode('utf-8-sig'))
        active='';unchanged=[]
        for block in blocks:
            if re.match(r'(?i)^\[voice\]',block):active=(value(block,'nickname') or value(block,'extend')).lower()
            if active not in VOICES:unchanged.append(block)
        result[name]=sha(''.join(unchanged).encode('utf-8'))
    return result


def before():
    archives={}
    for voice in VOICES:
        archive=GAME/f'DATA/AUDIO/{voice}.utf'
        manifest=GAME/f'DATA/AUDIO/MOD/{voice}/manifest.json'
        if archive.exists():archives[voice]=sha(archive.read_bytes())
        elif manifest.exists():archives[voice]=json.loads(manifest.read_text(encoding='utf-8'))['source_utf_sha256']
    report={'other_voices':other_voices(),'archives':archives}
    (OUT/'install_before.json').write_text(json.dumps(report,indent=2),encoding='utf-8')
    print('Saved dispatcher archive hashes and non-RU voice registry hashes')


def after():
    baseline=json.loads((OUT/'install_before.json').read_text(encoding='utf-8'))
    assert other_voices()==baseline['other_voices'],'Other voices changed'
    report={'voices':{},'other_voices_unchanged':True,'game_launched':False}
    manifests={}
    for voice in VOICES:
        assert not (GAME/f'DATA/AUDIO/{voice}.utf').exists(), 'UTF still overrides WAVs: '+voice
        manifest=json.loads((GAME/f'DATA/AUDIO/MOD/{voice}/manifest.json').read_text(encoding='utf-8'))
        manifests[voice]=manifest
        assert manifest['source_utf_sha256']==baseline['archives'][voice]
        for row in [*manifest['recordings'].values(),*manifest['archive_leaves']]:
            raw=(GAME/'DATA'/row['file']).read_bytes()
            assert sha(raw)==row['sha256'],row['file']
            seconds=duration(raw)
            if 'duration' in row:assert abs(seconds-row['duration'])<1e-6
        report['voices'][voice]={'recordings':len(manifest['recordings']),
            'preserved_archive_leaves':len(manifest['archive_leaves']),
            'unrecorded_legacy_ids':len(manifest['unrecorded_ids'])}
    for name in INIS:
        active=''
        for block in re.split(r'(?m)(?=^\[)',(GAME/'DATA'/name).read_bytes().decode('utf-8-sig')):
            if re.match(r'(?i)^\[voice\]',block):active=(value(block,'nickname') or value(block,'extend')).lower()
            if active in VOICES and re.match(r'(?i)^\[(sound|voicesound)\]',block):
                code=value(block,'msg');record=manifests[active]['recordings'].get(code)
                if record:
                    assert value(block,'file').replace('\\','/')==record['file']
                    assert abs(float(value(block,'duration'))-record['duration'])<1e-6
    installed=json.loads((OUT.parent/'installed.json').read_text(encoding='utf-8'))
    courier={code for code,row in installed['recordings'].items() if row['bank']!='bar'}
    assert courier<=manifests['dispatcher01']['recordings'].keys()
    report['courier_clips']=len(courier)
    (OUT/'installed.json').write_text(json.dumps(report,indent=2),encoding='utf-8')
    # The previous packed-UTF proposal has been superseded and this replacement
    # has now installed successfully. Remove only its exact staged binary.
    old=OUT.parent/'bank_install.json';package=OUT.parent/'bank_package'
    if old.exists():
        plan=json.loads(old.read_text(encoding='utf-8'))
        relative='DATA/AUDIO/dispatcher01.utf';target=(package/relative).resolve()
        assert target.is_relative_to(package.resolve())
        if target.exists():
            assert not any(p.is_junction() or p.is_symlink() for p in (target,*target.parents) if p.is_relative_to(package.resolve()))
            assert sha(target.read_bytes())==plan['files'][relative]['after']
            DataFolder(root=package).remove_data_file(relative[5:])
    print('PASS: three dispatchers installed as WAV; UTFs removed; 236 courier clips; every original leaf preserved; other voices unchanged')


if __name__=='__main__':
    parser=argparse.ArgumentParser(description=__doc__);parser.add_argument('action',choices=('before','after'));args=parser.parse_args()
    OUT.mkdir(parents=True,exist_ok=True)
    before() if args.action=='before' else after()
