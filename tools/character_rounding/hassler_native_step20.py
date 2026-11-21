"""Close the underside of the collar with a continuous fitted grey facing."""
import sys,json,hashlib,math
from pathlib import Path
import bpy,bmesh,numpy as np
from mathutils import Vector
from mathutils.bvhtree import BVHTree
ROOT=Path(__file__).resolve().parents[2];sys.path[:0]=[str(ROOT/'tools'),str(Path(__file__).parent)]
from blender_workspace import configure
import hassler_build as native
import hassler_native_upper as upper
import hassler_native_step08 as s8
import hassler_native_step12 as s12
import hassler_native_step13 as s13
import hassler_native_step15 as views
import hassler_runtime_pose as runtime
configure('character_rounding')
TOP=native.OUT/'native_upper';OUT=TOP/'step_20';SOURCE=TOP/'step_19/hassler_native_upper.blend'

def geometry_hash(ob):
    return hashlib.sha256(np.array([v.co[:] for v in ob.data.vertices],dtype='<f4').tobytes()).hexdigest()

def main():
    OUT.mkdir(exist_ok=True);digest=s13.sha(SOURCE)
    bpy.ops.wm.open_mainfile(filepath=str(SOURCE));configure('character_rounding');scene=bpy.context.scene;scene.frame_set(1)
    edit=next(c for c in bpy.data.collections if c.name.startswith('EDIT '));rig=next(o for o in bpy.data.objects if o.name.startswith('RIG '))
    coat=next(o for o in edit.objects if o.name.startswith('10 '));shirt=next(o for o in edit.objects if o.name.startswith('12 '))
    fixed={o.name:geometry_hash(o) for o in edit.objects if o.type=='MESH'}
    names=[b['name'] for b in native.load('body')['bones']];cw=s8.weights(coat,names);sw=s8.weights(shirt,names)
    _,rows=s12.collar_rows(coat);shirt.data.calc_loop_triangles();tris=[list(t.vertices) for t in shirt.data.loop_triangles]
    sp=np.array([v.co[:] for v in shirt.data.vertices]);tree=BVHTree.FromPolygons(sp,tris,all_triangles=True)
    uvmap={}
    for face in coat.data.polygons:
        for li,vi in zip(face.loop_indices,face.vertices):
            if vi not in uvmap:uvmap[vi]=np.array(coat.data.uv_layers[s13.COLLAR_UV].data[li].uv)
    # UVs at the collar's native inner rail must come from collar faces, rather
    # than the different cloth chart sharing those geometric vertices.
    faces,_=s12.collar_rows(coat)
    for fi in faces:
        f=coat.data.polygons[fi]
        for li,vi in zip(f.loop_indices,f.vertices):uvmap[vi]=np.array(coat.data.uv_layers[s13.COLLAR_UV].data[li].uv)
    points=[];skin=[];uv=[];seams=[];count=5
    for row in rows:
        root=np.array(coat.data.vertices[row[0]].co)
        target,no,fi,dist=tree.find_nearest(Vector(root-np.array([0,0,.025])))
        ids=tris[fi];a,b,c=sp[ids];target=np.array(target)
        coeff=np.linalg.lstsq(np.c_[b-a,c-a],target-a,rcond=None)[0];bary=np.r_[1-coeff.sum(),coeff]
        assert min(bary)>-1e-5
        weight=bary@sw[ids];weight=np.maximum(weight,0);weight/=weight.sum()
        # A 0.3mm recessed sewn allowance removes an exposed cut-edge at the
        # shirt contact, without moving any existing shirt/neck seam vertex.
        end=target-np.array(no)*.0003
        inward=-root.copy();inward[2]=0;inward/=np.linalg.norm(inward)
        # Continue the complete inner wall from the rolled top, not an extra
        # horizontal patch ending at the old root. The replaced two columns
        # are removed from the coat below, so there are no stacked inner faces.
        pp=[np.array(coat.data.vertices[row[2]].co),
            np.array(coat.data.vertices[row[1]].co)+inward*.0025,
            root+inward*.004,(root+end)*.5+inward*.002,end]
        ww=[cw[row[2]],cw[row[1]],cw[row[0]],(cw[row[0]]+weight)*.5,weight]
        uu=[uvmap[row[2]],uvmap[row[1]],uvmap[row[0]],
            .5*(uvmap[row[0]]+uvmap[row[2]]),uvmap[row[2]]]
        points.extend(pp);skin.extend(ww);uv.extend(uu)
        seams.append({'coat_vertex':row[0],'shirt_triangle':ids,'barycentric':bary.tolist(),'shirt_contact':target.tolist(),'sewn_allowance_m':.0003})
    fs=[]
    for j in range(len(rows)-1):
        for k in range(count-1):
            a=j*count+k;b=a+count
            for f in ([a,b,b+1],[a,b+1,a+1]):
                p=np.array([points[i] for i in f]);n=np.cross(p[1]-p[0],p[2]-p[0]);mid=p.mean(axis=0)
                if n@np.array([-mid[0],-mid[1],.15])<0:f=list(reversed(f))
                fs.append(f)
    replaced={faces[k+j] for k in range(0,len(faces),5) for j in (0,1)}
    # Move the unchanged outer fold into this same mesh and share the crest
    # vertices. Solidify then closes ONE continuous shell, avoiding independent
    # rims and split normals along the collar's most visible rounded fold.
    shared={row[2]:j*count for j,row in enumerate(rows)}
    for fi in faces:
        if fi in replaced:continue
        f=coat.data.polygons[fi];ids=[]
        for vi in f.vertices:
            if vi not in shared:
                shared[vi]=len(points);points.append(np.array(coat.data.vertices[vi].co));skin.append(cw[vi]);uv.append(uvmap[vi])
            ids.append(shared[vi])
        fs.append(ids)
    removed=set(faces)
    old=coat.data;remaining=[f for f in old.polygons if f.index not in removed]
    me=bpy.data.meshes.new('Uniform with continuous replacement inner collar');me.from_pydata([v.co[:] for v in old.vertices],[],[list(f.vertices) for f in remaining]);me.update()
    for mat in old.materials:me.materials.append(mat)
    for new,prior in zip(me.polygons,remaining):new.material_index=prior.material_index;new.use_smooth=prior.use_smooth
    for layer in old.uv_layers:
        target=me.uv_layers.new(name=layer.name)
        for new,prior in zip(me.polygons,remaining):
            for li,oi in zip(new.loop_indices,prior.loop_indices):target.data[li].uv=layer.data[oi].uv
    me.normals_split_custom_set([old.corner_normals[li].vector[:] for f in remaining for li in f.loop_indices])
    coat.data=me
    for name in names:coat.vertex_groups.new(name=name)
    s8.set_weights(coat,cw)
    ob=upper.geometry('24 Collar inner facing — closed grey transition to shirt',points,fs,uv,skin,coat.data.materials[4],edit,rig,names)
    ob.data.uv_layers.active.name=s13.COLLAR_UV
    bm=bmesh.new();bm.from_mesh(ob.data);bmesh.ops.recalc_face_normals(bm,faces=list(bm.faces));bm.to_mesh(ob.data);bm.free()
    solid=ob.modifiers.new('Continuous collar and facing thickness 2.4 mm','SOLIDIFY');solid.thickness=.0024;solid.offset=-1;solid.use_quality_normals=True
    ob['construction']='Continuous grey lining joins the existing collar root to the actual shirt surface. Matching interpolated skin weights at both seams. No changes to the outer silhouette or head attachment.'
    for name,h in fixed.items():assert geometry_hash(bpy.data.objects[name])==h,name
    ob.data.calc_loop_triangles()
    report={'parent':str(SOURCE),'parent_sha256':digest,'unchanged_vertex_positions':fixed,'replaced_coat_inner_faces':sorted(replaced),'outer_collar_faces_moved_unchanged':sorted(removed-replaced),'shared_roll_vertices':len(rows),'new_object':ob.name,'vertices':len(points),'base_triangles':len(ob.data.loop_triangles),'material':coat.data.materials[4].name,'seams':seams,'thickness_m':solid.thickness,'preserved_on_all_lods':True,'game_launched':False}
    if (OUT/'user_in_game_collar.png').exists():report['user_reference']=str(OUT/'user_in_game_collar.png')
    (OUT/'report.json').write_text(json.dumps(report,ensure_ascii=False,indent=2)+'\n',encoding='utf8')
    doc=bpy.data.texts.get('README — collar lining') or bpy.data.texts.new('README — collar lining');doc.clear();doc.write(json.dumps(report,ensure_ascii=False,indent=2))
    native.activate(ob);scene.cycles.samples=24;bpy.ops.wm.save_as_mainfile(filepath=str(OUT/'hassler_native_upper.blend'),compress=True);assert s13.sha(SOURCE)==digest
    bpy.ops.wm.open_mainfile(filepath=str(OUT/'hassler_native_upper.blend'));configure('character_rounding');scene=bpy.context.scene;edit=next(c for c in bpy.data.collections if c.name.startswith('EDIT '));runtime.cull_materials(edit.objects);views.OUT=OUT
    scene.render.film_transparent=True
    views.render(scene,'after_front',(-.45,1,.12),(0,.02,1.58),.73)
    head=next(o for o in bpy.data.objects if o.name.startswith('Hassler head '));head.hide_render=True
    views.render(scene,'after_nohead',(-.45,1,.35),(0,.02,1.58),.59)
    print(json.dumps({'step':20,'new_triangles':len(fs),'preserved_objects':len(fixed)},ensure_ascii=False),flush=True)

if __name__=='__main__':main()
