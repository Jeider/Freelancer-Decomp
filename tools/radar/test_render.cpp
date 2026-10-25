// Hidden offscreen D3D9 check; loads the real installed HUD through Common's reader.
#define WIN32_LEAN_AND_MEAN
#include <windows.h>
#include <d3d9.h>
#include "common_ini.h"
#include "../../src/freelancer/Client/radar_frame.h"
#include <cstdio>
#include <vector>
#include <cassert>

struct Vertex { float x,y,z,rhw; unsigned color; };
int main(int argc,char** argv)
{
    if(argc!=2)return 2;
    INI_Reader reader;if(!reader.open(argv[1],false))return 3;
    bool enabled=false;int sections=0,index=2;float cx=.84f,cy=.72f,r=.095f,e=.42f,h=.65f,a=.8f;
    while(reader.read_header())
    {
        bool const radar=reader.is_header("Radar");if(radar)++sections;
        while(reader.read_value())if(radar)
        {
            if(reader.is_value("enabled"))enabled=reader.get_value_bool(0);
            else if(reader.is_value("center")){cx=reader.get_value_float(0);cy=reader.get_value_float(1);}
            else if(reader.is_value("radius"))r=reader.get_value_float(0);
            else if(reader.is_value("ellipse"))e=reader.get_value_float(0);
            else if(reader.is_value("elevation"))h=reader.get_value_float(0);
            else if(reader.is_value("opacity"))a=reader.get_value_float(0);
            else if(reader.is_value("range_index"))index=reader.get_value_int(0);
        }
    }
    assert(sections==1 && enabled);
    RadarProjection::Layout layout;assert(RadarProjection::MakeLayout({0,0,1279,719},cx,cy,r,e,h,layout));
    std::vector<Vertex> vertices;unsigned lines=0;
    auto emit=[&](float x,float y,float bx,float by,unsigned color,float width)
    {
        ++lines;float dx=bx-x,dy=by-y,len=std::sqrt(dx*dx+dy*dy);if(len<=0)return;
        float ox=-dy/len*width,oy=dx/len*width;unsigned edge=color&0xffffff;
        Vertex q[8]={{x,y,0,1,color},{x+ox,y+oy,0,1,edge},{bx,by,0,1,color},{bx+ox,by+oy,0,1,edge},
                     {x,y,0,1,color},{x-ox,y-oy,0,1,edge},{bx,by,0,1,color},{bx-ox,by-oy,0,1,edge}};
        int const indices[12]={0,1,2,2,3,1,4,5,6,6,7,5};
        for(int i:indices)vertices.push_back(q[i]);
    };
    // Empty/suppressed scanner must still produce a visible frame.
    RadarFrame::Emit(layout,index,a*.55f,emit);
    unsigned const counts[]={825,833,845};assert(index>=0&&index<3&&lines==counts[index]);
    WNDCLASSW wc={};wc.lpfnWndProc=DefWindowProcW;wc.hInstance=GetModuleHandleW(nullptr);wc.lpszClassName=L"RadarCheckHidden";
    RegisterClassW(&wc);HWND wnd=CreateWindowW(wc.lpszClassName,L"",WS_OVERLAPPED,0,0,1280,720,nullptr,nullptr,wc.hInstance,nullptr);
    assert(wnd);IDirect3D9* d3d=Direct3DCreate9(D3D_SDK_VERSION);assert(d3d);
    D3DPRESENT_PARAMETERS pp={};pp.Windowed=TRUE;pp.SwapEffect=D3DSWAPEFFECT_DISCARD;pp.hDeviceWindow=wnd;
    pp.BackBufferWidth=1280;pp.BackBufferHeight=720;pp.BackBufferFormat=D3DFMT_A8R8G8B8;
    IDirect3DDevice9* device=nullptr;
    assert(SUCCEEDED(d3d->CreateDevice(0,D3DDEVTYPE_HAL,wnd,D3DCREATE_SOFTWARE_VERTEXPROCESSING,&pp,&device)));
    device->Clear(0,nullptr,D3DCLEAR_TARGET,0xff000000,1,0);device->BeginScene();
    device->SetRenderState(D3DRS_ZENABLE,FALSE);device->SetRenderState(D3DRS_LIGHTING,FALSE);device->SetRenderState(D3DRS_CULLMODE,D3DCULL_NONE);
    device->SetRenderState(D3DRS_ALPHABLENDENABLE,TRUE);device->SetRenderState(D3DRS_SRCBLEND,D3DBLEND_SRCALPHA);device->SetRenderState(D3DRS_DESTBLEND,D3DBLEND_INVSRCALPHA);
    device->SetTextureStageState(0,D3DTSS_COLOROP,D3DTOP_SELECTARG1);device->SetTextureStageState(0,D3DTSS_COLORARG1,D3DTA_DIFFUSE);
    device->SetTextureStageState(0,D3DTSS_ALPHAOP,D3DTOP_SELECTARG1);device->SetTextureStageState(0,D3DTSS_ALPHAARG1,D3DTA_DIFFUSE);
    device->SetFVF(D3DFVF_XYZRHW|D3DFVF_DIFFUSE);
    assert(SUCCEEDED(device->DrawPrimitiveUP(D3DPT_TRIANGLELIST,UINT(vertices.size()/3),vertices.data(),sizeof(Vertex))));
    device->EndScene();IDirect3DSurface9 *rt=nullptr,*read=nullptr;device->GetRenderTarget(0,&rt);
    assert(SUCCEEDED(device->CreateOffscreenPlainSurface(1280,720,D3DFMT_A8R8G8B8,D3DPOOL_SYSTEMMEM,&read,nullptr)));
    assert(SUCCEEDED(device->GetRenderTargetData(rt,read)));D3DLOCKED_RECT locked;assert(SUCCEEDED(read->LockRect(&locked,nullptr,D3DLOCK_READONLY)));
    unsigned lit=0;for(int y=0;y<720;++y)for(int x=0;x<1280;++x)
    {
        unsigned const pixel=*reinterpret_cast<unsigned*>(static_cast<char*>(locked.pBits)+y*locked.Pitch+x*4);
        if(pixel&0xffffff){++lit;assert(std::abs(float(x)-layout.x)<layout.radius+4 &&
            std::abs(float(y)-layout.y)<layout.radius*layout.ellipse+24);}
    }
    read->UnlockRect();assert(lit>300);read->Release();rt->Release();device->Release();d3d->Release();DestroyWindow(wnd);
    printf("PASS native installed INI: enabled=%d sections=%d; production frame=%u lines; hidden D3D9 draw=%u visible pixels with NO scanner/contacts.\n",enabled,sections,lines,lit);
}
