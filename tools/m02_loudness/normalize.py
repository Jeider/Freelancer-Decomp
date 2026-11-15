"""Match M02 dialogue to the median RU Reichman loudness; replace APPLY only."""
import argparse
from concurrent.futures import ThreadPoolExecutor
import csv
import hashlib
import json
from pathlib import Path
import re
import shutil
import statistics
import subprocess
import wave

import numpy as np

ROOT = Path(__file__).resolve().parents[2]
SOURCE = Path('D:/Games/FL_MOD/Assets/AUDIO_CUTSCENE_RU/M02')
APPLY = Path('D:/Games/FL_MOD/Assets/AUDIO_CUTSCENE_RU_APPLY/M02')
OUT = ROOT / 'out/m02_loudness'
PAYLOAD = OUT / 'M02'
FFMPEG = 'C:/ffmpeg/bin/ffmpeg.exe'
CEILING = -1.5
TOLERANCE = 0.06


def digest(path):
    return hashlib.sha256(path.read_bytes()).hexdigest()


def snapshot(folder):
    return {p.relative_to(folder).as_posix(): digest(p)
            for p in sorted(folder.rglob('*')) if p.is_file()}


def parameters(path):
    with wave.open(str(path), 'rb') as audio:
        params = audio.getparams()
        if params[:3] not in ((1, 2, 48000), (1, 3, 48000)) or params.comptype != 'NONE':
            raise ValueError(f'Unexpected source format: {path}: {params}')
        if len(audio.readframes(params.nframes)) != params.nframes * params.sampwidth:
            raise ValueError(f'Truncated WAV: {path}')
        return tuple(params)


def measure(path):
    result = subprocess.run([FFMPEG, '-hide_banner', '-nostdin', '-nostats',
                             '-threads', '1', '-i', str(path), '-af',
                             'loudnorm=I=-20:TP=-1.5:LRA=50:print_format=json',
                             '-f', 'null', '-'], capture_output=True, check=True)
    data = json.loads(re.findall(r'\{[^{}]*\}', result.stderr.decode())[-1])
    return {key: float(data[value]) for key, value in
            [('lufs', 'input_i'), ('true_peak_dbtp', 'input_tp'), ('lra', 'input_lra')]}


def samples(path):
    with wave.open(str(path), 'rb') as audio:
        width = audio.getsampwidth()
        raw = audio.readframes(audio.getnframes())
    if width == 2:
        return np.frombuffer(raw, dtype='<i2').astype(np.float64) / 32768
    octets = np.frombuffer(raw, dtype=np.uint8).reshape(-1, 3).astype(np.int32)
    values = octets[:, 0] | (octets[:, 1] << 8) | (octets[:, 2] << 16)
    values = (values ^ 0x800000) - 0x800000
    return values.astype(np.float64) / 8388608


def alignment(source, output):
    before, after = samples(source), samples(output)
    usable = len(before) // 1024 * 1024
    loudest = int(np.argmax(np.sum(before[:usable].reshape(-1, 1024) ** 2, axis=1))) * 1024
    start = min(max(32, loudest - 2048), len(before) - 4832)
    reference = before[start:start + 4800]
    scores = []
    for lag in range(-24, 25):
        window = after[start + lag:start + lag + 4800]
        score = float(np.dot(reference, window) / (np.linalg.norm(reference) * np.linalg.norm(window)))
        scores.append((score, lag))
    score, lag = max(scores)
    if lag != 0 or score < 0.95:
        raise ValueError(f'Unexpected waveform alignment: {source.name}: {lag} samples, r={score}')
    return {'lag_samples': lag, 'correlation': score}


