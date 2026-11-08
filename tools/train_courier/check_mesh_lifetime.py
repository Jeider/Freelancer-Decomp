"""Run actual VMesh destruction/hookup/draw code with shared train geometry."""
from pathlib import Path
import argparse
import subprocess
from check_orders import function, compiler_env

ROOT = Path(__file__).resolve().parents[2]
PREFIX = r'''
#include <cassert>
#include <cstdio>
#include <cstdlib>
#include <cstring>
#include <map>
#define DACOM_API
struct FTransform {int unused=0;};
struct FVbListing {}; struct FIbScratch {};
struct FMaterialSubmitContext {void *Inst,*World,*View,*SourceVertices; unsigned short* Indices;
    FVbListing* VbListing; FIbScratch* IbScratch; int Field20; void* ReplacedMaterial;};
struct IMaterial {
    int refs=1,draws=0;
    void AddRef(){++refs;} void Release(){assert(refs>0);--refs;}
    void Bind(void*){} void Teardown(void*){}
    void Submit(void*,unsigned,unsigned,unsigned,unsigned,unsigned,unsigned){++draws;}
};
struct FVmeshDataHeader {unsigned PrimitiveType=4;unsigned short FaceGroups=2;char padding[10]={};};
static_assert(sizeof(FVmeshDataHeader)==16);
struct FVmeshFacegroup {unsigned MaterialCrc=1;unsigned short VertexBegin=0,VertexEnd=2,IndexCount=3,pad=0;};
struct FVmeshRef {unsigned Crc=7,FacegroupStart=0,FacegroupCount=1,VertexStart=0,VertexCount=3,IndexStart=0;};
struct FVmeshGroup {};
struct FVmeshData {unsigned Crc=7;char* Name=nullptr;IMaterial** Materials=nullptr;
    FVmeshDataHeader* Header=nullptr;FVmeshGroup* Group=nullptr;int RefCount=1;float SizeKib=1;};
std::map<unsigned,FVmeshData*> meshes;
void VMeshDataMapErase(FVmeshData* d){meshes.erase(d->Crc);}
void VMeshGroupRemove(FVmeshGroup*,FVmeshData*){assert(false);}
namespace LogStream {void LogEvent(char const*,float,int){}}
struct FVmeshKey {char const* Name;unsigned Crc;};
FVmeshData* VMeshDataFind(FVmeshKey* key){return meshes.at(key->Crc);}
void VMeshBuildVertexDesc(FVmeshDataHeader*,unsigned,unsigned,int*){}
struct Library {bool fail=false;IMaterial* material=nullptr;
    int FindMaterialByCrc(unsigned long*,IMaterial** out){if(fail)return -1;*out=material;material->AddRef();return 0;}
} library;
Library* G_MaterialLibrary=&library;
using IMaterialLibrary=Library;
int kFdumpNotice=0;char const* G_FileVMPartArch="test";
void RendCompFdumpAt(int,char const*,int,char const*){}
struct ICamera {FTransform view;void* GetViewTransform(){return &view;}} camera;
struct Engine {FTransform world;void* GetInstanceTransform(void*){return &world;}} engine;
Engine* G_Engine=&engine;
struct Pipeline {void GetPipelineState(int,int* v){*v=1;}void SetModelview(float const*){}
    void SetWorld(float const*){}void SetView(float const*){}} pipeline;
Pipeline* G_Pipeline=&pipeline;
struct Math {void MulTransform(FTransform&,FTransform const&,FTransform const&){}} math;
int G_MathVMesh=0;Math* MathEngineCached(int&){return &math;}
struct FVMeshPart {
    struct MeshFace {void CloseFaceGroup(){}} Mesh;
    FVmeshData* Data=nullptr;FVmeshRef* Ref=nullptr;int VertexDesc=0;
    ~FVMeshPart();int HookUp();bool Draw(ICamera*,void*,unsigned long,void const*,IMaterial*);
    FVmeshFacegroup const* Facegroups()const{return reinterpret_cast<FVmeshFacegroup const*>(reinterpret_cast<char const*>(Data->Header)+16);}
    bool Prepare(void*,void*){return true;}
};
'''
MAIN = r'''
FVMeshPart* part(unsigned start,unsigned count=1){
    auto* p=new FVMeshPart;
    p->Ref=reinterpret_cast<FVmeshRef*>(new unsigned char[sizeof(FVmeshRef)]);
    *p->Ref=FVmeshRef{};p->Ref->FacegroupStart=start;p->Ref->FacegroupCount=count;
    assert(p->HookUp()==0);return p;
}
int main(int argc,char**){
    const bool expectBug=argc>1;
    for(int cycle=0;cycle<4;++cycle){
        IMaterial material;library.material=&material;
        auto* data=new FVmeshData;
        auto* raw=new unsigned char[16+2*sizeof(FVmeshFacegroup)+12]{};
        data->Header=reinterpret_cast<FVmeshDataHeader*>(raw);*data->Header=FVmeshDataHeader{};
        auto* faces=reinterpret_cast<FVmeshFacegroup*>(raw+16);
        faces[0]=FVmeshFacegroup{};faces[1]=FVmeshFacegroup{};
        data->Materials=new IMaterial*[2]{};meshes[7]=data;
        // Different CMP parts/consist sizes reference overlapping mesh facegroups.
        auto* delivered=part(0,2);auto* active=part(0);auto* other=part(1);
        assert(material.refs==3); // one library reference + one per shared slot
        active->Draw(&camera,nullptr,0,nullptr,nullptr);
        assert(material.draws==1);
        delete delivered;
        active->Draw(&camera,nullptr,0,nullptr,nullptr);
        if(expectBug){assert(material.draws==1 && !data->Materials[0]);}
        else{
            assert(material.draws==2 && data->Materials[0]==&material);
            // Losing a library lookup must retain the valid material already held.
            library.fail=true;assert(active->HookUp()<0);library.fail=false;
            active->Draw(&camera,nullptr,0,nullptr,nullptr);assert(material.draws==3);
            assert(active->HookUp()==0 && material.refs==3);
        }
        delete active;
        int before=material.draws;other->Draw(&camera,nullptr,0,nullptr,nullptr);
        assert(material.draws==before+(expectBug?0:1));
        delete other;
        // The mesh library still owns data; release it last, checking every material ref.
        assert(data->RefCount==1);VMeshDataRelease(data);
        assert(meshes.empty() && material.refs==1);
    }
    // Part outlives the library: its final release must also clean materials.
    IMaterial material;library.material=&material;
    auto* data=new FVmeshData;data->Header=reinterpret_cast<FVmeshDataHeader*>(new unsigned char[16+2*sizeof(FVmeshFacegroup)+12]{});
    *data->Header=FVmeshDataHeader{};
    auto* faces=reinterpret_cast<FVmeshFacegroup*>(reinterpret_cast<char*>(data->Header)+16);
    faces[0]=FVmeshFacegroup{};faces[1]=FVmeshFacegroup{};
    data->Materials=new IMaterial*[2]{};meshes[7]=data;
    auto* active=part(0);VMeshDataRelease(data);delete active;
    assert(material.refs==1 && meshes.empty());
    puts(expectBug?"REPRODUCED: unloading old wagon parts suppresses active wagon draw submissions":
         "PASS: active wagon draws survive old part unload; shared/overlapping materials, repeated hookups and both final-release orders stay balanced");
}
'''

