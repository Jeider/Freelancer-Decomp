"""Repair native RU dispatcher bank without replacing engine binaries or scenes."""
import argparse
import hashlib
import importlib.util
import json
from pathlib import Path
import sys

from courier_ru_bank import GAME, ROOT, merge, check, entries
from export import sections, one
from install_evacuation import idle, safe_file

sys.dont_write_bytecode = True
OUT = ROOT/'out/train_courier/audio_ru'
STAGE = OUT/'bank_package'
MANIFEST = OUT/'bank_install.json'
API = 'Assets/Pythonlancer/tools/data_folder.py'
MODULE = 'Assets/Pythonlancer/universe/audio/courier_ru.py'
BANK = 'DATA/AUDIO/dispatcher01.utf'


def sha(raw):
    return hashlib.sha256(raw).hexdigest()


def data_class():
    spec = importlib.util.spec_from_file_location('courier_bank_data_folder', STAGE/API)
    module = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(module)
    return module.DataFolder


def clips():
    report = json.loads((OUT/'installed.json').read_text(encoding='utf-8'))
    ids = [code for code, record in report['recordings'].items() if record['bank']!='bar']
    result = {code:(GAME/'DATA/AUDIO/MOD/dispatcher01'/(code+'.wav')).read_bytes() for code in ids}
    active=''; registered=set()
    for kind, values in sections(GAME/'DATA/AUDIO/voices_space_male.ini'):
        if kind=='voice': active=one(values,'nickname')
        elif kind=='sound' and active=='dispatcher01': registered.add(one(values,'msg'))
    assert result.keys() <= registered, 'Re-register missing courier INI entries first'
    return result


def stage():
    sources = clips()
    old = (GAME/BANK).read_bytes()
    packed, report = merge(old, sources)
    inherited = json.loads((OUT/'vocabulary_audit.json').read_text(encoding='utf-8'))['inherited']
    check(packed, sources, inherited)
    report['previous_leaf_hashes'] = {name:sha(raw) for name,raw in entries(old).items()}
    api = (GAME/API).read_bytes()
    if b"'AUDIO/dispatcher01.utf'" not in api:
        target = b"'AUDIO/RPG/rm0001_sounds.ini'}"
        assert api.count(target)==1
        api=api.replace(target, b"'AUDIO/RPG/rm0001_sounds.ini', 'AUDIO/dispatcher01.utf'}")
    path=safe_file(STAGE/API, STAGE);path.parent.mkdir(parents=True,exist_ok=True);path.write_bytes(api)
    source=(GAME/MODULE).read_bytes()
    start=source.index(b'    def get_sound(self, attenuation):')
    end=source.index(b'    def get_sound_as_file(', start)
    source=source[:start]+b'''    def get_sound(self, attenuation):
        # Existing dispatcher01.utf owns playback; compile new WAVs into it.
        return '\\n'.join(line for line in self.get_sound_as_file(attenuation, 'dispatcher01').split('\\n')
                         if not line.startswith('file = '))

'''+source[end:]
    path=safe_file(STAGE/MODULE, STAGE);path.parent.mkdir(parents=True,exist_ok=True);path.write_bytes(source)
    data_class()(root=STAGE).sync_train_courier_ru_audio({BANK[5:]:packed})
    report.update(files={name:{'before':sha((GAME/name).read_bytes()), 'after':sha((STAGE/name).read_bytes())}
                        for name in (API,MODULE,BANK)}, clips={code:sha(raw) for code,raw in sources.items()},
                  inherited=inherited, missing_before=[code for code,key in report['ids'].items() if key.lower() not in entries(old)])
    MANIFEST.write_text(json.dumps(report,indent=2),encoding='utf-8')
    print('Prepared native bank:',len(sources),'clips;',len(report['missing_before']),'previously absent;',
          report['preserved_leaves'],'old leaves preserved;',len(inherited),'base names verified')
    print('Logged missing ID 0xBC4D1DC9:',next((code for code,key in report['ids'].items() if key=='0xBC4D1DC9'),'not in this batch'))


def verify(report):
    raw=(GAME/BANK).read_bytes()
    assert sha(raw)==report['files'][BANK]['after']
    check(raw, clips(), report['inherited'])
    after=entries(raw);changed={key.lower() for key in report['ids'].values()}
    assert all(sha(after[name])==digest for name,digest in report['previous_leaf_hashes'].items() if name not in changed)
    for name,record in report['files'].items():
        assert sha((GAME/name).read_bytes())==record['after'],name


def apply():
    raise RuntimeError('UTF installation superseded by the user: use Pythonlancer single.py compile_dispatchers_audio for loose WAVs')
    # Historical transaction below is retained for review only.
    idle()
    report=json.loads(MANIFEST.read_text(encoding='utf-8'))
    assert {code:sha(raw) for code,raw in clips().items()}==report['clips']
    for name,record in report['files'].items():
        safe_file(GAME/name,GAME)
        assert sha((GAME/name).read_bytes())==record['before'],name
        assert sha((STAGE/name).read_bytes())==record['after'],name
    folder=data_class()(root=GAME)
    before={name:(GAME/name).read_bytes() for name in report['files']}
    applied=[]
    def put(name,raw):
        if name.startswith('DATA/'):
            folder.sync_train_courier_ru_audio({name[5:]:raw})
        else:
            safe_file(GAME/name,GAME).write_bytes(raw)
    try:
        for name in report['files']:
            applied.append(name);put(name,(STAGE/name).read_bytes())
        verify(report)
    except Exception:
        for name in reversed(applied):put(name,before[name])
        raise
    report['installed']=True
    (OUT/'bank_installed.json').write_text(json.dumps(report,indent=2),encoding='utf-8')
    safe_file(STAGE/BANK,STAGE)
    data_class()(root=STAGE).sync_train_courier_ru_audio({BANK[5:]:None})
    print('Installed/verified dispatcher01.utf:',len(report['clips']),'courier clips; original leaves preserved. No engine build.')


if __name__=='__main__':
    parser=argparse.ArgumentParser(description=__doc__)
    parser.add_argument('action',choices=('stage','apply','verify'))
    args=parser.parse_args()
    if args.action=='stage':stage()
    elif args.action=='apply':apply()
    else:verify(json.loads((OUT/'bank_installed.json').read_text(encoding='utf-8')))
