"""Offline regression of every story line through the real VoiceStudio composer.

Network, reference loading and output writes are replaced with capture stubs.
The existing and staged RU requests must be identical for the entire corpus.
"""
import ast
from collections import Counter
from contextlib import contextmanager
import importlib.util
import json
from pathlib import Path
import sys
from types import SimpleNamespace

from en_direction import OUT, PROJECT, sha, save, stripped_tree

sys.path.insert(0, str(PROJECT))
sys.dont_write_bytecode = True

from story import actors
from audio import delivery


def module(name, path):
    spec = importlib.util.spec_from_file_location(name, path)
    result = importlib.util.module_from_spec(spec)
    sys.modules[name] = result
    spec.loader.exec_module(result)
    return result


def recorder(base):
    class Capture(base):
        calls = []

        @classmethod
        def _log(cls, *args):
            pass

        @classmethod
        @contextmanager
        def _client(cls):
            yield None

        @classmethod
        def resolve_source(cls, source_name, source_lang, default_actor=None):
            return source_name, Path(f'reference/{source_lang}/{source_name}.wav')

        @classmethod
        def _profile_id(cls, client, source_name, source_lang, source):
            return f'profile:{source_lang}:{source_name}'

        @classmethod
        def _request(cls, client, method, endpoint, **kwargs):
            cls.calls.append({'method': method, 'endpoint': endpoint, **kwargs})
            return SimpleNamespace(status_code=200, content=b'captured', text='')

        @classmethod
        def _write(cls, voice_bytes, file_destination, trim_lead=False):
            assert voice_bytes == b'captured'
            return file_destination
    return Capture


def calls(raw):
    result = {}
    for cls in (node for node in ast.parse(raw.decode('utf-8-sig')).body if isinstance(node, ast.ClassDef)):
        for node in ast.walk(cls):
            if isinstance(node, ast.Call) and isinstance(node.func, ast.Name) and node.func.id == 'VoiceLine':
                key = (cls.name, ast.literal_eval(node.args[0]))
                assert key not in result, key
                result[key] = node
    return result


def instantiate(call, voice_line, performance):
    scope = dict(vars(actors))
    scope.update(vars(delivery))
    scope.update(VoiceLine=voice_line, delivery=delivery, performance=performance)
    return eval(compile(ast.Expression(call), '<reviewed-story-line>', 'eval'), scope)


def request(capture, line, language):
    capture.calls = []
    sound = SimpleNamespace(line=line)
    getattr(capture, f'generate_{language}_voice')(sound, 'unused.wav', default_actor='Default')
    assert len(capture.calls) == 1
    return capture.calls[0]


def payload(call):
    data = call.get('json', call.get('data'))
    return dict(text=data.get('input', data.get('text')), language=data['language'],
                speed=float(data['speed']), instruct=data.get('instruct'),
                voice=data.get('voice', data.get('profile_id')),
                denoise=str(data['denoise']).lower(), num_step=int(data['num_step']))


