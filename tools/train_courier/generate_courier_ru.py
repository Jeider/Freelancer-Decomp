"""Resumable RU courier recordings. Offline output; no game/THN writes."""
import argparse
import hashlib
import io
import json
from pathlib import Path
import re
import shutil
import sys
import time

from pydub import AudioSegment
from generate_evacuation_audio import Recorder, inspect
from evacuation_script import rows as evacuation_rows

ROOT = Path(__file__).resolve().parents[2]
ASSETS = Path('D:/Games/FL_MOD/Assets')
OUT = ROOT / 'out/train_courier/audio_ru'
REFS = {
    'Trent': ([
        ('AUDIO_CUTSCENE_RU/M01/m01_intro_0030_trent.wav', 'Нет, спасибо. Мистер Джеймсон, я пришел увольняться!'),
        ('AUDIO_CUTSCENE_RU/M01/m01_intro_0150_trent.wav', 'Да, друг, без тебя здесь стало бы совсем тоскливо. Так, мой транспорт почти прибыл. Так что мне пора.'),
    ]),
    'MaleDispatcher': ([
        ('PILOTS/dispatcher01/default/gcs_combat_announce_allclear_01-.mp3', 'Противников в радиусе базы не обнаружено.'),
        ('PILOTS/dispatcher01/default/gcs_combat_announce_allclear_03-.mp3', 'Противников в ближайшем радиусе не обнаружено.'),
    ]),
}


def sha(path):
    return hashlib.sha256(path.read_bytes()).hexdigest()


def save(path, value):
    path.parent.mkdir(parents=True, exist_ok=True)
    temporary = path.with_suffix('.tmp')
    temporary.write_text(json.dumps(value, ensure_ascii=False, indent=2), encoding='utf-8')
    temporary.replace(path)


def references():
    folder = OUT / 'references'
    folder.mkdir(parents=True, exist_ok=True)
    result = {}
    for name in ('Trent', 'MaleDispatcher', 'RpgTradeDirector'):
        target = folder / (name + '.wav')
        existing = ASSETS / 'VOICE_SOURCE_RU' / target.name
        parts = REFS['MaleDispatcher' if name == 'RpgTradeDirector' else name]
        if existing.exists():
            # Never replace the user's existing reference. Read its transcript
            # from our provenance record, otherwise obtain it through ASR.
            shutil.copyfile(existing, target)
            old = folder / 'manifest.json'
            old = json.loads(old.read_text(encoding='utf-8')).get(name, {}) if old.exists() else {}
            provenance = existing.with_suffix('.json')
            if provenance.exists():
                canonical = json.loads(provenance.read_text(encoding='utf-8'))
                if canonical.get('sha256') == sha(target):
                    old = canonical
            transcript = old.get('text') if old.get('sha256') == sha(target) else transcribe(target)['text']
            sources = old.get('sources', []) if old.get('sha256') == sha(target) else []
            if not sources:
                sources = [{'path': str(existing), 'sha256': sha(existing)}]
        else:
            sound = AudioSegment.empty()
            sources = []
            for relative, _ in parts:
                source = ASSETS / relative
                if len(sound):
                    sound += AudioSegment.silent(duration=200, frame_rate=24000)
                sound += AudioSegment.from_file(source).set_channels(1).set_frame_rate(24000).set_sample_width(2)
                sources.append({'path': str(source), 'sha256': sha(source)})
            sound.export(target, format='wav')
            transcript = ' '.join(text for _, text in parts)
        result[name] = {'path': str(target), 'text': transcript, 'sha256': sha(target),
                        'sources': sources, **inspect(target)}
        if existing.exists() and old.get('approved_generation'):
            result[name]['approved_generation'] = old['approved_generation']
    save(folder / 'manifest.json', result)
    return result


def plan():
    script = ASSETS / 'Pythonlancer/story/rpg/rm0001.json'
    result = [dict(id=row['id'] + '_l001_' + row['role'], text=row['ru'],
                   actor='Trent' if row['role'] == 'player' else 'RpgTradeDirector', bank='bar')
              for row in json.loads(script.read_text(encoding='utf-8'))['fragments']]
    try:
        from dispatcher_ru import clips
    except ImportError:
        clips = lambda: []
    result += [dict(id=code, text=text, actor='MaleDispatcher', bank='radio') for code, text in clips()]
    result += [dict(id=row['id'], text=row['ru'], actor='MaleDispatcher', bank='evacuation')
               for row in evacuation_rows() if row['speaker'] == 'dispatcher' and row['active']]
    vocabulary = OUT / 'vocabulary.json'
    if vocabulary.exists():
        result += json.loads(vocabulary.read_text(encoding='utf-8'))
    assert len({row['id'] for row in result}) == len(result)
    return result


def transcribe(path):
    sound = AudioSegment.from_wav(path)
    silence = AudioSegment.silent(duration=500, frame_rate=sound.frame_rate)
    stream = io.BytesIO()
    (silence + sound + silence).export(stream, format='wav')
    stream.seek(0)
    with Recorder._client() as client:
        # The capture /transcribe route ignores its language hint. This local
        # VoiceStudio route forwards Russian explicitly to the same ASR model.
        response = client.post('/v1/audio/transcriptions', data={'language':'ru','model':'whisper-1','response_format':'verbose_json'},
                               files={'file': (path.name, stream, 'audio/wav')})
    response.raise_for_status()
    return response.json()


