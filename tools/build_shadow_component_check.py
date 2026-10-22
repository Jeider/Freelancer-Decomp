from pathlib import Path
s=Path('src/freelancer/Client/space_scene_obj_draw.cpp').read_text()
body=s[s.index('    struct FShadowComponentMotion'):s.index('    IRPLocalShadows* BuildLocalShadows')]
prefix=r'''
#include <windows.h>
#include <map>
#include <vector>
#include <cmath>
#include <cstring>
#include <cstdio>
#include <cassert>
void* G_InvalidEngineHandle=(void*)-1;
struct Node {float M[12]={1,0,0,0,1,0,0,0,1,0,0,0};float R=1;float C[3]={};void* Arch=(void*)100;std::vector<void*> Children;};
struct IEngine {
 std::map<void*,Node> Nodes;
 float* GetInstanceTransform(void* i){return Nodes.at(i).M;}
 void* GetInstanceArchetype(void* i){return Nodes.at(i).Arch;}
 void ReleaseHandle(void*){}
 long GetInstanceExtent(void* i,int,float* r,float* c){*r=Nodes.at(i).R;memcpy(c,Nodes.at(i).C,12);return 0;}
 void* GetRelatedInstance(void* i,int,void* cursor){auto& v=Nodes.at(i).Children;if(cursor==(void*)-1)return v.empty()?(void*)-1:v[0];for(size_t j=0;j<v.size();j++)if(v[j]==cursor)return j+1<v.size()?v[j+1]:(void*)-1;return (void*)-1;}
};
namespace DALib {IEngine* Engine;}
'''
main=r'''
int main(){
 IEngine e;DALib::Engine=&e;void *root=(void*)1,*panel=(void*)2,*turret=(void*)3;
 e.Nodes[root].Children={panel,turret};e.Nodes[panel];e.Nodes[turret];
 std::vector<void*> fixed,live;
 auto frame=[&](DWORD time,bool allow=true){fixed.clear();live.clear();++G_ShadowMotionFrame;CollectShadowComponents(root,allow,time,fixed,live);};
 frame(100);assert(fixed.empty()&&live.size()==3);
 frame(700);assert(fixed.size()==3&&live.empty());
 e.Nodes[turret].M[9]=10;frame(710);assert(fixed.size()==2&&live.size()==1&&live[0]==turret);
 frame(1300);assert(fixed.size()==3&&live.empty());
 e.Nodes[panel].Arch=(void*)200;frame(1310);assert(fixed.size()==2&&live.size()==1&&live[0]==panel);
 frame(1320,false);assert(fixed.empty()&&live.size()==3);
 frame(2000);assert(fixed.empty()&&live.size()==3);
 puts("PASS: fixed panels cached independently; moving turret, mesh replacement, animated root and reappearance stay live");
 float eye[]={0,0,0},ray[]={0,0,1};
 auto visible=[&](){return NearShadowComponentVisible(panel,eye,ray,150,200);};
 e.Nodes[panel].M[9]=0;e.Nodes[panel].M[11]=0;assert(visible());
 e.Nodes[panel].M[9]=1000;assert(!visible());
 e.Nodes[panel].M[9]=0;e.Nodes[panel].M[11]=1000;assert(!visible());
 e.Nodes[panel].M[11]=-300;assert(visible());
 e.Nodes[panel].M[9]=151;e.Nodes[panel].M[11]=0;assert(visible());
 e.Nodes[panel].R=1000;assert(visible());
 e.Nodes[panel].M[9]=10000;assert(!visible());
 puts("PASS: near-map caster culling preserves upstream, edge and enclosing geometry; rejects remote panel clusters");
}
'''
Path('src/obj').mkdir(parents=True, exist_ok=True)
Path('src/obj/shadow_component_check.cpp').write_text(prefix+body+main)
