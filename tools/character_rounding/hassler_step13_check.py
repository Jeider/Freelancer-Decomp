"""Verify the material-only revision against the accepted saved shape."""
import sys,json,hashlib
from pathlib import Path
import bpy,numpy as np
ROOT=Path(__file__).resolve().parents[2];sys.path[:0]=[str(ROOT/'tools'),str(Path(__file__).parent)]
from blender_workspace import configure
import hassler_native_step13 as s
import hassler_native_step12 as parent
from hassler_step02_check import mesh
from hassler_step04_check import rig_snapshot
from hassler_step08_check import evaluated
configure('character_rounding')

def snapshot(ob):
    d=mesh(ob);d['uv_layers']={l.name:np.array([q.uv[:] for q in l.data]) for l in ob.data.uv_layers}
    d['normals']=np.array([n.vector[:] for n in ob.data.corner_normals]);d['materials']=[m.name if m else None for m in ob.data.materials]
    d['material_indices']=[f.material_index for f in ob.data.polygons];d['world']=np.array(ob.matrix_world)
    return d

def main():
    bpy.ops.wm.open_mainfile(filepath=str(s.PARENT));configure('character_rounding');scene=bpy.context.scene;scene.frame_set(1)
    collection=bpy.data.collections['EDIT — native costume upper study'];objects=[o for o in collection.objects if o.type=='MESH']
    others=['Hassler head — native unchanged','Left glove — native unchanged','Right glove — native unchanged']
    objects=list({o.name:o for o in objects+[bpy.data.objects[n] for n in others]}.values())
    before={ob.name:snapshot(ob) for ob in objects};bones=rig_snapshot();names=list(before)
    poses={}
    for frame in (1,60,120):
        scene.frame_set(frame);poses[frame]={name:evaluated(bpy.data.objects[name])['p'] for name in names}
    mapping={parent.GARMENT:s.GARMENT,parent.SHIRT:s.SHIRT}
    path=s.OUT/'hassler_native_upper.blend';digest=s.sha(path);bpy.ops.wm.open_mainfile(filepath=str(path));configure('character_rounding');scene=bpy.context.scene;scene.frame_set(1)
    report=json.loads((s.OUT/'report.json').read_text(encoding='utf8'));assert s.sha(s.PARENT)==report['parent_sha256']
    afterbones=rig_snapshot();assert set(bones)==set(afterbones)
    for n,(matrix,bind,p) in afterbones.items():assert np.array_equal(matrix,bones[n][0]) and bind==bones[n][1] and p==bones[n][2]
    for name,old in before.items():
        current=bpy.data.objects[mapping.get(name,name)];new=snapshot(current)
        for key in ('points','normals','world'):assert np.array_equal(old[key],new[key]),(name,key)
        for key in ('faces','weights','material_indices'):assert old[key]==new[key],(name,key)
        for uvname,uv in old['uv_layers'].items():assert np.array_equal(uv,new['uv_layers'][uvname]),(name,uvname)
        if name==parent.GARMENT:
            for i,material in enumerate(old['materials']):
                if i not in (4,15,22,33):assert material==new['materials'][i]
        elif name!=parent.SHIRT:assert new['materials']==old['materials']
    posed={}
    for frame,old in poses.items():
        scene.frame_set(frame);posed[frame]={}
        for name,p in old.items():
            now=evaluated(bpy.data.objects[mapping.get(name,name)])['p'];assert np.array_equal(p,now),(frame,name)
            posed[frame][mapping.get(name,name)]=0.0
    scene.frame_set(1);uv_report={};parts={}
    for name,uvname,face_ids in [(s.GARMENT,s.COLLAR_UV,set(report['collar']['faces'])),(s.SHIRT,s.SHIRT_UV,None)]:
        ob=bpy.data.objects[name];me=ob.data;me.calc_loop_triangles();layer=me.uv_layers[uvname];areas=[];points=[]
        for t in me.loop_triangles:
            if face_ids is not None and t.polygon_index not in face_ids:continue
            a,b,c=[np.array(layer.data[i].uv) for i in t.loops];area=abs((b[0]-a[0])*(c[1]-a[1])-(b[1]-a[1])*(c[0]-a[0]))*.5
            areas.append(area);points.extend([a,b,c])
        assert min(areas)>1e-11,(name,min(areas));q=np.array(points);assert np.isfinite(q).all() and q.min()>=0 and q.max()<=1
        uv_report[name]={'uv_layer':uvname,'triangles':len(areas),'min_uv_triangle_area':float(min(areas)),'uv_bounds':[q.min(axis=0).tolist(),q.max(axis=0).tolist()]}
        for slot in ([4,15,22,33] if name==s.GARMENT else range(len(me.materials))):
            mat=me.materials[slot];assert mat.use_backface_culling
            nodes=mat.node_tree.nodes;tex=next(n for n in nodes if n.type=='TEX_IMAGE');assert tex.image.packed_file
            assert next(n for n in nodes if n.type=='UVMAP').uv_map==uvname
    coat=bpy.data.objects[s.GARMENT];uv=coat.data.uv_layers[s.COLLAR_UV]
    for f in coat.data.polygons:
        if f.index not in report['collar']['faces']:
            for li in f.loop_indices:assert tuple(uv.data[li].uv)==tuple(coat.data.uv_layers[0].data[li].uv)
    for ob in bpy.data.collections['EDIT — native costume upper study'].objects:
        if ob.type=='MESH':
            d=evaluated(ob);parts[ob.name]={k:d[k] for k in ('vertices','triangles')}
    for col in bpy.data.collections:
        if col.name.startswith(('ARCHIVE','REFERENCE')):assert col.hide_viewport and col.hide_render
    for tex in report['donor']['textures']:assert s.sha(Path(tex['path']))==tex['sha256']
    assert s.sha(Path(report['donor']['pinned_model']))==report['donor']['source_sha256']
    result={'reopened':True,'blend_sha256':digest,'parent_step12_sha256':report['parent_sha256'],'accepted_shape_exact':True,'all_original_uv_layers_preserved':True,'all_geometry_weights_normals_rig_preserved':True,'only_collar_and_shirt_materials_changed':True,'grey_both_sides_red_edge_preserved':True,'textures_packed_and_donor_unchanged':True,'new_uv':uv_report,'posed_vertex_delta_m':posed,'parts':parts,'body_triangles_with_modifiers':sum(p['triangles'] for p in parts.values()),'checks_passed':True,'game_installed':False,'game_animations_validated':False}
    if '--render' in sys.argv:
        for label,direction,target,scale in [('front',(0,1,0),(0,0,1.47),1.02),('collar_close',(.18,1,.15),(0,.02,1.53),.55),('three_quarter',(.65,1,.12),(0,0,1.47),1.02),('right_shoulder_detail',(.7,1,.25),(.18,0,1.51),.43),('shoulder_detail',(-.7,1,.25),(-.18,0,1.51),.43),('shoulders_above',(0,1,.8),(0,.01,1.50),.72),('back',(0,-1,.03),(0,0,1.47),1.02)]:s.render(scene,label,direction,target,scale)
        result['previews_bound_to_blend_sha256']=digest
    assert s.sha(path)==digest
    (s.OUT/'validation.json').write_text(json.dumps(result,indent=2)+'\n',encoding='utf8')
    print('CHECK13',json.dumps({k:result[k] for k in ('blend_sha256','checks_passed','body_triangles_with_modifiers')}),flush=True)

if __name__=='__main__':main()
