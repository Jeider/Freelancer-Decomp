"""Normalize the current RU APPLY collection using the original M02 reference."""
import argparse
from collections import Counter
from concurrent.futures import ThreadPoolExecutor, as_completed
import csv
from datetime import datetime
import json
import math
from pathlib import Path
import shutil
import statistics

import numpy as np

import normalize as audio

TOPIC = audio.OUT
ORIGINALS = audio.SOURCE.parent
APPLY = audio.APPLY.parent
RUNS = TOPIC / 'all_apply'
PEAK_WINDOW_ALIGNMENT = audio.alignment


def verify_alignment(source, output):
    try:
        peak_result = PEAK_WINDOW_ALIGNMENT(source, output)
        if peak_result['correlation'] >= 0.999:
            return peak_result
        peak_check = f'Peak window affected by limiting: {peak_result}'
    except ValueError as exc:
        peak_check = str(exc)
    # A varying limiter gain can move the correlation maximum in the loudest
    # window without moving samples. Confirm timing on multiple unaffected
    # speech windows, still rejecting even a one-sample actual delay.
    before, after = audio.samples(source), audio.samples(output)
    if len(before) != len(after):
        raise ValueError(f'Sample count changed: {source}')
    verified = []
    audible = max(0.0001, float(np.sqrt(np.mean(before ** 2))) * 0.05)
    for start in np.linspace(32, len(before) - 4832, 13, dtype=int):
        reference = before[start:start + 4800]
        if float(np.sqrt(np.mean(reference ** 2))) < audible:
            continue
        scores = []
        for lag in range(-24, 25):
            window = after[start + lag:start + lag + 4800]
            denominator = float(np.linalg.norm(reference) * np.linalg.norm(window))
            score = float(np.dot(reference, window)) / denominator if denominator else 0.0
            scores.append((score, lag))
        score, lag = max(scores)
        if score < 0.999:
            continue
        if lag != 0:
            raise ValueError(f'Unprocessed speech window shifted: {source}: {lag} samples')
        if score - max(value for value, offset in scores if offset != 0) > 0.000001:
            verified.append({'start_sample': int(start), 'correlation': score})
    if len(verified) < 3:
        raise ValueError(f'Insufficient unaffected windows to verify timing: {source}')
    return {'lag_samples': 0, 'correlation': min(row['correlation'] for row in verified),
            'method': 'Multiple unaffected speech windows', 'windows': verified,
            'peak_window_check': peak_check}


def save(path, value):
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_text(json.dumps(value, indent=2, ensure_ascii=False), encoding='utf-8')


def read(path):
    return json.loads(path.read_text(encoding='utf-8'))


def safe_path(root, name):
    path = (root / name).resolve()
    if not path.is_relative_to(root.resolve()) or path == root.resolve():
        raise ValueError(f'Path outside expected directory: {name}')
    return path


def unchanged(snapshots):
    if audio.snapshot(ORIGINALS) != snapshots['originals']:
        raise ValueError('Original RU recordings changed since preparation')
    if audio.snapshot(APPLY) != snapshots['apply']:
        raise ValueError('Current APPLY collection changed since preparation')


