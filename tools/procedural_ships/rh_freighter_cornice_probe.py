"""Compare mirrored exposed cornice surfaces in the saved offline Blender."""
import hashlib
import json
import sys
from pathlib import Path
import bpy
from mathutils import Vector
from mathutils.bvhtree import BVHTree
HERE=Path(__file__).resolve().parent
sys.path.insert(0,str(HERE.parent))
from blender_workspace import configure
configure('ship_design')
sys.path.insert(0,str(HERE))
from rh_concept_b_final_blender import C
OUT=HERE.parents[1]/'out/ship_design/rh_freighter/prototypes/uv_15'


def main():
    path=OUT/'rh_pir_freighter_prototype.blend'
    bpy.ops.wm.open_mainfile(filepath=str(path));scene=bpy.context.scene
    assert scene.frame_current==211
    ob=bpy.data.objects['Root'];tree=BVHTree.FromPolygons([ob.matrix_world@v.co for v in ob.data.vertices],
        [tuple(p.vertices) for p in ob.data.polygons],all_triangles=True)
    cfg=json.loads((OUT/'cornice_symmetry.json').read_text());plane=cfg['plane_z']
    samples=[]
    def paired(origin,direction):
        hits=[]
        for back in (False,True):
            o=Vector(origin);d=Vector(direction)
            if back:o.z=2*plane-o.z;d.z=-d.z
            p,n,i,dist=tree.ray_cast(C@o,C@d,30)
            assert p is not None and n.dot(C@d)<-.1,(origin,direction,back,'missing or back-facing')
            material=ob.data.materials[ob.data.polygons[i].material_index]['External native material']
            assert material=='pir_r_panel01_256',material
            hit=C.transposed()@p
            hits.append(dict(position=list(hit),material=material))
        front=Vector(hits[0]['position']);rear=Vector(hits[1]['position']);rear.z=2*plane-rear.z
        error=(rear-front).length
        assert error<3e-5,(origin,direction,hits,error)
        samples.append(dict(origin=origin,direction=direction,front=hits[0],rear=hits[1],mirror_error=error))
    for x in (-1.25,0,1.25):
        for z in (-8.7,-8.2,-7.7,-7.2,-6.7,-6.,-5.7):paired((x,4.5,z),(0,-1,0))
        for y in (1.9,2.2,2.45,1.64,1.74):paired((x,y,-10),(0,0,1))
    for side in (-1,1):
        for y in (1.95,2.35):paired((side*4,y,-7.48),(-side,0,0))
    for x in (-1,0,1):paired((x,2.3,-8),(0,1,0))
    digest=lambda p:hashlib.sha256(p.read_bytes()).hexdigest()
    report=dict(cmp_sha256=digest(OUT/'rh_pir_freighter.cmp'),blend_sha256=digest(path),
        pair_count=len(samples),ray_count=2*len(samples),max_mirror_error=max(s['mirror_error'] for s in samples),
        surfaces='shelf tops, fascia, sloped return, ends, overhang underside',samples=samples)
    (OUT/'cornice_probe.json').write_text(json.dumps(report,indent=2),encoding='utf8')
    print('MIRRORED_CORNICE_PROBE',report['ray_count'],'rays; maximum error',report['max_mirror_error'])


if __name__=='__main__':main()
