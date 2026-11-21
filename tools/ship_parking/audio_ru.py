"""Russian commandant recordings from mc_leg_m01; offline preparation first."""
import argparse
import ast
import copy
import difflib
import importlib.util
import hashlib
import io
import json
from pathlib import Path
import re
import shutil
import stat
import sys
import time

ROOT = Path(__file__).resolve().parents[2]
sys.path.insert(0, str(ROOT / 'tools/train_courier'))
from generate_courier_ru import ASSETS, save, sha, transcribe
from generate_evacuation_audio import Recorder, inspect
from check_courier_ru import words
from pydub import AudioSegment
from story.rpg.script import RpgScript

PROJECT = ASSETS / 'Pythonlancer'
OUT = ROOT / 'out/ship_parking/audio_ru'
REFERENCE_CODES = ('rmb_success_ships_01-', 'rmb_flytosystem_01-')


def read(path):
    return json.loads(path.read_text(encoding='utf-8'))


def reference():
    folder = OUT / 'reference'
    folder.mkdir(parents=True, exist_ok=True)
    combined = AudioSegment.empty()
    sources = []
    for code in REFERENCE_CODES:
        path = ASSETS / 'PILOTS/mc_leg_m01/default' / (code + '.mp3')
        sound = AudioSegment.from_file(path).set_channels(1).set_frame_rate(24000).set_sample_width(2)
        sound = sound.apply_gain(min(-18 - sound.dBFS, -1 - sound.max_dBFS))
        decoded = folder / (code + '.wav')
        sound.export(decoded, format='wav')
        heard = transcribe(decoded)
        print(code, len(sound)/1000, heard['text'], flush=True)
        if len(combined):
            combined += AudioSegment.silent(duration=150, frame_rate=24000)
        combined += sound
        sources.append({'path': str(path), 'sha256': sha(path), 'text': heard['text'], 'asr': heard})
    target = folder / 'RpgAvalonParkingOfficer.wav'
    combined.export(target, format='wav')
    report = {'path': str(target), 'sha256': sha(target), 'sources': sources,
              'text': ' '.join(r['text'].strip() for r in sources), **inspect(target)}
    assert 5 < report['duration'] < 20
    save(folder / 'RpgAvalonParkingOfficer.json', report)
    print('Prepared clean RU mc_leg_m01 reference:', round(report['duration'], 2), 'seconds', flush=True)


def prepare():
    OUT.mkdir(parents=True, exist_ok=True)
    spec = importlib.util.spec_from_file_location('commandant_ru_source', Path(__file__).with_name('commandants.py'))
    module = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(module)
    registry_path = PROJECT / 'story/rpg/parking_commandants.json'
    registry = read(registry_path)
    officer_ref = read(OUT / 'reference/RpgAvalonParkingOfficer.json')
    trent_ref = read(ASSETS / 'VOICE_SOURCE_RU/Trent.json')
    trent_ref['path'] = str(ASSETS / 'VOICE_SOURCE_RU/Trent.wav')
    assert sha(Path(trent_ref['path'])) == trent_ref['sha256']
    refs = {'vendor': officer_ref, 'player': trent_ref}
    plans, unique, before = {}, {}, {}
    for entry in registry['bases']:
        path = PROJECT / 'story/rpg' / (entry['group'] + '.json')
        before[str(path)] = sha(path)
        data = read(path)
        original = copy.deepcopy(data)
        if entry.get('surname'):
            ru_name = entry.get('surname_ru') or module.RU_SURNAMES[entry['surname']]
            for row in data['fragments']:
                row['ru'] = row['ru'].replace(entry['surname'], ru_name)
                if row['id'].endswith('_frag0021'):
                    row['ru'] = 'Привет, Трент. Стоянка к твоим услугам.'
        script = RpgScript(data)
        fragments = []
        for row, old in zip(data['fragments'], original['fragments']):
            assert {k: v for k, v in row.items() if k != 'ru'} == {k: v for k, v in old.items() if k != 'ru'}
            ref = refs[row['role']]
            form = dict(engine='omnivoice', language='ru', text=row['ru'], ref_text=ref['text'],
                        seed='42', speed='1.0', denoise='false', postprocess_output='false',
                        pronounce='false', num_step='128')
            if row['role'] == 'vendor':
                form['guidance_scale'] = '3.0'
            key = hashlib.sha256(json.dumps([form, ref['sha256']], sort_keys=True).encode()).hexdigest()
            unique.setdefault(key, {'role': row['role'], 'text': row['ru'], 'request': form,
                                    'reference': ref, 'uses': [], 'names': []})['uses'].append(row['id'])
            names = [re.sub(r'^(База|Планета|Станция|Линкор)\s+', '', entry['name_ru'])]
            if entry.get('surname'):
                names.append(entry.get('surname_ru') or module.RU_SURNAMES[entry['surname']])
            for name in names:
                if name not in unique[key]['names']:
                    unique[key]['names'].append(name)
            fragments.append({'id': row['id'], 'name': script.line_name(row), 'key': key, 'role': row['role']})
        plans[script.name] = {'data': data, 'fragments': fragments}
    save(OUT / 'plan.json', {'groups': plans, 'unique': unique})
    baseline = OUT / 'source_before.json'
    if not baseline.exists():
        save(baseline, {'sources': before, 'registry_sha256': sha(registry_path),
                       'manager_sha256': sha(PROJECT / 'managers/parking_commandants.py')})
    else:
        assert read(baseline)['sources'] == before, 'Scenarios changed since preparation'
    print('Prepared', len(plans), 'commandants;', sum(len(p['fragments']) for p in plans.values()),
          'fragments;', len(unique), 'unique recordings', flush=True)


