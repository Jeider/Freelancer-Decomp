"""Convert AUDIO_XML_RU in place to PCM16/48 kHz/mono, without backups."""
import argparse
from collections import Counter, defaultdict
from concurrent.futures import ThreadPoolExecutor, as_completed
import hashlib
import importlib.util
import json
from pathlib import Path
import shutil
import xml.etree.ElementTree as ET

ROOT = Path(__file__).resolve().parents[2]
SOURCE = Path('D:/Games/FL_MOD/Assets/AUDIO_XML_RU').resolve()
OUT = ROOT / 'out/xml_ru_pcm'
PAYLOAD = OUT / 'payload'

# Reuse the checked float decode -> PCM16 conversion and sample-count checks.
spec = importlib.util.spec_from_file_location('cutscene_pcm', ROOT / 'tools/cutscene_ru_pcm/convert.py')
pcm = importlib.util.module_from_spec(spec)
spec.loader.exec_module(pcm)
pcm.SOURCE = SOURCE
pcm.PAYLOAD = PAYLOAD


def digest(path):
    return hashlib.sha256(path.read_bytes()).hexdigest()


def inventory():
    return {p.relative_to(SOURCE).as_posix(): digest(p)
            for p in sorted(SOURCE.rglob('*')) if p.is_file()}


def inside(root, relative):
    path = (root / relative).resolve()
    if not path.is_relative_to(root.resolve()) or path == root.resolve():
        raise ValueError(f'Path outside collection: {path}')
    return path


def xml_references(expected_files):
    available = {name.lower() for name in expected_files}
    count = 0
    for path in SOURCE.rglob('*.xml'):
        if not path.is_file():
            continue
        for element in ET.parse(path).iter():
            if element.get('type') != 'file':
                continue
            reference = element.attrib['filename'].replace('\\', '/')
            target = (path.parent / reference).resolve()
            if not target.is_relative_to(SOURCE):
                raise ValueError(f'XML reference outside collection: {path}: {reference}')
            if target.relative_to(SOURCE).as_posix().lower() not in available:
                raise ValueError(f'Missing converted XML reference: {path}: {reference}')
            count += 1
    return count


def prepare():
    if OUT.exists():
        raise ValueError(f'Refusing to overwrite previous staging: {OUT}')
    before = inventory()
    groups = defaultdict(list)
    other = []
    for name in before:
        if Path(name).suffix.lower() in ('.mp3', '.wav'):
            groups[Path(name).with_suffix('').as_posix().lower()].append(name)
        else:
            other.append(name)
    selected, duplicates = [], []
    for variants in groups.values():
        variants.sort(key=lambda p: (Path(p).suffix.lower() != '.mp3', p))
        if len(variants) > 2 or len({Path(p).suffix.lower() for p in variants}) != len(variants):
            raise ValueError(f'Ambiguous filenames: {variants}')
        selected.append(variants[0])
        if len(variants) > 1:
            duplicates.append({'selected': variants[0], 'unused': variants[1:]})
    expected = other + [Path(name).with_suffix('.wav').as_posix() for name in selected]
    references = xml_references(expected)
    PAYLOAD.mkdir(parents=True)
    (OUT / 'source_snapshot.json').write_text(json.dumps(before, indent=2), encoding='utf-8')
    rows = []
    with ThreadPoolExecutor(max_workers=4) as workers:
        futures = [workers.submit(pcm.convert, name) for name in selected]
        for future in as_completed(futures):
            rows.append(future.result())
            if len(rows) % 200 == 0:
                print(f'Converted and checked {len(rows)}/{len(selected)}', flush=True)
    if inventory() != before:
        raise ValueError('Original collection changed while converting')
    rows.sort(key=lambda row: row['output'])
    report = {'source': str(SOURCE), 'destination': str(SOURCE), 'backup': False,
              'format': {'codec': 'pcm_s16le', 'sample_rate': 48000, 'channels': 1, 'bits': 16},
              'normalization': False, 'trimming': False,
              'audio_files': len(rows), 'mp3_priority_pairs': duplicates,
              'source_formats': dict(Counter(f"{r['source_codec']}/{r['source_rate']}/{r['source_channels']}" for r in rows)),
              'xml_files_unchanged': sum(Path(name).suffix.lower() == '.xml' for name in other),
              'xml_references_checked': references, 'other_files_unchanged': other,
              'remove_after_conversion': [name for name in before if Path(name).suffix.lower() == '.mp3'],
              'maximum_duration_error_seconds': max(abs(r['duration_error_seconds']) for r in rows),
              'originals_unchanged_during_staging': True, 'files': rows}
    (OUT / 'report.json').write_text(json.dumps(report, indent=2), encoding='utf-8')
    print(json.dumps({key: value for key, value in report.items()
                      if key not in ('files', 'remove_after_conversion', 'other_files_unchanged')}, indent=2))
    print(f'Ready to replace audio in place; {len(report["remove_after_conversion"])} MP3 files will be removed after WAV verification.')


def install():
    report = json.loads((OUT / 'report.json').read_text(encoding='utf-8'))
    before = json.loads((OUT / 'source_snapshot.json').read_text(encoding='utf-8'))
    if inventory() != before:
        raise ValueError('Original collection changed since conversion')
    for row in report['files']:
        staged = inside(PAYLOAD, row['output'])
        target = inside(SOURCE, row['output'])
        pending = target.with_name(target.name + '.pcm-pending')
        if pending.exists():
            raise ValueError(f'Existing temporary file: {pending}')
        pcm.validate_wav(staged, row['output_frames'])
        if digest(staged) != row['sha256']:
            raise ValueError(f'Staged file changed: {staged}')
    # All deletions are explicit source MP3 files verified inside the named root.
    for name in report['remove_after_conversion']:
        path = inside(SOURCE, name)
        if path.suffix.lower() != '.mp3' or digest(path) != before[name]:
            raise ValueError(f'Invalid source removal: {path}')
    for row in report['files']:
        staged, target = inside(PAYLOAD, row['output']), inside(SOURCE, row['output'])
        pending = target.with_name(target.name + '.pcm-pending')
        if not pending.resolve().is_relative_to(SOURCE):
            raise ValueError('Temporary path outside collection')
        with staged.open('rb') as src, pending.open('xb') as dst:
            shutil.copyfileobj(src, dst)
        if digest(pending) != row['sha256']:
            raise ValueError(f'Temporary copy mismatch: {pending}')
        pending.replace(target)
        if digest(target) != row['sha256']:
            raise ValueError(f'Installed file mismatch: {target}')
    # Keep compressed inputs until every replacement has been verified.
    for name in report['remove_after_conversion']:
        path = inside(SOURCE, name)
        if digest(path) != before[name]:
            raise ValueError(f'MP3 changed during installation: {path}')
        path.unlink()
    expected = {name: before[name] for name in report['other_files_unchanged']}
    expected.update({row['output']: row['sha256'] for row in report['files']})
    if inventory() != expected:
        raise ValueError('Unexpected final collection contents')
    references = xml_references(expected)
    receipt = {'destination': str(SOURCE), 'pcm_wavs': len(report['files']),
               'removed_mp3s': len(report['remove_after_conversion']),
               'verified_xml_references': references, 'backups_created': False,
               'all_file_hashes_verified': True}
    (OUT / 'installed.json').write_text(json.dumps(receipt, indent=2), encoding='utf-8')
    print(json.dumps(receipt, indent=2))


if __name__ == '__main__':
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument('--install', action='store_true')
    args = parser.parse_args()
    install() if args.install else prepare()
