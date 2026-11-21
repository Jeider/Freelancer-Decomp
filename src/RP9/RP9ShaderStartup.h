#pragma once
#include "RP9ShaderManifest.h"
#include "RP9ShaderStartupWindow.h"
#include <atomic>
#include <thread>
#include <algorithm>
#include <functional>

namespace Rp9Startup {
struct Result {
    HRESULT Hr=E_PENDING;
    bool Hit=false;
    std::vector<unsigned char> Code;
    std::string Message;
};

// No D3D calls on workers. Every worker is joined before returning, including cancellation.
inline bool Prepare(const std::vector<FJob>& Jobs, const std::string& Directory,
    std::vector<Result>& Results, const std::function<bool(unsigned,unsigned)>& Progress) {
    Results.resize(Jobs.size());
    std::atomic<size_t> Next{0};
    std::atomic<unsigned> Done{0};
    std::atomic<unsigned> Cached{0};
    std::atomic<bool> Cancel{false};
    std::vector<std::thread> Workers;
    const unsigned Count=(std::min)(4u,(std::max)(1u,std::thread::hardware_concurrency()/2));
    try {
        for(unsigned i=0;i<Count;++i) Workers.emplace_back([&]() {
            while(!Cancel.load()) {
                const size_t Index=Next.fetch_add(1);
                if(Index>=Jobs.size()) break;
                auto& R=Results[Index];
                try { R.Hr=Compile(Jobs[Index],Directory,R.Code,R.Message,R.Hit); }
                catch(...) { R.Hr=E_OUTOFMEMORY; }
                if(SUCCEEDED(R.Hr)) ++Cached;
                ++Done;
            }
        });
        while(Done.load()<Jobs.size()) {
            if(!Progress(Cached.load(),(unsigned)Jobs.size())) {Cancel=true;break;}
            Sleep(10);
        }
    } catch(...) {Cancel=true;}
    for(auto& Worker:Workers) Worker.join();
    if(Cancel) return false;
    return Progress(Cached.load(),(unsigned)Jobs.size());
}

inline HRESULT Validate(IDirect3DDevice9* Device, const FJob& Job, const Result& R) {
    if(FAILED(R.Hr)) return R.Hr;
    if(R.Code.empty()) return E_FAIL;
    HRESULT Hr;
    if(Job.Profile[0]=='v') {
        IDirect3DVertexShader9* Shader=nullptr;
        Hr=Device->CreateVertexShader(reinterpret_cast<const DWORD*>(R.Code.data()),&Shader);
        if(Shader) Shader->Release();
    } else {
        IDirect3DPixelShader9* Shader=nullptr;
        Hr=Device->CreatePixelShader(reinterpret_cast<const DWORD*>(R.Code.data()),&Shader);
        if(Shader) Shader->Release();
    }
    return Hr;
}

struct Gate {
    bool Presented=false;
    bool Ready=false;
    HRESULT Status=E_PENDING;
    std::string Error;
    std::vector<FJob> Jobs;
    std::vector<Result> Results;
};
inline Gate& StartupGate() { static Gate G; return G; }

inline void ReportBlocked(HWND Owner, const std::string& Error,
    const std::function<void(const std::string&)>& Log) {
    Log("Shader startup BLOCKED: "+Error);
    MessageBoxA(Owner,("The game cannot start because required shaders are not ready.\n\n"+
        Error+"\n\nSee the RP9 game log for details. Fix the cause and restart; successfully cached shaders are retained.").c_str(),
        "Freelancer - Shader preparation failed",MB_OK|MB_ICONERROR);
}

// Animation and disk cache. No device, so this can finish before the game window is shown.
inline HRESULT Present(const std::function<void(const std::string&)>& Log) {
    Gate& G=StartupGate();
    if(G.Ready) return S_OK;
    if(G.Presented) return G.Status;
    std::string Directory;
    char Module[MAX_PATH]={};
    DWORD Length=GetModuleFileNameA(nullptr,Module,MAX_PATH);
    char* Slash=strrchr(Module,'\\');
    if(Length && Length<MAX_PATH && Slash) {
        Slash[1]=0;Directory=std::string(Module)+"../DATA_EXTRA/SHADERS/";
    }
    G.Status=E_FAIL;
    if(Directory.empty()) G.Error="Cannot resolve the game's shader directory.";
    else if(Build(Directory,G.Jobs,G.Error)) {
        G.Results.resize(G.Jobs.size());
        bool NeedsCompile=false;
        for(size_t i=0;i<G.Jobs.size();++i) {
            auto& R=G.Results[i];
            R.Hr=Compile(G.Jobs[i],Directory,R.Code,R.Message,R.Hit,true);
            if(R.Hr==S_FALSE) NeedsCompile=true;
            else if(FAILED(R.Hr)) {
                G.Status=R.Hr;
                G.Error=R.Message.empty()?"cache/compile FAILED":R.Message;
                ReportBlocked(nullptr,G.Error,Log);
                G.Presented=true;
                return G.Status;
            }
        }
        if(!NeedsCompile) {
            G.Status=S_OK;
            G.Presented=true;
            return S_OK;
        }
        Window Progress;
        if(!Prepare(G.Jobs,Directory,G.Results,[&](unsigned D,unsigned T){return Progress.Update(D,T);})) {
            G.Presented=true;
            G.Status=HRESULT_FROM_WIN32(ERROR_CANCELLED);
            return G.Status;
        }
        G.Status=S_OK;
        for(auto const& R: G.Results) if(FAILED(R.Hr)) {
            G.Status=R.Hr;
            if(G.Error.empty()) G.Error=R.Message.empty()?"cache/compile FAILED":R.Message;
            break;
        }
        if(FAILED(G.Status)) ReportBlocked(Progress.Get(),G.Error,Log);
    }
    if(FAILED(G.Status) && G.Error.size() && !G.Presented)
        ReportBlocked(nullptr,G.Error,Log);
    G.Presented=true;
    return G.Status;
}

inline HRESULT Run(IDirect3DDevice9* Device,
    const std::function<void(const std::string&)>& Log) {
    // Device resets must not open another startup window (activation can itself cause a reset).
    Gate& G=StartupGate();
    if(G.Ready) return S_OK;
    if(!G.Presented) {
        const HRESULT Shown=Present(Log);
        if(FAILED(Shown)) return Shown;
    }
    if(FAILED(G.Status)) return G.Status;
    HRESULT Status=S_OK;
    std::string Error;
    for(size_t i=0;i<G.Jobs.size();++i) {
        auto const& J=G.Jobs[i];auto const& R=G.Results[i];
        HRESULT Hr=Validate(Device,J,R);
        char Code[32];sprintf_s(Code,"0x%08lx",(unsigned long)Hr);
        std::string Line=J.Name+" "+J.Entry+" "+J.Profile+": "+
            (FAILED(R.Hr)?"cache/compile FAILED ":FAILED(Hr)?"GPU rejected shader ":R.Hit?"cache HIT ":"cache stored and verified ")+Code;
        Log(Line);
        if(!R.Message.empty()) Log(R.Message);
        if(FAILED(Hr)) {
            Status=Hr;
            if(Error.empty()) Error=Line+"\n"+R.Message;
        }
    }
    if(FAILED(Status)) {
        ReportBlocked(nullptr,Error,Log);
        G.Status=Status;
        return Status;
    }
    G.Ready=true;
    G.Jobs.clear();
    G.Results.clear();
    Log("Shader startup READY: every manifest stage is cached and accepted by the current GPU.");
    return S_OK;
}
}
