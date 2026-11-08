"""Compile production marker geometry and clipping/batching code; optionally preview.

python tools/targeting_hud/check_marker_geometry.py --preview-atlas PATH/TO/ButtonTextures.txm
The preview uses the installed atlas only as a reference; nothing is installed.
"""
import argparse
import json
import os
from pathlib import Path
import subprocess
import sys

ROOT = Path(__file__).resolve().parents[2]
CLIENT = ROOT / 'src/freelancer/Client'
OUT = ROOT / 'src/obj/hud_geometry'


def function(source, signature):
    start = source.index(signature)
    end = source.index('{', start) + 1
    depth = 1
    while depth:
        depth += (source[end] == '{') - (source[end] == '}')
        end += 1
    return source[start:end]


STUB = r'''
#include "hud_marker_geometry.h"
#include <cassert>
#include <cstdio>
#include <cstring>
#include <vector>
struct FScreenQuadColorVertex { float X,Y; unsigned Color; };
struct FScreenQuadGpuVert { float X,Y,Z,Rhw; unsigned Color,Specular; float U,V; };
struct FScreenQuadRecord {
    float X0,Y0,X1,Y1,DepthA,DepthB,U0,V0,U1,V1;unsigned ColorBits;
};
struct FScreenQuadBatchNode {
    int RotVertCount=0,RecordCount=0,RotVertCapacity=0;
    FScreenQuadGpuVert* RotatedVerts=nullptr;
    FScreenQuadRecord* Records=nullptr;
    void* TextureHandle=nullptr;int BlendMode=2;
    ~FScreenQuadBatchNode(){operator delete(RotatedVerts);}
};
struct FScreenQuadBatchContainer {FScreenQuadBatchNode* Current=nullptr;} testContainer;
std::vector<FScreenQuadBatchNode*> nodes;
unsigned long G_ScreenQuadDefaultFrame[5]={};
FScreenQuadBatchContainer* EnsureBatchContainer(){return &testContainer;}
FScreenQuadBatchNode* ContainerBeginBatch(FScreenQuadBatchContainer* c,
    unsigned long const*,int,bool) {
    c->Current=new FScreenQuadBatchNode; nodes.push_back(c->Current); return c->Current;
}
void reset(){for(auto* n:nodes)delete n;nodes.clear();testContainer.Current=nullptr;
    ContainerBeginBatch(&testContainer,G_ScreenQuadDefaultFrame,2,false);}
'''

GPU = r'''
constexpr unsigned kScreenQuadFvf=0x1c4;
constexpr int D3DRS_SRCBLEND=19,D3DRS_DESTBLEND=20,D3DRS_ALPHABLENDENABLE=27;
struct IRenderPipeline {
    void* texture=nullptr;int colorOp=4,alphaOp=4;
    void SetTextureStageTexture(int,void* t){texture=t;}
    void SetRenderState(int,int){}
    void SetTextureStageState(int,int type,int value){
        if(type==1)colorOp=value;if(type==4)alphaOp=value;
    }
} gpuPipe;
struct FVertexMemoryLock {struct {int BaseVertex=0;} Listing;void* Vertices=nullptr;};
struct IVertexBufferManager {
    std::vector<FScreenQuadGpuVert> data;
    int LockVertexMemory(unsigned fvf,unsigned count,FVertexMemoryLock* lock){
        assert(fvf==kScreenQuadFvf);data.resize(count);lock->Vertices=data.data();return 0;
    }
    void UnlockVertexMemory(FVertexMemoryLock*){}
} gpuVbm;
struct IRPIndexBuffer {
    std::vector<unsigned short> data;unsigned rejected=0;
    int LockIb(void*,unsigned* offset,void** out,unsigned count){
        if(count>0x4000){++rejected;return -1;}
        data.resize(count);*offset=0;*out=data.data();return 0;
    }
    void UnlockIb(void*){}
    int SelectIb(void*,unsigned,unsigned,unsigned){return 0;}
} gpuIb;
struct IRPDraw {
    unsigned draws=0,vertices=0;
    void DrawIndexedPrimitive(int type,unsigned,unsigned count,unsigned,unsigned indices){
        assert(type==4 && indices<=0x4000 && indices==gpuIb.data.size());
        for(auto i:gpuIb.data)assert(i<count);
        assert(gpuPipe.colorOp==(gpuPipe.texture?4:3));
        assert(gpuPipe.alphaOp==(gpuPipe.texture?4:3));
        ++draws;vertices+=count;
    }
} gpuDraw;
'''

