# Lightweight projectile surface accents

The RP9 surface shader adds a simple moving colour spot to supported opaque
ships, capitals and stations. This artistic cue creates no native D3D lights,
textures, extra render pass, particle objects or shadow-map updates.
weapon_lights=0 suppresses the old gun light_anim, including in cockpit view.
Muzzle/projectile particles remain unchanged.

## Collection and selection

Only live logical CBeam gun projectiles are considered. ALE-only, beam-only and
combined visuals share one submission path and cannot double count. Position
comes directly from CBeam::WorldPosition. The camera range is hard capped at
1000 metres; squared distances avoid square roots. After rejecting distant and
clearly empty positions, the native camera ClassifySphere test (radius zero)
rejects off-screen projectile centres. Off-screen glow spilling into the frame
is deliberately not retained. These checks happen before resolving colour.

A camera-relative 32x32x32 grid with 64 m cells marks the inflated bounding
volumes of queued visible opaque hulls. A projectile in an unmarked cell cannot
produce a visible local accent and is rejected before occupying a group. This
is a conservative broad phase, not ray tracing or an impact requirement. Large
station bounds and empty spaces inside those bounds can produce false positives;
per-object and per-pixel range rejection still prevent remote illumination.

A fixed-size selector admits at most eight shooters (configurable 1..8). The
player's own visible shots are prioritised, followed by shooters whose visible
projectile is closest to the camera. This is proximity prioritisation, not a
trajectory prediction. Two linear passes replace full candidate sorting. Scratch
vectors retain capacity between frames. Metadata resolves once per admitted
munition archetype per frame; successful ALE hue samples remain cached across
frames by effect nickname and visual CRC.

Each shooter produces ONE accent, regardless of turret directions, number of
simultaneous volleys or colours. All its admitted visible projectile colours are
averaged using their actual counts. Six red shots have the same colour/intensity
as one; equal red/green/blue counts become one neutral blended accent. This is
intentionally more aggressive than one effect per individual volley. A tracked
live projectile supplies the position, never the centroid of a long stream or
opposing turret directions. New muzzle shots do not displace that representative
while it remains eligible. Missing/off-screen/out-of-range seeds are replaced.
The retained identities are opaque address tokens, owner and remaining lifetime;
old tokens are never dereferenced. Camera changes clear the selection history.

## Receiver and shader cost

At each opaque hull draw, its bounding sphere is checked against the camera range
and each admitted spot. Only intersecting spots are packed into that draw's pixel
constants. Unrelated objects receive zero glint iterations and do not enter the
plain-material surface route solely because another distant hull is lit. Planets,
cloaked objects, decorative non-targetables, translucent/skinned and unsupported
material routes remain excluded. Rigid XYZ/NORMAL/TEX1-3 receivers work with and
without envmaps and local shadows.

The pixel shader rejects surfaces beyond the same camera range. Its glint-only
work uses dot products, multiply/add, saturate and a bounded colour shoulder with
one reciprocal. The previous short capsule, directional normalisation, specular
half vector, pow and exp are removed. There are no glint texture reads, shadows,
ray traces or temporal buffers. Basic arithmetic and coordinate transforms remain
necessary. Existing solar lighting, metallic finish, shadows, emission and fog are
preserved. Pixel registers c77-c93 carry control and up to eight position/colour
pairs; this optional interface is RP9_IRPWeaponGlints_v2 and needs a matched client
and RP9.dll.

## Authored colours

ALE BasicApp_Color curves are read through optional IAlchemyEffectColour from
already loaded const_effect archetypes. It follows effect Rec16.B hashes to node
prototypes and obtains IGenericFx::GetPropertySet. Saturated non-black key colours
are preferred over white cores. It mutates no nodes and never evaluates empty
ramps or loads ALE files in the draw loop. When vis_effect exists it is authoritative; vis_generic is considered only when
vis_effect is absent. Failed/unavailable ALE colour sampling skips the accent
and retries later, never falling through to a supplementary beam or light colour.
Beam outer/tip colour is used only for effects without ALE visuals; explicit
effect light colour is the final fallback for those effects. One combined ALE+beam projectile still
contributes only once. The ALE-only admission bug in the first implementation
was fixed before this lightweight profile.

## Settings

port.ini [Render], restart required:

| Key | Default | Meaning |
| --- | --- | --- |
| weapon_glints | 1 | Enable surface accents; requires surface_shaders |
| weapon_glint_groups | 8 | Maximum visible shooters, 1..8 |
| weapon_glint_strength | 1.25 | Added colour intensity, 0..4 |
| weapon_glint_radius | 22.5 | Influence radius in metres, 5..100 |
| weapon_glint_distance | 1000 | Camera range in metres, 100..1000 |

weapon_glint_trail is obsolete and ignored. The hard maximum remains 1000 even
if an older config requests more. No guarantee is made that every shooter in a
large battle gets an accent simultaneously: the global budget deliberately caps
work, with own shots and nearby projectiles favoured.

## Validation

Release Win32 client and RP9 builds pass. Both 2D and cube ps_3_0 variants compile
and are prewarmed. A standalone selector/coverage check verifies empty-space
rejection, grid edges, fixed shooter limits, player/nearest-projectile priority
and six mixed RGB shots becoming one averaged accent. Selection-only stress on
this machine: 100 frames x 10000 candidates, approximately 0.084 ms per frame.
This excludes game collection, camera tests, metadata and GPU rendering; it is
not an FPS or whole-feature timing claim.

The real RP9 HAL route harness checks plain TEX3 reception with shadow maps off,
identical one/six-shot brightness, mixed colours and opposite turret directions
remaining one group, receiver-bound rejection and constant compaction, backfaces,
radius and 1000 m rejection, and a moving representative through 30 continuous-fire
frames. Existing material/original cube, adaptive/200 m shadows, AF and FXAA
regressions pass. The separate real Alchemy implementation test checks red/green/
blue shell extraction against white cores and empty effect safety. In-game
battle performance and appearance still require user evaluation.

The active default budget is now eight shooters and the spot radius is 22.5 m
(diameter 45 m), half the previous diameter of 90 m. The client broad phase reads
the radius as a float, matching RP9 and preserving fractional settings. Shooter
aggregation remains unchanged: increasing this global budget does not split one
shooter's stream into several simultaneous accents.

## ALE hue and cockpit update

Colour selection now favours a distinct dominant RGB channel over bright
 two-channel transition keys, while retaining a smaller chroma preference.
Real extracted BasicApp_Color curves from rh_tachyon_04, rh_capgun_01 and
rh_plasma_03 test green: normalized RGB (0.198,1,0.198), (0.113,1,0.113)
and (0.143,1,0.143). No weapon-name colour overrides are used.

First-person cockpit geometry receives the same frame's selected accents.
Its bounds participate in the coverage grid even when the exterior player mesh
is absent. World submission disables reception without clearing the immutable
frame groups; cockpit submission scopes reception and restores it before HUD.