def changes(row, heard):
    expected, actual = words(row['text']), words(heard)
    # Written variants that ASR cannot reliably distinguish in spoken Russian:
    # final з is devoiced in Кадиз; дс contracts to ц in Лидс; Bennett spelling.
    spellings = {'кадиз': ('кадис',), 'лидс': ('лиц', 'литц'), 'беннет': ('беннетт',)}
    for canonical, variants in spellings.items():
        if canonical in expected:
            actual = [canonical if word in variants else word for word in actual]
    return [word for word in difflib.ndiff(expected, actual) if not word.startswith('  ')]


def names_only(row, heard):
    """Queue uncertain proper names for review instead of rerolling identical spelling ambiguities."""
    expected, actual = words(row['text']), words(heard)
    covered = set()
    for name in row.get('names', []):
        sequence = words(name)
        for start in range(len(expected)-len(sequence)+1):
            if expected[start:start+len(sequence)] == sequence:
                covered.update(range(start, start+len(sequence)))
    mismatches = [op for op in difflib.SequenceMatcher(None, expected, actual).get_opcodes() if op[0] != 'equal']
    return bool(mismatches) and all(a < b and set(range(a, b)) <= covered for _, a, b, _, _ in mismatches)


def transcribe_names(path, names):
    sound = AudioSegment.from_wav(path)
    silence = AudioSegment.silent(duration=500, frame_rate=sound.frame_rate)
    stream = io.BytesIO()
    (silence + sound + silence).export(stream, format='wav')
    stream.seek(0)
    with Recorder._client() as client:
        response = client.post('/v1/audio/transcriptions',
            data={'language': 'ru', 'model': 'whisper-1', 'response_format': 'verbose_json',
                  'prompt': ', '.join(names) + '.'},
            files={'file': ('names.wav', stream, 'audio/wav')})
    response.raise_for_status()
    return response.json()


def review_names():
    """Second ASR pass with a names-only lexicon; retain the original unguided transcript."""
    plan, records = read(OUT / 'plan.json'), read(OUT / 'recordings.json')
    target = OUT / 'name_recognition.json'
    reviews = read(target) if target.exists() else {}
    for key in plan['unique'].keys() & records.keys():
        row, record = plan['unique'][key], records[key]
        if not changes(row, record['asr']['text']) or not names_only(row, record['asr']['text']):
            continue
        if reviews.get(key, {}).get('sha256') == record['sha256']:
            continue
        names = [name for name in row['names'] if name in row['text']]
        heard = transcribe_names(OUT / 'recordings' / (key + '.wav'), names)
        reviews[key] = {'sha256': record['sha256'], 'lexicon': names, 'asr': heard,
                        'differences': changes(row, heard.get('text', ''))}
        save(target, reviews)
        print('Name lexicon:', row['uses'][0], heard.get('text'), flush=True)


