#include "feed_client.h"
#include <cstdio>
#include <cstdlib>

int wmain(int argc,wchar_t** argv)
{
    if(argc<2)return 2;
    unsigned mode=argc>2?static_cast<unsigned>(_wtoi(argv[2])):1;
    using Microsoft::WRL::ComPtr;
    ComPtr<ID3D11Device> device;ComPtr<ID3D11DeviceContext> context;ComPtr<ID3D11DeviceContext4> ctx4;
    D3D_FEATURE_LEVEL level;
    HRESULT hr=D3D11CreateDevice(nullptr,D3D_DRIVER_TYPE_HARDWARE,nullptr,0,nullptr,0,D3D11_SDK_VERSION,&device,&level,&context);
    if(FAILED(hr)||FAILED(context.As(&ctx4))){printf("device failed %08lx\n",hr);return 3;}
    BaseFeed::Client feed;
    bool cancel_start=argc>3&&wcscmp(argv[3],L"--cancel-startup")==0;
    bool kill_host=argc>3&&wcscmp(argv[3],L"--kill-host")==0;
    if(cancel_start)
    {
        DWORD before=0,after=0;GetProcessHandleCount(GetCurrentProcess(),&before);
        for(unsigned i=0;i<8;i++)
        {
            if(!feed.Start(device.Get(),256,256,mode,argv[1]))return 20;
            Sleep(i?100:0);ULONGLONG start=GetTickCount64();feed.Stop();
            if(GetTickCount64()-start>1500){puts("FAIL startup cancellation deadline");return 21;}
            for(auto const& texture:feed.textures)if(texture)return 22;
            context->Flush();Sleep(10);
            GetProcessHandleCount(GetCurrentProcess(),&after);
            printf("cancel %u: %lu handles\n",i,after);fflush(stdout);
            // D3D11 initializes shared-resource/driver pools on first use.
            // Measure repeated cancellations after those two warm-up cycles.
            if(i==1)before=after;
        }
        GetProcessHandleCount(GetCurrentProcess(),&after);
        if(after>before+2){printf("FAIL handle leak %lu -> %lu\n",before,after);return 23;}
        puts("PASS six startup cancellations; bounded stop, no leaked handles/textures");return 0;
    }
    if(!feed.Start(device.Get(),256,256,mode,argv[1])){puts("start failed");return 4;}
    ULONGLONG until=GetTickCount64()+90000;int ready=0;
    while((ready=feed.Poll())==0&&GetTickCount64()<until)Sleep(20);
    if(ready!=1){puts("host handshake/build failed");return 5;}
    HANDLE host=OpenProcess(SYNCHRONIZE|PROCESS_TERMINATE,FALSE,feed.HostPid());
    if(!host)return 24;
    if(kill_host)
    {
        TerminateProcess(host,9);WaitForSingleObject(host,2000);
        ULONGLONG start=GetTickCount64();
        if(feed.Evaluate(ctx4.Get(),true,50)){puts("FAIL dead host reported success");return 25;}
        feed.Stop();CloseHandle(host);
        if(GetTickCount64()-start>1000)return 26;
        puts("PASS dead helper rejected without stranding the GPU queue");return 0;
    }
    ComPtr<ID3D11UnorderedAccessView> color,depth,motion;
    if(FAILED(device->CreateUnorderedAccessView(feed.textures[BaseFeed::Color].Get(),nullptr,&color))||
       FAILED(device->CreateUnorderedAccessView(feed.textures[BaseFeed::Depth].Get(),nullptr,&depth))||
       FAILED(device->CreateUnorderedAccessView(feed.textures[BaseFeed::Motion].Get(),nullptr,&motion)))return 6;
    float d[4]={.5f,0,0,0},mv[4]={};
    context->ClearUnorderedAccessViewFloat(depth.Get(),d);context->ClearUnorderedAccessViewFloat(motion.Get(),mv);
    for(unsigned n=0;n<8;n++)
    {
        float c[4]={n/255.f,127/255.f,241/255.f,1};context->ClearUnorderedAccessViewFloat(color.Get(),c);
        if(!feed.Evaluate(ctx4.Get(),n==0,mode==1?2000:10000)){printf("evaluate failed at %u\n",n);return 7;}
        if(mode==1)
        {
            D3D11_TEXTURE2D_DESC desc;feed.textures[BaseFeed::Output]->GetDesc(&desc);
            desc.Usage=D3D11_USAGE_STAGING;desc.CPUAccessFlags=D3D11_CPU_ACCESS_READ;desc.MiscFlags=desc.BindFlags=0;
            ComPtr<ID3D11Texture2D> readback;if(FAILED(device->CreateTexture2D(&desc,nullptr,&readback)))return 8;
            context->CopyResource(readback.Get(),feed.textures[BaseFeed::Output].Get());D3D11_MAPPED_SUBRESOURCE map={};
            if(FAILED(context->Map(readback.Get(),0,D3D11_MAP_READ,0,&map)))return 9;
            bool ok=true;
            for(unsigned y=0;y<256;y++)for(unsigned x=0;x<256;x++)
            {auto p=static_cast<unsigned char*>(map.pData)+y*map.RowPitch+x*4;if(p[0]!=n||p[1]!=127||p[2]!=241||p[3]!=255)ok=false;}
            if(!ok){auto p=static_cast<unsigned char*>(map.pData);printf("pixel mismatch frame %u: %u %u %u %u\n",n,p[0],p[1],p[2],p[3]);}
            context->Unmap(readback.Get(),0);if(!ok)return 10;
        }
    }
    feed.Stop();
    if(WaitForSingleObject(host,0)!=WAIT_OBJECT_0)return 27;
    CloseHandle(host);
    for(auto const& texture:feed.textures)if(texture)return 11;
    printf("PASS mode=%u: 8 same-frame GPU roundtrips; resources retired\n",mode);
    return 0;
}
