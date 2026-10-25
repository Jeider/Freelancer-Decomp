// D3D9 HAL renders of the production shader. Synthetic scene, not in-game captures.
#define main JumpHoleFixtureMain
#include "check_jumphole_render.cpp"
#undef main
#include "../src/freelancer/Client/jumpgate_visual_state.h"
#include "../src/freelancer/Client/jumpgate_visual_geometry.h"
#include <chrono>
static IDirect3DPixelShader9* GateGlow=nullptr;
static IDirect3DPixelShader9* GateDonuts=nullptr;
static bool AlternateGate=false;
static float GateDonutSource[4]={1.039f,-.1357f,120.4996f+JumpGateDonutEmitterOffsetZ,1};
static IDirect3DPixelShader9* GateInflowPS=nullptr;
static IDirect3DVertexShader9* GateInflowVS=nullptr;
static bool InflowEnabled=true;
static float GateSource[4]={1.039f,-.1356f,-490.1961f,1};
static bool LensOnly=false;
static float GatePortal[4]={1.039f,-.8785f,300,195};
static float GatePortalRows[12]={1,0,0,0,0,1,0,0,0,0,1,0};
static float GatePlasma[4]={1.039f,-.1357f,-92.9682f,1};
static float GateRings[4]={130,190,.5235987756f,-.3926990817f};
static float GateTint[4]={160.f/303,1,160.f/303,1}; // gate_tunnel_edge layer0 + 0.6 layer1
static void GateDraw()
{
    Draw(); // opaque lens from the scene snapshot
    if(LensOnly)return;
    Check(Dev->SetPixelShader(AlternateGate?GateDonuts:GateGlow));
    Dev->SetDepthStencilSurface(nullptr);Dev->SetRenderState(D3DRS_ZENABLE,FALSE);
    Dev->SetRenderState(D3DRS_ALPHABLENDENABLE,TRUE);
    Dev->SetRenderState(D3DRS_SRCBLEND,D3DBLEND_ONE);
    Dev->SetRenderState(D3DRS_DESTBLEND,D3DBLEND_INVSRCALPHA);
    Dev->SetRenderState(D3DRS_BLENDOP,D3DBLENDOP_ADD);
    Dev->SetTexture(0,SceneColor);Dev->SetTexture(1,SceneDepth);
    Vertex q[]={{{-1,-1,0},0xffffffff,{0,1}},{{1,-1,0},0xffffffff,{1,1}},
        {{-1,1,0},0xffffffff,{0,0}},{{1,1,0},0xffffffff,{1,0}}};
    Check(Dev->DrawPrimitiveUP(D3DPT_TRIANGLESTRIP,2,q,sizeof(Vertex)));
    if(InflowEnabled) {
        float saved[68];Check(Dev->GetVertexShaderConstantF(0,saved,17));
        std::vector<FJumpHoleVertex> trails;
        BuildJumpGateInflow(OC[0],GateSource,GatePortal,GatePortalRows,OC+16,trails);
        Check(Dev->SetVertexShader(GateInflowVS));Check(Dev->SetPixelShader(GateInflowPS));
        Check(Dev->SetVertexShaderConstantF(0,OC,12));
        Check(Dev->SetVertexShaderConstantF(16,saved+28,1));
        Dev->SetRenderState(D3DRS_DESTBLEND,D3DBLEND_ONE);
        Check(Dev->DrawPrimitiveUP(D3DPT_TRIANGLELIST,UINT(trails.size()/3),trails.data(),sizeof(FJumpHoleVertex)));
        // Fixture Camera stores its projection in c3..c6; preserve it across draws.
        Check(Dev->SetVertexShaderConstantF(0,saved,17));
    }
    Dev->SetTexture(0,nullptr);Dev->SetTexture(1,nullptr);Dev->SetDepthStencilSurface(Depth);
}
static std::vector<DWORD> GateRender(const char* name=nullptr,bool background=false,bool blocker=false,bool cockpit=false)
{
    DepthTexture(blocker,cockpit);
    Check(Dev->Clear(0,nullptr,D3DCLEAR_TARGET|D3DCLEAR_ZBUFFER,0xff000000,1,0));Check(Dev->BeginScene());
    if(background)Backdrop();
    if(blocker){D3DRECT area={W/4,H/4,W*3/4,H*3/4};Check(Dev->Clear(1,&area,D3DCLEAR_TARGET,0xffff00ff,1,0));}
    if(cockpit){D3DRECT area={0,H*3/4+1,W,H};Check(Dev->Clear(1,&area,D3DCLEAR_TARGET,0xff00ff00,1,0));}
    Check(Dev->EndScene());CopyScene();Check(Dev->BeginScene());GateDraw();Check(Dev->EndScene());
    Check(Dev->GetRenderTargetData(Target,Cpu));
    if(name){std::string file=std::string(Out)+name+".png";Check(D3DXSaveSurfaceToFileA(file.c_str(),D3DXIFF_PNG,Cpu,nullptr,nullptr));}
    D3DLOCKED_RECT r;Check(Cpu->LockRect(&r,nullptr,D3DLOCK_READONLY));std::vector<DWORD> a(W*H);
    for(int y=0;y<H;++y)memcpy(a.data()+y*W,(char*)r.pBits+y*r.Pitch,W*4);Check(Cpu->UnlockRect());return a;
}
#define Render GateRender

