// Isolated GPU elapsed time for the production mesh shader/instancing helper at 1920x1080.
// Args: triples of exported mesh.bin, texture, rendered radius in metres (one triple per model).
// This is not a full-game FPS measurement: no ships, shadows, dust or postprocessing.
#include <windows.h>
#include <d3dx9.h>
#include <algorithm>
#include <cstdio>
#include <cstdlib>
#include <cstring>
#include <fstream>
#include <vector>
#include "../src/RP9/RP9MeshInstances.h"

static void Check(HRESULT H) { if (FAILED(H)) { std::printf("HRESULT %08lx\n", H); std::exit(1); } }
static ID3DXBuffer* Compile(const char* Entry, const char* Profile)
{
    ID3DXBuffer *Code = nullptr, *Errors = nullptr;
    HRESULT H = D3DXCompileShaderFromFileA("DATA_EXTRA/SHADERS/far_rocks.hlsl", nullptr, nullptr,
                                          Entry, Profile, 0, &Code, &Errors, nullptr);
    if (Errors) { std::puts((const char*)Errors->GetBufferPointer()); Errors->Release(); }
    Check(H); return Code;
}
static void Set(float* C, int R, float X, float Y, float Z, float W)
{ C[R*4]=X; C[R*4+1]=Y; C[R*4+2]=Z; C[R*4+3]=W; }
static void ReadQuery(IDirect3DQuery9* Q, void* Data, DWORD Size)
{
    DWORD Start = GetTickCount(); HRESULT H;
    while ((H = Q->GetData(Data, Size, D3DGETDATA_FLUSH)) == S_FALSE)
    { if (GetTickCount() - Start > 5000) { std::puts("Query timeout"); std::exit(1); } Sleep(0); }
    Check(H);
}
static float Random(unsigned& Seed)
{ Seed = 1664525u * Seed + 1013904223u; return (Seed >> 8) * (1.0f / 16777216.0f); }

