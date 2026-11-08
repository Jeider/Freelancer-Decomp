"""Prepare a checked PCM WAV patch for Pythonlancer; no game DATA writes."""
import json
from pathlib import Path
import hashlib

ROOT = Path(__file__).resolve().parents[2]
SOURCE = Path('D:/Games/FL_MOD/Assets/Pythonlancer')
OUT = ROOT / 'out/voicestudio_pcm'


def replace_once(text, old, new, count=1):
    if text.count(old) != count:
        raise ValueError(f'Unexpected source shape for {old[:80]!r}')
    return text.replace(old, new)


def digest(data):
    return hashlib.sha256(data).hexdigest()


def main():
    files = {}

    def put(relative, content):
        if any(part.lower() == 'data' for part in Path(relative).parts):
            raise ValueError('This patch must not write DATA')
        target = OUT / 'payload' / relative
        target.parent.mkdir(parents=True, exist_ok=True)
        data = content.encode('utf-8')
        target.write_bytes(data)
        original = SOURCE / relative
        files[relative] = {'before': digest(original.read_bytes()) if original.exists() else None,
                           'after': digest(data)}

    text = (SOURCE / 'tools/voicestudio.py').read_text(encoding='utf-8')
    text = replace_once(text, 'import hashlib\n', 'import hashlib\nimport io\nimport wave\n')
    text = replace_once(text, "'response_format': 'mp3'", "'response_format': 'wav'")
    text = replace_once(text, '        return response.content\n', '        return cls._pcm_wav(response.content)\n')
    anchor = '    @classmethod\n    def trim_leading(cls, file_destination, thresh=-34, pad_ms=40, min_cut_ms=60):'
    text = replace_once(text, anchor, '''    @staticmethod
    def output_path(file_destination):
        return pathlib.Path(file_destination).with_suffix('.wav')

    @staticmethod
    def _pcm_wav(voice_bytes):
        # Reject MP3 (including MP3-in-WAV), raw PCM, empty/truncated responses.
        # Preserve the engine's sample rate and channels; store integer PCM16.
        try:
            with wave.open(io.BytesIO(voice_bytes), 'rb') as wav:
                channels, width, rate, frames, compression, _ = wav.getparams()
                samples = wav.readframes(frames)
        except (wave.Error, EOFError) as error:
            raise ValueError('VoiceStudio must return an uncompressed PCM WAV') from error
        if compression != 'NONE' or not frames or len(samples) != frames * channels * width:
            raise ValueError('VoiceStudio returned empty or truncated PCM WAV')
        segment = AudioSegment(data=samples, sample_width=width, frame_rate=rate, channels=channels)
        result = io.BytesIO()
        segment.set_sample_width(2).export(result, format='wav')
        return result.getvalue()

''' + anchor)
    text = replace_once(text, '        path = pathlib.Path(file_destination)\n        seg = AudioSegment.from_file(path)',
                         "        path = pathlib.Path(file_destination)\n        if any(part.lower() == 'data' for part in path.resolve().parts):\n            raise ValueError('Trimming source recordings cannot write DATA')\n        seg = AudioSegment.from_wav(path).set_sample_width(2)")
    text = replace_once(text, "seg[cut:].export(tmp, format='mp3', bitrate='128k')", "seg[cut:].export(tmp, format='wav')")
    text = replace_once(text, '''        path = pathlib.Path(file_destination)
        path.parent.mkdir(parents=True, exist_ok=True)
        path.write_bytes(voice_bytes)
        if trim_lead:
            cls.trim_leading(path)
''', '''        path = cls.output_path(file_destination)
        if any(part.lower() == 'data' for part in path.resolve().parts):
            raise ValueError('VoiceStudio writes source recordings only; use DataFolder for DATA')
        pcm_wav = cls._pcm_wav(voice_bytes)
        path.parent.mkdir(parents=True, exist_ok=True)
        path.write_bytes(pcm_wav)
        if trim_lead:
            cls.trim_leading(path)
        return path
''')
    text = replace_once(text, '        cls._write(\n', '        return cls._write(\n', count=4)
    put('tools/voicestudio.py', text)
    put('tools/voice_output.py', (Path(__file__).with_name('voice_output.py')).read_text(encoding='utf-8'))

    text = (SOURCE / 'tools/audio_folder.py').read_text(encoding='utf-8')
    text = replace_once(text, 'from tools.voice_api import VoiceApi\n', 'from tools.voice_api import VoiceApi\nfrom tools.voice_output import output_path\n')
    text = replace_once(text, '''            file_destination = sounds_path / f"{sound.name}.mp3"
            alt_file_destination = sounds_path / f"{sound.name}.wav"''', '''            file_destination = output_path(sounds_path / f"{sound.name}.mp3")
            alt_file_destination = file_destination.with_suffix('.mp3' if file_destination.suffix == '.wav' else '.wav')''', count=2)
    text = replace_once(text, '''    def generate_simple_sound(cls, file_destination, actor, line):
        if file_destination.exists():''', '''    def generate_simple_sound(cls, file_destination, actor, line):
        file_destination = output_path(file_destination)
        alternate = file_destination.with_suffix('.mp3' if file_destination.suffix == '.wav' else '.wav')
        if file_destination.exists() or alternate.exists():''')
    put('tools/audio_folder.py', text)

    text = (SOURCE / 'tools/audio_pilot.py').read_text(encoding='utf-8')
    text = replace_once(text, 'from tools.voice_api import VoiceApi\n', 'from tools.voice_api import VoiceApi\nfrom tools.voice_output import output_path\n')
    text = replace_once(text, "            file_destination = pilot_folder / line.get_subfolder() / f'{code}.mp3'", "            file_destination = output_path(pilot_folder / line.get_subfolder() / f'{code}.mp3')")
    text = replace_once(text, '            if skip and file_destination.exists():', "            alternate = file_destination.with_suffix('.mp3' if file_destination.suffix == '.wav' else '.wav')\n            if skip and (file_destination.exists() or alternate.exists()):")
    text = replace_once(text, '''                file_destination = pilots_folder / line.get_subfolder() / f'{code}.mp3'
                target_destination = audios_folder / f'{code}.mp3'
'''.rstrip(), '''                file_destination = output_path(pilots_folder / line.get_subfolder() / f'{code}.mp3')
                if not file_destination.exists():
                    alternate = file_destination.with_suffix('.mp3' if file_destination.suffix == '.wav' else '.wav')
                    if alternate.exists():
                        file_destination = alternate
                target_destination = audios_folder / file_destination.name''')
    put('tools/audio_pilot.py', text)

    text = (SOURCE / 'single.py').read_text(encoding='utf-8')
    text = replace_once(text, 'from files.writer import FileWriter\n', 'from files.writer import FileWriter\nfrom tools.voice_output import output_path\n')
    text = replace_once(text, '        file_name = f"{key}.mp3"', '        file_name = output_path(f"{key}.mp3").name')
    put('single.py', text)

    text = (SOURCE / 'managers/rpg_voice.py').read_text(encoding='utf-8')
    text = replace_once(text, 'from story.rpg.script import RpgScript\n', 'from story.rpg.script import RpgScript\nfrom tools.voice_output import output_path\n')
    text = replace_once(text, 'str(destination / (sound.name + ".mp3"))', 'str(output_path(destination / (sound.name + ".mp3")))')
    put('managers/rpg_voice.py', text)
    text = (SOURCE / 'docs/rpg_cutscenes.md').read_text(encoding='utf-8')
    text = text.replace('_vendor.mp3', '_vendor.wav').replace('_player.mp3', '_player.wav')
    start = text.index('Текущий голосовой backend Pythonlancer запрашивает MP3.')
    end = text.index('\n## Разделение обязанностей', start)
    text = text[:start] + '''VoiceStudio запрашивает WAV и сохраняет PCM16 WAV без MP3-кодирования.
Частота и число каналов сохраняются из ответа сервиса. Обрезка начальной
тишины также остаётся в PCM WAV. Существующие MP3/WAV автоматически
не конвертируются и не перезаписываются; их пропуск при повторном запуске
сохранён. Если нужен новый PCM-вариант старой записи, сначала уберите именно
её старый файл из папки генерации. Настройка Steos не менялась.
Упаковка игрового звука и расчёт таймингов выполняются позже через DataFolder.
''' + text[end:]
    put('docs/rpg_cutscenes.md', text)
    (OUT / 'manifest.json').write_text(json.dumps({'destination': str(SOURCE), 'files': files}, indent=2), encoding='utf-8')
    print(f'Staged {len(files)} PCM WAV changes in {OUT}; installed files unchanged')


if __name__ == '__main__':
    main()