def repair_names():
    plan, records = check()
    report = read(OUT / 'verification.json')
    named_path = OUT / 'name_recognition.json'
    named = read(named_path) if named_path.exists() else {}
    stress = {'Очо-Риос': 'О́чо-Ри́ос', 'Хоторн': 'Хо́торн', 'Хаяси': 'Хая́си', 'Абэ': 'А́бэ'}
    repairs_path = OUT / 'pronunciation_repairs.json'
    repairs = read(repairs_path) if repairs_path.exists() else {}
    for key in report['differences']:
        row = plan['unique'][key]
        if not any(name in row['text'] for name in stress):
            continue
        folder = OUT / 'pronunciation' / key
        folder.mkdir(parents=True, exist_ok=True)
        form = dict(row['request'])
        for name, accented in stress.items():
            form['text'] = form['text'].replace(name, accented)
        assert form['text'].replace('\u0301', '') == row['text']
        names = [name for name in row['names'] if name in row['text']]
        ref = row['reference']
        for seed in (42, 43):
            form['seed'] = str(seed)
            if any(take['request'] == form for take in repairs.get(key, [])):
                continue
            print('Pronunciation take:', row['uses'][0], form['text'], flush=True)
            started = time.time()
            with Recorder._client() as client, Path(ref['path']).open('rb') as stream:
                response = client.post('/generate', data=form, files={'ref_audio': ('reference.wav', stream, 'audio/wav')})
            response.raise_for_status()
            assert not int(response.headers.get('X-OmniVoice-Dropped-Chunks', '0'))
            sound = AudioSegment.from_file(io.BytesIO(response.content), format='wav').set_channels(1).set_sample_width(2)
            if sound.max_dBFS > -.5:
                sound = sound.apply_gain(-.5-sound.max_dBFS)
            target = folder / f'seed{seed}.wav'
            sound.export(target, format='wav')
            info = inspect(target)
            heard = transcribe(target)
            lexical = transcribe_names(target, names)
            clean = not changes(row, heard['text']) or (names_only(row, heard['text']) and not changes(row, lexical['text']))
            candidate = {'sha256': sha(target), 'request': dict(form), 'asr': heard, 'asr_names': lexical,
                         'accepted': clean, 'generation_seconds': time.time()-started, **info}
            repairs.setdefault(key, []).append(candidate)
            save(repairs_path, repairs)
            print('Pronunciation ASR:', lexical['text'], 'accepted:', clean, flush=True)
            if not clean:
                continue
            old = OUT / 'recordings' / (key + '.wav')
            shutil.copyfile(old, folder / 'original_take.wav')
            shutil.copyfile(target, old)
            records[key] = {**candidate, 'text': row['text'], 'role': row['role'],
                            'reference_sha256': ref['sha256'], 'method': 'explicit_stress_v1',
                            'differences': changes(row, heard['text'])}
            save(OUT / 'recordings.json', records)
            named[key] = {'sha256': sha(target), 'lexicon': names, 'asr': lexical,
                          'differences': changes(row, lexical['text'])}
            save(named_path, named)
            break


def generate(preview=False):
    assert shutil.disk_usage(OUT).free > 2 * 1024**3
    plan = read(OUT / 'plan.json')
    ledger = OUT / 'recordings.json'
    records = read(ledger) if ledger.exists() else {}
    unique = plan['unique']
    if preview:
        selected = {'rm0002_frag0001', 'rm0002_frag0003', 'rm0002_frag0014'}
        unique = {k: v for k, v in unique.items() if selected.intersection(v['uses'])}
    audio = OUT / 'recordings'
    audio.mkdir(exist_ok=True)
    for index, (key, row) in enumerate(unique.items(), 1):
        target = audio / (key + '.wav')
        old = records.get(key)
        if old and target.exists() and sha(target) == old['sha256']:
            continue
        ref = row['reference']
        assert sha(Path(ref['path'])) == ref['sha256']
        form = dict(row['request'])
        start = time.time()
        for attempt in range(3):
            form['seed'] = str(42 + attempt)
            print(f'[{index}/{len(unique)}] {row["uses"][0]}: {row["text"]}', flush=True)
            with Recorder._client() as client, Path(ref['path']).open('rb') as stream:
                response = client.post('/generate', data=form, files={'ref_audio': ('reference.wav', stream, 'audio/wav')})
            response.raise_for_status()
            if int(response.headers.get('X-OmniVoice-Dropped-Chunks', '0')):
                if attempt == 2:
                    raise RuntimeError('Dropped TTS chunks: ' + key)
                continue
            sound = AudioSegment.from_file(io.BytesIO(response.content), format='wav').set_channels(1).set_sample_width(2)
            if sound.max_dBFS > -.5:
                sound = sound.apply_gain(-.5 - sound.max_dBFS)
            sound.export(target, format='wav')
            info = inspect(target)
            assert .25 < info['duration'] < max(10, len(row['text'].split()) * 1.25)
            heard = transcribe(target)
            delta = changes(row, heard.get('text', ''))
            if not delta or names_only(row, heard.get('text', '')):
                break
            print('ASR difference:', delta, flush=True)
        records[key] = {'text': row['text'], 'role': row['role'], 'sha256': sha(target), 'request': dict(form),
                        'reference_sha256': ref['sha256'], 'asr': heard, 'differences': delta,
                        'generation_seconds': time.time()-start, **info}
        save(ledger, records)
        print('Ready unique recordings:', len(records.keys() & plan['unique'].keys()), '/', len(plan['unique']), flush=True)
    if preview:
        combined = AudioSegment.empty()
        for key in unique:
            if len(combined):
                combined += AudioSegment.silent(duration=700, frame_rate=24000)
            combined += AudioSegment.from_wav(audio / (key + '.wav'))
        combined.export(OUT / 'preview_commandant.wav', format='wav')
    print('Recorded unique lines:', len(records.keys() & plan['unique'].keys()), flush=True)