int main(int Argc, char** Argv)
{
    if (Argc < 4 || (Argc-1)%3) { std::puts("Usage: benchmark_field_mesh <mesh> <texture> <radius> [...]"); return 1; }
    HWND Window = CreateWindowA("STATIC", "field GPU benchmark", WS_POPUP, 0, 0, 1920, 1080,
                                nullptr, nullptr, GetModuleHandle(nullptr), nullptr);
    IDirect3D9* Api = Direct3DCreate9(D3D_SDK_VERSION); if (!Api) return 1;
    D3DADAPTER_IDENTIFIER9 Adapter = {}; Check(Api->GetAdapterIdentifier(0, 0, &Adapter));
    D3DPRESENT_PARAMETERS P = {}; P.Windowed = TRUE; P.SwapEffect = D3DSWAPEFFECT_DISCARD;
    P.BackBufferWidth = 1920; P.BackBufferHeight = 1080; P.BackBufferFormat = D3DFMT_A8R8G8B8;
    P.EnableAutoDepthStencil = TRUE; P.AutoDepthStencilFormat = D3DFMT_D24S8;
    IDirect3DDevice9* D = nullptr;
    Check(Api->CreateDevice(0, D3DDEVTYPE_HAL, Window, D3DCREATE_HARDWARE_VERTEXPROCESSING, &P, &D));
    ID3DXBuffer* Code = Compile("VSMesh", "vs_3_0"); IDirect3DVertexShader9* Vs = nullptr;
    Check(D->CreateVertexShader((const DWORD*)Code->GetBufferPointer(), &Vs)); Code->Release();
    Code = Compile("PSMesh", "ps_3_0"); IDirect3DPixelShader9* Ps = nullptr;
    Check(D->CreatePixelShader((const DWORD*)Code->GetBufferPointer(), &Ps)); Code->Release();
    Check(D->SetVertexShader(Vs)); Check(D->SetPixelShader(Ps));
    struct Instance { float Centre[4], Quaternion[4]; DWORD Colour; };
    struct Model { IDirect3DVertexBuffer9 *Mesh=nullptr, *Instances=nullptr; IDirect3DTexture9* Texture=nullptr; unsigned Vertices=0, Count=0; };
    std::vector<Model> Models((Argc-1)/3); unsigned Seed=123456, Triangles=0;
    for (unsigned I=0; I<Models.size(); ++I)
    {
        Model& M=Models[I]; std::ifstream Input(Argv[1+I*3], std::ios::binary);
        Input.read((char*)&M.Vertices, 4); if (!Input || !M.Vertices || M.Vertices>65535 || M.Vertices%3) return 1;
        std::vector<float> Vertices(M.Vertices*8); Input.read((char*)Vertices.data(), Vertices.size()*4); if (!Input) return 1;
        M.Count=(1000+(unsigned)Models.size()-1-I)/(unsigned)Models.size(); Triangles+=M.Count*M.Vertices/3;
        std::vector<Instance> Instances(M.Count); float Radius=(float)std::atof(Argv[3+I*3]);
        for (Instance& V:Instances)
        {
            float X,Y,Z;
            do { X=Random(Seed)*2-1; Y=Random(Seed)*2-1; Z=Random(Seed)*2-1; } while (X*X+Y*Y+Z*Z>1);
            V.Centre[0]=X*12000; V.Centre[1]=Y*8000; V.Centre[2]=Z*12000-30000; V.Centre[3]=Radius;
            D3DXQUATERNION Q; D3DXQuaternionRotationYawPitchRoll(&Q, Random(Seed)*6.28f, Random(Seed)*6.28f, Random(Seed)*6.28f);
            memcpy(V.Quaternion, &Q, 16); V.Colour=0xff800000;
        }
        Check(D->CreateVertexBuffer(M.Vertices*32, 0, 0, D3DPOOL_MANAGED, &M.Mesh, nullptr));
        Check(D->CreateVertexBuffer(M.Count*sizeof(Instance), 0, 0, D3DPOOL_MANAGED, &M.Instances, nullptr));
        void* Bytes=nullptr; Check(M.Mesh->Lock(0,0,&Bytes,0)); memcpy(Bytes,Vertices.data(),M.Vertices*32); Check(M.Mesh->Unlock());
        Check(M.Instances->Lock(0,0,&Bytes,0)); memcpy(Bytes,Instances.data(),M.Count*sizeof(Instance)); Check(M.Instances->Unlock());
        Check(D3DXCreateTextureFromFileA(D,Argv[2+I*3],&M.Texture));
    }
    float V[36]={}, C[36]={};
    Set(V,1,1,0,0,0); Set(V,2,0,1,0,0); Set(V,3,0,0,1,0);
    Set(V,4,1.0f/(1920.0f/1080),1,100000.0f/99999,-100000.0f/99999); Set(V,5,1,1,0,0);
    Set(V,6,100000,540,1,1.0f-1.0f/4194304); Set(V,7,4500,1.0f/700,45000,1.0f/23000);
    Set(C,0,1,1,1,1); Set(C,5,.04f,.07f,.08f,0); Set(C,6,1,1,1,0); Set(C,7,.6f,0,.8f,1);
    Check(D->SetPixelShaderConstantF(0,C,9));
    Check(D->SetRenderState(D3DRS_CULLMODE,D3DCULL_NONE)); Check(D->SetRenderState(D3DRS_ZENABLE,TRUE));
    Check(D->SetRenderState(D3DRS_ALPHABLENDENABLE,TRUE));
    Check(D->SetRenderState(D3DRS_SRCBLEND,D3DBLEND_SRCALPHA)); Check(D->SetRenderState(D3DRS_DESTBLEND,D3DBLEND_INVSRCALPHA));
    Check(D->SetSamplerState(0,D3DSAMP_MINFILTER,D3DTEXF_LINEAR)); Check(D->SetSamplerState(0,D3DSAMP_MAGFILTER,D3DTEXF_LINEAR));
    Check(D->SetSamplerState(0,D3DSAMP_MIPFILTER,D3DTEXF_LINEAR));
    IDirect3DQuery9 *Start=nullptr,*End=nullptr,*Frequency=nullptr,*Disjoint=nullptr;
    Check(D->CreateQuery(D3DQUERYTYPE_TIMESTAMP,&Start)); Check(D->CreateQuery(D3DQUERYTYPE_TIMESTAMP,&End));
    Check(D->CreateQuery(D3DQUERYTYPE_TIMESTAMPFREQ,&Frequency)); Check(D->CreateQuery(D3DQUERYTYPE_TIMESTAMPDISJOINT,&Disjoint));
    FRp9MeshInstances Renderer;
    std::printf("GPU: %s; 1920x1080; 1000 instances/field; %u triangles/field/pass; two passes\n",Adapter.Description,Triangles);
    for (int Fields : {1,4})
    {
        std::vector<double> Times;
        for (int Frame=0; Frame<80; ++Frame)
        {
            Check(D->Clear(0,nullptr,D3DCLEAR_TARGET|D3DCLEAR_ZBUFFER,0,1,0)); Check(D->BeginScene());
            Check(Disjoint->Issue(D3DISSUE_BEGIN)); Check(Start->Issue(D3DISSUE_END));
            for (int F=0; F<Fields; ++F)
            {
                Set(V,0,Fields==1?0.0f:((F&1)?-13000.0f:13000.0f),0,(F&2)?-4000.0f:4000.0f,0);
                for (int Pass=0; Pass<2; ++Pass)
                {
                    Set(V,8,(float)Pass,5,0,0); Check(D->SetVertexShaderConstantF(0,V,9));
                    Check(D->SetRenderState(D3DRS_ZWRITEENABLE,Pass==0));
                    for (Model& M:Models)
                    { Check(D->SetTexture(0,M.Texture)); Check(Renderer.Draw(D,M.Mesh,M.Instances,M.Vertices,0,M.Count)); }
                }
            }
            Check(End->Issue(D3DISSUE_END)); Check(Disjoint->Issue(D3DISSUE_END)); Check(Frequency->Issue(D3DISSUE_END));
            Check(D->EndScene());
            UINT64 A=0,B=0,Hz=0; BOOL Invalid=TRUE;
            ReadQuery(End,&B,sizeof(B)); ReadQuery(Start,&A,sizeof(A)); ReadQuery(Frequency,&Hz,sizeof(Hz)); ReadQuery(Disjoint,&Invalid,sizeof(Invalid));
            if (Frame>=16 && !Invalid && Hz && B>=A) Times.push_back((double)(B-A)*1000/Hz);
        }
        if (Times.empty()) { std::puts("No valid timing samples"); return 1; }
        std::sort(Times.begin(),Times.end());
        std::printf("%d fields: median %.3f ms, p95 %.3f ms (%zu valid samples)\n",Fields,Times[Times.size()/2],Times[(Times.size()-1)*95/100],Times.size());
    }
    Renderer.Release(); Start->Release(); End->Release(); Frequency->Release(); Disjoint->Release();
    for (Model& M:Models) { M.Mesh->Release(); M.Instances->Release(); M.Texture->Release(); }
    Vs->Release(); Ps->Release(); D->Release(); Api->Release(); DestroyWindow(Window); return 0;
}
