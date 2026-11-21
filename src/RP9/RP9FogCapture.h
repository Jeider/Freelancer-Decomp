#pragma once
#include <windows.h>
#include <d3dx9.h>
#include <cstdio>
#include <cstring>

// Explicit, bounded diagnostic. Records three matching stages of at most two
// Omega-15 frames, then stops. Does not alter render state or start the game.
namespace Rp9FogCapture {
struct State { bool Read=false,Enabled=false,Armed=false,Active=false,InOmega=false; unsigned Count=0; ULONGLONG Due=0; };
inline State& Get() {static State s;return s;}
inline void Scope(unsigned flags) {
    auto& s=Get();
    if(!s.Read) {
        s.Read=true;char path[MAX_PATH]={};GetModuleFileNameA(nullptr,path,MAX_PATH);
        if(char* slash=strrchr(path,'\\')) {
            strcpy_s(slash+1,sizeof(path)-size_t(slash+1-path),"port.ini");
            s.Enabled=GetPrivateProfileIntA("Diagnostics","asteroid_fog_capture",0,path)==1;
        }
    }
    if(s.Enabled && s.Count<2 && (flags&512u))s.InOmega=true;
}
inline void Save(IDirect3DSurface9* surface,const char* stage) {
    auto& s=Get();if(!s.Active || !surface)return;
    char folder[MAX_PATH]={};DWORD size=GetEnvironmentVariableA("LOCALAPPDATA",folder,MAX_PATH);
    if(!size || size>MAX_PATH-80)return;
    strcat_s(folder,"\\Freelancer-Decomp");CreateDirectoryA(folder,nullptr);
    strcat_s(folder,"\\Diagnostics");CreateDirectoryA(folder,nullptr);
    strcat_s(folder,"\\asteroid_fog_capture");CreateDirectoryA(folder,nullptr);
    char file[MAX_PATH]={};sprintf_s(file,"%s\\%u_%s.png",folder,s.Count,stage);
    HRESULT result=D3DXSaveSurfaceToFileA(file,D3DXIFF_PNG,surface,nullptr,nullptr);
    sprintf_s(file,"%s\\capture.txt",folder);
    const char* mode=s.Count==0 && strcmp(stage,"opaque")==0?"w":"a";
    if(FILE* log=fopen(file,mode)){fprintf(log,"frame=%u stage=%s HRESULT=%08lx\n",s.Count,stage,result);fclose(log);}
}
inline void BeforeVolume(IDirect3DSurface9* scene) {
    auto& s=Get();if(!s.Enabled || !s.InOmega || s.Active || s.Count>=2)return;
    // Explicit trigger: capture the view exhibiting the defect, not the arrival
    // frame or an unrelated view while the player is still turning the camera.
    if(!s.Armed && (GetAsyncKeyState(VK_CONTROL)&0x8000) &&
        (GetAsyncKeyState(VK_SHIFT)&0x8000) && (GetAsyncKeyState(VK_F12)&0x8000))s.Armed=true;
    if(!s.Armed || GetTickCount64()<s.Due)return;
    s.Active=true;Save(scene,"opaque");
}
inline void AfterVolume(IDirect3DSurface9* scene) {Save(scene,"volume");}
inline void Present(IDirect3DDevice9* device) {
    auto& s=Get();s.InOmega=false;if(!s.Active)return;
    IDirect3DSurface9* scene=nullptr;
    if(device && SUCCEEDED(device->GetRenderTarget(0,&scene))) {Save(scene,"present");scene->Release();}
    s.Active=false;++s.Count;s.Due=GetTickCount64()+5000;
}
}
