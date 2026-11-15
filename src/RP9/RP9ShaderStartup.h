#pragma once
#include "RP9ShaderManifest.h"
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
            Sleep(30);
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

class Window {
    HWND Handle=nullptr, Label=nullptr;
    bool Cancelled=false;
    bool Russian=false;
    ULONGLONG Started=GetTickCount64();
    static LRESULT CALLBACK Proc(HWND H,UINT M,WPARAM W,LPARAM L) {
        auto* Self=reinterpret_cast<Window*>(GetWindowLongPtrW(H,GWLP_USERDATA));
        if(M==WM_NCCREATE) {
            Self=static_cast<Window*>(reinterpret_cast<CREATESTRUCTW*>(L)->lpCreateParams);
            SetWindowLongPtrW(H,GWLP_USERDATA,reinterpret_cast<LONG_PTR>(Self));
        }
        if(M==WM_MOUSEACTIVATE) return MA_NOACTIVATE;
        if(M==WM_CLOSE && Self) {
            Self->Cancelled=true;
            SetWindowTextW(Self->Label,Self->Russian ? L"\u041e\u0442\u043c\u0435\u043d\u0430. \u041e\u0436\u0438\u0434\u0430\u043d\u0438\u0435 \u043a\u043e\u043c\u043f\u0438\u043b\u044f\u0442\u043e\u0440\u043e\u0432..." : L"Cancelling. Waiting for active shader compilers...");
            return 0;
        }
        return DefWindowProcW(H,M,W,L);
    }
public:
    Window() {
        char Path[MAX_PATH]={},Language[16]={};
        DWORD Length=GetModuleFileNameA(nullptr,Path,MAX_PATH);
        if(char* Slash=Length && Length<MAX_PATH ? strrchr(Path,'\\') : nullptr) {
            strcpy(Slash+1,"port.ini");
            GetPrivateProfileStringA("Language","language","",Language,sizeof(Language),Path);
        }
        if(const char* Switch=strstr(GetCommandLineA(),"-lang"))
            strncpy(Language,Switch[5]?Switch+6:"",2);
        Russian=_strnicmp(Language,"ru",2)==0;
        WNDCLASSW C={}; C.lpfnWndProc=Proc; C.hInstance=GetModuleHandleW(nullptr);
        C.hCursor=LoadCursor(nullptr,IDC_ARROW);C.hbrBackground=(HBRUSH)(COLOR_WINDOW+1);
        C.lpszClassName=L"FreelancerShaderStartup";
        RegisterClassW(&C);
        Handle=CreateWindowExW(WS_EX_TOPMOST|WS_EX_NOACTIVATE,C.lpszClassName,L"Freelancer - Preparing shaders",
            WS_OVERLAPPED|WS_CAPTION|WS_SYSMENU,CW_USEDEFAULT,CW_USEDEFAULT,560,140,
            nullptr,nullptr,C.hInstance,this);
        Label=CreateWindowW(L"STATIC",L"Checking required shaders and persistent cache...",
            WS_CHILD|WS_VISIBLE,20,25,510,70,Handle,nullptr,C.hInstance,nullptr);
        ShowWindow(Handle,SW_SHOWNOACTIVATE);UpdateWindow(Handle);
    }
    ~Window() {if(Handle) DestroyWindow(Handle);}
    bool Update(unsigned Done,unsigned Total) {
        if(!Handle || !Label) return false;
        wchar_t Text[256];
        swprintf_s(Text,Russian ? L"\u041a\u044d\u0448\u0438\u0440\u043e\u0432\u0430\u043d\u0438\u0435 \u0448\u0435\u0439\u0434\u0435\u0440\u043e\u0432: %u / %u\n\u0418\u0433\u0440\u0430 \u0437\u0430\u043f\u0443\u0441\u0442\u0438\u0442\u0441\u044f \u043f\u043e\u0441\u043b\u0435 \u043f\u043e\u0434\u0433\u043e\u0442\u043e\u0432\u043a\u0438." : L"Preparing shader cache: %u / %u\nThe game starts only after all shaders are ready.",Done,Total);
        if(!Cancelled) SetWindowTextW(Label,Text);
        if(!Cancelled) {
            wchar_t Status[128];
            swprintf_s(Status,L"Freelancer - Preparing shaders (%llu s)",(GetTickCount64()-Started)/1000);
            SetWindowTextW(Handle,Status);
        }
        MSG M;
        // Filter queued game messages. Sent activation messages can still run here;
        // the caller must finish this gate before creating device-dependent resources.
        while(PeekMessageW(&M,Handle,0,0,PM_REMOVE)) {
            if(M.message==WM_QUIT) {Cancelled=true;PostQuitMessage((int)M.wParam);break;}
            TranslateMessage(&M);DispatchMessageW(&M);
        }
        return !Cancelled;
    }
    HWND Get() const {return Handle;}
};

inline HRESULT Run(IDirect3DDevice9* Device,
    const std::function<void(const std::string&)>& Log) {
    // Device resets must not open another startup window (activation can itself cause a reset).
    static bool Ready=false;
    if(Ready) return S_OK;
    Window Progress;
    std::string Error,Directory;
    char Module[MAX_PATH]={};
    DWORD Length=GetModuleFileNameA(nullptr,Module,MAX_PATH);
    char* Slash=strrchr(Module,'\\');
    if(Length && Length<MAX_PATH && Slash) {
        Slash[1]=0;Directory=std::string(Module)+"../DATA_EXTRA/SHADERS/";
    }
    std::vector<FJob> Jobs;
    std::vector<Result> Results;
    HRESULT Status=E_FAIL;
    if(Directory.empty()) Error="Cannot resolve the game's shader directory.";
    else if(Build(Directory,Jobs,Error)) {
        if(!Prepare(Jobs,Directory,Results,[&](unsigned D,unsigned T){return Progress.Update(D,T);}))
            return HRESULT_FROM_WIN32(ERROR_CANCELLED);
        Status=S_OK;
        for(size_t i=0;i<Jobs.size();++i) {
            auto const& J=Jobs[i];auto const& R=Results[i];
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
    }
    if(FAILED(Status)) {
        Log("Shader startup BLOCKED: "+Error);
        MessageBoxA(Progress.Get(),("The game cannot start because required shaders are not ready.\n\n"+
            Error+"\n\nSee the RP9 game log for details. Fix the cause and restart; successfully cached shaders are retained.").c_str(),
            "Freelancer - Shader preparation failed",MB_OK|MB_ICONERROR);
    } else {
        Ready=true;
        Log("Shader startup READY: every manifest stage is cached and accepted by the current GPU.");
    }
    return Status;
}
}
