# HUD plugins: target view, status view, inventory ship view

**English** · [Русский](ru/hud_plugins.md)

Three port-only features carried over from the HudInventory RC1 plugin pack (`HudTarget.dll`,
`HudStatus.dll`, `HudInventory.dll` — Delphi DLLs that patch the retail `freelancer.exe` in
memory). Those DLLs cannot be loaded by the port: they write to hard-coded retail addresses
(`0x004e1f91`, the vftable slot `0x005d85f4`, …) that hold other code in our `freelancer.exe`.
Their behaviour was therefore decompiled (the plugins' retail references, patch bytes and hook
sites, checked against the `HudInventory.dpr` source for the third one) and rebuilt in
`src/freelancer/Client`.

All three mostly **switch on code the retail client already has but never runs**: the target
view outside target mode, the HUD_Target_Base view slot that HUD_Status leaves empty, and the
inventory ship-view controls that `NN_Inventory` binds by name but never creates.

| Property (`src/Freelancer.Diagnostics.props`) | Define | Default in the sheet |
|---|---|---|
| `FreelancerHudTargetView` | `FREELANCER_HUD_TARGET_VIEW` | 1 |
| `FreelancerHudStatusView` | `FREELANCER_HUD_STATUS_VIEW` | 1 |
| `FreelancerHudInventoryView` | `FREELANCER_HUD_INVENTORY_VIEW` | 1 |

`src/Directory.Build.props` defaults each to 0 for projects without the sheet; `/p:<Name>=0`
builds the retail behaviour. With all three at 0 the client is identical to master.

## Separate player Health panel (port-only)

### Saved state and captions

Health/Targeting visibility, auto-open locks, projections, target autoselect and
the selected weapon group are stored in the native player-save `interface` word.
Changes update the server state immediately and reach disk with the next game save.
Bits 0..3 keep their original meanings; 4..5 are target projection, 6 is autoselect
disabled, 7/8 are Targeting/Health auto-open locks, 9 is Health closed, 10 is Health
left view, 11 is Targeting closed, 12..14 are weapon group 0..5, and 15/16 mark
explicit Health/Targeting visibility. Loading another player reapplies these values
even when the HUD survives the load. Targeting remains hidden without an eligible
target and applies its saved visibility to the first eligible selection; subsequent
selection changes follow its normal auto-open rules. Weapon-group restore activates
the saved group once a ship is available, instead of forcing group 1.

Backspace (`USER_MINIMIZE_HUD`) temporarily hides the detached windows too; pressing
it again restores their desired state. This temporary override is not saved and
does not alter either window's open/closed preference.

`hud_interface_ids.h` reserves IDs **238200..238224** in NameResources.dll for all
new buttons and the weapon-list icon. The editable translations are in the mod's
`Assets/Pythonlancer/text/static.py`, in `STATIC_NAMES`, automatically consumed by
`managers.ids`. Each entry is `Static(ID, MS('Russian', 'English'))`; keep IDs stable.
`tools/targeting_hud/stage_interface_strings.py` stages the initial entries and both
language DLLs, verifies that IDs are unused and preserves all unrelated resources.
It is an initial migration, not the translator's normal rebuild command; later edits
use Pythonlancer's existing static-string generation/resource import workflow.
Locks, pause/resume and autoselect show captions for the action their next click
will perform. Native key-binding hints remain enabled on weapon-group buttons.
Button tooltip anchors include the HUD's widescreen shift once and are clamped
against the full-screen camera, independently of the button's depth or montage path.

`[Health]` in `hud.ini` creates `HUD_Health` at `position = 0.152, -0.300`,
mirroring Targeting beside the right-hand HUD_Status. The existing centred
`hud_target2.cmp` supplies its frame. A separate player watcher, part cache and
camera keep it independent of the enemy selection and the weapon list's open state.
The top/left damage wireframe fits the rendered vertices to the viewport, using
the same fitting method as Targeting. Equipment state, subsystem damage colours,
hover descriptions and right-click weapon activation use the native ship logic.
The wireframe fills the space up to the inner top edge. Hull/shield gauges stay
in HUD_Core. Its bottom row has five buttons with equal hit areas at the same spacing
as Targeting: WingAnim play/resume, pause/resume, cruise-animation lock, top view,
and left view. There is no sixth/Fit button; both projections use geometric fitting.
The left camera is opposite Targeting's right camera. Projection selection stays
local to Health and does not alter Targeting's saved projection.

