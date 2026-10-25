#include "hud_vulnerable.h"

#include "common_archetype.h"
#include "common_cobject.h"
#include "common_cequip.h"
#include "common_iface.h"
#include "common_misc.h"
#include "DALib.h"
#include "dacom_iids.h"
#include "engine/engbase.h"
#include "game_options.h"
#include "globals.h"
#include "hud_command_dispatch.h"
#include "hud_target.h"
#include "hud_targetable_objects.h"
#include "input_manager.h"
#include "menu_sound_arch.h"
#include "menu_ui_init.h"
#include "part_cache.h"
#include "player_behavior.h"
#include "space_camera.h"
#include "space_letterbox.h"
#include "win3d.h"
#include "win3d_render.h"
#include "win3d_immediate.h"
#include "render/IRenderPipeline.h"
#include "render/rendcomp.h"
#include "render/mesh_iface.h"
#include "x86math.h"

#include <cmath>
#include <vector>
#include <utility>
#include <memory>
#include <cstring>

namespace
{
    void* Instance(long id) { return reinterpret_cast<void*>(id); }

    struct Hover
    {
        CEqObj* object = nullptr;
        CArchGroup* group = nullptr;
        CEGun* turret = nullptr;
        long root = -1;
        unsigned short subId = 0;
    };

    struct WirePart
    {
        FPartCacheEntry entry = {};
        std::unique_ptr<FVector[]> viewVertices;
        WirePart() { PartCacheEntryConstruct(&entry); }
        ~WirePart() { PartCacheEntryDestroy(&entry); }
        WirePart(WirePart const&) = delete;
        WirePart& operator=(WirePart const&) = delete;
    };

    struct WireState
    {
        std::vector<std::unique_ptr<WirePart>> wires;
        unsigned objectId = 0;
        long ownerInstance = -1;
        long root = -1;
        unsigned short subId = 0;
        std::vector<std::pair<void*, int>> parts;
        bool capturedLeft = false;
        void ClearWire()
        {
            wires.clear();
            objectId = 0;
            ownerInstance = root = -1;
            subId = 0;
            parts.clear();
        }
    } state;

    bool Available()
    {
        return GetForegroundWindow() == g_client.window &&
            GetGameOption(kGameOptInterfaceGroup) && GetGameOption(kGameOptHud) &&
            !HudIsMousePickBlocked() && !IsLetterboxVisible() &&
            !IsSpaceInitInProgress() && !HudGetInputFocus() &&
            Win3DGetHover() == nullptr && GetPlayerObjRW();
    }

    bool IsTurret(CEGun* gun)
    {
        auto const* arch = gun ? gun->GunArch() : nullptr;
        if (!arch) return false;
        if (arch->bAutoTurret) return true;
        // The accessor's empty-list fallback accepts every weapon class, including
        // turrets. Only explicit hp_gun_type entries identify a manual turret.
        if (!arch->HpGunTypesBegin) return false;
        for (auto* entry = arch->HpGunTypesBegin; entry != arch->HpGunTypesEnd; ++entry)
        {
            auto const type = *entry;
            if (type == HpTypeTurret || (type >= HpTypeTurretSpecial1 && type <= HpTypeTurretSpecial10))
                return true;
        }
        return false;
    }

    Hover Pick(ICamera* camera)
    {
        if (!camera) return {};
        auto* player = static_cast<IObjRW*>(GetPlayerObjRW());
        CShip* playerShip = HudShipOfObjRw(player);
        if (!playerShip) return {};
        int x = 0, y = 0, z = 0;
        GetClientSoftwareCursor(&x, &y, &z);
        FCameraRayHit hit = {};
        // Nearest physical surface only: a normal hull part in front blocks a
        // vulnerable part behind it. No bracket/nearest-contact assistance.
        CameraRayPick(&hit, camera, static_cast<float>(x), static_cast<float>(y), playerShip, true);
        if (!hit.Object || (static_cast<unsigned>(hit.Object->ObjectClass) & 0x503u) != 0x503u)
            return {};
        auto* object = static_cast<CEqObj*>(hit.Object);
        if (object == playerShip || object->CloakPercent >= 1.0f) return {};
        unsigned short const sub = object->inst_to_subobj_id(hit.Instance);
        CArchGroup* group = nullptr;
        CEGun* turret = nullptr;
        long root = -1;
        if (SubObjectID::IsArchGroupID(sub))
        {
            group = object->ArchGroups.FindByID(sub);
            if (!group || !group->Arch || !group->Arch->bVulnerable || group->State != 1 ||
                group->HitPts <= 0) return {};
            root = group->GetRootIndex();
        }
        else if (SubObjectID::IsEquipID(sub))
        {
            turret = CEGun::cast(object->EquipManager.FindByID(sub));
            if (!IsTurret(turret) || turret->GetOwner() != object || turret->IsDestroyed() ||
                turret->GetHitPoints() <= 0 || !turret->IsConnected()) return {};
            root = turret->GetRootIndex();
        }
        if (root == -1) return {};
        // Respect the player's scanner range, measured to the hit surface.
        CEScanner const* scanner = CEScanner::cast(playerShip->EquipManager.FindFirst(0x80000));
        if (scanner)
        {
            Vector const& p = playerShip->WorldPosition;
            double const dx = hit.Point.x - p.x, dy = hit.Point.y - p.y, dz = hit.Point.z - p.z;
            double const range = scanner->GetRadarRange();
            if (dx * dx + dy * dy + dz * dz > range * range) return {};
        }
        return {object, group, turret, root, sub};
    }