static void GateParams(float age=6,float time=8,float gain=1,float optics=1)
{
    OpticsParams(0,time,gain);
    OC[0]=time; OC[1]=age; OC[2]=gain; OC[3]=optics; OC[6]=.022f;
    float projection[16];Check(Dev->GetVertexShaderConstantF(3,projection,4));
    if(!JumpGateProjectionRayParams(projection,OC+20))Require(false,"invalid render projection");
    memcpy(OC+36,GatePortal,sizeof(GatePortal));
    memcpy(OC+40,GatePortalRows,8*sizeof(float));
    Check(Dev->SetPixelShaderConstantF(12,GatePortalRows+8,1));
    Check(Dev->SetPixelShaderConstantF(13,GatePlasma,1));
    Check(Dev->SetPixelShaderConstantF(14,GateRings,1));
    Check(Dev->SetPixelShaderConstantF(15,GateTint,1));
    Check(Dev->SetPixelShaderConstantF(16,GateDonutSource,1));
    float pulses[4*JumpGateDonutPulseCount];BuildJumpGateDonutPulses(time,age,GateDonutSource[2],pulses);
    Check(Dev->SetPixelShaderConstantF(17,pulses,JumpGateDonutPulseCount));
}
static void GateCompile()
{
    const char* entries[]={"VSMain","PSLens","PSMain","VSInflow","PSInflow","PSDonuts"};
    for(int i=0;i<6;++i) {
        printf("Compile stage %d\n",i);
        auto start=std::chrono::steady_clock::now();
        ID3DXBuffer *code=nullptr,*errors=nullptr,*assembly=nullptr;
        HRESULT hr=D3DXCompileShaderFromFileA("DATA_EXTRA/SHADERS/jumpgate_aperture.hlsl",nullptr,nullptr,
            entries[i],i==0||i==3?"vs_3_0":"ps_3_0",0,&code,&errors,nullptr);
        if(errors){puts((char*)errors->GetBufferPointer());Release(errors);}Check(hr);
        printf("Compiled %s in %.2f ms\n",entries[i],std::chrono::duration<double,std::milli>(std::chrono::steady_clock::now()-start).count());
        Check(D3DXDisassembleShader((DWORD*)code->GetBufferPointer(),FALSE,nullptr,&assembly));
        std::string path=std::string(Out)+entries[i]+".asm";FILE* f=fopen(path.c_str(),"wb");
        fwrite(assembly->GetBufferPointer(),1,assembly->GetBufferSize(),f);fclose(f);Release(assembly);
        if(i==5)Check(Dev->CreatePixelShader((DWORD*)code->GetBufferPointer(),&GateDonuts));
        else if(i==4)Check(Dev->CreatePixelShader((DWORD*)code->GetBufferPointer(),&GateInflowPS));
        else if(i==3)Check(Dev->CreateVertexShader((DWORD*)code->GetBufferPointer(),&GateInflowVS));
        else if(i==2)Check(Dev->CreatePixelShader((DWORD*)code->GetBufferPointer(),&GateGlow));
        else if(i)Check(Dev->CreatePixelShader((DWORD*)code->GetBufferPointer(),&OpticsPS[0]));
        else Check(Dev->CreateVertexShader((DWORD*)code->GetBufferPointer(),&OpticsVS[0]));
        Release(code);
    }
}
static void FloatCheck()
{
    IDirect3DSurface9 *fp=nullptr,*cpu=nullptr;
    Check(Dev->CreateRenderTarget(W,H,D3DFMT_A32B32G32R32F,D3DMULTISAMPLE_NONE,0,FALSE,&fp,nullptr));
    Check(Dev->CreateOffscreenPlainSurface(W,H,D3DFMT_A32B32G32R32F,D3DPOOL_SYSTEMMEM,&cpu,nullptr));
    for(int pose=0;pose<5;++pose) {
        Camera(pose==1?1.5707963f:pose==2?3.14159265f:0,0,pose==3?90:pose==4?270:1100);
        if(pose==4)Eye[2]=GatePortal[2]; // on the membrane itself
        GateParams();Render(nullptr,true);
        Check(Dev->SetRenderTarget(0,fp));Check(Dev->Clear(0,nullptr,D3DCLEAR_TARGET,0,1,0));Check(Dev->BeginScene());GateDraw();Check(Dev->EndScene());
        Check(Dev->GetRenderTargetData(fp,cpu));D3DLOCKED_RECT lock;Check(cpu->LockRect(&lock,nullptr,D3DLOCK_READONLY));
        bool finite=true;for(int y=0;y<H;++y)for(int x=0;x<W*4;++x)
            finite=finite&&std::isfinite(((float*)((char*)lock.pBits+y*lock.Pitch))[x]);
        Check(cpu->UnlockRect());Require(finite,"front/side/back/inside/on-cap FP32 output is finite");
        Check(Dev->SetRenderTarget(0,Target));
    }
    Release(fp);Release(cpu);
}
static void CheckPortalPlacement()
{
    LensOnly=true;
    for(int size=0;size<3;++size)for(int offset=0;offset<2;++offset) {
        Size(size==0?720:size==1?960:1260,540);Camera(0,0,1100);
        // Reproduce the game's Hor+: nominal horizontal half-FOV remains 35 degrees,
        // while the actual horizontal projection expands with screen aspect.
        D3DXMATRIX projection;
        float tanY=tanf(35*3.14159265f/180)/(4.f/3.f);
        D3DXMatrixPerspectiveFovLH(&projection,2*atanf(tanY),float(W)/H,1,20000);
        float p[16];for(int r=0;r<4;++r)for(int c=0;c<4;++c)p[r*4+c]=projection.m[c][r];
        Check(Dev->SetVertexShaderConstantF(3,p,4));
        Eye[0]=offset?320:0;Eye[1]=offset?-120:0;
        GateParams(6,8,0);auto base=Render(nullptr,true);
        GateParams();char name[50];sprintf(name,"portal_%d_%s",W,offset?"offset":"centred");auto portal=Render(name,true);
        int left=W,right=-1,top=H,bottom=-1;
        for(int y=0;y<H;++y)for(int x=0;x<W;++x) {
            int delta=0;for(int k=0;k<3;++k)delta=std::max(delta,abs(int((portal[y*W+x]>>(8*k))&255)-int((base[y*W+x]>>(8*k))&255)));
            if(delta>5){left=std::min(left,x);right=std::max(right,x);top=std::min(top,y);bottom=std::max(bottom,y);}
        }
        float z=GatePortal[2]-Eye[2];
        float expectedX=W*.5f+(GatePortal[0]-Eye[0])*p[0]/z*W*.5f;
        float expectedY=H*.5f-(GatePortal[1]-Eye[1])*p[5]/z*H*.5f;
        printf("%dx%d offset%d bounds %d %d %d %d, projected HP %.2f %.2f\n",W,H,offset,left,top,right,bottom,expectedX,expectedY);
        Require(right>left&&abs((right-left)-(bottom-top))<=2,"portal is round at 4:3, 16:9 and 21:9");
        Require(fabsf((left+right+1)*.5f-expectedX)<2&&fabsf((top+bottom+1)*.5f-expectedY)<2,
            "portal follows projected hardpoint when camera translates, not screen centre");
        // Reference rim points projected independently from the shader's ray intersections.
        int hits=0;
        for(int i=0;i<48;++i) {
            float angle=i*6.2831853f/48;
            int x=int(expectedX+cosf(angle)*GatePortal[3]*p[0]/z*W*.5f);
            int y=int(expectedY-sinf(angle)*GatePortal[3]*p[5]/z*H*.5f);
            int peak=0;
            for(int dy=-2;dy<=2;++dy)for(int dx=-2;dx<=2;++dx) {
                int index=(y+dy)*W+x+dx;
                if(x+dx<0||x+dx>=W||y+dy<0||y+dy>=H)continue;
                for(int k=0;k<3;++k)peak=std::max(peak,int((portal[index]>>(8*k))&255)-int((base[index]>>(8*k))&255));
            }
            hits+=peak>50;
        }
        Require(hits>=46,"bright border coincides with independently projected circular HP rim");
    }
    // Tilt and turn the HP independently of the camera; the ring must remain on
    // the authored plane under camera orbit and a translated/rotated solar.
    D3DXMATRIX hp;
    D3DXMatrixRotationYawPitchRoll(&hp,3.14159265f,.01745f,-.01745f);
    for(int r=0;r<3;++r)for(int c=0;c<3;++c)GatePortalRows[r*4+c]=hp.m[r][c];
    for(int pose=0;pose<3;++pose) {
        ActualWorld=pose==2;Camera(pose?.65f:0,.13f,1100);GateParams(6,8,0);auto base=Render(nullptr,true);
        GateParams();auto result=Render(pose==0?"portal_hp_front":pose==1?"portal_hp_orbit":"portal_hp_world",true);
        int hits=0;
        for(int i=0;i<48;++i) {
            float a=i*6.2831853f/48;float delta[3];
            for(int k=0;k<3;++k)delta[k]=GatePortal[k]+GatePortal[3]*(cosf(a)*GatePortalRows[k]+sinf(a)*GatePortalRows[4+k])-Eye[k];
            float v[3]={};for(int r=0;r<3;++r)for(int k=0;k<3;++k)v[r]+=delta[k]*OpticsBasis[k*4+r];
            int x=int((v[0]/v[2]/OC[20]+OC[22]+1)*W*.5f);
            int y=int((1-v[1]/v[2]/OC[21]-OC[23])*H*.5f);
            int peak=0;
            for(int dy=-2;dy<=2;++dy)for(int dx=-2;dx<=2;++dx) {
                if(x+dx<0||x+dx>=W||y+dy<0||y+dy>=H)continue;
                int index=(y+dy)*W+x+dx;
                for(int k=0;k<3;++k)peak=std::max(peak,int((result[index]>>(8*k))&255)-int((base[index]>>(8*k))&255));
            }
            hits+=peak>40;
        }
        Require(hits>=46,"portal follows hardpoint orientation through camera orbit and world transform");
    }
    ActualWorld=false;
    memset(GatePortalRows,0,sizeof(GatePortalRows));GatePortalRows[0]=GatePortalRows[5]=GatePortalRows[10]=1;
    LensOnly=false;Size(960,540);
}
static void CheckPlasmaRotation()
{
    InflowEnabled=false;
    Camera(0,0,1100);
    for(int ring=0;ring<2;++ring) {
        GateRings[0]=ring?0:130;GateRings[1]=ring?190:0;
        GateParams(6,0,1,0);auto first=Render(nullptr,false);
        GateParams(6,1,1,0);auto second=Render(ring?"outer_plasma":"inner_plasma",false);
        float z=GatePlasma[2]-Eye[2];
        float cx=W*.5f+(GatePlasma[0]-Eye[0])/OC[20]/z*W*.5f;
        float cy=H*.5f-(GatePlasma[1]-Eye[1])/OC[21]/z*H*.5f;
        float radius=(ring?190:130)/OC[21]/z*H*.5f;
        float profiles[2][360]={};
        for(int frame=0;frame<2;++frame)for(int a=0;a<360;++a) {
            auto const& pixels=frame?second:first;float angle=a*.01745329252f;
            for(int band=-2;band<=2;++band) {
                int x=int(cx+cosf(angle)*(radius+band)),y=int(cy-sinf(angle)*(radius+band));
                DWORD p=pixels[y*W+x];profiles[frame][a]+=((p&255)+((p>>8)&255)+((p>>16)&255))/15.f;
            }
        }
        double best=1e100;int shift=0;
        for(int candidate=-60;candidate<=60;++candidate) {
            double error=0;
            for(int a=0;a<360;++a) {double d=profiles[0][a]-profiles[1][(a+candidate+360)%360];error+=d*d;}
            if(error<best){best=error;shift=candidate;}
        }
        printf("Plasma ring %d measured angular displacement: %d degrees/second\n",ring,shift);
        Require(ring?(shift>=-26&&shift<=-19):(shift>=27&&shift<=33),
            "rendered plasma patterns rotate in opposite directions at the authored ring radii");
        Require(Changes(second,Render(nullptr,false))==0,"ring rotation freezes exactly on pause");
    }
    GateRings[0]=130;GateRings[1]=190;
    InflowEnabled=true;
}
static void CheckInflow()
{
    float a[3],b[3],c[3];
    JumpGateInflowPoint(0,.3f,GateSource,GatePortal,GatePortalRows,a);
    JumpGateInflowPoint(0,.5f,GateSource,GatePortal,GatePortalRows,b);
    JumpGateInflowPoint(0,.7f,GateSource,GatePortal,GatePortalRows,c);
    Require(b[2]>a[2] && c[2]-b[2]>b[2]-a[2],"inflow travels inward and accelerates toward the exit");
    JumpGateInflowPoint(0,1,GateSource,GatePortal,GatePortalRows,a);
    float plane=0;for(int k=0;k<3;++k)plane+=(a[k]-GatePortal[k])*GatePortalRows[8+k];
    Require(fabsf(plane)<.001f,"inflow terminates on the portal hardpoint plane");
    // Exercise the real exit orientation, not just an identity test fixture.
    float reversed[12]={-1,0,0,0,0,1,0,0,0,0,-1,0};
    float previousAngle=0,winding=0;
    bool inward=true,finite=true;
    float previousZ=GateSource[2]-1;
    for(int i=0;i<=100;++i) {
        float age=i/100.f;
        JumpGateInflowPoint(7,age,GateSource,GatePortal,reversed,a);
        float centreX=GateSource[0]+(GatePortal[0]-GateSource[0])*age*age;
        float centreY=GateSource[1]+(GatePortal[1]-GateSource[1])*age*age;
        float angle=atan2f(a[1]-centreY,a[0]-centreX);
        if(i){float delta=angle-previousAngle;while(delta<0)delta+=6.2831853f;winding+=delta;}
        previousAngle=angle;inward=inward&&a[2]>previousZ;previousZ=a[2];
        for(float v:a)finite=finite&&std::isfinite(v);
    }
    Require(inward&&finite&&winding>6.2831853f&&winding<12.566371f,
        "continuous vortex winds inward more than one turn, including reversed exit HP");
    JumpGateInflowPoint(7,.5f,GateSource,GatePortal,reversed,a);
    float midRadius=hypotf(a[0]-(GateSource[0]+GatePortal[0])* .5f,a[1]-(GateSource[1]+GatePortal[1])* .5f);
    Require(midRadius>60,"reversed exit HP does not collapse vortex midway");
    std::vector<FJumpHoleVertex> mesh,wrapped;
    float eye[3]={0,0,-1100};
    BuildJumpGateInflow(0,GateSource,GatePortal,reversed,eye,mesh);
    BuildJumpGateInflow(192,GateSource,GatePortal,reversed,eye,wrapped);
    float maxDelta=0;
    for(size_t i=0;i<mesh.size();++i)for(int k=0;k<3;++k)
        maxDelta=std::max(maxDelta,fabsf(mesh[i].Position[k]-wrapped[i].Position[k]));
    Require(mesh.size()==JumpGateInflowVertices&&maxDelta<.1f,"vortex clock wrap preserves continuous geometry");
    Camera(.65f,.06f,1100);
    GatePlasma[3]=0;GateParams(6,8,1,0);
    InflowEnabled=false;auto base=Render(nullptr,true);
    InflowEnabled=true;auto flow=Render("inflow",true);
    Require(Changes(base,flow)>100,"thin inward trails are visible independently of the plasma rings");
    Require(Changes(flow,Render(nullptr,true))==0,"inward trails freeze on pause");
    GateParams(6,8.1f,1,0);Require(Changes(flow,Render(nullptr,true))>100,"inward trails advance with simulation time");
    GatePlasma[3]=1;
}
static void CheckVortexPalette()
{
    Camera(.65f,.06f,1100);GatePlasma[3]=0;
    GateParams(6,8,1,0);auto green=Render("vortex_edge_palette");
    unsigned long long sum[3]={};
    for(DWORD p:green){sum[0]+=(p>>16)&255;sum[1]+=(p>>8)&255;sum[2]+=p&255;}
    Require(sum[1]>sum[0]*1.3&&sum[1]>sum[2]*1.3,"edge gate vortex uses upcoming green tunnel hue");
    GateTint[0]=1;GateTint[1]=.3f;GateTint[2]=.7f;
    GateParams(6,8,1,0);auto pink=Render("vortex_other_palette");
    Require(Changes(green,pink)>100,"vortex responds to a different gate tunnel palette");
    GatePlasma[3]=1;InflowEnabled=false;GateParams();auto rings=Render();
    GateTint[0]=GateTint[2]=160.f/303;GateTint[1]=1;GateParams();
    Require(Changes(rings,Render())==0,"vortex palette does not recolour the two plasma rings or mirror");
    InflowEnabled=true;
}
static void CheckAlternateGate()
{
    float a[4*JumpGateDonutPulseCount],b[4*JumpGateDonutPulseCount];
    BuildJumpGateDonutPulses(.2f,6,GateDonutSource[2],a);
    BuildJumpGateDonutPulses(.3f,6,GateDonutSource[2],b);
    for(int i=0;i<JumpGateDonutPulseCount;++i)Require(fabsf(b[i*4]-a[i*4]-42.5f)<.001f,"donut bodies move +Z at slower 425 m/s");
    Require(fabsf(a[4]-a[0]-425.f/2.25f)<.001f,"donut emission cadence is 10 percent lower at 2.25 per second");
    Require(fabsf(JumpGateDonutSpeed*JumpGateDonutLifetime-600*1.5455f)<.001f,"slower donuts retain original travel distance");
    Require(JumpGateDonutPulseCount*JumpGateDonutInterval>=JumpGateDonutLifetime,"pulse slots cover the longer lifetime");
    BuildJumpGateDonutPulses(.15f,6,GateDonutSource[2],a);
    Require(fabsf(a[3]-.5f)<.001f&&fabsf(b[3]-1)<.001f,"each donut fades in smoothly over 0.3 seconds");
    BuildJumpGateDonutPulses(0,0,GateDonutSource[2],a);
    for(int i=0;i<JumpGateDonutPulseCount;++i)Require(a[i*4+3]==0,"activation does not prefill old donuts");
    BuildJumpGateDonutPulses(0,6,GateDonutSource[2],a);
    BuildJumpGateDonutPulses(192,6,GateDonutSource[2],b);
    Require(memcmp(a,b,sizeof(a))==0,"donut motion and material seed repeat across clock wrap");
    AlternateGate=true;
    // Isolate one pulse and compare its projected envelope with the measured
    // 111.666 m opening in jump_ring.3db, allowing for axial depth/perspective.
    Camera(0,0,1100);InflowEnabled=false;GateParams(6,8.25f,1,0);
    float isolated[4*JumpGateDonutPulseCount]={0,.75f,0,1,100000,0,0,0,100000,0,0,0,100000,0,0,0,100000,0,0,0};
    Check(Dev->SetPixelShaderConstantF(17,isolated,JumpGateDonutPulseCount));
    auto compact=Render("alternate_clearance");
    float cx=W*.5f+GateDonutSource[0]/OC[20]/1100*W*.5f;
    float cy=H*.5f-GateDonutSource[1]/OC[21]/1100*H*.5f;
    // The 240 m wake is nearer than the head; include its perspective expansion.
    float limit=108.f/OC[21]/(1100-240)*H*.5f+1;
    int outside=0,lit=0;
    for(int y=0;y<H;++y)for(int x=0;x<W;++x)if(compact[y*W+x]&0xffffff) {
        ++lit;if(hypotf(x-cx,y-cy)>limit)++outside;
    }
    Require(lit>200&&outside==0,"plasma and halo fit inside the measured metal-ring opening with clearance");
    Camera(1.5707963f,0,1100);GateParams(6,8.25f,1,0);
    Check(Dev->SetPixelShaderConstantF(17,isolated,JumpGateDonutPulseCount));
    auto wake=Render("alternate_wake_side");
    auto patchEnergy=[&](float z) {
        float delta[3]={GateDonutSource[0]-Eye[0],GateDonutSource[1]+80-Eye[1],z-Eye[2]},v[3]={};
        for(int r=0;r<3;++r)for(int k=0;k<3;++k)v[r]+=delta[k]*OpticsBasis[k*4+r];
        int x=int((v[0]/v[2]/OC[20]+OC[22]+1)*W*.5f);
        int y=int((1-v[1]/v[2]/OC[21]-OC[23])*H*.5f);
        int sum=0;
        for(int j=-3;j<=3;++j)for(int i=-3;i<=3;++i) {
            DWORD p=wake[(y+j)*W+x+i];sum+=(p&255)+((p>>8)&255)+((p>>16)&255);
        }
        return sum;
    };
    int behind=patchEnergy(-130),ahead=patchEnergy(130);
    printf("Smoke wake energy behind/ahead: %d / %d\n",behind,ahead);
    Require(behind>ahead*2+100,"smoky wake follows behind each moving head, not ahead of it");
    InflowEnabled=true;
    float oldTint[4];memcpy(oldTint,GateTint,sizeof(oldTint));
    GateTint[0]=GateTint[1]=GateTint[2]=1; // actual rh_mnh -> rh_kgb dark tunnel
    Camera(.65f,.06f,1250);GateParams(6,8.25f,0);auto base=Render(nullptr,true);
    GateParams(6,8.25f);auto active=Render("alternate_oblique",true);
    Require(Changes(base,active)>1500,"alternate gate has visible volumetric energy bodies");
    Require(Changes(active,Render(nullptr,true))==0,"alternate gate is pixel-identical on pause");
    GateParams(6,8.35f);Require(Changes(active,Render(nullptr,true))>1000,"alternate energy bodies travel with simulation time");
    GateParams(6,8.25f);GateRings[0]=GateRings[1]=0;
    Require(Changes(active,Render(nullptr,true))==0,"alternate shooter replaces both ordinary plasma rings");
    GateRings[0]=130;GateRings[1]=190;
    GateParams(6,8.25f,1,0);Require(Changes(active,Render(nullptr,true))>50,"alternate gate retains reflecting portal");
    InflowEnabled=false;GateParams(6,8.25f);
    Require(Changes(active,Render("alternate_donuts",true))>100,"alternate gate retains inward vortex alongside flying donuts");
    InflowEnabled=true;
    BlockerDepth=ZForDistance(40);GateParams(6,8.25f);auto blocked=Render("alternate_occluded",true,true,true);
    GateParams(6,8.25f,0);auto blockedBase=Render(nullptr,true,true,true);
    int leaks=0;
    for(int y=0;y<H;++y)for(int x=0;x<W;++x)
        if((x>W/4+2&&x<W*3/4-2&&y>H/4+2&&y<H*3/4-2)||y>H*3/4+2)leaks+=blocked[y*W+x]!=blockedBase[y*W+x];
    Require(leaks==0,"alternate volumes respect foreground geometry and cockpit depth");
    for(int p=0;p<3;++p){Camera(p==1?1.5707963f:p==2?3.14159265f:0,.05f,1250);GateParams(6,8.25f);Render(p==0?"alternate_front":p==1?"alternate_side":"alternate_back",true);}
    Camera(.65f,.06f,1250);GateParams(0,0);Require(Changes(base,Render(nullptr,true))==0,"closed alternate gate is invisible");
    FloatCheck();
    AlternateGate=false;memcpy(GateTint,oldTint,sizeof(oldTint));
}
int main(int argc,char** argv)
{
    setvbuf(stdout,nullptr,_IONBF,0);
    Out="src/obj/jumpgate_check/";CreateDirectoryA(Out,nullptr);
    SetErrorMode(SEM_FAILCRITICALERRORS|SEM_NOGPFAULTERRORBOX);
    FJumpGateVisualPhase phase;phase.Activate();phase.Tick(1);auto saved=phase;
    phase.Tick(0);phase.Tick(-1);phase.Tick(std::numeric_limits<float>::quiet_NaN());
    Require(phase.Time==saved.Time&&phase.Gain==saved.Gain&&phase.Age==saved.Age,"pause and invalid dt preserve phase");
    phase.Activate();Require(phase.Age==saved.Age,"duplicate open does not restart ignition");
    phase.Open=false;phase.Tick(2);Require(phase.Gain==0,"close finishes without residual glow");
    phase.Activate();Require(phase.Age==0,"reopen starts a fresh ignition");
    auto* api=Direct3DCreate9(D3D_SDK_VERSION);Require(api!=nullptr,"D3D9 available");
    HWND window=CreateWindowA("STATIC","jumpgate check",WS_POPUP,0,0,64,64,nullptr,nullptr,GetModuleHandle(nullptr),nullptr);
    D3DPRESENT_PARAMETERS pp={};pp.Windowed=TRUE;pp.SwapEffect=D3DSWAPEFFECT_DISCARD;
    pp.BackBufferWidth=64;pp.BackBufferHeight=64;pp.BackBufferFormat=D3DFMT_A8R8G8B8;
    Check(api->CreateDevice(0,D3DDEVTYPE_HAL,window,D3DCREATE_HARDWARE_VERTEXPROCESSING,&pp,&Dev));
    puts("Device created");GateCompile();puts("Shader compiled");
    if(argc>1&&strcmp(argv[1],"--compile-only")==0)return 0;
    auto noiseStart=std::chrono::steady_clock::now();CreateNoise();
    printf("Noise generation/upload: %.2f ms\n",std::chrono::duration<double,std::milli>(std::chrono::steady_clock::now()-noiseStart).count());
    Size(960,540);OpticsMode=1;
    Dev->SetRenderState(D3DRS_CULLMODE,D3DCULL_NONE);Dev->SetRenderState(D3DRS_ZWRITEENABLE,FALSE);
    Dev->SetRenderState(D3DRS_ALPHATESTENABLE,FALSE);Dev->SetRenderState(D3DRS_LIGHTING,FALSE);
    puts("Textures created");Camera(0,0,1100);GateParams(6,8,0);auto base=Render("off",true);
    GateParams();auto active=Render("active",true);
    Require(Changes(base,active)>1500,"charged gate is visible");
    Require(Changes(active,Render(nullptr,true))==0,"paused rendering is pixel identical");
    GateParams(6,8,0);Require(Changes(base,Render(nullptr,true))==0,"zero gain is exact identity");
    GateParams(0);Require(Changes(base,Render(nullptr,true))==0,"closed gate is invisible");
    GateParams(6,8,1,0);auto noOptics=Render("no_optics",true);
    Require(Changes(active,noOptics)>50,"charged membrane visibly reflects the background");
    GateParams(6,9);Require(Changes(active,Render(nullptr,true))>500,"plasma flows with simulation time");
    BlockerDepth=ZForDistance(40);GateParams();auto blocked=Render("occluded",true,true,true);
    GateParams(6,8,0);auto blockedBase=Render(nullptr,true,true,true);
    int leaks=0;for(int y=0;y<H;++y)for(int x=0;x<W;++x)
        if((x>W/4+2&&x<W*3/4-2&&y>H/4+2&&y<H*3/4-2)||y>H*3/4+2)
            leaks+=blocked[y*W+x]!=blockedBase[y*W+x];
    Require(leaks==0,"foreground geometry and cockpit remain exact");
    for(int p=0;p<4;++p) {
        Camera(p==1?.65f:p==2?1.5707963f:p==3?3.14159265f:0,.06f,1100);GateParams();
        const char* names[]={"front","oblique","side","back"};Render(names[p],true);
    }
    for(int i=0;i<6;++i) {Camera(0,.03f,1100);GateParams(i*1.1f,i*1.1f);char name[40];sprintf(name,"ignition_%d",i);Render(name,true);}
    Camera(.2f,.04f,1100,.72f);GateParams();auto boxed=Render("letterbox",true);
    GateParams(6,8,0);auto boxedBase=Render(nullptr,true);
    int outside=0;for(int y=0;y<H;++y)for(int x=0;x<W;++x)
        if(y<H*.13f||y>H*.87f)outside+=boxed[y*W+x]!=boxedBase[y*W+x];
    Require(outside==0,"letterbox outside viewport is untouched");
    CheckPortalPlacement();
    CheckPlasmaRotation();
    CheckInflow();
    CheckVortexPalette();
    FloatCheck();
    CheckAlternateGate();
    if(argc>1&&strcmp(argv[1],"--frames")==0) {
        Beauty=true;Size(1280,720);
        for(int i=0;i<180;++i) {
            float time=i/24.f;Camera(.16f,.05f,1150);GateParams(time,time);
            char name[40];sprintf(name,"frame_%04d",i);Render(name,true);
        }
    }
    if(argc>1&&strcmp(argv[1],"--alt-frames")==0) {
        AlternateGate=true;GateTint[0]=GateTint[1]=GateTint[2]=1;
        Beauty=true;Size(1280,720);
        for(int i=0;i<180;++i) {
            float time=i/24.f;Camera(.6f,.06f,1250);GateParams(time,time);
            char name[40];sprintf(name,"alt_frame_%04d",i);Render(name,true);
        }
    }
    puts("Jumpgate production shader checks passed.");return 0;
}
