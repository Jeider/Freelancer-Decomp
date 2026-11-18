"""Stage/apply RU courier audio and language selection. Never builds THNs/ships.

All DATA staging, publication and rollback use Pythonlancer's DataFolder API.
The prepared transaction is hash-guarded against concurrent user changes.
"""
import argparse
import ast
import hashlib
import importlib.util
import json
import os
from pathlib import Path
import re
import shutil
import sys
import wave

from generate_courier_ru import ROOT, OUT, ASSETS, plan, sha, save
from dispatcher_ru import FAMILIES
from export import sections, one
from install_evacuation import safe_file, idle, verify_imports, SOURCES

GAME = ASSETS.parent
PROJECT = ASSETS / 'Pythonlancer'
PACKAGE = OUT / 'package'
GEN = 'Assets/Pythonlancer/'
BIN = ROOT / 'src/obj/train_courier/rpg1/bin'
MANIFEST = OUT / 'install.json'
BINARIES = ('Content.dll', 'Content.pdb', 'freelancer.exe', 'freelancer.pdb')
API = '''
    def sync_train_courier_ru_audio(self, files):
        """Russian courier audio only, including staging and rollback."""
        import re
        fixed = {'AUDIO/voices_space_male.ini', 'MISSIONS/voice_properties.ini',
                 'MISSIONS/TrainCourier/courier.ini', 'AUDIO/RPG/rm0001.json',
                 'AUDIO/RPG/rm0001_sounds.ini', 'AUDIO/dispatcher01.utf'}
        for name in files:
            if name not in fixed and not re.fullmatch(
                    r'AUDIO/MOD/(?:dispatcher01/[a-z0-9_+\\-]+|RPG/rm0001/rm0001_frag[0-9]{4}_l001_(?:vendor|player))\\.wav', name):
                raise ValueError('Unexpected RU courier audio target: ' + name)
            self.data_path(name)
        for name, content in files.items():
            if content is None:
                self.remove_data_file(name)
            else:
                self.sync_data_file(name, content)
'''


def digest(path):
    return sha(path) if path.is_file() else None


def data_class():
    source = PACKAGE / (GEN + 'tools/data_folder.py')
    spec = importlib.util.spec_from_file_location('courier_ru_data_folder', source)
    module = importlib.util.module_from_spec(spec)
    sys.dont_write_bytecode = True
    spec.loader.exec_module(module)
    return module.DataFolder


def write(root, data, relative, raw):
    target = safe_file(root / relative, root)
    if relative.startswith('DATA/'):
        data.sync_train_courier_ru_audio({relative[5:]: raw})
    elif raw is None:
        target.unlink(missing_ok=True)
    else:
        target.parent.mkdir(parents=True, exist_ok=True)
        target.write_bytes(raw)


def source_module(rows, records):
    payload = [(r['id'], r['text'], records[r['id']]['duration']) for r in rows if r['bank'] != 'bar']
    counts = {name: len(variants) for name, (_, variants) in FAMILIES.items()}
    for row in rows:
        if row['bank'] == 'evacuation':
            counts[row['id'].rsplit('_', 1)[0]] = 5
    return '''"""RU courier radio: clean recordings, nominative names, measured durations."""
from pathlib import Path
import wave
from universe.audio.pilot_line import PilotLine
from universe.audio.parse_rule import RuleDefaultNoProcess

class CourierLine(PilotLine):
    trim_lead = False

    def __init__(self, code, text, duration):
        super().__init__(code, text, RuleDefaultNoProcess)
        self.duration = duration

    def get_sound(self, attenuation):
        return self.get_sound_as_file(attenuation, 'dispatcher01')

    def get_sound_as_file(self, attenuation, voice):
        source = Path(__file__).resolve().parents[2].parent / 'PILOTS' / voice / 'default' / (self.code+'.wav')
        duration = self.duration
        if source.exists():
            with wave.open(str(source), 'rb') as wav:
                duration = wav.getnframes() / wav.getframerate()
        return (f'[Sound]\\nmsg = {self.code}\\nduration = {duration:.6f}\\n{attenuation}\\n'
                f'file = Audio\\\\MOD\\\\{voice}\\\\{self.code}.wav\\nPriority = -1')

def lines():
    return [CourierLine(*row) for row in RECORDINGS]

def permutation_properties():
    return ''.join(f'permutation_count = {name}, {count}\\n' for name, count in COUNTS.items())

RECORDINGS = ''' + repr(payload) + '\nCOUNTS = ' + repr(counts) + '\n'


