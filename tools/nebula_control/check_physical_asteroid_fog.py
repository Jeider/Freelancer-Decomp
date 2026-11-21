"""Production object queue/fog regression, plus the real-asset GPU overlay test."""
import json
from pathlib import Path
import subprocess
import sys
import check_asteroid_mesh as mesh

ROOT=mesh.ROOT
OUT=ROOT/'out/graphics_settings/nebula_asteroid_mesh/fog_coverage/physical_order'
STUB=r'''
#include <cassert>
#include <cmath>
#include <cstdio>
#include <cstring>
#include <cstdint>
#include "common_server_asteroid.h"
struct Vector {float x=0,y=0,z=0;};
namespace Archetype {struct EqObj {bool bNomad=false;};}
struct CObject {unsigned ObjectClass=0x303;Archetype::EqObj* Archetype=nullptr;};
struct CSolar:CObject {unsigned TypeBits=SERVER_ASTEROID_TYPE;};
struct ICamera {float eye[3]={};float nearZ=1,farZ=10000;
 float const* GetPosition(){return eye;}float GetZNear(){return nearZ;}};
using FSpaceCamera=ICamera;
ICamera* AsCamera(FSpaceCamera* p){return p;}
struct FNebulaEffect {
 float colour[3]={.6f,.35f,.08f};
 float FogFactor(float const* p)const{return p[0]==0?2500.f:20000.f;}
 float GetFloat2AC()const{return 200;}
 float const* CopyFogRgb(float* p)const{memcpy(p,colour,12);return p;}
};
struct FClientGameobj {int ManagerKind=2;CSolar solar;CObject* Object=&solar;
 unsigned DrawStateA=0,DrawStateB=0,type=SERVER_ASTEROID_TYPE;Vector pos{2700,0,0};
 Vector const& get_position(){return pos;}
 void get_type(unsigned& out){out=type;}
 float Slot178(Vector& centre){centre=pos;return 35;}
 unsigned Slot18c(unsigned* factor){*factor=DrawStateB;return DrawStateA;}
 unsigned* Slot17c(unsigned* lod,void*,void*){*lod=4;return lod;}
};
struct FClientSolarGameobj:FClientGameobj {void* Field_0xe4=nullptr;};
float lastFogEnd=0;unsigned lightingCalls=0;
void FogApplyColorAndRange(float const*,float,float end){lastFogEnd=end;}
void StarSysApplyObjectLighting(float const* pos,float,void*,unsigned,unsigned,unsigned char){++lightingCalls;lastFogEnd=pos[0]==0?2500.f:20000.f;}
double EffectPerfOneMinus(){return 1;}
enum {kGameOptNebula,kGameOptLighting};bool GetGameOption(int){return true;}
bool trial=true,volume=false;unsigned NebulaFogShapeScope(){return trial?512:0;}
namespace NebulaVolume {bool ReplacesObjectFog(FNebulaEffect*){return volume;}}
FNebulaEffect nebula;FNebulaEffect* G_FieldController=&nebula;int G_FieldEnclosure=1;
float G_SpaceDrawRange=10000,G_DrawCtxZFar=10000,G_FieldRadiusSq=1e10;
const float kDefaultZFar=250000,kNearBucketDistSq=40000;
void CameraSetNearFar(FSpaceCamera* c,float n,float f){c->nearZ=n;c->farZ=f;}
int bucket=-1;void PushNode(unsigned b,FClientGameobj*,float,unsigned){bucket=int(b);}
'''
TEST=r'''
int main(int argc,char**){
 FClientSolarGameobj rock;FSpaceCamera camera;
 // The real clear-zone edge can contain rocks: dynamic exclusion radius 2500,
 // nebula exclusion radius 3000. Retail bucket 0 is BEFORE the depthless cover.
 EnqueueObject(&rock,&camera);
 printf("partial enclosure / clear-zone physical rock: bucket %d\n",bucket);
 if(argc>1){assert(bucket==0);puts("REPRODUCED pre-cover submission");return 0;}
 assert(bucket==1);
 GameobjUpdateDrawLighting(&rock,&camera);assert(lightingCalls==1&&lastFogEnd==2500);
 rock.DrawStateA=unsigned(uintptr_t(&nebula));float immersion=1;memcpy(&rock.DrawStateB,&immersion,4);
 bucket=-1;EnqueueObject(&rock,&camera);assert(bucket==1);
 // Both foreground and full-volume schedules retain the asteroid after cover.
 volume=true;bucket=-1;EnqueueObject(&rock,&camera);assert(bucket==1);volume=false;
 // Off/low, no controller and exterior scenes keep native rules.
 rock.DrawStateA=rock.DrawStateB=0;trial=false;bucket=-1;EnqueueObject(&rock,&camera);assert(bucket==0);
 GameobjUpdateDrawLighting(&rock,&camera);assert(lastFogEnd==20000);trial=true;
 // The later solar trial deliberately extends the same handling to stations.
 rock.type=rock.solar.TypeBits=0x100;bucket=-1;EnqueueObject(&rock,&camera);assert(bucket==1);
 GameobjUpdateDrawLighting(&rock,&camera);assert(lastFogEnd==2500);
 rock.type=rock.solar.TypeBits=SERVER_ASTEROID_TYPE;G_FieldEnclosure=0;bucket=-1;EnqueueObject(&rock,&camera);assert(bucket==0);
 GameobjUpdateDrawLighting(&rock,&camera);assert(lastFogEnd==20000);
 G_FieldEnclosure=1;G_FieldController=nullptr;bucket=-1;EnqueueObject(&rock,&camera);assert(bucket==0);
 GameobjUpdateDrawLighting(&rock,&camera);assert(lastFogEnd==20000);
 // Keep existing object range/culling rules, including unrelated solar buckets.
 G_FieldController=&nebula;G_FieldEnclosure=2;bucket=-1;EnqueueObject(&rock,&camera);assert(bucket==-1);
 puts("PASS real enqueue/lighting: clear-zone transition, camera fog range, native scopes and existing culling");
}
'''

