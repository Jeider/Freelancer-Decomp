"""A small real Blender cache-containment check; no room or game edits."""
import json
import sys
from pathlib import Path
import bpy

ROOT = Path(__file__).resolve().parents[2]
sys.path.insert(0, str(ROOT / 'tools'))
from blender_workspace import configure

cache = configure('base_interiors')
assert Path.cwd() == cache and cache != ROOT
before = {p.name for p in ROOT.iterdir() if not p.name.isascii()}
source = ROOT / 'out/base_interiors/rheinland_batch/rh_depot_deck/textures'
image = bpy.data.images.load(str(next(source.glob('*.png'))))
assert image.size[0] > 0
saved = cache / 'cache_containment_check.blend'
bpy.ops.wm.save_as_mainfile(filepath=str(saved), compress=True)
bpy.ops.wm.open_mainfile(filepath=str(saved), load_ui=False)
assert Path.cwd() == cache
assert before == {p.name for p in ROOT.iterdir() if not p.name.isascii()}
saved.unlink()
report = dict(working_directory=str(cache), root_unchanged=True, image_load=True,
              blend_save_and_reopen=True, game_modified=False)
(cache.parent / 'containment_check.json').write_text(json.dumps(report, indent=2))
print('CACHE_CONTAINMENT', json.dumps(report), flush=True)
