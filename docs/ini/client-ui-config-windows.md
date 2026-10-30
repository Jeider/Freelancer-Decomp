# Client configuration: window definitions, HUD and UI lookup tables

This page documents the INI files that lay out and drive the client's 3D user-interface windows: the window-definition format (`navbar.ini` and the control classes it can instantiate), the HUD element file `hud.ini`, and the small lookup tables for rollover help, info cards, knowledge and button icons. Keyboard, options, display, fonts, cursors, cameras and start-up files are in [client-ui-config.md](client-ui-config.md); shape databases (`[Texture]`/`[Shape]`) in [client-audio-misc.md](client-audio-misc.md#5-shape-databases-texture-and-shape).

## File location / how it is found

### Global HUD preferences and Health controls (2026-10-30)

Port HUD choices live in `hud_preferences.ini` in `GetUserDataPath()`, shared by all characters. The old interface word is imported once if no global profile exists. Radar deployment/range/automation, Targeting projection/autoselect/auto-open, Health auto-open/view/visibility, active weapon group and auto-turret master/reserve are global. Native interface bits 0–3 and weapon-group membership remain game state. New saves strip the former HUD preference bits. Miscellaneous preferences can be edited from the main menu and retain Apply/Cancel behavior.

**Show weapon groups** is a global toggle, enabled by default. Health shows the three original `HUD_weaponsgroup1..3.3db` icons in one row from its left edge, with the current group highlighted. The right edge holds the cloak button when a cloak is installed; the icon cannot spin, reflects device activation and becomes disabled if destroyed. It invokes `USER_CLOAK` through the normal client/server activation path. No keyboard bindings are assigned. `DATA/INTERFACE/HUD/EXTRA/HUD_DefCloak.3db` now contains a standalone copy of the Health opening button, with unique mesh/material names and a full-icon `HUD_health_cloak_icon.tga` texture. Replace its `Texture library / HUD_health_cloak_icon.tga / MIP0` to supply new art; the Beta texture atlas is no longer used.

