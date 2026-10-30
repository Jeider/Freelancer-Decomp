#include "RP9Ex.h"
#include "../../src/include/render/NomadEnergyPolicy.h"
#include <d3dx9.h>
#include <cstdio>
#include <cstdlib>
#include <vector>
static void Need(bool b,const char* s){if(!b){printf("FAIL %s\n",s);exit(3);}}
static void Check(HRESULT h){if(FAILED(h)){printf("HRESULT %08lx\n",h);exit(2);}}
struct Vertex {float x,y,z,nx,ny,nz,u,v;};
#include "dds_upload_check.h"
int main(){
 setvbuf(stdout,nullptr,_IONBF,0);SetErrorMode(SEM_FAILCRITICALERRORS|SEM_NOGPFAULTERRORBOX);
 Need(NomadEnergyProfile("lair_rock_mbrn_2side","lair_rock_membrane.tga")==RPSurfaceLairMembrane,"outer identity");
 Need(NomadEnergyProfile("lair_rckint_mem_2side","lair_rckint_membrane.tgalair_op.tga")==RPSurfaceLairMembrane,"inner identity");
 Need(NomadEnergyProfile("lair_energyglow_ni","lair_energy2.tga")==RPSurfaceLairEnergy,"beta energy");
 Need(NomadEnergyProfile("lair_energy_ni","lair_energy.tga")==RPSurfaceLairEnergy,"retail energy");
 Need(!NomadEnergyProfile("lair_energy_red","dyson_skin05.tga") && !NomadEnergyProfile("unrelated","lair_energy2.tga") && !NomadEnergyProfile("lair_energy","wrong.tga"),"unrelated identities excluded");
 HWND w=CreateWindowA("STATIC","Energy test",WS_POPUP,0,0,64,64,nullptr,nullptr,GetModuleHandle(nullptr),nullptr);
 auto* api=Direct3DCreate9(D3D_SDK_VERSION);Need(api!=nullptr,"D3D9");
 D3DPRESENT_PARAMETERS pp={};pp.Windowed=TRUE;pp.SwapEffect=D3DSWAPEFFECT_DISCARD;pp.BackBufferWidth=pp.BackBufferHeight=64;pp.BackBufferFormat=D3DFMT_A8R8G8B8;pp.EnableAutoDepthStencil=TRUE;pp.AutoDepthStencilFormat=D3DFMT_D24S8;
 IDirect3DDevice9* d=nullptr;Check(api->CreateDevice(0,D3DDEVTYPE_HAL,w,D3DCREATE_HARDWARE_VERTEXPROCESSING,&pp,&d));
 auto* p=new FDirectX9();p->Device_=d;p->DeviceReady_=1;auto* e=p->Ex_;
 CheckWebDdsUpload(p,d);
 e->bNomadEnergyPrepared=true;e->bNomadEnergyEnabled=true;e->NomadEnergyStrength=1;
 Need(p->ExCompileShaderPair("nomad_energy.hlsl",&e->NomadEnergyVs,&e->NomadEnergyPs),"production shader compile");
 D3DMATERIAL9 m={};m.Diffuse=m.Ambient={1,1,1,1};Check(p->SetMaterial(&m));
 const DWORD fvf=D3DFVF_XYZ|D3DFVF_NORMAL|D3DFVF_TEX1;p->StreamCache_.Fvf=fvf;Check(d->SetFVF(fvf));
 D3DXMATRIX id;D3DXMatrixIdentity(&id);
 memcpy(p->Transforms_.World.Values,&id,64);memcpy(p->Transforms_.View.Values,&id,64);memcpy(p->Transforms_.Projection.Values,&id,64);memcpy(p->DeviceStates_.TextureTransforms[0].Values,&id,64);
 auto rs=[&](D3DRENDERSTATETYPE s,DWORD v){p->RenderStates_.MarkDirty(s,v);Check(d->SetRenderState(s,v));};
 auto tss=[&](D3DTEXTURESTAGESTATETYPE s,DWORD v){auto& x=p->DeviceStates_.TextureStates[0][s];x.Value=v;x.bValid=1;Check(d->SetTextureStageState(0,s,v));};
 rs(D3DRS_LIGHTING,FALSE);rs(D3DRS_ALPHABLENDENABLE,FALSE);rs(D3DRS_ZENABLE,TRUE);rs(D3DRS_ZWRITEENABLE,TRUE);rs(D3DRS_ZFUNC,D3DCMP_LESSEQUAL);rs(D3DRS_CULLMODE,D3DCULL_NONE);rs(D3DRS_COLORWRITEENABLE,15);rs(D3DRS_FOGENABLE,FALSE);rs(D3DRS_ALPHATESTENABLE,FALSE);
 tss(D3DTSS_TEXCOORDINDEX,0);tss(D3DTSS_TEXTURETRANSFORMFLAGS,0);tss(D3DTSS_COLOROP,D3DTOP_SELECTARG1);tss(D3DTSS_COLORARG1,D3DTA_TEXTURE);tss(D3DTSS_ALPHAOP,D3DTOP_SELECTARG1);tss(D3DTSS_ALPHAARG1,D3DTA_TEXTURE);
 d->SetTextureStageState(1,D3DTSS_COLOROP,D3DTOP_DISABLE);
 IDirect3DTexture9* tex=nullptr;Check(d->CreateTexture(8,8,1,0,D3DFMT_A8R8G8B8,D3DPOOL_MANAGED,&tex,nullptr));
 D3DLOCKED_RECT lock={};Check(tex->LockRect(0,&lock,nullptr,0));for(unsigned y=0;y<8;++y)for(unsigned x=0;x<8;++x)reinterpret_cast<DWORD*>(static_cast<char*>(lock.pBits)+y*lock.Pitch)[x]=(x<4?0:0xff000000)|((72+x*12)<<16)|((24+y*6)<<8)|16;tex->UnlockRect(0);d->SetTexture(0,tex);
 Vertex q[]={{-1,1,.5f,0,0,-1,0,0},{1,1,.5f,0,0,-1,1,0},{-1,-1,.5f,0,0,-1,0,1},{1,-1,.5f,0,0,-1,1,1}};
 IDirect3DSurface9* rt=nullptr;d->GetRenderTarget(0,&rt);IDirect3DSurface9* read=nullptr;Check(d->CreateOffscreenPlainSurface(64,64,D3DFMT_A8R8G8B8,D3DPOOL_SYSTEMMEM,&read,nullptr));
 auto image=[&](unsigned profile,float phase,float depth=1.f,float strength=1.f,bool nativeBase=false){
   Check(p->SetSurfaceShader(profile,0,-1));e->NomadEnergyStrength=strength;
   Check(d->Clear(0,nullptr,D3DCLEAR_TARGET|D3DCLEAR_ZBUFFER,0xff102030,depth,0));Check(d->BeginScene());
   Need(!p->ExSurfaceBegin(),"base remains native");p->ExSurfaceRelease();
   if(nativeBase) Check(d->DrawPrimitiveUP(D3DPT_TRIANGLESTRIP,2,q,sizeof(Vertex)));
   float saved[4]={.2f,.3f,.4f,.5f};d->SetPixelShaderConstantF(0,saved,1);
   if(p->ExNomadEnergyBegin()){
     float c[4];d->GetPixelShaderConstantF(0,c,1);c[0]=phase;d->SetPixelShaderConstantF(0,c,1);
     Check(d->DrawPrimitiveUP(D3DPT_TRIANGLESTRIP,2,q,sizeof(Vertex)));p->ExNomadEnergyEnd();
     DWORD value=0;d->GetRenderState(D3DRS_ALPHABLENDENABLE,&value);Need(value==FALSE,"blend restored");d->GetRenderState(D3DRS_ZWRITEENABLE,&value);Need(value==TRUE,"depth write restored");d->GetRenderState(D3DRS_COLORWRITEENABLE,&value);Need(value==15,"alpha target restored");
     float restored[4];d->GetPixelShaderConstantF(0,restored,1);Need(!memcmp(saved,restored,sizeof(saved)),"constants restored");
     IDirect3DPixelShader9* ps=nullptr;d->GetPixelShader(&ps);Need(!ps,"native shader restored");
   }else Need(strength==0 || profile==RPSurfaceAuto,"overlay accepted");
   Check(d->EndScene());Check(d->GetRenderTargetData(rt,read));D3DLOCKED_RECT l={};Check(read->LockRect(&l,nullptr,D3DLOCK_READONLY));std::vector<DWORD> out(4096);for(unsigned y=0;y<64;++y)memcpy(out.data()+y*64,static_cast<char*>(l.pBits)+y*l.Pitch,256);read->UnlockRect();return out;
 };
 auto native=image(RPSurfaceLairMembrane,0,1,0),membrane=image(RPSurfaceLairMembrane,0),later=image(RPSurfaceLairMembrane,2),energy=image(RPSurfaceLairEnergy,0),blocked=image(RPSurfaceLairMembrane,0,.1f);
 Need(native==blocked,"occluded glow suppressed");Need(native!=membrane && membrane==later,"visible stationary membrane; no second animation clock");
 Need(image(RPSurfaceLairEnergy,0,1,0,true)!=image(RPSurfaceLairEnergy,0,1,1,true),"overlay visible over native depth-writing base");
 Need(membrane==image(RPSurfaceLairMembrane,6.28318530718f),"seamless time wrap");
 Need(energy==image(RPSurfaceLairEnergy,2),"energy uses MaterialAnim only");
 Need(membrane[32*64+8]==native[32*64+8],"transparent holes remain open");Need(energy[32*64+8]!=native[32*64+8],"opaque energy ignores unused texture alpha");
 for(unsigned i=0;i<4096;++i)Need((membrane[i]&0xff000000)==(native[i]&0xff000000),"framebuffer alpha preserved");
 tss(D3DTSS_TEXTURETRANSFORMFLAGS,D3DTTFF_COUNT2);p->DeviceStates_.TextureTransforms[0].Values[12]=.5f;auto shifted=image(RPSurfaceLairMembrane,0);Need(shifted[32*64+8]!=native[32*64+8],"authored UV transform followed");
 Need(image(RPSurfaceLairEnergy,0)!=energy,"organic energy follows MaterialAnim UV movement");
 tss(D3DTSS_TEXTURETRANSFORMFLAGS,0);rs(D3DRS_FOGENABLE,TRUE);rs(D3DRS_FOGTABLEMODE,D3DFOG_LINEAR);float start=0,end=.1f;DWORD s,f;memcpy(&s,&start,4);memcpy(&f,&end,4);rs(D3DRS_FOGSTART,s);rs(D3DRS_FOGEND,f);Need(image(RPSurfaceLairMembrane,0)==native,"fog hides overlay");rs(D3DRS_FOGENABLE,FALSE);
 e->bShadowDrawing=true;Need(!p->ExNomadEnergyBegin(),"no shadow-pass overlay");e->bShadowDrawing=false;
 Check(p->SetSurfaceShader(RPSurfaceAuto,0,-1));Need(!p->ExNomadEnergyBegin(),"scope reset");
 p->ExReleaseAllGpu();Need(!e->NomadEnergyVs && !e->NomadEnergyPs && !e->NomadEnergySaved && !e->bNomadEnergyPrepared,"device release");p->Device_=nullptr;p->DeviceReady_=0;delete p;
 read->Release();rt->Release();d->SetTexture(0,nullptr);tex->Release();d->Release();api->Release();DestroyWindow(w);
 puts("PASS identities, native fallback, animation, alpha holes, depth occlusion, UV transform, fog, state restore, device release");
}
