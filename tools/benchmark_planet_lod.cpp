// Standalone D3D9 HAL regression/benchmark. Run from the repository root.
// cl /EHsc /O2 /I C:\DXSDK_Jun10\Include tools\benchmark_planet_lod.cpp
//    /link /LIBPATH:C:\DXSDK_Jun10\Lib\x86 d3d9.lib d3dx9.lib user32.lib
// Outputs go to src/obj/planet_lod. Requires the saved pre-change shader there.
#define NOMINMAX
#include <windows.h>
#include <d3d9.h>
#include <d3dx9.h>
#include <algorithm>
#include <cmath>
#include <cstdio>
#include <cstdlib>
#include <string>
#include <vector>
#include "../src/RP9/RP9PlanetQuality.h"

static int W=512,H=512;
static const char* Out="src/obj/planet_lod/";
static void Check(HRESULT hr) { if(FAILED(hr)) { printf("FAIL HRESULT %08lx\n",hr); exit(2); } }
template<class T> static void Release(T*& p) { if(p) {p->Release();p=nullptr;} }
struct Shader { IDirect3DVertexShader9* vs=nullptr; IDirect3DPixelShader9* ps=nullptr; };
struct Vertex { float x,y,z,nx,ny,nz,u,v; };
static IDirect3DDevice9* Dev;
static IDirect3DVertexBuffer9* Vb;
static IDirect3DIndexBuffer9* Ib;
static unsigned Nv,Ni;
static IDirect3DSurface9 *Target,*Readback,*FloatTarget,*FloatRead;
static IDirect3DTexture9* Tex[5]={};
static float C[22][4];
static void Set(int i,float a,float b=0,float c=0,float d=0) {C[i][0]=a;C[i][1]=b;C[i][2]=c;C[i][3]=d;}
static Shader Compile(const char* path,const char* name) {
    Shader s;
    for(int stage=0;stage<2;++stage) {
        ID3DXBuffer *code=nullptr,*error=nullptr,*dis=nullptr;
        HRESULT hr=D3DXCompileShaderFromFileA(path,nullptr,nullptr,stage?"PSMain":"VSMain",stage?"ps_3_0":"vs_3_0",0,&code,&error,nullptr);
        if(error) {printf("%s: %s\n",name,(char*)error->GetBufferPointer());Release(error);} Check(hr);
        Check(D3DXDisassembleShader((DWORD*)code->GetBufferPointer(),FALSE,nullptr,&dis));
        std::string file=std::string(Out)+name+(stage?"_ps.asm":"_vs.asm");
        FILE* f=fopen(file.c_str(),"wb"); fwrite(dis->GetBufferPointer(),1,strlen((char*)dis->GetBufferPointer()),f);fclose(f);Release(dis);
        if(stage) Check(Dev->CreatePixelShader((DWORD*)code->GetBufferPointer(),&s.ps));
        else Check(Dev->CreateVertexShader((DWORD*)code->GetBufferPointer(),&s.vs));
        Release(code);
    } return s;
}
static void Geometry() {
    std::vector<Vertex> v;std::vector<WORD> idx; const int lat=64,lon=128;
    for(int y=0;y<=lat;++y) for(int x=0;x<=lon;++x) {
        float u=float(x)/lon,t=float(y)/lat,p=u*6.2831853f,q=t*3.14159265f;
        float a=sinf(q)*cosf(p),b=cosf(q),c=sinf(q)*sinf(p);
        v.push_back({a,b,c,a,b,c,u,t});
    }
    for(int y=0;y<lat;++y) for(int x=0;x<lon;++x) {
        WORD a=WORD(y*(lon+1)+x),b=a+lon+1;
        idx.insert(idx.end(),{a,b,WORD(a+1),WORD(a+1),b,WORD(b+1)});
    }
    Nv=(unsigned)v.size();Ni=(unsigned)idx.size();void* p;
    Check(Dev->CreateVertexBuffer(Nv*sizeof(Vertex),0,0,D3DPOOL_MANAGED,&Vb,nullptr));Check(Vb->Lock(0,0,&p,0));memcpy(p,v.data(),Nv*sizeof(Vertex));Check(Vb->Unlock());
    Check(Dev->CreateIndexBuffer(Ni*sizeof(WORD),0,D3DFMT_INDEX16,D3DPOOL_MANAGED,&Ib,nullptr));Check(Ib->Lock(0,0,&p,0));memcpy(p,idx.data(),Ni*sizeof(WORD));Check(Ib->Unlock());
    Check(Dev->SetStreamSource(0,Vb,0,sizeof(Vertex)));Check(Dev->SetIndices(Ib));
}
static void Textures() {
    for(int k=0;k<5;++k) {
        Check(Dev->CreateTexture(256,256,0,0,D3DFMT_A8R8G8B8,D3DPOOL_MANAGED,&Tex[k],nullptr));D3DLOCKED_RECT r;Check(Tex[k]->LockRect(0,&r,nullptr,0));
        for(int y=0;y<256;++y) for(int x=0;x<256;++x) {
            float u=x/256.f,v=y/256.f,n=.5f+.5f*sinf(u*77+cosf(v*91))*cosf(v*57);
            float a=.28f+.24f*n,b=.20f+.16f*n,c=.12f+.12f*n;
            if(k==1) {a=.025f+.015f*n;b=.12f+.03f*n;c=.30f+.06f*n;}
            if(k==2) {a=.42f+.10f*n;b=.51f+.10f*n;c=.59f+.10f*n;}
            if(k==3) {float band=.5f+.5f*sinf(v*81+2*sinf(u*19));a=.32f+.32f*band;b=.22f+.28f*band;c=.14f+.22f*band;}
            if(k==4) a=b=c=.42f+.15f*n;
            ((DWORD*)((char*)r.pBits+y*r.Pitch))[x]=D3DCOLOR_COLORVALUE(a,b,c,n);
        } Check(Tex[k]->UnlockRect(0));Check(D3DXFilterTexture(Tex[k],nullptr,0,D3DX_FILTER_BOX));
    }
}
static void Setup(int kind,float quality,float glint=1,float time=17,bool zeroStorm=false) {
    memset(C,0,sizeof(C));Set(0,.45f,.15f,-sqrtf(1-.45f*.45f-.15f*.15f),.08f);Set(1,1,1,.95f);Set(2,.06f,.06f,.07f);
    Set(3,3,kind==3?1.f:0.f,8,12);Set(4,glint,.12f,.025f,.72f);Set(5,kind==3?0.f:6.f,1,1/256.f,1/256.f);Set(6,0,0,8,0);
    Set(7,10,100,0,0);Set(9,kind==1?1.f:0.f,kind==3?0.f:1.f,kind==1?1.f:0.f,kind==3?0.f:1.f);Set(10,.2f,.3f,.6f);Set(11,time,.012f,.0012f);
    Set(12,-1.2f,.2f,zeroStorm?0.f:.3f,zeroStorm?0.f:1.f);Set(13,1.2f,-.3f,zeroStorm?0.f:.2f,zeroStorm?0.f:-.7f);Set(14,2,.5f,zeroStorm?0.f:.2f,0);
    Set(15,0,0,3,.02f);Set(16,4,0,1,20);Set(17,0,glint,kind==2?1.f:0.f,kind==2?1.f:0.f);Set(19,0,0,-100,10);Set(21,quality,quality,quality,quality);
    Check(Dev->SetPixelShaderConstantF(0,&C[0][0],22));Check(Dev->SetTexture(0,Tex[kind]));Check(Dev->SetTexture(1,Tex[4]));Check(Dev->SetTexture(2,Tex[4]));
}
static void Matrix(float scale=1) {
    D3DXMATRIX w,p;D3DXMatrixScaling(&w,scale,scale,scale);w._43=3;
    D3DXMatrixPerspectiveFovLH(&p,1.1f,1,.1f,100);
    Check(Dev->SetVertexShaderConstantF(0,(float*)&w,4));Check(Dev->SetVertexShaderConstantF(4,(float*)&p,4));
}
static void Draw(Shader& s) {Check(Dev->SetVertexShader(s.vs));Check(Dev->SetPixelShader(s.ps));Check(Dev->DrawIndexedPrimitive(D3DPT_TRIANGLELIST,0,0,Nv,0,Ni/3));}
static std::vector<DWORD> Render(Shader& s,const char* name=nullptr) {
    Check(Dev->Clear(0,nullptr,D3DCLEAR_TARGET|D3DCLEAR_ZBUFFER,0,1,0));Check(Dev->BeginScene());Draw(s);Check(Dev->EndScene());
    Check(Dev->GetRenderTargetData(Target,Readback));
    if(name) {std::string f=std::string(Out)+name+".png";Check(D3DXSaveSurfaceToFileA(f.c_str(),D3DXIFF_PNG,Readback,nullptr,nullptr));}
    D3DLOCKED_RECT r;Check(Readback->LockRect(&r,nullptr,D3DLOCK_READONLY));std::vector<DWORD> a(W*H);
    for(int y=0;y<H;++y) memcpy(a.data()+y*W,(char*)r.pBits+y*r.Pitch,W*4);Check(Readback->UnlockRect());return a;
}
static double Difference(const std::vector<DWORD>& a,const std::vector<DWORD>& b,int& maxDiff,int& changed) {
    double sum=0;int n=0;maxDiff=changed=0;
    for(size_t i=0;i<a.size();++i) if(a[i]||b[i]) {bool change=false;for(int c=0;c<3;++c) {int d=abs(int((a[i]>>(8*c))&255)-int((b[i]>>(8*c))&255));sum+=d;maxDiff=std::max(maxDiff,d);change|=d>0;++n;}changed+=change;}
    return n?sum/n:0;
}
template<class T> static void Query(IDirect3DQuery9* q,T& value) {HRESULT hr;ULONGLONG start=GetTickCount64();while((hr=q->GetData(&value,sizeof(value),D3DGETDATA_FLUSH))==S_FALSE) {if(GetTickCount64()-start>30000) {puts("GPU query timeout");exit(2);}Sleep(0);}Check(hr);}
static double Benchmark(Shader& s) {
    IDirect3DQuery9 *a=nullptr,*b=nullptr,*f=nullptr,*d=nullptr;Check(Dev->CreateQuery(D3DQUERYTYPE_TIMESTAMP,&a));Check(Dev->CreateQuery(D3DQUERYTYPE_TIMESTAMP,&b));Check(Dev->CreateQuery(D3DQUERYTYPE_TIMESTAMPFREQ,&f));Check(Dev->CreateQuery(D3DQUERYTYPE_TIMESTAMPDISJOINT,&d));
    const int repeats=20;std::vector<double> samples;
    Render(s);
    for(int n=0;n<5;++n) {
        Check(Dev->BeginScene());Check(d->Issue(D3DISSUE_BEGIN));Check(f->Issue(D3DISSUE_END));Check(a->Issue(D3DISSUE_END));
        for(int j=0;j<repeats;++j) Draw(s);
        Check(b->Issue(D3DISSUE_END));Check(d->Issue(D3DISSUE_END));Check(Dev->EndScene());
        UINT64 t0,t1,freq;BOOL disjoint;Query(a,t0);Query(b,t1);Query(f,freq);Query(d,disjoint);
        if(!disjoint && freq) samples.push_back(double(t1-t0)*1e6/double(freq)/repeats);
    }Release(a);Release(b);Release(f);Release(d);if(samples.empty()) {puts("No valid GPU timestamp samples");exit(2);}std::sort(samples.begin(),samples.end());return samples[samples.size()/2];
}
static bool TestQuality() {
    bool pass=true;float q[4],prev[4]={},res[4],fov[4];
    Rp9PlanetQuality(0,5,1,3,1,q);for(float v:q)pass &= v==1;
    const float low[]={60,250,180,350},high[]={180,700,800,900};
    for(int i=0;i<4;++i) {Rp9PlanetQuality(4,5,1,3,low[i]/4,q);pass &= q[i]==0;Rp9PlanetQuality(4,5,1,3,high[i]/4,q);pass &= q[i]==1;}
    for(int pixels=1;pixels<=1000;++pixels) {Rp9PlanetQuality(4,5,1,3,pixels/4.f,q);for(int i=0;i<4;++i){pass &= q[i]>=prev[i] && q[i]>=0 && q[i]<=1;prev[i]=q[i];}}
    Rp9PlanetQuality(1,5,1,720,1,q);Rp9PlanetQuality(1,5,1,1440,1,res);Rp9PlanetQuality(1,5,2,720,1,fov);
    for(int i=0;i<4;++i)pass &= res[i]>=q[i] && res[i]==fov[i];
    printf("CPU quality: unknown radius, exact endpoints, monotonic diameter, resolution/FOV %s\n",pass?"PASS":"FAIL");return pass;
}
int main(int argc,char** argv) {
    if(argc>1 && std::string(argv[1])=="--large") {W=H=1536;Out="src/obj/planet_lod/large/";CreateDirectoryA(Out,nullptr);}
    bool pass=TestQuality();
    WNDCLASSA wc={};wc.lpfnWndProc=DefWindowProcA;wc.hInstance=GetModuleHandle(nullptr);wc.lpszClassName="PlanetGpuValidation";RegisterClassA(&wc);
    HWND wnd=CreateWindowA(wc.lpszClassName,"Hidden planet validation",WS_OVERLAPPEDWINDOW,0,0,W,H,nullptr,nullptr,wc.hInstance,nullptr);
    IDirect3D9* api=Direct3DCreate9(D3D_SDK_VERSION);if(!api)return 2;D3DADAPTER_IDENTIFIER9 id;Check(api->GetAdapterIdentifier(0,0,&id));printf("Adapter: %s\n",id.Description);
    D3DPRESENT_PARAMETERS pp={};pp.Windowed=TRUE;pp.SwapEffect=D3DSWAPEFFECT_DISCARD;pp.hDeviceWindow=wnd;pp.BackBufferWidth=W;pp.BackBufferHeight=H;pp.BackBufferFormat=D3DFMT_X8R8G8B8;pp.EnableAutoDepthStencil=TRUE;pp.AutoDepthStencilFormat=D3DFMT_D24S8;pp.PresentationInterval=D3DPRESENT_INTERVAL_IMMEDIATE;
    Check(api->CreateDevice(0,D3DDEVTYPE_HAL,wnd,D3DCREATE_HARDWARE_VERTEXPROCESSING,&pp,&Dev));
    Check(Dev->CreateRenderTarget(W,H,D3DFMT_A8R8G8B8,D3DMULTISAMPLE_NONE,0,FALSE,&Target,nullptr));Check(Dev->SetRenderTarget(0,Target));Check(Dev->CreateOffscreenPlainSurface(W,H,D3DFMT_A8R8G8B8,D3DPOOL_SYSTEMMEM,&Readback,nullptr));
    D3DVERTEXELEMENT9 decl[]={{0,0,D3DDECLTYPE_FLOAT3,D3DDECLMETHOD_DEFAULT,D3DDECLUSAGE_POSITION,0},{0,12,D3DDECLTYPE_FLOAT3,D3DDECLMETHOD_DEFAULT,D3DDECLUSAGE_NORMAL,0},{0,24,D3DDECLTYPE_FLOAT2,D3DDECLMETHOD_DEFAULT,D3DDECLUSAGE_TEXCOORD,0},D3DDECL_END()};IDirect3DVertexDeclaration9* vd=nullptr;Check(Dev->CreateVertexDeclaration(decl,&vd));Check(Dev->SetVertexDeclaration(vd));
    Check(Dev->SetRenderState(D3DRS_CULLMODE,D3DCULL_NONE));Check(Dev->SetRenderState(D3DRS_ZENABLE,TRUE));Check(Dev->SetRenderState(D3DRS_ZFUNC,D3DCMP_LESSEQUAL));Check(Dev->SetRenderState(D3DRS_LIGHTING,FALSE));
    for(int i=0;i<3;++i) {Check(Dev->SetSamplerState(i,D3DSAMP_MINFILTER,D3DTEXF_LINEAR));Check(Dev->SetSamplerState(i,D3DSAMP_MAGFILTER,D3DTEXF_LINEAR));Check(Dev->SetSamplerState(i,D3DSAMP_MIPFILTER,D3DTEXF_LINEAR));}
    Geometry();Textures();Matrix();Shader before=Compile("src/obj/planet_lod/planet_surface_before.hlsl","before"),after=Compile("DATA_EXTRA/SHADERS/planet_surface.hlsl","after");
    const char* names[]={"rock","water","ice","gas"};
    for(int k=0;k<4;++k) {
        Setup(k,1);auto a=Render(before,(std::string(names[k])+"_before").c_str());auto b=Render(after,(std::string(names[k])+"_full").c_str());int mx,ch;double mae=Difference(a,b,mx,ch);printf("%s full parity: mean %.6f/255 max %d changed %d\n",names[k],mae,mx,ch);
        // Solid surfaces should stay identical. Gas uses an analytic angular Jacobian:
        // allow small sampling shifts in these deliberately high-frequency procedural bands.
        // Keep both an average and a peak bound; save PNGs for visual/seam inspection.
        pass &= k==3 ? (mae<.05 && mx<=8) : (mae<.1 && mx<=2);
        Setup(k,0);auto low=Render(after,(std::string(names[k])+"_low").c_str());
        if(k==1||k==2) {Setup(k,0,0);auto off=Render(after,(std::string(names[k])+"_low_no_glint").c_str());mae=Difference(low,off,mx,ch);printf("%s LOW glint effect: mean %.6f max %d pixels %d\n",names[k],mae,mx,ch);pass &= ch>100 && mx>3;}
        if(k==3) {Setup(k,0,1,21);auto later=Render(after,"gas_low_later");mae=Difference(low,later,mx,ch);printf("gas LOW animation (17s versus 21s): mean %.6f max %d pixels %d\n",mae,mx,ch);pass &= ch>100;}
        for(float scale : {1.f,.25f}) {
            Matrix(scale);Setup(k,1);double old=Benchmark(before),full=Benchmark(after);Setup(k,0);double lo=Benchmark(after);
            float quality[4];Rp9PlanetQuality(scale,3,1/tanf(.55f),H,1,quality);Setup(k,1);Set(21,quality[0],quality[1],quality[2],quality[3]);Check(Dev->SetPixelShaderConstantF(21,C[21],1));double adaptive=Benchmark(after);
            float diameter=H/tanf(.55f)*scale/sqrtf(9-scale*scale);
            printf("GPU %s diameter %.1fpx: before %.3f us full %.3f us forced-low %.3f us adaptive %.3f us; adaptive speedup %.3fx; q %.3f %.3f %.3f %.3f\n",names[k],diameter,old,full,lo,adaptive,old/adaptive,quality[0],quality[1],quality[2],quality[3]);
        }Matrix();
    }
    // Float readback catches non-finite output hidden by UNORM conversion.
    Check(Dev->CreateRenderTarget(W,H,D3DFMT_A32B32G32R32F,D3DMULTISAMPLE_NONE,0,FALSE,&FloatTarget,nullptr));Check(Dev->CreateOffscreenPlainSurface(W,H,D3DFMT_A32B32G32R32F,D3DPOOL_SYSTEMMEM,&FloatRead,nullptr));Check(Dev->SetRenderTarget(0,FloatTarget));
    for(float quality : {0.f,1.f}) {Setup(3,quality,1,17,true);Check(Dev->Clear(0,nullptr,D3DCLEAR_TARGET|D3DCLEAR_ZBUFFER,0,1,0));Check(Dev->BeginScene());Draw(after);Check(Dev->EndScene());Check(Dev->GetRenderTargetData(FloatTarget,FloatRead));D3DLOCKED_RECT r;Check(FloatRead->LockRect(&r,nullptr,D3DLOCK_READONLY));int bad=0,lit=0;for(int y=0;y<H;++y)for(int x=0;x<W;++x){float* p=(float*)((char*)r.pBits+y*r.Pitch)+x*4;for(int c=0;c<4;++c)bad+=!std::isfinite(p[c]);lit+=p[0]+p[1]+p[2]>.01f;}Check(FloatRead->UnlockRect());printf("zero radius/strength storms quality %.0f: nonfinite %d lit pixels %d\n",quality,bad,lit);pass &= bad==0 && lit>1000;}
    printf("Times: median of five 20-draw GPU timestamp batches; %dx%d UNORM target, same sphere and coverage. Shader microbenchmark, not game FPS or a prediction for another GPU. Forced-low is an isolated branch benchmark; adaptive uses default screen-size thresholds.\n",W,H);
    Check(Dev->SetVertexShader(nullptr));Check(Dev->SetPixelShader(nullptr));Check(Dev->SetStreamSource(0,nullptr,0,0));Check(Dev->SetIndices(nullptr));Check(Dev->SetVertexDeclaration(nullptr));for(int i=0;i<3;++i)Check(Dev->SetTexture(i,nullptr));
    Release(before.vs);Release(before.ps);Release(after.vs);Release(after.ps);Release(vd);Release(Vb);Release(Ib);for(auto& t:Tex)Release(t);Release(Target);Release(Readback);Release(FloatTarget);Release(FloatRead);Release(Dev);Release(api);DestroyWindow(wnd);UnregisterClassA(wc.lpszClassName,wc.hInstance);printf("Validation %s\n",pass?"PASS":"FAIL");return pass?0:1;
}