def main():
    parser=argparse.ArgumentParser(description=__doc__)
    parser.add_argument('--expect-bug',action='store_true')
    args=parser.parse_args()
    part=(ROOT/'src/RendComp/VMeshPart.cpp').read_text()
    library=(ROOT/'src/RendComp/VMeshLibrary.cpp').read_text()
    code=PREFIX
    for name in ('static void VMeshDataDestruct(', 'int VMeshDataAddRef(', 'int VMeshDataRelease('):
        code+=function(library,name)+'\n'
    for name in ('FVMeshPart::~FVMeshPart()', 'int FVMeshPart::HookUp(', 'bool DACOM_API FVMeshPart::Draw('):
        code+=function(part,name)+'\n'
    out=ROOT/'src/obj/train_courier/mesh_lifetime';out.mkdir(parents=True,exist_ok=True)
    cpp=out/'check.cpp';cpp.write_text(code+MAIN)
    compiler,env=compiler_env();exe=out/'check.exe'
    subprocess.run([str(compiler/'cl.exe'),'/nologo','/std:c++17','/EHsc','/O2',str(cpp),
                    '/Fo'+str(out/'check.obj'),'/Fe'+str(exe)],cwd=out,env=env,check=True)
    subprocess.run([str(exe)]+(['bug'] if args.expect_bug else []),cwd=out,check=True)

if __name__=='__main__':main()
