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
target and applies its saved visibility to the first hostile ship selection; subsequent
selection changes follow its normal auto-open rules. Weapon-group restore activates
the saved group once a ship is available, instead of forcing group 1.

Backspace (`USER_MINIMIZE_HUD`) temporarily hides the detached windows too; pressing
it again restores their desired state. This temporary override is not saved and
does not alter either window's open/closed preference. Radar and its buttons are
independent of Backspace. Its enabled flag is saved in bit 17; bits 18..19 store
range index + 1 (zero uses the HUD INI default).

The native preferences menu has a separate **Miscellaneous** button with General
and Navigation tabs. Radar auto-show and route generation use drop-down lists:
click the value field to open the choices in a dark NeuroNet panel with native
fonts, thin frames and yellow marking of the current value. Hover/keyboard focus
has a blue background. The list draws after all other rows and captures input;
Esc, Tab or an outside click dismisses without changing the value. Up/Down,
Home/End and the wheel move the highlight; Enter/Space or a click chooses an item.
The former Interface-page Miscellaneous block moves here and continues to use
PerfOptions: tooltips and rollover help are on Navigation; transition skipping,
maneuver-bar auto-hide and cockpit geometry visibility stay on General. HUD controls follow:
radar auto-show (no / any contact / enemy), enemy status auto-open, ship status damage
auto-open, the global auto-turret switch and energy reserve (0..90%, steps of 5).
Yes/No options use native checkboxes again; numeric percentages retain their own
stepper. HUD changes are staged until the native Apply confirmation; Cancel discards
them. These rows are unavailable in the main menu until a game is loaded. The former
HUD settings window and maneuver-bar gear are removed. The two host-panel auto-open
locks and large auto-turret button are also removed; Health's separate wing-animation
lock and individual weapon-row auto-turret buttons remain.

Drop-down prototype (2026-10-30): `NnDropdownPopup` provides native wire buttons,
ItemName text and a filled overlay, shared by radar auto-show and route generation.
The owner renders it last and forwards keys before its ordinary Esc handler.
Popup capture is released on choice, dismissal, page changes and destruction;
an outside click is consumed through release. The production dropdown harness
checks keyboard/mouse selection, hover, wheel, upward placement, dismissal,
stale events and teardown with an outstanding child capture. The settings harness
also checks staged selection, tab changes, unavailable controls and persistence.
Release Win32 and both harnesses passed. Installed package:
`src/obj/flight_actions_install/20261030_101308`; backup:
`BACKUP/codex_flight_actions_20261030_102729_681`. All seven payloads and four DLL
dependencies were hash-verified; `port.ini` was preserved byte-for-byte. The
drop-down's appearance still needs an in-game check.

Drop-down visibility fix (2026-10-30): preferences keeps its Position at zero
and moves the controls to z=-1 with SetOffset. The new popup inherited plain
WinControl positioning, which ignored the attachment offset and left its panel
and choices at the camera plane. It now derives its anchor from the owner's
Position plus Offset, including when children reposition their parent during
creation. The regression reproduces the original failure before the fix and
checks the real preferences construction order. It also runs production wire
button press/release, picking and capture code to open the list and select a
choice; drag-out, outside dismissal and reopening are covered. Native pickable
and active/visible flags in both UI harnesses now match Win3D.
Release Win32 and both UI harnesses passed. Installed package:
`src/obj/flight_actions_install/20261030_104553`; backup:
`BACKUP/codex_flight_actions_20261030_104626_145`. All seven payloads and four DLL
dependencies were hash-verified; `port.ini` was preserved byte-for-byte. Live
appearance after this correction remains to be checked in game.

Resolution-style Miscellaneous selectors installed (2026-10-30): both tabs use
the same vertical UICycle dimensions and separate value/arrow frames as the
native video-mode control. Boolean ranges are 0..1; other ranges and staged
saving remain unchanged. The existing settings harness now operates the arrow
controls for every row and verifies layout bounds, native steps, persistence,
Apply/Cancel/defaults and unavailable settings. Release Win32 passed.
Package: `src/obj/flight_actions_install/20261030_024728`; backup:
`BACKUP/codex_flight_actions_20261030_025022_443`. Seven payloads and four DLL
dependencies were hash-verified; installed configuration was preserved. Visual
appearance still needs an in-game check.

Navigation also contains Standard/Avoid obstacles route generation, F2 route following
and automatic base docking. They are global preferences saved to `navigation.ini` in
the user data directory, with `port.ini [Navigation]` as installation defaults.
They are available before loading a game. Edits survive tab changes and are
committed by Apply; Cancel discards them. Defaults affects only the active tab.
F2 includes waypoint passage, trade-lane entry and jumps through gates/holes.
The separate base-docking permission covers only bases and planetary docking
rings. When it is off, F2 still uses lanes and jumps, then continues from the
checked approach with the native F2/Go To command to the destination base.
It keeps flying instead of stopping at the preceding waypoint; native Go To
owns the remaining distance and slowdown, with F3 left to the player.
Disabling route following restores native F2 and
leaves an already running native maneuver intact. A Dock underway can finish.

