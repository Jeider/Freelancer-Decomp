"""Render the actual exported mesh through RP9; does not start Freelancer."""
from pathlib import Path
import numpy as np
import subprocess,os
ROOT=Path(__file__).resolve().parents[2];OUT=ROOT/'out/nomad_character/surface'
m=np.load(ROOT/'out/nomad_character/game_body_v3/mesh.npz')
np.column_stack((m['points'],m['normals'],m['uv'],m['uv'])).astype('<f4').tofile(OUT/'vertices.bin')
m['faces'].astype('<u2').tofile(OUT/'indices.bin')
template=(ROOT/'tools/room_materials/check_route.cpp').read_text()
prefix=template.split(' auto native=render(false,q,sizeof(V))')[0]
prefix=prefix.replace('static void C(HRESULT h){if(FAILED(h)){printf("HRESULT %08lx\\n",h);exit(2);}}','static void CheckHr(HRESULT h,int line){if(FAILED(h)){printf("HRESULT %08lx line %d\\n",h,line);exit(2);}}\n#define C(h) CheckHr(h,__LINE__)')
body=r'''
 p->ExSurfaceRelease();
 IDirect3DTexture9* atlas=nullptr;
 C(D3DXCreateTextureFromFileA(d,"out/nomad_character/surface/base.jpg",&atlas));
 base.Texture->Release();base.Texture=atlas;C(d->SetTexture(0,atlas));
 tss(1,D3DTSS_COLOROP,D3DTOP_DISABLE);tss(0,D3DTSS_ALPHAARG2,D3DTA_DIFFUSE);
 mat.Diffuse={1,1,1,1};mat.Ambient={1,1,1,1};mat.Emissive={0,0,0,0};C(p->SetMaterial(&mat));
 rs(D3DRS_AMBIENT,0xff303038);rs(D3DRS_ZENABLE,1);rs(D3DRS_ZWRITEENABLE,1);
 light.Direction={.4f,-.6f,1};light.Diffuse={.8f,.8f,.85f,1};C(p->SetLight(nullptr,&light));p->LightManager_.Flush(d);
 std::vector<V> verts(VERT_COUNT);std::vector<unsigned short> ix(INDEX_COUNT);
 FILE* f=fopen("out/nomad_character/surface/vertices.bin","rb");R(f!=nullptr,"vertices open");R(fread(verts.data(),sizeof(V),verts.size(),f)==verts.size(),"vertices read");fclose(f);
 f=fopen("out/nomad_character/surface/indices.bin","rb");R(f!=nullptr,"indices open");R(fread(ix.data(),2,ix.size(),f)==ix.size(),"indices read");fclose(f);
 IDirect3DSurface9* rt=nullptr,*depth=nullptr;
 C(d->CreateRenderTarget(768,768,D3DFMT_A8R8G8B8,D3DMULTISAMPLE_NONE,0,FALSE,&rt,0));
 C(d->CreateDepthStencilSurface(768,768,D3DFMT_D24S8,D3DMULTISAMPLE_NONE,0,TRUE,&depth,0));
 C(d->SetRenderTarget(0,rt));C(d->SetDepthStencilSurface(depth));
 D3DVIEWPORT9 vp={0,0,768,768,0,1};C(d->SetViewport(&vp));
 for(int close=0;close<2;++close)for(int effect=0;effect<2;++effect){
  p->ExSurfaceRelease();
  D3DXVECTOR3 eye(.12f,close?.77f:.45f,-3),at(0,close?.72f:0,0),up(0,1,0);D3DXMATRIX view,projection;
  D3DXMatrixLookAtLH(&view,&eye,&at,&up);D3DXMatrixOrthoLH(&projection,close?.52f:2.1f,close?.52f:2.1f,.1f,10);
  memcpy(p->Transforms_.View.Values,&view,64);memcpy(p->Transforms_.Projection.Values,&projection,64);
  C(d->SetTransform(D3DTS_VIEW,&view));C(d->SetTransform(D3DTS_PROJECTION,&projection));
  C(p->SetRoomMaterial("alien_nomad_body","alien_nomad_body.tga"));
  C(d->Clear(0,0,D3DCLEAR_TARGET|D3DCLEAR_ZBUFFER,0xff10151c,1,0));C(d->BeginScene());
  if(effect)R(p->ExSurfaceBegin(),"alien preview route");
  C(d->DrawIndexedPrimitiveUP(D3DPT_TRIANGLELIST,0,(UINT)verts.size(),(UINT)ix.size()/3,ix.data(),D3DFMT_INDEX16,verts.data(),sizeof(V)));
  if(effect)p->ExSurfaceEnd();C(d->EndScene());
  char path[256];sprintf(path,"out/nomad_character/surface/%s_%s.png",close?"head":"body",effect?"alien":"native");
  C(D3DXSaveSurfaceToFileA(path,D3DXIFF_PNG,rt,0,0));puts(path);
 }
 return 0;
}
'''.replace('VERT_COUNT',str(len(m['points']))).replace('INDEX_COUNT',str(m['faces'].size))
(OUT/'preview.cpp').write_text(prefix+body)
cmd=ROOT/'src/obj/room_materials/check.cmd'
build=cmd.read_text().replace('tools/room_materials/check_route.cpp','out/nomad_character/surface/preview.cpp').replace('/Fosrc/obj/room_materials/check.obj','/Foout/nomad_character/surface/preview.obj').replace('/Febin/room_material_check.exe','/Febin/nomad_surface_preview.exe')
(OUT/'preview.cmd').write_text(build)
subprocess.run(['cmd','/c',str(OUT/'preview.cmd')],cwd=ROOT,check=True)
subprocess.run([str(ROOT/'bin/nomad_surface_preview.exe')],cwd=ROOT,env=dict(os.environ,FREELANCER_SHADER_CACHE_DIR=str(OUT/'shader_cache')),check=True)
