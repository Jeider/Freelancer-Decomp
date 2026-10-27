# Cosmic anomalies in space games

[Русский](../ru/space_anomalies/games.md) · [Overview](README.md) · [Rendering design](rendering.md)

Checked on 26 October 2026. This compares six games and one visual simulator, not their popularity rankings. Examples are bounded by the cited sources and versions, and do not establish the absence of other objects. Freelancer techniques below are proposals, not claims about proprietary renderer internals.

## Comparison

| Title | Supported examples | Useful design lesson |
|---|---|---|
| Elite Dangerous | Neutron stars and white dwarfs with cones; black holes | Recognition at distance; cones connected to route planning and risk |
| No Man's Sky | Black-hole travel and Endurance's updated effects | Distinct approach and transition stages |
| Outer Wilds | Brittle Hollow's black hole and falling fragments | Distortion integrated with environmental events |
| EVERSPACE, first game | Black holes and nearby resources | A local hazard with a reason to approach |
| EVE Online | Magnetar, Black Hole, Pulsar, Red Giant, Wolf–Rayet, Cataclysmic Variable | Anomaly conditions affect a whole system and ship preparation |
| X4 Tides of Avarice | Recurring Tide and spatial anomalies | Spatial event progression and warning time |
| SpaceEngine | Relativistic objects, lensing, volumetric disks and jets | Geometric reference and explicit performance tradeoffs |

Evidence and scope for each row follow.

The selected game sources do not establish a specific visitable quasar comparable to a normal local level. The quasar proposal therefore combines astrophysical modelling and design techniques rather than claiming an unverified game example.

## Elite Dangerous