Navigation-tab validation (2026-10-30): the production preferences harness covers
tab filtering, both generator values, tooltip migration, staged edits, persistence
after reload, Apply/Cancel/defaults, write failure and main-menu availability.
The route harness executes the real Dock handoff with automation on/off for bases,
gates, holes and lane entrances, and checks disabling F2 without braking.
Geometry, maneuver/camera checks and Release Win32 passed. Installed package:
`src/obj/flight_actions_install/20261030_014745`; backup:
`BACKUP/codex_flight_actions_20261030_014915_893`. Seven payloads and four DLL
dependencies were hash-verified; installed configuration was preserved. Visual
layout and live flight still need an in-game check.

Route/base distinction correction (2026-10-30): F2 always traverses trade lanes,
jump gates and jump holes on its route, independently of `auto_dock`. Only bases
and planetary docking rings require that permission. The UI now says Follow route
with F2 and Auto-dock with bases; the Beta generator is labelled Avoid obstacles
(Russian: Обход препятствий), while its saved `beta` value stays compatible.
Production-handler checks cover both permission values for all five destination
types, plus settings persistence. Release Win32 and route/maneuver checks passed.
Installed package: `src/obj/flight_actions_install/20261030_015321`; backup:
`BACKUP/codex_flight_actions_20261030_015414_268`. All seven payloads and four DLL
dependencies verified; installed settings preserved. Live flight remains untested.

Station-departure and waypoint-marker correction (2026-10-30): a ship near
Tokyo's composite hull can be inside overlapping conservative obstacle spheres
while outside the actual mesh. The fixed detour rings around their merged
sphere could miss the common outward direction. The visibility graph now also
tries ship-relative exit points, including tangents to overlapping guards.
Every added edge uses the existing solid/atmosphere/damage-zone checks; no
station component is ignored. The regression reproduces the old no-path result
between core/dock guards and checks departure through both map refinement and
F2, alongside rotated geometry and rejection of an internal destination.

The selected waypoint Solar is matched to the first player route entry by
AutoId, and to the first mission entry by its owner/index. Exact coordinates
are no longer required for that client proxy: `SetWaypoint` can reuse one
within two metres. This prevents a duplicate route marker and an incorrect
mission caption; later route selections keep the route caption, and separate
mission objectives remain distinct. `check_waypoint_markers.py` executes the
production identity/caption functions with drift, consumed indices, later
selections, object targets and independent mission entries. Route, marker,
world-HUD and maneuver/camera checks passed, as did Release Win32. The
departure fixtures use simplified guard spheres, not a live physics capture.
Installed package: `src/obj/flight_actions_install/20261030_022426`; backup:
`BACKUP/codex_flight_actions_20261030_022456_589`. All seven payloads and four
DLL dependencies verified; `port.ini` preserved byte-for-byte. Live flight and
the marker's on-screen appearance still need an in-game check.

Object-arrival correction (2026-10-30): map refinement previously sent a
non-dockable destination to the point planner at its centre. Tokyo's `ku_ksu_03`
in `KU_KYUSHU/ku_ksu.ini` demonstrates the failure: `odissey_core` is at
(-50000, 0, -41560), and `odissey.cmp` has a Level0 VMeshRef radius of 1650 m.
The centre lies inside its own obstacle. Map refinement and F2 now share
`PlanApproach`, selecting arrival points outside physical bounds/atmosphere,
clearance and hull radius. Nearby station components remain obstacles. The
object ID stays the final goal; any following leg starts at the actual arrival
point. No unchecked segment into the object's centre is added.

With base docking disabled, the final checked approach now invokes the existing
HUD F2/Go To request instead of cancelling with throttle zero. The native
object command controls final approach and slowdown; route ownership is released
without a cruise-off command. Lane/gate/hole traversal remains automatic.

`check_object_routes.py` executes production map/refinement/planner functions
against Tokyo's actual core location/radius and simplified nearby-solid fixtures:
12 approaches, an occupied near side, a following waypoint, atmosphere and
unreachable goals. The input harness executes the native HUD Go To case and
checks target mode/ID, retained cruise/throttle and absence of a Dock request.
These are isolated checks, not a live scene/physics capture. Route geometry,
maneuver/camera checks and Release Win32 passed. Installed package:
`src/obj/flight_actions_install/20261030_020554`; backup:
`BACKUP/codex_flight_actions_20261030_021246_429`. Seven payloads and four DLL
dependencies hash-verified; installed settings preserved.

