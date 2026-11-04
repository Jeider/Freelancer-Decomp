#include "server_asteroid_fields.h"
#include "../include/server_sysdb.h"
#include "../include/server_gameobject.h"
#include "../include/server_createinfo.h"
#include "../include/common_archetype.h"
#include "../include/common_cobject.h"
#include "../include/common_id.h"
#include "../include/common_ini.h"
#include "../include/common_universe.h"
#include "../include/common_physys.h"
#include "../include/common_server_asteroid.h"
#include "../include/common_casteroid.h"
#include "../include/common_misc.h"
#include "../include/common_server_playerdb.h"
#include "../include/DALib.h"
#include "../include/dacom.h"
#include "../include/runtime_hitch_log.h"
#include <algorithm>
#include <cmath>
#include <random>
#include <string>
#include <vector>
#include <map>
#include <memory>

namespace {
struct Field {
    unsigned archetype = 0;
    unsigned seed = 1;
    int count = 0;
    float radius = 3000.0f;
    float speed = 10.0f;
    float spin = 0.1f;
    float bandThickness = 0.0f;
    bool fromPlayer = false;
    bool forwardFormation = false;
    float offset = 200.0f;
    float despawnRadius = 0.0f;
};

struct RockState {
    unsigned id = 0;
    bool dead = false;
    Vector pos{}, velocity{}, spin{};
    Quaternion orientation{1.0f, 0.0f, 0.0f, 0.0f};
    int hitPoints = -1;
};
struct PlayerField {
    Field settings;
    Universe::IZone const* zone = nullptr;
    std::vector<Universe::IZone const*> exclusions;
    std::vector<Universe::IZone const*> lootZones;
    std::vector<RockState> rocks;
    std::mt19937 rng;
    bool errorReported = false;
    float modelRadius = 0.0f;
    std::shared_ptr<Archetype::Solar> loadedArch;
    struct FormationAnchor { Vector position{}; bool pending = true; };
    std::map<unsigned, FormationAnchor> anchors;
};
struct Population {
    std::vector<PlayerField> fields;
    float elapsed = 0.5f;
    int fixedCount = 0;
    float viewRadius = 0.0f;
};
std::map<StarSystem*, Population> Populations;

float DistanceSquared(Vector const& a, Vector const& b) {
    float x=a.x-b.x, y=a.y-b.y, z=a.z-b.z;
    return x*x+y*y+z*z;
}
Vector BandNormal(Universe::IZone const& zone) {
    auto const& m = zone.GetOrientation();
    return Vector{m.E[0][1], m.E[1][1], m.E[2][1]};
}
void ProjectToBand(Vector& value, Vector const& normal, float height) {
    float delta = height - (value.x*normal.x + value.y*normal.y + value.z*normal.z);
    value.x += normal.x*delta;
    value.y += normal.y*delta;
    value.z += normal.z*delta;
}
bool NearAny(Vector const& pos, std::vector<Vector> const& players, float radius) {
    for (auto const& p : players) if (DistanceSquared(pos,p)<=radius*radius) return true;
    return false;
}

// IDs are looked up each tick: destruction never leaves a retained raw pointer.
// Far objects keep their state in memory; death records keep a cleared area empty.
void Capture(RockState& state, GameObject* obj) {
    auto* solar = static_cast<CSolar*>(obj->cobj());
    state.pos = obj->get_position();
    state.velocity = solar->get_velocity();
    state.spin = PhySys::GetAngularVelocityOS(solar);
    Server_MatrixToQuat(state.orientation, solar->Orientation);
    state.hitPoints = (std::max)(1, static_cast<int>(solar->get_hit_pts()));
}

bool CreateRock(StarSystem& system, Archetype::Solar* arch, Field const& field, RockState& state) {
    RuntimeHitchScope Hitch("asteroids", "server create rock");
    auto* ids = CFLIDMaker::GetInstance();
    if (!ids) return false;
    CSolarCreateInfo info;
    info.Field_0xb4 = 0;
    info.Field_0xbc = 0;
    info.ObjId = ids->AllocateObjectID();
    info.Field_0xb8.Id = info.ObjId;
    info.ArchetypeNickname = field.archetype;
    // Carry the authored contents through the normal create packet so both the
    // server and clients see the same equipment/cargo (including valuable ore).
    info.Field_0x6c = arch->Loadout.Id;
    info.Position = state.pos;
    info.Orientation = state.orientation;
    info.HitPts = state.hitPoints;
    info.Field_0xac = 1;
    info.Field_0xad = 1;
    arch->get_undamaged_collision_group_list(info.CollisionGroups);
    Solar* created = system.create_solar(info);
    if (!created) return false;
    state.id = info.ObjId;
    system.remove_from_list_d4(created);
    system.add_to_list_d4(created);
    PhySys::AddToVelocity(created->cobj(), state.velocity);
    PhySys::AddToAngularVelocityOS(created->cobj(), state.spin);
    return true;
}

float ModelRadius(Archetype::Solar* arch) {
    float radius = 10.0f;
    Vector centre{};
    long instance = arch->create_instance(nullptr);
    if (instance != -1) {
        DALib::Engine->GetInstanceExtent(reinterpret_cast<void*>(instance), 0, &radius, &centre.x);
        DALib::Engine->DestroyInstance(reinterpret_cast<void*>(instance));
    }
    radius += std::sqrt(DistanceSquared(centre, Vector{}));
    return std::isfinite(radius) && radius >= 1.0f ? radius : 10.0f;
}

bool ValidPlacement(Universe::IZone const& zone,
                    std::vector<Universe::IZone const*> const& exclusions,
                    Vector const& pos, float radius) {
    if (zone.GetImmersion(pos) <= 0.001) return false;
    for (auto* exclusion : exclusions) if (exclusion->InZone(pos, radius)) return false;
    CObject* overlaps[1];
    return PhySys::FindSphereCollisions(zone.GetSystem(), pos, radius*1.5f, overlaps, 1) == 0;
}

Vector RandomVector(std::mt19937& rng) {
    auto unit = [&]() { return static_cast<float>(rng() >> 8) / 16777216.0f; };
    return Vector{unit()*2-1, unit()*2-1, unit()*2-1};
}
Vector RandomVelocity(std::mt19937& rng, float maxSpeed) {
    Vector v = RandomVector(rng);
    float scale = maxSpeed / (std::max)(1.0f, std::sqrt(DistanceSquared(v, Vector{})));
    return Vector{v.x*scale,v.y*scale,v.z*scale};
}

float Bounded(INI_Reader& reader, float fallback, float lo, float hi) {
    float value = reader.get_value_float(0);
    return std::isfinite(value) ? (std::max)(lo, (std::min)(hi, value)) : fallback;
}

void Populate(StarSystem& system, Universe::IZone const& zone, Field const& field,
              std::vector<Universe::IZone const*> const& exclusions, int& budget) {
    Archetype::Solar* arch = Archetype::GetSolar(field.archetype);
    if (!arch || !IsServerAsteroidType(arch->ObjectType)) {
        FDUMP(0x100001, "ServerDynamicAsteroids: archetype %u must be a Solar of type SERVER_ASTEROID", field.archetype);
        return;
    }
    CFLIDMaker* ids = CFLIDMaker::GetInstance();
    if (!ids) return;
    // load() returns false for an already loaded archetype too, but always
    // acquires a reference. Check the resulting state instead of its return.
    arch->load();
    if (!arch->is_loaded()) {
        FDUMP(0x100001, "ServerDynamicAsteroids: could not load archetype %u", field.archetype);
        arch->Release();
        return;
    }
    float rockRadius = 10.0f;
    Vector boundCentre{};
    long instance = arch->create_instance(nullptr);
    if (instance != -1) {
        DALib::Engine->GetInstanceExtent(reinterpret_cast<void*>(instance), 0, &rockRadius, &boundCentre.x);
        DALib::Engine->DestroyInstance(reinterpret_cast<void*>(instance));
    }
    rockRadius += std::sqrt(boundCentre.x*boundCentre.x + boundCentre.y*boundCentre.y + boundCentre.z*boundCentre.z);
    if (!std::isfinite(rockRadius) || rockRadius < 1.0f) rockRadius = 10.0f;
    std::mt19937 rng(field.seed ^ zone.GetId());
    auto unit = [&]() { return static_cast<float>(rng() >> 8) / 16777216.0f; };
    auto vector = [&]() { return Vector{unit()*2.0f-1.0f, unit()*2.0f-1.0f, unit()*2.0f-1.0f}; };
    float radius = (std::min)(field.radius, zone.GetRadius());
    int spawned = 0;
    for (int n = 0; n < field.count && budget > 0; ++n) {
        Vector pos{};
        bool placed = false;
        for (int attempt = 0; attempt < 1024 && !placed; ++attempt) {
            Vector offset = vector();
            if (offset.x*offset.x + offset.y*offset.y + offset.z*offset.z > 1.0f) continue;
            Vector const& centre = zone.GetPos();
            pos = Vector{centre.x+offset.x*radius, centre.y+offset.y*radius, centre.z+offset.z*radius};
            if (zone.GetImmersion(pos) <= 0.001) continue;
            bool excluded = false;
            for (auto* exclusion : exclusions)
                if (exclusion->InZone(pos, rockRadius)) { excluded = true; break; }
            if (excluded) continue;
            CObject* overlaps[1];
            if (PhySys::FindSphereCollisions(zone.GetSystem(), pos, rockRadius*1.5f, overlaps, 1)) continue;
            placed = true;
        }
        if (!placed) {
            FDUMP(0x100002, "ServerDynamicAsteroids: no clear spawn point in zone %u", zone.GetId());
            break;
        }
        CSolarCreateInfo info;
        info.Field_0xb4 = 0;
        info.Field_0xbc = 0;
        info.ObjId = ids->AllocateObjectID();
        info.Field_0xb8.Id = info.ObjId;
        info.ArchetypeNickname = field.archetype;
        info.Position = pos;
        info.Orientation.w = 1.0f;
        info.Orientation.x = info.Orientation.y = info.Orientation.z = 0.0f;
        info.HitPts = -1;
        info.Field_0xac = 1;
        info.Field_0xad = 1;
        arch->get_undamaged_collision_group_list(info.CollisionGroups);
        Solar* created = system.create_solar(info);
        if (!created) continue;
        // Include this moving solar in the regular tick even outside ship
        // proximity. It must not retain a stale position in the solar BSP.
        system.remove_from_list_d4(created);
        system.add_to_list_d4(created);
        Vector velocity = vector(), spin = vector();
        // max_velocity / max_angular_velocity are vector magnitude limits.
        auto scale = [](Vector v, float limit) {
            float length = std::sqrt(v.x*v.x+v.y*v.y+v.z*v.z);
            float factor = limit / (std::max)(1.0f, length);
            return Vector{v.x*factor, v.y*factor, v.z*factor};
        };
        PhySys::AddToVelocity(created->cobj(), scale(velocity, field.speed));
        PhySys::AddToAngularVelocityOS(created->cobj(), scale(spin, field.spin));
        --budget;
        ++spawned;
    }
    FDUMP(0x100004, "ServerDynamicAsteroids: zone %u archetype %u spawned %d of %d",
          zone.GetId(), field.archetype, spawned, field.count);
    arch->Release();
}

void UpdatePlayerFields(StarSystem& system, std::vector<Vector> const& players, float dt,
                        std::vector<Vector> const& velocities = {}, std::vector<unsigned> const& playerIds = {}) {
    auto found = Populations.find(&system);
    if (found == Populations.end() || !std::isfinite(dt) || dt <= 0) return;
    auto& population = found->second;
    population.elapsed += dt;
    bool const forwardMode = std::any_of(population.fields.begin(), population.fields.end(),
        [](PlayerField const& field) { return field.settings.forwardFormation; });
    if (population.elapsed < (forwardMode ? 0.05f : 0.25f)) return;
    population.elapsed = 0;
    int active = population.fixedCount;
    // Refresh authoritative positions before counting either player's population.
    // Hysteresis uses ALL players: one player leaving cannot remove another's rocks.
    for (auto& field : population.fields) {
        for (auto& state : field.rocks) {
            if (!state.id) continue;
            GameObject* obj = Server_LookupGameObject(state.id);
            if (!obj || obj->is_destroyed()) {
                state.id = 0;
                state.dead = true;
                continue;
            }
            Capture(state, obj);
            if (!NearAny(state.pos, players, field.settings.despawnRadius) && obj->destroy(0, 0))
                state.id = 0; // suspended, not killed; HP/transform were captured above
            else ++active;
        }
    }
    int spawnBudget = (std::min)(24, 1024-active);
    int formationBudget = 4; // Spread distant creation over frames, rather than bursts of 24.
    for (auto& field : population.fields) {
        Field const& f = field.settings;
        if (spawnBudget <= 0 || (f.forwardFormation && formationBudget <= 0) || players.empty() || field.errorReported) continue;
        bool relevant = false;
        for (auto const& player : players)
            if (field.zone->InZone(player, f.radius)) { relevant = true; break; }
        if (!relevant) continue;
        auto countNear = [&](Vector const& p) {
            int count = 0;
            for (auto const& state : field.rocks)
                if (DistanceSquared(state.pos,p) <= f.radius*f.radius) ++count;
            return count;
        };
        bool needsObjects = false;
        for (auto const& state : field.rocks)
            if (!state.id && !state.dead && NearAny(state.pos, players, f.radius+200.0f)) { needsObjects = true; break; }
        for (size_t i=0; i<players.size(); ++i) {
            auto const& player = players[i];
            if (!field.zone->InZone(player, f.radius)) continue;
            if (f.forwardFormation) {
                unsigned id = i<playerIds.size() ? playerIds[i] : static_cast<unsigned>(i+1);
                auto inserted = field.anchors.emplace(id, PlayerField::FormationAnchor{player, true});
                auto& anchor = inserted.first->second;
                float const step = (std::max)(100.0f, f.radius*0.05f);
                if (DistanceSquared(player, anchor.position) >= step*step) {
                    anchor.position = player;
                    anchor.pending = true;
                }
                if (!anchor.pending) continue;
                if (countNear(player) >= f.count) {
                    anchor.pending = false;
                    continue;
                }
            }
            if (countNear(player) < f.count) needsObjects = true;
        }
        if (!needsObjects) continue;
        if (!field.loadedArch) {
            auto* arch = Archetype::GetSolar(f.archetype);
            if (!arch || !IsServerAsteroidType(arch->ObjectType)) {
                FDUMP(0x100001, "ServerDynamicAsteroids: invalid player field archetype %u", f.archetype);
                field.errorReported = true;
                continue;
            }
            arch->load();
            if (!arch->is_loaded()) {
                arch->Release();
                field.errorReported = true;
                FDUMP(0x100001, "ServerDynamicAsteroids: cannot load player field archetype %u", f.archetype);
                continue;
            }
            // Retain while the system is loaded: exclusions must not cause the
            // same mesh/SUR to be loaded and released every half second.
            field.loadedArch = std::shared_ptr<Archetype::Solar>(arch, [](Archetype::Solar* p) { p->Release(); });
        }
        auto* arch = field.loadedArch.get();
        // Re-entering an area restores surviving rocks before generating new ones.
        for (auto& state : field.rocks) {
            if (spawnBudget <= 0 || (f.forwardFormation && formationBudget <= 0)) break;
            if (!state.id && !state.dead && NearAny(state.pos, players, f.radius+200.0f) &&
                CreateRock(system, arch, f, state)) {
                --spawnBudget;
                if (f.forwardFormation) --formationBudget;
            }
        }
        if (field.modelRadius == 0.0f) field.modelRadius = ModelRadius(arch);
        float rockRadius = field.modelRadius;
        for (size_t i=0; i<players.size(); ++i) {
            auto const& player = players[i];
            if (!field.zone->InZone(player, f.radius)) continue;
            PlayerField::FormationAnchor* anchor = nullptr;
            if (f.forwardFormation) {
                unsigned id = i<playerIds.size() ? playerIds[i] : static_cast<unsigned>(i+1);
                anchor = &field.anchors.at(id);
                if (!anchor->pending) continue;
            }
            int missing = f.count-countNear(player);
            Vector const velocity = i<velocities.size() ? velocities[i] : Vector{};
            bool const moving = DistanceSquared(velocity, Vector{}) > 1.0f;
            while (missing > 0 && spawnBudget > 0 && (!f.forwardFormation || formationBudget>0) && field.rocks.size() < 8192) {
                RockState state;
                bool placed = false;
                for (int attempt = 0; attempt < 256 && !placed; ++attempt) {
                    Vector offset = RandomVector(field.rng);
                    if (DistanceSquared(offset,Vector{}) > 1.0f) continue;
                    if (f.forwardFormation && moving && offset.x*velocity.x+offset.y*velocity.y+offset.z*velocity.z <= 0.0f) continue;
                    state.pos = Vector{player.x+offset.x*f.radius, player.y+offset.y*f.radius, player.z+offset.z*f.radius};
                    if (f.bandThickness > 0.0f) {
                        Vector const& centre = field.zone->GetPos();
                        Vector local{state.pos.x-centre.x, state.pos.y-centre.y, state.pos.z-centre.z};
                        ProjectToBand(local, BandNormal(*field.zone), RandomVector(field.rng).y*f.bandThickness);
                        state.pos = Vector{centre.x+local.x, centre.y+local.y, centre.z+local.z};
                        // Projection may move outside the ship's sphere or behind its velocity.
                        if (DistanceSquared(state.pos, player) > f.radius*f.radius) continue;
                        if (f.forwardFormation && moving &&
                            (state.pos.x-player.x)*velocity.x + (state.pos.y-player.y)*velocity.y +
                            (state.pos.z-player.z)*velocity.z <= 0.0f) continue;
                    }
                    float const inner = f.forwardFormation ? (std::max)(f.offset, f.radius*0.85f) : f.offset;
                    if (NearAny(state.pos, players, inner+rockRadius)) continue;
                    // Overlapping player bubbles share the same population.
                    bool full = false;
                    for (auto const& other : players) {
                        if (DistanceSquared(state.pos,other) <= f.radius*f.radius && countNear(other) >= f.count) {
                            full = true; break;
                        }
                    }
                    if (full || !ValidPlacement(*field.zone, field.exclusions, state.pos, rockRadius)) continue;
                    placed = true;
                }
                if (!placed) {
                    if (anchor) anchor->pending = false; // Retry after travel, not every frame in an exclusion.
                    break;
                }
                state.velocity = RandomVelocity(field.rng, f.speed);
                if (f.bandThickness > 0.0f) ProjectToBand(state.velocity, BandNormal(*field.zone), 0.0f);
                state.spin = RandomVelocity(field.rng, f.spin);
                if (!CreateRock(system, arch, f, state)) break;
                field.rocks.push_back(state);
                if (field.rocks.size() == 1)
                    FDUMP(0x100004, "ServerDynamicAsteroids: player population started, zone %u arch %u ship=(%.0f %.0f %.0f) count=%d radius=%.0f",
                          field.zone->GetId(), f.archetype, player.x, player.y, player.z, f.count, f.radius);
                --missing;
                --spawnBudget;
                if (f.forwardFormation) --formationBudget;
            }
            if (anchor && missing<=0) anchor->pending = false;
        }
    }
}

void LoadField(StarSystem& system, char const* file, Universe::IZone const& zone, int& budget) {
    char path[1024];
    GetFileSysPath(path, file, DALib::Data);
    INI_Reader reader;
    if (!reader.open(path, false)) {
        FDUMP(0x100002, "ServerDynamicAsteroids: cannot open field %s", path);
        return;
    }
    std::vector<Field> fields;
    std::vector<Universe::IZone const*> exclusions;
    std::vector<Universe::IZone const*> lootZones;
    while (reader.read_header()) {
        if (reader.is_header("ServerDynamicAsteroids")) {
            Field f;
            while (reader.read_value()) {
                if (reader.is_value("asteroid")) f.archetype = CreateID(reader.get_value_string());
                else if (reader.is_value("count")) f.count = static_cast<int>(Bounded(reader, 0, 0, 256));
                else if (reader.is_value("placement_radius")) f.radius = Bounded(reader, 3000, 10, 100000);
                else if (reader.is_value("max_velocity")) f.speed = Bounded(reader, 10, 0, 500);
                else if (reader.is_value("max_angular_velocity")) f.spin = Bounded(reader, 0.1f, 0, 10);
                else if (reader.is_value("band_thickness")) f.bandThickness = Bounded(reader, 0, 0, 100000);
                else if (reader.is_value("seed")) f.seed = static_cast<unsigned>(reader.get_value_int(0));
                else if (reader.is_value("spawn_mode")) {
                    f.forwardFormation = _stricmp(reader.get_value_string(), "forward") == 0;
                    f.fromPlayer = f.forwardFormation || _stricmp(reader.get_value_string(), "player") == 0;
                }
                else if (reader.is_value("placement_offset")) f.offset = Bounded(reader, 200, 0, 100000);
                else if (reader.is_value("despawn_radius")) f.despawnRadius = Bounded(reader, 0, 0, 300000);
            }
            // Port tuning: double the authored population while retaining the
            // per-system object budget and bounded per-tick creation work.
            f.count = (std::min)(512, f.count * 2);
            if (f.count > 0 && f.archetype) fields.push_back(f);
        } else if (reader.is_header("LootableZone")) {
            auto* lootZone = &zone;
            while (reader.read_value()) {
                if (reader.is_value("zone"))
                    lootZone = Universe::get_zone(zone.GetSystem(), reader.get_value_string());
            }
            if (lootZone) lootZones.push_back(lootZone);
        } else if (reader.is_header("Exclusion Zones")) {
            while (reader.read_value()) {
                if (reader.is_value("exclusion")) {
                    auto* excluded = Universe::get_zone(zone.GetSystem(), reader.get_value_string());
                    if (excluded) exclusions.push_back(excluded);
                }
            }
        }
    }
    // Common tests named loot zones before the field-wide fallback.
    std::stable_partition(lootZones.begin(), lootZones.end(),
        [&](Universe::IZone const* candidate) { return candidate != &zone; });
    for (auto field : fields) {
        if (!field.fromPlayer) { Populate(system, zone, field, exclusions, budget); continue; }
        field.offset = (std::min)(field.offset, field.radius*(field.forwardFormation ? 0.9f : 0.7f));
        field.despawnRadius = (std::max)(field.despawnRadius, field.radius*(field.forwardFormation ? 1.5f : 2.0f));
        PlayerField runtime;
        runtime.settings = field;
        runtime.zone = &zone;
        runtime.exclusions = exclusions;
        runtime.lootZones = lootZones;
        runtime.rng.seed(field.seed ^ zone.GetId());
        Populations[&system].fields.push_back(std::move(runtime));
        Populations[&system].viewRadius = (std::max)(Populations[&system].viewRadius, field.despawnRadius);
    }
}
}

