Hatcher hair refinement, strand lighting and inertial group motion
==============================================

Asset scope: CHARACTERS/HEADS/li_hatcher_head.dfm only.
Renderer: RP9.dll/PDB, Deformable2.dll/PDB and room_material.hlsl,
installed by install_renderer.py.
The package also includes matching Common.dll/client binaries and symbols for
the character_hair preference and communication portrait scope.
DETAILS: CHARACTER HAIR (Russian label is uppercase) uses 0/off, 1/shading only,
2/shading plus 55 percent motion, 3/full current effect. This setting follows
the existing restart-required preference model, presets and integrated defaults.
All FCommChannel::DrawPortrait calls hold a nested per-thread Common scope;
PortGraphicsRenderValue returns zero for character_hair and character_hair_motion
within that scope, including the material-batcher flush. Authored base models,
textures and ordinary facial animation remain visible. The vertex buffer is
rebuilt from the undeformed source when motion is disabled, not frozen mid-bend.

Head audit: 107 DFM heads scanned, no parser errors; only the modified Hatcher
head exposes an explicitly named hair material. No automatic colour-based
classification was deployed to other heads. Shared face/hair materials need
authored masks or geometry separation before safely opting in.
Exact material AND texture opt-in: hatcher_hair_v1 | hatcher_hair_v1.tga.
All shared face materials keep their original native shading.
The dedicated path adds a footprint-filtered analytic per-pixel strand normal
field and two bounded anisotropic highlight lobes. No extra texture allocation,
geometry or render pass. This is procedural microrelief, not a
baked normal-map image or parallax. Respects the room material/finish settings.
Existing room-material GPU tests cover routing, bone transforms, alpha,
CPU-skinned blended draws, face exclusion and visible shader response.
The front lock is raised by up to .005 model units, with smooth boundary fade.

Motion: six virtual strand joints with damped head-rotation response and weak
idle movement. CPU bind-space deformation runs before native bone skinning,
on instance VB output only; shared archetype vertices are never mutated.
Hair_motion_weights / Hair_motion_bone are optional DFM Geometry nodes.
Only LOD0..2 opt in; weight fades at hairline and by LOD. Face weights are zero.
State is keyed by the instance's FLodHolder and removed at holder destruction;
mesh opt-in data is removed at archetype destruction. Long gaps/large pose
changes reset inertia. Adjacent draws within 1/120 second reuse state; this is
a short time gate, not an engine frame-ID guarantee for very long render passes.
The same CPU VB deformation feeds normal and shadow draws. No new skeleton
slots, draw calls, triangles, texture allocations, or cloth collision solver.
Bounds get a six-millimetre allowance. Tests on the actual head measured peak
motion of 1.202/0.768/0.277 mm for the three LODs during a test head turn.
These are test-motion values, not a measurement from a live cutscene.
Run: python tools/hatcher_hair/build_motion.py
     python tools/hatcher_hair/check_motion.py
Tests cover fixed points, 30/60/144 FPS, bounded motion, repeated timestamps,
pause reset, unit normals, idle-vs-turn response and independent state.
The original face texture, facial vertices/normals, UV animation tables,
skeleton, original skin weights and original vertex/UV index prefixes are kept.
Hair-only faces use a separate opaque DcDt material and a 1024px mip chain.
TGA mip names stop at MIP9 (2x2): native LoadTgaTexture rejects MIP10,
which would make the entire hair texture fail to load. check.py validates this.
Offline Phong subdivision, swept ridges, a tapered rear volume and a curved
crown reshape the cap. Coincident UV-seam points share sculpting coordinates
and normals. Four offline relaxation passes smooth the welded hair surface
while fixing the original face/hair boundary.
Normals are recalculated from the refined geometry, welded across UV seams.
The upper hairstyle is compressed by 26 percent above y=0.090 (weighted by
distance from fixed face edges). A mirrored continuous directional normal
field adds lighting contrast across strands on both sides. The perturbation
is bounded below 31 degrees, fades at hairline and across LODs (1/.65/.3/0),
and requires no runtime normal map or special shader. Tests verify bilateral
field symmetry and unchanged normals at zero influence and distant LODs.
No runtime subdivision, alpha hair cards, or additional shader pass.
The original hairstyle silhouette is still recognizable; this is not a full
reconstruction of the pointed locks in the concept art.

Run from repository root:
  python tools/hatcher_hair/build.py
  python tools/hatcher_hair/check.py
  python tools/hatcher_hair/install.py --apply
  python tools/hatcher_hair/install.py --restore

The initial live DFM is retained in out/hatcher_hair/original.dfm.
Installation refuses to overwrite an independently changed live head.
All staged/live DATA writes and rollback use Pythonlancer DataFolder.
Per-install backups and installed hash are stored in out/hatcher_hair.

Preview actual exported triangles with Blender in background mode:
  blender --background --python tools/hatcher_hair/render.py -- out/hatcher_hair/after.json
These are Blender inspection renders, not screenshots from the game;
they do NOT reproduce the new RP9 per-pixel hair shading.
They are useful for geometry/UV review; game lighting can differ.
Checks cover all six LODs, array/index bounds, normalized skin weights,
original material/texture preservation, and untouched non-hair geometry.
No in-game FPS measurements or in-engine animation validation were performed.

Closest LOD: 13023 triangles total versus 864 original; 7044 points; one additional
material group. Other LOD totals: 2880, 881, 345, 173, 86 triangles.
Additional texture: about 5.33 MiB if expanded to RGBA8 including mipmaps.
This is a small GPU workload for RTX 3060, but not a measured FPS guarantee.

Texture source: assets/hair_atlas_v1.png, generated with built-in image_gen.
References: original extracted head atlas and H:/FL/VIDEO_EXP/LI/l19.JPG.
Prompt intent: preserve the UV layout; repaint only hair as smooth copper-red
swept locks close to Captain Tish concept art, remove noisy crosswise streaks,
avoid baked directional lighting. Generate a flat texture atlas, not a portrait.
The generated face region is deliberately unused: original facial material
and original texture remain in the DFM. Texture conversion/mips happen in build.
