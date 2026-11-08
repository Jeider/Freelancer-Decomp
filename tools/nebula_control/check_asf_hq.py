"""Exercise actual field parsing and volumetric distance gates with CPU fixtures."""
from pathlib import Path
import subprocess
from build_asf_hq import ROOT, OUT, compiler_env


def block(source, start, struct=False):
    a = source.index(start)
    b = source.index('{', a)
    depth, i = 1, b + 1
    while depth:
        depth += (source[i] == '{') - (source[i] == '}')
        i += 1
    return source[a:i] + (';' if struct else '') + '\n'


def main():
    ast = (ROOT/'src/freelancer/Client/cli_asteroid.cpp').read_text(encoding='utf-8-sig')
    vol = (ROOT/'src/freelancer/Client/nebula_volume.cpp').read_text(encoding='utf-8-sig')
    prefix = r'''
#include <cassert>
#include <cstdio>
#include <cstring>
#include <vector>
#include <unordered_map>
#define FREELANCER_RP9
struct FCliAsteroid {
 int CubeSize=0,FillDistAt24=0,Flag00=0,FlagD3=0;
 unsigned char FlagD0=0,FlagD1=0,FlagD2=0;
 float TintB4=0,TintB8=0,TintBC=0,TintC0=0,TintC4=0,TintC8=0,EmptyCubeFreq=0,ScaleCC=1;
};
int FloatToIntTrunc(float f){return int(f);}
struct INI_Reader {
 std::vector<std::pair<const char*,float>> Values;int Index=-1;
 bool read_value(){return ++Index<int(Values.size());}
 bool is_value(const char* key){return !strcmp(Values[Index].first,key);}
 float get_value_float(int){return Values[Index].second;}
 bool get_value_bool(int){return Values[Index].second!=0;}
};
struct Vector {float x=0,y=0,z=0;};
namespace Universe {struct IZone {
 Vector Pos;float Radius=100;
 const Vector& GetPos()const{return Pos;}float GetRadius()const{return Radius;}
};}
struct FNebulaEffect {Universe::IZone* Zone;};
struct Settings {float AsteroidSpawn=1,ExtendFarPlane=1,ReplaceObjectFog=1,ReplaceFogOverlay=1;
 float AsteroidMaxSpawnDistance=6000,AsteroidFadeFraction=.2f;};
struct FVolumeEntry {FNebulaEffect* Nebula;Settings Settings;bool bInside=true;
 float SpanScale=1,AsteroidSurfaceDistance=0,AsteroidHazeReach=10000;};
FVolumeEntry GEntries[2];int GEntryCount=1;
FNebulaEffect* GController=nullptr;
float GControllerMarchCap=10000,GMaxAsteroidReach=6000;
const FVolumeEntry* FindEntry(const FNebulaEffect* n){
 for(int i=0;i<GEntryCount;++i)if(GEntries[i].Nebula==n)return &GEntries[i];return nullptr;}
float Clamp(float v,float a,float b){return v<a?a:v>b?b:v;}
namespace NebulaVolume {
 float InsideFarPlane(float,float);float AsteroidSpawnReach(const Universe::IZone*,float*);
 bool ReplacesObjectFog(const FNebulaEffect*);bool ReplacesFogOverlay(const FNebulaEffect*);
}
'''
    code = prefix + block(ast, 'struct NearFieldBounds', True) + block(ast, 'std::unordered_map<FCliAsteroid*,NearFieldBounds>& NearBounds()')
    code += block(ast, 'void ParseFieldSection(')
    for name in ('float NebulaVolume::InsideFarPlane(', 'float NebulaVolume::AsteroidSpawnReach(',
                 'bool NebulaVolume::ReplacesObjectFog(', 'bool NebulaVolume::ReplacesFogOverlay('):
        code += block(vol, name)
    code += r'''
int main(){
 FCliAsteroid mines,ordinary;int lod=0;
 INI_Reader config{{{"cube_size",200.f},{"fill_dist",1000.f},{"rock_normals",0.f},{"contains_fog_zone",1.f}}};
 ParseFieldSection(&mines,config,lod);
 assert(mines.CubeSize==200 && mines.FillDistAt24==1000 && mines.FlagD3==1);
 assert(!NearBounds()[&mines].RockNormals && NearBounds()[&ordinary].RockNormals);
 NearFieldBounds merged=NearBounds()[&mines];assert(!merged.RockNormals);
 NearBounds().erase(&mines); // same reset as production reload/destruction
 assert(NearBounds()[&mines].RockNormals);
 puts("PASS actual [Field] parser: mine fog, relief opt-out, unrelated field default, reload reset");
 Universe::IZone field,nebulaZone;nebulaZone.Radius=2400000;
 FNebulaEffect nebula{&nebulaZone};GController=&nebula;GEntries[0].Nebula=&nebula;
 float fade=-1;
 assert(NebulaVolume::AsteroidSpawnReach(&field,&fade)==6000 && fade>.1f);
 assert(NebulaVolume::InsideFarPlane(3000,250000)==15000);
 auto& s=GEntries[0].Settings;s.AsteroidSpawn=0;s.ExtendFarPlane=0;s.ReplaceObjectFog=0;s.ReplaceFogOverlay=0;
 assert(NebulaVolume::AsteroidSpawnReach(&field,&fade)==0 && fade==0);
 assert(NebulaVolume::InsideFarPlane(3000,250000)==3000);
 assert(NebulaVolume::InsideFarPlane(17000,250000)==17000);
 assert(!NebulaVolume::ReplacesObjectFog(&nebula) && !NebulaVolume::ReplacesFogOverlay(&nebula));
 assert(FindEntry(&nebula)!=nullptr); // the volume entry survives the native fog/distance gates
 puts("PASS actual volume gates: 6km extension disabled, retail scene/exclusion limits and fog retained");
 s.AsteroidSpawn=1;s.ExtendFarPlane=1;
 assert(NebulaVolume::AsteroidSpawnReach(&field,nullptr)==6000);
 assert(NebulaVolume::InsideFarPlane(3000,250000)==15000);
 GEntryCount=0;assert(NebulaVolume::AsteroidSpawnReach(&field,&fade)==0);
 assert(NebulaVolume::InsideFarPlane(3000,250000)==3000);
 puts("PASS ordinary volume extension and absent-volume fallback unchanged");
}
'''
    OUT.mkdir(parents=True, exist_ok=True)
    cpp = OUT/'check.cpp'
    cpp.write_text(code)
    compiler, env = compiler_env()
    subprocess.run([str(compiler/'cl.exe'), '/nologo', '/std:c++17', '/EHsc', '/O2', '/MT', str(cpp), '/Fe'+str(OUT/'check.exe')], cwd=OUT, env=env, check=True)
    subprocess.run([str(OUT/'check.exe')], check=True)


if __name__ == '__main__':
    main()
