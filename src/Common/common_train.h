#pragma once
#include "common_exports.h"
struct CObject;
struct EngineObject;
struct Vector;
namespace PhySys {struct CreateParms;}
namespace CmnTrain {
// Separate yard vehicles: a locomotive and a train of unpowered wagons.
COMMON_API bool IsLocomotive(CObject const* object);
COMMON_API bool IsTrailer(CObject const* object);
COMMON_API bool IsDriven(CObject const* object);
COMMON_API CObject* Trailer(CObject const* locomotive);
// 1 ready, -1 unsupported, -2 already coupled, -3 different physics world,
// -4 too far, -5 relative speed, -7 scripted/cruise travel. Capture aligns the
// locomotive automatically; -6 (manual alignment) is no longer returned.
COMMON_API int CanCouple(CObject* locomotive, CObject* trailer, float* distance = nullptr);
COMMON_API int Couple(CObject* locomotive, CObject* trailer);
COMMON_API int BeginCouple(CObject* locomotive, CObject* trailer);
COMMON_API bool IsCoupling(CObject const* locomotive);
COMMON_API bool CancelCoupling(CObject* locomotive);
COMMON_API bool Uncouple(CObject* locomotive);
// Delivered consists remain solid parked world objects but can no longer be
// acquired. Applies to both SP physics copies by the shared object ID.
COMMON_API void SetCouplable(unsigned objectId, bool enabled);
// Restore a previously coupled cargo group after an inter-system transfer.
// Only the server's managed courier bridge may request this placement.
COMMON_API bool RestoreCoupling(CObject* locomotive, CObject* trailer);
COMMON_API void Sync(CObject* object);
bool Bounds(CObject const* object, float& radius, Vector& center);
float SteeringRadius(CObject const* object, float fallback);
bool IsWagon(CObject const* object);
void ChildParms(CObject* object, PhySys::CreateParms& parms);
void Build(CObject* root);
void Forget(CObject* object);
void InheritVelocity(CObject* root);
bool IsMember(CObject const* object);
bool IsHead(CObject const* object);
bool KeepPose(EngineObject const* object);
void Prepare(CObject* object);
CObject* AttachmentOwner(CObject* requestedParent, CObject* child);
}
