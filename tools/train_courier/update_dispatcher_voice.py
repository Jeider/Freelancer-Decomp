"""Apply the approved neutral RU dispatcher voice, with resumable offline takes."""
import argparse
import ast
import difflib
import hashlib
import io
import json
from pathlib import Path
import shutil
import stat
import sys
import time

from pydub import AudioSegment
from check_courier_ru import words
from generate_courier_ru import OUT, ASSETS, sha, save, transcribe
from generate_evacuation_audio import Recorder, inspect

FOLDER = OUT / 'voice_match'
BATCH = FOLDER / 'batch'
SOURCES = ASSETS / 'PILOTS/dispatcher01/default'


def read(path):
    return json.loads(path.read_text(encoding='utf-8'))


def prepare():
    BATCH.mkdir(parents=True, exist_ok=True)
    baseline = FOLDER / 'update_before.json'
    if not baseline.exists():
        selected = {k: v for k, v in read(OUT / 'recordings.json').items()
                    if v['bank'] in ('radio', 'evacuation')}
        assert len(selected) == 195
        for code, row in selected.items():
            assert sha(SOURCES / (code + '.wav')) == row['sha256'], 'Source edited: ' + code
        save(baseline, {'recordings': selected, 'reference_files': {
            name: sha(ASSETS / 'VOICE_SOURCE_RU' / name)
            for name in ('MaleDispatcher.wav', 'MaleDispatcher.json')},
            'preserved_sources': {str(p): sha(p) for p in SOURCES.glob('*.wav')
                                  if p.stem not in selected}})
    return read(baseline)['recordings']


def differences(row):
    expected, actual = words(row['text']), words(row['asr'].get('text', ''))
    return [w for w in difflib.ndiff(expected, actual) if not w.startswith('  ')]


def generate(ids=None):
    assert shutil.disk_usage(OUT).free > 2 * 1024**3
    selected = prepare()
    reference = read(FOLDER / 'reference_neutral.json')
    assert sha(Path(reference['path'])) == reference['sha256']
    previews = read(FOLDER / 'previews.json')
    ledger = FOLDER / 'batch.json'
    records = read(ledger) if ledger.exists() else {}
    if ids:
        assert set(ids) <= selected.keys()
        selected = {k: v for k, v in selected.items() if k in ids}
    for index, (code, old) in enumerate(selected.items(), 1):
        target = BATCH / (code + '.wav')
        if code in records and target.exists() and sha(target) == records[code]['sha256']:
            continue
        row = {k: old[k] for k in ('id', 'text', 'actor', 'bank')}
        if code in previews:
            preview = previews[code]
            assert sha(FOLDER / target.name) == preview['sha256']
            assert preview['reference_sha256'] == reference['sha256']
            shutil.copyfile(FOLDER / target.name, target)
            row.update(preview)
            row['approved_preview'] = True
        else:
            form = dict(engine='omnivoice', language='ru', text=row['text'].replace('!', '.'),
                        ref_text=reference['text'], seed='42', speed='1.0', denoise='false',
                        postprocess_output='false', pronounce='false', num_step='128', guidance_scale='3.0')
            started = time.time()
            for attempt in range(3):
                form['seed'] = str(42 + attempt)
                print(f'[{index}/{len(selected)}] Recording {code}, seed {form["seed"]}', flush=True)
                with Recorder._client() as client, Path(reference['path']).open('rb') as stream:
                    response = client.post('/generate', data=form,
                        files={'ref_audio': ('dispatcher.wav', stream, 'audio/wav')})
                response.raise_for_status()
                if int(response.headers.get('X-OmniVoice-Dropped-Chunks', '0')):
                    if attempt == 2:
                        raise RuntimeError('Dropped speech chunks: ' + code)
                    continue
                sound = AudioSegment.from_file(io.BytesIO(response.content), format='wav').set_channels(1).set_sample_width(2)
                if sound.max_dBFS > -.5:
                    sound = sound.apply_gain(-.5 - sound.max_dBFS)
                sound.export(target, format='wav')
                info = inspect(target)
                assert .25 < info['duration'] < max(10, len(row['text'].split()) * 1.25), code
                assert not code.startswith('te_return_10_') or info['duration'] < 8, code
                row.update(request=dict(form), reference_sha256=reference['sha256'], sha256=sha(target), **info)
                row['asr'] = transcribe(target)
                delta = differences(row)
                if not delta:
                    break
                print('ASR difference:', code, delta, flush=True)
            row['generation_seconds'] = time.time() - started
        row.update(seed=int(row['request']['seed']), engine='omnivoice', num_step=128,
                   signature=hashlib.sha256(json.dumps([row['request'], reference['sha256']], sort_keys=True).encode()).hexdigest())
        row['asr_differences'] = differences(row)
        records[code] = row
        save(ledger, records)
        print(f'Ready {len(records)}/195: {code}, {row["duration"]:.2f}s', flush=True)
    check()


