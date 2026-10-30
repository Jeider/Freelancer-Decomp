"""Hidden D3D9 device: compile surface variants and verify the user gates on pixels."""
from pathlib import Path
import os
import subprocess

root=Path(__file__).resolve().parents[2]
out=root/'src/obj/graphics_settings_gpu'
out.mkdir(parents=True,exist_ok=True)
source=(root/'tools/check_ice_surface.cpp').read_text()
source=source[:source.index(' pc[385]=0;auto noDepth')]
source=source.replace('float pc[97*4]','float pc[107*4]').replace('SetPixelShaderConstantF(0,pc,97)','SetPixelShaderConstantF(0,pc,107)')
source='\n'.join(line for line in source.splitlines() if 'auto oldCode=' not in line and 'oldCode.data()' not in line)+'\n'
begin=source.index(' for(float style:')
end=source.index(' pc[384]=1;auto ice',begin)
source=source[:begin]+' pc[376]=pc[377]=0;pc[31]=-1;pc[18]=0;\n'+source[end:]
source=source.replace('Check(D3DXCreateTextureFromFileA(d,"src/obj/ice_surface_check/base.dds",&base));',r'''
 Check(d->CreateTexture(1,1,1,0,D3DFMT_A8R8G8B8,D3DPOOL_MANAGED,&base,nullptr));
 D3DLOCKED_RECT baseLock;Check(base->LockRect(0,&baseLock,nullptr,0));*(DWORD*)baseLock.pBits=0xff657987;base->UnlockRect(0);
''')
source+=r'''
 pc[106*4+1]=1;auto noGlints=render(ps);
 Require(compare(ice,noGlints).first>1000,"user highlight gate removes ice's independent polish");
 pc[106*4+1]=0;pc[106*4+2]=1;auto noReflections=render(ps);
 Require(compare(ice,noReflections).first>1000,"user reflection gate removes ice's fallback sky reflection");
 pc[106*4+1]=1;auto bothOff=render(ps);
 Require(compare(bothOff,noReflections).first>1000,"reflection and highlight controls are independent");
 pc[106*4+1]=pc[106*4+2]=0;auto restored=render(ps);
 Require(compare(ice,restored).first==0,"reenabling restores the exact original frame");
 pc[384]=0;pc[31]=5;auto hull=render(ps);pc[106*4+1]=1;auto matteHull=render(ps);
 Require(compare(hull,matteHull).first>1000,"highlight gate removes ordinary hull gloss");
 pc[106*4+1]=0;pc[377]=1;pc[378]=1.5f;auto glass=render(ps);
 pc[106*4+2]=1;auto glassNoReflections=render(ps);Require(compare(glass,glassNoReflections).first>1000,"glass reflection gate");
 pc[106*4+1]=1;auto glassBothOff=render(ps);Require(compare(glassNoReflections,glassBothOff).first>1000,"glass highlights survive disabling reflections");
 puts("PASS: surface shader variants compile on D3D9; independent highlight/reflection switches change pixels and restore exactly");
 d->SetTexture(0,nullptr);d->SetTexture(10,nullptr);d->SetTexture(13,nullptr);d->SetVertexShader(nullptr);d->SetPixelShader(nullptr);
 read->Release();rt->Release();base->Release();layers->Release();env->Release();vs->Release();ps->Release();d->Release();api->Release();DestroyWindow(window);
}
'''
(out/'gpu.cpp').write_text(source)
vc=Path('C:/Program Files/Microsoft Visual Studio/18/Community/VC/Tools/MSVC/14.51.36231')
sdk=Path('C:/Program Files (x86)/Windows Kits/10'); version='10.0.26100.0'
dx=Path('C:/DXSDK_Jun10')
env=dict(os.environ)
env['INCLUDE']=';'.join(map(str,[vc/'include']+[sdk/'Include'/version/x for x in ('ucrt','shared','um')]+[dx/'Include']))
env['LIB']=';'.join(map(str,[vc/'lib/x86']+[sdk/'Lib'/version/x/'x86' for x in ('ucrt','um')]))
env['PATH']=str(root/'src/obj/graphics_settings_bin')+os.pathsep+env.get('PATH','')
env['FREELANCER_SHADER_CACHE_DIR']=str(out/'cache')
subprocess.run([str(vc/'bin/Hostx64/x86/cl.exe'),'/nologo','/std:c++17','/O2','/EHsc','/MT','/DNOMINMAX','/D_CRT_SECURE_NO_WARNINGS',f'/I{root/"src/RP9"}','gpu.cpp','/Fegpu.exe','/link','d3d9.lib',str(dx/'Lib/x86/d3dx9.lib'),'user32.lib'],cwd=out,env=env,check=True)
subprocess.run([str(out/'gpu.exe')],cwd=root,env=env,check=True)

