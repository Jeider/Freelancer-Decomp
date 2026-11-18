"""Compare existing M02/M08 native scenes before and after the API extension."""
import argparse
import importlib
import importlib.util
import json
import os
import sys
from types import SimpleNamespace
from inventory import OUT, PL, sha

parser = argparse.ArgumentParser(description=__doc__)
parser.add_argument('--staged', action='store_true')
args = parser.parse_args()
sys.path.insert(0, str(PL))
os.chdir(PL)
if args.staged:
    for mod in ('content', 'scene'):
        spec = importlib.util.spec_from_file_location('story.cutscenes.' + mod, OUT / f'api/story/cutscenes/{mod}.py')
        module = importlib.util.module_from_spec(spec)
        sys.modules[spec.name] = module
        spec.loader.exec_module(module)
from jinja2 import Environment, FileSystemLoader, StrictUndefined
import read_source
paths = ([str(OUT / 'api/templates')] if args.staged else []) + [str(PL / 'templates')]
env = Environment(loader=FileSystemLoader(paths), undefined=StrictUndefined)
templates = SimpleNamespace(get_result=lambda path, params: env.get_template(path).render(**params))
targets = [(2, 'Msn2Offer', 'THORN_CLASS'), (2, 'Msn2Offer', 'THORN_ACCEPT_CLASS'),
           (2, 'Msn2Miner', 'THORN_CLASS'), (2, 'Msn2Done', 'THORN_CLASS'),
           (8, 'Msn8PrinceWales', 'THORN_CLASS'), (8, 'Msn8Sprague', 'THORN_CLASS')]
reports = {}


def normalized(value):
    if isinstance(value, dict):
        return {k: normalized(v) for k, v in value.items()}
    if isinstance(value, list):
        return [normalized(v) for v in value]
    if isinstance(value, (int, float)):
        return round(value, 5) + 0.0
    return value


for mission, name, binding in targets:
    key = f'{name}:{binding}'
    try:
        props_cls = getattr(importlib.import_module(f'story.scripts.main.mission{mission}'), name)
        props = props_cls(SimpleNamespace(MISSION_INDEX=mission))
        instance = getattr(props_cls, binding)(templates, props, russian=True)
        content = instance.get_content()
        read_source.SOURCE = SimpleNamespace(read_text=lambda **kw: content)
        data = normalized(read_source.read())
        reports[key] = dict(sha256=sha(json.dumps(data, sort_keys=True).encode()),
                            duration=instance.get_duration(), events=len(data['events']))
    except Exception as exc:
        reports[key] = dict(preexisting_error=repr(exc))
if args.staged:
    baseline = json.loads((OUT / 'compatibility_baseline.json').read_text())
    assert reports == baseline, (reports, baseline)
    assert sum('sha256' in v for v in reports.values()) >= 4, reports
    print('Existing native scene output unchanged:', ', '.join(reports))
(OUT / ('compatibility_check.json' if args.staged else 'compatibility_baseline.json')).write_text(
    json.dumps(reports, indent=2), encoding='utf-8')
print(json.dumps(reports, indent=2))
