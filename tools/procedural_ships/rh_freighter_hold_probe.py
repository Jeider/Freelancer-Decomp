"""Probe the complete cargo opening of a saved offline prototype."""
import json,sys,hashlib
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
variant=sys.argv[sys.argv.index('--variant')+1]
OUT=HERE.parents[1]/'out/ship_design/rh_freighter/prototypes'/variant


def main():
    bpy.ops.wm.open_mainfile(filepath=str(OUT/'rh_pir_freighter_prototype.blend'))
    scene=bpy.context.scene;scene.frame_set(485);bpy.context.view_layer.update()
    trees={ob.name:(BVHTree.FromPolygons([ob.matrix_world@v.co for v in ob.data.vertices],
        [tuple(p.vertices) for p in ob.data.polygons],all_triangles=True),ob)
        for ob in scene.objects if ob.type=='MESH' and not ob.hide_render}
    def ray(origin,direction,only=None):
        o=C@Vector(origin);d=C@Vector(direction);found=[]
        for name,(tree,ob) in trees.items():
            if only is not None and name!=only:continue
            p,n,i,dist=tree.ray_cast(o,d,40)
            if p is not None:
                mat=ob.data.materials[ob.data.polygons[i].material_index]
                found.append(dict(part=name,point=list(C.transposed()@p),front=n.dot(d)<0,
                    material=mat.get('External native material'),distance=dist))
        return min(found,key=lambda v:v['distance']) if found else None
    floors=[];sides=[]
    for x in (-2,-1,0,1,2):
        for i in range(19):
            z=-3.5+i*.5;r=ray((x,1,z),(0,-1,0),'Root')
            floors.append(dict(origin=[x,1,z],hit=r,visible_surface=ray((x,1,z),(0,-1,0)),
                ok=bool(r and r['front'] and abs(r['point'][1]+3.1)<.001)))
    for y in (0,2,3.4,4,5,6,6.5):
        for i in range(19):
            z=-3.5+i*.5
            if y>2.435 and (y-2.435)**2+(z-.939)**2>4.3**2:continue
            for side in (-1,1):
                r=ray((0,y,z),(side,0,0))
                sides.append(dict(origin=[0,y,z],side=side,hit=r,
                    ok=bool(r and r['front'] and abs(r['point'][0])<2.95)))
    ends=[]
    for side,z in [(-1,-3.72),(1,5.72)]:
        for x in (-2,-1,0,1,2):
            for y in (-2.8,-1.5,0,1.5,3.2):
                r=ray((x,y,.9),(0,0,side),'Root')
                ends.append(dict(origin=[x,y,.9],side=side,hit=r,
                    ok=bool(r and r['front'] and abs(r['point'][2]-z)<.001)))
    report=dict(cmp_sha256=hashlib.sha256((OUT/'rh_pir_freighter.cmp').read_bytes()).hexdigest(),
        floors=floors,sides=sides,ends=ends,floor_failures=[r for r in floors if not r['ok']],
        side_failures=[r for r in sides if not r['ok']],end_failures=[r for r in ends if not r['ok']])
    (OUT/'hold_probe.json').write_text(json.dumps(report,indent=2),encoding='utf8')
    print('HOLD_PROBE',len(floors),len(report['floor_failures']),len(sides),len(report['side_failures']),len(ends),len(report['end_failures']))
    print('FAILURES',json.dumps(report['side_failures'][:12]))
    from collections import Counter
    print('MATERIALS',Counter(r['hit']['material'] for r in floors+sides if r['hit']))
    assert not report['floor_failures'] and not report['side_failures'] and not report['end_failures']


if __name__=='__main__':main()
