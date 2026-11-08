"""PCM WAV integration checks with fake speech responses; no external voice calls."""
import argparse
from contextlib import nullcontext
import io
import json
import math
from pathlib import Path
import struct
import sys
import tempfile
from types import SimpleNamespace
from unittest.mock import patch
import wave

ROOT = Path(__file__).resolve().parents[2]
PROJECT = Path('D:/Games/FL_MOD/Assets/Pythonlancer')


def wav_bytes(width=2, rate=24000):
    result = io.BytesIO()
    with wave.open(result, 'wb') as wav:
        wav.setparams((1, width, rate, 0, 'NONE', 'not compressed'))
        samples = [0] * (rate // 2) + [int(12000 * math.sin(2 * math.pi * 440 * n / rate)) for n in range(rate)]
        wav.writeframes(b''.join(value.to_bytes(width, 'little', signed=True) for value in samples))
    return result.getvalue()


def inspect(data):
    with wave.open(io.BytesIO(data), 'rb') as wav:
        assert wav.getcomptype() == 'NONE' and wav.getsampwidth() == 2
        assert wav.getframerate() == 24000 and wav.getnchannels() == 1
        return wav.getnframes()


def main():
    parser = argparse.ArgumentParser()
    parser.add_argument('--source', type=Path, default=ROOT / 'out/voicestudio_pcm/payload')
    args = parser.parse_args()
    source = args.source.resolve()
    sys.dont_write_bytecode = True
    sys.path.insert(0, str(PROJECT))
    import tools, managers
    tools.__path__.insert(0, str(source / 'tools'))
    managers.__path__.insert(0, str(source / 'managers'))
    from tools.voicestudio import VoiceStudioClone as V
    from tools.voice_output import output_path
    import tools.voice_output as naming
    from tools.audio_folder import AudioFolder
    from tools.voice_api import VoiceApi
    from managers.rpg_voice import RpgVoiceManager
    captured = []
    def request(client, method, path, **kwargs):
        captured.append(kwargs['json'])
        return SimpleNamespace(status_code=200, content=wav_bytes(), text='')
    with patch.object(V, '_client', return_value=nullcontext(object())), \
         patch.object(V, '_profile_id', return_value='test-profile'), \
         patch.object(V, 'source_file', return_value=Path('unused-reference.wav')), \
         patch.object(V, '_request', side_effect=request):
        for language in ('ru', 'en'):
            inspect(V.generate_voice_bytes(None, 'Format test', language, source_name='test'))
    assert all(body['response_format'] == 'wav' for body in captured) and len(captured) == 2
    assert inspect(V._pcm_wav(wav_bytes(width=3))) == 36000
    bad_tag = bytearray(wav_bytes()); struct.pack_into('<H', bad_tag, 20, 0x55)
    for bad in (b'ID3_fake_mp3', bytes(bad_tag), wav_bytes()[:-200]):
        try:
            V._pcm_wav(bad)
        except ValueError:
            pass
        else:
            raise AssertionError('Invalid/compressed response was accepted')
    scratch = ROOT / 'out/voicestudio_pcm/check'
    scratch.mkdir(parents=True, exist_ok=True)
    with tempfile.TemporaryDirectory(dir=scratch) as temp:
        temp = Path(temp)
        result = V._write(wav_bytes(), temp / 'new.mp3', trim_lead=True)
        assert result == temp / 'new.wav' and not (temp / 'new.mp3').exists()
        assert 20000 < inspect(result.read_bytes()) < 36000
        try:
            V._write(wav_bytes(), temp / 'DATA/audio/no.wav')
        except ValueError:
            pass
        else:
            raise AssertionError('DATA source write was allowed')
        group = SimpleNamespace(get_cutscene_folder=lambda: 'rm0001', get_sounds=lambda: [
            SimpleNamespace(name='old_mp3'), SimpleNamespace(name='old_wav'), SimpleNamespace(name='new')])
        destination = temp / 'voices/rm0001'
        destination.mkdir(parents=True)
        (destination / 'old_mp3.mp3').write_bytes(b'existing recording')
        (destination / 'old_wav.wav').write_bytes(wav_bytes())
        calls = []
        def generate(sound, file_destination):
            calls.append(file_destination)
            return V._write(wav_bytes(), file_destination)
        with patch.object(AudioFolder, 'get_initial_cutscene_audio_path', return_value=destination.parent), \
             patch.object(VoiceApi, 'generate_ru_voice', side_effect=generate):
            AudioFolder.generate_cutscene_sounds(group)
            AudioFolder.generate_cutscene_sounds(group)
        assert calls == [destination / 'new.wav']
        assert (destination / 'old_mp3.mp3').read_bytes() == b'existing recording'
        inspect((destination / 'new.wav').read_bytes())
        # Pilot XML staging must preserve new WAV and still locate older MP3.
        from tools.audio_pilot import TempPilot
        pilot_root = temp / 'pilots'
        pilot_files = pilot_root / 'test/sub'
        pilot_files.mkdir(parents=True)
        (pilot_files / 'fresh.wav').write_bytes(wav_bytes())
        (pilot_files / 'legacy.mp3').write_bytes(b'legacy audio')
        pilot_lines = [SimpleNamespace(get_code=lambda code=code: code,
                       get_subfolder=lambda: 'sub', is_static=lambda: False) for code in ('fresh', 'legacy')]
        pilot = SimpleNamespace(FOLDER='test', get_lines=lambda: pilot_lines)
        xml_root = temp / 'xml'
        xml_root.mkdir()
        with patch.object(TempPilot, 'get_root_pilot_path', return_value=pilot_root), \
             patch.object(AudioFolder, 'get_apply_xml_audio_path', return_value=xml_root):
            TempPilot.fill_files_for_xml(pilot)
        inspect((xml_root / 'test.xml/test/fresh.wav').read_bytes())
        assert (xml_root / 'test.xml/test/legacy.mp3').read_bytes() == b'legacy audio'
        with patch.object(naming, 'VOICE_BACKEND', 'steos'):
            assert output_path(temp / 'legacy.mp3').suffix == '.mp3'
        manager = RpgVoiceManager(PROJECT, PROJECT / 'story/rpg/rm0001.json')
        plan = manager.voices(temp / 'plan', ('ru', 'en'), 'Hassler', dry_run=True)
        assert all(row['filename'].endswith('.wav') for rows in plan['languages'].values() for row in rows)
    print('PASS: WAV API request RU/EN, PCM16 normalization, 24 kHz retained, PCM trimming, '
          'bad/truncated audio rejection, proper extension, repeat/legacy skip, pilot staging, Steos unchanged, RPG WAV plans, no DATA')


if __name__ == '__main__':
    main()
