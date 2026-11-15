Vector cursor prototype
=======================

Approved visual reference: assets/cursors/newcursors_preview_uniform_glow.png.
Correction authority is the original newcursors texture decoded upright:
the AI reference had mirrored/misread details and must not override it.
The game does NOT load this PNG. The 16 shapes are authored in
src/freelancer/Client/cursor_vector_art.h as circles, polygons and strokes.
This is a manual geometric reconstruction, not a pixel-identical PNG conversion.
Shared geometry/raster support is in icon_vector_raster.h. Equipment, cargo and
ship cursors use the exact base_icon_art.h shapes with coordinate transforms
that retain cursor size/placement, plus blue tint and cursor glow. BASESIDE
and these cursors therefore share tooth count, corrugation, wing cuts and
convex hull shading. CPU checks compare their evaluated alpha and surface
colours at matching points; installer hashes include both shared headers.
The talk_story cursor shares nn_icon_art.h's raised story-star facets, scaled
to its original 88-unit radius with blue tint. Menu and cursor convex shading
therefore stay identical; CPU checks also compare this shared shape.

Rasterization evaluates signed distance to the filled shapes. Glow follows the
contours with Gaussian falloff on both sides of a stroke, including holes.
Flight reticles have NO glow. Their thicker cores and curved shoulder marks
follow the original alpha silhouette. Fire retains its larger original extent.
The dollar uses one central bar and an open S stroke; information is lowercase i.
Cargo boxes are painted back to front with their short end faces on the right.
The arrow's two triangles share an analytic symmetry axis and tip (80,72).
Colours and spin from mouse.ini still apply, including hostile/fire variants.

Geometry is top-left/Y-down in 256-unit cells. It bypasses TGA/DDS orientation
entirely. Cached BGRA is uploaded top-down, with (0,0) at the top-left of the
unchanged CursorComputeQuad. Original atlas UVs are used ONLY by the fallback.
No DATA files, mouse.ini hotspots, cursor scales or source TXM are modified.

The runtime caches straight-alpha A8R8G8B8 textures at >=2x display size, in
64/128/256/512 buckets. One active bucket per shape (16 MiB absolute maximum).
Typical 1080p cache: 2.88 MiB. Creation is warmed at cursor startup; resizing
can regenerate buckets. Static frames use one textured quad / 2 triangles.
Managed textures survive D3D9 reset; MouseShutdown releases them.
Allocation/upload failure or unknown shape uses the original cursor.

Render settings in bin/port.ini:
  [Render]
  vector_cursors = 0
disables the prototype after restarting. Default is 1 in RP9 builds.

Checks and install:
  python tools/cursors/check.py
  python tools/cursors/check_gpu.py
  python tools/train_courier/build.py freelancer
  python tools/cursors/install.py
  python tools/cursors/install.py --apply

For the working client with optional DLSS menu support, build with
tools/shader_startup/build.py and pass --dlss-menu to both installer commands.
This still installs only the client/PDB, preserving the live renderer DLL.

CPU check runs the production rasterizer at 64/128/256, validates hotspot,
reflection symmetry, unclipped alpha, absent reticle halos, dollar orientation,
single dollar bar, information dot and
exports actual render previews to src/obj/cursor_vectors.
GPU check uses a hidden D3D9 device: all 16 textures are compared against CPU
pixels; verifies tint, rotation around hotspot and managed-resource reset.
It also renders 128 native-size cases (16 shapes, 720/1080/1440/2160 heights,
dark/light backgrounds), using the runtime texture buckets and linear sampling.
gpu_native_sizes_0.png and gpu_native_sizes_1.png retain native pixel sizes.
This is a rendering harness, not automated playthrough of every game state.

Installer deploys only freelancer.exe and matching PDB into FL_MOD/bin after
checking game is closed, input hashes and live DLL hashes. Backups and rollback
are under out/cursor_vectors/backups. Production profile is not used.
