"""Exercise the actual staged Blender dumper on signed and positive scales."""
import contextlib
import io
import json
import os
from pathlib import Path
import sys

REPO = Path(__file__).resolve().parents[3]
sys.path.insert(0, str(REPO / 'tools'))
from blender_workspace import configure
cache = configure('story_cutscenes')
import bpy

out = REPO / 'out/story_cutscenes/m03_m08'
script = out / 'integration/SCENES/SCRIPTS/dumper.py'
work = cache / 'm03_m08_dumper'
(work / 'DUMPS').mkdir(parents=True, exist_ok=True)
results = {}
for name in ('m05_piratebar', 'm06_briefing'):
    bpy.ops.wm.open_mainfile(filepath=str(out / name / f'{name}.blend'))
    configure('story_cutscenes')
    os.chdir(work)
    with contextlib.redirect_stdout(io.StringIO()):
        exec(compile(script.read_text(encoding='utf-8'), str(script), 'exec'), {'bpy': bpy})
    expected = json.loads((out / name / f'{name}.json').read_text())
    actual = json.loads((work / f'DUMPS/{name}.json').read_text())
    assert actual == expected, name
    results[name] = dict(points=len(actual), exact_match=True)
(out / 'dumper_check.json').write_text(json.dumps(results, indent=2), encoding='utf-8')
print(json.dumps(results))
