#pragma once
#include <algorithm>
#include <array>
#include <cmath>
#include <cstdint>
#include <cstring>
#include <vector>

namespace CloakGeometry
{
struct Vertex { float P[3], N[3]; };
struct Part { unsigned VertexStart, VertexCount, IndexStart, IndexCount, GroupStart, GroupCount; };
using Key = std::array<uint64_t,4>;
inline uint64_t Fingerprint(const void* data,size_t bytes)
{
    uint64_t hash=14695981039346656037ull;
    auto* p=static_cast<const unsigned char*>(data);
    for(size_t i=0;i<bytes;++i)hash=(hash^p[i])*1099511628211ull;
    return hash;
}
inline Key ContentKey(uint64_t library,const Part& part)
{
    return {{library,(uint64_t(part.VertexStart)<<32)|part.VertexCount,
        (uint64_t(part.IndexStart)<<32)|part.IndexCount,(uint64_t(part.GroupStart)<<32)|part.GroupCount}};
}
template<class T> T Read(const void* data,size_t offset)
{ T value;std::memcpy(&value,static_cast<const unsigned char*>(data)+offset,sizeof(value));return value; }
inline unsigned Stride(unsigned fvf)
{
    if((fvf&0x0e)!=2 || ((fvf>>8)&15)>8)return 0;
    unsigned stride=12+((fvf&0x10)?12:0)+((fvf&0x40)?4:0)+((fvf&0x80)?4:0);
    for(unsigned i=0;i<((fvf>>8)&15);++i)stride+=8; // VMesh header has a 16-bit FVF: 2D texcoords.
    return stride;
}
inline size_t Bytes(const void* data)
{ return 16+12u*Read<uint16_t>(data,8)+2u*Read<uint16_t>(data,10)+size_t(Stride(Read<uint16_t>(data,12)))*Read<uint16_t>(data,14); }
inline bool Decode(const void* data,size_t bytes,const Part& part,std::vector<Vertex>& out)
{
    out.clear();if(!data||bytes<16)return false;
    unsigned groups=Read<uint16_t>(data,8),indices=Read<uint16_t>(data,10),fvf=Read<uint16_t>(data,12);
    unsigned vertices=Read<uint16_t>(data,14),stride=Stride(fvf);
    if(!stride||Read<uint32_t>(data,4)!=4||Bytes(data)>bytes||part.GroupStart+part.GroupCount>groups||
       part.VertexStart+part.VertexCount>vertices||part.IndexStart>indices)return false;
    size_t ib=16+12u*groups,vb=ib+2u*indices;
    unsigned cursor=part.IndexStart;
    // Retail draws the selected facegroups, not Ref.IndexCount. Some exporters put
    // an end offset in that metadata field; the actual group counts remain valid.
    out.reserve((std::min)(part.IndexCount,indices));
    for(unsigned g=part.GroupStart;g<part.GroupStart+part.GroupCount;++g){
        unsigned base=(Read<uint8_t>(data,0)&1)?Read<uint16_t>(data,16+12*g+4):0;
        unsigned count=Read<uint16_t>(data,16+12*g+8);
        if(count%3||cursor+count>indices){out.clear();return false;}
        for(unsigned j=0;j<count;++j){
            unsigned index=base+Read<uint16_t>(data,ib+2*(cursor+j));
            if(index>=part.VertexCount){out.clear();return false;}
            Vertex v={};size_t offset=vb+size_t(part.VertexStart+index)*stride;
            std::memcpy(v.P,static_cast<const unsigned char*>(data)+offset,12);
            if(fvf&0x10)std::memcpy(v.N,static_cast<const unsigned char*>(data)+offset+12,12);
            for(float p:v.P)if(!std::isfinite(p)){out.clear();return false;}
            for(float n:v.N)if(!std::isfinite(n)){out.clear();return false;}
            out.push_back(v);
        }
        cursor+=count;
    }
    // Missing normals are uncommon, but triangle geometry still provides a usable silhouette.
    if(!(fvf&0x10))for(size_t i=0;i<out.size();i+=3){
        float a[3],b[3];for(int k=0;k<3;++k){a[k]=out[i+1].P[k]-out[i].P[k];b[k]=out[i+2].P[k]-out[i].P[k];}
        float n[]={a[1]*b[2]-a[2]*b[1],a[2]*b[0]-a[0]*b[2],a[0]*b[1]-a[1]*b[0]};
        float length=std::sqrt(n[0]*n[0]+n[1]*n[1]+n[2]*n[2]);
        for(int j=0;j<3;++j)for(int k=0;k<3;++k)out[i+j].N[k]=length>1e-8f?n[k]/length:0;
    }
    return !out.empty();
}
}
