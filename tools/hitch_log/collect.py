"""Snapshot automatic logs and rank observed resources for future preloading."""
import argparse
import csv
import hashlib
import io
import json
import math
import os
from pathlib import Path

ROOT = Path(__file__).resolve().parents[2]
RESOURCE_CATEGORIES = {'model_load', 'texture', 'room_texture', 'sound_load',
                       'sound_stream', 'voice_archive', 'shader'}


def collect(source, destination):
    captures = destination / 'captures'
    captures.mkdir(parents=True, exist_ok=True)
    for path in sorted(source.glob('hitches_*.csv')):
        # Bound the read to the size at open; never chase a growing live log.
        with path.open('rb') as f:
            data = f.read(os.fstat(f.fileno()).st_size)
        # The writer can be in the middle of a row. Preserve only complete rows.
        data = data[:data.rfind(b'\n') + 1]
        if not data:
            continue
        session = path.stem.rsplit('_', 1)[0]
        digest = hashlib.sha256(data).hexdigest()[:16]
        target = captures / f'{session}__{digest}.csv'
        if not target.exists():
            target.write_bytes(data)

    events = {}
    sessions = set()
    for path in sorted(captures.glob('*.csv')):
        session = path.stem.split('__', 1)[0]
        sessions.add(session)
        for row in csv.DictReader(io.StringIO(path.read_text(encoding='utf8', errors='replace'))):
            try:
                event = {k: row[k] for k in ('thread', 'frame', 'category', 'resource')}
                if any(v is None for v in event.values()):
                    continue
                event.update({k: float(row[k]) for k in ('start_ms', 'end_ms', 'duration_ms')})
                event['session'] = session
            except (ValueError, TypeError, KeyError):
                continue
            if event['category'] not in RESOURCE_CATEGORIES | {'frame', 'phase'}:
                continue
            # Repeated snapshots/rotated parts must not inflate the counts.
            key = (session, *(row[k] for k in ('start_ms', 'end_ms', 'thread', 'category', 'resource')))
            events[key] = event

    frames = {(e['session'], e['frame'], e['thread']): e for e in events.values() if e['category'] == 'frame'}
    groups = {}
    for event in events.values():
        if event['category'] not in RESOURCE_CATEGORIES:
            continue
        # Opaque voice member IDs require an owning archive before becoming a
        # usable preload key. Do not merge them across independent sessions.
        opaque = event['resource'].lower().startswith('0x')
        key = (event['category'], event['resource'], event['session'] if opaque else '')
        group = groups.setdefault(key, dict(category=key[0], resource=key[1],
            requires_archive_resolution=opaque, observed_count=0, total_ms=0.0,
            max_ms=0.0, slow_main_frame_count=0, max_associated_frame_ms=0.0,
            sessions=set(), durations=[], slow_frames=set()))
        group['observed_count'] += 1
        group['total_ms'] += event['duration_ms']
        group['max_ms'] = max(group['max_ms'], event['duration_ms'])
        group['durations'].append(event['duration_ms'])
        group['sessions'].add(event['session'])
        frame = frames.get((event['session'], event['frame'], event['thread']))
        if frame and event['start_ms'] < frame['end_ms'] and event['end_ms'] > frame['start_ms']:
            group['slow_frames'].add((event['session'], event['frame']))
            group['max_associated_frame_ms'] = max(group['max_associated_frame_ms'], frame['duration_ms'])
    resources = []
    for group in groups.values():
        durations = sorted(group.pop('durations'))
        group['p95_ms'] = durations[math.ceil(.95 * len(durations)) - 1]
        group['slow_main_frame_count'] = len(group.pop('slow_frames'))
        group['sessions'] = sorted(group['sessions'])
        resources.append(group)
    resources.sort(key=lambda r: r['total_ms'], reverse=True)
    report = dict(sessions=sorted(sessions), resource_timings_threshold_ms=1,
        location_context_available=False,
        notes=['Only measured scopes >=1 ms are recorded, not all load calls.',
               'Times are inclusive. Categories must not be summed together.',
               'A resource in a slow frame is a candidate, not proof of its cause.',
               'Startup/system-loading phases are not yet separated from flight.',
               'Shader scopes include cache access; they do not prove compilation.',
               'Present delays require separate investigation; resource caching may not fix them.'],
        resources=resources)
    (destination / 'resources.json').write_text(json.dumps(report, indent=2, ensure_ascii=False), encoding='utf8')
    fields = ['category', 'resource', 'observed_count', 'total_ms', 'max_ms', 'p95_ms',
              'slow_main_frame_count', 'max_associated_frame_ms', 'requires_archive_resolution']
    with (destination / 'resources.csv').open('w', newline='', encoding='utf-8-sig') as f:
        writer = csv.DictWriter(f, fields, extrasaction='ignore')
        writer.writeheader()
        writer.writerows(resources)
    print(f'Saved {len(sessions)} sessions, {len(resources)} resource entries: {destination}')
    print('Repeated resource scopes (>=1 ms), excluding shader/cache requests:')
    for r in [r for r in resources if r['observed_count'] > 1 and r['category'] != 'shader'][:12]:
        print(f"  {r['observed_count']:3}x {r['total_ms']:8.2f} ms total; max {r['max_ms']:7.2f} ms: {r['resource']}")
    return report


if __name__ == '__main__':
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument('--source', type=Path, default=Path(os.environ['LOCALAPPDATA'])/'Freelancer-Decomp/Diagnostics')
    parser.add_argument('--output', type=Path, default=ROOT/'src/obj/hitch_log/collected')
    args = parser.parse_args()
    collect(args.source, args.output)
