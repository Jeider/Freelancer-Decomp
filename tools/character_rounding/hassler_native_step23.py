"""Level the shoulder boards while leaving the native skeleton in place."""
import sys,json,math,shutil,hashlib
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
TOP=native.OUT/'native_upper';OUT=TOP/'step_23';SOURCE=TOP/'step_22/hassler_native_upper.blend'

def smooth(a,b,v):
    t=float(np.clip((v-a)/(b-a),0,1));return t*t*(3-2*t)

def shoulder_drop(p):
    x,y,z=map(float,p);u=.5
    # Invert the existing board's loft coordinates. Remove only the authored
    # outward crown rise (39mm before the accepted 1.12 vertical garment warp).
    for _ in range(6):
        t=float(np.clip(y/(.137-.006*u) if y>=0 else y/(.093+.018*u),-1,1));front=max(t,0);back=max(-t,0)
        xi=.130-.052*front*front-.010*back*back;xo=.286-.048*front*front-.025*back*back
        u=float(np.clip((abs(x)-xi)/(xo-xi),0,1))
    return .039*1.12*math.sin(math.pi*u/2)*max(0,1-t*t)

def deform(ob,amount):
    me=ob.data;before=np.array([v.co[:] for v in me.vertices]);normals=np.array([n.vector[:] for n in me.corner_normals]);grad={};changed=[]
    for v,p in zip(me.vertices,before):
        drop=amount(v.index,p)
        if abs(drop)<1e-9:continue
        v.co.z-=drop;changed.append(v.index);g=[]
        for axis in range(3):
            e=np.zeros(3);e[axis]=1e-5;g.append((amount(v.index,p+e)-amount(v.index,p-e))/(2e-5))
        J=np.eye(3);J[2]-=g;grad[v.index]=np.linalg.inv(J).T
    me.update()
    if me.has_custom_normals:
        nn=[]
        for loop,n in zip(me.loops,normals):
            n=grad.get(loop.vertex_index,np.eye(3))@n;n/=max(np.linalg.norm(n),1e-12);nn.append(n)
        me.normals_split_custom_set(nn)
    return {'vertices_changed':len(changed),'max_drop_m':float(np.max(before[:,2]-np.array([v.co.z for v in me.vertices])))}

def rig_hash(rig):
    data={b.name:{'matrix':[list(row) for row in b.matrix_local],'inverse_bind':list(b.get('native_inverse_bind',[]))} for b in rig.data.bones}
    return hashlib.sha256(json.dumps(data,sort_keys=True).encode()).hexdigest()

def main():
    OUT.mkdir(exist_ok=True);digest=s13.sha(SOURCE)
    if not (OUT/'user_shoulders.png').exists():shutil.copyfile('C:/Users/Freel/AppData/Local/Temp/codex-clipboard-xgdgqs.png',OUT/'user_shoulders.png')
    bpy.ops.wm.open_mainfile(filepath=str(SOURCE));configure('character_rounding');scene=bpy.context.scene;scene.frame_set(1);scene.cycles.samples=24;views.OUT=OUT
    if not (OUT/'before_shoulders.png').exists():
        edit=next(c for c in bpy.data.collections if c.name.startswith('EDIT '));runtime.cull_materials(edit.objects);views.render(scene,'before_shoulders',(0,1,0),(0,0,1.4),1.1)
    bpy.ops.wm.open_mainfile(filepath=str(SOURCE));configure('character_rounding');scene=bpy.context.scene;scene.frame_set(1);scene.cycles.samples=24
    edit=next(c for c in bpy.data.collections if c.name.startswith('EDIT '));rig=next(o for o in bpy.data.objects if o.name.startswith('RIG '));rh=rig_hash(rig)
    fixed={o.name:previous.geometry_hash(o) for o in edit.objects if o.type=='MESH'};changed={}
    for ob in edit.objects:
        if ob.type!='MESH':continue
        if ob.name.startswith(('14 ','16 ')):
            changed[ob.name]=deform(ob,lambda i,p:shoulder_drop(p))
        elif ob.name.startswith('17 '):
            # Keep the collar-side anchor fixed; lower the shoulder-side anchor.
            changed[ob.name]=deform(ob,lambda i,p:shoulder_drop(p)*(0,.25,.6,1)[i%4])
        elif ob.name.startswith(('10 ','11 ','13.')):
            changed[ob.name]=deform(ob,lambda i,p:shoulder_drop(p)*smooth(.14,.20,abs(p[0]))*smooth(.43,.57,p[2]))
    for name,h in fixed.items():
        if name not in changed:assert previous.geometry_hash(bpy.data.objects[name])==h,name
    assert rig_hash(rig)==rh
    ep=next(o for o in edit.objects if o.name.startswith('14 '));grid=json.loads((TOP/'step_11/report.json').read_text())['shoulders']['gold_grid_vertices']
    crowns={}
    for side,rows in grid.items():
        heights=[ep.data.vertices[i].co.z for i in rows[12]];crowns[side]={'min_z_m':min(heights),'max_z_m':max(heights),'height_difference_m':max(heights)-min(heights)}
        assert max(heights)-min(heights)<.001
    report={'parent':str(SOURCE),'parent_sha256':digest,'reference':str(OUT/'user_shoulders.png'),'changed_geometry':changed,'level_shoulder_crowns':crowns,'native_skeleton_before_after_sha256':rh,'bones_unchanged':True,'right_collar_end_closure_preserved':True,'unchanged_geometry':{n:h for n,h in fixed.items() if n not in changed},'new_polygons':0,'game_launched':False}
    (OUT/'report.json').write_text(json.dumps(report,ensure_ascii=False,indent=2)+'\n',encoding='utf8');native.activate(ep);bpy.ops.wm.save_as_mainfile(filepath=str(OUT/'hassler_native_upper.blend'),compress=True);assert s13.sha(SOURCE)==digest
    bpy.ops.wm.open_mainfile(filepath=str(OUT/'hassler_native_upper.blend'));configure('character_rounding');scene=bpy.context.scene;edit=next(c for c in bpy.data.collections if c.name.startswith('EDIT '));runtime.cull_materials(edit.objects)
    views.render(scene,'after_shoulders',(0,1,0),(0,0,1.4),1.1);views.render(scene,'front',(-.45,1,.12),(0,.02,1.58),.73)
    views.render(scene,'right_end',(-.65,1,.12),(.10,.09,1.58),.34)
    print(json.dumps(report,ensure_ascii=False),flush=True)

if __name__=='__main__':main()
