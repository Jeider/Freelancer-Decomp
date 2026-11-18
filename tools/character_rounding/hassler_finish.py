"""Finalize the normal-map tangent frame and actual culling views."""
import sys,json,warnings
from pathlib import Path
warnings.filterwarnings('ignore',category=DeprecationWarning)
import bpy,numpy as np
from mathutils import Vector
ROOT=Path(__file__).resolve().parents[2];sys.path.insert(0,str(ROOT/'tools'));sys.path.insert(0,str(Path(__file__).parent))
from blender_workspace import configure
from hassler_build import OUT,activate,load,C4
from mathutils import Matrix
configure('character_rounding')

def smooth_weights(ob):
    if ob.get('native_weight_smoothing_done'):return
    me=ob.data;p=np.array([v.co[:] for v in me.vertices]);weights=np.zeros((len(p),len(ob.vertex_groups)))
    for v in me.vertices:
        for g in v.groups:weights[v.index,g.group]=g.weight
    edges=np.array([tuple(e.vertices) for e in me.edges]);u=np.r_[edges[:,0],edges[:,1]];v=np.r_[edges[:,1],edges[:,0]]
    buckets={}
    for i,point in enumerate(p):buckets.setdefault(tuple(point.round(6)),[]).append(i)
    duplicates=[ids for ids in buckets.values() if len(ids)>1]
    strength=1/np.maximum(np.linalg.norm(p[u]-p[v],axis=1),.001)
    den=np.bincount(u,weights=strength,minlength=len(p))
    for _ in range(24):
        average=np.column_stack([np.bincount(u,weights=strength*weights[v,j],minlength=len(p))/np.maximum(den,1e-9) for j in range(weights.shape[1])])
        weights=.55*weights+.45*average
        for ids in duplicates:weights[ids]=weights[ids].mean(0)
    top=np.argsort(weights,axis=1)[:,-4:];mask=np.zeros_like(weights);np.put_along_axis(mask,top,np.take_along_axis(weights,top,axis=1),axis=1)
    mask[mask<.003]=0;mask/=mask.sum(1)[:,None]
    for group in ob.vertex_groups:group.remove(list(range(len(p))))
    for i,row in enumerate(mask):
        for j in np.flatnonzero(row):ob.vertex_groups[j].add([i],float(row[j]),'REPLACE')
    ob['native_weight_smoothing_done']=True
    print('SMOOTHED NATIVE WEIGHT TRANSFER',flush=True)

