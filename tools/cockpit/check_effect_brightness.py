"""Exercise production camera brightness, particle/beam draws and light uploads."""
import os
from pathlib import Path
import subprocess

ROOT = Path(__file__).resolve().parents[2]
CLIENT = ROOT / 'src/freelancer/Client'
OUT = ROOT / 'src/obj/cockpit_effect_brightness_check'
OUT.mkdir(parents=True, exist_ok=True)


def function(file, signature):
    source = (CLIENT / file).read_text(encoding='utf-8-sig')
    start = source.index(signature)
    end = source.index('{', start) + 1
    depth = 1
    while depth:
        depth += (source[end] == '{') - (source[end] == '}')
        end += 1
    return source[start:end]


stub = r'''
#include <cassert>
#include <cmath>
#include <cstdint>
#include <cstdio>
#include <cstring>
#include <map>
#include <unordered_map>
#include "cockpit_effect_brightness.h"
struct ICamera {};
struct FSpaceCamera:ICamera {};
FSpaceCamera cockpit,external,turret,rear,hud;
FSpaceCamera* GetFirstPersonSpaceCamera(){return &cockpit;}
ICamera* AsCamera(FSpaceCamera* p){return p;}
constexpr int kGameOptParticles=1;
bool particles=true;
int GetGameOption(int){return particles;}
float opacity=1,drawOpacity=1,solarOpacity=1;
unsigned soft=1,drawSoft=1,particleDraws=0;
bool solarReplacement=false;
struct IAlchemyRenderOpacity {
    void SetRenderOpacity(float value){opacity=value;}
    void SetRenderSoftParticles(unsigned value){soft=value;}
    void Release(){}
} opacityInterface;
namespace Iids {constexpr int AlchemyRenderOpacity=1;}
struct Alchemy {void QueryInterface(int,void** out){*out=&opacityInterface;}} alchemy;
struct Engine {float* GetInstanceTransform(void*){return nullptr;}} engine;
namespace DALib {Alchemy* Alchemy=&alchemy;Engine* Engine=&engine;}
struct Fx {
    void Slot9(FSpaceCamera*){drawOpacity=opacity;drawSoft=soft;++particleDraws;}
} fx;
struct FParticleEffect {
    unsigned char Flags7C=1;int EngineIndex=-1;Fx* FxEffect=&fx;void* owner=nullptr;
    unsigned char BuildGeometry(FSpaceCamera*);
};
void* EffectWatchedObject(FParticleEffect* p){return p->owner;}
bool StarSphereReplacesAttachedEffect(void*){return solarReplacement;}
float StarSphereAttachedEffectVisibility(void*,ICamera*){return solarOpacity;}

struct FTransform {float unused=0;};
struct Watchable {};
struct Watcher {Watchable* target(){return nullptr;}};
struct Math {void MulTransform(FTransform&,FTransform const&,FTransform const&){}} math;
Math* EffectMath(){return &math;}
struct FBeamEffectArch {int SegmentMode=0;};
struct FBeamEffect {
    unsigned char Flags70=0;FTransform LocalXform;::Watcher Watcher;int EngineIndex=-1;
    float Progress78=1,ProgressDenom80=2,Float7C=-1;FBeamEffectArch* Arch=nullptr;
    unsigned char BuildGeometry(FSpaceCamera*);
};
struct Vertex {unsigned char R,G,B,A;};
Vertex vertices[64];
struct {int VertCount=0;Vertex* Vertices=vertices;} G_EffectVertexBatch;
bool BeamGeometryOptionEnabled(){return true;}
void EmitBeam(){vertices[G_EffectVertexBatch.VertCount++]={240,160,80,255};}
void BeamEffectBuildSingleSegment(FBeamEffect*,FTransform*,float,float){EmitBeam();}
void BeamEffectBuildMultiSegment(FBeamEffect*,FTransform*,float,float){EmitBeam();}
Vertex animated;
void EffectVertexBatchSetBeamFrame(int first,FTransform const&,unsigned){animated=vertices[first];}

struct FGraphRange {int bClamp;float Min,Max;};
struct Graph {float Evaluate(float,FGraphRange*){return 1;}};
struct LightData {
    float Diffuse[4]={.8f,.4f,.2f,1},Specular[4]={.6f,.3f,.1f,1},Ambient[4]={.2f,.1f,.05f,1};
    float Direction[3]={};float Range=200,Attenuation2=.004f;
};
struct FEngineLight {
    unsigned char Flags=8|4|0x20;int Type=1;LightData D3d;float Orient[9]={};Graph* AmbientCurve=nullptr;
};
LightData uploaded;unsigned uploads=0;
int G_PipelineLightState=1;
std::map<FEngineLight*,float> G_NebulaSunUploads;
namespace NebulaVolume {float sun=-1;float SunLightScale(float const*){return sun;}}
void PushLightUpdate(FEngineLight* p){uploaded=p->D3d;++uploads;}
void SoftCameraRewriteLight(FEngineLight* p,ICamera*,float const*){PushLightUpdate(p);}
void EngineLightPushUpdate(FEngineLight* p){PushLightUpdate(p);}
void EngineLightComputeDirection(FEngineLight*,float*,float const*,float*){}
bool EngineLightGetEffectiveColor(FEngineLight* p,float,float* out){
    for(int i=0;i<3;++i)out[i]=p->D3d.Diffuse[i];return false;
}
void Vec3Negate(float* out,float const* in){for(int i=0;i<3;++i)out[i]=-in[i];}
void ScaleVec3(float* out,float const* in,float s){for(int i=0;i<3;++i)out[i]=in[i]*s;}
void LinkIntoRegisteredList(FEngineLight*){}
void UnlinkFromList(FEngineLight*){}
constexpr unsigned long D3DBLEND_ONE=2;
float G_AppearanceOpacity=1;
'''