def stage_sources():
    """Prepare Python/JSON and dialogue INIs; never render or publish THNs."""
    from files.rpg_runtime import dialog_ini
    from tools.data_folder import DataFolder
    plan = read(OUT / 'plan.json')
    before = read(OUT / 'source_before.json')
    staged = OUT / 'source'
    files = {}
    for group, item in plan['groups'].items():
        relative = 'Pythonlancer/story/rpg/' + group + '.json'
        path = ASSETS / relative
        assert sha(path) == before['sources'][str(path)], 'Scenario edited: ' + group
        files[relative] = (json.dumps(item['data'], ensure_ascii=False, indent=2) + '\n').encode('utf-8')
    # Patch only the RU surname rendering in the installed generator.
    manager_path = PROJECT / 'managers/parking_commandants.py'
    assert sha(manager_path) == before['manager_sha256']
    manager = manager_path.read_text(encoding='utf-8')
    authored = Path(__file__).with_name('commandants.py').read_text(encoding='utf-8')
    mapping = next(n for n in ast.parse(authored).body if isinstance(n, ast.Assign)
                   and any(isinstance(t, ast.Name) and t.id == 'RU_SURNAMES' for t in n.targets))
    mapping_text = '\n'.join(authored.splitlines()[mapping.lineno-1:mapping.end_lineno])
    assert 'RU_SURNAMES' not in manager, 'Review already modified generator'
    manager = manager.replace('\ndef parse(content):', '\n' + mapping_text + '\n\n\ndef parse(content):', 1)
    anchor = "    name, ru, officer = entry['name_en'], entry['name_ru'], entry['surname']"
    assert manager.count(anchor) == 1
    manager = manager.replace(anchor, anchor + "\n    officer_ru = entry.get('surname_ru') or RU_SURNAMES[officer]", 1)
    for old, new in [('стоянки {officer}', 'стоянки {officer_ru}'), ('Комендант {officer}', 'Комендант {officer_ru}')]:
        assert manager.count(old) == 1
        manager = manager.replace(old, new, 1)
    old = "f'Привет, Трент. Стоянка базы «{ru}» к твоим услугам.'"
    assert manager.count(old) == 1
    manager = manager.replace(old, "'Привет, Трент. Стоянка к твоим услугам.'", 1)
    files['Pythonlancer/managers/parking_commandants.py'] = manager.encode('utf-8')
    # Existing single.py rpg entry point, with an explicit all-parking selector.
    cli_path = PROJECT / 'tools/rpg_voices.py'
    cli = cli_path.read_text(encoding='utf-8')
    local_cli = (ROOT / 'tools/rpg_cutscenes/pythonlancer/tools/rpg_voices.py').read_text(encoding='utf-8')
    batch = local_cli.split('    if args.all_parking:\n', 1)[1].split('    output = args.output', 1)[0]
    assert '--all-parking' not in cli
    cli = cli.replace('import argparse\n', 'import argparse\nimport json\n', 1)
    anchor = '    parser.add_argument("--group", default="rm0001")'
    assert cli.count(anchor) == 1
    cli = cli.replace(anchor, anchor + '\n    parser.add_argument("--all-parking", action="store_true", help="Process every registered parking commandant")', 1)
    anchor = '    root = Path(__file__).resolve().parents[1]\n'
    assert cli.count(anchor) == 1
    cli = cli.replace(anchor, anchor + '    if args.all_parking:\n' + batch, 1)
    files['Pythonlancer/tools/rpg_voices.py'] = cli.encode('utf-8')
    info = {}
    for relative, raw in files.items():
        path = staged / relative
        if relative.endswith('.py'):
            compile(raw, relative, 'exec')
        path.parent.mkdir(parents=True, exist_ok=True)
        path.write_bytes(raw)
        info[relative] = {'before': sha(ASSETS / relative), 'after': sha(path)}
    # Shared graph controls transactions. Only RU display text is changed.
    folder = DataFolder(root=OUT / 'stage')
    graphs = {}
    def structural_lines(raw):
        return [s.strip() for s in raw.decode('utf-8-sig').splitlines()
                if s.strip() and not s.strip().startswith('text_ru =')]
    for group, item in plan['groups'].items():
        script = RpgScript(item['data'])
        text = dialog_ini(script)
        if script.data.get('local_scene'):
            text = text.replace('scene_group = ' + group + '\n', 'scene_group = ' + group + '\nlocal_scene = 1\n', 1)
        relative = 'RPG/' + group + '_dialog.ini'
        current = ASSETS.parent / 'DATA' / relative
        raw = text.encode('utf-8')
        assert structural_lines(raw) == structural_lines(current.read_bytes()), 'Graph changed beyond RU captions: ' + group
        folder.sync_data_file(relative, raw)
        graphs[relative] = {'before': sha(current), 'after': hashlib.sha256(raw).hexdigest()}
    save(OUT / 'staged_sources.json', {'files': info, 'graphs': graphs,
                                     'scene_command': 'single.py rpg scenes --all-parking --language ru'})
    print('Staged', len(files), 'source files and', len(graphs), 'RU dialogue graphs; no THNs built.', flush=True)