All these settings use the native save `interface` word. Bits 20..21 encode radar
auto-show (0 manual, 1 any, 2 hostile); bits 22..23 store auto-turrets disabled and
an explicit-value marker; bits 24..28 encode reserve / 5 + 1 (zero uses `port.ini`).
The master switch gates automatic fire without changing individual gun selection
or activation. The native cockpit flag (bit 3) is restored in both directions on
space entry, so loading an external-view save clears a previous cockpit preference.
Temporary rear/turret/script cameras do not write that preference.

Radar automation polls the same detectable contacts as the radar every 0.2 seconds,
even while closed. Hostile mode includes incoming missiles. After matching contacts
disappear, a 1.5-second grace period precedes closing. A manual close suppresses
automatic opening until matching contacts leave; manual opening keeps it open.
Choosing an automatic mode clears that manual-open override. The model slides down
off-screen on close; contacts and scanning resume only after opening completes.

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

Health restores its saved visibility and top/left projection. New/legacy saves
without an explicit visibility setting start closed. Its first button in
HUD_Status opens/closes it using the same scale/slide sequence as Targeting.
The detached Health and Targeting panels have no close crosses. New damage severity transitions or accepted NN damage warnings reopen
it when unlocked. Merely retaining the same damage, critical-colour pulsing, hover,
repairs and loading an already damaged ship do not count as new damage. The monitor
uses hull, collision-group and equipment health bands (75%, 50%, below 25%, destroyed),
including disappearance of an attached part; vulnerable groups retain their orange
baseline. No geometry is rebuilt for this monitoring.

The ship-status option in Miscellaneous preferences disables automatic opening, without
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

HUD_Status has Health on the left, with nanobots/count and shield
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

