"""Convert RU recordings into a separate PCM16/48 kHz/mono WAV collection."""
import argparse
from collections import Counter, defaultdict
from concurrent.futures import ThreadPoolExecutor, as_completed
import hashlib
import json
from pathlib import Path
import shutil
import subprocess
import wave

ROOT = Path(__file__).resolve().parents[2]
SOURCE = Path('D:/Games/FL_MOD/Assets/AUDIO_CUTSCENE_RU')
DESTINATION = SOURCE.with_name('AUDIO_CUTSCENE_RU_PCM')
STAGE = ROOT / 'out/cutscene_ru_pcm'
PAYLOAD = STAGE / 'AUDIO_CUTSCENE_RU_PCM'
FFMPEG = 'C:/ffmpeg/bin/ffmpeg.exe'
FFPROBE = 'C:/ffmpeg/bin/ffprobe.exe'
RATE = 48000


def digest(path):
    return hashlib.sha256(path.read_bytes()).hexdigest()


def inventory():
    return {p.relative_to(SOURCE).as_posix(): digest(p)
            for p in sorted(SOURCE.rglob('*')) if p.is_file()}


def run(command, data=None):
    result = subprocess.run(command, input=data, capture_output=True, check=True)
    return result.stdout, result.stderr.decode('utf-8', errors='replace')


def validate_wav(path, frames):
    with wave.open(str(path), 'rb') as audio:
        if audio.getparams()[:4] != (1, 2, RATE, frames):
            raise ValueError(f'Wrong WAV parameters: {path}: {audio.getparams()}')
        if audio.getcomptype() != 'NONE' or len(audio.readframes(frames)) != frames * 2:
            raise ValueError(f'Truncated/compressed WAV: {path}')


def convert(relative):
    source = SOURCE / relative
    metadata, _ = run([FFPROBE, '-v', 'error', '-select_streams', 'a:0',
                       '-show_entries', 'stream=codec_name,sample_rate,channels',
                       '-of', 'json', str(source)])
    info = json.loads(metadata)['streams'][0]
    rate, channels = int(info['sample_rate']), int(info['channels'])
    # Decode once to float PCM to preserve precision before resampling/quantization.
    decoded, warnings = run([FFMPEG, '-hide_banner', '-loglevel', 'warning',
                             '-nostdin', '-threads', '1', '-i', str(source),
                             '-map', '0:a:0', '-vn', '-sn', '-dn',
                             '-c:a', 'pcm_f32le', '-f', 'f32le', 'pipe:1'])
    if not decoded or len(decoded) % (channels * 4):
        raise ValueError(f'Invalid decoded audio: {source}')
    input_frames = len(decoded) // (channels * 4)
    pcm, encode_warnings = run([FFMPEG, '-hide_banner', '-loglevel', 'warning',
                               '-nostdin', '-threads', '1', '-f', 'f32le',
                               '-ar', str(rate), '-ac', str(channels), '-i', 'pipe:0',
                               '-ar', str(RATE), '-ac', '1', '-c:a', 'pcm_s16le',
                               '-f', 's16le', 'pipe:1'], decoded)
    frames = len(pcm) // 2
    if not pcm or len(pcm) % 2 or abs(frames - input_frames * RATE / rate) > 1.01:
        raise ValueError(f'Decoded duration changed: {source}')
    output_relative = Path(relative).with_suffix('.wav').as_posix()
    output = PAYLOAD / output_relative
    output.parent.mkdir(parents=True, exist_ok=True)
    # A classic PCM WAV header, matching VoiceStudio's integer PCM container.
    with output.open('xb') as handle:
        with wave.open(handle, 'wb') as audio:
            audio.setparams((1, 2, RATE, 0, 'NONE', 'not compressed'))
            audio.writeframes(pcm)
    validate_wav(output, frames)
    return {'source': relative, 'output': output_relative,
            'source_codec': info['codec_name'], 'source_rate': rate,
            'source_channels': channels, 'decoded_source_frames': input_frames,
            'output_frames': frames, 'duration_seconds': frames / RATE,
            'duration_error_seconds': frames / RATE - input_frames / rate,
            'sha256': digest(output),
            'decoder_warnings': warnings.strip(), 'encoder_warnings': encode_warnings.strip()}


