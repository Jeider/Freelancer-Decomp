#pragma once
#include "radar_wireframe_geometry.h"
#include "dacom_iids.h"
#include "render/mesh_iface.h"
#include <map>
#include <memory>

// Included after the engine/object declarations by hud_radar.cpp.
namespace RadarWireframe
{
    struct CachedWire
    {
        std::shared_ptr<IVMeshWire> source;
        void const* meshData = nullptr;
        Geometry geometry;
        bool seen = false;
    };

    struct Layer
    {
        std::map<IVMeshWire*, CachedWire> cache;
        std::vector<Point> scratch;
        unsigned system = 0;
        bool reported = false;

        void Clear() { cache.clear(); scratch.clear(); system = 0; reported = false; }

        template<class DrawLine>
        unsigned Part(void* instance, Transform const& player, float range,
                      RadarProjection::Layout const& layout, unsigned color, DrawLine draw)
        {
            if (!instance || instance == G_InvalidEngineHandle) return 0;
            IVMeshWire* raw = nullptr;
            if (DALib::Engine->QueryInstance(instance, Iids::VMeshWire, reinterpret_cast<void**>(&raw)) < 0 || !raw)
                return 0;
            // Keep only immutable wire interfaces/CPU geometry, never scene object/instance pointers.
            std::shared_ptr<IVMeshWire> source(raw, [](IVMeshWire* p) { p->Release(); });
            void const* mesh = source->GetMeshData();
            void const* wire = source->GetWireData();
            if (!mesh || !wire) return 0; // Retry if the mesh library is not yet loaded.
            auto& entry = cache[raw];
            if (!entry.source || entry.meshData != mesh)
            {
                entry.source = source;
                entry.meshData = mesh;
                Decode(mesh, MeshBytes(mesh), wire, 16u + 2u * Read<unsigned short>(wire, 12), entry.geometry);
            }
            entry.seen = true;
            return Emit(entry.geometry, DALib::Engine->GetInstanceTransform(instance),
                {player.Translation.x, player.Translation.y, player.Translation.z}, player.Rotation.E,
                range, layout, color, scratch, draw);
        }

        template<class DrawLine>
        void Draw(IObjDB* db, Transform const& player, unsigned systemId, float range,
                  RadarProjection::Layout const& layout, float opacity, DrawLine draw)
        {
            if (system != systemId) { Clear(); system = systemId; }
            if (!db || !DALib::Engine || range <= 0) { cache.clear(); return; }
            for (auto& item : cache) item.second.seen = false;
            unsigned objects = 0, lines = 0;
            // Walk all solars, independent of the scanner's cache, targetability, parents,
            // hidden/mining metadata, show_solars and max_contacts. Only screen clipping applies.
            struct { void* cursor; void* head; unsigned mask; } iter = {nullptr, nullptr, 0xfdffu};
            for (auto* contact = db->GetNext(&iter); contact; contact = db->GetNext(&iter))
            {
                auto const* object = contact->cobject();
                if (!object || contact->is_dying() || (object->ObjectClass & CObject::ClassSolar) != CObject::ClassSolar)
                    continue;
                auto const* arch = static_cast<CSolar const*>(object)->solararch();
                if (!arch || !arch->GetRadarWireframe()) continue;
                ++objects;
                void* const root = reinterpret_cast<void*>(static_cast<intptr_t>(contact->get_index()));
                if (!root || root == G_InvalidEngineHandle) continue;
                unsigned const color = RadarFrame::Color(0x8abecbu, opacity * 0.25f);
                lines += Part(root, player, range, layout, color, draw);
                void* child = G_InvalidEngineHandle;
                while ((child = DALib::Engine->GetRelatedInstance(root, 0, child)) != G_InvalidEngineHandle)
                    lines += Part(child, player, range, layout, color, draw);
            }
            for (auto it = cache.begin(); it != cache.end();)
                if (!it->second.seen) it = cache.erase(it); else ++it;
            if (objects && !reported)
            {
                reported = true;
                FDUMP(0x100002, "HUD_RADAR wireframe: solars=%u cached_parts=%u visible_lines=%u\n",
                      objects, static_cast<unsigned>(cache.size()), lines);
            }
        }
    };
}
