#include "flight_telemetry.h"
#include "flight_telemetry_recording.h"
#include "player_behavior.h"
#include "player_spawn.h"
#include "player_route.h"
#include "player_flight_actions.h"
#include "cockpit_free_look.h"
#include "game_options.h"
#include "globals.h"
#include "input_manager.h"
#include "hud_command_dispatch.h"
#include "menu_keymap_config.h"
#include "nn_modal.h"
#include "space_letterbox.h"
#include "star_sys.h"
#include "common_archetype.h"
#include "common_cequip.h"
#include "common_cobject.h"
#include "common_iface.h"
#include "common_misc.h"
#include <algorithm>
#include <cmath>
#include <limits>
#include <vector>

namespace FlightTelemetry {
namespace {
Recording recording;
SampleClock clock;
Origin origin = Origin::Unknown;
unsigned shipId = 0, systemId = 0, revision = 0, connectionId = 0;
bool paused = false, sampleDue = false, inputActive = false;
char const* startError = nullptr;
constexpr float missing = std::numeric_limits<float>::quiet_NaN();

std::string Vec(float x, float y, float z) {
    return '[' + Number(x) + ',' + Number(y) + ',' + Number(z) + ']';
}
std::string Vec(Vector const& v) { return Vec(v.x, v.y, v.z); }
Vector Difference(Vector const& a, Vector const& b) {
    Vector result; result.x = a.x-b.x; result.y = a.y-b.y; result.z = a.z-b.z; return result;
}
std::string Rotation(Matrix const& m) {
    return '[' + Vec(m.E[0][0], m.E[0][1], m.E[0][2]) + ',' +
        Vec(m.E[1][0], m.E[1][1], m.E[1][2]) + ',' + Vec(m.E[2][0], m.E[2][1], m.E[2][2]) + ']';
}
char const* Source() {
    switch (origin) {
    case Origin::MappedInput: return "mapped_input";
    case Origin::KeyboardSteering: return "keyboard_steering";
    case Origin::MouseSteering: return "mouse_steering";
    case Origin::Synthetic: return "synthetic";
    default: return "unknown";
    }
}
bool SessionValid() {
    if (!recording.Active()) return false;
    if (revision != GetGameSessionLoadRevision() || systemId != StarSysGetActiveSystemId() ||
        shipId != GetPlayerShipId() || connectionId != GetPlayerConnectionId() || !GetPlayerObjRW()) {
        recording.Stop("session_changed"); return false;
    }
    return true;
}
void Emit(char const* type, Json const& data) {
    recording.Record(type, clock.simulation, clock.frame, data.Str());
}
Json Object(IObjRW* object) {
    float hp = missing, maxHp = missing, shield = missing, maxShield = missing;
    bool shieldActive = false;
    if (object->get_status(hp, maxHp) != 0) hp = maxHp = missing;
    bool shieldKnown = object->get_shield_status(shield, maxShield, shieldActive) == 0;
    if (!shieldKnown) shield = maxShield = missing;
    unsigned type = 0;
    bool typeKnown = object->get_type(type) == 0;
    return Json().Num("id", object->get_id()).Raw("type_mask", typeKnown ? Number(type) : "null")
        .Raw("position", Vec(object->get_position())).Raw("velocity", Vec(object->get_velocity()))
        .Raw("orientation", Rotation(object->get_orientation()))
        .Raw("angular_velocity", Vec(object->get_angular_velocity()))
        .Num("hull", hp).Num("hull_max", maxHp).Num("shield", shield).Num("shield_max", maxShield)
        .Raw("shield_active", shieldKnown ? (shieldActive ? "true" : "false") : "null")
        .Bool("dying", object->is_dying());
}
Json Context() {
    auto* behavior = GetBehaviorManager(static_cast<IObjRW*>(GetPlayerObjRW()));
    return Json().Bool("paused", paused).Bool("input_active", ClientInputIsActive())
        .Bool("ui_focus", HudGetInputFocus() != nullptr).Bool("nn_screen", G_bNnScreenUp)
        .Bool("letterbox", IsLetterboxVisible()).Bool("cockpit_look", CockpitFreeLook::Enabled())
        .Bool("mouse_flight_locked", IsMouseFlightLocked())
        .Bool("mouse_flight_engaged", IsMouseFlightHoldThresholdReached())
        .Bool("route_active", PlayerRoute::Active()).Text("flight_action", PlayerFlightActions::TelemetryAction())
        .Raw("behavior", behavior ? Number(behavior->CurrentBehaviorIndex) : "null");
}
Json InputBaseline() {
    std::string held = "[";
    bool valid = ClientInputIsActive();
    if (valid) for (unsigned command = 0; command < 256; ++command) {
        if (!KeyMapIsCommandHeld(command)) continue;
        if (held.size() > 1) held += ',';
        held += Number(command);
    }
    return Json().Raw("held_mapped_commands", valid ? held + ']' : "null")
        .Bool("valid", valid).Num("command_id_limit", 256);
}
Json Snapshot(int docking) {
    auto* player = static_cast<IObjRW*>(GetPlayerObjRW());
    auto* ship = static_cast<CShip*>(GetPlayerShipObject());
    auto state = Object(player);
    float throttle = missing;
    if (player->get_throttle(throttle) != 0) throttle = missing;
    Vector axis, nudge; axis.x = axis.y = axis.z = missing; nudge = axis;
    if (player->get_axis_throttle(axis) != 0) axis.x = axis.y = axis.z = missing;
    if (player->get_nudge_vec(nudge) != 0) nudge.x = nudge.y = nudge.z = missing;
    StrafeDir strafe = static_cast<StrafeDir>(0);
    bool strafeKnown = player->get_strafe_dir(strafe) == 0;
    bool thrust = false, cruise = false, lane = false;
    bool thrustKnown = player->are_thrusters_active(thrust) == 0;
    bool cruiseKnown = player->is_cruise_active(cruise, lane) == 0;
    state.Num("throttle", throttle).Raw("axis_throttle", Vec(axis)).Raw("nudge", Vec(nudge))
        .Raw("strafe", strafeKnown ? Number(static_cast<int>(strafe)) : "null")
        .Bool("engine_active", GetPlayerEngineIsActive())
        .Raw("thrusters_active", thrustKnown ? (thrust ? "true" : "false") : "null")
        .Raw("cruise", cruiseKnown ? (cruise ? "true" : "false") : "null")
        .Raw("tradelane", cruiseKnown ? (lane ? "true" : "false") : "null")
        .Num("weapon_energy", ship ? ship->Power : missing)
        .Num("weapon_energy_max", ship ? ship->MaxPower : missing)
        .Num("thrust_energy", ship ? ship->ThrustPower : missing)
        .Num("thrust_energy_max", ship ? ship->MaxThrustPower : missing);
    IObjRW* target = nullptr; player->get_target(target);
    Json data;
    data.Text("phase", docking < 0 ? "initial" : "post_frame")
        .Raw("player", state.Str()).Raw("context", Context()
            .Raw("docking", docking < 0 ? "null" : (docking ? "true" : "false")).Str())
        .Num("missed_sample_intervals", clock.missed);
    if (target) {
        auto t = Object(target);
        Vector delta = Difference(target->get_position(), player->get_position());
        Vector velocity = Difference(target->get_velocity(), player->get_velocity());
        auto const& m = player->get_orientation();
        auto local = [&](Vector const& v) { return Vec(
            m.E[0][0]*v.x + m.E[1][0]*v.y + m.E[2][0]*v.z,
            m.E[0][1]*v.x + m.E[1][1]*v.y + m.E[2][1]*v.z,
            m.E[0][2]*v.x + m.E[1][2]*v.y + m.E[2][2]*v.z); };
        double distance = std::sqrt(double(delta.x)*delta.x + double(delta.y)*delta.y + double(delta.z)*delta.z);
        float attitude = missing; if (target->get_attitude_towards(attitude, player) != 0) attitude = missing;
        unsigned short sub = 0; bool subKnown = player->get_subtarget(sub) == 0;
        t.Raw("relative_position_local", local(delta)).Raw("relative_velocity_local", local(velocity))
            .Num("distance", distance).Num("closing_speed", distance > 0 ?
                -(double(delta.x)*velocity.x + double(delta.y)*velocity.y + double(delta.z)*velocity.z)/distance : missing)
            .Num("attitude_to_player", attitude).Raw("subtarget", subKnown ? Number(sub) : "null");
        data.Raw("target", t.Str());
    } else data.Raw("target", "null");

    // Observe the existing scanner cache only. Do not scan or change its filters.
    // This deliberately is not an omniscient list of NPCs/obstacles.
    auto* scanner = ship ? CEScanner::cast(const_cast<CEquip*>(ship->EquipManager.FindFirst(EquipTypeScanner))) : nullptr;
    struct Contact { IObjRW* object; double distance; };
    std::vector<Contact> contacts;
    int count = scanner ? (std::max)(0, (std::min)(256, scanner->Scans.Count)) : 0;
    for (int i = 0; i < count; ++i) {
        auto* contact = ObjRwFromWatchable(const_cast<Watchable*>(scanner->Scans.Entries[i].target()));
        if (!contact || contact == player || contact->is_dying()) continue;
        auto delta = Difference(contact->get_position(), player->get_position());
        double d = double(delta.x)*delta.x + double(delta.y)*delta.y + double(delta.z)*delta.z;
        if (std::isfinite(d)) contacts.push_back({contact, d});
    }
    std::sort(contacts.begin(), contacts.end(), [](Contact const& a, Contact const& b) {
        return a.distance == b.distance ? a.object->get_id() < b.object->get_id() : a.distance < b.distance;
    });
    std::string nearby = "[";
    size_t kept = (std::min)(contacts.size(), size_t(16));
    for (size_t i = 0; i < kept; ++i) {
        if (i) nearby += ',';
        auto* object = contacts[i].object;
        float attitude = missing; if (object->get_attitude_towards(attitude, player) != 0) attitude = missing;
        float radius = missing; Vector center;
        if (object->get_physical_radius(radius, center) != 0) radius = missing;
        nearby += Json().Num("id", object->get_id()).Raw("position", Vec(object->get_position()))
            .Raw("velocity", Vec(object->get_velocity())).Num("attitude_to_player", attitude)
            .Num("radius", radius).Str();
    }
    data.Raw("scanner_contacts", nearby + ']').Bool("scanner_available", scanner != nullptr)
        .Num("scanner_cache_count", scanner ? scanner->Scans.Count : 0)
        .Bool("contacts_truncated", contacts.size() > kept || (scanner && scanner->Scans.Count > count));
    return data;
}
}
OriginScope::OriginScope(Origin value) noexcept : previous(origin) { origin = value; }
OriginScope::~OriginScope() { origin = previous; }
bool IsRecording() noexcept { return recording.Active(); }
char const* LastError() noexcept { return startError ? startError : ErrorName(recording.LastError()); }
bool Stop(char const* reason) noexcept { return recording.Stop(reason); }
bool Start(wchar_t const* path) noexcept {
    if (recording.Active()) return false;
    // Reap a worker that stopped itself after a write/queue failure.
    recording.Stop("restart_after_error"); startError = nullptr;
    auto* player = static_cast<IObjRW*>(GetPlayerObjRW());
    auto* ship = static_cast<CShip*>(GetPlayerShipObject());
    if (!player || !ship || !ship->shiparch()) { startError = "not_in_space"; return false; }
    try {
        shipId = GetPlayerShipId(); systemId = StarSysGetActiveSystemId();
        revision = GetGameSessionLoadRevision(); connectionId = GetPlayerConnectionId();
        clock = {}; paused = ShouldSkipLocalServerTick(); sampleDue = false;
        inputActive = ClientInputIsActive();
        auto const* arch = ship->shiparch();
        auto metadata = Json().Text("client_build", __DATE__ " " __TIME__).Num("system", systemId)
            .Num("ship", shipId).Num("ship_archetype", GetPlayerShipArchetypeId()).Num("connection", connectionId)
            .Num("mass", player->get_mass()).Num("linear_drag", arch->LinearDrag)
            .Raw("angular_drag", Vec(arch->AngularDragX, arch->AngularDragY, arch->AngularDragZ))
            .Raw("steering_torque", Vec(arch->SteeringTorqueX, arch->SteeringTorqueY, arch->SteeringTorqueZ))
            .Raw("rotation_inertia", Vec(arch->RotationInertiaX, arch->RotationInertiaY, arch->RotationInertiaZ))
            .Num("strafe_force", arch->StrafeForce).Num("nudge_force", arch->NudgeForce)
            .Text("coordinates", "world XYZ; local +X right,+Y up,-Z forward; orientation row arrays, local-to-world")
            .Text("units", "native game distance, seconds, radians; velocities per second")
            .Text("snapshot_phase", "after physics and client controls, before object reap")
            .Text("damage_semantics", "server reports remaining subobject health, not damage amount or shot attribution");
        std::string equipment = "[";
        CEquipTraverser traverser;
        while (auto const* equip = ship->EquipManager.Traverse(traverser)) {
            if (equipment.size() > 1) equipment += ',';
            equipment += Json().Num("id", equip->GetID()).Num("type", equip->GetType())
                .Raw("archetype", equip->EquipArch() ? Number(equip->EquipArch()->get_id()) : "null")
                .Bool("active", equip->IsActive()).Str();
        }
        metadata.Raw("equipment", equipment + ']');
        if (!recording.Start(path, metadata.Str())) return false;
        // Baseline is a binding-level observation, not a fabricated key-down event.
        Emit("input_baseline", InputBaseline());
        Emit("snapshot", Snapshot(-1));
        return recording.Active();
    } catch (...) { recording.Fail(Error::Allocation); recording.Stop("start_failed"); return false; }
}
void BeginFrame(float dt, bool isPaused) noexcept {
    if (!SessionValid()) return;
    sampleDue = clock.Advance(dt, isPaused) || paused != isPaused;
    paused = isPaused;
    if (inputActive != ClientInputIsActive()) {
        inputActive = ClientInputIsActive(); sampleDue = true;
        try { Emit("input_baseline", InputBaseline()); }
        catch (...) { recording.Fail(Error::Allocation); }
    }
}
void EndFrame(bool docking) noexcept {
    if (!SessionValid() || !sampleDue) return;
    sampleDue = false;
    try { Emit("snapshot", Snapshot(docking)); }
    catch (...) { recording.Fail(Error::Allocation); }
}
void Input(unsigned command, int eventKind, bool down, bool repeat, unsigned modifiers) noexcept {
    if (!SessionValid()) return;
    try { Emit("mapped_input", Json().Num("command", command).Num("event_kind", eventKind)
        .Bool("down", down).Bool("repeat", repeat).Num("modifiers", modifiers).Raw("context", Context().Str())); }
    catch (...) { recording.Fail(Error::Allocation); }
}
void Steering(char const* device, float x, float y, float z) noexcept {
    if (!SessionValid()) return;
    try { Emit("steering_input", Json().Text("device", device).Raw("direction", Vec(x,y,z))); }
    catch (...) { recording.Fail(Error::Allocation); }
}
void Command(char const* name, float x, float y, float z) noexcept {
    if (!SessionValid()) return;
    try { Emit("behavior_command", Json().Text("name", name).Text("origin", Source())
        .Raw("value", Vec(x,y,z)).Raw("context", Context().Str())); }
    catch (...) { recording.Fail(Error::Allocation); }
}
void Shot(unsigned ship, unsigned short equipment, bool automatic, Vector const* aim) noexcept {
    if (!SessionValid() || ship != shipId) return;
    try { Emit("shot", Json().Num("equipment", equipment).Bool("automatic", automatic)
        .Raw("aim_world", aim ? Vec(*aim) : "null")); }
    catch (...) { recording.Fail(Error::Allocation); }
}
void Damage(unsigned object, DamageList const& damage) noexcept {
    if (!SessionValid()) return;
    // All reports delivered to this client are retained: a hit on a former target
    // must not disappear just because selection changed while the projectile flew.
    try {
        std::string entries = "[";
        for (auto const& e : damage.Entries) {
            if (entries.size() > 1) entries += ',';
            entries += Json().Num("subobject", e.SubObjId).Num("remaining_hp", e.HitPts)
                .Num("fate", static_cast<int>(e.Fate)).Str();
        }
        Emit("damage_report", Json().Num("object", object).Num("inflictor", damage.get_inflictor_id())
            .Num("inflictor_owner", damage.get_inflictor_owner_player())
            .Num("cause", static_cast<int>(damage.get_cause())).Bool("destroyed", damage.is_destroyed())
            .Raw("entries", entries + ']'));
    } catch (...) { recording.Fail(Error::Allocation); }
}
void Collision(unsigned a, unsigned b, unsigned short partA, unsigned short partB,
               Vector const& point, Vector const& normal, Vector const& relativeVelocity) noexcept {
    if (!SessionValid()) return;
    try {
        Emit("collision", Json().Num("object_a", a).Num("object_b", b)
            .Num("part_a", partA).Num("part_b", partB).Raw("point_world", Vec(point))
            .Raw("normal_as_delivered_to_b", Vec(normal))
            .Raw("relative_velocity_as_delivered_to_b", Vec(relativeVelocity)));
    } catch (...) { recording.Fail(Error::Allocation); }
}
}