The Health open/slide icon reuses `HUD_targetedobject.3db` at 0.022 radius.
Its former auto-open lock is now an option in Miscellaneous preferences.
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
the view. The Targeting-window button occupies the old list slot;
automatic opening is configured in Miscellaneous preferences. Formation moves to 0.029 right of scan
in the expanded HUD_Target toolbar, retaining separate hit boxes.
The view is independent of the contact list's collapsed state. It starts hidden,
opens automatically only on selection of a hostile ship and closes when selection is cleared or is a waypoint
(`CSolar::is_waypoint`, independent of name-fix options). Lock blocks automatic opening,
but allows automatic closing and manual opening for an eligible target. Enabling lock
does not close an already open view. Unlocking opens the current selection only if
it is a hostile ship. Hostility uses the native HUD attitude classification
(`GetAttitudeClass(player, target) == -1`, target attitude <= -0.6); hostile solars,
neutral and friendly ships do not trigger automatic opening. Manual opening remains
available for every eligible target, and switching away from a hostile ship does not
automatically close an already open panel.
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
The Targeting toolbar exposes this toggle for a live ship of type CRUISER
(including the mod's destroyers) or GUNBOAT. Other targets hide it without changing the saved mode.
World hover, direct subsystem clicks and the persistent world wireframe on these two
ship types require a hostile HUD attitude. Neutral/friendly ships do not intercept
subsystem clicks; attitude changes take effect on the next draw or click.
Autoselect and the auto-opening lock are stored per player in bits 6 and 7 of the
native save `interface` word, alongside projection bits 4..5. Bit 6 means disabled,
so old/new saves default to autoselect enabled and lock off. Each click updates the
server state for the next game save; loading a save replaces both values live.
HUD destruction resets transient hover/click data without changing saved preferences.
The nearest physical ray hit must belong to a live marked collision group or an attached
turret; ordinary hull surfaces in front block the pick. Turrets need no `vulnerable`
flag: `auto_turret` or an explicit `hp_turret`/`hp_turret_special_1..10` gun type
identifies them. Destroyed, detached and ordinary fixed guns are excluded.
Hover and the currently selected subsystem draw their health-coloured wireframes
as five-pixel-wide ribbons against scene depth before HUD depth is cleared.
The selected subsystem keeps its world wireframe after the pointer moves away,
including over UI or during mouse flight; hovering another part does not erase it.
The panel uses its native red selection arrows and damage colours, without an extra
yellow selected-part highlight. Selection is resolved from the player's live target
each frame and stops drawing when the part is destroyed, detached, cloaked or out of scanner range.
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
UI hover, hidden HUD, lost focus, destroyed parts and scanner range gate picking.
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
collapsed icon remains below the detached view. The host button follows HUD_Target's
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
The window button on HUD_Target collapses/restores this panel with the same
projection; the detached panel has no close cross. Both directions use HUD_Target's native
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

## Texture-free targeting markers (port)

The 16 targeting montage names use release-derived contours and matching Beta
meshes from `hud_marker_beta_data.h`, rendered by `hud_marker_geometry.h`: target corners,
contact/player/loot arrows, watch-list hats, quotes and waypoint diamonds, including
backgrounds. `tools/targeting_hud/export_beta_markers.py PATH/TO/BETA/DATA/INTERFACE/HUD --retail-atlas PATH/TO/ButtonTextures.txm`
exports the geometry and source SHA256 hashes without modifying the game files.
NumPy/SciPy/Pillow are offline exporter dependencies only. The client embeds the resulting
18 small native/derived meshes and does not require the Beta installation at runtime.

The release appearance takes priority wherever Beta differs visibly. The target
arrow and its background, target corner, target-arrow hat, target quotes, contact
hat and double-ring waypoint arrow are traced from the release atlas by
`trace_retail_marker.py`. It traces only
the bright core, simplifies the contours, and triangulates them with holes intact.
The atlas's baked halo and translucent quotes separator are excluded from opaque
geometry. Source hashes identify the exact reference; runtime never reads the atlas
for these markers. Selected/unselected player arrows retain their respective Beta
meshes; the side triangle is from `HUD_reticle_arrows`.
The Beta waypoint itself is a textured quad; the native `HUD_waypointhat`
diamond supplies the single-ring waypoint target and convex background. The
double-ring arrow follows the release's thinner strokes instead of Beta's wide bands.

Filled silhouettes are used for the background tiles. Foreground arrows have
separate detail meshes, including the release target arrow's outer frame and inset.
Contact, loot and player contours are derived from their matching Beta silhouettes.
Reusing the solid background
for the foreground would erase this internal drawing. The selected player now
draws `PlayerArrowBackground` before `PlayerArrow`, matching the unselected path.

The release target arrow is offset sideways inside its atlas tile. The exporter
registers the bisector of its two long exterior flanks to the tile-centre diagonal,
which is the axis used by the existing 3D health/shield bars. One rigid transform
applies to the target background, detail, hat and quotes together (approximately
+6/-6 tile units, with a 0.024-degree rotation). This preserves the release
contours while removing the roughly four-pixel lateral mismatch at the reported
1080p marker size. The bars themselves retain their existing placement.
The aligned flank intersection and bisector are checked by the C++ fixture;
atlas coverage comparisons apply the same rigid registration to the reference.
The concurrently installed client on 2026-10-29 at 15:45 already contains all four
aligned vertex arrays (verified byte-for-byte), and its EXE/PDB SHA256 matches the
current successful Release build. No older staged binary was copied over it.

These remain flat HUD meshes. Halos are removed: each marker emits its original
triangles and a one-physical-pixel antialiased edge only. The former 40 displaced
copies multiplied the geometry and exposed the scratch index buffer overflow
fixed below. Core opacity, internal cutouts and release-derived contours remain
unchanged; marker geometry no longer includes any glow passes.

`NnMontageDrawTileAt` routes these names before accessing the texture shape. Size,
RGBA, selection pulses, mirror modes, camera projection, arrow angle, picking and
target eligibility retain their existing callers. Other montage tiles, including
talking portraits and interface controls, keep the textured path. Contact brackets
and lead crosses already used geometry; their two-pixel 1080p line weight now
scales with display height above 1080p (four pixels at 2160p).

`ScreenQuadEnqueueColorQuad` clips coloured geometry to the camera viewport and
reuses the existing `buttons` batch, upload buffers and flush states. A triangle
uses a repeated fourth vertex. RP8/RP9's scratch buffer holds 16384 indices, so
lists split at 2730 quads / 10920 vertices (six indices per quad), without a separate
draw call for each marker. The former 60000-vertex cap exceeded that buffer and
caused marker batches to be silently skipped. Untextured nodes explicitly select
diffuse vertex RGBA, restoring MODULATE before subsequent textured UI draws.
No new texture files or renderer DLLs are
required. The shared `ButtonTextures.txm` still loads through the existing shape
database, so this change does **not** claim reduced atlas memory or measured FPS
gains; it removes the marker drawing's dependence on raster resolution.

Validation: `python tools/targeting_hud/check_marker_geometry.py` compiles the
production mesh, montage routing and clipping/batching code. It checks native core
coverage, unfilled foreground interiors, absence of halo copies and edge AA, scaling, mirror modes, rotations, alpha
interpolation at clipped edges, hidden geometry, missing marker textures, unrelated
tile fallback, and large batches. The production GPU-upload function is also run
against a strict 16384-index fixture: valid batches draw every vertex; an oversized
negative control reproduces the previous lock failure. Textured/untextured stage
transitions and restoration are checked. Optional `--preview-atlas PATH/TO/ButtonTextures.txm`
checks emitted opaque geometry against the release atlas's bright cores (including
the quotes separator and target inset), and creates `waypoint_marker_details.png` in
`src/obj/hud_geometry` (Pillow/NumPy). `retail_arrow_layers.png` previews assembled
green arrows; `target_arrow_release_comparison.png` compares the target arrow separately.
`waypoint_arrow_thin.png` compares the waypoint arrow's two thinner contours.
The Release RP9 client builds and the no-halo EXE/PDB are installed in
`D:/games/FL_MOD/bin`, with SHA256 verification and backup
`BACKUP/codex_hud_markers_no_glow_20261029_153036_652`. In-game visual validation
remains pending.


