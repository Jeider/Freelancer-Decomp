"""Stage/publish Pythonlancer source changes only. Never write live DATA or INIs."""
import argparse
import ast
import hashlib
import json
from pathlib import Path

ROOT=Path(__file__).resolve().parents[2]
PROJECT=Path('D:/Games/FL_MOD/Assets/Pythonlancer')
SOURCE=Path(__file__).resolve().parent/'pythonlancer'
OUT=ROOT/'out/train_courier/audio_ru/file_export'
PACKAGE=OUT/'source'


def digest(path):
    return hashlib.sha256(path.read_bytes()).hexdigest() if path.exists() else None


def stage():
    files={}
    files['tools/dispatcher_files.py']=(SOURCE/'tools/dispatcher_files.py').read_text(encoding='utf-8')
    api=(PROJECT/'tools/data_folder.py').read_text(encoding='utf-8')
    assert 'def sync_ru_dispatcher_files(' not in api, 'Migration source already published; review before replacing'
    files['tools/data_folder.py']=api+'\n'+(SOURCE/'dispatcher_files_data_folder.inc').read_text(encoding='utf-8')
    manager=(PROJECT/'universe/audio/manager.py').read_text(encoding='utf-8')
    start=manager.index('        data_folder.sync_audio_ini(')
    end=manager.index('    def prepare_pilots_audio(',start)
    manager=manager[:start]+'''        # RU dispatcher WAVs and their INI paths form one verified transaction.
        from pathlib import Path
        from tools.dispatcher_files import compile_dispatchers
        files = {
            'AUDIO/voices_space_male.ini': self.core.tpl_manager.get_result(VOICES_MALE_TEMPLATE, voice_male_params).encode('utf-8'),
            'AUDIO/voices_space_female.ini': self.core.tpl_manager.get_result(VOICES_FEMALE_TEMPLATE, voice_female_params).encode('utf-8'),
            'MISSIONS/voice_properties.ini': self.core.tpl_manager.get_result(VOICE_PROPS_TEMPLATE, {
                'props': DIVIDER.join(mission_props),
            }).encode('utf-8'),
        }
        project = Path(__file__).resolve().parents[2]
        return compile_dispatchers(project, data_folder, files, output=project/'results/dispatcher_files')

'''+manager[end:]
    start=manager.index('    def compile_pilots_audio(self):')
    # This method is the final member in the current source; refuse surprises.
    assert '\n    def ' not in manager[start+5:]
    manager=manager[:start]+'''    def compile_pilots_audio(self):
        # Keep the established command, now compiling WAV files and matching INIs.
        return self.compile_pilots_ini()
'''
    files['universe/audio/manager.py']=manager
    single=(PROJECT/'single.py').read_text(encoding='utf-8')
    marker='import sys\n'
    assert single.startswith(marker)
    files['single.py']=single.replace(marker,marker+'''# RU dispatcher-only export, independent of full universe generation.
if __name__ == "__main__" and len(sys.argv) > 1 and sys.argv[1] == "compile_dispatchers_audio":
    sys.dont_write_bytecode = True
    from tools.dispatcher_files import main as dispatcher_files_main
    dispatcher_files_main(sys.argv[2:])
    raise SystemExit(0)
''',1)
    report={}
    for name, text in files.items():
        ast.parse(text)
        target=PACKAGE/name;target.parent.mkdir(parents=True,exist_ok=True)
        target.write_text(text,encoding='utf-8')
        report[name]={'before':digest(PROJECT/name),'after':digest(target)}
    (OUT/'sources.json').write_text(json.dumps(report,indent=2),encoding='utf-8')
    print('Prepared',len(files),'Pythonlancer source files; no live writes')


def publish():
    report=json.loads((OUT/'sources.json').read_text(encoding='utf-8'))
    before={}
    for name,row in report.items():
        assert name.endswith('.py') and not name.startswith(('DATA/','bin/'))
        assert digest(PROJECT/name)==row['before'], 'Concurrent source change: '+name
        assert digest(PACKAGE/name)==row['after']
        before[name]=(PROJECT/name).read_bytes() if (PROJECT/name).exists() else None
    applied=[]
    try:
        for name in report:
            applied.append(name)
            target=PROJECT/name;target.parent.mkdir(parents=True,exist_ok=True)
            target.write_bytes((PACKAGE/name).read_bytes())
        for name,row in report.items():assert digest(PROJECT/name)==row['after']
    except Exception:
        for name in reversed(applied):
            if before[name] is None:(PROJECT/name).unlink(missing_ok=True)
            else:(PROJECT/name).write_bytes(before[name])
        raise
    (OUT/'published.json').write_text(json.dumps(report,indent=2),encoding='utf-8')
    print('Published Pythonlancer scripts only. Game INIs, WAVs, UTFs and bin unchanged.')


if __name__=='__main__':
    parser=argparse.ArgumentParser(description=__doc__)
    parser.add_argument('action',choices=('stage','publish'))
    args=parser.parse_args()
    if args.action=='stage':stage()
    else:publish()
