// Art studies only. Reuse the live corridor mesh/noise and standalone D3D9 harness.
#define main ExistingTradeLaneChecks
#include "../check_tradelane_render.cpp"
#undef main
#include <io.h>
#include <fcntl.h>

int main(int argc,char** argv){
    if(argc!=4)return 1;
    ShaderSource=argv[1];Out=argv[2];bool video=strcmp(argv[3],"video")==0;
    if(video)_setmode(_fileno(stdout),_O_BINARY);
    SetErrorMode(SEM_FAILCRITICALERRORS|SEM_NOGPFAULTERRORBOX);
    HWND window=CreateWindowA("STATIC","Tradelane band study",WS_POPUP,0,0,64,64,nullptr,nullptr,GetModuleHandle(nullptr),nullptr);
    auto* api=Direct3DCreate9(D3D_SDK_VERSION);if(!api)return 2;
    D3DPRESENT_PARAMETERS pp={};pp.Windowed=TRUE;pp.SwapEffect=D3DSWAPEFFECT_DISCARD;
    pp.BackBufferWidth=64;pp.BackBufferHeight=64;pp.BackBufferFormat=D3DFMT_A8R8G8B8;
    Check(api->CreateDevice(0,D3DDEVTYPE_HAL,window,D3DCREATE_HARDWARE_VERTEXPROCESSING,&pp,&Dev));
    // Shader-cache diagnostics must not enter the raw BGRA video stream.
    int savedOutput=video?_dup(_fileno(stdout)):-1;
    if(video){fflush(stdout);_dup2(_fileno(stderr),_fileno(stdout));}
    Compile();
    if(video){fflush(stdout);_dup2(savedOutput,_fileno(stdout));_close(savedOutput);_setmode(_fileno(stdout),_O_BINARY);}
    CreateNoise();Beauty=true;Size(960,540);
    Mesh.resize(TradeLaneVertexCount);BuildTradeLaneVisualMesh(Mesh.data());
    Check(Dev->CreateVertexBuffer(UINT(Mesh.size()*sizeof(Vertex)),D3DUSAGE_WRITEONLY,0,D3DPOOL_MANAGED,&VB,nullptr));
    void* vertices=nullptr;Check(VB->Lock(0,0,&vertices,0));memcpy(vertices,Mesh.data(),Mesh.size()*sizeof(Vertex));Check(VB->Unlock());
    Dev->SetRenderState(D3DRS_CULLMODE,D3DCULL_NONE);Dev->SetRenderState(D3DRS_ZENABLE,TRUE);
    Dev->SetRenderState(D3DRS_ZWRITEENABLE,FALSE);Dev->SetRenderState(D3DRS_ZFUNC,D3DCMP_LESSEQUAL);
    Dev->SetRenderState(D3DRS_ALPHATESTENABLE,FALSE);Dev->SetRenderState(D3DRS_ALPHABLENDENABLE,TRUE);
    Dev->SetRenderState(D3DRS_SRCBLEND,D3DBLEND_ONE);Dev->SetRenderState(D3DRS_DESTBLEND,D3DBLEND_INVSRCALPHA);
    Dev->SetRenderState(D3DRS_BLENDOP,D3DBLENDOP_ADD);Dev->SetRenderState(D3DRS_LIGHTING,FALSE);
    Camera();
    // Identical camera, distance clock and background for all four art variants.
    // Stable flight, with a short entry/exit at either end of an eight-second clip.
    for(int frame=0;frame<(video?480:1);++frame){
        float t=video?frame/60.f:2.5f;
        auto smooth=[](float x){x=std::max(0.f,std::min(1.f,x));return x*x*(3-2*x);};
        float exitProgress=std::max(0.f,(t-7.f));
        float envelope=smooth(t/.45f)*(1-smooth(exitProgress));
        Params(t*.9f,envelope,0,t,std::min(t,2.f),exitProgress,exitProgress>0);
        auto pixels=Render(video?nullptr:"preview",true);
        if(video&&fwrite(pixels.data(),4,pixels.size(),stdout)!=pixels.size())return 3;
        if(!video){auto paused=Render(nullptr,true);if(paused!=pixels)return 4;}
    }
    Release(Noise);Release(VB);Release(SceneColor);Release(SceneDepth);Release(Warp);Release(Background);
    Release(White);Release(VS);Release(PS);Release(Target);Release(Cpu);Release(Depth);Release(Dev);Release(api);DestroyWindow(window);
    fprintf(stderr,"PASS: %s preview\n",video?"480-frame":"paused-frame");return 0;
}