def main():
    bpy.ops.wm.open_mainfile(filepath=str(OUT/'hassler_rigged.blend'));configure('character_rounding')
    scene=bpy.context.scene;scene.frame_set(1);ob=bpy.data.objects['Hassler — EDIT clothing'];activate(ob)
    smooth_weights(ob)
    body=load('body')
    for kind,hp,name in [('head','hp_head','Hassler head — native unchanged'),('left_hand','hp_left b','Left glove — native unchanged'),('right_hand','hp_right b','Right glove — native unchanged')]:
        data=load(kind);part=bpy.data.objects[name]
        transform=C4@Matrix((np.array(body['hardpoints'][hp]['matrix'])@np.linalg.inv(np.array(data['hardpoints'][hp]['matrix']))).tolist())
        normal_matrix=transform.to_3x3().inverted().transposed()
        part.data.normals_split_custom_set([(normal_matrix@Vector(data['normals'][l.vertex_index])).normalized() for l in part.data.loops])
    final=ob.data.materials[0];source=bpy.data.objects['SOURCE Meshy — full density'].data.materials[0]
    # The old normal texture is defined in the original UV tangent frame.
    # Naming that UV explicitly is essential while baking onto another layout.
    need_fix=any(n.type=='NORMAL_MAP' and n.uv_map!='Meshy source UV' for n in source.node_tree.nodes)
    if need_fix:
        for n in source.node_tree.nodes:
            if n.type=='NORMAL_MAP':n.uv_map='Meshy source UV'
        blank=bpy.data.materials.new('Temporary waist normal');blank.use_nodes=True
        ob.data.materials.clear();ob.data.materials.append(source);ob.data.materials.append(blank)
        fit=np.load(OUT/'fit.npz');p=fit['source_positions']
        for f in ob.data.polygons:
            x,y,z=p[list(f.vertices)].mean(0);f.material_index=1 if .035-1e-6<z<.350+1e-6 and abs(x)<.285 else 0
        image=next(n.image for n in final.node_tree.nodes if n.type=='TEX_IMAGE' and n.label=='Normal')
        for mat in (source,blank):
            tex=mat.node_tree.nodes.new('ShaderNodeTexImage');tex.image=image;mat.node_tree.nodes.active=tex
        scene.cycles.samples=8;scene.render.bake.margin=8;scene.render.bake.use_selected_to_active=False
        bpy.ops.object.bake(type='NORMAL');image.save()
        ob.data.materials.clear();ob.data.materials.append(final)
        for f in ob.data.polygons:f.material_index=0
    scene.cycles.samples=24;cam=scene.camera
    shots=[('front',1,(0,1,0),(0,0,.92),2.10),('back',1,(0,-1,0),(0,0,.92),2.10),
           ('upper',1,(.25,1,.15),(0,0,1.47),.85),('elbows',30,(.3,1,.1),(0,0,1.27),1.35),
           ('step',90,(.5,1,.15),(0,0,.92),2.1),('side',1,(1,0,.03),(0,0,.92),2.1)]
    for label,frame,direction,center,scale in shots:
        scene.frame_set(frame);d=Vector(direction).normalized();cam.location=Vector(center)+d*5
        cam.rotation_euler=(-d).to_track_quat('-Z','Y').to_euler();cam.data.ortho_scale=scale
        scene.render.filepath=str(OUT/'preview'/(label+'.png'));bpy.ops.render.render(write_still=True)
    clay=bpy.data.materials.new('Actual back-face transparency diagnostic');clay.use_nodes=True
    nodes=clay.node_tree.nodes;links=clay.node_tree.links;bs=nodes.get('Principled BSDF');bs.inputs['Base Color'].default_value=(.3,.36,.4,1)
    geo=nodes.new('ShaderNodeNewGeometry');transparent=nodes.new('ShaderNodeBsdfTransparent');mix=nodes.new('ShaderNodeMixShader')
    links.new(geo.outputs['Backfacing'],mix.inputs[0]);links.new(bs.outputs[0],mix.inputs[1]);links.new(transparent.outputs[0],mix.inputs[2]);links.new(mix.outputs[0],nodes.get('Material Output').inputs['Surface'])
    scene.view_layers[0].material_override=clay;scene.frame_set(1)
    for label,direction in [('culling_front',(.5,1,.15)),('culling_back',(.5,-1,.15))]:
        d=Vector(direction).normalized();cam.location=Vector((0,0,1.05))+d*5;cam.rotation_euler=(-d).to_track_quat('-Z','Y').to_euler();cam.data.ortho_scale=1.95
        scene.render.filepath=str(OUT/'preview'/(label+'.png'));bpy.ops.render.render(write_still=True)
    scene.view_layers[0].material_override=None;scene.frame_set(1)
    d=Vector((.2,1,.08)).normalized();cam.location=Vector((0,0,1))+d*5;cam.rotation_euler=(-d).to_track_quat('-Z','Y').to_euler();cam.data.ortho_scale=2.1
    rig=bpy.data.objects['RIG — native Rheinland'];activate(rig)
    # Keep the useful authoring instructions inside the file as well.
    text=bpy.data.texts.get('README — editing') or bpy.data.texts.new('README — editing');text.clear();text.write((OUT/'README.txt').read_text(encoding='utf8'))
    bpy.ops.wm.save_as_mainfile(filepath=str(OUT/'hassler_rigged.blend'),compress=True)
    print(json.dumps({'normal_tangent_frame_corrected':need_fix,'actual_culling_views':True}))

if __name__=='__main__':main()
