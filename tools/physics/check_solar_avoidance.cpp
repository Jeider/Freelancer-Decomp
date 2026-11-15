#define NOMINMAX
#include "common_phyarch.h"
#include "dalib_core.h"
#include "readfile.h"
#include "../../src/Common/solar_avoidance_geometry.h"
#include <cassert>
#include <cstdio>
#include <chrono>
namespace DALib { DALIB_API extern ICOManager* Dacom; DALIB_API extern IFileSystem* Data; }
using namespace SolarAvoidanceGeometry;
static bool run(IVP_Compact_Surface const* s,V a,V b,double radius,bool attached=true) {
    Query q{a,b,radius};
    walk(s->get_compact_ledge_tree_root(),q,[&](unsigned){return attached;});
    assert(!q.exhausted);
    return q.hit;
}
int main(int argc,char** argv) {
    setvbuf(stdout,nullptr,_IONBF,0);
    assert(argc>=3);
    SetErrorMode(SEM_FAILCRITICALERRORS|SEM_NOGPFAULTERRORBOX);
    assert(LoadLibraryA("ReadFile.dll"));
    DALib::Dacom=DACOM_Acquire();DALib::OpenData(".");
    // Segment interiors, edges, grazing distances, reverse travel and stationary probes.
    V a{-100,-100,0},b{100,-100,0},c{0,100,0};
    assert(segmentTriangle({0,0,-100},{0,0,100},a,b,c).squared<1e-12);
    assert(segmentTriangle({0,0,100},{0,0,-100},a,b,c).squared<1e-12);
    assert(std::abs(segmentTriangle({0,0,40},{0,0,40},a,b,c).squared-1600)<1e-9);
    assert(segmentTriangle({500,500,-100},{500,500,100},a,b,c).squared>10000);
    for(int arg=1;arg<argc;++arg) {
        printf("Loading %s\n",argv[arg]);
        std::map<unsigned,PhyArch::Part> parts;
        assert(PhyArch::LoadSurfaces(argv[arg],parts));
        auto root=parts.find(0x12688f2d);
        if(root==parts.end()) root=parts.find(0);
        assert(root!=parts.end());
        auto* s=root->second.Surface;
        if(arg==1) {
            assert(!run(s,{0,0,-1000},{0,0,1000},30)); // through the ring hole
            assert(!run(s,{0,0,0},{0,0,0},30)); // inside its broadphase wrap
            assert(run(s,{300,0,-1000},{300,0,1000},30)); // actual wall
            assert(run(s,{190,0,-1000},{190,0,1000},30)); // swept hull grazes rim
            assert(!run(s,{160,0,-1000},{160,0,1000},30));
            assert(!run(s,{300,0,-1000},{300,0,1000},30,false)); // detached geometry
            puts("PASS: hollow ring, wall, clearance, wrapper and detached leaves");
        } else {
            unsigned clear=0,blocked=0;
            auto begin=std::chrono::steady_clock::now();
            for(int i=0;i<1000;++i) {
                double x=(i%10-5)*120.,y=((i/10)%10-5)*120.;
                if(run(s,{x,y,0},{x,y,200},35))++blocked;else++clear;
            }
            auto elapsed=std::chrono::duration<double,std::milli>(std::chrono::steady_clock::now()-begin).count();
            assert(clear>0); // interior is not entirely replaced by a solid outer capsule
            printf("PASS %s: interior clear=%u blocked=%u; 1000 queries %.2f ms\n",argv[arg],clear,blocked,elapsed);
            // Pick a real leaf and sweep through one nondegenerate face.
            auto* n=s->get_compact_ledge_tree_root();while(n->offset_right_node)n=n->left_son();
            auto* h=n->get_compact_ledge();auto* f=h->GetFirstTriangle();
            V p[3];for(int k=0;k<3;++k)p[k]=point(h->GetPoint(&f->CEdge[k])->AsArray());
            V center=mul(add(add(p[0],p[1]),p[2]),1./3),normal=cross(sub(p[1],p[0]),sub(p[2],p[0]));
            normal=mul(normal,100/std::sqrt(dot(normal,normal)));
            assert(run(s,sub(center,normal),add(center,normal),5));
        }
    }
    DALib::CloseData();
}
