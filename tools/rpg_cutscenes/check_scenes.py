"""Check native Autoplay fragment generation against isolated RU/EN audio."""
import argparse
import hashlib
import json
from pathlib import Path
import re
import sys
import tempfile
from xml.etree import ElementTree

from check_audio import wav_bytes, snapshot, expect_error


def main():
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument('--source', type=Path, required=True)
    parser.add_argument('--dependencies', type=Path, default=Path('D:/Games/FL_MOD/Assets/Pythonlancer'))
    args = parser.parse_args()
    sys.dont_write_bytecode = True
    source, dependencies = args.source.resolve(), args.dependencies.resolve()
    sys.path[:0] = [str(source), str(dependencies)]
    from managers.rpg_audio import RpgAudioManager
    from managers.rpg_scene import RpgSceneManager
    from story.rpg.script import RpgScript
    script = RpgScript.load(source / 'story/rpg/rm0001.json')
    scratch = Path(__file__).resolve().parents[2] / 'out/rpg_cutscenes/scene_checks'
    scratch.mkdir(parents=True, exist_ok=True)
    with tempfile.TemporaryDirectory(dir=scratch) as directory:
        root = Path(directory)
        audio = RpgAudioManager(root / 'Assets/Pythonlancer', script, root / 'game')
        scenes = RpgSceneManager(dependencies, script, root / 'game')
        for name in ('freelancer.ini', 'freelan_en_port.ini'):
            audio.folder.sync_rpg_bin_file(name, b'[Data]\nsounds = audio\\story.ini\n')
        for language, seconds in (('ru', 27), ('en', 2)):
            for fragment in script.fragments:
                path = audio.source(language, fragment)
                path.parent.mkdir(parents=True, exist_ok=True)
                path.write_bytes(wav_bytes(seconds * 24000))
        audio.install(('ru', 'en'), root / 'audio_reports')
        before = snapshot(root / 'game')
        scenes.build(('ru', 'en'), root / 'dry', dry_run=True)
        assert snapshot(root / 'game') == before
        files, catalogs = scenes.plan(('ru', 'en'))
        assert files == scenes.plan(('ru', 'en'))[0], 'Must not mutate shared animation sequences'
        assert len(files) == 2 * len(script.fragments) + 20
        for language, seconds in (('ru', 27), ('en', 2)):
            catalog = catalogs[language]
            assert not catalog['runtime_connected']
            assert len(catalog['fragments']) == len(script.fragments)
            for row in catalog['fragments']:
                content = files[row['path']].decode('utf-8')
                assert row['speech_seconds'] == seconds
                assert seconds < row['scene_seconds'] < seconds + 2
                assert content.count('type=DEFORMABLE') == 1
                assert content.count('type=SOUND') == content.count('START_SOUND') == 1
                assert content.count('type=CAMERA') == 1 and 'flags=REFERENCE' in content
                assert f'RpgCamera_{row["role"]}' in content
                assert f'Actor="{script.data["binding"][row["role"]]}"' in content
                assert not any(token in content for token in ('type=SCENE', 'type=LIGHT', 'ATTACH_ENTITY', 'special/p', 'offscreen'))
                assert f'duration={seconds}.0' in content
                assert hashlib.sha256(files[row['path']]).hexdigest() == row['sha256']
                # Every animation event finishes within the fragment (including facial tail).
                pattern = r'\{\s*([0-9.]+),\s*START_MOTION,\s*\{[^}]+\},\s*\{([^}]+)\}'
                events = re.findall(pattern, content)
                assert len(events) >= 1
                assert row['facial_timing'] == 'Character.facial(auto_lip=True)'
                assert 'Sc_MLBODY' not in content, 'Body must survive spoken fragment teardown'
                for start, props in events:
                    duration = float(re.search(r'duration=([0-9.]+)', props).group(1))
                    assert float(start) + duration <= row['scene_seconds'] + .02
            assert len(catalog['gestures']) == 16
            for gesture in catalog['gestures']:
                body = files[gesture['path']].decode('utf-8')
                assert hashlib.sha256(files[gesture['path']]).hexdigest() == gesture['sha256']
                assert 'START_SOUND' not in body and 'type=CAMERA' not in body
                assert body.count('type=DEFORMABLE') == 1
                assert body.count('START_MOTION') == (3 if gesture['step'] in (0, 3) else 1)
                assert gesture['duration'] > 10, 'Complete auto step must not be clipped to a short voice'
            assert catalog['gestures'] == catalogs['en']['gestures']
            xml = files[f'SCRIPTS/RPG/rm0001/{language}/subtitles.xml']
            assert len(ElementTree.fromstring(xml)) == len(script.fragments)
        report = scenes.build(('en',), root / 'scene_reports')
        assert report['fragments'] == len(script.fragments)
        assert not scenes.folder.data_path('SCRIPTS/RPG/rm0001/ru/manifest.json').exists()
        installed = snapshot(root / 'game')
        scenes.build(('en',), root / 'scene_repeat')
        assert snapshot(root / 'game') == installed
        # Corrupting installed WAV must abort before touching any existing scene.
        target = catalogs['en']['fragments'][0]['audio']
        scenes.folder.sync_data_file(target, wav_bytes(12000))
        before_error = snapshot(root / 'game')
        expect_error(ValueError, lambda: scenes.build(('en',), root / 'failed'))
        assert snapshot(root / 'game') == before_error
        expect_error(ValueError, lambda: scenes.folder.sync_rpg_scenes('rm0001',
            {'SCRIPTS/RPG/rm0002/en/rm0002_frag0001.thn': b''}, root / 'invalid'))
        # Also render the real installed recordings, without writing game files.
        live = RpgSceneManager(dependencies, script)
        installed_catalog = json.loads(live.folder.data_path('SCRIPTS/RPG/rm0001/en/manifest.json').read_text(encoding='utf-8'))
        recorded_script = RpgScript(installed_catalog['dialogue'])
        if len(recorded_script.fragments) != len(script.fragments):
            expect_error(ValueError, lambda: live.plan(('en',)))
        live = RpgSceneManager(dependencies, recorded_script)
        live_files, live_catalog = live.plan(('en',))
        assert len(live_catalog['en']['fragments']) == len(recorded_script.fragments)
        assert len(live_files) == len(recorded_script.fragments) + 18
    print('PASS: native Autoplay, all localized fragments, independent 27s/2s timing, event bounds, '
          '16 whole auto gesture steps, minimal bound entities, deterministic generation, localized install, WAV hash checks, '
          'and real installed EN recordings; no live game writes')


if __name__ == '__main__':
    main()
