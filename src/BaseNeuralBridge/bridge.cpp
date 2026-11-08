#include "feed_client.h"
#include "base_neural_bridge.h"
#include "shaders.h"
#include <d3dcompiler.h>
#include <imgui.h>
#include <reshade.hpp>
#include <memory>
#include <cmath>

using Microsoft::WRL::ComPtr;
namespace
{
    HMODULE Module = nullptr;
    ID3D11Device* TrackedDevice = nullptr; // weak; retired by destroy_device
    bool Faulted = false;
    bool NvidiaAdapter = false;
    void Log(char const* s) { reshade::log::message(reshade::log::level::info, s); }
    DXGI_FORMAT ColorFormat(DXGI_FORMAT f)
    {
        if (f == DXGI_FORMAT_R8G8B8A8_TYPELESS || f == DXGI_FORMAT_R8G8B8A8_UNORM_SRGB) return DXGI_FORMAT_R8G8B8A8_UNORM;
        if (f == DXGI_FORMAT_B8G8R8A8_TYPELESS || f == DXGI_FORMAT_B8G8R8A8_UNORM_SRGB) return DXGI_FORMAT_B8G8R8A8_UNORM;
        return f;
    }
    bool Compile(char const* entry, char const* target, ComPtr<ID3DBlob>& blob)
    {
        ComPtr<ID3DBlob> error;
        HRESULT hr = D3DCompile(BaseNeuralShaders, sizeof(BaseNeuralShaders)-1, "base_neural", nullptr, nullptr,
                               entry, target, D3DCOMPILE_OPTIMIZATION_LEVEL3, 0, &blob, &error);
        if (FAILED(hr) && error) Log(static_cast<char const*>(error->GetBufferPointer()));
        return SUCCEEDED(hr);
    }
    struct Source
    {
        ComPtr<ID3D11RenderTargetView> rtv;
        ComPtr<ID3D11Texture2D> color, depth;
        D3D11_TEXTURE2D_DESC cd = {}, dd = {};
        bool Get(ID3D11DeviceContext* context, BaseNeuralBridge::Frame const& f)
        {
            ComPtr<ID3D11DepthStencilView> dsv;
            context->OMGetRenderTargets(1, &rtv, &dsv);
            ComPtr<ID3D11Resource> resource;
            if (!rtv) return false;
            rtv->GetResource(&resource);
            if (FAILED(resource.As(&color))) return false;
            color->GetDesc(&cd);
            if (cd.Width != f.width || cd.Height != f.height || cd.SampleDesc.Count != 1 || cd.ArraySize != 1) return false;
            DXGI_FORMAT const cf = ColorFormat(cd.Format);
            if (cf != DXGI_FORMAT_R8G8B8A8_UNORM && cf != DXGI_FORMAT_B8G8R8A8_UNORM) return false;
            D3D11_RENDER_TARGET_VIEW_DESC view;rtv->GetDesc(&view);
            if(view.Format==DXGI_FORMAT_R8G8B8A8_UNORM_SRGB||view.Format==DXGI_FORMAT_B8G8R8A8_UNORM_SRGB)
            {
                // Composite already encodes sRGB. Do not apply hardware encoding twice.
                ComPtr<ID3D11Device> device;context->GetDevice(&device);view.Format=ColorFormat(view.Format);
                rtv.Reset();if(FAILED(device->CreateRenderTargetView(color.Get(),&view,&rtv)))return false;
            }
            if (f.mode == BaseNeuralBridge::Passthrough) return true;
            if (!dsv) return false;
            resource.Reset(); dsv->GetResource(&resource);
            if (FAILED(resource.As(&depth))) return false;
            depth->GetDesc(&dd);
            return dd.Width == cd.Width && dd.Height == cd.Height && dd.SampleDesc.Count == 1 && dd.ArraySize == 1;
        }
    };
    struct Session
    {
        BaseFeed::Client feed;
        ComPtr<ID3D11Device1> device;
        ComPtr<ID3D11DeviceContext4> context;
        ComPtr<ID3DDeviceContextState> isolated;
        ComPtr<ID3D11Texture2D> color, previous, depth;
        ComPtr<ID3D11ShaderResourceView> color_srv, previous_srv, depth_srv, neural_srv;
        ComPtr<ID3D11UnorderedAccessView> uav[3];
        ComPtr<ID3D11ComputeShader> copy, flow;
        ComPtr<ID3D11VertexShader> vs;
        ComPtr<ID3D11PixelShader> ps;
        ComPtr<ID3D11Buffer> constants;
        ComPtr<ID3D11RasterizerState> raster;
        ComPtr<ID3D11Query> retired;
        unsigned width = 0, height = 0, mode = 0;
        DXGI_FORMAT format = DXGI_FORMAT_UNKNOWN, depth_format = DXGI_FORMAT_UNKNOWN;
        bool history = false;
        bool warmed = false, warming = false;
        unsigned warm_frames = 0;
        ULONGLONG warm_deadline = 0;
        ~Session()
        {
            if(context&&retired)
            {
                context->End(retired.Get());context->Flush();
                ULONGLONG const end=GetTickCount64()+250;
                while(context->GetData(retired.Get(),nullptr,0,D3D11_ASYNC_GETDATA_DONOTFLUSH)==S_FALSE&&GetTickCount64()<end)Sleep(1);
            }
            feed.Stop();
        }
        bool Init(ID3D11Device* raw, Source const& source, BaseNeuralBridge::Frame const& f)
        {
            width=f.width; height=f.height; mode=f.mode; format=source.cd.Format; depth_format=source.dd.Format;
            if (FAILED(raw->QueryInterface(IID_PPV_ARGS(&device)))) return false;
            ComPtr<ID3D11DeviceContext> immediate; raw->GetImmediateContext(&immediate);
            if (FAILED(immediate.As(&context))) return false;
            D3D11_QUERY_DESC query={D3D11_QUERY_EVENT,0};
            if(FAILED(raw->CreateQuery(&query,&retired)))return false;
            D3D_FEATURE_LEVEL level=raw->GetFeatureLevel(), chosen;
            if (FAILED(device->CreateDeviceContextState(0,&level,1,D3D11_SDK_VERSION,__uuidof(ID3D11Device),&chosen,&isolated))) return false;
            D3D11_TEXTURE2D_DESC d=source.cd;
            d.MipLevels=1; d.Usage=D3D11_USAGE_DEFAULT; d.BindFlags=D3D11_BIND_SHADER_RESOURCE; d.CPUAccessFlags=0;d.MiscFlags=0;
            if (FAILED(raw->CreateTexture2D(&d,nullptr,&color)) || FAILED(raw->CreateTexture2D(&d,nullptr,&previous))) return false;
            D3D11_SHADER_RESOURCE_VIEW_DESC sv={};sv.ViewDimension=D3D11_SRV_DIMENSION_TEXTURE2D;sv.Texture2D.MipLevels=1;sv.Format=ColorFormat(d.Format);
            if (FAILED(raw->CreateShaderResourceView(color.Get(),&sv,&color_srv)) || FAILED(raw->CreateShaderResourceView(previous.Get(),&sv,&previous_srv))) return false;
            if (mode==BaseNeuralBridge::Neural)
            {
                d=source.dd;d.MipLevels=1;d.Usage=D3D11_USAGE_DEFAULT;d.BindFlags=D3D11_BIND_SHADER_RESOURCE;d.CPUAccessFlags=0;d.MiscFlags=0;
                if(d.Format==DXGI_FORMAT_D24_UNORM_S8_UINT||d.Format==DXGI_FORMAT_R24G8_TYPELESS)
                {d.Format=DXGI_FORMAT_R24G8_TYPELESS;sv.Format=DXGI_FORMAT_R24_UNORM_X8_TYPELESS;}
                else if(d.Format==DXGI_FORMAT_D32_FLOAT||d.Format==DXGI_FORMAT_R32_TYPELESS)
                {d.Format=DXGI_FORMAT_R32_TYPELESS;sv.Format=DXGI_FORMAT_R32_FLOAT;}
                else return false;
                if(FAILED(raw->CreateTexture2D(&d,nullptr,&depth))||FAILED(raw->CreateShaderResourceView(depth.Get(),&sv,&depth_srv)))return false;
            }
            ComPtr<ID3DBlob> blob;
            if(!Compile("CopyGuides","cs_5_0",blob)||FAILED(raw->CreateComputeShader(blob->GetBufferPointer(),blob->GetBufferSize(),nullptr,&copy)))return false;
            blob.Reset();if(!Compile("Flow","cs_5_0",blob)||FAILED(raw->CreateComputeShader(blob->GetBufferPointer(),blob->GetBufferSize(),nullptr,&flow)))return false;
            blob.Reset();if(!Compile("Fullscreen","vs_5_0",blob)||FAILED(raw->CreateVertexShader(blob->GetBufferPointer(),blob->GetBufferSize(),nullptr,&vs)))return false;
            blob.Reset();if(!Compile("Composite","ps_5_0",blob)||FAILED(raw->CreatePixelShader(blob->GetBufferPointer(),blob->GetBufferSize(),nullptr,&ps)))return false;
            D3D11_BUFFER_DESC cb={};cb.ByteWidth=32;cb.Usage=D3D11_USAGE_DEFAULT;cb.BindFlags=D3D11_BIND_CONSTANT_BUFFER;
            if(FAILED(raw->CreateBuffer(&cb,nullptr,&constants)))return false;
            D3D11_RASTERIZER_DESC rs={};rs.FillMode=D3D11_FILL_SOLID;rs.CullMode=D3D11_CULL_NONE;rs.DepthClipEnable=TRUE;
            if(FAILED(raw->CreateRasterizerState(&rs,&raster)))return false;
            wchar_t path[MAX_PATH];DWORD n=GetModuleFileNameW(Module,path,MAX_PATH);
            if(!n||n>=MAX_PATH)return false;
            std::wstring directory(path);directory.resize(directory.find_last_of(L"\\/"));directory+=L"\\neural\\host64";
            if(!feed.Start(raw,width,height,mode,directory.c_str()))return false;
            unsigned const slots[]={BaseFeed::Color,BaseFeed::Depth,BaseFeed::Motion};
            for(unsigned i=0;i<3;i++)if(FAILED(raw->CreateUnorderedAccessView(feed.textures[slots[i]].Get(),nullptr,&uav[i])))return false;
            return SUCCEEDED(raw->CreateShaderResourceView(feed.textures[BaseFeed::Output].Get(),nullptr,&neural_srv));
        }
        int Process(Source const& source, BaseNeuralBridge::Frame const& f)
        {
            int ready=feed.Poll(); if(ready<0)return BaseNeuralBridge::Failed;if(!ready)return BaseNeuralBridge::Warming;
            if(warming)
            {
                int done=feed.Complete(context.Get(),0);
                if(done<0||GetTickCount64()>warm_deadline)return BaseNeuralBridge::Failed;
                if(done==1){warming=false;warmed=++warm_frames>=4;}
                // The warm-up image belongs to an older frame: never display it.
                return BaseNeuralBridge::Warming;
            }
            ComPtr<ID3DDeviceContextState> saved;
            context->SwapDeviceContextState(isolated.Get(),&saved);
            context->CopyResource(color.Get(),source.color.Get());
            if(depth)context->CopyResource(depth.Get(),source.depth.Get());
            bool const reset=f.reset||!history;
            if(reset)context->CopyResource(previous.Get(),color.Get());
            struct {unsigned w,h,reset,mode;float strength,pad[3];} cb={width,height,reset?1u:0u,mode,f.strength,{}};
            context->UpdateSubresource(constants.Get(),0,nullptr,&cb,0,0);
            ID3D11Buffer* buffers[]={constants.Get()};
            ID3D11ShaderResourceView* srvs[]={color_srv.Get(),previous_srv.Get(),depth_srv.Get()};
            ID3D11UnorderedAccessView* targets[]={uav[0].Get(),uav[1].Get(),uav[2].Get()};
            context->CSSetConstantBuffers(0,1,buffers);context->CSSetShaderResources(0,3,srvs);context->CSSetUnorderedAccessViews(0,3,targets,nullptr);
            context->CSSetShader(copy.Get(),nullptr,0);context->Dispatch((width+7)/8,(height+7)/8,1);
            context->CSSetShader(flow.Get(),nullptr,0);context->Dispatch((width+31)/32,(height+31)/32,1);
            ID3D11UnorderedAccessView* empty_uav[3]={};ID3D11ShaderResourceView* empty_srv[3]={};
            context->CSSetUnorderedAccessViews(0,3,empty_uav,nullptr);context->CSSetShaderResources(0,3,empty_srv);
            bool ok=false;
            if(!warmed)
            {
                warming=feed.Submit(context.Get(),true,f.timeout_ms);
                warm_deadline=GetTickCount64()+60000;
            }
            else ok=feed.Evaluate(context.Get(),reset,f.timeout_ms);
            if(ok)
            {
                ID3D11RenderTargetView* target=source.rtv.Get();context->OMSetRenderTargets(1,&target,nullptr);
                D3D11_VIEWPORT vp={0,0,static_cast<float>(width),static_cast<float>(height),0,1};context->RSSetViewports(1,&vp);context->RSSetState(raster.Get());
                context->VSSetShader(vs.Get(),nullptr,0);context->PSSetShader(ps.Get(),nullptr,0);context->PSSetConstantBuffers(0,1,buffers);
                ID3D11ShaderResourceView* views[]={color_srv.Get(),nullptr,nullptr,neural_srv.Get()};context->PSSetShaderResources(0,4,views);
                context->IASetPrimitiveTopology(D3D11_PRIMITIVE_TOPOLOGY_TRIANGLELIST);context->Draw(3,0);
                context->CopyResource(previous.Get(),color.Get());history=true;
            }
            else history=false;
            // Reset our context state before parking it, so it does not retain the game's RTV.
            context->ClearState();context->SwapDeviceContextState(saved.Get(),nullptr);
            return warming?BaseNeuralBridge::Warming:ok?BaseNeuralBridge::Applied:BaseNeuralBridge::Failed;
        }
    };
    std::unique_ptr<Session> Active;
    void Stop()
    {
        Active.reset();Faulted=false;
        Log("BaseNeural: stopped; no owned helper, guides or history remain");
    }
    int32_t ProcessImpl(BaseNeuralBridge::Frame const* f)
    {
        if(!f||f->size!=sizeof(*f)||f->version!=BaseNeuralBridge::Version||!f->base||!f->room||
           f->width<1||f->height<1||f->width>8192||f->height>8192||f->timeout_ms<1||f->timeout_ms>250||
           (f->mode!=1&&f->mode!=2)||!std::isfinite(f->strength)||f->strength<0||f->strength>1)return BaseNeuralBridge::Failed;
        if(Faulted)return BaseNeuralBridge::Failed;
        if(!TrackedDevice)return BaseNeuralBridge::Unavailable;
        if(f->mode==BaseNeuralBridge::Neural&&!NvidiaAdapter)return BaseNeuralBridge::Unavailable;
        ComPtr<ID3D11DeviceContext> context;TrackedDevice->GetImmediateContext(&context);
        Source source;if(!source.Get(context.Get(),*f))return BaseNeuralBridge::Unavailable;
        if(Active&&(Active->width!=f->width||Active->height!=f->height||Active->mode!=f->mode||
                    Active->format!=source.cd.Format||Active->depth_format!=source.dd.Format))Stop();
        if(!Active)
        {
            Active=std::make_unique<Session>();
            if(!Active->Init(TrackedDevice,source,*f)){Active.reset();Faulted=true;Log("BaseNeural: initialization failed; original frame retained");return BaseNeuralBridge::Failed;}
            Log("BaseNeural: base session started; helper initializing asynchronously");
        }
        int result=Active->Process(source,*f);
        if(result==BaseNeuralBridge::Failed){Active.reset();Faulted=true;Log("BaseNeural: frame failed; session stopped until next base entry");}
        return result;
    }
    int32_t Process(BaseNeuralBridge::Frame const* f)
    {
        try { return ProcessImpl(f); }
        catch (...) { Active.reset();Faulted=true;Log("BaseNeural: exception contained; original frame retained");return BaseNeuralBridge::Failed; }
    }
    void OnInitDevice(reshade::api::device* device)
    {
        if(device->get_api()==reshade::api::device_api::d3d11&&!TrackedDevice){
            TrackedDevice=reinterpret_cast<ID3D11Device*>(device->get_native());
            ComPtr<IDXGIDevice> dxgi;ComPtr<IDXGIAdapter> adapter;DXGI_ADAPTER_DESC desc={};
            NvidiaAdapter=SUCCEEDED(TrackedDevice->QueryInterface(IID_PPV_ARGS(&dxgi)))&&
                SUCCEEDED(dxgi->GetAdapter(&adapter))&&SUCCEEDED(adapter->GetDesc(&desc))&&desc.VendorId==0x10de;
            if(!NvidiaAdapter)Log("BaseNeural: non-NVIDIA/unknown adapter; neural helper disabled, original scene retained");
        }
    }
    void OnDestroyDevice(reshade::api::device* device)
    {
        if(reinterpret_cast<void*>(device->get_native())==TrackedDevice){Stop();TrackedDevice=nullptr;NvidiaAdapter=false;}
    }
    bool PreventOverlay(reshade::api::effect_runtime*, bool open, reshade::api::input_source)
    {
        return open;
    }
    void HideSplash(reshade::api::effect_runtime*)
    {
        // ReShade 6.8 has no INI switch for its startup/update banner. This
        // documented overlay callback runs after its windows and before Render.
        // Append to that window and discard only its draw commands. ImGui drops
        // the empty command list, so no banner geometry is submitted to the GPU.
        ImGui::Begin("Splash Window", nullptr, ImGuiWindowFlags_NoDecoration |
            ImGuiWindowFlags_NoInputs | ImGuiWindowFlags_NoNav | ImGuiWindowFlags_NoSavedSettings |
            ImGuiWindowFlags_NoDocking | ImGuiWindowFlags_NoFocusOnAppearing);
        ImDrawList* draw = ImGui::GetWindowDrawList();
        ImGui::End();
        for (ImDrawCmd& cmd : draw->CmdBuffer) { cmd.ElemCount = 0; cmd.UserCallback = nullptr; }
    }
}
extern "C" __declspec(dllexport) char const* NAME="Freelancer Base Neural Render";
extern "C" __declspec(dllexport) char const* DESCRIPTION="Engine-controlled base interiors only; private acknowledged GPU transport";
extern "C" __declspec(dllexport) BaseNeuralBridge::Api const* __cdecl FlBaseNeuralGetApi(uint32_t version)
{
    static BaseNeuralBridge::Api const api={sizeof(api),BaseNeuralBridge::Version,Process,Stop};
    return version==BaseNeuralBridge::Version?&api:nullptr;
}
#pragma comment(linker,"/EXPORT:FlBaseNeuralGetApi=_FlBaseNeuralGetApi")
BOOL WINAPI DllMain(HMODULE module,DWORD reason,LPVOID)
{
    if(reason==DLL_PROCESS_ATTACH)
    {
        Module=module;DisableThreadLibraryCalls(module);
        if(!reshade::register_addon(module))return FALSE;
        reshade::register_event<reshade::addon_event::init_device>(OnInitDevice);
        reshade::register_event<reshade::addon_event::destroy_device>(OnDestroyDevice);
        reshade::register_event<reshade::addon_event::reshade_open_overlay>(PreventOverlay);
        reshade::register_event<reshade::addon_event::reshade_overlay>(HideSplash);
    }
    else if(reason==DLL_PROCESS_DETACH)
    {
        // Engine/device lifecycle must Stop outside the loader lock. Job Object also
        // terminates the helper on process exit. Never join a worker from DllMain.
        Active.release();
        reshade::unregister_event<reshade::addon_event::init_device>(OnInitDevice);
        reshade::unregister_event<reshade::addon_event::destroy_device>(OnDestroyDevice);
        reshade::unregister_event<reshade::addon_event::reshade_open_overlay>(PreventOverlay);
        reshade::unregister_event<reshade::addon_event::reshade_overlay>(HideSplash);
        reshade::unregister_addon(module);
    }
    return TRUE;
}