The animation controls call WingAnim's shared action API (also used by its key),
not a separate animation implementation. Play resumes a paused movement; otherwise
it toggles the eventual wing position. Pause holds the current channel times and
direction; play, pause again, or an allowed automatic animation request resumes it.
An opposite automatic destination queues behind the resumed movement. Cruise lock
blocks new cruise requests and cancels a queued cruise request without cancelling
a manual request or the current movement. Unlocking does not replay missed cruise
events. Launch and docking behavior remain independent of this cruise-only lock.
Pause and lock reset on a ship change. Ships without WingAnim have disabled animation
buttons, while both projection buttons remain available.

Health uses the native static part cache, built when the viewed ship changes.
Damage colours and part visibility still update, but the preview does not follow
animated wings or turrets. The WingAnim buttons control the actual ship independently
of this cached preview.

Health restores its saved visibility and top/left projection. Legacy saves start
open unless the auto-open lock is set. Its first button in
HUD_Status toggles it; the cross closes it using the same scale/slide sequence as
Targeting. New damage severity transitions or accepted NN damage warnings reopen
it when unlocked. Merely retaining the same damage, critical-colour pulsing, hover,
repairs and loading an already damaged ship do not count as new damage. The monitor
uses hull, collision-group and equipment health bands (75%, 50%, below 25%, destroyed),
including disappearance of an attached part; vulnerable groups retain their orange
baseline. No geometry is rebuilt for this monitoring.

The lock to the right of the Health button disables automatic opening, without
closing an existing window or preventing manual opening. Unlocking arms future
warnings without replaying old ones. The lock is saved in bit 8 of the native
`interface` word, independently of Targeting; legacy saves default to unlocked.
Damage/open/close requests retain their desired state across the slide/scale animation.
NN notifications are filtered to physical equipment loss, critical engine/hull
and radiation damage. Shields and shield generators are excluded from health
monitoring; shield depletion, failure, destruction and restoration do not open Health.

The panel follows the right-side widescreen shift and hides in NeuroNet, letterbox
and with the HUD. The former ship wireframe in the weapon list is suppressed while
Health owns that view. Without an enabled Health section, HUD_Status retains its
previous behavior.

HUD_Status has Health and its lock on the left, with nanobots/count and shield
batteries/count on the right in both expanded and collapsed layouts. The expanded
consumables are shifted left by one lock-icon width (0.031), to X=0.358/0.411. Weapon
groups 1, 2 and 3 form a vertical column under the close cross, left of the weapon
numbers, with the original 0.024 pitch starting at the first group. They hide when HUD_Status is collapsed; all custom
buttons hide during its native animation. The weapon-group buttons are
ported from Whiskas/T-Mech's `HudWeaponGroups.dll` (the mod DLL matches
`plugins/HudInventory_RC1/HudWeaponGroups.dll`, SHA256
`EB3AC067F430A1E54ADD7EFFDFE67254971C46DE7F9220A5A0356DC9C6895515`).
The plugin's creation loop at `00419DEB` loads `HUD_weaponsgroup1..3.3db`,
its execution handler at `0041A18C` dispatches native commands `0x91..0x93`,
and its update at `0041A121` selects the current group's button with property `0xc`.
The port uses those same assets and commands, preserving native group editing,
keyboard switching, and server/save persistence. Groups 4–6 remain available through
the existing keyboard commands; none of the three buttons lights for those groups.

The Health open/slide icon reuses `HUD_targetedobject.3db`; its lock reuses
`HUD_target_window_lock.3db`, matching Targeting's artwork and 0.022 radius.
The earlier standalone `HUD_health.3db` asset remains available but is no longer
used by these controls. No icon, shared VMS or montage edits are required.
The three animation glyphs are independent native meshes generated by
`tools/make_health_controls.py`: `HUD_health_wing.3db`, `HUD_health_pause.3db`, and
`HUD_health_wing_lock.3db`. Their unique `UI_` materials use normal HUD tinting.
They render at half their original size (0.008 radius); their hit areas are unchanged.
No shared library is modified. Top/left reuse `HUD_target_view1.3db` and
`HUD_target_view2.3db`, respectively, at the original 0.016 radius.

