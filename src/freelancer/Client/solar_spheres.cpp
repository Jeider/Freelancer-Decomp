#include "solar_spheres.h"

#include "client_gameobj.h"
#include "client_objdb.h"
#include "common_archetype.h"
#include "engine_light.h"
#include "globals.h" // GetClientElapsedTime
#include "port_config.h"
#include "texture_panels.h"

#include <algorithm>
#include <cmath>
#include <vector>

bool SolarSphere(FClientGameobj* Go, float* Out)
{
    if (Go == nullptr || Go->Object == nullptr)
        return false;
    Vector Center;
    float Radius = Go->Slot178(Center);
    auto* Arch = static_cast<Archetype::Solar*>(Go->Object->get_archetype());
    if (Arch != nullptr && Arch->SolarRadius > 0 && std::isfinite(Arch->SolarRadius))
    {
        Radius = Arch->SolarRadius;
        Center = Go->get_position();
    }
    if (!(Radius > 0) || !std::isfinite(Radius))
        return false;
    Out[0] = Center.x;
    Out[1] = Center.y;
    Out[2] = Center.z;
    Out[3] = Radius;
    return true;
}

bool FindSystemSunSphere(float* Out)
{
    int const SolarKind = 2;
    for (FClientGameobj* Solar = ClientObjDb_GetKindHead(&SolarKind); Solar != nullptr; Solar = Solar->ListNext)
    {
        unsigned Type = 0;
        Solar->get_type(Type);
        if ((Type & 4u) != 0 && SolarSphere(Solar, Out))
            return true;
    }
    return false;
}

bool FindHostPlanetSphere(const float* Centre, float MaxDistance, float* Out)
{
    return FindNearestPlanetSphere(Centre, MaxDistance, nullptr, Out);
}

bool FindNearestPlanetSphere(const float* Centre, float MaxDistance, const float* Exclude, float* Out)
{
    int const SolarKind = 2;
    float BestDistance = MaxDistance;
    bool bFound = false;
    for (FClientGameobj* Solar = ClientObjDb_GetKindHead(&SolarKind); Solar != nullptr; Solar = Solar->ListNext)
    {
        unsigned Type = 0;
        Solar->get_type(Type);
        float Sphere[4];
        if ((Type & 3u) == 0 || !SolarSphere(Solar, Sphere))
            continue;
        if (Exclude != nullptr && std::fabs(Sphere[0] - Exclude[0]) < 1.0f && std::fabs(Sphere[1] - Exclude[1]) < 1.0f &&
            std::fabs(Sphere[2] - Exclude[2]) < 1.0f)
            continue;
        float const Dx = Sphere[0] - Centre[0], Dy = Sphere[1] - Centre[1], Dz = Sphere[2] - Centre[2];
        float const Distance = std::sqrt(Dx * Dx + Dy * Dy + Dz * Dz);
        if (Distance <= BestDistance)
        {
            BestDistance = Distance;
            for (int I = 0; I < 4; ++I)
                Out[I] = Sphere[I];
            bFound = true;
        }
    }
    return bFound;
}

bool FindSunLightColour(const float* SunCentre, const float* At, float* Out)
{
    FGameLight* Best = nullptr;
    float BestDistance = 0.0f;
    for (FGameLight* Light = GameLightListHead(); Light != nullptr; Light = Light->ListNext)
    {
        // Enabled, and not an ambient light (Type -2).
        if ((Light->Flags & 8u) == 0 || Light->Type == -2)
            continue;
        float const Dx = Light->Position[0] - SunCentre[0], Dy = Light->Position[1] - SunCentre[1],
                    Dz = Light->Position[2] - SunCentre[2];
        float const Distance = Dx * Dx + Dy * Dy + Dz * Dz;
        if (Best == nullptr || Distance < BestDistance)
        {
            Best = Light;
            BestDistance = Distance;
        }
    }
    if (Best == nullptr)
        return false;
    float const Dx = At[0] - Best->Position[0], Dy = At[1] - Best->Position[1], Dz = At[2] - Best->Position[2];
    EngineLightGetEffectiveColor(Best, std::sqrt(Dx * Dx + Dy * Dy + Dz * Dz), Out);
    return true;
}

