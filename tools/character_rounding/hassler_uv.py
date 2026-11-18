"""Named clothing charts and rebaked maps for the editable Hassler prototype."""
import sys,json,math,warnings
from pathlib import Path
warnings.filterwarnings('ignore',category=DeprecationWarning)
import bpy,bmesh,numpy as np
from mathutils import Vector
ROOT=Path(__file__).resolve().parents[2];sys.path.insert(0,str(ROOT/'tools'));sys.path.insert(0,str(Path(__file__).parent))
from blender_workspace import configure
from hassler_build import OUT,activate,dump
configure('character_rounding')
SIZE=4096

def fix_closed_details(ob):
    """Give tiny closed relief pieces their own cut charts instead of UV points."""
    me=ob.data;me.calc_loop_triangles();uv=me.uv_layers['EDIT — clothing charts'];bad=set()
    for tri in me.loop_triangles:
        t=np.array([uv.data[l].uv[:] for l in tri.loops]);a=t[1]-t[0];b=t[2]-t[0]
        if abs(a[0]*b[1]-a[1]*b[0])<1e-13:bad.add(tri.polygon_index)
    if not bad:return 0
    metadata=json.loads((OUT/'uv_regions.json').read_text());regions=metadata['regions']
    # Find a vacant rectangular area outside every existing chart block.
    best=None
    for x in np.arange(.0,.91,.025):
        for y in np.arange(.0,.91,.025):
            for w in (.15,.175,.20,.225,.25,.275,.30,.35,.4):
                h=w
                if x+w>.995 or y+h>.995:continue
                if any(x<r['bounds'][1][0]+.004 and x+w>r['bounds'][0][0]-.004 and y<r['bounds'][1][1]+.004 and y+h>r['bounds'][0][1]-.004 for r in regions):continue
                if best is None or w>best[2]:best=(x,y,w)
    assert best is not None,'No unused atlas area for closed relief'
    activate(ob);bpy.ops.object.mode_set(mode='EDIT');bpy.ops.mesh.select_all(action='DESELECT')
    bm=bmesh.from_edit_mesh(me);bm.faces.ensure_lookup_table()
    for i in bad:bm.faces[i].select_set(True)
    bmesh.update_edit_mesh(me)
    bpy.ops.uv.smart_project(angle_limit=math.radians(66),island_margin=.035,area_weight=.1,correct_aspect=True,scale_to_bounds=True)
    bpy.ops.object.mode_set(mode='OBJECT');uv=me.uv_layers['EDIT — clothing charts']
    x,y,w=best;pad=10/SIZE;loops=[l for i in bad for l in me.polygons[i].loop_indices]
    for l in loops:uv.data[l].uv=Vector((x+pad,y+pad))+uv.data[l].uv*(w-2*pad)
    name='z_small_relief_chain_and_undersides';ids=sorted([r['name'] for r in regions]+[name]);attr=me.attributes['clothing_region']
    for i in bad:attr.data[i].value=ids.index(name)
    regions.append({'name':name,'faces':len(bad),'area_m2':sum(me.polygons[i].area for i in bad),'bounds':[[x,y],[x+w,y+w]],'note':'Closed relief details unfolded separately to eliminate collapsed UV faces'})
    metadata['closed_detail_faces_repaired']=len(bad);dump(OUT/'uv_regions.json',metadata)
    print('CLOSED DETAIL UV REPAIRED',len(bad),best,flush=True);return len(bad)

def restore_source_materials(ob):
    source=bpy.data.objects['SOURCE Meshy — full density'].data.materials[0]
    waist=bpy.data.materials.new('Waist source for UV rebake');waist.use_nodes=True;bs=waist.node_tree.nodes.get('Principled BSDF')
    uv=waist.node_tree.nodes.new('ShaderNodeUVMap');uv.uv_map='Meshy source UV'
    for key in ('Base Color','Roughness','Metallic'):
        image=bpy.data.images.load(str(OUT/'textures'/('waist_'+key.replace(' ','_').lower()+'.png')),check_existing=True)
        if key!='Base Color':image.colorspace_settings.name='Non-Color'
        tex=waist.node_tree.nodes.new('ShaderNodeTexImage');tex.image=image;waist.node_tree.links.new(uv.outputs[0],tex.inputs[0]);waist.node_tree.links.new(tex.outputs[0],bs.inputs[key])
    ob.data.materials.clear();ob.data.materials.append(source);ob.data.materials.append(waist)
    p=np.load(OUT/'fit.npz')['source_positions']
    for f in ob.data.polygons:
        x,y,z=p[list(f.vertices)].mean(0);f.material_index=1 if .035-1e-6<z<.350+1e-6 and abs(x)<.285 else 0

def categories(ob,fit):
    p=fit['source_positions'];arm=fit['arm'];labels=[]
    for f in ob.data.polygons:
        x,y,z=p[list(f.vertices)].mean(0);side='R' if x>0 else 'L';view='front' if y>-.025 else 'back'
        if arm[list(f.vertices)].mean()>.55:label=('bracer' if z<.29 else 'sleeve')+'_'+side+'_'+view
        elif z<.125:label=('boot' if z<-.48 else 'trousers')+'_'+side+'_'+view
        elif z<.225:label='belt_'+view
        elif z>.59 and abs(x)>.17:label='epaulette_'+side+'_'+view
        elif z>.51 and abs(x)<.175:label='collar_'+view
        else:label='torso_'+view
        labels.append(label)
    return labels