def prepare():
    if STAGE.exists():
        raise ValueError(f'Refusing to overwrite staging directory: {STAGE}')
    before = inventory()
    groups = defaultdict(list)
    non_audio = []
    for relative in before:
        if Path(relative).suffix.lower() in ('.mp3', '.wav'):
            groups[Path(relative).with_suffix('').as_posix().lower()].append(relative)
        else:
            non_audio.append(relative)
    selected, duplicates = [], []
    for variants in groups.values():
        variants.sort(key=lambda p: (Path(p).suffix.lower() != '.mp3', p))
        if len(variants) > 2 or len({Path(p).suffix.lower() for p in variants}) != len(variants):
            raise ValueError(f'Ambiguous filenames: {variants}')
        selected.append(variants[0])
        if len(variants) > 1:
            duplicates.append({'selected': variants[0], 'unused': variants[1:]})
    STAGE.mkdir(parents=True)
    (STAGE / 'source_snapshot.json').write_text(json.dumps(before, indent=2), encoding='utf-8')
    rows = []
    with ThreadPoolExecutor(max_workers=4) as workers:
        futures = [workers.submit(convert, relative) for relative in selected]
        for future in as_completed(futures):
            rows.append(future.result())
            if len(rows) % 100 == 0:
                print(f'Converted and checked {len(rows)}/{len(selected)}', flush=True)
    if inventory() != before:
        raise ValueError('Source collection changed during conversion; do not install')
    rows.sort(key=lambda row: row['output'])
    report = {'source': str(SOURCE), 'destination': str(DESTINATION),
              'format': {'codec': 'pcm_s16le', 'sample_rate': RATE, 'channels': 1, 'bits': 16},
              'normalization': False, 'trimming': False,
              'source_audio_files': sum(map(len, groups.values())),
              'output_audio_files': len(rows), 'mp3_priority_pairs': duplicates,
              'non_audio_not_converted': non_audio,
              'source_formats': dict(Counter(f"{r['source_codec']}/{r['source_rate']}/{r['source_channels']}" for r in rows)),
              'max_duration_error_seconds': max(abs(r['duration_error_seconds']) for r in rows),
              'source_hashes_unchanged': True, 'files': rows}
    (STAGE / 'conversion_report.json').write_text(json.dumps(report, indent=2), encoding='utf-8')
    print(json.dumps({key: value for key, value in report.items()
                      if key not in ('files', 'mp3_priority_pairs')}, indent=2))
    print(f'MP3 preferred for {len(duplicates)} pairs; ready to install into {DESTINATION}')


def install():
    report = json.loads((STAGE / 'conversion_report.json').read_text(encoding='utf-8'))
    before = json.loads((STAGE / 'source_snapshot.json').read_text(encoding='utf-8'))
    if DESTINATION.exists():
        raise ValueError(f'Refusing to overwrite existing directory: {DESTINATION}')
    if inventory() != before:
        raise ValueError('Source collection has changed since conversion')
    for row in report['files']:
        source = (PAYLOAD / row['output']).resolve()
        target = (DESTINATION / row['output']).resolve()
        if not source.is_relative_to(PAYLOAD.resolve()) or not target.is_relative_to(DESTINATION.resolve()):
            raise ValueError('Path outside collection')
        validate_wav(source, row['output_frames'])
        if digest(source) != row['sha256']:
            raise ValueError(f'Staged file changed: {source}')
    DESTINATION.mkdir()
    for row in report['files']:
        source = PAYLOAD / row['output']
        target = DESTINATION / row['output']
        target.parent.mkdir(parents=True, exist_ok=True)
        with source.open('rb') as src, target.open('xb') as dst:
            shutil.copyfileobj(src, dst)
        if digest(target) != row['sha256']:
            raise ValueError(f'Installed file mismatch: {target}')
    shutil.copyfile(STAGE / 'conversion_report.json', DESTINATION / 'conversion_report.json')
    if inventory() != before:
        raise ValueError('Source collection changed during installation')
    print(f'Installed and verified {len(report["files"])} PCM16/48000/mono WAVs: {DESTINATION}')
    print('Original collection hashes unchanged. No DATA or Pythonlancer configuration writes.')


if __name__ == '__main__':
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument('--install', action='store_true')
    args = parser.parse_args()
    install() if args.install else prepare()
