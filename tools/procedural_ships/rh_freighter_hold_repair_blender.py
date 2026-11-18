"""Rebuild a clean narrow cargo tub and its surrounds without squeezing decks."""
import copy,json,math,sys
from pathlib import Path
import bpy,bmesh,numpy as np
from mathutils import Vector
HERE=Path(__file__).resolve().parent
sys.path.insert(0,str(HERE.parent))
from blender_workspace import configure
configure('ship_design')
sys.path.insert(0,str(HERE))
import rh_freighter_final_blender as g
BASE=g.OUT;OUT=BASE/'hold_repair';PREV=BASE/'hold_damage';g.OUT=OUT
DATA=json.loads((OUT/'input.json').read_text());C=g.C
PALE=4138378680;BROWN=529652695;CARGO=3821786036

def box(name,lo,hi,mid):
    x,y,z=lo;X,Y,Z=hi
    return g.object_from_points(name,[(x,y,z),(X,y,z),(X,Y,z),(x,Y,z),(x,y,Z),(X,y,Z),(X,Y,Z),(x,Y,Z)],
        [(0,3,2,1),(4,5,6,7),(0,1,5,4),(1,2,6,5),(2,3,7,6),(3,0,4,7)],mid)

def map_faces(ob,only=None):
    """Explicit planar charts; no radial planar projection onto side walls."""
    uv=ob.data.uv_layers.active
    for p in ob.data.polygons:
        mid=int(ob.data.materials[p.material_index].name)
        if only is not None and mid not in only:continue
        n=C.transposed()@p.normal;axis=int(np.argmax(np.abs(n)))
        axes=(0,2) if axis==1 else (2,1) if axis==0 else (0,1)
        coords=np.array([C.transposed()@ob.data.vertices[ob.data.loops[i].vertex_index].co for i in p.loop_indices])[:,axes]
        if mid==CARGO:
            u=coords/2.4
        elif mid==BROWN:
            u=np.array([.53,.3])+coords*.13
        else:
            lo=coords.min(0);span=np.maximum(np.ptp(coords,axis=0),.01)
            u=np.array([.51,.27])+(coords-lo)/span*np.array([.48,.57])
        for li,uvp in zip(p.loop_indices,u):uv.data[li].uv=(uvp[0],1-uvp[1])

def groups(ob):return g.groups_from_mesh(ob.data,[int(m.name) for m in ob.data.materials])

def union(target,other):
    """Fuse contacting volumes; never leave coincident skins at the cargo rim."""
    uv_name=target.data.uv_layers.active.name
    for ob in (target,other):
        active=ob.data.uv_layers.active
        for layer in list(ob.data.uv_layers):
            if layer!=active:ob.data.uv_layers.remove(layer)
        ob.data.uv_layers.active.name=uv_name
    mids=list(dict.fromkeys([m.name for m in target.data.materials]+[m.name for m in other.data.materials]))
    for ob in (target,other):
        old=[m.name for m in ob.data.materials];indices=[mids.index(old[p.material_index]) for p in ob.data.polygons]
        ob.data.materials.clear()
        for m in mids:ob.data.materials.append(bpy.data.materials[m])
        for p,i in zip(ob.data.polygons,indices):p.material_index=i
    bpy.context.view_layer.objects.active=target
    mod=target.modifiers.new('One continuous cargo surround','BOOLEAN');mod.operation='UNION';mod.solver='MANIFOLD';mod.object=other
    bpy.ops.object.modifier_apply(modifier=mod.name);bpy.data.objects.remove(other,do_unlink=True)

def end_panel(side):
    """Stationary closing lip follows the actual swept roof/rail cross-section.

    The middle shutter has radius 4.51; the two raised rails reach 4.65.
    Profile the underside/inner edge outside that envelope rather than
    bridging its motion with a flat overlapping plate.
    """
    xs=[-2.72,-2.32,-2.15,-1.96,-1.82,1.82,1.96,2.15,2.32,2.72]
    rs=[4.51,4.51,4.65,4.65,4.51,4.51,4.65,4.65,4.51,4.51]
    cy,cz=2.4349513,.9392922;outer=-3.74 if side<0 else 5.74;verts=[]
    for x,r in zip(xs,rs):
        inner=[(y,cz+side*math.sqrt((r+.028)**2-(y-cy)**2)) for y in (3.48,3.59,3.70,3.81)]
        yz=[(3.48,outer)]+inner+[(3.81,outer)]
        verts.extend((x,y,z) for y,z in yz)
    n=6;faces=[tuple(range(n-1,-1,-1)),tuple(range((len(xs)-1)*n,len(xs)*n))]
    for a in range(len(xs)-1):
        for b in range(n):faces.append((a*n+b,a*n+(b+1)%n,(a+1)*n+(b+1)%n,(a+1)*n+b))
    ob=g.object_from_points('Front roof closing panel' if side<0 else 'Rear roof closing panel',verts,faces,PALE)
    uv=ob.data.uv_layers.active
    # A single continuous pale panel strip, including both rail clearances.
    for p in ob.data.polygons:
        for li in p.loop_indices:
            co=C.transposed()@ob.data.vertices[ob.data.loops[li].vertex_index].co
            u=.51+(co.x+2.72)/5.44*.48
            v=.40+(co.z-outer)*side*.20+(co.y-3.81)*.15
            uv.data[li].uv=(u,1-v)
    return ob