def check(complete=False):
    plan, records = read(OUT / 'plan.json'), read(OUT / 'recordings.json')
    missing = sorted(plan['unique'].keys() - records.keys())
    differences = {}
    named = read(OUT / 'name_recognition.json') if (OUT / 'name_recognition.json').exists() else {}
    resolved = []
    for key in plan['unique'].keys() & records.keys():
        expected, actual = plan['unique'][key], records[key]
        target = OUT / 'recordings' / (key + '.wav')
        assert sha(target) == actual['sha256'], key
        info = inspect(target)
        assert abs(info['duration'] - actual['duration']) < 1e-6
        assert expected['text'] == actual['text'] and expected['role'] == actual['role']
        assert actual['reference_sha256'] == expected['reference']['sha256']
        assert actual['request']['text'].replace('\u0301', '') == expected['text']
        assert all(actual['request'][k] == v for k, v in expected['request'].items() if k not in ('seed', 'text'))
        delta = changes(expected, actual['asr'].get('text', ''))
        spelling = named.get(key, {})
        if (delta and names_only(expected, actual['asr'].get('text', ''))
                and spelling.get('sha256') == actual['sha256']
                and not changes(expected, spelling['asr'].get('text', ''))):
            resolved.append(key)
            delta = []
        if delta:
            differences[key] = {'sha256': actual['sha256'], 'text': expected['text'],
                                'asr': actual['asr']['text'], 'changes': delta, 'uses': expected['uses']}
    report = {'groups': len(plan['groups']), 'unique': len(plan['unique']), 'missing': missing,
              'recorded': len(plan['unique']) - len(missing), 'differences': differences,
              'names_resolved_with_lexicon': resolved}
    save(OUT / 'verification.json', report)
    if complete:
        assert not missing, 'Record the complete set before publication'
        reviews = read(OUT / 'asr_reviews.json') if (OUT / 'asr_reviews.json').exists() else {}
        for key, row in differences.items():
            assert reviews.get(key, {}).get('sha256') == row['sha256'] and reviews[key].get('reason'), 'Unreviewed ASR: ' + row['uses'][0]
    print('Checked', report['recorded'], '/', report['unique'], 'unique recordings;', len(differences), 'ASR differences', flush=True)
    return plan, records


