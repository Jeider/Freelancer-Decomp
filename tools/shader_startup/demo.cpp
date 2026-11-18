#include "RP9ShaderStartupWindow.h"
#include <shellapi.h>
#include <stdexcept>
#include <cstdio>

static void Require(bool Value,const char* Message) {if(!Value) throw std::runtime_error(Message);}
static uint32_t Hash(const std::vector<BYTE>& Data) {
    uint32_t H=2166136261u;for(BYTE B:Data) {H^=B;H*=16777619u;}return H;
}
static int Check() {
    FILE* Log=_wfopen(L"animation_check.txt",L"wb");
    if(!Log) return 2;
    try {
        HMODULE Module=GetModuleHandleW(nullptr);
        HRSRC Resource=FindResourceW(Module,L"FREELANCER_SHADER_ANIMATION",MAKEINTRESOURCEW(10));
        Require(Resource!=nullptr,"embedded resource missing");
        const DWORD Size=SizeofResource(Module,Resource);
        const auto* Data=(const BYTE*)LockResource(LoadResource(Module,Resource));
        Rp9Startup::Animation Movie;
        Require(Movie.OpenResource(),"embedded JPEG decoder failed");
        Require(Movie.FrameCount()==361,"frame count");
        const uint32_t First=Hash(Movie.FramePixels());
        LARGE_INTEGER Frequency,Start,End;QueryPerformanceFrequency(&Frequency);QueryPerformanceCounter(&Start);
        bool Changed=false;
        for(DWORD i=1;i<Movie.FrameCount();++i) {
            Require(Movie.Decode(i),"frame decode failed");
            if(i==180) Changed=First!=Hash(Movie.FramePixels());
        }
        QueryPerformanceCounter(&End);
        Require(Changed,"static picture instead of animation");
        Require(Movie.FrameAt(15000)==360 && Movie.FrameAt(15042)==0,"loop timing");
        Require(Movie.Advance(15042) && Hash(Movie.FramePixels())==First,"loop returns first frame");
        const double Ms=1000.0*(End.QuadPart-Start.QuadPart)/Frequency.QuadPart;
        fprintf(Log,"PASS embedded resource: %lu bytes, 361 frames, 480x480, 24 fps, no audio\n",Size);
        fprintf(Log,"PASS all JPEG frames decode; changing pixels; seamless timing wrap; %.3f ms/frame\n",Ms/360);
        Require(!Movie.Open(Data,Size,CLSID_NULL) && !Movie.Available(),"unavailable decoder must disable animation");
        Require(!Movie.OpenResource(GetModuleHandleW(L"kernel32.dll")),"missing resource must be optional");
        Require(!Movie.Open(Data,10),"truncated resource accepted");
        std::vector<BYTE> Bad(Data,Data+Size);Bad[0]=0;
        Require(!Movie.Open(Bad.data(),Size),"invalid resource accepted");
        Bad.assign(Data,Data+Size);
        DWORD A,B;memcpy(&A,Bad.data()+32,4);memcpy(&B,Bad.data()+36,4);
        memset(Bad.data()+A+2,0,B-A-2);
        Require(Movie.Open(Bad.data(),Size),"first good frame should decode");
        Movie.Advance(42);
        Require(!Movie.Available(),"late decoder failure must disable animation");
        fprintf(Log,"PASS missing codec/resource, truncated/corrupt resource, late decode failure\n");
        {
            Rp9Startup::Window Plain(false,true,false);
            Require(Plain.Get() && !Plain.HasAnimation() && Plain.Update(50,100),"plain progress fallback");
            SendMessageW(Plain.Get(),WM_CLOSE,0,0);
            Require(!Plain.Update(60,100),"close/cancel fallback");
        }
        {
            Rp9Startup::Window Window(false,true);
            Require(Window.Get() && Window.HasAnimation() && Window.Update(50,100),"animated window");
            Require(SendMessageW(Window.Get(),WM_MOUSEACTIVATE,0,0)==MA_NOACTIVATE,"activation changed");
            SendMessageW(Window.Get(),WM_CLOSE,0,0);
            Require(!Window.Update(60,100),"close/cancel animated");
        }
        fprintf(Log,"PASS animated and plain windows; progress, nonactivation and close/cancel\n");
        fclose(Log);return 0;
    } catch(const std::exception& E) {fprintf(Log,"FAIL %s\n",E.what());fclose(Log);return 1;}
}

int WINAPI wWinMain(HINSTANCE,HINSTANCE,PWSTR,int) {
    int Count=0;LPWSTR* Args=CommandLineToArgvW(GetCommandLineW(),&Count);
    bool Test=false,Plain=false;
    for(int i=1;i<Count;++i) {Test|=wcscmp(Args[i],L"--check")==0;Plain|=wcscmp(Args[i],L"--plain")==0;}
    LocalFree(Args);
    if(Test) return Check();
    Rp9Startup::Window Window(true,true,!Plain);
    if(!Window.Get()) return 1;
    const ULONGLONG Started=GetTickCount64();
    // A repeating 45-second simulation stays open for review until the user closes it.
    while(Window.Update((unsigned)(((GetTickCount64()-Started)%45000)*128/45000),128)) Sleep(10);
    return 0;
}