def cpu_check(expect_bug=False):
    sys.path.insert(0,str(ROOT/'tools/physics'))
    from check_gravity import function
    folder=OUT/'probe';folder.mkdir(parents=True,exist_ok=True)
    source=folder/'queue.cpp'
    target='src/freelancer/Client/space_scene_obj_draw.cpp'
    policy=function('src/freelancer/Client/nebula_fog_shape.h','inline bool NebulaFogSolarHull(')
    source.write_text(STUB+policy+function(target,'void GameobjUpdateDrawLighting(')+function(target,'void EnqueueObject(')+TEST)
    compiler,env=mesh.compiler_env()
    with (OUT/'queue_build.log').open('w') as log:
        subprocess.run([str(compiler/'cl.exe'),'/nologo','/EHsc','/MD','/O2','/std:c++17','/DFREELANCER_RP9',
            '/Isrc/Include',str(source),'/Fo'+str(folder/'queue.obj'),'/Fe'+str(folder/'queue.exe')],
            env=env,stdout=log,stderr=subprocess.STDOUT,check=True)
    result=subprocess.run([str(folder/'queue.exe')]+(['before'] if expect_bug else []),env=env,capture_output=True,text=True)
    (OUT/('queue_before.log' if expect_bug else 'queue_after.log')).write_text(result.stdout+result.stderr)
    print(result.stdout);result.check_returncode()

def main():
    cpu_check('--expect-bug' in sys.argv)
    if '--cpu-only' in sys.argv or '--expect-bug' in sys.argv:return
    import check_asteroid_draw_order as order
    mesh.OUT=OUT;mesh.PROBE=OUT/'probe'
    mesh.EXTRA_DEFINES+=['/DASTEROID_PHYSICAL_ORDER_CHECK']
    mesh.EXTRA_SOURCES+=['tools/nebula_control/check_physical_asteroid_fog.py',
        'tools/nebula_control/install_physical_asteroid_fog.py','src/Include/common_server_asteroid.h',
        'tools/nebula_control/asteroid_physical_order_cases.inl']
    order.main()
    path=OUT/'checks.json';report=json.loads(path.read_text())
    report.update(shader_changes=[],scope='physical Omega-15 asteroids after fog cover, with camera-based range matching distant mesh grid')
    # Guard all shader files as well as the cloud/content inputs used by order.main.
    for root in (ROOT,Path('D:/Games/FL_MOD')):
        for name in ('surface_material.hlsl','far_rocks.hlsl'):
            p=root/'DATA_EXTRA/SHADERS'/name;report['guards'][str(p)]=mesh.digest(p)
    path.write_text(json.dumps(report,indent=2))

if __name__=='__main__':main()