CHECKS = r'''
using namespace HudMarkerGeometry;
using Quad=std::vector<Vertex>;
std::vector<Quad> geometry(Shape const& shape,float half,int mode=0,float angle=0) {
    std::vector<Quad> result;
    Draw(shape,128,128,half,half,mode,angle,0xc0ffffff,
        [&](Vertex a,Vertex b,Vertex c,Vertex d){result.push_back({a,b,c,d});});
    return result;
}
bool close(float a,float b){return std::fabs(a-b)<0.003f;}
bool covered(Mesh const& mesh,float x,float y){
    for(int i=0;i<mesh.triangleCount;++i){
        auto const& f=mesh.triangles[i];
        float side[3];
        for(int k=0;k<3;++k){auto a=mesh.vertices[f[k]],b=mesh.vertices[f[(k+1)%3]];
            side[k]=(b.x-a.x)*(y-a.y)-(b.y-a.y)*(x-a.x);}
        if((side[0]>=0&&side[1]>=0&&side[2]>=0)||(side[0]<=0&&side[1]<=0&&side[2]<=0))return true;
    }
    return false;
}
int main() {
    Integration::check();
    assert(ForSize(Shapes[12],.05f).mesh==&SmallPlayerDetailMesh);
    assert(ForSize(Shapes[12],.1f).mesh==&PlayerDetailMesh);
    assert(ForSize(Shapes[14],.05f).mesh==&SmallPlayerMesh);
    // Source meshes retain their expected topology.
    assert(Shapes[3].mesh->vertexCount>0);
    assert(Shapes[14].mesh->vertexCount==8);
    // The selected arrow's two outside flanks must meet on the tile diagonal,
    // the same centreline used by the 3D health/shield bars. These are endpoints
    // of the two longest exterior hull edges, not the inset/detail edges.
    auto const& p=TargetDetailVertices;
    float ux=p[29].x-p[31].x,uy=p[29].y-p[31].y;
    float vx=p[5].x-p[2].x,vy=p[5].y-p[2].y;
    float dx=p[2].x-p[31].x,dy=p[2].y-p[31].y;
    float t=(dx*vy-dy*vx)/(ux*vy-uy*vx);
    float tipX=p[31].x+t*ux,tipY=p[31].y+t*uy;
    assert(std::fabs(tipX-tipY)<.01f);
    float ul=std::hypot(ux,uy),vl=std::hypot(vx,vy);
    assert(std::fabs(ux/ul+vx/vl-uy/ul-vy/vl)<.0001f);
    // Foreground arrow meshes must leave substantial space for the dark
    // background/interior. This failed when foreground reused the solid mesh.
    int pairs[][2]={{2,5},{1,8},{13,10},{14,12}};
    for(auto const& pair:pairs){
        assert(Shapes[pair[0]].mesh!=Shapes[pair[1]].mesh);
        unsigned back=0,open=0;
        for(float y=.3f;y<256;y+=2)for(float x=.3f;x<256;x+=2)
            if(covered(*Shapes[pair[0]].mesh,x,y)){
                ++back;if(!covered(*Shapes[pair[1]].mesh,x,y))++open;
            }
        assert(back>0 && open>back/10);
    }
    // Native triangles retain their alpha; only core and edge AA are emitted.
    for(auto const& shape:Shapes) {
        Mesh const& mesh=*shape.mesh;
        assert(mesh.vertexCount<=MaxMeshVertices);
        int native=0,opaque=0;
        for(int i=0;i<mesh.triangleCount;++i){
            auto const& f=mesh.triangles[i];
            for(int j=0;j<3;++j)assert(f[j]<mesh.vertexCount);
            ++native;
        }
        auto drawn=geometry(shape,124);
        for(auto const& q:drawn)
            if((q[0].color>>24)==192 && (q[1].color>>24)==192 && (q[2].color>>24)==192)++opaque;
        assert(native>0 && opaque>=native);
        for(size_t i=drawn.size()-native;i<drawn.size();++i)
            for(auto const& v:drawn[i])assert((v.color>>24)==192);
        assert(drawn.size()==static_cast<size_t>(mesh.edgeCount+mesh.triangleCount));
        for(int i=0;i<mesh.edgeCount;++i){
            assert((drawn[i][0].color>>24)==192 && (drawn[i][1].color>>24)==192);
            assert((drawn[i][2].color>>24)==0 && (drawn[i][3].color>>24)==0);
        }
    }
    // Mirror modes and UI rotation must preserve the original anchor/direction.
    // Include representative 1080p/1440p/2160p sizes plus tiny subpixel strokes.
    for(float half:{4.0f,18.0f,24.0f,36.0f,124.0f}) for(auto const& shape:Shapes) {
        auto original=geometry(shape,half);
        assert(!original.empty());
        for(int mode=0;mode<4;++mode) {
            auto mirror=geometry(shape,half,mode);
            assert(mirror.size()==original.size());
            for(size_t i=0;i<original.size();++i)for(size_t j=0;j<4;++j){
                auto a=original[i][j],b=mirror[i][j];
                assert(std::isfinite(b.x)&&std::isfinite(b.y));
                assert((b.color>>24)<=192);
                assert(close(b.x,(mode&1)?256-a.x:a.x));
                assert(close(b.y,(mode&2)?256-a.y:a.y));
            }
            double ax=0,ay=0,bx=0,by=0;
            for(size_t i=0;i<original.size();++i)for(size_t j=0;j<4;++j){
                ax+=original[i][j].x-128;ay+=original[i][j].y-128;
                bx+=mirror[i][j].x-128;by+=mirror[i][j].y-128;
            }
            assert(std::fabs(ax-((mode&1)?-bx:bx))<0.1f);
            assert(std::fabs(ay-((mode&2)?-by:by))<0.1f);
        }
        auto rotated=geometry(shape,half,0,3.14159265358979323846f/2);
        assert(rotated.size()==original.size());
        for(size_t i=0;i<original.size();++i)for(size_t j=0;j<4;++j){
            assert(close(rotated[i][j].x,original[i][j].y));
            assert(close(rotated[i][j].y,256-original[i][j].x));
        }
    }
    // Clip a gradient through the left edge: halfway alpha, depth/RHW retained.
    reset();int rect[]={0,0,100,100};
    FScreenQuadColorVertex q[]={{-10,10,0x00ffffff},{10,10,0xc0ffffff},
                              {10,30,0xc0ffffff},{-10,30,0x00ffffff}};
    ScreenQuadEnqueueColorQuad(q,.3f,.8f,rect);
    assert(testContainer.Current->RotVertCount==4);
    for(int i=0;i<4;++i){auto const& v=testContainer.Current->RotatedVerts[i];
        assert(v.X>=0 && v.X<=10 && v.Y>=10 && v.Y<=30);
        assert(v.Z==.3f && v.Rhw==.8f);
        assert((v.Color>>24)==(v.X==0?96u:192u));
    }
    // Every marker remains clipped at all four edges, even after arbitrary rotation.
    reset();
    for(auto const& shape:Shapes)for(float angle:{0.0f,.7f,2.1f})
        Draw(shape,5,95,36,36,0,angle,0xc0ffffff,[&](Vertex a,Vertex b,Vertex c,Vertex d){
            FScreenQuadColorVertex v[]={{a.x,a.y,a.color},{b.x,b.y,b.color},
                                       {c.x,c.y,c.color},{d.x,d.y,d.color}};
            ScreenQuadEnqueueColorQuad(v,.3f,.8f,rect);
        });
    for(auto* node:nodes)for(int i=0;i<node->RotVertCount;++i){auto v=node->RotatedVerts[i];
        assert(v.X>=-.0001f && v.X<=100.0001f && v.Y>=-.0001f && v.Y<=100.0001f);
    }
    // Hidden geometry emits nothing; the real RP8/RP9 scratch buffer allows
    // only 16384 indices. Staying within 16-bit vertex indices alone is not enough.
    reset();int away[]={200,200,300,300};
    ScreenQuadEnqueueColorQuad(q,.3f,.8f,away);assert(testContainer.Current->RotVertCount==0);
    for(int i=0;i<16000;++i)ScreenQuadEnqueueColorQuad(q,.3f,.8f,rect);
    assert(nodes.size()==6);
    unsigned total=0;for(auto* n:nodes){assert(n->RotVertCount/4*6<=0x4000);total+=n->RotVertCount;}
    assert(total==64000);
    // Execute the production upload/flush against the actual scratch-IB limit,
    // not just the CPU geometry path. The previous 60000-vertex nodes were dropped.
    for(auto* n:nodes)FlushOneBatch(n,&gpuPipe,&gpuVbm,&gpuIb,&gpuDraw);
    assert(gpuIb.rejected==0 && gpuDraw.vertices==64000 && gpuDraw.draws==nodes.size());
    assert(gpuPipe.colorOp==4 && gpuPipe.alphaOp==4);
    // The next textured batch must still modulate its atlas with vertex colour.
    nodes[0]->TextureHandle=reinterpret_cast<void*>(1);
    FlushOneBatch(nodes[0],&gpuPipe,&gpuVbm,&gpuIb,&gpuDraw);
    assert(gpuIb.rejected==0 && gpuPipe.colorOp==4 && gpuPipe.alphaOp==4);
    // Negative control: reproduce the old failure on an oversized real upload.
    FScreenQuadBatchNode oversized;oversized.RotVertCount=12000;
    oversized.RotatedVerts=static_cast<FScreenQuadGpuVert*>(operator new(sizeof(FScreenQuadGpuVert)*12000));
    memset(oversized.RotatedVerts,0,sizeof(FScreenQuadGpuVert)*12000);
    unsigned before=gpuDraw.draws;
    FlushOneBatch(&oversized,&gpuPipe,&gpuVbm,&gpuIb,&gpuDraw);
    assert(gpuIb.rejected==1 && gpuDraw.draws==before);
    // Degenerate extents/hidden geometry must not divide by zero or emit geometry.
    int hidden=0;
    auto countHidden=[&](Vertex,Vertex,Vertex,Vertex){++hidden;};
    Draw(Shapes[0],0,0,0,10,0,0,0xffffffff,countHidden);
    Draw(Shapes[0],0,0,10,10,0,0,0x00ffffff,countHidden);
    assert(hidden==0);
    // Capture the production geometry for a visual comparison, not a second implementation.
    FILE* file=nullptr;fopen_s(&file,"marker_quads.txt","w");assert(file);
    for(size_t i=0;i<sizeof(Shapes)/sizeof(Shapes[0]);++i)
        for(auto const& quad:geometry(Shapes[i],124)) {
            std::fprintf(file,"%zu",i);
            for(auto v:quad)std::fprintf(file," %.6f %.6f %u",v.x,v.y,v.color);
            std::fprintf(file,"\n");
        }
    std::fclose(file);
    for(auto* n:nodes)delete n;
    std::puts("PASS: 16 silhouettes, cores without halos, scaling/mirrors/rotation, AA clipping, batch splitting");
}
'''

