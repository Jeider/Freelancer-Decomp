"""Run staged Pythonlancer dispatcher export without building the game universe."""
import importlib.util
import json
from pathlib import Path
import sys
from types import SimpleNamespace

ROOT=Path(__file__).resolve().parents[2]
PROJECT=Path('D:/Games/FL_MOD/Assets/Pythonlancer')
PACKAGE=ROOT/'out/train_courier/evacuation/audio_package'
sys.path.insert(0,str(PROJECT))

def module(name,path):
    spec=importlib.util.spec_from_file_location(name,path)
    result=importlib.util.module_from_spec(spec)
    sys.modules[name]=result;spec.loader.exec_module(result)
    return result

def main():
    staged=PACKAGE/'Assets/Pythonlancer'
    import universe.audio
    evacuation=module('universe.audio.evacuation_en',staged/'universe/audio/evacuation_en.py')
    universe.audio.evacuation_en=evacuation
    dispatcher=module('universe.audio.dispatcher_en',staged/'universe/audio/dispatcher_en.py')
    empty=lambda:[]
    core=SimpleNamespace(universe=SimpleNamespace(get_bases=empty),
        population=SimpleNamespace(get_world_factions=empty),store=SimpleNamespace(get_commodities=empty))
    voice=dispatcher.EngMaleDispatcher(core)
    from evacuation_script import rows,FAMILIES
    from install_evacuation_audio import voice_properties,sound,read,API,data_class
    records=json.loads((ROOT/'out/train_courier/evacuation/audio_en/recordings.json').read_text(encoding='utf-8'))
    required={r['id']:r for r in rows() if r['speaker']=='dispatcher'}
    for _ in range(2):
        lines=voice.get_dynamic_lines()
        ids=[line.get_code() for line in lines]
        assert len(ids)==len(set(ids))
        chosen=[line for line in lines if line.get_code().startswith('te_')]
        assert len(chosen)==120 and {line.get_code() for line in chosen}==set(required)
        for line in chosen:
            row=required[line.get_code()]
            assert line.get_text()==row['en'] and line.trim_lead is False
            if row.get('delivery'):
                assert list(line.delivery.emo_vector)==row['delivery']['emo_vector']
            assert line.get_sound_as_file('attenuation = -4',voice.FOLDER).strip()==sound(row,records[row['id']]['duration']).strip()
        ini=voice.get_file_sounds_ini()
        assert sum(line.startswith('msg = te_') for line in ini.splitlines())==120
    template=read(staged/'templates/hardcoded_inis/static_content/voice_properties.ini')
    assert voice_properties(template)==template
    # The central API rejects an out-of-topic payload before any member is written.
    cls=data_class(read(staged/'tools/data_folder.py'));folder=cls(root=PACKAGE)
    for name in ('../escape.wav','AUDIO/MOD_ENG/dispatcher_en01/te_intro_06-.wav','MISSIONS/empathy.ini'):
        try:folder.sync_train_evacuation_audio({name:b''})
        except ValueError:pass
        else:raise AssertionError(name)
    print('PASS staged Pythonlancer exports: 120 unique lines, PCM durations, full sentences, idempotent permutations, scoped DATA API')

if __name__=='__main__':main()