## Separate targeting panel (port-only)

`[Targeting]` in the active `hud.ini` creates `HUD_Targeting`, a separate panel to
the right of `HUD_Target`. It uses the centred `root_second` variant of
`Interface/hud/hud_target2.cmp` produced by `tools/center_hud_target2.py`; geometry
continues to reference `interface.generic.vms`. The original two-panel CMP is
not suitable for this layout.

`enabled = true` activates the item; `position = -0.152, -0.300` places its centre
in native Win3D coordinates at depth -1. It follows the same widescreen shift as
`HUD_Target`, touching its right side near the bottom edge. Without the section,
the original target view is used. See the template in
`tools/targeting_hud/hud_block.ini`.

The panel owns the native target name, subtarget/location caption and rank
controls, reparented from `HUD_Target`. The same target controller renders its
view into this panel: wireframes with damage colours, planetary wire spheres,
scan sweeps and subtarget markers. It shows the same selection as the original
target view, including neutral objects; no selection leaves an empty background.
The contact/formation list and other action buttons stay in their original panel.
The redundant list/target-view switches in HUD_Target are hidden while Targeting owns
the view. New host-owned buttons occupy the old list slot and the slot to its left:
Targeting window and automatic-opening lock. Formation moves to 0.029 right of scan
in the expanded HUD_Target toolbar, retaining separate hit boxes.
The view is independent of the contact list's collapsed state. It starts hidden,
opens on a new eligible selection and closes when selection is cleared or is a waypoint
(`CSolar::is_waypoint`, independent of name-fix options). Lock blocks automatic opening,
but allows automatic closing and manual opening for an eligible target. Enabling lock
does not close an already open view. Unlocking opens the current eligible selection.
Manual close stays closed until a new target is selected. Rapid target changes update
desired visibility even during animation, so the latest selection wins.
Mouse hover and
subtarget selection use the new viewport. The panel hides with the HUD,
NeuroNet and letterbox.
Rank, target name and subtarget/location text are currently hidden, including on
hover. Subsystem text remains suppressed; toolbar buttons have localized tooltips. Their former
header space extends the wireframe viewport up to the inner top edge; the same
enlarged rectangle handles picking. The projection buttons appear only with a selected target. The left
autoselect toggle is available whenever the panel is expanded.
`vulnerable = true` in a ship/solar's `[CollisionGroup]` marks that group's
wireframe orange from full health. It defaults to false and is copied by archetype
inheritance. Real damage retains the native red/critical colours. This visual
marker does not modify health or fuses; cosmetic startup damage is unnecessary
for marked groups.

The "Toggle autoselect subtarget" button (using `HUD_nextsub.3db`) enables direct
weak-point and turret selection on a ship's world model without holding Ctrl. It defaults on,
stays enabled across target changes and shows its selected state on the button.
Autoselect and the auto-opening lock are stored per player in bits 6 and 7 of the
native save `interface` word, alongside projection bits 4..5. Bit 6 means disabled,
so old/new saves default to autoselect enabled and lock off. Each click updates the
server state for the next game save; loading a save replaces both values live.
HUD destruction resets transient hover/click data without changing saved preferences.
The nearest physical ray hit must belong to a live marked collision group or an attached
turret; ordinary hull surfaces in front block the pick. Turrets need no `vulnerable`
flag: `auto_turret` or an explicit `hp_turret`/`hp_turret_special_1..10` gun type
identifies them. Destroyed, detached and ordinary fixed guns are excluded.
Hover draws the subsystem's health-coloured wireframe
as five-pixel-wide ribbons against scene depth before HUD depth is cleared.
Edges crossing the near plane are clipped before expansion. Parts keep their live world
transforms and the local wire cache refreshes when instances or LODs change.
Turret barrels follow their live articulated transforms. Their world overlay uses
equipment health colours and the critical pulse, without the HUD's manual-gun active override.
Left press on a subsystem sends the native target command with the ship and subsystem
IDs on every click, including an already selected target; the matching release is
consumed even if autoselect is disabled meanwhile. Misses and right-clicks pass to
ordinary input. Disabling the toggle hides the overlay but keeps the selected subsystem.
The HUD and world overlay share the damage colour function and critical pulse clock;
world hover does not apply the HUD's extra grey/amber hover pulse. Modal screens,
UI hover, hidden HUD, lost focus, destroyed parts and scanner range gate selection.
Picking follows the model's physical collision surface (SUR); wireframe edges
come from its VMeshWire/mesh data.
Keyboard bindings are unchanged: reverse and firing need no modifier while autoselect is on.

