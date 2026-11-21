"""Bake native-compatible diffuse maps and export approved Hassler geometry/LODs."""
import sys,json,gzip,math,itertools
from pathlib import Path
import bpy,numpy as np
from mathutils import Vector,Matrix
ROOT=Path(__file__).resolve().parents[2];sys.path[:0]=[str(ROOT/'tools'),str(Path(__file__).parent)]
from blender_workspace import configure
import hassler_build as native
from hassler_native_step13 import sha
configure('character_rounding')
TOP=native.OUT/'native_upper';OUT=TOP/'game';SOURCE=TOP/'step_27/hassler_native_upper.blend'

def bake(mat,index,scene):
    name=f'rh_hassler_{index:02d}';copy=mat.copy();nodes=copy.node_tree.nodes;links=copy.node_tree.links;bs=nodes.get('Principled BSDF')
    uvnames={n.uv_map for n in nodes if n.type=='UVMAP'};assert len(uvnames)<=1,(mat.name,uvnames)
    images=[n.image for n in nodes if n.type=='TEX_IMAGE' and n.image]
    size=max(max(i.size) for i in images) if images else 16;size=min(1024,size)
    emit=nodes.new('ShaderNodeEmission');base=bs.inputs['Base Color']
    if base.is_linked:links.new(base.links[0].from_socket,emit.inputs['Color'])
    else:emit.inputs['Color'].default_value=base.default_value
    links.new(emit.outputs[0],nodes.get('Material Output').inputs['Surface'])
    me=bpy.data.meshes.new('Bake plane');me.from_pydata([(0,0,0),(1,0,0),(1,1,0),(0,1,0)],[],[(0,1,2,3)]);me.update()
    for uvname in ['Bake UV']+sorted(uvnames):
        layer=me.uv_layers.new(name=uvname)
        for i,q in enumerate(((0,0),(1,0),(1,1),(0,1))):layer.data[i].uv=q
    me.uv_layers.active_index=0;me.uv_layers[0].active_render=True
    ob=bpy.data.objects.new('Bake plane',me);scene.collection.objects.link(ob);me.materials.append(copy)
    target=bpy.data.images.new(name,width=size,height=size,alpha=False);target.colorspace_settings.name='sRGB'
    node=nodes.new('ShaderNodeTexImage');node.image=target;nodes.active=node
    bpy.context.window.scene=scene;bpy.ops.object.select_all(action='DESELECT');ob.select_set(True);bpy.context.view_layer.objects.active=ob
    bpy.ops.object.bake(type='EMIT',margin=0,use_clear=True)
    path=OUT/'textures'/(name+'.png');target.filepath_raw=str(path);target.file_format='PNG';target.save()
    data={'source_material':mat.name,'name':name,'texture':str(path),'texture_sha256':sha(path),'uv_layer':next(iter(uvnames),None),'size':size,'roughness':float(bs.inputs['Roughness'].default_value),'metallic':float(bs.inputs['Metallic'].default_value)}
    bpy.data.objects.remove(ob,do_unlink=True);bpy.data.meshes.remove(me);bpy.data.materials.remove(copy);bpy.data.images.remove(target)
    print('BAKED',name,mat.name,size,flush=True);return data

