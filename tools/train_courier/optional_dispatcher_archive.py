"""Remove obsolete archive dependency; source-only install with isolated check."""
import ast
import importlib.util
import io
import json
from pathlib import Path
import sys
import tempfile
import wave

sys.dont_write_bytecode = True
ROOT = Path(__file__).resolve().parents[2]
PROJECT = Path('D:/Games/FL_MOD/Assets/Pythonlancer')
OUT = ROOT / 'out/train_courier/audio_ru/file_export/optional_archive'


def load(name, path):
    spec = importlib.util.spec_from_file_location(name, path)
    result = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(result)
    return result


def main():
    OUT.mkdir(parents=True, exist_ok=True)
    updates = {}
    source = (PROJECT / 'tools/dispatcher_files.py').read_text(encoding='utf-8')
    start = source.index("        for row in metadata[voice]['archive_leaves']:")
    end = source.index('        required_missing=', start)
    source = source[:start] + ('        # Historical archive metadata is optional provenance, not a build input.\n') + source[end:]
    updates['tools/dispatcher_files.py'] = source
    source = (PROJECT / 'tools/data_folder.py').read_text(encoding='utf-8')
    old = "            for row in [*manifest['recordings'].values(),*manifest['archive_leaves']]:"
    assert source.count(old) == 1
    updates['tools/data_folder.py'] = source.replace(old, "            # Only playable recordings are required; old archive files are optional.\n            for row in manifest['recordings'].values():")
    for relative, content in updates.items():
        ast.parse(content)
        target = OUT / relative
        target.parent.mkdir(parents=True, exist_ok=True)
        target.write_text(content, encoding='utf-8')
    export = load('optional_export', OUT / 'tools/dispatcher_files.py')
    DataFolder = load('optional_folder', OUT / 'tools/data_folder.py').DataFolder
    stream = io.BytesIO()
    with wave.open(stream, 'wb') as audio:
        audio.setparams((1, 2, 24000, 0, 'NONE', 'not compressed'))
        audio.writeframes(b'\0\0' * 2400)
    with tempfile.TemporaryDirectory(dir=OUT) as tmp:
        game = Path(tmp)
        folder = DataFolder(root=game)
        project = game / 'Assets/Pythonlancer'
        project.mkdir(parents=True)
        folder.sync_data_file('AUDIO/voices_space_male.ini', '[Voice]\nnickname = dispatcher01\n[Sound]\nmsg = tc_test\n')
        folder.sync_data_file('AUDIO/voices_space_female.ini', '; unchanged\n')
        folder.sync_data_file('AUDIO/MOD/dispatcher01/tc_test.wav', stream.getvalue())
        for voice in export.VOICES:
            folder.sync_data_file(f'AUDIO/MOD/{voice}/manifest.json', json.dumps({
                'archive_leaves': [{'file': f'AUDIO/MOD/{voice}/archive/missing.wav', 'sha256': 'obsolete'}],
                'recordings': {}, 'source_utf_sha256': 'historical'}))
        files, _ = export.plan(project, folder)
        folder.sync_ru_dispatcher_files(files, export.VOICES)
        assert folder.data_path('AUDIO/MOD/dispatcher01/tc_test.wav').read_bytes() == stream.getvalue()
        broken = dict(files)
        broken['AUDIO/MOD/dispatcher01/tc_test.wav'] = b'corrupt'
        try:
            folder.sync_ru_dispatcher_files(broken, export.VOICES)
        except ValueError:
            pass
        else:
            raise AssertionError('Active audio validation bypassed')
        # Scratch DATA cleanup also uses the central API.
        for path in (game / 'DATA').rglob('*'):
            if path.is_file():
                folder.remove_data_file(path.relative_to(game / 'DATA'))
    print('PASS: compilation without archive succeeds; corrupt active audio rejected.')
    if '--publish' in sys.argv:
        for relative, content in updates.items():
            target = PROJECT / relative
            backup = OUT / 'before' / relative
            backup.parent.mkdir(parents=True, exist_ok=True)
            backup.write_bytes(target.read_bytes())
            target.write_text(content, encoding='utf-8')
            assert target.read_text(encoding='utf-8') == content
        print('Installed Pythonlancer sources; live DATA and archive files untouched.')


if __name__ == '__main__':
    main()
