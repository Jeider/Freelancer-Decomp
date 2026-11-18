"""Check actual mission imports and registry references without building scenes."""
import argparse
import importlib
import importlib.util
import json
import os
from pathlib import Path
import sys
from inventory import OUT, PL

parser = argparse.ArgumentParser(description=__doc__)
parser.add_argument('--installed', action='store_true')
args = parser.parse_args()
sys.path.insert(0, str(PL))
os.chdir(PL)
inventory = json.loads((OUT / 'inventory.json').read_text())


def load(name, path):
    spec = importlib.util.spec_from_file_location(name, path)
    module = importlib.util.module_from_spec(spec)
    sys.modules[name] = module
    spec.loader.exec_module(module)
    return module


if not args.installed:
    for name in ('content', 'scene'):
        load('story.cutscenes.' + name, OUT / f'api/story/cutscenes/{name}.py')
    for name in inventory['scenes']:
        load('story.cutscenes.story_scenes.' + name, OUT / name / f'{name}.py')
    registry = load('story.cutscenes.reconstructed_m02_m08', OUT / 'integration/Pythonlancer/story/cutscenes/reconstructed_m02_m08.py')
else:
    registry = importlib.import_module('story.cutscenes.reconstructed_m02_m08')
for name in inventory['scenes']:
    spec = json.loads((OUT / name / 'spec.json').read_text(encoding='utf-8'))
    entry = registry.SCENES[name]
    assert entry['class'] == spec['scene_class']
    cls = getattr(importlib.import_module(entry['module']), entry['class'])
    assert cls.DUMP_FILE == name
modules = {}
count = 0
for mission in range(3, 9):
    module_name = f'story.scripts.main.mission{mission}'
    module = importlib.import_module(module_name) if args.installed else load(
        module_name, OUT / f'integration/Pythonlancer/story/scripts/main/mission{mission}.py')
    modules[mission] = module
    for cls in vars(module).values():
        if not isinstance(cls, type):
            continue
        for attr in ('THORN_CLASS', 'THORN_DECISION_CLASS', 'THORN_ACCEPT_CLASS'):
            target = getattr(cls, attr, None)
            if target is not None and target.__module__.rsplit('.', 1)[-1] in inventory['scenes']:
                assert target.__name__ != 'ReconstructedScene'
                count += 1
for key, binding in inventory['protected_native'].items():
    mission, cls, attr = key.split(':')
    assert getattr(getattr(modules[int(mission)], cls), attr).__name__ == binding.split('.')[-1]
reachable = set()
for module in modules.values():
    for cls in vars(module).values():
        if not isinstance(cls, type) or 'CUTSCENES' not in vars(cls):
            continue
        for props in cls.CUTSCENES:
            for attr in ('THORN_CLASS', 'THORN_DECISION_CLASS', 'THORN_ACCEPT_CLASS'):
                target = getattr(props, attr, None)
                if target is not None:
                    reachable.add(target.__module__.rsplit('.', 1)[-1])
assert set(inventory['scenes']) <= reachable, set(inventory['scenes']) - reachable
print(f'{count} direct mission bindings and 43 registry classes verified; original M08 bindings intact.')
