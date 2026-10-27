Dense exterior ship glass
========================
The existing Glass/EnvMap alpha pass in surface_material.hlsl uses ~33% opacity
for authored Oc=.8 face-on, increasing toward grazing angles. The previous
shader reduced the same material to ~20% opacity. The authored blue Liberty
and muted green Rheinland colours now contribute substantially to the surface.
Broader GGX/coat highlights and the smooth reflection band suggest a dense
laminated canopy. This is tint/opacity, not a scene-colour blur or refraction.

No model, UV, material-library, extra texture fetch or render pass is added.
Existing native opaque/back-face pass and transparent-material routing remain.
Applies to the existing glass shader family, not just these two ship nicknames.

python tools/ship_glass/check.py
Uses real D3D9 and the production SM3 shader, with the inspected li_elite and
rh_elite material colours. Checks face/grazing alpha, actual blended background
transmission, hue and missing-normal fallback. A local pre-edit snapshot at
src/obj/ship_glass/before.hlsl additionally verifies that hull/cockpit output is
unchanged. In-game art direction still needs comparison on actual ships.

Install through tools/room_materials/install.py (stage, then --apply); the shared
surface shader is allowlisted, backed up, hash-verified and warmed in game cache.
