"""Exercise production cockpit pass ordering and tunnel lighting with recorded render calls."""
import os
import subprocess
from pathlib import Path

repo = Path(__file__).resolve().parents[2]
out = repo / 'src/obj/cockpit_scene_check'
out.mkdir(parents=True, exist_ok=True)


def function(file, signature):
    source = (repo / 'src/freelancer/Client' / file).read_text()
    start = source.index(signature)
    end = source.index('{', start) + 1
    depth = 1
    while depth:
        depth += (source[end] == '{') - (source[end] == '}')
        end += 1
    return source[start:end]


stub = r'''
#include <cassert>
#include <cstdio>
#include <vector>
#include <algorithm>
enum Event {World, Wire, ClearDepth, BeginCabin, ClearLights, Ambient, TunnelLight, NormalLight, Mesh, Halo, Antialias, Hud, EndCabin};
std::vector<Event> events;
namespace RenderEx {void AntialiasScene(){events.push_back(Antialias);}}
bool sceneDepth=false, tunnelLit=false, lighting=true, hasMesh=true;
int hud=1;
unsigned char ambient[3]={};
constexpr int kGameOptHud=10,kWin3DClearDepth=2;
struct Vector {float x=1,y=2,z=3;};
struct ICamera {float nearZ=3,farZ=10000;float GetZNear(){return nearZ;}float GetZFar(){return farZ;}};
struct FSpaceCamera:ICamera {};
void StarSphereDrawNebulaHalo(FSpaceCamera*){events.push_back(Halo);}
struct FGameCamera:FSpaceCamera {};
struct FHudCamera:FGameCamera {struct Watcher {char storage[16];bool valid=true;void* target(){return valid?storage+8:nullptr;}} Watched;};
struct FFirstPersonCamera:FHudCamera {int Mesh=0;};
FSpaceCamera* SpaceCameraOf(FHudCamera* c){return c;}
ICamera* AsCamera(FSpaceCamera* c){return c;}
struct Perf {float Applied=1;} cockpit;
Perf* FindPerfOption(const char*){return &cockpit;}
int GetGameOption(int key){assert(key==kGameOptHud);return hud;}
void SpaceObjDrawPass(FSpaceCamera*,unsigned,unsigned){events.push_back(World);sceneDepth=true;}
void VulnerableTargetingDraw(FSpaceCamera* c){
    assert(sceneDepth && c->nearZ==3 && c->farZ==10000);
    events.push_back(Wire);
}
void ClearWin3DBuffers(int){events.push_back(ClearDepth);sceneDepth=false;}
void SpaceEnvFxBeginCockpitPass(FSpaceCamera*){events.push_back(BeginCabin);}
void SpaceEnvFxEndCockpitPass(FSpaceCamera*){events.push_back(EndCabin);}
void SpaceCameraSetNearFar(FSpaceCamera* c,float n,float f){c->nearZ=n;c->farZ=f;}
void Win3DApplyCamera(ICamera* c){assert(c->nearZ==.05f && c->farZ==500);}
struct FEngineLight {};
struct FGameLight:FEngineLight {};
struct FGateTunnel {FGameLight* Light=nullptr;};
struct FJumpShipEffect {unsigned char* Ambient=nullptr;FGateTunnel* Tunnel=nullptr;};
struct IObjRW {};
struct FClientGameobj:IObjRW {void Slot184(void*){events.push_back(NormalLight);}};
struct FClientShipGameobj:FClientGameobj {
    int Field_0x158=0;void* Field_0x188=nullptr;
    Vector get_position(){return {};}
    unsigned Slot18c(unsigned* b){*b=0;return 0;}
    void Slot184(void*);
} ship;
void* GetPlayerObjRW(){return static_cast<IObjRW*>(&ship);}
void EngineLightClearRegisteredList(){events.push_back(ClearLights);tunnelLit=false;}
void EngineLightSetAmbientRgbBytes(const unsigned char* rgb){events.push_back(Ambient);std::copy(rgb,rgb+3,ambient);}
void EngineLightSetPosition(FEngineLight*,const float* p){assert(p[0]==1 && p[1]==2 && p[2]==3);}
void EngineLightApplyList(FEngineLight* const* lights,unsigned count,ICamera* camera,const float*){
    assert(count==1 && lights[0] && camera->nearZ==.05f);
    events.push_back(TunnelLight);tunnelLit=lighting;
}
float SpaceEffectPerfOneMinus(){return 1;}
float ClientMeshHolderGetBoundingSphere(int*,float* center){center[0]=center[1]=center[2]=0;return 5;}
void SpaceApplyObjectLighting(const float*,float,FSpaceCamera*,unsigned,unsigned,unsigned char){events.push_back(NormalLight);}
bool ClientMeshHolderHasInstance(int*){return hasMesh;}
bool expectTunnelLight=false;
void ClientMeshHolderRender(int*,FSpaceCamera* c,unsigned){
    assert(!sceneDepth && c->nearZ==.05f && c->farZ==500);
    assert(tunnelLit==expectTunnelLight);events.push_back(Mesh);
}
void HudCameraDraw(FGameCamera* c){assert(c->nearZ==3 && c->farZ==10000);events.push_back(Hud);}
struct IRPSurfaceContext {void SetCockpitSurface(int){}void Release(){}} finish;
struct IRPWeaponGlints {void SetWeaponGlintReceiverBounds(const float*,float){}void SetWeaponGlintReceiver(int){}void Release(){}} glints;
namespace Iids {constexpr int RPSurfaceContext=1,RPWeaponGlints=2;}
struct Pipe {
    void SetDepthRange(float,float){}
    void QueryInterface(int id,void** out){*out=id==Iids::RPSurfaceContext?static_cast<void*>(&finish):static_cast<void*>(&glints);}
} pipe;
struct Batcher {void FlushAll(unsigned){}} batcher;
namespace DALib {Pipe* Pipeline=&pipe;Batcher* MaterialBatcher=&batcher;}
void SpaceSetCockpitGlintBounds(const float*,float){}
'''

