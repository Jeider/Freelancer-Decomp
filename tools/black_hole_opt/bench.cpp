#define NOMINMAX
#include <windows.h>
#include <d3dx9.h>
#include <algorithm>
#include <vector>
#include <cstdio>
#include <cmath>
#include <cstdint>
#include "tradelane_visual_noise.h"

static void Check(HRESULT hr){if(FAILED(hr)){printf("HRESULT %08lx\n",hr);exit(2);}}
static IDirect3DDevice9* dev;
static IDirect3DSurface9 *target,*cpu;
static int const W=1920,H=1080;
static std::vector<DWORD> Read(char const* path){FILE* f=fopen(path,"rb");if(!f)exit(3);fseek(f,0,SEEK_END);long n=ftell(f);rewind(f);std::vector<DWORD> data((n+3)/4);fread(data.data(),1,n,f);fclose(f);return data;}
struct Vertex {float x,y,z;DWORD color;float u,v;};
static void Draw(IDirect3DPixelShader9* ps){
    Vertex v[]={{-1,1,0,~0u,0,0},{1,1,0,~0u,1,0},{-1,-1,0,~0u,0,1},{1,-1,0,~0u,1,1}};
    Check(dev->SetPixelShader(ps));Check(dev->BeginScene());
    Check(dev->DrawPrimitiveUP(D3DPT_TRIANGLESTRIP,2,v,sizeof(Vertex)));Check(dev->EndScene());
}
template<class T> void Query(IDirect3DQuery9* q,T& value){
    ULONGLONG start=GetTickCount64();HRESULT hr;
    while((hr=q->GetData(&value,sizeof(value),D3DGETDATA_FLUSH))==S_FALSE){if(GetTickCount64()-start>30000)exit(4);Sleep(0);}Check(hr);
}
static double Time(IDirect3DPixelShader9* ps){
    IDirect3DQuery9 *a,*b,*f,*d;
    Check(dev->CreateQuery(D3DQUERYTYPE_TIMESTAMP,&a));Check(dev->CreateQuery(D3DQUERYTYPE_TIMESTAMP,&b));
    Check(dev->CreateQuery(D3DQUERYTYPE_TIMESTAMPFREQ,&f));Check(dev->CreateQuery(D3DQUERYTYPE_TIMESTAMPDISJOINT,&d));
    Check(d->Issue(D3DISSUE_BEGIN));Check(f->Issue(D3DISSUE_END));Check(a->Issue(D3DISSUE_END));
    for(int i=0;i<8;i++)Draw(ps);
    Check(b->Issue(D3DISSUE_END));Check(d->Issue(D3DISSUE_END));
    UINT64 begin,end,freq;BOOL bad;Query(a,begin);Query(b,end);Query(f,freq);Query(d,bad);
    a->Release();b->Release();f->Release();d->Release();
    return !bad&&freq?double(end-begin)*1000/double(freq)/8:-1;
}
static std::vector<DWORD> Capture(IDirect3DPixelShader9* ps,char const* path){
    Check(dev->Clear(0,nullptr,D3DCLEAR_TARGET,0xff000000,1,0));Draw(ps);
    Check(dev->GetRenderTargetData(target,cpu));Check(D3DXSaveSurfaceToFileA(path,D3DXIFF_PNG,cpu,nullptr,nullptr));
    D3DLOCKED_RECT lock;Check(cpu->LockRect(&lock,nullptr,D3DLOCK_READONLY));
    std::vector<DWORD> pixels(W*H);for(int y=0;y<H;y++)memcpy(pixels.data()+y*W,(char*)lock.pBits+y*lock.Pitch,W*4);
    Check(cpu->UnlockRect());return pixels;
}
static void Params(float x,float y,float z,float clock,float thick){
    D3DXVECTOR3 eye(x,y,z),forward(-x,-y,-z),up(0,1,0),right;
    D3DXVec3Normalize(&forward,&forward);D3DXVec3Cross(&right,&up,&forward);D3DXVec3Normalize(&right,&right);D3DXVec3Cross(&up,&forward,&right);
    float c[80]={};c[0]=clock;c[1]=1.6f;c[2]=180;c[3]=1;
    c[4]=1.f/W;c[5]=1.f/H;c[6]=27.5f;c[8]=.5f/W;c[9]=.5f/H;c[10]=1-.5f/W;c[11]=1-.5f/H;
    c[12]=1;c[13]=100000;c[15]=1;c[16]=x;c[17]=y;c[18]=z;c[19]=480;
    c[20]=tanf(.523598775f)*W/H;c[21]=tanf(.523598775f);c[23]=D3DXVec3Length(&eye)*480;
    for(int k=0;k<3;k++){c[24+k*4]=(&right.x)[k];c[25+k*4]=(&up.x)[k];c[26+k*4]=(&forward.x)[k];}
    c[36]=3;c[37]=22;c[38]=.9f;c[39]=1;c[40]=.7f;c[41]=1;c[42]=.35f;c[43]=1;
    c[44]=c[45]=c[46]=1;c[47]=1.2f;c[48]=650*1.15f/480;c[51]=.6f;
    c[52]=.6f;c[53]=.85f;c[54]=.35f;c[56]=thick;c[57]=.5f;c[58]=1;c[59]=1;
    c[61]=1;c[62]=1000.f/480;c[63]=3500.f/480;c[69]=.33f;c[70]=300.f/480;
    c[76]=3;c[77]=700.f/480;c[78]=6000.f/480;
    Check(dev->SetPixelShaderConstantF(0,c,20));
}
int main(int argc,char** argv){
    if(argc!=3)return 1;
    HWND window=CreateWindowA("STATIC","Black hole GPU check",WS_POPUP,0,0,64,64,nullptr,nullptr,GetModuleHandle(nullptr),nullptr);
    IDirect3D9* api=Direct3DCreate9(D3D_SDK_VERSION);D3DADAPTER_IDENTIFIER9 id;Check(api->GetAdapterIdentifier(0,0,&id));printf("GPU: %s; 1920x1080; isolated PSMain, not game FPS\n",id.Description);
    D3DPRESENT_PARAMETERS pp={};pp.Windowed=TRUE;pp.SwapEffect=D3DSWAPEFFECT_DISCARD;pp.hDeviceWindow=window;pp.BackBufferWidth=64;pp.BackBufferHeight=64;pp.BackBufferFormat=D3DFMT_X8R8G8B8;
    Check(api->CreateDevice(0,D3DDEVTYPE_HAL,window,D3DCREATE_HARDWARE_VERTEXPROCESSING,&pp,&dev));
    Check(dev->CreateRenderTarget(W,H,D3DFMT_A8R8G8B8,D3DMULTISAMPLE_NONE,0,FALSE,&target,nullptr));
    Check(dev->CreateOffscreenPlainSurface(W,H,D3DFMT_A8R8G8B8,D3DPOOL_SYSTEMMEM,&cpu,nullptr));Check(dev->SetRenderTarget(0,target));
    D3DVIEWPORT9 viewport={0,0,W,H,0,1};Check(dev->SetViewport(&viewport));
    Check(dev->SetRenderState(D3DRS_ZENABLE,FALSE));Check(dev->SetRenderState(D3DRS_CULLMODE,D3DCULL_NONE));Check(dev->SetRenderState(D3DRS_ALPHABLENDENABLE,FALSE));
    Check(dev->SetFVF(D3DFVF_XYZ|D3DFVF_DIFFUSE|D3DFVF_TEX1));
    auto vsCode=Read("src/obj/black_hole_opt/vertex.cso");IDirect3DVertexShader9* vs;Check(dev->CreateVertexShader(vsCode.data(),&vs));Check(dev->SetVertexShader(vs));float remap[4]={1,1,0,0};Check(dev->SetVertexShaderConstantF(7,remap,1));
    IDirect3DPixelShader9* shaders[2];for(int i=0;i<2;i++){auto code=Read(argv[i+1]);Check(dev->CreatePixelShader(code.data(),&shaders[i]));}
    IDirect3DTexture9 *scene,*depth;Check(dev->CreateTexture(W,H,1,0,D3DFMT_A8R8G8B8,D3DPOOL_MANAGED,&scene,nullptr));Check(dev->CreateTexture(W,H,1,0,D3DFMT_R32F,D3DPOOL_MANAGED,&depth,nullptr));
    D3DLOCKED_RECT lock;Check(scene->LockRect(0,&lock,nullptr,0));for(int y=0;y<H;y++)for(int x=0;x<W;x++)((DWORD*)((char*)lock.pBits+y*lock.Pitch))[x]=0xff000000u|((x*91/W)<<16)|((y*70/H)<<8)|(((x/80+y/80)%2)?60:20);Check(scene->UnlockRect(0));
    Check(depth->LockRect(0,&lock,nullptr,0));for(int y=0;y<H;y++)for(int x=0;x<W;x++)((float*)((char*)lock.pBits+y*lock.Pitch))[x]=(x<W/10&&y>H/2)? .99f:1.f;Check(depth->UnlockRect(0));
    IDirect3DVolumeTexture9* noise;int const N=TradeLaneNoiseSize;Check(dev->CreateVolumeTexture(N,N,N,1,0,D3DFMT_A8R8G8B8,D3DPOOL_MANAGED,&noise,nullptr));
    std::vector<uint32_t> texels(N*N*N);BuildTradeLaneNoise(texels.data());D3DLOCKED_BOX box;Check(noise->LockBox(0,&box,nullptr,0));
    for(int z=0;z<N;z++)for(int y=0;y<N;y++)memcpy((char*)box.pBits+z*box.SlicePitch+y*box.RowPitch,texels.data()+(z*N+y)*N,N*4);Check(noise->UnlockBox(0));
    Check(dev->SetTexture(0,scene));Check(dev->SetTexture(1,depth));Check(dev->SetTexture(2,noise));Check(dev->SetTexture(3,noise));
    for(int s=0;s<4;s++){dev->SetSamplerState(s,D3DSAMP_MINFILTER,s==1?D3DTEXF_POINT:D3DTEXF_LINEAR);dev->SetSamplerState(s,D3DSAMP_MAGFILTER,s==1?D3DTEXF_POINT:D3DTEXF_LINEAR);dev->SetSamplerState(s,D3DSAMP_MIPFILTER,D3DTEXF_NONE);for(auto a:{D3DSAMP_ADDRESSU,D3DSAMP_ADDRESSV,D3DSAMP_ADDRESSW})dev->SetSamplerState(s,a,s==2?D3DTADDRESS_WRAP:D3DTADDRESS_CLAMP);}
    float poses[][5]={{0,12,-28,3,0},{0,.2f,-26,3,0},{0,.2f,-8,3,0},{4,.1f,-5,17,0},{0,.2f,-26,17,.03f}};
    bool pass=true;
    for(int p=0;p<5;p++){
        Params(poses[p][0],poses[p][1],poses[p][2],poses[p][3],poses[p][4]);
        char path[128];sprintf(path,"src/obj/black_hole_opt/pose%d_before.png",p);auto before=Capture(shaders[0],path);
        sprintf(path,"src/obj/black_hole_opt/pose%d_after.png",p);auto after=Capture(shaders[1],path);
        size_t changed=0;int peak=0;double total=0;for(size_t i=0;i<before.size();i++){int m=0;for(int k=0;k<3;k++){int diff=abs(int((before[i]>>(k*8))&255)-int((after[i]>>(k*8))&255));m=std::max(m,diff);total+=diff;}peak=std::max(peak,m);changed+=m>2;}
        std::vector<double> times[2];for(int n=0;n<10;n++)for(int j=0;j<2;j++){int index=(n+j)%2;double t=Time(shaders[index]);if(n>=3&&t>0)times[index].push_back(t);}
        for(auto& t:times){if(t.empty())return 5;std::sort(t.begin(),t.end());}
        double a=times[0][times[0].size()/2],b=times[1][times[1].size()/2];
        printf("pose%d before=%.3fms after=%.3fms speedup=%.3fx mean_error=%.6f peak=%d pixels_gt2=%zu/%zu\n",p,a,b,a/b,total/(before.size()*3),peak,changed,before.size());fflush(stdout);
        pass=pass && changed<before.size()/1000 && total/(before.size()*3)<.1;
    }
    printf("Image tolerance: %s\n",pass?"PASS":"FAIL");return pass?0:6;
}