def unwrap(ob,labels,fit):
    me=ob.data;uv=me.uv_layers.get('EDIT — clothing charts') or me.uv_layers.new(name='EDIT — clothing charts')
    me.uv_layers.active=uv;uv.active_render=True
    activate(ob);bpy.context.tool_settings.mesh_select_mode=(False,False,True)
    unique=sorted(set(labels));ids={s:i for i,s in enumerate(unique)}
    attr=me.attributes.new('clothing_region','INT','FACE');attr.data.foreach_set('value',[ids[s] for s in labels])
    edge_faces={}
    for f in me.polygons:
        for e in f.edge_keys:edge_faces.setdefault(tuple(sorted(e)),set()).add(labels[f.index])
    for e in me.edges:e.use_seam=len(edge_faces.get(tuple(sorted(e.vertices)),set()))!=1
    patches=[]
    for label in unique:
        selected=[f.index for f in me.polygons if labels[f.index]==label]
        mask=np.zeros(len(me.polygons),dtype=bool);mask[selected]=True;me.polygons.foreach_set('select',mask)
        bpy.ops.object.mode_set(mode='EDIT');bpy.ops.uv.unwrap(method='ANGLE_BASED',margin=.015);bpy.ops.object.mode_set(mode='OBJECT')
        uv=me.uv_layers.active
        loops=[l for i in selected for l in me.polygons[i].loop_indices]
        points=np.array([uv.data[l].uv[:] for l in loops]);z=np.array([fit['source_positions'][me.loops[l].vertex_index,2] for l in loops])
        # Keep the clothing's vertical direction legible in the editing atlas.
        gradient=np.linalg.lstsq(np.column_stack((points,np.ones(len(points)))),z,rcond=None)[0][:2]
        if np.linalg.norm(gradient)>1e-6:
            v=gradient/np.linalg.norm(gradient);rotation=np.array([[v[1],-v[0]],[v[0],v[1]]]);points=points@rotation.T
        points-=points.min(0);extent=np.maximum(points.max(0),1e-6)
        area3=sum(me.polygons[i].area for i in selected)
        area_uv=0.;cursor=0
        for i in selected:
            n=len(me.polygons[i].vertices);poly=points[cursor:cursor+n];cursor+=n
            area_uv+=abs(np.dot(poly[:,0],np.roll(poly[:,1],-1))-np.dot(poly[:,1],np.roll(poly[:,0],-1)))*.5
        scale=math.sqrt(area3/max(area_uv,1e-9));points*=scale;extent*=scale
        patches.append({'name':label,'loops':loops,'points':points,'extent':extent,'faces':len(selected),'area_m2':area3})
        print('UNWRAPPED',label,len(selected),flush=True)
    # Shelf packing keeps all islands belonging to a garment region together.
    patches.sort(key=lambda p:-p['extent'][1]);margin=12/SIZE
    def pack(scale):
        x=y=row=0.;positions=[]
        for p in patches:
            w,h=p['extent']*scale+2*margin
            if w>1 or h>1:return None
            if x+w>1:x=0.;y+=row;row=0.
            if y+h>1:return None
            positions.append((x+margin,y+margin));x+=w;row=max(row,h)
        return positions
    lo,hi=0.,10.
    for _ in range(45):
        mid=(lo+hi)*.5
        if pack(mid) is None:hi=mid
        else:lo=mid
    positions=pack(lo);report=[]
    for p,origin in zip(patches,positions):
        points=p['points']*lo+origin
        for l,t in zip(p['loops'],points):uv.data[l].uv=t
        report.append({'name':p['name'],'faces':p['faces'],'area_m2':p['area_m2'],'bounds':[points.min(0).tolist(),points.max(0).tolist()]})
    me.polygons.foreach_set('select',np.ones(len(me.polygons),dtype=bool));me.update()
    dump(OUT/'uv_regions.json',{'atlas_size':SIZE,'uv_layer':uv.name,'regions':report,'source_uv_retained':True})
    return report