def render(source, destination, gain, limited, ceiling):
    params = parameters(source)
    filters = [f'volume={gain:.8f}dB:precision=double']
    if limited:
        # Fourfold oversampling and compensated lookahead prevent sample shifts.
        filters = ['aresample=192000'] + filters + [
            f'alimiter=limit={10 ** (ceiling / 20):.10f}:attack=5:release=80:level=false:latency=true',
            'aresample=48000']
    codec, raw_format = ('pcm_s16le', 's16le') if params[1] == 2 else ('pcm_s24le', 's24le')
    result = subprocess.run([FFMPEG, '-hide_banner', '-loglevel', 'error', '-nostdin',
                             '-threads', '1', '-i', str(source), '-map', '0:a:0',
                             '-af', ','.join(filters), '-ar', '48000', '-ac', '1',
                             '-c:a', codec, '-f', raw_format, 'pipe:1'],
                            capture_output=True, check=True)
    if len(result.stdout) != params[3] * params[1]:
        raise ValueError(f'Filter changed sample count: {source.name}')
    with wave.open(str(destination), 'wb') as audio:
        audio.setparams(params)
        audio.writeframes(result.stdout)
    if parameters(destination) != params:
        raise ValueError(f'Output format/duration mismatch: {source.name}')


def normalize(item, target):
    name, before = item
    source, destination = SOURCE / name, PAYLOAD / name
    gain = target - before['lufs']
    limited = before['true_peak_dbtp'] + gain > CEILING - 0.05
    ceiling = CEILING - 0.10
    for attempt in range(1, 9):
        render(source, destination, gain, limited, ceiling)
        after = measure(destination)
        error = target - after['lufs']
        if abs(error) <= TOLERANCE and after['true_peak_dbtp'] <= CEILING:
            break
        gain += error
        if after['true_peak_dbtp'] + max(error, 0) > CEILING:
            if limited and after['true_peak_dbtp'] > CEILING:
                ceiling -= after['true_peak_dbtp'] - CEILING + 0.05
            limited = True
    else:
        raise ValueError(f'Could not match target: {name}: {after}')
    timing = alignment(source, destination)
    return {'file': name, 'before': before, 'after': after,
            'gain_db': round(gain, 4), 'peak_limiter': limited,
            'limiter_ceiling_dbtp': ceiling if limited else None,
            'iterations': attempt, 'parameters': parameters(destination),
            'alignment': timing, 'sha256': digest(destination)}


def prepare():
    if OUT.exists():
        raise ValueError(f'Refusing to overwrite existing experiment: {OUT}')
    source_snapshot, apply_snapshot = snapshot(SOURCE), snapshot(APPLY)
    if any(Path(name).suffix.lower() == '.mp3' for name in source_snapshot):
        raise ValueError('A new MP3 appeared; resolve MP3 priority before processing')
    names = sorted(name for name in source_snapshot if Path(name).suffix.lower() == '.wav')
    if any('/' in name for name in names):
        raise ValueError('Unexpected nested mission audio')
    for name in names:
        parameters(SOURCE / name)
    with ThreadPoolExecutor(max_workers=4) as pool:
        measurements = dict(zip(names, pool.map(measure, (SOURCE / name for name in names))))
    reference = {name: stats for name, stats in measurements.items() if name.endswith('_reichman.wav')}
    if not reference:
        raise ValueError('No Reichman references found')
    target = round(statistics.median(stats['lufs'] for stats in reference.values()), 2)
    PAYLOAD.mkdir(parents=True)
    (OUT / 'snapshots.json').write_text(json.dumps({'source': source_snapshot, 'apply': apply_snapshot}, indent=2), encoding='utf-8')
    print(f'Reference: {len(reference)} Reichman lines, median {target} LUFS. Normalizing {len(names)} files.', flush=True)
    with ThreadPoolExecutor(max_workers=4) as pool:
        rows = list(pool.map(lambda item: normalize(item, target), measurements.items()))
    if snapshot(SOURCE) != source_snapshot or snapshot(APPLY) != apply_snapshot:
        raise ValueError('Source/APPLY changed during staging')
    report = {'source': str(SOURCE), 'destination': str(APPLY),
              'target_lufs': target, 'reference_method': 'Median integrated LUFS of all 8 current Reichman lines',
              'reference': reference, 'maximum_true_peak_dbtp': CEILING,
              'processing': 'Constant per-file gain; oversampled lookahead limiter only where required',
              'summary': {'files': len(rows), 'limited_files': sum(r['peak_limiter'] for r in rows),
                          'before_lufs_range': [min(r['before']['lufs'] for r in rows), max(r['before']['lufs'] for r in rows)],
                          'after_lufs_range': [min(r['after']['lufs'] for r in rows), max(r['after']['lufs'] for r in rows)],
                          'after_max_true_peak_dbtp': max(r['after']['true_peak_dbtp'] for r in rows),
                          'max_loudness_error_lu': max(abs(r['after']['lufs'] - target) for r in rows),
                          'sample_counts_and_formats_preserved': True,
                          'waveform_alignment_verified': True,
                          'source_and_apply_unchanged_during_prepare': True}, 'files': rows}
    (OUT / 'report.json').write_text(json.dumps(report, indent=2), encoding='utf-8')
    with (OUT / 'levels.csv').open('w', newline='', encoding='utf-8-sig') as handle:
        writer = csv.writer(handle)
        writer.writerow(['file', 'before_LUFS', 'after_LUFS', 'gain_dB', 'limiter', 'after_dBTP'])
        for row in rows:
            writer.writerow([row['file'], row['before']['lufs'], row['after']['lufs'], row['gain_db'], row['peak_limiter'], row['after']['true_peak_dbtp']])
    print(json.dumps(report['summary'], indent=2))


