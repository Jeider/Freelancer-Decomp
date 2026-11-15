#include <windows.h>
#include <d3dx9.h>
#include <cmath>
#include <cstdio>
#include <cstdlib>
#include <initializer_list>

static void check(HRESULT hr) { if(FAILED(hr)) { printf("HRESULT %08lx\n",hr); exit(2); } }
struct Include : ID3DXInclude {
    STDMETHOD(Open)(D3DXINCLUDE_TYPE,LPCSTR name,LPCVOID,LPCVOID* data,UINT* size) override {
        char path[512];sprintf_s(path,"DATA_EXTRA/SHADERS/%s",name);FILE* f=nullptr;
        if(fopen_s(&f,name,"rb") || !f)
            if(fopen_s(&f,path,"rb") || !f)return E_FAIL;
        fseek(f,0,SEEK_END);*size=(UINT)ftell(f);rewind(f);
        char* p=new char[*size];fread(p,1,*size,f);fclose(f);*data=p;return S_OK;
    }
    STDMETHOD(Close)(LPCVOID p) override {delete[] (const char*)p;return S_OK;}
};
static IDirect3DPixelShader9* shader(IDirect3DDevice9* dev,const char* path,const char* entry) {
    ID3DXBuffer *code=nullptr,*errors=nullptr;
    Include includes;
    HRESULT hr=D3DXCompileShaderFromFileA(path,nullptr,&includes,entry,"ps_3_0",0,&code,&errors,nullptr);
    if(errors){puts((char*)errors->GetBufferPointer());errors->Release();}
    check(hr);IDirect3DPixelShader9* ps=nullptr;
    check(dev->CreatePixelShader((DWORD*)code->GetBufferPointer(),&ps));code->Release();return ps;
}
int main() {
    SetErrorMode(SEM_FAILCRITICALERRORS|SEM_NOGPFAULTERRORBOX);
    HWND wnd=CreateWindowA("STATIC","core haze check",WS_POPUP,0,0,4,4,nullptr,nullptr,GetModuleHandle(nullptr),nullptr);
    IDirect3D9* api=Direct3DCreate9(D3D_SDK_VERSION);
    D3DPRESENT_PARAMETERS pp={};pp.Windowed=TRUE;pp.SwapEffect=D3DSWAPEFFECT_DISCARD;
    pp.BackBufferWidth=4;pp.BackBufferHeight=4;pp.BackBufferFormat=D3DFMT_A8R8G8B8;
    IDirect3DDevice9* dev=nullptr;
    check(api->CreateDevice(0,D3DDEVTYPE_HAL,wnd,D3DCREATE_HARDWARE_VERTEXPROCESSING,&pp,&dev));
    auto baseline=shader(dev,"D:/Games/FL_MOD/DATA_EXTRA/SHADERS/nebula_volume.hlsl","PSRaymarch");
    baseline->Release();puts("PASS installed baseline shader");
    const char* paths[]={"nebula_volume.hlsl","nebula_ice.hlsl","nebula_walker_ice.hlsl","nebula_edge_fibre.hlsl","nebula_alien.hlsl"};
    for(auto path:paths){char full[256];sprintf_s(full,"DATA_EXTRA/SHADERS/%s",path);
        auto ps=shader(dev,full,"PSRaymarch");ps->Release();printf("PASS GPU shader %s\n",path);}
    auto composite=shader(dev,"DATA_EXTRA/SHADERS/nebula_composite.hlsl","PSComposite");
    composite->Release();puts("PASS GPU composite with core haze");
    auto ps=shader(dev,"tools/nebula_control/core_haze_check.hlsl","PSCoreProbe");
    IDirect3DSurface9 *target=nullptr,*cpu=nullptr;
    check(dev->CreateRenderTarget(4,4,D3DFMT_A32B32G32R32F,D3DMULTISAMPLE_NONE,0,FALSE,&target,nullptr));
    check(dev->CreateOffscreenPlainSurface(4,4,D3DFMT_A32B32G32R32F,D3DPOOL_SYSTEMMEM,&cpu,nullptr));
    check(dev->SetRenderTarget(0,target));check(dev->SetDepthStencilSurface(nullptr));
    check(dev->SetPixelShader(ps));check(dev->SetVertexShader(nullptr));
    check(dev->SetFVF(D3DFVF_XYZRHW|D3DFVF_TEX1));
    dev->SetRenderState(D3DRS_ZENABLE,FALSE);dev->SetRenderState(D3DRS_CULLMODE,D3DCULL_NONE);
    dev->SetRenderState(D3DRS_ALPHABLENDENABLE,FALSE);
    struct Vertex {float x,y,z,w,u,v;} quad[]={{-.5f,-.5f,0,1,0,0},{3.5f,-.5f,0,1,1,0},{-.5f,3.5f,0,1,0,1},{3.5f,3.5f,0,1,1,1}};
    float constants[115*4]={};constants[78*4]=1;
    constants[24*4]=.15f;constants[24*4+1]=.08f;constants[24*4+2]=.04f;
    constants[113*4]=.1f;constants[113*4+1]=.2f;constants[113*4+2]=.3f;constants[113*4+3]=.6f;
    for(float sigma:{0.f,-std::log(.96f)/6400.f})for(float distance:{-1.f,0.f,1000.f,6400.f,12800.f}) {
        constants[24*4+3]=sigma;constants[114*4]=distance;
        check(dev->SetPixelShaderConstantF(0,constants,115));
        check(dev->BeginScene());check(dev->DrawPrimitiveUP(D3DPT_TRIANGLESTRIP,2,quad,sizeof(Vertex)));check(dev->EndScene());
        check(dev->GetRenderTargetData(target,cpu));D3DLOCKED_RECT lock;
        check(cpu->LockRect(&lock,nullptr,D3DLOCK_READONLY));float* got=(float*)lock.pBits;
        float t=std::exp(-std::fmax(distance,0.f)*sigma);
        for(int c=0;c<4;++c){float expected=c==3 ? .6f*t : constants[24*4+c]*(1-t)+constants[113*4+c]*t;
            if(std::fabs(got[c]-expected)>.0001f){printf("FAIL distance=%f channel=%d got=%f expected=%f\n",distance,c,got[c],expected);return 1;}}
        check(cpu->UnlockRect());
    }
    puts("PASS GPU interior haze: zero length, nearby geometry, core radius/diameter, disabled identity, premultiplied colour and transmission");
    cpu->Release();target->Release();ps->Release();dev->Release();api->Release();DestroyWindow(wnd);
}
