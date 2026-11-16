"""Run the actual C++ motion kernel against regression cases and the packed DFM."""
import sys,subprocess,struct
import numpy as np
from build import ROOT,OUT,REL,DataFolder,read_tree,child,arr
sys.path.insert(0,str(ROOT/'tools/nebula_control'))
from build_asf_hq import compiler_env
folder=OUT/'motion_check';folder.mkdir(parents=True,exist_ok=True)
compiler,env=compiler_env()
exe=folder/'motion.exe'
subprocess.run([str(compiler/'cl.exe'),'/nologo','/O2','/std:c++17','/EHsc','/MT',
 '/I'+str(ROOT/'src/Deformable2'),str(ROOT/'tools/hatcher_hair/test_motion.cpp'),
 '/Fe:'+str(exe),'/Fo:'+str(folder/'motion.obj')],cwd=folder,env=env,check=True)
root=read_tree(DataFolder(root=OUT/'stage').data_path(REL).read_bytes())[1][0]
for level in range(3):
    geo=child(child(child(root,'MultiLevel'),'Mesh'+str(level)),'Geometry')
    data=np.concatenate([arr(geo,'Points','<f4',3),arr(geo,'Vertex_normals','<f4',3),arr(geo,'Hair_motion_weights','<f4')],axis=1)
    fixture=folder/('lod'+str(level)+'.bin');fixture.write_bytes(struct.pack('<I',len(data))+data.astype('<f4').tobytes())
    result=subprocess.run([str(exe),str(fixture)],cwd=folder,check=True,capture_output=True,text=True)
    (folder/('lod'+str(level)+'.txt')).write_text(result.stdout);print(result.stdout,end='')
