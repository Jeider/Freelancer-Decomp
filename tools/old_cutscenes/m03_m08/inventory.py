"""Select M03-M08 authoring work strictly through master AddRTC references."""
import ast
from collections import Counter
import hashlib
import json
from pathlib import Path
import re
import shutil
import subprocess
import sys
from types import SimpleNamespace

REPO = Path(__file__).resolve().parents[3]
GAME = Path('D:/Games/FL_MOD')
PL = GAME / 'Assets/Pythonlancer'
OUT = REPO / 'out/story_cutscenes/m03_m08'
GIT = ['git', '-c', f'safe.directory={GAME.as_posix()}', '-C', str(GAME)]
sys.path.insert(0, str(REPO / 'tools/berlin_cutscene'))
sys.path.insert(0, str(REPO / 'tools/m02_m08_cutscenes'))
import read_source
from binary import read_binary


def sha(data):
    return hashlib.sha256(data).hexdigest()


def entries(text):
    for number, raw in enumerate(text.splitlines(), 1):
        line = raw.split(';', 1)[0].strip()
        if '=' in line:
            key, value = line.split('=', 1)
            yield number, key.strip().lower(), value.strip()


def main():
    assert shutil.disk_usage(REPO).free > 2 * 1024**3
    OUT.mkdir(parents=True, exist_ok=True)
    commit = subprocess.check_output(GIT + ['rev-parse', 'master'], text=True).strip()
    paths = subprocess.check_output(GIT + ['ls-tree', '-r', '--name-only', commit], text=True).splitlines()
    lookup = {p.lower(): p for p in paths}

    def read(path):
        return subprocess.check_output(GIT + ['show', f'{commit}:{lookup[path.lower()]}'])

    def resolve(relative):
        relative = relative.replace('\\', '/')
        return next(lookup[p.lower()] for p in ('Assets/Pythonlancer/templates/' + relative, 'DATA/' + relative)
                    if p.lower() in lookup)

    scenes, excluded, rtc_refs, scripts = {}, [], [], {}
    native = {}
    for mission in range(3, 9):
        master_script_path = f'Assets/Pythonlancer/story/scripts/mission{mission}.py'
        script = read(master_script_path)
        (OUT / f'master_mission{mission}.py').write_bytes(script)
        scripts[str(mission)] = {'path': master_script_path, 'sha256': sha(script)}
        # Protect already authored native classes, including the two M08 scenes
        # added after master. The previous reconstructed imports are the targets.
        working = ast.parse((PL / f'story/scripts/main/mission{mission}.py').read_text(encoding='utf-8-sig'))
        for cls in working.body:
            if not isinstance(cls, ast.ClassDef):
                continue
            for statement in cls.body:
                if isinstance(statement, ast.Assign) and isinstance(statement.value, ast.Attribute):
                    if any(isinstance(t, ast.Name) and t.id.startswith('THORN') for t in statement.targets):
                        if statement.value.attr != 'ReconstructedScene':
                            native[f'{mission}:{cls.name}:{statement.targets[0].id}'] = ast.unparse(statement.value)
        mission_path = resolve(f'missions/m{mission:02}/m{mission:02}.ini')
        text = read(mission_path).decode('utf-8-sig')
        references = [(n, v.split(',')[0].strip()) for n, k, v in entries(text) if k == 'act_addrtc']
        for n, line in enumerate(text.splitlines(), 1):
            if line.lstrip().startswith(';'):
                continue
            match = re.search(r"rtc\.add\(['\"]([^'\"]+)", line)
            if match:
                references.append((n, f'missions/m{mission:02}/{match[1]}.ini'))
        for line, reference in references:
            rtc_path = resolve(reference)
            rtc = read(rtc_path).decode('utf-8-sig')
            rtc_refs.append({'mission': mission, 'mission_path': mission_path, 'line': line, 'rtc': rtc_path})
            for number, role, thn in entries(rtc):
                if role not in ('action', 'offer', 'accept', 'decision', 'reject', 'fidget') or '.thn' not in thn.lower():
                    continue
                relative = thn.replace('\\', '/')
                proof = dict(mission=mission, mission_path=mission_path, line=line, rtc=rtc_path,
                             rtc_line=number, role=role, thn=thn)
                if not relative.lower().startswith('scripts/mod/'):
                    excluded.append(dict(proof, reason='native/generated/shared/null RTC content'))
                    continue
                path = resolve(relative)
                name = Path(path).stem.lower()
                item = scenes.setdefault(name, {'name': name, 'source': path, 'uses': []})
                item['uses'].append(proof)
    for name, item in scenes.items():
        raw = read(item['source'])
        read_source.SOURCE = SimpleNamespace(read_text=lambda **kw: raw.decode('utf-8-sig'))
        data = read_binary(raw) if raw.startswith(b'\x1bLua') else read_source.read()
        item.update(sha256=sha(raw), duration=data['duration'], events=len(data['events']),
                    types=dict(Counter(e[1] for e in data['events'])))
        folder = OUT / name
        folder.mkdir(exist_ok=True)
        (folder / 'source.json').write_text(json.dumps(data, indent=2), encoding='utf-8')
        old_report = REPO / f'tools/m02_m08_cutscenes/bundle/{name}/report.json'
        item['prior_report_same_source'] = old_report.exists() and json.loads(old_report.read_text())['sha256'] == item['sha256']
        current = PL / f'story/cutscenes/story_scenes/{name}.py'
        item['working_scene_sha256'] = sha(current.read_bytes()) if current.exists() else None
        voices = [e for e in data['events'] if e[1] == 'START_SOUND' and re.match('DX_m', e[2][0], re.I)]
        item['voice_count'] = len(voices)
        print(f'{name}: {len(voices)} voices, {len(data["events"])} events; prior source match={item["prior_report_same_source"]}')
    result = dict(commit=commit, selection='master AddRTC / rtc.add only; no CallThorn',
                  scripts=scripts, rtc_references=rtc_refs, scenes=scenes, excluded=excluded, protected_native=native)
    (OUT / 'inventory.json').write_text(json.dumps(result, indent=2), encoding='utf-8')
    print(f'Selected {len(scenes)} scenes via {len(rtc_refs)} RTC references; native bindings: {native}')


if __name__ == '__main__':
    main()