INTEGRATION = r'''
namespace Integration {
struct FScreenQuadColorVertex {float X,Y;unsigned Color;};
struct ICamera {int viewport[4]={0,0,1920,1080};
    float GetZNear(){return .1f;}int const* GetViewport(){return viewport;}} camera;
ICamera* Win3DGetCamera(){return &camera;}ICamera* AsCamera(ICamera* c){return c;}
struct TextureLib {int reads=0;void GetTextureFrame(int,int,unsigned long* frame){
    ++reads;for(int i=0;i<5;++i)frame[i]=0;frame[0]=99;}} textureLib;
namespace DALib {TextureLib* TextureLib=&textureLib;}
struct Shape {int Texture=1;};
struct FButtonMontageTile {std::string Name;float U=0,V=0,Step=.25f;Shape* Shape=nullptr;};
unsigned long G_ButtonsMaterialKey=7,material=0;
int frameCalls=0,iconCalls=0,geometryCalls=0;bool visible=true;
void ScreenQuadSetMaterialKey(unsigned long key){material=key;}
void ScreenQuadBeginBatchFrame(unsigned long const* frame,int blend,bool){
    assert(blend==2);++frameCalls;(void)frame;}
void ScreenQuadEnqueueIcon(ICamera*,float const*,unsigned long,float,float,int){++iconCalls;}
unsigned char ScreenQuadProjectObjectExtent(ICamera*,float const*,float,float* x,float* y,
    float* w,float* h,float* inv){*x=400;*y=300;*w=124;*h=124;*inv=1;return visible;}
void ScreenQuadEnqueueColorQuad(FScreenQuadColorVertex const* v,float,float,int const*){
    ++geometryCalls;assert((v[0].Color&0xffffff)==0x285078);
}
'''

