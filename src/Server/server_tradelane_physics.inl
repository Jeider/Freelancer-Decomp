// Physical rings use the existing server animation clock and snapshot packet.
// No local cosmetic playback may compete with this script on opted-in rings.
void ActivatePhysicalTradeLane(GameObject* ring, bool active, unsigned shipId)
{
    if (!ring || !ring->cobj() || !shipId ||
        (static_cast<unsigned>(ring->cobj()->ObjectClass) & 0x303u) != 0x303u) return;
    auto* solar = static_cast<CSolar*>(ring->cobj());
    SolarAnimation::RingConfig config;
    if (!solar->is_lane_ring() || !SolarAnimation::GetRingConfig(solar->Archetype, config)) return;
    GameObject* resolved = nullptr; StarSystem* sys = nullptr;
    if (!Server_FindLiveObject(ring->get_id(), resolved, sys) || resolved != ring || !sys) return;
    auto& e = Managers[sys].Objects[ring->get_id()];
    if (e.Object != solar) { e = Entry{}; e.Object = solar; }
    if (!active) { e.RingUsers.erase(shipId); return; }
    auto* ship = Server_LookupGameObject(shipId);
    if (!ship || ship->is_destroyed() || !ship->cobj()) return;
    bool side = false;
    if (ring->get_lane_direction(ship->get_transform(), &side) != 0) return;
    bool const empty = e.RingUsers.empty();
    if (!e.RingUsers.insert(shipId).second || !empty || !e.Finished()) return;
    if (!StartSolarAnimation(ring->get_id(), side ? config.Right : config.Left))
        FDUMP(0x100001, "physical trade lane %u: cannot start animation", ring->get_id());
}