def check():
    records = read(FOLDER / 'batch.json')
    reference = read(FOLDER / 'reference_neutral.json')
    previews = read(FOLDER / 'previews.json')
    expected = dict(next(iter(previews.values()))['request'])
    problems = {}
    for code, row in records.items():
        path = BATCH / (code + '.wav')
        if not path.exists() and (FOLDER / 'updated.json').exists():
            path = OUT / row['bank'] / path.name
        assert sha(path) == row['sha256'], code
        assert abs(inspect(path)['duration'] - row['duration']) < 1e-6, code
        assert row['reference_sha256'] == reference['sha256'], code
        assert row['request']['text'] == row['text'].replace('!', '.'), code
        assert all(row['request'].get(k) == v for k, v in expected.items() if k not in ('text', 'seed')), code
        if code in previews:
            assert row['sha256'] == previews[code]['sha256'], 'Approved preview replaced: ' + code
        if differences(row):
            problems[code] = {'expected': row['text'], 'heard': row['asr'].get('text'), 'changes': differences(row)}
    save(FOLDER / 'batch_check.json', {'count': len(records), 'differences': problems})
    print('Checked', len(records), 'recordings; ASR differences:', len(problems), flush=True)


def ready_records():
    check()
    records = read(FOLDER / 'batch.json')
    assert len(records) == 195
    reviews = read(FOLDER / 'batch_reviews.json') if (FOLDER / 'batch_reviews.json').exists() else {}
    for code, row in records.items():
        if differences(row):
            review = reviews.get(code, {})
            assert review.get('sha256') == row['sha256'] and review.get('reason'), 'Unreviewed ASR: ' + code
    return records


def publish():
    """Publish only Assets sources; DATA synchronization is a separate compiler command."""
    records = ready_records()
    assert not (FOLDER / 'published_update.json').exists(), 'Already published; verify or inspect transaction'
    baseline = read(FOLDER / 'update_before.json')
    files = {}
    for code, row in records.items():
        target = SOURCES / (code + '.wav')
        assert sha(target) == baseline['recordings'][code]['sha256'], 'Source edited: ' + code
        files[target] = (BATCH / target.name).read_bytes()
    for name, digest in baseline['reference_files'].items():
        assert sha(ASSETS / 'VOICE_SOURCE_RU' / name) == digest, 'Reference edited: ' + name
    reference = read(FOLDER / 'reference_neutral.json')
    source = ASSETS / 'VOICE_SOURCE_RU/MaleDispatcher.wav'
    files[source] = (FOLDER / 'reference_neutral.wav').read_bytes()
    reference['path'] = str(source)
    reference['approved_generation'] = {k: v for k, v in next(iter(records.values()))['request'].items()
                                         if k not in ('text', 'ref_text', 'seed')}
    files[source.with_suffix('.json')] = json.dumps(reference, ensure_ascii=False, indent=2).encode('utf-8')
    module = ASSETS / 'Pythonlancer/universe/audio/courier_ru.py'
    text = module.read_text(encoding='utf-8')
    assignment = next(n for n in ast.parse(text).body if isinstance(n, ast.Assign)
                      and any(isinstance(t, ast.Name) and t.id == 'RECORDINGS' for t in n.targets))
    payload = ast.literal_eval(assignment.value)
    assert records.keys() <= {r[0] for r in payload}
    for code, caption, _ in payload:
        if code in records:
            assert records[code]['text'] == caption, 'Script edited: ' + code
    payload = [(code, caption, records[code]['duration'] if code in records else duration)
               for code, caption, duration in payload]
    lines = text.splitlines(keepends=True)
    lines[assignment.lineno-1:assignment.end_lineno] = ['RECORDINGS = ' + repr(payload) + '\n']
    files[module] = ''.join(lines).encode('utf-8')
    assert not any('DATA' in p.relative_to(ASSETS).parts for p in files)
    rollback = FOLDER / 'rollback'
    rollback.mkdir(exist_ok=True)
    entries = []
    for index, (target, raw) in enumerate(files.items()):
        backup = rollback / (str(index) + target.suffix)
        shutil.copyfile(target, backup)
        entries.append({'path': str(target), 'backup': str(backup), 'before': sha(target),
                        'after': hashlib.sha256(raw).hexdigest()})
    save(FOLDER / 'publish_transaction.json', entries)
    changed = []
    try:
        for entry in entries:
            target = Path(entry['path'])
            assert sha(target) == entry['before'], 'Concurrent edit: ' + str(target)
            changed.append(entry)
            temporary = target.with_suffix(target.suffix + '.voice-update.tmp')
            temporary.write_bytes(files[target])
            temporary.replace(target)
            assert sha(target) == entry['after']
    except BaseException:
        for entry in reversed(changed):
            shutil.copyfile(entry['backup'], entry['path'])
        raise
    save(FOLDER / 'published_update.json', {'files': entries, 'recordings': len(records),
                                          'reference_sha256': reference['sha256']})
    print('Published and verified 195 Assets WAVs, dispatcher reference and source durations. Compile DATA next.', flush=True)


