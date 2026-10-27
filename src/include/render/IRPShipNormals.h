#pragma once
#include "dacom.h"
#include <string>
// Separate object scope: shared textures on ordinary NPCs must remain unchanged.
// Enabled: 0 = off, 1 = player, otherwise nearby-object range in metres.
struct IRPShipNormals : IDAComponent
{
    virtual GENRESULT DACOM_API SetShipNormalScope(unsigned long Enabled, const char* Model = nullptr) = 0;
};
inline bool ShipNormalSolarModel(const char* Model)
{
    if (!Model) return false;
    std::string Path(Model);
    for (char& C : Path)
    {
        if (C == '\\') C = '/';
        else if (C >= 'A' && C <= 'Z') C += 'a' - 'A';
    }
    // Full hulls, including pirate variants and Osiris. A nav_battleship icon
    // also labels liners, gunboats and debris, so it is not an eligibility test.
    if (Path.compare(0, 6, "ships/") != 0 || Path.find("nmd") != std::string::npos ||
        Path.find("nomad") != std::string::npos) return false;
    const std::string File = Path.substr(Path.find_last_of('/') + 1);
    for (const char* Suffix : {"_battleship.cmp", "_dreadnought.cmp", "_osiris.cmp"})
    {
        const size_t Length = std::char_traits<char>::length(Suffix);
        if (File.size() > Length && File.compare(File.size() - Length, Length, Suffix) == 0)
            return true;
    }
    return false;
}
inline bool ShipNormalTransportModel(const char* Model)
{
    if (!Model) return false;
    std::string Path(Model);
    for (char& C : Path) { if (C == '\\') C = '/'; else if (C >= 'A' && C <= 'Z') C += 'a' - 'A'; }
    // Content uses FIGHTER for the small transport and FREIGHTER for the armored one.
    return Path == "ships/utility/transport_small/transport_small.cmp" ||
        Path == "ships/utility/transport_armored/transport_armored_beta1.cmp";
}
inline bool ShipNormalEligible(unsigned ObjectType, bool Player, const char* Model = nullptr)
{
    if (Player || (ObjectType & (0x200000u | 0x80000u | 0x40000u | 0x100000u)) != 0) return true; // CAPITAL / CRUISER / GUNBOAT / TRANSPORT
    if ((ObjectType & (0x10000u | 0x20000u)) && ShipNormalTransportModel(Model)) return true;
    if (!Model || (ObjectType & (0x100u | 0x10u | 0x8000u | 0x4000u | 0x1000u | 0x2000u |
        0x20u | 0x40u | 0x80u | 0x400u | 0x800u)) == 0) return false;
    if (ShipNormalSolarModel(Model)) return true;
    std::string Path(Model);
    for (char& C : Path) { if (C == '\\') C = '/'; else if (C >= 'A' && C <= 'Z') C += 'a' - 'A'; }
    // Actual human solar membership is checked against the content manifest by RP9.
    for (const char* Word : {"nomad", "nmd", "dyson", "lair", "asteroid"})
        if (Path.find(Word) != std::string::npos) return false;
    return Path.compare(0,6,"solar/") == 0 || Path == "ships/utility/mining/mining.cmp" ||
        Path == "ships/utility/mining/mining_with_panels.cmp";
}
inline unsigned ShipNormalScope(unsigned Type, bool Player, const char* Model, bool Dockable, float SurfaceDistance)
{
    if (!ShipNormalEligible(Type,Player,Model)) return 0;
    if (Player) return 1;
    unsigned Range = Dockable || (Type & (0x80000u | 0x40000u | 0x100000u)) ||
        ShipNormalTransportModel(Model) ? 200u : 100u;
    if ((Type & 0x200000u) || ShipNormalSolarModel(Model)) Range = 400u;
    if (Model)
    {
        std::string Path(Model);
        for (char& C : Path) { if (C == '\\') C = '/'; else if (C >= 'A' && C <= 'Z') C += 'a' - 'A'; }
        // Full station models only; their detached parts keep the ordinary range.
        for (const char* Station : {"solar/dockable/station_large_a_lod.cmp",
            "solar/dockable/station_large_b_lod.cmp", "solar/dockable/station_small_a_lod.cmp",
            "solar/dockable/station_small_b_lod.cmp", "solar/dockable/station_small_b_lod_tgk.cmp",
            "solar/dockable/trading_outpost_lod.cmp"})
            if (Path == Station) { Range = 500u; break; }
    }
    return SurfaceDistance < float(Range) ? Range : 0u;
}
