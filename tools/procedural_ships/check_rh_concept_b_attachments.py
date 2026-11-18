"""Read the saved Blender file and bind static previews to the current CMP."""
import argparse
import hashlib
import json
from pathlib import Path
import sys

import bpy

sys.path.insert(0,str(Path(__file__).resolve().parent))
sys.path.insert(0,str(Path(__file__).resolve().parent.parent))
from blender_workspace import configure
configure('ship_design')
from rh_redesign_paths import CONCEPT_B_ATTACHMENTS, CONCEPT_B_COMPACT, CONCEPT_B_SOCKETS

parser=argparse.ArgumentParser()
parser.add_argument('--revision',type=int,choices=(6,7,8),default=6)
args=parser.parse_args(sys.argv[sys.argv.index('--')+1:] if '--' in sys.argv else [])
OUT={6:CONCEPT_B_ATTACHMENTS,7:CONCEPT_B_COMPACT,8:CONCEPT_B_SOCKETS}[args.revision]

checks=json.loads((OUT/'checks.json').read_text())
assert hashlib.sha256((OUT/'rh_concept_b_lod0.cmp').read_bytes()).hexdigest()==checks['output_sha256']
bpy.ops.wm.open_mainfile(filepath=str(OUT/'rh_concept_b_rigged.blend'))
assert bpy.context.scene['CMP_sha256']==checks['output_sha256']
assert sum(len(o.data.polygons) for o in bpy.context.scene.objects if o.type=='MESH')==checks['triangles']
packed=[]
for material in bpy.data.materials:
    if not material.use_nodes:continue
    for node in material.node_tree.nodes:
        if node.type=='TEX_IMAGE' and node.image:
            assert node.image.packed_file,node.image.name
            packed.append(node.image.name)
files=['geometry_open.png','geometry_side.png','geometry_top_folded.png','textured_open.png',
       'textured_side.png','textured_bottom.png','engine_detail.png','drum_detail.png','cabin_transition.png']
if args.revision>=7:files+=['textured_rear.png','textured_top.png']
if args.revision==8:
    files.remove('geometry_top_folded.png')
    files+=['geometry_top.png','side_sill.png','wing_socket.png','neck_front.png','neck_bottom.png','tail_engine_join.png']
manifest=dict(cmp_sha256=checks['output_sha256'],saved_blend_matches_cmp=True,
              packed_textures=sorted(set(packed)),triangles=checks['triangles'],previews=[])
for name in files:
    p=OUT/name
    assert p.stat().st_mtime>=(OUT/'rh_concept_b_lod0.cmp').stat().st_mtime
    assert p.read_bytes().startswith(b'\x89PNG\r\n\x1a\n')
    manifest['previews'].append(dict(file=name,sha256=hashlib.sha256(p.read_bytes()).hexdigest()))
(OUT/'preview_manifest.json').write_text(json.dumps(manifest,indent=2),encoding='utf-8')
print('VERIFIED saved Blender, current CMP, packed textures,',len(files),'static views',flush=True)
