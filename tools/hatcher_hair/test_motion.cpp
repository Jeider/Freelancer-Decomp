#include "HairMotion.h"
#include <cstdio>
#include <cstdlib>
#include <cstring>
#include <fstream>
#include <vector>
static void require(bool v,const char* text){if(!v){std::printf("FAIL %s\n",text);std::exit(1);}}
static void pose(float* m,double t,bool moving){
 float a=moving?.3f*(float)std::sin(t*3):0,b=moving?.12f*(float)std::sin(t*2):0;
 float c=std::cos(a),s=std::sin(a),cb=std::cos(b),sb=std::sin(b);
 float p[]={c,s*sb,s*cb,0,cb,-sb,-s,c*sb,c*cb};std::memcpy(m,p,sizeof(p));
}
static HairMotion::State simulate(int fps,bool moving){
 HairMotion::State state;float m[9];
 for(int i=0;i<=fps*8;++i){double t=(double)i/fps;pose(m,t,moving);state.update(t,m);
  for(auto& group:state.angle)for(float a:group)require(std::isfinite(a)&&std::fabs(a)<=.04001f,"bounded joint angle");
 }return state;
}
int main(int argc,char** argv){
 auto idle=simulate(60,false),moving=simulate(60,true),other=idle;
 float delta=0;for(int g=0;g<6;++g)for(int a=0;a<2;++a)delta+=std::fabs(moving.angle[g][a]-idle.angle[g][a]);
 require(delta>.005f,"head turns produce inertia beyond idle motion");
 auto slow=simulate(30,true),fast=simulate(144,true);
 float fpsDelta=0;for(int g=0;g<6;++g)for(int a=0;a<2;++a)fpsDelta=(std::max)(fpsDelta,std::fabs(slow.angle[g][a]-fast.angle[g][a]));
 require(fpsDelta<.012f,"frame-rate stability");
 float m[9];pose(m,8,true);auto saved=moving;moving.update(8,m);
 require(std::memcmp(&saved.angle,&moving.angle,sizeof(saved.angle))==0,"duplicate render pass does not advance motion");
 moving.update(20,m);for(auto&g:moving.angle)for(float a:g)require(a==0,"long pause resets inertia");
 require(std::memcmp(idle.angle,other.angle,sizeof(idle.angle))==0,"independent instance state");
 float source[]={.03f,.14f,.04f,0,1,0},out[6];idle.deform(source,0,out);
 require(std::memcmp(source,out,sizeof(source))==0,"fixed roots and face unchanged");
 auto deformed=simulate(60,true);deformed.deform(source,1,out);
 require(std::fabs(out[0]-source[0])+std::fabs(out[2]-source[2])>.00005f,"geometry actually moves");
 require(std::fabs(out[3]*out[3]+out[4]*out[4]+out[5]*out[5]-1)<1e-5,"normals stay normalized");
 if(argc>1){
  std::ifstream file(argv[1],std::ios::binary);unsigned count=0;file.read((char*)&count,4);
  require(count>0&&count<65536,"mesh input count");std::vector<float> vertices(count*7);file.read((char*)vertices.data(),vertices.size()*4);require(file.good(),"mesh input complete");
  HairMotion::State state;float maxTravel=0;unsigned active=0;
  for(unsigned v=0;v<count;++v)if(vertices[v*7+6]>0)++active;
  for(int frame=0;frame<360;++frame){double t=frame/60.;pose(m,t,true);state.update(t,m);
   for(unsigned v=0;v<count;++v){auto* p=&vertices[v*7];state.deform(p,p[6],out);
    for(float f:out)require(std::isfinite(f),"real mesh finite");
    if(p[6]==0)require(std::memcmp(p,out,24)==0,"real mesh fixed points unchanged");
    float d=std::sqrt((out[0]-p[0])*(out[0]-p[0])+(out[2]-p[2])*(out[2]-p[2]));maxTravel=(std::max)(maxTravel,d);
    require(d<.006f,"real mesh motion bounded below six millimetres");
   }
  }
  std::printf("Actual head: %u points, %u moving, maximum travel %.3f mm\n",count,active,maxTravel*1000);
  require(maxTravel>.00005f,"actual head reacts to motion");
 }
 std::printf("PASS: idle, turn inertia, dt stability (%.5f), fixed roots, normals, repeated pass and reset\n",fpsDelta);
}