## Freeflight actions (port-only prototype)

Build with `FreelancerPlayerFlightActions=1` (`FREELANCER_PLAYER_FLIGHT_ACTIONS`).
The diagnostics sheet enables the feature; builds without that sheet default to 0.
`port.ini [FlightActions] enabled=0` disables
an enabled build; missing `enabled` means 1. Freeflight gets the expanded
Cruise + clockwise spiral + engine-kill 180-degree turn + reverse/strafe strip.
Go To gets Cruise + sine weave. The weave supplements the active Go To autopilot;
no Beta Evade directive or NPC personality is copied.

The actions also have assignable cockpit shortcuts in Options > Controls.
All three start unassigned; no default keys or modifiers are reserved:

| Default | Freeflight | Active Go To (F2) | KeyCmd nickname |
|---|---|---|---|
| Unassigned | Clockwise spiral | Sine weave | `USER_PLAYER_EVADE` |
| Unassigned | Engine-kill 180-degree turn | No action | `USER_PLAYER_REVERSE_TURN` |
| Unassigned | Reverse + alternating strafe | No action | `USER_PLAYER_REVERSE_STRAFE` |

The same key toggles its action, just like the button. Key repeat and release do
not trigger it. Mode-inapplicable keys do not cancel an active action. Chat/input
focus, modal screens, cutscenes, launch, tradelanes and locked maneuvers block it;
freeflight actions additionally require cruise to be off. Button tooltips show the
current binding, including a user remap. The command IDs are 0xd0..0xd2 and remain
stable in builds without auto turrets. Loading an old user map leaves these actions
unassigned and preserves all existing control bindings.
Saving an unbound action writes an empty KeyCmd so it stays unbound after reload.
No game INI or resource DLL edits are needed for the shortcuts.
`python -B tools/flight_actions/check_hotkeys.py` checks the production dispatch,
mode gating, unassigned defaults and save/reload behavior in controlled fixtures.

The controller writes bounded steering torque and native thrust controls after the
normal object update and before physics. It never sets position, orientation or
velocity. The clockwise spiral tracks an unwrapped full turn; the reversal tracks a
half turn with the engine disengaged. Completion checks actual angular progress
and angular velocity; these two figures have a 12-second timeout. Ship torque, angular
drag, inertia and nudge force remain authoritative. A missing required force
makes that action unavailable. There is no invulnerability or recharge cheat.

Reverse/strafe holds the starting orientation and applies full reverse throttle
with native strafe, starting left immediately. It switches right after
`port.ini [FlightActions] reverse_strafe_interval` seconds, then left after the
same interval, indefinitely. The default is 2.0 seconds; any finite positive
value is accepted, invalid values fall back to 2.0. Restart after changing the
config. This action has no duration limit, obstruction veto or frame-stall
timeout; its bounded phase timer handles long frames without accumulating cycles.
Engine `reverse_fraction` and ship strafe force/power use remain authoritative.

Go To's sine weave physically turns the nose left and right with bounded steering
torque while the native autopilot continues throttle, cruise and arrival handling.
Forward engine thrust creates the curved flight path; the action adds no lateral
nudge or strafe. It reads
the actual Go To destination (object or point), independently of the selected
weapon target. Scripted spline routes are excluded. `goto_weave_interval`
(default 2.0 seconds, finite positive values) is one half-wave; the complete
cycle takes twice that time. `goto_weave_angle` (default 25.0 degrees, clamped to
0..60, nonfinite values fall back to 25.0) sets the requested yaw amplitude on
either side of the destination bearing. The old `goto_weave_strength` setting is
unused. The wave ramps in over one second, starts toward the left, repeats without
a duration limit, and fades near the destination. The ship follows the changing
orientation using its actual torque, angular drag and inertia; neither orientation
nor velocity is assigned. If the initial bearing error exceeds 60 degrees, native
Go To first aligns the ship before the wave starts. Native steering is restored
before each object update and on cancellation unless another owner has already
changed it. Arrival, target loss, a behavior change or an obstructed look-ahead ray
cancels the weave and hands steering back to Go To. The ray veto is not full path
planning. Actual turn amplitude and trajectory depend on ship handling.

