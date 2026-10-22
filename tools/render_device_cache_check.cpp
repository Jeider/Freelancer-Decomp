#include <windows.h>
#include <d3d9.h>
#include "RP9DeviceCallCache.h"
#include <cassert>
#include <cstdio>
#include <vector>

static void Check(HRESULT H){if(FAILED(H)){printf("HRESULT %08lx\n",H);ExitProcess(1);}}
int main()
{
    SetErrorMode(SEM_FAILCRITICALERRORS|SEM_NOGPFAULTERRORBOX);
    HWND Window=CreateWindowA("STATIC","device cache check",WS_POPUP,0,0,32,32,0,0,GetModuleHandle(0),0);
    auto* Api=Direct3DCreate9(D3D_SDK_VERSION);
    D3DPRESENT_PARAMETERS P={};P.Windowed=1;P.SwapEffect=D3DSWAPEFFECT_DISCARD;
    P.BackBufferWidth=P.BackBufferHeight=32;P.BackBufferFormat=D3DFMT_A8R8G8B8;
    IDirect3DDevice9* Device=nullptr;
    Check(Api->CreateDevice(0,D3DDEVTYPE_HAL,Window,D3DCREATE_SOFTWARE_VERTEXPROCESSING,&P,&Device));
    auto& C=Rp9DeviceCalls();C.Invalidate();C.ResetCounters();
    float Data[95*4]={},Read[95*4]={};
    for(int I=0;I<95*4;++I) Data[I]=(float)I*.01f;
    Check(Rp9SetPixelConstants(Device,0,Data,95));
    for(int I=0;I<1000;++I) Check(Rp9SetPixelConstants(Device,0,Data,95));
    assert(C.Submitted==1 && C.Skipped==1000 && C.ConstantVectors==95);
    Data[3*4+1]=17;
    Check(Rp9SetPixelConstants(Device,0,Data,95));assert(C.ConstantVectors==96);
    Check(Device->GetPixelShaderConstantF(0,Read,95));assert(!memcmp(Data,Read,sizeof(Data)));
    Check(Rp9SetSamplerState(Device,0,D3DSAMP_ADDRESSU,D3DTADDRESS_CLAMP));
    Check(Rp9SetRenderState(Device,D3DRS_ZWRITEENABLE,FALSE));
    auto Submitted=C.Submitted;
    for(int I=0;I<1000;++I){Check(Rp9SetSamplerState(Device,0,D3DSAMP_ADDRESSU,D3DTADDRESS_CLAMP));Check(Rp9SetRenderState(Device,D3DRS_ZWRITEENABLE,FALSE));}
    assert(C.Submitted==Submitted);
    D3DMATERIAL9 Material={};Material.Diffuse={.2f,.3f,.4f,1};Material.Power=16;
    D3DMATRIX Matrix={};Matrix._11=Matrix._22=Matrix._33=Matrix._44=1;Matrix._41=123;
    Check(Rp9SetMaterial(Device,&Material));Check(Rp9SetTransform(Device,D3DTS_WORLD,&Matrix));Check(Rp9SetFvf(Device,0x112));
    Submitted=C.Submitted;
    for(int I=0;I<1000;++I){Check(Rp9SetMaterial(Device,&Material));Check(Rp9SetTransform(Device,D3DTS_WORLD,&Matrix));Check(Rp9SetFvf(Device,0x112));}
    assert(C.Submitted==Submitted);
    D3DMATERIAL9 MaterialRead={};D3DMATRIX MatrixRead={};DWORD Fvf=0;
    Check(Device->GetMaterial(&MaterialRead));Check(Device->GetTransform(D3DTS_WORLD,&MatrixRead));Check(Device->GetFVF(&Fvf));
    assert(!memcmp(&Material,&MaterialRead,sizeof(Material))&&!memcmp(&Matrix,&MatrixRead,sizeof(Matrix))&&Fvf==0x112);
    IDirect3DStateBlock9* State=nullptr;Check(Device->CreateStateBlock(D3DSBT_ALL,&State));
    Check(Rp9SetRenderState(Device,D3DRS_ZWRITEENABLE,TRUE));
    Check(Rp9SetSamplerState(Device,0,D3DSAMP_ADDRESSU,D3DTADDRESS_WRAP));
    Data[0]=.73f;Check(Rp9SetPixelConstants(Device,0,Data,95));
    Check(State->Apply());C.Invalidate();
    Check(Rp9SetRenderState(Device,D3DRS_ZWRITEENABLE,TRUE));
    Check(Rp9SetSamplerState(Device,0,D3DSAMP_ADDRESSU,D3DTADDRESS_WRAP));
    Check(Rp9SetPixelConstants(Device,0,Data,95));
    DWORD Value=0;Check(Device->GetRenderState(D3DRS_ZWRITEENABLE,&Value));assert(Value==TRUE);
    Check(Device->GetSamplerState(0,D3DSAMP_ADDRESSU,&Value));assert(Value==D3DTADDRESS_WRAP);
    Check(Device->GetPixelShaderConstantF(0,Read,95));assert(!memcmp(Data,Read,sizeof(Data)));
    assert(FAILED(Rp9SetPixelConstants(Device,224,Data,1)));
    C.Enabled=false;Submitted=C.Submitted;
    Check(Rp9SetPixelConstants(Device,0,Data,95));Check(Rp9SetPixelConstants(Device,0,Data,95));assert(C.Submitted==Submitted+2);
    puts("PASS: real D3D9 material/transform/FVF/state/constant deduplication, single-register updates, state-block invalidation, API errors and cache-off fallback");
    State->Release();Device->Release();Api->Release();DestroyWindow(Window);
}
