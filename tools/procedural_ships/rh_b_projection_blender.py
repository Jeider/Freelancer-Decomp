"""Photograph LOD0 in Blender and map the same registered atlas onto both LODs."""
import json
import math
import faulthandler
import sys
from pathlib import Path
import numpy as np
import bpy
from mathutils import Matrix,Vector
sys.path.insert(0,str(Path(__file__).resolve().parent))
import rh_concept_b_final_blender as h
C=h.C;OUT=h.OUT.parent/'final_v2/lod_refinement';TILE=512;ATLAS=4096


def main():
    stack_file=open(OUT/'blender_stack.txt','w')
    faulthandler.dump_traceback_later(20,repeat=True,file=stack_file)
    data=json.loads((OUT/'input.json').read_text());records=data['records']
    for o in list(bpy.data.objects):bpy.data.objects.remove(o,do_unlink=True)
    scene=bpy.context.scene;scene.render.engine='CYCLES';scene.cycles.samples=8
    scene.cycles.use_denoising=False;scene.render.film_transparent=True
    scene.render.resolution_x=scene.render.resolution_y=TILE;scene.render.resolution_percentage=100
    scene.render.image_settings.file_format='PNG';scene.render.image_settings.color_mode='RGBA'
    scene.view_settings.view_transform='Standard';scene.view_settings.look='None';scene.view_settings.exposure=0
    scene.render.dither_intensity=0
    for key,entry in data['materials'].items():
        material=bpy.data.materials.get(key) or bpy.data.materials.new(key);material.use_nodes=True
        material.use_backface_culling=True;nodes=material.node_tree.nodes;nodes.clear();links=material.node_tree.links
        out=nodes.new('ShaderNodeOutputMaterial');em=nodes.new('ShaderNodeEmission');ao=nodes.new('ShaderNodeAmbientOcclusion')
        ao.inputs['Distance'].default_value=.22;ao.samples=8;ao.only_local=True
        multiply=nodes.new('ShaderNodeMixRGB');multiply.blend_type='MULTIPLY';multiply.inputs[0].default_value=1
        multiply.inputs[1].default_value=(*entry['colour'],1)
        if entry['image']:
            tex=nodes.new('ShaderNodeTexImage');tex.image=bpy.data.images.load(str(OUT/entry['image']),check_existing=True)
            links.new(tex.outputs['Color'],multiply.inputs[2])
        else:multiply.inputs[2].default_value=(1,1,1,1)
        # A weak, fixed contact shade shows photographed cavities while keeping
        # the same colour on faces reached from different projection directions.
        shade=nodes.new('ShaderNodeMixRGB');shade.blend_type='MULTIPLY';shade.inputs[0].default_value=.5
        links.new(multiply.outputs[0],shade.inputs[1]);links.new(ao.outputs['AO'],shade.inputs[2])
        links.new(shade.outputs[0],em.inputs['Color']);links.new(em.outputs[0],out.inputs['Surface'])
    objects={}
    for e in records:
        o,_=h.mesh_object(e,e['id']);objects[e['id']]=o;o.hide_render=True
    aux,_=h.mesh_object(dict(groups=data['auxiliaries']),'Closed glass and baydoors for body photography');aux.hide_render=True
    camera=bpy.data.objects.new('Orthographic projection camera',bpy.data.cameras.new('Projection lens'))
    scene.collection.objects.link(camera);scene.camera=camera;camera.data.type='ORTHO';camera.data.clip_end=500
    photos=OUT/'photos';photos.mkdir(exist_ok=True)
    directions=[((1,0,0),(0,0,-1),(0,1,0)),((-1,0,0),(0,0,1),(0,1,0)),
                ((0,1,0),(1,0,0),(0,0,-1)),((0,-1,0),(1,0,0),(0,0,1)),
                ((0,0,1),(1,0,0),(0,1,0)),((0,0,-1),(-1,0,0),(0,1,0))]
    projectors={};index=0
    for e in records:
        name=e['id']
        if name.startswith('BayDoor') or '_glass_' in name:continue
        obj=objects[name];obj.hide_render=False;aux.hide_render=name!='body'
        p=np.array([C.transposed()@vert.co for vert in obj.data.vertices]);center=(p.min(0)+p.max(0))*.5
        projectors[name]=[]
        for normal,u,w in directions:
            normal,u,w=map(np.array,(normal,u,w));extent=max(np.ptp(p@u),np.ptp(p@w));scale=extent*1.06
            camera.data.ortho_scale=scale;camera.location=C@Vector(center+normal*50)
            camera.rotation_euler=(C@Matrix(np.column_stack((u,w,normal)).tolist())).to_euler()
            image_name=name+'_'+str(len(projectors[name]))+'.png'
            scene.render.filepath=str(photos/image_name)
            if '--geometry-only' not in sys.argv:bpy.ops.render.render(write_still=True)
            projectors[name].append(dict(center=center.tolist(),u=u.tolist(),v=w.tolist(),normal=normal.tolist(),scale=float(scale),
                tile=[index%8,index//8],image='photos/'+image_name))
            index+=1
        obj.hide_render=True;aux.hide_render=True
        print('PHOTOGRAPHED',name,'tiles',index,flush=True)
    assert index<=64
    (OUT/'projectors.json').write_text(json.dumps(projectors,indent=2))

    def simplify(groups,name,ratio):
        print('SIMPLIFY START',name,ratio,flush=True)
        o,slots=h.mesh_object(dict(groups=groups),'Working '+name);o.hide_render=True
        o.data.validate(verbose=False,clean_customdata=False)
        mod=o.modifiers.new('Keep shape at distance','DECIMATE');mod.ratio=ratio;mod.use_collapse_triangulate=True
        ev=o.evaluated_get(bpy.context.evaluated_depsgraph_get());me=ev.to_mesh()
        print('SIMPLIFY EVALUATED',name,len(me.polygons),flush=True)
        gs=h.groups_from_mesh(me,slots);ev.to_mesh_clear();bpy.data.objects.remove(o,do_unlink=True)
        print('SIMPLIFY DONE',name,flush=True)
        return gs
    def project(groups,region):
        result=[]
        for g in groups:
            for tri in g['corners']:
                t=np.array(tri);n=np.cross(t[1,:3]-t[0,:3],t[2,:3]-t[0,:3]);n/=np.linalg.norm(n)
                proj=max(projectors[region],key=lambda q:n@q['normal'])
                q=t[:,:3]-proj['center'];u=q@proj['u']/proj['scale']+.5;vv=.5-q@proj['v']/proj['scale']
                assert min(u.min(),vv.min())>-.06 and max(u.max(),vv.max())<1.06,(region,u,vv)
                tx,ty=proj['tile'];t[:,6]=(tx+u)/8;t[:,7]=(ty+vv)/8
                result.append(t.tolist())
        return [dict(material=0,unused=204,corners=result)]
    levels=[];statistics=[]
    for level in (1,2):
        output={}
        for e in records:
            name=e['id'];source=e['groups'];direct=False
            if '_glass_' in name:gs=data['glass'][level-1];direct=True
            elif name.startswith('BayDoor'):gs=source;direct=True
            elif level==1 and name=='body':gs=data['coarse']['body']+data['coarse']['front']
            elif level==1 and name=='frame':gs=data['coarse']['frame']
            elif level==1 and name=='drum':gs=data['coarse']['mid_drum']
            elif level==1:
                ratio=.60 if name in ('body','Rh_tail_lod1') else .45 if name=='drum' else .58
                if 'upperarm' in name:ratio=1
                gs=simplify(source,name,ratio)
            elif name=='body':
                gs=data['coarse']['body']+data['coarse']['front_solid']
            elif name in ('frame','drum'):gs=data['coarse'][name]
            elif name in data['solid_parts']:gs=data['solid_parts'][name]
            else:
                ratio=.38 if '_engine_' in name or name=='Rh_tail_lod1' else .5
                gs=simplify(source,name,ratio)
            if not direct:gs=project(gs,name)
            if name=='body':gs+=data['bay_interior']
            output.setdefault(e['file'],[]).extend(gs)
        levels.append(output);statistics.append(dict(level=level,triangles=sum(len(g['corners']) for gs in output.values() for g in gs)))
    (OUT/'projected_geometry.json').write_text(json.dumps(levels,separators=(',',':')))
    (OUT/'photo_bake.json').write_text(json.dumps(dict(source_sha256=data['source_sha256'],photos=index,
        projection_tile_size=TILE,working_atlas=ATLAS,native_atlas=2048,levels=statistics,
        method='six Blender orthographic photographs per independently animated part / root region; native diffuse plus weak local AO'),indent=2))
    print('PROJECTED LODS READY',statistics,flush=True)
    faulthandler.cancel_dump_traceback_later();stack_file.close()


if __name__=='__main__':main()