def main():
    sys.stdout.reconfigure(encoding='utf-8')
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument('--bank', choices=('all', 'bar', 'radio', 'evacuation', 'vocabulary'), default='all')
    parser.add_argument('--ids', nargs='+')
    parser.add_argument('--prepare', action='store_true')
    parser.add_argument('--transcribe', action='store_true')
    parser.add_argument('--asr-only', action='store_true')
    parser.add_argument('--seed', type=int, help='Explicit new seed; otherwise keep each accepted take')
    parser.add_argument('--steps', type=int, help='Explicit OmniVoice sampling steps; keep accepted take settings by default')
    args = parser.parse_args()
    assert shutil.disk_usage(OUT.parent).free > 2 * 1024**3
    refs = references()
    all_rows = plan()
    save(OUT / 'script.json', all_rows)
    selected = [r for r in all_rows if (args.bank == 'all' or r['bank'] == args.bank)
                and (not args.ids or r['id'] in args.ids)]
    if args.prepare:
        print('Prepared references and script:', len(all_rows), 'lines')
        return
    manifest = OUT / 'recordings.json'
    records = json.loads(manifest.read_text(encoding='utf-8')) if manifest.exists() else {}
    for index, row in enumerate(selected, 1):
        ref = refs[row['actor']]
        path = OUT / row['bank'] / (row['id'] + '.wav')
        path.parent.mkdir(exist_ok=True)
        old = records.get(row['id'], {})
        seed = args.seed if args.seed is not None else old.get('seed', 42)
        form = dict(engine='omnivoice', language='ru', text=row['text'], ref_text=ref['text'],
                    seed=str(seed), speed='1.0', denoise='false', postprocess_output='false', pronounce='false')
        steps = args.steps if args.steps is not None else old.get('num_step')
        if steps is not None:
            form['num_step'] = str(steps)
        if row['actor'] == 'MaleDispatcher' and row['bank'] in ('radio', 'evacuation'):
            form.update(ref.get('approved_generation', {}))
            form['text'] = row['text'].replace('!', '.')
            if args.seed is not None:
                form['seed'] = str(args.seed)
            if args.steps is not None:
                form['num_step'] = str(args.steps)
            steps = int(form['num_step']) if 'num_step' in form else steps
        # Very short isolated nouns need a sentence boundary in the TTS prompt.
        # Keep UI/source text unchanged; punctuation is not spoken.
        if row['bank'] == 'vocabulary':
            form['text'] = row['text'].rstrip('.!?') + '.'
        signature = hashlib.sha256(json.dumps([form, ref['sha256']], sort_keys=True).encode()).hexdigest()
        keep_context = (old.get('method') == 'context_crop_v1' and old.get('text') == row['text']
                        and old.get('reference_sha256') == ref['sha256'] and args.seed is None and args.steps is None)
        if not (path.exists() and (old.get('signature') == signature or keep_context) and old.get('sha256') == sha(path)):
            assert not args.asr_only, 'Missing matching recording: ' + row['id']
            started = time.time()
            print(f'[{index}/{len(selected)}] Generating {row["id"]}', flush=True)
            for attempt in range(5):
                form['seed'] = str(seed + attempt)
                with Recorder._client() as client, Path(ref['path']).open('rb') as stream:
                    response = client.post('/generate', data=form, files={'ref_audio': (row['actor']+'.wav', stream, 'audio/wav')})
                response.raise_for_status()
                try:
                    assert not int(response.headers.get('X-OmniVoice-Dropped-Chunks', '0')), row['id']
                    sound = AudioSegment.from_file(io.BytesIO(response.content), format='wav').set_channels(1).set_sample_width(2)
                    if sound.max_dBFS > -.5:
                        sound = sound.apply_gain(-.5 - sound.max_dBFS)
                    sound.export(path, format='wav')
                    info = inspect(path)
                    assert .25 < info['duration'] < max(10, len(row['text'].split()) * 1.25), (row['id'], info)
                    break
                except AssertionError:
                    print('Rejected empty/truncated take:', row['id'], 'seed', form['seed'], flush=True)
                    if attempt == 4:
                        raise
            signature = hashlib.sha256(json.dumps([form, ref['sha256']], sort_keys=True).encode()).hexdigest()
            records[row['id']] = {**row, 'reference_sha256': ref['sha256'], 'signature': signature,
                                  'sha256': sha(path), 'seed': int(form['seed']), 'engine': 'omnivoice',
                                  'num_step': steps, 'request': form,
                                  'generation_seconds': time.time() - started, **info}
            save(manifest, records)
        if (args.transcribe or args.asr_only) and 'asr' not in records[row['id']]:
            records[row['id']]['asr'] = transcribe(path)
            save(manifest, records)
            print('ASR', row['id'], records[row['id']]['asr'].get('text'), flush=True)
        print(f'[{index}/{len(selected)}] Ready {row["id"]}: {records[row["id"]]["duration"]:.2f}s', flush=True)
    print('Recorded', len(records), 'RU lines. No game DATA or THN writes.', flush=True)


if __name__ == '__main__':
    main()