INTEGRATION_CHECK = r'''
void check(){
    float p[3]={0,0,-1};unsigned char rgba[]={40,80,120,160};
    Shape texture;
    // All names route before Shape lookup, so missing marker textures cannot hide the HUD.
    for(auto const& marker:HudMarkerGeometry::Shapes){
        FButtonMontageTile tile;tile.Name=marker.name;
        assert(NnMontageDrawTileAt(&tile,p,rgba,.1f,0,0));
    }
    assert(geometryCalls>0 && frameCalls==16 && material==G_ButtonsMaterialKey);
    assert(textureLib.reads==0 && iconCalls==0);
    FButtonMontageTile button;button.Name="CurrentTargetTalking";button.Shape=&texture;
    assert(NnMontageDrawTileAt(&button,p,rgba,.1f,1,.5f));
    assert(textureLib.reads==1 && iconCalls==1);
    button.Shape=nullptr;assert(!NnMontageDrawTileAt(&button,p,rgba,.1f,0,0));
    assert(!NnMontageDrawTileAt(nullptr,p,rgba,.1f,0,0));
    button.Name="CurrentTargetCorner";visible=false;
    int previous=frameCalls;
    assert(NnMontageDrawTileAt(&button,p,rgba,.1f,0,0));
    assert(frameCalls==previous);
    visible=true;rgba[3]=0;
    assert(NnMontageDrawTileAt(&button,p,rgba,.1f,0,0));assert(frameCalls==previous);
}
}
'''


