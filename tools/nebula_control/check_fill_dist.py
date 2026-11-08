"""CPU regression: production field tick and native fill/fade expressions, RP8 and RP9."""
import re
import subprocess
from build_asf_hq import ROOT, compiler_env
from check_asf_hq import block

OUT = ROOT/'src/obj/field_fog/check'


def main():
    source = (ROOT/'src/freelancer/Client/cli_asteroid.cpp').read_text(encoding='utf-8-sig')
    tick = block(source, 'void CliAsteroidTickOne(')
    draw = block(source, 'void CliAsteroidDrawNearField(')
    assert 'AsteroidSpawnReach' not in source and 'FillOverride' not in source and 'FadeBandOverride' not in source
    # Extract the expressions actually used by the cube renderer, avoiding a GPU dependency.
    expressions = '\n'.join(re.search(rf'(?:double|float) const {name}\s*=.*?;', draw, re.S)[0]
                            for name in ('Margin', 'Fill', 'HalfCube', 'ReachD', 'Reach', 'FadeStart'))
    prefix = r'''
#include <algorithm>
#include <cassert>
#include <cstdio>
struct Vector{float x,y,z;};
struct FSpaceCamera{float Pos[3]={};const float* GetPosition(){return Pos;}};
FSpaceCamera* AsCamera(FSpaceCamera* c){return c;}
struct CommonField{bool Near=true;bool near_field(Vector){return Near;}};
struct Billboard{float Float40=1250,Float44=1150;};
struct FCliDynamicAsteroid{float PlacementRadius=0;};
struct FCliAsteroid{
 CommonField* CmnField=nullptr;int FillDistAt24=1000,CubeSize=200,Flag198=1;
 float Scale230=1,ScaleCC=1;::Billboard Billboard;void* ExclusionMgr=nullptr;
 void** DynBegin=nullptr;void** DynEnd=nullptr;
};
enum{ kGameOptAsteroidExt,kGameOptEffectsGroup,kGameOptAsteroids,kGameOptObjectsGroup };
int GetGameOption(int){return 2;}bool FarRocksReplacesBillboards(FCliAsteroid*){return false;}
bool BillboardNearCamera(Billboard*,Vector){return true;}
void CliAsteroidAmbientPass(FCliAsteroid*,FSpaceCamera*,float){}
const float kAmbientScaleArg=100;
float CliDynamicAsteroidBandThickness(const FCliDynamicAsteroid*){return 0;}
void BillboardLinkDynamicBand(Billboard*,float,float){}
int BillboardCalls=0,DrawCalls=0;float ActualFill=0,ActualReach=0,ActualFade=0;
void BillboardDraw(Billboard* b,FSpaceCamera*,void*,int){
 ++BillboardCalls;assert(b->Float40==1250 && b->Float44==1150);}
void CliDynamicAsteroidDraw(FCliDynamicAsteroid*,FSpaceCamera*,unsigned char*,FCliAsteroid*){}
namespace NebulaVolume{bool Active=true;bool IsActive(){return Active;}}
FCliAsteroid* GTransparentFields[64];unsigned GTransparentFieldCount=0;
void CliAsteroidDrawNearField(FCliAsteroid* Field,FSpaceCamera*){
'''
    code = prefix+expressions+r'''
 ++DrawCalls;ActualFill=float(Fill);ActualReach=Reach;ActualFade=FadeStart;
}
'''+tick+r'''
int main(){
 CommonField common;FCliAsteroid f;f.CmnField=&common;FSpaceCamera camera;
 for(bool volume:{false,true}){
  NebulaVolume::Active=volume;
  for(int fill:{300,1000,15000})for(float detail:{.5f,1.f,2.f}){
   f.FillDistAt24=fill;f.Scale230=detail;int before=DrawCalls;
   CliAsteroidTickOne(&f,&camera);
   assert(DrawCalls==before+1 && ActualFill==fill*detail);
   assert(ActualReach==fill*detail+250 && ActualFade==ActualReach-100);
  }
  common.Near=false;int before=DrawCalls;CliAsteroidTickOne(&f,&camera);
  assert(DrawCalls==before);common.Near=true;
 }
 assert(BillboardCalls==20);
#ifdef FREELANCER_RP9
 f.ScaleCC=.5f;NebulaVolume::Active=true;int before=DrawCalls;
 CliAsteroidTickOne(&f,&camera);assert(DrawCalls==before && GTransparentFieldCount==1);
 // The actual post-volume queue uses the same authored-distance draw function.
 CliAsteroidDrawTransparentFields(&camera);assert(GTransparentFieldCount==0 && DrawCalls==before+1);
 assert(ActualFill==30000);
#endif
 puts("PASS production tick: authored fills 300/1000/15000, detail .5/1/2, volume on/off, native near-field and billboard limits");
}
'''
    # Insert the real deferred queue before main; it also must retain the field's distance.
    queue = '#ifdef FREELANCER_RP9\n'+block(source, 'void CliAsteroidDrawTransparentFields(')+'#endif\n'
    code = code.replace('int main(){', queue+'int main(){')
    OUT.mkdir(parents=True, exist_ok=True)
    cpp = OUT/'fill.cpp'
    cpp.write_text(code)
    compiler, env = compiler_env()
    for rp9 in (False, True):
        exe = OUT/('fill_rp9.exe' if rp9 else 'fill_rp8.exe')
        args = [str(compiler/'cl.exe'), '/nologo', '/O2', '/std:c++17', '/EHsc', '/MT', str(cpp), '/Fe'+str(exe)]
        if rp9:
            args.append('/DFREELANCER_RP9')
        subprocess.run(args, cwd=OUT, env=env, check=True)
        subprocess.run([str(exe)], check=True)


if __name__ == '__main__':
    main()