checks = r'''
int main(){
    unsigned char rgb[3]={10,30,70};FGameLight light;FGateTunnel tunnel{&light};
    FJumpShipEffect effect{rgb,&tunnel};
    unsigned cases=0;
    for(int jump:{0,2,3}) for(bool cabin:{false,true}) for(bool hudOn:{false,true})
    for(bool lit:{false,true}) for(int missing:{0,1,2,3,4}){
        events.clear();sceneDepth=false;tunnelLit=false;std::fill(ambient,ambient+3,static_cast<unsigned char>(0));
        lighting=lit;hud=hudOn;cockpit.Applied=cabin?1.f:0.f;
        ship.Field_0x158=jump;ship.Field_0x188=missing==1?nullptr:&effect;
        effect.Tunnel=missing==2?nullptr:&tunnel;tunnel.Light=missing==3?nullptr:&light;
        effect.Ambient=missing==4?nullptr:rgb;
        expectTunnelLight=cabin && jump!=0 && lit && (missing==0 || missing==4);
        FFirstPersonCamera camera;
        FirstPersonCameraSceneDraw(&camera,0xffff,0);
        assert(events[0]==World && events[1]==Wire);
        assert(std::count(events.begin(),events.end(),Wire)==1);
        auto clear=std::find(events.begin(),events.end(),ClearDepth);
        assert((clear!=events.end())==(cabin || hudOn));
        if(clear!=events.end()) assert(clear>events.begin()+1);
        assert(std::count(events.begin(),events.end(),Mesh)==(cabin?1:0));
        const bool hasTunnel=cabin && jump!=0 && (missing==0 || missing==4);
        assert(std::count(events.begin(),events.end(),TunnelLight)==(hasTunnel?1:0));
        if(cabin && jump && missing!=1 && missing!=4) assert(std::equal(ambient,ambient+3,rgb));
        assert(events[events.size()-2]==Hud && events.back()==EndCabin);
#ifdef FREELANCER_RP9
        assert(std::count(events.begin(),events.end(),Antialias)==1);
        assert(events[events.size()-3]==Antialias); // Complete cabin + world, before HUD.
        assert(std::count(events.begin(),events.end(),Halo)==1);
        assert(events[events.size()-4]==Halo); // Halo overlays the cabin, AA follows it.
#else
        assert(std::count(events.begin(),events.end(),Antialias)==0);
#endif
        assert(camera.nearZ==3 && camera.farZ==10000);++cases;
    }
    events.clear();FFirstPersonCamera detached;detached.Watched.valid=false;
    FirstPersonCameraSceneDraw(&detached,0xffff,0);assert(events.empty());
    std::printf("PASS: %u cockpit draw cases; world wire before depth clear, tunnel light/ambient, projection restoration and detached camera\n",cases);
}
'''

code = stub + function('client_gameobj.cpp', 'void FClientShipGameobj::Slot184(')
code += function('space_camera_first.cpp', 'void FirstPersonCameraSceneDraw(') + checks
(out / 'check.cpp').write_text(code)
vc = Path('C:/Program Files/Microsoft Visual Studio/18/Community/VC/Tools/MSVC/14.51.36231')
sdk = Path('C:/Program Files (x86)/Windows Kits/10')
version = '10.0.26100.0'
env = dict(os.environ)
env['INCLUDE'] = ';'.join(str(p) for p in [vc / 'include'] +
                        [sdk / 'Include' / version / x for x in ('ucrt', 'shared', 'um')])
env['LIB'] = ';'.join(str(p) for p in [vc / 'lib/x86'] +
                    [sdk / 'Lib' / version / x / 'x86' for x in ('ucrt', 'um')])
for mode in ('rp8', 'rp9'):
    args = ['/DFREELANCER_RP9'] if mode == 'rp9' else []
    subprocess.run([str(vc / 'bin/Hostx64/x86/cl.exe'), '/nologo', '/std:c++17', '/W4', '/WX',
                    '/EHsc', '/MT', *args, 'check.cpp', f'/Fe{mode}.exe'], cwd=out, env=env, check=True)
    subprocess.run([str(out / f'{mode}.exe')], cwd=out, check=True)
