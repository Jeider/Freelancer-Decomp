#include "RP9Ex.h"
#include "dacom_iids.h"
#include "RP9LightCompatibility.h"
#include <d3dx9.h>
#include <cstdio>
#include <cstdlib>
#include <algorithm>
#include <vector>
static void R(bool ok,const char* m){if(!ok){printf("FAIL: %s\n",m);exit(3);}}
static void C(HRESULT h){if(FAILED(h)){printf("HRESULT %08lx\n",h);exit(2);}}
struct Handle{IDirect3DTexture9* Texture=nullptr;unsigned long Extra=0;};
int main(){
 setvbuf(stdout,nullptr,_IONBF,0);SetErrorMode(SEM_FAILCRITICALERRORS|SEM_NOGPFAULTERRORBOX|SEM_NOOPENFILEERRORBOX);
 HWND w=CreateWindowA("STATIC","room fixture",WS_POPUP,0,0,64,64,0,0,GetModuleHandle(0),0);
 auto*a=Direct3DCreate9(D3D_SDK_VERSION);IDirect3DDevice9*d=nullptr;
 D3DPRESENT_PARAMETERS pp={};pp.Windowed=1;pp.SwapEffect=D3DSWAPEFFECT_DISCARD;pp.BackBufferWidth=pp.BackBufferHeight=64;pp.BackBufferFormat=D3DFMT_A8R8G8B8;
 C(a->CreateDevice(0,D3DDEVTYPE_HAL,w,D3DCREATE_HARDWARE_VERTEXPROCESSING,&pp,&d));
 auto*p=new FDirectX9();p->Outer_=&p->Inner_;p->Device_=d;p->DeviceReady_=1;auto*e=p->Ex_;
 e->bSurfaceConfigRead=true;e->bSurfaceEnabled=false;e->bRoomRead=true;
 D3DXMATRIX id;D3DXMatrixIdentity(&id);
 memcpy(p->Transforms_.World.Values,&id,64);memcpy(p->Transforms_.View.Values,&id,64);memcpy(p->Transforms_.Projection.Values,&id,64);
 d->SetTransform(D3DTS_WORLD,&id);d->SetTransform(D3DTS_VIEW,&id);d->SetTransform(D3DTS_PROJECTION,&id);
 for(int i=0;i<8;++i)memcpy(p->DeviceStates_.TextureTransforms[i].Values,&id,64);
 auto rs=[&](unsigned s,unsigned v){p->RenderStates_.MarkDirty(s,v);C(d->SetRenderState((D3DRENDERSTATETYPE)s,v));};
 auto tss=[&](unsigned s,unsigned t,unsigned v){auto&x=p->DeviceStates_.TextureStates[s][t];x.Value=v;x.bValid=1;C(d->SetTextureStageState(s,(D3DTEXTURESTAGESTATETYPE)t,v));};
 rs(D3DRS_LIGHTING,1);rs(D3DRS_ALPHABLENDENABLE,0);rs(D3DRS_AMBIENT,0xff202020);rs(D3DRS_CULLMODE,D3DCULL_NONE);rs(D3DRS_ZENABLE,0);
 rs(D3DRS_COLORVERTEX,0);rs(D3DRS_FOGENABLE,0);rs(D3DRS_SPECULARENABLE,0);
 for(unsigned s=0;s<2;++s){tss(s,D3DTSS_COLOROP,s ? D3DTOP_DISABLE:D3DTOP_MODULATE);tss(s,D3DTSS_COLORARG1,D3DTA_TEXTURE);tss(s,D3DTSS_COLORARG2,s?D3DTA_CURRENT:D3DTA_DIFFUSE);
  tss(s,D3DTSS_ALPHAOP,D3DTOP_MODULATE);tss(s,D3DTSS_ALPHAARG1,D3DTA_TEXTURE);tss(s,D3DTSS_ALPHAARG2,D3DTA_CURRENT);tss(s,D3DTSS_TEXCOORDINDEX,s);tss(s,D3DTSS_TEXTURETRANSFORMFLAGS,0);}
 tss(2,D3DTSS_COLOROP,D3DTOP_DISABLE);
 D3DMATERIAL9 mat={};mat.Diffuse={.8f,.7f,.6f,.7f};mat.Ambient={.7f,.6f,.5f,1};mat.Emissive={.02f,.01f,.03f,0};C(p->SetMaterial(&mat));
 auto texture=[&](Handle&h,DWORD color){C(d->CreateTexture(4,4,1,0,D3DFMT_A8R8G8B8,D3DPOOL_MANAGED,&h.Texture,0));D3DLOCKED_RECT l;C(h.Texture->LockRect(0,&l,0,0));
  for(int y=0;y<4;++y)for(int x=0;x<4;++x)((DWORD*)((char*)l.pBits+y*l.Pitch))[x]=color;h.Texture->UnlockRect(0);};
 Handle base,detail,finish;texture(base,0xbfa0c080);texture(detail,0xff806040);texture(finish,0xff8080c0);
 p->DeviceStates_.TextureBindings[0]={&base,1,{}};p->DeviceStates_.TextureBindings[1]={&detail,1,{}};C(d->SetTexture(0,base.Texture));C(d->SetTexture(1,detail.Texture));
 D3DLIGHT9 light={};light.Type=D3DLIGHT_DIRECTIONAL;light.Direction={.6f,0,.8f};light.Diffuse={.6f,.5f,.4f,1};
 C(p->SetLight(nullptr,&light));C(p->SetLightEnable(nullptr,1));p->LightManager_.Flush(d);
 auto&profile=e->RoomProfiles["fixture|base"];profile.Texture=finish.Texture;profile.Texture->AddRef();profile.Tried=true;profile.Normal=0;profile.Specular=0;
 profile.Skin=-1; // explicit environment scope; characters must not inherit it
 C(p->SetRoomMaterialFrame(1));C(p->SetRoomMaterial("fixture","base"));
 struct V{float x,y,z,nx,ny,nz,u,v,u1,v1;};V q[]={{-.7f,-.7f,.5,0,0,-1,0,1,1,0},{-.7f,.7f,.5,0,0,-1,0,0,1,1},{.7f,-.7f,.5,0,0,-1,1,1,0,0},{.7f,.7f,.5,0,0,-1,1,0,0,1}};
 unsigned fvf=D3DFVF_XYZ|D3DFVF_NORMAL|D3DFVF_TEX2;p->StreamCache_.Fvf=fvf;C(d->SetFVF(fvf));
 IDirect3DSurface9*target=nullptr,*read=nullptr;C(d->GetRenderTarget(0,&target));C(d->CreateOffscreenPlainSurface(64,64,D3DFMT_A8R8G8B8,D3DPOOL_SYSTEMMEM,&read,0));
 auto render=[&](bool room,const void*vertices,unsigned stride){C(d->Clear(0,0,D3DCLEAR_TARGET,0xff000000,1,0));C(d->BeginScene());
  if(room)R(p->ExSurfaceBegin(),"room route active");else {p->ExSurfaceRelease();}
  C(d->DrawPrimitiveUP(D3DPT_TRIANGLESTRIP,2,vertices,stride));if(room)p->ExSurfaceEnd();C(d->EndScene());C(d->GetRenderTargetData(target,read));
  D3DLOCKED_RECT l;C(read->LockRect(&l,0,D3DLOCK_READONLY));std::vector<DWORD>out;for(int y=0;y<64;++y)for(int x=0;x<64;++x)out.push_back(((DWORD*)((char*)l.pBits+y*l.Pitch))[x]);read->UnlockRect();return out;};
 auto delta=[&](std::vector<DWORD>const&a,std::vector<DWORD>const&b){unsigned max=0;for(size_t i=0;i<a.size();++i)for(int j=0;j<4;++j)max=(std::max)(max,(unsigned)abs(int((a[i]>>(j*8))&255)-int((b[i]>>(j*8))&255)));return max;};
 auto native=render(false,q,sizeof(V)),modern=render(true,q,sizeof(V));unsigned diff=delta(native,modern);printf("Single-stage baseline delta %u; native %08lx room %08lx\n",diff,native[2080],modern[2080]);R(diff<=2,"native diffuse/emission/alpha baseline");
 // Exercise both real RP9 light submission paths and read back the D3D state.
 // Sources must stay authored; repeated updates must never narrow the cone again.
 D3DLIGHT9 spot={};spot.Type=D3DLIGHT_SPOT;spot.Position={0,0,-.5f};spot.Direction={0,0,1};
 spot.Diffuse={.6f,.5f,.4f,1};spot.Range=100;spot.Attenuation0=1;spot.Falloff=1;spot.Theta=.7f;spot.Phi=1.2f;
 auto sameLight=[&](D3DLIGHT9 const&a,D3DLIGHT9 const&b){return memcmp(&a,&b,sizeof(a))==0;};
 for(unsigned kind=0;kind<5;++kind){
  D3DLIGHT9 source=spot;
  if(kind==1){source.Theta=source.Phi=.8f;source.Falloff=2;}
  if(kind==2){source.Phi=.8f;source.Theta=std::nextafter(source.Phi,0.0f);source.Falloff=2;
   R(source.Theta!=source.Phi && std::cos(source.Theta*.5f)==std::cos(source.Phi*.5f),"distinct angles can round to equal cosine");}
  if(kind==3)source.Type=D3DLIGHT_POINT;
  if(kind==4)source=light;
  const D3DLIGHT9 original=source,expected=Rp9CompatibleLight(original);
  if(kind==0)R(expected.Theta==source.Theta/1.75f && expected.Falloff==1,"soft cone compatibility");
  if(kind==1 || kind==2)R(expected.Theta==0 && expected.Falloff==1e-6f,"equal-cosine hard cone compatibility");
  if(kind>=3)R(sameLight(expected,original),"point/directional lighting unchanged");
  for(unsigned repeat=0;repeat<3;++repeat){
   C(p->SetLight(nullptr,&source));D3DLIGHT9 gpu={},collected[8]={};
   C(d->GetLight(p->LightManager_.FindOrCreate(0,nullptr),&gpu));
   R(sameLight(gpu,expected),"direct native spotlight correction");
   R(p->ExCollectSurfaceLights(collected,8)==1 && sameLight(collected[0],gpu),"direct shader and native light match");
   R(sameLight(source,original) && sameLight(e->SurfaceDirectLights[0],original),"direct source is never modified");
  }
  C(p->SetLightEnable(nullptr,0));C(p->LightManager_.Flush(d));
  C(p->AddLight(&source));C(p->SetLightEnable(&source,1));
  for(unsigned repeat=0;repeat<3;++repeat){
   C(p->UpdateLight(&source));C(p->LightManager_.Flush(d));D3DLIGHT9 gpu={},collected[8]={};
   C(d->GetLight(p->LightManager_.FindOrCreate((unsigned long)&source,nullptr),&gpu));
   R(sameLight(gpu,expected),"queued native spotlight correction");
   R(p->ExCollectSurfaceLights(collected,8)==1 && sameLight(collected[0],gpu),"queued shader and native light match");
   R(sameLight(source,original),"borrowed engine light is never modified");
  }
  C(p->RemoveLight(&source));C(p->SetLightEnable(nullptr,1));C(p->LightManager_.Flush(d));
 }
 // Small patches avoid the unrelated vertex-vs-pixel lighting interpolation
 // difference. Sample core, penumbra, and outside the authored cone on the GPU.
 V savedQ[4];memcpy(savedQ,q,sizeof(q));
 for(unsigned hard=0;hard<2;++hard){
  D3DLIGHT9 source=spot;if(hard){source.Theta=source.Phi=.8f;source.Falloff=2;}
  C(p->SetLight(nullptr,&source));unsigned lit[4]={},nativeLit[4]={};
  const int columns[]={32,44,50,60};
  for(unsigned sample=0;sample<4;++sample){
   const float x=(columns[sample]+.5f)/32-1,y=.5f/32,half=.016f;
   for(unsigned i=0;i<4;++i){q[i]=savedQ[i];q[i].x=x+((i&2)?half:-half);q[i].y=y+((i&1)?half:-half);}
   auto ffp=render(false,q,sizeof(V)),shader=render(true,q,sizeof(V));
   unsigned difference=delta(ffp,shader);printf("Spot hard %u sample %u native/shader delta %u\n",hard,sample,difference);
   // Modern FFP can overshoot 1 inside a soft inner cone; d3d8to9's
   // correction reduces this, but does not remove it. Material shaders clamp.
   // Hard cones (the singularity fix) and the penumbra must still agree.
   if(hard || sample>0)R(difference<=3,"spotlight native/material GPU response agrees outside soft inner core");
   for(DWORD pixel:shader)lit[sample]=(std::max)(lit[sample],unsigned((pixel>>16)&255));
   for(DWORD pixel:ffp)nativeLit[sample]=(std::max)(nativeLit[sample],unsigned((pixel>>16)&255));
  }
  R(lit[0]>lit[3]+20,"spotlight illuminates core but not outside cone");
  R(nativeLit[0]>nativeLit[3]+20 && nativeLit[0]<128,"native cone core is lit without full-bright overflow");
  if(hard)R(lit[1]>lit[2]+20 && abs(int(lit[2])-int(lit[3]))<=1,"hard cone retains edge without lighting outside");
  else R(lit[0]>lit[1] && lit[1]>lit[2] && lit[2]>lit[3],"soft spotlight retains smooth falloff");
 }
 memcpy(q,savedQ,sizeof(q));C(p->SetLight(nullptr,&light));
 puts("PASS: spotlight compatibility, source preservation, repeated updates, both submission paths and GPU cones");
 tss(1,D3DTSS_COLOROP,D3DTOP_MODULATE2X);native=render(false,q,sizeof(V));modern=render(true,q,sizeof(V));diff=delta(native,modern);printf("Two-stage baseline delta %u\n",diff);R(diff<=2,"native detail layer and alpha retained");
 D3DLOCKED_RECT grad;C(detail.Texture->LockRect(0,&grad,0,0));
 for(int y=0;y<4;++y)for(int x=0;x<4;++x)((DWORD*)((char*)grad.pBits+y*grad.Pitch))[x]=0xff000000|((40+x*40)<<16)|((40+y*40)<<8)|100;detail.Texture->UnlockRect(0);
 D3DXMATRIX uv=id;uv._11=1.7f;uv._22=.7f;uv._31=.23f;uv._32=.13f;
 memcpy(p->DeviceStates_.TextureTransforms[1].Values,&uv,64);C(d->SetTransform(D3DTS_TEXTURE1,&uv));tss(1,D3DTSS_TEXTURETRANSFORMFLAGS,D3DTTFF_COUNT2);
 native=render(false,q,sizeof(V));modern=render(true,q,sizeof(V));diff=delta(native,modern);printf("Authored UV transform delta %u\n",diff);R(diff<=2,"detail tiling/eye-style texture translation retained");
 memcpy(p->DeviceStates_.TextureTransforms[1].Values,&id,64);C(d->SetTransform(D3DTS_TEXTURE1,&id));tss(1,D3DTSS_TEXTURETRANSFORMFLAGS,0);
 C(detail.Texture->LockRect(0,&grad,0,0));for(int y=0;y<4;++y)for(int x=0;x<4;++x)((DWORD*)((char*)grad.pBits+y*grad.Pitch))[x]=0xff806040;detail.Texture->UnlockRect(0);modern=render(true,q,sizeof(V));
 profile.Normal=.7f;D3DLOCKED_RECT l;C(finish.Texture->LockRect(0,&l,0,0));for(int y=0;y<4;++y)for(int x=0;x<4;++x)((DWORD*)((char*)l.pBits+y*l.Pitch))[x]=0xffc080c0;finish.Texture->UnlockRect(0);
 auto bumped=render(true,q,sizeof(V));unsigned normalDelta=delta(bumped,modern);R(normalDelta>3,"normal map changes response to authored light");profile.Normal=0;profile.Specular=.8f;unsigned highlightDelta=delta(render(true,q,sizeof(V)),modern);R(highlightDelta>0,"material highlight responds to light");printf("Material response: normal delta %u, highlight delta %u\n",normalDelta,highlightDelta);profile.Specular=0;
 // Clothing gets its own maximum finish; eyes/legacy scope remains separate.
 profile.Skin=0;profile.Normal=.1f;
 auto mildCloth=render(true,q,sizeof(V));profile.Skin=-.25f;
 auto maxCloth=render(true,q,sizeof(V));
 profile.Skin=-1;auto maxInterior=render(true,q,sizeof(V));profile.Skin=-.25f;
 R(delta(mildCloth,maxCloth)<=1 && delta(mildCloth,maxInterior)>2,
   "clothing relief reduced to x3 while interior stays x12");
 profile.Normal=0;profile.Specular=.8f;profile.Skin=0;
 auto mildHighlight=render(true,q,sizeof(V));profile.Skin=-.25f;
 auto maxHighlight=render(true,q,sizeof(V));
 R((maxHighlight[2080]&255)>(mildHighlight[2080]&255),"maximum clothing increases highlights");
 profile.Skin=-1;profile.Specular=0;
 // Existing indexed palette: four weights, identity transforms then translated bone 1.
 struct SV{float x,y,z,w0,w1,w2;DWORD bones;float nx,ny,nz,u,v,u1,v1;};SV sq[4];
 for(int i=0;i<4;++i){auto&v=q[i];sq[i]={v.x,v.y,v.z,1,0,0,0x01010101,v.nx,v.ny,v.nz,v.u,v.v,v.u1,v.v1};}
 memcpy(e->RoomBones[1],&id,64);e->RoomBones[1][12]=.2f;
 fvf=D3DFVF_XYZB4|D3DFVF_LASTBETA_UBYTE4|D3DFVF_NORMAL|D3DFVF_TEX2;p->StreamCache_.Fvf=fvf;C(d->SetFVF(fvf));
 rs(D3DRS_INDEXEDVERTEXBLENDENABLE,1);rs(D3DRS_VERTEXBLEND,D3DVBF_3WEIGHTS);
 auto skinned=render(true,sq,sizeof(SV));R(skinned[32*64+57]!=0xff000000 && skinned[32*64+10]==0xff000000,"skinned palette translation preserved");
 rs(D3DRS_INDEXEDVERTEXBLENDENABLE,0);rs(D3DRS_VERTEXBLEND,D3DVBF_DISABLE);p->StreamCache_.Fvf=D3DFVF_XYZ|D3DFVF_NORMAL|D3DFVF_TEX2;C(d->SetFVF(p->StreamCache_.Fvf));
 profile.Skin=1;profile.Normal=1;profile.Specular=1;
 R(!p->ExRoomMaterialBegin(),"skin keeps native lighting even with strong material parameters");
 profile.Skin=-1;profile.Normal=0;profile.Specular=0;
 rs(D3DRS_ALPHABLENDENABLE,1);R(!p->ExSurfaceBegin(),"transparent authored pass excluded");rs(D3DRS_ALPHABLENDENABLE,0);
 tss(1,D3DTSS_TEXCOORDINDEX,D3DTSS_TCI_CAMERASPACEREFLECTIONVECTOR);R(!p->ExSurfaceBegin(),"authored envmap excluded");tss(1,D3DTSS_TEXCOORDINDEX,1);
 C(p->SetRoomMaterial("missing","base"));R(!p->ExSurfaceBegin(),"unprofiled material native");
 C(p->SetRoomMaterialFrame(0));R(!p->ExSurfaceBegin(),"room route absent in flight");
 // Actual INTZ depth, flat plane then a nearby occluder. AO must preserve flat
 // surfaces, darken only contact, keep alpha, and restore depth/blend state.
 C(p->SetRoomMaterialFrame(1));
 IDirect3DTexture9*depthTex=nullptr;C(d->CreateTexture(64,64,1,D3DUSAGE_DEPTHSTENCIL,(D3DFORMAT)MAKEFOURCC('I','N','T','Z'),D3DPOOL_DEFAULT,&depthTex,0));
 e->SceneDepth.Texture=depthTex;C(depthTex->GetSurfaceLevel(0,&e->SceneDepth.Surface));C(d->SetDepthStencilSurface(e->SceneDepth.Surface));
 auto contact=[&](bool obstacle,bool character=false){
  p->ExSurfaceRelease();C(d->SetFVF(D3DFVF_XYZRHW|D3DFVF_DIFFUSE));rs(D3DRS_LIGHTING,0);rs(D3DRS_ZENABLE,1);rs(D3DRS_ZWRITEENABLE,1);rs(D3DRS_ZFUNC,D3DCMP_LESSEQUAL);
  rs(D3DRS_ALPHABLENDENABLE,0);rs(D3DRS_ALPHATESTENABLE,0);rs(D3DRS_COLORWRITEENABLE,15);
  tss(0,D3DTSS_COLOROP,D3DTOP_SELECTARG1);tss(0,D3DTSS_COLORARG1,D3DTA_DIFFUSE);tss(0,D3DTSS_ALPHAOP,D3DTOP_SELECTARG1);tss(0,D3DTSS_ALPHAARG1,D3DTA_DIFFUSE);tss(1,D3DTSS_COLOROP,D3DTOP_DISABLE);
  struct QV{float x,y,z,w;DWORD c;};
  auto draw=[&](float right,float z){QV q[]={{-.5f,-.5f,z,1,0x80c0c0c0},{right,-.5f,z,1,0x80c0c0c0},{-.5f,63.5f,z,1,0x80c0c0c0},{right,63.5f,z,1,0x80c0c0c0}};C(d->DrawPrimitiveUP(D3DPT_TRIANGLESTRIP,2,q,sizeof(QV)));};
  C(d->Clear(0,0,D3DCLEAR_TARGET|D3DCLEAR_ZBUFFER,0,1,0));C(d->BeginScene());draw(63.5f,.6f);if(obstacle)draw(29.5f,.5f);
  C(p->ApplyRoomContactShadows());
  if(character){QV face[]={{31.5f,23.5f,.4f,1,0x80c0c0c0},{39.5f,23.5f,.4f,1,0x80c0c0c0},{31.5f,39.5f,.4f,1,0x80c0c0c0},{39.5f,39.5f,.4f,1,0x80c0c0c0}};
   C(d->DrawPrimitiveUP(D3DPT_TRIANGLESTRIP,2,face,sizeof(QV)));}
  C(d->EndScene());
  DWORD blend=99;C(d->GetRenderState(D3DRS_ALPHABLENDENABLE,&blend));R(blend==0,"contact pass restores blend state");
  IDirect3DSurface9*bound=nullptr;C(d->GetDepthStencilSurface(&bound));R(bound==e->SceneDepth.Surface,"contact pass restores depth surface");bound->Release();
  C(d->GetRenderTargetData(target,read));D3DLOCKED_RECT l;C(read->LockRect(&l,0,D3DLOCK_READONLY));std::vector<DWORD>out;
  for(int y=0;y<64;++y)for(int x=0;x<64;++x)out.push_back(((DWORD*)((char*)l.pBits+y*l.Pitch))[x]);read->UnlockRect();return out;
 };
 auto flat=contact(false),occluded=contact(true);R((flat[2080]&255)==192,"AO leaves flat plane unchanged");
 unsigned contactPixel=occluded[32*64+32]&255,distantPixel=occluded[32*64+60]&255;printf("Contact pixels: flat 192, contact %u, far %u\n",contactPixel,distantPixel);
 R(contactPixel<190 && distantPixel==192,"AO darkens contact only");R((occluded[2080]>>24)==128,"AO preserves alpha");
 for(DWORD pixel:occluded)R((pixel&255)>=130,"default contact AO cannot produce black patches");
 auto withCharacter=contact(true,true);R(withCharacter[2080]==0x80c0c0c0,"character drawn after AO retains its native colour and alpha");
 // A top-down silhouette lands on scene geometry below the caster, not on
 // geometry above it. Use actual INTZ depth and the production begin/draw/end.
 auto silhouette=[&](bool skin,bool above,bool transparent,bool modelview=false,bool character=false){
  contact(false); // opaque receiver at camera depth .6, RGB192 alpha128
  D3DXMATRIX camera;ZeroMemory(&camera,sizeof(camera));camera._11=1;camera._32=1;camera._23=-1;camera._43=above?.8f:.5f;camera._44=1;
  memcpy(p->Transforms_.View.Values,&camera,64);memcpy(p->Transforms_.World.Values,&id,64);
  rs(D3DRS_ALPHABLENDENABLE,0);rs(D3DRS_ALPHATESTENABLE,0);
  FRp9TransformCache packed;memcpy(packed.Values,&camera,64);float view12[12];packed.LoadAffine(view12);
  for(unsigned i=6;i<9;++i)view12[i]=-view12[i];view12[11]=-view12[11];
  C(d->BeginScene());float center[]={0,.1f,0};R(p->BeginRoomShadow(view12,center,.5f,character?1:0)>=0,"room silhouette opens on valid room depth");
  V caster[]={{-.3f,.1f,-.3f,0,1,0,0,0,0,0},{-.3f,.1f,.3f,0,1,0,0,0,0,0},
              {.3f,.1f,-.3f,0,1,0,0,0,0,0},{.3f,.1f,.3f,0,1,0,0,0,0,0}};
  rs(D3DRS_ALPHABLENDENABLE,transparent?1:0);
  rs(D3DRS_INDEXEDVERTEXBLENDENABLE,skin?1:0);rs(D3DRS_VERTEXBLEND,skin?D3DVBF_3WEIGHTS:D3DVBF_DISABLE);
  p->StreamCache_.Fvf=(skin ? D3DFVF_XYZB4|D3DFVF_LASTBETA_UBYTE4:D3DFVF_XYZ)|D3DFVF_NORMAL|D3DFVF_TEX2;C(d->SetFVF(p->StreamCache_.Fvf));
  memcpy(e->RoomBones[1],&id,64);e->RoomBones[1][12]=.15f;
  if(modelview){memcpy(p->Transforms_.World.Values,&camera,64);memcpy(p->Transforms_.View.Values,&id,64);
   D3DXMATRIX bone;memcpy(&bone,e->RoomBones[1],64);bone*=camera;memcpy(e->RoomBones[1],&bone,64);}
  bool draws=p->ExShadowDrawBegin();R(draws!=transparent,"opaque silhouette excludes transparent effects");
  if(draws){
   if(skin){SV v[4];for(int i=0;i<4;++i){auto&q=caster[i];v[i]={q.x,q.y,q.z,1,0,0,0x01010101,q.nx,q.ny,q.nz,0,0,0,0};}C(d->DrawPrimitiveUP(D3DPT_TRIANGLESTRIP,2,v,sizeof(SV)));}
   else C(d->DrawPrimitiveUP(D3DPT_TRIANGLESTRIP,2,caster,sizeof(V)));
  }
  GENRESULT ended=p->EndRoomShadow();R((ended>=0)!=transparent,"empty silhouette retains native fallback");C(d->EndScene());
  R(!e->bShadowDrawing && !e->bRoomShadowDrawing,"room shadow scope closed");
  D3DVIEWPORT9 vp;C(d->GetViewport(&vp));R(vp.Width==64 && vp.Height==64,"shadow viewport restored");
  IDirect3DSurface9*ds=nullptr;C(d->GetDepthStencilSurface(&ds));R(ds==e->SceneDepth.Surface,"silhouette depth restored");ds->Release();
  C(d->GetRenderTargetData(target,read));D3DLOCKED_RECT l;C(read->LockRect(&l,0,D3DLOCK_READONLY));
  DWORD middle=((DWORD*)((char*)l.pBits+32*l.Pitch))[32],outside=((DWORD*)((char*)l.pBits+32*l.Pitch))[55];
  DWORD extended=((DWORD*)((char*)l.pBits+32*l.Pitch))[43];read->UnlockRect();
  if(!skin && !above && !transparent)R(character ? (extended&255)<150:(extended&255)==192,
      "character silhouette extends with height; ship silhouette stays vertical");
  printf("Silhouette skin %u above %u transparent %u: center %lu, outside %lu\n",skin,above,transparent,middle&255,outside&255);
  R((middle>>24)==128 && (outside&255)==192,"silhouette preserves alpha and unaffected floor");
  R((above || transparent) ? (middle&255)==192:(middle&255)<150,"only geometry below opaque silhouette is shadowed");
  memcpy(p->Transforms_.View.Values,&id,64);memcpy(p->Transforms_.World.Values,&id,64);
 };
 silhouette(false,false,false);silhouette(true,false,false);silhouette(false,true,false);silhouette(false,false,true);
 silhouette(false,false,false,true);silhouette(true,false,false,true);
 silhouette(false,false,false,false,true);silhouette(false,false,false,true,true);
 C(p->SetRoomMaterialFrame(0));float center[]={0,0,0},view12[12]={};R(p->BeginRoomShadow(view12,center,1)<0,"room silhouettes unavailable in flight");
 p->ExReleaseAllGpu();p->Device_=nullptr;p->DeviceReady_=0;delete p;
 read->Release();target->Release();base.Texture->Release();detail.Texture->Release();finish.Texture->Release();d->Release();a->Release();DestroyWindow(w);
 puts("PASS: native layered baseline, normals/highlights, indexed skinning, fallbacks and room isolation");
}
