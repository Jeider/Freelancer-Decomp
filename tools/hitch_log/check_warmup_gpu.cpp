#define NOMINMAX
#include "RP9ShaderWarmup.h"
#include "RP9ShaderCache.h"
#include <cstdio>
#include <cstdlib>
#include <fstream>
#include <iterator>

void Check(HRESULT hr){if(FAILED(hr)){printf("FAIL hr=%08lx\n",hr);exit(1);}}
void Require(bool ok,char const* why){if(!ok){printf("FAIL %s\n",why);exit(1);}}
struct Include : ID3DXInclude {
    STDMETHOD(Open)(D3DXINCLUDE_TYPE,LPCSTR name,LPCVOID,LPCVOID* data,UINT* bytes) override {
        std::ifstream file(std::string("D:/games/FL_MOD/DATA_EXTRA/SHADERS/")+name,std::ios::binary);
        if(!file)return E_FAIL;
        std::string text((std::istreambuf_iterator<char>(file)),{});
        char* copy=new char[text.size()];memcpy(copy,text.data(),text.size());*data=copy;*bytes=static_cast<UINT>(text.size());return S_OK;
    }
    STDMETHOD(Close)(LPCVOID data) override {delete[] static_cast<char const*>(data);return S_OK;}
};
int main(){
    SetErrorMode(SEM_FAILCRITICALERRORS|SEM_NOGPFAULTERRORBOX);
    HWND window=CreateWindowA("STATIC","warmup check",WS_OVERLAPPEDWINDOW,0,0,64,64,nullptr,nullptr,GetModuleHandle(nullptr),nullptr);
    Rp9Warmup::Ref<IDirect3D9> api;api.p=Direct3DCreate9(D3D_SDK_VERSION);Require(api.p!=nullptr,"D3D9");
    D3DPRESENT_PARAMETERS pp={};pp.Windowed=TRUE;pp.SwapEffect=D3DSWAPEFFECT_DISCARD;
    pp.hDeviceWindow=window;pp.BackBufferWidth=64;pp.BackBufferHeight=64;pp.BackBufferFormat=D3DFMT_A8R8G8B8;
    Rp9Warmup::Ref<IDirect3DDevice9> device;
    Check(api.p->CreateDevice(0,D3DDEVTYPE_HAL,window,D3DCREATE_HARDWARE_VERTEXPROCESSING,&pp,&device.p));
    auto* d=device.p;
    std::ifstream file("D:/games/FL_MOD/DATA_EXTRA/SHADERS/surface_material.hlsl");
    std::string source((std::istreambuf_iterator<char>(file)),{});Require(!source.empty(),"surface source");
    auto compile=[&](std::string const& s,char const* entry,char const* profile){
        std::vector<unsigned char> out;std::string errors;bool hit=false,stored=false;
        Include include;
        Check(Rp9ShaderCache::Compile(s,&include,entry,profile,0,&out,&errors,&hit,&stored));return out;
    };
    Rp9Warmup::Ref<IDirect3DVertexShader9> standard,nomad;
    auto code=compile(source,"VSMain","vs_3_0");Check(d->CreateVertexShader(reinterpret_cast<DWORD*>(code.data()),&standard.p));
    code=compile("#define SURFACE_NOMAD 1\n"+source,"VSMain","vs_3_0");Check(d->CreateVertexShader(reinterpret_cast<DWORD*>(code.data()),&nomad.p));
    std::vector<Rp9Warmup::Pair> pairs;
    for(char const* family:{"","#define SURFACE_SHIP_NORMALS 1\n","#define SURFACE_ROCK 1\n","#define SURFACE_GREENHOUSE 1\n"})
        for(char const* shadow:{"","#define SURFACE_NO_SHADOW 1\n"})
            for(char const* cube:{"","#define SURFACE_ENV_CUBE 1\n"}){
                code=compile(std::string(family)+shadow+cube+source,"PSMain","ps_3_0");
                IDirect3DPixelShader9* ps=nullptr;Check(d->CreatePixelShader(reinterpret_cast<DWORD*>(code.data()),&ps));
                pairs.push_back({strstr(family,"ROCK")?nomad.p:standard.p,ps,true});
            }
    for(char const* cube:{"","#define SURFACE_ENV_CUBE 1\n"}){
        code=compile(std::string("#define SURFACE_LOW_DETAIL 1\n")+cube+source,"PSMain","ps_3_0");
        IDirect3DPixelShader9* ps=nullptr;Check(d->CreatePixelShader(reinterpret_cast<DWORD*>(code.data()),&ps));
        pairs.push_back({standard.p,ps,true});
    }
    for(char const* light:{"","#define SURFACE_NOMAD_LIGHT 1\n"})for(char const* shadow:{"","#define SURFACE_NO_SHADOW 1\n"}){
        code=compile(std::string("#define SURFACE_NOMAD 1\n")+light+shadow+source,"PSMain","ps_3_0");
        IDirect3DPixelShader9* ps=nullptr;Check(d->CreatePixelShader(reinterpret_cast<DWORD*>(code.data()),&ps));
        pairs.push_back({nomad.p,ps,true});
    }
    code=compile("#define SURFACE_NOMAD 1\n#define SURFACE_NOMAD_LIGHT 1\n#define SURFACE_NO_SHADOW 1\n"+source,"PSNomadDepth","ps_3_0");
    IDirect3DPixelShader9* depthPs=nullptr;Check(d->CreatePixelShader(reinterpret_cast<DWORD*>(code.data()),&depthPs));
    pairs.push_back({nomad.p,depthPs,true});
    // An effect with a volume sampler verifies that the warmup binds real 3D textures.
    code=compile("sampler3D noise:register(s1);float4 main(float4 uv:TEXCOORD0):COLOR{return tex3D(noise,uv.xyz);}","main","ps_3_0");
    IDirect3DPixelShader9* effect=nullptr;Check(d->CreatePixelShader(reinterpret_cast<DWORD*>(code.data()),&effect));
    pairs.push_back({standard.p,effect,false});
    std::vector<IDirect3DVertexShader9*> effectVertices;
    for(auto const& spec: {std::vector<std::string>{"far_rocks.hlsl","VSMain","PSMain"},
        {"far_rocks.hlsl","VSMesh","PSMesh"},{"field_dust.hlsl","VSMain","PSMarch"},
        {"field_dust.hlsl","VSMain","PSComposite"}}){
        std::ifstream fieldFile("D:/games/FL_MOD/DATA_EXTRA/SHADERS/"+spec[0]);
        std::string fieldSource((std::istreambuf_iterator<char>(fieldFile)),{});
        fieldSource="#line 1 \"SHADERS/"+spec[0]+"\"\n"+fieldSource;
        code=compile(fieldSource,spec[1].c_str(),"vs_3_0");
        IDirect3DVertexShader9* vs=nullptr;Check(d->CreateVertexShader(reinterpret_cast<DWORD*>(code.data()),&vs));
        code=compile(fieldSource,spec[2].c_str(),"ps_3_0");
        IDirect3DPixelShader9* ps=nullptr;Check(d->CreatePixelShader(reinterpret_cast<DWORD*>(code.data()),&ps));
        effectVertices.push_back(vs);pairs.push_back({vs,ps,false});
    }
    Rp9Warmup::Ref<IDirect3DSurface9> back;Check(d->GetRenderTarget(0,&back.p));
    D3DVIEWPORT9 vp={3,5,20,24,.2f,.8f};Check(d->SetViewport(&vp));
    Check(d->SetRenderState(D3DRS_ALPHABLENDENABLE,TRUE));Check(d->SetRenderState(D3DRS_SCISSORTESTENABLE,TRUE));
    Check(d->SetRenderState(D3DRS_CULLMODE,D3DCULL_CW));
    float c[4]={7,8,9,10};Check(d->SetPixelShaderConstantF(0,c,1));
    for(bool inScene:{false,true}){
        if(inScene)Check(d->BeginScene());
        ULONGLONG start=GetTickCount64();Check(Rp9Warmup::Draw(d,inScene,pairs));
        printf("warmup %zu pairs, inScene=%d, %llu ms\n",pairs.size(),inScene,GetTickCount64()-start);
        if(inScene)Check(d->EndScene());
        else {Check(d->BeginScene());Check(d->EndScene());}
        Rp9Warmup::Ref<IDirect3DSurface9> now;Check(d->GetRenderTarget(0,&now.p));Require(now.p==back.p,"render target restore");
        D3DVIEWPORT9 after={};Check(d->GetViewport(&after));Require(!memcmp(&after,&vp,sizeof(vp)),"viewport restore");
        DWORD blend=0,cull=0,scissor=0;d->GetRenderState(D3DRS_ALPHABLENDENABLE,&blend);
        d->GetRenderState(D3DRS_CULLMODE,&cull);d->GetRenderState(D3DRS_SCISSORTESTENABLE,&scissor);
        Require(blend==TRUE&&cull==D3DCULL_CW&&scissor==TRUE,"render state restore");
        float afterC[4]={};Check(d->GetPixelShaderConstantF(0,afterC,1));Require(!memcmp(c,afterC,sizeof(c)),"constant restore");
    }
    for(auto& p:pairs)p.ps->Release();
    for(auto* vs:effectVertices)vs->Release();
    DestroyWindow(window);
    puts("PASS: real D3D9 shader draws, 2D/cube/volume samplers, completion fence, scene state and render-state restoration");
}
