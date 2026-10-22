#pragma once
#include <cstring>
#include <cstdint>

// A mirror of actual D3D9 calls, separate from the retail logical state queues.
// All direct RP9 writes pass here; state-block Apply/reset invalidates the mirror.
// Holds no COM references: successfully bound resources are owned by the device.
struct FRp9DeviceCallCache
{
    IDirect3DDevice9* Device=nullptr;
    bool Enabled=true;
    bool TextureValid[16]={},SamplerValid[16][14]={};
    IDirect3DBaseTexture9* Textures[16]={};
    DWORD Samplers[16][14]={};
    bool RenderValid[256]={};DWORD Render[256]={};
    bool MaterialValid=false,FvfValid=false;D3DMATERIAL9 Material={};DWORD Fvf=0;
    bool TransformValid[11]={};D3DMATRIX Transforms[11]={};
    bool VsValid=false,PsValid=false;
    IDirect3DVertexShader9* Vs=nullptr;
    IDirect3DPixelShader9* Ps=nullptr;
    bool VcValid[256]={},PcValid[224]={};
    float Vc[256*4]={},Pc[224*4]={};
    std::uint64_t Submitted=0,Skipped=0,ConstantVectors=0;
    std::uint64_t MainDraws=0,ShadowDraws=0,MainPrimitives=0,ShadowPrimitives=0;
    std::uint64_t InstancedDraws=0,Instances=0;
    // Write counters (never reset) let the surface route keep shaders, pixel constants and
    // samplers 8+ bound between draws: a changed counter means another writer, or a state
    // block Apply (Invalidate), may have replaced them.
    std::uint32_t ShaderWrites=0,PixelConstantWrites=0,HighSamplerWrites=0;

    void Invalidate()
    {
        memset(TextureValid,0,sizeof(TextureValid));memset(SamplerValid,0,sizeof(SamplerValid));
        memset(RenderValid,0,sizeof(RenderValid));
        memset(TransformValid,0,sizeof(TransformValid));MaterialValid=FvfValid=false;
        memset(VcValid,0,sizeof(VcValid));memset(PcValid,0,sizeof(PcValid));
        VsValid=PsValid=false;
        ++ShaderWrites;++PixelConstantWrites;++HighSamplerWrites;
    }
    void Bind(IDirect3DDevice9* D) {if(Device!=D){Device=D;Invalidate();}}
    void ResetCounters()
    {Submitted=Skipped=ConstantVectors=MainDraws=ShadowDraws=MainPrimitives=ShadowPrimitives=InstancedDraws=Instances=0;}
    HRESULT Texture(IDirect3DDevice9* D,DWORD Stage,IDirect3DBaseTexture9* T)
    {
        Bind(D);
        if(Enabled && Stage<16 && TextureValid[Stage] && Textures[Stage]==T){++Skipped;return S_OK;}
        if(Stage>=8) ++HighSamplerWrites;
        ++Submitted;HRESULT H=D->SetTexture(Stage,T);
        if(Stage<16){TextureValid[Stage]=SUCCEEDED(H);Textures[Stage]=T;}return H;
    }
    HRESULT Sampler(IDirect3DDevice9* D,DWORD Stage,D3DSAMPLERSTATETYPE Type,DWORD Value)
    {
        Bind(D);unsigned T=(unsigned)Type;
        if(Enabled && Stage<16 && T<14 && SamplerValid[Stage][T] && Samplers[Stage][T]==Value)
        {++Skipped;return S_OK;}
        if(Stage>=8) ++HighSamplerWrites;
        ++Submitted;HRESULT H=D->SetSamplerState(Stage,Type,Value);
        if(Stage<16 && T<14){SamplerValid[Stage][T]=SUCCEEDED(H);Samplers[Stage][T]=Value;}return H;
    }
    HRESULT RenderState(IDirect3DDevice9* D,D3DRENDERSTATETYPE Type,DWORD Value)
    {
        Bind(D);unsigned T=(unsigned)Type;
        if(Enabled && T<256 && RenderValid[T] && Render[T]==Value){++Skipped;return S_OK;}
        ++Submitted;HRESULT H=D->SetRenderState(Type,Value);
        if(T<256){RenderValid[T]=SUCCEEDED(H);Render[T]=Value;}return H;
    }
    HRESULT SetMaterial(IDirect3DDevice9* D,const D3DMATERIAL9* M)
    {
        Bind(D);if(Enabled && M && MaterialValid && !memcmp(&Material,M,sizeof(Material)))
        {++Skipped;return S_OK;}
        ++Submitted;HRESULT H=D->SetMaterial(M);MaterialValid=SUCCEEDED(H)&&M;
        if(MaterialValid) Material=*M;return H;
    }
    HRESULT SetFvf(IDirect3DDevice9* D,DWORD Value)
    {
        Bind(D);if(Enabled && FvfValid && Fvf==Value){++Skipped;return S_OK;}
        ++Submitted;HRESULT H=D->SetFVF(Value);FvfValid=SUCCEEDED(H);Fvf=Value;return H;
    }
    HRESULT Transform(IDirect3DDevice9* D,D3DTRANSFORMSTATETYPE Type,const D3DMATRIX* M)
    {
        Bind(D);int Slot=Type==D3DTS_VIEW ? 0 : Type==D3DTS_PROJECTION ? 1 : Type==D3DTS_WORLD ? 2 :
            Type>=D3DTS_TEXTURE0 && Type<=D3DTS_TEXTURE7 ? 3+(int)Type-D3DTS_TEXTURE0 : -1;
        if(Enabled && Slot>=0 && M && TransformValid[Slot] && !memcmp(&Transforms[Slot],M,sizeof(*M)))
        {++Skipped;return S_OK;}
        ++Submitted;HRESULT H=D->SetTransform(Type,M);
        if(Slot>=0){TransformValid[Slot]=SUCCEEDED(H)&&M;if(TransformValid[Slot])Transforms[Slot]=*M;}return H;
    }
    HRESULT VertexShader(IDirect3DDevice9* D,IDirect3DVertexShader9* S)
    {
        Bind(D);if(Enabled && VsValid && Vs==S){++Skipped;return S_OK;}
        ++Submitted;++ShaderWrites;HRESULT H=D->SetVertexShader(S);VsValid=SUCCEEDED(H);Vs=S;return H;
    }
    HRESULT PixelShader(IDirect3DDevice9* D,IDirect3DPixelShader9* S)
    {
        Bind(D);if(Enabled && PsValid && Ps==S){++Skipped;return S_OK;}
        ++Submitted;++ShaderWrites;HRESULT H=D->SetPixelShader(S);PsValid=SUCCEEDED(H);Ps=S;return H;
    }
    HRESULT Constants(IDirect3DDevice9* D,bool Vertex,UINT Start,const float* Data,UINT Count)
    {
        Bind(D);const UINT Limit=Vertex ? 256 : 224;
        if(!Vertex) ++PixelConstantWrites;
        // Preserve device validation for invalid or zero-sized API requests.
        if(!Data || Start>=Limit || Count>Limit-Start || !Count)
        {
            ++Submitted;
            return Vertex ? D->SetVertexShaderConstantF(Start,Data,Count) : D->SetPixelShaderConstantF(Start,Data,Count);
        }
        bool* Valid=Vertex ? VcValid : PcValid;float* Cached=Vertex ? Vc : Pc;
        UINT First=0,End=Count;
        if(Enabled)
        {
            while(First<End && Valid[Start+First] && !memcmp(Cached+(Start+First)*4,Data+First*4,16)) ++First;
            while(End>First && Valid[Start+End-1] && !memcmp(Cached+(Start+End-1)*4,Data+(End-1)*4,16)) --End;
            if(First==End){++Skipped;return S_OK;}
        }
        ++Submitted;ConstantVectors+=End-First;
        HRESULT H=Vertex ? D->SetVertexShaderConstantF(Start+First,Data+First*4,End-First) :
                           D->SetPixelShaderConstantF(Start+First,Data+First*4,End-First);
        if(SUCCEEDED(H)) memcpy(Cached+Start*4,Data,Count*16);
        for(UINT I=0;I<Count;++I) Valid[Start+I]=SUCCEEDED(H);
        return H;
    }
};