def verify():
    records = ready_records()
    published = read(FOLDER / 'published_update.json')
    baseline = read(FOLDER / 'update_before.json')
    for entry in published['files']:
        assert sha(Path(entry['path'])) == entry['after'], entry['path']
    for path, digest in baseline['preserved_sources'].items():
        assert sha(Path(path)) == digest, 'Unrelated source changed: ' + path
    for code, row in records.items():
        target = ASSETS.parent / 'DATA/AUDIO/MOD/dispatcher01' / (code + '.wav')
        assert sha(target) == row['sha256'], 'Installed WAV mismatch: ' + code
    import verify_dispatcher_file_install
    verify_dispatcher_file_install.after()
    # Consolidate generated source files only after installed DATA verification.
    for code, row in records.items():
        target = OUT / row['bank'] / (code + '.wav')
        assert sha(target) in (baseline['recordings'][code]['sha256'], row['sha256']), 'Offline source edited: ' + code
        staged = BATCH / target.name
        if staged.exists():
            staged.replace(target)
    ledger = read(OUT / 'recordings.json')
    ledger.update(records)
    save(OUT / 'recordings.json', ledger)
    if (FOLDER / 'batch_reviews.json').exists():
        reviews_path = OUT / 'asr_reviews.json'
        reviews = read(reviews_path) if reviews_path.exists() else {}
        reviews.update(read(FOLDER / 'batch_reviews.json'))
        save(reviews_path, reviews)
    reference = read(ASSETS / 'VOICE_SOURCE_RU/MaleDispatcher.json')
    local_reference = OUT / 'references/MaleDispatcher.wav'
    shutil.copyfile(ASSETS / 'VOICE_SOURCE_RU/MaleDispatcher.wav', local_reference)
    reference['path'] = str(local_reference)
    references = read(OUT / 'references/manifest.json')
    references['MaleDispatcher'] = reference
    save(OUT / 'references/manifest.json', references)
    save(FOLDER / 'updated.json', {'recordings': len(records), 'reference_sha256': reference['sha256'],
                                  'installed_sha256': {code: row['sha256'] for code, row in records.items()},
                                  'all_installed_hashes_match': True, 'game_launched': False,
                                  'verified_utc': time.strftime('%Y-%m-%dT%H:%M:%SZ', time.gmtime())})
    root = (FOLDER / 'rollback').resolve()
    for entry in published['files']:
        original = Path(entry['backup'])
        path = original.resolve()
        assert path.is_relative_to(root) and root.is_relative_to(FOLDER.resolve())
        # VoiceStudio uses Python 3.11, before Path.is_junction was introduced.
        for parent in (original, *original.parents):
            if parent.exists():
                assert not (getattr(parent.lstat(), 'st_file_attributes', 0) & stat.FILE_ATTRIBUTE_REPARSE_POINT), parent
        if path.exists():
            assert sha(path) == entry['before']
            path.unlink()
    root.rmdir()
    BATCH.rmdir()
    print('PASS: 195 approved-voice recordings installed; sources and durations verified; temporary backups removed.', flush=True)


if __name__ == '__main__':
    sys.stdout.reconfigure(encoding='utf-8')
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument('action', choices=('generate', 'check', 'publish', 'verify'))
    parser.add_argument('--ids', nargs='+')
    args = parser.parse_args()
    if args.action == 'generate':
        generate(args.ids)
    else:
        {'check': check, 'publish': publish, 'verify': verify}[args.action]()
