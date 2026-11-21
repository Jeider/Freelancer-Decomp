"""Inspect the actual native shoulder surfaces before the step 11 shape pass."""
import sys,copy,json,shutil
from pathlib import Path
import bpy,numpy as np
ROOT=Path(__file__).resolve().parents[2]
sys.path[:0]=[str(ROOT/'tools'),str(Path(__file__).parent)]
from blender_workspace import configure
import hassler_build as native
import hassler_native_upper as upper
import hassler_native_step02 as s2
import hassler_native_step09 as s9
configure('character_rounding')
OUT=upper.TOP/'source/shoulder_fit_study'

def main():
    OUT.mkdir(parents=True,exist_ok=True)
    ref=OUT/'user_front_step11.png'
    if not ref.exists():shutil.copyfile('C:/Users/Freel/AppData/Local/Temp/codex-clipboard-htexcA.png',ref)
    bpy.ops.wm.open_mainfile(filepath=str(upper.TOP/'step_10/hassler_native_upper.blend'));configure('character_rounding')
    scene=bpy.context.scene;scene.frame_set(1);scene.cycles.samples=24
    for ob in bpy.data.objects:
        if ob.type=='MESH':ob.hide_render=True
    col=native.collection('Native shoulder construction reference');report={}
    for label,path in [('dietrich',upper.TOP/'source/dietrich/source/dietrich.json.gz'),('reichman',upper.TOP.parent/'source/epaulettes.json.gz')]:
        d=s2.load(path);p=np.array(d['points']);uv=np.array(d['uv']);d=copy.deepcopy(d)
        for g in d['groups']:
            g['faces']=[t for t in g['faces'] if all(p[i,1]>.49 and p[i,0]>.11 and uv[i,0]>.22 and uv[i,1]<.50 for i in t)]
        d=upper.compact(d);ob=native.native_mesh(d,'Native '+label+' shoulder',col);ob.location.z=.975662
        ob.hide_render=False
        report[label]={'source':str(path),'source_sha256':d['sha256'],'triangles':sum(len(g['faces']) for g in d['groups']),'points_blender':[list(v.co) for v in ob.data.vertices],'faces':[list(f.vertices) for f in ob.data.polygons]}
        s9.OUT=OUT
        s9.render(scene,label+'_front',(0,1,0),(.21,0,1.52),.32)
        s9.render(scene,label+'_profile',(1,.1,.12),(.21,0,1.52),.32)
        ob.hide_render=True
    upper.dump(OUT/'native_reference_geometry.json',report)

if __name__=='__main__':main()