inline FRp9DeviceCallCache& Rp9DeviceCalls() {static FRp9DeviceCallCache Cache;return Cache;}
inline HRESULT Rp9SetTexture(IDirect3DDevice9* D,DWORD S,IDirect3DBaseTexture9* T)
{return Rp9DeviceCalls().Texture(D,S,T);}
inline HRESULT Rp9SetSamplerState(IDirect3DDevice9* D,DWORD S,D3DSAMPLERSTATETYPE T,DWORD V)
{return Rp9DeviceCalls().Sampler(D,S,T,V);}
inline HRESULT Rp9SetRenderState(IDirect3DDevice9* D,D3DRENDERSTATETYPE T,DWORD V)
{return Rp9DeviceCalls().RenderState(D,T,V);}
inline HRESULT Rp9SetMaterial(IDirect3DDevice9* D,const D3DMATERIAL9* M)
{return Rp9DeviceCalls().SetMaterial(D,M);}
inline HRESULT Rp9SetFvf(IDirect3DDevice9* D,DWORD F)
{return Rp9DeviceCalls().SetFvf(D,F);}
inline HRESULT Rp9SetTransform(IDirect3DDevice9* D,D3DTRANSFORMSTATETYPE T,const D3DMATRIX* M)
{return Rp9DeviceCalls().Transform(D,T,M);}
inline HRESULT Rp9SetVertexShader(IDirect3DDevice9* D,IDirect3DVertexShader9* S)
{return Rp9DeviceCalls().VertexShader(D,S);}
inline HRESULT Rp9SetPixelShader(IDirect3DDevice9* D,IDirect3DPixelShader9* S)
{return Rp9DeviceCalls().PixelShader(D,S);}
inline HRESULT Rp9SetVertexConstants(IDirect3DDevice9* D,UINT S,const float* V,UINT C)
{return Rp9DeviceCalls().Constants(D,true,S,V,C);}
inline HRESULT Rp9SetPixelConstants(IDirect3DDevice9* D,UINT S,const float* V,UINT C)
{return Rp9DeviceCalls().Constants(D,false,S,V,C);}