def stage(prototype=False, available=False):
    assert shutil.disk_usage(ROOT).free > 2 * 1024**3
    rows = plan()
    records = json.loads((OUT / 'recordings.json').read_text(encoding='utf-8'))
    for row in rows:
        record = records[row['id']]
        assert record['text'] == row['text'] and record['sha256'] == sha(OUT / row['bank'] / (row['id'] + '.wav'))
    verification = json.loads((OUT / 'verification.json').read_text(encoding='utf-8'))
    assert verification['recordings_sha256'] == sha(OUT / 'recordings.json')
    assert not (prototype and available)
    assert prototype or available or not verification['unresolved'], 'Review takes or stage explicitly as a prototype'
    missing_cargo = []
    sources = {}
    for row in rows:
        name = row['id'] + '.wav'
        canonical = (ASSETS/'AUDIO_CUTSCENE_RU/rm0001'/name if row['bank']=='bar'
                     else ASSETS/'PILOTS/dispatcher01/default'/name)
        if available and row['bank']=='vocabulary' and row['id'] in verification['unresolved'] and not canonical.is_file():
            missing_cargo.append(row['id'])
            continue
        source = canonical if available and canonical.is_file() else OUT/row['bank']/name
        with wave.open(str(source), 'rb') as wav:
            assert wav.getnchannels()==1 and wav.getsampwidth()==2 and wav.getnframes()>0, source
            records[row['id']] = dict(records[row['id']], sha256=sha(source),
                duration=wav.getnframes()/wav.getframerate(), rate=wav.getframerate())
        sources[row['id']] = source
    rows = [row for row in rows if row['id'] in sources]
    files = {}
    def put(relative, raw):
        if isinstance(raw, str):
            raw = raw.encode('utf-8')
        assert not relative.endswith('.thn') and 'SHIPS/' not in relative.upper()
        write(PACKAGE, data, relative, raw)
        files[relative] = {'before': digest(GAME / relative), 'after': digest(PACKAGE / relative)}

    # Bootstrap the central API before staging any DATA, preserving all other methods.
    api = (PROJECT / 'tools/data_folder.py').read_text(encoding='utf-8')
    if 'def sync_train_courier_ru_audio(' not in api:
        api += '\n' + API
    elif "'AUDIO/dispatcher01.utf'" not in api:
        old = "'AUDIO/RPG/rm0001_sounds.ini'}"
        assert api.count(old)==1
        api = api.replace(old, "'AUDIO/RPG/rm0001_sounds.ini', 'AUDIO/dispatcher01.utf'}")
    target = PACKAGE / (GEN + 'tools/data_folder.py')
    target.parent.mkdir(parents=True, exist_ok=True)
    target.write_text(api, encoding='utf-8')
    DataFolder = data_class()
    data = DataFolder(root=PACKAGE)
    # Retire only this task's omitted drafts from an earlier full prototype.
    for code in missing_cargo:
        expected = sha(OUT/'vocabulary'/(code+'.wav'))
        for prefix in ('Assets/PILOTS/dispatcher01/default/', 'DATA/AUDIO/MOD/dispatcher01/'):
            relative = prefix+code+'.wav'
            if digest(PACKAGE/relative)==expected:
                write(PACKAGE, data, relative, None)
    put(GEN + 'tools/data_folder.py', api)
    put(GEN + 'universe/audio/courier_ru.py', source_module(rows, records))
    profile_cache = PROJECT/'results/voicestudio/profiles.json'
    profiles = json.loads(profile_cache.read_text(encoding='utf-8')) if profile_cache.exists() else {}
    profiles.update(json.loads((OUT/'profiles.json').read_text(encoding='utf-8')))
    put(GEN+'results/voicestudio/profiles.json', json.dumps(profiles, indent=2))
    path = PROJECT / 'universe/audio/dispatcher.py'
    text = path.read_text(encoding='utf-8')
    marker = "class MaleDispatcher(StationDispatcher):\n    STEOS_ID = 294  # lebedev, stalker\n    FOLDER = 'dispatcher01'\n    ATTENUATION = -4\n"
    if 'from universe.audio.courier_ru import lines' not in text:
        assert text.count(marker) == 1
        text = text.replace(marker, marker + '''
    def get_lines(self):
        from universe.audio.courier_ru import lines
        return list({line.get_code(): line for line in [*super().get_lines(), *lines()]}.values())

    def get_dynamic_lines(self):
        from universe.audio.courier_ru import lines
        return list({line.get_code(): line for line in [*super().get_dynamic_lines(), *lines()]}.values())

    def get_mission_props_ini(self):
        from universe.audio.courier_ru import permutation_properties
        return super().get_mission_props_ini().rstrip() + '\\n' + permutation_properties()
''')
    put(GEN + 'universe/audio/dispatcher.py', text)
    for name, record in json.loads((OUT / 'references/manifest.json').read_text(encoding='utf-8')).items():
        relative = 'Assets/VOICE_SOURCE_RU/' + name + '.wav'
        if not (GAME / relative).exists():
            put(relative, Path(record['path']).read_bytes())
        else:
            assert digest(GAME / relative) == record['sha256'], 'Reference changed: ' + name
        put('Assets/VOICE_SOURCE_RU/' + name + '.json', json.dumps(record, ensure_ascii=False, indent=2))
    radio = [row for row in rows if row['bank'] != 'bar']
    for row in rows:
        name = row['id'] + '.wav'
        raw = sources[row['id']].read_bytes()
        if row['bank'] == 'bar':
            put('Assets/AUDIO_CUTSCENE_RU/rm0001/' + name, raw)
            put('DATA/AUDIO/MOD/RPG/rm0001/' + name, raw)
        else:
            put('Assets/PILOTS/dispatcher01/default/' + name, raw)
            put('DATA/AUDIO/MOD/dispatcher01/' + name, raw)
    # Replace only new RU radio IDs; retain every other voice and static bank entry.
    existing = (GAME / 'DATA/AUDIO/voices_space_male.ini').read_text(encoding='utf-8-sig')
    blocks = re.split(r'(?m)(?=^\[)', existing)
    added = '\n'.join(f"[Sound]\nmsg = {r['id']}\nduration = {records[r['id']]['duration']:.6f}\nattenuation = -4\n"
                      f"file = Audio\\MOD\\dispatcher01\\{r['id']}.wav\nPriority = -1\n" for r in radio)
    active = ''
    output = []
    inserted = 0
    ids = {r['id'] for r in radio}
    for block in blocks:
        if block.lower().startswith('[voice]'):
            if active == 'dispatcher01':
                output.append(added + '\n')
                inserted += 1
            active = re.search(r'(?mi)^nickname\s*=\s*([^\r\n]+)', block)[1].strip()
        if active == 'dispatcher01' and block.lower().startswith('[sound]'):
            code = re.search(r'(?mi)^msg\s*=\s*([^\r\n]+)', block)[1].strip()
            if code in ids:
                continue
        output.append(block)
    if active == 'dispatcher01':
        output.append(added + '\n')
        inserted += 1
    assert inserted == 1
    put('DATA/AUDIO/voices_space_male.ini', ''.join(output))
    counts = {k: len(v[1]) for k, v in FAMILIES.items()}
    counts.update({r['id'].rsplit('_', 1)[0]: 5 for r in rows if r['bank'] == 'evacuation'})
    props = (GAME / 'DATA/MISSIONS/voice_properties.ini').read_text(encoding='utf-8-sig')
    blocks = re.split(r'(?m)(?=^\[)', props)
    matched = 0
    for i, block in enumerate(blocks):
        if block.lower().startswith('[mvoiceprop]') and re.search(r'(?m)^voice\s*=\s*dispatcher01\s*$', block):
            for family in counts:
                block = re.sub(r'(?mi)^permutation_count\s*=\s*' + family + r'\s*,[^\n]*\n?', '', block)
            blocks[i] = block.rstrip() + '\n' + ''.join(f'permutation_count = {k}, {v}\n' for k, v in counts.items()) + '\n'
            matched += 1
    assert matched == 1
    put('DATA/MISSIONS/voice_properties.ini', ''.join(blocks))
    config = (GAME / 'DATA/MISSIONS/TrainCourier/courier.ini').read_text(encoding='utf-8-sig')
    config = config.replace('; English radio: 13 active families;', '; RU/EN radio: 13 active evacuation families;')
    for key, value in [('voice_ru', 'dispatcher01'), ('voice_en', 'atc_leg_m01_new'), ('composed_audio', 'true')]:
        if re.search(r'(?m)^' + key + r'\s*=', config):
            config = re.sub(r'(?m)^' + key + r'\s*=.*$', key + ' = ' + value, config)
        else:
            config = config.replace('[Presentation]\n', '[Presentation]\n' + key + ' = ' + value + '\n')
    config = re.sub(r'(?mi)^unvoiced_cargo\s*=\s*dispatcher01\s*,[^\n]*\n?', '', config)
    config = config.replace('[Presentation]\n', '[Presentation]\n' + ''.join(
        f'unvoiced_cargo = dispatcher01, {code}\n' for code in missing_cargo))
    put('DATA/MISSIONS/TrainCourier/courier.ini', config)
    # Shared RPG sound registry keeps its verified EN entries and adds RU only.
    sys.path.insert(0, str(PROJECT))
    from files.rpg_audio import sound_bank, audio_manifest, register_bank
    old = json.loads((GAME / 'DATA/AUDIO/RPG/rm0001.json').read_text(encoding='utf-8'))
    languages = old['languages']
    for lang, entries in languages.items():
        if lang != 'ru':
            for row in entries:
                assert digest(GAME / 'DATA' / row['file']) == row['sha256']
    languages['ru'] = [dict(fragment=r['id'].split('_l001_')[0], file='AUDIO/MOD/RPG/rm0001/'+r['id']+'.wav',
        nickname='DX_'+r['id']+'_ru', sha256=records[r['id']]['sha256'], duration_seconds=records[r['id']]['duration'],
        sample_rate=records[r['id']]['rate'], channels=1) for r in rows if r['bank'] == 'bar']
    put('DATA/AUDIO/RPG/rm0001.json', audio_manifest('rm0001', languages))
    put('DATA/AUDIO/RPG/rm0001_sounds.ini', sound_bank(languages))
    for name in ('freelancer.ini', 'freelan_en_port.ini'):
        raw = (GAME / 'bin' / name).read_bytes()
        modified = register_bank(raw, 'rm0001')
        if modified != raw:
            put('bin/' + name, modified)
    for name in BINARIES:
        put('bin/' + name, (BIN / name).read_bytes())
    SOURCES.update({n: GAME/'bin'/n for n in ('Common.dll', 'Server.dll')})
    SOURCES.update({n: BIN/n for n in BINARIES if n.endswith(('.dll', '.exe'))})
    verify_imports()
    for name in files:
        if name.endswith('.py'):
            ast.parse((PACKAGE/name).read_text(encoding='utf-8'))
    dependencies = {str(p.relative_to(GAME)): digest(p) for p in (GAME/'bin').glob('*.dll')
                    if p.name not in BINARIES}
    dependencies['DATA/MISSIONS/TrainCourier/catalog.ini'] = digest(GAME/'DATA/MISSIONS/TrainCourier/catalog.ini')
    cleanup = {}
    suffixes = {'.obj','.pch','.pdb','.dll','.exe','.lib','.exp','.res','.ilk','.idb','.iobj','.ipdb','.tlog','.lastbuildstate'}
    for folder in (BIN.parent/'Content', BIN.parent/'freelancer', OUT/'imports', OUT/'checks'):
        for current, dirs, names in os.walk(folder, followlinks=False):
            for directory in dirs:
                safe_file(Path(current)/directory, ROOT)
            for name in names:
                path = safe_file(Path(current)/name, ROOT)
                if path.suffix.lower() in suffixes:
                    cleanup[str(path.relative_to(ROOT))] = digest(path)
    for name in (*BINARIES, 'Content.lib', 'Content.exp', 'freelancer.lib', 'freelancer.exp', 'Common.lib'):
        if (BIN/name).exists():
            cleanup[str((BIN/name).relative_to(ROOT))] = digest(BIN/name)
    report = dict(files=files, dependencies=dependencies, cleanup=cleanup, lines=len(rows), radio=len(radio), bar=32,
                  game_launched=False, thn_built=False, verification_sha256=sha(OUT/'verification.json'),
                  prototype=prototype, available=available, missing_cargo=missing_cargo,
                  recordings={r['id']: records[r['id']] for r in rows}, voice_backend='loose_wav',
                  needs_manual_review=verification['unresolved'])
    save(MANIFEST, report)
    print('Staged', len(files), 'files;', len(rows), 'RU recordings. No live writes or THNs.')


