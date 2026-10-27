#include <windows.h>
#include <d3d9.h>
#include <d3dx9.h>
#include <cstdio>
#include <cstring>
int main()
{
    HWND W=CreateWindowA("STATIC","normal compression",WS_POPUP,0,0,16,16,0,0,GetModuleHandle(0),0);
    auto* A=Direct3DCreate9(D3D_SDK_VERSION);if(!A)return 1;
    D3DPRESENT_PARAMETERS P={};P.Windowed=1;P.SwapEffect=D3DSWAPEFFECT_DISCARD;P.BackBufferWidth=P.BackBufferHeight=16;
    IDirect3DDevice9* D=nullptr;if(FAILED(A->CreateDevice(0,D3DDEVTYPE_HAL,W,D3DCREATE_SOFTWARE_VERTEXPROCESSING,&P,&D)))return 2;
    FILE* F=fopen("src/obj/ship_normals/compression.txt","rb");if(!F)return 3;
    char Line[2048];unsigned Count=0;
    while(fgets(Line,sizeof(Line),F))
    {
        Line[strcspn(Line,"\r\n")]=0;char* Dest=strchr(Line,'|');if(!Dest)return 4;*Dest++=0;
        char* Format=strchr(Dest,'|');if(Format)*Format++=0;
        const D3DFORMAT Fmt=Format && !strcmp(Format,"DXT1") ? D3DFMT_DXT1 : D3DFMT_DXT5;
        IDirect3DTexture9* T=nullptr;
        HRESULT H=D3DXCreateTextureFromFileExA(D,Line,D3DX_DEFAULT,D3DX_DEFAULT,D3DX_DEFAULT,0,Fmt,D3DPOOL_SYSTEMMEM,
            D3DX_FILTER_NONE,D3DX_FILTER_NONE,0,nullptr,nullptr,&T);
        if(SUCCEEDED(H))H=D3DXSaveTextureToFileA(Dest,D3DXIFF_DDS,T,0);if(T)T->Release();
        if(FAILED(H)){printf("FAILED %s: %08lx\n",Line,H);return 5;}++Count;
    }
    fclose(F);D->Release();A->Release();DestroyWindow(W);printf("Compressed %u normal/material mip chains\n",Count);
}