checks = r'''
bool near(float a,float b){return std::fabs(a-b)<.00001f;}
int main(){
    using namespace CockpitEffectBrightness;
    int token=0,other=0;
    Register(&token);assert(KindOf(&token)==Kind::None);
    {
        CreationScope weapon(Kind::Weapon);Register(&token);
        {CreationScope shield(Kind::Shield);
         {CreationScope nestedWeapon(Kind::Weapon);Register(&other);}
         assert(KindOf(&other)==Kind::Shield);}
        int nested;Register(&nested);assert(KindOf(&nested)==Kind::Weapon);Forget(&nested);
    }
    assert(Scale(&token,&cockpit)==.33f&&Scale(&other,&cockpit)==.20f);
    Register(&token);assert(KindOf(&token)==Kind::None); // Reused pool address.
    Forget(&other);assert(Scale(&other,&cockpit)==1);
    Register(nullptr);Forget(nullptr);assert(Scale(nullptr,&cockpit)==1);
    for(Kind kind:{Kind::None,Kind::Weapon,Kind::Shield}){
        FParticleEffect particle;FBeamEffect beam;FBeamEffectArch arch;beam.Arch=&arch;FEngineLight light;
        {CreationScope creation(kind);Register(&particle);Register(&beam);Register(&light);}
        for(int frame=0;frame<4;++frame)for(FSpaceCamera* camera:{&cockpit,&external,&turret,&rear,&hud,&cockpit}){
            float const expected=camera==&cockpit?(kind==Kind::Weapon?.33f:kind==Kind::Shield?.20f:1.f):1.f;
            assert(Scale(kind,nullptr)==1);
            solarOpacity=1;particle.owner=nullptr;particle.EngineIndex=-1;
            particle.BuildGeometry(camera);assert(near(drawOpacity,expected)&&opacity==1&&soft==1);
            particle.owner=&token;particle.EngineIndex=42;solarOpacity=.8f;
            particle.BuildGeometry(camera);
#ifdef FREELANCER_RP9
            assert(near(drawOpacity,expected*.8f)&&drawSoft==0);
#else
            assert(near(drawOpacity,expected)&&drawSoft==1);
#endif
            assert(opacity==1&&soft==1);
            for(int mode=0;mode<3;++mode){
                arch.SegmentMode=mode%2;beam.Flags70=mode==2?2:0;
                G_EffectVertexBatch.VertCount=1;vertices[0]={240,160,80,255};
                beam.BuildGeometry(camera);
                assert(vertices[0].R==240); // Only this beam's vertices may change.
                assert(std::fabs(vertices[1].R-240*expected)<=.5f&&std::fabs(vertices[1].G-160*expected)<=.5f&&std::fabs(vertices[1].B-80*expected)<=.5f);
                assert(vertices[1].A==255&&animated.R==vertices[1].R);
            }
            for(int pipeline=0;pipeline<2;++pipeline){
                G_PipelineLightState=pipeline;LightData before=light.D3d;float ambient[3]={};
                // Untagged hardware lights have no extra upload; tagged ones must restore 1 too.
                unsigned const prior=uploads;
                EngineLightApplyNearby(&light,camera,nullptr,ambient);
                if(kind!=Kind::None||pipeline!=0){
                    assert(uploads>prior);
                    for(int i=0;i<3;++i){
                        assert(near(uploaded.Diffuse[i],before.Diffuse[i]*expected));
                        assert(near(uploaded.Specular[i],before.Specular[i]*expected));
                        assert(near(uploaded.Ambient[i],before.Ambient[i]*expected));
                    }
                    assert(uploaded.Range==before.Range&&uploaded.Attenuation2==before.Attenuation2);
                    assert(uploaded.Diffuse[3]==1&&uploaded.Specular[3]==1);
                }
                assert(std::memcmp(&before,&light.D3d,sizeof before)==0);
            }
        }
        particles=false;unsigned draws=particleDraws;particle.BuildGeometry(&cockpit);
        assert(particleDraws==draws&&opacity==1);particles=true;
#ifdef FREELANCER_RP9
        solarReplacement=true;particle.BuildGeometry(&cockpit);assert(particleDraws==draws);solarReplacement=false;
#endif
        Forget(&particle);Forget(&beam);Forget(&light);
        assert(Scale(&light,&cockpit)==1);
    }
    // The existing ALE colour path must dim additive ONE/ONE RGB exactly once.
    for(float scale:{.33f,.20f}){
        G_AppearanceOpacity=scale;
        unsigned long colour=AlApplyRenderOpacity(0xfff0a050ul,D3DBLEND_ONE);
        assert(std::fabs(float((colour>>16)&255)-240*scale)<=.5f&&std::fabs(float((colour>>8)&255)-160*scale)<=.5f&&std::fabs(float(colour&255)-80*scale)<=.5f);
        colour=AlApplyRenderOpacity(0xfff0a050ul,5); // SRCALPHA: RGB retained, alpha dims contribution.
        assert((colour&0xffffff)==0xf0a050&&((colour>>24)&255)==(unsigned)(255*scale+.5f));
    }
    puts("PASS: 33% weapons / 20% shields, nested shield splash, object reuse and camera switching");
    puts("PASS: production particle opacity/reset, both beam paths/animated colours and both light upload paths; no cumulative dimming or radius changes");
}
'''