def publish():
    """Publish canonical Assets sources only. DATA audio has its own transaction."""
    plan, records = check(complete=True)
    baseline = read(OUT / 'source_before.json')
    assert sha(PROJECT / 'story/rpg/parking_commandants.json') == baseline['registry_sha256'], 'Parking registry edited'
    staged = read(OUT / 'staged_sources.json')
    if (OUT / 'published.json').exists():
        published = read(OUT / 'published.json')
        for relative, digest in published['files'].items():
            assert sha(ASSETS / relative) == digest, 'Published source changed: ' + relative
        print('Canonical sources already published and verified', flush=True)
        return
    files = {}
    for relative, row in staged['files'].items():
        assert sha(ASSETS / relative) == row['before'], 'Source edited: ' + relative
        target = OUT / 'source' / relative
        assert sha(target) == row['after']
        files[relative] = target.read_bytes()
    for group, item in plan['groups'].items():
        for fragment in item['fragments']:
            files['AUDIO_CUTSCENE_RU/' + group + '/' + fragment['name'] + '.wav'] = (
                OUT / 'recordings' / (fragment['key'] + '.wav')).read_bytes()
    ref = read(OUT / 'reference/RpgAvalonParkingOfficer.json')
    ref['path'] = str(ASSETS / 'VOICE_SOURCE_RU/RpgAvalonParkingOfficer.wav')
    ref['approved_generation'] = {k: v for k, v in next(row['request'] for row in plan['unique'].values() if row['role'] == 'vendor').items()
                                  if k not in ('text', 'ref_text', 'seed')}
    files['VOICE_SOURCE_RU/RpgAvalonParkingOfficer.wav'] = (OUT / 'reference/RpgAvalonParkingOfficer.wav').read_bytes()
    files['VOICE_SOURCE_RU/RpgAvalonParkingOfficer.json'] = json.dumps(ref, ensure_ascii=False, indent=2).encode('utf-8')
    before = {}
    required_space = sum(len(raw) for raw in files.values()) + 512 * 1024**2
    assert shutil.disk_usage(ASSETS).free > required_space, 'Insufficient space for canonical audio publication'
    for relative, raw in files.items():
        target = (ASSETS / relative).resolve()
        assert target.is_relative_to(ASSETS.resolve()) and 'DATA' not in target.relative_to(ASSETS.resolve()).parts
        before[relative] = target.read_bytes() if target.exists() else None
        if relative not in staged['files']:
            assert before[relative] is None or before[relative] == raw, 'User recording already exists: ' + relative
    previous = OUT / 'source_previous'
    for relative, raw in before.items():
        if raw is not None and raw != files[relative]:
            backup = previous / relative
            backup.parent.mkdir(parents=True, exist_ok=True)
            backup.write_bytes(raw)
    changed = []
    try:
        for relative, raw in files.items():
            if before[relative] == raw:
                continue
            target = ASSETS / relative
            assert (target.read_bytes() if target.exists() else None) == before[relative], 'Concurrent source edit: ' + relative
            changed.append(relative)
            target.parent.mkdir(parents=True, exist_ok=True)
            temporary = target.with_suffix(target.suffix + '.parking-ru.tmp')
            temporary.write_bytes(raw)
            temporary.replace(target)
            assert target.read_bytes() == raw
    except BaseException:
        for relative in reversed(changed):
            target = ASSETS / relative
            if before[relative] is None:
                target.unlink(missing_ok=True)
            else:
                target.write_bytes(before[relative])
        raise
    save(OUT / 'published.json', {'files': {p: hashlib.sha256(raw).hexdigest() for p, raw in files.items()},
                                  'groups': len(plan['groups']), 'reference_sha256': ref['sha256'],
                                  'pronunciation_prototypes': [k for k, v in read(OUT / 'asr_reviews.json').items() if v.get('needs_listening')],
                                  'built_thn': False})
    print('Published canonical RU WAVs, mc_leg voice reference, scenarios and batch compiler selector. No DATA/THN writes.', flush=True)


