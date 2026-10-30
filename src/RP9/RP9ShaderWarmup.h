#pragma once
#include <d3dx9.h>
#include <vector>

namespace Rp9Warmup {
template<class T> struct Ref {
    T* p=nullptr;
    ~Ref(){if(p)p->Release();}
    Ref()=default;
    Ref(Ref const&)=delete;
    Ref& operator=(Ref const&)=delete;
};
struct Pair {
    IDirect3DVertexShader9* vs;
    IDirect3DPixelShader9* ps;
    bool surface;
};

// Driver work must complete during loading, not at the first flight Present.
// All draws go to an 8x8 private target. Restore both D3D state and outputs;
// state blocks alone do not restore render targets or the depth surface.
inline HRESULT Draw(IDirect3DDevice9* d, bool inScene, std::vector<Pair> const& pairs) {
    if(pairs.empty()) return S_OK;
    Ref<IDirect3DStateBlock9> state;
    Ref<IDirect3DSurface9> outputs[4], depth, target;
    Ref<IDirect3DTexture9> tex;
    Ref<IDirect3DCubeTexture9> cube;
    Ref<IDirect3DVolumeTexture9> volume;
    Ref<IDirect3DVertexDeclaration9> decl;
    Ref<IDirect3DVertexShader9> fullscreen;
    Ref<IDirect3DQuery9> fence;
    Ref<ID3DXBuffer> code;
    D3DCAPS9 caps={}; d->GetDeviceCaps(&caps);
    unsigned const targets=(caps.NumSimultaneousRTs<4 ? caps.NumSimultaneousRTs : 4);
    HRESULT hr=d->CreateStateBlock(D3DSBT_ALL,&state.p);
    if(FAILED(hr)) return hr;
    for(unsigned i=0;i<targets;++i) d->GetRenderTarget(i,&outputs[i].p);
    d->GetDepthStencilSurface(&depth.p);
    D3DVIEWPORT9 viewport={}; d->GetViewport(&viewport);
    bool scene=inScene, touched=false;
    // Scope keeps every failure path from leaking bindings or target changes.
    struct Restore {
        IDirect3DDevice9* d; IDirect3DStateBlock9* state; Ref<IDirect3DSurface9>* outputs;
        IDirect3DSurface9* depth; D3DVIEWPORT9 viewport; unsigned count;
        bool wasScene; bool& scene; bool& touched;
        ~Restore(){
            if(!touched)return;
            if(scene && !wasScene)d->EndScene();
            for(unsigned i=0;i<count;++i)d->SetRenderTarget(i,outputs[i].p);
            d->SetDepthStencilSurface(depth);state->Apply();d->SetViewport(&viewport);
            if(wasScene && !scene)d->BeginScene();
        }
    } restore{d,state.p,outputs,depth.p,viewport,targets,inScene,scene,touched};
    hr=d->CreateRenderTarget(8,8,D3DFMT_A8R8G8B8,D3DMULTISAMPLE_NONE,0,FALSE,&target.p,nullptr);
    if(FAILED(hr))return hr;
    if(FAILED(hr=d->CreateTexture(1,1,1,0,D3DFMT_A8R8G8B8,D3DPOOL_MANAGED,&tex.p,nullptr)))return hr;
    if(FAILED(hr=d->CreateCubeTexture(1,1,0,D3DFMT_A8R8G8B8,D3DPOOL_MANAGED,&cube.p,nullptr)))return hr;
    if(FAILED(hr=d->CreateVolumeTexture(1,1,1,1,0,D3DFMT_A8R8G8B8,D3DPOOL_MANAGED,&volume.p,nullptr)))return hr;
    D3DLOCKED_RECT rect={};
    if(SUCCEEDED(tex.p->LockRect(0,&rect,nullptr,0))){*static_cast<DWORD*>(rect.pBits)=0xffffffff;tex.p->UnlockRect(0);}
    for(unsigned i=0;i<6;++i)if(SUCCEEDED(cube.p->LockRect(static_cast<D3DCUBEMAP_FACES>(i),0,&rect,nullptr,0))){
        *static_cast<DWORD*>(rect.pBits)=0xffffffff;cube.p->UnlockRect(static_cast<D3DCUBEMAP_FACES>(i),0);}
    D3DLOCKED_BOX box={};
    if(SUCCEEDED(volume.p->LockBox(0,&box,nullptr,0))){*static_cast<DWORD*>(box.pBits)=0xffffffff;volume.p->UnlockBox(0);}
    // Complete rigid-mesh input declaration, also accepted by fullscreen programs.
    D3DVERTEXELEMENT9 elements[]={{0,0,D3DDECLTYPE_FLOAT3,0,D3DDECLUSAGE_POSITION,0},
        {0,12,D3DDECLTYPE_FLOAT3,0,D3DDECLUSAGE_NORMAL,0},
        {0,24,D3DDECLTYPE_D3DCOLOR,0,D3DDECLUSAGE_COLOR,0},
        {0,28,D3DDECLTYPE_FLOAT2,0,D3DDECLUSAGE_TEXCOORD,0},
        {0,36,D3DDECLTYPE_FLOAT2,0,D3DDECLUSAGE_TEXCOORD,1},
        {0,44,D3DDECLTYPE_FLOAT2,0,D3DDECLUSAGE_TEXCOORD,2},D3DDECL_END()};
    if(FAILED(hr=d->CreateVertexDeclaration(elements,&decl.p)))return hr;
    char const source[]="struct O{float4 p:POSITION;float4 c:COLOR0;float4 t0:TEXCOORD0;float4 t1:TEXCOORD1;float4 t2:TEXCOORD2;float4 t3:TEXCOORD3;float4 t4:TEXCOORD4;float4 t5:TEXCOORD5;float4 t6:TEXCOORD6;float4 t7:TEXCOORD7;}; O main(float3 p:POSITION,float2 uv:TEXCOORD0){O o;o.p=float4(p,1);o.c=1;o.t0=float4(uv,1,1);o.t1=o.t2=o.t3=o.t4=o.t5=o.t6=o.t7=o.t0;return o;}";
    if(FAILED(hr=D3DXCompileShader(source,sizeof(source)-1,nullptr,nullptr,"main","vs_3_0",0,&code.p,nullptr,nullptr)))return hr;
    if(FAILED(hr=d->CreateVertexShader(static_cast<DWORD*>(code.p->GetBufferPointer()),&fullscreen.p)))return hr;
    if(FAILED(hr=d->CreateQuery(D3DQUERYTYPE_EVENT,&fence.p)))return hr;
    touched=true;
    for(unsigned i=1;i<targets;++i)d->SetRenderTarget(i,nullptr);
    d->SetDepthStencilSurface(nullptr);
    if(FAILED(hr=d->SetRenderTarget(0,target.p)))return hr;
    D3DVIEWPORT9 vp={0,0,8,8,0,1};d->SetViewport(&vp);
    d->SetRenderState(D3DRS_ZENABLE,FALSE);d->SetRenderState(D3DRS_ZWRITEENABLE,FALSE);
    d->SetRenderState(D3DRS_STENCILENABLE,FALSE);d->SetRenderState(D3DRS_CULLMODE,D3DCULL_NONE);
    d->SetRenderState(D3DRS_ALPHATESTENABLE,FALSE);d->SetRenderState(D3DRS_ALPHABLENDENABLE,FALSE);
    d->SetRenderState(D3DRS_SCISSORTESTENABLE,FALSE);d->SetRenderState(D3DRS_COLORWRITEENABLE,15);
    d->SetRenderState(D3DRS_CLIPPLANEENABLE,0);d->SetRenderState(D3DRS_FILLMODE,D3DFILL_SOLID);
    for(unsigned i=0;i<16;++i){
        d->SetStreamSourceFreq(i,1);
        d->SetSamplerState(i,D3DSAMP_MINFILTER,D3DTEXF_POINT);d->SetSamplerState(i,D3DSAMP_MAGFILTER,D3DTEXF_POINT);
        d->SetSamplerState(i,D3DSAMP_MIPFILTER,D3DTEXF_NONE);
    }
    float vc[256*4]={},pc[224*4]={};
    for(unsigned m=0;m<4;++m)for(unsigned i=0;i<4;++i)vc[m*16+i*5]=1;
    for(unsigned i=0;i<4;++i)pc[i]=pc[4+i]=1;
    pc[3*4+3]=.7f; pc[4*4]=1;pc[7*4]=pc[7*4+1]=4;
    // Finite denominators for shader-specific constants; no lights/volume fields.
    pc[5*4+1]=100;pc[60*4+1]=1.f/8;pc[63*4]=pc[63*4+2]=pc[63*4+3]=100;
    d->SetVertexShaderConstantF(0,vc,256);d->SetPixelShaderConstantF(0,pc,224);
    struct V {float p[3],n[3];DWORD c;float uv[6];};
    V vertices[]={{{-1,-1,.5f},{0,0,1},0xffffffff,{0,0,0,0,0,0}},
                  {{-1,3,.5f},{0,0,1},0xffffffff,{0,2,0,2,0,2}},
                  {{3,-1,.5f},{0,0,1},0xffffffff,{2,0,2,0,2,0}}};
    d->SetVertexDeclaration(decl.p);
    if(!scene){if(FAILED(hr=d->BeginScene()))return hr;scene=true;}
    for(auto const& pair:pairs){
        for(unsigned i=0;i<16;++i)d->SetTexture(i,tex.p);
        UINT bytes=0;pair.ps->GetFunction(nullptr,&bytes);std::vector<DWORD> words((bytes+3)/4);
        if(FAILED(hr=pair.ps->GetFunction(words.data(),&bytes)))return hr;
        Ref<ID3DXConstantTable> constants;
        if(SUCCEEDED(D3DXGetShaderConstantTable(words.data(),&constants.p))){
            D3DXCONSTANTTABLE_DESC td={};constants.p->GetDesc(&td);
            for(UINT i=0;i<td.Constants;++i){
                D3DXCONSTANT_DESC cd={};UINT count=1;
                if(SUCCEEDED(constants.p->GetConstantDesc(constants.p->GetConstant(nullptr,i),&cd,&count)) && cd.RegisterSet==D3DXRS_SAMPLER){
                    for(UINT j=0;j<cd.RegisterCount;++j)d->SetTexture(cd.RegisterIndex+j,
                        cd.Type==D3DXPT_SAMPLERCUBE ? static_cast<IDirect3DBaseTexture9*>(cube.p) :
                        cd.Type==D3DXPT_SAMPLER3D ? static_cast<IDirect3DBaseTexture9*>(volume.p) : tex.p);
                }
            }
        }
        d->SetPixelShader(pair.ps);
        // Surface shaders use the real pair. Effect-specific vertex constants
        // can clip dummy geometry: warm their pixel shader with a fullscreen VS.
        d->SetVertexShader(pair.surface ? pair.vs : fullscreen.p);
        if(FAILED(hr=d->DrawPrimitiveUP(D3DPT_TRIANGLELIST,1,vertices,sizeof(V))))return hr;
        if(!pair.surface){
            // Also submit the actual effect pair; geometry may be clipped by
            // effect-specific constants, but its vertex/declaration route is
            // now known to the driver too.
            d->SetVertexShader(pair.vs);
            if(FAILED(hr=d->DrawPrimitiveUP(D3DPT_TRIANGLELIST,1,vertices,sizeof(V))))return hr;
        }
    }
    if(FAILED(hr=d->EndScene()))return hr;scene=false;
    if(FAILED(hr=fence.p->Issue(D3DISSUE_END)))return hr;
    ULONGLONG const start=GetTickCount64();
    while((hr=fence.p->GetData(nullptr,0,D3DGETDATA_FLUSH))==S_FALSE){
        if(GetTickCount64()-start>10000)return HRESULT_FROM_WIN32(WAIT_TIMEOUT);
        Sleep(1);
    }
    return hr;
}
}
