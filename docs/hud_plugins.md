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
