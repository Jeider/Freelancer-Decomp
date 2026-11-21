"""Tuck the gold seam below the grey collar and deepen its shirt allowance."""
import sys,json,shutil
from pathlib import Path
import bpy,numpy as np
ROOT=Path(__file__).resolve().parents[2];sys.path[:0]=[str(ROOT/'tools'),str(Path(__file__).parent)]
from blender_workspace import configure
import hassler_build as native
import hassler_native_step13 as s13
import hassler_native_step15 as views
import hassler_native_step20 as previous
import hassler_runtime_pose as runtime
configure('character_rounding')
TOP=native.OUT/'native_upper';OUT=TOP/'step_21';SOURCE=TOP/'step_20/hassler_native_upper.blend'

def main():
    OUT.mkdir(exist_ok=True);digest=s13.sha(SOURCE)
    ref=OUT/'user_in_game.png'
    if not ref.exists():shutil.copyfile('C:/Users/Freel/AppData/Local/Temp/codex-clipboard-8dSJIh.png',ref)
    bpy.ops.wm.open_mainfile(filepath=str(SOURCE));configure('character_rounding');scene=bpy.context.scene;scene.frame_set(1)
    edit=next(c for c in bpy.data.collections if c.name.startswith('EDIT '));gusset=next(o for o in edit.objects if o.name.startswith('17 '));collar=next(o for o in edit.objects if o.name.startswith('24 '));shirt=next(o for o in edit.objects if o.name.startswith('12 '))
    fixed={o.name:previous.geometry_hash(o) for o in edit.objects if o.type=='MESH' and o not in (gusset,collar)}
    before_g=np.array([v.co[:] for v in gusset.data.vertices]);before_c=np.array([v.co[:] for v in collar.data.vertices])
    attachments=json.loads((TOP/'step_12/report.json').read_text(encoding='utf8'))['gold_join']['attachments']
    for attachment in attachments:
        for row in attachment['section_vertices']:
            p=before_g[row[0]];q=before_g[row[-1]];d=q-p;length=np.linalg.norm(d);d/=length
            inset=min(.004,length*.30)
            for i,factor in zip(row,(1,.55,.15,0)):gusset.data.vertices[i].co=before_g[i]+d*inset*factor
    if gusset.data.has_custom_normals:native.activate(gusset);bpy.ops.mesh.customdata_custom_splitnormals_clear()
    gusset.data.update()
    seams=json.loads((TOP/'step_20/report.json').read_text(encoding='utf8'))['seams'];shirt.data.calc_loop_triangles()
    for j,seam in enumerate(seams):
        end=j*5+4;mid=j*5+3;target=np.array(seam['shirt_contact']);p=before_c[end]
        inward=p-target;inward/=np.linalg.norm(inward)
        new=target+inward*.004;delta=new-p
        collar.data.vertices[end].co=new;collar.data.vertices[mid].co=before_c[mid]+delta*.5
    collar.data.update()
    # Outer rolled silhouette and all visible front-lapel positions stay fixed.
    fixed_collar=set(range(len(before_c)))-{j*5+k for j in range(len(seams)) for k in (3,4)}
    assert all(np.array_equal(np.array(collar.data.vertices[i].co),before_c[i]) for i in fixed_collar)
    for name,h in fixed.items():assert previous.geometry_hash(bpy.data.objects[name])==h
    report={'parent':str(SOURCE),'parent_sha256':digest,'reference':str(ref),'gold_seam_inset_max_m':float(np.max(np.linalg.norm(np.array([v.co[:] for v in gusset.data.vertices])-before_g,axis=1))),'shirt_sewn_allowance_m':.004,'previous_allowance_m':.0003,'unchanged_objects':fixed,'unchanged_outer_collar_vertices':len(fixed_collar),'head_belt_and_outer_collar_preserved':True,'game_launched':False}
    (OUT/'report.json').write_text(json.dumps(report,ensure_ascii=False,indent=2)+'\n',encoding='utf8')
    native.activate(collar);scene.cycles.samples=24;bpy.ops.wm.save_as_mainfile(filepath=str(OUT/'hassler_native_upper.blend'),compress=True);assert s13.sha(SOURCE)==digest
    bpy.ops.wm.open_mainfile(filepath=str(OUT/'hassler_native_upper.blend'));configure('character_rounding');scene=bpy.context.scene;edit=next(c for c in bpy.data.collections if c.name.startswith('EDIT '));runtime.cull_materials(edit.objects);views.OUT=OUT
    views.render(scene,'front',(-.45,1,.12),(0,.02,1.58),.73)
    views.render(scene,'other_side',(.6,1,.20),(0,.02,1.58),.73)
    print(json.dumps(report,ensure_ascii=False),flush=True)

if __name__=='__main__':main()
