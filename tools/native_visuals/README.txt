Native subtitles and ALE volume beams
====================================

Subtitles
---------
The game reads the existing FLSubs XML directly through Windows XmlLite. No
Converter, flsc/flsd bitmap database, wrapper DLL or subtitle shader is required.
Static entries follow the lifetime of their sound source. Dynamic Part intervals
are [Start,End), support seconds/mm:ss/hh:mm:ss, gaps, overlaps and XML entities.
WAV filenames are case/slash insensitive and relative to DATA/AUDIO. Voice UTF
entries resolve by profile UTF path and hexadecimal message ID. A source restart
restarts its caption; stopping, source destruction, scene skip and sound cleanup
remove it. WAV time follows the SoundManager clock including seeks and pauses.
The retail streaming interface has no position query: streamed captions follow
the client mixer delta while the stream is active and unpaused. They may drift
if the audio decoder stalls independently of the client clock.

Rendering uses the game's Unicode font atlas, word wrapping, white text and a
black outline. There is no rectangle behind it. Cinematic > News > Ingame >
Ingame_NN > Ingame_BG > Debug; at equal priority the newest active sound wins.
Only one caption is displayed at a time; lower-priority sources retain their
timelines and can become visible when the foreground sound finishes.

port.ini next to the running freelancer.exe:
  [Subtitles]
  enabled = 1
  font = Normal
  outline = 1              (0..3 screen pixels)
  bottom = 0.84            (0.5..0.95 screen height)
  xml = ..\BUILDS\RU_NORMAL\EXE\subtitles.xml

Without an explicit xml value: [Language.<active>] subtitles_xml, then local
subtitles.xml, then ../BUILDS/<language>_<difficulty>/EXE/subtitles.xml, then
../EXE/subtitles.xml. The first existing file is authoritative; a parse error is
logged and does not silently load another language. Config/entries load once.
Restart after editing XML. Missing XML is logged; no placeholder text is drawn.
The supplied installer does not overwrite game language or other port.ini values.
The workspace port.ini selects font = ConfirmPlayerText: this existing fonts.ini
nickname uses Arial at fixed_height 0.035 in the mod's font variants. The font
setting takes a nickname, not a Windows font family name. The compiled fallback
remains Normal when no explicit setting is supplied.

BeamAppearance
--------------
Alchemy collects the original particle centres, field tip, extrapolation,
widths, colour/alpha ramps and texture frame. RP9 builds one connected round
mesh with 24-sided rings. Curves use chord-scaled Hermite interpolation and
transported ring frames; adjacent spans share positions, normals and colours.
The ends stop at the authored positions, with no added spherical caps. Their
flat closing faces use explicit radial coordinates and the same soft core/halo
profile as the body, so they cannot become solid glowing discs. The shader shades a narrow hot core and
soft halo from smooth view-space normals. Only the visible wall contributes,
so brightness does not accumulate at every particle. Hardware depth tests the
actual mesh against scenery; the beam never writes the Z buffer. Scene targets,
viewport, HDR and render states are preserved.

  [Render]
  beam_volume = 1
  beam_volume_nodes = laser
  beam_volume_core = 0.18
  beam_volume_strength = 1.0
  beam_volume_trail_nodes = trail
  beam_volume_trail_fade = 10

Defaults above. Nodes match comma-separated, case-insensitive substrings of ALE
Node_Name. Examples: laser,maingun or ku_laser_01_proj.app. A single * selects
every additive FLBeamAppearance, including engine trails: use intentionally.
The workspace port.ini selects * for broad in-game testing. Set the game's
beam_volume_nodes back to laser to restore the initial filter, or beam_volume
to 0 for legacy ribbons. Restart the game after changing these settings.
Only ONE/ONE and SRCALPHA/ONE materials use this path. RP8, older RP9, unavailable
SM3 shaders, non-additive blends and debug wireframes retain native ribbons.
code_beam weapon effects are a different renderer and remain unchanged.

Only nodes matching beam_volume_trail_nodes fade near the camera. Matching uses
the same case-insensitive substring rules, default trail. The additive RGB fades
smoothly from zero at the active near plane to full intensity 10 metres beyond
it; farther parts of the same trail remain visible. Set beam_volume_trail_fade
to 0 to disable, or change its distance (0..1000). Ordinary laser nodes, including
Sphere's gf_alien_laser_on_beam.app, have no camera fade. Custom trail nodes with
other names can be added to the comma-separated trail filter. Settings load at
startup; restart after editing. No ALE assets are modified.

The texture frame's centre supplies colour/alpha tint. Axial texture tiling is
intentionally removed: repeating a texture's dark ends at each particle caused
visible bands. Particle colour, opacity and width ramps still apply along the
whole beam. The light profile is analytic; this is emissive tube geometry, not
ray-marched scattering or scene illumination. Tight loops may overlap, and
large numbers of curved trails still need in-game performance validation.
Gameplay, projectile speed and damage are unchanged.

The radial profile removes axial foreshortening: plain N.V would extinguish
the body at grazing views and leave only the end cap. Each ring supplies its
tangent; end faces use a separate radial profile instead of the body correction. Regression tests cover 5/15/30/60/85
degree views, including pixels on the body rather than only the axial end cap.
A wide end-on view also checks that the outer glow fades below a quarter of
the core brightness, guarding against the large bright-disc regression.
The GPU check also links the production RP9 objects to exercise its actual pass,
transform and state-cache route. Build RP9 Release before running it.

Optional beam_volume_debug = 1 captures up to eight beam samples and textures
to the Windows temp folder (freelancer_beam_N.txt/.dds); 2 records and uses the
legacy renderer. Default 0 disables capture. A captured sample can be replayed
with bin/beam_volume_route_check.exe <sample.txt> after tools/beam_volume/check.py.

Validation
----------
python tools/subtitles/check.py compiles the real XML reader/timeline: Russian
896 entries, English 9802 entries, Unicode, entities, UTF IDs, gaps/intervals,
seek, pause, failed-load atomicity and DTD rejection.
python tools/beam_volume/check.py renders the production shader on D3D9 using a
hidden window using the production mesh builder and shader. Checks particle-count
invariance in side/axial/oblique views, curves/taper, repeated points, radial
symmetry/core, depth occlusion, near-plane/camera-inside, behind-camera, zero-length
and alpha/atlas masks. Preview: src/obj/beam_volume/check.ppm (side, axial, curve).
Build freelancer, alchemy and RP9 Release Win32 with v145 and the appropriate
DX8/DX9 SDK paths. Source edits preserve the sizes of retail ALE node objects.

Still required in game: dialogue timing during mission/RTC playback and skipping,
font visibility at multiple resolutions, streams and paused menus, repeated
radio lines, actual ALE texture/frame selection, bends, HDR/fog and many beams.

Installation
------------
python tools/native_visuals/install.py prepares a verified payload in src/obj.
python tools/native_visuals/install.py --apply installs that exact payload with
backup and hash checks. It refuses if Freelancer/FLServer is running or files
changed after preparation. This replaces only freelancer.exe/pdb, alchemy.dll/pdb,
RP9.dll/pdb and DATA_EXTRA/SHADERS/beam_volume.hlsl in D:/games/FL_MOD.
It does not patch the old EXE retail launcher or deploy the D3D8 subtitle wrapper.