Clicking the active action again, Escape, manual steering, throttle, strafe, cruise,
engine toggle or afterburner cancels it. Mouse movement only cancels when it is
actually mouse-flight input, outside the HUD and outside cockpit free look.
Weapon aim and firing otherwise remain available. Engine state and throttle
are restored on completion/cancellation while the same ship is still in
Freeflight; a new autopilot state owns its own settings. A watched ship identity,
system check, docking/launch/lane/letterbox/mission-lock checks and frame-stall
cancellation protect handoffs. The simulation tick, not HUD visibility, drives
the action. Pause does not advance it.

During Go To weave, the third-person camera uses a stable route direction and
the initial up reference, rather than following the ship's alternating yaw/roll.
Its heading is measured from the route's starting point, with smoothing for a
moving destination. Entry and release blend with the live native camera around
the ship; switching out of third-person view clears the stabilization blend.

The spiral's third-person view eases outward and blends toward the initial up
direction; reverse/strafe uses the normal camera. The engine-kill 180-degree turn
captures the current third-person camera orientation and ship-relative offset.
The view follows the ship's translation while holding the initial part of the
turn. When the engine will resume with positive throttle, the last half of the
turn can start the camera return early: remaining angle divided by actual angular
speed must be at most two seconds. This is an estimate that follows ship handling,
not a fixed delay after clicking. The return takes three seconds, easing around
the ship at camera distance rather
than interpolating a straight line through the hull. The orbit angle is unwrapped
around 180 degrees to avoid side flips. Orientation blends to the live native
camera pose; native camera history keeps updating throughout the hold.

If early return is unavailable (including zero throttle or an engine that will
stay disengaged), natural completion leaves the camera holding until forward
velocity exceeds 3 m/s, contributes over half of total speed, and remains so for
0.2 s, or the player cancels manually. Restoring throttle on completion does not
restart a camera return already underway.

Manual cancellation also releases a waiting camera smoothly, without replaying
throttle restoration once the action is already complete. Switching camera,
ship or system, death, docking and cinematics discard the held pose. Cockpit
view is retained. Zero throttle can leave the camera waiting until the player
acts. Two look-ahead rays veto an obstructed rotation action but do
not guarantee hull clearance or predict moving obstacles. These are deliberate
pilot actions, not an automatic missile defense system. Multiplayer and actual
in-game handling/camera/UI appearance still need play testing.

The original Beta meshes contain their own materials/textures. Stage them from
the user's installation (never commit those original assets):

```powershell
python tools/flight_actions/stage_icons.py --beta-root 'D:/games/Freelancer Beta'
& tools/flight_actions/build.ps1 -Enabled 1 -Isolated
```

Local source assets are staged in `assets/hud/extra`; installation places them
in the game's `DATA/INTERFACE/HUD/EXTRA`, together with the custom Cloak icon.
The buttons are omitted if any required asset is
missing. `HUD_drasticevade` identifies the spiral, `HUD_turntoface` the
turn, `hud_mnvrstrafe` the reverse/strafe loop, and `hud_mnvrevade` the Go To
sine weave. Their
historical behavior is not copied. English/Russian tooltips identify
the buttons; there are no static direction or angle labels. Freeflight uses the
original wider `Interface/Baseside/CITY_maneuvertab3.cmp` backdrop, with all four
buttons centered at 0.032-unit spacing inside its native bounds. The whole tab
and its buttons are offset 0.048 units right of the Freeflight anchor, placing
Cruise at the original anchor. Go To uses `CITY_maneuvertab2.cmp`, two buttons
at the same spacing, and a 0.016-unit right offset that retains Cruise's original
anchor. Other behaviors restore `CITY_maneuvertab1.cmp`. Lateral-only Freeflight
dodges have been removed.

`tools/flight_actions/test_control.cpp` simulates a torque/drag/inertia-limited
body at 30, 60 and 144 Hz, both directions, half/full turns and three inertias.
It checks angular convergence, braking, torque limits, nonfinite error handling
and that the initial identity orientation cannot complete a full roll. It also
checks clockwise orientation, reverse/strafe phase at 30/60/144 Hz, custom and
invalid intervals, pause and skipped periods over a 24-hour simulation step.
Camera simulations check held poses throughout a half turn/backward drift,
forward-speed stability, pause/manual abort, camera distance through a 180-degree
orbit, angle wraparound, rotated camera bases and exact native handoff at
30/60/144 Hz (`flight_action_camera.h`). A torque-limited half-turn also checks
that the early return starts in the last half, before completion, takes three
seconds, and avoids the previous fast orbit.

Go To simulations integrate torque, angular drag and inertia into actual yaw,
then forward thrust into the flight path at 80/300 m/s. They check left-first
entry, repeated turns in both directions, bounded lateral motion, forward
progress, configurable periods, and fixed camera heading despite the physical
yaw at 30/60/144 Hz and three inertias. Vertical destinations also retain a valid
yaw axis and camera basis.