void OnServerAsteroidKilled(StarSystem& system, unsigned id, Vector const& position) {
    auto found = Populations.find(&system);
    if (found == Populations.end()) return;
    for (auto& field : found->second.fields) {
        for (auto& state : field.rocks) {
            if (state.id != id || state.dead) continue;
            // Mark first: one server death produces at most one loot roll for all clients.
            state.dead = true;
            state.id = 0;
            state.pos = position;
            for (auto* zone : field.lootZones) {
                if (!zone->InZone(position, 0.0f)) continue;
                auto* loot = zone->GetLootableInfo();
                if (!loot || !loot->DynamicLootCommodityId.Id) continue;
                unsigned difficulty = static_cast<unsigned>((std::max)(1, (std::min)(100, loot->DynamicLootDifficulty)));
                if (std::uniform_int_distribution<unsigned>(1, difficulty)(field.rng) != 1) return;
                int maximum = (std::max)(1, loot->DynamicLootCountMax);
                int minimum = (std::max)(1, (std::min)(maximum, loot->DynamicLootCountMin));
                int count = std::uniform_int_distribution<int>(minimum, maximum)(field.rng);
                system.spawn_mined_loot(position, loot->DynamicLootContainerId.Id,
                                       loot->DynamicLootCommodityId.Id, count);
                return;
            }
            return;
        }
    }
}

