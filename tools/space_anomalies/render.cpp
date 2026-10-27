// Hidden-window D3D9 HAL shader laboratory. No game process, assets or INIs modified.
#define NOMINMAX
#define _CRT_SECURE_NO_WARNINGS
#include <windows.h>
#include <d3dx9.h>
#include <algorithm>
#include <cmath>
#include <cstdint>
#include <cstdio>
#include <cstdlib>
#include <cstring>
#include <filesystem>
#include <string>
#include <vector>
#include "../../src/RP9/RP9ShaderCache.h"

struct Preset { const char* id; const char* shader; int variant; float time, inclination,yaw,exposure,distance,flare,sensor; };
#include "presets.generated.h"
static IDirect3DDevice9* dev=nullptr;
static IDirect3DVertexShader9* vs=nullptr;
static IDirect3DPixelShader9 *extract=nullptr,*blur=nullptr,*resolve=nullptr;
static IDirect3DTexture9 *hdr=nullptr,*ping=nullptr,*pong=nullptr,*finalImage=nullptr,*skyMap=nullptr;
static IDirect3DVolumeTexture9* noiseMap=nullptr;
static IDirect3DVertexDeclaration9* decl=nullptr;
static int width=1600,height=900;
static std::string output;
static void check(HRESULT h) { if(FAILED(h)){printf("FAIL HRESULT %08lx\n",h);exit(2);} }
template<class T> static void release(T*& p) { if(p){p->Release();p=nullptr;} }
static unsigned rng=830127;
static float random01() {rng^=rng<<13;rng^=rng>>17;rng^=rng<<5;return float(rng&0xffffff)/16777216.f;}
static float lattice(int x,int y,int z) {
    unsigned h=unsigned(x&31)*374761393u+unsigned(y&31)*668265263u+unsigned(z&31)*2246822519u;
    h=(h^(h>>13))*1274126177u; return float((h^(h>>16))&65535)/65535.f;
}
static float noise3(float x,float y,float z) {
    int ix=int(floorf(x)),iy=int(floorf(y)),iz=int(floorf(z));
    float u=x-ix,v=y-iy,w=z-iz;u=u*u*(3-2*u);v=v*v*(3-2*v);w=w*w*(3-2*w);
    float result=0;
    for(int k=0;k<2;++k)for(int j=0;j<2;++j)for(int i=0;i<2;++i)
        result+=lattice(ix+i,iy+j,iz+k)*(i?u:1-u)*(j?v:1-v)*(k?w:1-w);
    return result;
}
static void textures() {
    const int sw=Realistic?4096:2048,sh=sw/2;
    std::vector<float> rgb(size_t(sw)*sh*3);
    for(int y=0;y<sh;++y)for(int x=0;x<sw;++x) {
        float a=(float(x)/sw-.5f)*6.2831853f,b=float(y)/sh*3.14159265f;
        float dx=cosf(a)*sinf(b),dy=cosf(b),dz=sinf(a)*sinf(b);
        float n=noise3(dx*5+10,dy*5+10,dz*5+10)*.7f+noise3(dx*13,dy*13,dz*13)*.3f;
        float band=expf(-powf((dy+.26f*dx-.16f*dz)*5,2));
        float dust=powf(std::max(0.f,n-.25f),2)*band;
        size_t i=(size_t(y)*sw+x)*3;
        if(Realistic){
            float lanes=1-.78f*powf(noise3(dx*18+2,dy*18+4,dz*18+6),2);
            rgb[i]=.0002f+dust*.08f*lanes;rgb[i+1]=.00024f+dust*.075f*lanes;rgb[i+2]=.0003f+dust*.065f*lanes;
        }else{rgb[i]=.0015f+dust*.025f;rgb[i+1]=.002f+dust*.035f;rgb[i+2]=.004f+dust*.072f;}
    }
    for(int k=0;k<(Realistic?22000:5600);++k) {
        int cx=int(random01()*sw),cy=int((Realistic?acosf(1-2*random01())/3.14159265f:(.08f+random01()*.84f))*sh);
        float brightness=.035f+powf(random01(),5)*.8f;
        float sigma=brightness>.5f?.65f:.36f;
        float color=random01();
        for(int j=-3;j<=3;++j)for(int i=-3;i<=3;++i){
            int x=(cx+i+sw)%sw,y=cy+j;if(y<0||y>=sh)continue;
            float v=brightness*expf(-(i*i+j*j)/(sigma*sigma*2));size_t p=(size_t(y)*sw+x)*3;
            rgb[p]+=v*(.75f+color*.25f);rgb[p+1]+=v*.87f;rgb[p+2]+=v*(1-color*.3f);
        }
    }
    check(dev->CreateTexture(sw,sh,1,0,D3DFMT_A16B16G16R16F,D3DPOOL_MANAGED,&skyMap,nullptr));
    D3DLOCKED_RECT lock;check(skyMap->LockRect(0,&lock,nullptr,0));
    for(int y=0;y<sh;++y){auto* row=(D3DXFLOAT16*)((char*)lock.pBits+y*lock.Pitch);
        for(int x=0;x<sw;++x){size_t i=(size_t(y)*sw+x)*3;float v[4]={rgb[i],rgb[i+1],rgb[i+2],1};D3DXFloat32To16Array(row+x*4,v,4);}}
    check(skyMap->UnlockRect(0));
    check(dev->CreateVolumeTexture(64,64,64,1,0,D3DFMT_A8R8G8B8,D3DPOOL_MANAGED,&noiseMap,nullptr));
    D3DLOCKED_BOX box;check(noiseMap->LockBox(0,&box,nullptr,0));
    for(int z=0;z<64;++z)for(int y=0;y<64;++y)for(int x=0;x<64;++x){
        int n=int(noise3(x*.5f,y*.5f,z*.5f)*255);
        ((DWORD*)((char*)box.pBits+z*box.SlicePitch+y*box.RowPitch))[x]=D3DCOLOR_XRGB(n,n,n);
    } check(noiseMap->UnlockBox(0));
}
static ID3DXBuffer* compile(const char* file,const char* entry,const char* profile,int variant) {
    std::string path="DATA_EXTRA/SHADERS/ANOMALIES/"+std::string(file),value=std::to_string(variant);
    std::string quality=std::to_string(EpicQuality);
    D3DXMACRO macros[]={{"VARIANT",value.c_str()},{"REALISTIC_LOOK",Realistic?"1":"0"},{"EPIC_QUALITY",quality.c_str()},{nullptr,nullptr}};
    ID3DXBuffer *code=nullptr,*errors=nullptr,*assembly=nullptr,*expanded=nullptr;
    HRESULT h=D3DXPreprocessShaderFromFileA(path.c_str(),macros,nullptr,&expanded,&errors);
    if(errors){printf("%s %s: %s\n",file,entry,(char*)errors->GetBufferPointer());release(errors);}check(h);
    std::string source((char*)expanded->GetBufferPointer());release(expanded);
    std::vector<unsigned char> bytes;std::string diagnostics;bool hit=false,stored=false;
    // SM3's level-3 optimizer scales poorly with nested geodesic/volume loops.
    // Level 1 keeps the same sample budget and equations without that stall.
    h=Rp9ShaderCache::Compile(source,nullptr,entry,profile,D3DXSHADER_OPTIMIZATION_LEVEL1,&bytes,&diagnostics,&hit,&stored);
    if(!diagnostics.empty())printf("%s %s: %s\n",file,entry,diagnostics.c_str());check(h);
    check(D3DXCreateBuffer((DWORD)bytes.size(),&code));memcpy(code->GetBufferPointer(),bytes.data(),bytes.size());
    printf("CACHE %s %s %s\n",file,entry,hit?"HIT":(stored?"STORED":"UNCACHED"));
    check(D3DXDisassembleShader((DWORD*)code->GetBufferPointer(),FALSE,nullptr,&assembly));
    std::string asmPath=output+"/assembly/"+file+"_"+std::to_string(variant)+"_"+entry+".asm";
    FILE* f=fopen(asmPath.c_str(),"wb");if(!f){puts("Cannot write assembly");exit(3);}
    fwrite(assembly->GetBufferPointer(),1,assembly->GetBufferSize()-1,f);fclose(f);release(assembly);
    printf("COMPILED %s %s variant=%d bytes=%zu\n",file,entry,variant,code->GetBufferSize());return code;
}
static IDirect3DPixelShader9* pixelShader(const char* file,const char* entry,int variant=0) {
    auto* code=compile(file,entry,"ps_3_0",variant);IDirect3DPixelShader9* p=nullptr;
    check(dev->CreatePixelShader((DWORD*)code->GetBufferPointer(),&p));release(code);return p;
}
static void target(IDirect3DTexture9* texture,int w,int h) {
    IDirect3DSurface9* surface=nullptr;check(texture->GetSurfaceLevel(0,&surface));
    check(dev->SetRenderTarget(0,surface));release(surface);
    D3DVIEWPORT9 vp={0,0,DWORD(w),DWORD(h),0,1};check(dev->SetViewport(&vp));
    float frame[4]={0,float(w)/h,1.f/w,1.f/h};check(dev->SetVertexShaderConstantF(0,frame,1));
}
static void draw(IDirect3DPixelShader9* ps) {
    struct Vertex {float x,y,z,w,u,v;};
    Vertex vertices[]={{-1,1,0,1,0,0},{1,1,0,1,1,0},{-1,-1,0,1,0,1},{1,-1,0,1,1,1}};
    check(dev->SetPixelShader(ps));check(dev->DrawPrimitiveUP(D3DPT_TRIANGLESTRIP,2,vertices,sizeof(Vertex)));
}
static void render(const Preset& p,IDirect3DPixelShader9* ps,float timeOffset,float yawOffset,float flareOverride) {
    float constants[16]={p.time+timeOffset,float(width)/height,1.f/width,1.f/height,
        p.inclination,p.yaw+yawOffset,p.exposure,p.distance,flareOverride<0?p.flare:flareOverride,p.sensor,0,0,0,0,Realistic?2.5f:.9f,Realistic?.075f:.17f};
    check(dev->SetPixelShaderConstantF(0,constants,4));
    check(dev->SetTexture(0,skyMap));check(dev->SetTexture(1,noiseMap));check(dev->SetTexture(2,nullptr));check(dev->SetTexture(3,nullptr));
    check(dev->BeginScene());target(hdr,width,height);draw(ps);
    target(ping,width/4,height/4);check(dev->SetTexture(2,hdr));draw(extract);
    for(int step=0;step<3;++step){
        check(dev->SetTexture(2,nullptr));target(pong,width/4,height/4);check(dev->SetTexture(2,ping));
        float post[4]={4.f/width*(1+step),0,Realistic?2.5f:.9f,Realistic?.075f:.17f};check(dev->SetPixelShaderConstantF(3,post,1));draw(blur);
        check(dev->SetTexture(2,nullptr));target(ping,width/4,height/4);check(dev->SetTexture(2,pong));
        post[0]=0;post[1]=4.f/height*(1+step);check(dev->SetPixelShaderConstantF(3,post,1));draw(blur);
    }
    target(finalImage,width,height);check(dev->SetTexture(2,hdr));check(dev->SetTexture(3,ping));draw(resolve);
    check(dev->EndScene());check(dev->SetTexture(2,nullptr));check(dev->SetTexture(3,nullptr));
}
static void validateAndSave(const std::string& path) {
    IDirect3DSurface9 *surface=nullptr,*copy=nullptr;
    check(hdr->GetSurfaceLevel(0,&surface));check(dev->CreateOffscreenPlainSurface(width,height,D3DFMT_A16B16G16R16F,D3DPOOL_SYSTEMMEM,&copy,nullptr));
    check(dev->GetRenderTargetData(surface,copy));release(surface);
    D3DLOCKED_RECT lock;check(copy->LockRect(&lock,nullptr,D3DLOCK_READONLY));
    std::vector<float> row(size_t(width)*4);float maximum=0;double sum=0;int invalid=0;
    for(int y=0;y<height;++y){auto* bits=(const uint16_t*)((char*)lock.pBits+y*lock.Pitch);
        D3DXFloat16To32Array(row.data(),(const D3DXFLOAT16*)bits,width*4);
        // D3DX's legacy half conversion treats exponent 31 as a finite number.
        // Validate IEEE FP16 bits as well, so GPU NaN/Inf cannot pass readback.
        for(int x=0;x<width;++x)for(int c=0;c<3;++c){size_t at=size_t(x)*4+c;float v=row[at];
            if((bits[at]&0x7c00)==0x7c00||!std::isfinite(v)||v<0)++invalid;maximum=std::max(maximum,v);sum+=v;}}
    check(copy->UnlockRect());release(copy);
    printf("HDR %s finite_nonnegative=%s max=%.4f mean=%.6f\n",path.c_str(),invalid?"FAIL":"PASS",maximum,sum/(width*height*3));
    if(invalid||maximum<.01f){puts("Invalid or empty HDR output");exit(4);}
    check(finalImage->GetSurfaceLevel(0,&surface));
    check(D3DXSaveSurfaceToFileA(path.c_str(),D3DXIFF_PNG,surface,nullptr,nullptr));release(surface);
}
int main(int argc,char** argv) {
    setvbuf(stdout,nullptr,_IONBF,0);
    if(argc<2){puts("render.exe output [width height [preset-index time-offset yaw-offset flare frames step]]");return 1;}
    output=argv[1];if(argc>3){width=atoi(argv[2]);height=atoi(argv[3]);}
    if(width<64||height<64||width>4096||height>4096)return 1;
    int selected=argc>4?atoi(argv[4]):-1;
    if(selected< -1||selected>=int(sizeof(Presets)/sizeof(Presets[0])))return 1;
    float time=argc>5?float(atof(argv[5])):0,yaw=argc>6?float(atof(argv[6])):0,flare=argc>7?float(atof(argv[7])):-1;
    int frames=argc>8?atoi(argv[8]):1;float step=argc>9?float(atof(argv[9])):.1f;
    bool checks=argc>10&&atoi(argv[10])!=0;
    printf("LOOK %s quality=%d spectral-response=per-preset\n",Realistic?"realistic":"theatrical",EpicQuality);
    if(frames<1||frames>300)return 1;
    std::filesystem::create_directories(output+"/assembly");
    HWND window=CreateWindowA("STATIC","Anomaly shader lab",WS_POPUP,0,0,64,64,nullptr,nullptr,GetModuleHandle(nullptr),nullptr);
    if(!window)return 2;
    IDirect3D9* api=Direct3DCreate9(D3D_SDK_VERSION);if(!api)return 2;
    D3DADAPTER_IDENTIFIER9 adapter;check(api->GetAdapterIdentifier(0,0,&adapter));printf("GPU %s\n",adapter.Description);
    D3DPRESENT_PARAMETERS pp={};pp.Windowed=TRUE;pp.SwapEffect=D3DSWAPEFFECT_DISCARD;pp.hDeviceWindow=window;
    pp.BackBufferWidth=64;pp.BackBufferHeight=64;pp.BackBufferFormat=D3DFMT_X8R8G8B8;pp.PresentationInterval=D3DPRESENT_INTERVAL_IMMEDIATE;
    check(api->CreateDevice(0,D3DDEVTYPE_HAL,window,D3DCREATE_HARDWARE_VERTEXPROCESSING,&pp,&dev));
    D3DCAPS9 caps;check(dev->GetDeviceCaps(&caps));printf("CAPS PS=%lx slots=%lu VS=%lx\n",caps.PixelShaderVersion,caps.MaxPixelShader30InstructionSlots,caps.VertexShaderVersion);
    D3DVERTEXELEMENT9 elements[]={{0,0,D3DDECLTYPE_FLOAT4,D3DDECLMETHOD_DEFAULT,D3DDECLUSAGE_POSITION,0},{0,16,D3DDECLTYPE_FLOAT2,D3DDECLMETHOD_DEFAULT,D3DDECLUSAGE_TEXCOORD,0},D3DDECL_END()};
    check(dev->CreateVertexDeclaration(elements,&decl));check(dev->SetVertexDeclaration(decl));
    auto* code=compile("post.hlsl","VSMain","vs_3_0",0);check(dev->CreateVertexShader((DWORD*)code->GetBufferPointer(),&vs));release(code);check(dev->SetVertexShader(vs));
    extract=pixelShader("post.hlsl","PSExtract");blur=pixelShader("post.hlsl","PSBlur");resolve=pixelShader("post.hlsl","PSResolve");
    check(dev->CreateTexture(width,height,1,D3DUSAGE_RENDERTARGET,D3DFMT_A16B16G16R16F,D3DPOOL_DEFAULT,&hdr,nullptr));
    check(dev->CreateTexture(width/4,height/4,1,D3DUSAGE_RENDERTARGET,D3DFMT_A16B16G16R16F,D3DPOOL_DEFAULT,&ping,nullptr));
    check(dev->CreateTexture(width/4,height/4,1,D3DUSAGE_RENDERTARGET,D3DFMT_A16B16G16R16F,D3DPOOL_DEFAULT,&pong,nullptr));
    check(dev->CreateTexture(width,height,1,D3DUSAGE_RENDERTARGET,D3DFMT_A8R8G8B8,D3DPOOL_DEFAULT,&finalImage,nullptr));
    check(dev->SetRenderState(D3DRS_ZENABLE,FALSE));check(dev->SetRenderState(D3DRS_ZWRITEENABLE,FALSE));
    check(dev->SetRenderState(D3DRS_ALPHABLENDENABLE,FALSE));check(dev->SetRenderState(D3DRS_CULLMODE,D3DCULL_NONE));
    for(int i=0;i<4;++i){check(dev->SetSamplerState(i,D3DSAMP_MINFILTER,D3DTEXF_LINEAR));check(dev->SetSamplerState(i,D3DSAMP_MAGFILTER,D3DTEXF_LINEAR));
        check(dev->SetSamplerState(i,D3DSAMP_MIPFILTER,D3DTEXF_NONE));check(dev->SetSamplerState(i,D3DSAMP_ADDRESSU,i<2?D3DTADDRESS_WRAP:D3DTADDRESS_CLAMP));
        check(dev->SetSamplerState(i,D3DSAMP_ADDRESSV,i==1?D3DTADDRESS_WRAP:D3DTADDRESS_CLAMP));check(dev->SetSamplerState(i,D3DSAMP_ADDRESSW,D3DTADDRESS_WRAP));}
    textures();
    for(int i=0;i<int(sizeof(Presets)/sizeof(Presets[0]));++i){if(selected>=0&&i!=selected)continue;
        const auto& p=Presets[i];auto* ps=pixelShader(p.shader,"PSMain",p.variant);
        for(int frame=0;frame<frames;++frame){render(p,ps,time+step*frame,yaw,flare);
            char suffix[24]="";if(frames>1)sprintf(suffix,"_%04d",frame);
            validateAndSave(output+"/"+p.id+suffix+".png");}
        if(checks){
            render(p,ps,time+1.35f,yaw,flare);validateAndSave(output+"/"+p.id+"_time.png");
            render(p,ps,time,yaw+.65f,flare);validateAndSave(output+"/"+p.id+"_orbit.png");
            if(i==0){render(p,ps,time,yaw,flare);validateAndSave(output+"/"+p.id+"_repeat.png");}
            if(i==4){render(p,ps,time,yaw,.9f);validateAndSave(output+"/"+p.id+"_flare.png");}
        }
        release(ps);}
    dev->SetTexture(0,nullptr);dev->SetTexture(1,nullptr);dev->SetPixelShader(nullptr);dev->SetVertexShader(nullptr);dev->SetVertexDeclaration(nullptr);
    release(hdr);release(ping);release(pong);release(finalImage);release(skyMap);release(noiseMap);
    release(extract);release(blur);release(resolve);release(vs);release(decl);release(dev);release(api);DestroyWindow(window);
    puts("PASS shader compilation, HAL creation, rendering, finite HDR readback and PNG export");return 0;
}
