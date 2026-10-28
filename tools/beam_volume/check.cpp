#ifdef BEAM_ROUTE
#include "RP9Ex.h"
#endif
#include "RP9ShaderCache.h"
#include "RP9BeamMesh.h"
#include <algorithm>
#include <cstdio>
#include <cstdlib>
#include <fstream>

static void Require(bool b,const char* why) { if(!b){printf("FAIL: %s\n",why);exit(3);} }
static void CheckAt(HRESULT h,int line) { if(FAILED(h)){printf("HRESULT: %08lx at line %d\n",h,line);exit(2);} }
#define Check(h) CheckAt((h),__LINE__)
using Rp9BeamMesh::Point;
int main(int argc, char** argv)
{
    SetErrorMode(SEM_FAILCRITICALERRORS|SEM_NOGPFAULTERRORBOX);
    HWND window=CreateWindowA("STATIC","beam fixture",WS_POPUP,0,0,128,128,0,0,GetModuleHandle(0),0);
    auto* api=Direct3DCreate9(D3D_SDK_VERSION);Require(api!=nullptr,"D3D9");
    IDirect3DDevice9* device=nullptr;
    D3DPRESENT_PARAMETERS pp={};pp.Windowed=1;pp.SwapEffect=D3DSWAPEFFECT_DISCARD;
    pp.BackBufferWidth=pp.BackBufferHeight=128;pp.BackBufferFormat=D3DFMT_A8R8G8B8;
    pp.EnableAutoDepthStencil=1;pp.AutoDepthStencilFormat=D3DFMT_D24S8;
    Check(api->CreateDevice(0,D3DDEVTYPE_HAL,window,D3DCREATE_HARDWARE_VERTEXPROCESSING,&pp,&device));
    std::ifstream file("DATA_EXTRA/SHADERS/beam_volume.hlsl",std::ios::binary);
    std::string source((std::istreambuf_iterator<char>(file)),std::istreambuf_iterator<char>());
    auto compile=[&](const char* entry,const char* profile){
        std::vector<unsigned char> code;std::string errors;bool hit=false,stored=false;
        HRESULT hr=Rp9ShaderCache::Compile(source,nullptr,entry,profile,0,&code,&errors,&hit,&stored);
        if(FAILED(hr))printf("%s\n",errors.c_str());Check(hr);return code;};
    auto vc=compile("VSMain","vs_3_0"),pc=compile("PSMain","ps_3_0");
    IDirect3DVertexShader9* vs=nullptr;IDirect3DPixelShader9* ps=nullptr;
    Check(device->CreateVertexShader((DWORD*)vc.data(),&vs));Check(device->CreatePixelShader((DWORD*)pc.data(),&ps));
    IDirect3DTexture9* atlas=nullptr;
    Check(device->CreateTexture(1,1,1,0,D3DFMT_A8R8G8B8,D3DPOOL_MANAGED,&atlas,0));
    auto texture=[&](DWORD color){D3DLOCKED_RECT l;Check(atlas->LockRect(0,&l,0,0));*(DWORD*)l.pBits=color;atlas->UnlockRect(0);};
    texture(0xffffffff);device->SetTexture(0,atlas);
    D3DXMATRIX projection,inverse;
    D3DXMatrixPerspectiveFovLH(&projection,1.0f,1,.1f,100);
    D3DXMatrixInverse(&inverse,nullptr,&projection);
    float style[4]={.18f,.3f,1,1},fog[4]={};
    device->SetVertexShader(vs);device->SetPixelShader(ps);
    device->SetFVF(D3DFVF_XYZ|D3DFVF_NORMAL|D3DFVF_TEX4|
        D3DFVF_TEXCOORDSIZE4(0)|D3DFVF_TEXCOORDSIZE2(1)|D3DFVF_TEXCOORDSIZE4(2)|D3DFVF_TEXCOORDSIZE2(3));
    device->SetVertexShaderConstantF(0,&projection.m[0][0],4);
    device->SetPixelShaderConstantF(5,fog,1);
    device->SetRenderState(D3DRS_ZENABLE,TRUE);device->SetRenderState(D3DRS_ZWRITEENABLE,FALSE);
    device->SetRenderState(D3DRS_ZFUNC,D3DCMP_LESSEQUAL);device->SetRenderState(D3DRS_CULLMODE,D3DCULL_NONE);
    device->SetRenderState(D3DRS_ALPHABLENDENABLE,TRUE);
    device->SetRenderState(D3DRS_SRCBLEND,D3DBLEND_ONE);device->SetRenderState(D3DRS_DESTBLEND,D3DBLEND_ONE);device->SetRenderState(D3DRS_ALPHATESTENABLE,FALSE);
    IDirect3DSurface9 *target=nullptr,*read=nullptr;Check(device->GetRenderTarget(0,&target));
    Check(device->CreateOffscreenPlainSurface(128,128,D3DFMT_A8R8G8B8,D3DPOOL_SYSTEMMEM,&read,0));
#ifdef BEAM_ROUTE
    auto* pipe=new FDirectX9();pipe->Outer_=&pipe->Inner_;pipe->Device_=device;pipe->DeviceReady_=1;
    auto* ex=pipe->Ex_;ex->VolumeBeamEnabled=true;ex->VolumeBeamVs=vs;vs->AddRef();
    ex->VolumeBeamPs=ps;ps->AddRef();ex->VolumeBeamCore=style[0];ex->VolumeBeamStrength=style[1];
    ex->VolumeBeamNodes="*";
    D3DXMATRIX identity;D3DXMatrixIdentity(&identity);
    memcpy(pipe->Transforms_.World.Values,&identity,64);memcpy(pipe->Transforms_.View.Values,&identity,64);
    memcpy(pipe->Transforms_.Projection.Values,&projection,64);
    Check(device->GetViewport(&pipe->ViewportCache_));pipe->bViewportRectValid_=pipe->bDepthRangeValid_=1;
    pipe->RenderStates_.MarkDirty(D3DRS_FILLMODE,D3DFILL_SOLID);
    pipe->RenderStates_.MarkDirty(D3DRS_FOGENABLE,FALSE);
    pipe->RenderStates_.MarkDirty(D3DRS_COLORWRITEENABLE,15);
#endif
    float textureU=.5f, textureV=.5f;
    DWORD sourceBlend=D3DBLEND_SRCALPHA;
    const char* beamName="test_beam";
    bool fadeTrail=false;
    float fadeDistance=10;
    auto renderPath=[&](std::vector<Point> const& path,float depth=1.f){
        bool inside=false;
        auto mesh=Rp9BeamMesh::Build(path,textureU,textureV,inside);
        Require(!mesh.empty(),"mesh generated");
        style[3]=inside?-1.f:1.f;
        style[2]=sourceBlend==D3DBLEND_SRCALPHA?1.f:0.f;
        float cameraFade[4]={-projection._43/projection._33,
            fadeTrail && fadeDistance>0 ? 1.f/fadeDistance : 0.f,0,0};
        Check(device->SetPixelShaderConstantF(6,cameraFade,1));
        for(auto const& vertex:mesh)
            Require(std::isfinite(vertex.position.x+vertex.position.y+vertex.position.z+
                                  vertex.normal.x+vertex.normal.y+vertex.normal.z),"finite connected mesh");
        Check(device->Clear(0,0,D3DCLEAR_TARGET|D3DCLEAR_ZBUFFER,0xff000000,depth,0));
        Check(device->SetPixelShaderConstantF(4,style,1));Check(device->BeginScene());
#ifdef BEAM_ROUTE
        std::vector<FRPVolumeBeamPoint> points;
        for(auto const& q:path){
            DWORD c=D3DCOLOR_COLORVALUE(q.colour.x,q.colour.y,q.colour.z,q.colour.w);
            points.push_back({{q.position.x,q.position.y,q.position.z},q.radius,c,textureV});
        }
        ex->VolumeBeamTrailFade=fadeDistance;
        Require(pipe->VolumeBeamAvailable(beamName,sourceBlend,D3DBLEND_ONE)==GR_OK,"RP9 beam eligibility");
        Require(pipe->DrawVolumeBeam(points.data(),ULONG(points.size()),textureU,sourceBlend)==GR_OK,"RP9 beam submission");
#else
        Check(device->DrawPrimitiveUP(D3DPT_TRIANGLELIST,UINT(mesh.size()/3),mesh.data(),sizeof(Rp9BeamMesh::Vertex)));
#endif
        Check(device->EndScene());
        Check(device->GetRenderTargetData(target,read));D3DLOCKED_RECT l;Check(read->LockRect(&l,0,D3DLOCK_READONLY));
        std::vector<DWORD> result(128*128);
        for(int y=0;y<128;++y)memcpy(result.data()+y*128,(char*)l.pBits+y*l.Pitch,128*4);
        read->UnlockRect();return result;};
    auto render=[&](D3DXVECTOR3 a,D3DXVECTOR3 b,float radius,float depth=1.f,DWORD colour=0xff50a0ff){
        D3DXVECTOR4 c(float((colour>>16)&255)/255,float((colour>>8)&255)/255,float(colour&255)/255,float(colour>>24)/255);
        return renderPath({{a,radius,c},{b,radius,c}},depth);};
    auto energy=[](std::vector<DWORD> const& v){unsigned total=0;for(auto p:v)total+=(p&255)+((p>>8)&255)+((p>>16)&255);return total;};
    if(argc>1)
    {
        std::ifstream capture(argv[1]);Require(bool(capture),"capture exists");
        size_t count;int recordedInside;
        capture>>count>>textureU>>textureV>>sourceBlend>>recordedInside;
        Require(count>0 && count<65536,"capture point count");
        for(int i=0;i<16;++i)capture>>(&projection.m[0][0])[i];
        std::vector<Point> path(count);
        for(auto& q:path)capture>>q.position.x>>q.position.y>>q.position.z>>q.radius>>
            q.colour.x>>q.colour.y>>q.colour.z>>q.colour.w;
        Require(bool(capture),"capture data parsed");
        std::string label;unsigned state,value;
        while(capture>>label>>state>>value)
        {
#ifdef BEAM_ROUTE
            if(label=="rs" && state<FRp9RenderStateCache::StateCount)pipe->RenderStates_.MarkDirty(state,value);
#endif
        }
        std::string textureFile=argv[1];textureFile.replace(textureFile.size()-4,4,".dds");
        IDirect3DTexture9* realTexture=nullptr;
        Check(D3DXCreateTextureFromFileA(device,textureFile.c_str(),&realTexture));
        Check(device->SetTexture(0,realTexture));realTexture->Release();
        device->SetVertexShaderConstantF(0,&projection.m[0][0],4);
        style[2]=sourceBlend==D3DBLEND_SRCALPHA?1.f:0.f;
#ifdef BEAM_ROUTE
        memcpy(pipe->Transforms_.Projection.Values,&projection,64);
#endif
        auto pixels=renderPath(path);
        printf("CAPTURE: %zu points, energy %u, first (%g %g %g) radius %g, last (%g %g %g) radius %g\n",
            count,energy(pixels),path.front().position.x,path.front().position.y,path.front().position.z,path.front().radius,
            path.back().position.x,path.back().position.y,path.back().position.z,path.back().radius);
#ifdef BEAM_ROUTE
        const char* output="src/obj/beam_volume/replay_route.ppm";
#else
        const char* output="src/obj/beam_volume/replay_shader.ppm";
#endif
        std::ofstream image(output,std::ios::binary);image<<"P6\n128 128\n255\n";
        for(DWORD c:pixels){char rgb[3]={char(c>>16),char(c>>8),char(c)};image.write(rgb,3);}
        return 0;
    }
    auto side=render({-1,0,4},{1,0,4},.2f);Require(energy(side)>10000,"side view visible");
    D3DXVECTOR4 tint(80.f/255,160.f/255,1,1);
    auto segmented=renderPath({{{-1,0,4},.2f,tint},{{-.3f,0,4},.2f,tint},
                               {{0,0,4},.2f,tint},{{.1f,0,4},.2f,tint},{{1,0,4},.2f,tint}});
    auto same=[&](auto const& a,auto const& b){for(size_t i=0;i<a.size();++i)for(int shift:{0,8,16})
        Require(abs(int((a[i]>>shift)&255)-int((b[i]>>shift)&255))<=2,
            "adding particles must not add bands, gaps or cap brightening");};
    same(side,segmented);
    same(render({0,0,3},{0,0,6},.3f),renderPath({{{0,0,3},.3f,tint},{{0,0,4},.3f,tint},{{0,0,5},.3f,tint},{{0,0,6},.3f,tint}}));
    same(render({-1,0,3},{1,0,6},.2f),renderPath({{{-1,0,3},.2f,tint},{{0,0,4.5f},.2f,tint},{{1,0,6},.2f,tint}}));
    same(side,renderPath({{{-1,0,4},.2f,tint},{{-1,0,4},.2f,tint},{{1,0,4},.2f,tint}}));
    auto curve=renderPath({{{-1,-.5f,4},.18f,tint},{{-.4f,.2f,4},.23f,tint},
                           {{.4f,.2f,4},.23f,tint},{{1,-.5f,4},.18f,tint}});
    Require(energy(curve)>10000,"curved tapered beam visible");
    auto axial=render({0,0,3},{0,0,6},.3f);Require(energy(axial)>1000,"axial view visible, no flat-plane disappearance");
    auto grazing=render({-.5f,0,2},{1.f,0,20},.15f);
    printf("Grazing body centre: %lu\n",grazing[64*128+64]&255);
    Require((grazing[64*128+64]&255)>40,"body stays bright when looking almost along the beam, not just its end cap");
    for(float degrees : {5.f,15.f,30.f,60.f,85.f})
    {
        float a=degrees*Rp9BeamMesh::Pi/180;
        D3DXVECTOR3 offset(3*std::sin(a),0,3*std::cos(a)),centre(0,0,8);
        auto pixels=render(centre-offset,centre+offset,.15f);
        Require((pixels[64*128+64]&255)>120,"continuous bright core across grazing and side camera angles");
    }
    // Radial image must be symmetric about both diagonals: a crossed beam is not.
    unsigned worst=0;
    for(int y=48;y<80;++y)for(int x=48;x<80;++x)
        worst=(std::max)(worst,unsigned(abs(int(axial[y*128+x]&255)-int(axial[x*128+y]&255))));
    Require(worst<=2,"axial radial symmetry");
    Require((axial[64*128+64]&255)>(axial[64*128+70]&255),"bright core and soft falloff");
    auto wideEnd=render({0,0,3},{0,0,6},.5f);
    printf("End centre / halo: %lu / %lu\n",wideEnd[64*128+64]&255,wideEnd[64*128+76]&255);
    Require((wideEnd[64*128+76]&255)<(wideEnd[64*128+64]&255)/4,
        "end profile must fade radially, not form a uniformly glowing disc");
    Require(energy(render({-1,0,4},{1,0,4},.2f,.5f))==0,"real capsule depth occluded by foreground geometry");
    Require(energy(render({0,0,-1},{0,0,-3},.3f))==0,"behind-camera capsule rejected");
    Require(energy(render({0,0,.05f},{0,0,2},.3f))>0,"near-plane crossing and camera inside capsule");
    Require(energy(render({0,0,3},{0,0,3},.3f))>0,"zero length becomes a sphere");
    Require(energy(render({-1,0,4},{1,0,4},.2f,1,0x0050a0ff))==0,"authored alpha zero stays invisible");
    for(DWORD blend : {DWORD(D3DBLEND_SRCALPHA),DWORD(D3DBLEND_ONE)})
    {
        sourceBlend=blend;
        for(float distance : {.01f,2.5f,5.f,10.f,15.f})
        {
            float z=.1f+distance;
            auto drawNear=[&](){return render({0,0,z},{0,0,z*1.2f},z*.06f);};
            beamName="gf_br_smallengine01TRAIL.app";fadeTrail=true;fadeDistance=0;
            auto baseline=drawNear();
            fadeDistance=10;auto faded=drawNear();
            float t=(std::min)(1.f,distance/10),factor=t*t*(3-2*t);
            Require(std::abs(float(faded[64*128+64]&255)-float(baseline[64*128+64]&255)*factor)<=2,
                "trail fades smoothly from the actual near plane for both additive blends");
            // Alternate draws: the prior trail's classification/constants must
            // never attenuate the ordinary Sphere laser drawn after it.
            beamName="gf_alien_laser_on_beam.app";fadeTrail=false;
            same(baseline,drawNear());
        }
    }
    sourceBlend=D3DBLEND_SRCALPHA;beamName="test_beam";fadeTrail=false;
    puts("PASS: trail-only camera fade, disabled setting, distance ramp, ONE/ONE, SRCALPHA/ONE, Sphere laser isolation");
    texture(0xff000000);Require(energy(render({-1,0,4},{1,0,4},.2f))==0,"black authored atlas stays invisible");
    std::ofstream image("src/obj/beam_volume/check.ppm",std::ios::binary);image<<"P6\n384 128\n255\n";
    for(int y=0;y<128;++y)for(int x=0;x<384;++x){DWORD c=x<128?side[y*128+x]:x<256?axial[y*128+x-128]:curve[y*128+x-256];
        char rgb[3]={char(c>>16),char(c>>8),char(c)};image.write(rgb,3);}
    puts("PASS: connected tube; subdivision invariance in side/axial/oblique views; curved taper, axial symmetry, core, depth occlusion, near plane, behind camera, zero length, alpha and atlas masks");
    device->SetVertexShader(nullptr);device->SetPixelShader(nullptr);device->SetTexture(0,nullptr);
#ifdef BEAM_ROUTE
    pipe->ExReleaseAllGpu();pipe->Device_=nullptr;pipe->DeviceReady_=0;delete pipe;
    puts("PASS: actual RP9 draw route");
#endif
    read->Release();target->Release();atlas->Release();vs->Release();ps->Release();device->Release();api->Release();DestroyWindow(window);
}