def prepare(run):
    run.mkdir(parents=True, exist_ok=True)
    if not (run / 'snapshots.json').exists():
        previous = read(TOPIC / 'report.json')
        previous_hashes = read(TOPIC / 'snapshots.json')['source']
        reference = {}
        for name in previous['reference']:
            path = ORIGINALS / 'M02' / name
            if audio.digest(path) != previous_hashes[name]:
                raise ValueError(f'Original Reichman reference changed: {name}')
            reference[name] = audio.measure(path)
        target = round(statistics.median(row['lufs'] for row in reference.values()), 2)
        if target != previous['target_lufs']:
            raise ValueError('Reference target differs from the previous M02 pass')
        save(run / 'reference.json', {'target_lufs': target, 'reference': reference,
                                     'original_reference_hashes_verified': True})
        save(run / 'snapshots.json', {'originals': audio.snapshot(ORIGINALS),
                                     'apply': audio.snapshot(APPLY)})
    snapshots = read(run / 'snapshots.json')
    unchanged(snapshots)
    reference = read(run / 'reference.json')
    target = reference['target_lufs']
    names = sorted(name for name in snapshots['apply'] if Path(name).suffix.lower() == '.wav')
    if any(Path(name).suffix.lower() in ('.mp3', '.flac', '.ogg', '.m4a')
           for name in snapshots['apply']):
        raise ValueError('Non-WAV audio needs an explicit format/duplicate policy')
    if not names:
        raise ValueError('No WAV files in APPLY')
    for name in names:
        audio.parameters(safe_path(APPLY, name))
    print(f'Run: {run}\nTarget: {target} LUFS; {len(names)} current APPLY WAVs', flush=True)
    if not (run / 'measurements.json').exists():
        measurements = {}
        with ThreadPoolExecutor(max_workers=4) as pool:
            jobs = {pool.submit(audio.measure, APPLY / name): name for name in names}
            for job in as_completed(jobs):
                name = jobs[job]
                measurements[name] = job.result()
                if not all(math.isfinite(value) for value in measurements[name].values()):
                    raise ValueError(f'Non-finite input loudness: {name}')
                if len(measurements) % 100 == 0 or len(measurements) == len(names):
                    print(f'Measured {len(measurements)}/{len(names)}', flush=True)
        save(run / 'measurements.json', measurements)
    measurements = read(run / 'measurements.json')
    audio.SOURCE = APPLY
    audio.PAYLOAD = run / 'payload'
    audio.alignment = verify_alignment

    def process(name):
        result_path = safe_path(run / 'results', name + '.json')
        output = safe_path(audio.PAYLOAD, name)
        if result_path.exists():
            row = read(result_path)
            if audio.digest(output) != row['sha256']:
                raise ValueError(f'Staged result changed: {name}')
            if row.get('validation_version') != 2:
                row['alignment'] = verify_alignment(APPLY / name, output)
                row['validation_version'] = 2
                save(result_path, row)
            return row
        output.parent.mkdir(parents=True, exist_ok=True)
        before = measurements[name]
        if abs(before['lufs'] - target) <= audio.TOLERANCE and before['true_peak_dbtp'] <= audio.CEILING:
            shutil.copy2(APPLY / name, output)
            row = {'file': name, 'before': before, 'after': before, 'gain_db': 0,
                   'peak_limiter': False, 'limiter_ceiling_dbtp': None, 'iterations': 0,
                   'parameters': audio.parameters(output),
                   'alignment': {'lag_samples': 0, 'correlation': 1.0},
                   'sha256': audio.digest(output)}
        else:
            row = audio.normalize((name, before), target)
        row['changed'] = row['sha256'] != snapshots['apply'][name]
        row['validation_version'] = 2
        save(result_path, row)
        return row

    rows, errors = [], []
    with ThreadPoolExecutor(max_workers=4) as pool:
        jobs = {pool.submit(process, name): name for name in names}
        for job in as_completed(jobs):
            try:
                rows.append(job.result())
            except Exception as exc:
                errors.append({'file': jobs[job], 'error': str(exc)})
                print(f'FAILED {jobs[job]}: {exc}', flush=True)
            done = len(rows) + len(errors)
            if done % 50 == 0 or done == len(names):
                print(f'Prepared and verified {done}/{len(names)}; errors={len(errors)}', flush=True)
    if errors:
        save(run / 'errors.json', errors)
        raise ValueError(f'{len(errors)} files failed; APPLY was not modified. Resume with --resume {run}')
    save(run / 'errors.json', [])
    unchanged(snapshots)
    rows.sort(key=lambda row: row['file'])
    summary = {
        'files': len(rows), 'changed_files': sum(row['changed'] for row in rows),
        'already_matched_files': sum(not row['changed'] for row in rows),
        'limited_files': sum(row['peak_limiter'] for row in rows),
        'by_mission': dict(sorted(Counter(Path(row['file']).parts[0] for row in rows).items())),
        'before_lufs_range': [min(row['before']['lufs'] for row in rows), max(row['before']['lufs'] for row in rows)],
        'after_lufs_range': [min(row['after']['lufs'] for row in rows), max(row['after']['lufs'] for row in rows)],
        'after_max_true_peak_dbtp': max(row['after']['true_peak_dbtp'] for row in rows),
        'max_loudness_error_lu': max(abs(row['after']['lufs'] - target) for row in rows),
        'sample_counts_and_formats_preserved': True, 'waveform_alignment_verified': True,
        'originals_and_apply_unchanged_during_prepare': True,
    }
    report = {'source_and_destination': str(APPLY), **reference,
              'maximum_true_peak_dbtp': audio.CEILING,
              'processing': 'Same M02 constant gain and oversampled peak limiter; already matched audio is copied byte-for-byte',
              'summary': summary, 'files': rows}
    save(run / 'report.json', report)
    with (run / 'levels.csv').open('w', newline='', encoding='utf-8-sig') as handle:
        writer = csv.writer(handle)
        writer.writerow(['file', 'before_LUFS', 'after_LUFS', 'gain_dB', 'limiter', 'after_dBTP', 'changed'])
        for row in rows:
            writer.writerow([row['file'], row['before']['lufs'], row['after']['lufs'],
                             row['gain_db'], row['peak_limiter'], row['after']['true_peak_dbtp'], row['changed']])
    save(TOPIC / 'latest_all_apply.json', {'run': str(run), 'status': 'prepared'})
    print(json.dumps(summary, indent=2), flush=True)
    print(f'Install: python -B tools/m02_loudness/normalize_all.py --install "{run}"', flush=True)


