"""Contact and enclosure diagnostics for the fully wrapped epaulettes."""
import sys,json,hashlib
from pathlib import Path
import bpy,numpy as np
from mathutils import Vector
ROOT=Path(__file__).resolve().parents[2];sys.path[:0]=[str(ROOT/'tools'),str(Path(__file__).parent)]
from blender_workspace import configure
import hassler_native_step10 as s10
import hassler_step08_check as c8
from hassler_step03_check import topology
configure('character_rounding')
for k in ('GARMENT','EPAULETTES','SHIRT','LINING'):setattr(c8,k,getattr(s10,k))

def detail():
    obs={k:c8.evaluated(bpy.data.objects[getattr(s10,k)]) for k in ('GARMENT','EPAULETTES','PAD','LINING')};ep=obs['EPAULETTES'];pad=obs['PAD'];rows={}
    for name in ('GARMENT','PAD','LINING'):
        d=obs[name];rr=[]
        for i,j in ep['tree'].overlap(d['tree']):
            rr.append({'gold_tri':i,'other_tri':j,'other_mat':d['material_indices'][j],'gold_center':np.mean(ep['p'][ep['faces'][i]],axis=0).tolist(),'other_center':np.mean(d['p'][d['faces'][j]],axis=0).tolist(),'gold_vertices':ep['faces'][i]})
        rows[name]=rr
    distances=[];outside=[]
    for i,p in enumerate(pad['p']):
        h,no,fi,d=ep['tree'].find_nearest(Vector(p));signed=float((Vector(p)-h).dot(no));distances.append(signed)
        if signed>1e-6:outside.append(i)
    rows['padding_outside_gold_vertices']=outside;rows['padding_signed_distance_range_m']=[min(distances),max(distances)]
    return rows

def main():
    path=s10.OUT/'hassler_native_upper.blend';bpy.ops.wm.open_mainfile(filepath=str(path));configure('character_rounding');bpy.context.scene.frame_set(1);report=json.loads((s10.OUT/'report.json').read_text(encoding='utf8'))
    d=detail();d['blend_sha256']=hashlib.sha256(path.read_bytes()).hexdigest();d['pose_audit']=c8.pose_audit(bpy.context.scene,report,'rest')
    for key in ('GARMENT','PAD','LINING'):
        rr=d[key];print(key,len(rr),'materials',{m:sum(r['other_mat']==m for r in rr) for m in set(r['other_mat'] for r in rr)},flush=True);print(json.dumps(rr[:10]),flush=True)
    print('COVERAGE',len(d['padding_outside_gold_vertices']),d['padding_signed_distance_range_m'],flush=True)
    print('CORDS',d['pose_audit']['cord_contacts'],flush=True);print('HEAD',d['pose_audit']['head_coat_triangle_crossings'],flush=True)
    print('GOLD TOPOLOGY',topology(bpy.data.objects[s10.EPAULETTES].data),flush=True)
    (s10.OUT/'contacts.json').write_text(json.dumps(d,indent=2),encoding='utf8')

if __name__=='__main__':main()
