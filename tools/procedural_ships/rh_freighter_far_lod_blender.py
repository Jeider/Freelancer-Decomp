"""Offline LOD2 proxy: broad structural volumes, existing projection atlas."""
import json, sys, math
from pathlib import Path
import bpy, bmesh
import numpy as np
from mathutils import Vector
HERE = Path(__file__).resolve().parent
sys.path.insert(0, str(HERE.parent))
from blender_workspace import configure
configure('ship_design')
sys.path.insert(0, str(HERE))
from rh_concept_b_final_blender import mesh_object, groups_from_mesh, C
BASE = HERE.parents[1] / 'out/ship_design/rh_freighter/rh_pir_freighter'
OUT = BASE / 'lod_refinement'
DATA = json.loads((BASE / 'blender_input.json').read_text())
MECH = json.loads((BASE.parent / 'prototypes/uv_15/mechanical_geometry.json').read_text())
PROJ = json.loads((BASE / 'projectors.json').read_text())
STATS = []


def dump(name, data):
    OUT.mkdir(exist_ok=True)
    (OUT/name).write_text(json.dumps(data, indent=2, default=lambda a: a.tolist()), encoding='utf8')


def reduce(name, groups, ratio=1, hull=False, native_uv=False):
    print('BEGIN',name,flush=True)
    ob, slots = mesh_object(dict(groups=groups), name)
    bm=bmesh.new(); bm.from_mesh(ob.data)
    if hull:
        r=bmesh.ops.convex_hull(bm, input=list(bm.verts), use_existing_faces=False)
        bmesh.ops.delete(bm, geom=list(set(r['geom_interior']+r['geom_unused'])), context='VERTS')
    if not native_uv:
        bmesh.ops.dissolve_limit(bm, angle_limit=.004, verts=list(bm.verts), edges=list(bm.edges),
                                use_dissolve_boundaries=False, delimit=set())
    if not native_uv:
        bmesh.ops.recalc_face_normals(bm, faces=list(bm.faces)); bm.to_mesh(ob.data)
    bm.free()
    if ratio<1:
        mod=ob.modifiers.new('Structural distance reduction', 'DECIMATE');mod.ratio=ratio
        mod.use_collapse_triangulate=True
    ev=ob.evaluated_get(bpy.context.evaluated_depsgraph_get());me=ev.to_mesh()
    gs=groups_from_mesh(me,slots);ev.to_mesh_clear()
    STATS.append(dict(component=name, triangles=sum(len(g['corners']) for g in gs)))
    print('DONE',STATS[-1],flush=True)
    bpy.data.objects.remove(ob,do_unlink=True)
    return gs


def project(groups, owner):
    ts=[]
    for g in groups:
        for t in np.asarray(g['corners'],float):
            n=np.cross(t[1,:3]-t[0,:3],t[2,:3]-t[0,:3]); n/=np.linalg.norm(n)
            p=max(PROJ[owner],key=lambda p:n@p['normal']);co=t[:,:3]-p['center'];tx,ty=p['tile']
            t[:,6]=(tx+co@p['u']/p['scale']+.5)/8
            t[:,7]=(ty+.5-co@p['v']/p['scale'])/8
            ts.append(t)
    return [dict(material=0,corners=np.array(ts),unused=204)]


def panel(side):
    # Preserve the concave designed outline; close recesses rather than
    # collapsing their walls across incompatible projection charts.
    # Same authored profiles as rh_freighter_uv_b3; avoid importing the
    # non-Blender export stack (SciPy) into Blender's Python environment.
    UP_BACK=np.array([[-7.55,1.26],[-4.12,3.88],[5.66,3.88],[7.42,2.5],
        [7.42,.60],[5.82,.60],[-3.04,-1.49],[-4.56,.02],[-6.80,-1.52],[-7.55,-1.02]])
    UP_FACE=np.array([[-7.14,1.13],[-4.01,3.60],[5.48,3.60],[7.05,2.35],
        [7.05,.91],[5.77,.91],[-2.96,-1.13],[-4.51,.42],[-6.60,-1.08],[-7.14,-.72]])
    rings=[[(side*x,y,z) for z,y in yz] for x,yz in ((2.62,UP_BACK),(3.50,UP_FACE))]
    verts=rings[0]+rings[1];n=len(rings[0]);faces=[list(range(n-1,-1,-1)),list(range(n,2*n))]
    faces += [[i,(i+1)%n,(i+1)%n+n,i+n] for i in range(n)]
    me=bpy.data.meshes.new('Closed side silhouette');me.from_pydata([C@Vector(p) for p in verts],[],faces)
    me.uv_layers.new(); bm=bmesh.new();bm.from_mesh(me)
    bmesh.ops.triangulate(bm,faces=list(bm.faces),ngon_method='EAR_CLIP')
    bmesh.ops.recalc_face_normals(bm,faces=list(bm.faces));bm.to_mesh(me);bm.free()
    return groups_from_mesh(me,[0])


def main():
    import faulthandler
    OUT.mkdir(exist_ok=True)
    trace=open(OUT/'blender_stack.txt','w')
    faulthandler.dump_traceback_later(30,repeat=True,file=trace)
    for ob in list(bpy.data.objects):bpy.data.objects.remove(ob,do_unlink=True)
    original={o['name']:o['groups'] for o in DATA['objects']};result={};root=[]
    for o in MECH['objects']:
        name=o['name']
        if name.startswith('Continuous hull'):
            root+=reduce(name,o['groups'],.35)
        elif name.startswith('Stepped circular'):
            root+=reduce(name,o['groups'],.20,hull=True)
        elif name.startswith(('Lower diagonal hull','Foredeck angular shoulder','Aft structural rib','Aft transverse red','Raised cargo deck')):
            root+=reduce(name,o['groups'])
    result['Root']=project(root,'Root')+DATA['preserved_cockpit']
    result['glass_lod1']=original['glass_lod1']
    # Its native two materials encode the shutter exterior/interior. Keep
    # their UV boundaries while reducing the many curvature/UV subdivisions.
    result['Baydoor_lod1']=reduce('Baydoor',original['Baydoor_lod1'],.065,native_uv=True)
    for side,label in ((-1,'port'),(1,'star')):
        part='rh_'+label+'_side_lod1';result[part]=project(panel(side),part)
        for size,ids in (('big',[2]),('sml',[1,3])):
            part='rh_'+label+'_'+size+'_btn_lod1';groups=[]
            for i in ids:
                ob=next(o for o in MECH['objects'] if o['name']==f'New transverse unit {side:+} {i}')
                groups+=reduce(ob['name'],ob['groups'],.52,hull=True)
            result[part]=project(groups,part)
        part=('port' if side<0 else 'starboard')+'_engine_lod1'
        # Separate mount from pod to preserve the exposed narrow support.
        gs=original[part];front=[];pod=[]
        for g in gs:
            a=np.array(g['corners']);mask=a[:,:,2].max(1)<9.4
            if mask.any():front.append(dict(g,corners=a[mask]))
            if (~mask).any():pod.append(dict(g,corners=a[~mask]))
        result[part]=project(reduce(part+' support',front,hull=True)+reduce(part+' pod',pod,.75,hull=True),part)
    counts={name:sum(len(g['corners']) for g in gs) for name,gs in result.items()}
    assert set(result)==set(original)
    dump('far_world.json',result);dump('geometry.json',dict(parts=counts,total=sum(counts.values()),components=STATS))
    print('FAR LOD COUNTS',counts,'TOTAL',sum(counts.values()),flush=True)


if __name__=='__main__':main()
