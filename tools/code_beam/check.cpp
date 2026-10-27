#include "RP9ShaderCache.h"
#include <cstdio>
#include <cstdlib>
#include <cmath>
#include "../../src/freelancer/Client/code_beam_flow.h"

static void Require(bool Ok,const char* Why){if(!Ok){printf("FAIL: %s\n",Why);exit(3);}}
static void Check(HRESULT Hr){if(FAILED(Hr)){printf("HRESULT %08lx\n",Hr);exit(2);}}
struct Vertex { float X,Y,Z; DWORD Colour; float U,V; float LocalX=0,LocalY=0,Along=0,Phase=0; };
static_assert(sizeof(Vertex)==sizeof(FCodeBeamVertex), "production beam stride");
int main()
{
    setvbuf(stdout,nullptr,_IONBF,0);
    // Production CPU metadata: local flow must follow a rotated/translated projectile,
    // not world axes or the discontinuous atlas UVs. Adjacent segment copies agree.
    const float Transform[12]={0,0,1,0,1,0,-1,0,0,1000,2000,-3000};
    FEffectVertex Input[5]={};FCodeBeamVertex Output[5];
    const float Local[5][3]={{0,0,-10},{0,0,30},{1,0,0},{0,1,0},{0,0,30}};
    for(int I=0;I<5;++I){Input[I].X=1000+Local[I][2];Input[I].Y=2000+Local[I][1];
        Input[I].Z=-3000-Local[I][0];Input[I].U=I==4 ? .25f : 0;}
    CodeBeamFlow::Fill(Input,Output,5,Transform,12345);
    Require(std::fabs(Output[0].Along+.25f)<.0001f && std::fabs(Output[1].Along-.75f)<.0001f,
            "flow axis follows rotated projectile and covers full authored length");
    Require(std::fabs(Output[2].LocalX-1)<.0001f && std::fabs(Output[3].LocalY-1)<.0001f,
            "crossed planes share beam-local width coordinates");
    Require(Output[1].Along==Output[4].Along && Output[0].Phase==Output[4].Phase,"segment seams share flow and seed");
    float FirstPhase=Output[0].Phase;CodeBeamFlow::Fill(Input,Output,5,Transform,54321);
    Require(FirstPhase!=Output[0].Phase,"different projectiles do not pulse in lockstep");
    HWND Window=CreateWindowA("STATIC","beam GPU check",WS_POPUP,0,0,64,64,0,0,GetModuleHandle(0),0);
    auto* Api=Direct3DCreate9(D3D_SDK_VERSION);Require(Api!=nullptr,"D3D9");
    D3DPRESENT_PARAMETERS PP={};PP.Windowed=1;PP.SwapEffect=D3DSWAPEFFECT_DISCARD;
    PP.BackBufferWidth=PP.BackBufferHeight=64;PP.BackBufferFormat=D3DFMT_A8R8G8B8;
    PP.EnableAutoDepthStencil=TRUE;PP.AutoDepthStencilFormat=D3DFMT_D24S8;
    IDirect3DDevice9* D=nullptr;
    Check(Api->CreateDevice(0,D3DDEVTYPE_HAL,Window,D3DCREATE_HARDWARE_VERTEXPROCESSING,&PP,&D));
    FILE* F=fopen("DATA_EXTRA/SHADERS/code_beam.hlsl","rb");Require(F!=nullptr,"production shader file");
    std::string Source;char Buffer[4096];size_t N;
    while((N=fread(Buffer,1,sizeof(Buffer),F)))Source.append(Buffer,N);fclose(F);
    auto Compile=[&](const char* Entry,const char* Profile){
        std::vector<unsigned char> Code;std::string Errors;bool Hit=false,Stored=false;
        HRESULT Hr=Rp9ShaderCache::Compile(Source,nullptr,Entry,Profile,0,&Code,&Errors,&Hit,&Stored);
        if(FAILED(Hr))puts(Errors.c_str());Check(Hr);
        ID3DXBuffer* Text=nullptr;Check(D3DXDisassembleShader((DWORD*)Code.data(),FALSE,nullptr,&Text));
        std::string Assembly((char*)Text->GetBufferPointer());Text->Release();
        printf("%s: %zu bytes\n",Entry,Code.size());
        if(!strcmp(Entry,"PSMain")){
            size_t First=Assembly.find("texld ");
            Require(First!=std::string::npos && Assembly.find("texld ",First+1)==std::string::npos,
                    "exactly one texture fetch in pixel shader");
        }
        return Code;
    };
    auto V=Compile("VSMain","vs_3_0"),P=Compile("PSMain","ps_3_0");
    IDirect3DVertexShader9* VS=nullptr;IDirect3DPixelShader9* PS=nullptr;
    Check(D->CreateVertexShader((DWORD*)V.data(),&VS));Check(D->CreatePixelShader((DWORD*)P.data(),&PS));
    IDirect3DTexture9* Atlas=nullptr;Check(D->CreateTexture(1,1,1,0,D3DFMT_A8R8G8B8,D3DPOOL_MANAGED,&Atlas,0));
    auto Texel=[&](DWORD Colour){D3DLOCKED_RECT Lock;Check(Atlas->LockRect(0,&Lock,0,0));
        *(DWORD*)Lock.pBits=Colour;Check(Atlas->UnlockRect(0));};
    D3DXMATRIX Identity;D3DXMatrixIdentity(&Identity);
    const DWORD BeamFvf=D3DFVF_XYZ|D3DFVF_DIFFUSE|D3DFVF_TEX2|D3DFVF_TEXCOORDSIZE4(1);
    static_assert((D3DFVF_XYZ|D3DFVF_DIFFUSE|D3DFVF_TEX2|D3DFVF_TEXCOORDSIZE4(1))==0x80242,"client/RP9 FVF");
    D->SetVertexShader(VS);D->SetPixelShader(PS);D->SetFVF(BeamFvf);
    D->SetVertexShaderConstantF(0,(float*)&Identity,4);D->SetVertexShaderConstantF(4,(float*)&Identity,4);
    D->SetTexture(0,Atlas);D->SetRenderState(D3DRS_CULLMODE,D3DCULL_NONE);
    D->SetRenderState(D3DRS_ZENABLE,TRUE);D->SetRenderState(D3DRS_ZWRITEENABLE,FALSE);
    D->SetRenderState(D3DRS_ZFUNC,D3DCMP_LESSEQUAL);D->SetRenderState(D3DRS_ALPHABLENDENABLE,TRUE);
    D->SetRenderState(D3DRS_SRCBLEND,D3DBLEND_ONE);D->SetRenderState(D3DRS_DESTBLEND,D3DBLEND_ONE);
    IDirect3DSurface9 *RT=nullptr,*Read=nullptr;Check(D->GetRenderTarget(0,&RT));
    Check(D->CreateOffscreenPlainSurface(64,64,D3DFMT_A8R8G8B8,D3DPOOL_SYSTEMMEM,&Read,0));
    // Sample inside a trail cell (the atlas centre .5,.5 is a head-cell border).
    Vertex Quad[]={{-1,-1,.5f,0xff406080,.05f,.9f},{-1,1,.5f,0xff406080,.05f,.6f},
                   {1,-1,.5f,0xff406080,.15f,.9f},{1,1,.5f,0xff406080,.15f,.6f}};
    for(auto& X:Quad){X.LocalX=X.Y*.4f;X.Along=(X.X+1)*.25f;X.Phase=.17f;}
    float C[8]={0,1,0,0,0,1,1,0}; // static optical checks first, animated checks below
    auto Render=[&](DWORD Bg=0xff000000,float Depth=1.0f,bool Twice=false){
        Check(D->Clear(0,0,D3DCLEAR_TARGET|D3DCLEAR_ZBUFFER,Bg,Depth,0));Check(D->BeginScene());
        D->SetPixelShaderConstantF(0,C,2);Check(D->DrawPrimitiveUP(D3DPT_TRIANGLESTRIP,2,Quad,sizeof(Vertex)));
        if(Twice){for(auto& X:Quad)X.Z=.7f;Check(D->DrawPrimitiveUP(D3DPT_TRIANGLESTRIP,2,Quad,sizeof(Vertex)));for(auto& X:Quad)X.Z=.5f;}
        Check(D->EndScene());Check(D->GetRenderTargetData(RT,Read));
        D3DLOCKED_RECT L;Check(Read->LockRect(&L,0,D3DLOCK_READONLY));
        DWORD Result=((DWORD*)((char*)L.pBits+32*L.Pitch))[32];Check(Read->UnlockRect());return Result&0xffffff;
    };
    auto R=[](DWORD X){return (X>>16)&255;};auto B=[](DWORD X){return X&255;};
    Texel(0xff000000);Require(Render(0xff202020)==0x202020,"black atlas edges do not brighten background");
    C[7]=3;Require(Render(0xff202020)==0x202020,"fog does not introduce rectangular polygon glow");C[7]=0;
    Texel(0xff808080);C[1]=0;DWORD Native=Render();Require(abs(int(R(Native))-32)<=1,"strength zero retains texture times vertex colour");
    C[1]=1;DWORD Enhanced=Render();Require(R(Enhanced)>R(Native)+6,"mid-tone coloured sheath enhanced");
    Require(B(Enhanced)>R(Enhanced)*1.7,"blue weapon identity retained");
    Require(Render(0xff202020,.25f)==0x202020,"foreground hardware depth occludes beam");
    DWORD Both=Render(0xff000000,1,true);Require(abs(int(B(Both))-int(B(Enhanced))*2)<=2,"beams do not write depth and remain additive");
    C[2]=.045f;unsigned MinFlow=255,MaxFlow=0;
    for(int Frame=0;Frame<24;++Frame){C[0]=Frame*.04f;unsigned Value=B(Render());
        MinFlow=(std::min)(MinFlow,Value);MaxFlow=(std::max)(MaxFlow,Value);}
    printf("Tail animated intensity range %u..%u\n",MinFlow,MaxFlow);
    Require(MaxFlow-MinFlow>20,"tail has clearly visible internal motion");
    Require(MinFlow>10,"tail remains present through its animation");C[0]=0;C[2]=0;
    for(auto& X:Quad)X.Colour=0xff203040;DWORD Half=Render();Require(abs(int(B(Half))*2-int(B(Enhanced)))<=2,"authored brightness scales linearly");
    for(auto& X:Quad)X.Colour=0;Require(Render()==0,"zero authored brightness stays invisible");
    for(auto& X:Quad)X.Colour=0xff406080;
    C[7]=3;DWORD Fogged=Render();Require(abs(int(B(Fogged))*2-int(B(Enhanced)))<=2,"linear nebula fog attenuation");
    C[5]=.4f;Require(Render()==0,"fully fogged beam disappears");C[5]=1;C[7]=0;
    Texel(0xffffffff);DWORD Core=Render();Require(B(Core)>180 && B(Core)<220,"hot core is brighter without clipping");
    Require(float(R(Core))/B(Core)>float(R(Enhanced))/B(Enhanced)+.15f,
            "hot centre is visibly paler than the coloured mantle");
    // dacom.ini enables alpha testing. ONE/ONE blending does not bypass that test.
    for(auto& X:Quad)X.Colour=0xff1e37ff; // Li_laser_04_beam core_color = 30,55,255
    DWORD Liberty=Render();
    D->SetRenderState(D3DRS_ALPHATESTENABLE,TRUE);
    D->SetRenderState(D3DRS_ALPHAFUNC,D3DCMP_GREATER);
    D->SetRenderState(D3DRS_ALPHAREF,0);
    Require(Render()==Liberty && B(Liberty)>200,"Liberty laser 4 survives game's alpha test");
    Require(R(Liberty)>150,"saturated Liberty blue gains a visible hot core, not just clipped blue");
    for(auto& X:Quad)X.Colour=0xffebbe14; // ku_photon_04_beam core = 235,190,20
    DWORD PhotonCore=Render();Require((PhotonCore&255)>130 && R(PhotonCore)>230,"gold photon gains a warm pale core");
    Texel(0xff404040);DWORD PhotonEdge=Render();
    Require(R(PhotonEdge)>(PhotonEdge&255)*4,"photon mantle retains authored gold hue");
    for(auto& X:Quad)X.Colour=0xff000000; // head_brightness = 0, alpha still opaque
    Require(Render()==0,"photon's deliberately disabled head stays dark");
    for(auto& X:Quad)X.Colour=0xff1e37ff;
    Texel(0x00808080);Require(Render()==0,"transparent atlas pixels retain native alpha rejection");
    puts("PASS: one-fetch SM3 shader; core, sheath, colour, brightness, animation, fog, depth and additive overlap");
    // Visual fixture, not a game capture: actual atlas, representative authored colours,
    // native triangular trail UVs and star/ball fans. Identical geometry on both sides.
    IDirect3DTexture9* GameAtlas=nullptr;
    if(SUCCEEDED(D3DXCreateTextureFromFileExA(D,"src/obj/code_beam/atlas.tga",D3DX_DEFAULT,D3DX_DEFAULT,
        1,0,D3DFMT_A8R8G8B8,D3DPOOL_MANAGED,D3DX_FILTER_NONE,D3DX_FILTER_NONE,0,0,0,&GameAtlas)))
    {
        IDirect3DSurface9* Preview=nullptr;
        Check(D->CreateRenderTarget(1024,600,D3DFMT_A8R8G8B8,D3DMULTISAMPLE_NONE,0,FALSE,&Preview,0));
        D->SetDepthStencilSurface(nullptr);D->SetRenderTarget(0,Preview);
        D3DVIEWPORT9 Viewport={0,0,1024,600,0,1};D->SetViewport(&Viewport);
        D->SetTexture(0,GameAtlas);D->SetRenderState(D3DRS_ZENABLE,FALSE);
        D->SetSamplerState(0,D3DSAMP_MINFILTER,D3DTEXF_LINEAR);D->SetSamplerState(0,D3DSAMP_MAGFILTER,D3DTEXF_LINEAR);
        D->SetSamplerState(0,D3DSAMP_ADDRESSU,D3DTADDRESS_CLAMP);D->SetSamplerState(0,D3DSAMP_ADDRESSV,D3DTADDRESS_CLAMP);
        float OriginX=0,OriginY=0,ShotPhase=0;
        auto Pt=[&](float X,float Y,DWORD Colour,float U,float V){return Vertex{X/512-1,1-Y/300,.5f,Colour,U,V,
            (Y-OriginY)/21,0,(X-OriginX)/330,ShotPhase};};
        auto Triangle=[&](Vertex A,Vertex B,Vertex C){Vertex T[]={A,B,C};Check(D->DrawPrimitiveUP(D3DPT_TRIANGLELIST,1,T,sizeof(Vertex)));};
        const DWORD Colours[]={0xff1e37ff,0xffebbe14,0xffe05030};
        std::vector<DWORD> FirstFrame;
        IDirect3DSurface9* PreviewRead=nullptr;
        Check(D->CreateOffscreenPlainSurface(1024,600,D3DFMT_A8R8G8B8,D3DPOOL_SYSTEMMEM,&PreviewRead,0));
        for(int Frame=0;Frame<48;++Frame)
        {
        Check(D->Clear(0,0,D3DCLEAR_TARGET,0xff080c16,1,0));Check(D->BeginScene());
        D->SetVertexShader(VS);D->SetPixelShader(PS);D->SetFVF(BeamFvf);D->SetTexture(0,GameAtlas);
        D->SetVertexShaderConstantF(0,(float*)&Identity,4);D->SetVertexShaderConstantF(4,(float*)&Identity,4);
        C[0]=Frame*.04f;C[2]=.045f;C[7]=0;
        for(int Col=0;Col<2;++Col)for(int Row=0;Row<3;++Row)
        {
            C[1]=float(Col);D->SetPixelShaderConstantF(0,C,2);
            float X=Col*512.0f+125,Y=130+Row*160.0f;DWORD Colour=Colours[Row];
            OriginX=X;OriginY=Y;ShotPhase=Row*.271f;
            // Four triangles form the original spear's two tapered ends.
            Vertex Centre=Pt(X,Y,Colour,0,.55f),Front=Pt(X-65,Y,Colour,.25f,1),Tail=Pt(X+265,Y,Colour,.25f,1);
            Vertex Top=Pt(X,Y-21,Colour,.25f,.55f),Bottom=Pt(X,Y+21,Colour,.25f,.55f);
            Triangle(Centre,Front,Top);Triangle(Centre,Front,Bottom);
            Triangle(Centre,Tail,Top);Triangle(Centre,Tail,Bottom);
            // Photon row intentionally has no head: head_brightness = 0.
            if(Row!=1)
            {
                float V0=Row==0?0:.5f,V1=V0+.5f;
                Vertex H=Pt(X,Y,Colour,.75f,V0+.25f);
                Vertex Corners[]={Pt(X-38,Y-38,Colour,.5f,V0),Pt(X+38,Y-38,Colour,1,V0),
                                  Pt(X+38,Y+38,Colour,1,V1),Pt(X-38,Y+38,Colour,.5f,V1)};
                for(int I=0;I<4;++I)Triangle(H,Corners[I],Corners[(I+1)%4]);
            }
        }
        ID3DXFont* Font=nullptr;
        if(SUCCEEDED(D3DXCreateFontA(D,20,0,400,1,FALSE,DEFAULT_CHARSET,OUT_DEFAULT_PRECIS,ANTIALIASED_QUALITY,
                                   DEFAULT_PITCH,"Segoe UI",&Font)))
        {
            RECT L={22,20,500,60},R={534,20,1000,60};
            Font->DrawTextA(0,"Original texture / vertex colour",-1,&L,DT_LEFT,0xffd0d9ed);
            Font->DrawTextA(0,"Animated head / flowing energy tail",-1,&R,DT_LEFT,0xffd0d9ed);
            const char* Names[]={"Blue laser / star head","Gold photon / head disabled","Warm tint / ball head"};
            for(int Row=0;Row<3;++Row)for(int Col=0;Col<2;++Col){RECT T={22+Col*512,78+Row*160,500+Col*512,105+Row*160};
                Font->DrawTextA(0,Names[Row],-1,&T,DT_LEFT,0xff8090ab);}
            Font->Release();
        }
        Check(D->EndScene());
        char Filename[128];sprintf(Filename,"src/obj/code_beam/flow_%02d.png",Frame);
        Check(D3DXSaveSurfaceToFileA(Filename,D3DXIFF_PNG,Preview,0,0));
        if(Frame==0)Check(D3DXSaveSurfaceToFileA("src/obj/code_beam/comparison.png",D3DXIFF_PNG,Preview,0,0));
        if(Frame==0 || Frame==17)
        {
            Check(D->GetRenderTargetData(Preview,PreviewRead));D3DLOCKED_RECT Lock;
            Check(PreviewRead->LockRect(&Lock,0,D3DLOCK_READONLY));
            if(Frame==0){FirstFrame.resize(1024*600);for(int Y=0;Y<600;++Y)
                memcpy(FirstFrame.data()+Y*1024,(char*)Lock.pBits+Y*Lock.Pitch,1024*4);}
            else
            {
                unsigned HeadChanges=0,TailChanges=0,NativeChanges=0;
                for(int Y=100;Y<490;++Y)for(int X=0;X<1024;++X)
                {
                    DWORD A=FirstFrame[Y*1024+X],B=((DWORD*)((char*)Lock.pBits+Y*Lock.Pitch))[X];
                    if(A==B)continue;
                    if(X<512)++NativeChanges;
                    else if(X>600 && X<675 && Y<160)++HeadChanges;
                    else if(X>680 && Y>270 && Y<310)++TailChanges;
                }
                printf("Actual atlas animation: head %u, photon tail %u, original %u changed pixels\n",HeadChanges,TailChanges,NativeChanges);
                Require(HeadChanges>150 && TailChanges>250 && NativeChanges==0,"actual head and photon tail animate independently, legacy profile stays static");
            }
            PreviewRead->UnlockRect();
        }
        }
        PreviewRead->Release();
        D->SetRenderTarget(0,RT);D->SetTexture(0,nullptr);Preview->Release();GameAtlas->Release();
        puts("Preview: src/obj/code_beam/comparison.png (original left, artistic right)");
    }
    D->SetTexture(0,nullptr);D->SetVertexShader(nullptr);D->SetPixelShader(nullptr);
    Atlas->Release();RT->Release();Read->Release();VS->Release();PS->Release();D->Release();Api->Release();DestroyWindow(Window);
}