def export_mesh(ob,matids,materials,bones,poses):
    ev=ob.evaluated_get(bpy.context.evaluated_depsgraph_get());me=ev.to_mesh();me.calc_loop_triangles()
    names=[g.name for g in ob.vertex_groups];vertices=[];faces={};lookup={};maxdiscard=0.;maxposeerror=0.;normals=me.corner_normals;skin_cache={}
    for tri in me.loop_triangles:
        mat=me.materials[tri.material_index];mi=matids[mat.name];uvname=materials[mi]['uv_layer'];uv=me.uv_layers[uvname] if uvname else me.uv_layers[0]
        face=[]
        for li in tri.loops:
            vi=me.loops[li].vertex_index;v=me.vertices[vi];p=native.C.inverted()@v.co
            normal=normals[li].vector if normals[li].vector.length>.01 else tri.normal
            n=native.C.inverted()@normal;n.normalize()
            if vi not in skin_cache:
                w=sorted(((bones.index(names[g.group]),g.weight) for g in v.groups if g.weight>1e-7),key=lambda q:-q[1]);assert w
                total=sum(value for _,value in w);w=[(i,value/total) for i,value in w];maxdiscard=max(maxdiscard,sum(value for _,value in w[4:]))
                if len(w)>4:
                    ids=[i for i,_ in w];weights=np.array([value for _,value in w]);posed=(poses[:,ids]@np.r_[list(p),1.])[:,:,:3];target=np.einsum('pbc,b->pc',posed,weights)
                    best=None
                    for subset in itertools.combinations(range(len(ids)),4):
                        a=posed[:,subset,:].transpose(0,2,1).reshape(-1,4);lhs=np.vstack((a,np.ones((1,4))*10));rhs=np.r_[target.ravel(),10.]
                        fitted=np.linalg.lstsq(lhs,rhs,rcond=None)[0]
                        if min(fitted)<-1e-6:continue
                        fitted=np.maximum(fitted,0);fitted/=fitted.sum();error=float(np.linalg.norm((a@fitted).reshape(-1,3)-target,axis=1).max())
                        if best is None or error<best[0]:best=(error,[(ids[j],float(value)) for j,value in zip(subset,fitted) if value>1e-8])
                    assert best is not None;maxposeerror=max(maxposeerror,best[0]);w=best[1]
                skin_cache[vi]=tuple(sorted(w))
            w=skin_cache[vi]
            q=uv.data[li].uv;tex=(float(q.x),float(1-q.y))
            key=(vi,tuple(round(float(x),7) for x in n),tex,w)
            if key not in lookup:lookup[key]=len(vertices);vertices.append([list(p),list(n),list(tex),w])
            face.append(lookup[key])
        a,b,c=[np.array(vertices[i][0]) for i in face]
        if np.linalg.norm(np.cross(b-a,c-a))>1e-12:faces.setdefault(mi,[]).append(face)
    used=sorted({i for fs in faces.values() for f in fs for i in f});remap={v:i for i,v in enumerate(used)}
    vertices=[vertices[i] for i in used];faces={mi:[[remap[i] for i in f] for f in fs] for mi,fs in faces.items()}
    ev.to_mesh_clear();return vertices,faces,maxdiscard,maxposeerror

