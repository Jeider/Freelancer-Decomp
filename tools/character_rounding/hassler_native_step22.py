"""Close the open wearer-right end of the folded collar, using its real rim."""
import sys,json,shutil
from pathlib import Path
import bpy,bmesh,numpy as np
from mathutils import Vector
from mathutils.geometry import tessellate_polygon
ROOT=Path(__file__).resolve().parents[2];sys.path[:0]=[str(ROOT/'tools'),str(Path(__file__).parent)]
from blender_workspace import configure
import hassler_build as native
import hassler_native_step08 as s8
import hassler_native_step13 as s13
import hassler_native_step15 as views
import hassler_native_step20 as previous
import hassler_runtime_pose as runtime
configure('character_rounding')
TOP=native.OUT/'native_upper';OUT=TOP/'step_22';SOURCE=TOP/'step_21/hassler_native_upper.blend'

def main():
    OUT.mkdir(exist_ok=True);digest=s13.sha(SOURCE)
    for src,name in [('C:/Users/Freel/AppData/Local/Temp/codex-clipboard-3NyLCa.png','user_game.png'),('C:/Users/Freel/AppData/Local/Temp/codex-clipboard-9J5DDG.png','user_hole_comparison.png')]:
        if not (OUT/name).exists():shutil.copyfile(src,OUT/name)
    bpy.ops.wm.open_mainfile(filepath=str(SOURCE));configure('character_rounding');scene=bpy.context.scene;scene.frame_set(1);scene.cycles.samples=24
    edit=next(c for c in bpy.data.collections if c.name.startswith('EDIT '));collar=next(o for o in edit.objects if o.name.startswith('24 '));views.OUT=OUT
    if not (OUT/'before_right_end.png').exists():
        runtime.cull_materials(edit.objects)
        views.render(scene,'before_right_end',(-.65,1,.12),(.10,.09,1.58),.34)
    # Reopen the unchanged source so preview-only culling nodes are not saved.
    bpy.ops.wm.open_mainfile(filepath=str(SOURCE));configure('character_rounding');scene=bpy.context.scene;scene.frame_set(1);scene.cycles.samples=24
    edit=next(c for c in bpy.data.collections if c.name.startswith('EDIT '));collar=next(o for o in edit.objects if o.name.startswith('24 '));me=collar.data
    fixed={o.name:previous.geometry_hash(o) for o in edit.objects if o.type=='MESH'}
    p=np.array([v.co[:] for v in me.vertices]);names=[b['name'] for b in native.load('body')['bones']];weights=s8.weights(collar,names)
    source_row=json.loads((TOP/'step_20/collar_audit.json').read_text())['rows'][0]
    outer=[]
    for q in source_row[3:]:
        i=int(np.argmin(np.linalg.norm(p-q,axis=1)));assert np.linalg.norm(p[i]-q)<2e-7;outer.append(i)
    # Real border of the U-shaped folded cloth: shirt contact -> inner wall ->
    # roll -> outer fall. Its formerly open end exposes the right shoulder.
    border=[4,3,2,1,0]+outer
    edges={}
    for f in me.polygons:
        ids=list(f.vertices)
        for a,b in zip(ids,ids[1:]+ids[:1]):key=tuple(sorted((a,b)));edges[key]=edges.get(key,0)+1
    assert all(edges[tuple(sorted((a,b)))]==1 for a,b in zip(border,border[1:])),border
    # The traced end is slightly non-planar. Tessellate its Y/Z contour (the
    # end faces sideways) instead of using a fan across the concave fold.
    polygon=[Vector((p[i,1],p[i,2],0)) for i in border];triangles=tessellate_polygon([polygon]);faces=[]
    for triangle in triangles:
        local=[v if isinstance(v,int) else min(range(len(polygon)),key=lambda i:(polygon[i]-v).length_squared) for v in triangle]
        f=[border[i] for i in local];q=p[f]
        if np.cross(q[1]-q[0],q[2]-q[0])[0]>0:f.reverse()
        faces.append(f)
    assert len(faces)==len(border)-2
    me.calc_loop_triangles();base_triangles=len(me.loop_triangles)
    bm=bmesh.new();bm.from_mesh(me);bm.verts.ensure_lookup_table();uv=bm.loops.layers.uv[s13.COLLAR_UV]
    y0,y1=p[border,1].min(),p[border,1].max();z0,z1=p[border,2].min(),p[border,2].max()
    for ids in faces:
        f=bm.faces.new([bm.verts[i] for i in ids]);f.material_index=0;f.smooth=False
        for loop in f.loops:
            q=np.array(loop.vert.co);loop[uv].uv=(.835+.075*(q[1]-y0)/(y1-y0),.18+.13*(q[2]-z0)/(z1-z0))
    bm.to_mesh(me);bm.free();me.update()
    # The old gold gusset ran right through this formerly open end. Fit that
    # concealed joining cloth BEHIND the new cap rather than leaving gold
    # intersections visible through the grey surface.
    gold_changes={}
    for prefix,margin in [('17 ',.015),('14 ',.005)]:
        gold=next(o for o in edit.objects if o.name.startswith(prefix));old_gold=np.array([v.co[:] for v in gold.data.vertices]);moved=[]
        for v in gold.data.vertices:
            q=np.array(v.co)
            if not .04<q[0]<.17:continue
            best=None
            for ids in faces:
                t=p[ids];a,b,c=t[:,1:];d=q[1:];uvv=np.linalg.lstsq(np.c_[b-a,c-a],d-a,rcond=None)[0];bary=np.r_[1-uvv.sum(),uvv]
                candidates=[]
                if min(bary)>=0:candidates.append((0.,float(bary@t[:,0])))
                for i,j in ((0,1),(1,2),(2,0)):
                    e=t[j,1:]-t[i,1:];u=float(np.clip((d-t[i,1:])@e/max(e@e,1e-15),0,1));hit=t[i]*(1-u)+t[j]*u;candidates.append((float(np.linalg.norm(d-hit[1:])),float(hit[0])))
                candidate=min(candidates)
                if best is None or candidate[0]<best[0]:best=candidate
            distance,x=best
            if distance<margin and q[0]<x+.004:
                v.co.x=x+.004;moved.append(v.index)
        if gold.data.has_custom_normals:native.activate(gold);bpy.ops.mesh.customdata_custom_splitnormals_clear()
        gold.data.update()
        gold_changes[gold.name]={'vertices':moved,'max_inset_m':float(np.max(np.linalg.norm(np.array([v.co[:] for v in gold.data.vertices])-old_gold,axis=1)))}
    for name,h in fixed.items():
        if name not in gold_changes:assert previous.geometry_hash(bpy.data.objects[name])==h,name
    assert np.max(abs(s8.weights(collar,names)-weights))<1e-8
    report={'parent':str(SOURCE),'parent_sha256':digest,'target':'wearer-right side opening, between short outer lapel and inner collar wall','boundary_vertices':border,'new_triangles':faces,'base_triangle_count_before':base_triangles,'new_triangle_count':len(faces),'border_points_blender':p[border].tolist(),'skin_weights':weights[border].tolist(),'bone_names':names,'new_vertex_count':0,'unchanged_objects':{n:h for n,h in fixed.items() if n not in gold_changes},'hidden_gold_tucked_behind_cap':gold_changes,'all_skin_weights_unchanged':True,'uv_crop':[.835,.91,.18,.31],'game_launched':False}
    (OUT/'report.json').write_text(json.dumps(report,ensure_ascii=False,indent=2)+'\n',encoding='utf8')
    native.activate(collar);bpy.ops.wm.save_as_mainfile(filepath=str(OUT/'hassler_native_upper.blend'),compress=True);assert s13.sha(SOURCE)==digest
    bpy.ops.wm.open_mainfile(filepath=str(OUT/'hassler_native_upper.blend'));configure('character_rounding');scene=bpy.context.scene;edit=next(c for c in bpy.data.collections if c.name.startswith('EDIT '));runtime.cull_materials(edit.objects)
    views.render(scene,'after_right_end',(-.65,1,.12),(.10,.09,1.58),.34)
    views.render(scene,'front',(-.45,1,.12),(0,.02,1.58),.73)
    print(json.dumps({'side':'wearer-right','new_triangles':len(faces),'changed_collar_vertices':0,'tucked_hidden_gold_vertices':sum(len(x['vertices']) for x in gold_changes.values())}),flush=True)

if __name__=='__main__':main()