namespace
{
    // The outer radius of the ring (loaded TexturePanels) that belongs to the planet at Centre /
    // Radius -- its zone sits within Radius of the planet's centre -- or 0.
    float RingOuterFor(const float* Centre, float Radius)
    {
        FTexturePanelsGlobalNode* const Sentinel = TexturePanelsListSentinel();
        for (FTexturePanelsGlobalNode* Node = Sentinel->Next; Node != Sentinel; Node = Node->Next)
        {
            FTexturePanels const* const Panels = Node->Panels;
            if (Panels == nullptr || Panels->bLoaded == 0 || Panels->Zone == nullptr)
                continue;
            Vector const& Pos = Panels->Zone->GetPos();
            float const Dx = Pos.x - Centre[0], Dy = Pos.y - Centre[1], Dz = Pos.z - Centre[2];
            if (Dx * Dx + Dy * Dy + Dz * Dz > Radius * Radius)
                continue;
            float const Outer = Panels->Zone->GetSize().x;
            if (Outer > Radius && std::isfinite(Outer))
                return Outer;
        }
        return 0.0f;
    }

    float ShadowReachFor(float Radius, float RingOuter)
    {
        float const Default = PortConfigFloat("Render", "shadow_max_length", 200.0f);
        if (!(RingOuter > 0.0f))
            return Default;
        return (std::max)(Default, (RingOuter - Radius) * 1.15f + 500.0f);
    }

    struct FPlanetShadow
    {
        float Centre[3];
        float Radius;
        float Reach;
    };
}

float SolarRingShadowReach(const float* Centre, float Radius)
{
    float const Outer = RingOuterFor(Centre, Radius);
    return Outer > 0.0f ? ShadowReachFor(Radius, Outer) : 0.0f;
}

bool SolarNearBody(const float* Position, float Scale, float Pad, const float* HostAt)
{
    static std::vector<float> S_Bodies; // xyz, radius (negative: the sun)
    static double S_Time = -1.0;
    double const Now = GetClientElapsedTime();
    if (Now != S_Time)
    {
        S_Time = Now;
        S_Bodies.clear();
        int const SolarKind = 2;
        for (FClientGameobj* Solar = ClientObjDb_GetKindHead(&SolarKind); Solar != nullptr; Solar = Solar->ListNext)
        {
            unsigned Type = 0;
            Solar->get_type(Type);
            float Sphere[4];
            // Planets and moons (bits 1|2) and the sun (4, as FindSystemSunSphere tests).
            if ((Type & 7u) == 0 || !SolarSphere(Solar, Sphere))
                continue;
            if ((Type & 4u) != 0)
                Sphere[3] = -Sphere[3];
            S_Bodies.insert(S_Bodies.end(), Sphere, Sphere + 4);
        }
    }
    for (size_t I = 0; I + 3 < S_Bodies.size(); I += 4)
    {
        bool const bSun = S_Bodies[I + 3] < 0.0f;
        if (!bSun && HostAt != nullptr && std::fabs(S_Bodies[I] - HostAt[0]) < 1.0f &&
            std::fabs(S_Bodies[I + 1] - HostAt[1]) < 1.0f && std::fabs(S_Bodies[I + 2] - HostAt[2]) < 1.0f)
            continue;
        double const Dx = (double)Position[0] - S_Bodies[I], Dy = (double)Position[1] - S_Bodies[I + 1],
                     Dz = (double)Position[2] - S_Bodies[I + 2];
        double const Reach = std::fabs((double)S_Bodies[I + 3]) * Scale + Pad;
        if (Dx * Dx + Dy * Dy + Dz * Dz < Reach * Reach)
            return true;
    }
    return false;
}

namespace
{
    std::vector<FPlanetShadow> G_ShadowPlanets;
    float G_ShadowSun[4];
    bool G_bShadowSun = false;

    // The frame's sun and shadow casting planets (planets and moons with their shadow reach),
    // rebuilt once per client time step; shared by SolarSunlitAt and SolarShadowCasters.
    void RefreshShadowPlanets()
    {
        static double S_Time = -1.0;
        double const Now = GetClientElapsedTime();
        if (Now == S_Time)
            return;
        S_Time = Now;
        G_ShadowPlanets.clear();
        G_bShadowSun = FindSystemSunSphere(G_ShadowSun);
        if (!G_bShadowSun)
            return;
        int const SolarKind = 2;
        for (FClientGameobj* Solar = ClientObjDb_GetKindHead(&SolarKind); Solar != nullptr; Solar = Solar->ListNext)
        {
            unsigned Type = 0;
            Solar->get_type(Type);
            float Sphere[4];
            if ((Type & 3u) == 0 || !SolarSphere(Solar, Sphere))
                continue;
            FPlanetShadow Planet;
            Planet.Centre[0] = Sphere[0];
            Planet.Centre[1] = Sphere[1];
            Planet.Centre[2] = Sphere[2];
            Planet.Radius = Sphere[3];
            Planet.Reach = ShadowReachFor(Sphere[3], RingOuterFor(Planet.Centre, Sphere[3]));
            // A planet_eclipses caster reaches its receiver (and its ring), as on the ships.
            Planet.Reach = (std::max)(Planet.Reach, PlanetEclipseCasterReach(Solar));
            G_ShadowPlanets.push_back(Planet);
        }
    }
}

