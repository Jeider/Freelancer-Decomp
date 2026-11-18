"""Validate RU bank coverage, timings, language isolation and source regeneration."""
import ast
from collections import Counter
import json
from pathlib import Path
import re
from generate_courier_ru import OUT, ASSETS, plan, sha
from install_courier_ru import PACKAGE, GEN, data_class
from export import sections, one
from voice_audio import wav_duration


def voices(path):
    active = ''
    result = {}
    for kind, values in sections(path):
        if kind == 'voice':
            active = one(values, 'nickname')
        if kind == 'sound':
            result.setdefault(active, []).append(values)
    return result


def main():
    game = ASSETS.parent
    manifest = json.loads((OUT/'install.json').read_text(encoding='utf-8'))
    records = manifest['recordings']
    missing = set(manifest.get('missing_cargo', []))
    for name, entry in manifest['files'].items():
        assert sha(PACKAGE/name) == entry['after'], name
        assert not name.endswith('.thn') and 'SHIPS/' not in name.upper()
    before = voices(game/'DATA/AUDIO/voices_space_male.ini')
    after = voices(PACKAGE/'DATA/AUDIO/voices_space_male.ini')
    assert before.keys() == after.keys()
    for voice in before:
        if voice != 'dispatcher01':
            assert before[voice] == after[voice], 'Other voice changed: '+voice
    sounds = {one(row, 'msg'): row for row in after['dispatcher01']}
    new_ids = {r['id'] for r in plan() if r['bank'] != 'bar'} - missing
    counts=Counter(one(row,'msg') for row in after['dispatcher01'])
    assert all(counts[code]==1 for code in new_ids), 'Duplicate new RU sound IDs'
    # Shared retail-style base names already repeat (Osiris, Musashi, etc.).
    # Preserve their complete sequence; do not clean unrelated legacy entries.
    assert ([r for r in before['dispatcher01'] if one(r,'msg') not in new_ids] ==
            [r for r in after['dispatcher01'] if one(r,'msg') not in new_ids])
    for code in new_ids:
        row = sounds[code]
        assert one(row, 'file') == 'Audio\\MOD\\dispatcher01\\'+code+'.wav'
        path = PACKAGE/'DATA'/one(row, 'file').replace('\\','/')
        assert abs(wav_duration(path)-float(one(row,'duration'))) < .000001
        assert sha(path) == records[code]['sha256']
    old_props = {one(v,'voice'):v for kind,v in sections(game/'DATA/MISSIONS/voice_properties.ini') if kind=='mvoiceprop'}
    new_props = {one(v,'voice'):v for kind,v in sections(PACKAGE/'DATA/MISSIONS/voice_properties.ini') if kind=='mvoiceprop'}
    for voice in old_props:
        if voice!='dispatcher01':
            assert new_props[voice] == old_props[voice]
    for entry in new_props['dispatcher01']['permutation_count']:
        family, count = [s.strip() for s in entry.split(',')]
        if family.startswith(('tc_','te_')) and any(code.startswith(family+'_') for code in new_ids):
            for number in range(1,int(count)+1):
                assert sum(code in sounds for code in (f'{family}_{number:02}+',f'{family}_{number:02}-')) >= 1
    vocabulary = json.loads((OUT/'vocabulary_audit.json').read_text(encoding='utf-8'))
    assert not vocabulary['utf_missing'] and not vocabulary['utf_silent']
    assert set(vocabulary['required']) - missing <= sounds.keys()
    assert not missing.intersection(new_ids)
    for code in missing:
        assert not (PACKAGE/'DATA/AUDIO/MOD/dispatcher01'/(code+'.wav')).exists()
    assert len(vocabulary['utf_durations']) == len(vocabulary['inherited'])
    assert manifest.get('voice_backend')=='loose_wav'
    assert 'DATA/AUDIO/dispatcher01.utf' not in manifest['files']
    assert not (game/'DATA/AUDIO/dispatcher01.utf').exists(), 'Run Pythonlancer dispatcher file migration first'
    for code in vocabulary['inherited']:
        path=game/'DATA'/one(sounds[code],'file').replace('\\','/')
        assert path.is_file(), 'Missing migrated base recording: '+code
        wav_duration(path)
    bank = json.loads((PACKAGE/'DATA/AUDIO/RPG/rm0001.json').read_text(encoding='utf-8'))
    old_bank = json.loads((game/'DATA/AUDIO/RPG/rm0001.json').read_text(encoding='utf-8'))
    assert bank['languages']['en'] == old_bank['languages']['en']
    assert len(bank['languages']['ru']) == 32
    for row in bank['languages']['ru']:
        path = PACKAGE/'DATA'/row['file']
        assert sha(path)==row['sha256'] and abs(wav_duration(path)-row['duration_seconds']) < .000001
    config = next(v for k,v in sections(PACKAGE/'DATA/MISSIONS/TrainCourier/courier.ini') if k=='presentation')
    assert config['voice_ru']==['dispatcher01'] and config['voice_en']==['atc_leg_m01_new']
    assert config['composed_audio']==['true'] and config['audio_enabled']==['true']
    assert {entry.split(',')[1].strip() for entry in config.get('unvoiced_cargo', [])
            if entry.split(',')[0].strip()=='dispatcher01'} == missing
    module = (PACKAGE/(GEN+'universe/audio/courier_ru.py')).read_text(encoding='utf-8')
    tree = ast.parse(module)
    payload = next(ast.literal_eval(n.value) for n in tree.body if isinstance(n,ast.Assign) and n.targets[0].id=='RECORDINGS')
    assert {r[0] for r in payload} == new_ids
    assert all(text==records[code]['text'] and duration==records[code]['duration'] for code,text,duration in payload)
    # Reject forbidden targets before the central API performs any write.
    folder = data_class()(root=OUT/'rejected_path_check')
    for name in ('../outside', 'SHIPS/shiparch.ini', 'SCRIPTS/RPG/rm0001/ru/anything.thn', 'AUDIO/MOD_ENG/dispatcher_en01/tc_board_01-.wav'):
        try:
            folder.sync_train_courier_ru_audio({name:b'forbidden'})
        except ValueError:
            pass
        else:
            raise AssertionError(name)
    print(f'PASS: {len(new_ids)} RU radio/name clips, 32 bar clips, 76 inherited base clips; real durations; EN and other voices unchanged; DATA scope guards')


if __name__ == '__main__':
    main()
