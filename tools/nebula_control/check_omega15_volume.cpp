// Production volume/composite shaders and noise; synthetic depth fixtures, never the game.
#include <windows.h>
#include <d3dx9.h>
#include <algorithm>
#include <cmath>
#include <cstdio>
#include <cstdlib>
#include <vector>
#include "RP9ShaderManifest.h"
#include "nebula_noise_fixture.h"
static void Check(HRESULT h){if(FAILED(h)){printf("HRESULT %08lx\n",h);exit(2);}}
static void Require(bool b,const char*m){if(!b){printf("FAIL %s\n",m);exit(3);}}
static void Query(IDirect3DQuery9*q,void*p,unsigned n){DWORD start=GetTickCount();HRESULT h;while((h=q->GetData(p,n,D3DGETDATA_FLUSH))==S_FALSE){Require(GetTickCount()-start<15000,"GPU timeout");Sleep(0);}Check(h);}
int main(int argc,char**argv){
 Require(argc==6,"constants, shader directory, cache, preview, quality");setvbuf(stdout,nullptr,_IONBF,0);
 SetErrorMode(SEM_FAILCRITICALERRORS|SEM_NOGPFAULTERRORBOX|SEM_NOOPENFILEERRORBOX);
 SetEnvironmentVariableA("FREELANCER_SHADER_CACHE_DIR",argv[3]);
 const unsigned W=1920,H=1080,LW=W/2,LH=H/2;const int quality=atoi(argv[5]);
 float c[112][4]={},tone[4]={};FILE*f=nullptr;fopen_s(&f,argv[1],"rb");Require(f!=nullptr,"profile constants");
 Require(fread(c,sizeof(c),1,f)==1&&fread(tone,sizeof(tone),1,f)==1,"complete constants");fclose(f);
 if(quality==2)c[10][0]=(std::min)(c[10][0],64.f);
 c[2][1]=float(H)/W;c[2][2]=.5f/W;c[2][3]=.5f/H;c[36][0]=LW;c[36][1]=LH;c[78][1]=4.f/H;
 auto*api=Direct3DCreate9(D3D_SDK_VERSION);Require(api!=nullptr,"D3D9");IDirect3DDevice9*d=nullptr;
 HWND wnd=CreateWindowA("STATIC","Omega-15 volume probe",WS_POPUP,0,0,W,H,nullptr,nullptr,GetModuleHandle(nullptr),nullptr);
 D3DPRESENT_PARAMETERS pp={};pp.Windowed=1;pp.SwapEffect=D3DSWAPEFFECT_DISCARD;pp.BackBufferWidth=W;pp.BackBufferHeight=H;pp.BackBufferFormat=D3DFMT_A8R8G8B8;
 Check(api->CreateDevice(0,D3DDEVTYPE_HAL,wnd,D3DCREATE_HARDWARE_VERTEXPROCESSING,&pp,&d));
 std::vector<Rp9Startup::FJob>jobs;std::string err;Require(Rp9Startup::Build(argv[2],jobs,err),err.c_str());
 IDirect3DVertexShader9*vs=nullptr;IDirect3DPixelShader9*ps=nullptr,*composite=nullptr;
 for(auto const&job:jobs)if(job.Name=="nebula_volume.hlsl"||job.Name=="nebula_composite.hlsl"){
  std::vector<unsigned char>code;std::string msg;bool hit=false;HRESULT h=Rp9Startup::Compile(job,argv[2],code,msg,hit);if(FAILED(h))puts(msg.c_str());Check(h);
  if(job.Profile[0]=='v'){IDirect3DVertexShader9*s=nullptr;Check(d->CreateVertexShader((DWORD*)code.data(),&s));if(!vs)vs=s;else s->Release();}
  else {IDirect3DPixelShader9*s=nullptr;Check(d->CreatePixelShader((DWORD*)code.data(),&s));if(job.Name=="nebula_volume.hlsl")ps=s;else composite=s;}
 }
 Require(vs&&ps&&composite,"production volume shader pair");
 std::vector<unsigned long>noise;unsigned long hist[256];GenerateNoise(&noise,hist);
 const float coverage=c[16][0],softness=c[16][1];double above=0;int lo=0,hi=255;bool found=false;
 for(int b=255;b>=0;--b){above+=hist[b];if(!found&&above>=coverage*(1-softness)*noise.size()){hi=b;found=true;}if(above>=coverage*noise.size()){lo=b;break;}}
 c[16][0]=lo/255.f;c[16][1]=1.f/(std::max)((hi-lo)/255.f,.01f);c[91][3]=c[16][0]+.5f/c[16][1];
 IDirect3DVolumeTexture9*volume=nullptr;Check(d->CreateVolumeTexture(64,64,64,1,0,D3DFMT_A8R8G8B8,D3DPOOL_MANAGED,&volume,nullptr));
 D3DLOCKED_BOX box;Check(volume->LockBox(0,&box,nullptr,0));for(unsigned z=0;z<64;++z)for(unsigned y=0;y<64;++y)memcpy((char*)box.pBits+z*box.SlicePitch+y*box.RowPitch,&noise[(z*64+y)*64],256);volume->UnlockBox(0);
 IDirect3DTexture9*depth=nullptr,*target=nullptr;IDirect3DSurface9*low=nullptr,*back=nullptr,*read=nullptr;
 Check(d->CreateTexture(W,H,1,0,D3DFMT_R32F,D3DPOOL_MANAGED,&depth,nullptr));
 Check(d->CreateTexture(LW,LH,1,D3DUSAGE_RENDERTARGET,D3DFMT_A16B16G16R16F,D3DPOOL_DEFAULT,&target,nullptr));
 Check(target->GetSurfaceLevel(0,&low));Check(d->GetRenderTarget(0,&back));Check(d->CreateOffscreenPlainSurface(LW,LH,D3DFMT_A16B16G16R16F,D3DPOOL_SYSTEMMEM,&read,nullptr));
 auto setDepth=[&](float distance,bool split){D3DLOCKED_RECT lock;Check(depth->LockRect(0,&lock,nullptr,0));for(unsigned y=0;y<H;++y)for(unsigned x=0;x<W;++x){float z=split&&x<W/2?500:distance;((float*)((char*)lock.pBits+y*lock.Pitch))[x]=c[0][0]+c[0][1]/z;}depth->UnlockRect(0);};
 for(unsigned s:{0u,1u}){Check(d->SetSamplerState(s,D3DSAMP_MINFILTER,s?D3DTEXF_LINEAR:D3DTEXF_POINT));Check(d->SetSamplerState(s,D3DSAMP_MAGFILTER,s?D3DTEXF_LINEAR:D3DTEXF_POINT));Check(d->SetSamplerState(s,D3DSAMP_MIPFILTER,D3DTEXF_NONE));}
 for(unsigned s:{0u,1u})for(auto address:{D3DSAMP_ADDRESSU,D3DSAMP_ADDRESSV,D3DSAMP_ADDRESSW})Check(d->SetSamplerState(s,address,s?D3DTADDRESS_WRAP:D3DTADDRESS_CLAMP));
 Check(d->SetTexture(0,depth));Check(d->SetVertexShader(vs));Check(d->SetFVF(D3DFVF_XYZ|D3DFVF_TEX1));
 Check(d->SetRenderState(D3DRS_ZENABLE,0));Check(d->SetRenderState(D3DRS_CULLMODE,D3DCULL_NONE));Check(d->SetRenderState(D3DRS_SRGBWRITEENABLE,0));
 float quad[4][5]={{-1,1,0,0,0},{1,1,0,1,0},{-1,-1,0,0,1},{1,-1,0,1,1}};
 auto pass=[&](bool march){unsigned width=march?LW:W,height=march?LH:H;float q[4][5];memcpy(q,quad,sizeof(q));for(auto&v:q){v[0]-=1.f/width;v[1]+=1.f/height;}
  D3DVIEWPORT9 vp={0,0,width,height,0,1};Check(d->SetRenderTarget(0,march?low:back));Check(d->SetViewport(&vp));Check(d->SetTexture(1,march?(IDirect3DBaseTexture9*)volume:target));
  for(auto address:{D3DSAMP_ADDRESSU,D3DSAMP_ADDRESSV,D3DSAMP_ADDRESSW})Check(d->SetSamplerState(1,address,march?D3DTADDRESS_WRAP:D3DTADDRESS_CLAMP));
  Check(d->SetPixelShader(march?ps:composite));Check(d->SetRenderState(D3DRS_ALPHABLENDENABLE,march?0:1));Check(d->SetRenderState(D3DRS_COLORWRITEENABLE,march?15:7));
  if(march)Check(d->SetPixelShaderConstantF(0,&c[0][0],112));
  else {float p[26][4]={};memcpy(p[0],c[0],16);p[1][0]=LW;p[1][1]=LH;p[1][2]=1.f/LW;p[1][3]=1.f/LH;
   p[2][0]=.5f/W;p[2][1]=.5f/H;p[2][2]=.06f;memcpy(p[3],tone,16);memcpy(p[4],c[1],16);memcpy(p[5],c[2],16);memcpy(p[6],c[3],48);memcpy(p[14],c[93],64);
   memcpy(p[19],c[6],64);p[19][3]=1;Check(d->SetPixelShaderConstantF(0,&p[0][0],26));Check(d->SetRenderState(D3DRS_SRCBLEND,D3DBLEND_ONE));Check(d->SetRenderState(D3DRS_DESTBLEND,D3DBLEND_SRCALPHA));}
  Check(d->DrawPrimitiveUP(D3DPT_TRIANGLESTRIP,2,q,sizeof(q[0])));
 };
 auto transmission=[&](){Check(d->GetRenderTargetData(low,read));D3DLOCKED_RECT lock;Check(read->LockRect(&lock,nullptr,D3DLOCK_READONLY));std::vector<float>row(LW*4);double sum=0,square=0;
  for(unsigned y=0;y<LH;++y){D3DXFloat16To32Array(row.data(),(D3DXFLOAT16*)((char*)lock.pBits+y*lock.Pitch),LW*4);for(unsigned x=0;x<LW;++x){for(unsigned k=0;k<4;++k)Require(std::isfinite(row[x*4+k]),"finite volume output");float t=row[x*4+3];Require(t>=0&&t<=1.001f,"bounded transmission");sum+=t;square+=t*t;}}
  Check(read->UnlockRect());return std::pair<double,double>(sum/(LW*LH),square/(LW*LH)-sum/(LW*LH)*sum/(LW*LH));};
 double previous=1;
 for(float distance:{50.f,500.f,1500.f,3000.f,6000.f,15000.f}){setDepth(distance,false);Check(d->BeginScene());pass(true);Check(d->EndScene());auto t=transmission();printf("Depth %.0f: mean T %.5f variance %.6f\n",distance,t.first,t.second);
  Require(t.first<=previous+.025,"farther surfaces lose transmission");if(distance==50)Require(t.first>.98,"near surface remains clear");if(distance==3000)Require(t.second>.00005,"spatially varying cloud density");if(distance==15000)Require(t.first<.08,"distant geometry hidden by medium");previous=t.first;}
 setDepth(3000,false);Check(d->BeginScene());pass(true);Check(d->EndScene());auto dense=transmission();
 float saved[112][4];memcpy(saved,c,sizeof(c));c[35][0]=1;c[37][3]=5;c[45][0]=c[53][1]=c[61][2]=1.f/5000;c[45][3]=-.95f;c[53][3]=5006;
 Check(d->BeginScene());pass(true);Check(d->EndScene());auto clear=transmission();Require(clear.first>dense.first+.15,"exclusion volume clears actual depth interval");memcpy(c,saved,sizeof(c));
 IDirect3DSurface9*readColor=nullptr;Check(d->CreateOffscreenPlainSurface(W,H,D3DFMT_A8R8G8B8,D3DPOOL_SYSTEMMEM,&readColor,nullptr));
 auto readPixels=[&](){Check(d->GetRenderTargetData(back,readColor));D3DLOCKED_RECT l;Check(readColor->LockRect(&l,nullptr,D3DLOCK_READONLY));std::vector<DWORD>pixels(W*H);for(unsigned y=0;y<H;++y)memcpy(pixels.data()+y*W,(char*)l.pBits+y*l.Pitch,W*4);readColor->UnlockRect();return pixels;};
 setDepth(500,false);Check(d->BeginScene());pass(true);Check(d->EndScene());auto nearT=transmission();std::vector<DWORD>black;
 for(int white=0;white<2;++white){Check(d->SetRenderTarget(0,back));D3DVIEWPORT9 vp={0,0,W,H,0,1};Check(d->SetViewport(&vp));Check(d->Clear(0,nullptr,D3DCLEAR_TARGET,white?0xffffffff:0xff000000,1,0));Check(d->BeginScene());pass(false);Check(d->EndScene());auto color=readPixels();if(!white)black=std::move(color);else{double contrast=0;for(size_t i=0;i<color.size();++i)for(int s:{0,8,16})contrast+=int((color[i]>>s)&255)-int((black[i]>>s)&255);contrast/=W*H*3.*255.;Require(std::abs(contrast-nearT.first)<.03,"composite retains the raymarched surface contrast");printf("PASS composite: near contrast %.5f vs raw T %.5f\n",contrast,nearT.first);}}
 // Save a depth-step reference; checker squares are depth-writing object colours,
 // not another fog overlay. The production composite performs all fogging.
 setDepth(6000,true);Check(d->SetRenderTarget(0,back));D3DVIEWPORT9 vp={0,0,W,H,0,1};Check(d->SetViewport(&vp));Check(d->Clear(0,nullptr,D3DCLEAR_TARGET,0xff252b31,1,0));
 for(unsigned y=0;y<H;y+=64)for(unsigned x=0;x<W;x+=64)if((x/64+y/64)%2){D3DRECT rect={(LONG)x,(LONG)y,(LONG)(std::min)(x+64,W),(LONG)(std::min)(y+64,H)};Check(d->Clear(1,&rect,D3DCLEAR_TARGET,0xffb6bcc2,1,0));}
 Check(d->BeginScene());pass(true);pass(false);Check(d->EndScene());Check(D3DXSaveSurfaceToFileA(argv[4],D3DXIFF_PNG,back,nullptr,nullptr));
 IDirect3DQuery9 *start=nullptr,*end=nullptr,*freq=nullptr,*disjoint=nullptr;Check(d->CreateQuery(D3DQUERYTYPE_TIMESTAMP,&start));Check(d->CreateQuery(D3DQUERYTYPE_TIMESTAMP,&end));Check(d->CreateQuery(D3DQUERYTYPE_TIMESTAMPFREQ,&freq));Check(d->CreateQuery(D3DQUERYTYPE_TIMESTAMPDISJOINT,&disjoint));
 setDepth(6000,false);std::vector<double>times;for(int frame=0;frame<16;++frame){Check(d->BeginScene());Check(disjoint->Issue(D3DISSUE_BEGIN));Check(start->Issue(D3DISSUE_END));pass(true);pass(false);Check(end->Issue(D3DISSUE_END));Check(disjoint->Issue(D3DISSUE_END));Check(freq->Issue(D3DISSUE_END));Check(d->EndScene());
  UINT64 a,b,hz;BOOL bad;Query(end,&b,8);Query(start,&a,8);Query(freq,&hz,8);Query(disjoint,&bad,4);if(frame>=4&&!bad&&hz)times.push_back(double(b-a)*1000/hz);}
 Require(!times.empty(),"GPU timing");std::sort(times.begin(),times.end());printf("PASS quality %d: production raymarch + composite, 1920x1080 / half-resolution volume, %.0f steps; median %.3f ms, p95 %.3f ms\n",quality,c[10][0],times[times.size()/2],times[(times.size()-1)*95/100]);return 0;
}
