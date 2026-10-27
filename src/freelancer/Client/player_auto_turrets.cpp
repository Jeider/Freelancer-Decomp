#include "player_auto_turrets.h"
#ifdef FREELANCER_PLAYER_AUTO_TURRETS
#include "player_turret_rules.h"
#include "player_behavior.h"
#include "player_spawn.h"
#include "character_select_equip.h"
#include "game_options.h"
#include "cli_projectile_fx.h"
#include "space_letterbox.h"
#include "space_camera.h"
#include "nn_modal.h"
#include "star_sys.h"
#include "common_cequip.h"
#include "common_archetype.h"
#include "common_iface.h"
#include "common_physys.h"
#include "common_misc.h"
#include "port_config.h"
#include <algorithm>
#include <cmath>
#include <vector>

namespace PlayerAutoTurrets
{
namespace
{
    struct MemberState
    {
        unsigned short id;
        CEGun* identity; // Compared only; always resolve through the live equipment manager.
        bool selected = true;
        bool manual = false;
        unsigned targetId = 0;
        float searchAfter = 0, held = 0;
    };
    BaseWatcher owner, designated;
    std::vector<MemberState> members;
    Mode mode = Mode::Manual;
    Mode preferred = Mode::Hostiles;
    Status status = Status::Off;
    unsigned revision = ~0u, system = 0, hullId = 0, reserve = 35, cursor = 0;
    bool energyHold = false;
    char preferencePath[MAX_PATH] = {}, preferenceSection[160] = {};

    void LoadPreferences(CShip* ship)
    {
        preferencePath[0] = preferenceSection[0] = 0;
        if (!ship || !GetUserDataPath(preferencePath)) return;
        strcat_s(preferencePath, "\\auto_turrets.ini");
        strcpy_s(preferenceSection, "v1.");
        wchar_t const* name = GetPlayerCharacterNameRetail();
        if (!name || !*name) { preferencePath[0] = 0; return; }
        for (unsigned i = 0; name[i] && i < 24; ++i)
        {
            char unit[8]; sprintf_s(unit, "%04x", unsigned(name[i])); strcat_s(preferenceSection, unit);
        }
        char hull[16]; sprintf_s(hull, ".%08x", ship->Archetype->get_id()); strcat_s(preferenceSection, hull);
        reserve = (std::min)(90u, GetPrivateProfileIntA(preferenceSection, "reserve_percent", reserve, preferencePath));
        preferred = GetPrivateProfileIntA(preferenceSection, "mode", 2, preferencePath) == 1 ? Mode::Target : Mode::Hostiles;
    }
    bool SavedSelection(CEGun* gun)
    {
        char const* hp = gun->GetParentHPName().Value;
        return !preferencePath[0] || !hp || GetPrivateProfileIntA(preferenceSection, hp, 1, preferencePath) != 0;
    }
    void SavePreference(char const* key, unsigned value)
    {
        if (!preferencePath[0] || !key || !*key) return;
        char text[16]; sprintf_s(text, "%u", value);
        if (!WritePrivateProfileStringA(preferenceSection, key, text, preferencePath))
            FDUMP(0x100001, "Auto turrets: could not save preferences (%lu)\n", GetLastError());
    }

