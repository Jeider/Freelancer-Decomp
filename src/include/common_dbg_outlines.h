// Freelancer Decomp: a reimplementation of the Freelancer (2003) game client and engine,
// faithful to the behaviour of the original game.
// This file was reconstructed by reverse engineering the binaries of Freelancer 1.1,
// developed by Digital Anvil.
// Author: Giperion.

#pragma once

// Port-only (FREELANCER_DBG_OPTIONS, docs/dbg_options.md): the collision geometry the 2002 beta's
// [OUTLINES] debug options drew (beta freelancer.exe FUN_005167a0 / FUN_00516420 / FUN_005162c0).
// Retail stripped the drawing with the options menu; the geometry is read here from the IVP
// bodies the beta read too (CObject +0x54 body, +0x5c surface manager).

#include "common_exports.h"

struct CObject;

// One world-space segment.
typedef void(__cdecl* FDbgOutlineLineFn)(void* Context, float const* A, float const* B);

// One world-space sphere (centre, radius).
typedef void(__cdecl* FDbgOutlineSphereFn)(void* Context, float const* Centre, float Radius);

// The object's collision hull: every edge of every convex ledge of a polygon surface, once, in
// world space. A body without a polygon surface (an IVP ball) reports its sphere instead. Returns
// false when the object has no physics body.
COMMON_API bool __cdecl DbgOutlineCollisionHull(CObject const* Object, FDbgOutlineLineFn Line,
                                                FDbgOutlineSphereFn Sphere, void* Context);

// The object's physical sphere (get_physical_radius_r). Returns false without a body.
COMMON_API bool __cdecl DbgOutlinePhysicalSphere(CObject const* Object, FDbgOutlineSphereFn Sphere,
                                                 void* Context);

// The phantoms attached to the object (CObject +0x78): a box or part phantom's hull, a sphere
// phantom's sphere. Returns the number of phantoms reported.
COMMON_API bool __cdecl DbgOutlineBodyTransform(CObject const* Object, float* OutRows9, float* OutOrigin3);

COMMON_API int __cdecl DbgOutlinePhantoms(CObject const* Object, FDbgOutlineLineFn Line,
                                          FDbgOutlineSphereFn Sphere, void* Context);