def main():
    plan = json.loads((OUT / 'plan.json').read_text(encoding='utf-8'))
    inventory = json.loads((OUT / 'inventory.json').read_text(encoding='utf-8'))
    for name, expected in plan['files'].items():
        assert sha((OUT / 'stage' / name).read_bytes()) == expected['after']
    original = module('story_direction_original_sound', OUT / 'before/audio/sound.py')
    changed = module('story_direction_changed_sound', OUT / 'stage/audio/sound.py')
    performance = module('audio.story_delivery', OUT / 'stage/audio/story_delivery.py')
    old_backend = module('story_direction_old_backend', OUT / 'before/tools/voicestudio.py')
    new_backend = module('story_direction_new_backend', OUT / 'stage/tools/voicestudio.py')
    old_recorder = recorder(old_backend.VoiceStudioClone)
    new_recorder = recorder(new_backend.VoiceStudioClone)
    selected = {(row['file'], row['segment'], row['index']): row['style'] for row in plan['annotations']}
    ru, en, emotional, plain = 0, 0, 0, 0
    baseline_presets = {name: dict(vars(value)) for name, value in vars(delivery).items()
                        if isinstance(value, delivery.Delivery)}
    for path in sorted(name for name in inventory['files'] if name.startswith('story/scripts/')):
        before = (OUT / 'before' / path).read_bytes()
        staged = OUT / 'stage' / path
        after = staged.read_bytes() if staged.exists() else before
        assert stripped_tree(before) == stripped_tree(after), path
        old_calls, new_calls = calls(before), calls(after)
        assert old_calls.keys() == new_calls.keys()
        for key, old_call in old_calls.items():
            before_line = instantiate(old_call, original.VoiceLine, performance)
            after_line = instantiate(new_calls[key], changed.VoiceLine, performance)
            ru_before = request(old_recorder, before_line, 'ru')
            ru_after = request(new_recorder, after_line, 'ru')
            assert ru_before == ru_after, ('RU request changed', path, key)
            assert after_line.get_delivery('ru') is after_line.delivery
            ru += 1
            if not before_line.en:
                assert after_line.delivery_en is None
                continue
            old_request = request(old_recorder, before_line, 'en')
            new_request = request(new_recorder, after_line, 'en')
            en += 1
            style = selected.get((path, *key))
            if not style:
                assert new_request == old_request, ('Unmarked EN request changed', path, key)
                plain += 1
                continue
            assert after_line.delivery_en is getattr(performance, style)
            assert payload(new_request) == payload(old_request), ('Voice traits changed', path, key)
            assert new_request['endpoint'] == '/generate'
            form = new_request['data']
            assert form['engine'] == 'indextts2' and form['language'] == 'en'
            assert ('emo_vector' in form) != ('emo_text' in form)
            if 'emo_vector' in form:
                vector = json.loads(form['emo_vector'])
                assert len(vector) == 8 and all(0 <= value <= 1 for value in vector)
                assert any(vector)
                assert tuple(vector) == getattr(performance, style).emo_vector
            else:
                assert 0 < float(form['emo_alpha']) <= .6
                assert form['emo_text'] == getattr(performance, style).emo_text
            # The English call must not contaminate a subsequent Russian request.
            assert request(new_recorder, after_line, 'ru') == ru_before
            emotional += 1
    assert {name: dict(vars(getattr(delivery, name))) for name in baseline_presets} == baseline_presets
    assert emotional == plan['marked_lines'] and en == plan['reviewed_en_lines']
    # Guard the entire composer and the RU method, not just the current examples.
    old_tree = ast.parse((OUT / 'before/tools/voicestudio.py').read_text(encoding='utf-8'))
    new_tree = ast.parse((OUT / 'stage/tools/voicestudio.py').read_text(encoding='utf-8'))
    for tree in (old_tree, new_tree):
        for node in ast.walk(tree):
            if isinstance(node, ast.ClassDef):
                node.body = [item for item in node.body if not (
                    isinstance(item, ast.FunctionDef) and item.name == 'generate_en_voice')]
    assert ast.dump(old_tree) == ast.dump(new_tree), 'Unrelated backend change'
    result = dict(passed=True, plan_sha256=sha((OUT / 'plan.json').read_bytes()),
                  russian_requests_identical=ru, english_requests_checked=en,
                  english_emotion_requests=emotional, unmarked_english_unchanged=plain,
                  marked_space=plan['marked_space_lines'], actor_traits_preserved=True,
                  no_network=True, no_audio_generated=True, no_data_writes=True,
                  presets=dict(Counter(row['style'] for row in plan['annotations'])))
    save(OUT / 'checked.json', result)
    print(f'PASS: {ru} identical RU requests; {emotional} emotional EN requests; '
          f'{plain} unchanged EN requests. Reference, pitch instructions, speed, '
          'denoise, text and generation steps preserved. No network/audio/DATA writes.')


if __name__ == '__main__':
    main()