Updated `D:/games/FL_MOD` on 2026-10-29 with Go To's repeating yaw turns,
stable route camera and original Beta `hud_mnvrevade` icon. The default requested
angle is 25 degrees on either side, with a four-second complete cycle; both are
configurable. Forward thrust traces the wave. The existing Freeflight actions,
early three-second reversal camera orbit and native Miscellaneous preferences page are
included. Release Win32 and the physical yaw/camera harness passed; imports
against four installed DLLs and all seven installed payload hashes (client/PDB,
preserved config with the new angle default, and four icon models) were checked.
Backup: `BACKUP/codex_flight_actions_20261029_234105_186`.
The port entry point is `bin/freelancer.exe`; the legacy `EXE` launcher is not
changed. The new Go To handling and camera still need validation in-game.

Installed package: `src/obj/flight_actions_install/20261029_233745`.

### F2 route autopilot and Beta corridor planner

With `FreelancerPlayerFlightActions=1`, `[Navigation] autopilot=1` extends F2:
the selected player route is flown in order, free-space points are consumed in
the simulation tick, and dockable destinations use the native Dock directive.
The map selects the first route point when its response arrives. F3 remains
available but is not required to finish a route. Selecting a planet resolves
its docking ring before planning the approach. Selected ships retain native
Go To behavior.

Intermediate Go To directives use the native fly-through stop style. Their
destination is updated through Slot10 without exiting/re-entering the behavior,
so passing a point does not deliberately disengage or recharge cruise. Native
obstacle avoidance still controls cruise. Passage uses the swept movement
segment and a radius that includes the player's hull. The final point brakes;
docking approaches hand over at a checked arrival point, normally 2000 m out,
or farther out for a larger hull/clearance or occupied arrival directions.
Lane exits and the arrival gate after a jump are consumed as arrival markers;
the next leg resumes after the native transition releases control. Keyboard
steering, engine controls, other maneuvers, route edits, death, and session
teardown cancel ownership. Mouse-flight mode and held LMB temporarily override
Go To steering while retaining F2 and cruise. Releasing mouse steering replans
the current leg from the ship's position and resumes the automatic heading.
Head-look input remains camera-only, including Space in cockpit look.
Cruise changes preserve Go To and
throttle, and the chosen cruise state carries over to following waypoints.
Pressing Cruise during a sine weave cancels the weave and requests cruise on;
when already cruising, this continues normal Go To without stopping/recharging.
Without a weave, the Cruise command retains its normal on/off toggle.
Freeflight suspends the generated route. A subsequent F2 requests a fresh route
from the current ship position to the saved final destination, then resumes when
the response is ready. Space waypoint selection uses the HUD marker's AutoId
rather than trying to match its temporary solar id against ObjectId=0. Manually
authored waypoint lists retain their selected entry and remaining objectives.
Changing the map route, landing, or cancelling a pending request prevents stale
responses from automatically taking control.
Mission control locks and server docking decisions remain authoritative.

`[Navigation] route_generator=beta` is an adaptation of the user's Beta
`DLLS/BIN/Content.dll` (SHA256
`048852D064817779370ECAF54D461ADD1A67ED0F76F8F9BBE7D5512E65D6B4C4`).
The recovered pieces are the ordered path-label polyline construction
(`06EAB2E0`: nearest zone ends, midpoint joints, 5000 m loop closure), the
`06EDB320` corridor travel costs (distance/300 along a path, distance/40 outside),
and the -0.2 reputation cutoff observed in `06EDA310`. The reconstruction tools
are in `tools/route_autopilot`; IDA research output stays under `src/obj`.

The port uses a bounded visibility-graph search instead of the Beta's greedy
path walk. Server-generated system connections and trade-lane topology are
retained. Free legs in the loaded system are refined using friendly patrol
corridors, solid solar bounds/atmosphere ranges, and native damage-zone shapes.
Ship radius and configurable clearance pad hazards. An outward escape from an
initial hazard is permitted; entering one is rejected. No-path/point-budget
failure clears the generated map route, and the executor refuses a failed leg.
Unloaded systems are planned after entry. This is a hybrid planner with recovered
Beta rules and a new safety extension, not a binary-identical Beta generator;
the inspected Beta functions did not establish a guarantee of avoiding every
hazard. `retail` keeps the original map generator; F2's local safety planning
still operates. Dynamic combat and moving obstacles remain the native pilot's
responsibility. Mission objective lists remain owned by the mission system.

Validation: Release Win32, original maneuver/camera simulations, and
`tools/route_autopilot/check.ps1` (30/60/144 Hz passage, long-frame crossing,
Beta path joints/costs, atmosphere detours, outward escape, no-path and graph
bounds). Configuration merging is additive/idempotent and retains existing
planner choices. Native docking, jumps and a complete route have not yet been
verified in a live flight.

