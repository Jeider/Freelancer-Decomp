#include <windows.h>
#include <d3d9.h>
#include "cursor_vector_art.h"
#ifdef BASE_ICON_CHECK
#include "base_icon_art.h"
#endif
#ifdef NN_ICON_CHECK
#include "nn_icon_art.h"
#endif
#include <cstdio>
#include <cstdlib>
#include <cstring>
#include <fstream>
#include <string>
using namespace CursorVectorArt;
static void Check(HRESULT h) {if(FAILED(h)){std::printf("D3D9 FAIL: %08lx\n",h);std::exit(1);}}
static void Require(bool c,char const* s){if(!c){std::printf("FAIL: %s\n",s);std::exit(1);}}
struct Vertex {float x,y,z,rhw;DWORD color;float u,v;};
int main(int argc,char** argv) {
    Require(argc==2,"output directory");
    WNDCLASSA wc{};wc.lpfnWndProc=DefWindowProcA;wc.hInstance=GetModuleHandleA(nullptr);wc.lpszClassName="CursorVectorCheck";
    RegisterClassA(&wc);HWND window=CreateWindowA(wc.lpszClassName,"",WS_POPUP,0,0,320,320,nullptr,nullptr,wc.hInstance,nullptr);
    Require(window!=nullptr,"hidden device window");
    auto* api=Direct3DCreate9(D3D_SDK_VERSION);Require(api!=nullptr,"D3D9");
    D3DPRESENT_PARAMETERS pp{};pp.Windowed=TRUE;pp.hDeviceWindow=window;pp.SwapEffect=D3DSWAPEFFECT_DISCARD;
    pp.BackBufferWidth=320;pp.BackBufferHeight=320;pp.BackBufferFormat=D3DFMT_X8R8G8B8;pp.PresentationInterval=D3DPRESENT_INTERVAL_IMMEDIATE;
    IDirect3DDevice9* device=nullptr;Check(api->CreateDevice(0,D3DDEVTYPE_HAL,window,D3DCREATE_SOFTWARE_VERTEXPROCESSING,&pp,&device));
    D3DADAPTER_IDENTIFIER9 adapter{};api->GetAdapterIdentifier(0,0,&adapter);std::printf("Adapter: %s\n",adapter.Description);
    auto render=[&](IDirect3DTexture9* texture,DWORD tint,float angle,float hotspotX,float hotspotY,float scale=1.f,DWORD background=0xff0c1420,
                    float u0=0,float v0=0,float u1=1,float v1=1) {
        Check(device->SetRenderState(D3DRS_ZENABLE,FALSE));Check(device->SetRenderState(D3DRS_LIGHTING,FALSE));
        Check(device->SetRenderState(D3DRS_CULLMODE,D3DCULL_NONE));Check(device->SetRenderState(D3DRS_ALPHATESTENABLE,FALSE));
        Check(device->SetRenderState(D3DRS_ALPHABLENDENABLE,TRUE));Check(device->SetRenderState(D3DRS_SRCBLEND,D3DBLEND_SRCALPHA));
        Check(device->SetRenderState(D3DRS_DESTBLEND,D3DBLEND_INVSRCALPHA));
        Check(device->SetTextureStageState(0,D3DTSS_COLOROP,D3DTOP_MODULATE));
        Check(device->SetTextureStageState(0,D3DTSS_COLORARG1,D3DTA_TEXTURE));Check(device->SetTextureStageState(0,D3DTSS_COLORARG2,D3DTA_DIFFUSE));
        Check(device->SetTextureStageState(0,D3DTSS_ALPHAOP,D3DTOP_MODULATE));
        Check(device->SetTextureStageState(0,D3DTSS_ALPHAARG1,D3DTA_TEXTURE));Check(device->SetTextureStageState(0,D3DTSS_ALPHAARG2,D3DTA_DIFFUSE));
        Check(device->SetTextureStageState(1,D3DTSS_COLOROP,D3DTOP_DISABLE));
        Check(device->SetSamplerState(0,D3DSAMP_MINFILTER,D3DTEXF_LINEAR));Check(device->SetSamplerState(0,D3DSAMP_MAGFILTER,D3DTEXF_LINEAR));
        Check(device->SetSamplerState(0,D3DSAMP_ADDRESSU,D3DTADDRESS_CLAMP));Check(device->SetSamplerState(0,D3DSAMP_ADDRESSV,D3DTADDRESS_CLAMP));
        Check(device->SetTexture(0,texture));Check(device->SetFVF(D3DFVF_XYZRHW|D3DFVF_DIFFUSE|D3DFVF_TEX1));
        Point p[]={{0,0},{256,0},{256,256},{0,256}};Vertex v[4];
        for(int i=0;i<4;++i) {
            auto q=Point{32,32}+(Point{hotspotX,hotspotY}+Rotate(p[i]-Point{hotspotX,hotspotY},angle))*scale;
            v[i]={q.x-.5f,q.y-.5f,0,1,tint,u0+p[i].x/256*(u1-u0),v0+p[i].y/256*(v1-v0)};
        }
        unsigned short indices[]={0,1,2,0,2,3};
        Check(device->Clear(0,nullptr,D3DCLEAR_TARGET,background,1,0));Check(device->BeginScene());
        Check(device->DrawIndexedPrimitiveUP(D3DPT_TRIANGLELIST,0,4,2,indices,D3DFMT_INDEX16,v,sizeof(Vertex)));Check(device->EndScene());
        IDirect3DSurface9* back=nullptr;IDirect3DSurface9* read=nullptr;
        Check(device->GetRenderTarget(0,&back));Check(device->CreateOffscreenPlainSurface(320,320,D3DFMT_X8R8G8B8,D3DPOOL_SYSTEMMEM,&read,nullptr));
        Check(device->GetRenderTargetData(back,read));D3DLOCKED_RECT lock{};Check(read->LockRect(&lock,nullptr,D3DLOCK_READONLY));
        std::vector<uint32_t> pixels(320*320);
        for(int y=0;y<320;++y)std::memcpy(pixels.data()+y*320,static_cast<char*>(lock.pBits)+y*lock.Pitch,320*4);
        read->UnlockRect();read->Release();back->Release();return pixels;
    };
#ifdef NN_ICON_CHECK
    auto const& testedIcons=NnIconArt::Shapes();
#elif defined(BASE_ICON_CHECK)
    auto const& testedIcons=BaseIconArt::Shapes();
#else
    auto const& testedIcons=Icons();
#endif
    for(auto const& icon:testedIcons) {
        auto cpu=Rasterize(icon,256);IDirect3DTexture9* tex=nullptr;
        Check(device->CreateTexture(256,256,1,0,D3DFMT_A8R8G8B8,D3DPOOL_MANAGED,&tex,nullptr));
        D3DLOCKED_RECT lock{};Check(tex->LockRect(0,&lock,nullptr,0));
        for(int y=0;y<256;++y)std::memcpy(static_cast<char*>(lock.pBits)+y*lock.Pitch,cpu.data()+y*256,256*4);
        tex->UnlockRect(0);
        auto actual=render(tex,0xffffffff,0,80,72);
        // Tests channel packing, straight-alpha blend, transparent background,
        // top-down orientation and full-texture UVs against production pixels.
        for(int y=0;y<256;++y)for(int x=0;x<256;++x) {
            unsigned src=cpu[y*256+x],gpu=actual[(y+32)*320+x+32];float alpha=(src>>24)/255.f;
            for(int s=0;s<=16;s+=8) {
                int bg=(0x0c1420>>s)&255;
                int expected=int(((src>>s)&255)*alpha+bg*(1-alpha)+.5f);
                Require(std::abs(expected-int((gpu>>s)&255))<=2,"GPU matches top-down CPU raster and alpha blend");
            }
        }
        if(!std::strcmp(icon.name,"arrow")) {
            auto rotated=render(tex,0xffffffff,Pi/2,80,72);
            Require((rotated[104*320+112]&0xffffff)!=0x0c1420,"rotated arrow stays on its hotspot");
            std::ofstream f(std::string(argv[1])+"/gpu_arrow.bgra",std::ios::binary);
            f.write(reinterpret_cast<char const*>(actual.data()),actual.size()*4);
            Check(device->SetTexture(0,nullptr));Check(device->Reset(&pp));
            auto after=render(tex,0xffffffff,0,80,72);
            Require(after==actual,"managed cursor texture survives device reset");
        }
        if(!std::strcmp(icon.name,"hostile_fire")) {
            auto red=render(tex,0xffbf1d1d,.37f,128,128),green=render(tex,0xff3bbf1d,.37f,128,128);
            Require(red!=green,"live hostile/friendly tint remains independent of cached pixels");
        }
        Check(device->SetTexture(0,nullptr));tex->Release();
        for(int height:{720,1080,1440,2160}) {
            float factor=!std::strcmp(icon.name,"arrow")?.25f:
                !std::strncmp(icon.name,"talk_",5)?.175f:
                !std::strcmp(icon.name,"cross")?.1f:.1125f;
            float scale=factor*height/600.f;
            int size=TextureSize(256*scale);
            auto pixels=Rasterize(icon,size);
            Check(device->CreateTexture(size,size,1,0,D3DFMT_A8R8G8B8,D3DPOOL_MANAGED,&tex,nullptr));
            Check(tex->LockRect(0,&lock,nullptr,0));
            for(int y=0;y<size;++y)std::memcpy(static_cast<char*>(lock.pBits)+y*lock.Pitch,pixels.data()+y*size,size*4);
            tex->UnlockRect(0);
            DWORD tint=!std::strcmp(icon.name,"hostile_fire")?0xffbf1d1d:
                !std::strcmp(icon.name,"cross")?0xff87c3e0:0xffffffff;
            for(int light=0;light<2;++light) {
                DWORD bg=light?0xffa0a8b0:0xff0c1420;
                auto actualSize=render(tex,tint,0,80,72,scale,bg);
                size_t visible=0;
                for(auto p:actualSize)visible+=(p&0xffffff)!=(bg&0xffffff);
                Require(visible>10,"cursor remains visible at game display size");
                std::ofstream f(std::string(argv[1])+"/size_"+icon.name+"_"+std::to_string(height)+"_"+std::to_string(light)+".bgra",std::ios::binary);
                f.write(reinterpret_cast<char const*>(actualSize.data()),actualSize.size()*4);
                Require(bool(f),"GPU size preview saved");
            }
            Check(device->SetTexture(0,nullptr));tex->Release();
        }
    }
#ifdef NN_ICON_CHECK
    // Actual staged atlas bytes in the engine's bottom-up TGA decode order,
    // sampled through the real montage's 1/256 inset and original tile mapping.
    std::ifstream mapping(std::string(argv[1])+"/atlas_gpu.txt");
    std::string name,file;int width,col,row,count,verified=0;
    while(mapping>>name>>file>>width>>col>>row>>count) {
        std::vector<uint32_t> pixels(width*width);
        std::ifstream input(std::string(argv[1])+"/"+file,std::ios::binary);
        input.read(reinterpret_cast<char*>(pixels.data()),pixels.size()*4);
        Require(bool(input),"staged atlas bytes available");
        IDirect3DTexture9* tex=nullptr;
        Check(device->CreateTexture(width,width,1,0,D3DFMT_A8R8G8B8,D3DPOOL_MANAGED,&tex,nullptr));
        D3DLOCKED_RECT lock{};Check(tex->LockRect(0,&lock,nullptr,0));
        for(int y=0;y<width;++y)std::memcpy(static_cast<char*>(lock.pBits)+y*lock.Pitch,pixels.data()+y*width,width*4);
        tex->UnlockRect(0);
        int tile=width/count,inset=width/256,side=tile-2*inset;
        auto actual=render(tex,0xffffffff,0,0,0,side/256.f,0xff0c1420,
            float(col*tile+inset)/width,float(row*tile+inset)/width,
            float((col+1)*tile-inset)/width,float((row+1)*tile-inset)/width);
        Icon const* icon=nullptr;for(auto const& candidate:testedIcons)if(name==candidate.name)icon=&candidate;
        Require(icon!=nullptr,"mapped NeuroNet icon exists");auto expected=Rasterize(*icon,tile);
        for(int y=0;y<side;++y)for(int x=0;x<side;++x) {
            unsigned src=expected[(y+inset)*tile+x+inset],gpu=actual[(y+32)*320+x+32];
            float alpha=(src>>24)/255.f;
            for(int s=0;s<=16;s+=8) {
                int bg=(0x0c1420>>s)&255;
                int value=int(((src>>s)&255)*alpha+bg*(1-alpha)+.5f);
                Require(std::abs(value-int((gpu>>s)&255))<=2,"staged montage agrees with upright geometry at original UVs");
            }
        }
        Check(device->SetTexture(0,nullptr));tex->Release();++verified;
    }
    Require(verified==7,"all seven montage buttons checked");
    std::puts("PASS: seven staged montage cells, engine TGA orientation and original inset UVs");
#endif
    device->Release();api->Release();DestroyWindow(window);
    std::printf("PASS: %zu icons on D3D9; CPU/GPU orientation, RGBA, alpha; %zu size/background renders\n",testedIcons.size(),testedIcons.size()*8);
}
