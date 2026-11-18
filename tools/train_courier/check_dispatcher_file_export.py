"""Exercise migration/rollback and audit actual RU inputs without game writes."""
import argparse
import importlib.util
import io
import json
from pathlib import Path
import re
import tempfile
import wave
import sys

from prepare_dispatcher_file_export import ROOT,PROJECT,OUT,PACKAGE,digest
from install_evacuation import safe_file
sys.path.insert(0,str(ROOT/'tools'))
from generate_station_lods import read_tree,write_tree,Node


def module(name,path):
    spec=importlib.util.spec_from_file_location(name,path)
    result=importlib.util.module_from_spec(spec);spec.loader.exec_module(result)
    return result


def wav(seconds):
    stream=io.BytesIO()
    with wave.open(stream,'wb') as out:
        out.setparams((1,2,24000,0,'NONE','not compressed'))
        out.writeframes(b'\x20\x01'*int(seconds*24000))
    return stream.getvalue()


def snapshot(path):
    return {p.relative_to(path).as_posix():p.read_bytes() for p in path.rglob('*') if p.is_file()}


def isolated(export,DataFolder):
    header,_=read_tree((PROJECT.parent.parent/'DATA/AUDIO/dispatcher01.utf').read_bytes())
    with tempfile.TemporaryDirectory(dir=OUT,prefix='checks_') as directory:
        root=Path(directory);game=root/'game';project=game/'Assets/Pythonlancer';project.mkdir(parents=True)
        safe_file(root,OUT)
        class Folder(DataFolder):
            fail=False
            def sync_data_file(self,name,content):
                if self.fail and name=='AUDIO/voices_space_male.ini':
                    self.fail=False
                    raise OSError('injected INI write failure')
                return super().sync_data_file(name,content)
        folder=Folder(root=game)
        native=Node('\\');native.children=[Node('0x1',blob=wav(1)),Node('0x2',blob=wav(.2)),Node('0x2',blob=wav(.3))]
        folder.sync_data_file('AUDIO/dispatcher01.utf',write_tree(header,[native]))
        folder.sync_data_file('AUDIO/voices_space_male.ini',b'[Voice]\nnickname = dispatcher01\n[Sound]\nmsg = tc_board_01-\nduration = 2\nPriority = -1\n[Sound]\nmsg = unused_legacy\n[Voice]\nnickname = english_unchanged\n[Sound]\nmsg = english\nfile = Audio\\MOD_ENG\\english.wav\n')
        folder.sync_data_file('AUDIO/voices_space_female.ini',b'; unchanged female file\n')
        source=project.parent/'PILOTS/dispatcher01/default/tc_board_01-.wav'
        source.parent.mkdir(parents=True);source.write_bytes(wav(1.5))
        actual_key=export.audio_key;export.audio_key=lambda game,code:'0x1' if code=='tc_board_01-' else '0x3'
        try:
            files,report=export.plan(project,folder)
            assert report['voices']['dispatcher01']['unrecorded_ids']==['unused_legacy']
            assert len(json.loads(files['AUDIO/MOD/dispatcher01/manifest.json'])['archive_leaves'])==3
            original=snapshot(game/'DATA');folder.fail=True
            try:folder.sync_ru_dispatcher_files(files,export.VOICES)
            except OSError:pass
            else:raise AssertionError('Rollback was not exercised')
            assert snapshot(game/'DATA')==original
            folder.sync_ru_dispatcher_files(files,export.VOICES)
            assert not folder.data_path('AUDIO/dispatcher01.utf').exists()
            assert folder.data_path('AUDIO/MOD/dispatcher01/tc_board_01-.wav').read_bytes()==wav(1.5)
            assert files['AUDIO/voices_space_male.ini'].split(b'[Voice]\nnickname = english_unchanged')[1]==original['AUDIO/voices_space_male.ini'].split(b'[Voice]\nnickname = english_unchanged')[1]
            source.write_bytes(wav(2))
            export.compile_dispatchers(project,folder)
            assert folder.data_path('AUDIO/MOD/dispatcher01/tc_board_01-.wav').read_bytes()==wav(2)
            before=snapshot(game/'DATA')
            for name in ('../escape','SHIPS/shiparch.ini','AUDIO/MOD_ENG/dispatcher_en01/a.wav'):
                try:folder.sync_ru_dispatcher_files({name:b'bad'},export.VOICES)
                except ValueError:pass
                else:raise AssertionError(name)
            assert snapshot(game/'DATA')==before
            # Missing required courier input aborts before any publication.
            broken=dict(files);broken['AUDIO/voices_space_male.ini']+=b'\n[Voice]\nnickname = dispatcher01\n[Sound]\nmsg = tc_missing_01-\n'
            try:export.compile_dispatchers(project,folder,broken)
            except ValueError:pass
            else:raise AssertionError('Missing courier audio accepted')
            assert snapshot(game/'DATA')==before
        finally:export.audio_key=actual_key
    print('PASS: transactional rollback, UTF deletion after verified WAV/INI, duplicate leaf preservation, later source edits, missing courier rejection, scoped DATA writes')


