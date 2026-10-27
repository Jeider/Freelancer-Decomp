"""Exercise production nebula-halo eligibility/fade and billboard depth setup."""
import os
from pathlib import Path
import subprocess

repo = Path(__file__).resolve().parents[2]
out = repo / 'src/obj/sun_halo/check'
out.mkdir(parents=True, exist_ok=True)
source = (repo / 'src/freelancer/Client/star_sphere.cpp').read_text()
start = source.index('void StarSphereDrawNebulaHalo(void* Cam)')
end = source.index('\nvoid NebulaShipAuraDraw', start)
halo = source[start:end]
start = source.index('    void FStarSphere::DrawBillboard(')
start = source.index('{', start) + 1
end = source.index('// 0x00511901..0x00511930:', start)
setup = source[start:end].replace('this', 'sphere')
stub = r'''
#include <cassert>
#include <cmath>
#include <cstdio>
#include <cstring>
#include "solar_nebula_transition.h"
#define FREELANCER_RP9
#define FDUMP(...) ((void)0)
bool active=true,blocked=false,visible=true,fog=true,depth=true;
int depthWrite=1,depthFunc=2;float minDepth=0,maxDepth=.75f;
float immersion=1,through=0,burn=.4f,size=1;
bool GbSolarPostBurnthrough=false;int G_StarBillboardEnabled=1;
constexpr int kWin3DCullFace=1,kWin3DDepthTest=2,kWin3DFog=3,D3DRS_FOGENABLE=4;
constexpr int D3DRS_ZENABLE=5,D3DRS_ZWRITEENABLE=6,D3DRS_ZFUNC=7,D3DCMP_LESSEQUAL=4;
void Win3DDisable(int c){if(c==kWin3DDepthTest)depth=false;if(c==kWin3DFog)fog=false;}
void Win3DEnable(int c){if(c==kWin3DDepthTest)depth=true;if(c==kWin3DFog)fog=true;}
void Win3DSetDepthWrite(int v){depthWrite=v;}
struct ICamera {int Project(float*,float*,float*,float*){return visible?1:0;}} camera;
struct Owner {float pos[3]={0,0,1000};float const (&get_position())[3]{return pos;}} owner;
struct FStarSphere {
    void* StarGlow=(void*)1;void* SunBody=(void*)1;struct Owner* Owner=&owner;
    void DrawBillboard(void*,float,float);
} sphere;
struct FStarSphereListNode {FStarSphere* Sphere;FStarSphereListNode* Next;};
struct FStarSphereList {FStarSphereListNode* Sentinel;};
FStarSphereListNode sentinel={},node={&sphere,&sentinel};FStarSphereList list={&sentinel};
FStarSphereList* StarSphereList(){return &list;}
namespace NebulaVolume {bool IsFrameActive(){return active;}}
float SolarNebulaImmersion(){return immersion;}
bool SolarNebulaBlocked(FStarSphere*,ICamera*){return blocked;}
float SolarNebulaThrough(FStarSphere*,ICamera*){return through;}
float SolarSunFade(FStarSphere*,ICamera*){return 1;}
struct FNebulaEffect {float GetFloat2C4(){return burn;}float GetFloat2C8(){return size;}} controller;
void* GetSpaceFieldController(){return &controller;}
float PortConfigFloat(char const*,char const*,float value){return value;}
double GetClientElapsedTime(){return 0;}
struct Batcher {void FlushAll(unsigned){}} batcher;
struct Pipe {
 void GetRenderState(int s,int* out){*out=s==D3DRS_FOGENABLE?fog:s==D3DRS_ZENABLE?depth:s==D3DRS_ZWRITEENABLE?depthWrite:depthFunc;}
 void SetRenderState(int s,int v){assert(s==D3DRS_ZFUNC);depthFunc=v;}
 void GetDepthRange(float*a,float*b){*a=minDepth;*b=maxDepth;}
 void SetDepthRange(float a,float b){minDepth=a;maxDepth=b;}
} pipe;
namespace DALib {Batcher* MaterialBatcher=&batcher;Pipe* Pipeline=&pipe;}
int draws=0;float lastStrength=0;
'''
# Keep the actual nebula crossfade, including its thresholds.
fade_start = source.index('    float SolarNebulaFade(float Through)')
fade_end = source.index('    float SolarSunFade(', fade_start)
fade = source[fade_start:fade_end]
test = r'''
void FStarSphere::DrawBillboard(void* cam,float strength,float){
    assert(GbSolarPostBurnthrough && !fog);depth=true;
    DrawBillboardStates(this,cam);assert(depth && !depthWrite);
    assert(minDepth==1 && maxDepth==1 && depthFunc==D3DCMP_LESSEQUAL);
    ++draws;lastStrength=strength;
    depth=true; // Native billboard restores depth test after submitting its sprite.
}
int main(){
    for(int fps:{30,60,144}){
        SolarNebulaTransition sunlight,immersionFade;
        sunlight.Update(0,0,3,.75f);immersionFade.Update(1,0,.75f,3);
        float previous=0;
        for(int frame=1;frame<=fps*4;++frame){
            double time=double(frame)/fps;
            float fade=SolarNebulaFade(sunlight.Update(1,time,3,.75f));
            float clear=1-SolarNebulaSmoothUnit(immersionFade.Update(0,time,.75f,3));
            float visible=fade*clear;
            assert(visible>=previous-1e-6f && visible-previous<.04f);
            if(frame==fps)assert(visible<.2f);
            if(frame==2*fps)assert(visible>.3f && visible<.8f);
            previous=visible;
        }
        assert(previous>.999f);
        float before=sunlight.Update(0,4.0,3,.75f);
        assert(before>.999f); // Repeated query in the same frame cannot advance time.
        assert(sunlight.Update(0,4.0+1.0/fps,3,.75f)<before);
    }
    SolarNebulaTransition stalled;
    stalled.Update(0,0,3,.75f);
    assert(stalled.Update(1,10,3,.75f)<.034f); // Long frame/offscreen gap never snaps to full sun.
    SolarNebulaTransition fresh;assert(fresh.Update(1,0,3,.75f)==1); // Clear-space initialisation.
    assert(SolarNebulaFade(.6f)<.65f && SolarNebulaFade(1)==1);
    puts("PASS: smooth exit at 30/60/144 FPS, full strength only at clear, no hitch snap, prompt re-entry fade");
    sentinel.Next=&node;
    StarSphereDrawNebulaHalo(&camera);assert(draws==1&&lastStrength>.79f&&fog&&depth);
    assert(minDepth==0 && maxDepth==.75f && depthWrite==1 && depthFunc==2);
    assert(!GbSolarPostBurnthrough);
    float const full=lastStrength;
    through=.3f;StarSphereDrawNebulaHalo(&camera);assert(draws==2&&lastStrength>0&&lastStrength<full);
    through=1;StarSphereDrawNebulaHalo(&camera);assert(draws==2); // Hand-off to normal sun.
    through=0;visible=false;StarSphereDrawNebulaHalo(&camera);assert(draws==2);
    visible=true;active=false;StarSphereDrawNebulaHalo(&camera);assert(draws==2);active=true;
    immersion=0;blocked=false;StarSphereDrawNebulaHalo(&camera);assert(draws==2);
    blocked=true;fog=false;StarSphereDrawNebulaHalo(&camera);assert(draws==3&&!fog);
    immersion=1;burn=0;StarSphereDrawNebulaHalo(&camera);assert(draws==3);
    StarSphereDrawNebulaHalo(nullptr);assert(draws==3);
    burn=.4f;depth=false;depthWrite=0;depthFunc=8;minDepth=.2f;maxDepth=.8f;
    StarSphereDrawNebulaHalo(&camera);assert(draws==4 && !depth && !depthWrite && depthFunc==8);
    assert(minDepth==.2f && maxDepth==.8f);
    GbSolarPostBurnthrough=false; // Normal sun retains its original depth-disabled sprite.
    depth=true;DrawBillboardStates(&sphere,&camera);assert(!depth);
    puts("PASS: background depth masking, strength/crossfade, guards, fog and depth state restoration");
}
'''
(out / 'check.cpp').write_text(stub + fade + '\nvoid DrawBillboardStates(FStarSphere* sphere,void* Cam){' + setup + '}\n' + halo + test)
vc = Path('C:/Program Files/Microsoft Visual Studio/18/Community/VC/Tools/MSVC/14.51.36231')
sdk = Path('C:/Program Files (x86)/Windows Kits/10')
version = '10.0.26100.0'
env = dict(os.environ)
env['INCLUDE'] = ';'.join(str(p) for p in [vc / 'include', repo / 'src/freelancer/Client'] +
                        [sdk / 'Include' / version / x for x in ('ucrt', 'shared', 'um')])
env['LIB'] = ';'.join(str(p) for p in [vc / 'lib/x86'] +
                    [sdk / 'Lib' / version / x / 'x86' for x in ('ucrt', 'um')])
subprocess.run([str(vc / 'bin/Hostx64/x86/cl.exe'), '/nologo', '/std:c++17', '/W3', '/WX',
                '/EHsc', '/MT', 'check.cpp', '/Fecheck.exe'], cwd=out, env=env, check=True)
subprocess.run([str(out / 'check.exe')], cwd=out, check=True)

# Real D3D9 verifies equal viewport depth bounds and foreground masking.
subprocess.run([str(vc / 'bin/Hostx64/x86/cl.exe'), '/nologo', '/std:c++17', '/W3', '/WX',
                '/EHsc', '/MT', str(repo / 'tools/sun_halo/check_depth.cpp'), '/Fecheck_depth.exe',
                '/link', 'd3d9.lib', 'user32.lib'], cwd=out, env=env, check=True)
subprocess.run([str(out / 'check_depth.exe')], cwd=out, check=True)
