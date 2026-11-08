#define main WarpFixtureMain
#include "../check_ship_warp_render.cpp"
#undef main
#include "../../src/freelancer/Client/cloak_geometry.h"
#include <string>
static std::vector<CloakGeometry::Vertex> Hull;
static float CV[56],CP[16];
static void LoadMeshes()
{
    FILE* f=fopen("src/obj/cloak_visual/meshes.bin","rb");Require(f!=nullptr,"mesh fixtures available");
    unsigned count=0;fread(&count,4,1,f);unsigned valid=0;
    for(unsigned i=0;i<count;++i){
        unsigned sizes[2];CloakGeometry::Part part;fread(sizes,4,2,f);fread(&part,sizeof(part),1,f);
        std::string name(sizes[0],' ');std::vector<unsigned char> data(sizes[1]);
        fread(&name[0],1,name.size(),f);fread(data.data(),1,data.size(),f);
        std::vector<CloakGeometry::Vertex> decoded;
        if(!CloakGeometry::Decode(data.data(),data.size(),part,decoded)){
            printf("FAIL decode %s (%u,%u,%u,%u,%u,%u)\n",name.c_str(),part.VertexStart,part.VertexCount,part.IndexStart,part.IndexCount,part.GroupStart,part.GroupCount);exit(4);
        }
        ++valid;
        if(Hull.empty()&&name.find("Li_fighter_lod1021021183448.3db/MultiLevel/Level0")!=std::string::npos)Hull=decoded;
        // A truncated buffer and a reference outside its library must be rejected.
        if(CloakGeometry::Decode(data.data(),15,part,decoded)){puts("FAIL truncated header");exit(4);}
        auto invalid=part;invalid.VertexStart=100000;
        if(CloakGeometry::Decode(data.data(),data.size(),invalid,decoded)){puts("FAIL out-of-range part");exit(4);}
    }
    fclose(f);printf("PASS decoded %u actual ship part/LOD records; invalid references rejected\n",valid);
    Require(!Hull.empty(),"actual Liberty fighter geometry selected");
    float radius=0;for(auto& v:Hull)radius=std::max(radius,std::sqrt(v.P[0]*v.P[0]+v.P[1]*v.P[1]+v.P[2]*v.P[2]));
    for(auto& v:Hull)for(auto& p:v.P)p*=32/radius;
}
static void CloakCompile()
{
    Compile();
    for(int i=0;i<2;++i){
        ID3DXBuffer *code=nullptr,*error=nullptr;HRESULT r=D3DXCompileShaderFromFileA("DATA_EXTRA/SHADERS/cloak_refraction.hlsl",nullptr,nullptr,i?"PSMain":"VSMain",i?"ps_3_0":"vs_3_0",0,&code,&error,nullptr);
        if(error){puts((char*)error->GetBufferPointer());error->Release();}Check(r);
        if(i){Warp->Release();Check(D->CreatePixelShader((DWORD*)code->GetBufferPointer(),&Warp));}
        else{VS->Release();Check(D->CreateVertexShader((DWORD*)code->GetBufferPointer(),&VS));}code->Release();
    }
}
static void Setup(bool side,int partition)
{
    Camera(side);memcpy(CV,VC,sizeof(VC));
    CV[34]=partition?.1f:0;CV[35]=partition?1.f:.9f;
    CV[36]=CV[41]=CV[46]=1;CV[48]=VC[3];CV[49]=VC[7];CV[50]=-VC[11];CV[51]=32;
    // View translation is carried by Centre, as in production.
    CV[3]=CV[7]=CV[11]=0;CV[52]=3;CV[53]=1;CV[54]=1;CV[55]=.4f;
    float params[]={3,1,1.f/W,1.f/H,1,1,32,.4f,1,1000,CV[34],CV[35],.5f/W,.5f/H,1-.5f/W,1-.5f/H};memcpy(CP,params,sizeof(CP));
}
static std::vector<DWORD> DrawCloak(char const* name=nullptr,float gain=1,float depth=1,bool bars=false,bool mask=false)
{
    D3DVIEWPORT9 vp={0,0,W,H,0,1};float quad[]={-1,-1,0,1,1,-1,0,1,-1,1,0,1,1,1,0,1};
    auto screen=[&](IDirect3DPixelShader9* shader){D->SetVertexShader(ScreenVS);D->SetPixelShader(shader);D->SetFVF(D3DFVF_XYZW);Check(D->DrawPrimitiveUP(D3DPT_TRIANGLESTRIP,2,quad,16));};
    D->SetRenderState(D3DRS_ZENABLE,FALSE);D->SetRenderState(D3DRS_ZWRITEENABLE,FALSE);D->SetRenderState(D3DRS_ALPHABLENDENABLE,FALSE);D->SetRenderState(D3DRS_CULLMODE,D3DCULL_NONE);
    D->SetDepthStencilSurface(nullptr);D->SetRenderTarget(0,RT);D->SetViewport(&vp);Check(D->Clear(0,nullptr,D3DCLEAR_TARGET,0xff182838,1,0));Check(D->BeginScene());
    float settings[]={float(Marker),0,depth,ProtectMarker?CP[10]+(CP[11]-CP[10])*(1000.f-1000.f/60)/999:1.f};
    D->SetPixelShaderConstantF(0,settings,1);if(PatternOn)screen(Pattern);Check(D->EndScene());
    IDirect3DSurface9* copy=nullptr;SceneCopy->GetSurfaceLevel(0,&copy);Check(D->StretchRect(RT,nullptr,copy,nullptr,D3DTEXF_NONE));copy->Release();
    IDirect3DSurface9* z=nullptr;Z->GetSurfaceLevel(0,&z);D->SetRenderTarget(0,z);Check(D->BeginScene());D->SetPixelShaderConstantF(0,settings,1);screen(DepthBackground);Check(D->EndScene());z->Release();
    D->SetRenderTarget(0,RT);Check(D->BeginScene());D->SetVertexShader(VS);D->SetVertexShaderConstantF(0,CV,14);D->SetFVF(D3DFVF_XYZ|D3DFVF_NORMAL);
    CP[4]=gain;CP[13]=bars?.2f:.5f/H;CP[15]=bars?.8f:1-.5f/H;D->SetPixelShaderConstantF(0,CP,4);D->SetTexture(0,Z);D->SetTexture(1,SceneCopy);
    for(int i=0;i<2;++i){D->SetSamplerState(i,D3DSAMP_MINFILTER,i?D3DTEXF_LINEAR:D3DTEXF_POINT);D->SetSamplerState(i,D3DSAMP_MAGFILTER,i?D3DTEXF_LINEAR:D3DTEXF_POINT);D->SetSamplerState(i,D3DSAMP_ADDRESSU,D3DTADDRESS_CLAMP);D->SetSamplerState(i,D3DSAMP_ADDRESSV,D3DTADDRESS_CLAMP);}
    D->SetRenderState(D3DRS_ALPHABLENDENABLE,TRUE);D->SetRenderState(D3DRS_SRCBLEND,D3DBLEND_ONE);D->SetRenderState(D3DRS_DESTBLEND,D3DBLEND_INVSRCALPHA);D->SetPixelShader(mask?White:Warp);
    Check(D->DrawPrimitiveUP(D3DPT_TRIANGLELIST,UINT(Hull.size()/3),Hull.data(),sizeof(Hull[0])));Check(D->EndScene());D->SetTexture(0,nullptr);D->SetTexture(1,nullptr);
    Check(D->GetRenderTargetData(RT,CPU));if(name){std::string path=std::string("src/obj/cloak_visual/")+name+".png";Check(D3DXSaveSurfaceToFileA(path.c_str(),D3DXIFF_PNG,CPU,nullptr,nullptr));}
    D3DLOCKED_RECT lock;CPU->LockRect(&lock,nullptr,D3DLOCK_READONLY);std::vector<DWORD> pixels(W*H);for(int y=0;y<H;++y)memcpy(pixels.data()+y*W,(char*)lock.pBits+y*lock.Pitch,W*4);CPU->UnlockRect();return pixels;
}
int main()
{
    CreateDirectoryA("src/obj/ship_warp_check",nullptr);LoadMeshes();
    auto* api=Direct3DCreate9(D3D_SDK_VERSION);Require(api!=nullptr,"D3D9 available");
    HWND window=CreateWindowA("STATIC","cloak check",WS_POPUP,0,0,64,64,nullptr,nullptr,GetModuleHandle(nullptr),nullptr);
    D3DPRESENT_PARAMETERS pp={};pp.Windowed=TRUE;pp.SwapEffect=D3DSWAPEFFECT_DISCARD;pp.BackBufferWidth=64;pp.BackBufferHeight=64;pp.BackBufferFormat=D3DFMT_A8R8G8B8;
    Check(api->CreateDevice(0,D3DDEVTYPE_HAL,window,D3DCREATE_HARDWARE_VERTEXPROCESSING,&pp,&D));CloakCompile();
    D3DADAPTER_IDENTIFIER9 adapter;api->GetAdapterIdentifier(0,0,&adapter);printf("GPU: %s\n",adapter.Description);
    Check(D->CreateRenderTarget(W,H,D3DFMT_A8R8G8B8,D3DMULTISAMPLE_NONE,0,FALSE,&RT,nullptr));Check(D->CreateOffscreenPlainSurface(W,H,D3DFMT_A8R8G8B8,D3DPOOL_SYSTEMMEM,&CPU,nullptr));
    Check(D->CreateTexture(W,H,1,D3DUSAGE_RENDERTARGET,D3DFMT_R32F,D3DPOOL_DEFAULT,&Z,nullptr));Check(D->CreateTexture(W,H,1,D3DUSAGE_RENDERTARGET,D3DFMT_A8R8G8B8,D3DPOOL_DEFAULT,&SceneCopy,nullptr));PatternOn=true;
    for(int partition=0;partition<2;++partition)for(int side=0;side<2;++side)for(float cloak:{.5f,1.f}){
        Setup(side!=0,partition);CV[53]=CP[1]=cloak;
        auto base=DrawCloak(nullptr,0),effect=DrawCloak(side?"side":"front");Require(Changes(base,effect)>30,"actual ship refracts while fading and fully cloaked");
        Require(Changes(effect,DrawCloak())==0,"pause is pixel exact");CV[52]=CP[0]=3.15f;Require(Changes(effect,DrawCloak())>20,"multidirectional waves advance");CV[52]=CP[0]=3;
        Require(Changes(base,DrawCloak(nullptr,1,0))==0,"foreground completely occludes refraction");
        if(!partition)Require(Changes(base,DrawCloak(nullptr,1,.95f))==0,"cockpit depth partition protected");
        auto mask=DrawCloak(nullptr,1,1,false,true);int outside=0;for(int i=0;i<W*H;++i)if(mask[i]==base[i])outside+=effect[i]!=base[i];Require(outside==0,"no distortion outside deformed ship silhouette");
        auto bars=DrawCloak(nullptr,1,1,true);int leaks=0;for(int y=0;y<H;++y)if(y<H*.2f-2||y>H*.8f+2)for(int x=0;x<W;++x)leaks+=bars[y*W+x]!=base[y*W+x];Require(leaks==0,"viewport bounds respected");
        CV[52]=CP[0]=0;auto zero=DrawCloak();CV[52]=CP[0]=96;Require(Changes(zero,DrawCloak())<20,"96-second animation wrap continuous");CV[52]=CP[0]=3;
        CV[53]=CP[1]=0;Require(Changes(base,DrawCloak())==0,"uncloaked ship has no effect");CV[53]=CP[1]=cloak;
        int delta=-1;for(int i=0;i<W*H;++i){int d=abs(int(effect[i]&255)-int(base[i]&255));if(d>delta){delta=d;Marker=i%W;}}
        auto markedbase=DrawCloak(nullptr,0),marked=DrawCloak();int changed=0,smear=0;
        auto magenta=[](DWORD c){return int((c>>16)&255)>int((c>>8)&255)+20&&int(c&255)>int((c>>8)&255)+20;};
        for(int i=0;i<W*H;++i)if(magenta(markedbase[i]))changed+=markedbase[i]!=marked[i];else smear+=magenta(marked[i]);
        Require(changed==0&&smear==0,"displaced source footprint protects foreground colours");
        ProtectMarker=false;auto unprotected=DrawCloak();int control=0;for(int i=0;i<W*H;++i)control+=!magenta(markedbase[i])&&magenta(unprotected[i]);Require(control>0,"negative control samples foreground without depth protection");ProtectMarker=true;Marker=-1;
    }
    Setup(true,0);PatternOn=false;auto base=DrawCloak(nullptr,0),effect=DrawCloak("uniform");int added=0;for(int i=0;i<W*H;++i)for(int c=0;c<3;++c)added+=abs(int((base[i]>>(8*c))&255)-int((effect[i]>>(8*c))&255))>1;Require(added==0,"uniform background receives no tint or glow");
    PatternOn=true;for(int i=0;i<48;++i){CV[52]=CP[0]=3+i/8.f;std::string name="frame_"+std::to_string(i);DrawCloak(name.c_str());}
    puts("PASS all cloak refraction checks");return 0;
}
