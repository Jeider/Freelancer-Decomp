Code beam shader, artistic profile
=================================

The client marks only EffectVertexBatchFlush's indexed code_beam draw via the
optional IRPCodeBeam v2 interface. RP9 applies code_beam.hlsl to that draw only.
RP8/older RP9, missing shader files or unsupported SM3 retain native rendering.

The existing atlas, beam geometry, colour interpolation, head and
trail choices, brightness, dimensions and lifetime are unchanged. BeamSpear and
BeamBolt INI settings remain authoritative. No gameplay or DATA edits.

The original 24-byte CPU vertices and retail layouts remain intact. A reused sidecar
GPU buffer expands vertices to 40 bytes (FVF 0x80242): TEXCOORD1 holds local XY,
normalised axial Z and a stable per-projectile phase. CodeBeamFlow::Fill derives
these coordinates using the projectile transform, independently of atlas UV seams.
The shader consumes that copy in the same indexed draw; no extra draw per weapon.

One pass, one original atlas fetch, no extra geometry, render targets, scene-depth
sampling, noise textures, lights or shadow maps. Trail luminance is separated into
a narrow seventh-power filament and a broad coloured mantle. Star/ball heads use
a fourth-power core and a circular boundary fade on their mantle. The hot core is
mixed toward the authored colour's peak channel (68% trails / 80% heads); the outer
mantle retains the weapon hue. Dark atlas quantisation steps are suppressed to
avoid exposing the low-resolution source's square head boundaries.
The mantle now contains advected, domain-warped cells, a winding light filament and
moving bright packets. They flow toward the local +Z tail and are derivative-filtered
when subpixel. The core remains continuous while its intensity varies modestly.
Star/ball head UVs rotate and breathe within the authored footprint; expanding rings
and core pulses animate the head independently. Projectiles use different phases.
Zero authored brightness remains dark, including photon heads.
Hardware depth test and additive ONE/ONE blending remain, with depth writes off.
Fog attenuates additive light to black, so transparent polygon edges cannot add
a fog-coloured rectangle. Native crossed geometry/angle dependence is retained.

Optional port.ini [Render] controls (read at device creation; no config edits needed):
  code_beam_shader = 1       ; 0 selects the original renderer
  code_beam_strength = 1     ; range 0..2, default 1
  code_beam_ripple = 0.045    ; range 0..0.15, default 0.045
Ripple zero disables motion; 0.045 or higher uses the full animated profile.
Strength zero preserves texture*vertex colour; fog remains additive-correct.
The shader uses one shared style; optional per-weapon style controls are
not implemented. Existing per-weapon colours and sizes remain independent.

Shaders are prepared during device creation, never compiled at first shot.
tools/warm_surface_cache.cpp and tools/asteroid_normals/warm.py include both stages
and verify cache hits on a second run before installation/play.

Validation:
  python tools/code_beam/check.py
Actual D3D9 HAL shader compilation/rendering: one texture fetch, black borders,
colour preservation, linear authored brightness, visible internal motion, stronger
core/shoulder, fog attenuation, foreground occlusion, additive overlap/no Z writes.
Liberty laser 4 core colour is also checked with the game's alpha > 0 test enabled;
the shader preserves texture alpha * vertex alpha instead of returning zero alpha.
Checks also cover gold photon core/mantle colour separation and its disabled head.
The production flow-coordinate helper is checked for rotated/translated beams,
segment continuity and independent phases. Real-atlas temporal comparisons verify
moving head and photon-tail pixels while the legacy comparison stays static.
When the installed beam.txm is available, check.py extracts its atlas read-only and
renders src/obj/code_beam/comparison.png and flow_00..47.png (original left, animated
right, 50 ms per frame). This uses
representative triangular geometry; it is a GPU fixture, not an in-game screenshot.
This fixture does not replace an in-game visual/performance check in combat.

Stage/install (client, RP9, debug symbols, shader only):
  python tools/code_beam/install.py
  python tools/code_beam/install.py --apply
The installer refuses a running game/server, verifies staged/original hashes,
backs up replaced files and rolls back a failed copy. --restore BACKUP restores
the installation. Warm the real cache using tools/asteroid_normals/warm.py.