Installed on 2026-10-30 into `D:/games/FL_MOD/bin`, package
`src/obj/flight_actions_install/20261030_003119`, with installed DLL imports and
all seven payload hashes verified. Backup:
`BACKUP/codex_flight_actions_20261030_003139_323`.

OM15 composite-base correction (2026-10-30): route planning now ends at a free
approach point rather than at the docking object's centre. OM15 miners combine
the station with a cargo object at +5 m Y and a separate asteroid at +5 m Y,
-235 m Z. Ignoring only the station previously left the endpoint inside the
asteroid's guard, making the whole route fail. Both map refinement and the F2
executor now use the same arrival-region search. Cruise legs check every solid;
native Dock handles the nearby solid components after handoff. Atmospheres and
damage zones remain constraints on the handoff segment as well.

System INIs now resolve through `Universe::get_filename`, so mod files under
`DATA/UNIVERSE/SYSTEMS_MOD` actually supply their Beta path-label corridors.
Candidate generation first tries visible goals/corridors, then shares detours
among overlapping obstacle bounds. Reaching the candidate budget no longer
rejects a route before searching; every original obstacle remains checked.

Regression coverage uses the seven actual OM15 miner positions with conservative
spherical bounds: 63 approaches from the jumpgate, across the sun and from other
miners, plus crowded geometry, blocked approaches, and a docking ring behind a
planet. This is a geometry fixture, not a live physics or docking capture.

The correction passed Release Win32 and the maneuver/camera harness, then was
installed into `D:/games/FL_MOD/bin` from package
`src/obj/flight_actions_install/20261030_005146`. All seven installed payloads
and four DLL dependency hashes were verified. Backup:
`BACKUP/codex_flight_actions_20261030_005236_370`. The latest game configuration
was preserved, including its selected route generator; live docking remains
to be checked in-game.

F2 input correction (2026-10-30): removed route cancellation from the mouse-mode
toggle and from held-LMB/cursor handling, including cockpit head-look Space.
Cruise commands no longer call the route's stop/reset path. Cruise during the
Go To sine weave returns to ordinary cruise without disabling the engine;
other cruise toggles preserve Go To and throttle. The requested cruise state
is retained across waypoint handoffs.
`tools/route_autopilot/check_controls.py` runs the production handlers against a
recording behavior manager and covers these sequences; the route geometry and
maneuver/camera checks and Release Win32 build also passed. These are isolated
checks, not a live flight capture.
Installed package: `src/obj/flight_actions_install/20261030_005927`.
Backup: `BACKUP/codex_flight_actions_20261030_010407_070`.
All seven installed payloads and four DLL dependencies were hash-verified;
the game configuration was retained byte for byte.

F2 manual override and resume correction (2026-10-30): mouse steering is now
passed to Go To's native direction override, retaining the active route and
cruise. The sine weave yields to that override. Mouse release clears the override
and rebuilds the current leg; camera/head-look input does not steer the ship.
Freeflight retains the generated route's final goal; F2 requests new topology
and detours from the current position and automatically starts the received
route. The selected HUD waypoint is resolved by AutoId, fixing the erroneous
fallback to entry zero for space markers. Route changes/cancelled requests and
session changes invalidate automatic resumption.

The production-handler harness now checks actual direction forwarding/release,
head-look isolation, selection of waypoint 2 with a stale HUD index, the
Freeflight/F2 request's current start and final goal, repeated F2 during a
pending request, cancelled responses and mission-waypoint isolation. Release
Win32, geometry and maneuver/camera checks passed; live flight remains untested.
Installed package: `src/obj/flight_actions_install/20261030_011817`.
Backup: `BACKUP/codex_flight_actions_20261030_012207_636`.
Seven payloads and four DLL dependencies verified; settings preserved.

F2 stuck steering correction (2026-10-30): clearing Go To's manual flag alone
did not release the turn. Common replays `LastCommandedDirection` every player
update, reinstating the override even after a fresh directive. Mouse release
now sends zero through the behavior manager to clear both its cached command
and `UserTurningInputState`, then releases Go To's flag (point-target Go To
sets that flag even for zero input). The same release runs when F2 starts and
when cockpit head look clears mouse input, independently of the client latch.
The route tick detects release before the next behavior update and rebuilds
the current leg while retaining cruise and throttle.

The regression first failed with the old handlers and now passes with Common's
actual direction-replay block and the production route tick. It covers Space,
LMB release, head look and HUD hover at 30/60/144 Hz for 120 subsequent frames,
plus F2 restart with stale input and a cleared client latch. Route geometry,
maneuver/camera checks and Release Win32 passed; live flight remains untested.
Installed package: `src/obj/flight_actions_install/20261030_013300`.
Backup: `BACKUP/codex_flight_actions_20261030_013318_784`.
Seven payloads and four DLL dependencies verified; settings preserved byte for byte.
