"""Offline native sphere-joint evaluation (EngBase ApplySphereJoint)."""
import sys,json,struct
from pathlib import Path
import numpy as np
ROOT=Path(__file__).resolve().parents[2]
sys.path[:0]=[str(Path(__file__).parent),str(ROOT/'tools/hatcher_hair')]
from hand_animations import quat_matrix,sample

def read_rig(path):
    if Path(path).suffix=='.json':
        d=json.loads(Path(path).read_text());return d['bones'],{n:{k:np.array(v) if k!='parent' else v for k,v in j.items()} for n,j in d['joints'].items()},{n:np.array(v) for n,v in d['bind'].items()}
    import contours as c
    from hands import skeleton
    root=c.read_tree(Path(path).read_bytes())[1][0];bones=skeleton(root);joints={};raw=c.blob(c.child(c.child(root,'Cmpnd'),'Cons'),'Sphere')
    for at in range(0,len(raw),212):
        parent=raw[at:at+64].split(b'\0')[0].decode();name=raw[at+64:at+128].split(b'\0')[0].decode();f=np.array(struct.unpack_from('<21f',raw,at+128))
        joints[name]={'parent':parent,'origin':f[:3],'offset':f[3:6],'rotation':f[6:15].reshape(3,3)}
    bind={}
    for b in bones:
        M=np.eye(4);v=b['native_bind'];M[:3,:3]=np.array(v[:9]).reshape(3,3);M[:3,3]=v[9:];bind[b['name']]=np.linalg.inv(M)
    return bones,joints,bind

def evaluate(bones,joints,bind,clip,time):
    result={}
    def at(name):
        if name in result:return result[name]
        j=joints.get(name)
        if j is None or j['parent'] not in bind:M=bind[name].copy()
        else:
            parent=j['parent'];R=(quat_matrix(sample(clip[name],time))@j['rotation'] if name in clip else (np.linalg.inv(bind[parent])@bind[name])[:3,:3])
            local=np.eye(4);local[:3,:3]=R;local[:3,3]=j['origin']-R@j['offset'];M=at(parent)@local
        result[name]=M;return M
    for b in bones:at(b['name'])
    return result

def apply_blender(rig,source,clip,time):
    import bpy
    from mathutils import Matrix
    import hassler_build as native
    bones,joints,bind=read_rig(source)
    # Authoring can have a newer rest translation than the installed model.
    fresh={}
    for name in bind:
        v=rig.data.bones[name]['native_inverse_bind'];M=np.eye(4);M[:3,:3]=np.array(v[:9]).reshape(3,3);M[:3,3]=v[9:];fresh[name]=np.linalg.inv(M)
    for name,j in joints.items():
        parent=j['parent']
        if name in bind and parent in bind:
            old=np.linalg.inv(bind[parent])@bind[name];new=np.linalg.inv(fresh[parent])@fresh[name];j['origin']+=new[:3,3]-old[:3,3]
    world=evaluate(bones,joints,fresh,clip,time)
    rig.animation_data.action=None
    def depth(name):return 1+depth(rig.data.bones[name].parent.name) if rig.data.bones[name].parent else 0
    for name in sorted(world,key=depth):
        rig.pose.bones[name].matrix=native.C4@Matrix(world[name].tolist());bpy.context.view_layer.update()
    return world

def cull_materials(objects):
    for ob in objects:
        if ob.type!='MESH':continue
        for mat in ob.data.materials:
            if not mat or not mat.use_nodes or mat.get('offline_culling'):continue
            mat['offline_culling']=True;n=mat.node_tree.nodes;l=mat.node_tree.links;out=n.get('Material Output');socket=out.inputs['Surface'].links[0].from_socket
            geo=n.new('ShaderNodeNewGeometry');mix=n.new('ShaderNodeMixShader');trans=n.new('ShaderNodeBsdfTransparent');l.new(geo.outputs['Backfacing'],mix.inputs[0]);l.new(socket,mix.inputs[1]);l.new(trans.outputs[0],mix.inputs[2]);l.new(mix.outputs[0],out.inputs['Surface'])