    bool PrepareWire(Hover const& hover)
    {
        long const root = hover.root;
        std::vector<std::pair<void*, int>> parts;
        auto add = [&](void* inst) {
            int lod = 0;
            DALib::Renderer->GetInstanceCurrentLod(inst, &lod);
            parts.emplace_back(inst, lod);
        };
        add(Instance(root));
        for (void* child = DALib::Engine->GetRelatedInstance(Instance(root), 0, Instance(-1));
             child != Instance(-1); child = DALib::Engine->GetRelatedInstance(Instance(root), 0, child))
            add(child);
        if (state.objectId == hover.object->Id && state.ownerInstance == hover.object->EngineInstanceId &&
            state.root == root && state.subId == hover.subId && state.parts == parts) return !state.wires.empty();
        state.ClearWire();
        state.objectId = hover.object->Id;
        state.ownerInstance = hover.object->EngineInstanceId;
        state.root = root;
        state.subId = hover.subId;
        state.parts = std::move(parts);
        FTransform identity = {};
        identity.Rotation.D[0][0] = identity.Rotation.D[1][1] = identity.Rotation.D[2][2] = 1;
        // Cache each part in its own local coordinates. Never temporarily move
        // a live child instance to identity: its parent transform would remain.
        // Draw with fresh world transforms, including animated child parts.
        for (auto const& part : state.parts)
        {
            if (hover.object->inst_to_subobj_id(reinterpret_cast<long>(part.first)) != hover.subId)
                continue;
            auto wire = std::make_unique<WirePart>();
            wire->entry.InstanceId = part.first;
            IVMeshWire* meshWire = nullptr;
            if (DALib::Engine->QueryInstance(part.first, Iids::VMeshWire,
                    reinterpret_cast<void**>(&meshWire)) >= 0 && meshWire)
            {
                PartCacheBuildFromWire(&wire->entry, meshWire, &identity);
                meshWire->Release();
            }
            else
            {
                IMesh* mesh = nullptr;
                if (DALib::Engine->QueryInstance(part.first, Iids::Mesh,
                        reinterpret_cast<void**>(&mesh)) >= 0 && mesh)
                {
                    PartCacheBuildFromMeshTwice(&wire->entry, mesh, &identity);
                    mesh->Release();
                }
            }
            if (!wire->entry.IndexCount || !wire->entry.Vertices || !wire->entry.Indices ||
                wire->entry.VertexCount > 65535 || wire->entry.IndexCount > 16000) continue;
            wire->viewVertices = std::make_unique<FVector[]>(wire->entry.VertexCount);
            state.wires.push_back(std::move(wire));
        }
        return !state.wires.empty();
    }

    // Expand an edge in view space into a five-pixel ribbon. Keeping the original
    // endpoint depths lets the normal scene depth buffer occlude the ribbon.
    bool BuildWireQuad(FVector a, FVector b, float nearPlane, float scaleX, float scaleY,
                       unsigned color, FPartCacheVertex* out)
    {
        if (!(nearPlane > 0) || scaleX == 0 || scaleY == 0) return false;
        if (a.Z > -nearPlane && b.Z > -nearPlane) return false;
        if (a.Z > -nearPlane || b.Z > -nearPlane)
        {
            float const t = (-nearPlane - a.Z) / (b.Z - a.Z);
            FVector const cut = {a.X + (b.X - a.X) * t, a.Y + (b.Y - a.Y) * t, -nearPlane};
            if (a.Z > -nearPlane) a = cut; else b = cut;
        }
        float const dx = scaleX * (b.X / -b.Z - a.X / -a.Z);
        float const dy = scaleY * (b.Y / -b.Z - a.Y / -a.Z);
        float const length = std::sqrt(dx * dx + dy * dy);
        if (!(length > 0.0001f) || !std::isfinite(length)) return false;
        float const ox = -dy * (2.5f / length) / scaleX;
        float const oy = dx * (2.5f / length) / scaleY;
        FPartCacheVertex const a0 = {a.X + ox * -a.Z, a.Y + oy * -a.Z, a.Z, color};
        FPartCacheVertex const a1 = {a.X - ox * -a.Z, a.Y - oy * -a.Z, a.Z, color};
        FPartCacheVertex const b0 = {b.X + ox * -b.Z, b.Y + oy * -b.Z, b.Z, color};
        FPartCacheVertex const b1 = {b.X - ox * -b.Z, b.Y - oy * -b.Z, b.Z, color};
        out[0] = a0; out[1] = a1; out[2] = b0;
        out[3] = b0; out[4] = a1; out[5] = b1;
        return true;
    }

