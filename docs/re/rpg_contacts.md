# Static RPG contacts

First presence slice, independent of StoryLauncher and mission controllers. Build
Content with `FreelancerRpgWorld=1` (`FREELANCER_RPG_WORLD`); default is 0, including
Diagnostics. The enabled DLL reads `DATA/RPG/contacts.ini`. Presence and a plain
click cutscene use existing GF messages. The optional choices prototype requires
both Content and the client built with this flag; no new packet layout is added.

Each `[RpgContact]` declares `nickname`, `enabled` (default false), `base`, `rtc`
(relative to DATA). The catalog is read on base entry; edits take effect on the
next base visit. A missing catalog has no contacts. Paths must be relative.

The loader accepts a small RTC subset with an optional click cutscene:

* `[CharacterEncounter] Location = base, room`, exactly one location.
  Optional `click_script = scripts\generated\m10_offer_accept.thn` attaches
  a single THN to the first `[Char]`; omission leaves a presence-only contact.
  Optional `choices = true` appends the RPG choice stage after that THN (requires
  `click_script`). Defaults to false.
* `[Reserve] spot = placement` (repeat for several distinct places).
* `[Char] npc`, `actor`, `spot`, `fidget`. Each actor needs a distinct role and
  placement; every actor placement must be reserved. Role <32 bytes, fidget <64.
* Local `[NPC]` records use existing character-description keys: nickname,
  body/head/hands/accessory or base_appr, voice, individual_name, affiliation.
  They are resolved locally, never added to Story's `GSpecificNpcs`.

This is not yet a conversation controller. Action/offer/decision/autoplay and
unknown RTC sections/keys are rejected. There is no mission offer. The optional
click script uses the native character-behavior player without generic bar/GCS
scripts, autoplay, relocation, decisions or a Story RTCDone id. It uses authored
coordinates and no explicit room actor bindings; the player actor and costume
templates resolve through the native THN loader. It can be replayed by clicking.
`StartBarCharacterScript` skips characters owned by RPG visits, including contacts
without a click script. This guard also covers room refreshes after other dialogs.
RtcSlider graphics settings are unchanged; the disconnected part is generic GCS.

Contacts reserve places before ordinary fixtures/population. An occupied/locked
place, an authored fixture collision, duplicate role, missing local NPC, missing
placement or invalid RTC rejects the whole contact before room mutation. Each
player owns a separate presence; repeated entry does not duplicate it. Owned
characters and counted locks are released on base exit, logout, base unload and
world reset, using FBarScene::Release. No persistent handles enter a save. The
static definition recreates presence after SP load or MP reconnect.

The supplied generator creates `rpg_biz_contact` at `rh_biz_01_base`, Bar,
`Zg/NPC/mFloor2/01/A/Stand`. He wears Rheinland guard clothing and uses
`scripts\extras\fidget_stand_male_01.thn`. The name uses existing faction IDS
196847 until an individual dialogue/name is authored.
Its test click script is the existing 11.324-second `m10_offer_accept.thn` (Trent,
Darcy and Hassler). This tests launch/return, not adaptation of scene coordinates
and cameras to the Bismarck bar. The scene file itself is not modified.

With choices enabled the next entry is generated `RPG/dialogue_choice.thn`: player
actor at `special/p`, mapped from this NPC placement to the room's `P/Stand`, and
`camera/PCU` mapped to the room's player close-up camera. The standing idle and
camera script loops until the menu closes. A local WinControl overlay presents
four numbered Russian text options; click or keys 1-4 choose. Three open distinct
placeholder replies with Back/End, the fourth (or Esc) ends the conversation.
The overlay uses draw sublayer 7 (the manager only draws 0..7). During choices
the player uses one ordinary `Sc_MLBODY_STND_IDLE_000LV_XB_04` motion in the
choice THN, looped while the menu is open. There is no separate player fidget
sequence and no alternation between gestures. The menu's sequence owns the motion,
position and camera and tears them down together on exit.
The story's CHRB idle is seated and unsuitable for the standing PCU framing.
Captions/replies are currently a compiled client prototype in `rpg_dialog.cpp`,
not generated dialogue content. Persuasion/threat are labels only; no skill rolls,
reputation changes or server decisions. The normal sequence restores player,
camera and room input on exit; sequence teardown destroys the overlay/capture.
Behavior offer type `0x525047` and entry kind 7 isolate this from native mission
offers and the generic skip path. Clients must install the matching binary.

## Build and installation

* `tools/rpg_contacts/build.ps1 -Enabled 1` builds an isolated Release Content.
* Repeat with `-Enabled 0`; use `-Configuration DebugASan` for an ASan build.
* Add `-Client` to build the corresponding client, isolated from the main bin.
* `tools/rpg_contacts/check.ps1` runs production parser/lifecycle code against a
  fake GF room: two players, repeated enter, logout/re-entry, exit/unload/reset,
  occupied/fixture conflicts, malformed records and failed creation rollback.
  It also runs the real generic-script entry point to check owned behavior is
  preserved, normal NPCs still use GCS, and behavior cleanup/creation rollback.
  It substitutes the INI/GF adapters; this is not a renderer or network test.
* `python tools/rpg_contacts/install.py` validates the installed Bismarck room's
  marker, player camera/place, fidget and fixtures, then stages DLL/EXE/PDBs,
  two INIs, the choice THN and a standalone
  Pythonlancer tool. `--apply` installs only those files with hash checks and backups.
* The installed Pythonlancer tool is invoked explicitly:
  `python tools/rpg_contacts.py --output <staging-root>`. It is not automatically
  imported by LancerCore; existing world generation is unchanged.

In-game acceptance still requires entering/leaving the bar, launching and
redocking, SP save/load and two MP clients entering independently. Check animation,
placement and absence of duplicate NPCs. Also check click, finish/skip, second
click, and talking to an ordinary NPC before clicking the RPG contact again.
The user confirmed initial NPC/fidget and click cutscene. The new choices need
visual validation: camera framing, mouse targets at different aspect ratios,
all four choices, back/exit/Esc, replay, scene teardown/disconnect and two MP clients.
No full RPG world persistence is added.

## Space contact prototype

`DATA/RPG/space.ini`, emitted by the same generator, defines an enabled
`[RpgShip]` named `rpg_biz_hassler`. Player load, system entry and departure
register players for a once-per-second presence check of their live ship's
system. Loading directly in space or arriving through a jump also creates
one server-owned ship beside the active `rh_biz_01` docking ring. The offset
`-1000, 200, 400` is in world axes (about 1.1 km from the ring).
It uses `rh_elite`, the installed mission-three loadout `ms3_hassler`,
`mod_fighter_universe`, Hassler's name/costume, and an idle directive.
The `m03_hassler` reference in the mission NPC archetype has no matching loaded
loadout; this prototype explicitly uses the existing `ms3_hassler` entry.

The ship is shared by all clients, friendly to players in that system,
and survives player logout. Repeated checks reuse the same object.
`respawn_seconds = 60` delays respawn after disappearance, and `0` disables
respawn until world reset. Respawn requires a player in the system; failed
creation retries after five seconds. World reset clears tracking and timers.
No ship state or respawn timer is serialized
and no quest, escort or conversation in space is started.

`check.ps1` additionally runs the production space lifecycle against mocked
server APIs: space-load readiness, system arrival, two players, duplicate
suppression, logout, delayed/disabled respawn, reset, and creation rollback/retry.
Actual position, AI and MP replication still require an in-game check.
