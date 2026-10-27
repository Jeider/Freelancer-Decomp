# Physics and cosmic object catalogue

[Русский](../ru/space_anomalies/physics.md) · [Overview](README.md) · [Rendering](rendering.md)

Date: 26 October 2026. Values marked as examples are model inputs, not measurements of a particular star. Gameplay suggestions are unimplemented proposals.

## Object relationships

| Object | Defining property | Suggested visual identity |
|---|---|---|
| Black hole | Event horizon | Dark capture region and distorted background |
| Accreting black hole | Surrounding matter supplies the hole | Disk, lensed disk images and unequal brightness across it |
| Neutron star | Dense stellar remnant with a surface | Compact surface and hot regions |
| Pulsar | Observed periodic emission | Sweeping emission direction; viewpoint-dependent pulses |
| Magnetar | Magnetic energy powers its characteristic activity | Disturbed magnetosphere and occasional strong flares |
| Quasar | Exceptionally luminous active galactic nucleus | Accreting nucleus and surroundings; powerful jets in some objects |
| Microquasar | Stellar-scale accreting system with jets | Compact disk, companion and outflows |

Classification sources: [NASA black holes](https://science.nasa.gov/universe/black-holes/), [ESA neutron stars](https://www.esa.int/Science_Exploration/Space_Science/Neutron_stars_pulsars_and_magnetars), [magnetar review](https://arxiv.org/abs/1503.06313), [NASA active galaxies](https://science.nasa.gov/universe/galaxies/types/). Pulsar and magnetar can describe the same star.

## Black holes

### Physical basis

The horizon is a causal boundary, not a solid surface. A hole without surrounding fuel need not have a luminous disk. Accretion supplies emitting matter and plasma; jets do not emerge from inside the horizon. The apparent shadow and horizon radius are distinct. [NASA Anatomy](https://science.nasa.gov/universe/black-holes/anatomy/).

Content variants:

1. **Quiet hole:** background distortion, little emitting material; most legible against stars or a nebula.
2. **Thin disk:** a flattened emitter whose far side appears bent around the shadow.
3. **Thick flow:** irregular hot material and partial absorption, with a less tidy silhouette.
4. **Binary:** a companion and mass-transfer stream feeding the disk.
5. **Transient:** tidal disruption stretches a star into material feeding a flare. This is an event rather than a mandatory state. [NASA TDE](https://science.nasa.gov/asset/hubble/black-hole-tidal-disruption-event/).

### Appearance

Lensing can reveal the far disk above and below the shadow. Differential rotation stretches bright structures. Approaching gas appears brighter, while an exactly face-on view removes that approaching/receding asymmetry. [NASA's 2019 visualization](https://www.nasa.gov/universe/nasa-visualization-shows-a-black-holes-warped-world/).

**Art direction:** a warm disk with a white inner region, a quiet dark centre and fine edge detail. Orange is a palette choice, not a universal disk colour. Put most movement in the matter; constant shaking of the dark centre would undermine its apparent mass.

Keep four concepts separate: the physical horizon; the Schwarzschild photon sphere; the observer's shadow or capture directions; and bright rings formed by images of light sources. A photon sphere is not inherently a glowing shell.

### Scale and calculation

Use an uncharged, non-rotating Schwarzschild model initially. With `r_s = 2GM/c²`, radii below are Schwarzschild coordinate radii except `b_crit`, an impact parameter. Geometry and ray equations: [Bruneton 2020, section 3](https://ebruneton.github.io/black_hole_shader/paper.pdf).

```text
r_s      = 2 G M / c²             ≈ 2.95334 km × (M / M_sun)
r_ph     = 1.5 r_s                photon sphere
r_ISCO   = 3 r_s                  innermost stable circular matter orbit
b_crit   = (3 sqrt(3) / 2) r_s    ≈ 2.59808 r_s
```

`b_crit` gives the shadow radius in the impact plane for a distant observer and distant background. It is neither the photon-sphere radius nor a universal screen radius near the horizon. Spin, observer motion and finite distance require appropriate models.

Calculated examples using `G = 6.67430e-11`, `M_sun = 1.98847e30 kg`, `c = 299792458 m/s`, `1 AU = 149597870700 m`:

| Model | Horizon | Photon sphere | ISCO | `b_crit` |
|---|---:|---:|---:|---:|
| 10 solar masses | 29.53 km | 44.30 km | 88.60 km | 76.73 km |
| 100 million solar masses | 1.974 AU | 2.961 AU | 5.923 AU | 5.129 AU |

For a distant camera, the initial small-angle estimate is `shadow angular radius ≈ b_crit / distance`. At 10000 km, the 10-solar-mass example has a radius of about 0.44 degrees. Approach or deliberate scale exaggeration makes it prominent. Store mass separately from presentation scale.

**Game proposal:** outer debris and probe fields, a warning region, then an unrecoverable inner zone. Warning distance should account for ship control rather than simply multiply shadow radius. Distant gravity is not a special vacuum-cleaner force; a traversable portal is a separate fictional anomaly. [NASA Black Holes](https://science.nasa.gov/universe/black-holes/).

## Neutron stars and pulsars

### Physical basis

A neutron star has a surface. For the prototype choose `M = 1.4 M_sun`, `R = 12 km` as example inputs. A 2024 NICER analysis inferred an equatorial radius of `11.36 (+0.95 / −0.63) km` for PSR J0437−4715 under its preferred model, bounded by the posterior's 16th and 84th percentiles. This illustrates an individual estimate rather than establishing one radius for all neutron stars. [Choudhury et al. 2024](https://arxiv.org/abs/2407.06789).

Rotation and directional emission produce observed pulses. Different observers need not see the same pulses; profiles can differ between observing bands. Two cones provide a useful simplified geometry, not a complete magnetosphere model. [ESA](https://www.esa.int/Science_Exploration/Space_Science/Neutron_stars_pulsars_and_magnetars).

### Proposed appearance

A small blue-white surface, two hot regions and a magnetic axis tilted relative to the spin axis establish the basic composition. Cones follow the magnetic axis. A weak surrounding glow leaves the geometry readable. Looking down a cone increases a local glare and instrument signal.

Distinguish a radiation beam from a material jet. Pulsar wind nebulae contain tori, arcs, knots and jets; the large jet can align with the spin axis. Do not rotate an entire extended nebula with the simplified radio beam. [Cerutti and Giacinti 2021](https://www.aanda.org/articles/aa/pdf/2021/12/aa42178-21.pdf).

**Artistic departures:** side-visible coloured cones, an enlarged core and slowed motion. A radiation direction is not automatically a bright tube viewed sideways in vacuum. Plasma, dust or a sensor visualization mode can supply that presentation.

### Geometry and parameters

With local Z as the spin axis, magnetic tilt `alpha` and period `P`, the proposed geometry is:

```text
phase = 2 pi (t - epoch) / P + phase0
m(t)  = (sin(alpha) cos(phase), sin(alpha) sin(phase), cos(alpha))
```

For star-to-observer direction `v`, evaluate both `dot(m,v)` and `dot(-m,v)` through a cone profile. When `alpha = 0`, the axis does not sweep the sky; the model must not invent blinking. A view missing both cones should not receive a global pulse each period.

The light-cylinder radius follows from `Omega R_L = c`:

```text
R_L = c P / (2 pi) ≈ 47713 km × P[seconds]
```

It bounds rigid corotation in the idealized model, not a luminous wall. Separate `physical_period` and `display_period` can preserve scientific metadata while keeping visible movement readable. Millisecond periods need an averaged signal to avoid temporal aliasing.

**Game proposal:** cone crossings alter instruments, heat equipment or provide research data. Effects depend on ship position, not camera direction. Rhythmic audio is an instrument's sonification, not sound travelling through vacuum.

## Magnetars

### Physical basis

Magnetic energy powers characteristic magnetar activity. Mereghetti, Pons and Melatos report 2–12-second periods and inferred external dipole fields around `10^13–10^15 G` for their reviewed sample, not hard class boundaries. Some magnetars also appear as pulsars. [2015 review](https://arxiv.org/abs/1503.06313).

An artistic preset could use `10^14–10^15 G`, equivalent to `10^10–10^11 T`, and a five-second period. Field magnitude should not directly become RGB intensity or a damage radius.

Rare giant flares differ from regular pulsation. NASA describes the 15 April 2020 event as an approximately 140-ms pulse; it is an example of a brief transient, not continuous strobing. [NASA 2021](https://www.nasa.gov/universe/nasa-missions-unmask-magnetar-eruptions-in-nearby-galaxies/).

### Distinct visual identity

**Proposed composition:** a surface, a few large closed arcs, smaller irregular filaments and local hot spots. Anchor arcs to the star, give them thickness and let the surface occlude their far sides. Violet, blue-white or turquoise are palette choices.

The quiet state slowly twists a few structures. An event brightens one arc, produces a brief localized flare, and leaves fading plasma. The buildup is authored gameplay warning, not a claim that actual flares are always predictable.

Field lines visualize geometry; they are not luminous wires. An intense magnetic field alone does not justify a giant screen-refraction bubble. Label field visualization and instrument interference as presentation choices.

### Geometric starting point

For an ideal static dipole outside the star:

```text
B(r) = (B_p / 2) (R / r)^3 [3 (m dot r_hat) r_hat - m]
r(theta) = L sin²(theta)
```

`B_p` is polar surface field, `m` the unit magnetic axis and `L` the chosen field line's equatorial radius. This is a mathematical curve generator, not a simulation of real magnetar currents or plasma. Clip inside `r < R`; arc footpoints obey `sin²(theta0) = R/L`. Apply noise along the arc while preserving attachment and overall shape.

The ideal dipole's `r^-3` scaling reduces the field by a factor of 1000 at `10R` along the same radial direction. Do not extend that law to the entire distant rotating magnetosphere and wind.

**Game proposal:** quiet scanning intervals, rare warned flares and a reason to leave the dangerous region. Radar disruption, shield drain and heating are tunable rules, not direct physical predictions without equipment, spectrum, distance and shielding models.

## Quasars and microquasars

### Physical basis

A quasar is a luminous galactic nucleus powered by accretion onto a supermassive black hole, not a special small star. Blazars have jets pointing nearly toward the observer; orientation strongly affects appearance. [NASA Galaxy Types](https://science.nasa.gov/universe/galaxies/types/).

Powerful radio jets are not mandatory for all quasars. ESO quotes around 10% as radio-loud; selection and definitions matter, and the remainder need not lack all weak jets. [ESO 2021](https://www.eso.org/public/news/eso2103/), [Macfarlane et al. 2021](https://academic.oup.com/mnras/article/506/4/5888/6321852).

Microquasars put an accreting compact object and jets in a stellar system, often supplied by a companion. [NASA Microquasars](https://www.nasa.gov/universe/two-black-holes-teach-astronomers-a-lesson/).

### Proposed scene layers

| Layer | Composition role | Implementation |
|---|---|---|
| Nucleus and inner disk | Main light source | Shared disk component and bounded glare |
| Absorbing torus | Depth and partial obscuration | Irregular dust volume; an authored parametric model |
| Narrow jets | Direction and energy | Cones or tubes with moving knots |
| Distant lobes | Scale of activity | Sparse broad volumes at low detail |
| Host galaxy | Scale context | Distant background separate from local geometry |

An emitting disk can obscure the shadow: do not force a dark circle through every foreground layer. Parsecs of torus and small inner structures should not share one animation period. A blazar preset can enhance the approaching jet and core with viewing angle while keeping the ship readable.

**Recommendation:** use a true quasar as a distant object or a dedicated galactic-nucleus set piece. Use a microquasar for a normal navigable Freelancer map. If a quasar is compressed into a local scene, explicitly identify that scale compression. The black-hole radius examples above show why one global scale factor is insufficient.

**Game proposals:** a research station near the hazardous region, routes outside jets, variability observations and salvage in a feeding stream. A microquasar's companion and stream tell a spatial story without explanatory text.

## Related families

| Phenomenon | Scientific basis | Game opportunity |
|---|---|---|
| White dwarf | Roughly planet-sized compact remnant; distinct from a neutron star. [NASA Stars](https://science.nasa.gov/universe/stars/types/) | Bright core and restrained halo; add a stream and disk for an accreting binary |
| Accreting binary and nova | A white dwarf receives matter; accumulated hydrogen can undergo a thermonuclear outburst. [NASA CV](https://science.nasa.gov/asset/hubble/cataclysmic-variable-star/) | Disk plus a distinct event; distinguish a classical nova from a supernova or disk instability |
| Pulsar wind nebula | Wind, torus, jets, arcs and knots. [Cerutti and Giacinti](https://www.aanda.org/articles/aa/pdf/2021/12/aa42178-21.pdf) | Pulsar within a filamentary volume, distinct in scale from surface magnetic loops |
| Supernova remnant | Ejected shell after an explosion. [NASA Stars](https://science.nasa.gov/universe/stars/types/) | Broken shell, filaments and cavities as an exploration location |
| Tidal disruption | Close passage tears a star into a luminous stream. [NASA TDE](https://science.nasa.gov/asset/hubble/black-hole-tidal-disruption-event/) | Authored sequence of stretching, stream formation and bright accretion with compressed time |
| Neutron-star merger and kilonova | Ejecta and subsequent glow, possibly a short gamma-ray burst. [NASA Kilonova](https://science.nasa.gov/asset/hubble/neutron-star-collision-creates-kilonova/) | One-time climax followed by an evolving shell |
| Fast radio burst | FRB 200428 was associated with a Galactic magnetar; this does not establish one origin for all FRBs. [Bochenek et al. 2020](https://www.nature.com/articles/s41586-020-2872-x) | Brief instrument signal, recording and triangulation task; visible rings are stylization |
| Wolf–Rayet binary dust shells | WR 140 has repeated dust shells; the MIRI image maps infrared data to assigned colours. [NASA WR 140](https://science.nasa.gov/asset/webb/wolf-rayet-140-miri/) | Large nested arcs and shells using geometry and sparse volumetric noise |
| Wormhole or white hole | Hypothetical constructions without established astrophysical detection | Separate fictional class extending the existing jumphole, not an ordinary black hole |
| Dark-matter cloud or spatial storm | Visible emission and interaction need an explicit fictional mechanism | Reserve for authored fiction; do not treat dark matter as ordinary glowing smoke or mineable luminous chunks |

## Scale, danger and time

For the example neutron star, `1.4 M_sun` and `12 km`, the Newtonian estimate `GM/R² ≈ 1.29e12 m/s²` illustrates the scale. General relativity matters near the surface. Playable flights a few radii away therefore need explicit artistic assumptions.

Weak-field estimates include `a = GM/r²`, a radial tidal difference `delta_a ≈ 2GM L/r³` across a small body of radial length `L`, and isotropic radiative flux `F = luminosity/(4 pi r²)`. These omit jet directionality, spectrum, shielding and relativity. They are comparison tools, not complete damage formulas.

Store scientific metadata, game coordinates, visual scale, animation time scale and hazard radii separately. Average fast signals or accelerate slow events deliberately, independently of frame rate.
