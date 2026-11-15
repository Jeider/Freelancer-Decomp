"""Trace mission RTC/CallThorn references, preferring the authored templates."""
import collections
import importlib.util
import json
from pathlib import Path
import re
import sys

ROOT = Path(__file__).resolve().parent
GAME = Path('D:/Games/FL_MOD')
PL = GAME / 'Assets/Pythonlancer'
DATA = GAME / 'DATA'
OUT = ROOT / 'bundle'
sys.path.insert(0, str(ROOT.parent / 'berlin_cutscene'))
import read_source
from binary import read_binary

def entries(path):
    for num, line in enumerate(path.read_text(encoding='utf-8-sig').splitlines(), 1):
        line = line.split(';', 1)[0].strip()
        if '=' in line:
            key, value = line.split('=', 1)
            yield num, key.strip().lower(), value.strip()

def resolve(relative):
    relative = relative.replace('\\', '/')
    template = PL / 'templates' / relative
    return template if template.exists() else DATA / relative

def collect():
    scenes = {}
    excluded = []
    for mission in range(2, 9):
        source = resolve(f'missions/m{mission:02}/m{mission:02}.ini')
        references = list(entries(source))
        for num, text in enumerate(source.read_text(encoding='utf-8-sig').splitlines(), 1):
            if text.lstrip().startswith(';'):
                continue
            match = re.search(r"rtc\.add\(['\"]([^'\"]+)", text)
            if match:
                references.append((num, 'act_addrtc', f'missions/m{mission:02}/{match[1]}.ini'))
        for line, key, value in references:
            if key not in ('act_addrtc', 'act_callthorn'):
                continue
            ref = value.split(',')[0].strip()
            links = [(source, line, key, ref)]
            if key == 'act_addrtc':
                rtc = resolve(ref)
                if not rtc.exists():
                    raise FileNotFoundError(rtc)
                links = [(rtc, n, k, v) for n,k,v in entries(rtc)
                         if k in ('action','offer','accept','decision','reject','fidget') and '.thn' in v.lower()]
            for file, num, role, thn in links:
                proof = dict(mission=mission, mission_file=str(source), mission_line=line,
                             reference=str(file), line=num, role=role, thn=thn)
                if '/generated/' in thn.replace('\\','/') or '/extras/' in thn.replace('\\','/'):
                    excluded.append(proof)
                    continue
                target = resolve(thn)
                name = target.stem.lower()
                item = scenes.setdefault(name, dict(name=name, source=str(target), uses=[]))
                item['uses'].append(proof)
    return scenes, excluded

def main():
    OUT.mkdir(parents=True, exist_ok=True)
    scenes, excluded = collect()
    counts = collections.Counter()
    for name, item in scenes.items():
        try:
            read_source.SOURCE = Path(item['source'])
            raw = Path(item['source']).read_bytes()
            data = read_binary(raw) if raw.startswith(b'\x1bLua') else read_source.read()
            item['duration'] = data['duration']
            item['events'] = len(data['events'])
            item['types'] = dict(collections.Counter(e[1] for e in data['events']))
            counts.update(item['types'])
            folder = OUT / name
            folder.mkdir(exist_ok=True)
            (folder / 'source.json').write_text(json.dumps(data, indent=2), encoding='utf-8')
        except Exception as exc:
            item['error'] = str(exc)
        print(name, item.get('events'), item.get('error',''))
    (OUT / 'inventory.json').write_text(json.dumps(dict(scenes=scenes, excluded=excluded), indent=2), encoding='utf-8')
    print('SCENES', len(scenes), 'TYPES', counts)

if __name__ == '__main__':
    main()
