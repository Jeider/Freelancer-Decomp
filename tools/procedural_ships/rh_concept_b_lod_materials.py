"""Two LOD atlases only, in a separate MAT. Existing shared user MAT is read-only."""
import json
import subprocess
from pathlib import Path
import rh_concept_b_final as f

ROOT=Path(__file__).resolve().parents[2]
CACHE=ROOT/'out/ship_design/tool_cache/lod_materials'


def main():
    CACHE.mkdir(parents=True,exist_ok=True)
    command=CACHE/'build.cmd';exe=CACHE/'lod_dds.exe'
    command.write_text('@echo off\ncall "C:/Program Files/Microsoft Visual Studio/18/Community/VC/Auxiliary/Build/vcvars32.bat" > nul\nif errorlevel 1 exit /b 1\n'
        'set "INCLUDE=%INCLUDE%;C:/DXSDK_Jun10/Include"\n'
        f'cl /nologo /EHsc /O2 /std:c++17 /D_CRT_SECURE_NO_WARNINGS tools/procedural_ships/rh_concept_b_lod_dds.cpp /Fo"{CACHE}/lod_dds.obj" /Fe"{exe}" '
        '/link d3d9.lib "C:/DXSDK_Jun10/Lib/x86/d3dx9.lib" user32.lib\n')
    subprocess.run(['cmd','/c',str(command)],cwd=ROOT,check=True)
    before=f.digest(f.b.prior.LIBRARY);header,nodes=f.mesh.read_tree(f.b.prior.LIBRARY.read_bytes())
    root=nodes[0];root.children=[f.folder('Material library'),f.folder('Texture library')]
    mats,tex=root.children;checks=[]
    for lv in (1,2):
        name=f'rh_b_lod{lv}';target=f.OUT/(name+'.dds')
        result=subprocess.run([str(exe),str(f.OUT/(name+'.png')),str(target)],cwd=ROOT,capture_output=True,text=True)
        print(result.stdout.strip(),flush=True)
        result.check_returncode()
        # Texture lookup names stay unchanged; MIPS selects the native DDS path.
        texture=name+'.tga'
        mats.children.append(f.folder(name,f.textnode('Type','DcDt'),f.mesh.Node('Dc',f.np.ones(3,dtype='<f4').tobytes()),f.textnode('Dt_name',texture)))
        tex.children.append(f.folder(texture,f.mesh.Node('MIPS',target.read_bytes())))
        checks.append(dict(name=name,bytes=target.stat().st_size,sha256=f.digest(target),format='DXT1',mips=12,gpu_check=result.stdout.strip()))
    f.LOD_MAT.write_bytes(f.mesh.write_tree(header,nodes))
    assert before==f.digest(f.b.prior.LIBRARY)
    report=dict(shared_mat=str(f.b.prior.LIBRARY),shared_mat_sha256=before,lod_mat=f.LOD_MAT.name,lod_mat_sha256=f.digest(f.LOD_MAT),textures=checks)
    (f.OUT/'lod_materials.json').write_text(json.dumps(report,indent=2))
    print('READY',f.LOD_MAT,flush=True)


if __name__=='__main__':main()