def close_subpixel(ob):
    splits=g.conform(ob);bm=bmesh.new();bm.from_mesh(ob.data);edges=[e for e in bm.edges if e.is_boundary]
    if edges:
        assert len(edges)<32,len(edges)
        fs=bmesh.ops.holes_fill(bm,edges=edges,sides=0)['faces'];area=sum(p.calc_area() for p in fs)
        assert area<.005,area
    bmesh.ops.recalc_face_normals(bm,faces=list(bm.faces));bm.to_mesh(ob.data);bm.free()
    return dict(splits=splits,**g.topology(ob))

def author():
    g.clear();g.materials();report={}
    previous=json.loads((PREV/'geometry.json').read_text())['roots'][0]
    # These nine untouched groups are the exact stable source geometry kept by
    # the previous revision. The last five groups were the rejected squeezed core.
    stable=previous[:9];assert sum(len(a['corners']) for a in stable)==17624
    assert sum(len(a['corners']) for a in previous[9:])==3655
    original=json.loads((OUT/'original_core.json').read_text())
    core,_=g.mesh_object(dict(groups=original),'Original deck and lower hull')
    report['original_core']=close_subpixel(core)
    # Remove ONLY the outboard internal wall below its original deck. The
    # horizontal/sloping deck and both cornices keep their accepted coordinates.
    profile=[(.215,-3.72),(.215,7.15),(2.70,7.15),(3.65,5.72),(3.65,-3.72)]
    for side in (-1,1):
        cutter=g.extruded('Deep side mechanism volume',profile,min(side*1.25,side*3.0),max(side*1.25,side*3.0),BROWN)
        g.boolean(core,cutter)
    map_faces(core,{BROWN});report['restored_core']=g.topology(core)
    assert not report['restored_core']['boundary_edges'] and not report['restored_core']['nonmanifold_edges']
    # Closed rectangular tub: straight walls and a flat raised floor. The old
    # full-width floor is omitted, rather than deformed into slivers.
    tub=box('Narrow cargo liner',(-1.25,.215,-2.66),(1.25,3.81,4.54),BROWN)
    cutter=box('Cargo interior',(-1.10,.355,-2.51),(1.10,4.2,4.39),CARGO);g.boolean(tub,cutter)
    map_faces(tub);report['cargo_tub']=g.topology(tub);assert not report['cargo_tub']['nonmanifold_edges']
    # Cover the side mechanism chambers above the highest retracted button.
    # The underside remains open towards the deep damage niche. Short coherent
    # panels run longitudinally, with no strained cross-hull UV triangles.
    report['covers']=[]
    for side in (-1,1):
        for a,b in zip([-3.10,-.39,2.32],[ -.39,2.32,4.98]):
            ob=box('Cargo shoulder cover', (min(side*1.10,side*2.72),3.65,a),(max(side*1.10,side*2.72),3.81,b),PALE)
            map_faces(ob);report['covers'].append(g.topology(ob));union(tub,ob)
    # End ledges approach the shutter slot; the moving shell needs the short
    # transverse clearance beyond them. Keep it deliberate, dark and even.
    for a,b in [(-3.10,-2.66),(4.54,4.98)]:
        ob=box('Cargo end sill',(-1.10,3.65,a),(1.10,3.81,b),PALE)
        map_faces(ob);union(tub,ob)
    report['fused_cargo_rim']=g.topology(tub)
    union(core,tub)
    for side in (-1,1):union(core,end_panel(side))
    report['final_connected_surround']=close_subpixel(core)
    assert not report['final_connected_surround']['boundary_edges'] and not report['final_connected_surround']['nonmanifold_edges']
    new=groups(core);bpy.data.objects.remove(core,do_unlink=True)
    roots=[stable+new,DATA['levels'][1]['Root'],DATA['levels'][2]['Root']]
    g.dump('geometry.json',dict(roots=roots,restored_core=new,stable_groups=9,topology=report,
        cargo=dict(inner_half_width=1.10,outer_half_width=1.25,floor_y=.355,top_y=3.81,z_inner=[-2.51,4.39]),
        lights='All current user HPs preserved byte-for-byte; no automatic repositioning'))
    print('CLEAN CARGO GEOMETRY',sum(len(a['corners']) for a in roots[0]),report,flush=True)

if __name__=='__main__':author()
