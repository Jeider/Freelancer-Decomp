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

## Console

The beta's in-game console (`con_KHandler` at beta `0x006862a8`, drawing `0x00555020`, the
command table at `0x00690fb0`; `src/freelancer/Client/dbg_console.cpp`). The **`** key (the one
under Esc; `ё` on a Russian layout) opens and closes it. Enter runs a line, Tab completes a
command, Up / Down walk the history, PgUp / PgDn / Home / End scroll.

| Command | Action |
|---|---|
| `TimeScale` / `ts` [scale] | slow down or speed up the single-player game (beta `0x00550b10`; the frame timer multiplies the capped dt by it, beta `0x00427bf0`); at least 0.01, the port stops at 10 |
| `time` | seconds since the start |
| `max_fps` / `fps` [fps] | the frame-rate cap (retail `DAT_00610a0c`) |
| `lines` [2..40] | visible lines |
| `pos` / `p` | the player's position |
| `clear`, `quiet` / `q`, `help` / `h`, `quit` | |

From adoxa's console.dll (`console.cpp` v1.24; the server half is `Server/server_port_console.cpp`,
found by the client through `GetProcAddress(server.dll, "PortConsoleServer")`, single player):

| Command | Action |
|---|---|
| `save` / `s` [name \| 1-9] | save now, in space too (`PlayerData_SaveGame`); one character or none is a quick save `qsave<c>.fl` |
| `load` / `l` [name \| 1-9] | load such a save (`QueueLoadGameCharacter`; `[ModServer] account_folder` picks the folder) |
| `base` <name> | land at a base (nickname, or part of the name; `pub::Player::ForceLand`), from space |
| `system` <name> [x,y,z [rx,ry,rz] \| object] | move to another system: same coordinates, a position, or at an object (nickname or `~part`); `SystemSwitchOutComplete` takes it instead of a gate, without the autosave |
| `jump` / `j` [forward,right,up \| object] | move in this system: by an offset, to an object, or (nothing) to the target |
| `launch` | the base's launch tab |
| `ghost` | toggle the ship's collisions (the `DISABLE_COLLIDE` option) |

## Chase camera and hardpoints

The beta's `ChaseCamera` (vtable beta `0x005c79e4`, update `0x004f1dd0`, events `0x004f2ac0`) and
its hardpoint display (beta `0x0040c040` / `0x0040c160`), `dbg_chase_camera.cpp`. Retail has no
chase keymap commands, so the keys are fixed:

| Key | Action |
|---|---|
| Ctrl+Shift+C | watch the player's target (else the player); again, or Esc, returns |
| PgDn / PgUp | next / previous ship; with Ctrl, solar; with hardpoints shown, next / previous hardpoint |
| arrows, Num+ / Num-, Home | orbit, zoom out / in, reset |
| V | view: orbit, ahead, behind, facing |
| Num* | hardpoints: off, drawn on top, depth-tested (red X, green Y, blue Z axes) |
| Backspace, I | minimum distance 1; the info line |