int SolarShadowCasters(const float* At, float MaxDistance, float* OutSphere, float* OutReach, int Max)
{
    RefreshShadowPlanets();
    if (!G_bShadowSun || Max <= 0)
        return 0;
    struct FPick
    {
        double Distance;
        FPlanetShadow const* Planet;
    };
    std::vector<FPick> Picks;
    for (FPlanetShadow const& Planet : G_ShadowPlanets)
    {
        double const Dx = (double)Planet.Centre[0] - At[0], Dy = (double)Planet.Centre[1] - At[1],
                     Dz = (double)Planet.Centre[2] - At[2];
        double const Distance = std::sqrt(Dx * Dx + Dy * Dy + Dz * Dz);
        if (Distance - Planet.Radius > MaxDistance)
            continue;
        FPick Pick = {Distance, &Planet};
        Picks.push_back(Pick);
    }
    std::sort(Picks.begin(), Picks.end(), [](FPick const& A, FPick const& B) { return A.Distance < B.Distance; });
    int Count = 0;
    for (FPick const& Pick : Picks)
    {
        if (Count >= Max)
            break;
        OutSphere[Count * 4 + 0] = Pick.Planet->Centre[0];
        OutSphere[Count * 4 + 1] = Pick.Planet->Centre[1];
        OutSphere[Count * 4 + 2] = Pick.Planet->Centre[2];
        OutSphere[Count * 4 + 3] = Pick.Planet->Radius;
        OutReach[Count] = Pick.Planet->Reach;
        ++Count;
    }
    return Count;
}

float SolarSunlitAt(const float* Position)
{
    RefreshShadowPlanets();
    std::vector<FPlanetShadow> const& S_Planets = G_ShadowPlanets;
    float const* const S_Sun = G_ShadowSun;
    bool const S_bSun = G_bShadowSun;
    if (!S_bSun)
        return 1.0f;

    float const ToSun[3] = {S_Sun[0] - Position[0], S_Sun[1] - Position[1], S_Sun[2] - Position[2]};
    float const SunDistance = std::sqrt(ToSun[0] * ToSun[0] + ToSun[1] * ToSun[1] + ToSun[2] * ToSun[2]);
    if (!(SunDistance > 1.0f))
        return 1.0f;
    float const D[3] = {ToSun[0] / SunDistance, ToSun[1] / SunDistance, ToSun[2] / SunDistance};

    float Lit = 1.0f;
    for (FPlanetShadow const& Planet : S_Planets)
    {
        float const R = Planet.Radius;
        float const ToC[3] = {Planet.Centre[0] - Position[0], Planet.Centre[1] - Position[1],
                              Planet.Centre[2] - Position[2]};
        float const Along = ToC[0] * D[0] + ToC[1] * D[1] + ToC[2] * D[2];
        if (Along <= 0.0f)
            continue;
        float const Q[3] = {ToC[0] - D[0] * Along, ToC[1] - D[1] * Along, ToC[2] - D[2] * Along};
        float const Perp2 = Q[0] * Q[0] + Q[1] * Q[1] + Q[2] * Q[2];
        float const Gap = Along - std::sqrt((std::max)(R * R - (std::min)(Perp2, R * R), 0.0f));
        if (Gap > Planet.Reach)
            continue;
        float const Perp = std::sqrt(Perp2);
        float const Edge = (std::max)(50.0f, Along * S_Sun[3] / SunDistance);
        float T = (Perp - (R - Edge)) / (2.0f * Edge);
        T = T < 0.0f ? 0.0f : (T > 1.0f ? 1.0f : T);
        float const Occlusion = 1.0f - T * T * (3.0f - 2.0f * T);
        Lit *= 1.0f - Occlusion;
    }
    return Lit;
}