def real(export,DataFolder):
    folder=DataFolder(root=PROJECT.parent.parent)
    watched=[folder.data_path(name) for name in (*export.INIS,'MISSIONS/voice_properties.ini',*[f'AUDIO/{v}.utf' for v in export.VOICES])]
    before={str(p):digest(p) for p in watched}
    files,report=export.plan(PROJECT,folder)
    for voice,stats in report['voices'].items():
        manifest=json.loads(files[f'AUDIO/MOD/{voice}/manifest.json'])
        for row in [*manifest['recordings'].values(),*manifest['archive_leaves']]:
            assert export.digest(files[row['file']])==row['sha256']
        print(voice,stats['recordings'],'playable WAVs;',stats['archive_leaves_preserved'],'original leaves;',len(stats['unrecorded_ids']),'unrecorded legacy IDs')
    courier=json.loads((ROOT/'out/train_courier/audio_ru/installed.json').read_text(encoding='utf-8'))
    expected={code for code,record in courier['recordings'].items() if record['bank']!='bar'}
    manifest=json.loads(files['AUDIO/MOD/dispatcher01/manifest.json'])
    assert expected<=manifest['recordings'].keys()
    bases=json.loads((ROOT/'out/train_courier/audio_ru/vocabulary_audit.json').read_text())['inherited']
    assert set(bases)<=manifest['recordings'].keys()
    # Every rewritten file path resolves in the prepared batch. Non-RU blocks
    # retain their exact bytes, including English records and animation scripts.
    for ini in export.INIS:
        old=re.split(r'(?m)(?=^\[)',folder.data_path(ini).read_bytes().decode('utf-8-sig'))
        new=re.split(r'(?m)(?=^\[)',files[ini].decode('utf-8-sig'))
        assert len(old)==len(new)
        active=''
        for a,b in zip(old,new):
            if re.match(r'(?i)^\[voice\]',a):active=(export.value(a,'nickname') or export.value(a,'extend')).lower()
            if active not in export.VOICES:assert a==b
            elif a!=b:
                path=export.value(b,'file').replace('\\','/')
                assert path in files
                assert b.index('msg =')<b.index('file =')
    assert {str(p):digest(p) for p in watched}==before
    report['courier_clips']=len(expected);report['courier_base_names']=len(bases)
    report['live_data_unchanged']=True
    (OUT/'validation.json').write_text(json.dumps(report,ensure_ascii=False,indent=2),encoding='utf-8')
    print('PASS: real RU inventory, 236 courier clips, 76 base names, EN blocks unchanged; no live DATA writes')


if __name__=='__main__':
    parser=argparse.ArgumentParser(description=__doc__);parser.add_argument('--real',action='store_true');args=parser.parse_args()
    sys.dont_write_bytecode=True
    export=module('dispatcher_files_under_test',PACKAGE/'tools/dispatcher_files.py')
    DataFolder=module('dispatcher_data_folder_under_test',PACKAGE/'tools/data_folder.py').DataFolder
    isolated(export,DataFolder)
    if args.real:real(export,DataFolder)
