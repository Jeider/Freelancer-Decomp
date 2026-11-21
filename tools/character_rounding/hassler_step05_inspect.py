import sys,json
from pathlib import Path
import bpy,numpy as np
ROOT=Path(__file__).resolve().parents[2];sys.path[:0]=[str(ROOT/'tools'),str(Path(__file__).parent)]
from blender_workspace import configure
from hassler_native_step05 import OUT,GARMENT
from hassler_step03_check import topology
configure('character_rounding')
bpy.ops.wm.open_mainfile(filepath=str(OUT/'hassler_native_upper.blend'));configure('character_rounding')
base=bpy.data.objects['00 Native sleeves and lower body'];report={'base_materials':[]}
for i,m in enumerate(base.data.materials):
    faces=[f for f in base.data.polygons if f.material_index==i and abs(f.center.x)>.20]
    images=[n.image.filepath for n in m.node_tree.nodes if n.type=='TEX_IMAGE']
    report['base_materials'].append({'index':i,'name':m.name,'images':images,'arm_faces':len(faces),
                                   'arm_bounds':[[min(v.co.z for f in faces for v in [base.data.vertices[k] for k in f.vertices]),max(v.co.z for f in faces for v in [base.data.vertices[k] for k in f.vertices])]] if faces else []})
ob=bpy.data.objects[GARMENT];report['topology']=topology(ob.data)
report['smooth_faces']=sum(f.use_smooth for f in ob.data.polygons)
report['face_count']=len(ob.data.polygons);report['attributes']=[a.name for a in ob.data.attributes]
report['sharp_edges']=sum(e.use_edge_sharp for e in ob.data.edges)
ob.data.calc_loop_triangles();uv=ob.data.uv_layers.active;bad={}
for tri in ob.data.loop_triangles:
    a,b,c=[np.array(uv.data[i].uv) for i in tri.loops]
    if abs(np.cross(b-a,c-a))<1e-11:
        bad[tri.material_index]=bad.get(tri.material_index,0)+1
        print('BAD_UV',tri.polygon_index,list(tri.vertices),[list(ob.data.vertices[i].co) for i in tri.vertices],[a.tolist(),b.tolist(),c.tolist()],len(ob.data.polygons[tri.polygon_index].vertices),flush=True)
report['zero_uv_by_material']=bad
for label,cond in [('right_sleeve',lambda f:f.center.x>.23 and .32<f.center.z<.45),('flap',lambda f:f.material_index==3)]:
    ff=[f for f in ob.data.polygons if cond(f)];report[label]={'faces':len(ff),'normals':np.mean([f.normal[:] for f in ff],axis=0).tolist() if ff else None}
print(json.dumps(report,ensure_ascii=False,indent=2),flush=True)
