#include "render/BeamRibbon.h"
#include "render/IRPVolumeBeam.h"
#include <vector>
#include <cstdint>
#include <cstring>
#include <cstdio>
#include <cstdlib>
using namespace BeamRibbon;
static void Need(bool b,const char* message) { if(!b){printf("FAIL %s\n",message);exit(1);} }
struct FTransform { struct {float D[3][3];} Rotation; struct {float X,Y,Z;} Translation; };
enum { D3DBLEND_ONE=2, D3DBLEND_SRCALPHA=5 };
struct FBeamTrailFadeSettings { std::string Nodes="trail"; float Distance=10.f; } trailSettings;
FBeamTrailFadeSettings const& BeamTrailFadeSettings() { return trailSettings; }
struct ICamera { float* GetViewTransform() { return nullptr; } float GetZNear() { return 1.f; } };
ICamera camera;
uintptr_t G_DrawCookie=reinterpret_cast<uintptr_t>(&camera);
FTransform fixtureInverse={{{1,0,0,0,1,0,0,0,1}},{0,0,0}};
FTransform fixtureView={{{1,0,0,0,1,0,0,0,1}},{0,0,0}};
void ComposeTransform(float* out,const float*,const float*) { std::memcpy(out,&fixtureView,sizeof(fixtureView)); }
void ComputeGeneralInverseTransform(const FTransform&,FTransform& inverse,float& w)
{ inverse=fixtureInverse;w=1; }
struct Vertex {Vec p;unsigned long colour;float u,v;};
std::vector<Vertex> vertices;
std::vector<unsigned short> indices;
unsigned short StoreBeamRawVertex(const float* p,unsigned long c,float u,float v)
{ vertices.push_back({{p[0],p[1],p[2]},c,u,v});return (unsigned short)(vertices.size()-1); }
void StoreBeamTriangle(unsigned short a,unsigned short b,unsigned short c)
{ indices.insert(indices.end(),{a,b,c}); }
void StoreBeamQuad(unsigned short a,unsigned short b,unsigned short c,unsigned short d)
{ StoreBeamTriangle(a,b,c);StoreBeamTriangle(c,b,d); }
struct FLBeamAppearance {
    struct Descriptor {unsigned Flags=0; unsigned BlendInfo[2]={D3DBLEND_SRCALPHA,D3DBLEND_ONE};} descriptor;
    Descriptor* Descriptor_=&descriptor;
    struct {float Frame[5]={0,.2f,.3f,.8f,.9f};} Texture_;
    float NodeWorldXform_[12]={};
    std::vector<FRPVolumeBeamPoint> points;
    const char* name="ordinary_laser";
    void GetInstanceName(const char** out){*out=name;}
    size_t ResolveLiveInstanceCount(){return points.size();}
    void FillRibbon(std::vector<FRPVolumeBeamPoint>* p){*p=points;}
    void FillCameraRibbon();
};
// PRODUCTION_EMITTER
int main()
{
    FLBeamAppearance beam;
    auto render=[&] {vertices.clear();indices.clear();beam.FillCameraRibbon();};
    render();Need(vertices.empty(),"empty beam skipped");
    beam.points={{{0,0,10},.25f,0xff123456,.3f}};
    render();Need(vertices.empty(),"single point skipped");
    for(int curved=0;curved<2;++curved) for(unsigned flag : {0u,2u})
    {
        beam.points.clear();beam.descriptor.Flags=flag;
        for(int i=0;i<30;++i) beam.points.push_back({{curved ? .3f*std::sin(i*.2f) : 0.f,i*.1f,10},.25f,0xff123456,i%2?.9f:.3f});
        render();
        Need(vertices.size()==60+(flag?29:0),"one vertex pair per ring plus optional centre");
        Need(indices.size()==29*(flag?12:6),"two/four triangles per span");
        for(auto i:indices)Need(i<vertices.size(),"valid batch indices");
        size_t offset=0;
        Vec previous={};
        for(size_t i=0;i<beam.points.size();++i)
        {
            auto& a=vertices[offset];auto& b=vertices[offset+1];
            Need(std::fabs(Dot(Sub(a.p,b.p),Sub(a.p,b.p))-.25f)<1e-5f,"original beam width");
            Need(a.u==.2f && b.u==.8f && a.v==beam.points[i].V && b.v==a.v,"atlas UV and particle parity preserved");
            Need(a.colour==beam.points[i].Colour && b.colour==a.colour,"colour and alpha preserved");
            Vec side=Sub(b.p,a.p);Need(Dot(previous,side)>=0,"no edge swap around a bend");previous=side;
            offset+=2+(flag && i?1:0);
        }
    }
    // Side-on, end-on, coincident camera/particle and reversing path frames.
    for(int i=0;i<2000;++i)
    {
        float t=i*.01f;
        Vec eye={10*std::sin(t),3*std::cos(t),10*std::cos(t)};
        Vec side=Side({0,0,-1},{0,0,0},{0,0,1},eye,{1,0,0},{0,1,0},{});
        Need(std::fabs(Dot(side,side)-1)<1e-5f && std::fabs(side.z)<1e-5f,"orbit keeps unit perpendicular width");
        Need(std::fabs(Dot(side,Unit(eye,{0,0,1})))<1e-4f,"ribbon faces camera");
    }
    for(Vec eye : {Vec{0,0,10},Vec{0,0,-10},Vec{0,0,0},Vec{1e-8f,0,10}})
    {
        Vec side=Side({0,0,-1},{0,0,0},{0,0,1},eye,{1,0,0},{0,1,0},{});
        Need(std::isfinite(side.x+side.y+side.z) && std::fabs(Dot(side,side)-1)<1e-5f,"end-on fallback finite and full width");
    }
    // View inverse supplies local camera axes; a translated/rotated node still faces it.
    fixtureInverse={{{0,0,1,0,1,0,-1,0,0}},{10,0,0}};
    beam.descriptor.Flags=0;
    beam.points={{{0,-1,0},.25f,0xffffffff,0},{{0,1,0},.25f,0xffffffff,1}};
    render();Need(std::fabs(vertices[0].p.z)==.25f && vertices[0].p.x==0,"rotated local camera frame");
    puts("PASS: production ribbon topology, width, UV, colour, curved trails, camera orbit and axial fallback");
    fixtureInverse={{{1,0,0,0,1,0,0,0,1}},{0,0,0}};
    Need(NameMatches(" trail, engine_wake ","Player_TRAIL"),"case-insensitive node matching");
    Need(!NameMatches("trail","sphere_laser") && !NameMatches("","trail") && !NameMatches("trail",nullptr),"unmatched and disabled node filters");
    beam.name="Player_TRAIL";
    beam.descriptor.Flags=2;
    // Near-plane colour must vanish, the mid-point must fade too, and the distant tail must remain.
    beam.points={{{0,0,-1},.25f,0x80402010,0},{{0,0,-11},.25f,0x80402010,1},{{0,0,-21},.25f,0x80402010,0}};
    for(unsigned src : {unsigned(D3DBLEND_ONE),unsigned(D3DBLEND_SRCALPHA)})
    {
        beam.descriptor.BlendInfo[0]=src;
        render();
        Need(vertices.size()==8 && indices.size()==24,"fade adds no geometry or passes");
        Need(vertices[0].colour==(src==D3DBLEND_ONE ? 0x80000000ul : 0x00402010ul),"near plane invisible for both additive blend modes");
        Need(vertices[2].colour==0x80402010ul && vertices[5].colour==0x80402010ul,"far trail keeps authored colour and opacity");
        Need(vertices[4].colour==(src==D3DBLEND_ONE ? 0x80201008ul : 0x40402010ul),"centre vertex follows smooth distance fade");
        // Same material, another node in the same batch must not inherit trail fade.
        beam.name="sphere_laser";beam.FillCameraRibbon();
        Need(vertices[8].colour==0x80402010ul,"laser unaffected after trail in same batch");
        for(auto i:indices)Need(i<vertices.size(),"batched index offsets stay valid");
        beam.name="Player_TRAIL";
    }
    trailSettings.Distance=0;render();Need(vertices[0].colour==0x80402010ul,"zero setting disables fade");
    trailSettings.Distance=10;trailSettings.Nodes="";render();Need(vertices[0].colour==0x80402010ul,"empty filter disables fade");
    trailSettings.Nodes="trail";beam.descriptor.BlendInfo[1]=6;render();Need(vertices[0].colour==0x80402010ul,"non-additive authored materials unchanged");
    beam.descriptor.BlendInfo[1]=D3DBLEND_ONE;
    // Camera translation changes the fade in view space, not world/local distance.
    fixtureView.Translation.Z=-20;render();Need(vertices[0].colour==0x80402010ul,"moving camera away restores whole trail");
    fixtureView.Translation.Z=20;render();Need((vertices[0].colour>>24)==0,"behind-camera trail fades out");
    Need(FadeColour(0xffffffff,1,1,10,true)==0x00fffffful,"near boundary exact");
    Need(FadeColour(0xffffffff,6,1,10,true)==0x80fffffful,"fade midpoint");
    Need(FadeColour(0xffffffff,11,1,10,true)==0xfffffffful,"far boundary exact");
    puts("PASS: trail-only vertex fade, both blend modes, midpoint, disabled settings, batching, camera movement and laser isolation");
}
