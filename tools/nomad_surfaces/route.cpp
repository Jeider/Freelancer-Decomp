// Tests production ExSurfaceBegin, including the actual DcDtEt/Bt stage layouts.
#include "RP9Ex.h"
#include "../../src/include/render/NomadSurfacePolicy.h"
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
 pipe->ExRockNormalsPrepare();Need(e->RockDetail!=nullptr,"shared asteroid detail");
 Check(D3DXSaveTextureToFileA("src/obj/nomad_lair_revision/rock.dds",D3DXIFF_DDS,e->RockDetail,nullptr));
 Need(!pipe->ExSurfaceBegin(),"unrelated detail stays native");
 Check(pipe->SetSurfaceShader(RPSurfaceNomadInterior,0,-1));Need(pipe->ExSurfaceBegin(),"actual DcDtEt routes to wet shader");float style[4],detail[4];d->GetPixelShaderConstantF(96,style,1);d->GetPixelShaderConstantF(97,detail,1);Need(style[0]==3 && style[1]>1 && detail[0]==7 && detail[3]==1,"interior and original illumination passed");pipe->ExSurfaceEnd();
 Check(pipe->SetSurfaceShader(RPSurfaceNomadLair,0,-1));tss(1,D3DTSS_COLOROP,D3DTOP_MODULATE2X);Need(pipe->ExSurfaceBegin(),"actual Bt detail exterior routes");d->GetPixelShaderConstantF(96,style,1);Need(style[0]==1,"outside stays rock profile");pipe->ExSurfaceEnd();
 tss(1,D3DTSS_TEXTURETRANSFORMFLAGS,D3DTTFF_COUNT2);pipe->DeviceStates_.TextureTransforms[1].Values[0]=8;Need(pipe->ExSurfaceBegin(),"scaled detail accepted");float transform[4];d->GetPixelShaderConstantF(98,transform,1);Need(transform[0]==8,"authored detail tile rate");pipe->ExSurfaceEnd();
 tss(1,D3DTSS_COLOROP,D3DTOP_DISABLE);Check(pipe->SetSurfaceShader(RPSurfaceDyson,.48f,0));
 Need(e->SurfaceShader==RPSurfaceDyson,"direct cube-field Dyson selects one-layer bump");
 rs(D3DRS_COLORWRITEENABLE,0);Need(pipe->ExSurfaceBegin(),"Dyson existing depth pass available");
 IDirect3DVertexShader9* depthVs=nullptr;d->GetVertexShader(&depthVs);pipe->ExSurfaceEnd();
 rs(D3DRS_COLORWRITEENABLE,15);Need(pipe->ExSurfaceBegin(),"Dyson colour pass bump");
 IDirect3DVertexShader9* colourVs=nullptr;d->GetVertexShader(&colourVs);Need(colourVs==depthVs,"Dyson depth/colour transforms identical");depthVs->Release();colourVs->Release();
 d->GetPixelShaderConstantF(96,style,1);Need(style[0]==2 && style[1]==1,"independent Dyson strength default");
 float texel[4];d->GetPixelShaderConstantF(102,texel,1);Need(texel[0]==1 && texel[1]==1,"actual texture dimensions uploaded");pipe->ExSurfaceEnd();
 e->SurfaceDistanceTier=2;Need(pipe->ExSurfaceBegin(),"far Dyson retains stable material with shader footprint fade");pipe->ExSurfaceEnd();e->SurfaceDistanceTier=0;
 rs(D3DRS_ALPHABLENDENABLE,1);rs(D3DRS_SRCBLEND,D3DBLEND_SRCALPHA);rs(D3DRS_DESTBLEND,D3DBLEND_INVSRCALPHA);
 Need(pipe->ExSurfaceBegin(),"authored alpha-blended Dyson fade supported");pipe->ExSurfaceEnd();
 rs(D3DRS_DESTBLEND,D3DBLEND_ONE);Need(!pipe->ExSurfaceBegin(),"additive energy keeps native path");rs(D3DRS_ALPHABLENDENABLE,0);
 e->bDysonShader=false;Need(!pipe->ExSurfaceBegin(),"dyson_shader off restores native");e->bDysonShader=true;
 e->DysonRelief=2;e->bNomadShader=false;
 auto* savedLayers=e->NomadLayers;e->NomadLayers=nullptr;
 Need(pipe->ExSurfaceBegin(),"Dyson independent of organic shader and atlas");d->GetPixelShaderConstantF(96,style,1);Need(style[1]==2,"Dyson maximum strength forwarded");pipe->ExSurfaceEnd();
 e->NomadLayers=savedLayers;e->DysonRelief=1;e->bNomadShader=true;
 for(const char* name:{"dyson_surface_atlas","detailmap_dyson_skin01","asteroid_dyson01"})
  Need(NomadSurfaceProfile(name)==RPSurfaceDyson,"Dyson material family selects bump");
 Need(NomadSurfaceProfile("BEAST_DYSON_RECESS")==RPSurfaceBeast,"only explicit BEAST material selects medium bump");
 Need(!IsDysonSurfaceMaterial("beast_dyson_recess","dyson_surface_atlas.tga"),"BEAST private material survives shared Dyson texture policy");
 Need(IsDysonSurfaceMaterial("sphere_beast_gen1","DYSON_skin02.tga"),"texture alias selects Dyson bump");
 Need(IsDysonSurfaceMaterial("dom_kavash_gen_skin","dyson_skin04.tga_marbleless"),"Dyson texture suffix included");
 Need(IsDysonSurfaceMaterial("alias","folder/Dyson_skin01.tga"),"texture path recognized");
 for(const char* alias:{"vdyson1","vdyson2","vdyson3","folder/VDYSON1"})
  Need(IsDysonSurfaceMaterial("virt_tlr_root2",alias),"ANM virtual Dyson texture alias included");
 for(const char* excluded:{"nomad_land_v2","nomad_land_v2_1","the_nomad_lang_radiantx","alien_lv"})
  Need(!IsDysonSurfaceMaterial("the_land",excluded),"experimental nomad land remains outside Dyson");
 // Actual ANM BtDetailMapMaterial binding tables: two UV sets, MODULATE2X detail.
 Check(pipe->SetSurfaceShader(RPSurfaceDyson,0,-1));pipe->StreamCache_.Fvf=D3DFVF_XYZ|D3DFVF_NORMAL|D3DFVF_TEX2;
 tss(1,D3DTSS_COLOROP,D3DTOP_MODULATE2X);tss(1,D3DTSS_TEXCOORDINDEX,1);tss(1,D3DTSS_TEXTURETRANSFORMFLAGS,D3DTTFF_DISABLE);
 Need(pipe->ExSurfaceBegin(),"ANM BtDetailMapMaterial with two UV sets routes to Dyson bump");
 d->GetPixelShaderConstantF(97,detail,1);Need(detail[0]==5 && detail[1]==1 && detail[3]==1,"ANM authored marble detail and UV set preserved");pipe->ExSurfaceEnd();
 tss(1,D3DTSS_COLOROP,D3DTOP_DISABLE);tss(1,D3DTSS_TEXCOORDINDEX,0);pipe->StreamCache_.Fvf=D3DFVF_XYZ|D3DFVF_NORMAL|D3DFVF_TEX1;
 Need(!IsDysonSurfaceMaterial("detailmap_lair_skin01","lair_skin01.tga"),"Lair not reclassified");
 e->bShadowReceiver=true;e->ShadowReadyMask=3;
 Check(pipe->SetSurfaceShader(RPSurfaceBeast,0,-1));Need(pipe->ExSurfaceBegin(),"BEAST opaque atlas routes");
 IDirect3DPixelShader9* beastPs=nullptr;d->GetPixelShader(&beastPs);Need(beastPs==e->NomadPs[5],"dedicated BEAST shader variant");beastPs->Release();
 d->GetPixelShaderConstantF(96,style,1);Need(style[0]==1 && style[1]==1,"BEAST static style and configured strength");pipe->ExSurfaceEnd();e->bShadowReceiver=false;e->ShadowReadyMask=0;
 const char* originalNames[]={"detailmap_lair_rockdtl01","detailmap_lair_rockdtl02","detailmap_lair_rockdtl03","detailmap_lair_rockdtl04","detailmap_lair_skin02"};
 for(unsigned i=0;i<5;++i){unsigned profile=NomadSurfaceProfile(originalNames[i]);
  Need(profile==(i==4?RPSurfaceNomadInterior:RPSurfaceNomadLair),"restored material identity");
  Check(pipe->SetSurfaceShader(profile,0,-1));Need(pipe->ExSurfaceBegin(),"original lair material route");
  IDirect3DBaseTexture9* atlas=nullptr;d->GetTexture(13,&atlas);
  Need(atlas==e->NomadLayers,"original layered atlas bound instead of bone mask");atlas->Release();pipe->ExSurfaceEnd();}
 e->bNomadShader=false;Need(!pipe->ExSurfaceBegin(),"feature off restores native");e->bNomadShader=true;Check(pipe->SetSurfaceShader(RPSurfaceAuto,0,-1));Need(!pipe->ExSurfaceBegin(),"scope reset");
 e->ShadowReadyMask=7;e->bShadowReceiver=true;e->bShadowFrameValid=true;e->bShadowStaticPrepared=true;e->ShadowPlanetCount=2;
 Need(pipe->BeginLocalShadowFrame(nullptr,nullptr,nullptr)<0,"nebula shadow-off aborts frame construction");
 Need(!e->ShadowReadyMask && !e->bShadowReceiver && !e->bShadowFrameValid && !e->bShadowStaticPrepared && !e->ShadowPlanetCount,"nebula shadow-off clears all previous-frame shadow inputs");
 puts("PASS nebula shadow-off clears stale maps/receivers before returning without map work");
 pipe->ExReleaseAllGpu();Need(!e->NomadLayers && !e->NomadVs && !e->NomadDepthPs && !e->bNomadTextureTried,"release reset");pipe->Device_=nullptr;pipe->DeviceReady_=0;delete pipe;for(int s:{0,1,13})d->SetTexture(s,nullptr);texture.Texture->Release();d->Release();api->Release();DestroyWindow(w);puts("PASS production routing, illumination, detail UV transform, depth VS, fade, feature-off, scope and device reset");
}