    IObjRW* Resolve(BaseWatcher const& watch)
    {
        return watch.target() ? ObjRwFromWatchable(const_cast<Watchable*>(watch.target())) : nullptr;
    }
    IObjRW* Player() { return static_cast<IObjRW*>(GetPlayerObjRW()); }
    CShip* Ship()
    {
        auto* rw = Resolve(owner);
        auto* obj = rw ? const_cast<CObject*>(rw->cobject()) : nullptr;
        return obj && obj->ObjectClass == CObject::ClassShip ? static_cast<CShip*>(obj) : nullptr;
    }
    bool Eligible(CEGun* gun)
    {
        if (!gun || !gun->IsConnected() || !gun->ProjectileArch()) return false;
        auto const* arch = gun->GunArch();
        auto const* ammo = gun->MunitionArch();
        if (!ammo || ammo->bRequiresAmmo || ammo->Seeker || ammo->bForceGunOri) return false;
        if (!std::isfinite(arch->MuzzleVelocity) || arch->MuzzleVelocity <= 0 ||
            !std::isfinite(arch->RefireDelay) || arch->RefireDelay < 0 ||
            !std::isfinite(ammo->Lifetime) || ammo->Lifetime <= 0) return false;
        bool turret = arch->bAutoTurret;
        for (auto* hp = arch->HpGunTypesBegin; hp != arch->HpGunTypesEnd; ++hp)
            turret |= *hp == HpTypeTurret || (*hp >= HpTypeTurretSpecial1 && *hp <= HpTypeTurretSpecial10);
        return turret && gun->GetBarrelInfo(0) != nullptr;
    }
    CEGun* ResolveGun(MemberState const& member)
    {
        auto* ship = Ship();
        auto* gun = ship ? CEGun::cast(ship->EquipManager.FindByID(member.id)) : nullptr;
        return gun == member.identity && Eligible(gun) ? gun : nullptr;
    }
    MemberState* Find(CEquip const* equip)
    {
        if (!equip || equip->GetOwner() != Ship()) return nullptr;
        for (auto& member : members)
            if (member.id == equip->GetID() && member.identity == equip) return &member;
        return nullptr;
    }
    void Release(MemberState& member)
    {
        if (auto* gun = ResolveGun(member))
        {
            // An individual OFF always wins over the group's remembered state.
            bool const active = gun->IsActive() && member.manual;
            auto* rw = Resolve(owner);
            if (rw && gun->IsActive() != active)
                CliShipActivateEquip(static_cast<IObjAffect*>(rw), &member.id, active ? 1 : 0,
                                     static_cast<int>(GetPlayerConnectionId()));
            auto* ship = Ship();
            auto* target = ship->get_target();
            auto const* object = target ? target->cobject() : nullptr;
            auto* simple = object && (object->ObjectClass & 3u) == 3u ?
                static_cast<CSimple*>(const_cast<CObject*>(object)) : nullptr;
            gun->SetTarget(simple, ship->get_sub_target());
            // Do not leave a stale automatic point in the native two-second aim cache.
            Vector point = gun->GetBarrelPosWS(0);
            Vector const dir = gun->GetBarrelDirWS(0);
            point.x += dir.x * 1000; point.y += dir.y * 1000; point.z += dir.z * 1000;
            gun->SetTargetPoint(point);
        }
    }
    bool Hostile(IObjRW* target)
    {
        if (!target || target == Player() || !target->is_targetable() || target->is_dying()) return false;
        auto const* obj = target->cobject();
        if (!obj || obj->ObjectClass != CObject::ClassShip) return false;
        // SP shares objects with the local server: scanner contacts can have the
        // server's ObjectDb while the player's ship uses the client's adapter.
        // Database pointer identity is not system identity.
        if (obj->PhysicsSystemId != system || Ship()->PhysicsSystemId != system) return false;
        // Match HUD enemy selection: the contact's attitude towards the player.
        // Relations can be asymmetric; the native hostile boundary includes -0.6.
        return GetAttitudeClass(Player(), target) == -1;
    }
    bool Finite(Vector const& v) { return std::isfinite(v.x) && std::isfinite(v.y) && std::isfinite(v.z); }
    float Distance2(Vector const& a, Vector const& b)
    {
        float const x = a.x-b.x, y = a.y-b.y, z = a.z-b.z;
        return x*x+y*y+z*z;
    }
    bool Lead(CEGun* gun, IObjRW* target, Vector& point)
    {
        Vector const origin = gun->GetBarrelPosWS(0);
        Vector const pos = target->cobject()->get_center_of_mass();
        Vector const vel = target->get_velocity(), ownVel = Player()->get_velocity();
        Vector rel; rel.x = pos.x-origin.x; rel.y = pos.y-origin.y; rel.z = pos.z-origin.z;
        Vector speed; speed.x = vel.x-ownVel.x; speed.y = vel.y-ownVel.y; speed.z = vel.z-ownVel.z;
        float time = 0;
        if (!Finite(rel) || !Finite(speed) ||
            !CEGun::ComputeTimeToTgt(rel, speed, gun->GunArch()->MuzzleVelocity, time) ||
            !std::isfinite(time) || time < 0 || time > gun->ProjectileArch()->Lifetime) return false;
        point.x = pos.x + speed.x*time; point.y = pos.y + speed.y*time; point.z = pos.z + speed.z*time;
        return Finite(point) && Distance2(origin, point) > 0 && gun->CanPointAt(point, 0.01f);
    }
    bool ClearLine(CEGun* gun, IObjRW* target, Vector const& aim)
    {
        for (unsigned i = 0; i < 8; ++i)
        {
            if (!gun->GetBarrelInfo(i)) continue;
            Vector from = gun->GetBarrelPosWS(i);
            Vector const dir = gun->GetBarrelDirWS(i);
            float const distance = std::sqrt(Distance2(from, aim));
            if (!Finite(from) || !Finite(dir) || !std::isfinite(distance) || distance <= 0) return false;
            double const dot = ((aim.x-from.x)*dir.x + (aim.y-from.y)*dir.y + (aim.z-from.z)*dir.z) / distance;
            if (!(dot >= std::cos(0.02))) return false;
            // Only a numerical muzzle offset, never a ship-sized blind zone.
            from.x += dir.x * 0.05f; from.y += dir.y * 0.05f; from.z += dir.z * 0.05f;
            PhySys::RayHit hits[32];
            int const count = PhySys::FindRayCollisions(system, from, aim, hits, 32);
            if (count < 0 || count >= 32) return false;
            for (int h = 0; h < count; ++h)
                if (hits[h].Object && hits[h].Object != target->cobject())
                {
                    // The player's shield encloses the muzzle; the hull still blocks fire.
                    if (hits[h].Object == Ship() && Ship()->is_shield_part(hits[h].PartId)) continue;
                    return false;
                }
        }
        return true;
    }
}

bool Enabled()
{
    static bool const enabled = PortConfigInt("AutoTurrets", "enabled", 0) != 0;
    return enabled;
}

void Reset()
{
    if (Resolve(owner) == Player() && SinglePlayer())
        for (auto& member : members) if (mode != Mode::Manual && member.selected) Release(member);
    mode = Mode::Manual; status = Status::Off; energyHold = false;
    designated.set(nullptr); owner.set(nullptr); members.clear(); cursor = 0;
    preferencePath[0] = preferenceSection[0] = 0;
    preferred = Mode::Hostiles;
}

void Reconcile()
{
    auto* player = Enabled() && SinglePlayer() ? Player() : nullptr;
    unsigned const currentRevision = GetGameSessionLoadRevision();
    unsigned const currentSystem = StarSysGetActiveSystemId();
    auto const* object = player ? player->cobject() : nullptr;
    unsigned const currentHull = object && object->Archetype ? object->Archetype->get_id() : 0;
    if (player != Resolve(owner) || revision != currentRevision || currentSystem != system || hullId != currentHull)
    {
        Reset(); revision = currentRevision; system = currentSystem; hullId = currentHull;
        if (player) owner.set(static_cast<Watchable*>(player));
        reserve = (std::min)(90u, unsigned((std::max)(0, PortConfigInt("AutoTurrets", "reserve_percent", 35))));
        LoadPreferences(Ship());
    }
    auto* ship = Ship();
    if (!ship || (player && player->is_dying())) { Reset(); return; }
    std::vector<MemberState> live;
    CEquipTraverser walk(EquipTypeGun);
    while (auto* equip = ship->EquipManager.Traverse(walk))
    {
        auto* gun = CEGun::cast(equip);
        if (!Eligible(gun)) continue;
        auto* old = Find(equip);
        if (old) live.push_back(*old);
        else live.push_back({gun->GetID(), gun, mode == Mode::Manual && SavedSelection(gun), gun->IsActive()});
    }
    members.swap(live);
}

bool Owns(CEquip const* equip)
{
    if (mode == Mode::Manual || Resolve(owner) != Player()) return false;
    auto* member = Find(equip);
    return member && member->selected;
}
bool GroupActivation(CEquip const* equip, bool active)
{
    if (!Owns(equip)) return false;
    Find(equip)->manual = active;
    return true;
}
bool ManualActive(CEquip const* equip) { return Owns(equip) ? Find(equip)->manual : equip->IsActive(); }
void ActivationChanged(CEquip const* equip, bool active)
{
    if (Owns(equip)) Find(equip)->manual = active;
}

void SetMode(Mode next)
{
    Reconcile();
    if (next == Mode::Manual)
    {
        for (auto& member : members) if (mode != Mode::Manual && member.selected) Release(member);
        mode = next; status = Status::Off; designated.set(nullptr); energyHold = false; return;
    }
    if (!SinglePlayer()) { status = Status::Multiplayer; return; }
    if (!Ship() || !Enabled()) return;
    if (IsSpaceInitInProgress()) { status = Status::Suspended; return; }
    if (next == Mode::Target)
    {
        auto* target = Ship()->get_target();
        if (!Hostile(target)) { SetMode(Mode::Manual); status = Status::NoTarget; return; }
        designated.set(static_cast<Watchable*>(target));
    }
    else designated.set(nullptr);
    if (mode == Mode::Manual)
        for (auto& member : members) if (auto* gun = ResolveGun(member)) member.manual = gun->IsActive();
    for (auto& member : members) { member.targetId = 0; member.searchAfter = member.held = 0; }
    mode = next; status = Status::Ready;
}
Mode GetMode() { return mode; }
Mode GetPreferredMode() { return preferred; }
void SetPreferredMode(Mode next)
{
    SetMode(Mode::Manual);
    preferred = next == Mode::Target ? Mode::Target : Mode::Hostiles;
    SavePreference("mode", preferred == Mode::Target ? 1 : 2);
}
Status GetStatus() { return status; }
void CycleReserve()
{
    reserve = reserve < 20 ? 20 : reserve < 35 ? 35 : reserve < 50 ? 50 : 0; energyHold = false;
    SavePreference("reserve_percent", reserve);
}
unsigned ReservePercent() { return reserve; }
unsigned MemberCount() { return unsigned(members.size()); }
CEGun* Member(unsigned index) { return index < members.size() ? ResolveGun(members[index]) : nullptr; }
bool Selected(unsigned index) { return index < members.size() && members[index].selected; }
void ToggleMember(unsigned index)
{
    // Changing the automatic group revokes the current order; adding a gun cannot arm it.
    SetMode(Mode::Manual);
    if (index >= members.size()) return;
    auto& member = members[index];
    if (mode != Mode::Manual && member.selected) Release(member);
    if (auto* gun = ResolveGun(member)) member.manual = gun->IsActive();
    member.selected = !member.selected;
    if (auto* gun = ResolveGun(member)) SavePreference(gun->GetParentHPName().Value, member.selected ? 1 : 0);
}

void Tick(float dt, bool docking)
{
    Reconcile();
    if (mode == Mode::Manual) return;
    if (mode == Mode::Target && !Resolve(designated)) { SetMode(Mode::Manual); return; }
    auto* ship = Ship();
    if (!ship || !std::isfinite(dt) || dt <= 0) return;
    if (docking || IsLetterboxVisible() || G_bNnScreenUp || ship->is_cruise_active() ||
        ship->is_using_tradelane() || ship->is_control_excluded(4u) || ship->CloakPercent > 0)
    { status = Status::Suspended; return; }
    auto* scanner = CEScanner::cast(ship->EquipManager.FindFirst(EquipTypeScanner));
    if (!scanner || !scanner->IsFunctioning()) { status = Status::NoScanner; return; }
    // Native FIGHTER..ARMORED_TRANSPORT type bits; do not add loot/projectiles
    // to the scanner's shared, bounded contact cache.
    scanner->scan_for_types(0x7f0000u);
    std::vector<IObjRW*> contacts;
    for (int i = 0; i < scanner->Scans.Count && i < 256; ++i)
        if (auto* candidate = Resolve(scanner->Scans.Entries[i]))
            if (Hostile(candidate) && (mode != Mode::Target || candidate == Resolve(designated)))
                contacts.push_back(candidate);
    if (contacts.empty()) { status = Status::NoTarget; return; }
    if (members.empty()) { status = Status::NoTurrets; return; }
    if (energyHold && !PlayerTurretRules::Resume(ship->Power, ship->MaxPower, reserve))
    { status = Status::Energy; return; }
    energyHold = false; status = Status::NoTurrets;
    unsigned const start = cursor++ % unsigned(members.size());
    bool fired = false;
    for (unsigned n = 0; n < members.size(); ++n)
    {
        auto& member = members[(start+n) % members.size()];
        auto* gun = ResolveGun(member);
        if (!member.selected || !gun || !gun->IsFunctioning()) continue;
        IObjRW* target = nullptr; Vector aim; float best = 3.402823466e+38F;
        member.searchAfter -= dt; member.held += dt;
        for (auto* candidate : contacts)
            if (candidate->get_id() == member.targetId && Lead(gun, candidate, aim))
            { target = candidate; best = Distance2(gun->GetBarrelPosWS(0), aim); break; }
        if (!target && member.searchAfter > 0) { status = Status::NoTarget; continue; }
        // Keep a valid target for at least 0.75 s; afterwards switch only for a
        // substantially closer candidate. No hidden contacts or frame-rate-dependent churn.
        if (!target || (member.searchAfter <= 0 && member.held >= 0.75f))
        {
            member.searchAfter = 0.2f;
            float const threshold = target ? best * 0.64f : best;
            float nextBest = threshold;
            for (auto* candidate : contacts)
            {
                Vector point;
                if (!Lead(gun, candidate, point)) continue;
                float const distance = Distance2(gun->GetBarrelPosWS(0), point);
                if (distance < nextBest) { nextBest = distance; target = candidate; aim = point; }
            }
        }
        if (!target) { status = Status::NoTarget; continue; }
        if (member.targetId != target->get_id()) { member.targetId = target->get_id(); member.held = 0; }
        gun->SetTarget(static_cast<CSimple*>(const_cast<CObject*>(target->cobject())), 0);
        gun->SetTargetPoint(aim);
        status = Status::Aiming;
        if (!gun->CanSeeTargetPoint(aim, 0.02f) || gun->RefireElapsed < gun->GunArch()->RefireDelay) continue;
        if (!PlayerTurretRules::CanSpend(ship->Power, ship->MaxPower, gun->GetPowerDrawPerFire(), reserve))
        { energyHold = true; status = Status::Energy; continue; }
        if (!ClearLine(gun, target, aim)) { status = Status::Blocked; continue; }
        fired |= CliShipFireAutomatic(static_cast<IObjAffect*>(Player()), member.id, aim);
    }
    if (fired) status = Status::Firing;
}
}
#endif
