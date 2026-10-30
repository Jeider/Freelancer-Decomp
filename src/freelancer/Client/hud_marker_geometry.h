// Release-derived contours and matching Beta HUD meshes, with antialiased edges.
#pragma once
#include <cmath>
#include <cstddef>
namespace HudMarkerGeometry
{
struct Vertex { float x,y; unsigned color; };
struct MeshVertex { float x,y,nx,ny; };
struct Mesh {
    MeshVertex const* vertices; int vertexCount;
    unsigned short const (*triangles)[3]; int triangleCount;
    unsigned short const (*edges)[2]; int edgeCount;
};
struct Shape {
    char const* name; Mesh const* mesh;
    Mesh const* smallMesh=nullptr;
};
#include "hud_marker_beta_data.h"

inline Shape ForSize(Shape shape,float size)
{
    // Offscreen callers use .1 for the selected player, .05 for other players.
    if(shape.smallMesh && size<.075f) shape.mesh=shape.smallMesh;
    return shape;
}

template<class Emit>
void Draw(Shape const& shape,float x,float y,float halfW,float halfH,
          int mode,float angle,unsigned color,Emit emit)
{
    if(halfW<=0 || halfH<=0 || (color>>24)==0) return;
    float c=std::cos(angle),s=std::sin(angle);
    float sx=halfW/124.0f*((mode&1)?-1.0f:1.0f);
    float sy=halfH/124.0f*((mode&2)?-1.0f:1.0f);
    Mesh const& mesh=*shape.mesh;
    Vertex vertices[MaxMeshVertices],fringe[MaxMeshVertices];
    for(int i=0;i<mesh.vertexCount;++i){
        auto const& v=mesh.vertices[i];
        float px=(v.x-128)*sx,py=(v.y-128)*sy;
        vertices[i]={x+c*px+s*py,y-s*px+c*py,color};
        // Normals transform with inverse scale; retain the miter length while
        // keeping the fringe one physical pixel at any output resolution.
        float nx=v.nx/sx,ny=v.ny/sy;
        float length=std::sqrt(nx*nx+ny*ny);
        float miter=std::sqrt(v.nx*v.nx+v.ny*v.ny);
        if(length>0){nx*=miter/length;ny*=miter/length;}
        fringe[i]={vertices[i].x+c*nx+s*ny,vertices[i].y-s*nx+c*ny,color&0xffffffu};
    }
    for(int i=0;i<mesh.edgeCount;++i){
        auto const& e=mesh.edges[i];
        emit(vertices[e[0]],vertices[e[1]],fringe[e[1]],fringe[e[0]]);
    }
    for(int i=0;i<mesh.triangleCount;++i){
        auto const& f=mesh.triangles[i];
        emit(vertices[f[0]],vertices[f[1]],vertices[f[2]],vertices[f[2]]);
    }
}
}
