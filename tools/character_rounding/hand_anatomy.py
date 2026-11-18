"""Author a continuous anatomical hand on the unchanged native finger rig.

Quad reconstruction supplies a rounded surface; authored palm pads, knuckles,
phalange volume and distal taper supply the shape. Wrist vertices are pinned.
"""
import gzip
import json
import math
import re
from pathlib import Path
import sys
import bmesh
import bpy
import numpy as np
from mathutils import Matrix,Vector
from mathutils.bvhtree import BVHTree

ROOT=Path(__file__).resolve().parents[2]
sys.path.insert(0,str(ROOT/'tools'))
sys.path.insert(0,str(Path(__file__).resolve().parent))
from blender_workspace import configure
from hand_caps import rebuild as rebuild_caps
configure('character_rounding')
OUT=ROOT/'out/character_rounding/hands'
C=Matrix(((1,0,0),(0,0,-1),(0,1,0)))


def unit(v):return v/max(np.linalg.norm(v),1e-12)
def smooth(a,b,x):
    t=np.clip((x-a)/(b-a),0,1);return t*t*(3-2*t)


def build(folder):
    data=json.loads(gzip.decompress((folder/'source.json.gz').read_bytes()))
    bpy.ops.object.select_all(action='SELECT');bpy.ops.object.delete(use_global=False)
    points=np.array(data['points'])
    tris=[t for g in data['groups'] for t in g['faces']]
    faces=[[data['point_indices'][i] for i in t] for t in tris]
    mesh=bpy.data.meshes.new('Anatomical hand');mesh.from_pydata(points,[],faces);mesh.update()
    ob=bpy.data.objects.new('Hand',mesh);bpy.context.collection.objects.link(ob)
    bpy.context.view_layer.objects.active=ob;ob.select_set(True)
    uv=mesh.uv_layers.new(name='UV0')
    for poly,tri in zip(mesh.polygons,tris):
        for loop,idx in zip(poly.loop_indices,tri):uv.data[loop].uv=data['uv'][data['uv_indices'][idx]]
    for idx,bone in enumerate(data['bones']):
        vg=ob.vertex_groups.new(name=bone['name'])
        for i,weights in enumerate(data['skin']):
            w=weights.get(str(idx),0)
            if w:vg.add([i],w,'REPLACE')
    bm=bmesh.new();bm.from_mesh(mesh)
    bmesh.ops.join_triangles(bm,faces=list(bm.faces),angle_face_threshold=math.pi,angle_shape_threshold=math.pi,cmp_uvs=False)
    edgecrease=bm.edges.layers.float.get('crease_edge') or bm.edges.layers.float.new('crease_edge')
    vertcrease=bm.verts.layers.float.get('crease_vert') or bm.verts.layers.float.new('crease_vert')
    boundary={v for e in bm.edges if e.is_boundary for v in e.verts}
    wrist=[np.array(v.co) for v in boundary]
    for e in bm.edges:
        if e.is_boundary:e[edgecrease]=1
    for v in boundary:v[vertcrease]=1
    bm.to_mesh(mesh);bm.free()
    sub=ob.modifiers.new('Anatomical surface support','SUBSURF');sub.levels=1;sub.subdivision_type='CATMULL_CLARK'
    bpy.ops.object.modifier_apply(modifier=sub.name)
    mesh=ob.data
    bones=data['bones'];bind=[];origins=[]
    for b in bones:
        a=np.array(b['native_bind']);M=np.eye(4);M[:3,:3]=a[:9].reshape(3,3);M[:3,3]=a[9:]
        B=np.linalg.inv(M);bind.append(B);origins.append(B[:3,3])
    origins=np.array(origins);names=[re.sub(r' 0([123])$',r' \1',b['name']) for b in bones]
    side='R' if 'right' in folder.name else 'L'
    chains={finger:[names.index(f'{side} {finger} {joint}') for joint in ('1','2','3','End')] for finger in ('Index','Middle','Ring','Pinky','Thumb')}
    mcp=origins[[chains[f][0] for f in ('Index','Middle','Ring','Pinky')]]
    longitudinal=unit(mcp.mean(0))
    width=unit(mcp[0]-mcp[-1]);normal=unit(np.cross(longitudinal,width))
    if np.dot(normal,origins[chains['Middle'][3]]-mcp[1])<0:normal=-normal
    finger_for={i:f for f,chain in chains.items() for i in chain}
    moves=[]
    for v in mesh.vertices:
        p=np.array(v.co);old=p.copy();weights={g.group:g.weight for g in v.groups if g.weight>.00001}
        totals={f:sum(w for i,w in weights.items() if finger_for.get(i)==f) for f in chains}
        f=max(totals,key=totals.get);influence=totals[f]
        if influence>.2:
            joints=origins[chains[f]];best=None
            for j in range(3):
                axis=joints[j+1]-joints[j];t=np.clip(np.dot(p-joints[j],axis)/np.dot(axis,axis),0,1)
                center=joints[j]+axis*t;delta=p-center;dist=np.linalg.norm(delta)
                if best is None or dist<best[0]:best=(dist,j,t,center,unit(axis),delta)
            dist,j,t,center,axis,rad=best
            # Restore cross-sectional volume lost by the quad surface. A small
            # joint swell and distal taper separate knuckles from phalanges.
            joint_swell=.035*(math.exp(-((t-.03)/.22)**2)+math.exp(-((t-.97)/.22)**2))
            factor=1.16+joint_swell-(.075*smooth(.15,.9,t) if j==2 else 0)
            radial=rad-axis*np.dot(rad,axis)
            p+=radial*(factor-1)*smooth(.2,.85,influence)
        palm=weights.get(0,0)
        longitudinal_pos=np.dot(p,longitudinal)
        if palm>.05:
            # Thenar/hypothenar pads and dorsal metacarpal contours, millimetres.
            palm_center=mcp.mean(0)*.48
            thick=np.dot(p-palm_center,normal)
            surface=math.tanh(thick/.007)
            thumb_center=origins[chains['Thumb'][0]]*.6+mcp[0]*.25
            little_center=mcp[-1]*.52
            thenar=math.exp(-np.linalg.norm((p-thumb_center)-normal*np.dot(p-thumb_center,normal))**2/.026**2)
            hypothenar=math.exp(-np.linalg.norm((p-little_center)-normal*np.dot(p-little_center,normal))**2/.027**2)
            cup=math.exp(-np.linalg.norm((p-palm_center)-normal*np.dot(p-palm_center,normal))**2/.021**2)
            dorsal=sum(math.exp(-np.linalg.norm((p-q)-normal*np.dot(p-q,normal))**2/.014**2) for q in mcp)
            displacement=(.0028*thenar+.0014*hypothenar-.0009*cup) if surface>0 else -.0012*dorsal
            p+=normal*displacement*abs(surface)*palm*smooth(-.005,.025,longitudinal_pos)
        # No change at the sleeve attachment; no new gap even with a bent wrist.
        if wrist and min(np.linalg.norm(old-q) for q in wrist)<1e-7:p=old
        v.co=p;moves.append(float(np.linalg.norm(p-old)))
    mesh.update()
    rebuild_caps(mesh,data,chains,origins,width)
    for poly in mesh.polygons:poly.use_smooth=True
    mesh.calc_loop_triangles()
    skin=[]
    for v in mesh.vertices:
        ordered=sorted(((g.group,g.weight) for g in v.groups if g.weight>.00001),key=lambda x:x[1],reverse=True)[:4]
        total=sum(w for i,w in ordered);assert total>0
        skin.append({str(i):w/total for i,w in ordered})
    output=dict(data);output.update(points=[list(v.co) for v in mesh.vertices],normals=[list(v.normal) for v in mesh.vertices],skin=skin,
        point_indices=[],uv_indices=[],uv=[],groups=[])
    faces=[];uv=mesh.uv_layers.active
    for tri in mesh.loop_triangles:
        face=[]
        for loop in tri.loops:
            face.append(len(output['point_indices']));output['point_indices'].append(mesh.loops[loop].vertex_index)
            output['uv_indices'].append(len(output['uv']));output['uv'].append(list(uv.data[loop].uv))
        faces.append(face)
    assert len(data['groups'])==1
    output['groups']=[dict(data['groups'][0],faces=faces)]
    assert len(faces)<=1200,(folder.name,len(faces))
    output['authoring']=dict(revision=5,method='quad surface with authored phalange volume, joint swell, rebuilt rounded fingertip topology and palm pads',
        triangles=len(faces),max_anatomical_sculpt_m=max(moves),wrist_pinned=True,bone_pivots_unchanged=True)
    (folder/'edited.json.gz').write_bytes(gzip.compress(json.dumps(output,separators=(',',':')).encode(),mtime=0))
    print(folder.name,output['authoring'],flush=True)


for folder in sorted(OUT.iterdir()):
    if (folder/'source.json.gz').exists():build(folder)