Pythonlancer's `ShiparchManagerV2` uses `world/capital.py::Capital.get_damage`.
The staged generator patch replaces its cosmetic `*_init_dmg_*` fuse and the
matching HP padding with `vulnerable = true`. Effective post-startup HP and all
combat fuse actions are preserved. Both V2's active `shiparch.ini` and V1's
`shiparch2.ini` are migrated; unused init fuse definitions need not be deleted.
The tools in `tools/targeting_hud` validate the actual V2 templates, generator
methods, toggled input/pick logic, world transforms and saved projection state before installation.
The close button is visible with the expanded window, slightly beyond the top-right edge. It matches
HUD_Target's mesh and depth (-1.5), giving it the same apparent size.
The scale/slide animation now ends at the host's Targeting button; no persistent
collapsed icon remains below the detached view. Both host buttons follow HUD_Target's
layout and widescreen shift and forward their events to the detached controller.
`HUD_target_window_lock.3db` is standalone, with mesh
`HUD_target_window_lock_icon.lod0.vms`, material `UI_HUD_target_window_lock_icon_mat`
and embedded `Texture library / HUD_target_window_lock_icon.tga / MIP0` for artwork replacement.
The wireframe uses the full rectangle between the inner top edge and toolbar. Its camera distance
and centre fit the rendered vertices against all four side planes and the near
plane, leaving a two-pixel border; native target/status view sizes are unaffected.
The lowered bottom toolbar has five equally sized buttons, larger than the original
toolbar: autoselect, Vanilla, Fit, Top and Side. Previous/next subsystem buttons are hidden.
The centred row uses a 0.026 button pitch with separate horizontal hit boxes;
icon artwork retains its 0.016 normalization radius.
The two native subsystem buttons are reparented
here and are available for any selected object with subsystems, including normal
ships. Private montage copies and instance scaling normalize the icons without
changing their assets or other HUD controls. Projection buttons load
`HUD_target_view1.3db` (Vanilla), `HUD_target_view2.3db` (Fit) and
`HUD_target_view3.3db` (Top) and `HUD_target_view4.3db` (Side) from
`DATA/INTERFACE/HUD`. Missing custom icons fall
back to stock meshes; installation never overwrites those custom files.
Fit uses the existing fitted camera; Vanilla keeps the native
max-width camera distance; Top locks the fitted view above the object's hull;
Side fits it from the object's starboard side with its local Y axis up.
The selected mode stays highlighted and is saved per character/save in bits 4..5
of the native `interface` word (0 Vanilla, 1 Fit, 2 Top, 3 Side). Selection sends
the updated word through `SetInterfaceState`; native saves/autosaves and character
loading handle persistence. Old saves default to Vanilla. Existing projection indices
retain their button positions under the new order. The HUD reads restored state
even when it survives a load, and native HUD toggles preserve the projection bits.
The cross at the far right collapses this
panel into `hud_targetedobject.3db` centred on its bottom edge; clicking that icon
restores it with the same projection. Both directions use HUD_Target's native
ButtonScaler/ButtonMover sequence: 0.3-second cosine-eased scaling between
1.0 and 0.1, followed by a 0.3-second icon slide (reversed when opening).
Content and input are suppressed during the animation, as in HUD_Target.
Native watchers and the existing part cache continue
to handle selection changes and system exits. The labels and arrows are returned if the
new panel is destroyed before its controller. `HUD_TARGETING` diagnostics log
creation and content attachment.

### Editing projection icon textures

`tools/make_targeting_icons.py` prepares standalone `HUD_target_view1..4.3db`
files in `bin/targeting_icons/DATA/INTERFACE/HUD`. Each contains its own small
double-sided quad in `VMeshLibrary`, material and texture. No shared-library
edits or montage entries are needed. For icon N, the unique internal names are:

| Resource | Name |
|---|---|
| Mesh | `HUD_target_viewN_icon.lod0.vms` |
| Material | `UI_HUD_target_viewN_icon_mat` |
| Texture | `HUD_target_viewN_icon.tga` |

In a UTF editor, import your 32-bit TGA with alpha into
`Texture library / HUD_target_viewN_icon.tga / MIP0`. Keep the node name and
material reference; replace the payload. Each file is independent, so changing
one icon does not replace another icon's image. N = 1 Vanilla, 2 Fit, 3 Top,
4 Side. Restart the game to reload edited resources.
Keep the material's `UI_` prefix: the standard `dacom.ini` material map uses it
to select `HUDIconMaterial`, which applies normal, hover and selected HUD colours.

The generator also exports the original TGA payloads to
`bin/targeting_icons/textures`. Supply a directory containing all four named
TGA replacements with `--texture-dir` to rebuild the files programmatically:

```powershell
python tools/make_targeting_icons.py --source-dir D:/games/FL_MOD/DATA/INTERFACE/HUD --shared-vms D:/games/FL_MOD/DATA/INTERFACE/interface.generic.vms --out bin/targeting_icons
```

The tool writes a separate output directory, preserves existing per-icon images
unless replacement textures are supplied, and validates local mesh/material/
texture links and cross-file CRC uniqueness. It reads the shared VMS only when
converting legacy icons; standalone input meshes are reused directly.

## Target HUD (`HudTarget.dll`)

The plugin is six byte patches and no code of its own:

| Retail site | Patch | Port (`FREELANCER_HUD_TARGET_VIEW`) |
|---|---|---|
| `0x004cfe75` HUD_ContactList, double click on a row | `PUSH 1` → `PUSH 0` | `SetMode(0)`: stay on the contact list (`hud_contact_list.cpp`) |
| `0x004e3ce0` `FUN_004e3c90` (Slot14, the wireframe view) | `JNZ` → 6×`NOP` | the view is drawn in every mode, not only mode 1 (`hud_target_panel.cpp`) |
| `0x004e1f91` HUD_Target Update | `JZ` → `NOP NOP` | the three switch buttons are refreshed every frame |
| `0x004e203e` / `0x004e20ff` HUD_Target Update | `JZ` → `JMP` | both mode-transition blocks skipped: the target details stay up next to the list |
| `0x004e36da` `OnMoveFinished` | `OR` → `XOR` | the second write to `SwitchToTarget` clears it: the button is hidden |

Result: the expanded target panel shows the target's wireframe, name, sub-target and rank
together with the contact or formation list.

## Status HUD (`HudStatus.dll`)

The plugin writes one function into HUD_Status's HUDItem vftable slot 14 (`0x005d85f4`, the
empty `FUN_00401e90` of HUD_Target_Base). The port overrides `HUD_Status::Slot14`
(`hud_status_core.cpp`): gated by game option `0xa` ("HUD"), it saves the viewport, points the
view camera at the status panel's view object (the player ship; fixed orbit, shift -0.0125),
recolours the part cache for damage and draws it — the part-cache branch of HUD_Target's own
Slot14 without the wire sphere, the scan sweep and the sub-target bracket.

## Inventory ship view (`HudInventory.dll`, beta client)

