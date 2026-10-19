// Freelancer Decomp: a reimplementation of the Freelancer (2003) game client and engine,
// faithful to the behaviour of the original game.
// This file was reconstructed by reverse engineering the binaries of Freelancer 1.1,
// developed by Digital Anvil.
// Author: Giperion.

// Port-only (FREELANCER_DBG_OPTIONS): the collision geometry behind the beta's [OUTLINES] debug
// options. See common_dbg_outlines.h and docs/dbg_options.md.

#ifdef FREELANCER_DBG_OPTIONS

#include "common_dbg_outlines.h"
#include "common_cobject.h"
#include "common_ivp_real_object.h"
#include "../IVP/ivp_utility/ivp_math.h"
#include "../IVP/ivp_physics/ivp_surman_polygon.h"
#include "../IVP/ivp_collision/ivp_compact_surface.h"
#include "../IVP/ivp_compact_builder/ivp_compact_ledge.h"

#include <list>

namespace
{
    // The handle PhySys hands out for a phantom (PhySys::Phantom, common_phantom.cpp): the
    // listener vptr, then the body at +0x04 and the surface manager at +0x0c.
    struct FDbgPhantomView
    {
        void* Vtable;                                // +0x00
        IVP_Real_Object* Body;                       // +0x04
        void* Surface;                               // +0x08
        IVP_SurfaceManager_Polygon* SurfaceManager;  // +0x0c
    };

    void ToWorld(IVP_U_Matrix const& World, IVP_U_Float_Point const& Local, float* Out)
    {
        IVP_U_Point In;
        In.k[0] = Local.X;
        In.k[1] = Local.Y;
        In.k[2] = Local.Z;
        IVP_U_Point Result;
        World.vmult4(&In, &Result);
        Out[0] = Result.k[0];
        Out[1] = Result.k[1];
        Out[2] = Result.k[2];
    }

    void EmitLedge(IVP_Compact_Ledge const* Ledge, IVP_U_Matrix const& World, FDbgOutlineLineFn Line,
                   void* Context)
    {
        IVP_U_Float_Point const* const Points = Ledge->GetPointArray();
        IVP_Compact_Triangle const* Triangle = Ledge->GetFirstTriangle();
        int const Count = Ledge->GetNTriangles();
        for (int Index = 0; Index < Count; ++Index, ++Triangle)
        {
            for (int EdgeIndex = 0; EdgeIndex < 3; ++EdgeIndex)
            {
                IVP_Compact_Edge const* const Edge = Triangle->GetEdge(EdgeIndex);
                unsigned const From = Edge->GetStartPointIndex();
                unsigned const To = Edge->GetNextEdge()->GetStartPointIndex();
                // Each edge is shared by two triangles with opposite directions: keep one.
                if (From >= To)
                    continue;
                float A[3];
                float B[3];
                ToWorld(World, Points[From], A);
                ToWorld(World, Points[To], B);
                Line(Context, A, B);
            }
        }
    }

    void EmitLedgeTree(IVP_Compact_Ledgetree_Node const* Node, IVP_U_Matrix const& World,
                       FDbgOutlineLineFn Line, void* Context)
    {
        // The same walk as IVP_Compact_Ledge_Solver::get_all_ledges: left subtrees recursively,
        // right subtrees iteratively, down to the terminal ledges.
        while (Node->offset_right_node != 0)
        {
            EmitLedgeTree(Node->left_son(), World, Line, Context);
            Node = Node->right_son();
        }
        IVP_Compact_Ledge const* const Ledge = Node->get_compact_ledge();
        if (Ledge != nullptr)
            EmitLedge(Ledge, World, Line, Context);
    }

    // A body's surface: a polygon surface's ledges, otherwise its bounding sphere.
    bool EmitBody(IVP_Real_Object* Body, IVP_SurfaceManager* Manager, FDbgOutlineLineFn Line,
                  FDbgOutlineSphereFn Sphere, void* Context)
    {
        if (Body == nullptr)
            return false;
        IVP_U_Matrix World;
        Body->get_m_world_f_object_AT(&World);
        if (Manager == nullptr)
            Manager = Body->surface_manager;
        if (Manager != nullptr && Manager->get_type() == 0)
        {
            IVP_Compact_Surface const* const Surface =
                static_cast<IVP_SurfaceManager_Polygon*>(Manager)->compact_surface;
            if (Surface != nullptr)
            {
                EmitLedgeTree(Surface->get_compact_ledge_tree_root(), World, Line, Context);
                return true;
            }
        }
        if (Sphere != nullptr)
        {
            float const Centre[3] = {World.vv.k[0], World.vv.k[1], World.vv.k[2]};
            Sphere(Context, Centre, Body->get_upper_limit_radius());
        }
        return true;
    }
}

bool __cdecl DbgOutlineCollisionHull(CObject const* Object, FDbgOutlineLineFn Line,
                                     FDbgOutlineSphereFn Sphere, void* Context)
{
    if (Object == nullptr)
        return false;
    return EmitBody(Object->BodyPtr, Object->SurfaceManager, Line, Sphere, Context);
}

bool __cdecl DbgOutlinePhysicalSphere(CObject const* Object, FDbgOutlineSphereFn Sphere, void* Context)
{
    if (Object == nullptr || Object->BodyPtr == nullptr)
        return false;
    Vector Centre;
    float const Radius = Object->get_physical_radius_r(Centre);
    float const At[3] = {Centre.x, Centre.y, Centre.z};
    Sphere(Context, At, Radius);
    return true;
}

bool __cdecl DbgOutlineBodyTransform(CObject const* Object, float* OutRows9, float* OutOrigin3)
{
    if (Object == nullptr || Object->BodyPtr == nullptr)
        return false;
    IVP_U_Matrix World;
    Object->BodyPtr->get_m_world_f_object_AT(&World);
    for (int Row = 0; Row < 3; ++Row)
        for (int Col = 0; Col < 3; ++Col)
            OutRows9[Row * 3 + Col] = World.rows[Row].k[Col];
    OutOrigin3[0] = World.vv.k[0];
    OutOrigin3[1] = World.vv.k[1];
    OutOrigin3[2] = World.vv.k[2];
    return true;
}

int __cdecl DbgOutlinePhantoms(CObject const* Object, FDbgOutlineLineFn Line,
                               FDbgOutlineSphereFn Sphere, void* Context)
{
    if (Object == nullptr)
        return 0;
    int Count = 0;
    for (std::list<void*>::const_iterator It = Object->Phantoms.begin(); It != Object->Phantoms.end(); ++It)
    {
        FDbgPhantomView const* const Phantom = static_cast<FDbgPhantomView const*>(*It);
        if (Phantom != nullptr &&
            EmitBody(Phantom->Body, Phantom->SurfaceManager, Line, Sphere, Context))
            ++Count;
    }
    return Count;
}

#endif