def main():
    OUT.mkdir(exist_ok=True);(OUT/'textures').mkdir(exist_ok=True);digest=sha(SOURCE)
    bpy.ops.wm.open_mainfile(filepath=str(SOURCE));configure('character_rounding');scene=bpy.context.scene;scene.frame_set(1)
    obs=sorted([o for o in bpy.data.collections['EDIT — native costume upper study'].objects if o.type=='MESH'],key=lambda o:o.name)
    used={}
    for ob in obs:
        ev=ob.evaluated_get(bpy.context.evaluated_depsgraph_get());me=ev.to_mesh()
        for face in me.polygons:used[me.materials[face.material_index].name]=me.materials[face.material_index]
        ev.to_mesh_clear()
    if '--reuse-bakes' in sys.argv:
        previous=json.loads((OUT/'export.json').read_text(encoding='utf8'));assert previous['source_sha256']==digest
        materials=previous['materials'];assert [m['source_material'] for m in materials]==sorted(used)
        for m in materials:assert sha(Path(m['texture']))==m['texture_sha256']
    else:
        baking=bpy.data.scenes.new('Hassler diffuse transfer');baking.render.engine='CYCLES';baking.cycles.samples=1;baking.cycles.device='CPU';baking.render.bake.use_selected_to_active=False
        materials=[]
        for i,(name,mat) in enumerate(sorted(used.items())):materials.append(bake(mat,i,baking))
        bpy.context.window.scene=scene;bpy.data.scenes.remove(baking)
    matids={m['source_material']:i for i,m in enumerate(materials)};rig=bpy.data.objects['RIG — native Rheinland'];bones=[b['name'] for b in native.load('body')['bones']]
    poses=[]
    for frame in (1,30,60,90,120):
        scene.frame_set(frame);poses.append([np.array(native.C4.inverted()@rig.pose.bones[n].matrix@rig.data.bones[n].matrix_local.inverted()@native.C4) for n in bones])
    poses=np.array(poses);scene.frame_set(1)
    temp=native.collection('EXPORT temporary evaluated geometry');copies=[]
    for ob in obs:
        copy=ob.copy();copy.data=ob.data.copy();copy.name=ob.name+' export';copy.parent=None;copy.matrix_world=Matrix.Identity(4);temp.objects.link(copy)
        for modifier in list(copy.modifiers):
            if modifier.type=='ARMATURE':copy.modifiers.remove(modifier)
        copies.append(copy)
    lods=[]
    for level,ratio in enumerate((1.,.32,.18,.10,.06)):
        records=[];groups={};discard=0.;poseerror=0.;parts=[]
        for ob in copies:
            # Native trousers are already only 322 triangles. Preserve their
            # UV islands, knees and feet, plus the thin belt/fittings and seam.
            keep=ob.name.startswith(('00 ','12 ','19 ','20 ','21 ','23 ','24 '))
            local_ratio=ratio
            if ob.name.startswith(('14 ','16 ')):local_ratio=max(ratio,.18)
            if ob.name.startswith(('11 ','18 ')):local_ratio=max(ratio,.24)
            if ob.name.startswith('13.') and level>=3:continue
            if level:
                ob.data.calc_loop_triangles();count=len(ob.data.loop_triangles);target=max(24,int(count*local_ratio));mod=ob.modifiers.new('Distant simplification','DECIMATE');mod.ratio=1. if keep else min(1.,target/max(count,1));mod.use_collapse_triangulate=True
                native.activate(ob);bpy.ops.object.modifier_move_to_index(modifier=mod.name,index=0)
            vs,fs,err,pe=export_mesh(ob,matids,materials,bones,poses);offset=len(records);records+=vs;discard=max(discard,err);poseerror=max(poseerror,pe)
            for mi,faces in fs.items():groups.setdefault(mi,[]).extend([[x+offset for x in face] for face in faces])
            parts.append({'object':ob.name,'vertices':len(vs),'triangles':sum(map(len,fs.values()))})
            if level:ob.modifiers.remove(mod)
        assert len(records)<65536,(level,len(records));assert poseerror<.004,(level,poseerror)
        payload={'records':records,'groups':groups,'bone_names':bones}
        path=OUT/f'mesh{level}.json.gz';path.write_bytes(gzip.compress(json.dumps(payload,separators=(',',':')).encode(),mtime=0))
        lods.append({'level':level,'vertices':len(records),'triangles':sum(map(len,groups.values())),'naive_top4_discard_would_be':discard,'fitted_top4_pose_error_m':poseerror,'path':str(path),'sha256':sha(path),'parts':parts})
        print('LOD',level,len(records),lods[-1]['triangles'],'skin error',poseerror,flush=True)
    result={'source':str(SOURCE),'source_sha256':digest,'head_offset_m':float(bpy.data.objects['Hassler head — native unchanged']['head_fit_offset_m'][2]),'materials':materials,'lods':lods,'bone_names':bones,'native_inverse_bind':{n:list(rig.data.bones[n]['native_inverse_bind']) for n in bones},'body_coordinates':'native: x, Blender z, -Blender y; no studio floor translation','uv_conversion':'native v = 1 - Blender v','game_installed':False}
    (OUT/'export.json').write_text(json.dumps(result,ensure_ascii=False,indent=2)+'\n',encoding='utf8');assert sha(SOURCE)==digest

if __name__=='__main__':main()