def apply():
    idle()
    assert not (GAME/'DATA/AUDIO/dispatcher01.utf').exists(), 'First run Pythonlancer single.py compile_dispatchers_audio; the user compiles game INIs'
    report = json.loads(MANIFEST.read_text(encoding='utf-8'))
    assert not report.get('prototype'), 'Prototype is for authoring/review; do not install it into the game'
    for name, record in report['files'].items():
        assert digest(GAME/name) == record['before'], 'Changed since staging: '+name
        assert digest(PACKAGE/name) == record['after'], 'Package changed: '+name
    for name, expected in report['dependencies'].items():
        assert digest(GAME/name) == expected, 'Dependency changed: '+name
    DataFolder = data_class()
    data = DataFolder(root=GAME)
    rollback = OUT/'rollback'
    backup_data = DataFolder(root=rollback)
    applied = []
    backup_files = {}
    try:
        for name, record in report['files'].items():
            if record['before'] == record['after']:
                continue
            old = (GAME/name).read_bytes() if record['before'] else None
            if old is not None:
                write(rollback, backup_data, name, old)
                backup_files[name] = record['before']
            # Track before writing so a partially failed write is also restored.
            applied.append(name)
            write(GAME, data, name, (PACKAGE/name).read_bytes())
        for name, record in report['files'].items():
            assert digest(GAME/name) == record['after'], 'Install verification failed: '+name
    except Exception:
        for name in reversed(applied):
            old = (rollback/name).read_bytes() if report['files'][name]['before'] else None
            write(GAME, data, name, old)
        raise
    report['installed'] = True
    save(OUT/'installed.json', report)
    # Remove only exact task-owned copies after installation has verified.
    for name, expected in backup_files.items():
        target = safe_file(rollback/name, rollback)
        assert digest(target) == expected
        write(rollback, backup_data, name, None)
    stage_data = DataFolder(root=PACKAGE)
    for name, record in report['files'].items():
        if Path(name).suffix.lower() in ('.wav','.dll','.exe','.pdb','.utf'):
            assert digest(PACKAGE/name) == record['after']
            write(PACKAGE, stage_data, name, None)
    for relative, expected in report['cleanup'].items():
        path = safe_file(ROOT/relative, ROOT)
        if path.exists() and digest(path) == expected:
            path.unlink()
    print('Installed and verified', report['lines'], 'RU recordings. Build/package binary copies cleaned.')


