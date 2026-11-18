"""Reopen final hand sources and check rigs, geometry, poses and image links."""
import gzip
import hashlib
import json
from pathlib import Path
import sys
import bpy
import numpy as np
from mathutils import Matrix
from mathutils.bvhtree import BVHTree

ROOT=Path(__file__).resolve().parents[2];sys.path.insert(0,str(ROOT/'tools'));sys.path.insert(0,str(Path(__file__).resolve().parent))
from blender_workspace import configure
configure('character_rounding')
from hand_animations import bindings
OUT=ROOT/'out/character_rounding/hands';C=np.array([[1,0,0],[0,0,-1],[0,1,0]])
if '--gloves' in sys.argv:OUT=ROOT/'out/character_rounding/gloves'
results=[]
for folder in sorted(OUT.iterdir()):
    if not (folder/'edited.json.gz').exists():continue
    data=json.loads(gzip.decompress((folder/'edited.json.gz').read_bytes()))
    bpy.ops.wm.open_mainfile(filepath=str(folder/'hand.blend'),load_ui=False)
    source=bpy.data.collections['SOURCE - original LOD1'];assert source.hide_render and source.hide_viewport
    col=bpy.data.collections['EDIT - anatomical LOD0'];assert not col.hide_render and not col.hide_viewport
    rig=next(o for o in col.objects if o.type=='ARMATURE');ob=next(o for o in col.objects if o.type=='MESH')
    assert set(rig.data.bones.keys())=={b['name'] for b in data['bones']}
    p=np.array([v.co[:] for v in ob.data.vertices]);assert np.max(abs(p-np.array(data['points'])@C.T))<1e-7
    assert len(ob.data.polygons)==sum(len(g['faces']) for g in data['groups'])
    for bone,B in zip(data['bones'],bindings(data)):
        M=np.eye(4);M[:3,:3]=C@B[:3,:3];M[:3,3]=C@B[:3,3]
        assert np.max(abs(np.array(rig.data.bones[bone['name']].matrix_local)-M))<2e-6
    for im in bpy.data.images:
        if im.source=='FILE' and im.filepath:assert Path(bpy.path.abspath(im.filepath)).exists(),im.filepath
    bpy.context.scene.frame_set(1);bpy.context.view_layer.update()
    ev=ob.evaluated_get(bpy.context.evaluated_depsgraph_get());me=ev.to_mesh()
    assert np.max(abs(np.array([v.co[:] for v in me.vertices])-p))<2e-6;ev.to_mesh_clear()
    fs=[tuple(poly.vertices) for poly in ob.data.polygons]
    tree=BVHTree.FromPolygons(p.tolist(),fs,all_triangles=True)
    intersections=[(a,b) for a,b in tree.overlap(tree) if a<b and not set(fs[a])&set(fs[b])]
    assert not intersections,(folder.name,'rest self intersection',intersections[:5])
    results.append(dict(name=folder.name,blend_sha256=hashlib.sha256((folder/'hand.blend').read_bytes()).hexdigest(),rest_self_intersections=0))
(OUT/'blend_validation.json').write_text(json.dumps(dict(valid=results),indent=2))
print('PASS reopened',len(results),'hand blends: exact native bind, source hidden, texture links, rest skin, closed surface intersections')
