// Read staged SURs through the actual Common.dll/ReadFile.dll loader and then
// walk them with the engine's IVP accessors (alignment and relative-edge ABI).
#include "common_phyarch.h"
#include "dalib_core.h"
#include "readfile.h"
#include "../../src/IVP/ivp_collision/ivp_compact_surface.h"
#include "../../src/IVP/ivp_compact_builder/ivp_compact_ledge.h"
#include <cstdio>
#include <cstdlib>
#include <set>
#include <cmath>
#include <algorithm>
#include <dbghelp.h>
#pragma comment(lib, "dbghelp.lib")

namespace DALib { DALIB_API extern ICOManager* Dacom; DALIB_API extern IFileSystem* Data; }
static void need(bool ok, const char* what) { if (!ok) { std::fprintf(stderr,"FAIL: %s\n",what); std::exit(1); } }
static const char* beginSurface;
static size_t surfaceSize;
static std::set<const void*> visited;
static size_t hullCount, triangleCount;
static LONG WINAPI fault(EXCEPTION_POINTERS* e) {
    HMODULE module=nullptr; char name[MAX_PATH]={};
    GetModuleHandleExA(GET_MODULE_HANDLE_EX_FLAG_FROM_ADDRESS|GET_MODULE_HANDLE_EX_FLAG_UNCHANGED_REFCOUNT,
                     reinterpret_cast<LPCSTR>(e->ExceptionRecord->ExceptionAddress),&module);
    GetModuleFileNameA(module,name,MAX_PATH);
    std::fprintf(stderr,"Exception %08lx in %s + %zx accessing %p\n",e->ExceptionRecord->ExceptionCode,name,
        reinterpret_cast<uintptr_t>(e->ExceptionRecord->ExceptionAddress)-reinterpret_cast<uintptr_t>(module),
        reinterpret_cast<void*>(e->ExceptionRecord->ExceptionInformation[1]));
    SymInitialize(GetCurrentProcess(),nullptr,TRUE);
    char buffer[sizeof(SYMBOL_INFO)+512]={};
    auto* symbol=reinterpret_cast<SYMBOL_INFO*>(buffer);
    symbol->SizeOfStruct=sizeof(SYMBOL_INFO);symbol->MaxNameLen=511;
    DWORD64 displacement=0;
    if(SymFromAddr(GetCurrentProcess(),reinterpret_cast<DWORD64>(e->ExceptionRecord->ExceptionAddress),&displacement,symbol))
        std::fprintf(stderr,"Symbol: %s + %llu\n",symbol->Name,displacement);
    return EXCEPTION_EXECUTE_HANDLER;
}
static bool inside(const void* p, size_t bytes) {
    auto a = reinterpret_cast<uintptr_t>(p), b = reinterpret_cast<uintptr_t>(beginSurface);
    return a >= b && a-b <= surfaceSize && bytes <= surfaceSize-(a-b);
}
static void walk(const IVP_Compact_Ledgetree_Node* node) {
    need(inside(node,sizeof(*node)) && visited.insert(node).second,"valid acyclic tree");
    need(std::isfinite(node->radius) && node->radius > 0,"node radius");
    if (node->offset_compact_ledge) {
        auto* h = node->get_compact_ledge();
        need(inside(h,16) && (reinterpret_cast<uintptr_t>(h)%16)==0,"aligned hull");
        const int count = h->GetNTriangles();
        need(count >= 4 && count < 4096 && count%2==0 && inside(h,16+count*16),"triangle count");
        std::set<unsigned> points;
        auto* first = h->GetFirstTriangle();
        for(int i=0;i<count;++i) {
            auto* t = first+i;
            need(t->GetCompactLedge()==h,"triangle back-reference");
            need(((t->TriInfo>>12)&4095)<static_cast<unsigned>(count),"opposite face");
            for(int e=0;e<3;++e) {
                auto* edge = &t->CEdge[e];
                auto* opposite = edge->GetOppositeEdge();
                need(reinterpret_cast<const char*>(opposite)>=reinterpret_cast<const char*>(first) &&
                     reinterpret_cast<const char*>(opposite)<reinterpret_cast<const char*>(first+count),"edge reference range");
                need((reinterpret_cast<uintptr_t>(opposite)&15)!=0,"edge points at edge, not header");
                need(opposite->GetOppositeEdge()==edge,"reciprocal opposite edges");
                need(opposite->GetStartPointIndex()==edge->GetNextEdge()->GetStartPointIndex() &&
                     opposite->GetNextEdge()->GetStartPointIndex()==edge->GetStartPointIndex(),"edge endpoints");
                auto* p = h->GetPoint(edge);
                need(inside(p,16) && std::isfinite(p->X) && std::isfinite(p->Y) && std::isfinite(p->Z),"point range");
                points.insert(edge->GetStartPointIndex());
                const float* v = p->AsArray();
                for(int axis=0;axis<3;++axis)
                    need(std::abs(v[axis]-node->center[axis]) <= node->box_sizes[axis]*node->radius*.004f+.001f,"node contains hull");
            }
        }
        need(static_cast<int>(points.size())-count*3/2+count==2,"closed convex topology (Euler)");
        // Verify winding and convexity independently of the Python hull generator.
        for(int i=0;i<count;++i) {
            const float* a = h->GetPoint(&first[i].CEdge[0])->AsArray();
            const float* b = h->GetPoint(&first[i].CEdge[1])->AsArray();
            const float* c = h->GetPoint(&first[i].CEdge[2])->AsArray();
            double u[3],v[3],n[3];
            for(int k=0;k<3;++k) {u[k]=b[k]-a[k];v[k]=c[k]-a[k];}
            for(int k=0;k<3;++k) n[k]=u[(k+1)%3]*v[(k+2)%3]-u[(k+2)%3]*v[(k+1)%3];
            double length=std::sqrt(n[0]*n[0]+n[1]*n[1]+n[2]*n[2]);
            need(length>1e-9,"nondegenerate triangle");
            for(unsigned idx:points) {
                auto* p=h->GetPointArray()+idx;
                double d=0; for(int k=0;k<3;++k)d+=n[k]*(p->AsArray()[k]-a[k]);
                need(d<=length*.002,"outward winding and convexity");
            }
        }
        if(!node->offset_right_node) {++hullCount;triangleCount+=count;}
    }
    if(node->offset_right_node) {walk(node->left_son());walk(node->right_son());}
    else need(node->offset_compact_ledge!=0,"terminal hull exists");
}
int main(int argc,char** argv) {
    setvbuf(stdout,nullptr,_IONBF,0);
    SetUnhandledExceptionFilter(fault);
    std::puts("Initializing SUR loader");
    SetErrorMode(SEM_FAILCRITICALERRORS|SEM_NOGPFAULTERRORBOX);
    need(argc>1,"supply SUR paths");
    need(LoadLibraryA("ReadFile.dll")!=nullptr,"ReadFile.dll");
    DALib::Dacom=DACOM_Acquire();
    std::puts("ReadFile loaded");
    DALib::OpenData(".");
    need(DALib::Data!=nullptr,"DOS filesystem");
    for(int i=1;i<argc;++i) {
        std::map<unsigned,PhyArch::Part> parts;
        std::printf("Loading %s\n",argv[i]);
        need(PhyArch::LoadSurfaces(argv[i],parts) && !parts.empty(),"Common.dll LoadSurfaces");
        std::printf("Loaded %zu parts\n",parts.size());
        for(auto& entry:parts) {
            auto* s=entry.second.Surface;
            need(s!=nullptr,"surface exists");
            beginSurface=reinterpret_cast<const char*>(s);
            surfaceSize=s->max_deviation_and_size>>8;
            need(surfaceSize>=48 && surfaceSize<10000000,"surface size");
            visited.clear();hullCount=triangleCount=0;
            walk(s->get_compact_ledge_tree_root());
            std::printf("PASS %s part=%08x hulls=%zu triangles=%zu nodes=%zu\n",argv[i],entry.first,hullCount,triangleCount,visited.size());
        }
    }
    DALib::CloseData();
    return 0;
}
