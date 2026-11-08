"""Exercise selected-group audio installation on a temporary game, without TTS."""
import argparse
import io
from pathlib import Path
import sys
import tempfile
from unittest.mock import patch
import wave


def wav_bytes(frames):
    output = io.BytesIO()
    with wave.open(output, 'wb') as stream:
        stream.setparams((1, 2, 24000, 0, 'NONE', 'not compressed'))
        stream.writeframes(b'\0\0' * frames)
    return output.getvalue()


def expect_error(kind, action):
    try:
        action()
    except kind:
        return
    raise AssertionError(f'Expected {kind.__name__}')


def snapshot(root):
    return {p.relative_to(root).as_posix(): p.read_bytes() for p in root.rglob('*') if p.is_file()}


def main():
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument('--source', type=Path, required=True)
    parser.add_argument('--dependencies', type=Path, default=Path('D:/Games/FL_MOD/Assets/Pythonlancer'))
    args = parser.parse_args()
    sys.dont_write_bytecode = True
    source = args.source.resolve()
    sys.path[:0] = [str(source), str(args.dependencies.resolve())]
    from managers.rpg_audio import RpgAudioManager
    from story.rpg.script import RpgScript
    from tools.data_folder import DataFolder
    from files.rpg_audio import register_bank
    script = RpgScript.load(source / 'story/rpg/rm0001.json')
    scratch = Path(__file__).resolve().parents[2] / 'out/rpg_cutscenes/audio_checks'
    scratch.mkdir(parents=True, exist_ok=True)
    with tempfile.TemporaryDirectory(dir=scratch) as directory:
        root = Path(directory)
        game = root / 'game'
        project = root / 'Assets/Pythonlancer'
        manager = RpgAudioManager(project, script, game)
        folder = manager.folder
        ini = b'; old encoding \xff\r\n[Data]\r\nsounds = audio\\story.ini\r\n[Other]\r\nx = y\r\n'
        for name in ('freelancer.ini', 'freelan_en_port.ini'):
            folder.sync_rpg_bin_file(name, ini)
        folder.sync_data_file('AUDIO/story.ini', b'story untouched')
        folder.sync_data_file('AUDIO/MOD/space/voice.wav', b'space untouched')
        before = snapshot(game)
        expect_error(FileNotFoundError, lambda: manager.install(('ru',), root / 'missing'))
        assert snapshot(game) == before
        for language, frames in (('ru', 2400), ('en', 4800)):
            for fragment in script.fragments:
                path = manager.source(language, fragment)
                path.parent.mkdir(parents=True, exist_ok=True)
                path.write_bytes(wav_bytes(frames))
        first = manager.source('ru', script.fragments[0])
        valid = first.read_bytes()
        first.write_bytes(b'RIFFnot a PCM WAV')
        expect_error(ValueError, lambda: manager.install(('ru',), root / 'invalid'))
        assert snapshot(game) == before
        first.write_bytes(valid)
        manager.install(('ru',), root / 'dry', dry_run=True)
        assert snapshot(game) == before
        writes = []
        original = DataFolder.sync_data_file
        def track(self, path, content):
            writes.append((self.get_root(), path))
            return original(self, path, content)
        with patch.object(DataFolder, 'sync_data_file', track):
            manager.install(('ru',), root / 'ru')
            ru = snapshot(game / 'DATA/AUDIO/MOD/RPG/rm0001')
            manager.install(('en',), root / 'en')
        assert len(ru) == len(script.fragments)
        assert snapshot(game / 'DATA/AUDIO/MOD/RPG/rm0001') == ru
        assert len(snapshot(game / 'DATA/AUDIO/MOD_ENG/RPG/rm0001')) == len(script.fragments)
        assert any(target != game for target, _ in writes), 'Backups must also use DataFolder'
        _, _, records = manager.plan(('en',))
        assert len(records['ru']) == len(records['en']) == len(script.fragments)
        assert records['ru'][0]['duration_seconds'] == .1
        assert records['en'][0]['duration_seconds'] == .2
        bank = folder.data_path('AUDIO/RPG/rm0001_sounds.ini').read_text()
        assert bank.count('[Sound]') == 2 * len(script.fragments)
        for name in ('freelancer.ini', 'freelan_en_port.ini'):
            installed = folder.rpg_bin_path(name).read_bytes()
            assert installed.count(b'rm0001_sounds.ini') == 1
            assert installed.replace(b'      sounds = audio\\RPG\\rm0001_sounds.ini\r\n', b'') == ini
        stable = snapshot(game)
        stamps = {p: p.stat().st_mtime_ns for p in game.rglob('*') if p.is_file()}
        manager.install(('ru', 'en'), root / 'repeat')
        assert snapshot(game) == stable
        assert all(p.stat().st_mtime_ns == stamp for p, stamp in stamps.items())
        # Fail after replacing one WAV, then ensure DATA rollback restores everything.
        first.write_bytes(wav_bytes(7200))
        count = 0
        def fail_once(self, path, content):
            nonlocal count
            if self.get_root() == game:
                count += 1
                if count == 2:
                    raise OSError('simulated interrupted install')
            return original(self, path, content)
        with patch.object(DataFolder, 'sync_data_file', fail_once):
            expect_error(OSError, lambda: manager.install(('ru',), root / 'rollback'))
        assert snapshot(game) == stable
        expect_error(ValueError, lambda: folder.sync_rpg_audio('rm0001',
            {'AUDIO/MOD/RPG/rm0002/rm0002_frag0001_l001_vendor.wav': valid}, {}, root / 'wrong'))
        assert snapshot(game) == stable
        expect_error(ValueError, lambda: register_bank(b'[Other]\nx=1', 'rm0001'))
        assert folder.data_path('AUDIO/story.ini').read_bytes() == b'story untouched'
        assert folder.data_path('AUDIO/MOD/space/voice.wav').read_bytes() == b'space untouched'
    print('PASS: isolated group, PCM validation, RU/EN durations and retention, bank registration, '
          'idempotent installation, DataFolder backups and rollback; no live game writes')


if __name__ == '__main__':
    main()
