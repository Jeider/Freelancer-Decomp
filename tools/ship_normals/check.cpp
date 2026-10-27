// Production shader GPU regression: strength, tangent handedness, distance and native fallback.
#include "RP9ShaderCache.h"
#include "render/IRPShipNormals.h"
#include <algorithm>
#include <cstdio>
#include <cstdlib>
#include <cmath>
static void Require(bool b,const char*m){if(!b){printf("FAIL: %s\n",m);exit(3);}}
static void Check(HRESULT h){if(FAILED(h)){printf("HRESULT %08lx\n",h);exit(2);}}
static std::string Read(const char*p){FILE*f=fopen(p,"rb");Require(f!=nullptr,p);std::string s;char b[4096];size_t n;
 while((n=fread(b,1,sizeof(b),f)))s.append(b,n);fclose(f);return s;}
static std::vector<unsigned char> Compile(std::string s,const char*entry,const char*profile){
 std::vector<unsigned char> c;std::string e;bool hit=false,stored=false;
 HRESULT h=Rp9ShaderCache::Compile(s,nullptr,entry,profile,0,&c,&e,&hit,&stored);if(FAILED(h))puts(e.c_str());Check(h);return c;}
struct Vertex{float x,y,z,nx,ny,nz,u,v;};
int main(int argc,char**argv){
 if(argc==2) { printf("%d\n",ShipNormalEligible(0x100,false,argv[1])?1:0);return 0; }
 setvbuf(stdout,nullptr,_IONBF,0);SetErrorMode(SEM_FAILCRITICALERRORS|SEM_NOGPFAULTERRORBOX);
 Require(ShipNormalEligible(0x10000,true),"player fighter receives normals");
 Require(ShipNormalEligible(0x200000,false),"CAPITAL receives normals");
 Require(ShipNormalEligible(0x80000,false),"NPC CRUISER receives normals");
 for(unsigned type:{0x10000u,0x20000u,0u})
  Require(!ShipNormalEligible(type,false),"ordinary NPCs and other objects stay native");
 for(unsigned type:{0x100u,0x10u,0x8000u})
 {
  for(const char*model:{"ships/liberty/li_dreadnought/li_dreadnought.cmp",
      "SHIPS\\BRETONIA\\BR_BATTLESHIP\\BR_BATTLESHIP.CMP",
      "ships/kusari/ku_battleship/ku_battleship.cmp",
      "ships/rheinland/rh_pir_battleship/rh_pir_battleship.cmp",
      "ships/order/or_osiris/or_osiris.cmp",
      "ships/bretonia/br_jack_battleship/br_jack_battleship.cmp"})
   Require(ShipNormalEligible(type,false,model),"solar battleship model receives normals");
  for(const char*model:{
      "ships/utility/luxury_liner/luxury_liner.cmp","ships/bretonia/br_gunship/br_gunship.cmp",
      "ships/liberty/li_nmd_dreadnought/li_nmd_dreadnought.cmp",
      "ships/nomad/test_battleship/test_battleship.cmp","solar/dyson/test.cmp","solar/asteroids/rock.cmp"})
   Require(!ShipNormalEligible(type,false,model),"liners, gunboats, asteroids and NMD stay excluded");
 }
 Require(!ShipNormalEligible(0x100,false,nullptr),"missing solar model stays native");
 Require(!ShipNormalEligible(0x10000,false,"ships/liberty/li_dreadnought/li_dreadnought.cmp"),"ordinary NPC eligibility unchanged");
 for(unsigned type:{0x100u,0x10u,0x8000u,0x4000u,0x40u,0x20u})
 {
  const char* model="solar/dockable/depot_lod.cmp";
  Require(ShipNormalScope(type,false,model,true,199.9f)==200,"dockable surface inside 200m");
  Require(ShipNormalScope(type,false,model,true,200)==0,"dockable surface cutoff");
  Require(ShipNormalScope(type,false,model,false,99.9f)==100,"non-dockable surface inside 100m");
  Require(ShipNormalScope(type,false,model,false,100)==0,"non-dockable cutoff even with STATION type");
 }
 for(const char* model:{"solar/dockable/station_large_a_lod.cmp","solar/dockable/station_large_b_lod.cmp",
     "solar/dockable/station_small_a_lod.cmp","solar/dockable/station_small_b_lod.cmp",
     "solar/dockable/station_small_b_lod_tgk.cmp","SOLAR\\DOCKABLE\\TRADING_OUTPOST_LOD.CMP"})
 {
  Require(ShipNormalScope(0x100,false,model,true,499.9f)==500,"selected station range is 500m");
  Require(ShipNormalScope(0x100,false,model,true,500)==0,"selected station cutoff at 500m");
 }
 for(unsigned type:{0x80000u,0x40000u,0x100000u})
 {
  Require(ShipNormalScope(type,false,"ships/human.cmp",false,199)==200,"NPC cruiser/gunboat/transport near range");
  Require(ShipNormalScope(type,false,"ships/human.cmp",false,200)==0,"NPC cruiser/gunboat/transport distant fallback");
 }
 for(unsigned type:{0x200000u,0x100u,0x10u,0x8000u})
 {
  const char* model="ships/liberty/li_dreadnought/li_dreadnought.cmp";
  Require(ShipNormalScope(type,false,model,false,399)==400,"mobile and solar battleships inside 400m");
  Require(ShipNormalScope(type,false,model,true,400)==0,"battleship cutoff with or without dock");
 }
 for(const char* model:{"ships/utility/transport_small/transport_small.cmp",
     "SHIPS\\UTILITY\\TRANSPORT_ARMORED\\TRANSPORT_ARMORED_BETA1.CMP"})
 {
  Require(ShipNormalScope(0x10000,false,model,false,199)==200,"transport content type exception");
  Require(ShipNormalScope(0x20000,false,model,false,200)==0,"transport content type exception cutoff");
 }
 Require(ShipNormalScope(0x10000,true,"ships/player.cmp",false,10000)==1,"player retains previous range");
 Require(ShipNormalScope(0x8000,false,"ships/utility/mining/mining.cmp",false,99)==100,"Roid Miner mission satellite");
 Require(ShipNormalScope(0x100,false,"ships/utility/mining/mining_with_panels.cmp",true,199)==200,"Roid Miner with dock");
 Require(ShipNormalScope(0x20000000,false,"solar/asteroids/rock.cmp",false,0)==0,"asteroid always excluded");
 HWND w=CreateWindowA("STATIC","normal fixture",WS_POPUP,0,0,64,64,0,0,GetModuleHandle(0),0);
 auto*api=Direct3DCreate9(D3D_SDK_VERSION);Require(api!=nullptr,"D3D9");IDirect3DDevice9*d=nullptr;
 D3DPRESENT_PARAMETERS pp={};pp.Windowed=1;pp.SwapEffect=D3DSWAPEFFECT_DISCARD;
 pp.BackBufferWidth=pp.BackBufferHeight=64;pp.BackBufferFormat=D3DFMT_A8R8G8B8;
 Check(api->CreateDevice(0,D3DDEVTYPE_HAL,w,D3DCREATE_HARDWARE_VERTEXPROCESSING,&pp,&d));
 std::string src=Read("DATA_EXTRA/SHADERS/surface_material.hlsl");
 const std::string prefix="#define SURFACE_SHIP_NORMALS 1\n#define SURFACE_NO_SHADOW 1\n";
 auto v=Compile(src,"VSMain","vs_3_0");IDirect3DVertexShader9*vs=nullptr;Check(d->CreateVertexShader((DWORD*)v.data(),&vs));
 auto make=[&](std::string s,const char*entry){auto c=Compile(s,entry,"ps_3_0");IDirect3DPixelShader9*p=nullptr;
  Check(d->CreatePixelShader((DWORD*)c.data(),&p));return p;};
 auto*normal=make(prefix+src+"\nfloat4 PSCheck(SurfacePixel In):COLOR0{return float4(ShipReliefNormal(In,normalize(In.Normal))*.5+.5,1);}\n","PSCheck");
 auto*ship=make(prefix+src,"PSMain");auto*native=make("#define SURFACE_NO_SHADOW 1\n"+src,"PSMain");
 D3DXMATRIX id;D3DXMatrixIdentity(&id);float vc[68]={},pc[102*4]={};for(int i=0;i<4;++i)memcpy(vc+i*16,&id,64);
 Vertex q[]={{-1,-1,.5,0,0,-1,0,1},{-1,1,.5,0,0,-1,0,0},{1,-1,.5,0,0,-1,1,1},{1,1,.5,0,0,-1,1,0}};
 d->SetVertexShader(vs);d->SetFVF(D3DFVF_XYZ|D3DFVF_NORMAL|D3DFVF_TEX1);
 d->SetRenderState(D3DRS_ZENABLE,0);d->SetRenderState(D3DRS_CULLMODE,D3DCULL_NONE);
 IDirect3DTexture9*map=nullptr;Check(d->CreateTexture(1,1,1,0,D3DFMT_A8R8G8B8,D3DPOOL_MANAGED,&map,0));
 D3DLOCKED_RECT lock;Check(map->LockRect(0,&lock,0,0));*(DWORD*)lock.pBits=0xacff9900;Check(map->UnlockRect(0));
 // Packed XY=(+.35,+.20). UV's down direction is negative view Y.
 d->SetTexture(13,map);d->SetSamplerState(13,D3DSAMP_SRGBTEXTURE,0);
 pc[389]=2000;pc[390]=6000;pc[391]=2;
 IDirect3DSurface9*rt=nullptr,*read=nullptr;Check(d->GetRenderTarget(0,&rt));
 Check(d->CreateOffscreenPlainSurface(64,64,D3DFMT_A8R8G8B8,D3DPOOL_SYSTEMMEM,&read,0));
 auto render=[&](IDirect3DPixelShader9*p){Check(d->Clear(0,0,D3DCLEAR_TARGET,0,1,0));Check(d->BeginScene());
  Check(d->SetPixelShader(p));Check(d->SetVertexShaderConstantF(0,vc,17));Check(d->SetPixelShaderConstantF(0,pc,102));
  Check(d->DrawPrimitiveUP(D3DPT_TRIANGLESTRIP,2,q,sizeof(Vertex)));Check(d->EndScene());Check(d->GetRenderTargetData(rt,read));
  Check(read->LockRect(&lock,0,D3DLOCK_READONLY));DWORD c=((DWORD*)((char*)lock.pBits+32*lock.Pitch))[32];Check(read->UnlockRect());return c;};
 auto r=[](DWORD c){return int((c>>16)&255);};auto g=[](DWORD c){return int((c>>8)&255);};
 pc[388]=0;DWORD flat=render(normal);Require(abs(r(flat)-128)<=1&&abs(g(flat)-128)<=1&&(flat&255)==0,"zero strength = geometry normal");
 pc[388]=1;DWORD mild=render(normal);pc[388]=4;DWORD strong=render(normal);
 Require(r(mild)>150&&g(mild)<115,"DXT5nm orientation");Require(r(strong)>r(mild)+35,"maximum strength amplifies relief");
 for(float limit:{100.f,200.f,400.f,500.f})
 {
  pc[389]=limit*.8f;pc[390]=limit;vc[26]=.001f;
  vc[14]=limit*.7f;DWORD nearby=render(normal);
  vc[14]=limit*.9f;DWORD transition=render(normal);
  vc[14]=limit;Require(render(normal)==flat,"surface at range limit uses unperturbed normal");
  Require(r(nearby)>r(transition)&&r(transition)>r(flat),"near boundary fades smoothly");
 }
 pc[389]=2000;pc[390]=6000;vc[14]=0;vc[26]=1;
 for(auto&x:q)x.u=1-x.u;DWORD mirror=render(normal);
 Require(abs(r(strong)+r(mirror)-255)<=2&&abs(g(strong)-g(mirror))<=1,"mirrored U tangent");
 for(auto&x:q){x.u=1-x.u;x.v=1-x.v;}mirror=render(normal);
 Require(abs(g(strong)+g(mirror)-255)<=2&&abs(r(strong)-r(mirror))<=1,"mirrored V tangent");
 for(auto&x:q)x.v=1-x.v;
 vc[14]=7000;vc[26]=.0001f;Require(render(normal)==flat,"distant normal fade");vc[14]=0;vc[26]=1;
 for(auto&x:q)x.u=0;Require(render(normal)==flat,"degenerate UV fallback");q[2].u=q[3].u=1;
 pc[0]=pc[1]=pc[2]=.5f;pc[3]=1;pc[4]=pc[5]=pc[6]=.1f;pc[15]=.8f;pc[19]=1;
 pc[28]=pc[29]=3;pc[31]=-1;memcpy(pc+32,&id,64);
 pc[51]=3;pc[52]=-1;pc[53]=0;pc[54]=.25f;pc[56]=pc[57]=pc[58]=1;
 pc[388]=0;DWORD base=render(ship);pc[388]=4;DWORD lit=render(ship);
 Require(abs(r(base)-r(lit))>=15,"full production lighting responds to normals");Require((lit>>24)==255,"hull remains opaque");
 DWORD unchanged=render(native);d->SetTexture(13,nullptr);Require(render(native)==unchanged,"ordinary material ignores bound normal map");
 pc[388]=0;Require(abs(r(render(ship))-r(unchanged))<=1,"zero strength matches ordinary hull lighting");
 std::string baseline=Read("src/obj/ship_normals/matte/before.hlsl");
 auto*originalGloss=make(prefix+baseline,"PSMain");
 d->SetTexture(13,map);
 for(float strength:{0.f,.25f,1.f,4.f})
 {
  pc[388]=strength;
  Require(render(originalGloss)==render(ship),"nearby glossy hull lighting unchanged by distance optimization");
 }
 originalGloss->Release();
 d->SetTexture(13,map);pc[388]=.25f;DWORD quarter=render(normal);
 Require(r(quarter)>r(flat)&&r(quarter)<r(mild),"0.25 relief is weaker than strength 1");
 puts("PASS: restored glossy material and quarter-strength normals");
 printf("PASS: player/CAPITAL/solar scope, packed normals, mirrored UVs, zero/far/degenerate fallback; lighting %d -> %d at x4\n",r(base),r(lit));
 d->SetPixelShader(nullptr);d->SetVertexShader(nullptr);normal->Release();ship->Release();native->Release();vs->Release();
 map->Release();read->Release();rt->Release();d->Release();api->Release();DestroyWindow(w);
 return 0;
}
