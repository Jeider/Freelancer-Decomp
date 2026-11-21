"""Compare pauldron geometry in the scaled blend against a uniform scale of the source."""
import sys
from pathlib import Path

import bpy
import numpy as np

ROOT = Path(__file__).resolve().parents[2]
sys.path.insert(0, str(ROOT / 'tools'))
from blender_workspace import configure

configure('character_rounding')
SRC = ROOT / 'out/character_rounding/higa/rigged/higa_kaitlyn_rigged.blend'
CUR = ROOT / 'out/character_rounding/higa/uniform_scale/higa_uniform.blend'


def mesh_of(path):
    bpy.ops.wm.open_mainfile(filepath=str(path))
    configure('character_rounding')
    body = bpy.data.objects['Higa - skinned Meshy mesh']
    rig = body.parent
    pose = None
    if rig and rig.pose:
        pose = max(float((b.matrix - b.bone.matrix_local).to_translation().length) for b in rig.pose.bones)
    deps = bpy.context.evaluated_depsgraph_get()
    ev = body.evaluated_get(deps)
    raw = np.array([v.co[:] for v in body.data.vertices])
    got = np.array([v.co[:] for v in ev.data.vertices])
    return raw, got, pose, [m.type for m in body.modifiers], len(body.data.vertices)


raw_src, ev_src, pose_src, mods_src, n_src = mesh_of(SRC)
raw_cur, ev_cur, pose_cur, mods_cur, n_cur = mesh_of(CUR)
print('counts', n_src, n_cur, 'pose delta src/cur', pose_src, pose_cur, 'mods', mods_cur)
if n_src != n_cur:
    raise SystemExit('count mismatch')
# pauldron band from the source, before scale
band = (raw_src[:, 2] > 1.30) & (np.abs(raw_src[:, 0]) > 0.08) & (np.abs(raw_src[:, 0]) < 0.32)
ratio = raw_cur[band] / np.where(np.abs(raw_src[band]) < 1e-6, np.nan, raw_src[band])
print('pauldron verts', int(band.sum()))
print('scale median xyz', np.round(np.nanmedian(ratio, axis=0), 4))
print('scale std xyz', np.round(np.nanstd(ratio, axis=0), 5))
pred = raw_src * float(np.nanmedian(ratio))
err = np.linalg.norm(raw_cur - pred, axis=1)
print('uniform error mm max/p99/mean', np.round(err.max() * 1000, 2), np.round(np.percentile(err, 99) * 1000, 2), np.round(err.mean() * 1000, 2))
print('pauldron error mm max', round(float(err[band].max()) * 1000, 2))
deform = np.linalg.norm(ev_cur - raw_cur, axis=1)
print('armature deform mm max/p99', round(float(deform.max()) * 1000, 2), round(float(np.percentile(deform, 99)) * 1000, 2))
print('pauldron deform mm max', round(float(deform[band].max()) * 1000, 2))
# local shape: distances from pauldron centroid should scale by one factor
for name, mask in (('all', np.ones(len(raw_src), dtype=bool)), ('pauldron', band)):
    c0 = raw_src[mask].mean(axis=0)
    c1 = raw_cur[mask].mean(axis=0)
    d0 = np.linalg.norm(raw_src[mask] - c0, axis=1)
    d1 = np.linalg.norm(raw_cur[mask] - c1, axis=1)
    ok = d0 > 1e-4
    k = d1[ok] / d0[ok]
    print(name, 'centroid shift', np.round(c1 - c0 * np.median(k), 4), 'radial scale', round(float(np.median(k)), 4), 'radial std', round(float(np.std(k)), 5))
