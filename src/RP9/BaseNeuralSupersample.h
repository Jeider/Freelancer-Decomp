#pragma once
#include <d3d9.h>
#include <d3dx9.h>
#include <wrl/client.h>
#include <cmath>

// Owns only the base scene targets. The camera, picking and UI keep native dimensions.
class BaseNeuralSupersample
{
    template<class T> using Ptr=Microsoft::WRL::ComPtr<T>;
    Ptr<IDirect3DTexture9> texture;
    Ptr<IDirect3DSurface9> color,depth,savedColor,savedDepth;
    Ptr<IDirect3DPixelShader9> resolve;
    Ptr<IDirect3DStateBlock9> state;
    IDirect3DDevice9* device=nullptr;
    D3DVIEWPORT9 viewport={}; RECT scissor={};
    unsigned width=0,height=0,nativeW=0,nativeH=0;
    bool active=false;
public:
    bool Active()const{return active;}
    void ScaleViewport(D3DVIEWPORT9& v)
    {
        if(!active)return;
        Ptr<IDirect3DSurface9> target;device->GetRenderTarget(0,&target);
        if(target.Get()!=color.Get())return; // Shadow/offscreen passes have their own size.
        v.X=DWORD(double(v.X)*width/nativeW);v.Y=DWORD(double(v.Y)*height/nativeH);
        v.Width=DWORD(double(v.Width)*width/nativeW);v.Height=DWORD(double(v.Height)*height/nativeH);
    }
    HRESULT Begin(IDirect3DDevice9* d,float scale)
    {
        if(active)return D3DERR_INVALIDCALL;
        if(!std::isfinite(scale)||scale<=1.f)return S_FALSE;
        scale=scale>2.f?2.f:scale;
        Ptr<IDirect3DSurface9> original,originalDepth;
        D3DSURFACE_DESC desc={},dd={};D3DVIEWPORT9 vp={};
        HRESULT hr=d->GetRenderTarget(0,&original);if(FAILED(hr))return hr;
        hr=original->GetDesc(&desc);if(FAILED(hr))return hr;
        hr=d->GetDepthStencilSurface(&originalDepth);if(FAILED(hr)||!originalDepth)return D3DERR_INVALIDCALL;
        originalDepth->GetDesc(&dd);hr=d->GetViewport(&vp);if(FAILED(hr))return hr;
        if(desc.MultiSampleType!=D3DMULTISAMPLE_NONE||dd.MultiSampleType!=D3DMULTISAMPLE_NONE)return D3DERR_INVALIDCALL;
        unsigned w=unsigned(std::ceil(desc.Width*scale)),h=unsigned(std::ceil(desc.Height*scale));
        // Model contract is limited to 4K for this experimental quality mode.
        if(w>3840||h>2160)return D3DERR_NOTAVAILABLE;
        if(device!=d||width!=w||height!=h)
        {
            Reset();device=d;
            hr=d->CreateTexture(w,h,1,D3DUSAGE_RENDERTARGET,D3DFMT_A8R8G8B8,D3DPOOL_DEFAULT,&texture,nullptr);
            if(SUCCEEDED(hr))hr=texture->GetSurfaceLevel(0,&color);
            if(SUCCEEDED(hr))hr=d->CreateDepthStencilSurface(w,h,dd.Format,D3DMULTISAMPLE_NONE,0,TRUE,&depth,nullptr);
            // Exact area integration for a 1..2x footprint, in linear light.
            static char const shader[]=R"hlsl(
sampler2D Source:register(s0);
float4 Size:register(c0); // source W,H; source/native X,Y
float3 Linear(float3 c){return lerp(c/12.92,pow(max((c+.055)/1.055,0),2.4),step(.04045,c));}
float3 Encoded(float3 c){return lerp(c*12.92,1.055*pow(max(c,0),1./2.4)-.055,step(.0031308,c));}
float4 main(float2 pixel:VPOS):COLOR0 {
 float2 lo=floor(pixel)*Size.zw,hi=lo+Size.zw,first=floor(lo);
 float3 sum=0;float alpha=0;
 [unroll] for(int y=0;y<3;y++) [unroll] for(int x=0;x<3;x++) {
  float2 p=first+float2(x,y);
  float2 overlap=max(0,min(hi,p+1)-max(lo,p));float weight=overlap.x*overlap.y;
  float4 c=tex2Dlod(Source,float4((p+.5)/Size.xy,0,0));
  sum+=Linear(c.rgb)*weight;alpha+=c.a*weight;
 }
 float area=Size.z*Size.w;return float4(Encoded(sum/area),alpha/area);
})hlsl";
            Ptr<ID3DXBuffer> code,errors;
            if(SUCCEEDED(hr))hr=D3DXCompileShader(shader,sizeof(shader)-1,nullptr,nullptr,"main","ps_3_0",D3DXSHADER_OPTIMIZATION_LEVEL3,&code,&errors,nullptr);
            if(SUCCEEDED(hr))hr=d->CreatePixelShader(static_cast<DWORD*>(code->GetBufferPointer()),&resolve);
            if(FAILED(hr)){Reset();return hr;}width=w;height=h;
        }
        nativeW=desc.Width;nativeH=desc.Height;viewport=vp;d->GetScissorRect(&scissor);
        savedColor=original;savedDepth=originalDepth;active=true;
        hr=d->SetDepthStencilSurface(nullptr);
        if(SUCCEEDED(hr))hr=d->SetRenderTarget(0,color.Get());
        if(SUCCEEDED(hr))hr=d->SetDepthStencilSurface(depth.Get());
        D3DVIEWPORT9 high=vp;ScaleViewport(high);
        if(SUCCEEDED(hr))hr=d->SetViewport(&high);
        RECT full={0,0,LONG(width),LONG(height)};d->SetScissorRect(&full);
        if(SUCCEEDED(hr))hr=d->Clear(0,nullptr,D3DCLEAR_TARGET|D3DCLEAR_ZBUFFER,0xff000000,1,0);
        if(FAILED(hr))End(false);
        return hr;
    }
    // Must be called inside a scene for resolve=true. State is restored even on failure.
    HRESULT End(bool composite)
    {
        if(!active)return S_FALSE;
        HRESULT hr=S_OK;
        if(composite)hr=state?state->Capture():device->CreateStateBlock(D3DSBT_ALL,&state);
        device->SetDepthStencilSurface(nullptr);device->SetRenderTarget(0,savedColor.Get());
        device->SetViewport(&viewport);device->SetScissorRect(&scissor);
        if(composite&&SUCCEEDED(hr))
        {
            D3DVIEWPORT9 out={0,0,nativeW,nativeH,0,1};device->SetViewport(&out);
            device->SetVertexShader(nullptr);device->SetPixelShader(resolve.Get());
            device->SetFVF(D3DFVF_XYZRHW);device->SetTexture(0,texture.Get());
            device->SetSamplerState(0,D3DSAMP_MINFILTER,D3DTEXF_POINT);device->SetSamplerState(0,D3DSAMP_MAGFILTER,D3DTEXF_POINT);
            device->SetSamplerState(0,D3DSAMP_MIPFILTER,D3DTEXF_NONE);device->SetSamplerState(0,D3DSAMP_ADDRESSU,D3DTADDRESS_CLAMP);
            device->SetSamplerState(0,D3DSAMP_ADDRESSV,D3DTADDRESS_CLAMP);device->SetSamplerState(0,D3DSAMP_SRGBTEXTURE,FALSE);
            device->SetRenderState(D3DRS_ZENABLE,FALSE);device->SetRenderState(D3DRS_ZWRITEENABLE,FALSE);
            device->SetRenderState(D3DRS_STENCILENABLE,FALSE);device->SetRenderState(D3DRS_ALPHATESTENABLE,FALSE);
            device->SetRenderState(D3DRS_ALPHABLENDENABLE,FALSE);device->SetRenderState(D3DRS_FOGENABLE,FALSE);
            device->SetRenderState(D3DRS_CULLMODE,D3DCULL_NONE);device->SetRenderState(D3DRS_SCISSORTESTENABLE,FALSE);
            device->SetRenderState(D3DRS_SRGBWRITEENABLE,FALSE);device->SetRenderState(D3DRS_COLORWRITEENABLE,15);
            float size[4]={float(width),float(height),float(width)/nativeW,float(height)/nativeH};
            device->SetPixelShaderConstantF(0,size,1);
            float vertices[16]={-.5f,-.5f,0,1,float(nativeW)-.5f,-.5f,0,1,-.5f,float(nativeH)-.5f,0,1,float(nativeW)-.5f,float(nativeH)-.5f,0,1};
            hr=device->DrawPrimitiveUP(D3DPT_TRIANGLESTRIP,2,vertices,4*sizeof(float));
            HRESULT restored=state->Apply();if(SUCCEEDED(hr))hr=restored;
        }
        device->SetDepthStencilSurface(savedDepth.Get());device->SetViewport(&viewport);device->SetScissorRect(&scissor);
        savedColor.Reset();savedDepth.Reset();active=false;
        return hr;
    }
    void Reset(){if(active)End(false);texture.Reset();color.Reset();depth.Reset();resolve.Reset();state.Reset();device=nullptr;width=height=0;}
};