**Community evidence:** DSN describes opposing cones around neutron stars and white dwarfs. In Supercruise they can boost FSD range, quoted as ×4 and ×1.5 respectively; in normal space they are hazardous. These are gameplay rules. [DSN guide](https://ed-dsn.net/en/neutrons-2/).

The community wiki documents black holes including Sagittarius A*, lensing and exclusion zones. Direct retrieval failed, so detailed current damage behaviour is not used here; indexed text was available. [Elite Dangerous Wiki](https://elite-dangerous.fandom.com/wiki/Black_Holes).

**For Freelancer:** make the cone readable before a ship reaches danger. Distinguish the centre, rotation direction and exit route geometrically. Scientific data or an equipment bonus could reward a crossing. A quiet black hole can work through background distortion alone.

Do not automatically give every white dwarf cones, assume black holes are safe, or copy the exact boost coefficients. First establish clear geometry and an understandable influence region.

## No Man's Sky

**Primary evidence:** Endurance update 3.94 explicitly describes travel through black holes and new cinematic effects, with a linked visual example. [Hello Games](https://www.nomanssky.com/endurance-update/).

**For Freelancer:** separate the distant object, approach, entry and transition. This particularly suits the existing jumphole. Keep a recognizable distant shape while allowing a close passage to briefly affect the whole view.

Black-hole travel is fiction. Classifying this as a wormhole or artificial spatial anomaly lets traversable portals coexist with non-traversable astrophysical black holes.

**Proposed combination:** localized distortion, readable entrance, volumetric interior and a separate transit animation. This does not describe No Man's Sky's implementation.

## Outer Wilds

**Primary evidence:** Mobius describes light-bending at Brittle Hollow's black hole, planetary fragments falling inside and particle ejections indicating consumption. The developers explicitly describe the representation as an approximation. [Brittle Hollow VFX, 17 August 2018](https://www.mobiusdigitalgames.com/news/brittle-hollow-visual-effects-vfx).

**For Freelancer:** involve the environment. Debris, a damaged station or probe trajectories add more than an isolated overlay against empty sky. Particles can communicate the loss of a specific fragment rather than emit randomly around the entire rim.

**Proposed combination:** lensed background, oriented debris paths, a consumption event and bounded local ejection. Ejecting particles after every impact is feedback language, not a physical law.

Acceptance criterion: a fragment disappears appropriately into the capture region while a foreground ship remains visible. Painting a black sprite over everything fails this test.

## EVERSPACE

This concerns **the first EVERSPACE**, not automatically its sequel. Official version 1.0 notes restrict black-hole spawning near ancient structures; version 1.2.0 increases dark-matter spawning around holes. These establish connections to placement and resources. [Version 1.0](https://steamcommunity.com/games/396750/announcements/detail/1252410711759059753), [24 October 2017 patch](https://store.steampowered.com/news/posts/?appids=396750&enddate=1508849080).

**For Freelancer:** build a short approach, recover and retreat task. Put rewards on a readable outer hazard boundary and verify an escape route for the intended ship class. Probe data, cargo or wreckage can replace fictional luminous dark-matter resources.

**Proposed combination:** dark centre, external lensing, sparse highlighted debris and directional flow. Pulling a ship requires separate movement, server and balance work; a shader does not apply gravity.

## EVE Online

**CCP-hosted documentation marked crowdsourced:** `mapSecondarySuns` lists Magnetar, Black Hole, Red Giant, Pulsar, Wolf–Rayet and Cataclysmic Variable. These apply system bonuses and penalties in wormhole space; the secondary sun is not a normal warp destination. [EVE Developer Documentation](https://developers.eveonline.com/docs/guides/staticdata/#wormhole-effects).

**For Freelancer:** support two presentations: a visitable local object and a distant source defining system conditions. The latter can prioritize background structure, state indicators and equipment effects over expensive close-up surfaces.

**Proposals:** magnetar flares interrupt scanning windows; a pulsar defines a directional hazard; an accreting hole provides a debris and radiation environment. EVE's numerical bonuses belong to its combat system and should not be copied directly. Explain conditions through instruments and descriptions, not only field-line graphics.

This source confirms classes and system effects, not particular shader techniques or the exact appearance of every object.

## X4 Tides of Avarice

The official expansion page describes stellar phenomena that influence player plans. The Egosoft-hosted community wiki reproduces the Tide's encyclopaedia description: repeated stellar thermal pulses cross the system, giving the more distant sector additional warning. It also documents spatial anomalies. [Expansion page](https://store.steampowered.com/app/1701060/X4_Tides_of_Avarice/), [Avarice V, wiki revision 7.9 dated 2023-10-11](https://wiki.egosoft.com/X4%20Foundations%20Wiki/Manual%20and%20Guides/Objects%20in%20the%20Game%20Universe/Systems%2C%20Sectors%20and%20Zones/Systems%20Database/Avarice/Avarice%20V%3A%20Dead%20End/?rev=7.9).

**For Freelancer:** a magnetar or active-star event can use a shared clock and spatial propagation: warning, peak influence, recovery. Arrival time depends on ship location.

A slowly advancing visible radiation wall is an artistic choice; actual electromagnetic radiation travels at light speed. Separate a fast radiative front from slower ejecta, or explicitly compress propagation speed for playability.

## SpaceEngine

This is a visual simulator, useful as a technical reference rather than an equivalent adventure loop.

**Primary evidence:** the 16 December 2022 release describes relativistic geodesic tracing including rotating holes, with volumetric disks and polar jets. [General Relativity release](https://spaceengine.org/news/blog221216/).

The manual exposes environment-capture tradeoffs: low quality substitutes mirrored screen content for missing off-screen information; medium refreshes one environment-map face per frame; high refreshes all faces. [Graphics settings](https://spaceengine.org/manual/user-manual).

**For Freelancer:** adopt geometric reference targets while choosing a separate budget. A non-rotating hole with precomputed deflection and a static distant environment is a practical first physical version. Dynamic backgrounds, Kerr tracing and all-direction scene capture are later work.

SpaceEngine's disk and jet features do not imply these are obligatory around every actual star. Author a specific system.

## Synthesis

| Proposed object | Combined lessons | Prototype target |
|---|---|---|
| Pulsar | Elite's readability and X4's spatial timing | Thick 3D cone that rotates and is occluded correctly |
| Magnetar | EVE's system influence and X4's events | Arcs and flares create an identity beyond a recoloured sun |
| Black hole | SpaceEngine geometry and Outer Wilds environment | Disk and background lensing survives orbiting; cockpit stays intact |
| Microquasar | Shared disk and jet with an EVERSPACE-style local task | Companion, stream and disk form a coherent scene |
| Quasar | SpaceEngine scale and EVE's system presentation | Nucleus, dusty volume and distant jets remain distinguishable |
| Wormhole | No Man's Sky transition stages and existing jumphole | A separate fictional object with readable entrance and transit |

Before the final art pass, capture comparison views at distance, from the side, along the axis, against a nebula and behind a foreground ship. Visual-source links are in the [register](sources.md). No third-party textures or shaders were added.