    void ApplyWireViewSpace(IRenderPipeline* pipe)
    {
        float const identity[12] = {1, 0, 0, 0, 1, 0, 0, 0, 1, 0, 0, 0};
        int combined = 1;
        pipe->GetPipelineState(7, &combined);
        // These are alternative APIs. SetView flips Z; SetModelview also flips
        // Z in combined mode and may keep the cached view from the previous call.
        // Mixing both would put our already view-space vertices behind the camera.
        if (combined) pipe->SetModelview(identity);
        else
        {
            pipe->SetWorld(identity);
            pipe->SetView(identity);
        }
    }

    // The wire draw uses the ordinary pipeline on both RP8 and RP9. Save every
    // state it touches so the following HUD/effect passes see their prior state.
    struct WirePass
    {
        IRenderPipeline* pipe = DALib::Pipeline;
        D3DRENDERSTATETYPE keys[13] = {D3DRS_ZENABLE, D3DRS_ZWRITEENABLE, D3DRS_ZFUNC,
            D3DRS_ZBIAS, D3DRS_LIGHTING, D3DRS_SPECULARENABLE, D3DRS_ALPHABLENDENABLE,
            D3DRS_COLORVERTEX, D3DRS_DIFFUSEMATERIALSOURCE, D3DRS_FOGENABLE, D3DRS_ALPHATESTENABLE,
            D3DRS_CULLMODE, D3DRS_FILLMODE};
        int values[13] = {}, stages[2][6] = {};
        void* texture = nullptr;
        int combined = 1;
        float world[12], view[12], modelview[12], immediateModelview[12];
        WirePass()
        {
            for (int i = 0; i < 13; ++i) pipe->GetRenderState(keys[i], &values[i]);
            for (int s = 0; s < 2; ++s)
                for (int i = 0; i < 6; ++i) pipe->GetTextureStageState(s, i + 1, &stages[s][i]);
            pipe->GetTextureStageTexture(0, &texture);
            pipe->GetPipelineState(7, &combined);
            Win3DPushProjection();
            std::memcpy(immediateModelview, GWin3DModelview, sizeof(immediateModelview));
            pipe->GetWorld(world);
            pipe->GetView(view);
            pipe->GetModelview(modelview);
        }
        ~WirePass()
        {
            for (int i = 0; i < 13; ++i) pipe->SetRenderState(keys[i], values[i]);
            for (int s = 0; s < 2; ++s)
                for (int i = 0; i < 6; ++i) pipe->SetTextureStageState(s, i + 1, stages[s][i]);
            pipe->SetTextureStageTexture(0, texture);
            Win3DPopProjection();
            std::memcpy(GWin3DModelview, immediateModelview, sizeof(immediateModelview));
            if (combined) pipe->SetModelview(modelview);
            else
            {
                pipe->SetWorld(world);
                pipe->SetView(view);
            }
        }
    };
}

bool VulnerableAutoselectEnabled()
{
    return GetSavedTargetingAutoselect();
}

void SetVulnerableAutoselect(bool enabled)
{
    SetSavedTargetingAutoselect(enabled);
    state.ClearWire();
    // Keep ownership of a pending left release if the toggle changes mid-click.
}

bool VulnerableTargetingMouse(FMouseEvent const& event)
{
    if (event.bMove || event.ButtonIndex != 0) return false;
    if (!event.Record.Byte18)
    {
        bool const captured = state.capturedLeft;
        state.capturedLeft = false;
        return captured;
    }
    if (!VulnerableAutoselectEnabled() || !Available()) return false;
    Hover const hover = Pick(static_cast<ICamera*>(GetClientSoundListenerObject()));
    // Only a hit on a live marked group or turret owns the click. Ordinary targeting and
    // weapon bindings must keep working everywhere else while the toggle is on.
    if (!hover.object) return false;
    FSpaceCommand command = {};
    command.Id = 0x1c;
    command.ObjectId = hover.object->Id;
    command.SubObjectId = hover.subId;
    command.Byte26 = 1;
    SpaceSendCommand(&command);
    PlayOrRewindUiSoundSlot(0x18);
    state.capturedLeft = true;
    return true;
}