registry = (CLIENT / 'cockpit_effect_brightness.cpp').read_text()
registry = '\n'.join(line for line in registry.splitlines() if not line.startswith('#include'))
code = stub + registry
code += function('particle_effect.cpp', 'unsigned char FParticleEffect::BuildGeometry(')
code += function('beam_effect.cpp', 'unsigned char FBeamEffect::BuildGeometry(')
code += function('engine_light.cpp', 'bool EngineLightApplyNearby(')
code += function('../../alchemy/alchemy_appearances.cpp', 'unsigned long AlApplyRenderOpacity(')
(OUT / 'check.cpp').write_text(code + checks)
vc = Path('C:/Program Files/Microsoft Visual Studio/18/Community/VC/Tools/MSVC/14.51.36231')
sdk = Path('C:/Program Files (x86)/Windows Kits/10')
version = '10.0.26100.0'
env = dict(os.environ)
env['INCLUDE'] = ';'.join(str(p) for p in [vc / 'include', CLIENT] +
                        [sdk / 'Include' / version / x for x in ('ucrt', 'shared', 'um')])
env['LIB'] = ';'.join(str(p) for p in [vc / 'lib/x86'] +
                    [sdk / 'Lib' / version / x / 'x86' for x in ('ucrt', 'um')])
for rp9 in (False, True):
    exe = 'rp9.exe' if rp9 else 'rp8.exe'
    defines = ['/DFREELANCER_RP9'] if rp9 else []
    subprocess.run([str(vc / 'bin/Hostx64/x86/cl.exe'), '/nologo', '/std:c++17', '/W4', '/WX',
                    '/wd4458', '/EHsc', '/MT', *defines, 'check.cpp', '/Fe' + exe], cwd=OUT, env=env, check=True)
    subprocess.run([str(OUT / exe)], cwd=OUT, check=True)
