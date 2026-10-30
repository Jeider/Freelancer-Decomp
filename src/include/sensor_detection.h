// Shared content/geometry rules. No object-size or packet-format changes.
#pragma once
#include "common_archetype.h"
#include "common_cequip.h"
#include "common_cobject.h"
#include "common_server_asteroid.h"
#include <algorithm>
#include <cmath>

namespace SensorDetection
{
    inline float EffectiveRange(float range, float interference)
    {
        if (!std::isfinite(range) || range <= 0 || !std::isfinite(interference)) return 0;
        return range * (1.f - (std::max)(0.f, (std::min)(1.f, interference)));
    }

    inline bool InRange(Vector const& origin, Vector const& position, float range)
    {
        if (!std::isfinite(range) || range <= 0) return false;
        double const x = double(position.x) - origin.x;
        double const y = double(position.y) - origin.y;
        double const z = double(position.z) - origin.z;
        return x*x + y*y + z*z <= double(range)*range;
    }

    inline bool IsValuable(CObject const* object)
    {
        if (!object) return false;
        if ((object->ObjectClass & CObject::ClassSolar) == CObject::ClassSolar)
        {
            auto const* arch = static_cast<CSolar const*>(object)->solararch();
            if (arch && arch->bRadarValuable) return true;
        }
        if ((object->ObjectClass & CObject::ClassLoot) == CObject::ClassLoot)
        {
            auto const* loot = static_cast<CLoot const*>(object);
            return loot->Units > 0 && loot->ContentsArch && loot->ContentsArch->bRadarValuable;
        }
        if ((object->ObjectClass & CObject::ClassEqObj) != CObject::ClassEqObj) return false;
        auto const& manager = static_cast<CEqObj const*>(object)->EquipManager;
        CEquipTraverser walk(-1);
        for (auto const* equip = manager.Traverse(walk); equip; equip = manager.Traverse(walk))
        {
            if (!equip->Arch || !equip->Arch->bRadarValuable || equip->IsDestroyed()) continue;
            auto const* cargo = CECargo::cast(equip);
            if (!cargo || cargo->GetCount() > 0) return true;
        }
        return false;
    }

    inline CETractor const* WorkingTractor(CShip const* ship)
    {
        auto const* equip = ship ? ship->EquipManager.FindFirst(EquipTypeTractor) : nullptr;
        auto const* tractor = CETractor::cast(equip);
        // Tractors activate only after AddTarget: an idle tractor is usable.
        return tractor && !tractor->IsDestroyed() && !tractor->IsDisabled() ? tractor : nullptr;
    }

    inline bool CanCollect(CETractor const* tractor, CObject const* object)
    {
        if (!tractor || !object || (object->ObjectClass & CObject::ClassLoot) != CObject::ClassLoot) return false;
        auto const* loot = static_cast<CLoot const*>(object);
        // Reuse the server's range origin, max_length=0 convention, contents and
        // hold/ammo-capacity checks rather than a second HUD-only distance rule.
        return loot->ContentsArch && tractor->VerifyTarget(loot) == TractorOk;
    }
}