def bake(ob):
    scene=bpy.context.scene;scene.frame_set(1);scene.cycles.samples=8
    scene.render.bake.use_selected_to_active=False;scene.render.bake.margin=8;scene.render.bake.margin_type='EXTEND'
    activate(ob);mats=list(ob.data.materials);outputs=[];targets=[]
    for mat in mats:
        nodes=mat.node_tree.nodes;output=next(n for n in nodes if n.type=='OUTPUT_MATERIAL')
        for node in nodes:
            if node.type=='NORMAL_MAP':node.uv_map='Meshy source UV'
        outputs.append((mat,output,output.inputs['Surface'].links[0].from_socket))
        target=nodes.new('ShaderNodeTexImage');target.name='Bake target';targets.append(target)
    result={}
    for key,filename,kind in [('Base Color','hassler_color.png','EMIT'),('Roughness','hassler_roughness.png','EMIT'),('Metallic','hassler_metallic.png','EMIT'),('Normal','hassler_normal.png','NORMAL')]:
        im=bpy.data.images.new(filename,width=SIZE,height=SIZE,alpha=False)
        if key!='Base Color':im.colorspace_settings.name='Non-Color'
        for target,(mat,output,socket) in zip(targets,outputs):
            target.image=im;mat.node_tree.nodes.active=target
            if kind=='EMIT':
                bs=mat.node_tree.nodes.get('Principled BSDF');em=mat.node_tree.nodes.new('ShaderNodeEmission');em.name='Bake emission'
                source=bs.inputs[key]
                if source.is_linked:mat.node_tree.links.new(source.links[0].from_socket,em.inputs['Color'])
                else:
                    value=source.default_value;em.inputs['Color'].default_value=tuple(value) if key=='Base Color' else (value,value,value,1)
                mat.node_tree.links.new(em.outputs[0],output.inputs['Surface'])
            else:mat.node_tree.links.new(socket,output.inputs['Surface'])
        bpy.ops.object.bake(type=kind)
        im.filepath_raw=str(OUT/'textures'/filename);im.file_format='PNG';im.save();result[key]=im
        for mat,output,socket in outputs:
            mat.node_tree.links.new(socket,output.inputs['Surface'])
            node=mat.node_tree.nodes.get('Bake emission')
            if node:mat.node_tree.nodes.remove(node)
        print('BAKED',filename,flush=True)
    mat=bpy.data.materials.new('Hassler — editable clothing atlas');mat.use_nodes=True;mat.use_backface_culling=True
    bs=mat.node_tree.nodes.get('Principled BSDF');uv=mat.node_tree.nodes.new('ShaderNodeUVMap');uv.uv_map='EDIT — clothing charts'
    for key,im in result.items():
        tex=mat.node_tree.nodes.new('ShaderNodeTexImage');tex.image=im;tex.label=key;mat.node_tree.links.new(uv.outputs[0],tex.inputs[0])
        if key=='Normal':
            normal=mat.node_tree.nodes.new('ShaderNodeNormalMap');normal.uv_map=uv.uv_map;mat.node_tree.links.new(tex.outputs[0],normal.inputs['Color']);mat.node_tree.links.new(normal.outputs[0],bs.inputs['Normal'])
        else:mat.node_tree.links.new(tex.outputs[0],bs.inputs[key])
    ob.data.materials.clear();ob.data.materials.append(mat)
    for f in ob.data.polygons:f.material_index=0
    return result

def main():
    bpy.ops.wm.open_mainfile(filepath=str(OUT/'hassler_rigged.blend'));configure('character_rounding')
    ob=bpy.data.objects['Hassler — EDIT clothing'];fit=np.load(OUT/'fit.npz');labels=categories(ob,fit)
    if '--repair' in sys.argv:
        fix_closed_details(ob);restore_source_materials(ob)
    else:
        unwrap(ob,labels,fit);fix_closed_details(ob)
    report=json.loads((OUT/'uv_regions.json').read_text())['regions'];bake(ob)
    scene=bpy.context.scene;cam=scene.camera;scene.cycles.samples=24
    for label,frame,direction,center,scale in [('front',1,(0,1,0),(0,0,.92),2.10),('back',1,(0,-1,0),(0,0,.92),2.10),
           ('upper',1,(.25,1,.15),(0,0,1.47),.85),('elbows',30,(.3,1,.1),(0,0,1.27),1.35),('step',90,(.5,1,.15),(0,0,.92),2.1)]:
        scene.frame_set(frame);d=Vector(direction).normalized();cam.location=Vector(center)+d*5
        cam.rotation_euler=(-d).to_track_quat('-Z','Y').to_euler();cam.data.ortho_scale=scale
        scene.render.filepath=str(OUT/'preview'/(label+'.png'));bpy.ops.render.render(write_still=True)
    scene.frame_set(1);d=Vector((.2,1,.08)).normalized();cam.location=Vector((0,0,1))+d*5
    cam.rotation_euler=(-d).to_track_quat('-Z','Y').to_euler();cam.data.ortho_scale=2.1
    rig=bpy.data.objects['RIG — native Rheinland'];activate(rig)
    metadata=json.loads((OUT/'prototype_report.json').read_text());metadata['uv_status']='named clothing charts; diffuse, normal, roughness and metallic rebaked at 4096';metadata['uv_regions']=len(report)
    dump(OUT/'prototype_report.json',metadata);bpy.data.texts['README — Hassler prototype'].clear();bpy.data.texts['README — Hassler prototype'].write(json.dumps(metadata,indent=2))
    # Retain packed embedded FBX resources for source references; edit maps are
    # external, human-readable PNGs beside this file.
    bpy.ops.wm.save_as_mainfile(filepath=str(OUT/'hassler_rigged.blend'),compress=True)
    print('EDITABLE UV COMPLETE',len(report),flush=True)

if __name__=='__main__':main()
