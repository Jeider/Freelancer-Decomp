// Tests production ExSurfaceBegin, including the actual DcDtEt/Bt stage layouts.
#include "RP9Ex.h"
#include <d3dx9.h>
#include <cstdio>
#include <cstdlib>
static void Need(bool b,const char* s){if(!b){printf("FAIL %s\n",s);exit(3);}}
static void Check(HRESULT h){if(FAILED(h)){printf("HRESULT %08lx\n",h);exit(2);}}
struct Handle{IDirect3DTexture9* Texture;unsigned long Extra;};
int main(){
 setvbuf(stdout,nullptr,_IONBF,0);SetErrorMode(SEM_FAILCRITICALERRORS|SEM_NOGPFAULTERRORBOX|SEM_NOOPENFILEERRORBOX);
 HWND w=CreateWindowA("STATIC","Nomad route",WS_POPUP,0,0,64,64,nullptr,nullptr,GetModuleHandle(nullptr),nullptr);auto* api=Direct3DCreate9(D3D_SDK_VERSION);Need(api!=nullptr,"D3D9");
 D3DPRESENT_PARAMETERS pp={};pp.Windowed=TRUE;pp.SwapEffect=D3DSWAPEFFECT_DISCARD;pp.BackBufferWidth=pp.BackBufferHeight=64;pp.BackBufferFormat=D3DFMT_A8R8G8B8;
 IDirect3DDevice9* d=nullptr;Check(api->CreateDevice(0,D3DDEVTYPE_HAL,w,D3DCREATE_HARDWARE_VERTEXPROCESSING,&pp,&d));
 auto* pipe=new FDirectX9();pipe->Device_=d;pipe->DeviceReady_=1;auto* e=pipe->Ex_;e->bSurfaceConfigRead=e->bSurfaceEnabled=e->bSurfaceLogged=e->bQualityConfigRead=true;e->bShadowConfigRead=e->bWeaponGlintConfigRead=true;e->ShadowResolution[0]=e->ShadowResolution[1]=4096;
 D3DMATERIAL9 m={};m.Diffuse=m.Ambient={1,1,1,1};Check(pipe->SetMaterial(&m));pipe->StreamCache_.Fvf=D3DFVF_XYZ|D3DFVF_NORMAL|D3DFVF_TEX1;d->SetFVF(pipe->StreamCache_.Fvf);
 D3DXMATRIX id;D3DXMatrixIdentity(&id);memcpy(pipe->Transforms_.World.Values,&id,64);memcpy(pipe->Transforms_.View.Values,&id,64);memcpy(pipe->Transforms_.Projection.Values,&id,64);for(int i=0;i<8;++i)memcpy(pipe->DeviceStates_.TextureTransforms[i].Values,&id,64);
 auto rs=[&](unsigned s,unsigned v){pipe->RenderStates_.MarkDirty(s,v);};auto tss=[&](unsigned s,unsigned t,unsigned v){auto& a=pipe->DeviceStates_.TextureStates[s][t];a.Value=v;a.bValid=1;};
 rs(D3DRS_LIGHTING,1);rs(D3DRS_ALPHABLENDENABLE,0);rs(D3DRS_AMBIENT,0xff303030);rs(D3DRS_COLORWRITEENABLE,15);
 for(int s=0;s<2;++s){tss(s,D3DTSS_COLOROP,s==0?D3DTOP_MODULATE:D3DTOP_ADD);tss(s,D3DTSS_COLORARG1,D3DTA_TEXTURE);tss(s,D3DTSS_COLORARG2,s==0?D3DTA_DIFFUSE:D3DTA_CURRENT);tss(s,D3DTSS_ALPHAOP,D3DTOP_MODULATE);tss(s,D3DTSS_ALPHAARG1,D3DTA_TEXTURE);tss(s,D3DTSS_ALPHAARG2,s==0?D3DTA_DIFFUSE:D3DTA_CURRENT);tss(s,D3DTSS_TEXCOORDINDEX,0);}
 tss(2,D3DTSS_COLOROP,D3DTOP_DISABLE);Handle texture={};Check(d->CreateTexture(1,1,1,0,D3DFMT_A8R8G8B8,D3DPOOL_MANAGED,&texture.Texture,nullptr));for(int s=0;s<2;++s){pipe->DeviceStates_.TextureBindings[s]={&texture,1,{}};d->SetTexture(s,texture.Texture);}
 Need(!pipe->ExSurfaceBegin(),"unrelated detail stays native");
 Check(pipe->SetSurfaceShader(RPSurfaceNomadInterior,0,-1));Need(pipe->ExSurfaceBegin(),"actual DcDtEt routes to wet shader");float style[4],detail[4];d->GetPixelShaderConstantF(96,style,1);d->GetPixelShaderConstantF(97,detail,1);Need(style[0]==3 && style[1]>1 && detail[0]==7 && detail[3]==1,"interior and original illumination passed");pipe->ExSurfaceEnd();
 Check(pipe->SetSurfaceShader(RPSurfaceNomadLair,0,-1));tss(1,D3DTSS_COLOROP,D3DTOP_MODULATE2X);Need(pipe->ExSurfaceBegin(),"actual Bt detail exterior routes");d->GetPixelShaderConstantF(96,style,1);Need(style[0]==1,"outside stays rock profile");pipe->ExSurfaceEnd();
 tss(1,D3DTSS_TEXTURETRANSFORMFLAGS,D3DTTFF_COUNT2);pipe->DeviceStates_.TextureTransforms[1].Values[0]=8;Need(pipe->ExSurfaceBegin(),"scaled detail accepted");float transform[4];d->GetPixelShaderConstantF(98,transform,1);Need(transform[0]==8,"authored detail tile rate");pipe->ExSurfaceEnd();
 tss(1,D3DTSS_COLOROP,D3DTOP_DISABLE);Check(pipe->SetSurfaceShader(RPSurfaceDyson,.48f,0));rs(D3DRS_COLORWRITEENABLE,0);Need(pipe->ExSurfaceBegin(),"cheap depth routes");IDirect3DVertexShader9* depthVs=nullptr;d->GetVertexShader(&depthVs);Need(e->NomadDepthPs!=nullptr,"dedicated depth PS");pipe->ExSurfaceEnd();rs(D3DRS_COLORWRITEENABLE,15);Need(pipe->ExSurfaceBegin(),"Dyson colour routes");IDirect3DVertexShader9* colourVs=nullptr;d->GetVertexShader(&colourVs);Need(depthVs==colourVs,"bit-identical depth vertex transform");depthVs->Release();colourVs->Release();pipe->ExSurfaceEnd();
 e->SurfaceDistanceTier=2;Need(pipe->ExSurfaceBegin(),"far profile continuous");pipe->ExSurfaceEnd();e->SurfaceDistanceTier=0;
 rs(D3DRS_ALPHABLENDENABLE,1);rs(D3DRS_SRCBLEND,D3DBLEND_SRCALPHA);rs(D3DRS_DESTBLEND,D3DBLEND_INVSRCALPHA);Need(pipe->ExSurfaceBegin(),"distance fading cubes retain relief");pipe->ExSurfaceEnd();Check(pipe->SetSurfaceShader(RPSurfaceNomadInterior,0,-1));Need(!pipe->ExSurfaceBegin(),"unrelated transparent membranes stay native");rs(D3DRS_ALPHABLENDENABLE,0);
 e->bNomadShader=false;Need(!pipe->ExSurfaceBegin(),"feature off restores native");e->bNomadShader=true;Check(pipe->SetSurfaceShader(RPSurfaceAuto,0,-1));Need(!pipe->ExSurfaceBegin(),"scope reset");
 pipe->ExReleaseAllGpu();Need(!e->NomadLayers && !e->NomadVs && !e->NomadDepthPs && !e->bNomadTextureTried,"release reset");pipe->Device_=nullptr;pipe->DeviceReady_=0;delete pipe;for(int s:{0,1,13})d->SetTexture(s,nullptr);texture.Texture->Release();d->Release();api->Release();DestroyWindow(w);puts("PASS production routing, illumination, detail UV transform, depth VS, fade, feature-off, scope and device reset");
}