def install():
    report = json.loads((OUT / 'report.json').read_text(encoding='utf-8'))
    snapshots = json.loads((OUT / 'snapshots.json').read_text(encoding='utf-8'))
    if snapshot(SOURCE) != snapshots['source'] or snapshot(APPLY) != snapshots['apply']:
        raise ValueError('Source/APPLY changed since preparation')
    for row in report['files']:
        source, target = (PAYLOAD / row['file']).resolve(), (APPLY / row['file']).resolve()
        if source.parent != PAYLOAD.resolve() or target.parent != APPLY.resolve():
            raise ValueError('File outside mission folder')
        if digest(source) != row['sha256'] or list(parameters(source)) != row['parameters']:
            raise ValueError(f'Staged file changed: {source}')
    backup = OUT / 'apply_before'
    backup.mkdir()
    for row in report['files']:
        name = row['file']
        if (APPLY / name).exists():
            shutil.copy2(APPLY / name, backup / name)
            if digest(backup / name) != snapshots['apply'][name]:
                raise ValueError(f'Backup failed: {name}')
    touched = []
    try:
        for row in report['files']:
            name = row['file']
            touched.append(name)
            shutil.copyfile(PAYLOAD / name, APPLY / name)
            if digest(APPLY / name) != row['sha256']:
                raise ValueError(f'Installed hash mismatch: {name}')
    except Exception:
        for name in reversed(touched):
            if (backup / name).exists():
                shutil.copy2(backup / name, APPLY / name)
        raise
    if snapshot(SOURCE) != snapshots['source']:
        raise ValueError('Originals changed during installation')
    expected = dict(snapshots['apply'])
    expected.update({row['file']: row['sha256'] for row in report['files']})
    if snapshot(APPLY) != expected:
        raise ValueError('Unexpected APPLY changes')
    (OUT / 'installed.json').write_text(json.dumps({'files': len(report['files']), 'destination': str(APPLY),
                                                   'source_unchanged': True, 'hashes_verified': True}, indent=2), encoding='utf-8')
    print(f'Updated and verified {len(report["files"])} current APPLY/M02 WAVs at {report["target_lufs"]} LUFS.')
    print('Original RU recordings unchanged. Existing APPLY files backed up in ' + str(backup))


if __name__ == '__main__':
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument('--install', action='store_true')
    args = parser.parse_args()
    install() if args.install else prepare()
