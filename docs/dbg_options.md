# Beta debug options window (DBG_OPTIONS)

**English** · [Русский](ru/dbg_options.md)

The 2002 beta of `freelancer.exe` has a debug options window (keymap command `DBG_OPTIONS`, 221;
key handler `opt_KHandler` at beta `0x00570410`, list drawing `FUN_0056ffd0`). It edits the same
71-row option table retail still carries ([game_options.h](../src/freelancer/Client/game_options.h)):
retail kept the table and its 138 guards but removed the window, so every option keeps its
default. The port brings the window back and the drawing behind its `[OUTLINES]` group.

| Property (`src/Freelancer.Diagnostics.props`) | Define | Sheet default |
|---|---|---|
| `FreelancerDbgOptions` | `FREELANCER_DBG_OPTIONS` (client and `Common.dll`) | 1 |

## Window

Retail has no `DBG_*` keymap commands, so the window opens on **Ctrl+Shift+O**.

| Key | Action |
|---|---|
| Up / Down | select a row |
| Enter / Space | switch the row on or off (a multi-valued option goes back to its default when on) |
| Left / Right | decrease / increase the value |
| Esc, Ctrl+Shift+O | close |

The rows are the whole table: the bracketed rows are group switches that retail tests together
with the rows under them (`[EFFECTS]` and `PARTICLES`, ...). Changing a row writes the value the
game's guards read, so the other groups (`[OBJECTS]`, `[EFFECTS]`, `[INTERFACE]`, ...) work as in
the beta wherever retail still tests them. The values are not saved.

## [OUTLINES]

Drawn over the space scene after the effects, for objects within 7500 m of the camera (beta
`FUN_00516a10`, `DAT_005c92a0` = 56250000), when `[OUTLINES]` is on:

| Row | Beta | Port |
|---|---|---|
| `PHYS WIRES` | `FUN_00516420`: per physics part the hull (CObject +0x5c) as wires, or the sphere (+0x54) | every edge of the IVP compact surface's convex ledges, in world space (`DbgOutlineCollisionHull`); an IVP ball as a sphere. Yellow for the player's ship, cyan otherwise |
| `PHYS SPHERES` | the part spheres | the physical sphere (`get_physical_radius_r`), magenta |
| `SHIELDS` | `FUN_005162c0`: the physical sphere, blue | the same for ships, lighter blue |
| `PHANTOMS` | a functor over the phantoms | the phantoms attached to the object (CObject +0x78): box / part phantoms as hulls, sphere phantoms as spheres, green |
| `HOTSPOTS` | `Client\supt\Hotspot.cpp`, the beta's own hotspot list | not ported: retail has no such list |

The geometry comes from `Common.dll` (`src/include/common_dbg_outlines.h`). The beta and retail
use the same IVP physics; the beta's per-part walk over the engine instance tree is replaced by
the object's single surface, which already holds every part's ledges.

Compiled, not yet run.