def publish_sources():
    """Publish authoring inputs while the user works; never touch live DATA/bin."""
    report=json.loads(MANIFEST.read_text(encoding='utf-8'))
    disputed=set(report.get('needs_manual_review',[]))
    chosen={name:entry for name,entry in report['files'].items() if name.startswith('Assets/')
            and not (name.endswith('.wav') and Path(name).stem in disputed)}
    for name,entry in chosen.items():
        assert digest(GAME/name) in (entry['before'],entry['after']), 'Source changed since staging: '+name
        assert digest(PACKAGE/name)==entry['after']
        safe_file(GAME/name,GAME)
    backups={}
    try:
        for name,entry in chosen.items():
            target=GAME/name
            if digest(target)==entry['after']:continue
            backups[name]=target.read_bytes() if target.exists() else None
            target.parent.mkdir(parents=True,exist_ok=True)
            target.write_bytes((PACKAGE/name).read_bytes())
        for name,entry in chosen.items():
            assert digest(GAME/name)==entry['after'],name
    except Exception:
        for name,raw in backups.items():
            target=safe_file(GAME/name,GAME)
            if raw is None:target.unlink(missing_ok=True)
            else:target.write_bytes(raw)
        raise
    save(OUT/'sources_published.json',dict(files=chosen,needs_manual_review=sorted(disputed),
         live_data_changed=False,live_bin_changed=False,thn_built=False))
    print('Published',len(chosen),'authoring files; disputed takes stay offline:',len(disputed),
          '; live DATA/bin untouched.')


if __name__ == '__main__':
    sys.stdout.reconfigure(encoding='utf-8')
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument('action', choices=('stage', 'apply', 'publish-sources'))
    parser.add_argument('--prototype',action='store_true',help='Stage drafts with an explicit manual-review list; game installation disabled')
    parser.add_argument('--available',action='store_true',help='Use canonical sources; omit unavailable cargo names with a voice-specific fallback')
    args = parser.parse_args()
    if args.action=='stage':stage(args.prototype, args.available)
    elif args.action=='publish-sources':publish_sources()
    else:apply()