void LoadServerAsteroidFields(StarSystem& system) {
    Populations.erase(&system);
    char path[1024];
    Universe::get_filename(path, system.SystemInfo->GetFile());
    INI_Reader reader;
    if (!reader.open(path, false)) {
        FDUMP(0x100002, "ServerDynamicAsteroids: cannot open system %s", path);
        return;
    }
    int budget = 1024;
    while (reader.read_header()) {
        if (!reader.is_header("Asteroids")) continue;
        std::string file, zoneName;
        while (reader.read_value()) {
            if (reader.is_value("file")) file = reader.get_value_string();
            else if (reader.is_value("zone")) zoneName = reader.get_value_string();
        }
        if (file.empty() || zoneName.empty()) continue;
        auto* zone = Universe::get_zone(system.SystemInfo->GetId(), zoneName.c_str());
        if (zone) LoadField(system, file.c_str(), *zone, budget);
    }
    auto found = Populations.find(&system);
    if (found != Populations.end()) {
        found->second.fixedCount = 1024-budget;
        FDUMP(0x100004, "ServerDynamicAsteroids: system %u loaded %u player population sections",
              system.SystemInfo->GetId(), static_cast<unsigned>(found->second.fields.size()));
    }
}

void UpdateServerAsteroidFields(StarSystem& system, float dt) {
    if (Populations.find(&system) == Populations.end()) return;
    RuntimeHitchScope Hitch("asteroids", "server population");
    std::vector<Vector> players;
    std::vector<Vector> velocities;
    std::vector<unsigned> playerIds;
    auto* head = static_cast<SystemPlayerNode*>(system.PlayerListHead);
    for (auto* node = head->Next; node != head; node = node->Next) {
        auto* ship = Server_LookupGameObject(Players[node->View.PlayerId].ship_object_id);
        if (ship && !ship->is_destroyed() && ship->cobj()->PhysicsSystemId == system.SystemInfo->GetId()) {
            players.push_back(ship->get_position());
            velocities.push_back(ship->get_velocity());
            playerIds.push_back(node->View.PlayerId);
        }
    }
    UpdatePlayerFields(system, players, dt, velocities, playerIds);
}

void UnloadServerAsteroidFields(StarSystem& system) {
    Populations.erase(&system);
}

float ServerAsteroidViewRadius(StarSystem& system) {
    auto found = Populations.find(&system);
    return found == Populations.end() ? 0.0f : found->second.viewRadius;
}