void VulnerableTargetingDraw(FSpaceCamera* camera)
{
    if (!camera || !VulnerableAutoselectEnabled() || !Available()) { state.ClearWire(); return; }
    Hover const hover = Pick(AsCamera(camera));
    if (!hover.object) { state.ClearWire(); return; }
    if (!PrepareWire(hover)) return;
    // Follow health (including the critical red pulse), without the HUD's extra
    // grey/amber mouse-hover animation masking the part's damage colour.
    unsigned const color = hover.turret ? HudEquipmentDamageWireColor(hover.turret) :
        HudCollisionGroupWireColor(hover.group, false);
    WirePass pass;
    Win3DApplyCamera(AsCamera(camera));
    pass.pipe->SetRenderState(D3DRS_ZENABLE, 1);
    pass.pipe->SetRenderState(D3DRS_ZWRITEENABLE, 0);
    pass.pipe->SetRenderState(D3DRS_ZFUNC, D3DCMP_LESSEQUAL);
    pass.pipe->SetRenderState(D3DRS_ZBIAS, 1);
    pass.pipe->SetRenderState(D3DRS_FOGENABLE, 0);
    pass.pipe->SetRenderState(D3DRS_ALPHATESTENABLE, 0);
    pass.pipe->SetRenderState(D3DRS_LIGHTING, 0);
    pass.pipe->SetRenderState(D3DRS_SPECULARENABLE, 0);
    pass.pipe->SetRenderState(D3DRS_ALPHABLENDENABLE, 0);
    pass.pipe->SetRenderState(D3DRS_COLORVERTEX, 1);
    pass.pipe->SetRenderState(D3DRS_DIFFUSEMATERIALSOURCE, D3DMCS_COLOR1);
    pass.pipe->SetRenderState(D3DRS_CULLMODE, D3DCULL_NONE);
    pass.pipe->SetRenderState(D3DRS_FILLMODE, D3DFILL_SOLID);
    pass.pipe->SetTextureStageTexture(0, nullptr);
    pass.pipe->SetTextureStageState(0, D3DTSS_COLOROP, D3DTOP_SELECTARG1);
    pass.pipe->SetTextureStageState(0, D3DTSS_COLORARG1, D3DTA_DIFFUSE);
    pass.pipe->SetTextureStageState(0, D3DTSS_ALPHAOP, D3DTOP_SELECTARG1);
    pass.pipe->SetTextureStageState(0, D3DTSS_ALPHAARG1, D3DTA_DIFFUSE);
    pass.pipe->SetTextureStageState(1, D3DTSS_COLOROP, D3DTOP_DISABLE);
    pass.pipe->SetTextureStageState(1, D3DTSS_ALPHAOP, D3DTOP_DISABLE);
    ApplyWireViewSpace(pass.pipe);
    static I3DMathEngine* const math = Acquire3DMathEngine();
    auto const& view = *reinterpret_cast<FTransform const*>(camera->GetViewTransform());
    FPartCacheVertex triangles[1536]; // 256 edges per draw; bounded even for large meshes.
    unsigned count = 0;
    auto flush = [&]() {
        if (count) pass.pipe->DrawPrimitive(D3DPT_TRIANGLELIST, D3DFVF_XYZ | D3DFVF_DIFFUSE,
                                           triangles, count, nullptr);
        count = 0;
    };
    for (auto const& wire : state.wires)
    {
        auto const* transform = reinterpret_cast<FTransform const*>(
            DALib::Engine->GetInstanceTransform(wire->entry.InstanceId));
        if (!transform) continue;
        FTransform modelview;
        math->MulTransform(modelview, view, *transform);
        for (unsigned i = 0; i < wire->entry.VertexCount; ++i)
        {
            auto const& v = wire->entry.Vertices[i];
            FVector const local = {v.X, v.Y, v.Z};
            math->TransformXform(wire->viewVertices[i], modelview, local);
        }
        for (unsigned i = 0; i + 1 < wire->entry.IndexCount; i += 2)
        {
            unsigned const a = wire->entry.Indices[i], b = wire->entry.Indices[i + 1];
            if (a >= wire->entry.VertexCount || b >= wire->entry.VertexCount) continue;
            if (BuildWireQuad(wire->viewVertices[a], wire->viewVertices[b], camera->ZNear,
                              camera->XScale, camera->YScale, color, triangles + count))
            {
                count += 6;
                if (count == 1536) flush();
            }
        }
    }
    flush();
}

void VulnerableTargetingReset()
{
    state.ClearWire();
    state.capturedLeft = false;
}