All files are read through `INI_Reader` ([parsers.md](parsers.md)); section and key names are case-insensitive; repeated keys are delivered in file order. Conventions are the same as in [client-ui-config.md](client-ui-config.md#file-location--how-it-is-found): *Type* names the getter (*string*, *int*, *number* = `get_value_float`, *bool*); a **flag** key is true when `get_value_float(0) != 0` (so `1` is on, `0` or an empty value is off, and the words `true`/`false` are not understood); a **vector** key `x, y, z` is three numbers in that order; the Default column is the value the control's constructor leaves in place when the key is absent. "Not validated" means the code does not check the value.

Paths are relative to the Data path (`[Freelancer] data path` in `Freelancer.ini`, default `..\Data`) unless stated. The shipped files are binary `BINI`; text files with the same sections work identically.

| File | Located by | Read by | Section |
|---|---|---|---|
| `interface\baseside\navbar.ini` | fixed name, relative to Data | `NavBar::Create` → `WinControl::LoadIni` | 1, 2, 3 |
| `hud.ini` | `[Data] HUD = ...` in `Freelancer.ini` | `LoadHudElementsFromIni` | 4 |
| `interface\Rollover.ini` | fixed name | `NnRolloverControl::LoadRolloverTable` | 5.1 |
| `interface\InfocardMap.ini` | fixed name | `FInfocardMap::Load` | 5.2 |
| `interface\KnowledgeMap.ini` | fixed name | `FKnowledgeMap::Load` | 5.3 |
| `interface\ButtonMontage.ini` | fixed name | `LoadButtonMontage` | 5.4 |

The scripts that drive the same windows (`PAGE_*` text files, character and base screens) are not INI and are not covered here.

---

## 1. Window definition format (`WinControl::LoadIni`)

Source: [wincontrol_base.cpp:336](../../src/freelancer/Client/wincontrol_base.cpp#L336). The only window-definition INI the client opens by name is `interface\baseside\navbar.ini` (opened by [nav_bar.cpp:303](../../src/freelancer/Client/nav_bar.cpp#L303)); the loader itself is generic (any `WinControl` can run it on a path), and the control sections below are what it understands.

Layout of a definition file:

```ini
[BaseFrame]            ; the window itself
mesh   = interface\hud\example_frame.cmp
offset = 0.0, 0.1, -0.5

[SomeChild]            ; any other section creates one child control
class_name = ButtonControl
mesh   = interface\hud\example_button.3db
offset = 0.1, 0.0, 0.0
tooltip = 1234
```

Rules:

* The file is opened with `open(path, false)`: a missing file or a missing `[BaseFrame]` section ends loading silently.
* `[BaseFrame]` is found with `find_header` and must be the section whose values are read first. Its keys configure the window itself (table 1.1).
* **Every later section** (in file order) creates a child control. The section **name becomes the child's name** (truncated to 31 characters). The scan looks for a `class_name` value in the section; the first one found selects the class and the factory is invoked with the reader positioned *after* that line, so **`class_name` must be the first key of the section**: any key written before it is skipped, any key after it is read by the control's own parser (section 2). Sections without `class_name` (for example `[NavBar]`, section 3) create nothing.
* `class_name` is matched **case-sensitively** against the registered window factories (below). An unknown class name is silently ignored (no child, no message).

Registered `class_name` values (`WINFACTORY` statics): `BlockingDialog`, `ButtonControl`, `CargoBarControl`, `ChatControl`, `ChatTextInputDisplay`, `EditControl`, `MissionLogMoveFromNNWindow`, `MissionLogMoveToNNWindow`, `MissionObjectiveWindow`, `MsgWin`, `NN_ArrivalText`, `NN_CommodityByBase`, `NN_Confirm`, `NN_Dealer`, `NN_Error`, `NN_Exit`, `NN_GroupControl`, `NN_Help`, `NN_Inventory`, `NN_LoadSave`, `NN_MainButton`, `NN_MissionVendor`, `NN_NetworkOperation`, `NN_News`, `NN_OfferDialog`, `NN_Pause`, `NN_PlayerInfo`, `NN_Preferences`, `NN_Prompt`, `NN_Repair`, `NN_Scanner`, `NN_ShipTrader`, `NN_Trade`, `NavBar`, `NeuroNetMissionMessage`, `NeuroNetNavMap`, `NeuroNetStoryStar`, `RichTextButtonControl`, `RichTextEditWin`, `RichTextWin`, `RichTextWireButtonControl`, `Rollover`, `ScrollControl`, `ServerFilterDialog`, `ShipViewControl`, `StaticControl`, `TextControl`, `ToggleButtonControl`, `ToolTip`, `UICycle`, `UIFastTable`, `UIListBox`, `UIRichTextWin`, `UIScroll`, `UIScrollTable`, `UIShipViewControl`, `UIStaticText`, `UITable`, `UITextEdit`, `UITextMsgButton`, `UIWinDeform`, `UIWinObject`, `WinControl`, `WireButtonControl`, `WireStaticControl` (each is a `WINFACTORY<T>` static, see [win_factory.h](../../src/freelancer/Client/win_factory.h); the case-sensitive lookup is `WinFactoryCreate` in [win_factory.cpp](../../src/freelancer/Client/win_factory.cpp#L80)).

Only the classes in section 2 read keys from the definition section. All other classes ignore the payload and build their content in code; naming them in `class_name` creates the object but the remaining keys of that section have no effect.

Port-only ship dealer: `NN_ShipTrader` now keeps the complete category-3 market
catalogue and displays it through three reusable rows. A vertical scrollbar and
mouse wheel over the catalogue move one row at a time; the information panes keep
their own scrolling. Selection survives scrolling and availability sorting, and
purchase uses the package's original market index. The scrollbar is hidden for
three or fewer ships. This window still creates its layout in code, with no new
INI keys; see [nn_ship_trader.cpp](../../src/freelancer/Client/nn_ship_trader.cpp).

### 1.1 `[BaseFrame]` keys

| Key | Type | Default | Meaning / allowed values | Source |
|---|---|---|---|---|
| `mesh` | string | none | 3D model (`.3db`/`.cmp`) of the window frame. | [wincontrol_base.cpp:347](../../src/freelancer/Client/wincontrol_base.cpp#L347) |
| `offset` | vector | `0, 0, 0` | Position of the window relative to its parent. | [wincontrol_base.cpp:352](../../src/freelancer/Client/wincontrol_base.cpp#L352) |
| `mouse_size` | vector | `0, 0, 0` | Half-extents of the mouse hit box. | [wincontrol_base.cpp:372](../../src/freelancer/Client/wincontrol_base.cpp#L372) |
| `no_z_enable` | flag | off | Draw without depth testing. | [wincontrol_base.cpp:382](../../src/freelancer/Client/wincontrol_base.cpp#L382) |
| `z_order` | number → unsigned | Win3D default (unchanged) | Draw layer. Not validated. | [wincontrol_base.cpp:387](../../src/freelancer/Client/wincontrol_base.cpp#L387) |
| `tooltip` | number → int | `0` | String-resource id of the hover tooltip; `0` = none. | [wincontrol_base.cpp:392](../../src/freelancer/Client/wincontrol_base.cpp#L392) |
| `behavior`, `subcontrol`, `class_name` | – | – | Recognised/ignored in `[BaseFrame]` (no effect). | [wincontrol_base.cpp:345](../../src/freelancer/Client/wincontrol_base.cpp#L345), [wincontrol_base.cpp:370](../../src/freelancer/Client/wincontrol_base.cpp#L370) |

---

## 2. Control sections

Each class below is created when a section has `class_name = <Class>`; keys after it are read until the end of the section. All unknown keys are ignored. `hardpoint = <name>` in every class means: attach to the hardpoint called `<name>` on the **parent** control's mesh (the control's position follows that hardpoint); a parent that is not a window control, or a hardpoint that does not exist, leaves the attachment at the identity transform.

### 2.1 `ButtonControl`, `ToggleButtonControl`, `RichTextButtonControl`

All three use the same parser ([nn_button_control.cpp:335](../../src/freelancer/Client/nn_button_control.cpp#L335)); `ToggleButtonControl` additionally uses `mesh2` as its second (toggled) model.

| Key | Type | Default | Meaning / allowed values | Source |
|---|---|---|---|---|
| `mesh` | string | none | Button model. The same string (case-insensitive) is the key into `ButtonMontage.ini` (section 5.4): if a tile of that name exists the button is drawn from the icon montage. | [nn_button_control.cpp:347](../../src/freelancer/Client/nn_button_control.cpp#L347), [nn_button_control.cpp:464](../../src/freelancer/Client/nn_button_control.cpp#L464) |
| `mesh2` | string | empty | Second model (used by `ToggleButtonControl`). | [nn_button_control.cpp:352](../../src/freelancer/Client/nn_button_control.cpp#L352) |
| `button_sound` | string | none | Name of a UI sound slot played by the button; an empty value is ignored; not validated. | [nn_button_control.cpp:357](../../src/freelancer/Client/nn_button_control.cpp#L357) |
| `event` | string | none | Ties the button to a game command. Recognised values (case-insensitive): `tractor`, `next`, `prev`, `next_subtarget`, `prev_subtarget`. Other values give the button no command and no tooltip. A recognised value also sets the tooltip. | [nn_button_control.cpp:366](../../src/freelancer/Client/nn_button_control.cpp#L366), [nn_button_control.cpp:198](../../src/freelancer/Client/nn_button_control.cpp#L198) |
| `offset` | vector | `0, 0, 0` | Position relative to the parent (or hardpoint). | [nn_button_control.cpp:378](../../src/freelancer/Client/nn_button_control.cpp#L378) |
| `hardpoint` | string | none | See above. | [nn_button_control.cpp:398](../../src/freelancer/Client/nn_button_control.cpp#L398) |
| `mouse_size` | vector | `0, 0, 0` | Half-extents of the click box. | [nn_button_control.cpp:422](../../src/freelancer/Client/nn_button_control.cpp#L422) |
| `no_mesh_render` | flag | off | Do not draw the model (the montage icon or code draws instead). | [nn_button_control.cpp:432](../../src/freelancer/Client/nn_button_control.cpp#L432) |
| `action_button` | flag | off | Marks the button as an action button. | [nn_button_control.cpp:438](../../src/freelancer/Client/nn_button_control.cpp#L438) |
| `no_color_change` | flag | off | Do not tint the button on hover/press. | [nn_button_control.cpp:444](../../src/freelancer/Client/nn_button_control.cpp#L444) |
| `no_z_enable` | flag | off | Draw without depth test. | [nn_button_control.cpp:450](../../src/freelancer/Client/nn_button_control.cpp#L450) |
| `tooltip` | number → int | `0` | String-resource id of the tooltip. | [nn_button_control.cpp:455](../../src/freelancer/Client/nn_button_control.cpp#L455) |
| `tooltip2` | number → int | `0` | Second tooltip id (alternate state). | [nn_button_control.cpp:460](../../src/freelancer/Client/nn_button_control.cpp#L460) |

### 2.2 `StaticControl`

[nn_static_control.cpp:275](../../src/freelancer/Client/nn_static_control.cpp#L275). A (possibly rotating) model with no interaction.

| Key | Type | Default | Meaning / allowed values | Source |
|---|---|---|---|---|
| `mesh` | string | none | Model. | [nn_static_control.cpp:287](../../src/freelancer/Client/nn_static_control.cpp#L287) |
| `mouse_size` | vector | `0, 0, 0` | Half-extents of the hit box. | [nn_static_control.cpp:292](../../src/freelancer/Client/nn_static_control.cpp#L292) |
| `offset` | vector | `0, 0, 0` | Position relative to the parent. | [nn_static_control.cpp:302](../../src/freelancer/Client/nn_static_control.cpp#L302) |
| `hardpoint` | string | none | See above. | [nn_static_control.cpp:314](../../src/freelancer/Client/nn_static_control.cpp#L314) |
| `no_z_enable` | flag | off | Draw without depth test. | [nn_static_control.cpp:343](../../src/freelancer/Client/nn_static_control.cpp#L343) |
| `zclear` | flag | off | Clear the depth buffer before drawing. | [nn_static_control.cpp:348](../../src/freelancer/Client/nn_static_control.cpp#L348) |
| `no_mesh_render` | flag | off | Do not draw the solid model. | [nn_static_control.cpp:353](../../src/freelancer/Client/nn_static_control.cpp#L353) |
| `no_wire_render` | flag | off | Do not draw the wireframe. | [nn_static_control.cpp:358](../../src/freelancer/Client/nn_static_control.cpp#L358) |
| `no_coloring` | flag | off | Do not apply the HUD colour tint. | [nn_static_control.cpp:363](../../src/freelancer/Client/nn_static_control.cpp#L363) |
| `render_to_window` | flag | off | Render the model into the window's own viewport. | [nn_static_control.cpp:368](../../src/freelancer/Client/nn_static_control.cpp#L368) |
| `no_clear_render` | flag | **on** | Do not clear the target before rendering (default is on; set `0` to clear). | [nn_static_control.cpp:373](../../src/freelancer/Client/nn_static_control.cpp#L373) |
| `force_radius` | number | `0` | Override of the bounding radius used to fit the model in view. | [nn_static_control.cpp:378](../../src/freelancer/Client/nn_static_control.cpp#L378) |
| `rotation_speed` | number | `0` | Rotation speed; `0` = does not rotate. | [nn_static_control.cpp:383](../../src/freelancer/Client/nn_static_control.cpp#L383) |
| `enable_rotation` | flag | off | Allow rotation by the user. | [nn_static_control.cpp:388](../../src/freelancer/Client/nn_static_control.cpp#L388) |
| `starting_yaw_pitch_roll` | number ×3 | `0, 0, 0` | Initial orientation: yaw, pitch, roll (units as consumed by the rotation code; not validated). | [nn_static_control.cpp:393](../../src/freelancer/Client/nn_static_control.cpp#L393) |

### 2.3 `TextControl` and `EditControl`

[nn_text_control.cpp:207](../../src/freelancer/Client/nn_text_control.cpp#L207). `EditControl` inherits the same parser (no override).

| Key | Type | Default | Meaning / allowed values | Source |
|---|---|---|---|---|
| `font` | string | system default | Font nickname from the `fonts` file ([client-ui-config.md](client-ui-config.md#51-fonts-file-truetype)); an unknown nickname leaves the current font. | [nn_text_control.cpp:219](../../src/freelancer/Client/nn_text_control.cpp#L219) |
| `offset` | vector | `0, 0, 0` | Position relative to the parent. | [nn_text_control.cpp:227](../../src/freelancer/Client/nn_text_control.cpp#L227) |
| `hardpoint` | string | none | See above. | [nn_text_control.cpp:237](../../src/freelancer/Client/nn_text_control.cpp#L237) |
| `width` | number | `0` | Text box width. | [nn_text_control.cpp:263](../../src/freelancer/Client/nn_text_control.cpp#L263) |
| `height` | number | `0` | Text box height. | [nn_text_control.cpp:267](../../src/freelancer/Client/nn_text_control.cpp#L267) |
| `font_scale` | – | – | Recognised and skipped (no effect). | [nn_text_control.cpp:271](../../src/freelancer/Client/nn_text_control.cpp#L271) |
| `stringID` | number → int | none | String-resource id of the displayed text. | [nn_text_control.cpp:275](../../src/freelancer/Client/nn_text_control.cpp#L275) |
| `justification` | number → int | `0` | Horizontal alignment: `1` = centre, `2` = right, anything else = left. | [nn_text_control.cpp:280](../../src/freelancer/Client/nn_text_control.cpp#L280), [font_string.h](../../src/freelancer/Client/font_string.h#L298) |
| `tooltip` | number → int | `0` | Tooltip string-resource id; a non-zero value also makes the text box hoverable. | [nn_text_control.cpp:284](../../src/freelancer/Client/nn_text_control.cpp#L284) |

### 2.4 `ScrollControl`

[scroll_control.cpp:613](../../src/freelancer/Client/scroll_control.cpp#L613). A scroll bar made of four parts (*back*, *next button*, *prev button*, *thumb*). Each part has the same group of keys with a prefix: `back_`, `nextb_`, `prevb_`, `thumb_`.

| Key | Type | Default | Meaning / allowed values | Source |
|---|---|---|---|---|
| `back_mesh`, `nextb_mesh`, `prevb_mesh`, `thumb_mesh` | string | none | Model of the part. | [scroll_control.cpp:626](../../src/freelancer/Client/scroll_control.cpp#L626) |
| `back_offset`, `nextb_offset`, `prevb_offset` | vector | `0, 0, 0` | Part position relative to its hardpoint. | [scroll_control.cpp:630](../../src/freelancer/Client/scroll_control.cpp#L630) |
| `thumb_offset0`, `thumb_offset1` | vector | `0, 0, 0` | Thumb position at the start and end of the track. | [scroll_control.cpp:703](../../src/freelancer/Client/scroll_control.cpp#L703) |
| `back_hp`, `nextb_hp`, `prevb_hp`, `thumb_hp0`, `thumb_hp1` | string | identity | Hardpoint name on the parent the control is created for; the part is attached to it. | [scroll_control.cpp:636](../../src/freelancer/Client/scroll_control.cpp#L636) |
| `back_mouse`, `nextb_mouse`, `prevb_mouse`, `thumb_mouse` | vector | `0, 0, 0` | Half-extents of the part's click box. | [scroll_control.cpp:643](../../src/freelancer/Client/scroll_control.cpp#L643) |
| `back_no_mesh_render`, `nextb_no_mesh_render`, `prevb_no_mesh_render`, `thumb_no_mesh_render` | flag | off | Do not draw the part's model. | [scroll_control.cpp:647](../../src/freelancer/Client/scroll_control.cpp#L647) |
| `min_range` | number → int | `0` | Lowest value. | [scroll_control.cpp:735](../../src/freelancer/Client/scroll_control.cpp#L735) |
| `max_range` | number → int | `0` | Highest value. | [scroll_control.cpp:739](../../src/freelancer/Client/scroll_control.cpp#L739) |
| `page_size` | number → int | `1` | Value step for a page click. | [scroll_control.cpp:743](../../src/freelancer/Client/scroll_control.cpp#L743) |
| `slider_behavior` | flag | off | Behave as a slider (thumb jumps/drag) instead of a scroll bar. | [scroll_control.cpp:747](../../src/freelancer/Client/scroll_control.cpp#L747) |
| `no_z_enable` | flag | off | Draw without depth test. | [scroll_control.cpp:751](../../src/freelancer/Client/scroll_control.cpp#L751) |

### 2.5 `CargoBarControl`

[cargo_bar_control.cpp:185](../../src/freelancer/Client/cargo_bar_control.cpp#L185). The cargo capacity bar. Note: `mesh` does not `continue`, so the same line is also tested against the keys that follow it (no practical effect).

| Key | Type | Default | Meaning / allowed values | Source |
|---|---|---|---|---|
| `mesh` | string | none | Model. | [cargo_bar_control.cpp:196](../../src/freelancer/Client/cargo_bar_control.cpp#L196) |
| `offset` | vector | `0, 0, 0` | Position relative to the parent. | [cargo_bar_control.cpp:202](../../src/freelancer/Client/cargo_bar_control.cpp#L202) |
| `hardpoint` | string | none | See above. | [cargo_bar_control.cpp:212](../../src/freelancer/Client/cargo_bar_control.cpp#L212) |
| `mouse_size` | vector | `0, 0, 0` | Half-extents of the hover box. | [cargo_bar_control.cpp:229](../../src/freelancer/Client/cargo_bar_control.cpp#L229) |
| `horizontal` | flag | off | Bar fills horizontally instead of vertically. | [cargo_bar_control.cpp:239](../../src/freelancer/Client/cargo_bar_control.cpp#L239) |
| `tooltip` | flag | off | Enable the hover tooltip. | [cargo_bar_control.cpp:245](../../src/freelancer/Client/cargo_bar_control.cpp#L245) |
| `tooltip2` | number → int | `0` | Tooltip string-resource id; also turns the tooltip on. | [cargo_bar_control.cpp:250](../../src/freelancer/Client/cargo_bar_control.cpp#L250) |
| `color` | number ×4 | `0, 0, 0, 0` | R, G, B, A of the bar, each **`0 ... 255`** (truncated to a byte; not scaled). | [cargo_bar_control.cpp:256](../../src/freelancer/Client/cargo_bar_control.cpp#L256) |
| `color_highlight` | number ×4 | `255, 255, 0, 255` | R, G, B, A of the highlighted (used) part, each `0 ... 255`. | [cargo_bar_control.cpp:271](../../src/freelancer/Client/cargo_bar_control.cpp#L271) |

### 2.6 `ShipViewControl`

[ship_view_control.cpp:363](../../src/freelancer/Client/ship_view_control.cpp#L363). The rotating ship preview. Every key is tested independently (a line may be matched by more than one test, but key names are distinct, so this has no effect).

| Key | Type | Default | Meaning / allowed values | Source |
|---|---|---|---|---|
| `rot_speed` | vector | `0, 0, 0` | Rotation speed per axis. | [ship_view_control.cpp:375](../../src/freelancer/Client/ship_view_control.cpp#L375) |
| `offset` | vector | `0, 0, 0` | View offset. | [ship_view_control.cpp:384](../../src/freelancer/Client/ship_view_control.cpp#L384) |
| `object_ypr` | vector | identity orientation | Initial yaw, pitch, roll of the ship. Units as consumed by the orientation builder; not validated. | [ship_view_control.cpp:393](../../src/freelancer/Client/ship_view_control.cpp#L393) |
| `viewSize` | vector | `0, 0, 0` | Size of the preview area. | [ship_view_control.cpp:403](../../src/freelancer/Client/ship_view_control.cpp#L403) |
| `hardpoint` | string | none | See above. | [ship_view_control.cpp:412](../../src/freelancer/Client/ship_view_control.cpp#L412) |
| `show_rect` | flag | off | Draw the frame rectangle. | [ship_view_control.cpp:433](../../src/freelancer/Client/ship_view_control.cpp#L433) |
| `show_wireframe` | flag | off | Draw the wireframe overlay. | [ship_view_control.cpp:439](../../src/freelancer/Client/ship_view_control.cpp#L439) |
| `rect_color` | number ×4 | HUD chrome colour | R, G, B, A, each **`0 ... 1`** (multiplied by 255 and truncated). | [ship_view_control.cpp:444](../../src/freelancer/Client/ship_view_control.cpp#L444) |
| `wire_color` | number ×4 | HUD chrome colour | R, G, B, A, each `0 ... 1`. | [ship_view_control.cpp:456](../../src/freelancer/Client/ship_view_control.cpp#L456) |

Note the colour convention differs between controls: `CargoBarControl` colours are `0 ... 255`, `ShipViewControl` colours are `0 ... 1`.

---

## 3. `[NavBar]` (in `navbar.ini`)

The navigation bar on base screens ([nav_bar.cpp:303](../../src/freelancer/Client/nav_bar.cpp#L303)). After `LoadIni`, the same file is opened again and the section `[NavBar]` is read ([nav_bar.cpp:337](../../src/freelancer/Client/nav_bar.cpp#L337)): **every key is stored** as a pair *hotspot name → mesh path*. The key is the name of a hotspot (room object) in the current room; the value is the 3D model used for that hotspot's navigation button (value buffer is 128 bytes, the code copies without a length check — keep values below 127 characters). A hotspot with no entry uses `interface\baseside\unknown.3db` and the game remembers that choice for the session. There are no fixed key names and no validation.

---

## 4. `hud.ini`

Located by `[Data] HUD = <path>` in `Freelancer.ini` (the path is stored at start-up and the file is read when the player enters space; [cockpit_load.cpp:122](../../src/freelancer/Client/cockpit_load.cpp#L122), [hud_element_list.cpp:445](../../src/freelancer/Client/hud_element_list.cpp#L445)). A missing file logs `hud file not found`. Sections other than `[HUD]` each create one HUD element; the section name selects the element type (case-insensitive).

### 4.1 `[HUD]`

| Key | Type | Default | Meaning / allowed values | Source |
|---|---|---|---|---|
| `shapes` | string | none | Shape database (`[Texture]`/`[Shape]` file, see [client-audio-misc.md](client-audio-misc.md#5-shape-databases-texture-and-shape)) holding the HUD textures, relative to Data. | [hud_element_list.cpp:463](../../src/freelancer/Client/hud_element_list.cpp#L463) |
| `static_txm` | string | none | Texture used for the HUD static/noise overlay. | [hud_element_list.cpp:468](../../src/freelancer/Client/hud_element_list.cpp#L468) |
| `static_blend` | number → int | `2` | Blend mode id of the static overlay. Not validated. | [hud_element_list.cpp:473](../../src/freelancer/Client/hud_element_list.cpp#L473) |

### 4.2 Element sections

| Section | Element | Keys read |
|---|---|---|
| `[Button]` | HUD button | `action`, `object`, `object_pos`, `tool_tip_id` (4.3) |
| `[Receiver]` | comm receiver / chat portrait | 4.4 |
| `[Maneuvers]` | maneuver button bar | `maneuver` (4.5) |
| `[Steer]` | steering arrow | `radius`, `range` (4.6) |
| `[ContactList]`, `[CruiseProgress]`, `[DamageIndicator]`, `[Core]`, `[Status]`, `[Target]`, `[Targetable_Objects]`, `[Waypoint]` | the corresponding HUD elements | **no keys are read**; the section only has to exist for the element to be created |

A section name that no element accepts logs `HUD - unknown INI entry` and is skipped. If several sections of the same name exist, one element is created for each. An element whose `Init` fails is discarded.

### 4.3 `[Button]`

[hud_button.cpp:249](../../src/freelancer/Client/hud_button.cpp#L249).

| Key | Type | Default | Meaning / allowed values | Source |
|---|---|---|---|---|
| `action` | string | empty | Command triggered by the button. Exact words (case-sensitive): `radio`, `status`, `zoom`, `navmap`, `toggle_manuevers` (sic, spelled as in the code). Any other value logs `unknown HUD_Button action` and the button has no command. | [hud_button.cpp:264](../../src/freelancer/Client/hud_button.cpp#L264) |
| `object` | string | none | Button model. | [hud_button.cpp:282](../../src/freelancer/Client/hud_button.cpp#L282) |
| `object_pos` | vector | `0, 0, -5` | Button position. | [hud_button.cpp:287](../../src/freelancer/Client/hud_button.cpp#L287) |
| `tool_tip_id` | number → int | `0` | Tooltip string-resource id. | [hud_button.cpp:302](../../src/freelancer/Client/hud_button.cpp#L302) |

### 4.4 `[Receiver]`

[hud_comm.cpp:1581](../../src/freelancer/Client/hud_comm.cpp#L1581). The comm window keys (`corner` ... `static`) apply to the **first** comm channel's window only.

| Key | Type | Default | Meaning / allowed values | Source |
|---|---|---|---|---|
| `corner` | string | none | Model of the comm-window corner frame; tinted with the HUD colour. | [hud_comm.cpp:745](../../src/freelancer/Client/hud_comm.cpp#L745) |
| `btn_pos` | vector | `0, 0, -2` | Position of the comm button. | [hud_comm.cpp:756](../../src/freelancer/Client/hud_comm.cpp#L756) |
| `win_pos` | vector | `0.3, 0.3, -1` | Window position. Parsed, but the first channel's window position is afterwards overwritten with a fixed `-1.068, 0.65, -2.392`, so the key has no effect there. | [hud_comm.cpp:767](../../src/freelancer/Client/hud_comm.cpp#L767), [hud_comm.cpp:1679](../../src/freelancer/Client/hud_comm.cpp#L1679) |
| `win_size` | number, number | `0.2, 0.2` | Window width and height. | [hud_comm.cpp:777](../../src/freelancer/Client/hud_comm.cpp#L777) |
| `fly_time` | number | `0.5` | Fly time of the window opening animation (stored as given; not validated). | [hud_comm.cpp:783](../../src/freelancer/Client/hud_comm.cpp#L783) |
| `static` | flag | on | Show the static/noise overlay on the portrait. | [hud_comm.cpp:788](../../src/freelancer/Client/hud_comm.cpp#L788) |
| `speaker_offset` | – | – | Obsolete: logs a warning telling to use the two keys below; no effect. | [hud_comm.cpp:1612](../../src/freelancer/Client/hud_comm.cpp#L1612) |
| `male_speaker_offset` | vector | `0, 0, 0` | Position of a male speaker's head model. | [hud_comm.cpp:1619](../../src/freelancer/Client/hud_comm.cpp#L1619) |
| `female_speaker_offset` | vector | `0, 0, 0` | Position of a female speaker's head model. | [hud_comm.cpp:1628](../../src/freelancer/Client/hud_comm.cpp#L1628) |
| `speaker_rotate` | number ×3 | zero rotation | Euler angles of the speaker model (units as consumed by `EulerMatrix`; not validated). | [hud_comm.cpp:1637](../../src/freelancer/Client/hud_comm.cpp#L1637) |
| `video_fovx` | number | camera default | **Half** horizontal field of view, in degrees, of the speaker-portrait camera (note: `fovx` in `cameras.ini` is the *full* angle). | [hud_comm.cpp:1646](../../src/freelancer/Client/hud_comm.cpp#L1646) |
| `backdrop` | string | none | Texture drawn behind the speaker. | [hud_comm.cpp:1650](../../src/freelancer/Client/hud_comm.cpp#L1650) |

### 4.5 `[Maneuvers]`

[hud_maneuvers.cpp:182](../../src/freelancer/Client/hud_maneuvers.cpp#L182). One `maneuver` line per button, in order.

| Key | Type | Default | Meaning / allowed values | Source |
|---|---|---|---|---|
| `maneuver` | **repeated**; 5 positional parameters | none | `maneuver = <name>, <tooltip ids>, <ids2>, <mesh>, <gray mesh>` — `name`: behaviour name (resolved to a behaviour id by `BehaviorTypes::get_behavior_id`; names `Dock`, `Goto`, `Formation`, `FreeFlight` (case-insensitive) additionally bind the button to a fixed command, others have no command); `tooltip ids`, `ids2`: string-resource ids (numbers); `mesh`: model of the enabled button; `gray mesh`: model of the disabled button. Both mesh strings are also looked up (case-insensitive) in `ButtonMontage.ini` (section 5.4). Not validated. | [hud_maneuvers.cpp:191](../../src/freelancer/Client/hud_maneuvers.cpp#L191), [hud_maneuvers.cpp:47](../../src/freelancer/Client/hud_maneuvers.cpp#L47) |

### 4.6 `[Steer]`

[hud_element_list.cpp:563](../../src/freelancer/Client/hud_element_list.cpp#L563).

| Key | Type | Default | Meaning / allowed values | Source |
|---|---|---|---|---|
| `radius` | number | `40` | Radius of the steering-arrow circle. | [hud_element_list.cpp:587](../../src/freelancer/Client/hud_element_list.cpp#L587) |
| `range` | number | `200` | Mouse-flight range. | [hud_element_list.cpp:589](../../src/freelancer/Client/hud_element_list.cpp#L589) |

---

## 5. Lookup tables

All four tables are tiny and share a shape: one section with a repeated `map` key. A missing file leaves the table empty.

### 5.1 `interface\Rollover.ini` — `[RolloverTable]`

Maps a hover tooltip's string id to the id of the longer "rollover" help text ([nn_rollover.cpp:153](../../src/freelancer/Client/nn_rollover.cpp#L153)).

| Key | Type | Default | Meaning / allowed values | Source |
|---|---|---|---|---|
| `map` | **repeated**; `a, b` | none | `a` = string id of the tooltip being shown (the hovered control's `tooltip` value), `b` = string id of the rollover text shown instead. Both are converted to integers. A repeated `a` keeps its **first** line. | [nn_rollover.cpp:170](../../src/freelancer/Client/nn_rollover.cpp#L170) |

### 5.2 `interface\InfocardMap.ini` — `[InfocardMapTable]`

Extends object info cards ([infocard_map.cpp:8](../../src/freelancer/Client/infocard_map.cpp#L8), semantics in [infocard_map.h](../../src/freelancer/Client/infocard_map.h)).

| Key | Type | Default | Meaning / allowed values | Source |
|---|---|---|---|---|
| `map` | **repeated**; `key, extra [, a, b, c]` | none | `key` = the object's `ids_info`; `extra` = a second string id appended to that object's info card; `a`, `b`, `c` = switches (default `1`) for the equipment list, the commodity lists and the ships-for-sale list shown in the card. All values are converted to integers. A repeated `key` keeps its **first** line. Not validated. | [infocard_map.cpp:27](../../src/freelancer/Client/infocard_map.cpp#L27) |

### 5.3 `interface\KnowledgeMap.ini` — `[KnowledgeMapTable]`

Makes reading a text reveal objects ([knowledge_map.cpp:51](../../src/freelancer/Client/knowledge_map.cpp#L51)): when the text whose string id is `key` is shown, every object listed under the key gets its visit flags raised.

| Key | Type | Default | Meaning / allowed values | Source |
|---|---|---|---|---|
| `map` | **repeated**; `key, nickname, flags` | none | `key` = string id of the text (integer); `nickname` = object nickname (hashed with `CreateID`); `flags` = visit flags byte (low 8 bits of the integer). If `flags & 0x40` the nickname is interpreted as a **faction** nickname and resolved with `Reputation::get_id`. Several lines with the same `key` are all kept (newest first). | [knowledge_map.cpp:69](../../src/freelancer/Client/knowledge_map.cpp#L69) |

### 5.4 `interface\ButtonMontage.ini` — `[Montage]`

Describes the icon atlas that button models are drawn from ([nn_montage_draw.cpp:32](../../src/freelancer/Client/nn_montage_draw.cpp#L32)). The textures themselves come from `Interface\ButtonTextures.ini`, a shape database ([client-audio-misc.md](client-audio-misc.md#5-shape-databases-texture-and-shape)), whose shapes `Montage32`, `Montage64`, `HUD_targetingelement` and `HUD_talkelement` are looked up by name.

Within each `[Montage]` section the keys are processed in order:

| Key | Type | Default | Meaning / allowed values | Source |
|---|---|---|---|---|
| `size` | int | `0` | Tile edge in pixels of the 256-pixel atlas page; tiles per row = `256 / size` (4 if `size <= 0`). Resets the tile cursor to the page origin. Selects the shape: `32` → `Montage32`, `64` → `Montage64`. | [nn_montage_draw.cpp:70](../../src/freelancer/Client/nn_montage_draw.cpp#L70) |
| `texture` | int | `0` | Atlas selector: `2` → `HUD_targetingelement`, `3` → `HUD_talkelement` (tile step fixed at `0.5`); any other value picks the shape by `size`. | [nn_montage_draw.cpp:81](../../src/freelancer/Client/nn_montage_draw.cpp#L81) |
| `num_pages` | int | – | Read and discarded. | [nn_montage_draw.cpp:85](../../src/freelancer/Client/nn_montage_draw.cpp#L85) |
| *any other key* | `<anything> [, scale]` | – | The **key name is a tile name**: it is matched (case-insensitively) against the button's `mesh` string (or a maneuver's mesh strings). Tiles are assigned to atlas cells in file order, left to right then top to bottom (a page wraps back to the start after the last row). The first parameter is ignored; the optional second parameter is the icon scale (default `0`). | [nn_montage_draw.cpp:89](../../src/freelancer/Client/nn_montage_draw.cpp#L89) |

Because the tile name must equal a mesh path, `mesh = interface\...\example.3db` in a button section uses the montage tile named `interface\...\example.3db` when one exists.


### Port-only Freeflight and Go To action strips

Three cockpit shortcuts start unassigned: contextual evasion invokes the clockwise
spiral in Freeflight or sine weave during Go To/F2; the other commands invoke the
engine-kill turn and reverse/alternating strafe, both only in Freeflight.
Options > Controls lists all three commands, and button tooltips show their
current bindings. A second press cancels the action; held-key repeats are ignored.

With `FreelancerPlayerFlightActions=1`, `port.ini [FlightActions] enabled`
(integer, default 1) controls the additional Freeflight and Go To action buttons.
`reverse_strafe_interval` (float seconds, default 2.0) in the same section
sets how long to strafe each way during continuous reverse: left first, then
right, repeating until cancelled. Any finite positive interval is accepted;
invalid values fall back to 2.0. The config is cached; restart after editing it.
`goto_weave_interval` (float seconds, default 2.0) sets the half-wave duration
for Go To's alternating yaw turns: a full sine cycle takes twice this value.
It accepts finite positive values, otherwise falling back to 2.0.
`goto_weave_angle` (float degrees, default 25.0) sets the requested yaw amplitude
to either side of the destination bearing, clamped to 0..60; nonfinite values
fall back to 25.0. The ship turns through physical steering torque and flies
forward, with no added strafe/nudge. The old `goto_weave_strength` is unused.
The wave ramps in over one second and fades near arrival. The third-person camera keeps a stable route
heading and up direction. Repeating the click or manual flight input cancels it.
No extra `hud.ini maneuver` entries are needed. The four primary maneuvers
remain unchanged; actions are children of the Freeflight or Go To tab. See
[Freeflight actions](../hud_plugins.md#freeflight-actions-port-only-prototype)
for assets, input behavior and validation limits.

### Port-only route navigation

`port.ini [Navigation]`, with `FreelancerPlayerFlightActions=1`.
Miscellaneous > Navigation exposes the generator, F2 route following and
automatic base docking, alongside the two existing tooltip/rollover-help options.
Navigation preferences apply after confirmation and are saved globally in
`navigation.ini` under the user data directory. Explicit user values override
the defaults below; these controls also work in the main menu. Cancel discards
pending changes; Defaults resets only the selected Miscellaneous tab.

| Key | Default | Meaning |
| --- | --- | --- |
| `autopilot` | `1` | F2 follows player waypoints, enters trade lanes and jumps through gates/holes along the route. `0` restores native F2; disabling it during a route leaves the current native maneuver running, without braking. |
| `auto_dock` | `1` | Allows automatic docking with bases, including planetary docking rings. `0` continues from the checked approach using native F2/Go To to the base, without stopping at the preceding waypoint or issuing Dock. F3 remains manual. Lane entry and gate/hole jumps remain part of F2, independent of this setting. Does not interrupt a Dock already in progress. |
| `route_generator` | `beta` | Shown as Avoid obstacles (Обход препятствий): recovered Beta patrol-corridor rules plus a new hazard-checking graph search for local free-space legs. `retail` is Standard and preserves the original map generator. |
| `clearance` | `300` | Additional metres outside hazardous volumes, clamped to 150..3000; player hull radius is added. |
| `dock_distance` | `2000` | Preferred approach radius for native Dock handoff, clamped to 750..5000; enlarged for hull/clearance. Tries other directions and, if all are occupied, up to twice this radius. |

The UI settings do not require a restart. Generator changes affect subsequent
route planning. Inter-system/trade-lane topology
comes from the server. Atmospheres, solid solars and damage zones are checked
in the loaded system, including after a jump. Mouse steering temporarily overrides
F2; releasing it resumes the route. Native collision avoidance can reduce speed; points do not themselves
force a cruise restart. See [implementation and validation](../hud_plugins.md#f2-route-autopilot-and-beta-corridor-planner).

For non-dockable objects, map refinement and F2 share an arrival-region search
outside the object's physical bounds or atmosphere plus hull/clearance. Nearby
station parts remain obstacles; alternate approach directions are tried without
adding an unchecked segment into the object. The selected object remains the
route's goal. An impossible safe approach still reports no path.


## Desktop HUD perspective prototype

User `PerfOptions.ini`, section `[HUD]`: `hud_tilt_degrees` (integer degrees, default 0, range 0..50; non-finite values become 0). Options > Miscellaneous > General > HUD tilt uses native arrows with a 2-degree step; Apply saves, Cancel discards edits and Defaults selects 0. This setting is available in the main menu and in flight; it does not change the retail PerfCount. Requires RP9 and widescreen support. Rotates flight side panels with their text and ShipView; central markers and the radar remain unchanged. The experimental `port.ini [Render]` key is retired. Console `hud_tilt 0..50` overrides the angle for this process only; it does not change character saves or write the INI. Set 0 for the original flat presentation. See [checks and limitations](../../tools/hud_tilt/README.txt).

### Resolution dropdown

The Interface settings resolution field uses a vertical, ascending dropdown of supported 32-bit modes. The existing one-height-per-width desktop-aspect selection is retained; refresh-rate duplicates are not listed. Eight rows are visible at once, with mouse-wheel and Up/Down, Page Up/Page Down, Home/End navigation and a scroll-position indicator. Enter/click stages the selection; Escape or clicking outside dismisses without changing it. Native Apply, confirmation timeout, Cancel and persistence remain in place. 16-bit modes are excluded from the choices; internal legacy-mode lookup remains for rollback. Checks: `python tools/targeting_hud/check_dropdown.py` and `python tools/targeting_hud/check_video_modes.py`.

### User graphics settings (RP9)

The first Interface page uses its former Miscellaneous area for nine graphics settings.
Display and mouse section headings are removed and their three controls are compacted; toggles use native checkboxes and quality/mode
choices use the same dropdown as resolution. All nine settings are staged until the
native Apply confirmation. Cancel restores the snapshot and Defaults stages defaults.
The page explicitly says that these settings require a full game restart, in both
the main menu and flight. Changing resolution or returning to the menu does not
apply a pending graphics change.

User `PerfOptions.ini` has a separate `[Graphics]` section; the original 36-entry
PerfCount and `[HUD]` section are retained. Values are choice indices:

| Key | Values | Default |
| --- | --- | --- |
| `shadows` | 0 off, 1 low, 2 medium, 3 high | 3 |
| `relief` | 0 off, 1 on | 1 |
| `highlights` | 0 off, 1 on | 1 |
| `reflections` | 0 off, 1 on | 1 |
| `anisotropy` | 0 off, 1 2x, 2 4x, 3 8x, 4 16x | 4 |
| `antialiasing` | 0 off, 1 FXAA, 2 SMAA 1x High | 2 |
| `nebulae` | 0 off, 1 low, 2 medium, 3 high | 3 |
| `vsync` | 0 off, 1 on | 1 |
| `fps_limit` | 1 30, 2 60, 3 75, 4 90, 5 120, 6 144, 7 165, 8 180 | 6 |

On first use, existing port.ini VSync, anisotropy and listed FPS values are migrated.
FPS is capped at 180: old unlimited/240/360 indices (0/9/10) migrate to index 8,
and the dropdown offers only 30..180. The restart hint has its own row above the buttons.
Malformed/out-of-range saved values fall back to those defaults. Common owns one
immutable active snapshot, read from the same redirected save folder as the client;
RP9 reads that snapshot through `PortGraphicsRenderValue`. Configured values are
separate and never partially update existing render caches.

Shadow low/medium cap map resolution at 1024/2048 and sample counts at 8/16; high
retains authored values. Off also disables room contact/object shadows and native
hangar shadow fallback. Relief controls ship/solar maps, cockpit, rocks, planets,
ice and alien surfaces. Highlights include weapon glints and room materials;
reflections gate environment maps and glass/ice reflections. These gates preserve
other material features and authored emission. Anisotropy is capped by the device.
AA runs before the HUD; SMAA retains its existing FXAA fallback on shader failure.

Nebula low/medium cap resolution scale at 0.25/0.5, marching steps at 32/64 and
shadow steps at 2/4. Quality overrides are applied after per-nebula style patches;
Off cannot be overridden by a style and restores the native fallback. Density,
colour and visibility distances remain authored values. High retains authored
quality. User settings never rewrite port.ini or volumetric.ini.

Checks: `python tools/graphics_settings/check.py` (real policy, save writer and UI
methods with fixture dependencies), `check_native.py` (built Common and RP9 bridge,
redirected save folder), and `check_gpu.py` (hidden D3D9 device, shader variants and
pixel comparisons for independent highlights/reflections). `prepare.py` stages
the client, Common, RP9 and surface shader for a hash-checked installation with
backup and rollback. Game INIs and character saves are not part of the payload.