def install(run):
    if (run / 'installed.json').exists():
        raise ValueError('This run is already installed')
    report = read(run / 'report.json')
    snapshots = read(run / 'snapshots.json')
    if report['source_and_destination'] != str(APPLY):
        raise ValueError('Unexpected destination in report')
    unchanged(snapshots)
    rows = report['files']
    expected_names = {name for name in snapshots['apply'] if Path(name).suffix.lower() == '.wav'}
    if len(rows) != len(expected_names) or {row['file'] for row in rows} != expected_names:
        raise ValueError('Incomplete prepared collection')
    for row in rows:
        source = safe_path(run / 'payload', row['file'])
        target = safe_path(APPLY, row['file'])
        if audio.digest(source) != row['sha256'] or list(audio.parameters(source)) != row['parameters']:
            raise ValueError(f'Staged output changed: {source}')
        if list(audio.parameters(target)) != row['parameters']:
            raise ValueError(f'Input/output format or sample count mismatch: {target}')
        if abs(row['after']['lufs'] - report['target_lufs']) > audio.TOLERANCE or row['after']['true_peak_dbtp'] > audio.CEILING:
            raise ValueError(f'Staged output does not meet target: {source}')
    changed = [row for row in rows if row['changed']]
    backup = run / 'apply_before'
    backup.mkdir()
    for row in changed:
        name = row['file']
        saved = safe_path(backup, name)
        saved.parent.mkdir(parents=True, exist_ok=True)
        shutil.copy2(APPLY / name, saved)
        if audio.digest(saved) != snapshots['apply'][name]:
            raise ValueError(f'Backup verification failed: {name}')
    unchanged(snapshots)
    touched = []
    try:
        for row in changed:
            name = row['file']
            if audio.digest(APPLY / name) != snapshots['apply'][name]:
                raise ValueError(f'File changed immediately before installation: {name}')
            touched.append(name)
            shutil.copyfile(run / 'payload' / name, APPLY / name)
            if audio.digest(APPLY / name) != row['sha256']:
                raise ValueError(f'Installed hash mismatch: {name}')
        expected = dict(snapshots['apply'])
        expected.update({row['file']: row['sha256'] for row in rows})
        if audio.snapshot(APPLY) != expected:
            raise ValueError('Unexpected APPLY content after installation')
        if audio.snapshot(ORIGINALS) != snapshots['originals']:
            raise ValueError('Original RU recordings changed during installation')
    except Exception:
        for name in reversed(touched):
            shutil.copy2(backup / name, APPLY / name)
            if audio.digest(APPLY / name) != snapshots['apply'][name]:
                raise RuntimeError(f'Rollback hash mismatch: {name}')
        raise
    save(run / 'installed.json', {'destination': str(APPLY), 'verified_files': len(rows),
                                 'updated_files': len(changed), 'target_lufs': report['target_lufs'],
                                 'originals_unchanged': True, 'hashes_verified': True, 'backup': str(backup)})
    save(TOPIC / 'latest_all_apply.json', {'run': str(run), 'status': 'installed'})
    print(f'Installed {len(changed)} changed WAVs; all {len(rows)} APPLY WAVs verified at {report["target_lufs"]} LUFS.', flush=True)
    print(f'Originals unchanged. Backup: {backup}', flush=True)


if __name__ == '__main__':
    parser = argparse.ArgumentParser(description=__doc__)
    mode = parser.add_mutually_exclusive_group()
    mode.add_argument('--resume', type=Path)
    mode.add_argument('--install', type=Path)
    args = parser.parse_args()
    run = (args.install or args.resume or RUNS / datetime.now().strftime('%Y%m%d_%H%M%S_%f')).resolve()
    if not run.is_relative_to(RUNS.resolve()) or run == RUNS.resolve():
        parser.error('Run directory must be under out/m02_loudness/all_apply')
    install(run) if args.install else prepare(run)
