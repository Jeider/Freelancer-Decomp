"""Inspect the saved uv_10 assembly: raised floor, stern and pale gap closures."""
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
OUT=HERE.parents[1]/'out/ship_design/rh_freighter/prototypes/uv_10'
if '--variant' in sys.argv:
    variant=sys.argv[sys.argv.index('--variant')+1]
    assert variant.replace('_','').isalnum();OUT=OUT.parent/variant


def main():
    path=OUT/'rh_pir_freighter_prototype.blend'
    bpy.ops.wm.open_mainfile(filepath=str(path));scene=bpy.context.scene
    assert scene.frame_current==211
    assert not bpy.data.objects['Baydoor_lod1'].hide_render
    scene.frame_set(485);bpy.context.view_layer.update()
    trees={}
    for ob in scene.objects:
        if ob.type=='MESH' and not ob.hide_render:
            trees[ob.name]=(BVHTree.FromPolygons([ob.matrix_world@v.co for v in ob.data.vertices],
                [tuple(p.vertices) for p in ob.data.polygons],all_triangles=True),ob)
    def ray(origin,direction,only=None):
        o=C@Vector(origin);d=C@Vector(direction);found=[]
        for name,(tree,ob) in trees.items():
            if only and name!=only:continue
            p,n,i,dist=tree.ray_cast(o,d,30)
            if p is not None:
                mat=ob.data.materials[ob.data.polygons[i].material_index]
                found.append(dict(part=name,point=list(C.transposed()@p),front=n.dot(d)<0,
                    material=mat.get('External native material'),distance=dist))
        return min(found,key=lambda r:r['distance']) if found else None
    cfg=json.loads((OUT/'raised_hold_geometry.json').read_text());y=cfg['new_floor_y']
    assert abs(cfg['new_depth']/cfg['old_depth']-.5)<1e-8
    floors=[];undersides=[]
    for x in (-2.2,-1.5,-.7,0,.7,1.5,2.2):
        for i in range(15):
            z=-2.5+i*.48
            r=ray((x,y+.35,z),(0,-1,0))
            assert r and r['front'] and r['part']=='Root' and abs(r['point'][1]-y)<1e-4,r
            assert r['material']=='metal03D',r
            floors.append(r)
            r=ray((x,y-.3,z),(0,1,0),'Root')
            assert r and r['front'] and abs(r['point'][1]-(y-.14))<1e-4,r
            undersides.append(r)
    walls=[]
    for x in (-2.2,0,2.2):
        for direction,z in [((0,0,1),cfg['stations_zy'][0][0]),((0,0,-1),cfg['stations_zy'][-1][0])]:
            r=ray((x,y-.07,z-direction[2]*.08),direction,'Root')
            assert r and r['front'] and abs(r['point'][2]-z)<1e-4,r
            walls.append(r)
    sides=[]
    for side in (-1,1):
        for z in (-2.4,-1,0,1,2,3,4.3):
            r=ray((0,y+.25,z),(side,0,0))
            assert r and r['front'] and abs(r['point'][0])<2.95,r
            sides.append(r)
    stern=[];belt=json.loads((OUT/'stern_transition_geometry.json').read_text())
    cornice=json.loads((OUT/'cornice_geometry.json').read_text()) if (OUT/'cornice_geometry.json').exists() else None
    for x in (-1.1,-.6,0,.6,1.1):
        for yy in (-2.4,-1.6,-.8,-.28,.4,1.3):
            r=ray((x,yy,10),(0,0,-1),'Root')
            isbelt=abs(yy-belt['belt_y'])<belt['belt_half_height']
            expected=belt['belt_material'] if isbelt else belt['upper_material'] if yy>belt['belt_y'] else belt['lower_material']
            zz=belt['belt_outer_z'] if isbelt else belt['stern_z']
            if cornice and yy>.15:
                zz=cornice['backing_z'] if yy<.66 else cornice['fascia_z']
            assert r and r['front'] and abs(r['point'][2]-zz)<1e-4 and r['material']==expected,(r,expected)
            stern.append(r)
    cornice_checks=[]
    if cornice:
        for x in (-1.1,0,1.1):
            for z in (7.7,8.2,8.7,8.95):
                r=ray((x,4,z),(0,-1,0),'Root')
                assert r and r['front'] and abs(r['point'][1]-cornice['top_y'])<1e-4,r
                cornice_checks.append(r)
            for yy in (.95,1.10,1.5,2.2):
                zz=8.51+(yy-.84)/.44*.35 if yy<1.28 else cornice['fascia_z']
                r=ray((x,yy,10),(0,0,-1),'Root')
                assert r and r['front'] and abs(r['point'][2]-zz)<1e-4,r
                assert r['material']=='pir_r_panel01_256',r
                cornice_checks.append(r)
    shoulders=[]
    for side in (-1,1):
        for z in (7.1,7.3,7.45,7.6):
            for x in (2.49,2.55,2.60):
                r=ray((side*x,5,z),(0,-1,0),'Root')
                assert r and r['front'] and r['point'][1]>2.3 and r['material']=='pir_r_panel01_256',r
                shoulders.append(r)
    fore_checks=[]
    if (OUT/'fore_cornice_geometry.json').exists():
        fore=json.loads((OUT/'fore_cornice_geometry.json').read_text())
        assert abs(fore['top_y']-cornice['top_y'])<1e-8
        long_shelf=fore.get('long_platform',False)
        xs=(-1.25,0,1.25) if long_shelf else (-1.65,0,1.65)
        zs=(fore['top_z'][0]+.1,-8.2,-7.7,-7.2,-6.7,-6.,-5.7) if long_shelf else (-7.7,-7.2,-6.7,-6.,-5.7)
        for x in xs:
            for z in zs:
                r=ray((x,4.5,z),(0,-1,0),'Root')
                assert r and r['front'] and abs(r['point'][1]-fore['top_y'])<1e-4,r
                assert r['material']=='pir_r_panel01_256',r
                fore_checks.append(r)
            for yy in (1.9,2.2,2.45,1.64,1.74):
                zz=fore['fascia_z'] if yy>1.78 else -7.40-(yy-1.50)/.28*.22
                r=ray((x,yy,-9),(0,0,1),'Root')
                assert r and r['front'] and abs(r['point'][2]-zz)<1e-4,r
                assert r['material']=='pir_r_panel01_256',r
                fore_checks.append(r)
        if long_shelf:
            for x in (-1,0,1):
                r=ray((x,2.3,-8),(0,1,0),'Root')
                assert r and r['front'] and abs(r['point'][1]-fore['native_platform']['bottom_y'])<1e-4,r
                fore_checks.append(r)
        for side in (-1,1):
            for yy in (1.95,2.35):
                r=ray((side*4,yy,-7.48),(-side,0,0),'Root')
                assert r and r['front'] and abs(r['point'][0]-side*fore['width']/2)<1e-4,r
                fore_checks.append(r)
    report=dict(cmp_sha256=hashlib.sha256((OUT/'rh_pir_freighter.cmp').read_bytes()).hexdigest(),
        blend_sha256=hashlib.sha256(path.read_bytes()).hexdigest(),floor_depth_ratio=.5,
        floors=floors,undersides=undersides,deck_end_faces=walls,hold_side_walls=sides,
        stern_material_bands=stern,pale_shoulder_closures=shoulders,
        cornice_samples=cornice_checks,
        fore_cornice_samples=fore_checks,
        saved_flight_pose=True,roof_present_in_saved_model=True,installed=False,game_launched=False)
    (OUT/'hold_and_stern_probe.json').write_text(json.dumps(report,indent=2),encoding='utf8')
    print('UV10_PROBES',len(floors),'floor,',len(undersides),'underside,',len(stern),'stern,',len(shoulders),'shoulder')


if __name__=='__main__':main()
