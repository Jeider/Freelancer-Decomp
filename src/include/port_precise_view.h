// Freelancer Decomp: a reimplementation of the Freelancer (2003) game client and engine,
// faithful to the behaviour of the original game.
// This file was reconstructed by reverse engineering the binaries of Freelancer 1.1,
// developed by Digital Anvil.
// Author: Giperion.

#pragma once

// Port-only (FREELANCER_PRECISE_RENDER, docs/precise_render.md): camera-relative modelview.
//
// Every renderer (RendComp, alchemy, flmaterials, the client's own draws) builds an object's
// modelview as I3DMathEngine::MulTransform(View, World). Far from the system centre both
// translations are huge floats (View's is -R^T * CameraPos) and their sum, the small distance
// from the camera, keeps only the rounding noise of the two: objects shake by decimetres a
// million metres out. A camera registers its view here whenever it rebuilds it; x86math's
// MulTransform recognises that view (bit for bit, copies too) as the left operand and returns
// R * (WorldPos - CameraPos) instead, whose subtraction of two nearby floats is exact.
//
// x86math.dll exports the function; the client finds it with GetProcAddress, so an x86math
// built without the flag simply leaves the retail product in place.

// Owner: the camera object (one slot each); View12: its packed view transform (3x3 rows, then
// the translation); CameraPos: its world position. Owner nullptr clears every slot.
typedef void(__cdecl* PortRegisterViewFn)(void const* Owner, float const* View12, float const* CameraPos);

#define PORT_REGISTER_VIEW_EXPORT "PortRegisterView"