def cleanup_backup(path):
    """Remove this verified transaction's DATA backups through DataFolder only."""
    from tools.data_folder import DataFolder
    path = Path(path)
    assert path.resolve().is_relative_to((OUT / 'install').resolve())
    for parent in (path, *path.parents):
        if parent.exists():
            assert not (getattr(parent.lstat(), 'st_file_attributes', 0) & stat.FILE_ATTRIBUTE_REPARSE_POINT), parent
    transaction = read(path / 'transaction.json')
    backup = DataFolder(root=path)
    for relative, existed in transaction['data_files'].items():
        if existed:
            target = path / 'DATA' / relative
            assert target.resolve().is_relative_to(path.resolve())
            for parent in (target, *target.parents):
                if parent.exists():
                    assert not (getattr(parent.lstat(), 'st_file_attributes', 0) & stat.FILE_ATTRIBUTE_REPARSE_POINT), parent
            backup.remove_data_file(relative)
    # Existing English banks already register these groups, so no bin change is expected.
    assert not transaction['bin_files'], 'Review unexpected startup configuration change'


def install_audio():
    from managers.rpg_audio import RpgAudioManager
    from tools.data_folder import DataFolder
    plan, records = check(complete=True)
    published = read(OUT / 'published.json')
    assert shutil.disk_usage(ASSETS.parent).free > 2 * 1024**3, 'Insufficient space for audio installation'
    for relative, digest in published['files'].items():
        assert sha(ASSETS / relative) == digest, 'Canonical source changed: ' + relative
    folder = DataFolder(root=ASSETS.parent)
    baseline_path = OUT / 'data_before.json'
    if not baseline_path.exists():
        save(baseline_path, {'english': {group: read(folder.data_path('AUDIO/RPG/' + group + '.json'))['languages']['en']
                                        for group in plan['groups']}})
    baseline = read(baseline_path)
    installed = read(OUT / 'installed.json') if (OUT / 'installed.json').exists() else {'groups': {}}
    for index, (group, item) in enumerate(plan['groups'].items(), 1):
        manager = RpgAudioManager(PROJECT, RpgScript(item['data']))
        files, configs, metadata = manager.plan(('ru',))
        assert metadata['en'] == baseline['english'][group], 'English bank changed: ' + group
        assert all(folder.rpg_bin_path(name).read_bytes() == raw for name, raw in configs.items()), 'Unexpected new startup registration'
        report = manager.install(('ru',), OUT / 'install' / group)
        for relative, raw in files.items():
            assert folder.data_path(relative).read_bytes() == raw, relative
        installed['groups'][group] = {'recordings': len(metadata['ru']),
            'files': {p: hashlib.sha256(raw).hexdigest() for p, raw in files.items()}, 'english_preserved': True}
        save(OUT / 'installed.json', installed)
        cleanup_backup(report['backup'])
        print(f'[{index}/{len(plan["groups"])}] Installed RU audio: {group}', flush=True)
    staged = read(OUT / 'staged_sources.json')
    stage = DataFolder(root=OUT / 'stage')
    graphs = {}
    for relative, entry in staged['graphs'].items():
        assert sha(folder.data_path(relative)) in (entry['before'], entry['after']), 'Dialogue edited: ' + relative
        assert sha(stage.data_path(relative)) == entry['after']
        graphs[relative] = stage.data_path(relative).read_bytes()
    backup = OUT / 'install/dialogues/backups/current'
    folder.sync_parking_commandants(graphs, backup)
    for relative, raw in graphs.items():
        assert folder.data_path(relative).read_bytes() == raw
        stage.remove_data_file(relative)
    cleanup_backup(backup)
    installed.update(graphs={p: hashlib.sha256(raw).hexdigest() for p, raw in graphs.items()},
                     recordings=sum(v['recordings'] for v in installed['groups'].values()),
                     thn_built=False, game_launched=False,
                     pronunciation_prototypes=published['pronunciation_prototypes'],
                     pending_command='single.py rpg scenes --all-parking --language ru')
    save(OUT / 'installed.json', installed)
    print('PASS: 55 RU commandants, 1265 audio fragments, source/reference hashes and shared graphs verified. Final THNs pending user compilation.', flush=True)


def apply():
    publish()
    install_audio()


if __name__ == '__main__':
    sys.stdout.reconfigure(encoding='utf-8')
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument('action', choices=('reference', 'prepare', 'preview', 'generate', 'stage-sources', 'check', 'review-names', 'repair-names', 'publish', 'install-audio', 'apply'))
    args = parser.parse_args()
    if args.action in ('preview', 'generate'):
        generate(args.action == 'preview')
    else:
        {'reference': reference, 'prepare': prepare, 'stage-sources': stage_sources,
         'check': check, 'review-names': review_names, 'repair-names': repair_names,
         'publish': publish, 'install-audio': install_audio, 'apply': apply}[args.action]()
