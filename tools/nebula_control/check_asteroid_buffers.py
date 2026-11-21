"""Exercise the built RP9 partial-buffer API on a hidden D3D9 device."""
from pathlib import Path
import json,subprocess,hashlib
from check_asteroid_mesh import compiler_env,ROOT
OUT=ROOT/'out/graphics_settings/nebula_asteroid_mesh/handoff/performance'
def main():
    probe=OUT/'buffer_probe';probe.mkdir(exist_ok=True)
    prefix=(ROOT/'tools/nebula_control/check_object_fog.cpp').read_text().split(' e->bSurfaceConfigRead=')[0]
    source=probe/'buffers.cpp';source.write_text(prefix+r'''
 std::vector<unsigned char> original(300000,17),patch(10000,55);FRPExBuffer* buffer=nullptr;
 C(p->CreateExVertexBuffer(unsigned(original.size()),original.data(),&buffer));auto* identity=buffer->Vb;
 C(p->UpdateExVertexBuffer(buffer,12345,unsigned(patch.size()),patch.data()));
 std::copy(patch.begin(),patch.end(),original.begin()+12345);R(buffer->Data==original,"reset backing store patched");
 R(buffer->Vb==identity,"same GPU allocation");void* raw=nullptr;C(buffer->Vb->Lock(0,0,&raw,0));
 R(!memcmp(raw,original.data(),original.size()),"GPU bytes, offset and unaffected range");C(buffer->Vb->Unlock());
 R(p->UpdateExVertexBuffer(buffer,299999,2,patch.data())==GR_INVALID_PARMS,"range rejection");
 R(p->UpdateExVertexBuffer(buffer,0xffffffff,2,patch.data())==GR_INVALID_PARMS,"overflow rejection");
 e->bInPass=true;R(p->UpdateExVertexBuffer(buffer,0,2,patch.data())==GR_INVALID_PARMS,"in-pass rejection");e->bInPass=false;
 C(p->DestroyExVertexBuffer(buffer));
 // During device loss, backing data still accepts updates for later recreation.
 p->Device_=nullptr;C(p->CreateExVertexBuffer(unsigned(original.size()),original.data(),&buffer));
 R(!buffer->Vb,"CPU backing only");C(p->UpdateExVertexBuffer(buffer,0,2,patch.data()));
 R(buffer->Data[0]==55&&buffer->Data[1]==55&&buffer->Data[2]==17,"device-loss backing update");
 C(p->DestroyExVertexBuffer(buffer));p->Device_=d;
 puts("PASS actual built RP9: partial GPU write, stable buffer, reset backing, loss/overflow/range/in-pass handling");
 return 0;
}
''')
    compiler,env=compiler_env()
    env['INCLUDE']=';'.join(p for p in env['INCLUDE'].split(';') if 'DXSDK' not in p.upper())+';C:/DXSDK_Jun10/Include'
    env['PATH']=str(ROOT/'bin')+';D:/Games/FL_MOD/bin;'+env['PATH']
    objects=[str(OUT/'build/obj/RP9'/(n+'.obj')) for n in ('RP9','RP9Ex','Mgsdb')]
    exe=probe/'check.exe'
    cmd=[str(compiler/'cl.exe'),'/nologo','/EHsc','/MD','/O2','/std:c++17','/utf-8',
         '/DRP_DIRECT3D9','/DFREELANCER_DLSS5','/D_ITERATOR_DEBUG_LEVEL=1','/D_CRT_SECURE_NO_WARNINGS','/DNOMINMAX',
         '/Isrc/RP9','/Isrc/include',str(source),'/Fo'+str(probe/'check.obj'),'/Fe'+str(exe),*objects,
         '/link','/LTCG','/LIBPATH:'+str(ROOT/'bin'),'d3d9.lib','user32.lib','gdi32.lib','C:/DXSDK_Jun10/Lib/x86/d3dx9.lib',
         'dacom.lib','ddraw.lib','version.lib','C:/DXSDK_Jun10/Lib/x86/DxErr.lib','legacy_stdio_definitions.lib']
    for name,args in [('build_buffers',cmd),('result_buffers',[str(exe),'unused'])]:
        result=subprocess.run(args,cwd=ROOT,env=env,stdout=subprocess.PIPE,stderr=subprocess.STDOUT)
        (OUT/(name+'.log')).write_bytes(result.stdout);print(result.stdout.decode(errors='replace')[-2000:]);result.check_returncode()
    paths=['src/RP9/RP9Ex.cpp','src/RP9/RP9.h','src/include/render/IRenderPipelineEx.h','tools/nebula_control/check_asteroid_buffers.py']
    (OUT/'buffer_checks.json').write_text(json.dumps({'passed':True,'sources':{p:hashlib.sha256((ROOT/p).read_bytes()).hexdigest() for p in paths}},indent=2))
if __name__=='__main__':main()
