"""Fit Hassler's neck and map the actual Wilham collar artwork on both faces."""
import sys,json,gzip,math,hashlib
from pathlib import Path
import bpy,numpy as np
from mathutils import Matrix,Vector
ROOT=Path(__file__).resolve().parents[2];sys.path[:0]=[str(ROOT/'tools'),str(Path(__file__).parent)]
from blender_workspace import configure
import hassler_build as native
import hassler_native_step08 as s8
import hassler_native_step12 as s12
import hassler_native_step13 as s13
import hassler_native_step15 as views
import hassler_runtime_pose as runtime
configure('character_rounding')
TOP=native.OUT/'native_upper';OUT=TOP/'step_18';SOURCE=TOP/'step_17/hassler_native_upper.blend'
HEAD_DROP=.010

def main():
    OUT.mkdir(exist_ok=True);digest=s13.sha(SOURCE)
    bpy.ops.wm.open_mainfile(filepath=str(SOURCE));configure('character_rounding');scene=bpy.context.scene;scene.frame_set(1)
    edit=bpy.data.collections['EDIT — native costume upper study'];rig=bpy.data.objects['RIG — native Rheinland'];head=bpy.data.objects['Hassler head — native unchanged']
    coat=next(o for o in edit.objects if o.name.startswith('10 '));shirt=next(o for o in edit.objects if o.name.startswith('12 '))
    original={o.name:hashlib.sha256(np.array([v.co[:] for v in o.data.vertices],dtype='<f4').tobytes()).hexdigest() for o in edit.objects if o.type=='MESH' and o!=shirt}
    # The shape is kept; only the body-local head rest attachment is fitted.
    for v in head.data.vertices:v.co.z-=HEAD_DROP
    head['head_fit_offset_m']=[0,0,-.035]
    native.activate(rig);bpy.ops.object.mode_set(mode='EDIT')
    for name in ('Body_Head','Head_End'):
        b=rig.data.edit_bones[name];b.head.z-=HEAD_DROP;b.tail.z-=HEAD_DROP
    bpy.ops.object.mode_set(mode='OBJECT')
    for name in ('Body_Head','Head_End'):
        b=rig.data.bones[name];old=np.array(b['native_inverse_bind']);b['native_inverse_bind']=old[:9].tolist()+(old[9:]+old[:9].reshape(3,3)@np.array([0,HEAD_DROP,0])).tolist()
    for i,v in enumerate(shirt.data.vertices):
        # Exact 48-vertex seam follows the head, with a smooth transition below.
        v.co.z-=HEAD_DROP*float(np.clip((i//48-3)/3,0,1))
    if shirt.data.has_custom_normals:native.activate(shirt);bpy.ops.mesh.customdata_custom_splitnormals_clear()
    shirt.data.update()

    donor=json.loads(gzip.decompress((TOP/'source/wilham.json.gz').read_bytes()))
    # Native inner-collar rails, read from the actual donor's UV chart.
    # Each pair is the sewn root and the rolled outer edge, right tip -> left tip.
    pairs=[(257,256),(258,259),(252,253),(249,246),(247,245),(241,242),(229,224),(225,226),(233,232)]
    # Explicitly use source vertex indices, preserving the artwork's shape.
    rails=np.array([[donor['uv'][a],donor['uv'][b]] for a,b in pairs])
    atlas=bpy.data.images.load(donor['groups'][0]['texture'],check_existing=True);pixels=np.array(atlas.pixels[:]).reshape(atlas.size[1],atlas.size[0],4)
    def grey_span(v):
        line=pixels[int(np.clip(v,0,1)*(atlas.size[1]-1))];lo=int(.80*atlas.size[0]);hi=int(.96*atlas.size[0]);rgb=line[lo:hi,:3]
        mask=(rgb[:,0]<rgb[:,1]*1.18)&(rgb[:,1]>.035)&(rgb[:,2]>.025)
        edges=np.flatnonzero(np.diff(np.r_[False,mask,False].astype(int)));runs=[(a,b) for a,b in zip(edges[::2],edges[1::2]) if b-a>5]
        assert runs,('Missing gray collar cloth',v)
        a,b=max(runs,key=lambda ab:ab[1]-ab[0]);return (lo+a+1)/atlas.size[0],(lo+b-2)/atlas.size[0]
    centres=np.array([(np.array(donor['points'][a])+np.array(donor['points'][b]))*.5 for a,b in pairs])
    # Chart progression is the original collar's native azimuth, not arbitrary
    # equal-length cuts. Clamp the gray field inside its painted red border.
    arc=np.r_[0,np.cumsum(np.linalg.norm(np.diff(centres,axis=0),axis=1))];arc/=arc[-1]
    faces,rows=s12.collar_rows(coat);me=coat.data;mapping={};along=np.r_[0,np.cumsum([(me.vertices[a[2]].co-me.vertices[b[2]].co).length for a,b in zip(rows,rows[1:])])];along/=along[-1]
    for row,t in zip(rows,along):
        k=min(len(arc)-2,max(0,np.searchsorted(arc,t)-1));u=float((t-arc[k])/max(1e-8,arc[k+1]-arc[k]));rail=rails[k]*(1-u)+rails[k+1]*u
        widths=np.r_[0,np.cumsum([(me.vertices[a].co-me.vertices[b].co).length for a,b in zip(row,row[1:])])];widths/=widths[-1]
        for i,w in zip(row,widths):
            v=float(.13+(((1-w)*rail[0]+w*rail[1])[1]-.1033)*(.67-.13)/(.6914-.1033));left,right=grey_span(v)
            mapping[i]=[left+(right-left)*(.08+.84*w),v]
    ids={i for f in faces for i in me.polygons[f].vertices};s13.interpolate_extras(me,rows,mapping,ids)
    layer=me.uv_layers[s13.COLLAR_UV]
    for f in faces:
        for li,i in zip(me.polygons[f].loop_indices,me.polygons[f].vertices):layer.data[li].uv=mapping[i]
    old=me.materials[4];mat=old.copy();mat.name='Hassler 18 — Wilham actual collar facing';nodes=mat.node_tree.nodes
    tex=next(n for n in nodes if n.type=='TEX_IMAGE');tex.image=bpy.data.images.load(donor['groups'][0]['texture'],check_existing=True);tex.image.pack()
    ramp=next(n for n in nodes if n.type=='VALTORGB');ramp.color_ramp.elements[0].position=0;ramp.color_ramp.elements[0].color=(.035,.038,.039,1);ramp.color_ramp.elements[1].position=.65;ramp.color_ramp.elements[1].color=(.24,.26,.26,1)
    for i in (4,15,22,33):me.materials[i]=mat
    mat['donor']='Wilham atlas 1, actual collar inner rails; desaturated cloth, separate red piping'
    # The original jacket's red reverse was visible as an accidental stripe
    # behind the neck. Give the green/back shell a charcoal fabric facing.
    layer=me.uv_layers.get(s13.SHIRT_UV) or me.uv_layers.new(name=s13.SHIRT_UV)
    for f in me.polygons:
        for li,i in zip(f.loop_indices,f.vertices):
            p=me.vertices[i].co;a=math.atan2(p.x,p.y+.006);t=float(np.clip((p.z-.40)/.19,0,1));layer.data[li].uv=(.868+(.085-.04*t)*math.sin(a/2),.55+.35*t)
    facing=shirt.data.materials[0]
    for i in (11,17):me.materials[i]=facing
    coat['collar_texture']='Actual Wilham collar atlas island, both sides; gray cloth, red perimeter'
    coat['inner_back_facing']='Charcoal cloth instead of red jacket reverse behind neck'
    for name,d in original.items():assert hashlib.sha256(np.array([v.co[:] for v in bpy.data.objects[name].data.vertices],dtype='<f4').tobytes()).hexdigest()==d
    report={'parent':str(SOURCE),'parent_sha256':digest,'head_additional_drop_m':HEAD_DROP,'head_total_drop_m':.035,'unchanged_garment_geometry':original,'collar_donor':donor['source'],'collar_donor_sha256':donor['sha256'],'collar_texture':donor['groups'][0]['texture'],'collar_uv_rails':rails.tolist(),'collar_uv_rows':[[mapping[i] for i in row] for row in rows],'collar_faces':faces,'inner_facing_material':facing.name,'new_geometry':False,'game_launched':False}
    (OUT/'report.json').write_text(json.dumps(report,ensure_ascii=False,indent=2)+'\n',encoding='utf8')
    native.activate(coat);scene.cycles.samples=32;bpy.ops.wm.save_as_mainfile(filepath=str(OUT/'hassler_native_upper.blend'),compress=True);assert s13.sha(SOURCE)==digest
    # Reload what will be exported before rendering any evidence.
    bpy.ops.wm.open_mainfile(filepath=str(OUT/'hassler_native_upper.blend'));configure('character_rounding');scene=bpy.context.scene;rig=bpy.data.objects['RIG — native Rheinland'];edit=bpy.data.collections['EDIT — native costume upper study']
    runtime.cull_materials(edit.objects);views.OUT=OUT
    views.render(scene,'front',(0,1,.03),(0,.02,1.56),.73)
    views.render(scene,'collar_close',(-.45,1,.20),(0,.02,1.56),.73)
    views.render(scene,'inside_back',(0,-1,.7),(0,0,1.52),.55)
    clips=json.loads((OUT/'ru_scene_clips.json').read_text())['clips'];runtime.apply_blender(rig,OUT/'installed_rig.json',clips['Sc_MLBODY_STND_CROSS_ARMS_000LV_xa_06'],2.)
    views.render(scene,'ru_pose',(-.45,1,.12),(0,.02,1.56),.73)
    print('STEP18 collar + head fit saved',flush=True)

if __name__=='__main__':main()
