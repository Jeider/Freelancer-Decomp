#pragma once
#include <algorithm>
#include <cmath>
#include <cstdint>
#include <cstring>

// Shared recipe and bounded protocol. No renderer, physics or savegame pointers.
namespace ProceduralAsteroids {
constexpr float CellSize=1000.f, Activate=2000.f, Suspend=2400.f, View=6000.f;
constexpr unsigned PerCell=6, MaxModels=4, Chunk=12;
constexpr unsigned Channel=0x0001ff02, Magic=0x31524150, Version=2;
constexpr float SpinRate=.035f;
using Key=std::uint64_t;
inline Key Hash(Key x){x+=0x9e3779b97f4a7c15ull;x=(x^(x>>30))*0xbf58476d1ce4e5b9ull;x=(x^(x>>27))*0x94d049bb133111ebull;return x^(x>>31);}
inline double Unit(Key& h){h=Hash(h);return double(h>>40)/16777216.0;}
inline int Cell(float x){return int(std::floor(double(x)/CellSize));}
inline Key Id(int x,int y,int z,unsigned slot){return Key(std::uint16_t(x))|(Key(std::uint16_t(y))<<16)|(Key(std::uint16_t(z))<<32)|(Key(slot)<<48);}
inline bool ValidKey(Key key){return (key>>48)<PerCell;}
struct Rock {Key key=0;float position[3]={},rotation[4]={0,0,0,1};unsigned model=0,colour=0xffffffff;};
inline void Spin(float* rotation,float const* angular,float seconds){
    double speed=std::sqrt(double(angular[0])*angular[0]+double(angular[1])*angular[1]+double(angular[2])*angular[2]);
    if(speed<1e-10||seconds==0)return;
    double half=speed*seconds*.5,s=std::sin(half)/speed,c=std::cos(half);
    float b[4]={float(angular[0]*s),float(angular[1]*s),float(angular[2]*s),float(c)},a[4];std::memcpy(a,rotation,16);
    rotation[0]=a[3]*b[0]+a[0]*b[3]+a[1]*b[2]-a[2]*b[1];
    rotation[1]=a[3]*b[1]+a[1]*b[3]+a[2]*b[0]-a[0]*b[2];
    rotation[2]=a[3]*b[2]+a[2]*b[3]+a[0]*b[1]-a[1]*b[0];
    rotation[3]=a[3]*b[3]-a[0]*b[0]-a[1]*b[1]-a[2]*b[2];
}
inline void Spin(float* rotation,float seconds){float angular[3]={0,SpinRate,0};Spin(rotation,angular,seconds);}
inline Rock Generate(Key key,unsigned seed,unsigned models){
    Rock rock;rock.key=key;
    int cell[3]={std::int16_t(key),std::int16_t(key>>16),std::int16_t(key>>32)};
    Key h=Hash(key^Hash(seed));
    // Six jittered, distinct octants per cell. The 100 m margin keeps native
    // 42 m-radius meshes apart, including neighbours across cell boundaries;
    // otherwise overlapping decorative seeds could never acquire a collider.
    unsigned octant=unsigned(key>>48)^unsigned(Hash((key&0x0000ffffffffffffull)^Hash(seed))&7);
    for(int i=0;i<3;++i)rock.position[i]=float(cell[i]*CellSize+((octant>>i)&1)*500+100+Unit(h)*300);
    rock.model=models ? (std::min)(models-1,unsigned(Unit(h)*models)) : 0;
    double u=Unit(h),a=6.283185307179586*Unit(h),b=6.283185307179586*Unit(h);
    rock.rotation[0]=float(std::sqrt(1-u)*std::sin(a));rock.rotation[1]=float(std::sqrt(1-u)*std::cos(a));
    rock.rotation[2]=float(std::sqrt(u)*std::sin(b));rock.rotation[3]=float(std::sqrt(u)*std::cos(b));
    rock.colour=0xff000000u|(unsigned(100+155*Unit(h))<<16);
    return rock;
}
template<class Emit> void Around(float const* centre,float radius,unsigned seed,unsigned models,Emit emit){
    int lo[3],hi[3];for(int i=0;i<3;++i){lo[i]=Cell(centre[i]-radius);hi[i]=Cell(centre[i]+radius);}
    for(int z=lo[2];z<=hi[2];++z)for(int y=lo[1];y<=hi[1];++y)for(int x=lo[0];x<=hi[0];++x)
        for(unsigned slot=0;slot<PerCell;++slot){auto rock=Generate(Id(x,y,z,slot),seed,models);double d=0;
            for(int i=0;i<3;++i){double a=rock.position[i]-centre[i];d+=a*a;}if(d<=double(radius)*radius)emit(rock);}
}
enum Kind:unsigned {Request=1,Begin=2,Records=3,End=4,Delta=5};
enum Flags:unsigned {Dead=1,Active=2};
struct Entry {
    Key key=0;unsigned object=0,flags=0;
    float position[3]={},rotation[4]={0,0,0,1},stamp=0,spin[3]={0,SpinRate,0},reserved=0;
};
struct Header {
    unsigned magic=Magic,version=Version,kind=0,system=0,zone=0,epoch=0,token=0,revision=0,seed=0,models=0;
    unsigned archetypes[MaxModels]={},count=0;float clock=0;
};
struct Packet {Header header;Entry entries[Chunk];};
static_assert(sizeof(Header)==64 && sizeof(Entry)==64 && sizeof(Packet)==832,"Procedural asteroid wire layout");
inline unsigned Bytes(Packet const& p){return sizeof(Header)+p.header.count*sizeof(Entry);}
inline bool Decode(void const* bytes,unsigned size,Packet& out){
    if(!bytes || size<sizeof(Header) || size>sizeof(Packet))return false;
    out=Packet{};std::memcpy(&out.header,bytes,sizeof(Header));auto const& h=out.header;
    if(h.magic!=Magic || h.version!=Version || h.kind<Request || h.kind>Delta || !h.system || !h.zone || !h.token ||
       h.models>MaxModels || h.count>Chunk || size!=Bytes(out) || !std::isfinite(h.clock) || h.clock<0)return false;
    if((h.kind==Request || h.kind==Begin || h.kind==End) && h.count)return false;
    if(h.kind!=Request && (!h.epoch || !h.models))return false;
    std::memcpy(out.entries,static_cast<unsigned char const*>(bytes)+sizeof(Header),h.count*sizeof(Entry));
    for(unsigned i=0;i<h.count;++i){auto const& e=out.entries[i];
        if(!ValidKey(e.key) || (e.flags&~(Dead|Active)) || ((e.flags&Dead)&&(e.flags&Active)) ||
           ((e.flags&Active)!=0)!=(e.object!=0))return false;
        for(float p:e.position)if(!std::isfinite(p)||std::fabs(p)>10000000.f)return false;
        float q=0;for(float p:e.rotation){if(!std::isfinite(p))return false;q+=p*p;}
        if(std::fabs(q-1)>0.02f)return false;
        if(!std::isfinite(e.stamp)||e.stamp<0)return false;
        for(float spin:e.spin)if(!std::isfinite(spin)||std::fabs(spin)>100)return false;
    }
    return true;
}
}