def preview(atlas):
    import io
    import numpy as np
    from PIL import Image, ImageDraw
    sys.path.insert(0, str(ROOT / 'tools'))
    from generate_station_lods import read_tree, child
    root = read_tree(atlas.read_bytes())[1][0]
    blob = child(child(child(root, 'Texture library'), 'HUD_targetingelement'), 'MIP0').blob
    # TGA bottom-origin pixels are uploaded in file order by the game's loader.
    reference = Image.open(io.BytesIO(blob)).transpose(Image.Transpose.FLIP_TOP_BOTTOM)
    manifest=json.loads((OUT/'beta_marker_manifest.json').read_text())
    registrations={index:manifest[key]['alignment'] for index,key in
                   ((2,'Target'),(3,'TargetHat'),(4,'Quotes'),(5,'TargetDetail'),(7,'ContactHat'))}
    def registered_tile(index):
        tile=reference.crop((index%4*256,index//4*256,index%4*256+256,index//4*256+256))
        if index in registrations:
            registration=registrations[index]
            offset=np.array(registration['offset'])
            if 'matrix' in registration:
                inverse=np.linalg.inv(registration['matrix'])
            else:
                angle=registration['angle'];c,s=np.cos(angle),np.sin(angle)
                inverse=np.array([[c,s],[-s,c]])
            translation=np.array([128.,128.])-inverse@(np.array([128.,128.])+offset)
            tile=tile.transform((256,256),Image.Transform.AFFINE,
                                tuple(np.column_stack((inverse,translation)).ravel()),
                                resample=Image.Resampling.NEAREST)
        return tile
    def registered_probe(index,x,y):
        registration=registrations[index];angle=registration['angle']
        c,s=np.cos(angle),np.sin(angle)
        result=np.array([[c,-s],[s,c]])@(np.array([x,y])-128)+128+registration['offset']
        return tuple(np.rint(result[::-1]).astype(int))
    quads = [[] for _ in range(16)]
    for line in (OUT / 'marker_quads.txt').read_text().splitlines():
        values = line.split()
        quads[int(values[0])].append([(float(values[i]), float(values[i+1]), int(values[i+2]))
                                    for i in range(1, 13, 3)])
    names = ['Target corner', 'Contact back', 'Target arrow back', 'Target arrow hat',
             'Target quotes', 'Target arrow', 'Target hat', 'Contact hat',
             'Contact arrow', 'Waypoint target', 'Loot arrow', 'Waypoint arrow',
             'Player arrow', 'Loot back', 'Player back', 'Waypoint back']
    sheet = Image.new('RGB', (1024, 1160), (30, 34, 40))
    draw = ImageDraw.Draw(sheet)
    def paint(image, records, rgb=(248,248,248), opacity=1.0):
        for quad in records:
            for ids in ((0, 1, 2), (0, 2, 3)):
                a, b, c = [quad[i] for i in ids]
                area = (b[0]-a[0])*(c[1]-a[1])-(b[1]-a[1])*(c[0]-a[0])
                if abs(area) < 1e-6:
                    continue
                x0, x1 = max(0, int(min(a[0], b[0], c[0]))), min(256, int(max(a[0], b[0], c[0]))+1)
                y0, y1 = max(0, int(min(a[1], b[1], c[1]))), min(256, int(max(a[1], b[1], c[1]))+1)
                if x0>=x1 or y0>=y1:
                    continue
                yy, xx = np.mgrid[y0:y1, x0:x1] + .5
                u = ((b[0]-xx)*(c[1]-yy)-(b[1]-yy)*(c[0]-xx))/area
                v = ((c[0]-xx)*(a[1]-yy)-(c[1]-yy)*(a[0]-xx))/area
                w = 1-u-v
                alpha = np.where((u>=0)&(v>=0)&(w>=0),
                                 (u*(a[2]>>24)+v*(b[2]>>24)+w*(c[2]>>24))/192*opacity, 0)[..., None]
                image[y0:y1, x0:x1] = np.array(rgb)*alpha + image[y0:y1, x0:x1]*(1-alpha)
    # Compare the actual emitted opaque triangles to the release's bright core,
    # independently of the exporter's smoothing/simplification. This catches a
    # wrong silhouette or a filled hole even if geometry/batching checks pass.
    for index in (0,2,3,4,5,7,11):
        mask=np.zeros((256,256,3))
        core=[q for q in quads[index] if all((v[2]>>24)==192 for v in q)]
        paint(mask,core,(1,1,1))
        actual=mask[:,:,0]>.5
        tile=registered_tile(index)
        expected=np.array(tile)[:,:,3]>=240
        overlap=np.count_nonzero(actual&expected)/np.count_nonzero(actual|expected)
        print(f'{names[index]} release core overlap: {overlap:.1%}')
        assert overlap>.85,(names[index],overlap)
        if index==4:assert not actual[registered_probe(index,143,120)], 'Quotes separator filled'
        if index==5:assert not actual[registered_probe(index,140,150)], 'Target arrow inset filled'
    # Each pair is the reference at left, actual emitted geometry at right.
    for index, records in enumerate(quads):
        image = np.full((256, 256, 3), (30., 34., 40.))
        paint(image,records)
        tile = Image.fromarray(np.uint8(np.clip(image, 0, 255)))
        x, y = index%4*256, index//4*290
        old = reference.crop((index%4*256, index//4*256, index%4*256+256, index//4*256+256))
        old = old.resize((128, 128))
        sheet.paste(old, (x, y+36), old)
        sheet.paste(tile.resize((128, 128)), (x+128, y+36))
        # Also show the new contour enlarged to make geometry defects easy to see.
        sheet.paste(tile.resize((112, 112)), (x+72, y+170))
        draw.text((x+5, y+4), names[index], fill='white')
        draw.text((x+5, y+20), 'Atlas                 Geometry', fill='#aab4c4')
    sheet.save(OUT / 'waypoint_marker_details.png')
    # Composite foreground/background pairs in colour so a filled foreground
    # regression is visible without installing the client.
    layers=Image.new('RGB',(1024,288),(30,34,40)); labels=ImageDraw.Draw(layers)
    for column,(name,back,front) in enumerate((('Target',2,5),('Contact',1,8),
                                               ('Loot',13,10),('Player',14,12))):
        pixels=np.full((256,256,3),(30.,34.,40.))
        paint(pixels,quads[back],(0,0,0),.65)
        paint(pixels,quads[front],(65,255,130),.9)
        layers.paste(Image.fromarray(np.uint8(np.clip(pixels,0,255))),(column*256,30))
        labels.text((column*256+12,8),name+' / background + details',fill='white')
    layers.save(OUT/'retail_arrow_layers.png')
    detail=Image.new('RGB',(768,280),(30,34,40));label=ImageDraw.Draw(detail)
    old=reference.crop((256,256,512,512));detail.paste(old,(0,24),old)
    pixels=np.full((256,256,3),(30.,34.,40.));paint(pixels,quads[5])
    detail.paste(Image.fromarray(np.uint8(np.clip(pixels,0,255))),(256,24))
    pixels=np.full((256,256,3),(30.,34.,40.))
    paint(pixels,quads[2],(0,0,0),.65);paint(pixels,quads[5],(65,255,130),.9)
    detail.paste(Image.fromarray(np.uint8(np.clip(pixels,0,255))),(512,24))
    for x,title in ((8,'Release'),(264,'Current geometry'),(520,'Composited marker')):
        label.text((x,6),title,fill='white')
    detail.save(OUT/'target_arrow_release_comparison.png')
    waypoint=Image.new('RGB',(512,280),(30,34,40));label=ImageDraw.Draw(waypoint)
    old=reference.crop((768,512,1024,768));waypoint.paste(old,(0,24),old)
    pixels=np.full((256,256,3),(30.,34.,40.));paint(pixels,quads[11])
    waypoint.paste(Image.fromarray(np.uint8(np.clip(pixels,0,255))),(256,24))
    label.text((8,6),'Release',fill='white');label.text((264,6),'Thinner geometry',fill='white')
    waypoint.save(OUT/'waypoint_arrow_thin.png')
    print(OUT / 'waypoint_marker_details.png')


def main():
    parser = argparse.ArgumentParser()
    parser.add_argument('--preview-atlas', type=Path)
    args = parser.parse_args()
    OUT.mkdir(parents=True, exist_ok=True)
    source = (CLIENT / 'screen_quad_state.cpp').read_text(encoding='utf-8-sig')
    montage = (CLIENT / 'nn_montage_draw.cpp').read_text(encoding='utf-8-sig')
    (OUT / 'check.cpp').write_text('#include <string>\n' + STUB + GPU +
        function(source, 'void WriteRecordVertex(') + function(source, 'void FlushOneBatch(') +
        function(source, 'void ScreenQuadEnqueueColorQuad(') + INTEGRATION +
        function(montage, 'bool NnMontageDrawTileAt(') + INTEGRATION_CHECK + CHECKS)
    vc = Path('C:/Program Files/Microsoft Visual Studio/18/Community/VC/Tools/MSVC/14.51.36231')
    sdk = Path('C:/Program Files (x86)/Windows Kits/10')
    version = '10.0.26100.0'
    env = dict(os.environ)
    env['INCLUDE'] = ';'.join(str(p) for p in [vc/'include', CLIENT] +
                            [sdk/'Include'/version/x for x in ('ucrt', 'shared', 'um')])
    env['LIB'] = ';'.join(str(p) for p in [vc/'lib/x86'] +
                        [sdk/'Lib'/version/x/'x86' for x in ('ucrt', 'um')])
    subprocess.run([str(vc/'bin/Hostx64/x86/cl.exe'), '/nologo', '/std:c++17', '/W4', '/WX',
                    '/EHsc', '/MT', 'check.cpp', '/Fecheck.exe'], cwd=OUT, env=env, check=True)
    subprocess.run([str(OUT/'check.exe')], cwd=OUT, check=True)
    if args.preview_atlas:
        preview(args.preview_atlas)


if __name__ == '__main__':
    main()
