#include "RP9Ex.h"
#include "dacom_iids.h"
#include "RP9DeviceCallCache.h"
#include <d3dx9.h>
#include <cstdio>
#include <cstdlib>
#include <vector>
#include <algorithm>
#include <string>
static void CheckResult(HRESULT h,int line) {if(FAILED(h)){printf("HRESULT %08lx at line %d\n",h,line);exit(2);}}
#define C(h) CheckResult((h),__LINE__)
static void R(bool ok,const char* what){if(!ok){printf("FAIL %s\n",what);exit(3);}}
struct V {float x,y,z,nx,ny,nz,u,v;};
struct SV {float x,y,z,w0,w1,w2;DWORD bones;float nx,ny,nz,u,v;};
struct Group {unsigned hair;std::vector<V> vertices;};
struct Handle {IDirect3DTexture9* Texture=nullptr;unsigned long Extra=0;};
int main(int argc,char**argv){
 setvbuf(stdout,nullptr,_IONBF,0);
 SetErrorMode(SEM_FAILCRITICALERRORS|SEM_NOGPFAULTERRORBOX|SEM_NOOPENFILEERRORBOX);
 const std::string out=std::string(argc>1?argv[1]:"out/hair_lighting/lutz")+"/";
 FILE*f=fopen((out+"head.bin").c_str(),"rb");R(f!=nullptr,"head input");
 unsigned count=0;fread(&count,4,1,f);std::vector<Group> groups(count);
 for(auto&g:groups){unsigned n=0;fread(&g.hair,4,1,f);fread(&n,4,1,f);g.vertices.resize(n);R(fread(g.vertices.data(),sizeof(V),n,f)==n,"vertices");}fclose(f);
 HWND w=CreateWindowA("STATIC","Lutz offline material probe",WS_POPUP,0,0,512,640,0,0,GetModuleHandle(0),0);
 auto*a=Direct3DCreate9(D3D_SDK_VERSION);R(a!=nullptr,"D3D9");IDirect3DDevice9*d=nullptr;
 D3DPRESENT_PARAMETERS pp={};pp.Windowed=1;pp.SwapEffect=D3DSWAPEFFECT_DISCARD;
 pp.BackBufferWidth=512;pp.BackBufferHeight=640;pp.BackBufferFormat=D3DFMT_A8R8G8B8;
 pp.EnableAutoDepthStencil=1;pp.AutoDepthStencilFormat=D3DFMT_D24X8;
 C(a->CreateDevice(0,D3DDEVTYPE_HAL,w,D3DCREATE_HARDWARE_VERTEXPROCESSING,&pp,&d));
 auto*p=new FDirectX9();p->Outer_=&p->Inner_;p->Device_=d;p->DeviceReady_=1;auto*e=p->Ex_;
 e->bSurfaceConfigRead=true;e->bSurfaceEnabled=false;e->bRoomRead=true;
 D3DXMATRIX id,view,projection;D3DXMatrixIdentity(&id);
 D3DXVECTOR3 eye(.32f,.045f,.65f),at(0,.025f,0),up(0,1,0);
 D3DXMatrixLookAtLH(&view,&eye,&at,&up);D3DXMatrixOrthoLH(&projection,.27f,.3375f,.01f,2);
 memcpy(p->Transforms_.World.Values,&id,64);memcpy(p->Transforms_.View.Values,&view,64);
 memcpy(p->Transforms_.Projection.Values,&projection,64);
 C(Rp9SetTransform(d,D3DTS_WORLD,&id));C(Rp9SetTransform(d,D3DTS_VIEW,&view));C(Rp9SetTransform(d,D3DTS_PROJECTION,&projection));
 for(int i=0;i<8;i++)memcpy(p->DeviceStates_.TextureTransforms[i].Values,&id,64);
 auto rs=[&](unsigned s,unsigned v){p->RenderStates_.MarkDirty(s,v);C(Rp9SetRenderState(d,(D3DRENDERSTATETYPE)s,v));};
 auto tss=[&](unsigned s,unsigned t,unsigned v){auto&x=p->DeviceStates_.TextureStates[s][t];x.Value=v;x.bValid=1;C(d->SetTextureStageState(s,(D3DTEXTURESTAGESTATETYPE)t,v));};
 rs(D3DRS_LIGHTING,1);rs(D3DRS_ALPHABLENDENABLE,0);rs(D3DRS_AMBIENT,0xff30383c);
 rs(D3DRS_CULLMODE,D3DCULL_NONE);rs(D3DRS_ZENABLE,1);rs(D3DRS_ZWRITEENABLE,1);rs(D3DRS_ZFUNC,D3DCMP_LESSEQUAL);
 rs(D3DRS_COLORVERTEX,0);rs(D3DRS_FOGENABLE,0);rs(D3DRS_SPECULARENABLE,0);rs(D3DRS_NORMALIZENORMALS,1);
 for(unsigned s=0;s<2;s++){tss(s,D3DTSS_COLOROP,s?D3DTOP_DISABLE:D3DTOP_MODULATE);tss(s,D3DTSS_COLORARG1,D3DTA_TEXTURE);tss(s,D3DTSS_COLORARG2,D3DTA_DIFFUSE);
  tss(s,D3DTSS_ALPHAOP,D3DTOP_SELECTARG1);tss(s,D3DTSS_ALPHAARG1,D3DTA_TEXTURE);tss(s,D3DTSS_ALPHAARG2,D3DTA_CURRENT);
  tss(s,D3DTSS_TEXCOORDINDEX,0);tss(s,D3DTSS_TEXTURETRANSFORMFLAGS,0);tss(s,D3DTSS_RESULTARG,D3DTA_CURRENT);}
 tss(2,D3DTSS_COLOROP,D3DTOP_DISABLE);
 D3DMATERIAL9 mat={};mat.Diffuse={1,1,1,1};mat.Ambient={1,1,1,1};C(p->SetMaterial(&mat));
 Handle base;C(D3DXCreateTextureFromFileExA(d,(out+"diffuse.tga").c_str(),D3DX_DEFAULT,D3DX_DEFAULT,D3DX_DEFAULT,0,D3DFMT_A8R8G8B8,D3DPOOL_MANAGED,D3DX_FILTER_NONE,D3DX_FILTER_BOX,0,nullptr,nullptr,&base.Texture));
 p->DeviceStates_.TextureBindings[0]={&base,1,{}};C(Rp9SetTexture(d,0,base.Texture));
 for(auto s:{D3DSAMP_MINFILTER,D3DSAMP_MAGFILTER,D3DSAMP_MIPFILTER})C(Rp9SetSamplerState(d,0,s,D3DTEXF_LINEAR));
 D3DLIGHT9 light={};light.Type=D3DLIGHT_DIRECTIONAL;light.Direction={-.4f,-.7f,-.5f};light.Diffuse={.8f,.75f,.65f,1};
 C(p->SetLight(nullptr,&light));C(p->SetLightEnable(nullptr,1));C(p->LightManager_.Flush(d));
 C(p->SetRoomMaterialFrame(1));
 unsigned fvf=D3DFVF_XYZ|D3DFVF_NORMAL|D3DFVF_TEX1;p->StreamCache_.Fvf=fvf;C(Rp9SetFvf(d,fvf));
 IDirect3DSurface9*target=nullptr,*read=nullptr;C(d->GetRenderTarget(0,&target));
 C(d->CreateOffscreenPlainSurface(512,640,D3DFMT_A8R8G8B8,D3DPOOL_SYSTEMMEM,&read,0));
 bool skinned=false;
 auto render=[&](const char*name,bool modern,bool prime,bool faceOnly){
  C(d->Clear(0,0,D3DCLEAR_TARGET|D3DCLEAR_ZBUFFER,0xff182028,1,0));C(d->BeginScene());
  auto draw=[&](Group const&g,bool shader){
   C(p->SetRoomMaterial(shader?"short_hair_rh_sales_head01":"rh_sales_head01","rh_sales_head02.TGA"));
   bool active=p->ExSurfaceBegin();R(active==shader,"face native / hair shader selection");if(!active)p->ExSurfaceRelease();
   if(skinned){std::vector<SV> vertices;for(auto const&v:g.vertices)vertices.push_back({v.x,v.y,v.z,1,0,0,0,v.nx,v.ny,v.nz,v.u,v.v});
    C(d->DrawPrimitiveUP(D3DPT_TRIANGLELIST,(UINT)vertices.size()/3,vertices.data(),sizeof(SV)));}
   else C(d->DrawPrimitiveUP(D3DPT_TRIANGLELIST,(UINT)g.vertices.size()/3,g.vertices.data(),sizeof(V)));
   if(active)p->ExSurfaceEnd();
  };
  if(prime){for(auto const&g:groups)if(g.hair)draw(g,true);C(d->Clear(0,0,D3DCLEAR_TARGET|D3DCLEAR_ZBUFFER,0xff182028,1,0));}
  for(auto const&g:groups){if(faceOnly&&g.hair)continue;draw(g,modern&&g.hair);}
  C(d->EndScene());C(d->GetRenderTargetData(target,read));
  C(D3DXSaveSurfaceToFileA((out+name+".png").c_str(),D3DXIFF_PNG,read,0,0));
  D3DLOCKED_RECT l;C(read->LockRect(&l,0,D3DLOCK_READONLY));std::vector<DWORD>pixels;
  for(int y=0;y<640;y++)for(int x=0;x<512;x++)pixels.push_back(((DWORD*)((char*)l.pBits+y*l.Pitch))[x]);read->UnlockRect();
  return pixels;
 };
 auto native=render("native",false,false,false);
 auto enhanced=render("enhanced",true,false,false);
 auto face=render("face_native",false,false,true);
 auto after=render("face_after_hair",false,true,true);
 unsigned maxDelta=0,changed=0;
 for(size_t i=0;i<face.size();i++){if(face[i]!=after[i])changed++;for(int k=0;k<3;k++)maxDelta=(std::max)(maxDelta,unsigned(abs(int((face[i]>>(k*8))&255)-int((after[i]>>(k*8))&255))));}
 printf("Face after hair: %u changed pixels; max channel delta %u\n",changed,maxDelta);
 R(maxDelta==0,"hair shader leaves native face unchanged");
 skinned=true;fvf=D3DFVF_XYZB4|D3DFVF_LASTBETA_UBYTE4|D3DFVF_NORMAL|D3DFVF_TEX1;
 p->StreamCache_.Fvf=fvf;C(Rp9SetFvf(d,fvf));
 for(unsigned i=0;i<64;i++)memcpy(e->RoomBones[i],&id,64);
 rs(D3DRS_INDEXEDVERTEXBLENDENABLE,1);rs(D3DRS_VERTEXBLEND,D3DVBF_3WEIGHTS);
 auto skinNative=render("skinned_native",false,false,false);
 auto skinEnhanced=render("skinned_enhanced",true,false,false);
 auto skinFace=render("skinned_face_native",false,false,true);
 auto skinAfter=render("skinned_face_after_hair",false,true,true);
 maxDelta=changed=0;
 for(size_t i=0;i<skinFace.size();i++){if(skinFace[i]!=skinAfter[i])changed++;for(int k=0;k<3;k++)maxDelta=(std::max)(maxDelta,unsigned(abs(int((skinFace[i]>>(k*8))&255)-int((skinAfter[i]>>(k*8))&255))));}
 printf("Skinned face after hair: %u changed pixels; max channel delta %u\n",changed,maxDelta);
 R(maxDelta==0,"hair shader leaves indexed skinned face unchanged");
 puts("PASS actual Lutz face/hair geometry, shared diffuse, native rendering after programmable shader.");
 return 0;
}