A toggle in the inventory (`ShipView_Toggle`, tool tips IDS 3026 "Ship View" / 3027 "Ship
Inventory") replaces the item list with the ship. The plugin rebuilt a mode that the 2002-09-16
beta `freelancer.exe` really has; the ship view's behaviour is ported from the beta's
`ShipViewControl` (vftable `0x005cc0fc`: Update `0x0057a9b0`, Draw `0x0057a390`, MouseEvent
`0x0057a860`, picks `0x0057bef0` / `0x0057c1e0`, markers `0x0057c520` / `0x0057ca30` /
`0x0057ce00`). Retail still keeps that code's state — the hover `+0x4f0`, the selection
`+0x4fc..+0x508`, `ViewFlags` bits 4 / 5 and the colour `+0x4c4` — and `NN_Inventory` still
fills it; only the code that reads it was removed.

- the mounted items of the current filter page are tinted in `rect_color`; the hovered item
  pulses and the selected one shows the `+0x4c4` yellow;
- free hardpoints show `mountpoint.3db` markers: with no item selected, those of the page; with
  an item selected, those it fits plus grey ones of the page it does not fit; the marker under
  the mouse pulses, and entering one the item fits plays `ui_select_item`;
- the tool tip shows the item name, the hardpoint type caption, or "Weapon / Equipment Hardpoint
  (empty)" (IDS 1078 / 1079);
- a click on equipment selects it and finds its row across the filter pages (`0x15`,
  `NnInventory::PickShipViewHardpoint`); a click on a fitting marker mounts the selected item
  there (`0x16`);
- the name label, a frame, a hull damage bar and an info button come with it (positions from
  the plugin: the beta's window layout is different);
- kept from the plugin: hulls of radius over 30 are picked by item origin instead of part
  spheres, the hardpoint reach grows with the hull, and from radius 80 the smallest equipment
  is drawn enlarged.

Code: `NnInventory::CreateShipViewModeControls` / `UpdateShipViewMode` / `PlaceShipView` /
`PickShipViewHardpoint` (`nn_inventory.cpp`), `ShipViewControl::UpdateInventoryHover` /
`DrawInventoryEquipment` / `PlaceInventoryMarkers` / `PickInventoryEquipment` /
`PickInventoryHardpoint` / `MouseEvent` / `ApplyInventoryModelOverride`
(`ship_view_control.cpp`). The row-visibility hook splits retail's two hide flags (`[ESP+0x10]` /
`[ESP+0x11]` of `FUN_0047f3e0`). Only the inventory's own `ShipView_Control` gets the new
behaviour; one part applies to every ship view, as in the plugin: the fixed camera distance 14
of `SetInstance` is skipped (Adoxa's `74 → EB` at `0x005855c0`), so every preview frames its
hull.

### Data

- `DATA\INTERFACE\NEURONET\INVENTORY\gotoinven.3db` — the toggle's second mesh (required; from
  the plugin's `DATA`). The stock `mountpoint.3db` (the same as the beta's) is the marker; the
  plugin's replacement works too, with `mountpoint_size = 0.7`.
- `DATA\INTERFACE\HudInventory.ini` (optional), read once on the first ship-view draw:

  ```ini
  [HudInventory]
  debug = false          ; true: re-read the file every time an inventory opens
  mountpoint_size = 1.2  ; port-only: marker scale (beta 1.2; 0.7 for the plugin's mesh)
  ship = SHIPS\RHEINLAND\RH_BATTLESHIP\rh_battleship.cmp, center, 0, -70, 0
  ship = SHIPS\RHEINLAND\RH_GUNSHIP\rh_gunship.cmp, radius, 80
  ```

  `center, x, y, z` moves the hull inside the preview, `radius, r` (r ≥ 1) overrides the radius
  used for framing and picking. The key is the hull's `.cmp` path (`CreateID`, case-insensitive).

The mod's files are third-party and are not part of this repository.

## Differences from the plugins and the beta

- The ship view follows the beta, not the plugin: equipment of every page is pickable; the
  highlight is the `+0x4c4` yellow instead of the plugin's blue and amber; the hardpoint reach is
  0.9 instead of 0.45; markers are drawn with renderer flags 0 at the beta's scale, and the
  equipment without the plugin's blue ambient.
- Not ported from the beta: its wireframe and rectangle draw (`ViewFlags` bits 3 / 2, which
  retail dropped for every ship view) and the `(0x26, this, hover)` message on a right click,
  which matches none of retail `NN_Inventory`'s buttons.
- `PickShipViewHardpoint` reads the dealer's trade mode; the plugin read `+0x978` of the
  inventory itself, past the end of a plain `NN_Inventory` (0x974 bytes).
- The model override is keyed by the path `ShipViewControl::LoadMesh` loaded, not by the
  engine's archetype record of the framed instance (the same string), and applies only while
  the hull itself is framed.
- `stricmp` on hardpoint names treats a missing name as empty instead of crashing.

Status: built only as source here — not yet compiled or tested in game. See
[re/deviations.md](re/deviations.md) (HUD-PLUGINS).
