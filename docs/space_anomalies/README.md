# Cosmic anomalies for Freelancer

**English** · [Русский](../ru/space_anomalies/README.md)

Research date: **26 October 2026**. Status: research and proposals for future implementation. New effects, settings and gameplay described here are not implemented by this documentation change.

Update: [eight standalone shader studies and actual GPU images](shaders.md) are now available, including [a fictional black-hole interior](interior.md). They are not integrated into game systems. The art direction prioritizes theatrical shapes and colour over realism.

The aim is a set of distinctive objects worth observing, exploring and navigating, with a scientific foundation and manageable RP9 rendering cost. The main subjects are black holes, neutron stars as pulsars and magnetars, and quasars. Related phenomena broaden the catalogue while reusing the same rendering components.

## Documents

| Document | Purpose |
|---|---|
| [Physics and object catalogue](physics.md) | Identity, appearance, meaningful quantities and artistic departures |
| [Game references](games.md) | Elite Dangerous, No Man's Sky, Outer Wilds, EVERSPACE, EVE Online, X4 and the SpaceEngine visual simulator |
| [RP9 effect design](rendering.md) | Shader layers, equations, engine constraints, pass ordering, cost, milestones and acceptance criteria |
| [Source register](sources.md) | Direct links, evidence provenance, visual references and follow-up reading; shared by both languages |
| [Shader laboratory](shaders.md) | Implemented HLSL prototypes, image gallery, reproduction and validation |
| [Black-hole interior](interior.md) | Working tunnel study and two further artistic directions |
| [Nomad / Dyson surfaces](nomad.md) | Wet interior relief, rock exterior, Sphere depth prepass and asteroid frustum correction |
| [Realistic maximum-quality studies](realistic.md) | Eight actual 4K GPU captures, shader sources, CPU math and GPU image checks; [gallery](realistic_previews/report.html) |

## Suggested implementation order

| Order | Deliverable | Reason |
|---|---|---|
| 1 | Pulsar with a rotating, tilted emission axis | Recognizable; establishes clocks, cones, occlusion and glow |
| 2 | Magnetar with spatial magnetic arcs and a controlled flare | Distinct geometry and rhythm; reuses the neutron-star foundation |
| 3 | Black hole with a disk and lensing | Strong visual identity; requires background and depth integration |
| 4 | Microquasar | Combines disk, jets and a companion's mass-transfer stream into a visitable scene |
| 5 | Quasar or active galactic nucleus | Large set piece with separate scales for the nucleus, torus and jets |

This orders dependencies; it is not a schedule. There are no measured GPU costs or in-game prototypes for these proposals yet.

## Shared components

Pulsar and magnetar should be independent attributes of a neutron star. A quasar is a luminous galactic nucleus powered by a supermassive black hole; a microquasar is a stellar-scale accreting system with jets. Scientific sources for these distinctions are in the [catalogue](physics.md).

Proposed reusable components:

- compact emitting surface and hot spots;
- volumetric emission cones and matter jets;
- magnetic arcs and directed particles;
- differentially rotating accretion disk;
- lensing of the background and disk;
- dust, shells and nebulae;
- flares, ejections and tidal disruption events;
- separate gameplay volumes and instrument signals.

## Interpretation

**Physics** means sourced properties or explicitly bounded models. **Art direction** means chosen colours, exaggerated scale, slowed time or visualization of invisible radiation. **Game proposal** means an unimplemented mechanic or architecture needing validation.

Radio, X-ray and infrared images often use assigned colours. Visible field lines, endless blue beams, expanding shock rings and black-hole travel are not automatically natural window views. Sensor processing can explain some visualization; other features can be deliberate stylization.

This covers the major families useful to this project, not all astrophysical literature or every space game. Game examples refer to identified sources and versions; no closed-source renderer was inspected. Local findings reflect the working tree while RP9 and code beam are changing concurrently. Recheck function locations before integration.
